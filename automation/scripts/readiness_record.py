#!/usr/bin/env python3
"""Read a staged readiness record against the code under review (rule step P2b).

``impl-generate.yml`` and ``impl-repair.yml`` stage ``adapt/readiness.json``,
the record of ``readiness_scan.py``: what the agent chat's validator refuses in
the new implementation and in its predecessor. ``impl-review.yml`` reads it
here before anything keys a decision on it:

- The record must be the scanner's: its version, this pair, identifiers only.
- It must be about this code: ``new_sha256`` is the code hash of the
  implementation at the PR head and ``prev_sha256`` that of the file on
  ``origin/main`` (``code_sha256``: the source without its leading docstring
  header, the rule of the adapt records). impl-review rewrites that header
  when it stores a review, so a re-review of the same code still finds its
  record, and the validator never reads the header either.
- The regression is recomputed from the two sides' refusal keys. The record's
  own ``verdict``, ``added`` and ``removed`` are never read.

The status, first match wins:

- ``missing``: no record was staged.
- ``invalid``: the file is not a record this reader knows.
- ``stale``: the record is of other code than the head or the predecessor.
- ``unreadable``, ``excluded``, ``first_generation``, ``regression`` and
  ``none``: as ``readiness_scan.py`` defines them.

Only ``regression`` ever changes a decision: on a gated regeneration
``regen_gate.py`` keeps the live implementation (``readiness_regression``).
Every other status leaves the pipeline as it is, so a lost upload, a push
after the scan or a scan that could not run never refuses anything::

    readiness_record.py check --record adapt/readiness.json --new IMPL_AT_HEAD --prev IMPL_ON_MAIN \\
        --spec-id S --library B [--out VERDICT.json]

``--record``, ``--new`` and ``--prev`` may name files that do not exist.
``check`` prints one ``::notice::`` (a ``::warning::`` for a regression),
writes a job-summary line and ``status=`` to ``$GITHUB_OUTPUT`` when they are
set, and with ``--out`` the verdict as one JSON line. It always exits 0 (2 on
a usage error). Stdlib only and a single file: impl-review runs it with the
runner's Python from a copy at the workflow's ref, and ``readiness_scan.py``
imports ``code_sha256`` from the copy beside it.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any


# The record version of ``readiness_scan.py`` this reader knows, and the
# version of the verdict it writes for ``regen_gate.py decide --readiness``.
RECORD_VERSION = 2
VERDICT_VERSION = 1
RECORD_LIMIT = 1_000_000
KEY_LIMIT = 64
# A refusal key: ``security:<rule>``, ``error:<name>`` or a bare category.
# Never two hyphens in a row: the gate record that carries the keys sits in an
# HTML comment. ``regen_gate.READINESS_KEY_RE`` is the same pattern.
KEY_RE = re.compile(r"(?=.{1,81}$)[a-z][a-z0-9]*(?:-[a-z0-9]+)*(?::[a-z][a-z0-9]*(?:-[a-z0-9]+)*)?")
HASH_RE = re.compile(r"[0-9a-f]{64}")

MISSING = "missing"
INVALID = "invalid"
STALE = "stale"
UNREADABLE = "unreadable"
EXCLUDED = "excluded"
FIRST_GENERATION = "first_generation"
REGRESSION = "regression"
NONE = "none"
STATUSES = (MISSING, INVALID, STALE, UNREADABLE, EXCLUDED, FIRST_GENERATION, REGRESSION, NONE)
# What the validator says about one file (``readiness_scan.scan_side``); only
# a file it does not accept has refusal keys.
SIDE_STATUSES = ("clean", "coupled", "blocked", "error", "unsupported")
REFUSED = ("blocked", "error")
NO_SIDE = "n/a"

# Why a record is ``invalid`` or ``stale``: fixed words, never a value from the file.
WHY_TEXT = {
    "unparsable": "the file is not JSON, or too large",
    "shape": "the file is not a record of readiness_scan.py",
    "version": "the record has another version than this reader knows",
    "pair": "the record is of another spec, library or language",
    "side": "a side of the record is malformed",
    "hash": "the record carries no usable hash",
    "head": "the record is not of the implementation at the PR head",
    "main": "the record's predecessor is not the implementation on origin/main",
}


@dataclass(frozen=True)
class Verdict:
    """What the record says about this code: the status, each side's status, and the refusal keys that changed."""

    status: str
    new: str = NO_SIDE
    prev: str = NO_SIDE
    added: tuple[str, ...] = ()
    removed: tuple[str, ...] = ()
    why: str = ""

    def to_json(self) -> dict[str, Any]:
        return {
            "version": VERDICT_VERSION,
            "status": self.status,
            "new": self.new,
            "prev": self.prev,
            "added": list(self.added),
            "removed": list(self.removed),
        }


