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
    KEEP,
    KIND_EXPECTED,
    KIND_SHOWS,
    MERGE,
    REASON_CODES,
    GateInput,
    build_record,
    characteristic_kind,
    decide,
    main,
    parse_characteristics,
    parse_record_markers,
    permission_refs,
    record_token,
    render_previous_review,
    render_record_marker,
    render_summary,
    reset_header_score,
    validate_record,
    validate_regen,
    weakness_ids,
)


KNOWN = frozenset({"W1", "W2", "W3"})


def _regen(**overrides) -> dict:
    payload = {
        "prev_rescored": 85,
        "improvements": [{"ref": "W2", "what": "Size legend circles filled", "where_visible": "size legend, both renders"}],
        "regressions": [],
        "scenario_changed": False,
        "encodings_added": [],
        "change_request_applied": None,
    }
    payload.update(overrides)
    return payload


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
    }
    fields.update(overrides)
    return GateInput(**fields)


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
            {"ref": "P1", "what": "Title no longer crowds the legend", "where_visible": "top right, light render"},
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
        imp = [
            {"ref": "C5", "what": "a", "where_visible": "x"},
            {"ref": "C2", "what": "b", "where_visible": "y"},
        ]
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
        inp = _inp(regen=_regen(improvements=imp), characteristic_count=len(items), permission_refs=permission_refs(items))
        assert decide(inp).verdict == MERGE

    def test_summary_marks_the_permission(self):
        imp = [
            {"ref": "C2", "what": "Overlap visible", "where_visible": "centre"},
            {"ref": "W2", "what": "Legend fixed", "where_visible": "legend"},
        ]
        result = decide(_inp(regen=_regen(improvements=imp), characteristic_count=3, permission_refs=frozenset({"C2"})))
        text = render_summary(result, "90", 85)
        assert "- `C2` Overlap visible — centre _(permission, not counted)_" in text
        assert "- `W2` Legend fixed — legend\n" in text


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
        assert out.endswith(body[-60:])  # lines past the header are untouched

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
        assert "**W1:** w" in md

    def test_weakness_ids_are_stable_and_skip_blanks(self):
        assert weakness_ids(["a", " ", "b"]) == [{"id": "W1", "text": "a"}, {"id": "W2", "text": "b"}]

    def test_render_previous_review_writes_ids(self):
        data = {
            "quality_score": 90,
            "review": {"strengths": ["clean"], "weaknesses": ["legend invisible", "labels overlap"]},
        }
        md, weaknesses = render_previous_review(data, "bubble-basic", "r", "ggplot2", ["overlap handled with alpha"])
        assert "**W1:** legend invisible" in md
        assert "**W2:** labels overlap" in md
        assert "**C1:** overlap handled with alpha" in md
        assert '(only "A good version shows" bullets can be improvement refs)' in md
        assert "**Previous quality score (stored):** 90" in md
        assert [w["id"] for w in weaknesses] == ["W1", "W2"]

    def test_parse_characteristics(self):
        spec = (
            "# bubble-basic\n\n## Notes\n- not this\n\n"
            "## What a good version looks like\n\n"
            "- Overlap is expected\n  - nested detail\n1. Sizes scale by area\n* Legend readable\n\n"
            "## Later\n- not this either\n"
        )
        assert parse_characteristics(spec) == ["Overlap is expected; nested detail", "Sizes scale by area", "Legend readable"]

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
        assert json.loads(wj.read_text())[1]["id"] == "W2"

        regen = tmp_path / "review_regen.json"
        regen.write_text(json.dumps(_regen(prev_rescored=80)), encoding="utf-8")
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
        assert "::notice::regen_gate spec=bubble-basic lib=altair prev_stored=88 prev_rescored=80 new=81 verdict=merge" in stdout
        assert "verdict=merge" in out.read_text()
        assert "| 88 | 80 | 81 |" in summary.read_text()

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
        imp = [{"ref": "C2", "what": "Bubbles overlap in the dense cluster now", "where_visible": "centre, both renders"}]
        regen.write_text(json.dumps(_regen(prev_rescored=80, improvements=imp)), encoding="utf-8")
        summary = tmp_path / "summary.md"
        args = ["decide", "--spec-id", "bubble-basic", "--library", "d3", "--score", "84", "--regen-json", str(regen)]
        args += ["--spec-file", str(spec), "--prev-renders", "available", "--summary-out", str(summary)]
        assert main(args) == 0
        stdout = capsys.readouterr().out
        assert "verdict=keep" in stdout
        assert "C2 = 'Expected, not a defect' bullet, not counted as an improvement" in stdout
        assert "verdict=keep" in out.read_text()
        assert "_(permission, not counted)_" in summary.read_text()

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

    def test_every_code_is_declared(self):
        seen = {
            decide(_inp(canvas_failed=True)).code,
            decide(_inp(score=None)).code,
            decide(_inp(score=0)).code,
            decide(_inp(prev_renders=False)).code,
            decide(_inp(context_ok=False)).code,
            decide(_inp(score=80)).code,
            decide(_inp()).code,
        }
        assert seen <= set(REASON_CODES)
        assert "script_crashed" in REASON_CODES  # the workflow's fallback

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
        assert record["improvements"] == {"total": 2, "visible": 1, "W": 1, "P": 0, "C": 0, "new": 1}
        assert record["regressions"] == 0
        assert record["prev_model"] == "n/a"
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
        assert out.endswith(body[-60:])

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
