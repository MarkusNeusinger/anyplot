"""Tests for core.defects — the review feedback grammar.

``automation/scripts/regen_gate.py`` keeps its own copy of these definitions,
because the workflows run it as a single-file copy with the runner's system
Python, where ``core`` is not importable. ``TestRegenGateParity`` pins the two
to the same constants, patterns and results — on hand-written lines and on the
catalogue's stored weaknesses and spec sections — until the pipeline imports
this module.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
import yaml

from automation.scripts import regen_gate
from core import defects
from core.defects import (
    AR_IDS,
    CRITERIA,
    DEFECT,
    DEFECT_RE,
    KIND_EXPECTED,
    KIND_SHOWS,
    KNOWN_IDS,
    LEGACY,
    MAX_SUGGESTIONS,
    NOTHING_TO_REPAIR_MIN,
    RENDERS,
    SUGGESTION,
    characteristic_kind,
    defect_ids,
    defect_target,
    format_defect,
    is_cq04_code_defect,
    nothing_to_repair,
    parse_characteristics,
    technical_items_at_maximum,
    weakness_class,
)


REPO_ROOT = Path(__file__).resolve().parents[3]

# Lines in every shape the grammar distinguishes: the prompt's own examples,
# multi-ID and code lines, suggestions, legacy text and malformed near-misses.
LINES: list[Any] = [
    "VQ-01 (dark): tick labels render near-black on the #1A1A17 background and cannot be read → light text "
    "from the INK_SOFT token. Likely cause: ax.tick_params colors not set from INK_SOFT.",
    "VQ-05 (both): x-axis label 'Date' at 18 pt dominates the axis for its short content → about 10 pt (−8 pt). "
    "Likely cause: xlabel fontsize=18.",
    "VQ-01, VQ-05 (both): title overflows past the plot edge at about 95 % of the width → under 90 % (about −6 pt). "
    "Likely cause: title fontsize=18.",
    "VQ-03, SC-04 (both): the size legend's circles are drawn in the page color → fill and outline them like the "
    "data marks. Likely cause: `guide_legend()` without `override.aes`.",
    "CQ-04 (code): a `make_legend()` helper that is never called → delete both. Likely cause: a replaced approach.",
    "CQ-04 (code): a hand-written autocorrelation loop → `acf(series, nlags=35)`. Likely cause: statsmodels unused.",
    "CQ-02, CQ-04 (code): x -> x^2 written out → `np.square(x)`.",
    "CQ-04 (light): wrong render tag for a code defect → code.",
    "AR-09 (both): the legend is clipped at the right canvas edge → inside the canvas.",
    "XX-01 (both): unknown family → not a defect line.",
    "VQ-99 (both): unknown number in a known family still reads as a defect line → check-feedback reports it.",
    "VQ-1 (both): one-digit number.",
    "VQ-01 (both):no space after the colon.",
    "VQ-01 (Both): capitalised render tag.",
    "VQ-01,VQ-02 (both): no space after the comma.",
    "  VQ-02 (light): leading whitespace is stripped → still a defect line.",
    "VQ-07 (both): no arrow at all, so no target.",
    "VQ-07 (both): only an ascii arrow -> its target. Likely cause: palette index.",
    "Suggestion: a focal annotation on the peak would tell the story.",
    "Suggestion:missing space.",
    "suggestion: lower case.",
    "Tick labels are slightly small.",
    "",
    "   ",
    None,
    42,
]


def _real_weaknesses(stride: int = 6) -> list[str]:
    """Every ``stride``-th stored review's weaknesses from the catalogue metadata."""
    loader = getattr(yaml, "CSafeLoader", yaml.SafeLoader)
    out: list[str] = []
    for path in sorted(REPO_ROOT.glob("plots/*/metadata/*/*.yaml"))[::stride]:
        data = yaml.load(path.read_text(encoding="utf-8"), Loader=loader) or {}
        weaknesses = (data.get("review") or {}).get("weaknesses") or []
        out.extend(str(w) for w in weaknesses)
    return out


