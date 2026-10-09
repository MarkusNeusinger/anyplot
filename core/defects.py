"""The review feedback grammar: defect lines, suggestion lines and spec characteristics.

A review writes its weaknesses in two formats (``weakness_class``):

- a *defect* line ``<ID>[, <ID>] (<light|dark|both|code>): <observed> → <target>.
  Likely cause: <code element>.`` naming the criterion it violates
  (``DEFECT_RE``; ``format_defect`` builds one), and
- a ``Suggestion: …`` line, of which a review keeps at most ``MAX_SUGGESTIONS``.

Anything else is a *legacy* line from an older review. The IDs come from the
rubric (``CRITERIA``, ``prompts/quality-criteria.md``) and the AI-judged
auto-reject checks (``AR_IDS``). A spec's "What a good version looks like"
section lists the characteristics a review judges against
(``parse_characteristics``, ``characteristic_kind``).

This module is the canonical implementation for every consumer that can import
``core``, the planned agents service included
(``docs/concepts/agent-network.md``). It is stdlib-only on purpose: the
pipeline runs ``automation/scripts/regen_gate.py`` as a single-file copy with
the runner's system Python, so that script keeps a copy of these definitions
until its copy sites also ship this file;
``tests/unit/core/test_defects.py`` pins the two to identical behaviour.
"""

from __future__ import annotations

import re
from collections.abc import Mapping, Sequence


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
# The AI-judged auto-reject checks a defect line may name besides the criteria.
AR_IDS = ("AR-06", "AR-07", "AR-08", "AR-09")
# Every ID a well-formed defect line may name: the fixed set of the agents'
# ``Defect.id``. ``DEFECT_RE`` alone also reads an unknown ID as a defect line,
# so that a review check can report it.
KNOWN_IDS = frozenset(CRITERIA) | frozenset(AR_IDS)
# The render tags of a defect line: which theme shows it, or ``code`` for a
# defect only the source shows.
RENDERS = ("light", "dark", "both", "code")

# Weakness line formats. The class is the format, so the stored text carries it.
DEFECT = "defect"
SUGGESTION = "suggestion"
LEGACY = "legacy"

_DEFECT_ID = r"(?:VQ|DE|SC|DQ|CQ|LM|AR)-\d{2}"
# Prefix only: ``<ID>[, <ID>] (<light|dark|both|code>): <text>``. An unknown ID
# still reads as a defect line; check-feedback reports it.
DEFECT_RE = re.compile(rf"^(?P<ids>{_DEFECT_ID}(?:, {_DEFECT_ID})*) \((?P<render>light|dark|both|code)\): \S")
SUGGESTION_RE = re.compile(r"^Suggestion: \S")
MAX_SUGGESTIONS = 3

# The code-only path of the regen gate: a CQ-04 defect line the previous
# review named, fixed in the source alone. Its target, the text after the
# arrow up to "Likely cause:" (``defect_target``), names the replacement call
# in backticks, or "remove".
CODE_RULE = "CQ-04"
_LIKELY_CAUSE_RE = re.compile(r"\bLikely cause:")
ARROW = "→"

# The criteria whose every deduction a defect line carries (70 of 100 points);
# DE and LM are judgments that start at a default.
TECHNICAL_PREFIXES = ("VQ", "SC", "DQ", "CQ")
# The lowest score a first-generation review with nothing to repair is
# approved at (impl-review.yml's threshold after one repair).
NOTHING_TO_REPAIR_MIN = 80

CHARACTERISTICS_HEADING_RE = re.compile(r"^##\s+what a good version looks like\b", re.IGNORECASE)
NEXT_SECTION_RE = re.compile(r"^#{1,2}\s")
# Column 0 only. An indented line continues the bullet above it — a wrapped
# line, or a sub-point whose marker is dropped (NESTED_MARKER_RE).
TOP_LEVEL_BULLET_RE = re.compile(r"^(?:[-*+]|\d+[.)])\s+(?P<text>\S.*)$")
NESTED_MARKER_RE = re.compile(r"^(?:[-*+]|\d+[.)])\s+")

# The two kinds of characteristic bullet, each written as the bullet's opening
# words. spec_characteristics_lint.py requires these exact prefixes; readers
# match them leniently (any case, optional bold markers) and anchored at the
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


