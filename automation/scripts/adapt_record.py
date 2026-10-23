#!/usr/bin/env python3
"""Adapt records: impl-review's record-only adaptability check of one implementation.

Standard library only. ``impl-review.yml`` "Adaptability check (record-only)"
runs it from the copy it takes at its own ref (``$RUNNER_TEMP/regen-tools/``),
once per side of a Python pair:

- ``new``: the PR head's implementation. Always, for a Python library.
- ``prev``: the predecessor from ``origin/main``. A regeneration only.

Each side combines two inputs into one JSON record
(``docs/concepts/adaptable-code.md``, "The checks"):

- ``static``: what the checker mirror (``adaptability_check.py check --out``)
  wrote, verbatim, plus its exit code. When the mirror exits 2 or writes
  nothing, it is ``{"status": "error", "exit": N}``.
- ``smoke``: the perturbation smoke run impl-generate staged
  (``core.smoke_run run``, ``new-smoke.json`` or ``prev-smoke.json``), trimmed
  to its status, reason and failures. A missing or unreadable file is
  ``missing``; a file whose ``code_sha256`` differs from the checked source's is
  ``stale``, because it ran on another version of the code.

CLI::

    adapt_record.py record --side new --spec bar-grouped --lib matplotlib --language python \\
        --source plots/bar-grouped/implementations/python/matplotlib.py \\
        --static static-new.json --static-exit 0 --smoke new-smoke.json \\
        [--selfcheck selfcheck.jsonl] --out /tmp/anyplot-adapt-new.json

``record`` writes the record and prints one ``::notice::adapt_check`` line.
It exits 0 once the record is written, 1 when it cannot be written, and 2 on
a usage error. The workflow never gates on it.

The derived ``status`` (first matching rule wins; ``why`` is a token):

=========  =================================  ============================================
status     why                                rule
=========  =================================  ============================================
unknown    static_error                       ``static.status`` is ``error``
excluded   excluded                           ``static.status`` is ``excluded`` (map specs)
fail       static_fail                        ``static.status`` is ``fail``
unknown    smoke_missing, smoke_stale         ``smoke.status`` is ``missing`` or ``stale``
fail       smoke_fail                         ``smoke.status`` is ``fail``
pass       smoke_na                           ``skipped`` for ``shape:generated`` or ``shape:network``
unknown    smoke_skipped                      any other ``skipped`` (``no_perturbations:*`` too)
pass       ``-``                              ``smoke.status`` is ``pass``
=========  =================================  ============================================

The regen gate (``regen_gate.py adapt-route`` and ``decide --adapt-new
--adapt-prev``) reads ``v``, ``side``, ``spec``, ``lib``, ``language``,
``checker_version``, ``status``, ``static.status``, ``smoke.status`` and
``smoke.why``. It cross-checks the derived status against the two blocks
with its own copy of this table (``regen_gate.derived_adapt_status``; a unit
test runs both over every combination) and rejects a record whose status
does not follow from them. Everything else is diagnostics for the regen-pair
artifact and the weekly review.

``code_sha256`` is byte for byte the function of ``core.smoke_run``: the
SHA-256 of the source without its leading docstring header, which the
workflows rewrite (``Quality:``, ``Updated:``). A unit test pins the two.

Every value the notice prints is reduced to a token first: the smoke results
come from the generation runner, where a model session had a shell.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any


RECORD_VERSION = 1
SIDES = ("new", "prev")
STATUSES = ("pass", "fail", "excluded", "unknown")
STATIC_STATUSES = ("pass", "fail", "excluded")
STAGED_SMOKE_STATUSES = ("pass", "fail", "skipped")
# A `skipped` smoke run whose shape has no table to perturb is not a gap: the
# static check is the whole check there.
SMOKE_NOT_APPLICABLE = ("shape:generated", "shape:network")
# core.smoke_run.SELFCHECK_SKIP_PREFIXES (tests/unit/automation/scripts/
# test_adapt_record.py ties the two; this script is copied alone and imports no
# core): a skip with one of these reasons passes a self-check attempt, as
# `selfcheck` exits 0 on it. `no_perturbations:` still reads `unknown` in the
# record (derive_status): the smoke run checked nothing.
SELFCHECK_SKIP_PREFIXES = ("shape:", "no_perturbations:")
# core.adaptability.RULE_ORDER (tests/unit/automation/scripts/test_adapt_record.py
# ties the two): the notice lists rule classes in this order.
RULE_ORDER = (
    "layout",
    "columns",
    "interface",
    "column-literal",
    "sample-literal",
    "data-coordinate",
    "statistic-text",
    "df-comparison",
    "count-literal",
    "palette",
    "constants",
)
TOKEN_RE = re.compile(r"^[A-Za-z0-9_.:+-]{1,64}$")
MAX_ERROR_CHARS = 300
MAX_RESULTS = 50
NONE = "-"


def code_sha256(text: str) -> str:
    """The SHA-256 of the source without its leading docstring header (core.smoke_run's rule)."""
    body = text.lstrip()
    if body.startswith('"""'):
        end = body.find('"""', 3)
        if end != -1:
            body = body[end + 3 :]
    return hashlib.sha256(body.strip().encode("utf-8")).hexdigest()


def token(value: Any, default: str = "n/a") -> str:
    """``value`` when it is a short token safe for a notice line, else ``default``."""
    if isinstance(value, bool) or value is None:
        return default
    text = str(value)
    return text if TOKEN_RE.fullmatch(text) else default


def _tokens(values: Any) -> list[str]:
    if not isinstance(values, list):
        return []
    return [str(v) for v in values if isinstance(v, str) and TOKEN_RE.fullmatch(v)]


def _int_or_none(value: Any) -> int | None:
    if isinstance(value, bool) or not isinstance(value, int):
        return None
    return value


def load_json(path: Path | None) -> Any:
    """The parsed file, or None when it is absent, unreadable or not JSON."""
    if path is None or not path.is_file():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        print(f"::warning::{path.name} is unreadable: {' '.join(str(exc).split())[:200]}")
        return None


def static_block(path: Path | None, exit_code: int) -> dict[str, Any]:
    """The mirror's record verbatim plus ``exit``, or ``{"status": "error", "exit": N}``."""
    data = load_json(path)
    if exit_code not in (0, 1) or not isinstance(data, dict) or data.get("status") not in STATIC_STATUSES:
        return {"status": "error", "exit": exit_code}
    return {**data, "exit": exit_code}


def _empty_smoke(status: str, fresh: bool | None) -> dict[str, Any]:
    return {"status": status, "why": NONE, "fresh": fresh, "failed": [], "advisory_failed": [], "results": []}


def _result(item: Any) -> dict[str, Any] | None:
    if not isinstance(item, dict):
        return None
    error = item.get("error")
    return {
        "name": token(item.get("name"), default=NONE),
        "status": token(item.get("status"), default=NONE),
        "advisory": item.get("advisory") is True,
        "line": _int_or_none(item.get("line")),
        "error": " ".join(error.split())[:MAX_ERROR_CHARS] if isinstance(error, str) else None,
    }


def smoke_block(path: Path | None, source_sha: str | None) -> dict[str, Any]:
    """The staged smoke run, trimmed: ``pass``, ``fail``, ``skipped``, ``missing`` or ``stale``."""
    data = load_json(path)
    if not isinstance(data, dict) or data.get("status") not in STAGED_SMOKE_STATUSES:
        return _empty_smoke("missing", None)
    staged_sha = data.get("code_sha256")
    if source_sha is None or not isinstance(staged_sha, str) or staged_sha != source_sha:
        return _empty_smoke("stale", False)
    raw_results = data.get("results")
    results = (
        [r for r in (_result(item) for item in raw_results[:MAX_RESULTS]) if r] if isinstance(raw_results, list) else []
    )
    return {
        "status": data["status"],
        "why": token(data.get("why"), default=NONE),
        "fresh": True,
        "failed": _tokens(data.get("failed")),
        "advisory_failed": _tokens(data.get("advisory_failed")),
        "results": results,
    }


def selfcheck_block(path: Path | None) -> dict[str, Any] | None:
    """``{"attempts": N, "first": "pass"|"fail"}`` from the generator's Step 3c log, or None.

    An attempt passes as ``selfcheck`` exits 0: its static check is ``pass``
    or ``excluded``, and its smoke run is ``pass`` or ``skipped`` for the
    shape or for a sample with nothing to perturb (``smoke_why`` ``shape:*``
    or ``no_perturbations:*``, ``SELFCHECK_SKIP_PREFIXES``). A log line
    without ``smoke_why`` reads any ``skipped`` as a pass.
    """
    if path is None or not path.is_file():
        return None
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError:
        return None
    attempts: list[dict[str, Any]] = []
    for line in lines:
        try:
            item = json.loads(line)
        except ValueError:
            continue
        if isinstance(item, dict):
            attempts.append(item)
    if not attempts:
        return None
    first = attempts[0]
    smoke, smoke_why = first.get("smoke"), first.get("smoke_why")
    if isinstance(smoke_why, str):
        smoke_ok = smoke == "pass" or (smoke == "skipped" and smoke_why.startswith(SELFCHECK_SKIP_PREFIXES))
    else:
        smoke_ok = smoke in ("pass", "skipped")
    passed = first.get("static") in ("pass", "excluded") and smoke_ok
    return {"attempts": len(attempts), "first": "pass" if passed else "fail"}


def derive_status(static_status: str, smoke_status: str, smoke_why: str) -> tuple[str, str]:
    """The record's ``(status, why)`` from the static and smoke statuses (module docstring table)."""
    if static_status not in STATIC_STATUSES:
        return "unknown", "static_error"
    if static_status == "excluded":
        return "excluded", "excluded"
    if static_status == "fail":
        return "fail", "static_fail"
    if smoke_status in ("missing", "stale"):
        return "unknown", f"smoke_{smoke_status}"
    if smoke_status == "fail":
        return "fail", "smoke_fail"
    if smoke_status == "skipped":
        if smoke_why in SMOKE_NOT_APPLICABLE:
            return "pass", "smoke_na"
        return "unknown", "smoke_skipped"
    if smoke_status == "pass":
        return "pass", NONE
    return "unknown", "smoke_missing"


def build_record(
    *,
    side: str,
    spec: str,
    lib: str,
    language: str,
    source: Path | None,
    static: Path | None,
    static_exit: int,
    smoke: Path | None,
    selfcheck: Path | None = None,
) -> dict[str, Any]:
    """One side's record (the format of the module docstring)."""
    text: str | None = None
    if source is not None and source.is_file():
        try:
            text = source.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError) as exc:
            print(f"::warning::{source} is unreadable: {' '.join(str(exc).split())[:200]}")
    source_sha = code_sha256(text) if text is not None else None
    static_rec = static_block(static, static_exit)
    smoke_rec = smoke_block(smoke, source_sha)
    status, why = derive_status(str(static_rec["status"]), smoke_rec["status"], smoke_rec["why"])
    record: dict[str, Any] = {
        "v": RECORD_VERSION,
        "side": side,
        "spec": spec,
        "lib": lib,
        "language": language,
        "checker_version": _int_or_none(static_rec.get("version")),
        "status": status,
        "why": why,
        "lines": len(text.splitlines()) if text is not None else None,
        "code_sha256": source_sha,
        "static": static_rec,
        "smoke": smoke_rec,
    }
    if side == "new":
        record["selfcheck"] = selfcheck_block(selfcheck)
    return record


