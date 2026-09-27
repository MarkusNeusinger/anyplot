#!/usr/bin/env python3
"""Close a spec issue once every supported library is done or failed.

Shared by ``impl-merge.yml`` (after a merge) and ``impl-review.yml`` (after a
regen was kept: the live implementation stays, so the library counts as done
again). Stdlib-only apart from ``gh`` on PATH; the library list comes from the
caller (``core.constants.SUPPORTED_LIBRARIES``) so this file never carries its
own copy that could drift.

Usage::

    python3 close_issue_if_complete.py --issue 123 --spec-id scatter-basic \
        --libraries "altair bokeh ..." --run-url https://github.com/.../actions/runs/1 --source impl-merge
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from dataclasses import dataclass, field


@dataclass
class Completion:
    done: list[str] = field(default_factory=list)
    failed: list[str] = field(default_factory=list)
    total: int = 0

    @property
    def complete(self) -> bool:
        return self.total > 0 and len(self.done) + len(self.failed) == self.total


def completion_status(labels: list[str], libraries: list[str]) -> Completion:
    """Count ``impl:<lib>:done`` / ``impl:<lib>:failed`` labels. Done wins over failed."""
    present = set(labels)
    status = Completion(total=len(libraries))
    for lib in sorted(libraries):
        if f"impl:{lib}:done" in present:
            status.done.append(lib)
        elif f"impl:{lib}:failed" in present:
            status.failed.append(lib)
    return status


def completion_comment(status: Completion, spec_id: str, run_url: str, source: str) -> str:
    rows = ["| Library | Status |", "|---------|--------|"]
    for lib in sorted(status.done + status.failed):
        rows.append(f"| {lib} | {':white_check_mark:' if lib in status.done else ':x: (not supported)'} |")
    if not status.failed:
        title = ":tada: All Implementations Complete!"
        summary = f"All {status.total} library implementations for `{spec_id}` have been successfully merged."
    else:
        title = ":white_check_mark: Implementations Complete"
        summary = (
            f"{len(status.done)}/{status.total} implementations merged, "
            f"{len(status.failed)} libraries could not implement this plot type."
        )
    return f"## {title}\n\n{summary}\n\n" + "\n".join(rows) + f"\n\n---\n:robot: *[{source}]({run_url})*"


def _gh(*args: str) -> str:
    return subprocess.run(["gh", *args], check=True, capture_output=True, text=True).stdout


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0] if __doc__ else None)
    parser.add_argument("--issue", required=True)
    parser.add_argument("--spec-id", required=True)
    parser.add_argument("--libraries", required=True, help="space-separated supported libraries")
    parser.add_argument("--run-url", required=True)
    parser.add_argument("--source", default="impl-merge")
    args = parser.parse_args(argv)

    libraries = args.libraries.split()
    if not libraries:
        print("::error::No supported libraries given", file=sys.stderr)
        return 1

    # A failed read is not fatal: the issue simply stays open (the next merge
    # re-checks), and the caller's later steps (the Postgres sync) must not be
    # skipped because of it.
    try:
        raw = _gh("issue", "view", args.issue, "--json", "labels")
        labels = [label["name"] for label in json.loads(raw)["labels"]]
    except (subprocess.CalledProcessError, ValueError, KeyError, TypeError) as exc:
        print(f"::warning::Could not read labels of issue #{args.issue}: {' '.join(str(exc).split())[:300]}")
        return 0
    status = completion_status(labels, libraries)
    print(
        f"::notice::Libraries: {len(status.done)} done, {len(status.failed)} failed, "
        f"{len(status.done) + len(status.failed)}/{status.total} total"
    )
    if not status.complete:
        return 0

    try:
        _gh("issue", "comment", args.issue, "--body", completion_comment(status, args.spec_id, args.run_url, args.source))
        _gh("issue", "close", args.issue)
    except subprocess.CalledProcessError as exc:
        err = " ".join((exc.stderr or "").split())[:300]
        print(f"::warning::Could not comment on / close issue #{args.issue}: {err}")
        return 0
    print(
        f"::notice::Closed issue #{args.issue} - all implementations complete "
        f"({len(status.done)} done, {len(status.failed)} failed)"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
