#!/usr/bin/env python3
"""Readiness scan of an implementation against its predecessor (record-only).

The agent chat ("Use with my data") adapts a catalogue file only when its
validator accepts the file: the SECURITY profile, the theme block, the save
target (``agents/anyplot/code/readiness.py``). A regeneration or a repair can
add a construct the validator refuses and so turn a pair the chat could use
into one it refuses, while the render gets better. This script scans the new
file and the predecessor with that validator and records what the new file
adds (rule step P2b, the readiness-regression gate). The scan itself gates
nothing: it prints one line, writes a job-summary line and a record, and exits
0 for every verdict. ``impl-review.yml`` reads the record
(``readiness_record.py``), and on a gated regeneration a regression there
keeps the live implementation (``regen_gate.py``, ``readiness_regression``).

The record carries the hash of each file it scanned (``new_sha256``,
``prev_sha256``; ``readiness_record.code_sha256``, the source without its
leading docstring header, which impl-review rewrites). The reader compares
them with the implementation at the PR head and on ``origin/main``, so a
record of other code never decides anything.

A *refusal key* names why the validator blocks a file: ``security:<rule>`` for
every rule of the SECURITY profile the file breaks, read from the validator's
own findings (the scan's reasons list only the first five), and the reason's
category otherwise (``no-theme``, ``savefig-target``, ``syntax``, ``webgl``).
Keys are fixed identifiers of the validator; a record never quotes code.

The verdict, first match wins:

- ``unreadable``: no new file, or a library without a Python profile.
- ``excluded``: a map spec. The chat refuses those whatever the code holds.
- ``first_generation``: no predecessor.
- ``regression``: the new file is refused for a key the predecessor was not
  refused for. A predecessor the chat accepted has no key, so every key of
  the new file counts.
- ``none``: anything else, also a new file with fewer keys than before.

Python only: the profiles of R, Julia and JavaScript need tree-sitter grammars
that the generate and repair jobs do not carry.

``impl-generate.yml`` and ``impl-repair.yml`` run a copy from the workflow's
own ref, next to ``readiness_record.py`` (the hash) and a
bare copy of the validator (``agents/anyplot/code``, the
two schema modules it imports, and ``core/``). The step puts empty
``__init__.py`` files into ``agents/`` and ``agents/anyplot/`` there: the real
ones import the agent runtime, and without any the two would be namespace
packages, which lose the import to a regular ``agents`` package anywhere else
on the path. The scan refuses to go on when a validator module comes from
outside its own tree, and the implementation is never executed::

    readiness_scan.py scan --new NEW --spec-id S --library B [--prev PREV] [--out RECORD.json]

``--new`` and ``--prev`` may name files that do not exist.

``check`` is the generating or repairing session's own look at its file, before
it commits (Step 3c of ``impl-generate-claude.md``, Step 5b of
``impl-repair-claude.md``). It takes the same path through the validator as the
scan, so it calls a file accepted exactly when the scan would record no refusal
key, but it prints what the record leaves out: every reason in the validator's
own words, with its hint (``→ …``) where the validator gives one, and with the
line in the file as the session wrote it (the validator reads the normalised
text, which drops the header and rewrites the save). The last line is the
verdict: ``readiness: accepted``, ``refused (<keys>)``, ``excluded`` (a map
spec), ``not checked`` (a library without a Python profile) or ``not run``.
It writes nothing. The session runs it from a copy the workflow makes before
the session starts; the record-only scan makes its own after the session and
never reads that one, because the session can write anywhere on the runner::

    readiness_scan.py check FILE --spec-id S --library B

Exit 0 accepted, excluded or not checked; 1 refused; 2 when the check itself
cannot run (a path that names no file, a validator from outside its tree, a
broken copy). Python exits 2 as well when the copy is missing. A file the
session can fix is no such case: a normaliser or validator that fails on it is
a refusal key in the scan (``error:<type>``, ``security:validator-failed``),
and a file that is not UTF-8 text is one the chat cannot read (``encoding``),
so the check reports each as a refusal, exit 1.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from types import ModuleType


if __package__:  # imported as automation.scripts.readiness_scan (tests, local tools)
    from automation.scripts import readiness_record
else:  # run as a script: the readiness_record.py next to this file (the workflow-ref copy)
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import readiness_record


# 2: the record names the hash of both scanned files.
RECORD_VERSION = 2
TREE = Path(__file__).resolve().parents[2]
_TOKEN = re.compile(r"^[a-z][a-z0-9-]*$")
# How the readiness scan's own reasons name a line: `at line 12`, `at lines 12-14`, `syntax: line 12 does not parse`.
_LINES = re.compile(r"\b(lines?) (\d+)(?:-(\d+))?\b")
_MAX_ERROR_CHARS = 200


def _token(value: str) -> str:
    """``value`` when it is one of the validator's identifiers, else ``other``: a record never carries free text."""
    return value if _TOKEN.match(value) else "other"


