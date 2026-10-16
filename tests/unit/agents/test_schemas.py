"""Tests for agents/anyplot/schemas.py: the field limits and the defect-line grammar."""

import json
from typing import Any, get_args

import pytest
from pydantic import ValidationError

from agents.anyplot.schemas import (
    ELLIPSIS,
    MAX_ATTEMPTS,
    MAX_CHANGE_CHARS,
    MAX_DEFECT_TEXT_CHARS,
    MAX_FULL_CODE_CHARS,
    MAX_LINE_CHARS,
    MAX_TITLE_CHARS,
    AdaptPlan,
    AdaptRequest,
    Binding,
    ColumnProfile,
    DatasetProfile,
    Defect,
    DefectId,
    DefectTheme,
    Edit,
    PipelineArgs,
    PlotResult,
    ReviewRequest,
    Verdict,
    repair_plan,
    repair_verdict,
)
from automation.scripts.regen_gate import AR_IDS, CRITERIA, DEFECT, DEFECT_RE, defect_ids, defect_target, weakness_class


def column(name: str = "x", **overrides: Any) -> dict[str, Any]:
    return {"name": name, "dtype": "number", "missing": 0, "unique": 10, "min": 0.0, "max": 9.5, **overrides}


def profile(**overrides: Any) -> dict[str, Any]:
    return {
        "rows": 10,
        "columns": [column("x"), column("y")],
        "sample": [["1", "2"], ["3", "4"]],
        "source_format": "csv",
        **overrides,
    }


def defect(**overrides: Any) -> dict[str, Any]:
    return {
        "id": "VQ-01",
        "theme": "dark",
        "observed": "tick labels 9 px tall",
        "target": "at least 14 px (+5 px)",
        "likely_cause": "`ax.tick_params(labelsize=6)`",
        **overrides,
    }


class TestDatasetProfile:
    def test_valid_profile(self) -> None:
        parsed = DatasetProfile.model_validate(profile())

        assert parsed.rows == 10
        assert parsed.decimal == "."
        assert [c.name for c in parsed.columns] == ["x", "y"]

    def test_column_name_over_64_characters_is_refused(self) -> None:
        with pytest.raises(ValidationError):
            ColumnProfile.model_validate(column("n" * 65))

    def test_more_than_five_top_values_are_refused(self) -> None:
        with pytest.raises(ValidationError):
            ColumnProfile.model_validate(column(top=["a", "b", "c", "d", "e", "f"]))

    def test_min_and_max_take_numbers_or_short_text(self) -> None:
        parsed = ColumnProfile.model_validate(column(dtype="datetime", min="2024-01-01", max="2024-12-31"))

        assert parsed.min == "2024-01-01"
        with pytest.raises(ValidationError):
            ColumnProfile.model_validate(column(dtype="text", min="m" * 41))

    def test_more_than_50_columns_are_refused(self) -> None:
        columns = [column(f"c{i}") for i in range(51)]

        with pytest.raises(ValidationError):
            DatasetProfile.model_validate(profile(columns=columns, sample=[]))

    def test_exactly_50_columns_are_accepted(self) -> None:
        columns = [column(f"c{i}") for i in range(50)]

        assert len(DatasetProfile.model_validate(profile(columns=columns, sample=[])).columns) == 50

    def test_more_than_five_sample_rows_are_refused(self) -> None:
        with pytest.raises(ValidationError):
            DatasetProfile.model_validate(profile(sample=[["1", "2"]] * 6))

    def test_sample_cell_over_40_characters_is_refused(self) -> None:
        with pytest.raises(ValidationError):
            DatasetProfile.model_validate(profile(sample=[["c" * 41, "2"]]))

    def test_sample_row_width_must_match_the_columns(self) -> None:
        with pytest.raises(ValidationError, match="one per column"):
            DatasetProfile.model_validate(profile(sample=[["1"]]))

    def test_duplicate_column_names_are_refused(self) -> None:
        with pytest.raises(ValidationError, match="unique"):
            DatasetProfile.model_validate(profile(columns=[column("x"), column("x")]))

    @pytest.mark.parametrize("rows", [0, 20_001])
    def test_row_count_outside_the_parser_limits_is_refused(self, rows: int) -> None:
        with pytest.raises(ValidationError):
            DatasetProfile.model_validate(profile(rows=rows, sample=[]))

    def test_unknown_source_format_is_refused(self) -> None:
        with pytest.raises(ValidationError):
            DatasetProfile.model_validate(profile(source_format="xlsx"))

    def test_unknown_fields_are_refused(self) -> None:
        with pytest.raises(ValidationError):
            DatasetProfile.model_validate(profile(raw_text="a,b\n1,2"))