def _spec_texts() -> list[str]:
    return [p.read_text(encoding="utf-8") for p in sorted(REPO_ROOT.glob("plots/*/specification.md"))]


def _full_checklist(**overrides: int) -> dict[str, int]:
    return {**CRITERIA, **overrides}


class TestWeaknessClass:
    @pytest.mark.parametrize(
        ("line", "cls"),
        [
            (LINES[0], DEFECT),
            ("CQ-04 (code): x → y.", DEFECT),
            ("XX-01 (both): text", LEGACY),
            ("VQ-01 (Both): text", LEGACY),
            ("Suggestion: text", SUGGESTION),
            ("Suggestion:text", LEGACY),
            ("Plain prose", LEGACY),
            ("", LEGACY),
            (None, LEGACY),
        ],
    )
    def test_classes(self, line, cls):
        assert weakness_class(line) == cls

    def test_defect_ids(self):
        assert defect_ids(LINES[2]) == ["VQ-01", "VQ-05"]
        assert defect_ids("Suggestion: x") == []
        assert defect_ids(None) == []

    def test_cq04_code_defect(self):
        assert is_cq04_code_defect("CQ-04 (code): a loop → `acf()`.")
        assert is_cq04_code_defect("CQ-02, CQ-04 (code): x → y.")
        assert not is_cq04_code_defect("CQ-04 (light): x → y.")
        assert not is_cq04_code_defect("CQ-03 (code): x → y.")

    def test_defect_target(self):
        assert defect_target(LINES[1]) == "about 10 pt (−8 pt)."
        assert defect_target("CQ-02 (code): x -> x^2 written out → `np.square(x)`.") == "`np.square(x)`."
        assert defect_target("VQ-07 (both): ascii -> target. Likely cause: idx.") == "target."
        assert defect_target("VQ-07 (both): no arrow") == ""


class TestFormatDefect:
    @pytest.mark.parametrize(
        ("ids", "theme", "observed", "target", "cause"),
        [
            (["VQ-05"], "both", "x-axis label 'Date' at 18 pt dominates the axis", "about 10 pt (−8 pt)", "xlabel"),
            (["VQ-01", "VQ-05"], "light", "title at 95 % of the width.", "under 90 %.", "title fontsize=18."),
            (["CQ-04"], "code", "a hand-written autocorrelation loop", "`acf(series, nlags=35)`", "no statsmodels"),
            (["AR-09"], "dark", "legend clipped at the right edge", "inside the canvas", ""),
            (["DQ-03"], "both", "x -> x^2 mislabelled", "a target → with an arrow", "the label"),
        ],
    )
    def test_round_trip(self, ids, theme, observed, target, cause):
        line = format_defect(ids, theme, observed, target, cause)
        assert DEFECT_RE.match(line)
        assert weakness_class(line) == DEFECT
        assert defect_ids(line) == ids
        assert defect_target(line) == target.rstrip(".") + "."
        assert is_cq04_code_defect(line) == ("CQ-04" in ids and theme == "code")
        assert ("Likely cause:" in line) == bool(cause)
        assert ".." not in line
        # The pipeline's own reader agrees.
        assert regen_gate.weakness_class(line) == regen_gate.DEFECT
        assert regen_gate.defect_target(line) == defect_target(line)

    def test_exact_form(self):
        assert (
            format_defect(["VQ-03"], "both", "32 sparse points drawn at 4 px", "10–14 px (+6 to +10 px)", "scatter s=4")
            == "VQ-03 (both): 32 sparse points drawn at 4 px → 10–14 px (+6 to +10 px). Likely cause: scatter s=4."
        )

    def test_collapses_whitespace_to_one_line(self):
        line = format_defect(("VQ-02",), "dark", "  label\noverlaps\tthe   bubble ", " clear it\n", "offset\n")
        assert line == "VQ-02 (dark): label overlaps the bubble → clear it. Likely cause: offset."
        assert "\n" not in line

    @pytest.mark.parametrize(
        ("ids", "theme", "observed", "target"),
        [
            ([], "both", "o", "t"),
            (["VQ-99"], "both", "o", "t"),
            (["XX-01"], "both", "o", "t"),
            (["VQ-01", "VQ-01"], "both", "o", "t"),
            (["VQ-01"], "Both", "o", "t"),
            (["VQ-01"], "print", "o", "t"),
            (["VQ-01"], "both", "  ", "t"),
            (["VQ-01"], "both", "o", "..."),
            (["VQ-01"], "both", "a → b", "t"),
            (["VQ-01"], "both", "o", "t. Likely cause: x"),
        ],
    )
    def test_rejects_lines_that_would_read_back_differently(self, ids, theme, observed, target):
        with pytest.raises(ValueError):
            format_defect(ids, theme, observed, target, "cause")

    def test_vocabulary(self):
        assert KNOWN_IDS == set(CRITERIA) | set(AR_IDS)
        assert len(CRITERIA) == 24 and sum(CRITERIA.values()) == 100
        assert RENDERS == ("light", "dark", "both", "code")
        assert all(DEFECT_RE.match(f"{cid} (both): x") for cid in KNOWN_IDS)


