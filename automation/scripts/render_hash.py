"""Tie the staged renders to the code that made them (rule P2a, warn-only).

Every render path stages ``render.sha256`` beside the PNGs it uploads:
``impl-generate.yml`` (a generated or an adopted file) and ``impl-repair.yml``.
``impl-review.yml`` compares it with the implementation at the PR head and
warns on a mismatch or a missing hash; it never changes the review or its
score.

The hash covers the implementation with its header score reset to
``Quality: pending`` (``regen_gate.reset_header_score``, what
``regen_gate.py sanitize-source --pending`` writes). That is the form the
file is committed in after a generation, and the form the reviewer reads, so
the generator's own ``Quality: N/100`` and impl-generate's reset never change
it. impl-review's header commit lands after its comparison and before any
repair renders, so it never sits between a render and the head it is checked
against. The name is not ``plot-*``: review and merge copy exactly those
objects, and the hash must never reach production.

Subcommands::

    render_hash.py write --source IMPL --out render.sha256

    render_hash.py check --hash render.sha256 --source IMPL_AT_HEAD --head SHA \
        [--fetch-error TEXT] [--run-url URL] [--comment-out FILE]

``write`` writes ``<sha256>  <source>`` (the ``sha256sum`` format). ``check``
writes ``status=match|mismatch|missing|unreadable`` to ``$GITHUB_OUTPUT`` and
one line to ``$GITHUB_STEP_SUMMARY`` when they are set, prints a
``::notice::`` or ``::warning::``, and on anything but a match writes the PR
comment to ``--comment-out``. It always exits 0 (2 on a usage error).
Stdlib only; ``regen_gate`` is imported from this file's own directory when
it runs as a script, so a workflow's copy never reads the checkout's.
"""

from __future__ import annotations

import argparse
import hashlib
import os
import re
import sys
from pathlib import Path


if __package__:  # imported as automation.scripts.render_hash (tests, local tools)
    from automation.scripts import regen_gate
else:  # run as a script: the regen_gate.py next to this file (the workflow-ref copy)
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import regen_gate


HASH_RE = re.compile(r"[0-9a-f]{64}")
MARKER = "<!-- render-hash:v1 status={status} head={head} -->"


def render_hash(data: bytes) -> str:
    """sha256 of the source with its header score reset to pending; every other byte counts."""
    text = data.decode("utf-8", errors="surrogateescape")
    blind = regen_gate.reset_header_score(text)
    return hashlib.sha256(blind.encode("utf-8", errors="surrogateescape")).hexdigest()


def read_hash(path: Path) -> str | None:
    """The hash in a ``render.sha256`` file, or None when its first field is not one."""
    fields = path.read_text(encoding="utf-8", errors="replace").split()
    return fields[0] if fields and HASH_RE.fullmatch(fields[0]) else None


def compare(hash_file: Path, source: Path, fetch_error: str = "") -> tuple[str, str, str, str]:
    """(status, staged hash, head hash, reason): the four statuses ``check`` reports."""
    head = render_hash(source.read_bytes()) if source.is_file() else ""
    if fetch_error:
        return "unreadable", "", head, f"staging could not be read ({regen_gate._one_line(fetch_error)[:200]})"
    if not hash_file.is_file():
        return "missing", "", head, "no render.sha256 in staging"
    staged = read_hash(hash_file)
    if staged is None:
        return "unreadable", "", head, "render.sha256 holds no sha256"
    if not head:
        return "unreadable", staged, "", "the implementation at the head could not be read"
    return ("match" if staged == head else "mismatch"), staged, head, ""


def comment(status: str, staged: str, head_hash: str, reason: str, head: str, run_url: str) -> str:
    """The PR comment for every status but a match."""
    short = head[:7] or "the head"
    title = "Staged renders not checked against this code"
    if status == "mismatch":
        title = "Staged renders do not match this code"
        what = (
            f"`render.sha256` beside the staged renders is `{staged[:12]}`, but the implementation at "
            f"`{short}` hashes to `{head_hash[:12]}`: the renders under review were made from other code."
        )
    elif status == "missing":
        what = (
            "The staged renders carry no `render.sha256`, so this review cannot tell whether they come "
            f"from the implementation at `{short}`. Renders staged before the hash existed have none."
        )
    else:
        what = f"The render hash could not be checked: {reason}."
    lines = [
        MARKER.format(status=status, head=head or "n/a"),
        f"## :warning: {title}",
        "",
        what,
        "",
        "This check only warns: the review and its score go ahead unchanged. Every render path stages "
        "the sha256 of the implementation it rendered, with its `Quality:` header reset to `pending`, "
        "as `render.sha256` (`automation/scripts/render_hash.py`).",
    ]
    if run_url:
        lines += ["", "---", f":robot: *[impl-review]({run_url})*"]
    return "\n".join(lines) + "\n"


def _append(env_var: str, text: str) -> None:
    target = os.environ.get(env_var)
    if target:
        with open(target, "a", encoding="utf-8") as handle:
            handle.write(text)


def cmd_write(args: argparse.Namespace) -> int:
    digest = render_hash(Path(args.source).read_bytes())
    Path(args.out).write_text(f"{digest}  {args.source}\n", encoding="utf-8")
    print(f"::notice::render_hash sha256={digest[:12]} source={args.source}")
    return 0


def cmd_check(args: argparse.Namespace) -> int:
    status, staged, head_hash, reason = compare(Path(args.hash), Path(args.source), args.fetch_error)
    short = args.head[:7] or "n/a"
    if status == "match":
        print(f"::notice::render_hash status=match sha256={staged[:12]} head={short}")
        summary = f"**Render hash:** match: the staged renders come from the implementation at `{short}`."
    else:
        detail = reason or f"staged {staged[:12]}, head {head_hash[:12]}"
        print(f"::warning::render_hash status={status} head={short}: {detail}")
        summary = f"**Render hash:** {status} at `{short}` ({detail}); warn-only, the score is unchanged."
        if args.comment_out:
            Path(args.comment_out).write_text(
                comment(status, staged, head_hash, reason, args.head, args.run_url), encoding="utf-8"
            )
    _append("GITHUB_OUTPUT", f"status={status}\n")
    _append("GITHUB_STEP_SUMMARY", f"\n{summary}\n")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0] if __doc__ else None)
    sub = parser.add_subparsers(dest="command", required=True)

    write = sub.add_parser("write", help="Write render.sha256 for the implementation the renders came from")
    write.add_argument("--source", required=True)
    write.add_argument("--out", required=True)
    write.set_defaults(func=cmd_write)

    check = sub.add_parser("check", help="Compare the staged render.sha256 with the implementation at the head")
    check.add_argument("--hash", required=True, help="the downloaded render.sha256 (absent: missing)")
    check.add_argument("--source", required=True, help="the implementation at the head (absent: unreadable)")
    check.add_argument("--head", default="")
    check.add_argument("--fetch-error", default="", help="the download's error, other than a missing object")
    check.add_argument("--run-url", default="")
    check.add_argument("--comment-out", default="")
    check.set_defaults(func=cmd_check)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
