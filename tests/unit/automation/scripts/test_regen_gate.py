"""Tests for automation.scripts.regen_gate — the regen keep-vs-replace decision.

Locks the contract between prompts/workflow-prompts/ai-quality-review.md step
8b (review_regen.json), the extractor that assigns weakness ids, and the gate
step in .github/workflows/impl-review.yml.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest
import yaml

from automation.scripts.regen_gate import (
    CARRIER_CRITERIA,
    CRITERIA,
    KEEP,
    KIND_EXPECTED,
    KIND_SHOWS,
    MERGE,
    REASON_CODES,
    RECORD_KEYS,
    WRITEBACK_CODES,
    GateInput,
    build_record,
    call_count,
    characteristic_kind,
    checklist_scores,
    classify_improvements,
    decide,
    is_cq04_code_defect,
    is_removal,
    load_checklist_scores,
    load_weakness_classes,
    load_weakness_texts,
    main,
    parse_characteristics,
    parse_record_markers,
    permission_refs,
    record_token,
    render_previous_review,
    render_record_marker,
    render_summary,
    replacement_tokens,
    reset_header_score,
    source_language,
    validate_record,
    validate_regen,
    weakness_class,
    weakness_ids,
)


KNOWN = frozenset({"W1", "W2", "W3"})
# The re-score deducts VQ-03 (4 of 6) and the new render scores it 6 of 6, so
# the fixture's W2 (classed a VQ-03 defect) carries the merge; every other
# item sits at its maximum in both.
PREV_CHECKLIST = {**CRITERIA, "VQ-03": 4}
NEW_CHECKLIST = dict(CRITERIA)
CATEGORY_KEYS = {
    "VQ": "visual_quality",
    "DE": "design_excellence",
    "SC": "spec_compliance",
    "DQ": "data_quality",
    "CQ": "code_quality",
    "LM": "library_mastery",
}


def _with_kind(improvements, kind: str = "fix"):
    """Every improvement object without a ``kind`` gets one (P3-era fixtures keep their meaning)."""
    if not isinstance(improvements, list):
        return improvements
    return [{"kind": kind, **item} if isinstance(item, dict) and "kind" not in item else item for item in improvements]


def _regen(**overrides) -> dict:
    """A valid review_regen.json; every improvement without a ``kind`` is a ``fix``.
    A missing kind is tested through explicit fixtures (``_no_kind``)."""
    payload = {
        "prev_rescored": 85,
        "prev_checklist": dict(PREV_CHECKLIST),
        "prev_weaknesses": [{"ref": "W2", "class": "defect", "rule": "VQ-03"}],
        "improvements": [
            {"ref": "W2", "what": "Size legend circles filled", "where_visible": "size legend, both renders"}
        ],
        "regressions": [],
        "scenario_changed": False,
        "encodings_added": [],
        "change_request_applied": None,
    }
    payload.update(overrides)
    if "improvements" in payload:
        payload["improvements"] = _with_kind(payload["improvements"])
    return payload


def _no_kind(payload: dict) -> dict:
    """``payload`` with the ``kind`` key removed from every improvement."""
    return {
        **payload,
        "improvements": [
            {k: v for k, v in item.items() if k != "kind"} if isinstance(item, dict) else item
            for item in payload["improvements"]
        ],
    }


def _inp(score: int | None = 85, regen=None, **overrides) -> GateInput:
    fields = {
        "spec_id": "scatter-annotated",
        "score": score,
        "regen": _regen() if regen is None else regen,
        "known_weakness_ids": KNOWN,
        "characteristic_count": 0,
        "prev_renders": True,
        "canvas_failed": False,
        "change_request_present": False,
        "new_checklist": NEW_CHECKLIST,
    }
    fields.update(overrides)
    return GateInput(**fields)


def _checklist_json(scores: dict[str, int]) -> dict:
    """The six-category review_checklist.json shape for a flat score map."""
    out: dict = {}
    for cid, score in scores.items():
        cat = out.setdefault(CATEGORY_KEYS[cid[:2]], {"score": 0, "max": 0, "items": []})
        top = CRITERIA[cid]
        cat["items"].append({"id": cid, "name": cid, "score": score, "max": top, "passed": score == top, "comment": ""})
        cat["score"] += score
        cat["max"] += top
    return out


class TestScoreRule:
    """new_score >= prev_rescored - 1, against the RE-SCORED predecessor."""

    def test_equal_score_merges(self):
        assert decide(_inp(score=85)).verdict == MERGE

    def test_one_below_rescored_merges(self):
        result = decide(_inp(score=84))
        assert result.verdict == MERGE
        assert result.prev_rescored == 85

    def test_two_below_rescored_keeps(self):
        result = decide(_inp(score=83))
        assert result.verdict == KEEP
        assert "83 < re-scored predecessor 85 - 1" in result.reason

    def test_stored_score_plays_no_part(self):
        # prev_rescored 70, new 72: merges however high the stored score was
        # (the gate never sees it — display only).
        assert decide(_inp(score=72, regen=_regen(prev_rescored=70))).verdict == MERGE

    def test_score_zero_keeps(self):
        result = decide(_inp(score=0, regen=_regen(prev_rescored=0)))
        assert result.verdict == KEEP
        assert "scored 0" in result.reason

    def test_missing_score_keeps(self):
        assert decide(_inp(score=None)).verdict == KEEP


class TestImprovements:
    def test_no_improvements_keeps(self):
        result = decide(_inp(regen=_regen(improvements=[])))
        assert result.verdict == KEEP
        assert "no visible improvement" in result.reason

    def test_missing_where_visible_keeps(self):
        imp = [{"ref": "W2", "what": "Legend fixed"}]
        assert decide(_inp(regen=_regen(improvements=imp))).verdict == KEEP

    def test_blank_where_visible_keeps(self):
        imp = [{"ref": "W2", "what": "Legend fixed", "where_visible": "   "}]
        assert decide(_inp(regen=_regen(improvements=imp))).verdict == KEEP

    def test_one_visible_among_invisible_merges(self):
        imp = [
            {"ref": "new", "what": "Refactored loop", "where_visible": ""},
            {
                "ref": "P1",
                "rule": "VQ-03",
                "what": "Title no longer crowds the legend",
                "where_visible": "top right, light render",
            },
        ]
        assert decide(_inp(regen=_regen(improvements=imp))).verdict == MERGE

    def test_unknown_w_id_keeps(self):
        imp = [{"ref": "W9", "what": "Legend fixed", "where_visible": "legend"}]
        result = decide(_inp(regen=_regen(improvements=imp)))
        assert result.verdict == KEEP
        assert "W9 is not a weakness id" in result.reason

    def test_w_ref_without_previous_weaknesses_keeps(self):
        assert decide(_inp(known_weakness_ids=frozenset())).verdict == KEEP

    def test_c_ref_without_characteristic_section_keeps(self):
        imp = [{"ref": "C1", "what": "Overlap handled with alpha", "where_visible": "dense cluster"}]
        result = decide(_inp(regen=_regen(improvements=imp), characteristic_count=0))
        assert result.verdict == KEEP
        assert "C1 does not exist" in result.reason

    def test_c_ref_within_characteristic_section_merges(self):
        imp = [{"ref": "C2", "what": "Overlap handled with alpha", "where_visible": "dense cluster"}]
        assert decide(_inp(regen=_regen(improvements=imp), characteristic_count=3)).verdict == MERGE

    @pytest.mark.parametrize("ref", ["W0", "w0", "X1", "", None, 3, "new2"])
    def test_malformed_ref_keeps(self, ref):
        imp = [{"ref": ref, "what": "x", "where_visible": "y"}]
        assert decide(_inp(regen=_regen(improvements=imp))).verdict == KEEP


class TestPermissionRefs:
    """An "Expected, not a defect" bullet is a permission, never an improvement
    (the bubble-overlap leak: "overlap now visible" cited as satisfying C2)."""

    def test_permission_only_improvement_keeps(self):
        imp = [{"ref": "C2", "what": "Bubbles now overlap in the dense cluster", "where_visible": "centre, both"}]
        result = decide(_inp(regen=_regen(improvements=imp), characteristic_count=5, permission_refs=frozenset({"C2"})))
        assert result.verdict == KEEP
        assert result.reason.startswith("no visible improvement (C2 = 'Expected, not a defect' bullet")
        assert "not counted as an improvement" in result.reason
        assert "where_visible" not in result.reason  # the item had one; that is not why it failed

    def test_permission_next_to_a_real_improvement_merges_with_a_note(self):
        imp = [
            {"ref": "C2", "what": "Overlap visible", "where_visible": "centre"},
            {"ref": "C4", "what": "Size legend circles filled", "where_visible": "legend, both renders"},
        ]
        result = decide(_inp(regen=_regen(improvements=imp), characteristic_count=5, permission_refs=frozenset({"C2"})))
        assert result.verdict == MERGE
        assert result.reason.startswith("1 visible improvement(s)")
        assert "(C2 = 'Expected, not a defect' bullet, not counted as an improvement)" in result.reason

    def test_several_permissions_are_listed_in_order(self):
        imp = [{"ref": "C5", "what": "a", "where_visible": "x"}, {"ref": "C2", "what": "b", "where_visible": "y"}]
        result = decide(
            _inp(regen=_regen(improvements=imp), characteristic_count=5, permission_refs=frozenset({"C2", "C5"}))
        )
        assert result.verdict == KEEP
        assert "(C2, C5 = 'Expected, not a defect' bullets, not counted as an improvement)" in result.reason

    def test_permission_ref_does_not_invalidate_the_file(self):
        imp = [{"ref": "C2", "what": "Overlap", "where_visible": "centre"}]
        result = decide(_inp(regen=_regen(improvements=imp), characteristic_count=3, permission_refs=frozenset({"C2"})))
        assert not result.reason.startswith("invalid")

    def test_unprefixed_section_counts_every_c_ref(self):
        """Backward compatible: a section without kind prefixes has no permissions."""
        spec = "## What a good version looks like\n- Overlap is expected, not a defect\n- Legend readable\n"
        items = parse_characteristics(spec)
        assert permission_refs(items) == frozenset()
        imp = [{"ref": "C1", "what": "Overlap handled", "where_visible": "centre"}]
        inp = _inp(
            regen=_regen(improvements=imp), characteristic_count=len(items), permission_refs=permission_refs(items)
        )
        assert decide(inp).verdict == MERGE

    def test_summary_marks_the_permission(self):
        imp = [
            {"ref": "C2", "what": "Overlap visible", "where_visible": "centre"},
            {"ref": "W2", "what": "Legend fixed", "where_visible": "legend"},
        ]
        result = decide(_inp(regen=_regen(improvements=imp), characteristic_count=3, permission_refs=frozenset({"C2"})))
        text = render_summary(result, "90", 85)
        assert "- `C2` Overlap visible — centre _(permission, not counted)_" in text
        assert "- `W2` Legend fixed — legend _(defect: VQ-03, 4 → 6)_\n" in text


class TestRegressions:
    def test_any_regression_keeps(self):
        reg = [{"what": "Size legend lost", "where_visible": "right margin"}]
        result = decide(_inp(regen=_regen(regressions=reg)))
        assert result.verdict == KEEP
        assert "1 regression(s)" in result.reason

    def test_regression_without_what_is_invalid(self):
        assert decide(_inp(regen=_regen(regressions=[{"where_visible": "x"}]))).verdict == KEEP

    def test_scenario_changed_on_basic_keeps(self):
        result = decide(_inp(spec_id="bubble-basic", regen=_regen(scenario_changed=True)))
        assert result.verdict == KEEP
        assert "data scenario replaced" in result.reason

    def test_encodings_added_on_basic_keeps(self):
        result = decide(_inp(spec_id="bubble-basic", regen=_regen(encodings_added=["color by region"])))
        assert result.verdict == KEEP
        assert "color by region" in result.reason

    def test_scenario_changed_on_basic_with_applied_change_request_merges(self):
        regen = _regen(scenario_changed=True, encodings_added=["color"], change_request_applied=True)
        assert decide(_inp(spec_id="bubble-basic", regen=regen, change_request_present=True)).verdict == MERGE

    def test_claimed_change_request_without_one_does_not_exempt(self):
        regen = _regen(scenario_changed=True, change_request_applied=True)
        assert decide(_inp(spec_id="bubble-basic", regen=regen, change_request_present=False)).verdict == KEEP

    def test_change_request_not_applied_does_not_exempt(self):
        regen = _regen(scenario_changed=True, change_request_applied=False)
        assert decide(_inp(spec_id="bubble-basic", regen=regen, change_request_present=True)).verdict == KEEP

    def test_scenario_changed_on_non_basic_is_not_a_regression(self):
        regen = _regen(scenario_changed=True, encodings_added=["trend line"])
        assert decide(_inp(spec_id="scatter-annotated", regen=regen)).verdict == MERGE


class TestFailClosed:
    def test_missing_json_keeps(self):
        result = decide(GateInput(spec_id="x", score=90, regen=None, regen_error="missing"))
        assert result.verdict == KEEP
        assert "missing" in result.reason

    def test_not_an_object_keeps(self):
        assert decide(_inp(regen=["not", "an", "object"])).verdict == KEEP

    @pytest.mark.parametrize(
        "overrides",
        [
            {"prev_rescored": "85 points"},
            {"prev_rescored": True},
            {"prev_rescored": 101},
            {"prev_rescored": -1},
            {"improvements": "W2"},
            {"regressions": None},
            {"scenario_changed": "no"},
            {"encodings_added": "color"},
            {"encodings_added": [1]},
            {"change_request_applied": "yes"},
        ],
    )
    def test_invalid_structure_keeps(self, overrides):
        result = decide(_inp(regen=_regen(**overrides)))
        assert result.verdict == KEEP
        assert result.reason.startswith("invalid review_regen.json")

    def test_missing_required_field_keeps(self):
        payload = _regen()
        del payload["scenario_changed"]
        assert decide(_inp(regen=payload)).verdict == KEEP

    def test_change_request_applied_may_be_omitted(self):
        payload = _regen()
        del payload["change_request_applied"]
        assert decide(_inp(regen=payload)).verdict == MERGE

    def test_canvas_failure_keeps(self):
        result = decide(_inp(canvas_failed=True))
        assert result.verdict == KEEP
        assert "canvas" in result.reason

    def test_missing_prev_renders_keeps(self):
        result = decide(_inp(prev_renders=False))
        assert result.verdict == KEEP
        assert "previous production renders" in result.reason

    def test_context_failure_keeps(self):
        assert decide(_inp(context_ok=False)).verdict == KEEP

    def test_validate_reports_every_error(self):
        errors = validate_regen({"prev_rescored": None}, KNOWN, 0)
        assert len(errors) >= 4


class TestCoercion:
    """Predictable model slips are repaired, and the reason says so."""

    def test_digit_string_prev_rescored(self):
        result = decide(_inp(score=85, regen=_regen(prev_rescored="85")))
        assert result.verdict == MERGE
        assert "coerced: prev_rescored '85' -> 85" in result.reason

    def test_lower_case_ref(self):
        imp = [{"ref": "w2", "what": "Legend fixed", "where_visible": "legend"}]
        result = decide(_inp(regen=_regen(improvements=imp)))
        assert result.verdict == MERGE
        assert "ref 'w2' -> 'W2'" in result.reason

    def test_lower_case_unknown_ref_still_keeps(self):
        imp = [{"ref": "w9", "what": "Legend fixed", "where_visible": "legend"}]
        result = decide(_inp(regen=_regen(improvements=imp)))
        assert result.verdict == KEEP
        assert "W9 is not a weakness id" in result.reason

    def test_missing_lists_read_as_empty(self):
        payload = _regen()
        del payload["regressions"]
        del payload["encodings_added"]
        result = decide(_inp(regen=payload))
        assert result.verdict == MERGE
        assert "missing regressions -> []" in result.reason
        assert "missing encodings_added -> []" in result.reason

    @pytest.mark.parametrize("value", ["n/a", "null", "None", ""])
    def test_change_request_applied_placeholder(self, value):
        result = decide(_inp(regen=_regen(change_request_applied=value)))
        assert result.verdict == MERGE
        assert "change_request_applied" in result.reason

    def test_coercion_noted_on_keep_too(self):
        result = decide(_inp(score=80, regen=_regen(prev_rescored="85")))
        assert result.verdict == KEEP
        assert "coerced" in result.reason


class TestSummary:
    def test_mentions_are_neutralised(self):
        imp = [{"ref": "new", "what": "Pinged @octocat", "where_visible": "legend @team"}]
        result = decide(_inp(regen=_regen(improvements=imp)))
        text = render_summary(result, "90", 85)
        assert "@octocat" not in text
        assert "@​octocat" in text
        assert "@​team" in text


class TestSanitizeSource:
    """The predecessor copy handed to the reviewer never shows the stored score."""

    @pytest.mark.parametrize(
        "header",
        [
            '""" anyplot.ai\nscatter-basic: Basic Scatter\nLibrary: altair 5.5 | Python 3.13\nQuality: 92/100 | Updated: 2026-09-01\n"""\n',
            "#' anyplot.ai\n#' scatter-basic: Basic\n#' Library: ggplot2 3.5 | R 4.4\n#' Quality: 88/100 | Created: 2026-05-28\n",
            "# anyplot.ai\n# scatter-basic: Basic\n# Library: makie 0.21 | Julia 1.11\n# Quality: 7/100 | Created: 2026-05-28\n",
            "// anyplot.ai\n// scatter-basic: Basic\n// Library: d3 7.9 | JavaScript 22\n// Quality: 100 / 100 | Updated: 2026-08-24\n",
        ],
    )
    def test_header_score_hidden(self, header):
        from automation.scripts.regen_gate import sanitize_source

        body = "import x\nprint('Quality: 50/100 is data, not a header')\n" * 10
        out = sanitize_source(header + body)
        head = out.splitlines()[: header.count("\n")]
        assert not any(re.search(r"Quality:\s*\d+\s*/\s*100", line) for line in head)
        assert any("Quality: hidden" in line for line in head)
        assert out.count("\n") == (header + body).count("\n")  # line count unchanged
        # Every line after the header is untouched, including the data lines
        # that sit inside the first HEADER_LINES lines.
        assert out.splitlines(keepends=True)[header.count("\n") :] == body.splitlines(keepends=True)

    @pytest.mark.parametrize(
        "line",
        [
            "print('Quality: 50/100 is data, not a header')",
            "# Quality: 50/100 is what the old version scored",
            "    Quality: 50/100 | Created: 2026-05-28",
            "x = 'Quality: 50/100 | Created: 2026-05-28'",
            "// Quality: 50/100 of the points",
        ],
    )
    def test_only_whole_header_lines_are_rewritten(self, line):
        from automation.scripts.regen_gate import sanitize_source

        text = f"import x\n{line}\n"
        assert sanitize_source(text) == text
        assert reset_header_score(text) == text

    def test_crlf_line_endings_are_kept(self):
        from automation.scripts.regen_gate import sanitize_source

        text = "// anyplot.ai\r\n// Quality: 91/100 | Created: 2026-05-28\r\nconst a = 1;\r\n"
        assert (
            sanitize_source(text) == "// anyplot.ai\r\n// Quality: hidden/100 | Created: 2026-05-28\r\nconst a = 1;\r\n"
        )

    def test_cli(self, tmp_path):
        src = tmp_path / "raw.py"
        src.write_text('"""\nQuality: 91/100 | Updated: 2026-09-01\n"""\n', encoding="utf-8")
        out = tmp_path / "prev.py"
        main(["sanitize-source", "--source", str(src), "--out", str(out)])
        assert "91" not in out.read_text(encoding="utf-8")


class TestExtraction:
    def test_omit_scores_hides_stored_numbers(self):
        data = {
            "quality_score": 93,
            "review": {
                "weaknesses": ["w"],
                "criteria_checklist": {"visual_quality": {"score": 27, "max": 30, "items": []}},
            },
        }
        md, _ = render_previous_review(data, "s", "python", "altair", include_scores=False)
        assert "93" not in md
        assert "27/30" not in md
        assert "### visual_quality" in md
        assert "**W1** (older review): w" in md

    def test_weakness_ids_are_stable_and_skip_blanks(self):
        assert weakness_ids(["a", " ", "b"]) == [{"id": "W1", "text": "a"}, {"id": "W2", "text": "b"}]

    def test_render_previous_review_writes_ids(self):
        data = {
            "quality_score": 90,
            "review": {"strengths": ["clean"], "weaknesses": ["legend invisible", "labels overlap"]},
        }
        md, weaknesses = render_previous_review(data, "bubble-basic", "r", "ggplot2", ["overlap handled with alpha"])
        assert "**W1** (older review): legend invisible" in md
        assert "**W2** (older review): labels overlap" in md
        assert "**C1:** overlap handled with alpha" in md
        assert '(only "A good version shows" bullets can be improvement refs)' in md
        assert "**Previous quality score (stored):** 90" in md
        assert [w["id"] for w in weaknesses] == ["W1", "W2"]
        assert [w["class"] for w in weaknesses] == ["legacy", "legacy"]

    def test_tags_and_headings_follow_the_class(self):
        data = {
            "review": {
                "strengths": ["clean"],
                "weaknesses": [
                    "VQ-03, SC-04 (both): size legend circles invisible → fill them like the marks. Likely cause: guide.",
                    "Suggestion: a subtler grid",
                    "Grid too prominent",
                ],
                "criteria_checklist": {"visual_quality": {"score": 27, "max": 30, "items": []}},
            }
        }
        md, weaknesses = render_previous_review(data, "s", "python", "altair", include_scores=False)
        assert "## Weaknesses — stable ids W1..Wn" in md
        assert "- **W1** (defect): VQ-03, SC-04 (both): size legend" in md
        assert "- **W2** (suggestion): Suggestion: a subtler grid" in md
        assert "- **W3** (older review): Grid too prominent" in md
        assert "## Strengths the previous review credited (keep those the current criteria still credit)" in md
        assert "## Criteria checklist (context — act on the defects, not on ❌ marks)" in md
        assert "FIX these" not in md and "KEEP these" not in md
        assert [w["class"] for w in weaknesses] == ["defect", "suggestion", "legacy"]

    def test_guidance_explains_the_classes_and_never_mentions_the_gate(self):
        """The regen reviewer reads the same file (8b step 2), so the paragraph
        must not reveal what carries a merge (D7)."""
        md, _ = render_previous_review({"review": {"weaknesses": ["a"]}}, "s", "python", "altair")
        paragraph = md[md.index("Defects are fixes to make.") :].split("\n\n", 1)[0]
        assert "Suggestions are ideas the previous review did not require" in paragraph
        assert "Older notes predate the current rubric" in paragraph
        assert "is obsolete" in paragraph
        for word in ("gate", "merge", "carr", "count"):
            assert word not in paragraph.lower(), word

    def test_legacy_list_is_tagged_older_review_on_every_line(self):
        weaknesses = ["Legend too small", "DE-02 (4/6): spines remain", "Consider adding a trend line"]
        md, items = render_previous_review({"review": {"weaknesses": weaknesses}}, "s", "python", "altair")
        tagged = [line for line in md.splitlines() if line.startswith("- **W")]
        assert len(tagged) == 3
        assert all("(older review)" in line for line in tagged)
        assert {w["class"] for w in items} == {"legacy"}

    def test_scalar_keys_in_an_older_checklist_are_skipped(self):
        """16 stored reviews carry total_score / score_caps_applied next to the
        categories; context used to raise on them, so their regens kept with
        context_failed."""
        checklist = {
            "visual_quality": {"score": 27, "max": 30, "items": [{"id": "VQ-01", "passed": True}, "junk", None]},
            "total_score": 88,
            "score_caps_applied": "none",
            "score_caps": ["x"],
        }
        md, _ = render_previous_review({"review": {"criteria_checklist": checklist}}, "s", "python", "altair")
        assert "### visual_quality  (27/30)" in md
        assert "- ✅ VQ-01" in md
        assert "total_score" not in md and "score_caps" not in md

    def test_parse_characteristics(self):
        spec = (
            "# bubble-basic\n\n## Notes\n- not this\n\n"
            "## What a good version looks like\n\n"
            "- Overlap is expected\n  - nested detail\n1. Sizes scale by area\n* Legend readable\n\n"
            "## Later\n- not this either\n"
        )
        assert parse_characteristics(spec) == [
            "Overlap is expected; nested detail",
            "Sizes scale by area",
            "Legend readable",
        ]

    def test_parse_characteristics_absent(self):
        assert parse_characteristics("# spec\n\n## Notes\n- a\n") == []

    def test_wrapped_line_continues_the_bullet(self):
        spec = "## What a good version looks like\n- A good version shows: bubble area grows\n  with the size value.\n- B\n"
        assert parse_characteristics(spec) == ["A good version shows: bubble area grows with the size value.", "B"]

    def test_blank_line_does_not_end_a_bullet(self):
        spec = "## What a good version looks like\n- A\n\n    continued after a blank line\n\n- B\n"
        assert parse_characteristics(spec) == ["A continued after a blank line", "B"]

    def test_whitespace_inside_a_bullet_is_collapsed(self):
        spec = "## What a good version looks like\n- A good  version shows:   area\n\ttab-indented tail\n"
        assert parse_characteristics(spec) == ["A good version shows: area tab-indented tail"]

    @pytest.mark.parametrize("stop", ["## Later", "# Top"])
    def test_parsing_stops_at_the_next_heading(self, stop):
        spec = f"## What a good version looks like\n- A\n{stop}\n- not this\n  nor this\n"
        assert parse_characteristics(spec) == ["A"]

    def test_sub_heading_does_not_end_the_section(self):
        """Lenient on purpose (the lint rejects it as K2): a ### line is skipped."""
        spec = "## What a good version looks like\n- A\n### Sub\n- B\n"
        assert parse_characteristics(spec) == ["A", "B"]

    def test_indented_line_before_any_bullet_is_ignored(self):
        assert parse_characteristics("## What a good version looks like\n  stray\n- A\n") == ["A"]