class TestNothingToRepair:
    def test_clean_technical_sheet_qualifies(self):
        checklist = _full_checklist(**{"DE-01": 4, "DE-02": 3, "DE-03": 3, "LM-01": 3, "LM-02": 3})
        score = sum(checklist.values())
        assert score >= NOTHING_TO_REPAIR_MIN
        assert technical_items_at_maximum(checklist)
        assert nothing_to_repair(score, checklist, ["Suggestion: a focal highlight."])

    def test_a_defect_line_or_a_technical_deduction_disqualifies(self):
        checklist = _full_checklist(**{"DE-01": 4})
        score = sum(checklist.values())
        assert not nothing_to_repair(score, checklist, ["DE-01 (both): flat → depth."])
        deducted = _full_checklist(**{"VQ-01": 7})
        assert not technical_items_at_maximum(deducted)
        assert not nothing_to_repair(sum(deducted.values()), deducted, [])

    @pytest.mark.parametrize(
        ("score", "weaknesses", "drop"),
        [
            (None, [], None),
            (79, [], None),
            (95, [], None),
            (96, "not a list", None),
            (96, [1], None),
            (96, [], "LM-02"),
        ],
    )
    def test_fails_closed(self, score, weaknesses, drop):
        checklist = _full_checklist(**{"DE-01": 4})
        if drop:
            checklist.pop(drop)
        assert not nothing_to_repair(score, checklist, weaknesses)


class TestCharacteristics:
    SPEC = (
        "# spec\n\n## Description\n\n- not this one\n\n"
        "## What a good version looks like\n\n"
        "- A good version shows: the peak labelled\n  and wrapped\n"
        "- **Expected, not a defect:** overlapping markers\n  - nested point\n\n"
        "1. a numbered bullet without a prefix\n"
        "## Notes\n\n- ignored\n"
    )

    def test_parse(self):
        assert parse_characteristics(self.SPEC) == [
            "A good version shows: the peak labelled and wrapped",
            "**Expected, not a defect:** overlapping markers; nested point",
            "a numbered bullet without a prefix",
        ]
        assert parse_characteristics("# spec\n\n- no section\n") == []

    def test_kind(self):
        kinds = [characteristic_kind(item) for item in parse_characteristics(self.SPEC)]
        assert kinds == [KIND_SHOWS, KIND_EXPECTED, None]
        assert characteristic_kind("Labels are expected, not a defect: mid-sentence") is None


