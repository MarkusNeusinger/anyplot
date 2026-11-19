"""Tests for agents/evals/ladder_lab.py: the pure helpers; no CLI, no model, no renderer."""

import asyncio
import json
from pathlib import Path

import pytest

from agents.anyplot.scoring import SCORED
from agents.evals import ladder_lab


CASES_DIR = Path(__file__).resolve().parents[4] / "agents" / "evals" / "fixtures" / "cases"


def result(**deductions: int) -> dict:
    return {"points": {item: SCORED[item] - deductions.get(item, 0) for item in SCORED}}


def test_a_promoted_case_never_opens_in_the_lab(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Every lab call goes through the Claude Code CLI, which is not Vertex AI, so the lab must never hold a promoted
    case (`agents/evals/replay.py`). It opens cases from the committed fixtures alone: an id that only the promoted
    directory holds fails before any call, also when that directory is the one the harness reads."""
    from agents.anyplot.dev_fixture import FixtureError
    from agents.evals import import_case

    promoted = tmp_path / ".cases"
    case_dir = promoted / "case-invented-promoted"
    case_dir.mkdir(parents=True)
    fields = {"spec_id": "scatter-basic", "library": "matplotlib", "bindings": [], "expected": "rejected"}
    (case_dir / "case.json").write_text(json.dumps(fields), encoding="utf-8")
    (case_dir / "data.csv").write_text("a,b\n1,2\n", encoding="utf-8")
    monkeypatch.setattr(import_case, "PROMOTED_DIR", promoted)

    with pytest.raises(FixtureError, match="case-invented-promoted"):
        ladder_lab.open_case("case-invented-promoted")


def test_seed_cases_are_twenty_existing_fixtures() -> None:
    cases = ladder_lab.seed_cases()
    assert len(cases) == len(set(cases)) == 20
    assert all((CASES_DIR / case).is_dir() for case in cases)


def test_ask_sends_the_image_before_the_text_and_retries_a_failed_call(monkeypatch: pytest.MonkeyPatch) -> None:
    from agents.anyplot.cli_transport import ClaudeCliClient

    seen: list[list[str]] = []
    answers = iter(
        [
            json.dumps({"type": "result", "is_error": True, "result": "limit"}),
            json.dumps({"type": "result", "is_error": False, "structured_output": {"ok": True}}),
        ]
    )

    async def runner(argv: list[str], stdin: bytes, cwd: str) -> str:
        content = json.loads(stdin)["message"]["content"]
        seen.append([block["type"] for block in content])
        return next(answers)

    monkeypatch.setattr(ladder_lab, "_CLIENT", [ClaudeCliClient(runner=runner, executable="claude")])
    answer = asyncio.run(ladder_lab.ask("haiku", "SYSTEM", "look", {"type": "object"}, role="reviewer", png=b"png"))
    assert answer == {"ok": True}
    assert seen == [["image", "text"], ["image", "text"]]


def test_score_plan_parses_counts_and_refuses_unknown_models() -> None:
    assert ladder_lab.score_plan("opus:3, sonnet:1,haiku") == [("opus", 3), ("sonnet", 1), ("haiku", 1)]
    with pytest.raises(ladder_lab.LabError):
        ladder_lab.score_plan("gpt:1")


def test_suggestion_line_keeps_one_prefix() -> None:
    assert ladder_lab.suggestion_line("Suggestion: add a grid.") == "Suggestion: add a grid."
    assert ladder_lab.suggestion_line("add a grid.") == "Suggestion: add a grid."


def test_detection_counts_against_the_deductions_two_reference_runs_agree_on() -> None:
    reference = [result(**{"VQ-03": 2, "SC-01": 3}), result(**{"VQ-03": 1}), result(**{"SC-01": 2, "VQ-02": 1})]
    # Agreed: VQ-03 and SC-01 (two runs each); VQ-02 only once. DE never counts.
    assert ladder_lab.detection(reference, result(**{"VQ-03": 1, "DE-01": 2, "DQ-03": 1})) == (1, 1, 1)
    assert ladder_lab.detection(reference, {"ids": ["SC-01", "VQ-01"]}) == (1, 1, 1)
    assert ladder_lab.detection(reference, None) == (0, 0, 0)


def test_seeds_of_narrows_to_the_selected_cases(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    for case in ("a", "b", "c"):
        (tmp_path / "seeds" / case).mkdir(parents=True)
        (tmp_path / "seeds" / case / "plot.png").write_bytes(b"png")
    (tmp_path / "seeds" / "failed-one").mkdir()
    monkeypatch.setattr(ladder_lab, "SELECTED", [])
    assert ladder_lab.seeds_of(tmp_path) == ["a", "b", "c"]
    monkeypatch.setattr(ladder_lab, "SELECTED", ["c", "a", "missing"])
    assert ladder_lab.seeds_of(tmp_path) == ["a", "c"]


def test_arms_are_unique_and_well_formed() -> None:
    names = [arm.name for arm in ladder_lab.ARMS]
    assert len(names) == len(set(names))
    for arm in ladder_lab.ARMS:
        assert arm.repairer in ladder_lab.MODELS
        assert arm.feedback in ("review", "lines", "suggest", "advisor")
        assert (arm.advisor is not None) == (arm.feedback == "advisor")