class TestCharacteristicKind:
    @pytest.mark.parametrize(
        ("text", "kind"),
        [
            ("A good version shows: area-scaled bubbles.", KIND_SHOWS),
            ("Expected, not a defect: overlapping bubbles.", KIND_EXPECTED),
            ("a good version shows: lower case still reads", KIND_SHOWS),
            ("EXPECTED, NOT A DEFECT: upper case", KIND_EXPECTED),
            ("Expected not a defect: comma missing", KIND_EXPECTED),
            ("**Expected, not a defect:** bold prefix", KIND_EXPECTED),
            ("**A good version shows**: bold prefix, colon outside", KIND_SHOWS),
            ("  A good version shows : spaced", KIND_SHOWS),
            ("Bubble area grows with the size value.", None),
            ("Overlapping bubbles are expected, not a defect: translucency handles them.", None),
            ("A good version shows area-scaled bubbles (no colon).", None),
        ],
    )
    def test_kind(self, text, kind):
        assert characteristic_kind(text) == kind

    def test_permission_refs(self):
        items = [
            "A good version shows: area",
            "Expected, not a defect: overlap",
            "Legend readable",
            "Expected, not a defect: uneven sizes",
        ]
        assert permission_refs(items) == frozenset({"C2", "C4"})


class TestCli:
    def test_context_then_decide_roundtrip(self, tmp_path, monkeypatch, capsys):
        out = tmp_path / "gh_output"
        monkeypatch.setenv("GITHUB_OUTPUT", str(out))
        meta = tmp_path / "meta.yaml"
        meta.write_text(yaml.safe_dump({"quality_score": 88, "review": {"weaknesses": ["a", "b"]}}), encoding="utf-8")
        spec = tmp_path / "specification.md"
        spec.write_text("# s\n\n## What a good version looks like\n- one\n", encoding="utf-8")
        md = tmp_path / "prev.md"
        wj = tmp_path / "weak.json"

        assert (
            main(
                [
                    "context",
                    "--metadata",
                    str(meta),
                    "--spec-id",
                    "bubble-basic",
                    "--language",
                    "python",
                    "--library",
                    "altair",
                    "--spec-file",
                    str(spec),
                    "--out-md",
                    str(md),
                    "--out-weaknesses",
                    str(wj),
                ]
            )
            == 0
        )
        assert "prev_stored=88" in out.read_text()
        assert json.loads(wj.read_text())[1] == {"id": "W2", "text": "b", "class": "legacy"}
        assert "::notice::weakness_classes defect=0 suggestion=0 legacy=2" in capsys.readouterr().out

        regen = tmp_path / "review_regen.json"
        regen.write_text(json.dumps(_regen(prev_rescored=80)), encoding="utf-8")
        # The gate reads the new render's checklist from the directory of --regen-json.
        (tmp_path / "review_checklist.json").write_text(json.dumps(_checklist_json(NEW_CHECKLIST)), encoding="utf-8")
        summary = tmp_path / "summary.md"
        assert (
            main(
                [
                    "decide",
                    "--spec-id",
                    "bubble-basic",
                    "--library",
                    "altair",
                    "--score",
                    "81",
                    "--prev-stored",
                    "88",
                    "--regen-json",
                    str(regen),
                    "--weaknesses-json",
                    str(wj),
                    "--spec-file",
                    str(spec),
                    "--prev-renders",
                    "available",
                    "--summary-out",
                    str(summary),
                ]
            )
            == 0
        )
        stdout = capsys.readouterr().out
        assert (
            "::notice::regen_gate spec=bubble-basic lib=altair prev_stored=88 prev_rescored=80 new=81 verdict=merge"
            in stdout
        )
        assert "verdict=merge" in out.read_text()
        assert "| 88 | 80 | 81 |" in summary.read_text()
        assert "_(defect: VQ-03, 4 → 6)_" in summary.read_text()

        # Without the checklist next to review_regen.json nothing verifies.
        (tmp_path / "review_checklist.json").unlink()
        args = ["decide", "--spec-id", "bubble-basic", "--library", "altair", "--score", "81", "--regen-json"]
        args += [str(regen), "--weaknesses-json", str(wj), "--spec-file", str(spec), "--prev-renders", "available"]
        assert main([*args, "--summary-out", str(summary)]) == 0
        assert "verdict=keep" in capsys.readouterr().out
        assert "_(unverified: VQ-03, 4 → n/a)_" in summary.read_text()

    def test_decide_reads_permissions_from_the_spec_file(self, tmp_path, monkeypatch, capsys):
        """cmd_decide derives the permission refs from --spec-file itself."""
        out = tmp_path / "gh_output"
        monkeypatch.setenv("GITHUB_OUTPUT", str(out))
        spec = tmp_path / "specification.md"
        spec.write_text(
            "# bubble-basic\n\n## Notes\n- n\n\n## What a good version looks like\n\n"
            "- A good version shows: bubble area grows with the size value.\n"
            "- Expected, not a defect: overlapping bubbles in dense regions.\n"
            "- A good version shows: a size legend drawn like the data marks.\n",
            encoding="utf-8",
        )
        regen = tmp_path / "review_regen.json"
        imp = [
            {"ref": "C2", "what": "Bubbles overlap in the dense cluster now", "where_visible": "centre, both renders"}
        ]
        regen.write_text(json.dumps(_regen(prev_rescored=80, improvements=imp)), encoding="utf-8")
        summary = tmp_path / "summary.md"
        record_file = tmp_path / "record.json"
        args = ["decide", "--spec-id", "bubble-basic", "--library", "d3", "--score", "84", "--regen-json", str(regen)]
        args += ["--spec-file", str(spec), "--prev-renders", "available", "--summary-out", str(summary)]
        args += ["--record-out", str(record_file)]
        assert main(args) == 0
        stdout = capsys.readouterr().out
        assert "verdict=keep" in stdout
        assert "code=no_visible_improvement" in stdout
        assert "C2 = 'Expected, not a defect' bullet, not counted as an improvement" in stdout
        assert "verdict=keep" in out.read_text()
        assert "_(permission, not counted)_" in summary.read_text()
        record = json.loads(record_file.read_text(encoding="utf-8"))
        assert record["improvements"]["visible"] == 0
        assert record["improvements"]["permission"] == 1

    def test_decide_invalid_json_keeps(self, tmp_path, monkeypatch, capsys):
        monkeypatch.delenv("GITHUB_OUTPUT", raising=False)
        regen = tmp_path / "review_regen.json"
        regen.write_text("{not json", encoding="utf-8")
        main(["decide", "--spec-id", "x", "--library", "y", "--score", "95", "--regen-json", str(regen)])
        assert "verdict=keep" in capsys.readouterr().out

    def test_decide_missing_json_keeps(self, tmp_path, capsys):
        main(
            [
                "decide",
                "--spec-id",
                "x",
                "--library",
                "y",
                "--score",
                "95",
                "--prev-renders",
                "available",
                "--regen-json",
                str(Path(tmp_path) / "absent.json"),
            ]
        )
        assert "reason=review_regen.json missing" in capsys.readouterr().out


class TestReasonCodes:
    """Every decision branch carries its own machine-readable code."""

    @pytest.mark.parametrize(
        ("overrides", "code"),
        [
            ({"canvas_failed": True}, "canvas_failed"),
            ({"score": None}, "no_score"),
            ({"score": 0}, "score_zero"),
            ({"prev_renders": False}, "prev_renders_missing"),
            ({"context_ok": False}, "context_failed"),
        ],
    )
    def test_precondition_codes(self, overrides, code):
        result = decide(_inp(**overrides))
        assert (result.verdict, result.code) == (KEEP, code)

    def test_missing_and_unreadable_json(self):
        missing = decide(GateInput(spec_id="x", score=90, regen=None, regen_error="missing"))
        unreadable = decide(GateInput(spec_id="x", score=90, regen=None, regen_error="unreadable (bad)"))
        assert missing.code == "regen_json_missing"
        assert unreadable.code == "regen_json_unreadable"

    def test_judge_codes(self):
        assert decide(_inp(regen=_regen(prev_rescored="many"))).code == "regen_json_invalid"
        assert decide(_inp(regen=_regen(regressions=[{"what": "lost legend"}]))).code == "regression"
        assert decide(_inp(regen=_regen(improvements=[]))).code == "no_visible_improvement"
        assert decide(_inp(score=80)).code == "below_tolerance"
        assert decide(_inp()).code == "merge"

    def test_permission_only_improvement_is_no_visible_improvement(self):
        imp = [{"ref": "C2", "what": "Overlap visible", "where_visible": "centre"}]
        result = decide(_inp(regen=_regen(improvements=imp), characteristic_count=3, permission_refs=frozenset({"C2"})))
        assert (result.verdict, result.code) == (KEEP, "no_visible_improvement")

    def test_every_code_is_declared(self):
        seen = {
            decide(_inp(canvas_failed=True)).code,
            decide(_inp(score=None)).code,
            decide(_inp(score=0)).code,
            decide(_inp(prev_renders=False)).code,
            decide(_inp(context_ok=False)).code,
            decide(_inp(score=80)).code,
            decide(_inp(new_checklist={})).code,
            decide(_inp()).code,
        }
        assert "no_defect_improvement" in seen
        assert seen <= set(REASON_CODES)
        assert "script_crashed" in REASON_CODES  # the workflow's fallback

    def test_carrier_check_comes_before_the_tolerance(self):
        """Content checks first, as no_visible_improvement already does."""
        result = decide(_inp(score=70, new_checklist={}))
        assert (result.verdict, result.code) == (KEEP, "no_defect_improvement")

    def test_judgement_facts_are_kept(self):
        result = decide(_inp(spec_id="scatter-x", regen=_regen(scenario_changed=True, encodings_added=["size", " "])))
        assert result.scenario_changed is True
        assert result.encodings_added == 1
        assert result.coerced is False
        assert decide(_inp(regen=_regen(prev_rescored="85"))).coerced is True


