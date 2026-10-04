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
   neither an "Expected, not a defect" bullet (a permission is never an
   improvement) nor a previous weakness the re-score classed ``obsolete``
   (one such a bullet covers); such an item is not counted, and the file
   stays valid;
6. at least one of those visible improvements is a *carrier*: an affirmative
   ``C`` ref, or a ``W`` classed ``defect`` / a ``P`` or ``new`` item whose
   ``rule`` verifies -- a VQ, SC, DQ or CQ criterion other than DQ-01 the new
   render scores higher on (``review_checklist.json`` next to
   ``review_regen.json``) than the re-score did (``prev_checklist``), an
   affirmative ``C`` id, or ``AR-06``..``AR-09`` while ``prev_rescored`` is
   0 -- and whose ``kind`` is ``fix`` or ``removal``. Suggestions, unverified
   claims, design, library-mastery and feature-coverage (DQ-01) points,
   additions, polish and items without a kind ride along but never carry a
   merge alone (``classify_improvements``); 5 and 6 are also met, with no
   carrier, by a counted *code improvement* (``classify_code_improvements``):
   a previous CQ-04 ``(code)`` defect line the re-score classed ``defect``,
   fixed with the named call or removal in a shorter source, with the data
   scenario and encodings unchanged (``decide --prev-impl/--new-impl``);
7. no regressions -- on a ``*-basic`` spec a changed data scenario or added
   encodings count as regressions unless a change request asked for them.

Anything missing or malformed fails closed to ``keep``. The classification
keys (``prev_checklist``, ``prev_weaknesses``, ``rule``, ``kind``) never
invalidate the file: a missing or malformed one only leaves fewer carriers.

Stored weaknesses come in two formats (``weakness_class``): a *defect* line
``<ID>[, <ID>] (<light|dark|both|code>): …`` naming the criterion it violates,
and a ``Suggestion: …`` line. Anything else is a *legacy* line from an older
review.

Every decision also carries a machine-readable reason ``code`` (see
``REASON_CODES``) and, with ``--record-out``, a gate record: a one-line JSON
object with scores, counts, codes and provenance, and no model-written text.
``impl-review.yml`` embeds it in the PR comment on both paths as
``<!-- regen-gate-record:v1 {...} -->`` (``marker``), where it outlives the
run log; ``review_retest.py gate-report`` aggregates them with
``parse_record_markers``. On a keep the record also carries ``writeback``
(``WRITEBACK_CODES``): what happened to the session's re-score of the live
implementation, which ``regen_writeback.py`` stores as its review; that
file's checks (``check_prev_review``) live here, so the review's step-10
self-check (``check-feedback --prev-review``) runs the same code.

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
        [--prev-model ID] [--prev-criteria-version V] [--record-out FILE] \
        [--prev-impl /tmp/anyplot-prev-impl.EXT --new-impl plots/S/implementations/L/B.EXT]

    regen_gate.py sanitize-source --source PREV_IMPL --out /tmp/anyplot-prev-impl.EXT [--pending]

    regen_gate.py marker --record FILE

    regen_gate.py nothing-to-repair --score N [--checklist review_checklist.json] \
        [--weaknesses review_weaknesses.json]

    regen_gate.py check-feedback [--weaknesses review_weaknesses.json] --checklist review_checklist.json \
        [--regen review_regen.json --prev-weaknesses /tmp/anyplot-prev-weaknesses.json \
         --spec-file plots/S/specification.md [--prev-review review_prev.json]] [--warn-only]

``context`` and ``decide`` write ``key=value`` outputs to ``$GITHUB_OUTPUT``
when it is set. ``decide`` reads the new render's ``review_checklist.json``
from the directory of ``--regen-json``. ``check-feedback`` is the review's
self-check (step 10 of the review prompt) and the workflow's warn-only format
check: one line per problem, exit 1 when there is any (``--warn-only``:
``::warning::`` annotations plus a ``weakness_format`` notice, exit 0).
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from collections.abc import Mapping, Sequence
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
    "no_defect_improvement",
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

# The 24 rubric criteria and their maxima (prompts/quality-criteria.md, the
# step 7 tables of prompts/workflow-prompts/ai-quality-review.md).
CRITERIA: dict[str, int] = {
    "VQ-01": 8,
    "VQ-02": 6,
    "VQ-03": 6,
    "VQ-04": 2,
    "VQ-05": 4,
    "VQ-06": 2,
    "VQ-07": 2,
    "DE-01": 8,
    "DE-02": 6,
    "DE-03": 6,
    "SC-01": 5,
    "SC-02": 4,
    "SC-03": 3,
    "SC-04": 3,
    "DQ-01": 6,
    "DQ-02": 5,
    "DQ-03": 4,
    "CQ-01": 3,
    "CQ-02": 2,
    "CQ-03": 2,
    "CQ-04": 2,
    "CQ-05": 1,
    "LM-01": 5,
    "LM-02": 5,
}
# Criteria whose verified fix can carry a regeneration. DE and LM never do:
# stored reviews deduct DE-01..03 and LM-02 in 96-100 % of cases, so no score
# delta tells a fix from a taste change there; they ride along instead. DQ-01
# (feature coverage) rides along for the same reason: Opus deducts it in 65-98 %
# of reviews, and what a regeneration must show is SC-02 or an affirmative C id.
CARRIER_CRITERIA = frozenset(c for c in CRITERIA if c[:2] in {"VQ", "SC", "DQ", "CQ"} and c != "DQ-01")
# The AI-judged auto-reject checks a defect line may name besides the criteria.
AR_IDS = ("AR-06", "AR-07", "AR-08", "AR-09")

# Weakness line formats. The class is the format, so the stored text carries it.
DEFECT = "defect"
SUGGESTION = "suggestion"
LEGACY = "legacy"
OBSOLETE = "obsolete"
# Not a line class: a technical item below its maximum that no defect line names.
SILENT = "silent"
# The criteria whose every deduction a defect line carries (70 of 100 points);
# DE and LM are judgments that start at a default.
TECHNICAL_PREFIXES = ("VQ", "SC", "DQ", "CQ")
# The lowest score a first-generation review with nothing to repair is
# approved at (impl-review.yml's threshold after one repair).
NOTHING_TO_REPAIR_MIN = 80
# Classes the re-score may give a previous weakness (8b, ``prev_weaknesses``).
RESCORE_CLASSES = (DEFECT, SUGGESTION, OBSOLETE)
_DEFECT_ID = r"(?:VQ|DE|SC|DQ|CQ|LM|AR)-\d{2}"
# Prefix only: ``<ID>[, <ID>] (<light|dark|both|code>): <text>``. An unknown ID
# still reads as a defect line; check-feedback reports it.
DEFECT_RE = re.compile(rf"^(?P<ids>{_DEFECT_ID}(?:, {_DEFECT_ID})*) \((?P<render>light|dark|both|code)\): \S")
SUGGESTION_RE = re.compile(r"^Suggestion: \S")
MAX_SUGGESTIONS = 3
C_REF_RE = re.compile(r"^C(?P<num>[1-9]\d*)$")

# The six categories of review_checklist.json (step 10 of the review prompt)
# and the criterion prefix each one holds; a category's maximum is the sum of
# its criteria (30/20/15/15/10/10).
CHECKLIST_CATEGORIES: dict[str, str] = {
    "visual_quality": "VQ",
    "design_excellence": "DE",
    "spec_compliance": "SC",
    "data_quality": "DQ",
    "code_quality": "CQ",
    "library_mastery": "LM",
}
CATEGORY_MAX: dict[str, int] = {
    key: sum(top for cid, top in CRITERIA.items() if cid.startswith(f"{prefix}-"))
    for key, prefix in CHECKLIST_CATEGORIES.items()
}
REVIEW_VERDICTS = ("APPROVED", "REJECTED")


def weakness_class(text: Any) -> str:
    """``defect``, ``suggestion`` or ``legacy`` (any other line, blank included)."""
    line = str(text or "").strip()
    if DEFECT_RE.match(line):
        return DEFECT
    if SUGGESTION_RE.match(line):
        return SUGGESTION
    return LEGACY


def defect_ids(text: Any) -> list[str]:
    """The IDs a defect line names, in order; empty for any other line."""
    m = DEFECT_RE.match(str(text or "").strip())
    return m.group("ids").split(", ") if m else []


# The code-only path (``_code_path``): a CQ-04 defect line the previous review
# named, fixed in the source alone. Its target — the text after the arrow, up
# to "Likely cause:" (``defect_target``) — names the replacement call in
# backticks, or "remove".
CODE_RULE = "CQ-04"
_LIKELY_CAUSE_RE = re.compile(r"\bLikely cause:")
_BACKTICK_RE = re.compile(r"`([^`]+)`")
_CALL_NAME_RE = re.compile(r"^[A-Za-z_][\w.:]*!?$")
_CALL_RE = re.compile(r"([A-Za-z_][\w!]*)\s*\(")
# Sources larger than this are not read (--prev-impl/--new-impl); the code path is then off.
SOURCE_LIMIT = 1_000_000


def is_cq04_code_defect(text: Any) -> bool:
    """A defect line (``DEFECT_RE``) that names ``CQ-04`` with the render tag ``code``."""
    m = DEFECT_RE.match(str(text or "").strip())
    return m is not None and CODE_RULE in m.group("ids").split(", ") and m.group("render") == "code"


def defect_target(text: Any) -> str:
    """What a defect line asks for: the text after its first arrow, without the "Likely cause:" part.

    The arrow is the first ``→``; only a line without one falls back to the
    first ``->``, which a description may contain (``x -> x^2``, an R pipe).
    """
    line = str(text or "")
    arrow = "→" if "→" in line else "->"
    if arrow not in line:
        return ""
    target = line.split(arrow, 1)[1]
    return _LIKELY_CAUSE_RE.split(target, maxsplit=1)[0].strip()


def replacement_tokens(text: Any) -> list[str]:
    """The call names a defect line's target names in backticks, in order.

    A span with calls yields every name called at its top level (not inside
    another call's arguments), each the last component split on ``.`` and
    ``::``: `` `acf(series, nlags=35)` `` → ``acf``, `` `stats::acf()` `` →
    ``acf``, `` `density!(ax, x)` `` → ``density!``, `` `d3.bin()` `` → ``bin``,
    `` `df["v"].rolling(7).mean()` `` → ``rolling``, ``mean``. A span without
    a call yields its last component when it is a bare name
    (`` `scipy.stats.gaussian_kde` `` → ``gaussian_kde``), and nothing
    otherwise (``{type: 'boxplot'}``, ``X \\ y``).
    """
    tokens: list[str] = []
    for span in _BACKTICK_RE.findall(defect_target(text)):
        if "(" in span:
            names = [
                m.group(1)
                for m in _CALL_RE.finditer(span)
                if span.count("(", 0, m.start()) == span.count(")", 0, m.start())
            ]
        else:
            name = span.strip()
            names = [re.split(r"\.|::", name)[-1]] if _CALL_NAME_RE.match(name) else []
        for name in names:
            if name and name not in tokens:
                tokens.append(name)
    return tokens


