#!/usr/bin/env python3
"""Regen gate: decide whether a regenerated implementation replaces the live one.

A regeneration (an implementation PR for a (spec, library) pair that already
has an implementation on ``main``) gets exactly one review and no repair loop.
The review scores the new render blind, then re-scores the predecessor's
production renders against the same criteria and writes a pairwise judgement
to ``review_regen.json`` (contract in
``prompts/workflow-prompts/ai-quality-review.md`` step 8b). This script turns
that judgement into a verdict:

- ``merge`` -- the new implementation replaces the live one
  (``impl-review.yml`` adds ``regen:improved`` and then ``ai-approved``).
- ``keep`` -- the PR is closed and the live implementation stays
  (``regen:kept``; never ``ai-rejected``, so no repair and no deletion).

Merge requires ALL of:

1. the canvas gate passed and the new score is a real, non-zero score;
2. the predecessor's production renders were available to the reviewer;
3. ``review_regen.json`` exists and is structurally valid, every ``W`` ref is
   one of the previous review's weakness ids and every ``C`` ref is one of the
   spec's characteristic bullets;
4. ``new_score >= prev_rescored - 1`` (``prev_rescored`` is the predecessor
   re-scored in the same session; the stored score is display-only);
5. at least one improvement with a non-empty ``where_visible`` whose ref is
   not an "Expected, not a defect" bullet (a permission is never an
   improvement; such an improvement is not counted, and the file stays valid);
6. no regressions -- on a ``*-basic`` spec a changed data scenario or added
   encodings count as regressions unless a change request asked for them.

Anything missing or malformed fails closed to ``keep``.

Every decision also carries a machine-readable reason ``code`` (see
``REASON_CODES``) and, with ``--record-out``, a gate record: a one-line JSON
object with scores, counts, codes and provenance, and no model-written text.
``impl-review.yml`` embeds it in the PR comment on both paths as
``<!-- regen-gate-record:v1 {...} -->`` (``marker``), where it outlives the
run log; ``review_retest.py gate-report`` aggregates them with
``parse_record_markers``.

The script is stdlib-only except for the ``context`` subcommand, which needs
PyYAML to read the previous metadata. ``impl-review.yml`` runs it from a copy
taken at the workflow's own ref, so the parser always matches the workflow.

Subcommands::

    regen_gate.py context --metadata META.yaml --spec-id S --language L --library B \
        [--spec-file plots/S/specification.md] \
        [--out-md /tmp/anyplot-prev-review.md] [--out-weaknesses /tmp/anyplot-prev-weaknesses.json]

    regen_gate.py decide --spec-id S --library B --score N --prev-stored N|n/a \
        --regen-json review_regen.json --weaknesses-json /tmp/anyplot-prev-weaknesses.json \
        --spec-file plots/S/specification.md --prev-renders available|missing \
        [--canvas-failed] [--change-request-present] [--context-failed] [--summary-out FILE] \
        [--pr N] [--model ID] [--criteria-version V] [--prompts-tree SHA] \
        [--prev-model ID] [--prev-criteria-version V] [--record-out FILE]

    regen_gate.py sanitize-source --source PREV_IMPL --out /tmp/anyplot-prev-impl.EXT [--pending]

    regen_gate.py marker --record FILE

``context`` and ``decide`` write ``key=value`` outputs to ``$GITHUB_OUTPUT``
when it is set.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


MERGE = "merge"
KEEP = "keep"

# Machine-readable reason codes, one per decision branch. ``script_crashed``
# is written by the workflow's fallback when this script cannot run at all.
REASON_CODES = (
    "canvas_failed",
    "no_score",
    "score_zero",
    "prev_renders_missing",
    "context_failed",
    "regen_json_missing",
    "regen_json_unreadable",
    "regen_json_invalid",
    "regression",
    "no_visible_improvement",
    "below_tolerance",
    "merge",
    "script_crashed",
)

REF_RE = re.compile(r"^(?:(?P<kind>[WPC])(?P<num>[1-9]\d*)|new)$")
CHARACTERISTICS_HEADING_RE = re.compile(r"^##\s+what a good version looks like\b", re.IGNORECASE)
NEXT_SECTION_RE = re.compile(r"^#{1,2}\s")
# Column 0 only. An indented line continues the bullet above it — a wrapped
# line, or a sub-point whose marker is dropped (NESTED_MARKER_RE).
TOP_LEVEL_BULLET_RE = re.compile(r"^(?:[-*+]|\d+[.)])\s+(?P<text>\S.*)$")
NESTED_MARKER_RE = re.compile(r"^(?:[-*+]|\d+[.)])\s+")

# The two kinds of characteristic bullet, each written as the bullet's opening
# words. spec_characteristics_lint.py requires these exact prefixes; the gate
# reads them leniently (any case, optional bold markers) and anchored at the
# start of the bullet, and a bullet without a recognisable prefix counts as
# affirmative, so an older or unlabeled section parses as it always did.
SHOWS_PREFIX = "A good version shows:"
EXPECTED_PREFIX = "Expected, not a defect:"
KIND_SHOWS = "shows"
KIND_EXPECTED = "expected"
_KIND_RES = (
    (KIND_SHOWS, re.compile(r"^\s*[*_]{0,2}\s*a good version shows\s*[*_]{0,2}\s*:", re.IGNORECASE)),
    (KIND_EXPECTED, re.compile(r"^\s*[*_]{0,2}\s*expected,?\s*not a defect\s*[*_]{0,2}\s*:", re.IGNORECASE)),
)


# ---------------------------------------------------------------------------
# Previous review extraction (shared by impl-generate and impl-review)
# ---------------------------------------------------------------------------


def weakness_ids(weaknesses: list[Any]) -> list[dict[str, str]]:
    """Assign stable ids W1..Wn to the previous review's weaknesses, in order."""
    texts = [str(w).strip() for w in weaknesses if str(w).strip()]
    return [{"id": f"W{i}", "text": text} for i, text in enumerate(texts, start=1)]