class TestGateRecord:
    def _record(self, **overrides) -> dict:
        imp = [
            {"ref": "W2", "what": "Legend fixed @someone", "where_visible": "legend"},
            {"ref": "new", "what": "Refactor", "where_visible": ""},
        ]
        result = decide(_inp(regen=_regen(improvements=imp)))
        fields = {
            "spec_id": "scatter-annotated",
            "library": "chartjs",
            "score": 85,
            "prev_stored": 92,
            "pr": 11926,
            "model": "claude-sonnet-5",
            "criteria_version": "qc-e1373b1495.aqr-15492a059e.sg-7006008fc6.lib-e97ebfa5c3",
            "prompts_tree": "8c118c04cfaf7255e7530ce81075fa199dd84896",
            "at": "2026-10-02T02:31:10Z",
        }
        fields.update(overrides)
        return build_record(result, **fields)

    def test_shape(self):
        record = self._record()
        assert record["v"] == 1
        assert record["verdict"] == "merge"
        assert record["code"] == "merge"
        assert (record["prev_stored"], record["prev_rescored"], record["new"]) == (92, 85, 85)
        assert record["improvements"] == {
            "total": 2,
            "visible": 1,
            "W": 1,
            "P": 0,
            "C": 0,
            "new": 1,
            "permission": 0,
            "obsolete": 0,
            "carriers": 1,
            "suggestion": 0,
            "unverified": 0,
            "de_lm": 0,
            "addition": 0,
            "polish": 0,
            "no_kind": 0,
            "carriers_pn": 0,
            "by_kind": {"fix": 2, "removal": 0, "addition": 0, "polish": 0, "none": 0},
            "code": 0,
        }
        assert record["regressions"] == 0
        assert record["prev_model"] == "n/a"
        assert validate_record(record) == []

    def test_permission_is_listed_but_not_counted_as_visible(self):
        """``visible`` is the number the gate decided on, so it agrees with the code."""
        imp = [
            {"ref": "C2", "what": "Overlap visible", "where_visible": "centre"},
            {"ref": "C4", "what": "Size legend circles filled", "where_visible": "legend"},
        ]
        permissions = frozenset({"C2"})
        merged = decide(_inp(regen=_regen(improvements=imp), characteristic_count=5, permission_refs=permissions))
        record = build_record(merged, spec_id="bubble-basic", library="d3", score=85, prev_stored=90)
        assert (record["verdict"], record["code"]) == ("merge", "merge")
        counts = record["improvements"]
        assert {k: counts[k] for k in ("total", "visible", "W", "P", "C", "new", "permission")} == {
            "total": 2,
            "visible": 1,
            "W": 0,
            "P": 0,
            "C": 2,
            "new": 0,
            "permission": 1,
        }
        assert counts["carriers"] == 1

        kept = decide(_inp(regen=_regen(improvements=imp[:1]), characteristic_count=5, permission_refs=permissions))
        record = build_record(kept, spec_id="bubble-basic", library="d3", score=85, prev_stored=90)
        assert (record["verdict"], record["code"]) == ("keep", "no_visible_improvement")
        assert record["improvements"]["visible"] == 0
        assert record["improvements"]["permission"] == 1
        assert validate_record(record) == []

    def test_contains_no_model_written_text(self):
        text = json.dumps(self._record())
        assert "Legend fixed" not in text
        assert "someone" not in text
        assert "legend" not in text

    def test_every_string_is_a_plain_token(self):
        record = self._record(model="claude sonnet; rm -rf /", criteria_version="<b>qc</b>")
        assert validate_record(record) == []
        assert record["model"] == "claudesonnetrm-rf/"

    def test_validate_rejects_free_text_and_unknown_keys(self):
        record = self._record()
        record["reason"] = "1 regression(s): legend lost"
        record["model"] = "has spaces"
        errors = validate_record(record)
        assert any("unknown key 'reason'" in e for e in errors)
        assert any("record.model is not a plain token" in e for e in errors)

    def test_marker_roundtrip(self):
        record = self._record()
        marker = render_record_marker(record)
        assert marker.startswith("<!-- regen-gate-record:v1 {") and marker.endswith("} -->")
        assert parse_record_markers(f"## Kept\n\ntext\n\n{marker}\n") == [record]

    def test_marker_never_contains_a_double_dash(self):
        record = self._record(model="claude--sonnet", criteria_version="qc--x")
        assert "--" not in json.dumps(record)
        render_record_marker(record)  # does not raise

    def test_marker_refuses_a_record_that_would_break_the_comment(self):
        record = self._record()
        record["model"] = "a--b"
        with pytest.raises(ValueError, match="'--'"):
            render_record_marker(record)
        record["model"] = "a b"
        with pytest.raises(ValueError, match="invalid gate record"):
            render_record_marker(record)

    def test_parse_skips_malformed_markers(self):
        text = '<!-- regen-gate-record:v1 {not json} -->\n<!-- regen-gate-record:v1 {"x":1} -->'
        assert parse_record_markers(text) == []

    def test_validate_rejects_a_foreign_version_verdict_and_code(self):
        bogus = {"v": 999, "spec": "x", "lib": "y", "verdict": "bogus", "code": "bogus"}
        errors = validate_record(bogus)
        assert any("record.v must be 1" in e for e in errors)
        assert any("record.verdict must be" in e for e in errors)
        assert any("record.code is not one of REASON_CODES" in e for e in errors)

    @pytest.mark.parametrize(
        ("key", "value"),
        [("v", True), ("v", "1"), ("v", 2), ("verdict", "MERGE"), ("verdict", None), ("code", ""), ("code", 1)],
    )
    def test_validate_rejects_each_bad_enum_value(self, key, value):
        record = self._record()
        record[key] = value
        assert validate_record(record) != []

    def test_every_reason_code_and_verdict_validates(self):
        for code in REASON_CODES:
            for verdict in (MERGE, KEEP):
                record = {**self._record(), "code": code, "verdict": verdict}
                assert validate_record(record) == [], (code, verdict)

    def test_parse_skips_markers_with_a_foreign_version_verdict_or_code(self):
        good = self._record()
        bad = [{**good, "v": 999}, {**good, "verdict": "bogus"}, {**good, "code": "bogus"}]
        markers = [f"<!-- regen-gate-record:v1 {json.dumps(r, separators=(',', ':'))} -->" for r in bad]
        text = "\n".join([*markers, render_record_marker(good)])
        assert parse_record_markers(text) == [good]

    @pytest.mark.parametrize("status", WRITEBACK_CODES)
    def test_writeback_on_a_keep(self, status):
        """P9b: the verdict step adds `writeback` to keep records, and the marker carries it."""
        kept = decide(_inp(regen=_regen(improvements=[])))
        record = {
            **build_record(kept, spec_id="count-basic", library="ggplot2", score=80, prev_stored=91),
            "writeback": status,
        }
        assert validate_record(record) == []
        assert parse_record_markers(render_record_marker(record)) == [record]

    @pytest.mark.parametrize("value", ["merged", "OPENED", "", None, 1])
    def test_writeback_rejects_other_values(self, value):
        kept = decide(_inp(regen=_regen(improvements=[])))
        record = {
            **build_record(kept, spec_id="count-basic", library="ggplot2", score=80, prev_stored=91),
            "writeback": value,
        }
        assert "record.writeback is not one of WRITEBACK_CODES" in validate_record(record)

    def test_writeback_belongs_to_a_keep(self):
        record = {**self._record(), "writeback": "opened"}
        assert record["verdict"] == "merge"
        assert validate_record(record) == ["record.writeback belongs to a keep record only"]
        assert parse_record_markers(f"<!-- regen-gate-record:v1 {json.dumps(record, separators=(',', ':'))} -->") == []

    def test_record_token(self):
        assert record_token(None) == "n/a"
        assert record_token("  ") == "n/a"
        assert record_token("claude-opus-5-5") == "claude-opus-5-5"
        assert record_token("claude-sonnet-5[1m]") == "claude-sonnet-5[1m]"


class TestDecideProvenanceCli:
    def _decide(self, tmp_path, extra: list[str]) -> list[str]:
        regen = tmp_path / "review_regen.json"
        regen.write_text(json.dumps(_regen(prev_rescored=80, improvements=[])), encoding="utf-8")
        return [
            "decide",
            "--spec-id",
            "bubble-basic",
            "--library",
            "altair",
            "--score",
            "81",
            "--prev-stored",
            "88",
            "--regen-json",
            str(regen),
            "--prev-renders",
            "available",
            *extra,
        ]

    def test_notice_carries_code_model_and_criteria(self, tmp_path, monkeypatch, capsys):
        monkeypatch.delenv("GITHUB_OUTPUT", raising=False)
        main(self._decide(tmp_path, ["--model", "claude-sonnet-5", "--criteria-version", "qc-a.aqr-b.sg-c"]))
        out = capsys.readouterr().out
        notice = next(line for line in out.splitlines() if line.startswith("::notice::regen_gate"))
        assert notice.startswith(
            "::notice::regen_gate spec=bubble-basic lib=altair prev_stored=88 prev_rescored=80 new=81 verdict=keep "
        )
        assert " code=no_visible_improvement model=claude-sonnet-5 criteria=qc-a.aqr-b.sg-c reason=" in notice
        assert "code=no_visible_improvement" in out.splitlines()

    def test_old_argument_set_still_works(self, tmp_path, monkeypatch, capsys):
        monkeypatch.delenv("GITHUB_OUTPUT", raising=False)
        assert main(self._decide(tmp_path, [])) == 0
        notice = next(line for line in capsys.readouterr().out.splitlines() if line.startswith("::notice::"))
        assert "model=" not in notice
        assert " code=no_visible_improvement reason=" in notice

    def test_record_out(self, tmp_path, monkeypatch, capsys):
        monkeypatch.delenv("GITHUB_OUTPUT", raising=False)
        record_file = tmp_path / "record.json"
        args = [
            "--pr",
            "11926",
            "--model",
            "claude-sonnet-5",
            "--criteria-version",
            "qc-a.aqr-b.sg-c.lib-d",
            "--prompts-tree",
            "8c118c04",
            "--prev-model",
            "n/a",
            "--prev-criteria-version",
            "n/a",
            "--record-out",
            str(record_file),
        ]
        main(self._decide(tmp_path, args))
        record = json.loads(record_file.read_text(encoding="utf-8"))
        assert record["pr"] == 11926
        assert record["prev_stored"] == 88
        assert record["prev_rescored"] == 80
        assert record["new"] == 81
        assert record["code"] == "no_visible_improvement"
        assert record["criteria_version"] == "qc-a.aqr-b.sg-c.lib-d"
        assert validate_record(record) == []
        assert record_file.read_text(encoding="utf-8").count("\n") == 1  # one line

    def test_record_failure_never_changes_the_decision(self, tmp_path, monkeypatch, capsys):
        # impl-review.yml turns a non-zero exit into keep/script_crashed, so a
        # record that cannot be written must not fail the decide step.
        gh_output = tmp_path / "gh_output"
        monkeypatch.setenv("GITHUB_OUTPUT", str(gh_output))
        unwritable = tmp_path / "no-such-dir" / "record.json"
        assert main(self._decide(tmp_path, ["--record-out", str(unwritable)])) == 0
        out = capsys.readouterr().out
        assert "::warning::regen gate record not written:" in out
        assert not unwritable.exists()
        outputs = gh_output.read_text(encoding="utf-8").splitlines()
        assert "verdict=keep" in outputs
        assert "code=no_visible_improvement" in outputs

    def test_marker_subcommand(self, tmp_path, monkeypatch, capsys):
        monkeypatch.delenv("GITHUB_OUTPUT", raising=False)
        record_file = tmp_path / "record.json"
        main(self._decide(tmp_path, ["--record-out", str(record_file)]))
        capsys.readouterr()
        assert main(["marker", "--record", str(record_file)]) == 0
        marker = capsys.readouterr().out.strip()
        assert parse_record_markers(marker)[0]["code"] == "no_visible_improvement"

    def test_marker_subcommand_fails_on_missing_or_bad_record(self, tmp_path, capsys):
        assert main(["marker", "--record", str(tmp_path / "absent.json")]) == 1
        bad = tmp_path / "bad.json"
        bad.write_text('{"v": 1, "spec": "x", "lib": "y", "verdict": "keep", "code": "a b"}', encoding="utf-8")
        assert main(["marker", "--record", str(bad)]) == 1
        assert capsys.readouterr().out == ""

    def test_workflow_crash_fallback_record_is_accepted(self, tmp_path, capsys):
        # The shape impl-review.yml writes with jq when this script cannot run.
        fallback = {
            "v": 1,
            "pr": 11926,
            "spec": "bubble-basic",
            "lib": "chartjs",
            "model": "claude-sonnet-5",
            "criteria_version": "n/a",
            "verdict": "keep",
            "code": "script_crashed",
            "at": "2026-10-02T02:31:10Z",
        }
        assert validate_record(fallback) == []
        record_file = tmp_path / "record.json"
        record_file.write_text(json.dumps(fallback), encoding="utf-8")
        assert main(["marker", "--record", str(record_file)]) == 0


class TestContextProvenance:
    def _context(self, tmp_path, review: dict) -> str:
        out = tmp_path / "gh_output"
        meta = tmp_path / "meta.yaml"
        meta.write_text(yaml.safe_dump({"quality_score": 90, "review": review}), encoding="utf-8")
        main(
            [
                "context",
                "--metadata",
                str(meta),
                "--spec-id",
                "s",
                "--language",
                "python",
                "--library",
                "altair",
                "--out-md",
                str(tmp_path / "prev.md"),
                "--out-weaknesses",
                str(tmp_path / "weak.json"),
            ]
        )
        return out.read_text()

    def test_prev_provenance_from_stored_review(self, tmp_path, monkeypatch):
        monkeypatch.setenv("GITHUB_OUTPUT", str(tmp_path / "gh_output"))
        text = self._context(tmp_path, {"model": "claude-opus-5-5", "criteria_version": "qc-a.aqr-b.sg-c.lib-d"})
        assert "prev_model=claude-opus-5-5" in text
        assert "prev_criteria_version=qc-a.aqr-b.sg-c.lib-d" in text

    def test_prev_provenance_absent_is_na(self, tmp_path, monkeypatch):
        monkeypatch.setenv("GITHUB_OUTPUT", str(tmp_path / "gh_output"))
        text = self._context(tmp_path, {"weaknesses": ["a"]})
        assert "prev_model=n/a" in text
        assert "prev_criteria_version=n/a" in text


class TestResetHeaderScore:
    """M3: impl-generate resets the new file's header to `Quality: pending`."""

    @pytest.mark.parametrize(
        "header",
        [
            '""" anyplot.ai\nscatter-basic: Basic Scatter\nLibrary: altair 5.5 | Python 3.13\nQuality: 92/100 | Updated: 2026-09-01\n"""\n',
            "#' anyplot.ai\n#' scatter-basic: Basic\n#' Library: ggplot2 3.5 | R 4.4\n#' Quality: 88/100 | Created: 2026-05-28\n",
            "# anyplot.ai\n# scatter-basic: Basic\n# Library: makie 0.21 | Julia 1.11\n# Quality: 7/100 | Created: 2026-05-28\n",
            "// anyplot.ai\n// scatter-basic: Basic\n// Library: d3 7.9 | JavaScript 22\n// Quality: 100 / 100 | Updated: 2026-08-24\n",
        ],
    )
    def test_header_reset(self, header):
        body = "import x\nprint('Quality: 50/100 is data, not a header')\n" * 10
        out = reset_header_score(header + body)
        head = out.splitlines()[: header.count("\n")]
        assert not any(re.search(r"Quality:\s*\d+\s*/\s*100", line) for line in head)
        assert any(re.search(r"Quality: pending \| (Created|Updated): ", line) for line in head)
        assert out.count("\n") == (header + body).count("\n")
        # The data line inside the first HEADER_LINES lines keeps its number.
        assert out.splitlines(keepends=True)[header.count("\n") :] == body.splitlines(keepends=True)

    def test_pending_header_is_unchanged(self):
        text = "// anyplot.ai\n// x: y\n// Library: d3 7 | JavaScript 22\n// Quality: pending | Created: 2026-06-02\n"
        assert reset_header_score(text) == text

    def test_cli_rewrites_in_place(self, tmp_path):
        src = tmp_path / "impl.js"
        src.write_text("// anyplot.ai\n// Quality: 91/100 | Updated: 2026-09-01\nconst a = 1;\n", encoding="utf-8")
        assert main(["sanitize-source", "--pending", "--source", str(src), "--out", str(src)]) == 0
        assert (
            src.read_text(encoding="utf-8")
            == "// anyplot.ai\n// Quality: pending | Updated: 2026-09-01\nconst a = 1;\n"
        )