def is_removal(text: Any) -> bool:
    """The defect line's target is a removal: it starts with the word "remove" or "delete"."""
    return re.match(r"(?:remove|delete)\b", defect_target(text).lstrip("`* ").lower()) is not None


# The languages the pipeline generates (``impl-review.yml`` picks the suffix).
SOURCE_LANGUAGES = {
    ".py": "python",
    ".r": "r",
    ".jl": "julia",
    ".js": "javascript",
    ".jsx": "javascript",
    ".mjs": "javascript",
    ".ts": "javascript",
    ".tsx": "javascript",
}


def source_language(path_text: str | None) -> str | None:
    """The language of a source file by its suffix, or None for a suffix the gate cannot read."""
    return SOURCE_LANGUAGES.get(Path(path_text).suffix.lower()) if path_text else None


_JULIA_CHAR_RE = re.compile(r"'(?:\\[^'\n]+|[^\\'\n])'")


def _string_end(source: str, start: int, language: str) -> int:
    """The index after the string literal that opens at ``start``."""
    quote = source[start]
    if language in ("python", "julia") and source.startswith(quote * 3, start):
        closer, pos, multiline = quote * 3, start + 3, True
    else:
        # A Python or JavaScript one-quote string ends with its line, so an
        # unbalanced quote costs one line; R, Julia and a template span lines.
        closer, pos, multiline = quote, start + 1, language in ("r", "julia") or quote == "`"
    while pos < len(source):
        if source[pos] == "\\":
            pos += 2
        elif source.startswith(closer, pos):
            return pos + len(closer)
        elif source[pos] == "\n" and not multiline:
            return pos
        else:
            pos += 1
    return len(source)


def _julia_comment_end(source: str, start: int) -> int:
    """The index after the ``#= … =#`` comment that opens at ``start``; these nest."""
    depth, pos = 0, start
    while pos < len(source):
        if source.startswith("#=", pos):
            depth, pos = depth + 1, pos + 2
        elif source.startswith("=#", pos):
            depth, pos = depth - 1, pos + 2
            if depth == 0:
                return pos
        else:
            pos += 1
    return len(source)


def executable_text(source: str, language: str) -> str:
    """``source`` with every comment and string literal blanked; the line structure stays.

    Comments: ``#`` (Python, R, Julia), ``#= … =#`` (Julia), ``//`` and
    ``/* … */`` (JavaScript, TypeScript). Strings: ``'``, ``"``, the triple
    quotes of Python and Julia, a JavaScript template and a Julia character
    (a lone ``'`` is Julia's adjoint and stays). The inside of an f-string, an
    interpolation or a template goes with its string, so a call in there is
    not counted.
    """
    quotes = {"python": "'\"", "r": "'\"", "julia": '"', "javascript": "'\"`"}.get(language, "")
    out: list[str] = []
    pos = 0
    while pos < len(source):
        end = pos
        if language == "javascript":
            if source.startswith("//", pos):
                end = source.find("\n", pos)
            elif source.startswith("/*", pos):
                end = source.find("*/", pos + 2)
                end = end + 2 if end >= 0 else -1
        elif language == "julia" and source.startswith("#=", pos):
            end = _julia_comment_end(source, pos)
        elif language in ("python", "r", "julia") and source[pos] == "#":
            end = source.find("\n", pos)
        if end == pos and source[pos] in quotes:
            end = _string_end(source, pos, language)
        elif end == pos and language == "julia" and (char := _JULIA_CHAR_RE.match(source, pos)):
            end = char.end()
        if end == pos:
            out.append(source[pos])
            pos += 1
            continue
        end = len(source) if end < 0 else end
        out.append("".join("\n" if c == "\n" else " " for c in source[pos:end]))
        pos = end
    return "".join(out)


# What precedes a name that is being defined, not called.
_DEFINITION_KEYWORD = {
    "python": re.compile(r"\b(?:def|class)\s+$"),
    "julia": re.compile(r"\b(?:function|macro)\s+$"),
    "javascript": re.compile(r"\bfunction\s*\*?\s*$"),
}
# A definition without a keyword: Julia's ``name(x) = …`` and a JavaScript
# method ``name(x) {``, each at the start of its line (what may precede the
# name there, and what follows its closing parenthesis).
_DEFINITION_SHORT = {
    "julia": (
        re.compile(r"\s*(?:@\w+\s+)*(?:[\w.]+\.)?"),
        re.compile(r"\s*(?:::[^=]+?)?\s*(?:where\b[^=]*)?=(?![=>])"),
    ),
    "javascript": (
        re.compile(r"\s*(?:(?:async|static|get|set|public|private|protected|override)\s+)*[*#]?"),
        re.compile(r"\s*(?::[^={;]+)?\{"),
    ),
}


def _after_arguments(text: str) -> str | None:
    """What follows the parenthesis that closes the one just before ``text``; None when it closes on a later line."""
    depth = 1
    for index, char in enumerate(text):
        depth += (char == "(") - (char == ")")
        if depth == 0:
            return text[index + 1 :]
    return None


def _is_definition(line: str, match: re.Match[str], language: str) -> bool:
    before = line[: match.start()]
    keyword = _DEFINITION_KEYWORD.get(language)
    if keyword is not None and keyword.search(before):
        return True
    lead, tail = _DEFINITION_SHORT.get(language, (None, None))
    if lead is None or tail is None or not lead.fullmatch(before):
        return False
    rest = _after_arguments(line[match.end() :])
    return rest is not None and tail.match(rest) is not None


def call_count(source: str, token: str, language: str = "python") -> int:
    """How often ``source`` calls ``token``: the name, not preceded by a word character, then ``(``.

    Only executable text counts (``executable_text``): a comment such as
    ``# use acf(series)`` or a string that spells the call is not the call.
    Neither is a definition (``def name(``, ``class name(``, ``function
    name(``, Julia's ``name(x) = …``, a JavaScript method ``name(x) {``): a
    hand-roll named after the call it imitates is not that call. R defines
    with ``name <- function(``, which is no call of ``name`` to begin with.
    """
    pattern = re.compile(rf"(?<!\w){re.escape(token)}\s*\(")
    return sum(
        1
        for line in executable_text(source, language).splitlines()
        for match in pattern.finditer(line)
        if not _is_definition(line, match, language)
    )


def _score_in_range(criterion: str, value: Any) -> bool:
    return (
        criterion in CRITERIA
        and isinstance(value, int)
        and not isinstance(value, bool)
        and 0 <= value <= CRITERIA[criterion]
    )


def flat_scores(mapping: Any) -> dict[str, int]:
    """``{criterion: score}`` for the known criteria with an integer in range; the rest is dropped."""
    if not isinstance(mapping, Mapping):
        return {}
    return {str(k): v for k, v in mapping.items() if _score_in_range(str(k), v)}


def checklist_scores(checklist: Any) -> dict[str, int]:
    """Flatten a six-category ``review_checklist.json`` into ``{criterion: score}``.

    Keeps the first item per id, and only integers from 0 to the item's
    maximum (a float, a bool or an out-of-range score is dropped).
    """
    scores: dict[str, int] = {}
    if not isinstance(checklist, Mapping):
        return scores
    for category in checklist.values():
        items = category.get("items") if isinstance(category, Mapping) else None
        for item in items if isinstance(items, list) else []:
            if not isinstance(item, Mapping):
                continue
            cid = item.get("id")
            if isinstance(cid, str) and cid not in scores and _score_in_range(cid, item.get("score")):
                scores[cid] = item["score"]
    return scores


def load_checklist_scores(path: Path | None) -> dict[str, int]:
    """``checklist_scores`` of a ``review_checklist.json`` file; ``{}`` on any error."""
    if path is None or not path.is_file():
        return {}
    try:
        return checklist_scores(json.loads(path.read_text(encoding="utf-8")))
    except (OSError, ValueError):
        return {}


def technical_items_at_maximum(checklist: Mapping[str, int]) -> bool:
    """Every VQ, SC, DQ and CQ item is present and at its maximum."""
    technical = [cid for cid in CRITERIA if cid[:2] in TECHNICAL_PREFIXES]
    return all(checklist.get(cid) == CRITERIA[cid] for cid in technical)


def nothing_to_repair(score: int | None, checklist: Mapping[str, int], weaknesses: Any) -> bool:
    """A first-generation review below its threshold that a repair cannot improve.

    A repair fixes defect lines. A review qualifies when it has none and its
    every technical item is at its maximum: the points it withheld are then
    design and library levels (DE, LM) that no line asks a repair to change,
    and the cycle would only buy a second, noisier score. Such a review is
    approved as it stands when it scores at least ``NOTHING_TO_REPAIR_MIN``.

    Both conditions are needed. The checklist alone would approve a review
    whose defect line names a DE or LM item, which a repair can act on. The
    absence of defect lines alone would approve a technical deduction that
    was written without a line, a reviewer slip that still gets its repair.

    A missing or incomplete checklist never qualifies, nor does one that does
    not add up to the score: no score cap can apply here (each needs a
    technical item at 0, or lands at 75), so a typed score off the sum is a
    deduction the checklist does not carry. A weakness list that is not a
    list of strings never qualifies either.
    """
    return (
        score is not None
        and score >= NOTHING_TO_REPAIR_MIN
        and technical_items_at_maximum(checklist)
        and set(checklist) == set(CRITERIA)
        and sum(checklist.values()) == score
        and isinstance(weaknesses, list)
        and all(isinstance(line, str) for line in weaknesses)
        and not any(weakness_class(line) == DEFECT for line in weaknesses)
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


WEAKNESS_TAGS = {DEFECT: "defect", SUGGESTION: "suggestion", LEGACY: "older review"}
# Read by the generator AND by the regen reviewer (8b step 2), so it explains
# the classes only and never says what the gate counts.
WEAKNESS_GUIDANCE = (
    "Defects are fixes to make. Suggestions are ideas the previous review did not require; they are not "
    "acted on. Older notes predate the current rubric: act on one only when it names something visibly "
    "wrong under the current criteria. A weakness that asks for less of something an "
    "`Expected, not a defect:` bullet of the spec names is obsolete."
)


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
    Each weakness is tagged with its class (``weakness_class``), and each
    returned item carries ``id``, ``text`` and ``class``.
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
        lines.append("## Strengths the previous review credited (keep those the current criteria still credit)")
        lines += [f"- {s}" for s in strengths]
        lines.append("")

    weaknesses = [{**w, "class": weakness_class(w["text"])} for w in weakness_ids(review.get("weaknesses") or [])]
    if weaknesses:
        lines.append("## Weaknesses — stable ids W1..Wn")
        lines += [f"- **{w['id']}** ({WEAKNESS_TAGS[w['class']]}): {w['text']}" for w in weaknesses]
        lines += ["", WEAKNESS_GUIDANCE, ""]

    checklist = review.get("criteria_checklist") or {}
    if isinstance(checklist, dict) and checklist:
        lines.append("## Criteria checklist (context — act on the defects, not on ❌ marks)")
        for cat, payload in checklist.items():
            # Older reviews stored scalars next to the six categories
            # (total_score, score_caps_applied, …); they are no category.
            if not isinstance(payload, dict):
                continue
            if include_scores:
                lines.append(f"### {cat}  ({payload.get('score', '?')}/{payload.get('max', '?')})")
            else:
                lines.append(f"### {cat}")
            for item in payload.get("items") or []:
                if not isinstance(item, dict):
                    continue
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
    r"(?P<head>(?:(?:#'|#|//)[ \t]?)?Quality:[ \t]*)(?P<score>\d{1,3})(?P<scale>[ \t]*/[ \t]*100)"
    r"(?P<tail>[ \t]*(?:\|[ \t]*(?:Created|Updated):.*)?)"
)
HEADER_LINES = 15


