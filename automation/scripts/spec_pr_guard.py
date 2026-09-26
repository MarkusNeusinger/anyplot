#!/usr/bin/env python3
# /// script
# requires-python = ">=3.12"
# dependencies = []
# ///
"""Fail-closed file allowlist for the spec PR that `spec-create.yml` merges.

The merge job in `.github/workflows/spec-create.yml` merges a PR that Claude
opened from `specification/<spec-id>`, once the owner adds `approved` to the
issue. The owner reviews the specification text; this guard makes sure that is
ALL the PR carries. It reads the PR's diff exactly as GitHub would squash it —
`git diff --raw origin/main...<head sha>`, renames off — and accepts only:

- `plots/<spec-id>/specification.md` and `plots/<spec-id>/specification.yaml`,
- `plots/<spec-id>/implementations/.gitkeep`, `plots/<spec-id>/metadata/.gitkeep`
  and one lowercase level below them (`.../implementations/python/.gitkeep`),

each added or modified as a regular, non-executable file (mode 100644). A
deletion, a symlink, an executable bit, a submodule, any other path, or an
empty diff is a violation. Anything the guard cannot read (a git error, an
unparseable line) is an error, never a pass.

Usage (from the repository root, with `<head sha>` fetched):

    python3 automation/scripts/spec_pr_guard.py --spec-id scatter-basic --head <sha>

Exit status: 0 = the diff is clean, 1 = violations (one per line on stdout),
2 = the guard could not decide (bad input, git failure). The workflow treats
anything but 0 as a refusal.

Standard library only (Python 3.12+), so the merge job runs it with the
runner's `python3` without syncing the project's dependencies.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys


SPEC_ID_RE = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*")
ALLOWED_STATUSES = frozenset({"A", "M"})
REGULAR_FILE_MODE = "100644"
ABSENT_MODE = "000000"


class GuardError(Exception):
    """The guard could not read the diff; the caller must refuse, not pass."""


def allowed_path_re(spec_id: str) -> re.Pattern[str]:
    """The exact set of paths a spec PR may touch, for one spec id."""
    if not SPEC_ID_RE.fullmatch(spec_id):
        raise GuardError(f"invalid spec id: {spec_id!r}")
    base = re.escape(f"plots/{spec_id}/")
    return re.compile(base + r"(?:specification\.(?:md|yaml)|(?:implementations|metadata)(?:/[a-z]+)?/\.gitkeep)")


def check_raw_diff(raw: str, spec_id: str) -> list[str]:
    """Violations in a `git diff --raw -z --no-renames --no-abbrev` output; empty means clean.

    Each entry is `:<old mode> <new mode> <old sha> <new sha> <status>` followed
    by NUL, the path, NUL. With renames off there is exactly one path per entry.
    """
    allowed = allowed_path_re(spec_id)
    fields = raw.split("\0")
    if fields and fields[-1] == "":
        fields.pop()
    if len(fields) % 2:
        raise GuardError("unparseable raw diff: odd number of NUL-separated fields")

    violations: list[str] = []
    for meta, path in zip(fields[0::2], fields[1::2], strict=True):
        parts = meta.lstrip(":").split(" ")
        if not meta.startswith(":") or len(parts) != 5:
            raise GuardError(f"unparseable raw diff entry: {meta!r}")
        old_mode, new_mode, _old_sha, _new_sha, status = parts
        # Quoted and escaped, backticks included: the path lands in an issue comment.
        shown = json.dumps(path).replace("`", "\\u0060")
        if not allowed.fullmatch(path):
            violations.append(f"{shown}: outside the allowed spec files")
        elif status not in ALLOWED_STATUSES:
            violations.append(f"{shown}: status {status} (only added or modified files are allowed)")
        elif new_mode != REGULAR_FILE_MODE or old_mode not in (ABSENT_MODE, REGULAR_FILE_MODE):
            violations.append(f"{shown}: mode {old_mode} -> {new_mode} (only regular 100644 files are allowed)")
    if not fields:
        violations.append("the pull request changes no files")
    return violations


def read_raw_diff(base: str, head: str) -> str:
    """The raw diff of `head` against its merge base with `base` — what a squash merge applies."""
    try:
        result = subprocess.run(
            ["git", "diff", "--raw", "-z", "--no-renames", "--no-abbrev", f"{base}...{head}"],
            check=True,
            capture_output=True,
        )
    except (OSError, subprocess.CalledProcessError) as exc:
        stderr = getattr(exc, "stderr", b"") or b""
        raise GuardError(f"git diff failed: {stderr.decode('utf-8', 'replace').strip() or exc}") from exc
    return result.stdout.decode("utf-8", "surrogateescape")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--spec-id", required=True, help="the spec id from the issue title")
    parser.add_argument("--head", required=True, help="the PR head commit SHA (40 hex characters)")
    parser.add_argument("--base", default="origin/main", help="the ref the PR merges into (default: origin/main)")
    args = parser.parse_args(argv)

    try:
        if not re.fullmatch(r"[0-9a-f]{40}", args.head):
            raise GuardError(f"head is not a full commit SHA: {args.head!r}")
        violations = check_raw_diff(read_raw_diff(args.base, args.head), args.spec_id)
    except GuardError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    for violation in violations:
        print(violation)
    return 1 if violations else 0


if __name__ == "__main__":
    sys.exit(main())