class TestBinding:
    @pytest.mark.parametrize("role", ["x", "yield_pct", "log2_fold_change", "lower_95", "temperature_K", "X1"])
    def test_spec_role_names_are_accepted(self, role: str) -> None:
        assert Binding(role=role, column="value").role == role

    @pytest.mark.parametrize("role", ["", "x y", "1x", "role;drop", "r" * 33, "ignore previous instructions"])
    def test_other_role_strings_are_refused(self, role: str) -> None:
        with pytest.raises(ValidationError):
            Binding(role=role, column="value")

    def test_column_over_64_characters_is_refused(self) -> None:
        with pytest.raises(ValidationError):
            Binding(role="x", column="c" * 65)

    def test_the_bff_accepts_the_same_roles(self) -> None:
        """The BFF copies the pattern (the API image has no agents package); the copies must agree."""
        from agents.anyplot.schemas import ROLE_PATTERN
        from api.routers.agent import ROLE_PATTERN as BFF_ROLE_PATTERN

        assert BFF_ROLE_PATTERN == ROLE_PATTERN


class TestPipelineArgs:
    def test_empty_call_uses_the_defaults(self) -> None:
        args = PipelineArgs.model_validate({})

        assert args.change_request == ""
        assert args.base == "catalogue"

    def test_change_request_over_600_characters_is_refused(self) -> None:
        with pytest.raises(ValidationError):
            PipelineArgs(change_request="c" * 601)

    def test_unknown_base_is_refused(self) -> None:
        with pytest.raises(ValidationError):
            PipelineArgs.model_validate({"base": "scratch"})

    @pytest.mark.parametrize("field", ["spec_id", "library", "dataset_id"])
    def test_the_model_cannot_redirect_the_pipeline(self, field: str) -> None:
        with pytest.raises(ValidationError):
            PipelineArgs.model_validate({field: "anything"})


class TestAdaptPlan:
    def test_edit_plan(self) -> None:
        plan = AdaptPlan.model_validate(
            {"edits": [{"find": "x = [1, 2]", "replace": "x = df['x']"}], "title": "Sales", "changes": ["Use df"]}
        )

        assert plan.full_code is None
        assert plan.edits[0].replace == "x = df['x']"

    def test_more_than_20_edits_are_refused(self) -> None:
        with pytest.raises(ValidationError):
            AdaptPlan(edits=[Edit(find=f"a{i}", replace="b") for i in range(21)])

    def test_full_code_over_24_kib_is_refused(self) -> None:
        AdaptPlan(full_code="x" * MAX_FULL_CODE_CHARS)
        with pytest.raises(ValidationError):
            AdaptPlan(full_code="x" * (MAX_FULL_CODE_CHARS + 1))

    def test_title_over_120_characters_is_refused(self) -> None:
        with pytest.raises(ValidationError):
            AdaptPlan(title="t" * 121)

    def test_more_than_five_changes_are_refused(self) -> None:
        with pytest.raises(ValidationError):
            AdaptPlan(changes=[f"change {i}" for i in range(6)])

    def test_edits_and_full_code_together_are_refused(self) -> None:
        with pytest.raises(ValidationError, match="never both"):
            AdaptPlan(edits=[Edit(find="a", replace="b")], full_code="import numpy as np\n")

    def test_empty_find_is_refused(self) -> None:
        with pytest.raises(ValidationError):
            Edit(find="", replace="b")

    def test_find_keeps_its_whitespace(self) -> None:
        assert Edit(find="    ax.set_xlim(0, 10)\n", replace="").find == "    ax.set_xlim(0, 10)\n"

    def test_unknown_model_output_fields_are_ignored(self) -> None:
        plan = AdaptPlan.model_validate({"edits": [], "explanation": "free text"})

        assert not hasattr(plan, "explanation")