def _side(
    status: str,
    *,
    refusals: set[str] | None = None,
    spec_refused: bool = False,
    coupled: set[str] | None = None,
    findings: dict[str, int] | None = None,
) -> dict:
    return {
        "status": status,
        "refusals": sorted(refusals or ()),
        "spec_refused": spec_refused,
        "coupled": sorted(coupled or ()),
        "findings": dict(sorted((findings or {}).items())),
    }


@dataclass(frozen=True)
class _Scan:
    """One file's side of the record, and what only the session's check prints.

    ``reasons`` holds every refusal in the validator's own words, each line number one of the scanned file. A
    normaliser or validator that fails on the file is a refusal too: the chat cannot take the file either.
    """

    side: dict
    reasons: list[str] = field(default_factory=list)


# What a session can do about a normaliser or validator that fails on its file: the error names no line.
_CRASH_ADVICE = (
    "write the construct the error points at more plainly (often the one changed last) and run the check again"
)


def _validator() -> tuple[ModuleType, ModuleType, ModuleType, ModuleType, ModuleType]:
    """The normaliser, the scan, the validator, the spec roles and the code utilities, all from this tree."""
    if str(TREE) not in sys.path:
        sys.path.insert(0, str(TREE))
    from agents.anyplot.code import normalise as normalise_module
    from agents.anyplot.code import readiness, validate
    from core import spec_roles, utils

    for module in (normalise_module, readiness, validate, spec_roles, utils):
        if TREE not in Path(module.__file__ or "").resolve().parents:
            raise ImportError(f"{module.__name__} was imported from outside {TREE}: not this ref's validator")
    return normalise_module, readiness, validate, spec_roles, utils


def scan_side(code: str, *, spec_id: str, library: str) -> dict:
    """The validator's verdict on one file: its status, its refusal keys, and whether the spec itself is refused.

    ``findings`` counts how often each SECURITY rule fires. The verdict compares keys only, so a rule that fires
    more often than before is no regression; the count is in the record for whoever reads it later.
    """
    return _scan(code, spec_id=spec_id, library=library).side


def _scan(code: str, *, spec_id: str, library: str) -> _Scan:
    """``scan_side`` with the reasons the session's check prints; the record and the check share this one path."""
    normalise_module, readiness, validate, spec_roles, utils = _validator()
    if library not in normalise_module.SUPPORTED_LIBRARIES:
        return _Scan(_side("unsupported"))
    map_spec = spec_id in spec_roles.MAP_SPECS  # refused whatever the code holds, also when the code cannot be read
    stripped = utils.strip_noqa_comments(code) or ""
    try:
        normalised = normalise_module.normalise(stripped, library=library)
    except Exception as exc:  # a file the normaliser cannot take: the chat cannot open it either
        side = _side("error", refusals={f"error:{_token(type(exc).__name__.lower())}"}, spec_refused=map_spec)
        reason = f"error: the chat's normaliser fails on this file ({_error(exc)}), so the chat cannot open it"
        return _Scan(side, [f"{reason} → {_CRASH_ADVICE}"])
    result = readiness.scan(normalised, spec_id=spec_id, library=library, enabled_libraries=[library])
    categories = {_token(reason.split(":", 1)[0].strip()) for reason in result.reasons}
    if result.status != "blocked":
        return _Scan(_side(result.status, coupled=categories))
    # The validator read the normalised text; the session edits the file as it wrote it. Two steps, because a
    # line whose noqa comment was stripped no longer matches its original, and a run of such lines beside a
    # removed guard would map as one replaced region.
    to_stripped, to_code = utils.line_map(stripped, normalised), utils.line_map(code, stripped)
    lines = {line: to_code.get(middle, middle) for line, middle in to_stripped.items()}
    keys = categories - {"map-spec", "security"}
    reasons = [
        _relined(reason, lines)
        for reason in result.reasons
        if _token(reason.split(":", 1)[0].strip()) not in ("map-spec", "security")
    ]
    counts: dict[str, int] = {}
    if "security" in categories:
        try:
            # Every finding, not the scan's first five: the session needs each line, and the key needs each rule.
            findings = validate.validate_security(normalised, library=library)
        except Exception as exc:  # the scan fails closed on a crashing validator, and so does the key
            findings = []
            reason = f"security: validator-failed: the chat's validator fails on this file ({_error(exc)})"
            reasons.append(f"{reason}, so the chat refuses it → {_CRASH_ADVICE}")
        for finding in findings:
            rule = _token(finding.rule)
            counts[rule] = counts.get(rule, 0) + 1
            where = "" if finding.line is None else f" at line {lines.get(finding.line, finding.line)}"
            reasons.append(f"security: {finding.rule}{where}: {finding.message}")
        keys |= {f"security:{rule}" for rule in counts} or {"security:validator-failed"}
    side = _side("blocked", refusals=keys, spec_refused=map_spec, findings=counts)
    return _Scan(side, sorted(reasons, key=_first_line))