# ---------------------------------------------------------------------------
# P3: defects and suggestions, obsolete weaknesses, carriers
# ---------------------------------------------------------------------------


class TestWeaknessClass:
    @pytest.mark.parametrize(
        ("text", "cls"),
        [
            (
                "VQ-03, SC-04 (both): size legend circles invisible on dark → fill them like the marks. "
                "Likely cause: guide_legend without override.aes.",
                "defect",
            ),
            ("AR-09 (light): title clipped at the top edge → shrink the plot area. Likely cause: margin.", "defect"),
            ("VQ-01 (dark): tick labels at 9 px → 12 px, −3 px short. Likely cause: fontsize.", "defect"),
            ("CQ-04 (code): 40 lines without a visible change → drop them. Likely cause: helper loop.", "defect"),
            ("DE-02 (4/6): top and right spines remain", "legacy"),
            ("Suggestion: a focal highlight on the leading bar", "suggestion"),
            ("", "legacy"),
            ("   ", "legacy"),
            (None, "legacy"),
            ("VQ-03 (both):no space after the colon", "legacy"),
            ("vq-03 (both): lower-case id", "legacy"),
            ("VQ-03 (all): unknown render", "legacy"),
            ("suggestion: lower-case prefix", "legacy"),
            ("Grid too prominent", "legacy"),
            ("  Suggestion: surrounding blanks are stripped  ", "suggestion"),
        ],
    )
    def test_class(self, text, cls):
        assert weakness_class(text) == cls

    def test_multi_id_defect_names_each_id(self):
        from automation.scripts.regen_gate import defect_ids

        assert defect_ids("VQ-03, SC-04 (both): x") == ["VQ-03", "SC-04"]
        assert defect_ids("Suggestion: VQ-03 (both): x") == []

    def test_carrier_criteria_are_the_18_vq_sc_dq_cq_items(self):
        assert len(CRITERIA) == 24
        assert sum(CRITERIA.values()) == 100
        assert len(CARRIER_CRITERIA) == 18
        assert not any(c.startswith(("DE", "LM")) for c in CARRIER_CRITERIA)
        assert "DQ-01" not in CARRIER_CRITERIA
        assert {"DQ-02", "DQ-03", "SC-02", "VQ-06"} <= CARRIER_CRITERIA


class TestLoadChecklistScores:
    def test_six_category_shape(self, tmp_path):
        path = tmp_path / "review_checklist.json"
        path.write_text(json.dumps(_checklist_json({"VQ-01": 7, "DE-02": 3, "CQ-05": 1})), encoding="utf-8")
        assert load_checklist_scores(path) == {"VQ-01": 7, "DE-02": 3, "CQ-05": 1}

    @pytest.mark.parametrize("score", [6.0, 7.5, -1, 9, True, "7", None])
    def test_bad_scores_are_dropped(self, score):
        checklist = {"visual_quality": {"items": [{"id": "VQ-01", "score": score}, {"id": "VQ-02", "score": 5}]}}
        assert checklist_scores(checklist) == {"VQ-02": 5}

    def test_unknown_ids_and_duplicates(self):
        checklist = {
            "visual_quality": {"items": [{"id": "VQ-09", "score": 1}, {"id": "VQ-02", "score": 5}]},
            "extra": {"items": [{"id": "VQ-02", "score": 1}, "not an item"]},
            "broken": "not a category",
        }
        assert checklist_scores(checklist) == {"VQ-02": 5}

    def test_missing_and_malformed_files(self, tmp_path):
        assert load_checklist_scores(tmp_path / "absent.json") == {}
        assert load_checklist_scores(None) == {}
        bad = tmp_path / "bad.json"
        bad.write_text("{not json", encoding="utf-8")
        assert load_checklist_scores(bad) == {}
        listed = tmp_path / "list.json"
        listed.write_text("[1, 2]", encoding="utf-8")
        assert load_checklist_scores(listed) == {}

    def test_weakness_classes_default_to_legacy(self, tmp_path):
        path = tmp_path / "weak.json"
        path.write_text(
            json.dumps([{"id": "W1", "text": "a"}, {"id": "W2", "class": "suggestion"}, {"id": "W3", "class": "x"}]),
            encoding="utf-8",
        )
        assert load_weakness_classes(path) == {"W1": "legacy", "W2": "suggestion", "W3": "legacy"}
        assert load_weakness_classes(tmp_path / "absent.json") == {}


def _classes(result) -> list[tuple[str, str, str]]:
    return [(i["ref"], i["class"], i["basis"]) for i in result.improvements]


class TestCarriers:
    """Only a visible improvement that fixes a verified defect, or an
    affirmative characteristic, carries a merge (D2, D11)."""

    def test_verified_w_defect_carries(self):
        result = decide(_inp())
        assert (result.verdict, result.code) == (MERGE, "merge")
        assert _classes(result) == [("W2", "carrier", "criterion")]
        assert (result.improvements[0]["prev_score"], result.improvements[0]["new_score"]) == (4, 6)
        assert "1 carrying (W2)" in result.reason

    def test_equal_new_score_is_unverified(self):
        result = decide(_inp(new_checklist={**NEW_CHECKLIST, "VQ-03": 4}))
        assert (result.verdict, result.code) == (KEEP, "no_defect_improvement")
        assert _classes(result) == [("W2", "suggestion", "unverified")]
        assert "_(unverified: VQ-03, 4 → 4)_" in render_summary(result, "90", 85)

    @pytest.mark.parametrize("rule", ["DE-02", "LM-02", "DE-03", "DE-01", "LM-01", "DQ-01"])
    def test_de_lm_and_dq01_never_carry(self, rule):
        regen = _regen(
            prev_checklist={**PREV_CHECKLIST, rule: 1}, prev_weaknesses=[{"ref": "W2", "class": "defect", "rule": rule}]
        )
        result = decide(_inp(regen=regen, new_checklist={**NEW_CHECKLIST, rule: CRITERIA[rule]}))
        assert (result.verdict, result.code) == (KEEP, "no_defect_improvement")
        assert _classes(result) == [("W2", "suggestion", "de_lm")]
        assert f"_(design, library or coverage point {rule}: does not carry)_" in render_summary(result, "90", 85)
        assert "1 design, library or coverage" in result.reason

    @pytest.mark.parametrize("rule", ["SC-02", "VQ-06", "DQ-02"])
    def test_other_criteria_still_carry(self, rule):
        regen = _regen(
            prev_checklist={**PREV_CHECKLIST, rule: 1}, prev_weaknesses=[{"ref": "W2", "class": "defect", "rule": rule}]
        )
        result = decide(_inp(regen=regen, new_checklist={**NEW_CHECKLIST, rule: CRITERIA[rule]}))
        assert _classes(result) == [("W2", "carrier", "criterion")]

    @pytest.mark.parametrize("checklist", [{}, {"VQ-01": 8}])
    def test_missing_new_checklist_leaves_every_criterion_unverified(self, checklist):
        result = decide(_inp(new_checklist=checklist))
        assert result.code == "no_defect_improvement"

    def test_missing_prev_checklist_lets_only_c_refs_carry(self):
        regen = _regen()
        del regen["prev_checklist"]
        assert decide(_inp(regen=regen)).code == "no_defect_improvement"
        regen["improvements"].append(
            {"ref": "C1", "kind": "fix", "what": "Area-scaled bubbles", "where_visible": "all bubbles"}
        )
        result = decide(_inp(regen=regen, characteristic_count=2))
        assert result.verdict == MERGE
        assert _classes(result)[-1] == ("C1", "carrier", "characteristic")

    def test_w_suggestion_alone_keeps(self):
        regen = _regen(prev_weaknesses=[{"ref": "W2", "class": "suggestion"}])
        result = decide(_inp(regen=regen))
        assert (result.verdict, result.code) == (KEEP, "no_defect_improvement")
        assert "1 visible improvement(s) (1 suggestion), none fixes a verified defect" in result.reason
        assert "_(suggestion: does not carry)_" in render_summary(result, "90", 85)

    def test_obsolete_is_not_counted(self):
        regen = _regen(prev_weaknesses=[{"ref": "W2", "class": "obsolete", "rule": "C2"}])
        result = decide(_inp(regen=regen, characteristic_count=3, permission_refs=frozenset({"C2"})))
        assert (result.verdict, result.code) == (KEEP, "no_visible_improvement")
        assert "obsolete: W2 (C2), not counted" in result.reason
        assert "where_visible" not in result.reason
        assert "_(obsolete: covered by C2, not counted)_" in render_summary(result, "90", 85)

    def test_obsolete_next_to_a_carrier_merges(self):
        regen = _regen(
            prev_weaknesses=[
                {"ref": "W1", "class": "obsolete", "rule": "C2"},
                {"ref": "W2", "class": "defect", "rule": "VQ-03"},
            ],
            improvements=[
                {"ref": "W1", "what": "Less overlap", "where_visible": "cluster"},
                {"ref": "W2", "what": "Legend fixed", "where_visible": "legend"},
            ],
        )
        result = decide(_inp(regen=regen, characteristic_count=3, permission_refs=frozenset({"C2"})))
        assert result.verdict == MERGE
        assert result.reason.startswith("1 visible improvement(s), 1 carrying (W2)")

    @pytest.mark.parametrize("rule", ["C1", "C9", None, "VQ-02"])
    def test_obsolete_with_a_c_id_that_is_no_permission_is_still_obsolete(self, rule):
        entry = {"ref": "W2", "class": "obsolete"} | ({"rule": rule} if rule else {})
        result = decide(_inp(regen=_regen(prev_weaknesses=[entry]), characteristic_count=3))
        assert (result.verdict, result.code) == (KEEP, "no_visible_improvement")
        assert _classes(result) == [("W2", "obsolete", "unlabeled")]
        assert "is not an 'Expected, not a defect' bullet; not counted)_" in render_summary(result, "90", 85)

    def test_stored_suggestion_caps_a_reclassed_defect(self):
        result = decide(_inp(weakness_classes={"W2": "suggestion"}))
        assert (result.verdict, result.code) == (KEEP, "no_defect_improvement")
        assert result.improvements[0]["capped"] is True
        assert "_(suggestion, stored as a suggestion: does not carry)_" in render_summary(result, "90", 85)

    @pytest.mark.parametrize("stored", ["defect", "legacy"])
    def test_stored_defect_or_legacy_is_not_capped(self, stored):
        assert decide(_inp(weakness_classes={"W2": stored})).verdict == MERGE

    def test_downgrade_is_always_allowed(self):
        regen = _regen(prev_weaknesses=[{"ref": "W2", "class": "suggestion"}])
        assert decide(_inp(regen=regen, weakness_classes={"W2": "defect"})).code == "no_defect_improvement"

    @pytest.mark.parametrize(
        "entries",
        [
            [],
            [{"ref": "W1", "class": "defect", "rule": "VQ-03"}],
            [{"ref": "W2"}],
            [{"ref": "W2", "class": "bogus", "rule": "VQ-03"}],
            [{"ref": "W2", "class": "defect"}],
        ],
    )
    def test_unclassified_or_unruled_w_never_carries(self, entries):
        result = decide(_inp(regen=_regen(prev_weaknesses=entries)))
        assert (result.verdict, result.code) == (KEEP, "no_defect_improvement")

    def test_first_entry_per_w_wins(self):
        entries = [{"ref": "W2", "class": "defect", "rule": "VQ-03"}, {"ref": "W2", "class": "suggestion"}]
        assert decide(_inp(regen=_regen(prev_weaknesses=entries))).verdict == MERGE

    @pytest.mark.parametrize("ref", ["P1", "new"])
    def test_p_and_new_carry_their_own_verified_rule(self, ref):
        def run(**item):
            imp = [{"ref": ref, "what": "Legend fixed", "where_visible": "legend", **item}]
            return decide(_inp(regen=_regen(improvements=imp, prev_weaknesses=[])))

        assert run(rule="VQ-03").verdict == MERGE
        assert run(rule="VQ-02").code == "no_defect_improvement"  # 6 → 6: unverified
        assert run().code == "no_defect_improvement"  # no rule
        assert run(rule=None).code == "no_defect_improvement"  # null reads as absent
        assert run(rule="DE-02").code == "no_defect_improvement"
        assert run(rule="bogus").code == "no_defect_improvement"
        assert "_(unverified: no rule)_" in render_summary(run(), "90", 85)

    def test_affirmative_c_carries_without_a_rule(self):
        imp = [{"ref": "C3", "what": "Marks at their data values", "where_visible": "all bubbles"}]
        result = decide(_inp(regen=_regen(improvements=imp, prev_weaknesses=[]), characteristic_count=5))
        assert result.verdict == MERGE
        assert "_(characteristic)_" in render_summary(result, "90", 85)

    def test_c_rule_on_a_w_defect(self):
        regen = _regen(prev_weaknesses=[{"ref": "W2", "class": "defect", "rule": "C3"}])
        assert decide(_inp(regen=regen, characteristic_count=5)).verdict == MERGE
        assert (
            decide(_inp(regen=regen, characteristic_count=5, permission_refs=frozenset({"C3"}))).code
            == "no_defect_improvement"
        )
        assert decide(_inp(regen=regen, characteristic_count=2)).code == "no_defect_improvement"

    def test_ar_rule_carries_only_after_an_auto_reject(self):
        imp = [{"ref": "P1", "rule": "AR-09", "what": "Title no longer clipped", "where_visible": "title, light"}]
        rejected = decide(_inp(score=80, regen=_regen(prev_rescored=0, improvements=imp, prev_weaknesses=[])))
        assert rejected.verdict == MERGE
        assert "_(defect: AR-09)_" in render_summary(rejected, "90", 80)
        scored = decide(_inp(score=80, regen=_regen(prev_rescored=79, improvements=imp, prev_weaknesses=[])))
        assert scored.code == "no_defect_improvement"

    @pytest.mark.parametrize(
        "overrides",
        [
            {"prev_weaknesses": "W2 defect VQ-03"},
            {"prev_weaknesses": [1, None, {"ref": 3}, {"ref": "W2", "class": 5}]},
            {"prev_checklist": "VQ-03 4"},
            {"prev_checklist": {"VQ-03": "4", "XX-01": 1}},
        ],
    )
    def test_malformed_classification_never_invalidates_the_file(self, overrides):
        result = decide(_inp(regen=_regen(**overrides)))
        assert result.code == "no_defect_improvement"
        assert not result.reason.startswith("invalid")

    def test_classification_slips_are_coerced_and_noted(self):
        regen = _regen(prev_weaknesses=[{"ref": "w2", "class": "Defect", "rule": "vq-03"}])
        result = decide(_inp(regen=regen))
        assert result.verdict == MERGE
        assert result.coerced is True
        assert "prev_weaknesses[1].class 'Defect' -> 'defect'" in result.reason
        imp = [{"ref": "P1", "rule": "vq-03", "what": "x", "where_visible": "y"}]
        result = decide(_inp(regen=_regen(improvements=imp)))
        assert result.verdict == MERGE
        assert "rule 'vq-03' -> 'VQ-03'" in result.reason

    @pytest.mark.parametrize("rule", [3, ["VQ-03"], {"id": "VQ-03"}])
    def test_non_string_rule_is_invalid(self, rule):
        imp = [{"ref": "P1", "rule": rule, "what": "x", "where_visible": "y"}]
        assert decide(_inp(regen=_regen(improvements=imp))).code == "regen_json_invalid"

    def test_classify_is_robust_to_payloads_the_gate_rejects(self):
        payload = {"improvements": [{"ref": "W9", "where_visible": "x"}, "junk", {"ref": 3}, {"ref": "C9"}]}
        items = classify_improvements(payload, _inp())
        assert [(i["ref"], i["class"]) for i in items] == [
            ("W9", "suggestion"),
            ("3", "suggestion"),
            ("C9", "suggestion"),
        ]
        assert classify_improvements(None, _inp()) == []
        assert classify_improvements({"improvements": "W2"}, _inp()) == []


# One would-be carrier per ref type: a W classed defect, a P and a new item
# with a verified rule, and an affirmative C id.
CARRIER_ITEMS = {
    "W": {"ref": "W2", "what": "Legend fixed", "where_visible": "legend"},
    "P": {"ref": "P1", "rule": "VQ-03", "what": "Legend fixed", "where_visible": "legend"},
    "new": {"ref": "new", "rule": "VQ-03", "what": "Legend fixed", "where_visible": "legend"},
    "C": {"ref": "C1", "what": "Legend fixed", "where_visible": "legend"},
}


