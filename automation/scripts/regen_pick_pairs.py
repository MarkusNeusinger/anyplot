#!/usr/bin/env python3
"""Pick the oldest implementations for daily-regen's pair mode.

Spec mode, the default, regenerates the N oldest specs with all their
libraries. Pair mode picks the N oldest implementations, one (spec, library)
pair each, across the catalogue:

- A pair's age counts from its newest touch: its metadata ``updated``
  (``created`` when there is none), or its last real regeneration attempt,
  whichever is newer. A pair touched within ``--attempt-window-days``
  (default 30) is not picked, so an attempted pair waits at least that long
  and then queues behind every pair touched before it.
- A real attempt is one that reached a verdict or burned a generation attempt:
  the pair's implementation PR (head ``implementation/<spec>/<library>``)
  once it is merged or closed (a ``regen:kept`` PR included), and a failed
  generation, which leaves an ``<!-- impl-fail:<spec>:<library> -->`` comment
  on the spec issue. A merge moves ``updated`` anyway; the other two leave it
  alone, and without them the same pair would come back the next night. An
  infrastructure failure (its comment carries ``impl-fail-cause:infra``) and
  a stop at the Claude spend limit (its own pause comment) are not attempts:
  the pair stays in the queue and comes back on a later night.
- A pair with an open implementation PR is skipped: its attempt is still
  running or stuck, and the watchdog owns it.
- Every pair of a spec whose issue saw activity within ``--min-age-hours`` is
  skipped, like the spec mode's postponement: a comment, a label or a report
  holds the spec back, and a night does not stack a spec whose last batch is
  still in flight.
- An unparseable metadata timestamp skips the pair, as in spec mode. Only
  pairs with a metadata file and a ``specification.md`` are candidates, so
  pair mode never writes a first implementation; gap backfill stays with
  ``bulk-generate.yml``.

The PR and issue listings are one ``gh`` call each, at most 1000 entries, most
recent first (kept regenerations get a listing of their own, which reaches
much further back). The failed-generation comments are read per spec issue,
only for the specs at the front of the queue, at most ``--max-issue-reads``
issues per run. A read that fails degrades to the other records with a
warning, like the spec mode's issue listing.

Usage, from the repository root::

    python3 automation/scripts/regen_pick_pairs.py --count 5 --min-age-hours 20 \\
        --attempt-window-days 30 --repo OWNER/NAME --libraries "altair bokeh ..."

The library list comes from the caller (``core.constants.SUPPORTED_LIBRARIES``),
so this file carries no copy that could drift. Writes ``pairs_json``,
``specs``, ``specs_json`` and ``count`` to ``$GITHUB_OUTPUT`` and a table of
the picks to ``$GITHUB_STEP_SUMMARY``.
"""

from __future__ import annotations

import argparse
import heapq
import json
import os
import re
import subprocess
import sys
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import yaml


ANCIENT = datetime.min.replace(tzinfo=timezone.utc)
LIMIT = "1000"
BRANCH_RE = re.compile(r"^implementation/(?P<spec>[a-z0-9][a-z0-9-]*)/(?P<lib>[a-z0-9]+)$")
# impl-generate.yml "Handle generation failure": every failure comment carries
# the marker; an infrastructure failure's comment also carries the infra tag.
FAIL_MARKER_RE = re.compile(r"<!-- impl-fail:(?P<spec>[a-z0-9][a-z0-9-]*):(?P<lib>[a-z0-9]+) -->")
INFRA_TAG = "<!-- impl-fail-cause:infra -->"

Pair = tuple[str, str]


@dataclass(frozen=True)
class Candidate:
    spec: str
    library: str
    metadata: datetime | None  # None: the metadata file names no timestamp


@dataclass(frozen=True)
class Pick:
    spec: str
    library: str
    touched: datetime
    basis: str


@dataclass
class Records:
    """What GitHub says about past attempts, per pair and per spec issue."""

    attempts: dict[Pair, tuple[datetime, str]]
    open_pairs: set[Pair]
    issue_activity: dict[int, datetime]