def rule_classes(static: Mapping[str, Any]) -> tuple[list[str], list[str]]:
    """The non-advisory and the advisory rule classes with a finding, each in ``RULE_ORDER``."""
    binding: set[str] = set()
    advisory: set[str] = set()
    findings = static.get("findings")
    for finding in findings if isinstance(findings, list) else []:
        if not isinstance(finding, dict) or finding.get("class") not in RULE_ORDER:
            continue
        (advisory if finding.get("advisory") is True else binding).add(finding["class"])
    return [c for c in RULE_ORDER if c in binding], [c for c in RULE_ORDER if c in advisory]


def _joined(values: Sequence[str]) -> str:
    return ",".join(values) if values else NONE


def notice_line(record: Mapping[str, Any]) -> str:
    """``::notice::adapt_check spec=... lib=... side=... status=... rules=...`` for one record."""
    static = record["static"]
    smoke = record["smoke"]
    binding, advisory = rule_classes(static)
    fields = [
        ("spec", token(record["spec"])),
        ("lib", token(record["lib"])),
        ("side", token(record["side"])),
        ("status", token(record["status"])),
        ("static", token(static.get("status"))),
        ("smoke", token(smoke.get("status"))),
        ("rules", _joined(binding)),
        ("advisory", _joined(advisory)),
        ("perturbations", _joined(smoke.get("failed") or [])),
        ("advisory_perturbations", _joined(smoke.get("advisory_failed") or [])),
        ("version", token(record.get("checker_version"))),
        ("lines", token(record.get("lines"))),
    ]
    if record["side"] == "new":
        selfcheck = record.get("selfcheck")
        if isinstance(selfcheck, dict):
            fields += [
                ("selfcheck_attempts", token(selfcheck.get("attempts"))),
                ("selfcheck_first", token(selfcheck.get("first"))),
            ]
        else:
            fields += [("selfcheck_attempts", "n/a"), ("selfcheck_first", "n/a")]
    fields.append(("why", token(record["why"])))
    return "::notice::adapt_check " + " ".join(f"{key}={value}" for key, value in fields)