def parse_characteristics(spec_text: str) -> list[str]:
    """Top-level bullets of the spec's "What a good version looks like" section.

    Ids are C1..Cn in document order. An indented, non-empty line continues the
    bullet above it, across blank lines: a wrapped line is joined with a space,
    a nested sub-point with "; " (its marker dropped). The next ``#``/``##``
    heading ends the section. Whitespace inside a bullet is collapsed, as the
    lint compares it. Returns an empty list when the spec has no section.
    """
    items: list[str] = []
    in_section = False
    for line in spec_text.splitlines():
        if CHARACTERISTICS_HEADING_RE.match(line):
            in_section = True
            continue
        if not in_section:
            continue
        if NEXT_SECTION_RE.match(line):
            break
        m = TOP_LEVEL_BULLET_RE.match(line)
        if m:
            items.append(m.group("text"))
        elif items and line[:1].isspace() and line.strip():
            text = line.strip()
            nested = NESTED_MARKER_RE.match(text)
            items[-1] += f"; {text[nested.end() :]}" if nested else f" {text}"
    return [" ".join(item.split()) for item in items]


def characteristic_kind(text: str) -> str | None:
    """Kind of one characteristic bullet: ``"shows"``, ``"expected"`` or None.

    Only the bullet's opening words count: a bullet that mentions "expected,
    not a defect" mid-sentence is not a permission. None means no recognisable
    prefix, and the gate then reads the bullet as affirmative.
    """
    for kind, pattern in _KIND_RES:
        if pattern.match(text):
            return kind
    return None


def permission_refs(items: list[str]) -> frozenset[str]:
    """C ids of the "Expected, not a defect" bullets — never an improvement ref."""
    return frozenset(f"C{i}" for i, text in enumerate(items, start=1) if characteristic_kind(text) == KIND_EXPECTED)


def render_previous_review(
    data: dict[str, Any],
    spec_id: str,
    language: str,
    library: str,
    characteristics: list[str] | None = None,
    include_scores: bool = True,
) -> tuple[str, list[dict[str, str]]]:
    """Build ``/tmp/anyplot-prev-review.md`` and the id'd weakness list.

    ``include_scores=False`` (impl-review) leaves out the stored total and the
    per-category numbers, so the reviewer's re-score of the predecessor cannot
    anchor on them; the stored score stays in the gate's notice and summary.
    """
    review = data.get("review") or {}
    quality = data.get("quality_score")

    lines = [f"# Previous Review for {spec_id} / {language} / {library}", ""]
    if include_scores:
        lines.append(f"**Previous quality score (stored):** {quality if quality is not None else 'n/a'}")
        lines.append("")

    desc = review.get("image_description")
    if desc:
        lines += ["## Previous image description", str(desc).strip(), ""]

    strengths = review.get("strengths") or []
    if strengths:
        lines.append("## Strengths (KEEP these)")
        lines += [f"- {s}" for s in strengths]
        lines.append("")

    weaknesses = weakness_ids(review.get("weaknesses") or [])
    if weaknesses:
        lines.append("## Weaknesses (FIX these) — stable ids W1..Wn")
        lines += [f"- **{w['id']}:** {w['text']}" for w in weaknesses]
        lines.append("")

    checklist = review.get("criteria_checklist") or {}
    if checklist:
        lines.append("## Criteria checklist (focus on items that failed)")
        for cat, payload in checklist.items():
            payload = payload or {}
            if include_scores:
                lines.append(f"### {cat}  ({payload.get('score', '?')}/{payload.get('max', '?')})")
            else:
                lines.append(f"### {cat}")
            for item in payload.get("items") or []:
                item = item or {}
                mark = "✅" if item.get("passed") else "❌"
                lines.append(f"- {mark} {item.get('id', '?')} {item.get('name', '')}: {item.get('comment', '')}")
            lines.append("")

    if characteristics:
        lines.append(
            '## Characteristic bullets from the spec — stable ids C1..Cn (only "A good version shows" bullets '
            "can be improvement refs)"
        )
        lines += [f"- **C{i}:** {text}" for i, text in enumerate(characteristics, start=1)]
        lines.append("")

    return "\n".join(lines), weaknesses


