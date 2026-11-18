#!/usr/bin/env python3
"""Audit a branch's merge commits for content one side added and the merge dropped.

For every two-parent merge M (first parent: the branch, second parent: what was merged in) that the
given refs reach and the base does not, the merge is redone mechanically
(`git merge-tree --write-tree`) and compared with what was committed:

- A file the mechanical merge resolves without a conflict must be identical in M. If it is not, a
  side was taken wholesale or the file was edited by hand during the merge.
- In a file that did conflict, the hunks outside the conflict still merge cleanly. A line one side
  added there that M no longer has was dropped although no conflict asked for it: the mark of
  `git checkout --ours <file>` or `--theirs <file>`, which takes the whole file.
- Lines inside a conflict that M does not have are listed too, as the resolution's own choice: one
  side of a real conflict always loses lines.

Lines are compared as a set per file, so a dropped line that also stands elsewhere in the file (a
lone brace, a repeated heading) is not seen. A finding is a place to look at, not a verdict: a
merge may have to adapt a cleanly merged file to the other side's change.

Read-only: it writes loose tree objects into the object store and changes no ref, index or
worktree. Needs git 2.38 or newer.

Usage, from the branch's worktree: merge_audit.py <base-ref> [<ref> ...]   (refs default to HEAD)
Exit code: 0 nothing dropped outside a conflict, 1 something to look at, 2 usage or git error.
"""

from __future__ import annotations

import subprocess
import sys


CONFLICT_START = "<<<<<<< "
CONFLICT_END = ">>>>>>> "
SHOWN_LINES = 6


class GitError(RuntimeError):
    """A git command this audit cannot go on without failed."""


def git(*args: str, check: bool = True) -> str:
    done = subprocess.run(["git", *args], capture_output=True, text=True, errors="replace", check=False)
    if check and done.returncode != 0:
        raise GitError(f"git {' '.join(args)} failed: {done.stderr.strip()[:300]}")
    return done.stdout


def blob(tree: str, path: str) -> str | None:
    """The file's text in a tree or commit, or None when it is not there."""
    done = subprocess.run(
        ["git", "show", f"{tree}:{path}"], capture_output=True, text=True, errors="replace", check=False
    )
    return done.stdout if done.returncode == 0 else None


def added_lines(old: str, new: str, path: str) -> list[str]:
    out = git("diff", "--no-color", "-U0", old, new, "--", path, check=False)
    return [line[1:] for line in out.splitlines() if line.startswith("+") and not line.startswith("+++")]


def outside_conflicts(merged: str) -> set[str]:
    """The lines of a mechanically merged file that stand outside its conflict markers."""
    lines: set[str] = set()
    inside = False
    for line in merged.splitlines():
        if line.startswith(CONFLICT_START):
            inside = True
        elif line.startswith(CONFLICT_END):
            inside = False
        elif not inside:
            lines.add(line)
    return lines


def mechanical_merge(ours: str, theirs: str) -> tuple[str, list[str]]:
    """The tree a merge without a human gives, and the files it could not resolve."""
    done = subprocess.run(
        ["git", "merge-tree", "--write-tree", "--name-only", "--no-messages", ours, theirs],
        capture_output=True,
        text=True,
        check=False,
    )
    if done.returncode not in (0, 1) or not done.stdout.strip():
        raise GitError(f"git merge-tree failed for {ours[:9]} and {theirs[:9]}: {done.stderr.strip()[:300]}")
    lines = done.stdout.splitlines()
    return lines[0], [name for name in lines[1:] if name]


def audit(merge: str, ours: str, theirs: str) -> tuple[list[str], bool, list[str]]:
    """What to report for one merge, whether any of it is a loss outside a conflict, and its conflicts."""
    merge_base = git("merge-base", ours, theirs).split()[0]
    tree, conflicted = mechanical_merge(ours, theirs)
    report: list[str] = []
    to_look_at = False

    for path in (name for name in git("diff", "--name-only", tree, merge).split("\n") if name):
        if path in conflicted:
            continue
        to_look_at = True
        report.append(f"  CHANGED BY HAND OR A SIDE TAKEN (a mechanical merge has no conflict here): {path}")
        result = blob(merge, path)
        if result is not None and result == blob(ours, path):
            report.append("    = the branch's version, whole")
        elif result is not None and result == blob(theirs, path):
            report.append("    = the merged-in version, whole")

    for path in conflicted:
        result = blob(merge, path)
        if result is None:
            to_look_at = True
            report.append(f"  CONFLICTED AND GONE from the result: {path}")
            continue
        have = set(result.splitlines())
        clean = outside_conflicts(blob(tree, path) or "")
        for label, side in (("merged-in side", theirs), ("branch", ours)):
            lost = [line for line in added_lines(merge_base, side, path) if line.strip() and line not in have]
            dropped = [line for line in lost if line in clean]
            chosen = [line for line in lost if line not in clean]
            if dropped:
                to_look_at = True
                report.append(f"  DROPPED OUTSIDE A CONFLICT in {path}: {len(dropped)} line(s) the {label} added")
                report.extend(f"      | {line[:150]}" for line in dropped[:SHOWN_LINES])
            if chosen:
                report.append(f"  resolved against the {label} in {path}: {len(chosen)} line(s) of the conflict itself")
                report.extend(f"      | {line[:150]}" for line in chosen[:SHOWN_LINES])
    return report, to_look_at, conflicted


def main(argv: list[str]) -> int:
    if not argv or argv[0] in ("-h", "--help"):
        print(__doc__)
        return 2 if not argv else 0
    base, refs = argv[0], argv[1:] or ["HEAD"]
    try:
        merges: list[str] = []
        for ref in refs:
            for sha in git("rev-list", "--merges", ref, "--not", base).split():
                if sha not in merges:
                    merges.append(sha)
        print(f"{len(merges)} merge commit(s) to audit")
        findings = 0
        for merge in merges:
            parents = git("rev-list", "--parents", "-n", "1", merge).split()[1:]
            if len(parents) != 2:
                continue
            ours, theirs = parents
            report, to_look_at, conflicted = audit(merge, ours, theirs)
            subject = git("log", "-1", "--format=%h %cd %s", "--date=format:%m-%d %H:%M", merge).strip()
            print(f"\n{subject}")
            print(
                f"  parents {ours[:9]} + {theirs[:9]}, {len(conflicted)} conflicted file(s): {', '.join(conflicted) or '-'}"
            )
            print("\n".join(report) if report else "  nothing lost")
            findings += to_look_at
    except GitError as error:
        print(error, file=sys.stderr)
        return 2
    print(f"\n{findings} merge(s) with something to look at")
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
