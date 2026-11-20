#!/usr/bin/env python3
# /// script
# requires-python = ">=3.12"
# dependencies = []
# ///
"""Fail-closed check that a pull request is one of the plot pipeline's own.

The pipeline's privileged workflows (impl-review, impl-repair, impl-merge,
impl-review-retry, the watchdog, impl-generate's lookup of an existing PR and
daily-regen's pair pick) hold a write token, cloud credentials and a model
credential, and act only on a pull request that is the pipeline's own. That is
one whose fields from `gh pr view --json` (or one entry of `gh pr list --json`)
show all of:

- its head branch lives in this repository: `isCrossRepository` is `false`, and
  `headRepositoryOwner.login` / `headRepository.name` name the repository the
  workflow runs in (compared without case, as GitHub compares them);
- its head branch is `implementation/<spec-id>/<library>`, where the spec id is
  lowercase letters and digits in hyphen-separated groups (the catalogue's
  shape, `spec_pr_guard.SPEC_ID_RE`) and the library is one of the caller's
  list, `core.constants.SUPPORTED_LIBRARIES`;
- its head commit is a full 40-character SHA;
- its number is the one the workflow was asked about (`check --number`), and
  the spec id and library are the ones it was dispatched with, when it was
  dispatched with any (`check --spec-id/--library`).

A missing or null field, or one of the wrong type, refuses the pull request,
like any other mismatch: nothing is assumed.

Usage (the workflows run a copy staged from their own commit, see
`docs/workflows/overview.md#pull-requests-the-pipeline-acts-on`):

    python3 pr_guard.py check --repo OWNER/NAME --libraries "altair bokeh ..." \\
        --number 123 [--spec-id SPEC --library LIB] < pr.json
    python3 pr_guard.py filter --repo OWNER/NAME --libraries "altair bokeh ..." \\
        < prs.json > own.json

`check` exits 0 and prints `number=`, `spec_id=`, `library=`, `branch=` and
`head_sha=` lines, every value checked, so a workflow can append them to
`$GITHUB_OUTPUT`; or exits 1 and prints one `reason=<code>` line, a code from
`REASONS`; or exits 2 when it cannot run at all (bad arguments). `filter` reads
a JSON array, prints the entries that pass as a JSON array, writes one line per
skipped entry to stderr, and exits 2 when its input is not a JSON array. A
caller treats any exit status but 0 as a refusal.

Standard library only, and Python 3.12 syntax, so a job runs it with the
runner's own `python3` before it sets up anything else.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from typing import Any


# The catalogue's spec id shape; equal to spec_pr_guard.SPEC_ID_RE (a test
# keeps the two in step), duplicated because the workflows stage this file alone.
SPEC_ID_PATTERN = r"[a-z0-9]+(?:-[a-z0-9]+)*"
LIBRARY_PATTERN = r"[a-z0-9]+"
BRANCH_RE = re.compile(rf"implementation/(?P<spec>{SPEC_ID_PATTERN})/(?P<library>{LIBRARY_PATTERN})")
HEAD_SHA_RE = re.compile(r"[0-9a-f]{40}")
NUMBER_RE = re.compile(r"[1-9][0-9]{0,9}")
# GitHub's own limits: owner 39 characters of letters, digits and hyphens; a
# repository name 100 of letters, digits, hyphens, dots and underscores.
REPO_RE = re.compile(r"(?P<owner>[A-Za-z0-9-]{1,39})/(?P<name>[A-Za-z0-9._-]{1,100})")
LIBRARY_RE = re.compile(LIBRARY_PATTERN)
# A branch name far longer than any spec id is not worth matching.
MAX_BRANCH = 200

# Every reason a pull request is refused, the workflows' own included. A code
# is a fixed word, so it can go into a log line or a job summary as it is.
REASONS: dict[str, str] = {
    # The checker's.
    "unreadable": "the pull request data is not a JSON object",
    "missing_field": "a required field is missing, null or of the wrong type",
    "bad_number": "the pull request number is not a positive integer",
    "number_mismatch": "the data is for another pull request than the one asked for",
    "cross_repository": "the head branch lives in another repository",
    "branch_shape": "the head branch is not implementation/<spec-id>/<library>",
    "unknown_library": "the library in the head branch is not a registered library",
    "head_sha_shape": "the head commit is not a full commit SHA",
    "input_mismatch": "the spec id or library differs from the one the workflow was dispatched with",
    # The workflows'.
    "pr_unreadable": "the pull request could not be read from GitHub",
    "guard_failed": "the guard could not be staged or did not run to an answer",
}
REQUIRED_FIELDS = ("number", "headRefName", "headRefOid", "isCrossRepository", "headRepository", "headRepositoryOwner")


@dataclass(frozen=True)
class Verdict:
    """The answer for one pull request: `reason` is None when it is the pipeline's own."""

    reason: str | None
    number: int | None = None
    spec_id: str = ""
    library: str = ""
    branch: str = ""
    head_sha: str = ""

    @property
    def allowed(self) -> bool:
        return self.reason is None


def _refuse(reason: str, number: int | None = None) -> Verdict:
    assert reason in REASONS, reason
    return Verdict(reason, number)


def _string_field(data: Mapping[str, Any], *path: str) -> str | None:
    value: Any = data
    for key in path:
        if not isinstance(value, Mapping):
            return None
        value = value.get(key)
    return value if isinstance(value, str) else None