def load_record(path_text: str) -> tuple[Any, str]:
    """The parsed record and ``""``, or None and why it is not there (``missing`` or ``unparsable``)."""
    path = Path(path_text)
    try:
        if not path.is_file() or path.stat().st_size == 0:
            return None, MISSING
        if path.stat().st_size > RECORD_LIMIT:
            return None, "unparsable"
        return json.loads(path.read_text(encoding="utf-8")), ""
    except OSError, ValueError, RecursionError:
        return None, "unparsable"


def _side(value: Any) -> tuple[str, frozenset[str], bool] | None:
    """One side as (status, refusal keys, spec refused), or None when it is not a side of the scanner's."""
    if not isinstance(value, dict):
        return None
    status, refusals, spec_refused = value.get("status"), value.get("refusals"), value.get("spec_refused")
    if status not in SIDE_STATUSES or not isinstance(spec_refused, bool):
        return None
    if not isinstance(refusals, list) or len(refusals) > KEY_LIMIT:
        return None
    if not all(isinstance(key, str) and KEY_RE.fullmatch(key) for key in refusals):
        return None
    # A file the validator accepts has no refusal: its keys never count.
    return status, frozenset(refusals) if status in REFUSED else frozenset(), spec_refused


def code_sha256(text: str) -> str:
    """The SHA-256 of a source without its leading docstring header.

    The rule of ``core.smoke_run.code_sha256`` and ``adapt_record.code_sha256``,
    reimplemented because this file runs alone (a parity test holds the three
    together). impl-review rewrites the header when it stores a review; the
    code below it is what the validator scans.
    """
    body = text.lstrip()
    if body.startswith('"""'):
        end = body.find('"""', 3)
        if end != -1:
            body = body[end + 3 :]
    return hashlib.sha256(body.strip().encode("utf-8")).hexdigest()


def file_sha256(data: bytes | None) -> str | None:
    """``code_sha256`` of a file's bytes, or None for no file and for bytes that are not UTF-8.

    Bytes, not text read in text mode: ``git show`` hands out bytes, and a
    ``\\r\\n`` file must hash the same on both sides.
    """
    if data is None:
        return None
    try:
        return code_sha256(data.decode("utf-8"))
    except UnicodeDecodeError:
        return None


def assess(record: Any, *, spec_id: str, library: str, head: bytes | None, main: bytes | None) -> Verdict:
    """The verdict of a parsed record for the implementation at the head and the one on ``origin/main``.

    ``head`` and ``main`` are the two files' bytes, None for a file that is
    not there. A first generation has neither a ``prev`` side nor a file on
    ``origin/main``; a record and a repository that disagree on that are
    ``stale``.
    """
    if not isinstance(record, dict):
        return Verdict(INVALID, why="shape")
    version = record.get("version")
    if isinstance(version, bool) or version != RECORD_VERSION:
        return Verdict(INVALID, why="version")
    if (record.get("spec_id"), record.get("library"), record.get("language")) != (spec_id, library, "python"):
        return Verdict(INVALID, why="pair")
    if record.get("new") is None:
        return Verdict(UNREADABLE)
    new = _side(record["new"])
    prev = None if record.get("prev") is None else _side(record["prev"])
    if new is None or (record.get("prev") is not None and prev is None):
        return Verdict(INVALID, why="side")
    new_hash, prev_hash = record.get("new_sha256"), record.get("prev_sha256")
    if not (isinstance(new_hash, str) and HASH_RE.fullmatch(new_hash)):
        return Verdict(INVALID, why="hash")
    if prev is not None and not (isinstance(prev_hash, str) and HASH_RE.fullmatch(prev_hash)):
        return Verdict(INVALID, why="hash")
    sides = {"new": new[0], "prev": prev[0] if prev else NO_SIDE}
    if file_sha256(head) != new_hash:
        return Verdict(STALE, why="head", **sides)
    if (prev_hash if prev is not None else None) != file_sha256(main):
        return Verdict(STALE, why="main", **sides)
    if new[0] == "unsupported":
        return Verdict(UNREADABLE, **sides)
    if new[2]:
        return Verdict(EXCLUDED, **sides)
    if prev is None:
        return Verdict(FIRST_GENERATION, **sides)
    added = tuple(sorted(new[1] - prev[1]))
    removed = tuple(sorted(prev[1] - new[1]))
    return Verdict(REGRESSION if added else NONE, added=added, removed=removed, **sides)