def cmd_record(args: argparse.Namespace) -> int:
    record = build_record(
        side=args.side,
        spec=args.spec,
        lib=args.lib,
        language=args.language,
        source=args.source,
        static=args.static,
        static_exit=args.static_exit,
        smoke=args.smoke,
        selfcheck=args.selfcheck,
    )
    try:
        args.out.write_text(json.dumps(record, ensure_ascii=False) + "\n", encoding="utf-8")
    except OSError as exc:
        print(f"::warning::adapt record ({args.side}) not written: {' '.join(str(exc).split())[:200]}")
        return 1
    print(notice_line(record))
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build impl-review's adapt records (record-only).")
    sub = parser.add_subparsers(dest="command", required=True)
    rec = sub.add_parser("record", help="write one side's adapt record and print its notice")
    rec.add_argument("--side", required=True, choices=SIDES)
    rec.add_argument("--spec", required=True)
    rec.add_argument("--lib", required=True)
    rec.add_argument("--language", required=True)
    rec.add_argument("--source", type=Path, required=True, help="the checked implementation file")
    rec.add_argument("--static", type=Path, required=True, help="the mirror's --out file")
    rec.add_argument("--static-exit", type=int, required=True, help="the mirror's exit code")
    rec.add_argument("--smoke", type=Path, default=None, help="the staged smoke-run JSON")
    rec.add_argument("--selfcheck", type=Path, default=None, help="the staged Step 3c log (new side only)")
    rec.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    return cmd_record(args)


if __name__ == "__main__":
    sys.exit(main())