def _rewrite_header_score(text: str, template: str, first_only: bool = False) -> str:
    """Apply ``template`` (``QUALITY_HEADER_RE`` groups) to each header line.

    Only the first ``HEADER_LINES`` lines are read; line endings and the line
    count stay as they were. ``first_only`` stops after the first header line.
    """
    lines = text.splitlines(keepends=True)
    for i, line in enumerate(lines[:HEADER_LINES]):
        body = line.rstrip("\r\n")
        match = QUALITY_HEADER_RE.fullmatch(body)
        if match:
            lines[i] = match.expand(template) + line[len(body) :]
            if first_only:
                break
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


def set_header_score(text: str, score: int) -> str:
    """Put ``score`` into the ``Quality: N/100`` header (O9: the write-back on a keep).

    Only the number changes: the ``Created:`` / ``Updated:`` tail stays, and
    so does everything else. Whole header lines in the leading lines only,
    line count unchanged; a file without a header is returned as it is. Only
    the first header line is rewritten, the one ``header_score`` reads: a few
    JavaScript files carry a stale second header below an ``//#`` directive
    (the header writer's prepend fallback), which keeps its number, so a
    write-back changes exactly one line (``regen_writeback.verify-diff``).
    """
    if not _is_int(score) or not 0 <= score <= 100:
        raise ValueError(f"score must be an integer 0-100 (got {score!r})")
    return _rewrite_header_score(text, rf"\g<head>{score}\g<scale>\g<tail>", first_only=True)


def header_score(text: str) -> int | None:
    """The number of the first ``Quality: N/100`` header line, or None without one."""
    for line in text.splitlines()[:HEADER_LINES]:
        match = QUALITY_HEADER_RE.fullmatch(line)
        if match:
            return int(match.group("score"))
    return None


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
    # Stored class of each previous weakness (``load_weakness_classes``): a
    # stored ``suggestion`` caps the re-score's class. Missing ids read as legacy.
    weakness_classes: Mapping[str, str] = field(default_factory=dict)
    # The new render's item scores (``review_checklist.json``, flattened).
    new_checklist: Mapping[str, int] = field(default_factory=dict)
    # Stored text of each previous weakness (``load_weakness_texts``), and the
    # predecessor's and the new source (``--prev-impl``/``--new-impl``). The
    # code path (``_code_path``) is off unless both sources are read.
    weakness_texts: Mapping[str, str] = field(default_factory=dict)
    prev_source: str | None = None
    new_source: str | None = None
    # The sources' language (``source_language`` of ``--new-impl``): what
    # ``call_count`` reads as a comment, a string and a definition.
    source_language: str = "python"


@dataclass
class GateResult:
    verdict: str
    reason: str
    code: str = ""
    prev_rescored: int | None = None
    # ``ref``/``what``/``where_visible`` plus ``class``, ``basis`` and ``rule``
    # (``classify_improvements``), and ``prev_score``/``new_score`` when a
    # criterion was tested.
    improvements: list[dict[str, Any]] = field(default_factory=list)
    regressions: list[dict[str, str]] = field(default_factory=list)
    # Improvements whose ref is in here were listed but not counted.
    permission_refs: frozenset[str] = frozenset()
    # Filled once review_regen.json validated; None before that.
    scenario_changed: bool | None = None
    encodings_added: int | None = None
    coerced: bool = False
    # ``ref``/``what``/``where_in_code`` plus ``kind``, ``counted`` and ``why``
    # (``classify_code_improvements``); line counts when both sources were read.
    code_improvements: list[dict[str, Any]] = field(default_factory=list)
    prev_lines: int | None = None
    new_lines: int | None = None


