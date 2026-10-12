"""Tests for agents/anyplot/scoring.py: the rubric sections, the answer check, the total and the caps."""

from typing import Any

import pytest

from agents.anyplot.scoring import (
    CRITERIA_SECTIONS,
    REVIEW_SECTIONS,
    SCORED,
    SCORED_MAX,
    TECHNICAL,
    TOOL_SCHEMA,
    ScoreError,
    ScoreRequest,
    parse_answer,
    section,
    system_prompt,
    user_text,
)


def perfect(**overrides: int) -> dict[str, Any]:
    """An answer at every maximum (Design Excellence too), with the given points changed."""
    points = {**SCORED, **overrides}
    return {
        "items": [{"id": name, "points": value} for name, value in points.items()],
        "defects": [],
        "suggestions": [],
        "description": "A scatter of the user's two columns.",
    }


class TestRubric:
    def test_the_scored_criteria_are_the_user_visible_ones(self) -> None:
        assert SCORED_MAX == 75
        assert len(SCORED) == 16
        assert {name[:2] for name in SCORED} == {"VQ", "DE", "SC", "DQ"}
        assert "DQ-02" not in SCORED and not any(name[:2] in ("CQ", "LM") for name in SCORED)
        assert set(TECHNICAL) == {name for name in SCORED if not name.startswith("DE")}

    def test_section_runs_to_the_next_heading_of_its_level(self) -> None:
        text = "# A\nintro\n## B\none\n### B1\ntwo\n## C\nthree\n"

        assert section(text, "## B") == "## B\none\n### B1\ntwo"
        assert section(text, "### B1") == "### B1\ntwo"
        with pytest.raises(ValueError):
            section(text, "## D")

    def test_the_system_prompt_carries_the_catalogue_rubric_verbatim(self) -> None:
        prompt = system_prompt()

        for heading in (*CRITERIA_SECTIONS, *REVIEW_SECTIONS):
            assert heading in prompt, heading
        assert prompt.startswith("# Scorer")
        # The catalogue-only categories stay out; their names only appear where the rubric mentions them in passing.
        assert "## Code Quality (10 Points)" not in prompt
        assert "## Library Mastery (10 Points)" not in prompt
        assert "### 8b." not in prompt

    def test_the_tool_schema_is_strict_and_names_every_criterion(self) -> None:
        item = TOOL_SCHEMA["properties"]["items"]["items"]

        assert TOOL_SCHEMA["additionalProperties"] is False and item["additionalProperties"] is False
        assert item["properties"]["id"]["enum"] == list(SCORED)

    def test_user_text_fences_every_value(self) -> None:
        request = ScoreRequest("spec", "code", "3 rows", "[]", b"png", theme="dark", plot_language="de")
        text = user_text(request)

        for block in ("<spec_text>", "<plot_code>", "<user_data>", "<plot_language>de</plot_language>"):
            assert block in text
        assert text.endswith("plot-dark.png")


class TestParseAnswer:
    def test_a_perfect_answer_scores_100(self) -> None:
        result = parse_answer(perfect())

        assert (result.raw, result.scaled, result.score, result.caps) == (75, 100, 100, [])
        assert result.category("VQ") == (30, 30) and result.category("DQ") == (10, 10)

    def test_the_style_guide_baseline_is_the_rubrics_default_design(self) -> None:
        """Defect-free with Design Excellence at its defaults (4, 2, 2): 63 of 75, scaled to 84."""
        result = parse_answer(perfect(**{"DE-01": 4, "DE-02": 2, "DE-03": 2}))

        assert (result.raw, result.score) == (63, 84)

    def test_caps_lower_the_total_only(self) -> None:
        overlap = parse_answer(perfect(**{"VQ-02": 0}))
        boring = parse_answer(perfect(**{"DE-01": 2, "DE-02": 2}))
        wrong_type = parse_answer(perfect(**{"SC-01": 0}))

        assert overlap.score == 49 and overlap.points["VQ-02"] == 0 and overlap.caps
        assert boring.score == 75 and boring.scaled > 75
        assert wrong_type.score == 40

    def test_a_deduction_without_a_line_is_silent(self) -> None:
        answer = perfect(**{"VQ-01": 5, "SC-03": 2})
        answer["defects"] = ["VQ-01 (light): tick labels at 20 px → about 44 px (+24 px). Likely cause: labelsize."]

        result = parse_answer(answer)

        assert result.silent == ["SC-03"]
        assert result.malformed == []

    def test_malformed_lines_are_reported(self) -> None:
        answer = perfect(**{"VQ-03": 4})
        answer["defects"] = [
            "markers too small",
            "VQ-03 (light): 12 markers at 3 px → 10 px (+7 px). Likely cause: s=3.",
        ]

        result = parse_answer(answer)

        assert result.malformed == ["markers too small"]
        assert result.silent == []

    @pytest.mark.parametrize(
        ("change", "message"),
        [
            (lambda answer: answer["items"].pop(), "criteria missing"),
            (lambda answer: answer["items"].append({"id": "VQ-01", "points": 1}), "scored twice"),
            (lambda answer: answer["items"].append({"id": "CQ-01", "points": 1}), "unknown criterion"),
            (lambda answer: answer["items"].__setitem__(0, {"id": "VQ-01", "points": 9}), "outside"),
            (lambda answer: answer["items"].__setitem__(0, {"id": "VQ-01", "points": True}), "outside"),
            (lambda answer: answer.__setitem__("items", "all"), "not a list"),
        ],
    )
    def test_incomplete_answers_are_refused(self, change: Any, message: str) -> None:
        answer = perfect()
        change(answer)

        with pytest.raises(ScoreError, match=message):
            parse_answer(answer)

    def test_suggestions_are_capped_at_three(self) -> None:
        answer = perfect()
        answer["suggestions"] = [f"Suggestion: idea {index}" for index in range(5)]

        assert len(parse_answer(answer).suggestions) == 3