class TestKinds:
    """P3.1: only a fix or a removal carries; an addition, polish or a missing
    kind demotes a would-be carrier to a suggestion and never invalidates the file."""

    def _decide(self, ref_type: str, **kind):
        item = {**CARRIER_ITEMS[ref_type], **kind}
        regen = _regen(improvements=[item])
        if not kind:
            regen = _no_kind(regen)
        return decide(_inp(regen=regen, characteristic_count=3))

    @pytest.mark.parametrize("ref_type", sorted(CARRIER_ITEMS))
    @pytest.mark.parametrize("kind", ["fix", "removal"])
    def test_fix_and_removal_carry(self, ref_type, kind):
        result = self._decide(ref_type, kind=kind)
        assert result.verdict == MERGE
        assert result.improvements[0]["class"] == "carrier"
        assert result.improvements[0]["kind"] == kind

    @pytest.mark.parametrize("ref_type", sorted(CARRIER_ITEMS))
    @pytest.mark.parametrize(
        ("kind", "flag", "label"),
        [
            ("addition", "_(addition: does not carry)_", "1 addition"),
            ("polish", "_(polish of an out-of-scope element: does not carry)_", "1 polish of an out-of-scope element"),
        ],
    )
    def test_addition_and_polish_ride_along(self, ref_type, kind, flag, label):
        result = self._decide(ref_type, kind=kind)
        assert (result.verdict, result.code) == (KEEP, "no_defect_improvement")
        assert (result.improvements[0]["class"], result.improvements[0]["basis"]) == ("suggestion", kind)
        assert flag in render_summary(result, "90", 85)
        assert f"1 visible improvement(s) ({label}), none fixes" in result.reason

    @pytest.mark.parametrize("ref_type", sorted(CARRIER_ITEMS))
    @pytest.mark.parametrize("kind", [{}, {"kind": "kinda"}, {"kind": 3}, {"kind": None}, {"kind": ["fix"]}])
    def test_missing_or_unknown_kind_is_no_kind(self, ref_type, kind):
        result = self._decide(ref_type, **kind)
        assert (result.verdict, result.code) == (KEEP, "no_defect_improvement")
        assert (result.improvements[0]["class"], result.improvements[0]["basis"]) == ("suggestion", "no_kind")
        assert result.improvements[0]["kind"] is None
        assert "_(no kind named: does not carry)_" in render_summary(result, "90", 85)
        assert "1 no kind named" in result.reason
        assert validate_regen(_regen(improvements=[{**CARRIER_ITEMS[ref_type], **kind}]), KNOWN, 3) == []

    def test_kind_is_coerced_and_noted(self):
        result = self._decide("P", kind=" Removal")
        assert result.verdict == MERGE
        assert "kind ' Removal' -> 'removal'" in result.reason

    @pytest.mark.parametrize("kind", ["addition", None])
    def test_other_classes_keep_their_basis(self, kind):
        """The kind only demotes a would-be carrier: a permission, an obsolete W,
        a W suggestion and a DE point stay what they were. An unverified claim
        stays unverified without a kind; an addition claims no defect, so it
        takes its kind as basis instead (it never fails to verify one)."""
        regen = _regen(
            prev_checklist={**PREV_CHECKLIST, "DE-02": 3},
            prev_weaknesses=[{"ref": "W1", "class": "obsolete", "rule": "C2"}, {"ref": "W3", "class": "suggestion"}],
            improvements=[
                {"ref": "C2", "what": "a", "where_visible": "x", "kind": kind},
                {"ref": "W1", "what": "b", "where_visible": "x", "kind": kind},
                {"ref": "W3", "what": "c", "where_visible": "x", "kind": kind},
                {"ref": "P1", "rule": "VQ-02", "what": "d", "where_visible": "x", "kind": kind},
                {"ref": "P2", "rule": "DE-02", "what": "e", "where_visible": "x", "kind": kind},
            ],
        )
        result = decide(_inp(regen=regen, characteristic_count=3, permission_refs=frozenset({"C2"})))
        assert _classes(result) == [
            ("C2", "permission", "permission"),
            ("W1", "obsolete", "labeled"),
            ("W3", "suggestion", "suggestion"),
            ("P1", "suggestion", kind or "unverified"),
            ("P2", "suggestion", "de_lm"),
        ]

    @pytest.mark.parametrize("kind", ["addition", "polish"])
    def test_non_fix_kind_needs_no_rule(self, kind):
        """An addition or polish without a rule is counted under its kind, never as unverified."""
        imp = [{"ref": "P1", "kind": kind, "what": "Percentage labels added", "where_visible": "bars"}]
        result = decide(_inp(regen=_regen(improvements=imp, prev_weaknesses=[])))
        assert (result.verdict, result.code) == (KEEP, "no_defect_improvement")
        assert _classes(result) == [("P1", "suggestion", kind)]
        record = build_record(result, spec_id="count-basic", library="d3", score=85, prev_stored=90)
        assert (record["improvements"][kind], record["improvements"]["unverified"]) == (1, 0)

    def test_one_carrying_item_is_enough(self):
        imp = [{**CARRIER_ITEMS["P"], "kind": "polish"}, {**CARRIER_ITEMS["W"], "kind": "fix"}]
        result = decide(_inp(regen=_regen(improvements=imp)))
        assert result.verdict == MERGE
        assert "1 carrying (W2)" in result.reason


# Round 1 of the verification regens after #11949 and #11950 (13 Sonnet
# regenerations, 2026-09-27): the refs each review cited, the classes P3 gives
# them (PLAN_p3_v2 §8.5) and the item scores that decide each pair — refs,
# classes and numbers only, no model text. The stored predecessor review and
# the new review stand in for prev_checklist and review_checklist.json (round 1
# wrote no prev_checklist). Where round 1's re-score named a predecessor defect
# the stored review had missed (#11958 P1-P3: title segment, canvas, palette;
# #11961: title segment), the re-score deducts it by one point.
BUBBLE = {"characteristic_count": 5, "permission_refs": frozenset({"C2"})}
COUNT = {"characteristic_count": 5, "permission_refs": frozenset({"C5"})}
BAR_ERROR = {"characteristic_count": 5, "permission_refs": frozenset({"C5"})}
ROUND1: dict[int, dict] = {
    11951: {
        "spec": BUBBLE,
        "scores": (83, 74),
        "refs": [("W1", None), ("W2", None), ("C3", None), ("C5", None)],
        "classes": {"W1": ("obsolete", "C2"), "W2": ("suggestion", None)},
        "items": {},
        "expected": (MERGE, "merge"),
    },
    11952: {
        "spec": BUBBLE,
        "scores": (89, 84),
        "refs": [("W1", None)],
        "classes": {"W1": ("obsolete", "C2")},
        "items": {"VQ-02": (4, 6)},
        "expected": (KEEP, "no_visible_improvement"),
    },
    11953: {
        "spec": BUBBLE,
        "scores": (89, 87),
        "refs": [("W1", None), ("W3", None)],
        "classes": {"W1": ("defect", "VQ-02"), "W3": ("defect", "VQ-07")},
        "items": {"VQ-02": (5, 5), "VQ-07": (2, 2)},
        # §8.5 b: merges only when the re-score deducts VQ-02 to 4 or VQ-07 to 1
        # (TestVerificationRound.test_conditional_pairs); the stored numbers keep.
        "expected": (KEEP, "no_defect_improvement"),
    },
    11954: {
        "spec": COUNT,
        "scores": (95, 93),
        "refs": [("W1", None)],
        "classes": {"W1": ("defect", "VQ-06")},
        "items": {"VQ-06": (1, 2)},
        "expected": (MERGE, "merge"),
    },
    11955: {
        "spec": COUNT,
        "scores": (81, 80),
        "refs": [],
        "classes": {},
        "items": {},
        "expected": (KEEP, "no_visible_improvement"),
    },
    11956: {
        "spec": COUNT,
        "scores": (85, 79),
        "refs": [("C4", None), ("W2", None)],
        "classes": {"W2": ("suggestion", None)},
        "items": {},
        "expected": (MERGE, "merge"),
    },
    11957: {
        "spec": COUNT,
        "scores": (85, 84),
        "refs": [("W1", None)],
        "classes": {"W1": ("suggestion", None)},
        "items": {"VQ-07": (2, 1), "SC-01": (5, 3)},
        "expected": (KEEP, "no_defect_improvement"),
    },
    11958: {
        "spec": BAR_ERROR,
        "scores": (93, 79),
        "refs": [("W1", None), ("W2", None), ("W4", None), ("new", "SC-04"), ("new", "VQ-05"), ("new", "VQ-07")],
        "classes": {"W1": ("suggestion", None), "W2": ("suggestion", None), "W4": ("suggestion", None)},
        "items": {"SC-04": (2, 3), "VQ-05": (3, 4), "VQ-07": (1, 2), "DE-01": (4, 6), "DE-03": (2, 6)},
        "expected": (MERGE, "merge"),
    },
    11959: {
        "spec": COUNT,
        "scores": (85, 82),
        "refs": [("P1", None), ("P2", None), ("P3", "DE-02")],
        "classes": {},
        "items": {"SC-04": (3, 3), "DQ-01": (6, 6), "DE-02": (5, 4)},
        "expected": (KEEP, "no_defect_improvement"),
    },
    11960: {
        "spec": BAR_ERROR,
        "scores": (89, 85),
        "refs": [("W1", None)],
        "classes": {"W1": ("suggestion", None)},
        "items": {"LM-02": (2, 3), "VQ-06": (2, 2)},
        "expected": (KEEP, "no_defect_improvement"),
    },
    11961: {
        "spec": BAR_ERROR,
        "scores": (85, 63),
        "refs": [("W1", None), ("W2", None), ("W3", None), ("W4", None), ("new", "SC-04")],
        "classes": {
            "W1": ("defect", "VQ-07"),
            "W2": ("defect", "DE-02"),
            "W3": ("suggestion", None),
            "W4": ("suggestion", None),
        },
        "items": {"VQ-07": (0, 2), "DE-02": (2, 4), "SC-04": (2, 3)},
        "expected": (MERGE, "merge"),
    },
    11962: {
        "spec": BAR_ERROR,
        "scores": (87, 85),
        "refs": [("W1", None)],
        "classes": {"W1": ("suggestion", None)},
        "items": {"VQ-01": (7, 7), "VQ-05": (4, 4)},
        "expected": (KEEP, "no_defect_improvement"),
    },
    11963: {
        "spec": BAR_ERROR,
        "scores": (96, 92),
        "refs": [("W1", None), ("W2", None), ("W3", None)],
        "classes": {"W1": ("suggestion", None), "W2": ("suggestion", None), "W3": ("suggestion", None)},
        "items": {"LM-02": (2, 5), "DE-03": (5, 6), "DQ-01": (5, 6)},
        "expected": (KEEP, "no_defect_improvement"),
    },
}


def _round1(
    pr: int, classes: dict | None = None, items: dict | None = None, refs: list | None = None, kinds: dict | None = None
):
    """One round-1 decision; every improvement is a ``fix`` unless ``kinds`` (``{ref: kind}``) says otherwise."""
    case = ROUND1[pr]
    score, prev_rescored = case["scores"]
    scores = {**case["items"], **(items or {})}
    classes = {**case["classes"], **(classes or {})}
    improvements = [
        {"ref": ref, "what": f"improvement {n}", "where_visible": "both renders", "kind": (kinds or {}).get(ref, "fix")}
        | ({"rule": rule} if rule else {})
        for n, (ref, rule) in enumerate(refs or case["refs"], start=1)
    ]
    regen = _regen(
        prev_rescored=prev_rescored,
        prev_checklist={cid: prev for cid, (prev, _) in scores.items()},
        prev_weaknesses=[
            {"ref": ref, "class": cls} | ({"rule": rule} if rule else {}) for ref, (cls, rule) in classes.items()
        ],
        improvements=improvements,
    )
    known = frozenset(f"W{i}" for i in range(1, 5))
    return decide(
        _inp(
            score=score,
            regen=regen,
            spec_id="bubble-basic",
            known_weakness_ids=known,
            new_checklist={cid: new for cid, (_, new) in scores.items()},
            **case["spec"],
        )
    )


class TestVerificationRound:
    """P3's verdicts on the 13 round-1 decisions (12 merges and 1 keep before
    P3): 5 merges and 8 keeps with the stored numbers, 6 and 7 once the
    re-score deducts #11953's VQ-02 or VQ-07."""

    @pytest.mark.parametrize("pr", sorted(ROUND1))
    def test_p3_verdict(self, pr):
        result = _round1(pr)
        assert (result.verdict, result.code) == ROUND1[pr]["expected"]

    def test_totals(self):
        verdicts = [_round1(pr).verdict for pr in ROUND1]
        assert (verdicts.count(MERGE), verdicts.count(KEEP)) == (5, 8)

    @pytest.mark.parametrize(
        ("pr", "classes"),
        [
            (11958, {"W1": ("defect", "DE-01"), "W2": ("defect", "DE-03"), "W4": ("defect", "DE-03")}),
            (11960, {"W1": ("defect", "LM-02")}),
            (11963, {"W1": ("defect", "LM-02"), "W3": ("defect", "DE-03")}),
            (11962, {"W1": ("defect", "VQ-01")}),
            (11957, {"W1": ("defect", "VQ-07")}),
            (11959, {}),
        ],
    )
    def test_calling_it_a_defect_does_not_change_the_verdict(self, pr, classes):
        """The reviewer's likeliest misreadings of round 1: a storytelling
        layer, a library feature or taste called a DE or LM defect, a title
        bump called VQ-01 at 7 → 7, a creep recolor called VQ-07 at 2 → 1."""
        result = _round1(pr, classes=classes)
        assert (result.verdict, result.code) == ROUND1[pr]["expected"]
        if pr == 11958:  # carried by the three `new` fixes alone
            assert [i["ref"] for i in result.improvements if i["class"] == "carrier"] == ["new", "new", "new"]
            assert sum(1 for i in result.improvements if i["basis"] == "de_lm") == 3

    def test_p_items_named_by_criterion_still_keep(self):
        """#11959's percentage labels and title prefix claimed as DQ-01 and SC-04 (6 → 6, 3 → 3)."""
        result = _round1(11959, refs=[("P1", "DQ-01"), ("P2", "SC-04"), ("P3", "DE-02")])
        assert (result.verdict, result.code) == (KEEP, "no_defect_improvement")
        assert result.reason.startswith("3 visible improvement(s) (1 unverified, 2 design, library or coverage)")

    @pytest.mark.parametrize(
        ("pr", "classes", "items"),
        [
            (11953, {}, {"VQ-07": (1, 2)}),  # §8.5 b: the re-score catches the slot-5 red
            # §8.5 b: or the BEAU-001 callout clearance, misread as a `fix`
            # (P3.1: polish of a callout SC-01 lists; (b) has no mechanical backstop)
            (11953, {}, {"VQ-02": (4, 5)}),
            (11952, {"W1": ("defect", "VQ-02")}, {}),  # §8.5 a: F1 read as a VQ-02 defect
        ],
    )
    def test_conditional_pairs(self, pr, classes, items):
        """What the stored numbers cannot decide: #11953 merges once the
        re-score deducts either criterion, and #11952 merges only when the
        reviewer misclasses the weakness — the v2 forward-keep target and
        class_flip measure exactly those."""
        assert _round1(pr, classes=classes, items=items).verdict == MERGE

    def test_callout_clearance_named_polish_keeps(self):
        """P31-7: the #11953 BEAU-001 clearance, named `polish`, no longer carries."""
        result = _round1(11953, items={"VQ-02": (4, 5)}, kinds={"W1": "polish"})
        assert (result.verdict, result.code) == (KEEP, "no_defect_improvement")
        assert ("W1", "suggestion", "polish") in _classes(result)
        assert "_(polish of an out-of-scope element: does not carry)_" in render_summary(result, "89", 89)

    def test_optional_error_bars_read_as_dq01_keep(self):
        """P3.1 M1 (§8.5 f): optional asymmetric bars read as a DQ-01 defect no longer carry."""
        result = _round1(11963, classes={"W2": ("defect", "DQ-01")})
        assert (result.verdict, result.code) == (KEEP, "no_defect_improvement")
        assert ("W2", "suggestion", "de_lm") in _classes(result)