def _is_int(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def normalize_regen(payload: Any) -> tuple[Any, list[str]]:
    """Coerce predictable model slips; every coercion is recorded for the reason.

    Only unambiguous slips are repaired: a digit-string ``prev_rescored``,
    lower-case refs (``w2``) and rules (``vq-02``), missing ``regressions`` /
    ``encodings_added`` (read as empty) and ``"n/a"`` / ``"null"`` for
    ``change_request_applied``. Anything else is left for ``validate_regen``
    to reject. The classification keys are coerced, never rejected: a
    non-list ``prev_weaknesses`` or a non-object ``prev_checklist`` becomes
    empty, ``prev_weaknesses`` entries get a lower-case ``class`` and an
    upper-case ``ref`` and ``rule``, and an improvement's string ``kind`` is
    lower-cased and stripped. ``code_improvements`` is coerced the same way:
    a non-list becomes empty, and its refs are upper-cased.
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
            rule = item.get("rule") if isinstance(item, dict) else None
            if isinstance(rule, str) and rule.strip().upper() != rule:
                notes.append(f"rule {rule!r} -> {rule.strip().upper()!r}")
                item = {**item, "rule": rule.strip().upper()}
            kind = item.get("kind") if isinstance(item, dict) else None
            if isinstance(kind, str) and kind.strip().lower() != kind:
                notes.append(f"kind {kind!r} -> {kind.strip().lower()!r}")
                item = {**item, "kind": kind.strip().lower()}
            fixed.append(item)
        data["improvements"] = fixed

    if "prev_checklist" in data and not isinstance(data["prev_checklist"], dict):
        notes.append(f"prev_checklist {type(data['prev_checklist']).__name__} -> {{}}")
        data["prev_checklist"] = {}

    if "prev_weaknesses" in data:
        entries = data["prev_weaknesses"]
        if not isinstance(entries, list):
            notes.append(f"prev_weaknesses {type(entries).__name__} -> []")
            data["prev_weaknesses"] = []
        else:
            fixed_entries = []
            for i, entry in enumerate(entries, start=1):
                if isinstance(entry, dict):
                    changed = dict(entry)
                    for key, canon in (("class", str.lower), ("ref", str.upper), ("rule", str.upper)):
                        value = entry.get(key)
                        if isinstance(value, str) and canon(value.strip()) != value:
                            changed[key] = canon(value.strip())
                            notes.append(f"prev_weaknesses[{i}].{key} {value!r} -> {changed[key]!r}")
                    entry = changed
                fixed_entries.append(entry)
            data["prev_weaknesses"] = fixed_entries

    # Coerced, never rejected, like the classification keys. A missing list is
    # simply empty (older reviews have none), so it adds no note.
    if "code_improvements" in data:
        code = data["code_improvements"]
        if not isinstance(code, list):
            notes.append(f"code_improvements {type(code).__name__} -> []")
            data["code_improvements"] = []
        else:
            fixed_code = []
            for item in code:
                ref = item.get("ref") if isinstance(item, dict) else None
                if isinstance(ref, str) and _canonical_ref(ref) != ref and REF_RE.match(_canonical_ref(ref)):
                    notes.append(f"code ref {ref!r} -> {_canonical_ref(ref)!r}")
                    item = {**item, "ref": _canonical_ref(ref)}
                fixed_code.append(item)
            data["code_improvements"] = fixed_code

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
            # null reads as absent (no rule: the item cannot carry).
            if item.get("rule") is not None and not isinstance(item["rule"], str):
                errors.append(f"improvements[{i}].rule must be a string")

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
    """Apply the regen gate. Every uncertain input resolves to ``keep``.

    The two sources' line counts are on every result when both were read,
    so an early keep still reports them.
    """
    result = _decide(inp)
    if inp.prev_source is not None and inp.new_source is not None:
        result.prev_lines = len(inp.prev_source.splitlines())
        result.new_lines = len(inp.new_source.splitlines())
    return result


def _decide(inp: GateInput) -> GateResult:
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


# Improvement classes (``classify_improvements``). Only a visible ``carrier``
# can carry a merge; ``permission`` and ``obsolete`` items are not counted at
# all. ``basis`` says why: a carrier rests on a ``criterion`` delta, a
# ``characteristic`` or an ``auto_reject`` fix; a suggestion is a
# ``suggestion`` (a W the re-score classed so, or left unclassified), an
# ``unverified`` claim, a ``de_lm`` (design, library-mastery or DQ-01
# feature-coverage) point, or a would-be carrier whose ``kind`` does not carry:
# an ``addition`` (an element nothing requires), ``polish`` (of an element the
# spec's scope excludes) or ``no_kind`` (a missing or unknown kind).
PERMISSION = "permission"
CARRIER = "carrier"
UNVERIFIED = "unverified"
DE_LM = "de_lm"
# The ``kind`` every improvement names (8b step 3); only a fix or a removal
# carries. A missing or unknown kind fails toward keep, and never reads as
# ``unverified``: its scores may well confirm the claim.
KINDS = ("fix", "removal", "addition", "polish")
CARRYING_KINDS = frozenset({"fix", "removal"})
ADDITION = "addition"
POLISH = "polish"
# Kinds that fix no rule: they need no ``rule`` and claim no score delta.
NON_FIX_KINDS = frozenset({ADDITION, POLISH})
NO_KIND = "no_kind"


def load_weakness_classes(path: Path | None) -> dict[str, str]:
    """``{W id: stored class}`` from the ``context`` weaknesses JSON.

    An item without a known ``class`` (a file an older gate wrote) reads as
    ``legacy``; a missing or malformed file gives ``{}``.
    """
    if path is None or not path.is_file():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    if not isinstance(data, list):
        return {}
    classes: dict[str, str] = {}
    for item in data:
        if isinstance(item, dict) and "id" in item:
            cls = item.get("class")
            classes[str(item["id"])] = cls if cls in (DEFECT, SUGGESTION, LEGACY) else LEGACY
    return classes


def load_weakness_texts(path: Path | None) -> dict[str, str]:
    """``{W id: stored text}`` from the ``context`` weaknesses JSON; ``{}`` on any error."""
    if path is None or not path.is_file():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    if not isinstance(data, list):
        return {}
    return {
        str(item["id"]): item["text"]
        for item in data
        if isinstance(item, dict) and "id" in item and isinstance(item.get("text"), str)
    }


def load_source(path_text: str | None) -> str | None:
    """A source file for the code path, or None when absent, unreadable or over ``SOURCE_LIMIT`` bytes."""
    if not path_text:
        return None
    path = Path(path_text)
    try:
        if not path.is_file() or path.stat().st_size > SOURCE_LIMIT:
            return None
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return None


def _rescore_classes(payload: Mapping[str, Any]) -> dict[str, tuple[str, str | None]]:
    """``{W ref: (class, rule)}`` from ``prev_weaknesses``; the first entry per ref wins.

    An entry without a known class reads as a suggestion; a malformed entry is
    skipped (its W then reads as unclassified, which is a suggestion too).
    """
    out: dict[str, tuple[str, str | None]] = {}
    entries = payload.get("prev_weaknesses")
    for entry in entries if isinstance(entries, list) else []:
        if not isinstance(entry, Mapping):
            continue
        ref = entry.get("ref")
        if not isinstance(ref, str) or not re.fullmatch(r"W[1-9]\d*", ref.strip().upper()):
            continue
        ref = ref.strip().upper()
        if ref in out:
            continue
        cls = str(entry.get("class") or "").strip().lower()
        out[ref] = (cls if cls in RESCORE_CLASSES else SUGGESTION, _canonical_rule(entry.get("rule")))
    return out


def _canonical_rule(value: Any) -> str | None:
    """A rule as the gate compares it (``VQ-02``, ``C3``); None when absent or blank."""
    return (value.strip().upper() or None) if isinstance(value, str) else None


def _affirmative_c(ref: str, inp: GateInput) -> bool:
    """An "A good version shows" (or unlabeled) bullet within the spec's count."""
    m = C_REF_RE.match(ref)
    if m is None:
        return False
    return int(m.group("num")) <= inp.characteristic_count and ref not in inp.permission_refs


def _verify(rule: str | None, inp: GateInput, prev_checklist: Mapping[str, int], prev_rescored: Any) -> dict[str, Any]:
    """``class``/``basis`` (and the two scores for a carrier criterion) of one claimed rule."""
    if not rule:
        return {"class": SUGGESTION, "basis": UNVERIFIED}
    if rule in CARRIER_CRITERIA:
        prev, new = prev_checklist.get(rule), inp.new_checklist.get(rule)
        scores = {"prev_score": prev, "new_score": new}
        if isinstance(prev, int) and isinstance(new, int) and new > prev:
            return {"class": CARRIER, "basis": "criterion", **scores}
        return {"class": SUGGESTION, "basis": UNVERIFIED, **scores}
    if rule in CRITERIA:  # DE, LM and DQ-01: stored and repaired, never a carrier
        return {"class": SUGGESTION, "basis": DE_LM}
    if C_REF_RE.match(rule):
        return (
            {"class": CARRIER, "basis": "characteristic"}
            if _affirmative_c(rule, inp)
            else {"class": SUGGESTION, "basis": UNVERIFIED}
        )
    if rule in AR_IDS and prev_rescored == 0:
        return {"class": CARRIER, "basis": "auto_reject"}
    return {"class": SUGGESTION, "basis": UNVERIFIED}


def classify_improvements(payload: Any, inp: GateInput) -> list[dict[str, Any]]:
    """Every listed improvement with its class, the basis of that class and its rule.

    - A ``C`` ref: a ``permission`` when it is an "Expected, not a defect"
      bullet, otherwise a ``carrier`` (an affirmative characteristic).
    - A ``W`` ref: the class the re-score gave it in ``prev_weaknesses`` —
      ``obsolete`` (never counted, whatever C id it names), ``suggestion``, or
      ``defect``, whose ``rule`` is then verified. A W stored as a
      ``Suggestion:`` line is capped at suggestion; an unclassified W is a
      suggestion.
    - A ``P`` or ``new`` item: its own ``rule``, verified.

    A rule verifies when it is a VQ/SC/DQ/CQ criterion other than DQ-01 the
    new render (``inp.new_checklist``) scores higher on than
    ``prev_checklist``, an affirmative C id, or ``AR-06``..``AR-09`` while
    ``prev_rescored`` is 0. A DE, LM or DQ-01 rule is a ``de_lm`` suggestion.

    The item's ``kind`` (``kind`` in the entry: one of ``KINDS``, or None) is
    read only after the class is set, and only demotes a would-be carrier: an
    ``addition`` or ``polish`` becomes a suggestion with that basis, and a
    missing, unknown or non-string kind one with basis ``no_kind``. An
    ``addition`` or ``polish`` that would be ``unverified`` (its rule does not
    verify, or it names none, which it need not) takes its kind as basis: it
    claims no defect. Every other class keeps its basis, whatever the kind
    (a DQ-01 addition stays ``de_lm``). Robust to a payload the
    gate would reject (the retest harness counts item by item).
    """
    if not isinstance(payload, Mapping) or not isinstance(payload.get("improvements"), list):
        return []
    prev_checklist = flat_scores(payload.get("prev_checklist"))
    rescore = _rescore_classes(payload)
    prev_rescored = payload.get("prev_rescored")
    out: list[dict[str, Any]] = []
    for item in payload["improvements"]:
        if not isinstance(item, Mapping):
            continue
        ref = str(item.get("ref") or "")
        raw_kind = item.get("kind")
        entry: dict[str, Any] = {
            "ref": ref,
            "what": str(item.get("what") or "").strip(),
            "where_visible": str(item.get("where_visible") or "").strip(),
            "rule": None,
            "kind": raw_kind if raw_kind in KINDS else None,
        }
        m = REF_RE.match(ref)
        ref_kind = m.group("kind") if m else None
        if ref_kind == "C":
            entry["rule"] = ref
            if ref in inp.permission_refs:
                entry.update({"class": PERMISSION, "basis": PERMISSION})
            elif _affirmative_c(ref, inp):
                entry.update({"class": CARRIER, "basis": "characteristic"})
            else:
                entry.update({"class": SUGGESTION, "basis": UNVERIFIED})
        elif ref_kind == "W":
            cls, rule = rescore.get(ref, (SUGGESTION, None))
            entry["rule"] = rule
            if cls == DEFECT and inp.weakness_classes.get(ref, LEGACY) == SUGGESTION:
                cls = SUGGESTION  # a stored Suggestion: line is capped; a real defect becomes a P finding
                entry["capped"] = True
            if cls == OBSOLETE:
                entry.update({"class": OBSOLETE, "basis": "labeled" if rule in inp.permission_refs else "unlabeled"})
            elif cls == DEFECT:
                entry.update(_verify(rule, inp, prev_checklist, prev_rescored))
            else:
                entry.update({"class": SUGGESTION, "basis": SUGGESTION})
        elif m:  # P<n> or new
            entry["rule"] = _canonical_rule(item.get("rule"))
            entry.update(_verify(entry["rule"], inp, prev_checklist, prev_rescored))
        else:
            entry.update({"class": SUGGESTION, "basis": UNVERIFIED})
        if entry["class"] == CARRIER and entry["kind"] not in CARRYING_KINDS:
            entry.update({"class": SUGGESTION, "basis": entry["kind"] or NO_KIND})
        elif entry.get("basis") == UNVERIFIED and entry["kind"] in NON_FIX_KINDS:
            entry["basis"] = entry["kind"]  # it claims no defect, so it cannot fail to verify one
        out.append(entry)
    return out


def _counted(item: Mapping[str, Any]) -> bool:
    """Counted by the gate: neither a permission nor an obsolete weakness."""
    return item.get("class") not in (PERMISSION, OBSOLETE)


def _code_item_problem(item: Any, inp: GateInput, payload: Mapping[str, Any]) -> tuple[str | None, str | None]:
    """``(kind, None)`` when one ``code_improvements`` entry holds on its own, else ``(None, why)``.

    The kind is ``removal`` when the stored line's target is one, else ``fix``.
    The sources are checked here only for the new-call test; the path-wide
    conditions are ``classify_code_improvements``'.
    """
    if not isinstance(item, Mapping):
        return None, "not an object"
    ref = str(item.get("ref") or "")
    if not re.fullmatch(r"W[1-9]\d*", ref):
        return None, "only a W id of the previous review qualifies"
    if ref not in inp.known_weakness_ids:
        return None, "not a weakness id of the previous review"
    if not str(item.get("what") or "").strip() or not str(item.get("where_in_code") or "").strip():
        return None, "needs a non-empty what and where_in_code"
    cls, rule = _rescore_classes(payload).get(ref, (SUGGESTION, None))
    if cls != DEFECT or rule != CODE_RULE:
        return None, f"classed {cls} ({rule or 'no rule'}), not a {CODE_RULE} defect"
    text = inp.weakness_texts.get(ref, "")
    if not is_cq04_code_defect(text):
        return None, f"its stored line is not a '{CODE_RULE} (code)' defect line"
    prev = flat_scores(payload.get("prev_checklist")).get(CODE_RULE)
    new = inp.new_checklist.get(CODE_RULE)
    if not (isinstance(prev, int) and isinstance(new, int) and new > prev):
        return None, f"{CODE_RULE} did not score higher ({_score_text(prev)} → {_score_text(new)})"
    if is_removal(text):
        return "removal", None
    tokens = replacement_tokens(text)
    if not tokens:
        return None, "its stored line names no call and no removal"
    prev_source, new_source = inp.prev_source or "", inp.new_source or ""
    language = inp.source_language
    if not any(call_count(new_source, t, language) > call_count(prev_source, t, language) for t in tokens):
        return None, f"the named call ({', '.join(tokens)}) is not called more often than before"
    return "fix", None


def classify_code_improvements(payload: Any, inp: GateInput) -> list[dict[str, Any]]:
    """Every ``code_improvements`` entry, with ``kind``, ``counted`` and ``why``.

    An entry counts when all of these hold (the code path, P8):

    - its ``ref`` is a previous weakness (a ``W`` id) the re-score classed
      ``defect`` with rule ``CQ-04``, and ``what`` and ``where_in_code`` are
      non-empty;
    - the stored line of that ``W`` is a ``CQ-04 (code)`` defect line
      (``is_cq04_code_defect``): an older line names no checkable replacement;
    - the new render scores CQ-04 higher than ``prev_checklist`` does;
    - its target is a removal, or the new source calls one of the named calls
      (``replacement_tokens``) more often than the predecessor's source;
    - path-wide: both sources were read, the new one has fewer lines, the data
      scenario is unchanged and no encoding was added (on any spec).

    A malformed entry is listed as not counted with the reason; it never
    invalidates ``review_regen.json``. ``kind`` is ``fix`` or ``removal`` for an
    entry that holds on its own, else None.
    """
    raw = payload.get("code_improvements") if isinstance(payload, Mapping) else None
    if not isinstance(raw, list) or not raw:
        return []
    path_why = None
    if inp.prev_source is None or inp.new_source is None:
        path_why = "code path off: the previous or the new source was not read"
    elif len(inp.new_source.splitlines()) >= len(inp.prev_source.splitlines()):
        path_why = "the new source is not shorter"
    elif payload.get("scenario_changed") is True:
        path_why = "the code path needs an unchanged data scenario"
    elif any(str(e).strip() for e in payload.get("encodings_added") or []):
        path_why = "the code path needs no added encodings"
    out: list[dict[str, Any]] = []
    for item in raw:
        kind, why = _code_item_problem(item, inp, payload) if path_why is None else (None, path_why)
        entry = item if isinstance(item, Mapping) else {}
        out.append(
            {
                "ref": str(entry.get("ref") or ""),
                "what": str(entry.get("what") or "").strip(),
                "where_in_code": str(entry.get("where_in_code") or "").strip(),
                "kind": kind,
                "counted": why is None,
                "why": why,
            }
        )
    return out


def _judge(inp: GateInput, regen: Any) -> GateResult:
    errors = validate_regen(regen, inp.known_weakness_ids, inp.characteristic_count)
    if errors:
        return GateResult(KEEP, "invalid review_regen.json: " + "; ".join(errors), "regen_json_invalid")

    payload: dict[str, Any] = regen
    prev_rescored: int = payload["prev_rescored"]
    improvements = classify_improvements(payload, inp)
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
        code_improvements=classify_code_improvements(payload, inp),
    )
    if inp.prev_source is not None and inp.new_source is not None:
        result.prev_lines = len(inp.prev_source.splitlines())
        result.new_lines = len(inp.new_source.splitlines())

    if regressions:
        result.code = "regression"
        result.reason = f"{len(regressions)} regression(s): " + "; ".join(r["what"] for r in regressions)
        return result

    # A permission ("Expected, not a defect") is never an improvement, and a
    # previous weakness such a bullet covers is obsolete: neither item is
    # counted, but the rest of the file still is.
    counted = [i for i in improvements if _counted(i)]
    cited = sorted({i["ref"] for i in improvements if i["class"] == PERMISSION}, key=lambda ref: int(ref[1:]))
    obsolete = [i for i in improvements if i["class"] == OBSOLETE]
    notes = []
    if cited:
        bullets = "bullet" if len(cited) == 1 else "bullets"
        notes.append(f"{', '.join(cited)} = 'Expected, not a defect' {bullets}, not counted as an improvement")
    if obsolete:
        refs = ", ".join(f"{i['ref']} ({i['rule'] or 'no C id'})" for i in obsolete)
        notes.append(f"obsolete: {refs}, not counted")
    note = "".join(f" ({n})" for n in notes)

    visible = [i for i in counted if i["where_visible"]]
    carriers = [i for i in visible if i["class"] == CARRIER]
    # The code path (P8): with no carrier, a counted code improvement still
    # carries; visible suggestions ride along as they do with any carrier.
    code_counted = [c for c in result.code_improvements if c["counted"]]
    code_note = ""
    if result.code_improvements and not code_counted:
        why = "; ".join(f"{c['ref'] or '?'}: {c['why']}" for c in result.code_improvements)
        code_note = f" (code path: nothing counted — {why})"

    if not visible and not code_counted:
        detail = " (every improvement needs a non-empty where_visible)" if counted or not (cited or obsolete) else ""
        result.code = "no_visible_improvement"
        result.reason = f"no visible improvement{detail}{note}{code_note}"
        return result

    if not carriers and not code_counted:
        kinds = [
            (sum(1 for i in visible if i["basis"] == basis), label)
            for basis, label in (
                (SUGGESTION, "suggestion"),
                (UNVERIFIED, "unverified"),
                (DE_LM, "design, library or coverage"),
                (ADDITION, "addition"),
                (POLISH, "polish of an out-of-scope element"),
                (NO_KIND, "no kind named"),
            )
        ]
        breakdown = ", ".join(f"{n} {label}" for n, label in kinds if n)
        result.code = "no_defect_improvement"
        result.reason = (
            f"{len(visible)} visible improvement(s) ({breakdown}), none fixes a verified defect "
            f"or an 'A good version shows' property{note}{code_note}"
        )
        return result

    if inp.score < prev_rescored - 1:
        result.code = "below_tolerance"
        result.reason = f"new score {inp.score} < re-scored predecessor {prev_rescored} - 1{note}"
        return result

    result.verdict = MERGE
    result.code = "merge"
    if carriers:
        result.reason = (
            f"{len(visible)} visible improvement(s), {len(carriers)} carrying "
            f"({', '.join(i['ref'] for i in carriers)}), no regressions, new score {inp.score} >= "
            f"re-scored predecessor {prev_rescored} - 1{note}"
        )
    else:
        fixed = ", ".join(f"{c['ref']} ({CODE_RULE}, {c['kind']})" for c in code_counted)
        result.reason = (
            f"code path: {fixed} fixed, {result.prev_lines} → {result.new_lines} lines, no carrier, "
            f"no regressions, new score {inp.score} >= re-scored predecessor {prev_rescored} - 1{note}"
        )
    return result


