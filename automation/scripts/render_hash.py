"""Tie the staged renders to the code that made them (rules P2a and P2b).

Every render path stages ``render.sha256`` beside the PNGs it uploads:
``impl-generate.yml`` (a generated or an adopted file) and ``impl-repair.yml``.
``impl-review.yml`` compares it with the implementation at the PR head. Only
a match lets the review run. Anything else stops it: nothing is scored and no
header is committed.

The file holds two hashes of the implementation the renders came from:

- The *render hash*: the file with its header score reset to
  ``Quality: pending`` (``regen_gate.reset_header_score``, what
  ``regen_gate.py sanitize-source --pending`` writes). That is the form the
  file is committed in after a generation, and the form the reviewer reads, so
  the generator's own ``Quality: N/100`` and impl-generate's reset never change
  it.
- The *code hash*: the file without its header, with the score reset as well.
  impl-review's "Update metadata and implementation header" step rewrites the
  whole header when it stores a review (title, library line, date, score), so
  after that commit the render hash of the head is another one although no
  line of code changed. The code hash leaves out exactly what that writer
  replaces (``strip_header``), so a re-review of the same code still matches.
  A JavaScript file's ``//#`` directives are not header: the render harness
  reads them, and they count.

``check`` reports a match when either hash fits, and otherwise why the renders
are not tied to this code (``cause``):

- ``mismatch``: neither hash fits, so the renders were made from other code.
  That holds for a one-line file as well. The writer has written two lines
  since the code hash exists, so a one-line file is left from an older run.
- ``missing``: staging holds no ``render.sha256``. The writers put it there
  last and fail their run when they cannot, so renders without one are not
  this run's.
- ``content``: the file holds no sha256.
- ``head``: the implementation at the PR head could not be read.
- ``fetch``: the file could not be downloaded, which is a failure of the
  storage and not a property of the renders.

Every cause stops the review (``stop=true``). ``fetch`` also writes
``retry=true``: the same review may well pass an hour later, so impl-review
ends it as a failed review that the watchdog starts again, where the other
causes park the PR. On a gated regeneration every cause is a keep, with the
code in ``code``: ``render_mismatch`` for a mismatch and ``render_unverified``
for the rest.

The name is not ``plot-*``: review and merge copy exactly those objects, and
the hash must never reach production.

Subcommands::

    render_hash.py write --source IMPL --language LANGUAGE --out render.sha256

    render_hash.py check --hash render.sha256 --source IMPL_AT_HEAD --language LANGUAGE --head SHA \
        [--fetch-error TEXT] [--run-url URL] [--comment-out FILE] \
        [--regeneration] [--spec-id S --library B]

``write`` writes ``<render hash>  <source>`` (the ``sha256sum`` format) and
``<code hash>  code``. ``check`` writes
``status=match|mismatch|missing|unreadable``, ``stop=true|false``, ``cause``,
``retry=true|false`` and ``code`` to ``$GITHUB_OUTPUT`` and one line to
``$GITHUB_STEP_SUMMARY`` when they are set, prints a ``::notice::`` or
``::warning::``, and on anything but a match writes the PR comment to
``--comment-out``. It exits 0 whatever the status (2 on a usage error); a
crash exits 1, and the step that runs it then lets the review go on without a
stop.
Stdlib only; ``regen_gate`` and, for JavaScript, ``impl_header`` are imported
from this file's own directory when it runs as a script, so a workflow's copy
never reads the checkout's.
"""

from __future__ import annotations

import argparse
import hashlib
import os
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from types import ModuleType


if __package__:  # imported as automation.scripts.render_hash (tests, local tools)
    from automation.scripts import regen_gate
else:  # run as a script: the regen_gate.py next to this file (the workflow-ref copy)
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import regen_gate


HASH_RE = re.compile(r"[0-9a-f]{64}")
# One comment per status, cause and head (impl-review dedupes on this line).
MARKER = "<!-- render-hash:v2 status={status} cause={cause} head={head} -->"
LANGUAGES = ("python", "r", "julia", "javascript")
# The name field of the second line of render.sha256.
CODE_NAME = "code"
# What a staged file holds: both hashes, or the render hash alone (staged
# before the code hash existed).
FORM_CODE = "two-line"
FORM_LEGACY = "legacy"
# Why the renders are not tied to the code at the head (Comparison.cause).
CAUSE_MISMATCH = "mismatch"
CAUSE_MISSING = "missing"
CAUSE_CONTENT = "content"
CAUSE_HEAD = "head"
CAUSE_FETCH = "fetch"
# The label of a first generation whose review stopped on the render hash
# (impl-review.yml "Stop on the render hash"; the watchdog skips it).
STOP_LABEL = "ai-render-unverified"
# The label of a review that failed and that the watchdog starts again once:
# what a first generation gets when the hash could not be downloaded.
RETRY_LABEL = "ai-review-failed"
# The regen gate's keep codes for a regeneration whose review stopped: the
# renders were made from other code, or nothing ties them to this code.
KEEP_CODE = "render_mismatch"
UNVERIFIED_CODE = "render_unverified"