# Nine forward cells of the set v2 P3 arm (run 36413159640, PLAN_p3_1 §3): the
# refs, rules, classes and the item scores each claim rests on — no model
# text. `kinds` are appendix A's hand-assigned kinds; every other item is a
# `fix`. P3 merged all nine.
V2_CELLS: dict[str, dict] = {
    "11957-r1": {
        "spec": "count-basic",
        "scores": (85, 82),
        "classes": {"W1": ("suggestion", None), "W2": ("defect", "VQ-02"), "W3": ("suggestion", None)},
        "refs": [("W2", None), ("P1", "VQ-01")],
        "items": {"VQ-01": (6, 7), "VQ-02": (5, 6)},
        "kinds": {"W2": "polish", "P1": "polish"},
        "expected": KEEP,
    },
    "11957-r2": {
        "spec": "count-basic",
        "scores": (83, 80),
        "classes": {"W1": ("suggestion", None), "W2": ("defect", "VQ-02"), "W3": ("suggestion", None)},
        "refs": [("W2", None), ("P1", "VQ-04")],
        "items": {"VQ-02": (4, 6), "VQ-04": (1, 2)},
        "kinds": {"W2": "polish", "P1": "polish"},
        "expected": KEEP,
    },
    "11957-r3": {
        "spec": "count-basic",
        "scores": (79, 77),
        "classes": {"W1": ("suggestion", None), "W2": ("suggestion", None), "W3": ("suggestion", None)},
        "refs": [("P1", "VQ-02")],
        "items": {"VQ-02": (4, 6)},
        "kinds": {"P1": "polish"},
        "expected": KEEP,
    },
    "11963-r2": {
        "spec": "bar-error",
        "scores": (86, 85),
        "classes": {"W1": ("suggestion", None), "W2": ("obsolete", "C5"), "W3": ("suggestion", None)},
        "refs": [("P1", "VQ-02")],
        "items": {"VQ-02": (5, 6)},
        "kinds": {"P1": "polish"},
        "expected": KEEP,
    },
    "11963-r3": {
        "spec": "bar-error",
        "scores": (83, 82),
        "classes": {"W1": ("suggestion", None), "W2": ("suggestion", None), "W3": ("suggestion", None)},
        "refs": [("P1", "VQ-02")],
        "items": {"VQ-02": (5, 6)},
        "kinds": {"P1": "polish"},
        "expected": KEEP,
    },
    "11959-r1": {
        "spec": "count-basic",
        "scores": (85, 81),
        "classes": {"W1": ("defect", "CQ-04"), "W2": ("suggestion", None), "W3": ("suggestion", None)},
        "refs": [("P2", "DQ-01"), ("P3", "DE-03")],
        "items": {"CQ-04": (1, 2), "DE-03": (2, 3), "DQ-01": (4, 5)},
        "kinds": {"P2": "addition", "P3": "addition"},
        "expected": KEEP,
    },
    "11959-r2": {
        "spec": "count-basic",
        "scores": (87, 85),
        "classes": {"W1": ("defect", "CQ-04"), "W2": ("suggestion", None), "W3": ("suggestion", None)},
        "refs": [("new", "DQ-01")],
        "items": {"CQ-04": (1, 2), "DQ-01": (5, 6)},
        "kinds": {"new": "addition"},
        "expected": KEEP,
    },
    "11960-r1": {
        "spec": "bar-error",
        "scores": (84, 83),
        "classes": {"W1": ("suggestion", None), "W2": ("suggestion", None), "W3": ("suggestion", None)},
        "refs": [("P1", "VQ-02")],
        "items": {"VQ-02": (5, 6)},
        "kinds": {},
        "expected": MERGE,
    },
    "11960-r2": {
        "spec": "bar-error",
        "scores": (83, 81),
        "classes": {"W1": ("suggestion", None), "W2": ("suggestion", None), "W3": ("suggestion", None)},
        "refs": [("P1", "VQ-02"), ("W1", None)],
        "items": {"VQ-02": (5, 6)},
        "kinds": {},
        "expected": MERGE,
    },
}


def _v2_cell(key: str, kinds: dict | None = None, with_kind: bool = True):
    case = V2_CELLS[key]
    score, prev_rescored = case["scores"]
    kinds = case["kinds"] if kinds is None else kinds
    improvements = [
        {"ref": ref, "what": f"improvement {n}", "where_visible": "both renders"}
        | ({"rule": rule} if rule else {})
        | ({"kind": kinds.get(ref, "fix")} if with_kind else {})
        for n, (ref, rule) in enumerate(case["refs"], start=1)
    ]
    regen = _regen(
        prev_rescored=prev_rescored,
        prev_checklist={**CRITERIA, **{cid: prev for cid, (prev, _) in case["items"].items()}},
        prev_weaknesses=[
            {"ref": ref, "class": cls} | ({"rule": rule} if rule else {})
            for ref, (cls, rule) in case["classes"].items()
        ],
        improvements=improvements,
    )
    if not with_kind:
        regen = _no_kind(regen)
    return decide(
        _inp(
            score=score,
            regen=regen,
            spec_id=case["spec"],
            new_checklist={**CRITERIA, **{cid: new for cid, (_, new) in case["items"].items()}},
            characteristic_count=5,
            permission_refs=frozenset({"C5"}),
        )
    )


class TestVerificationRoundP31:
    """P3.1 on nine set v2 forward cells that P3 merged: polish (#11957,
    #11963) and additions (#11959) keep, the #11960 collision fix merges."""

    @pytest.mark.parametrize("key", sorted(V2_CELLS))
    def test_p31_verdict(self, key):
        assert _v2_cell(key).verdict == V2_CELLS[key]["expected"]

    @pytest.mark.parametrize("key", sorted(V2_CELLS))
    def test_p3_merged_every_cell_when_everything_is_a_fix(self, key):
        """Every kind `fix` (the compliance floor): only M1 changes a verdict."""
        expected = KEEP if key.startswith("11959") else MERGE
        assert _v2_cell(key, kinds={}).verdict == expected

    @pytest.mark.parametrize("key", ["11959-r1", "11959-r2"])
    def test_m1_alone_keeps_the_percentage_labels(self, key):
        result = _v2_cell(key, with_kind=False)
        assert (result.verdict, result.code) == (KEEP, "no_defect_improvement")
        assert {i["basis"] for i in result.improvements} == {"de_lm"}


