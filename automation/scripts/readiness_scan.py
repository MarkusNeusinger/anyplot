#!/usr/bin/env python3
"""Readiness scan of an implementation against its predecessor (record-only).

The agent chat ("Use with my data") adapts a catalogue file only when its
validator accepts the file: the SECURITY profile, the theme block, the save
target (``agents/anyplot/code/readiness.py``). A regeneration or a repair can
add a construct the validator refuses and so turn a pair the chat could use
into one it refuses, while the render gets better. This script scans the new
file and the predecessor with that validator and records what the new file
adds (rule step P2b, the readiness-regression gate). Record-only for now: it
prints one line, writes a job-summary line and a record, and always exits 0.

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
own ref, next to a bare copy of the validator (``agents/anyplot/code``, the
two schema modules it imports, and ``core/``). Without ``agents/__init__.py``
the directories are namespace packages, so nothing of the agent runtime is
imported, and the implementation is never executed::

    readiness_scan.py scan --new NEW --spec-id S --library B [--prev PREV] [--out RECORD.json]

``--new`` and ``--prev`` may name files that do not exist.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path


RECORD_VERSION = 1
TREE = Path(__file__).resolve().parents[2]
_TOKEN = re.compile(r"^[a-z][a-z0-9-]*$")


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


def scan_side(code: str, *, spec_id: str, library: str) -> dict:
    """The validator's verdict on one file: its status, its refusal keys, and whether the spec itself is refused.

    ``findings`` counts how often each SECURITY rule fires. The verdict compares keys only, so a rule that fires
    more often than before is no regression; the count is in the record for whoever reads it later.
    """
    if str(TREE) not in sys.path:
        sys.path.insert(0, str(TREE))
    from agents.anyplot.code.normalise import SUPPORTED_LIBRARIES, normalise
    from agents.anyplot.code.readiness import scan
    from agents.anyplot.code.validate import validate_security
    from core.spec_roles import MAP_SPECS
    from core.utils import strip_noqa_comments

    if library not in SUPPORTED_LIBRARIES:
        return _side("unsupported")
    map_spec = spec_id in MAP_SPECS  # refused whatever the code holds, also when the code cannot be read
    try:
        normalised = normalise(strip_noqa_comments(code) or "", library=library)
    except Exception as exc:  # a file the normaliser cannot take: the chat cannot open it either
        return _side("error", refusals={f"error:{_token(type(exc).__name__.lower())}"}, spec_refused=map_spec)
    result = scan(normalised, spec_id=spec_id, library=library, enabled_libraries=[library])
    categories = {_token(reason.split(":", 1)[0].strip()) for reason in result.reasons}
    if result.status != "blocked":
        return _side(result.status, coupled=categories)
    keys = categories - {"map-spec", "security"}
    counts: dict[str, int] = {}
    if "security" in categories:
        try:
            for finding in validate_security(normalised, library=library):
                rule = _token(finding.rule)
                counts[rule] = counts.get(rule, 0) + 1
        except Exception:  # the scan fails closed on a crashing validator, and so does the key
            counts = {}
        keys |= {f"security:{rule}" for rule in counts} or {"security:validator-failed"}
    return _side("blocked", refusals=keys, spec_refused=map_spec, findings=counts)


def build_record(new: str | None, prev: str | None, *, spec_id: str, library: str) -> dict:
    """The record of one scan: both sides, the keys the new file adds and drops, and the verdict."""
    record: dict = {"version": RECORD_VERSION, "spec_id": spec_id, "library": library, "language": "python"}
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


def cmd_scan(args: argparse.Namespace) -> int:
    record = build_record(_read(args.new), _read(args.prev), spec_id=args.spec_id, library=args.library)
    print(log_line(record))
    summary = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary:
        with open(summary, "a", encoding="utf-8") as handle:
            handle.write(summary_line(record) + "\n")
    if args.out:
        Path(args.out).write_text(json.dumps(record, sort_keys=True) + "\n", encoding="utf-8")
    return 0


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
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