# The header block impl-review's writer replaces at the start of a file, per
# language: the patterns of "Update metadata and implementation header" in
# impl-review.yml. JavaScript's writer is impl_header.replace_js_header.
_HEADER_RES = {
    "python": re.compile(r'""".*?"""', re.DOTALL),
    "r": re.compile(r"(?:#'[^\n]*\n)+"),
    "julia": re.compile(r"(?:#(?:[ \t][^\n]*|)\n)+"),
}


def render_hash(data: bytes) -> str:
    """sha256 of the source with its header score reset to pending; every other byte counts."""
    text = data.decode("utf-8", errors="surrogateescape")
    blind = regen_gate.reset_header_score(text)
    return hashlib.sha256(blind.encode("utf-8", errors="surrogateescape")).hexdigest()


def _impl_header() -> ModuleType:
    """impl_header, imported only for JavaScript so the other languages never depend on it."""
    if __package__:
        from automation.scripts import impl_header
    else:
        import impl_header
    return impl_header


def strip_header(text: str, language: str) -> str:
    """The source without the header block impl-review's writer replaces.

    The writer and this function read the same block, so the result is the
    same before and after a header commit. For JavaScript that is the writer
    itself with an empty header: the directives and the code stay, in the
    order the writer leaves them in.
    """
    if language == "javascript":
        return _impl_header().replace_js_header(text, "")[1:]
    match = _HEADER_RES[language].match(text)
    return text[match.end() :] if match else text


def _trim_blank_lines(text: str) -> str:
    """``text`` without the whitespace-only lines at its start and its end; every other character stays."""
    lines = text.split("\n")
    start, end = 0, len(lines)
    while start < end and not lines[start].strip():
        start += 1
    while end > start and not lines[end - 1].strip():
        end -= 1
    return "\n".join(lines[start:end])


def code_hash(data: bytes, language: str) -> str:
    """sha256 of the source without its header; the score, line endings and blank lines around the code do not count.

    The writer reads the file in text mode and writes ``\\n``, and it puts a
    line break after a header it has to prepend, so neither may change the
    hash of unchanged code. Only whole blank lines are dropped: the
    indentation of the first line of code and the spaces at the end of the
    last one are code, and the writer never touches them.

    The score is reset first, as for the render hash. impl-generate stages the
    hash of the file as the generator left it and commits the file with
    ``Quality: N/100`` reset to ``pending``. A score line outside the block
    ``strip_header`` removes (a file that starts with a shebang or a coding
    line, a header in another comment style) would otherwise count with its
    number on one side and as ``pending`` on the other.
    """
    text = data.decode("utf-8", errors="surrogateescape").replace("\r\n", "\n").replace("\r", "\n")
    body = _trim_blank_lines(strip_header(regen_gate.reset_header_score(text), language))
    return hashlib.sha256(body.encode("utf-8", errors="surrogateescape")).hexdigest()


def read_hashes(path: Path) -> tuple[str | None, str | None]:
    """(render hash, code hash) of a ``render.sha256`` file, None for one that is not there."""
    rows = [line.split() for line in path.read_text(encoding="utf-8", errors="replace").splitlines() if line.strip()]
    staged = rows[0][0] if rows and HASH_RE.fullmatch(rows[0][0]) else None
    code = next(
        (row[0] for row in rows[1:] if len(row) == 2 and row[1] == CODE_NAME and HASH_RE.fullmatch(row[0])), None
    )
    return staged, code


def read_hash(path: Path) -> str | None:
    """The render hash in a ``render.sha256`` file, or None when its first field is not one."""
    return read_hashes(path)[0]