def _relined(reason: str, lines: dict[int, int]) -> str:
    """``reason`` with every line number it names moved from the normalised text to the scanned file."""

    def moved(match: re.Match[str]) -> str:
        first = lines.get(int(match.group(2)), int(match.group(2)))
        if match.group(3) is None:
            return f"{match.group(1)} {first}"
        last = lines.get(int(match.group(3)), int(match.group(3)))
        return f"line {first}" if first == last else f"lines {first}-{last}"

    return _LINES.sub(moved, reason)


def _first_line(reason: str) -> int:
    """The first line number a reason names; 0 for a reason about the whole file, which then comes first."""
    match = _LINES.search(reason)
    return int(match.group(2)) if match else 0


def _error(exc: BaseException) -> str:
    """An exception as one short line: its type and the start of its message."""
    text = " ".join(f"{type(exc).__name__}: {exc}".split())
    return text if len(text) <= _MAX_ERROR_CHARS else text[: _MAX_ERROR_CHARS - 1] + "…"


def check(code: str, *, spec_id: str, library: str) -> tuple[int, list[str]]:
    """The session's self-check of one file: its exit code and the lines it prints (module docstring)."""
    result = _scan(code, spec_id=spec_id, library=library)
    side = result.side
    if side["status"] == "unsupported":
        return 0, [f"readiness: not checked ({library} has no Python profile in the chat's validator)"]
    if side["spec_refused"]:
        return 0, [
            f"readiness: excluded ({spec_id} is a map spec, which the chat refuses whatever the code holds; "
            "nothing to fix)"
        ]
    if not side["refusals"]:
        return 0, ["readiness: accepted"]
    return 1, [*result.reasons, f"readiness: refused ({', '.join(side['refusals'])})"]


def build_record(
    new: str | None,
    prev: str | None,
    *,
    spec_id: str,
    library: str,
    new_sha256: str | None = None,
    prev_sha256: str | None = None,
) -> dict:
    """The record of one scan: both sides with their hashes, the keys the new file adds and drops, and the verdict."""
    record: dict = {
        "version": RECORD_VERSION,
        "spec_id": spec_id,
        "library": library,
        "language": "python",
        "new_sha256": new_sha256 if new is not None else None,
        "prev_sha256": prev_sha256 if prev is not None else None,
    }
    new_side = None if new is None else scan_side(new, spec_id=spec_id, library=library)
    prev_side = None if prev is None or new_side is None else scan_side(prev, spec_id=spec_id, library=library)
    added: list[str] = []
    removed: list[str] = []
    if new_side is None or new_side["status"] == "unsupported":
        verdict = "unreadable"
    elif new_side["spec_refused"]:
        verdict = "excluded"
    elif prev_side is None:
        verdict = "first_generation"
    else:
        added = [key for key in new_side["refusals"] if key not in prev_side["refusals"]]
        removed = [key for key in prev_side["refusals"] if key not in new_side["refusals"]]
        verdict = "regression" if added else "none"
    return {**record, "verdict": verdict, "new": new_side, "prev": prev_side, "added": added, "removed": removed}