def parse_ts(raw: str) -> datetime | None:
    try:
        dt = datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError:
        return None
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


def load_candidates(plots: Path, libraries: Iterable[str]) -> tuple[list[Candidate], dict[str, int]]:
    """Every pair with a metadata file, plus each spec's issue number."""
    supported = set(libraries)
    candidates: list[Candidate] = []
    issues: dict[str, int] = {}
    for spec_dir in sorted(plots.iterdir()):
        if not spec_dir.is_dir() or spec_dir.name.startswith(".") or not (spec_dir / "specification.md").is_file():
            continue
        try:
            issue = (yaml.safe_load((spec_dir / "specification.yaml").read_text(encoding="utf-8")) or {}).get("issue")
        except OSError, yaml.YAMLError, AttributeError:
            issue = None
        if isinstance(issue, int):
            issues[spec_dir.name] = issue
        for meta in sorted(spec_dir.glob("metadata/*/*.yaml")):
            if meta.stem not in supported:
                continue
            try:
                data = yaml.safe_load(meta.read_text(encoding="utf-8")) or {}
            except OSError, yaml.YAMLError:
                continue
            if not isinstance(data, dict):
                continue
            raw = data.get("updated") or data.get("created")
            if not raw:
                candidates.append(Candidate(spec_dir.name, meta.stem, None))
                continue
            dt = parse_ts(str(raw))
            if dt is None:
                continue  # unparseable timestamp: skipped, as in spec mode
            candidates.append(Candidate(spec_dir.name, meta.stem, dt))
    return candidates, issues


def _newer(records: dict[Pair, tuple[datetime, str]], pair: Pair, when: datetime | None, basis: str) -> None:
    if when is not None and (pair not in records or when > records[pair][0]):
        records[pair] = (when, basis)


def fold_pulls(pulls: Iterable[dict[str, Any]], records: Records) -> None:
    """An open PR blocks its pair; a merged or closed one is the pair's attempt."""
    for pull in pulls:
        match = BRANCH_RE.match(str(pull.get("headRefName") or ""))
        if not match:
            continue
        pair = (match["spec"], match["lib"])
        state = pull.get("state")
        if state == "OPEN":
            records.open_pairs.add(pair)
            continue
        if state not in ("MERGED", "CLOSED"):
            continue
        labels = {str(label.get("name")) for label in pull.get("labels") or [] if isinstance(label, dict)}
        basis = "merged PR" if state == "MERGED" else "kept PR" if "regen:kept" in labels else "closed PR"
        when = parse_ts(str(pull.get("closedAt") or pull.get("updatedAt") or ""))
        _newer(records.attempts, pair, when, basis)


def fold_issues(issues: Iterable[dict[str, Any]], records: Records) -> None:
    for issue in issues:
        ts = parse_ts(str(issue.get("updatedAt") or ""))
        if ts and isinstance(issue.get("number"), int):
            records.issue_activity[issue["number"]] = ts


def failed_generations(comments: Iterable[dict[str, Any]], spec: str) -> dict[str, datetime]:
    """Newest failed generation per library of ``spec``, from the spec issue's comments."""
    newest: dict[str, datetime] = {}
    for comment in comments:
        body = str(comment.get("body") or "")
        if INFRA_TAG in body:
            continue  # an infrastructure failure, not an attempt
        when = parse_ts(str(comment.get("created_at") or ""))
        for match in FAIL_MARKER_RE.finditer(body):
            if match["spec"] == spec and when and (match["lib"] not in newest or when > newest[match["lib"]]):
                newest[match["lib"]] = when
    return newest


def _touched(pair: Pair, metadata: datetime | None, records: Records) -> tuple[datetime | None, str]:
    touched, basis = (metadata, "metadata") if metadata else (None, "none")
    attempt = records.attempts.get(pair)
    if attempt and (touched is None or attempt[0] > touched):
        touched, basis = attempt
    return touched, basis