class TestRecordCounts:
    def _record(self, regen, **inp) -> dict:
        return build_record(
            decide(_inp(regen=regen, **inp)), spec_id="bar-error", library="plotly", score=85, prev_stored=81
        )

    def test_nested_counts(self):
        regen = _regen(
            prev_checklist={**PREV_CHECKLIST, "VQ-07": 0, "DE-02": 2},
            prev_weaknesses=[
                {"ref": "W1", "class": "defect", "rule": "VQ-07"},
                {"ref": "W2", "class": "defect", "rule": "DE-02"},
                {"ref": "W3", "class": "obsolete", "rule": "C5"},
            ],
            improvements=[
                {"ref": "W1", "what": "a", "where_visible": "bars"},
                {"ref": "W2", "what": "b", "where_visible": "frame"},
                {"ref": "W3", "what": "c", "where_visible": "bars"},
                {"ref": "P1", "what": "d", "where_visible": "title"},
                {"ref": "C2", "what": "e", "where_visible": "bars"},
                {"ref": "C5", "what": "f", "where_visible": "bars"},
                {"ref": "new", "rule": "SC-04", "what": "g", "where_visible": ""},
            ],
        )
        record = self._record(regen, characteristic_count=5, permission_refs=frozenset({"C5"}))
        counts = record["improvements"]
        assert counts == {
            "total": 7,
            "visible": 4,
            "W": 3,
            "P": 1,
            "C": 2,
            "new": 1,
            "permission": 1,
            "obsolete": 1,
            "carriers": 2,
            "suggestion": 2,
            "unverified": 1,
            "de_lm": 1,
            "addition": 0,
            "polish": 0,
            "no_kind": 0,
            "carriers_pn": 0,
            "by_kind": {"fix": 7, "removal": 0, "addition": 0, "polish": 0, "none": 0},
            "code": 0,
        }
        assert counts["visible"] == counts["carriers"] + counts["suggestion"]
        assert counts["unverified"] + counts["de_lm"] <= counts["suggestion"]
        assert validate_record(record) == []

    def test_kind_counts(self):
        """P3.1: addition, polish and no_kind are disjoint subsets of suggestion,
        disjoint from unverified and de_lm; carriers_pn is a subset of carriers,
        and by_kind sums to total."""
        regen = _regen(
            prev_checklist={**PREV_CHECKLIST, "VQ-02": 4, "VQ-07": 0, "SC-04": 2, "DE-02": 2, "DQ-01": 3},
            prev_weaknesses=[{"ref": "W1", "class": "defect", "rule": "VQ-07"}],
            improvements=[
                {"ref": "W1", "kind": "removal", "what": "a", "where_visible": "bars"},
                {"ref": "P1", "rule": "VQ-02", "kind": "fix", "what": "b", "where_visible": "labels"},
                {"ref": "P2", "rule": "VQ-03", "kind": "polish", "what": "c", "where_visible": "mean line"},
                {"ref": "P3", "rule": "DQ-01", "kind": "addition", "what": "d", "where_visible": "labels"},
                {"ref": "new", "rule": "SC-04", "kind": "addition", "what": "e", "where_visible": "title"},
                {"ref": "C1", "what": "f", "where_visible": "bars"},
                {"ref": "P4", "rule": "DE-02", "kind": "Fix ", "what": "g", "where_visible": "frame"},
                {"ref": "P5", "kind": "tweak", "what": "h", "where_visible": "grid"},
            ],
        )
        del regen["improvements"][5]["kind"]
        record = self._record(regen, characteristic_count=5)
        counts = record["improvements"]
        assert {k: counts[k] for k in ("total", "visible", "carriers", "suggestion", "carriers_pn")} == {
            "total": 8,
            "visible": 8,
            "carriers": 2,  # W1 (removal) and P1 (fix)
            "suggestion": 6,
            "carriers_pn": 1,
        }
        assert {k: counts[k] for k in ("unverified", "de_lm", "addition", "polish", "no_kind")} == {
            "unverified": 1,  # P5: no rule, whatever its kind
            "de_lm": 2,  # P3 (DQ-01, an addition) and P4 (DE-02): already suggestions, so they keep their basis
            "addition": 1,  # new (SC-04 2 → 3)
            "polish": 1,  # P2 (VQ-03 4 → 6)
            "no_kind": 1,  # C1
        }
        assert counts["by_kind"] == {"fix": 2, "removal": 1, "addition": 2, "polish": 1, "none": 2}
        assert sum(counts["by_kind"].values()) == counts["total"]
        assert counts["visible"] == counts["carriers"] + counts["suggestion"]
        assert sum(counts[k] for k in ("unverified", "de_lm", "addition", "polish", "no_kind")) == counts["suggestion"]
        assert counts["carriers_pn"] <= counts["carriers"]
        assert validate_record(record) == []

    def test_marker_roundtrip_and_schema_unchanged(self):
        record = self._record(_regen())
        assert parse_record_markers(render_record_marker(record)) == [record]
        assert record["v"] == 1
        assert RECORD_KEYS == frozenset(
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

    def test_a_record_without_the_new_keys_still_validates(self):
        record = self._record(_regen())
        for key in ("obsolete", "carriers", "suggestion", "unverified", "de_lm"):
            del record["improvements"][key]
        assert validate_record(record) == []


def _feedback(
    tmp_path, capsys, *, weaknesses=None, checklist=None, regen=None, prev=None, spec=None, warn=False, prev_review=None
):
    args = ["check-feedback"]
    if prev_review is not None:
        (tmp_path / "review_prev.json").write_text(json.dumps(prev_review), encoding="utf-8")
        args += ["--prev-review", str(tmp_path / "review_prev.json")]
    if weaknesses is not None:
        (tmp_path / "review_weaknesses.json").write_text(json.dumps(weaknesses), encoding="utf-8")
        args += ["--weaknesses", str(tmp_path / "review_weaknesses.json")]
    if checklist is not None:
        (tmp_path / "review_checklist.json").write_text(json.dumps(_checklist_json(checklist)), encoding="utf-8")
        args += ["--checklist", str(tmp_path / "review_checklist.json")]
    if regen is not None:
        (tmp_path / "review_regen.json").write_text(json.dumps(regen), encoding="utf-8")
        weak = [{"id": f"W{i}", "text": t, "class": weakness_class(t)} for i, t in enumerate(prev or [], start=1)]
        (tmp_path / "prev-weaknesses.json").write_text(json.dumps(weak), encoding="utf-8")
        spec_file = tmp_path / "specification.md"
        spec_file.write_text(spec or "# s\n", encoding="utf-8")
        args += [
            "--regen",
            str(tmp_path / "review_regen.json"),
            "--prev-weaknesses",
            str(tmp_path / "prev-weaknesses.json"),
        ]
        args += ["--spec-file", str(spec_file)]
    if warn:
        args.append("--warn-only")
    code = main(args)
    return code, capsys.readouterr().out


DEFECT_LINE = "VQ-03 (both): size legend circles invisible → fill them. Likely cause: guide."
SPEC_5 = (
    "# s\n\n## What a good version looks like\n\n"
    "- A good version shows: a\n- Expected, not a defect: b\n- A good version shows: c\n"
)


class TestCheckFeedback:
    def test_clean_weaknesses_pass(self, tmp_path, capsys):
        weak = [DEFECT_LINE, "Suggestion: a subtler grid"]
        code, out = _feedback(tmp_path, capsys, weaknesses=weak, checklist={**NEW_CHECKLIST, "VQ-03": 4})
        assert code == 0
        assert "check-feedback: no problems" in out

    def test_empty_list_passes(self, tmp_path, capsys):
        assert _feedback(tmp_path, capsys, weaknesses=[], checklist=NEW_CHECKLIST)[0] == 0

    @pytest.mark.parametrize(
        ("weaknesses", "message"),
        [
            (["Grid too prominent"], "is neither a defect line"),
            (["VQ-09 (both): x → y. Likely cause: z."], "names VQ-09, which is neither a criterion"),
            (["AR-02 (both): x → y. Likely cause: z."], "names AR-02"),
            ([DEFECT_LINE], "names VQ-03, but your checklist gives VQ-03 its maximum"),
            ([f"Suggestion: idea {i}" for i in range(4)], "4 'Suggestion:' lines; keep at most 3"),
            ([3], "weakness 1 is not a string"),
            ("VQ-03", "is not a JSON list of strings"),
        ],
    )
    def test_weakness_problems(self, tmp_path, capsys, weaknesses, message):
        code, out = _feedback(tmp_path, capsys, weaknesses=weaknesses, checklist=NEW_CHECKLIST)
        assert code == 1
        assert message in out

    def test_missing_checklist_item_skips_the_maximum_check(self, tmp_path, capsys):
        assert _feedback(tmp_path, capsys, weaknesses=[DEFECT_LINE], checklist={"VQ-01": 8})[0] == 0

    def test_ar_line_needs_no_checklist_item(self, tmp_path, capsys):
        line = "AR-09 (light): title clipped → shrink the plot area. Likely cause: margin."
        assert _feedback(tmp_path, capsys, weaknesses=[line], checklist=NEW_CHECKLIST)[0] == 0

    def test_clean_regen_passes(self, tmp_path, capsys):
        regen = _regen(
            prev_weaknesses=[{"ref": "W1", "class": "suggestion"}, {"ref": "W2", "class": "defect", "rule": "VQ-03"}]
        )
        code, out = _feedback(tmp_path, capsys, checklist=NEW_CHECKLIST, regen=regen, prev=["a", "b"])
        assert (code, out.strip()) == (0, "check-feedback: no problems")

    @pytest.mark.parametrize(
        ("overrides", "message"),
        [
            ({"prev_checklist": None}, "has no prev_checklist"),
            ({"prev_checklist": {"VQ-01": 8}}, "prev_checklist lacks VQ-02"),
            ({"prev_checklist": {**PREV_CHECKLIST, "XX-01": 1}}, "prev_checklist has unknown ids XX-01"),
            ({"prev_checklist": {**PREV_CHECKLIST, "VQ-01": 9}}, "prev_checklist VQ-01 must be an integer from 0 to 8"),
            ({"prev_weaknesses": None}, "has no prev_weaknesses: classify every previous weakness (W1, W2)"),
            (
                {"prev_weaknesses": [{"ref": "W2", "class": "defect", "rule": "VQ-03"}]},
                "prev_weaknesses does not classify W1",
            ),
            (
                {
                    "prev_weaknesses": [
                        {"ref": "W1", "class": "suggestion"},
                        {"ref": "W1", "class": "suggestion"},
                        {"ref": "W2", "class": "defect", "rule": "VQ-03"},
                    ]
                },
                "classifies W1 2 times",
            ),
            (
                {"prev_weaknesses": [{"ref": "W7", "class": "suggestion"}]},
                "prev_weaknesses[1].ref 'W7' is not a weakness id",
            ),
            ({"prev_weaknesses": [{"ref": "W1", "class": "maybe"}]}, "W1: class 'maybe' is not one of"),
            (
                {"prev_weaknesses": [{"ref": "W1", "class": "defect", "rule": "C2"}]},
                "W1 is classed defect but its rule 'C2'",
            ),
            ({"prev_weaknesses": [{"ref": "W1", "class": "defect"}]}, "W1 is classed defect but its rule None"),
            (
                {"prev_weaknesses": [{"ref": "W1", "class": "obsolete", "rule": "VQ-02"}]},
                "W1 is classed obsolete but its rule",
            ),
            (
                {"prev_weaknesses": [{"ref": "W1", "class": "obsolete", "rule": "C9"}]},
                "W1 is classed obsolete but its rule 'C9'",
            ),
            ({"improvements": [{"ref": "P1", "what": "x", "where_visible": "y"}]}, "improvement 1 (P1) has no rule"),
            ({"improvements": [{"ref": "W9", "what": "x", "where_visible": "y"}]}, "W9 is not a weakness id"),
        ],
    )
    def test_regen_problems(self, tmp_path, capsys, overrides, message):
        regen = _regen(
            prev_weaknesses=[{"ref": "W1", "class": "suggestion"}, {"ref": "W2", "class": "defect", "rule": "VQ-03"}]
        )
        regen.update(overrides)
        if regen.get("prev_checklist") is None:
            regen.pop("prev_checklist")
        if regen.get("prev_weaknesses") is None:
            regen.pop("prev_weaknesses")
        code, out = _feedback(tmp_path, capsys, checklist=NEW_CHECKLIST, regen=regen, prev=["a", "b"], spec=SPEC_5)
        assert code == 1
        assert message in out, out

    def test_missing_or_unknown_kind_is_reported_once_per_item(self, tmp_path, capsys):
        regen = _regen(
            prev_weaknesses=[{"ref": "W1", "class": "suggestion"}, {"ref": "W2", "class": "defect", "rule": "VQ-03"}],
            improvements=[
                {"ref": "W2", "what": "a", "where_visible": "legend"},
                {"ref": "W1", "kind": "tweak", "what": "b", "where_visible": "grid"},
                {"ref": "C1", "kind": "Polish", "what": "c", "where_visible": "bars"},
            ],
        )
        del regen["improvements"][0]["kind"]
        code, out = _feedback(tmp_path, capsys, checklist=NEW_CHECKLIST, regen=regen, prev=["a", "b"], spec=SPEC_5)
        assert code == 1
        assert out.count("has no kind") == 2, out
        assert "improvement 1 (W2) has no kind: name fix, removal, addition or polish" in out
        assert "improvement 2 (W1) has no kind ('tweak' is not one): name fix, removal, addition or polish" in out
        assert "(C1)" not in out  # 'Polish' is coerced
        for phrase in ("carr", "merge"):
            assert phrase not in out, phrase

    def test_addition_and_polish_need_no_rule_or_score_delta(self, tmp_path, capsys):
        """A compliant addition (percentage labels, which leave DQ-01 as it was)
        and a polish item pass the self-check: they fix no rule, so there is no
        rule to name and no score delta to show."""
        regen = _regen(
            prev_weaknesses=[{"ref": "W1", "class": "suggestion"}, {"ref": "W2", "class": "defect", "rule": "VQ-03"}],
            improvements=[
                {"ref": "W2", "kind": "fix", "what": "a", "where_visible": "legend"},
                {"ref": "P1", "kind": "addition", "what": "percentage labels", "where_visible": "bars"},
                {
                    "ref": "new",
                    "rule": "DQ-01",
                    "kind": "addition",
                    "what": "percentage labels",
                    "where_visible": "bars",
                },
                {"ref": "W1", "kind": "polish", "what": "mean rule recolored", "where_visible": "mean rule"},
            ],
        )
        code, out = _feedback(tmp_path, capsys, checklist=NEW_CHECKLIST, regen=regen, prev=["a", "b"])
        assert (code, out.strip()) == (0, "check-feedback: no problems"), out
        # A fix still names its rule and still shows in the scores.
        regen["improvements"][1]["kind"] = "fix"
        code, out = _feedback(tmp_path, capsys, checklist=NEW_CHECKLIST, regen=regen, prev=["a", "b"])
        assert code == 1 and "improvement 2 (P1) has no rule" in out

    def test_defect_the_rescore_did_not_deduct(self, tmp_path, capsys):
        regen = _regen(
            prev_checklist=dict(CRITERIA),
            prev_weaknesses=[{"ref": "W1", "class": "defect", "rule": "VQ-07"}],
            improvements=[],
        )
        code, out = _feedback(tmp_path, capsys, checklist=NEW_CHECKLIST, regen=regen, prev=["a"])
        assert code == 1
        assert "W1 is classed defect under VQ-07, but prev_checklist gives VQ-07 its maximum (2/2)" in out
        assert "reclass W1 as suggestion or obsolete — change the claim, not the scores" in out

    @pytest.mark.parametrize("rule", ["VQ-03", "DE-02"])
    def test_claim_the_new_render_does_not_score_higher_on(self, tmp_path, capsys, rule):
        """The same test for all 24 criteria, so the message never reveals which carry."""
        regen = _regen(
            prev_checklist={**PREV_CHECKLIST, "VQ-03": 4, "DE-02": 4},
            prev_weaknesses=[{"ref": "W1", "class": "defect", "rule": rule}],
            improvements=[{"ref": "W1", "what": "x", "where_visible": "y"}],
        )
        checklist = {**NEW_CHECKLIST, "VQ-03": 4, "DE-02": 3}
        code, out = _feedback(tmp_path, capsys, checklist=checklist, regen=regen, prev=["a"])
        assert code == 1
        assert f"improvement 1 (W1) claims {rule}, but your checklist for the new render gives {rule}" in out
        assert "change the claim, not the scores" in out

    def test_stored_suggestion_cannot_be_classed_defect(self, tmp_path, capsys):
        regen = _regen(prev_weaknesses=[{"ref": "W1", "class": "defect", "rule": "VQ-03"}], improvements=[])
        code, out = _feedback(
            tmp_path, capsys, checklist=NEW_CHECKLIST, regen=regen, prev=["Suggestion: a subtler grid"]
        )
        assert code == 1
        assert "W1 was stored as a 'Suggestion:' line and cannot be classed defect" in out

    @pytest.mark.parametrize(
        ("spec", "rule", "flagged"),
        [
            (SPEC_5, "C1", True),  # labeled "A good version shows:" bullet
            (SPEC_5, "C2", False),  # the "Expected, not a defect:" bullet
            ("# s\n\n## What a good version looks like\n\n- a\n- b\n", "C1", False),  # unlabeled section
        ],
    )
    def test_obsolete_names_a_permission_bullet(self, tmp_path, capsys, spec, rule, flagged):
        regen = _regen(
            prev_weaknesses=[
                {"ref": "W1", "class": "obsolete", "rule": rule},
                {"ref": "W2", "class": "defect", "rule": "VQ-03"},
            ]
        )
        code, out = _feedback(tmp_path, capsys, checklist=NEW_CHECKLIST, regen=regen, prev=["a", "b"], spec=spec)
        message = f"W1 is classed obsolete under {rule}, an 'A good version shows:' bullet"
        assert (code, message in out) == ((1, True) if flagged else (0, False)), out
        if flagged:
            assert "name the bullet that permits it, or class W1 defect or suggestion" in out

    def test_missing_files(self, tmp_path, capsys):
        args = ["check-feedback", "--weaknesses", str(tmp_path / "a.json"), "--checklist", str(tmp_path / "b.json")]
        assert main([*args, "--regen", str(tmp_path / "c.json")]) == 1
        out = capsys.readouterr().out
        assert "a.json missing" in out and "c.json missing" in out and "b.json is missing" in out

    def test_needs_something_to_check(self, capsys):
        assert main(["check-feedback", "--checklist", "x.json"]) == 2

    def test_warn_only_exits_zero_with_annotations_and_a_notice(self, tmp_path, capsys):
        weak = [DEFECT_LINE, "Suggestion: a", "Grid too prominent"]
        code, out = _feedback(tmp_path, capsys, weaknesses=weak, checklist={**NEW_CHECKLIST, "VQ-03": 4}, warn=True)
        assert code == 0
        assert "::warning::weakness 3 is neither a defect line" in out
        assert "::notice::weakness_format defect=1 suggestion=1 other=1" in out

    def test_legacy_artifacts_never_crash(self, tmp_path, capsys):
        """Round-1 pair artifacts: legacy weaknesses and a review_regen.json without the new keys."""
        legacy_regen = {
            "prev_rescored": 84,
            "improvements": [{"ref": "W1", "what": "x", "where_visible": "y"}],
            "regressions": [],
            "scenario_changed": False,
            "encodings_added": [],
            "change_request_applied": None,
        }
        code, out = _feedback(
            tmp_path,
            capsys,
            weaknesses=["Legend too small", "Grid too prominent"],
            checklist=NEW_CHECKLIST,
            regen=legacy_regen,
            prev=["overlap in the dense cluster"],
            warn=True,
        )
        assert code == 0
        assert out.count("is neither a defect line") == 2
        assert "has no prev_checklist" in out and "has no prev_weaknesses" in out
        assert "::notice::weakness_format defect=0 suggestion=0 other=2" in out


# ---------------------------------------------------------------------------
# P9b: review_prev.json, the re-score as a full review
# ---------------------------------------------------------------------------


def _prev_review(**overrides) -> dict:
    review = {
        "image_description": "Light render (plot-light.png): …\n\nDark render (plot-dark.png): …",
        "criteria_checklist": _checklist_json(PREV_CHECKLIST),
        "strengths": ["Native size legend"],
        "weaknesses": [DEFECT_LINE, "Suggestion: a subtler grid"],
        "verdict": "REJECTED",
    }
    review.update(overrides)
    return review


CLEAN_REGEN = _regen(
    prev_weaknesses=[{"ref": "W1", "class": "suggestion"}, {"ref": "W2", "class": "defect", "rule": "VQ-03"}]
)
BAD_PREV_REVIEWS = [
    pytest.param({"verdict": "OK"}, id="verdict"),
    pytest.param({"criteria_checklist": _checklist_json({**PREV_CHECKLIST, "VQ-03": 5})}, id="checklist-mismatch"),
    pytest.param(
        {
            "criteria_checklist": {
                **_checklist_json(PREV_CHECKLIST),
                "code_quality": {**_checklist_json(PREV_CHECKLIST)["code_quality"], "score": 3},
            }
        },
        id="category-sum",
    ),
    pytest.param({"weaknesses": ["Suggestion: a", DEFECT_LINE]}, id="order"),
    pytest.param({"weaknesses": ["P1: " + DEFECT_LINE]}, id="p-prefix"),
    pytest.param({"image_description": ""}, id="description"),
    pytest.param({"strengths": "one"}, id="strengths"),
]


class TestCheckPrevReview:
    """The step-10 self-check runs the same checks as regen_writeback.py check."""

    def test_clean(self, tmp_path, capsys):
        code, out = _feedback(
            tmp_path, capsys, checklist=NEW_CHECKLIST, regen=CLEAN_REGEN, prev=["a", "b"], prev_review=_prev_review()
        )
        assert (code, out.strip()) == (0, "check-feedback: no problems")

    @pytest.mark.parametrize("overrides", BAD_PREV_REVIEWS)
    def test_same_problems_as_the_writeback_check(self, tmp_path, capsys, overrides):
        from automation.scripts import regen_writeback

        review = _prev_review(**overrides)
        (tmp_path / "review_prev.json").write_text(json.dumps(review), encoding="utf-8")
        (tmp_path / "review_regen.json").write_text(json.dumps(CLEAN_REGEN), encoding="utf-8")
        args = [
            "--prev-review",
            str(tmp_path / "review_prev.json"),
            "--regen-json",
            str(tmp_path / "review_regen.json"),
        ]
        assert regen_writeback.main(["check", *args]) == 1
        expected = [line for line in capsys.readouterr().out.splitlines() if line.strip()]
        assert expected

        code, out = _feedback(
            tmp_path, capsys, checklist=NEW_CHECKLIST, regen=CLEAN_REGEN, prev=["a", "b"], prev_review=review
        )
        assert code == 1
        for line in expected:
            assert f"review_prev.json: {line}" in out, (line, out)

    def test_defect_ids_are_checked_against_prev_checklist(self, tmp_path, capsys):
        """The content check stays in check-feedback: a defect under a criterion the re-score maxed."""
        line = "VQ-01 (both): tick labels small → larger. Likely cause: size."
        code, out = _feedback(
            tmp_path,
            capsys,
            checklist=NEW_CHECKLIST,
            regen=CLEAN_REGEN,
            prev=["a", "b"],
            prev_review=_prev_review(weaknesses=[line]),
        )
        assert code == 1
        assert "review_prev.json: weakness 1 names VQ-01, but your checklist gives VQ-01 its maximum (8/8)" in out

    def test_a_missing_file_is_reported(self, tmp_path, capsys):
        (tmp_path / "review_regen.json").write_text(json.dumps(CLEAN_REGEN), encoding="utf-8")
        code = main(
            [
                "check-feedback",
                "--regen",
                str(tmp_path / "review_regen.json"),
                "--prev-review",
                str(tmp_path / "x.json"),
            ]
        )
        assert code == 1
        assert "x.json missing" in capsys.readouterr().out

    def test_without_the_regen_file_there_is_nothing_to_compare(self, tmp_path, capsys):
        code, out = _feedback(tmp_path, capsys, prev_review=_prev_review())
        assert code == 1
        assert "review_prev.json: review_regen.json has no prev_checklist" in out

    def test_warn_only_never_fails(self, tmp_path, capsys):
        code, out = _feedback(
            tmp_path,
            capsys,
            weaknesses=[],
            checklist=NEW_CHECKLIST,
            regen=CLEAN_REGEN,
            prev=["a", "b"],
            prev_review=_prev_review(verdict="OK"),
            warn=True,
        )
        assert code == 0
        assert "::warning::review_prev.json: verdict must be APPROVED or REJECTED" in out


# ---------------------------------------------------------------------------
# P8: the code-only path
# ---------------------------------------------------------------------------

CODE_LINE = (
    "CQ-04 (code): lines 39–60 write out the ACF and a Durbin-Levinson PACF (22 lines) → "
    '`acf(series, nlags=35)` and `pacf(series, nlags=35, method="ldb")` (statsmodels.tsa.stattools). '
    "Likely cause: `np.sum` loops; statsmodels unused although lib-plotly installs it."
)
REMOVE_LINE = "CQ-04 (code): lines 80–120 define a legend helper that is never called → remove it. Likely cause: x."
LEGACY_CQ = "CQ-04: code is somewhat verbose, the ACF could use statsmodels"
PREV_SOURCE = "import numpy as np\n" + "".join(f"acf_values[{i}] = np.sum(x[:n - {i}] * x[{i}:])\n" for i in range(30))
NEW_SOURCE = "import numpy as np\nfrom statsmodels.tsa.stattools import acf, pacf\n" + (
    "acf_values = acf(series, nlags=35)\npacf_values = pacf(series, nlags=35, method='ldb')\n"
)
CODE_ITEM = {"ref": "W1", "what": "ACF/PACF via statsmodels", "where_in_code": "prev lines 39–60 → new lines 3–4"}


def _code_regen(**overrides) -> dict:
    """No visible improvement; W1 is a CQ-04 defect the re-score deducts (1 of 2)."""
    payload = _regen(
        prev_checklist={**PREV_CHECKLIST, "CQ-04": 1},
        prev_weaknesses=[{"ref": "W1", "class": "defect", "rule": "CQ-04"}],
        improvements=[],
        code_improvements=[dict(CODE_ITEM)],
    )
    payload.update(overrides)
    payload["improvements"] = _with_kind(payload["improvements"])
    return payload


def _code_inp(regen=None, **overrides) -> GateInput:
    fields = {
        "regen": _code_regen() if regen is None else regen,
        "weakness_texts": {"W1": CODE_LINE, "W2": DEFECT_LINE, "W3": LEGACY_CQ},
        "prev_source": PREV_SOURCE,
        "new_source": NEW_SOURCE,
    }
    fields.update(overrides)
    score = fields.pop("score", 85)
    return _inp(score, **fields)


class TestCodePath:
    def test_merges_with_no_visible_improvement(self):
        result = decide(_code_inp())
        assert (result.verdict, result.code) == (MERGE, "merge")
        assert result.reason.startswith("code path: W1 (CQ-04, fix) fixed, 31 → 4 lines, no carrier")
        assert [c["counted"] for c in result.code_improvements] == [True]
        assert (
            build_record(result, spec_id="acf-pacf", library="plotly", score=85, prev_stored=91)["improvements"]["code"]
            == 1
        )

    def test_merges_with_visible_suggestions_riding_along(self):
        """The base-style case: the regeneration also aligned fonts, which the re-score lists as suggestions."""
        regen = _code_regen(
            improvements=[{"ref": "P1", "rule": "DE-02", "what": "fonts aligned", "where_visible": "both renders"}]
        )
        result = decide(_code_inp(regen))
        assert result.verdict == MERGE and result.reason.startswith("code path: W1")

    def test_a_removal_needs_no_call(self):
        result = decide(_code_inp(weakness_texts={"W1": REMOVE_LINE}))
        assert result.verdict == MERGE
        assert result.code_improvements[0]["kind"] == "removal"

    @pytest.mark.parametrize(
        ("change", "why"),
        [
            ({"regen": {"code_improvements": [{**CODE_ITEM, "ref": "P1"}]}}, "only a W id"),
            ({"regen": {"code_improvements": [{**CODE_ITEM, "ref": "new"}]}}, "only a W id"),
            ({"regen": {"code_improvements": [{**CODE_ITEM, "ref": "W9"}]}}, "not a weakness id"),
            ({"regen": {"prev_weaknesses": [{"ref": "W1", "class": "suggestion"}]}}, "classed suggestion"),
            ({"regen": {"prev_weaknesses": [{"ref": "W1", "class": "obsolete", "rule": "C2"}]}}, "classed obsolete"),
            ({"regen": {"prev_weaknesses": [{"ref": "W1", "class": "defect", "rule": "CQ-01"}]}}, "(CQ-01)"),
            ({"regen": {"prev_checklist": dict(PREV_CHECKLIST)}}, "did not score higher (2 → 2)"),
            ({"new_checklist": {**NEW_CHECKLIST, "CQ-04": 1}}, "did not score higher (1 → 1)"),
            ({"weakness_texts": {"W1": LEGACY_CQ}}, "not a 'CQ-04 (code)' defect line"),
            ({"weakness_texts": {"W1": "CQ-04 (both): verbose → `acf()`. Likely cause: x."}}, "defect line"),
            ({"weakness_texts": {"W1": "Suggestion: use `acf()`"}}, "defect line"),
            ({"weakness_texts": {"W1": "CQ-04 (code): verbose ACF → shorter. Likely cause: x."}}, "no call"),
            ({"new_source": "".join(PREV_SOURCE.splitlines(keepends=True)[:10])}, "not called more often"),
            ({"new_source": PREV_SOURCE + "x = 1\n"}, "not shorter"),
            ({"new_source": NEW_SOURCE * 8}, "not shorter"),
            ({"regen": {"code_improvements": [{**CODE_ITEM, "where_in_code": " "}]}}, "non-empty what"),
            ({"regen": {"code_improvements": ["W1"]}}, "not an object"),
            ({"regen": {"scenario_changed": True}}, "unchanged data scenario"),
            ({"regen": {"encodings_added": ["color by lag sign"]}}, "no added encodings"),
            ({"prev_source": None}, "code path off"),
            ({"new_source": None}, "code path off"),
        ],
    )
    def test_not_counted_keeps_with_p3s_code(self, change, why):
        change = dict(change)
        regen = _code_regen(**change.pop("regen", {}))
        result = decide(_code_inp(regen, spec_id="acf-pacf", **change))
        assert result.verdict == KEEP
        assert result.code == "no_visible_improvement"
        assert "code path: nothing counted" in result.reason and why in result.reason
        assert not any(c["counted"] for c in result.code_improvements)

    def test_a_call_the_predecessor_already_made_is_not_new(self):
        prev = PREV_SOURCE + "a = acf(series)\nb = pacf(series)\n"
        new = NEW_SOURCE + "c = acf(other)\n"  # acf 2 → 2, pacf 1 → 1
        assert (
            decide(_code_inp(prev_source=prev, new_source=new.replace("pacf(series, nlags=35", "pacf(series"))).verdict
            == MERGE
        )
        same = decide(_code_inp(prev_source=prev + "d = acf(x)\n", new_source=NEW_SOURCE))
        assert same.verdict == KEEP and "not called more often" in same.reason

    def test_suggestions_only_keep_with_no_defect_improvement(self):
        regen = _code_regen(
            improvements=[{"ref": "P1", "rule": "DE-02", "what": "fonts", "where_visible": "both renders"}],
            prev_weaknesses=[{"ref": "W1", "class": "suggestion"}],
        )
        result = decide(_code_inp(regen))
        assert (result.verdict, result.code) == (KEEP, "no_defect_improvement")
        assert "code path: nothing counted — W1: classed suggestion" in result.reason

    def test_below_tolerance(self):
        result = decide(_code_inp(score=80, regen=_code_regen(prev_rescored=85)))
        assert (result.verdict, result.code) == (KEEP, "below_tolerance")

    def test_a_regression_beats_the_code_path(self):
        regen = _code_regen(regressions=[{"what": "legend lost", "where_visible": "both renders"}])
        assert decide(_code_inp(regen)).code == "regression"

    def test_basic_spec_scenario_change_is_a_regression_first(self):
        result = decide(_code_inp(_code_regen(scenario_changed=True), spec_id="bubble-basic"))
        assert result.code == "regression"

    def test_a_carrier_takes_the_carrier_path_and_the_code_fix_rides_along(self):
        regen = _code_regen(
            prev_checklist={**PREV_CHECKLIST, "CQ-04": 1},
            prev_weaknesses=[
                {"ref": "W1", "class": "defect", "rule": "CQ-04"},
                {"ref": "W2", "class": "defect", "rule": "VQ-03"},
            ],
            improvements=[{"ref": "W2", "what": "legend", "where_visible": "size legend, both renders"}],
        )
        result = decide(_code_inp(regen))
        assert result.verdict == MERGE and "1 carrying (W2)" in result.reason
        record = build_record(result, spec_id="s", library="b", score=85, prev_stored=90)
        assert (record["improvements"]["carriers"], record["improvements"]["code"]) == (1, 1)
        assert "_(rides along)_" in render_summary(result, "90", 85)

    def test_without_the_sources_every_p3_verdict_stands(self):
        """Flags absent: a code_improvements list changes no verdict, code or merge reason."""
        for regen in (_regen(), _regen(improvements=[]), _regen(prev_weaknesses=[])):
            base = decide(_inp(regen=regen))
            with_code = decide(_inp(regen={**regen, "code_improvements": [dict(CODE_ITEM)]}))
            assert (with_code.verdict, with_code.code) == (base.verdict, base.code)
            assert with_code.reason.startswith(base.reason)
            assert decide(_inp(regen=regen)).reason == base.reason

    @pytest.mark.parametrize("bad", [None, "W1", {"ref": "W1"}, [None], [{"ref": 5}]])
    def test_a_malformed_list_never_invalidates_the_file(self, bad):
        result = decide(_code_inp(_regen(code_improvements=bad)))
        assert result.code != "regen_json_invalid"
        assert (result.verdict, result.code) == (MERGE, "merge")  # the carrier fixture W2 still carries
        assert not any(c["counted"] for c in result.code_improvements)

    def test_lower_case_refs_are_coerced(self):
        result = decide(_code_inp(_code_regen(code_improvements=[{**CODE_ITEM, "ref": "w1"}])))
        assert result.verdict == MERGE and result.coerced and "code ref 'w1' -> 'W1'" in result.reason

    def test_summary_lists_the_code_improvements_and_the_size(self):
        summary = render_summary(decide(_code_inp()), "91", 85)
        assert "**Code improvements**" in summary
        assert (
            "- `W1` ACF/PACF via statsmodels — prev lines 39–60 → new lines 3–4 _(code path: counted, fix)_" in summary
        )
        assert "**Code size:** 31 → 4 lines" in summary
        kept = render_summary(decide(_code_inp(weakness_texts={"W1": LEGACY_CQ})), "91", 85)
        assert "_(not counted: its stored line is not a 'CQ-04 (code)' defect line)_" in kept

    def test_record_without_code_path_counts_zero_and_old_parsers_accept_it(self):
        record = build_record(decide(_inp()), spec_id="s", library="b", score=85, prev_stored=90)
        assert record["improvements"]["code"] == 0
        assert validate_record(record) == []
        assert set(record) <= RECORD_KEYS


class TestCodeHelpers:
    @pytest.mark.parametrize(
        ("text", "expected"),
        [
            (CODE_LINE, True),
            ("CQ-01, CQ-04 (code): a helper function computes the KDE → `gaussian_kde()`. Likely cause: x.", True),
            ("CQ-04 (both): verbose → `acf()`. Likely cause: x.", False),
            (LEGACY_CQ, False),
            ("Suggestion: `acf()` would be shorter", False),
            ("VQ-03 (code): x → y. Likely cause: z.", False),
        ],
    )
    def test_is_cq04_code_defect(self, text, expected):
        assert is_cq04_code_defect(text) is expected

    @pytest.mark.parametrize(
        ("text", "tokens"),
        [
            (CODE_LINE, ["acf", "pacf"]),
            ("CQ-04 (code): lines 3–20 → `stats::acf()` (base R). Likely cause: x.", ["acf"]),
            ("CQ-04 (code): lines 3–20 → `density!(ax, x)` (Makie). Likely cause: x.", ["density!"]),
            ("CQ-04 (code): lines 3–20 → `d3.bin()` (d3). Likely cause: `manualBins`.", ["bin"]),
            ("CQ-04 (code): lines 3–20 → `scipy.stats.gaussian_kde` (SciPy). Likely cause: x.", ["gaussian_kde"]),
            ("CQ-04 (code): lines 3–20 → the `{type: 'boxplot'}` transform. Likely cause: x.", []),
            ("CQ-04 (code): `x` lines 3–20 without arrow", []),
            ('CQ-04 (code): lines 5–15 → `df["v"].rolling(7).mean()` (pandas). Likely cause: x.', ["rolling", "mean"]),
            ("CQ-04 (code): lines 5–15 → `gaussian_kde(v)(np.linspace(0, 1, 50))`. Likely cause: x.", ["gaussian_kde"]),
            ("CQ-04 (code): lines 10–30 map `x -> y` by hand → `d3.rollup()` (d3). Likely cause: x.", ["rollup"]),
        ],
    )
    def test_replacement_tokens(self, text, tokens):
        assert replacement_tokens(text) == tokens

    def test_is_removal_and_call_count(self):
        assert is_removal(REMOVE_LINE) and is_removal("CQ-04 (code): x -> delete the dead branch. Likely cause: y.")
        assert not is_removal(CODE_LINE)
        assert not is_removal("CQ-04 (code): x → `remove_outliers()` helper. Likely cause: y.")

    @pytest.mark.parametrize(
        ("language", "source", "count"),
        [
            # A comment that spells the call is not the call (Copilot, #12005).
            ("python", "# use acf(series)\nx = 1\n", 0),
            ("python", "x = np.sum(a)  # acf(series) would do\n", 0),
            ("r", "#' acf(series)\nx <- 1 # acf(x)\n", 0),
            ("julia", "# acf(series)\n#= acf(a)\n #= acf(b) =#\nacf(c) =#\nx = 1\n", 0),
            ("javascript", "// acf(series)\n/* acf(a)\n * acf(b)\n */\nconst x = 1; // acf(c)\n", 0),
            # Neither is a string literal.
            ("python", 't = \'acf(x)\'\nu = "acf(y)"\nv = f"{acf(z)}"\n', 0),
            ("python", '"""Docstring.\n\nacf(series) by hand.\n"""\nx = 1\n', 0),
            ("r", "t <- 'acf(x)'\nu <- \"acf(\ny)\"\n", 0),
            ("julia", 't = "acf(x)"\nu = """\nacf(y)\n"""\n', 0),
            ("javascript", "const t = 'acf(x)', u = \"acf(y)\", v = `acf(${acf(z)})\nacf(w)`;\n", 0),
            # Neither is a definition: a hand-roll named after the call it imitates.
            ("python", "def acf(x):\n    return 1\n", 0),
            ("python", "async def acf(x):\n    return 1\nclass acf(Base):\n    pass\n", 0),
            ("r", "acf <- function(x) {\n  1\n}\n", 0),
            ("julia", "function acf(x)\n    1\nend\nacf(x) = 1\nacf(x::Vector{T}) where {T} = 1\n", 0),
            ("javascript", "function acf(x) {}\nasync function* acf(y) {}\nconst acf = (x) => 1;\n", 0),
            ("javascript", "class A {\n  acf(x) {\n  }\n  static async acf(y): number {\n  }\n}\n", 0),
            # The call itself counts, next to all of the above.
            ("python", "# acf(a)\ndef acf(x):\n    return 'acf(b)'\nv = acf(series)\n", 1),
            ("python", "a = acf(x)\nb = stattools.acf (y)\nc = pacf(z)\nd = 7 // acf(w)\n", 3),
            ("python", "s = 'it''s'\nv = acf(x)  # '\nw = acf(y)\n", 2),
            ("r", "v <- stats::acf(x, plot = FALSE)  # 'quoted\nw <- acf(y)\n", 2),
            ("julia", "v = acf(x') * acf(y)'\nc = 'a'; w = acf(z)\nacf(q) == 1\n", 4),
            ("javascript", "const v = d3.acf(x); if (acf(y)) {\n}\nconst u = 'a' + acf(z) + \"b\";\n", 3),
        ],
    )
    def test_call_count_reads_executable_text_only(self, language, source, count):
        assert call_count(source, "acf", language) == count

    def test_a_comment_or_a_definition_alone_does_not_carry_the_code_path(self):
        for extra in ("# use acf(series)\n", "note = 'acf(series)'\n", "def acf(series):\n    return series\n"):
            new = "import numpy as np\n" + extra + "v = np.correlate(x, x)\n"
            result = decide(_code_inp(new_source=new))
            assert result.verdict == KEEP and "not called more often" in result.reason
        julia = decide(_code_inp(new_source="acf(x) = sum(x)\n# pacf(x)\n", source_language="julia"))
        assert julia.verdict == KEEP and "not called more often" in julia.reason

    def test_source_language(self):
        assert [source_language(p) for p in ("/tmp/anyplot-prev-impl.py", "plots/s/implementations/r/ggplot2.R")] == [
            "python",
            "r",
        ]
        assert [source_language(p) for p in ("a/makie.jl", "a/d3.js", "a/muix.tsx")] == [
            "julia",
            "javascript",
            "javascript",
        ]
        assert source_language("a/notes.txt") is None and source_language("") is None

    def test_line_counts_on_an_early_keep(self):
        result = decide(_code_inp(canvas_failed=True))
        assert (result.code, result.prev_lines, result.new_lines) == ("canvas_failed", 31, 4)
        assert decide(_inp(canvas_failed=True)).prev_lines is None
        assert call_count("a = acf(x)\nb = stattools.acf (y)\nc = pacf(z)", "acf") == 2
        assert call_count("density!(ax, x)", "density!") == 1

    def test_load_weakness_texts(self, tmp_path):
        path = tmp_path / "w.json"
        path.write_text(json.dumps([{"id": "W1", "text": CODE_LINE, "class": "defect"}, {"id": "W2"}, 3]))
        assert load_weakness_texts(path) == {"W1": CODE_LINE}
        assert load_weakness_texts(tmp_path / "missing.json") == {}


class TestCodePathCli:
    def _run(self, tmp_path, monkeypatch, capsys, *, prev_text=PREV_SOURCE, with_flags=True, ext=".py"):
        monkeypatch.delenv("GITHUB_OUTPUT", raising=False)
        (tmp_path / "review_regen.json").write_text(json.dumps(_code_regen()), encoding="utf-8")
        (tmp_path / "review_checklist.json").write_text(json.dumps(_checklist_json(NEW_CHECKLIST)), encoding="utf-8")
        weak = [
            {"id": "W1", "text": CODE_LINE, "class": "defect"},
            {"id": "W2", "text": DEFECT_LINE, "class": "defect"},
        ]
        (tmp_path / "weak.json").write_text(json.dumps(weak), encoding="utf-8")
        (tmp_path / "prev.py").write_text(prev_text, encoding="utf-8")
        (tmp_path / f"new{ext}").write_text(NEW_SOURCE, encoding="utf-8")
        args = ["decide", "--spec-id", "acf-pacf", "--library", "plotly", "--score", "85", "--prev-stored", "91"]
        args += ["--regen-json", str(tmp_path / "review_regen.json"), "--weaknesses-json", str(tmp_path / "weak.json")]
        args += ["--prev-renders", "available", "--record-out", str(tmp_path / "record.json")]
        if with_flags:
            args += ["--prev-impl", str(tmp_path / "prev.py"), "--new-impl", str(tmp_path / f"new{ext}")]
        assert main(args) == 0
        out = capsys.readouterr().out
        notice = next(line for line in out.splitlines() if line.startswith("::notice::regen_gate"))
        return notice, json.loads((tmp_path / "record.json").read_text())

    def test_flags_turn_the_code_path_on(self, tmp_path, monkeypatch, capsys):
        notice, record = self._run(tmp_path, monkeypatch, capsys)
        assert " verdict=merge code=merge prev_lines=31 new_lines=4 reason=code path: W1" in notice
        assert record["improvements"]["code"] == 1 and record["improvements"]["carriers"] == 0

    def test_old_argument_set_keeps_the_old_notice(self, tmp_path, monkeypatch, capsys):
        notice, record = self._run(tmp_path, monkeypatch, capsys, with_flags=False)
        assert " code=no_visible_improvement reason=" in notice and "prev_lines=" not in notice
        assert record["improvements"]["code"] == 0

    def test_an_unreadable_or_oversized_source_turns_the_path_off(self, tmp_path, monkeypatch, capsys):
        notice, _ = self._run(tmp_path, monkeypatch, capsys, prev_text="x\n" * 600_000)
        assert " code=no_visible_improvement prev_lines=n/a new_lines=n/a reason=" in notice
        assert "code path off" in notice

    @pytest.mark.parametrize("ext", [".txt", ".jl"])
    def test_an_unknown_or_a_different_language_turns_the_path_off(self, tmp_path, monkeypatch, capsys, ext):
        notice, _ = self._run(tmp_path, monkeypatch, capsys, ext=ext)
        assert " code=no_visible_improvement prev_lines=n/a new_lines=n/a reason=" in notice
        assert "code path off" in notice


class TestCodeFeedback:
    def test_a_clean_entry_passes(self, tmp_path, capsys):
        regen = _code_regen(prev_weaknesses=[{"ref": f"W{i}", "class": "suggestion"} for i in (2, 3)])
        regen["prev_weaknesses"].insert(0, {"ref": "W1", "class": "defect", "rule": "CQ-04"})
        code, out = _feedback(
            tmp_path, capsys, checklist=NEW_CHECKLIST, regen=regen, prev=[CODE_LINE, DEFECT_LINE, "Suggestion: x"]
        )
        assert "code improvement" not in out, out

    @pytest.mark.parametrize(
        ("entries", "classes", "texts", "message"),
        [
            ([{**CODE_ITEM, "ref": "P1"}], None, None, "must cite a W id of the previous review"),
            ([dict(CODE_ITEM)], [{"ref": "W1", "class": "suggestion"}], None, "cites a W you classed suggestion"),
            ([{**CODE_ITEM, "what": ""}], None, None, "needs a non-empty what"),
            ([dict(CODE_ITEM)], None, [LEGACY_CQ], "is not a 'CQ-04 (code): …' defect line"),
            ("W1", None, None, "code_improvements must be a list"),
        ],
    )
    def test_problems(self, tmp_path, capsys, entries, classes, texts, message):
        regen = _code_regen(code_improvements=entries)
        if classes is not None:
            regen["prev_weaknesses"] = classes
        _, out = _feedback(tmp_path, capsys, checklist=NEW_CHECKLIST, regen=regen, prev=texts or [CODE_LINE])
        assert message in out, out

    def test_the_claim_must_show_in_the_scores(self, tmp_path, capsys):
        _, out = _feedback(
            tmp_path, capsys, checklist={**NEW_CHECKLIST, "CQ-04": 1}, regen=_code_regen(), prev=[CODE_LINE]
        )
        assert "code improvement 1 (W1) claims CQ-04, but your checklist for the new render gives CQ-04 1" in out