# ---------------------------------------------------------------------------
# Feedback format and consistency (check-feedback)
# ---------------------------------------------------------------------------

# The fix direction for every inconsistent claim: the checklists are final.
CLAIM_FIX = "change the claim, not the scores"


def check_weaknesses(weaknesses: Any, checklist: Mapping[str, int]) -> tuple[list[str], dict[str, int]]:
    """Problems of a ``review_weaknesses.json`` list, and its class counts.

    Every line is a defect or a ``Suggestion:`` line, every defect ID is known,
    every criterion a defect names is below its maximum in the review's own
    checklist (skipped when the item is missing), every technical item below
    its maximum is named by a defect line (``silent`` counts the ones that are
    not), and there are at most ``MAX_SUGGESTIONS`` suggestions.
    """
    counts = {DEFECT: 0, SUGGESTION: 0, LEGACY: 0, SILENT: 0}
    if not isinstance(weaknesses, list):
        return ["review_weaknesses.json is not a JSON list of strings"], counts
    problems: list[str] = []
    for i, raw in enumerate(weaknesses, start=1):
        if not isinstance(raw, str):
            problems.append(f"weakness {i} is not a string")
            counts[LEGACY] += 1
            continue
        text = raw.strip()
        cls = weakness_class(text)
        counts[cls] += 1
        if cls == LEGACY:
            problems.append(
                f"weakness {i} is neither a defect line ('<ID> (<light|dark|both|code>): <what is wrong> → <target>. "
                f"Likely cause: <code element>.') nor a 'Suggestion: …' line: {_one_line(text)[:80]!r}"
            )
            continue
        problems += _defect_id_problems(i, text, checklist)
    if counts[SUGGESTION] > MAX_SUGGESTIONS:
        problems.append(f"{counts[SUGGESTION]} 'Suggestion:' lines; keep at most {MAX_SUGGESTIONS}")
    silent = _silent_deduction_problems(weaknesses, checklist)
    counts[SILENT] = len(silent)
    return problems + silent, counts


def _silent_deduction_problems(weaknesses: list[Any], checklist: Mapping[str, int]) -> list[str]:
    """Technical items below their maximum that no defect line names.

    A deduction on a VQ, SC, DQ or CQ item is carried by a defect line (8a):
    without one the next generation has nothing to fix. DE and LM items are
    judgments and need none. A review that names an auto-reject (``AR-06`` …
    ``AR-09``) scores 0 whatever its items say, and is left alone.
    """
    named = {cid for raw in weaknesses if isinstance(raw, str) for cid in defect_ids(raw.strip())}
    if named & set(AR_IDS):
        return []
    return [
        f"{cid} is below its maximum ({checklist[cid]}/{top}), but no defect line names it: write the defect "
        f"line the deduction rests on ('{cid} (<light|dark|both|code>): <what is wrong> → <target>. Likely "
        f"cause: …'), or the item keeps its maximum — a 'Suggestion:' line costs no points"
        for cid, top in CRITERIA.items()
        if cid[:2] in TECHNICAL_PREFIXES and cid in checklist and checklist[cid] < top and cid not in named
    ]


def _defect_id_problems(i: int, text: str, checklist: Mapping[str, int]) -> list[str]:
    """Every ID a defect line names is known, and a criterion it names is below its maximum."""
    problems: list[str] = []
    for cid in defect_ids(text):
        if cid not in CRITERIA and cid not in AR_IDS:
            problems.append(f"weakness {i} names {cid}, which is neither a criterion (VQ-01..LM-02) nor AR-06..AR-09")
        elif cid in CRITERIA and checklist.get(cid) == CRITERIA[cid]:
            problems.append(
                f"weakness {i} names {cid}, but your checklist gives {cid} its maximum "
                f"({CRITERIA[cid]}/{CRITERIA[cid]}): name the criterion the defect costs points on, "
                f"or make it a 'Suggestion:' line"
            )
    return problems


