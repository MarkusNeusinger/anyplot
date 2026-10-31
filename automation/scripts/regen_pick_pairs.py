#!/usr/bin/env python3
"""Pick the night's work for daily-regen's pair mode.

Spec mode, the default, regenerates the N oldest specs with all their
libraries. Pair mode spends the night's N on two kinds of work:

1. Resumes first. Open implementation PRs whose review or repair Claude
   stopped (a spend or usage limit, or refused credentials) carry
   ``ai-review-paused`` or ``ai-repair-paused``; the oldest of them are
   re-dispatched before anything new. A refused request costs nothing, so a
   stop that is still active only pauses them again, and they resume on
   their own once it lifts.
2. Then the oldest implementations, one (spec, library) pair each, across the
   catalogue:

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
  a generation Claude stopped (its own pause comment, ``impl-paused-claude``)
  are not attempts: the pair stays in the queue and comes back on a later
  night.
- A pair with an open implementation PR is skipped: its attempt is still
  running, stuck or paused, and the watchdog or the resume owns it.
- Every pair of a spec whose issue saw activity within ``--min-age-hours`` is
  skipped, like the spec mode's postponement: a comment, a label or a report
  holds the spec back, and a night does not stack a spec whose last batch is
  still in flight.
- An unparseable metadata timestamp skips the pair, as in spec mode. Only
  pairs with a metadata file and a ``specification.md`` are candidates, so
  pair mode never writes a first implementation; gap backfill stays with
  ``bulk-generate.yml``.

The implementation-PR listing is the loop guard: when it fails, the run stops
with an error instead of picking without it. The kept-regeneration and issue
listings are best effort (one ``gh`` call each, at most 1000 entries, most
recent first; kept regenerations reach much further back than the PR
listing). The failed-generation comments are read per spec issue, only for
the specs at the front of the queue, at most ``--max-issue-reads`` issues per
run; a spec whose comments cannot be read is left out of the night.

Usage, from the repository root::

    python3 automation/scripts/regen_pick_pairs.py --count 5 --min-age-hours 20 \\
        --attempt-window-days 30 --repo OWNER/NAME --libraries "altair bokeh ..."

The library list comes from the caller (``core.constants.SUPPORTED_LIBRARIES``),
so this file carries no copy that could drift. Writes ``resume_json``,
``resume_count``, ``pairs_json``, ``specs``, ``specs_json`` and ``count`` (new
pairs) to ``$GITHUB_OUTPUT`` and a table of both to ``$GITHUB_STEP_SUMMARY``.
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
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import yaml


ANCIENT = datetime.min.replace(tzinfo=timezone.utc)
LIMIT = "1000"
BRANCH_RE = re.compile(r"^implementation/(?P<spec>[a-z0-9][a-z0-9-]*)/(?P<lib>[a-z0-9]+)$")
ATTEMPT_RE = re.compile(r"^ai-attempt-(?P<n>[0-9]+)$")
# impl-generate.yml "Handle generation failure": every failure comment carries
# the marker; an infrastructure failure's comment also carries the infra tag.
FAIL_MARKER_RE = re.compile(r"<!-- impl-fail:(?P<spec>[a-z0-9][a-z0-9-]*):(?P<lib>[a-z0-9]+) -->")
INFRA_TAG = "<!-- impl-fail-cause:infra -->"
# impl-review.yml and impl-repair.yml set these when Claude stopped the session.
PAUSED_LABELS = {"ai-repair-paused": "repair", "ai-review-paused": "review"}

Pair = tuple[str, str]


class ListingError(Exception):
    """A listing the pick cannot do without failed."""


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


@dataclass(frozen=True)
class Resume:
    pr: int
    kind: str  # "review" or "repair"
    spec: str
    library: str
    attempt: int
    updated: datetime


@dataclass
class Records:
    """What GitHub says about past attempts, per pair and per spec issue."""

    attempts: dict[Pair, tuple[datetime, str]]
    open_pairs: set[Pair]
    issue_activity: dict[int, datetime]
    paused: list[Resume] = field(default_factory=list)


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
    """An open PR blocks its pair (and is a resume when paused); a merged or closed one is an attempt."""
    for pull in pulls:
        match = BRANCH_RE.match(str(pull.get("headRefName") or ""))
        if not match:
            continue
        pair = (match["spec"], match["lib"])
        state = pull.get("state")
        labels = {str(label.get("name")) for label in pull.get("labels") or [] if isinstance(label, dict)}
        if state == "OPEN":
            records.open_pairs.add(pair)
            kind = next((PAUSED_LABELS[name] for name in PAUSED_LABELS if name in labels), None)
            number = pull.get("number")
            if kind and isinstance(number, int) and all(r.pr != number for r in records.paused):
                attempts = [int(m["n"]) for name in labels if (m := ATTEMPT_RE.match(name))]
                updated = parse_ts(str(pull.get("updatedAt") or "")) or ANCIENT
                records.paused.append(Resume(number, kind, pair[0], pair[1], max(attempts, default=1), updated))
            continue
        if state not in ("MERGED", "CLOSED"):
            continue
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


def resumes(records: Records, count: int) -> list[Resume]:
    """The oldest paused reviews and repairs, at most ``count``."""
    return sorted(records.paused, key=lambda r: (r.updated, r.pr))[:count]


def pick(
    candidates: Iterable[Candidate],
    records: Records,
    spec_issues: dict[str, int],
    now: datetime,
    min_age: timedelta,
    window: timedelta,
    count: int,
    failures: Callable[[str], dict[str, datetime] | None] | None = None,
    max_reads: int = 100,
) -> tuple[list[Pick], int]:
    """The ``count`` oldest eligible pairs, oldest first, and how many were eligible.

    ``failures(spec)`` returns the spec's failed generations per library, or
    None when they cannot be read. It is asked lazily, once per spec, when one
    of the spec's pairs reaches the front of the queue; a pair whose failure is
    newer than its age goes back into the queue, or out of it while the
    failure is within the window. A spec whose failures cannot be read is
    left out of the night (fail closed: its pairs may have failed last night).
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
    unreadable: set[str] = set()
    picks: list[Pick] = []
    while queue and len(picks) < count:
        key, spec, lib, basis = heapq.heappop(queue)
        if failures is not None and spec not in read:
            if len(read) == max_reads:
                print(f"::warning::Read the failed generations of {max_reads} specs; picking the rest without them")
                failures = None
            else:
                read.add(spec)
                found = failures(spec)
                if found is None:
                    unreadable.add(spec)
                    print(f"::warning::Leaving {spec} out of tonight: its failed generations could not be read")
                for flib, when in (found or {}).items():
                    _newer(records.attempts, (spec, flib), when, "failed generation")
        if spec in unreadable:
            eligible -= 1
            continue
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
        print(f"::warning::Could not list {what} ({' '.join(str(exc).split())[:200]})")
        return None
    return data if isinstance(data, list) else None