def pick(
    candidates: Iterable[Candidate],
    records: Records,
    spec_issues: dict[str, int],
    now: datetime,
    min_age: timedelta,
    window: timedelta,
    count: int,
    failures: Callable[[str], dict[str, datetime]] | None = None,
    max_reads: int = 100,
) -> tuple[list[Pick], int]:
    """The ``count`` oldest eligible pairs, oldest first, and how many were eligible.

    ``failures(spec)`` returns the spec's failed generations per library. It is
    asked lazily, once per spec, when one of the spec's pairs reaches the front
    of the queue; a pair whose failure is newer than its age goes back into
    the queue, or out of it while the failure is within the window.
    """
    metadata: dict[Pair, datetime | None] = {}
    queue: list[tuple[datetime, str, str, str]] = []
    for cand in candidates:
        pair = (cand.spec, cand.library)
        if pair in records.open_pairs:
            continue
        issue_ts = records.issue_activity.get(spec_issues.get(cand.spec, -1))
        if issue_ts is not None and now - issue_ts < min_age:
            continue
        touched, basis = _touched(pair, cand.metadata, records)
        if touched is not None and now - touched < window:
            continue  # touched within the window: not yet
        metadata[pair] = cand.metadata
        queue.append((touched or ANCIENT, cand.spec, cand.library, basis))
    heapq.heapify(queue)
    eligible = len(queue)

    read: set[str] = set()
    picks: list[Pick] = []
    while queue and len(picks) < count:
        key, spec, lib, basis = heapq.heappop(queue)
        if failures is not None and spec not in read:
            if len(read) == max_reads:
                print(f"::warning::Read the failed generations of {max_reads} specs; picking the rest without them")
                failures = None
            else:
                read.add(spec)
                for flib, when in failures(spec).items():
                    _newer(records.attempts, (spec, flib), when, "failed generation")
        touched, new_basis = _touched((spec, lib), metadata[(spec, lib)], records)
        if (touched or ANCIENT) != key:
            if touched is not None and now - touched < window:
                eligible -= 1
                continue
            heapq.heappush(queue, (touched or ANCIENT, spec, lib, new_basis))
            continue
        picks.append(Pick(spec, lib, key, basis))
    return picks, eligible


def _gh_json(args: list[str], what: str) -> list[dict[str, Any]] | None:
    try:
        raw = subprocess.run(["gh", *args], check=True, capture_output=True, text=True).stdout
        data = json.loads(raw)
    except (subprocess.CalledProcessError, ValueError, OSError) as exc:
        print(f"::warning::Could not list {what} ({' '.join(str(exc).split())[:200]}) — picking without them")
        return None
    return data if isinstance(data, list) else None


def read_records(repo: str) -> Records:
    records = Records(attempts={}, open_pairs=set(), issue_activity={})
    pr_list = ["pr", "list", "--repo", repo, "--limit", LIMIT, "--json", "headRefName,state,updatedAt,closedAt,labels"]
    pulls = _gh_json(
        [*pr_list, "--state", "all", "--search", "head:implementation/ sort:updated-desc"], "implementation PRs"
    )
    fold_pulls(pulls or [], records)
    # Kept regenerations again on their own: they are the attempts that leave
    # `updated` alone, and this listing reaches much further back.
    kept = _gh_json(
        [*pr_list, "--state", "closed", "--label", "regen:kept", "--search", "sort:updated-desc"], "kept regenerations"
    )
    fold_pulls(kept or [], records)
    issues = _gh_json(
        ["issue", "list", "--repo", repo, "--state", "all", "--search", "sort:updated-desc", "--limit", LIMIT]
        + ["--json", "number,updatedAt"],
        "issues",
    )
    fold_issues(issues or [], records)
    print(
        f"::notice::Attempt records for {len(records.attempts)} pair(s), {len(records.open_pairs)} open PR(s), "
        f"activity for {len(records.issue_activity)} issue(s)"
    )
    return records


