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
    MERGE,
    GateInput,
    decide,
    main,
    parse_characteristics,
    render_previous_review,
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
        from automation.scripts.regen_gate import render_summary

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
        assert "**Previous quality score (stored):** 90" in md
        assert [w["id"] for w in weaknesses] == ["W1", "W2"]

    def test_parse_characteristics(self):
        spec = (
            "# bubble-basic\n\n## Notes\n- not this\n\n"
            "## What a good version looks like\n\n"
            "- Overlap is expected\n  - nested detail\n1. Sizes scale by area\n* Legend readable\n\n"
            "## Later\n- not this either\n"
        )
        assert parse_characteristics(spec) == ["Overlap is expected", "Sizes scale by area", "Legend readable"]

    def test_parse_characteristics_absent(self):
        assert parse_characteristics("# spec\n\n## Notes\n- a\n") == []


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