def check(
    data: Any,
    *,
    repo: str,
    libraries: Iterable[str],
    number: int | None = None,
    spec_id: str | None = None,
    library: str | None = None,
) -> Verdict:
    """Whether `data` (one pull request as `gh` prints it) is the pipeline's own."""
    if not isinstance(data, Mapping):
        return _refuse("unreadable")
    pr_number = data.get("number")
    # bool is an int subclass; JSON `true` is no pull request number.
    if not isinstance(pr_number, int) or isinstance(pr_number, bool) or pr_number < 1:
        return _refuse("missing_field")
    if any(data.get(name) is None for name in REQUIRED_FIELDS):
        return _refuse("missing_field", pr_number)
    branch = data.get("headRefName")
    head_sha = data.get("headRefOid")
    owner = _string_field(data, "headRepositoryOwner", "login")
    name = _string_field(data, "headRepository", "name")
    if not isinstance(branch, str) or not isinstance(head_sha, str) or owner is None or name is None:
        return _refuse("missing_field", pr_number)
    if not isinstance(data.get("isCrossRepository"), bool):
        return _refuse("missing_field", pr_number)
    if number is not None and pr_number != number:
        return _refuse("number_mismatch", pr_number)

    want = REPO_RE.fullmatch(repo)
    if (
        data["isCrossRepository"] is not False
        or want is None
        or owner.lower() != want["owner"].lower()
        or name.lower() != want["name"].lower()
    ):
        return _refuse("cross_repository", pr_number)

    match = BRANCH_RE.fullmatch(branch) if len(branch) <= MAX_BRANCH else None
    if match is None:
        return _refuse("branch_shape", pr_number)
    if match["library"] not in set(libraries):
        return _refuse("unknown_library", pr_number)
    if not HEAD_SHA_RE.fullmatch(head_sha):
        return _refuse("head_sha_shape", pr_number)
    if (spec_id is not None and spec_id != match["spec"]) or (library is not None and library != match["library"]):
        return _refuse("input_mismatch", pr_number)
    return Verdict(None, pr_number, match["spec"], match["library"], branch, head_sha)


def own_pull_requests(
    entries: Iterable[Any], *, repo: str, libraries: Iterable[str]
) -> tuple[list[Any], list[Verdict]]:
    """The entries of a listing that are the pipeline's own, and the verdicts of the rest."""
    libraries = frozenset(libraries)
    kept: list[Any] = []
    skipped: list[Verdict] = []
    for entry in entries:
        verdict = check(entry, repo=repo, libraries=libraries)
        if verdict.allowed:
            kept.append(entry)
        else:
            skipped.append(verdict)
    return kept, skipped


def _libraries(raw: str) -> frozenset[str] | None:
    names = raw.split()
    if not names or not all(LIBRARY_RE.fullmatch(name) for name in names):
        return None
    return frozenset(names)


def _shown(number: int | None) -> str:
    return str(number) if number is not None else "?"


def _run_check(args: argparse.Namespace, libraries: frozenset[str]) -> int:
    if args.number is None or not NUMBER_RE.fullmatch(args.number):
        print("reason=bad_number")
        return 1
    try:
        data = json.loads(sys.stdin.read())
    except ValueError:
        print("reason=unreadable")
        return 1
    verdict = check(
        data, repo=args.repo, libraries=libraries, number=int(args.number), spec_id=args.spec_id, library=args.library
    )
    if not verdict.allowed:
        print(f"reason={verdict.reason}")
        return 1
    print(f"number={verdict.number}")
    print(f"spec_id={verdict.spec_id}")
    print(f"library={verdict.library}")
    print(f"branch={verdict.branch}")
    print(f"head_sha={verdict.head_sha}")
    return 0


def _run_filter(args: argparse.Namespace, libraries: frozenset[str]) -> int:
    try:
        entries = json.loads(sys.stdin.read())
    except ValueError:
        print("error: the listing is not JSON", file=sys.stderr)
        return 2
    if not isinstance(entries, list):
        print("error: the listing is not a JSON array", file=sys.stderr)
        return 2
    kept, skipped = own_pull_requests(entries, repo=args.repo, libraries=libraries)
    for verdict in skipped:
        print(
            f"PR #{_shown(verdict.number)}: skipped ({verdict.reason}), not one of the pipeline's own pull requests",
            file=sys.stderr,
        )
    print(json.dumps(kept, separators=(",", ":")))
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0] if __doc__ else None)
    parser.add_argument("mode", choices=("check", "filter"))
    parser.add_argument("--repo", required=True, help="OWNER/NAME of the repository the workflow runs in")
    parser.add_argument("--libraries", required=True, help="space-separated registered libraries")
    parser.add_argument("--number", help="check: the pull request number the workflow was asked about")
    parser.add_argument("--spec-id", help="check: the spec id the workflow was dispatched with, if any")
    parser.add_argument("--library", help="check: the library the workflow was dispatched with, if any")
    args = parser.parse_args(argv)

    libraries = _libraries(args.libraries)
    if libraries is None or not REPO_RE.fullmatch(args.repo):
        print("error: --libraries must name at least one library and --repo must be OWNER/NAME", file=sys.stderr)
        if args.mode == "check":
            print("reason=guard_failed")
        return 2
    if args.mode == "check":
        return _run_check(args, libraries)
    return _run_filter(args, libraries)


if __name__ == "__main__":
    sys.exit(main())