# Names the regen gate must keep exposing with the same values (its callers:
# review_retest.py, spec_characteristics_lint.py, the workflow tests).
SHARED_CONSTANTS = (
    "CRITERIA",
    "AR_IDS",
    "DEFECT",
    "SUGGESTION",
    "LEGACY",
    "MAX_SUGGESTIONS",
    "CODE_RULE",
    "TECHNICAL_PREFIXES",
    "NOTHING_TO_REPAIR_MIN",
    "SHOWS_PREFIX",
    "EXPECTED_PREFIX",
    "KIND_SHOWS",
    "KIND_EXPECTED",
)
SHARED_PATTERNS = (
    "DEFECT_RE",
    "SUGGESTION_RE",
    "CHARACTERISTICS_HEADING_RE",
    "NEXT_SECTION_RE",
    "TOP_LEVEL_BULLET_RE",
    "NESTED_MARKER_RE",
    "_DEFECT_ID",
    "_LIKELY_CAUSE_RE",
)
SHARED_FUNCTIONS = (
    "weakness_class",
    "defect_ids",
    "is_cq04_code_defect",
    "defect_target",
    "technical_items_at_maximum",
    "nothing_to_repair",
    "parse_characteristics",
    "characteristic_kind",
)


class TestRegenGateParity:
    @pytest.mark.parametrize("name", SHARED_CONSTANTS + SHARED_PATTERNS + SHARED_FUNCTIONS)
    def test_regen_gate_still_exposes_the_name(self, name):
        assert hasattr(regen_gate, name), name
        assert hasattr(defects, name), name

    @pytest.mark.parametrize("name", SHARED_CONSTANTS)
    def test_constants_are_equal(self, name):
        assert getattr(regen_gate, name) == getattr(defects, name)

    @pytest.mark.parametrize("name", SHARED_PATTERNS)
    def test_patterns_are_equal(self, name):
        ours, theirs = getattr(defects, name), getattr(regen_gate, name)
        if isinstance(ours, str):
            assert ours == theirs
        else:
            assert (ours.pattern, ours.flags) == (theirs.pattern, theirs.flags)

    def test_kind_patterns_are_equal(self):
        ours = [(kind, p.pattern, p.flags) for kind, p in defects._KIND_RES]
        theirs = [(kind, p.pattern, p.flags) for kind, p in regen_gate._KIND_RES]
        assert ours == theirs

    def test_line_functions_agree_on_the_corpus(self):
        corpus = LINES + _real_weaknesses()
        assert len(corpus) > 1000  # the catalogue sample is really there
        for name in ("weakness_class", "defect_ids", "is_cq04_code_defect", "defect_target"):
            ours, theirs = getattr(defects, name), getattr(regen_gate, name)
            mismatches = [line for line in corpus if ours(line) != theirs(line)]
            assert not mismatches, (name, mismatches[:3])

    def test_characteristics_agree_on_every_spec(self):
        specs = _spec_texts()
        assert len(specs) > 100
        for text in specs:
            items = parse_characteristics(text)
            assert items == regen_gate.parse_characteristics(text)
            assert [characteristic_kind(i) for i in items] == [regen_gate.characteristic_kind(i) for i in items]

    def test_nothing_to_repair_agrees(self):
        de_lm = {"DE-01": 4, "DE-02": 3, "DE-03": 3, "LM-01": 3, "LM-02": 3}
        cases: list[tuple[Any, dict[str, int], Any]] = []
        for overrides in ({}, de_lm, {**de_lm, "VQ-01": 7}, {**de_lm, "CQ-05": 0}):
            checklist = _full_checklist(**overrides)
            total = sum(checklist.values())
            for score in (None, 79, total, total - 1):
                for weaknesses in ([], ["Suggestion: x"], ["DE-01 (both): x → y."], "nope", [3]):
                    cases.append((score, checklist, weaknesses))
        for score, checklist, weaknesses in cases:
            expected = regen_gate.nothing_to_repair(score, checklist, weaknesses)
            assert nothing_to_repair(score, checklist, weaknesses) == expected, (score, weaknesses)
            assert technical_items_at_maximum(checklist) == regen_gate.technical_items_at_maximum(checklist)
        assert any(regen_gate.nothing_to_repair(*case) for case in cases)

    def test_max_suggestions_is_the_prompts_limit(self):
        assert MAX_SUGGESTIONS == 3