def check_prev_review(prev_review: Any, regen: Any) -> list[str]:
    """Problems of a ``review_prev.json`` (8b step 5); empty when it can be stored.

    The file is the session's re-score of the predecessor written as a full
    review, and ``regen_writeback.py`` stores it as the live implementation's
    review when the gate keeps it. So it has the shapes of the new render's
    review files: a non-empty ``image_description``; a ``criteria_checklist``
    with exactly the six category keys, their maxima and every criterion as an
    item with its ``id``, a non-empty ``name``, an integer ``score`` in range,
    its ``max``, a boolean ``passed`` and a string ``comment`` (the stored
    checklist is rendered as is), each category's score the sum of its
    items, each item equal to the same item of ``review_regen.json``'s
    ``prev_checklist`` (the gate contract stays authoritative); the total is
    not compared with ``prev_rescored``, which a score cap (step 8) may hold
    below it; ``strengths`` and ``weaknesses`` as lists of non-empty
    strings, the weaknesses being defect lines first and then at most
    ``MAX_SUGGESTIONS`` ``Suggestion:`` lines. A ``verdict`` is optional: the
    write-back sets the stored verdict itself, and the reviewer, who is not
    shown the approval bar, writes none; a review under older rules still
    carries one, which must then be ``APPROVED`` or ``REJECTED``. It has no
    score: the stored score is ``prev_rescored``, and other keys are ignored. The content of a defect line (its IDs against the
    checklist) is ``check-feedback``'s, which only warns.
    """
    if not isinstance(prev_review, Mapping):
        return ["review_prev.json is not a JSON object"]
    problems: list[str] = []
    desc = prev_review.get("image_description")
    if not isinstance(desc, str) or not desc.strip():
        problems.append("image_description must be a non-empty string describing both production renders")
    problems += _prev_review_checklist_problems(prev_review.get("criteria_checklist"), regen)
    for key in ("strengths", "weaknesses"):
        value = prev_review.get(key)
        if not isinstance(value, list) or not all(isinstance(v, str) and v.strip() for v in value):
            problems.append(f"{key} must be a list of non-empty strings")
        elif key == "weaknesses":
            problems += _prev_weakness_order_problems(value)
    if "verdict" in prev_review and prev_review["verdict"] not in REVIEW_VERDICTS:
        problems.append(f"verdict, when present, must be APPROVED or REJECTED (got {prev_review['verdict']!r})")
    return problems


def _prev_weakness_order_problems(weaknesses: list[str]) -> list[str]:
    problems: list[str] = []
    suggestions = 0
    for i, raw in enumerate(weaknesses, start=1):
        cls = weakness_class(raw)
        if cls == LEGACY:
            problems.append(
                f"weakness {i} is neither a defect line ('<ID> (<light|dark|both|code>): …', no P id in front) "
                f"nor a 'Suggestion: …' line: {_one_line(raw)[:80]!r}"
            )
        elif cls == DEFECT and suggestions:
            problems.append(f"weakness {i} is a defect line after a 'Suggestion:' line: list the defect lines first")
        elif cls == SUGGESTION:
            suggestions += 1
    if suggestions > MAX_SUGGESTIONS:
        problems.append(f"{suggestions} 'Suggestion:' lines; keep at most {MAX_SUGGESTIONS}")
    return problems


def _prev_review_checklist_problems(checklist: Any, regen: Any) -> list[str]:
    if not isinstance(checklist, Mapping):
        return ["criteria_checklist must be an object with the six category keys of review_checklist.json"]
    problems: list[str] = []
    missing = [key for key in CHECKLIST_CATEGORIES if key not in checklist]
    if missing:
        problems.append(f"criteria_checklist lacks {', '.join(missing)}")
    unknown = sorted(str(key) for key in checklist if key not in CHECKLIST_CATEGORIES)
    if unknown:
        problems.append(f"criteria_checklist has unknown keys {', '.join(unknown)}")
    items: dict[str, int] = {}
    for key, prefix in CHECKLIST_CATEGORIES.items():
        category = checklist.get(key)
        if key not in checklist:
            continue
        if not isinstance(category, Mapping):
            problems.append(f"criteria_checklist.{key} is not an object")
            continue
        top = CATEGORY_MAX[key]
        if not (_is_int(category.get("max")) and category["max"] == top):
            problems.append(f"criteria_checklist.{key}.max must be {top} (got {category.get('max')!r})")
        score = category.get("score")
        if not (_is_int(score) and 0 <= score <= top):
            problems.append(f"criteria_checklist.{key}.score must be an integer from 0 to {top} (got {score!r})")
        raw_items = category.get("items")
        if not isinstance(raw_items, list):
            problems.append(f"criteria_checklist.{key}.items must be a list")
            continue
        seen: set[str] = set()
        # The category total is compared only when every item of it is sound.
        items_sound = True
        total = 0
        for i, item in enumerate(raw_items, start=1):
            where = f"criteria_checklist.{key}.items[{i}]"
            if not isinstance(item, Mapping):
                problems.append(f"{where} is not an object")
                items_sound = False
                continue
            cid = item.get("id")
            if not isinstance(cid, str) or not cid.startswith(f"{prefix}-") or cid not in CRITERIA:
                problems.append(f"{where}.id {cid!r} is not a {prefix} criterion")
                items_sound = False
                continue
            if cid in seen:
                problems.append(f"{where} repeats {cid}")
                items_sound = False
                continue
            seen.add(cid)
            if not (_is_int(item.get("max")) and item["max"] == CRITERIA[cid]):
                problems.append(f"{where} ({cid}) max must be {CRITERIA[cid]} (got {item.get('max')!r})")
            # The stored checklist renders as is: the name is the criterion's
            # label, passed its mark (render_previous_review), comment its text.
            name = item.get("name")
            if not isinstance(name, str) or not name.strip():
                problems.append(f"{where} ({cid}) name must be a non-empty string (got {name!r})")
            if not isinstance(item.get("passed"), bool):
                problems.append(f"{where} ({cid}) passed must be true or false (got {item.get('passed')!r})")
            if not isinstance(item.get("comment"), str):
                problems.append(f"{where} ({cid}) comment must be a string (got {item.get('comment')!r})")
            if not _score_in_range(cid, item.get("score")):
                problems.append(
                    f"{where} ({cid}) score must be an integer from 0 to {CRITERIA[cid]} (got {item.get('score')!r})"
                )
                items_sound = False
                continue
            items[cid] = item["score"]
            total += item["score"]
        absent = [cid for cid in CRITERIA if cid.startswith(f"{prefix}-") and cid not in seen]
        if absent:
            problems.append(f"criteria_checklist.{key} lacks the items {', '.join(absent)}")
        elif items_sound and _is_int(score) and 0 <= score <= top and score != total:
            problems.append(
                f"criteria_checklist.{key}.score {score} is not the sum of its item scores ({total}): set it to {total}"
            )

    raw_prev = regen.get("prev_checklist") if isinstance(regen, Mapping) else None
    if not isinstance(raw_prev, Mapping):
        problems.append("review_regen.json has no prev_checklist to compare criteria_checklist with")
        return problems
    prev = flat_scores(raw_prev)
    differ = [f"{cid} {score} vs {prev.get(cid, 'n/a')}" for cid, score in items.items() if prev.get(cid) != score]
    if differ:
        problems.append(
            "criteria_checklist differs from prev_checklist at "
            + ", ".join(differ)
            + " (review_prev.json vs review_regen.json): the item scores must be equal — change review_prev.json, "
            "never prev_checklist"
        )
    return problems


def _prev_checklist_problems(raw: Any) -> list[str]:
    if raw is None:
        return ["review_regen.json has no prev_checklist: add the 24 item scores of your re-score of the predecessor"]
    if not isinstance(raw, Mapping):
        return ["prev_checklist is not an object of criterion ids to item scores"]
    problems = []
    missing = [c for c in CRITERIA if c not in raw]
    if missing:
        problems.append(f"prev_checklist lacks {', '.join(missing)}")
    unknown = sorted(str(k) for k in raw if str(k) not in CRITERIA)
    if unknown:
        problems.append(f"prev_checklist has unknown ids {', '.join(unknown)}")
    for cid, value in raw.items():
        if str(cid) in CRITERIA and not _score_in_range(str(cid), value):
            problems.append(f"prev_checklist {cid} must be an integer from 0 to {CRITERIA[str(cid)]} (got {value!r})")
    return problems