class TestAdaptAndReviewRequests:
    def test_adapt_request_with_a_previous_plan(self) -> None:
        request = AdaptRequest.model_validate(
            {
                "code": "df = load_user_data()\n",
                "profile": profile(),
                "bindings": [{"role": "x", "column": "x"}],
                "loader_columns": ["x", "y"],
                "previous_plan": {"edits": [{"find": "a", "replace": "b"}]},
                "allow_full": True,
            }
        )

        assert request.previous_plan is not None
        assert request.feedback == []

    def test_adapt_request_refuses_unknown_fields(self) -> None:
        with pytest.raises(ValidationError):
            AdaptRequest.model_validate(
                {"code": "x", "profile": profile(), "bindings": [], "loader_columns": [], "library": "plotly"}
            )

    @pytest.mark.parametrize("render_id", ["r-3f2a_1", "a" * 64])
    def test_review_request_accepts_render_ids(self, render_id: str) -> None:
        request = ReviewRequest(render_id=render_id, code="x", bindings=[], profile_summary="", spec_brief="")

        assert request.render_id == render_id

    @pytest.mark.parametrize("render_id", ["", "../plot-light.png", "a" * 65, "r 1"])
    def test_review_request_refuses_path_like_render_ids(self, render_id: str) -> None:
        with pytest.raises(ValidationError):
            ReviewRequest(render_id=render_id, code="x", bindings=[], profile_summary="", spec_brief="")


class TestDefect:
    def test_ids_are_the_reviewer_checklist(self) -> None:
        ids = set(get_args(DefectId))

        assert ids == {"VQ-01", "VQ-02", "VQ-03", "VQ-06", "VQ-07", "SC-01", "SC-03", "SC-04", "DQ-03", "AR-09"}
        assert ids <= set(CRITERIA) | set(AR_IDS)

    @pytest.mark.parametrize("defect_id", get_args(DefectId))
    @pytest.mark.parametrize("theme", get_args(DefectTheme))
    def test_as_line_matches_the_regen_gate_grammar(self, defect_id: str, theme: str) -> None:
        line = Defect.model_validate(defect(id=defect_id, theme=theme)).as_line()

        match = DEFECT_RE.match(line)
        assert match is not None
        assert match.group("render") == theme
        assert weakness_class(line) == DEFECT
        assert defect_ids(line) == [defect_id]

    def test_as_line_layout(self) -> None:
        line = Defect.model_validate(defect(target="at least 14 px (+5 px).", likely_cause="labelsize=6.")).as_line()

        assert line == "VQ-01 (dark): tick labels 9 px tall → at least 14 px (+5 px). Likely cause: labelsize=6."
        assert defect_target(line) == "at least 14 px (+5 px)."

    def test_text_is_collapsed_to_one_line(self) -> None:
        line = Defect.model_validate(defect(observed="legend\n  overlaps\tthe data")).as_line()

        assert "\n" not in line
        assert "legend overlaps the data →" in line

    def test_arrow_in_observed_cannot_move_the_target(self) -> None:
        line = Defect.model_validate(defect(observed="x → x^2 axis label clipped")).as_line()

        assert defect_target(line).startswith("at least 14 px")

    @pytest.mark.parametrize("defect_id", ["DE-01", "LM-02", "VQ-04", "AR-01", "vq-01"])
    def test_ids_outside_the_fixed_set_are_refused(self, defect_id: str) -> None:
        with pytest.raises(ValidationError):
            Defect.model_validate(defect(id=defect_id))

    def test_unknown_theme_is_refused(self) -> None:
        with pytest.raises(ValidationError):
            Defect.model_validate(defect(theme="sepia"))

    @pytest.mark.parametrize("field", ["observed", "target", "likely_cause"])
    def test_text_fields_are_bounded(self, field: str) -> None:
        with pytest.raises(ValidationError):
            Defect.model_validate(defect(**{field: "w" * (MAX_DEFECT_TEXT_CHARS + 1)}))
        with pytest.raises(ValidationError):
            Defect.model_validate(defect(**{field: "   "}))

    def test_replaced_arrows_count_toward_the_limit(self) -> None:
        with pytest.raises(ValidationError):
            Defect.model_validate(defect(observed="→" * MAX_DEFECT_TEXT_CHARS))

    def test_the_longest_defect_line_is_a_valid_feedback_and_residual_line(self) -> None:
        text = "w" * MAX_DEFECT_TEXT_CHARS
        longest = Defect.model_validate(
            defect(id="AR-09", theme="light", observed=text, target=text, likely_cause=text)
        ).as_line()

        assert len(longest) <= MAX_LINE_CHARS
        request = AdaptRequest.model_validate(
            {"code": "x", "profile": profile(), "bindings": [], "loader_columns": [], "feedback": [longest]}
        )
        assert request.feedback == [longest]
        result = PlotResult(status="needs_attention", attempts=2, residual_defects=[longest])
        assert result.residual_defects == [longest]