def check(record_path: str, *, spec_id: str, library: str, head: bytes | None, main: bytes | None) -> Verdict:
    """``assess`` for a record file that may be absent or unreadable."""
    record, problem = load_record(record_path)
    if problem == MISSING:
        return Verdict(MISSING)
    if problem:
        return Verdict(INVALID, why=problem)
    return assess(record, spec_id=spec_id, library=library, head=head, main=main)


def _sides(verdict: Verdict) -> str:
    return f"new {verdict.new}, predecessor {verdict.prev}"


def summary_line(verdict: Verdict) -> str:
    """One Markdown line for the job summary."""
    head = "**Readiness check:** "
    if verdict.status == REGRESSION:
        return f"{head}regression: {', '.join(verdict.added)} ({_sides(verdict)})"
    if verdict.status == NONE:
        return f"{head}no new refusal ({_sides(verdict)})"
    if verdict.status == FIRST_GENERATION:
        return f"{head}first generation (new {verdict.new})"
    if verdict.status == EXCLUDED:
        return f"{head}excluded (a map spec, which the chat refuses whatever the code holds)"
    if verdict.status == UNREADABLE:
        return f"{head}unreadable (the scan had no new file, or the library has no Python profile)"
    if verdict.status == MISSING:
        return f"{head}missing (no readiness record is staged)"
    return f"{head}{verdict.status} ({WHY_TEXT.get(verdict.why, verdict.why)})"


def log_line(verdict: Verdict, *, spec_id: str, library: str) -> str:
    """One log line: a warning for a regression, a notice otherwise."""
    level = "warning" if verdict.status == REGRESSION else "notice"
    why = f" why={verdict.why}" if verdict.why else ""
    return (
        f"::{level}::readiness_check spec={spec_id} lib={library} status={verdict.status} "
        f"new={verdict.new} prev={verdict.prev} added={','.join(verdict.added) or 'none'} "
        f"removed={','.join(verdict.removed) or 'none'}{why}"
    )


def _bytes(path: str | None) -> bytes | None:
    if not path:
        return None
    try:
        return Path(path).read_bytes()
    except OSError:
        return None


def _append(env_var: str, text: str) -> None:
    target = os.environ.get(env_var)
    if target:
        with open(target, "a", encoding="utf-8") as handle:
            handle.write(text)


def cmd_check(args: argparse.Namespace) -> int:
    verdict = check(
        args.record, spec_id=args.spec_id, library=args.library, head=_bytes(args.new), main=_bytes(args.prev)
    )
    print(log_line(verdict, spec_id=args.spec_id, library=args.library))
    _append("GITHUB_STEP_SUMMARY", summary_line(verdict) + "\n")
    _append("GITHUB_OUTPUT", f"status={verdict.status}\n")
    if args.out:
        Path(args.out).write_text(json.dumps(verdict.to_json(), sort_keys=True) + "\n", encoding="utf-8")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=(__doc__ or "").split("\n", 1)[0])
    sub = parser.add_subparsers(dest="command", required=True)
    check_parser = sub.add_parser("check", help="read a staged readiness record against the code under review")
    check_parser.add_argument("--record", required=True, help="the staged adapt/readiness.json (absent: missing)")
    check_parser.add_argument("--new", required=True, help="the implementation at the PR head")
    check_parser.add_argument("--prev", help="the implementation on origin/main; a missing file is a first generation")
    check_parser.add_argument("--spec-id", required=True)
    check_parser.add_argument("--library", required=True)
    check_parser.add_argument("--out", help="write the verdict as one JSON line")
    check_parser.set_defaults(func=cmd_check)
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