def check_regen_feedback(
    regen: Any,
    prev_weakness_ids: list[str],
    stored_classes: Mapping[str, str],
    characteristics: list[str],
    checklist: Mapping[str, int],
    weakness_texts: Mapping[str, str] | None = None,
) -> list[str]:
    """Contract and consistency problems of a ``review_regen.json`` (8b).

    Structure (``validate_regen``), ``prev_checklist`` completeness, one known
    class per previous weakness with the rule its class needs, a rule on every
    ``P`` and ``new`` item of kind ``fix`` or ``removal``, a ``kind``
    (``KINDS``) on every improvement (the message never says which kinds
    carry), and two consistency tests that treat all 24 criteria alike (an
    ``addition`` or ``polish`` item claims no criterion, so it skips the
    second): a ``W`` classed ``defect`` under a criterion names one
    ``prev_checklist`` deducts, and an improvement that claims a criterion
    scores higher on it in the new render's ``checklist`` than in
    ``prev_checklist``. A failed claim is fixed by changing the claim.
    ``code_improvements`` entries are checked by ``_code_feedback`` (the stored
    line format only when ``weakness_texts`` is given).
    """
    payload, _ = normalize_regen(regen)
    known = frozenset(prev_weakness_ids)
    problems = [f"review_regen.json: {e}" for e in validate_regen(payload, known, len(characteristics))]
    if not isinstance(payload, Mapping):
        return problems
    permissions = permission_refs(characteristics)
    probe = GateInput(
        spec_id="", score=None, regen=None, characteristic_count=len(characteristics), permission_refs=permissions
    )

    raw_checklist = payload.get("prev_checklist")
    problems += _prev_checklist_problems(raw_checklist)
    prev_checklist = flat_scores(raw_checklist)

    entries = payload.get("prev_weaknesses")
    if prev_weakness_ids and not isinstance(entries, list):
        problems.append(
            "review_regen.json has no prev_weaknesses: classify every previous weakness "
            f"({', '.join(prev_weakness_ids)}) as defect, suggestion or obsolete"
        )
    seen: dict[str, int] = {}
    for i, entry in enumerate(entries if isinstance(entries, list) else [], start=1):
        ref = entry.get("ref") if isinstance(entry, Mapping) else None
        if not isinstance(ref, str) or ref not in known:
            problems.append(f"prev_weaknesses[{i}].ref {ref!r} is not a weakness id of the previous review")
            continue
        seen[ref] = seen.get(ref, 0) + 1
        cls = entry.get("class")
        rule = _canonical_rule(entry.get("rule"))
        if cls not in RESCORE_CLASSES:
            problems.append(f"{ref}: class {cls!r} is not one of defect, suggestion, obsolete")
        elif cls == DEFECT:
            if stored_classes.get(ref) == SUGGESTION:
                problems.append(
                    f"{ref} was stored as a 'Suggestion:' line and cannot be classed defect: class it suggestion, "
                    "and number a defect the predecessor shows as a P finding instead"
                )
            if not (rule in CRITERIA or rule in AR_IDS or (rule and _affirmative_c(rule, probe))):
                problems.append(
                    f"{ref} is classed defect but its rule {rule!r} is neither a criterion nor the C id of an "
                    "'A good version shows:' bullet"
                )
            elif rule in CRITERIA and prev_checklist.get(rule) == CRITERIA[rule]:
                problems.append(
                    f"{ref} is classed defect under {rule}, but prev_checklist gives {rule} its maximum "
                    f"({CRITERIA[rule]}/{CRITERIA[rule]}): reclass {ref} as suggestion or obsolete — {CLAIM_FIX}"
                )
        elif cls == OBSOLETE:
            num = int(rule[1:]) if rule and C_REF_RE.match(rule) else 0
            if not 0 < num <= len(characteristics):
                problems.append(f"{ref} is classed obsolete but its rule {rule!r} is not a C id of the spec's section")
            elif characteristic_kind(characteristics[num - 1]) == KIND_SHOWS:
                # Only a labeled "A good version shows:" bullet: an unlabeled
                # (older) section has no permissions to name instead.
                problems.append(
                    f"{ref} is classed obsolete under {rule}, an 'A good version shows:' bullet, not an "
                    f"'Expected, not a defect:' one: name the bullet that permits it, or class {ref} defect or suggestion"
                )
    for ref in prev_weakness_ids:
        if isinstance(entries, list) and seen.get(ref, 0) == 0:
            problems.append(f"prev_weaknesses does not classify {ref}")
        elif seen.get(ref, 0) > 1:
            problems.append(f"prev_weaknesses classifies {ref} {seen[ref]} times; classify it once")

    rescore = _rescore_classes(payload)
    improvements = payload.get("improvements")
    for i, item in enumerate(improvements if isinstance(improvements, list) else [], start=1):
        if not isinstance(item, Mapping) or not isinstance(item.get("ref"), str):
            continue
        ref = item["ref"]
        raw_kind = item.get("kind")
        if raw_kind not in KINDS:
            unknown = f" ({_one_line(str(raw_kind))[:40]!r} is not one)" if raw_kind is not None else ""
            problems.append(f"improvement {i} ({ref}) has no kind{unknown}: name fix, removal, addition or polish")
        m = REF_RE.match(ref)
        ref_kind = m.group("kind") if m else None
        if raw_kind in NON_FIX_KINDS:
            claimed = None  # an addition or polish fixes no rule: nothing to name or to verify
        elif ref_kind == "W":
            cls, rule = rescore.get(ref, (SUGGESTION, None))
            claimed = rule if cls == DEFECT else None
        elif m and ref_kind != "C":  # P<n> or new
            claimed = _canonical_rule(item.get("rule"))
            if claimed is None:
                problems.append(
                    f"improvement {i} ({ref}) has no rule: name the criterion or the C id of the "
                    "'A good version shows:' bullet it fixes"
                )
        else:
            claimed = None
        if claimed in CRITERIA:
            prev, new = prev_checklist.get(claimed), checklist.get(claimed)
            if isinstance(prev, int) and isinstance(new, int) and new <= prev:
                problems.append(
                    f"improvement {i} ({ref}) claims {claimed}, but your checklist for the new render gives "
                    f"{claimed} {new} and prev_checklist {prev}: it did not fix {claimed}, so remove it from "
                    f"improvements or name the rule it does fix — {CLAIM_FIX}"
                )
    # The raw file: normalize_regen would already have coerced a non-list to [].
    return problems + _code_feedback(regen, known, rescore, prev_checklist, checklist, weakness_texts or {})


def _code_feedback(
    payload: Mapping[str, Any],
    known: frozenset[str],
    rescore: Mapping[str, tuple[str, str | None]],
    prev_checklist: Mapping[str, int],
    checklist: Mapping[str, int],
    weakness_texts: Mapping[str, str],
) -> list[str]:
    """Problems of ``code_improvements`` (8b): each entry cites a known ``W`` classed
    ``defect`` under CQ-04 whose stored line is a ``CQ-04 (code)`` defect line,
    names ``what`` and ``where_in_code``, and CQ-04 scores higher in the new
    render's checklist than in ``prev_checklist``."""
    raw = payload.get("code_improvements")
    if raw is None:
        return []
    if not isinstance(raw, list):
        return ["review_regen.json: code_improvements must be a list (use [] when there is none)"]
    problems: list[str] = []
    for i, item in enumerate(raw, start=1):
        if not isinstance(item, Mapping):
            problems.append(f"code improvement {i} is not an object with ref, what and where_in_code")
            continue
        ref = _canonical_ref(str(item.get("ref") or ""))
        if not re.fullmatch(r"W[1-9]\d*", ref) or ref not in known:
            problems.append(
                f"code improvement {i} ({ref or 'no ref'}) must cite a W id of the previous review; "
                "a code issue you found yourself is never a code improvement"
            )
            continue
        for key in ("what", "where_in_code"):
            if not isinstance(item.get(key), str) or not item[key].strip():
                problems.append(f"code improvement {i} ({ref}) needs a non-empty {key}")
        cls, rule = rescore.get(ref, (SUGGESTION, None))
        if cls != DEFECT or rule != CODE_RULE:
            problems.append(
                f"code improvement {i} ({ref}) cites a W you classed {cls} ({rule or 'no rule'}); only a W classed "
                f"defect under {CODE_RULE} qualifies — remove it from code_improvements"
            )
        elif weakness_texts and not is_cq04_code_defect(weakness_texts.get(ref, "")):
            problems.append(
                f"code improvement {i} ({ref}): its stored line is not a '{CODE_RULE} (code): …' defect line, "
                "so it names no replacement — remove it from code_improvements"
            )
        prev, new = prev_checklist.get(CODE_RULE), checklist.get(CODE_RULE)
        if isinstance(prev, int) and isinstance(new, int) and new <= prev:
            problems.append(
                f"code improvement {i} ({ref}) claims {CODE_RULE}, but your checklist for the new render gives "
                f"{CODE_RULE} {new} and prev_checklist {prev}: remove it from code_improvements — {CLAIM_FIX}"
            )
    return problems


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


def _score_text(value: Any) -> str:
    return str(value) if isinstance(value, int) and not isinstance(value, bool) else "n/a"


def improvement_flag(item: Mapping[str, Any]) -> str:
    """The summary's class flag for one classified improvement (empty when unclassified).

    Only fixed ids and integers from the classification appear: the rule is
    re-checked against the known id shapes, so no model text reaches the flag.
    """
    raw = item.get("rule")
    rule = raw if isinstance(raw, str) and re.fullmatch(r"[A-Z]{1,2}-?\d{1,3}", raw) else None
    if raw and rule is None:
        rule = "an unrecognized rule"
    cls, basis = item.get("class"), item.get("basis")
    if cls == PERMISSION:
        return " _(permission, not counted)_"
    if cls == OBSOLETE:
        if basis == "labeled":
            return f" _(obsolete: covered by {rule}, not counted)_"
        return f" _(obsolete: {rule or 'no C id'} is not an 'Expected, not a defect' bullet; not counted)_"
    if cls == CARRIER:
        if basis == "criterion":
            return f" _(defect: {rule}, {_score_text(item.get('prev_score'))} → {_score_text(item.get('new_score'))})_"
        if basis == "characteristic" and item.get("ref") == rule:
            return " _(characteristic)_"
        return f" _(defect: {rule})_"
    if basis == DE_LM:
        return f" _(design, library or coverage point {rule}: does not carry)_"
    if basis == ADDITION:
        return " _(addition: does not carry)_"
    if basis == POLISH:
        return " _(polish of an out-of-scope element: does not carry)_"
    if basis == NO_KIND:
        return " _(no kind named: does not carry)_"
    if basis == UNVERIFIED:
        if "prev_score" in item or "new_score" in item:
            scores = f"{_score_text(item.get('prev_score'))} → {_score_text(item.get('new_score'))}"
            return f" _(unverified: {rule}, {scores})_"
        return f" _(unverified: {rule or 'no rule'})_"
    if cls == SUGGESTION:
        capped = ", stored as a suggestion" if item.get("capped") else ""
        return f" _(suggestion{capped}: does not carry)_"
    return ""


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
            lines.append(f"- `{item['ref']}` {_safe(item['what'])} — {where}{improvement_flag(item)}")
    else:
        lines.append("- none")
    if result.code_improvements:
        rides = any(i.get("class") == CARRIER and i.get("where_visible") for i in result.improvements)
        lines += ["", "**Code improvements**"]
        for item in result.code_improvements:
            if not item["counted"]:
                flag = f" _(not counted: {_safe(str(item['why']))})_"
            elif rides:
                flag = " _(rides along)_"
            else:
                flag = f" _(code path: counted, {item['kind']})_"
            where = _safe(item["where_in_code"]) or "_no location_"
            ref = _safe(item["ref"]) or "?"
            lines.append(f"- `{ref}` {_safe(item['what'])} — {where}{flag}")
    if result.prev_lines is not None and result.new_lines is not None:
        lines += ["", f"**Code size:** {result.prev_lines} → {result.new_lines} lines"]
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
        "writeback",
    }
)
# What happened to the re-score of the live implementation on a keep
# (impl-review.yml "Write back the re-score (regen keep)"). ``opened`` means the
# write-back PR exists and its merge was dispatched, not that it merged. The
# verdict step adds the key to keep records only; a missing step status reads
# as ``failed``.
WRITEBACK_CODES = ("opened", "unchanged", "no_rescore", "invalid", "stale", "failed")


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


