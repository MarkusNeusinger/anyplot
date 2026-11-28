#!/usr/bin/env python3
"""Fail-closed check that an implementation pull request changes only its pair's two files.

impl-generate, impl-repair and impl-review write exactly two files on a branch
``implementation/<spec-id>/<library>``: the pair's implementation and its
metadata. Anything else the head adds or changes would sit in the review job's
workspace once it checks the head out, where a later step could pick it up. So
impl-review runs this before that checkout, from the workflow's own ref, and
stops on anything else.

The head passes when every path ``git diff --no-renames --raw BASE...HEAD``
lists is one of

- ``plots/<spec-id>/implementations/<language>/<library><ext>``, with the
  extension impl-review derives from the library,
- ``plots/<spec-id>/metadata/<language>/<library>.yaml``,

added or modified as a regular file (mode ``100644``). A deletion, a symlink,
an executable file, a submodule or any other path refuses.

Usage::

    pr_tree_check.py --base origin/main --head SHA --spec-id S --language L --library B --ext .py

Exit 0 when the head passes, 1 with one ``::error::`` line naming what refuses
it, 2 on a usage error or when git cannot compare the two (fail closed: the
caller stops either way). Stdlib only, a single file.
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys


SPEC_ID_RE = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*")
NAME_RE = re.compile(r"[a-z0-9]+")
EXT_RE = re.compile(r"\.[A-Za-z]+")
REGULAR = "100644"


def pair_files(spec_id: str, language: str, library: str, ext: str) -> frozenset[str]:
    """The pair's implementation and metadata file, the only paths its pull request may change."""
    return frozenset(
        {
            f"plots/{spec_id}/implementations/{language}/{library}{ext}",
            f"plots/{spec_id}/metadata/{language}/{library}.yaml",
        }
    )


def changes(base: str, head: str) -> list[tuple[str, str, str]]:
    """``(new mode, status, path)`` of every entry the head changes against the merge base."""
    out = subprocess.run(
        ["git", "diff", "--no-renames", "--raw", "-z", f"{base}...{head}"], capture_output=True, check=True
    ).stdout.decode("utf-8", "surrogateescape")
    fields = out.split("\0")
    entries = []
    for meta, path in zip(fields[0::2], fields[1::2], strict=False):
        if not meta:
            continue
        # ":<old mode> <new mode> <old sha> <new sha> <status>"
        parts = meta.lstrip(":").split()
        entries.append((parts[1], parts[4], path))
    return entries


def problems(entries: list[tuple[str, str, str]], allowed: frozenset[str]) -> list[str]:
    """What refuses the head, one item per path; empty when it passes."""
    found = []
    for mode, status, path in entries:
        if path not in allowed:
            found.append(f"{path} (not this pair's implementation or metadata)")
        elif status not in ("A", "M") or mode != REGULAR:
            found.append(f"{path} (status {status}, mode {mode})")
    return found


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0] if __doc__ else None)
    parser.add_argument("--base", required=True)
    parser.add_argument("--head", required=True)
    parser.add_argument("--spec-id", required=True)
    parser.add_argument("--language", required=True)
    parser.add_argument("--library", required=True)
    parser.add_argument("--ext", required=True, help="the implementation's extension, with its dot")
    args = parser.parse_args(argv)
    if not SPEC_ID_RE.fullmatch(args.spec_id) or not NAME_RE.fullmatch(args.language):
        print(f"::error::pr_tree_check: malformed spec id or language ({args.spec_id!r}, {args.language!r})")
        return 2
    if not NAME_RE.fullmatch(args.library) or not EXT_RE.fullmatch(args.ext):
        print(f"::error::pr_tree_check: malformed library or extension ({args.library!r}, {args.ext!r})")
        return 2
    try:
        entries = changes(args.base, args.head)
    except (subprocess.CalledProcessError, OSError, IndexError) as error:
        print(f"::error::pr_tree_check: git could not compare {args.base} and {args.head} ({type(error).__name__})")
        return 2
    found = problems(entries, pair_files(args.spec_id, args.language, args.library, args.ext))
    if found:
        listed = "; ".join(found[:10]) + (f"; and {len(found) - 10} more" if len(found) > 10 else "")
        print(f"::error::the pull request head changes more than its pair's two files: {listed}")
        return 1
    print(f"::notice::pr_tree_check: {len(entries)} file(s), all the pair's own")
    return 0


if __name__ == "__main__":
    sys.exit(main())