# One whole header line as impl-review writes it: the language's comment lead
# (none inside a Python docstring, ``#'`` for R, ``#`` for Julia, ``//`` for
# JavaScript), ``Quality: N/100``, then nothing or the ``| Created: …`` /
# ``| Updated: …`` date. Matched against the full line, so a line that only
# mentions a score — ``print('Quality: 50/100 …')``, a sentence in a comment —
# is never rewritten.
QUALITY_HEADER_RE = re.compile(
    r"(?P<head>(?:(?:#'|#|//)[ \t]?)?Quality:[ \t]*)\d{1,3}(?P<scale>[ \t]*/[ \t]*100)"
    r"(?P<tail>[ \t]*(?:\|[ \t]*(?:Created|Updated):.*)?)"
)
HEADER_LINES = 15


def _rewrite_header_score(text: str, template: str) -> str:
    """Apply ``template`` (``QUALITY_HEADER_RE`` groups) to each header line.

    Only the first ``HEADER_LINES`` lines are read; line endings and the line
    count stay as they were.
    """
    lines = text.splitlines(keepends=True)
    for i, line in enumerate(lines[:HEADER_LINES]):
        body = line.rstrip("\r\n")
        match = QUALITY_HEADER_RE.fullmatch(body)
        if match:
            lines[i] = match.expand(template) + line[len(body) :]
    return "".join(lines)


def sanitize_source(text: str) -> str:
    """Hide the stored score in the generated file header of the predecessor.

    impl-review writes ``Quality: N/100`` into every implementation's header
    (docstring for Python, ``#'`` for R, ``#`` for Julia, ``//`` for
    JavaScript). The copy handed to the reviewer must not reveal N before the
    predecessor is re-scored, so the value becomes ``hidden`` — only on a
    whole header line (``QUALITY_HEADER_RE``) in the leading ``HEADER_LINES``
    lines, and the line count stays the same.
    """
    return _rewrite_header_score(text, r"\g<head>hidden\g<scale>\g<tail>")


def reset_header_score(text: str) -> str:
    """Turn ``Quality: N/100`` back into ``Quality: pending`` (M3).

    A regeneration edits the live file, so its header still carries the
    predecessor's stored score, and the review would score the new version
    with that number in plain sight. ``impl-generate.yml`` resets it before
    the PR opens, the way a fresh file starts (``prompts/plot-generator.md``:
    ``Quality: pending``). Same scope as ``sanitize_source``: whole header
    lines in the leading lines only, line count unchanged.
    """
    return _rewrite_header_score(text, r"\g<head>pending\g<tail>")


# ---------------------------------------------------------------------------
# Decision
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class GateInput:
    spec_id: str
    score: int | None
    regen: Any
    regen_error: str | None = None
    known_weakness_ids: frozenset[str] = frozenset()
    characteristic_count: int = 0
    # C ids of the spec's "Expected, not a defect" bullets (permission_refs()).
    permission_refs: frozenset[str] = frozenset()
    prev_renders: bool = True
    canvas_failed: bool = False
    change_request_present: bool = False
    context_ok: bool = True


@dataclass
class GateResult:
    verdict: str
    reason: str
    code: str = ""
    prev_rescored: int | None = None
    improvements: list[dict[str, str]] = field(default_factory=list)
    regressions: list[dict[str, str]] = field(default_factory=list)
    # Improvements whose ref is in here were listed but not counted.
    permission_refs: frozenset[str] = frozenset()
    # Filled once review_regen.json validated; None before that.
    scenario_changed: bool | None = None
    encodings_added: int | None = None
    coerced: bool = False