@dataclass(frozen=True)
class Comparison:
    """What ``check`` found: the status, both render hashes, and why the renders are not tied to the code.

    ``via`` says which hash matched: ``file`` (every byte but the score) or
    ``code`` (only the header differs). ``form`` is the staged file's:
    ``two-line`` with a code hash, ``legacy`` without, empty when it was not
    read. ``cause`` is empty for a match and one of the ``CAUSE_*`` words for
    everything else.
    """

    status: str
    staged: str = ""
    head: str = ""
    reason: str = ""
    via: str = ""
    form: str = ""
    cause: str = ""

    @property
    def stop(self) -> bool:
        """Only a match lets the review run."""
        return self.status != "match"

    @property
    def retry(self) -> bool:
        """A failed download says nothing about the renders, so the same review is worth another run."""
        return self.cause == CAUSE_FETCH

    @property
    def keep_code(self) -> str:
        """The regen gate's code for a gated regeneration that stops here; empty for a match."""
        if not self.stop:
            return ""
        return KEEP_CODE if self.cause == CAUSE_MISMATCH else UNVERIFIED_CODE


def compare(hash_file: Path, source: Path, fetch_error: str = "", language: str = "") -> Comparison:
    """Compare the staged ``render.sha256`` with the implementation at the head.

    Without a known ``language`` the code hash is not compared, and the file
    counts as ``legacy``: only its render hash can match then.
    """
    data = source.read_bytes() if source.is_file() else None
    head = render_hash(data) if data is not None else ""
    if fetch_error:
        reason = f"staging could not be read ({regen_gate._one_line(fetch_error)[:200]})"
        return Comparison("unreadable", head=head, reason=reason, cause=CAUSE_FETCH)
    if not hash_file.is_file():
        return Comparison("missing", head=head, reason="no render.sha256 in staging", cause=CAUSE_MISSING)
    staged, staged_code = read_hashes(hash_file)
    if staged is None:
        return Comparison("unreadable", head=head, reason="render.sha256 holds no sha256", cause=CAUSE_CONTENT)
    form = FORM_CODE if staged_code is not None and language in LANGUAGES else FORM_LEGACY
    if data is None:
        reason = "the implementation at the head could not be read"
        return Comparison("unreadable", staged=staged, reason=reason, form=form, cause=CAUSE_HEAD)
    if staged == head:
        return Comparison("match", staged=staged, head=head, via="file", form=form)
    if form == FORM_CODE and staged_code == code_hash(data, language):
        return Comparison("match", staged=staged, head=head, via=CODE_NAME, form=form)
    return Comparison("mismatch", staged=staged, head=head, form=form, cause=CAUSE_MISMATCH)