class TestVerdict:
    def test_pass_without_defects(self) -> None:
        assert Verdict(ok=True).defects == []

    def test_rejection_holds_one_to_five_defects(self) -> None:
        assert len(Verdict(ok=False, defects=[Defect.model_validate(defect())] * 5).defects) == 5
        with pytest.raises(ValidationError):
            Verdict(ok=False, defects=[Defect.model_validate(defect())] * 6)

    def test_pass_with_defects_is_refused(self) -> None:
        with pytest.raises(ValidationError, match="ok verdict names no defects"):
            Verdict(ok=True, defects=[Defect.model_validate(defect())])

    def test_rejection_without_defects_is_refused(self) -> None:
        with pytest.raises(ValidationError, match="at least one defect"):
            Verdict(ok=False)


def strict_errors(schema: type[Verdict] | type[AdaptPlan], data: dict[str, Any]) -> list[tuple[Any, str]]:
    """The location and type of every rule `data` breaks in the strict schema."""
    with pytest.raises(ValidationError) as caught:
        schema.model_validate(data)
    return [(error["loc"], error["type"]) for error in caught.value.errors()]


class TestRepairVerdict:
    """The reviewer answers spike X and the rerun could not read, each mended to a valid verdict."""

    def test_long_observed_is_clipped_with_an_ellipsis(self) -> None:
        long = "the x tick labels " + "overlap the axis title " * 10
        answer = {"ok": False, "defects": [defect(id="VQ-02", observed=long)]}
        assert strict_errors(Verdict, answer) == [(("defects", 0, "observed"), "string_too_long")]

        verdict = Verdict.model_validate(repair_verdict(answer))

        observed = verdict.defects[0].observed
        assert len(observed) == MAX_DEFECT_TEXT_CHARS and observed.endswith(ELLIPSIS)
        assert observed.startswith("the x tick labels overlap the axis title")

    def test_arrows_count_before_the_clip(self) -> None:
        answer = {"ok": False, "defects": [defect(observed="→" * MAX_DEFECT_TEXT_CHARS)]}

        verdict = Verdict.model_validate(repair_verdict(answer))

        assert len(verdict.defects[0].observed) == MAX_DEFECT_TEXT_CHARS
        assert verdict.defects[0].as_line().count("→") == 1

    def test_ok_with_defects_becomes_a_rejection(self) -> None:
        answer = {"ok": True, "defects": [defect()]}
        assert strict_errors(Verdict, answer) == [((), "value_error")]

        verdict = Verdict.model_validate(repair_verdict(answer))

        assert verdict.ok is False and [item.id for item in verdict.defects] == ["VQ-01"]

    def test_six_defects_keep_the_first_five(self) -> None:
        ids = ["AR-09", "VQ-01", "VQ-02", "VQ-03", "VQ-06", "SC-03"]
        answer = {"ok": False, "defects": [defect(id=item) for item in ids]}
        assert strict_errors(Verdict, answer) == [(("defects",), "too_long")]

        verdict = Verdict.model_validate(repair_verdict(answer))

        assert [item.id for item in verdict.defects] == ids[:5]

    @pytest.mark.parametrize(("theme", "kept"), [("both", "both"), ("Dark", "dark"), ("light and dark", "both")])
    def test_theme_is_case_folded_and_an_unknown_one_becomes_both(self, theme: str, kept: str) -> None:
        answer = {"ok": False, "defects": [defect(theme=theme)]}

        verdict = Verdict.model_validate(repair_verdict(answer))

        assert verdict.defects[0].theme == kept  # the pipeline files `both` under the rendered theme

    def test_unknown_id_is_dropped_and_the_rest_kept(self) -> None:
        answer = {"ok": False, "defects": [defect(id="VQ-05"), defect(id="vq-02")]}
        assert strict_errors(Verdict, answer) == [
            (("defects", 0, "id"), "literal_error"),
            (("defects", 1, "id"), "literal_error"),
        ]

        verdict = Verdict.model_validate(repair_verdict(answer))

        assert [item.id for item in verdict.defects] == ["VQ-02"]

    def test_a_pass_whose_only_defects_are_off_the_checklist_stays_a_pass(self) -> None:
        # The style guide that the reviewer reads names VQ-05; the reviewer's checklist leaves it out.
        answer = {"ok": True, "defects": [defect(id="VQ-05"), defect(id="vq-04")]}
        assert strict_errors(Verdict, answer)

        verdict = Verdict.model_validate(repair_verdict(answer))

        assert (verdict.ok, verdict.defects) == (True, [])

    def test_defects_sent_as_json_text_are_read(self) -> None:
        answer = {"ok": False, "defects": json.dumps([defect()])}

        assert [item.id for item in Verdict.model_validate(repair_verdict(answer)).defects] == ["VQ-01"]

    @pytest.mark.parametrize(
        "answer",
        [
            {"ok": False, "defects": []},
            {"ok": False, "defects": [defect(id="VQ-05")]},
            {"defects": [defect(id="VQ-05")]},
            {"ok": True, "defects": [defect(id="VQ-05"), defect(likely_cause="  ")]},
            {"ok": True, "defects": [defect(likely_cause="  ")]},
            {"defects": [{"id": "VQ-01"}]},
            {},
        ],
        ids=[
            "rejection-without-defects",
            "rejection-with-only-unknown-ids",
            "unknown-ids-without-ok",
            "pass-with-an-unknown-id-and-a-broken-checklist-defect",
            "defect-without-cause",
            "defect-without-texts",
            "empty",
        ],
    )
    def test_an_answer_without_a_usable_defect_stays_invalid(self, answer: dict[str, Any]) -> None:
        with pytest.raises(ValidationError):
            Verdict.model_validate(repair_verdict(answer))

    def test_a_valid_verdict_is_unchanged(self) -> None:
        answer = {"ok": False, "defects": [defect()]}

        assert Verdict.model_validate(repair_verdict(answer)) == Verdict.model_validate(answer)