def improvement_class_counts(items: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    """The class counts of classified improvements (``classify_improvements``).

    The gate record's ``improvements`` block without the per-ref counts, and
    what ``review_retest.py`` records per cell, so the two cannot drift apart;
    ``build_record`` documents each key.
    """
    visible = [i for i in items if _counted(i) and i["where_visible"]]
    carriers = [i for i in visible if i.get("class") == CARRIER]
    suggestions = [i for i in visible if i.get("class") != CARRIER]
    by_kind = dict.fromkeys((*KINDS, "none"), 0)
    for item in items:
        by_kind[item["kind"] if item.get("kind") in KINDS else "none"] += 1

    def basis(value: str) -> int:
        return sum(1 for i in suggestions if i.get("basis") == value)

    return {
        "total": len(items),
        "visible": len(visible),
        "permission": sum(1 for i in items if i.get("class") == PERMISSION),
        "obsolete": sum(1 for i in items if i.get("class") == OBSOLETE),
        "carriers": len(carriers),
        "suggestion": len(suggestions),
        "unverified": basis(UNVERIFIED),
        "de_lm": basis(DE_LM),
        "addition": basis(ADDITION),
        "polish": basis(POLISH),
        "no_kind": basis(NO_KIND),
        "carriers_pn": sum(1 for i in carriers if _ref_kind(str(i["ref"])) in ("P", "new")),
        "by_kind": by_kind,
    }


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
    the items that cite an "Expected, not a defect" bullet, ``obsolete`` the
    previous weaknesses the re-score classed obsolete, and ``visible`` only the
    counted ones (neither of the two) with a non-empty ``where_visible``. Of
    those, ``carriers`` can carry a merge and ``suggestion`` cannot, so
    ``visible == carriers + suggestion``; ``unverified`` (a claimed rule that
    did not verify, or none), ``de_lm`` (a DE, LM or DQ-01 rule),
    ``addition``, ``polish`` (an item of that kind that is neither a DE, LM
    or DQ-01 point nor a W the re-score classed a suggestion) and ``no_kind``
    (a would-be carrier without a valid kind) are disjoint subsets of ``suggestion``, and
    ``carriers_pn`` (carriers with a ``P`` or ``new`` ref) is a subset of
    ``carriers``. ``by_kind`` counts the ``kind`` of every listed item
    (``none`` for a missing or unknown one), so it sums to ``total``. The
    record stays ``v1``: records written before P3 lack the five
    classification keys, and ``visible`` then still counted obsolete
    citations; records written before P3.1 lack the kind keys. ``code``
    (from P8) counts the code improvements that hold
    (``classify_code_improvements``): with no carrier they carried the merge
    (the code path), with one they rode along; records written before P8
    lack it.
    """
    kinds = {"W": 0, "P": 0, "C": 0, "new": 0}
    for item in result.improvements:
        kind = _ref_kind(item["ref"])
        if kind in kinds:
            kinds[kind] += 1
    counts = improvement_class_counts(result.improvements)
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
            "total": counts.pop("total"),
            "visible": counts.pop("visible"),
            **kinds,
            **counts,
            "code": sum(1 for c in result.code_improvements if c["counted"]),
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
    ``KEEP``, and one of ``REASON_CODES``. ``writeback`` is optional, one of
    ``WRITEBACK_CODES``, and only on a keep.
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
    if "writeback" in record:
        if not (isinstance(record["writeback"], str) and record["writeback"] in WRITEBACK_CODES):
            errors.append("record.writeback is not one of WRITEBACK_CODES")
        elif record.get("verdict") != KEEP:
            errors.append("record.writeback belongs to a keep record only")

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
    counts = {cls: sum(1 for w in weaknesses if w["class"] == cls) for cls in (DEFECT, SUGGESTION, LEGACY)}
    print("::notice::weakness_classes " + " ".join(f"{cls}={n}" for cls, n in counts.items()))
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
    weaknesses_json = Path(args.weaknesses_json) if args.weaknesses_json else None
    language = source_language(args.new_impl)
    if language != source_language(args.prev_impl):
        language = None
    inp = GateInput(
        spec_id=args.spec_id,
        score=score,
        regen=regen,
        regen_error=regen_error,
        known_weakness_ids=load_known_weakness_ids(weaknesses_json),
        characteristic_count=len(characteristics),
        permission_refs=permission_refs(characteristics),
        prev_renders=args.prev_renders == "available",
        canvas_failed=args.canvas_failed,
        change_request_present=args.change_request_present,
        context_ok=not args.context_failed,
        weakness_classes=load_weakness_classes(weaknesses_json),
        # The review writes its checklist next to review_regen.json (the
        # repository root in impl-review, the cell workspace in the retest
        # harness), so no new flag: every caller's argument set still works.
        new_checklist=load_checklist_scores(Path(args.regen_json).parent / "review_checklist.json"),
        # Both optional: without them the code path is off and every older
        # caller (the retest harness at any rules_ref) decides as before.
        weakness_texts=load_weakness_texts(weaknesses_json),
        # A suffix the gate cannot read as code (or two different languages)
        # leaves the code path off, like an unreadable file.
        prev_source=load_source(args.prev_impl) if language else None,
        new_source=load_source(args.new_impl) if language else None,
        source_language=language or "python",
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
    # Only with the code path's flags, so an older argument set prints the old line.
    lines = ""
    if args.prev_impl or args.new_impl:
        lines = f" prev_lines={_score_text(result.prev_lines)} new_lines={_score_text(result.new_lines)}"
    print(
        f"::notice::regen_gate spec={args.spec_id} lib={args.library} prev_stored={args.prev_stored} "
        f"prev_rescored={rescored} new={score if score is not None else 'n/a'} verdict={result.verdict} "
        f"code={result.code}{provenance}{lines} reason={reason}"
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


def cmd_check_feedback(args: argparse.Namespace) -> int:
    if not args.weaknesses and not args.regen and not args.prev_review:
        print("check-feedback needs --weaknesses, --regen, --prev-review or several", file=sys.stderr)
        return 2
    problems: list[str] = []
    checklist: dict[str, int] = {}
    if args.checklist:
        checklist = load_checklist_scores(Path(args.checklist))
        if not checklist:
            problems.append(f"{args.checklist} is missing, unreadable or holds no item scores")
    counts = {DEFECT: 0, SUGGESTION: 0, LEGACY: 0, SILENT: 0}
    if args.weaknesses:
        weaknesses, error = load_regen_json(Path(args.weaknesses))
        if error:
            problems.append(f"{args.weaknesses} {error}")
        else:
            found, counts = check_weaknesses(weaknesses, checklist)
            problems += found
    regen: Any = None
    if args.regen:
        regen, error = load_regen_json(Path(args.regen))
        if error:
            problems.append(f"{args.regen} {error}")
        else:
            prev_path = Path(args.prev_weaknesses) if args.prev_weaknesses else None
            ids = sorted(load_known_weakness_ids(prev_path), key=lambda ref: int(ref[1:]) if ref[1:].isdigit() else 0)
            characteristics: list[str] = []
            if args.spec_file and Path(args.spec_file).is_file():
                characteristics = parse_characteristics(Path(args.spec_file).read_text(encoding="utf-8"))
            problems += check_regen_feedback(
                regen, ids, load_weakness_classes(prev_path), characteristics, checklist, load_weakness_texts(prev_path)
            )
    if args.prev_review:
        prev_review, error = load_regen_json(Path(args.prev_review))
        if error:
            problems.append(f"{args.prev_review} {error}")
        else:
            problems += [f"review_prev.json: {p}" for p in check_prev_review(prev_review, regen)]
            # The content of its defect lines, against the re-score's own checklist.
            prev_checklist = flat_scores(regen.get("prev_checklist")) if isinstance(regen, Mapping) else {}
            lines = prev_review.get("weaknesses") if isinstance(prev_review, Mapping) else None
            for i, line in enumerate(lines if isinstance(lines, list) else [], start=1):
                if isinstance(line, str) and weakness_class(line) == DEFECT:
                    problems += [f"review_prev.json: {p}" for p in _defect_id_problems(i, line.strip(), prev_checklist)]
            if isinstance(lines, list):
                problems += [f"review_prev.json: {p}" for p in _silent_deduction_problems(lines, prev_checklist)]
    for problem in problems:
        print(f"::warning::{_one_line(problem)}" if args.warn_only else _one_line(problem))
    if args.warn_only:
        print(
            f"::notice::weakness_format defect={counts[DEFECT]} suggestion={counts[SUGGESTION]} "
            f"other={counts[LEGACY]} silent={counts[SILENT]}"
        )
        return 0
    if not problems:
        print("check-feedback: no problems")
    return 1 if problems else 0


def cmd_marker(args: argparse.Namespace) -> int:
    try:
        record = json.loads(Path(args.record).read_text(encoding="utf-8"))
        print(render_record_marker(record))
    except (OSError, ValueError) as exc:
        print(f"no gate record marker: {_one_line(str(exc))[:200]}", file=sys.stderr)
        return 1
    return 0


def cmd_nothing_to_repair(args: argparse.Namespace) -> int:
    """Print ``true`` or ``false``; any unreadable input is ``false`` (today's behavior)."""
    weaknesses, error = load_regen_json(Path(args.weaknesses))
    qualifies = not error and nothing_to_repair(
        parse_score(args.score), load_checklist_scores(Path(args.checklist)), weaknesses
    )
    print("true" if qualifies else "false")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0] if __doc__ else None)
    sub = parser.add_subparsers(dest="command", required=True)

    ntr = sub.add_parser(
        "nothing-to-repair", help="Whether a first-generation review below its threshold has nothing a repair can fix"
    )
    ntr.add_argument("--score", required=True)
    ntr.add_argument("--checklist", default="review_checklist.json")
    ntr.add_argument("--weaknesses", default="review_weaknesses.json")
    ntr.set_defaults(func=cmd_nothing_to_repair)

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

    fb = sub.add_parser("check-feedback", help="Check the review's weakness lines and review_regen.json claims")
    fb.add_argument("--weaknesses", default="", help="review_weaknesses.json")
    fb.add_argument("--checklist", default="", help="review_checklist.json of the new render")
    fb.add_argument("--regen", default="", help="review_regen.json (regeneration only)")
    fb.add_argument(
        "--prev-weaknesses", default="", help="context's weaknesses JSON (/tmp/anyplot-prev-weaknesses.json)"
    )
    fb.add_argument("--spec-file", default="", help="plots/S/specification.md (C ids and their kinds)")
    fb.add_argument(
        "--prev-review", default="", help="review_prev.json, the re-score as a full review (checked against --regen)"
    )
    fb.add_argument("--warn-only", action="store_true", help="::warning:: annotations and a notice, exit 0")
    fb.set_defaults(func=cmd_check_feedback)

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
    # The code path's sources; without both, it is off (older callers unchanged).
    dec.add_argument("--prev-impl", default="", help="the predecessor's source (/tmp/anyplot-prev-impl.EXT)")
    dec.add_argument("--new-impl", default="", help="the regenerated source")
    dec.set_defaults(func=cmd_decide)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    sys.exit(main())