def _is_int(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def normalize_regen(payload: Any) -> tuple[Any, list[str]]:
    """Coerce predictable model slips; every coercion is recorded for the reason.

    Only unambiguous slips are repaired: a digit-string ``prev_rescored``,
    lower-case refs (``w2``), missing ``regressions`` / ``encodings_added``
    (read as empty) and ``"n/a"`` / ``"null"`` for ``change_request_applied``.
    Anything else is left for ``validate_regen`` to reject.
    """
    if not isinstance(payload, dict):
        return payload, []
    data = dict(payload)
    notes: list[str] = []

    prev = data.get("prev_rescored")
    if isinstance(prev, str) and re.fullmatch(r"\s*\d{1,3}\s*", prev):
        data["prev_rescored"] = int(prev)
        notes.append(f"prev_rescored {prev!r} -> {int(prev)}")

    for key in ("regressions", "encodings_added"):
        if key not in data:
            data[key] = []
            notes.append(f"missing {key} -> []")

    applied = data.get("change_request_applied")
    if isinstance(applied, str) and applied.strip().lower() in {"n/a", "na", "null", "none", ""}:
        data["change_request_applied"] = None
        notes.append(f"change_request_applied {applied!r} -> null")

    improvements = data.get("improvements")
    if isinstance(improvements, list):
        fixed = []
        for item in improvements:
            ref = item.get("ref") if isinstance(item, dict) else None
            if isinstance(ref, str):
                canonical = _canonical_ref(ref)
                if canonical != ref and REF_RE.match(canonical):
                    notes.append(f"ref {ref!r} -> {canonical!r}")
                    item = {**item, "ref": canonical}
            fixed.append(item)
        data["improvements"] = fixed

    return data, notes


def _canonical_ref(ref: str) -> str:
    ref = ref.strip()
    return "new" if ref.lower() == "new" else ref.upper()


def validate_regen(payload: Any, known_weakness_ids: frozenset[str], characteristic_count: int) -> list[str]:
    """Structural and id validation of ``review_regen.json``. Returns error strings."""
    if not isinstance(payload, dict):
        return ["top level is not a JSON object"]
    errors: list[str] = []

    prev = payload.get("prev_rescored")
    if not _is_int(prev) or not 0 <= prev <= 100:
        errors.append(f"prev_rescored must be an integer 0-100 (got {prev!r})")

    improvements = payload.get("improvements")
    if not isinstance(improvements, list):
        errors.append("improvements must be a list")
    else:
        for i, item in enumerate(improvements, start=1):
            if not isinstance(item, dict):
                errors.append(f"improvements[{i}] is not an object")
                continue
            ref = item.get("ref")
            m = REF_RE.match(ref) if isinstance(ref, str) else None
            if m is None:
                errors.append(f"improvements[{i}].ref {ref!r} is not W<n>, P<n>, C<n> or 'new'")
            elif m.group("kind") == "W" and ref not in known_weakness_ids:
                errors.append(f"improvements[{i}].ref {ref} is not a weakness id of the previous review")
            elif m.group("kind") == "C" and int(m.group("num")) > characteristic_count:
                errors.append(
                    f"improvements[{i}].ref {ref} does not exist (the spec lists {characteristic_count} characteristic bullets)"
                )
            if not isinstance(item.get("what"), str) or not item["what"].strip():
                errors.append(f"improvements[{i}].what must be a non-empty string")
            if "where_visible" in item and not isinstance(item["where_visible"], str):
                errors.append(f"improvements[{i}].where_visible must be a string")

    regressions = payload.get("regressions")
    if not isinstance(regressions, list):
        errors.append("regressions must be a list")
    else:
        for i, item in enumerate(regressions, start=1):
            if not isinstance(item, dict) or not isinstance(item.get("what"), str) or not item["what"].strip():
                errors.append(f"regressions[{i}] must be an object with a non-empty 'what'")

    if not isinstance(payload.get("scenario_changed"), bool):
        errors.append("scenario_changed must be true or false")

    encodings = payload.get("encodings_added")
    if not isinstance(encodings, list) or not all(isinstance(e, str) for e in encodings):
        errors.append("encodings_added must be a list of strings")

    applied = payload.get("change_request_applied")
    if applied is not None and not isinstance(applied, bool):
        errors.append("change_request_applied must be true, false or null")

    return errors


def decide(inp: GateInput) -> GateResult:
    """Apply the regen gate. Every uncertain input resolves to ``keep``."""
    if inp.canvas_failed:
        return GateResult(KEEP, "canvas dimension gate failed", "canvas_failed")
    if inp.score is None:
        return GateResult(KEEP, "no valid review score", "no_score")
    if inp.score == 0:
        return GateResult(KEEP, "new render scored 0 (auto-reject)", "score_zero")
    if not inp.prev_renders:
        return GateResult(
            KEEP, "previous production renders unavailable, no before/after comparison possible", "prev_renders_missing"
        )
    if not inp.context_ok:
        return GateResult(
            KEEP, "regen context extraction failed (previous review not available to the reviewer)", "context_failed"
        )
    if inp.regen is None:
        error = inp.regen_error or "missing"
        code = "regen_json_missing" if error == "missing" else "regen_json_unreadable"
        return GateResult(KEEP, f"review_regen.json {error}", code)

    regen, coerced = normalize_regen(inp.regen)
    result = _judge(inp, regen)
    if coerced:
        result.reason += f" (coerced: {'; '.join(coerced)})"
        result.coerced = True
    return result


def _judge(inp: GateInput, regen: Any) -> GateResult:
    errors = validate_regen(regen, inp.known_weakness_ids, inp.characteristic_count)
    if errors:
        return GateResult(KEEP, "invalid review_regen.json: " + "; ".join(errors), "regen_json_invalid")

    payload: dict[str, Any] = regen
    prev_rescored: int = payload["prev_rescored"]
    improvements = [
        {
            "ref": item["ref"],
            "what": item["what"].strip(),
            "where_visible": str(item.get("where_visible") or "").strip(),
        }
        for item in payload["improvements"]
    ]
    regressions = [
        {"what": item["what"].strip(), "where_visible": str(item.get("where_visible") or "").strip()}
        for item in payload["regressions"]
    ]

    # A change request is the only thing that may legitimately swap the
    # scenario or add encodings on a -basic spec — and only one that exists.
    change_request_applied = inp.change_request_present and payload.get("change_request_applied") is True
    if inp.spec_id.endswith("-basic") and not change_request_applied:
        if payload["scenario_changed"]:
            regressions.append(
                {"what": "data scenario replaced on a -basic spec", "where_visible": "data and labels of both renders"}
            )
        encodings = [e.strip() for e in payload["encodings_added"] if e.strip()]
        if encodings:
            regressions.append(
                {"what": f"encodings added on a -basic spec: {', '.join(encodings)}", "where_visible": "both renders"}
            )

    result = GateResult(
        KEEP,
        "",
        prev_rescored=prev_rescored,
        improvements=improvements,
        regressions=regressions,
        permission_refs=inp.permission_refs,
        scenario_changed=bool(payload["scenario_changed"]),
        encodings_added=len([e for e in payload["encodings_added"] if e.strip()]),
    )

    if regressions:
        result.code = "regression"
        result.reason = f"{len(regressions)} regression(s): " + "; ".join(r["what"] for r in regressions)
        return result

    # A permission ("Expected, not a defect") is never an improvement: the
    # item is not counted, but the rest of the file still is.
    counted = [i for i in improvements if i["ref"] not in inp.permission_refs]
    cited = sorted({i["ref"] for i in improvements if i["ref"] in inp.permission_refs}, key=lambda ref: int(ref[1:]))
    note = ""
    if cited:
        bullets = "bullet" if len(cited) == 1 else "bullets"
        note = f" ({', '.join(cited)} = 'Expected, not a defect' {bullets}, not counted as an improvement)"

    visible = [i for i in counted if i["where_visible"]]
    if not visible:
        detail = " (every improvement needs a non-empty where_visible)" if counted or not cited else ""
        result.code = "no_visible_improvement"
        result.reason = f"no visible improvement{detail}{note}"
        return result

    if inp.score < prev_rescored - 1:
        result.code = "below_tolerance"
        result.reason = f"new score {inp.score} < re-scored predecessor {prev_rescored} - 1{note}"
        return result

    result.verdict = MERGE
    result.code = "merge"
    result.reason = (
        f"{len(visible)} visible improvement(s), no regressions, new score {inp.score} >= "
        f"re-scored predecessor {prev_rescored} - 1{note}"
    )
    return result


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def _write_outputs(values: dict[str, str]) -> None:
    for key, value in values.items():
        print(f"{key}={value}")
    path = os.environ.get("GITHUB_OUTPUT")
    if path:
        with open(path, "a", encoding="utf-8") as f:
            for key, value in values.items():
                f.write(f"{key}={value}\n")


def _one_line(text: str) -> str:
    return " ".join(str(text).split())


def _safe(text: str) -> str:
    """Model-written text for a GitHub comment: one line, no @-mentions.

    A zero-width space after every ``@`` keeps the text readable while GitHub
    no longer resolves it as a user or team mention.
    """
    return _one_line(text).replace("@", "@​")


def load_regen_json(path: Path) -> tuple[Any, str | None]:
    if not path.is_file():
        return None, "missing"
    try:
        return json.loads(path.read_text(encoding="utf-8")), None
    except (OSError, ValueError) as exc:
        return None, f"unreadable ({_one_line(str(exc))[:200]})"


def load_known_weakness_ids(path: Path | None) -> frozenset[str]:
    if path is None or not path.is_file():
        return frozenset()
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return frozenset()
    if not isinstance(data, list):
        return frozenset()
    return frozenset(str(item["id"]) for item in data if isinstance(item, dict) and "id" in item)


def parse_score(raw: str | None) -> int | None:
    if raw is None or not re.fullmatch(r"\d{1,3}", raw.strip()):
        return None
    value = int(raw.strip())
    return value if value <= 100 else None


def render_summary(result: GateResult, prev_stored: str, score: int | None) -> str:
    """Markdown block for the PR/issue comment (improvements, regressions, reason)."""
    rescored = str(result.prev_rescored) if result.prev_rescored is not None else "n/a"
    lines = [
        "| Previous (stored) | Previous (re-scored) | New |",
        "|---|---|---|",
        f"| {prev_stored} | {rescored} | {score if score is not None else 'n/a'} |",
        "",
        "**Improvements**",
    ]
    if result.improvements:
        for item in result.improvements:
            where = _safe(item["where_visible"]) if item["where_visible"] else "_not visible_"
            flag = " _(permission, not counted)_" if item["ref"] in result.permission_refs else ""
            lines.append(f"- `{item['ref']}` {_safe(item['what'])} — {where}{flag}")
    else:
        lines.append("- none")
    lines += ["", "**Regressions**"]
    if result.regressions:
        for item in result.regressions:
            where = f" — {_safe(item['where_visible'])}" if item["where_visible"] else ""
            lines.append(f"- {_safe(item['what'])}{where}")
    else:
        lines.append("- none")
    lines += ["", f"**Reason:** {_safe(result.reason)}"]
    return "\n".join(lines) + "\n"


# ---------------------------------------------------------------------------
# Gate record (machine-readable, no model-written text)
# ---------------------------------------------------------------------------

RECORD_VERSION = 1
RECORD_MARKER = "regen-gate-record:v1"
RECORD_MARKER_RE = re.compile(r"<!-- regen-gate-record:v1 (\{[^\n]*?\}) -->")
# Every string in a record is an identifier from the workflow (spec, library,
# model id, rules version, timestamp) or a fixed code — never review prose.
RECORD_TOKEN_RE = re.compile(r"^[A-Za-z0-9._:/\[\]-]*$")
RECORD_KEYS = frozenset(
    {
        "v",
        "pr",
        "spec",
        "lib",
        "model",
        "criteria_version",
        "prompts_tree",
        "prev_model",
        "prev_criteria_version",
        "prev_stored",
        "prev_rescored",
        "new",
        "verdict",
        "code",
        "improvements",
        "regressions",
        "scenario_changed",
        "encodings_added",
        "coerced",
        "at",
    }
)


def record_token(value: Any, limit: int = 100) -> str:
    """A workflow-supplied identifier reduced to a safe token (``n/a`` when empty).

    Runs of ``-`` collapse to one, so a record can always sit inside an HTML
    comment (``--`` would end it early).
    """
    if value is None:
        return "n/a"
    text = re.sub(r"[^A-Za-z0-9._:/\[\]-]", "", str(value).strip())[:limit]
    text = re.sub(r"-{2,}", "-", text)
    return text or "n/a"


def _ref_kind(ref: str) -> str:
    return "new" if ref == "new" else ref[:1]


def build_record(
    result: GateResult,
    *,
    spec_id: str,
    library: str,
    score: int | None,
    prev_stored: int | None,
    pr: int | None = None,
    model: str | None = None,
    criteria_version: str | None = None,
    prompts_tree: str | None = None,
    prev_model: str | None = None,
    prev_criteria_version: str | None = None,
    at: str | None = None,
) -> dict[str, Any]:
    """The gate record: scores, counts, codes and provenance — nothing a model wrote.

    ``improvements`` counts what the review listed: ``total`` and the per-kind
    counts (``W``/``P``/``C``/``new``) cover every listed item, ``permission``
    the items that cite an "Expected, not a defect" bullet, and ``visible`` only
    the counted ones (not a permission) with a non-empty ``where_visible`` —
    the number the gate decided on.
    """
    kinds = {"W": 0, "P": 0, "C": 0, "new": 0}
    for item in result.improvements:
        kind = _ref_kind(item["ref"])
        if kind in kinds:
            kinds[kind] += 1
    counted = [i for i in result.improvements if i["ref"] not in result.permission_refs]
    return {
        "v": RECORD_VERSION,
        "pr": pr,
        "spec": record_token(spec_id),
        "lib": record_token(library),
        "model": record_token(model),
        "criteria_version": record_token(criteria_version, limit=200),
        "prompts_tree": record_token(prompts_tree),
        "prev_model": record_token(prev_model),
        "prev_criteria_version": record_token(prev_criteria_version, limit=200),
        "prev_stored": prev_stored,
        "prev_rescored": result.prev_rescored,
        "new": score,
        "verdict": result.verdict,
        "code": result.code,
        "improvements": {
            "total": len(result.improvements),
            "visible": len([i for i in counted if i["where_visible"]]),
            **kinds,
            "permission": len(result.improvements) - len(counted),
        },
        "regressions": len(result.regressions),
        "scenario_changed": result.scenario_changed,
        "encodings_added": result.encodings_added,
        "coerced": result.coerced,
        "at": at or datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }


def validate_record(record: Any) -> list[str]:
    """Schema check for a gate record. Returns error strings.

    Known keys only, no free text anywhere, and a ``v`` / ``verdict`` /
    ``code`` this module can have written: ``RECORD_VERSION``, ``MERGE`` or
    ``KEEP``, and one of ``REASON_CODES``.
    """
    if not isinstance(record, dict):
        return ["record is not a JSON object"]
    errors = [f"unknown key {key!r}" for key in record if key not in RECORD_KEYS]
    for missing in ("v", "spec", "lib", "verdict", "code"):
        if missing not in record:
            errors.append(f"missing key {missing!r}")
    if "v" in record and not (_is_int(record["v"]) and record["v"] == RECORD_VERSION):
        errors.append(f"record.v must be {RECORD_VERSION}")
    if "verdict" in record and record["verdict"] not in (MERGE, KEEP):
        errors.append(f"record.verdict must be {MERGE!r} or {KEEP!r}")
    if "code" in record and not (isinstance(record["code"], str) and record["code"] in REASON_CODES):
        errors.append("record.code is not one of REASON_CODES")

    def walk(value: Any, where: str) -> None:
        if isinstance(value, dict):
            for key, inner in value.items():
                walk(inner, f"{where}.{key}")
        elif isinstance(value, str) and not RECORD_TOKEN_RE.fullmatch(value):
            errors.append(f"{where} is not a plain token")
        elif value is not None and not isinstance(value, str | int | float | bool | dict):
            errors.append(f"{where} has an unsupported type")

    walk(record, "record")
    return errors


def render_record_marker(record: dict[str, Any]) -> str:
    """``<!-- regen-gate-record:v1 {json} -->`` for a PR comment.

    Raises ``ValueError`` when the record is not a clean record or its JSON
    would close the HTML comment early.
    """
    errors = validate_record(record)
    if errors:
        raise ValueError("invalid gate record: " + "; ".join(errors))
    payload = json.dumps(record, separators=(",", ":"), ensure_ascii=True)
    if "--" in payload:
        raise ValueError("gate record contains '--' and would break the HTML comment")
    return f"<!-- {RECORD_MARKER} {payload} -->"


def parse_record_markers(text: str) -> list[dict[str, Any]]:
    """Every valid gate record embedded in a comment body, in order.

    A marker whose JSON does not parse or fails ``validate_record`` (a foreign
    version, an unknown verdict or code, free text) is skipped.
    """
    records: list[dict[str, Any]] = []
    for match in RECORD_MARKER_RE.finditer(text or ""):
        try:
            record = json.loads(match.group(1))
        except ValueError:
            continue
        if not validate_record(record):
            records.append(record)
    return records


def cmd_context(args: argparse.Namespace) -> int:
    import yaml  # PyYAML — only this subcommand needs it

    data = yaml.safe_load(Path(args.metadata).read_text(encoding="utf-8")) or {}
    characteristics: list[str] = []
    if args.spec_file and Path(args.spec_file).is_file():
        characteristics = parse_characteristics(Path(args.spec_file).read_text(encoding="utf-8"))
    md, weaknesses = render_previous_review(
        data, args.spec_id, args.language, args.library, characteristics, include_scores=not args.omit_scores
    )
    Path(args.out_md).write_text(md, encoding="utf-8")
    Path(args.out_weaknesses).write_text(json.dumps(weaknesses, indent=2, ensure_ascii=False), encoding="utf-8")
    quality = data.get("quality_score")
    stored = str(quality) if _is_int(quality) else "n/a"
    # Provenance of the stored review, so a gate decision can later be told
    # apart as comparable (same model, same rules) or not. Older metadata has
    # neither key.
    raw_review = data.get("review")
    review: dict[str, Any] = raw_review if isinstance(raw_review, dict) else {}
    _write_outputs(
        {
            "prev_stored": stored,
            "weakness_count": str(len(weaknesses)),
            "characteristic_count": str(len(characteristics)),
            "prev_model": record_token(review.get("model")),
            "prev_criteria_version": record_token(review.get("criteria_version"), limit=200),
        }
    )
    return 0


def _optional_int(raw: str | None) -> int | None:
    if raw is None or not re.fullmatch(r"\s*\d+\s*", raw):
        return None
    return int(raw)


def cmd_decide(args: argparse.Namespace) -> int:
    regen, regen_error = load_regen_json(Path(args.regen_json))
    characteristics: list[str] = []
    if args.spec_file and Path(args.spec_file).is_file():
        characteristics = parse_characteristics(Path(args.spec_file).read_text(encoding="utf-8"))
    score = parse_score(args.score)
    inp = GateInput(
        spec_id=args.spec_id,
        score=score,
        regen=regen,
        regen_error=regen_error,
        known_weakness_ids=load_known_weakness_ids(Path(args.weaknesses_json) if args.weaknesses_json else None),
        characteristic_count=len(characteristics),
        permission_refs=permission_refs(characteristics),
        prev_renders=args.prev_renders == "available",
        canvas_failed=args.canvas_failed,
        change_request_present=args.change_request_present,
        context_ok=not args.context_failed,
    )
    result = decide(inp)
    rescored = str(result.prev_rescored) if result.prev_rescored is not None else "n/a"
    reason = _one_line(result.reason)
    # The stable prefix (spec … verdict) is what readers match on; the new
    # fields sit before `reason=`, which stays last and runs to the line end.
    provenance = ""
    if args.model:
        provenance += f" model={record_token(args.model)}"
    if args.criteria_version:
        provenance += f" criteria={record_token(args.criteria_version, limit=200)}"
    print(
        f"::notice::regen_gate spec={args.spec_id} lib={args.library} prev_stored={args.prev_stored} "
        f"prev_rescored={rescored} new={score if score is not None else 'n/a'} verdict={result.verdict} "
        f"code={result.code}{provenance} reason={reason}"
    )
    if args.summary_out:
        Path(args.summary_out).write_text(render_summary(result, args.prev_stored, score), encoding="utf-8")
    if args.record_out:
        # The record is monitoring only: a failure to build or write it must
        # never reach the workflow's crash fallback, which would turn a
        # legitimate merge into keep/script_crashed.
        try:
            record = build_record(
                result,
                spec_id=args.spec_id,
                library=args.library,
                score=score,
                prev_stored=parse_score(args.prev_stored),
                pr=_optional_int(args.pr),
                model=args.model or None,
                criteria_version=args.criteria_version or None,
                prompts_tree=args.prompts_tree or None,
                prev_model=args.prev_model or None,
                prev_criteria_version=args.prev_criteria_version or None,
            )
            Path(args.record_out).write_text(json.dumps(record, separators=(",", ":")) + "\n", encoding="utf-8")
        except Exception as exc:
            print(f"::warning::regen gate record not written: {_one_line(str(exc))[:200]}")
    _write_outputs({"verdict": result.verdict, "reason": reason, "prev_rescored": rescored, "code": result.code})
    return 0


def cmd_sanitize_source(args: argparse.Namespace) -> int:
    text = Path(args.source).read_text(encoding="utf-8")
    rewrite = reset_header_score if args.pending else sanitize_source
    Path(args.out).write_text(rewrite(text), encoding="utf-8")
    return 0


def cmd_marker(args: argparse.Namespace) -> int:
    try:
        record = json.loads(Path(args.record).read_text(encoding="utf-8"))
        print(render_record_marker(record))
    except (OSError, ValueError) as exc:
        print(f"no gate record marker: {_one_line(str(exc))[:200]}", file=sys.stderr)
        return 1
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0] if __doc__ else None)
    sub = parser.add_subparsers(dest="command", required=True)

    ctx = sub.add_parser("context", help="Extract the previous review with stable weakness ids")
    ctx.add_argument("--metadata", required=True)
    ctx.add_argument("--spec-id", required=True)
    ctx.add_argument("--language", required=True)
    ctx.add_argument("--library", required=True)
    ctx.add_argument("--spec-file", default="")
    ctx.add_argument("--omit-scores", action="store_true", help="leave stored scores out of the markdown (review)")
    ctx.add_argument("--out-md", default="/tmp/anyplot-prev-review.md")
    ctx.add_argument("--out-weaknesses", default="/tmp/anyplot-prev-weaknesses.json")
    ctx.set_defaults(func=cmd_context)

    san = sub.add_parser("sanitize-source", help="Hide the stored score in a source file's generated header")
    san.add_argument("--source", required=True)
    san.add_argument("--out", required=True, help="may equal --source (rewrite in place)")
    san.add_argument(
        "--pending", action="store_true", help="write 'Quality: pending' instead of 'hidden' (impl-generate, M3)"
    )
    san.set_defaults(func=cmd_sanitize_source)

    mark = sub.add_parser("marker", help="Print the PR-comment marker for a gate record written by --record-out")
    mark.add_argument("--record", required=True)
    mark.set_defaults(func=cmd_marker)

    dec = sub.add_parser("decide", help="Apply the regen gate to review_regen.json")
    dec.add_argument("--spec-id", required=True)
    dec.add_argument("--library", required=True)
    dec.add_argument("--score", default="")
    dec.add_argument("--prev-stored", default="n/a")
    dec.add_argument("--regen-json", default="review_regen.json")
    dec.add_argument("--weaknesses-json", default="/tmp/anyplot-prev-weaknesses.json")
    dec.add_argument("--spec-file", default="")
    dec.add_argument("--prev-renders", choices=["available", "missing"], default="missing")
    dec.add_argument("--canvas-failed", action="store_true")
    dec.add_argument("--change-request-present", action="store_true")
    dec.add_argument("--context-failed", action="store_true")
    dec.add_argument("--summary-out", default="")
    # Provenance for the notice line and the gate record; all optional, so
    # older callers (the retest harness at any rules_ref) keep working.
    dec.add_argument("--pr", default="")
    dec.add_argument("--model", default="", help="resolved model id of the review session")
    dec.add_argument("--criteria-version", default="", help="review_provenance.py criteria-version")
    dec.add_argument("--prompts-tree", default="", help="git tree id of the prompts/ the reviewer read")
    dec.add_argument("--prev-model", default="", help="context's prev_model")
    dec.add_argument("--prev-criteria-version", default="", help="context's prev_criteria_version")
    dec.add_argument("--record-out", default="", help="write the gate record (one-line JSON) here")
    dec.set_defaults(func=cmd_decide)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    sys.exit(main())