class TestRepairPlan:
    def test_six_changes_keep_the_first_five(self) -> None:
        answer = {"edits": [], "changes": [f"change {number}" for number in range(6)]}
        assert strict_errors(AdaptPlan, answer) == [(("changes",), "too_long")]

        assert AdaptPlan.model_validate(repair_plan(answer)).changes == [f"change {n}" for n in range(5)]

    def test_long_title_and_changes_are_clipped(self) -> None:
        answer = {"title": "t" * (MAX_TITLE_CHARS + 5), "changes": ["c" * (MAX_CHANGE_CHARS + 1), "  "]}

        plan = AdaptPlan.model_validate(repair_plan(answer))

        assert len(plan.title) == MAX_TITLE_CHARS and plan.title.endswith(ELLIPSIS)
        assert len(plan.changes) == 1 and len(plan.changes[0]) == MAX_CHANGE_CHARS

    def test_blank_full_code_means_no_full_file(self) -> None:
        answer = {"edits": [{"find": "a", "replace": "b"}], "full_code": "", "title": None}
        assert (("full_code",), "string_too_short") in strict_errors(AdaptPlan, answer)

        plan = AdaptPlan.model_validate(repair_plan(answer))

        assert (plan.full_code, plan.title, len(plan.edits)) == (None, "", 1)

    def test_edits_sent_as_json_text_are_read_unchanged(self) -> None:
        edits = [{"find": "x = [1, 2]\n", "replace": "x = df['x']\n"}]

        plan = AdaptPlan.model_validate(repair_plan({"edits": json.dumps(edits)}))

        assert [edit.model_dump() for edit in plan.edits] == edits

    @pytest.mark.parametrize(
        "answer",
        [
            {"edits": [{"find": "", "replace": "b"}]},
            {"edits": [{"replace": "b"}]},
            {"edits": [{"find": f"a{number}", "replace": "b"} for number in range(21)]},
            {"edits": [{"find": "a", "replace": "b"}], "full_code": "import numpy as np\n"},
        ],
        ids=["empty-find", "missing-find", "21-edits", "edits-and-full-code"],
    )
    def test_the_edit_contract_is_never_repaired(self, answer: dict[str, Any]) -> None:
        with pytest.raises(ValidationError):
            AdaptPlan.model_validate(repair_plan(answer))