def read_records(repo: str) -> Records:
    records = Records(attempts={}, open_pairs=set(), issue_activity={})
    fields = "number,headRefName,state,updatedAt,closedAt,labels"
    pr_list = ["pr", "list", "--repo", repo, "--limit", LIMIT, "--json", fields]
    pulls = _gh_json(
        [*pr_list, "--state", "all", "--search", "head:implementation/ sort:updated-desc"], "implementation PRs"
    )
    if pulls is None:
        # The loop guard: without it a kept, closed or paused pair would be
        # picked again tonight.
        raise ListingError("the implementation PRs could not be listed")
    fold_pulls(pulls, records)
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
        f"::notice::Attempt records for {len(records.attempts)} pair(s), {len(records.open_pairs)} open PR(s) "
        f"({len(records.paused)} paused), activity for {len(records.issue_activity)} issue(s)"
    )
    return records


def issue_failures(repo: str, spec_issues: dict[str, int]) -> Callable[[str], dict[str, datetime] | None]:
    """``failures(spec)`` backed by the spec issue's comments (one paginated read per spec)."""

    def failures(spec: str) -> dict[str, datetime] | None:
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
            return None
        return failed_generations(comments, spec)

    return failures


def summary_table(resumed: list[Resume], picks: list[Pick], eligible: int, count: int) -> str:
    lines = [f"### Pair mode: {len(resumed)} resumed, {len(picks)} new pair(s) of {count} ({eligible} eligible)", ""]
    if resumed:
        lines += ["| Resume | PR | Spec | Library |", "|--------|----|------|---------|"]
        lines += [f"| {r.kind} | #{r.pr} | `{r.spec}` | `{r.library}` |" for r in resumed]
        lines.append("")
    lines += ["| # | Spec | Library | Last touched | From |", "|---|------|---------|--------------|------|"]
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
    try:
        records = read_records(args.repo)
    except ListingError as exc:
        print(f"::error::Pair mode stops: {exc}, so the pick would lose its record of last nights' attempts")
        return 1
    resumed = resumes(records, args.count)
    picks, eligible = pick(
        candidates,
        records,
        spec_issues,
        datetime.now(timezone.utc),
        timedelta(hours=args.min_age_hours),
        timedelta(days=args.attempt_window_days),
        args.count - len(resumed),
        failures=issue_failures(args.repo, spec_issues),
        max_reads=args.max_issue_reads,
    )

    print(f"::notice::Resumed: {[f'#{r.pr} {r.kind}' for r in resumed]}")
    print(
        f"::notice::Eligible pairs: {eligible} (attempt window {args.attempt_window_days} d)  "
        f"picked: {[f'{p.spec}/{p.library}' for p in picks]}"
    )
    for p in picks:
        print(f"  - {p.spec + '/' + p.library:52s}  last_touched={p.touched.isoformat()}  ({p.basis})")

    specs = list(dict.fromkeys(p.spec for p in picks))
    pairs = [{"spec": p.spec, "library": p.library} for p in picks]
    resume_rows = [
        {"pr": r.pr, "kind": r.kind, "spec": r.spec, "library": r.library, "attempt": r.attempt} for r in resumed
    ]
    with open(os.environ["GITHUB_OUTPUT"], "a", encoding="utf-8") as f:
        f.write(f"resume_json={json.dumps(resume_rows, separators=(',', ':'))}\n")
        f.write(f"resume_count={len(resumed)}\n")
        f.write(f"pairs_json={json.dumps(pairs, separators=(',', ':'))}\n")
        f.write(f"specs={' '.join(specs)}\n")
        f.write(f"specs_json={json.dumps(specs)}\n")
        f.write(f"count={len(picks)}\n")
    summary = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary:
        with open(summary, "a", encoding="utf-8") as f:
            f.write(summary_table(resumed, picks, eligible, args.count))
    return 0


if __name__ == "__main__":
    sys.exit(main())