def issue_failures(repo: str, spec_issues: dict[str, int]) -> Callable[[str], dict[str, datetime]]:
    """``failures(spec)`` backed by the spec issue's comments (one paginated read per spec)."""

    def failures(spec: str) -> dict[str, datetime]:
        issue = spec_issues.get(spec)
        if issue is None:
            return {}
        jq = '.[] | select(.body != null and (.body | contains("<!-- impl-fail:"))) | {created_at, body} | @json'
        try:
            raw = subprocess.run(
                ["gh", "api", "--paginate", f"repos/{repo}/issues/{issue}/comments?per_page=100", "--jq", jq],
                check=True,
                capture_output=True,
                text=True,
            ).stdout
            comments = [json.loads(line) for line in raw.splitlines() if line.strip()]
        except (subprocess.CalledProcessError, ValueError, OSError) as exc:
            print(f"::warning::Could not read the comments of issue #{issue} ({' '.join(str(exc).split())[:200]})")
            return {}
        return failed_generations(comments, spec)

    return failures


def summary_table(picks: list[Pick], eligible: int, count: int) -> str:
    lines = [
        f"### Pair mode: {len(picks)} of {count} requested ({eligible} eligible)",
        "",
        "| # | Spec | Library | Last touched | From |",
        "|---|------|---------|--------------|------|",
    ]
    for i, p in enumerate(picks, 1):
        touched = "never" if p.touched == ANCIENT else p.touched.strftime("%Y-%m-%dT%H:%M:%SZ")
        lines.append(f"| {i} | `{p.spec}` | `{p.library}` | {touched} | {p.basis} |")
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0] if __doc__ else None)
    parser.add_argument("--count", type=int, required=True)
    parser.add_argument("--min-age-hours", type=int, required=True)
    parser.add_argument("--attempt-window-days", type=int, default=30)
    parser.add_argument("--max-issue-reads", type=int, default=100)
    parser.add_argument("--repo", required=True)
    parser.add_argument("--libraries", required=True, help="space-separated supported libraries")
    parser.add_argument("--plots", default="plots")
    args = parser.parse_args(argv)

    libraries = args.libraries.split()
    if args.count < 1 or args.attempt_window_days < 0 or not libraries:
        print("::error::--count must be at least 1, --attempt-window-days at least 0, and --libraries not empty")
        return 1

    candidates, spec_issues = load_candidates(Path(args.plots), libraries)
    records = read_records(args.repo)
    picks, eligible = pick(
        candidates,
        records,
        spec_issues,
        datetime.now(timezone.utc),
        timedelta(hours=args.min_age_hours),
        timedelta(days=args.attempt_window_days),
        args.count,
        failures=issue_failures(args.repo, spec_issues),
        max_reads=args.max_issue_reads,
    )

    print(
        f"::notice::Eligible pairs: {eligible} (attempt window {args.attempt_window_days} d)  "
        f"picked: {[f'{p.spec}/{p.library}' for p in picks]}"
    )
    for p in picks:
        print(f"  - {p.spec + '/' + p.library:52s}  last_touched={p.touched.isoformat()}  ({p.basis})")

    specs = list(dict.fromkeys(p.spec for p in picks))
    pairs = [{"spec": p.spec, "library": p.library} for p in picks]
    with open(os.environ["GITHUB_OUTPUT"], "a", encoding="utf-8") as f:
        f.write(f"pairs_json={json.dumps(pairs, separators=(',', ':'))}\n")
        f.write(f"specs={' '.join(specs)}\n")
        f.write(f"specs_json={json.dumps(specs)}\n")
        f.write(f"count={len(picks)}\n")
    summary = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary:
        with open(summary, "a", encoding="utf-8") as f:
            f.write(summary_table(picks, eligible, args.count))
    return 0


if __name__ == "__main__":
    sys.exit(main())