class TestPlotResult:
    def test_ok(self) -> None:
        result = PlotResult(
            status="ok", attempts=1, artifacts=["plot-light.png", "plot-dark.png", "plot.py", "data.csv"]
        )

        assert result.reason is None
        assert result.residual_defects == []
        assert result.version is None  # set once the version is stored

    def test_only_a_shipped_result_carries_a_version(self) -> None:
        assert PlotResult(status="ok", attempts=1, version=2).version == 2
        with pytest.raises(ValidationError, match="stores no version"):
            PlotResult(status="failed", reason="render", attempts=1, version=1)
        with pytest.raises(ValidationError, match="stores no version"):
            PlotResult(status="not_ready", reason="no_dataset", version=1)
        with pytest.raises(ValidationError):
            PlotResult(status="ok", attempts=1, version=0)

    def test_needs_attention_names_its_residual_defects(self) -> None:
        result = PlotResult(status="needs_attention", attempts=2, residual_defects=["canvas padded after render"])

        assert result.status == "needs_attention"
        with pytest.raises(ValidationError, match="residual defects"):
            PlotResult(status="needs_attention", attempts=2)

    @pytest.mark.parametrize("reason", ["validation", "render", "deadline", "budget", "error"])
    def test_failed_needs_a_failure_reason(self, reason: str) -> None:
        assert PlotResult(status="failed", reason=reason, attempts=2).reason == reason

    @pytest.mark.parametrize("reason", [None, "no_dataset"])
    def test_failed_refuses_a_missing_or_foreign_reason(self, reason: str | None) -> None:
        with pytest.raises(ValidationError, match="failed result"):
            PlotResult(status="failed", reason=reason, attempts=1)

    @pytest.mark.parametrize("reason", ["no_dataset", "incomplete_bindings"])
    def test_not_ready_shortcut(self, reason: Any) -> None:
        result = PlotResult.not_ready(reason)

        assert result.status == "not_ready"
        assert result.reason == reason
        assert result.attempts == 0

    def test_not_ready_refuses_a_failure_reason_and_attempts(self) -> None:
        with pytest.raises(ValidationError, match="not_ready result"):
            PlotResult(status="not_ready", reason="budget")
        with pytest.raises(ValidationError, match="no attempts"):
            PlotResult(status="not_ready", reason="no_dataset", attempts=1)

    def test_ok_refuses_a_reason_and_residual_defects(self) -> None:
        with pytest.raises(ValidationError, match="carries no reason"):
            PlotResult(status="ok", reason="error", attempts=1)
        with pytest.raises(ValidationError, match="needs_attention"):
            PlotResult(status="ok", attempts=1, residual_defects=["VQ-01 (dark): x → y. Likely cause: z."])

    def test_ok_needs_an_attempt(self) -> None:
        with pytest.raises(ValidationError, match="at least one attempt"):
            PlotResult(status="ok")

    @pytest.mark.parametrize("status", ["done", "OK", "partial"])
    def test_unknown_status_is_refused(self, status: str) -> None:
        with pytest.raises(ValidationError):
            PlotResult.model_validate({"status": status, "attempts": 1})

    def test_artifacts_come_from_the_allowlist_once(self) -> None:
        with pytest.raises(ValidationError):
            PlotResult(status="ok", attempts=1, artifacts=["plot.html"])
        with pytest.raises(ValidationError, match="unique"):
            PlotResult(status="ok", attempts=1, artifacts=["plot.py", "plot.py"])

    def test_attempts_are_bounded_by_the_largest_attempt_setting(self) -> None:
        assert PlotResult(status="failed", reason="render", attempts=MAX_ATTEMPTS).attempts == 3
        with pytest.raises(ValidationError):
            PlotResult(status="failed", reason="render", attempts=MAX_ATTEMPTS + 1)
