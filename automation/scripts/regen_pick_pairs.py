#!/usr/bin/env python3
"""Pick the oldest implementations for daily-regen's pair mode.

Spec mode, the default, regenerates the N oldest specs with all their
libraries. Pair mode picks the N oldest implementations, one (spec, library)
pair each, across the catalogue, and applies the spec mode's rules per pair:

- A pair's age counts from the newer of its metadata ``updated`` (``created``
  when there is none) and its last regeneration attempt, so a regeneration the
  gate kept, which leaves ``updated`` alone, is not picked again the next
  night. The attempt record is the newest of the pair's implementation PR
  (head ``implementation/<spec>/<library>``, any state), its ``regen:kept`` PR
  and its ``impl-generate.yml`` run (``Generate: <library> for <spec>``, which
  also covers a generation that failed before it opened a PR).
- A pair younger than ``--min-age-hours`` is skipped, and so is every pair of
  a spec whose issue saw activity within that window: a comment, a label or a
  report postpones the spec as in spec mode, and a night does not stack a
  spec whose last batch is still in flight.
- A pair with an open implementation PR is skipped: its last attempt is still
  running or stuck, and the watchdog owns it.
- An unparseable metadata timestamp skips the pair, as in spec mode. Only
  pairs with a metadata file and a ``specification.md`` are candidates, so
  pair mode never writes a first implementation; gap backfill stays with
  ``bulk-generate.yml``.

Each listing is one ``gh`` call of at most 1000 entries, most recent first. A
listing that fails degrades to the other records with a warning, like the
spec mode's issue listing.

Usage, from the repository root::

    python3 automation/scripts/regen_pick_pairs.py --count 5 --min-age-hours 20 \\
        --repo OWNER/NAME --libraries "altair bokeh ..."

The library list comes from the caller (``core.constants.SUPPORTED_LIBRARIES``),
so this file carries no copy that could drift. Writes ``pairs_json``,
``specs``, ``specs_json`` and ``count`` to ``$GITHUB_OUTPUT`` and a table of
the picks to ``$GITHUB_STEP_SUMMARY``.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import yaml


ANCIENT = datetime.min.replace(tzinfo=timezone.utc)
LIMIT = "1000"
BRANCH_RE = re.compile(r"^implementation/(?P<spec>[a-z0-9][a-z0-9-]*)/(?P<lib>[a-z0-9]+)$")
RUN_TITLE_RE = re.compile(r"^Generate: (?P<lib>[a-z0-9]+) for (?P<spec>[a-z0-9][a-z0-9-]*)$")

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


def fold_pulls(pulls: Iterable[dict[str, Any]], basis: str, records: Records) -> None:
    for pull in pulls:
        match = BRANCH_RE.match(str(pull.get("headRefName") or ""))
        if not match:
            continue
        pair = (match["spec"], match["lib"])
        _newer(records.attempts, pair, parse_ts(str(pull.get("updatedAt") or "")), basis)
        if pull.get("state") == "OPEN":
            records.open_pairs.add(pair)


def fold_runs(runs: Iterable[dict[str, Any]], records: Records) -> None:
    for run in runs:
        match = RUN_TITLE_RE.match(str(run.get("displayTitle") or ""))
        if match:
            _newer(records.attempts, (match["spec"], match["lib"]), parse_ts(str(run.get("createdAt") or "")), "run")


def fold_issues(issues: Iterable[dict[str, Any]], records: Records) -> None:
    for issue in issues:
        ts = parse_ts(str(issue.get("updatedAt") or ""))
        if ts and isinstance(issue.get("number"), int):
            records.issue_activity[issue["number"]] = ts


def pick(
    candidates: Iterable[Candidate],
    records: Records,
    spec_issues: dict[str, int],
    now: datetime,
    min_age: timedelta,
    count: int,
) -> tuple[list[Pick], int]:
    """The ``count`` oldest eligible pairs, oldest first, and how many were eligible."""
    eligible: list[Pick] = []
    for cand in candidates:
        pair = (cand.spec, cand.library)
        if pair in records.open_pairs:
            continue
        issue_ts = records.issue_activity.get(spec_issues.get(cand.spec, -1))
        if issue_ts is not None and now - issue_ts < min_age:
            continue
        touched, basis = (cand.metadata, "metadata") if cand.metadata else (None, "none")
        attempt = records.attempts.get(pair)
        if attempt and (touched is None or attempt[0] > touched):
            touched, basis = attempt
        if touched is None:
            eligible.append(Pick(cand.spec, cand.library, ANCIENT, basis))
            continue
        if now - touched < min_age:
            continue  # too fresh to re-roll
        eligible.append(Pick(cand.spec, cand.library, touched, basis))
    eligible.sort(key=lambda p: (p.touched, p.spec, p.library))
    return eligible[:count], len(eligible)


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
    pr_list = ["pr", "list", "--repo", repo, "--limit", LIMIT, "--json", "headRefName,state,updatedAt"]
    pulls = _gh_json(
        [*pr_list, "--state", "all", "--search", "head:implementation/ sort:updated-desc"], "implementation PRs"
    )
    fold_pulls(pulls or [], "implementation PR", records)
    # Kept regenerations again on their own: they are the attempts that leave
    # `updated` alone, and this listing reaches much further back.
    kept = _gh_json(
        [*pr_list, "--state", "closed", "--label", "regen:kept", "--search", "sort:updated-desc"], "kept regenerations"
    )
    fold_pulls(kept or [], "kept PR", records)
    runs = _gh_json(
        ["run", "list", "--repo", repo, "--workflow", "impl-generate.yml", "--limit", LIMIT]
        + ["--json", "displayTitle,createdAt"],
        "impl-generate runs",
    )
    fold_runs(runs or [], records)
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
    parser.add_argument("--repo", required=True)
    parser.add_argument("--libraries", required=True, help="space-separated supported libraries")
    parser.add_argument("--plots", default="plots")
    args = parser.parse_args(argv)

    libraries = args.libraries.split()
    if args.count < 1 or not libraries:
        print("::error::--count must be at least 1 and --libraries must name at least one library")
        return 1

    candidates, spec_issues = load_candidates(Path(args.plots), libraries)
    records = read_records(args.repo)
    picks, eligible = pick(
        candidates, records, spec_issues, datetime.now(timezone.utc), timedelta(hours=args.min_age_hours), args.count
    )

    print(f"::notice::Eligible pairs: {eligible}  picked: {[f'{p.spec}/{p.library}' for p in picks]}")
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
