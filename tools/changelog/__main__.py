"""`python -m tools.changelog` — check fragments, preview the pending section, cut a release.

    uv run python -m tools.changelog check                      # every fragment well-formed
    uv run python -m tools.changelog check --base origin/main   # …and this branch carries one (the CI gate)
    uv run python -m tools.changelog preview                    # [Unreleased] as the next cut would write it
    uv run python -m tools.changelog release 3.3.0 --title "…" [--date YYYY-MM-DD] [--dry-run]

`release` rewrites CHANGELOG.md — the section, its heading and the compare links
at the bottom — bumps pyproject.toml, uv.lock and app/package.json and deletes
the fragments, in the working tree only. What it deliberately leaves to
`agentic/commands/release.md`: the two aggregate lines (the italic *Catalog*
line and the single **Dependencies:** bullet, which summarize the window rather
than any PR), the release branch and PR, the tag on the merge commit, and the
condensed GitHub release. Nothing here touches a remote, a database or a
deployment.
"""

from __future__ import annotations

import argparse
import os
import sys
from datetime import date

from tools.changelog import (
    CHANGELOG_NAME,
    REPO_ROOT,
    ChangelogError,
    apply_release,
    check_pr,
    load_fragments,
    plan_release,
    render,
    unreleased,
)


def _fail(message: str) -> int:
    # GitHub turns the `::error::` line into an annotation on the PR's checks tab.
    prefix = "::error::" if os.environ.get("GITHUB_ACTIONS") else "error: "
    print(f"{prefix}{message}", file=sys.stderr)
    return 1


def cmd_check(args: argparse.Namespace) -> int:
    fragments = load_fragments()
    print(
        f"{len(fragments)} fragment(s) well-formed"
        + (": " + ", ".join(f.path.name for f in fragments) if fragments else "")
    )
    unreleased()  # the section in the file parses too — a malformed seam would break the next cut
    if args.base:
        problems = check_pr(args.base)
        if problems:
            for problem in problems:
                _fail(problem)
            return 1
        print(f"the diff against {args.base} passes the fragment rule")
    return 0


def cmd_preview(args: argparse.Namespace) -> int:
    entries = unreleased()
    if not entries:
        print("(nothing pending: no fragments, [Unreleased] empty)")
        return 0
    print(render(entries), end="")
    return 0


def cmd_release(args: argparse.Namespace) -> int:
    release = plan_release(version=args.version, date=args.date, title=args.title)
    verb = "would write" if args.dry_run else "wrote"
    for path in release.writes:
        print(f"{verb} {path.relative_to(REPO_ROOT)}")
    for path in release.deletes:
        print(f"{'would delete' if args.dry_run else 'deleted'} {path.relative_to(REPO_ROOT)}")
    if args.dry_run:
        text = release.writes[REPO_ROOT / CHANGELOG_NAME]
        start = text.index(f"## [{args.version}]")
        end = text.find("\n## [", start + 1)
        print("\n" + text[start : end if end > 0 else len(text)].rstrip() + "\n")
        return 0
    apply_release(release)
    print(
        f"\nnext: add the window's aggregate lines by hand (the italic *Catalog* line and the\n"
        f"single **Dependencies:** bullet — agentic/commands/release.md step 2), review the diff,\n"
        f"then on a release/v{args.version} branch\n"
        f"  git add -A CHANGELOG.md changelog.d pyproject.toml uv.lock app/package.json\n"
        f'  git commit -m "release: v{args.version} — {args.title}"\n'
        f"after the merge: tag the merge commit v{args.version}, then post the condensed GitHub release."
    )
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m tools.changelog", description=__doc__.split("\n\n")[0])
    sub = parser.add_subparsers(dest="verb", required=True)

    check = sub.add_parser("check", help="every fragment parses; with --base, the branch carries one")
    check.add_argument("--base", help="git ref of the PR base (CI: origin/<base branch>)")
    check.set_defaults(run=cmd_check)

    preview = sub.add_parser("preview", help="print [Unreleased] as the next cut would write it")
    preview.set_defaults(run=cmd_preview)

    release = sub.add_parser("release", help="cut a release: fold the fragments, bump the version files")
    release.add_argument("version", help="MAJOR.MINOR.PATCH, above the newest section")
    release.add_argument("--title", required=True, help="the heading's title after the date")
    release.add_argument("--date", default=date.today().isoformat(), help="YYYY-MM-DD (default: today)")
    release.add_argument("--dry-run", action="store_true", help="print the plan and the new section, write nothing")
    release.set_defaults(run=cmd_release)

    args = parser.parse_args(argv)
    try:
        return args.run(args)
    except ChangelogError as e:
        return _fail(str(e))


if __name__ == "__main__":
    sys.exit(main())