def comment(
    result: Comparison, head: str, run_url: str, *, regeneration: bool = False, spec_id: str = "", library: str = ""
) -> str:
    """The PR comment for every status but a match: what was found, and what happens to the PR."""
    short = head[:7] or "the head"
    title = "Staged renders not checked against this code"
    if result.cause == CAUSE_MISMATCH:
        title = "Staged renders do not match this code"
        what = (
            f"`render.sha256` beside the staged renders is `{result.staged[:12]}`, but the implementation at "
            f"`{short}` hashes to `{result.head[:12]}`: the renders under review were made from other code."
        )
        if result.form == FORM_LEGACY:
            what += (
                " The file holds one hash only. Every render path has written two since the code hash exists, "
                "so this file is left from an older run."
            )
    elif result.cause == CAUSE_MISSING:
        what = (
            f"The staged renders carry no `render.sha256`, so nothing ties them to the implementation at `{short}`. "
            "Every render path writes the hash last and fails its run when it cannot, so renders without one were "
            "not staged by this PR's own run: they are left from an earlier run or were put there by hand."
        )
    elif result.cause == CAUSE_FETCH:
        what = (
            f"The render hash could not be downloaded after three attempts: {result.reason}. That is a failure of "
            "the storage, not a finding about the renders."
        )
    else:
        what = f"The render hash could not be checked: {result.reason}."
    then = "The review did not run: nothing is scored and the file header stays as it is. "
    if regeneration:
        then += (
            f"The regen gate keeps the live implementation (`{result.keep_code}`) and closes this PR; the pair "
            "returns after the attempt window."
        )
    elif result.retry:
        then += (
            f"This run ends as failed and labels the PR `{RETRY_LABEL}`, so the watchdog starts the review again "
            "once, at its next scan within six hours. If the download fails then as well, the PR needs a look."
        )
    else:
        then += (
            f"The review run labels this PR `{STOP_LABEL}` and ends as failed; the PR stays open, and no workflow "
            "picks it up again by itself."
        )
        if spec_id and library:
            # impl-generate.yml deletes the pair's branch before it creates it
            # anew ("Create implementation branch"), which closes this PR. The
            # command is the plain generation; a forced or adopted run takes
            # this path too (`regen:forced`, or an adopted first
            # implementation), and only its PR description says how it was made.
            then += (
                " To continue, generate the pair again. That run replaces this PR's branch, which closes this PR, "
                "and opens a new one with its own renders and review:\n\n"
                "```\n"
                f"gh workflow run bulk-generate.yml -f specification_id={spec_id} -f library={library}\n"
                "```\n\n"
                "That command generates the file anew, and for a pair that is live on `main` the regen gate decides. "
                "If this PR's description says it was forced or adopted from a branch, repeat that run instead: add "
                "`-f regen_gate=false`, or `-f source_ref=<the ref>` with its `-f source_model=<the model>`."
            )
    lines = [
        MARKER.format(status=result.status, cause=result.cause or "none", head=head or "n/a"),
        f"## :warning: {title}",
        "",
        what,
        "",
        then,
        "",
        "Every render path stages `render.sha256` beside its renders: the sha256 of the implementation it "
        "rendered with its `Quality:` header reset to `pending`, and the sha256 of the code below the header "
        "(`automation/scripts/render_hash.py`).",
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
    data = Path(args.source).read_bytes()
    digest, code = render_hash(data), code_hash(data, args.language)
    Path(args.out).write_text(f"{digest}  {args.source}\n{code}  {CODE_NAME}\n", encoding="utf-8")
    print(f"::notice::render_hash sha256={digest[:12]} code={code[:12]} language={args.language} source={args.source}")
    return 0


def cmd_check(args: argparse.Namespace) -> int:
    result = compare(Path(args.hash), Path(args.source), args.fetch_error, args.language)
    short = args.head[:7] or "n/a"
    form = result.form or "n/a"
    if result.status == "match":
        print(
            f"::notice::render_hash status=match sha256={result.staged[:12]} head={short} via={result.via} form={form}"
        )
        summary = f"**Render hash:** match: the staged renders come from the implementation at `{short}`."
        if result.via == CODE_NAME:
            summary = (
                f"**Render hash:** match: the staged renders come from the code at `{short}`; "
                "only the file header differs."
            )
    else:
        detail = result.reason or f"staged {result.staged[:12]}, head {result.head[:12]}"
        print(
            f"::warning::render_hash status={result.status} head={short} form={form} stop=true "
            f"cause={result.cause} retry={'true' if result.retry else 'false'}: {detail}"
        )
        summary = f"**Render hash:** {result.status} at `{short}` ({detail}); the review does not run."
        if args.comment_out:
            text = comment(
                result,
                args.head,
                args.run_url,
                regeneration=args.regeneration,
                spec_id=args.spec_id,
                library=args.library,
            )
            Path(args.comment_out).write_text(text, encoding="utf-8")
    outputs = {
        "status": result.status,
        "stop": "true" if result.stop else "false",
        "cause": result.cause,
        "retry": "true" if result.retry else "false",
        "code": result.keep_code,
    }
    _append("GITHUB_OUTPUT", "".join(f"{key}={value}\n" for key, value in outputs.items()))
    _append("GITHUB_STEP_SUMMARY", f"\n{summary}\n")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0] if __doc__ else None)
    sub = parser.add_subparsers(dest="command", required=True)

    write = sub.add_parser("write", help="Write render.sha256 for the implementation the renders came from")
    write.add_argument("--source", required=True)
    # Required: a file without the code hash matches by its render hash only,
    # so the review's own header commit would read as a mismatch. A writer
    # that could not name the language must fail, not write half a file.
    write.add_argument("--language", required=True, choices=LANGUAGES)
    write.add_argument("--out", required=True)
    write.set_defaults(func=cmd_write)

    check = sub.add_parser("check", help="Compare the staged render.sha256 with the implementation at the head")
    check.add_argument("--hash", required=True, help="the downloaded render.sha256 (absent: missing)")
    check.add_argument("--source", required=True, help="the implementation at the head (absent: unreadable)")
    check.add_argument("--language", default="", help="without a known one, only the render hash is compared")
    check.add_argument("--head", default="")
    check.add_argument("--fetch-error", default="", help="the download's error, other than a missing object")
    check.add_argument("--run-url", default="")
    check.add_argument("--comment-out", default="")
    check.add_argument("--regeneration", action="store_true", help="the comment names the regen gate's keep")
    check.add_argument("--spec-id", default="", help="for the comment's command on a first generation")
    check.add_argument("--library", default="", help="for the comment's command on a first generation")
    check.set_defaults(func=cmd_check)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