def weakness_class(text: object) -> str:
    """``defect``, ``suggestion`` or ``legacy`` (any other line, blank included)."""
    line = str(text or "").strip()
    if DEFECT_RE.match(line):
        return DEFECT
    if SUGGESTION_RE.match(line):
        return SUGGESTION
    return LEGACY


def defect_ids(text: object) -> list[str]:
    """The IDs a defect line names, in order; empty for any other line."""
    m = DEFECT_RE.match(str(text or "").strip())
    return m.group("ids").split(", ") if m else []


def is_cq04_code_defect(text: object) -> bool:
    """A defect line (``DEFECT_RE``) that names ``CQ-04`` with the render tag ``code``."""
    m = DEFECT_RE.match(str(text or "").strip())
    return m is not None and CODE_RULE in m.group("ids").split(", ") and m.group("render") == "code"


def defect_target(text: object) -> str:
    """What a defect line asks for: the text after its first arrow, without the "Likely cause:" part.

    The arrow is the first ``→``; only a line without one falls back to the
    first ``->``, which a description may contain (``x -> x^2``, an R pipe).
    """
    line = str(text or "")
    arrow = ARROW if ARROW in line else "->"
    if arrow not in line:
        return ""
    target = line.split(arrow, 1)[1]
    return _LIKELY_CAUSE_RE.split(target, maxsplit=1)[0].strip()


def _clause(value: str) -> str:
    """One clause of a defect line: whitespace collapsed to single spaces, trailing periods dropped."""
    return " ".join(str(value).split()).rstrip(". ")


def format_defect(ids: Sequence[str], theme: str, observed: str, target: str, likely_cause: str) -> str:
    """Build a defect line that ``DEFECT_RE`` reads back.

    The line is ``<ID>[, <ID>] (<theme>): <observed> → <target>. Likely cause:
    <likely_cause>.``, the form ``prompts/workflow-prompts/ai-quality-review.md``
    asks a review to write (8a). Each clause is collapsed to one line and loses
    its trailing periods; an empty ``likely_cause`` leaves out the "Likely
    cause:" sentence. ``defect_ids`` reads ``ids`` back, and ``defect_target``
    reads back the ``target`` clause with its closing period, as it does for a
    line a review wrote.

    Raises ``ValueError`` for an empty or duplicated ID list, an ID outside
    ``KNOWN_IDS``, a theme outside ``RENDERS``, an empty ``observed`` or
    ``target``, an arrow in ``observed`` (the first arrow separates observed
    from target) or "Likely cause:" in ``target`` (it ends the target).
    """
    id_list = list(ids)
    if not id_list:
        raise ValueError("a defect line names at least one ID")
    unknown = [cid for cid in id_list if cid not in KNOWN_IDS]
    if unknown:
        raise ValueError(f"unknown defect ID(s): {', '.join(unknown)}")
    if len(set(id_list)) != len(id_list):
        raise ValueError(f"duplicate defect ID in {', '.join(id_list)}")
    if theme not in RENDERS:
        raise ValueError(f"theme must be one of {', '.join(RENDERS)}, not {theme!r}")
    observed_text, target_text, cause_text = _clause(observed), _clause(target), _clause(likely_cause)
    if not observed_text or not target_text:
        raise ValueError("observed and target must not be empty")
    if ARROW in observed_text:
        raise ValueError(f"observed must not contain {ARROW!r}: the first arrow separates observed from target")
    if _LIKELY_CAUSE_RE.search(target_text):
        raise ValueError("target must not contain 'Likely cause:': it ends the target")
    line = f"{', '.join(id_list)} ({theme}): {observed_text} {ARROW} {target_text}."
    if cause_text:
        line += f" Likely cause: {cause_text}."
    return line


def technical_items_at_maximum(checklist: Mapping[str, int]) -> bool:
    """Every VQ, SC, DQ and CQ item is present and at its maximum."""
    technical = [cid for cid in CRITERIA if cid[:2] in TECHNICAL_PREFIXES]
    return all(checklist.get(cid) == CRITERIA[cid] for cid in technical)


def nothing_to_repair(score: int | None, checklist: Mapping[str, int], weaknesses: object) -> bool:
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
    prefix, and the bullet then reads as affirmative.
    """
    for kind, pattern in _KIND_RES:
        if pattern.match(text):
            return kind
    return None