def _statuses(record: dict) -> str:
    new = record["new"]["status"] if record["new"] else "missing"
    prev = record["prev"]["status"] if record["prev"] else "none"
    return f"new {new}, predecessor {prev}"


def summary_line(record: dict) -> str:
    """One Markdown line for the job summary."""
    head = "**Readiness (record-only):** "
    verdict = record["verdict"]
    if verdict == "regression":
        return f"{head}regression: {', '.join(record['added'])} ({_statuses(record)})"
    if verdict == "none":
        return f"{head}no new refusal ({_statuses(record)})"
    if verdict == "first_generation":
        return f"{head}first generation (new {record['new']['status']})"
    if verdict == "excluded":
        return f"{head}excluded (a map spec, which the chat refuses whatever the code holds)"
    return f"{head}unreadable (no new file, or a library without a Python profile)"


def log_line(record: dict) -> str:
    """One log line: a warning for a regression, a notice otherwise."""
    new = record["new"]["status"] if record["new"] else "missing"
    prev = record["prev"]["status"] if record["prev"] else "n/a"
    level = "warning" if record["verdict"] == "regression" else "notice"
    return (
        f"::{level}::readiness_scan spec={record['spec_id']} lib={record['library']} verdict={record['verdict']} "
        f"new={new} prev={prev} added={','.join(record['added']) or 'none'} "
        f"removed={','.join(record['removed']) or 'none'}"
    )


def _read(path: str | None) -> str | None:
    if not path:
        return None
    try:
        return Path(path).read_text(encoding="utf-8")
    except OSError, UnicodeDecodeError:
        return None


def _digest(path: str | None) -> str | None:
    """The code hash of a file's bytes (``readiness_record.file_sha256``), or None when it cannot be read."""
    if not path:
        return None
    try:
        return readiness_record.file_sha256(Path(path).read_bytes())
    except OSError:
        return None


def cmd_scan(args: argparse.Namespace) -> int:
    record = build_record(
        _read(args.new),
        _read(args.prev),
        spec_id=args.spec_id,
        library=args.library,
        new_sha256=_digest(args.new),
        prev_sha256=_digest(args.prev),
    )
    print(log_line(record))
    summary = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary:
        with open(summary, "a", encoding="utf-8") as handle:
            handle.write(summary_line(record) + "\n")
    if args.out:
        Path(args.out).write_text(json.dumps(record, sort_keys=True) + "\n", encoding="utf-8")
    return 0


def cmd_check(args: argparse.Namespace) -> int:
    """Print every refusal of one file and the verdict; never raises (module docstring, ``check``)."""
    try:
        code = Path(args.file).read_text(encoding="utf-8")
    except UnicodeDecodeError as exc:  # the session's file, which it can fix: the chat cannot read it either
        line = exc.object[: exc.start].count(b"\n") + 1
        print(f"encoding: line {line} is not UTF-8 text, so the chat cannot read the file → save it as UTF-8")
        print("readiness: refused (encoding)")
        return 1
    except OSError as exc:
        print(f"readiness: not run (cannot read {args.file}: {_error(exc)})")
        return 2
    try:
        status, lines = check(code, spec_id=args.spec_id, library=args.library)
    except Exception as exc:  # a self-check that cannot run says so; it never takes the session down
        print(f"readiness: not run ({_error(exc)})")
        return 2
    print("\n".join(lines))
    return status


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    sub = parser.add_subparsers(dest="command", required=True)
    scan_parser = sub.add_parser("scan", help="scan one implementation and its predecessor, record-only")
    scan_parser.add_argument("--new", required=True, help="the implementation of this run")
    scan_parser.add_argument("--prev", help="the predecessor from main; a missing file is a first generation")
    scan_parser.add_argument("--spec-id", required=True)
    scan_parser.add_argument("--library", required=True)
    scan_parser.add_argument("--out", help="write the record as one JSON line")
    scan_parser.set_defaults(func=cmd_scan)
    check_parser = sub.add_parser("check", help="the session's self-check: every refusal of one file, with its line")
    check_parser.add_argument("file", help="the implementation the session wrote")
    check_parser.add_argument("--spec-id", required=True)
    check_parser.add_argument("--library", required=True)
    check_parser.set_defaults(func=cmd_check)
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
