"""Tests for agents/evals/score.py and the harness's --keep-attempts recorder; no model, no renderer."""

import asyncio
import json
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import anthropic
import httpx
import pytest

from agents.anyplot.render.contract import RenderJob, RenderResult, ThemeOutput
from agents.anyplot.scoring import SCORED, ScoreError, ScoreRequest, parse_answer
from agents.evals import score
from agents.evals.matrix import AttemptRecorder


def answer(**overrides: int) -> dict[str, Any]:
    points = {**SCORED, **overrides}
    return {
        "items": [{"id": name, "points": value} for name, value in points.items()],
        "defects": [
            f"{name} (light): off → on. Likely cause: x." for name, value in overrides.items() if value < SCORED[name]
        ],
        "suggestions": [],
        "description": "A plot.",
    }


def entry(turn: str, render: int) -> dict[str, Any]:
    stem = f"attempts/case-r1-{turn}-n{render}"
    return {
        "turn": turn,
        "render": render,
        "theme": "light",
        "png": f"{stem}.png",
        "code": f"{stem}.py",
        "data": "attempts/case-r1.csv",
    }


def record(**fields: Any) -> dict[str, Any]:
    base = {"case_id": "scatter-basic-matplotlib", "spec_id": "scatter-basic", "library": "matplotlib", "repeat": 1}
    return {**base, **fields}


class TestWhichRenders:
    @pytest.mark.parametrize(
        ("stages", "shipped", "expected"),
        [
            (["reviewer_ok"], 1, 1),
            (["reviewer_defects", "reviewer_ok"], 2, 2),
            (["edit_apply", "reviewer_ok"], 2, 1),  # attempt 1 failed its check and rendered nothing
            (["reviewer_defects", "validator"], 1, 1),  # the repair failed its check, attempt 1 shipped
            (["validator"], 1, None),
            ([], 1, None),
        ],
    )
    def test_shipped_render_index(self, stages: list[str], shipped: int, expected: int | None) -> None:
        assert score.shipped_render_index({"stages": stages, "shipped_attempt": shipped}) == expected

    def test_one_render_shipped_at_once_is_one_target(self, tmp_path: Path) -> None:
        found = score.targets_of(
            record(status="ok", stages=["reviewer_ok"], shipped_attempt=1, attempt_renders=[entry("m1", 1)]), tmp_path
        )

        assert [target.role for target in found] == ["both"]
        assert found[0].png == tmp_path / "attempts/case-r1-m1-n1.png"

    def test_a_repaired_run_has_a_first_and_a_shipped_target(self, tmp_path: Path) -> None:
        renders = [entry("m1", 1), entry("m1", 2)]
        run = record(
            status="ok", stages=["reviewer_defects", "reviewer_ok"], shipped_attempt=2, attempt_renders=renders
        )

        found = score.targets_of(run, tmp_path)

        assert [(target.role, target.png.name) for target in found] == [
            ("first", "case-r1-m1-n1.png"),
            ("shipped", "case-r1-m1-n2.png"),
        ]

    def test_a_change_request_ships_from_the_last_turn(self, tmp_path: Path) -> None:
        renders = [entry("m1", 1), entry("m2", 1)]
        run = record(status="needs_attention", stages=["reviewer_defects"], shipped_attempt=1, attempt_renders=renders)

        assert [target.png.name for target in score.targets_of(run, tmp_path)] == [
            "case-r1-m1-n1.png",
            "case-r1-m2-n1.png",
        ]

    def test_a_failed_run_has_only_its_first_render(self, tmp_path: Path) -> None:
        run = record(
            status="failed", stages=["render", "render"], shipped_attempt=None, attempt_renders=[entry("m1", 1)]
        )

        assert [target.role for target in score.targets_of(run, tmp_path)] == ["first"]
        assert score.targets_of(record(status="failed", attempt_renders=[]), tmp_path) == []


class FakeMessages:
    """Answers each create() with the next scripted tool input (or a text-only reply for None)."""

    def __init__(self, inputs: list[dict[str, Any] | None], error: Exception | None = None) -> None:
        self.inputs = list(inputs)
        self.error = error
        self.calls: list[dict[str, Any]] = []

    async def create(self, **kwargs: Any) -> Any:
        self.calls.append(kwargs)
        if self.error is not None:
            raise self.error
        tool_input = self.inputs.pop(0) if self.inputs else None
        content = [SimpleNamespace(type="text", text="thinking aloud")]
        if tool_input is not None:
            content = [SimpleNamespace(type="tool_use", id="toolu_1", name="submit_score", input=tool_input)]
        usage = SimpleNamespace(
            input_tokens=1000, output_tokens=500, cache_read_input_tokens=200, cache_creation_input_tokens=0
        )
        return SimpleNamespace(content=content, usage=usage, stop_reason="tool_use" if tool_input else "end_turn")


def scorer_with(messages: FakeMessages) -> score.Scorer:
    return score.Scorer("claude-opus-5-5", "eu", "high", system="SYSTEM", client=SimpleNamespace(messages=messages))


REQUEST = ScoreRequest("spec", "code", "2 rows", "[]", b"\x89PNG")


class TestScorer:
    def test_a_complete_answer_is_scored_with_its_tokens(self) -> None:
        messages = FakeMessages([answer(**{"VQ-01": 6})])

        result, tokens, _ = asyncio.run(scorer_with(messages).score(REQUEST))

        assert result.points["VQ-01"] == 6
        assert tokens == {"prompt": 1200, "cached": 200, "cache_write": 0, "candidates": 500}
        call = messages.calls[0]
        assert call["model"] == "claude-opus-5-5" and call["tool_choice"] == {"type": "auto"}
        assert call["tools"][0]["strict"] is True and call["output_config"] == {"effort": "high"}
        assert call["system"][0]["cache_control"] == {"type": "ephemeral"}
        assert [block["type"] for block in call["messages"][0]["content"]] == ["text", "image"]

    def test_an_incomplete_answer_is_asked_again_once_in_the_same_conversation(self) -> None:
        broken = answer()
        broken["items"] = broken["items"][:-1]
        messages = FakeMessages([None, broken])

        with pytest.raises(ScoreError, match="criteria missing"):
            asyncio.run(scorer_with(messages).score(REQUEST))
        assert len(messages.calls) == 2
        second = messages.calls[1]["messages"]
        assert [message["role"] for message in second] == ["user", "assistant", "user"]

    def test_a_missing_model_stops_before_any_scoring(self) -> None:
        response = httpx.Response(404, request=httpx.Request("POST", "https://vertex"))
        messages = FakeMessages([], error=anthropic.NotFoundError("not found", response=response, body=None))

        with pytest.raises(score.SetupError, match="not found or not enabled"):
            asyncio.run(scorer_with(messages).probe())

    def test_a_large_png_is_re_encoded_smaller(self) -> None:
        from io import BytesIO

        import numpy as np
        from PIL import Image

        buffer = BytesIO()
        Image.fromarray(np.random.default_rng(0).integers(0, 255, (1800, 3200, 3), dtype=np.uint8)).save(buffer, "PNG")
        block = score.image_block(buffer.getvalue())

        assert len(block["source"]["data"]) * 3 / 4 < len(buffer.getvalue())


class TestScoreAll:
    def jobs(self, count: int) -> list[tuple[score.Target, ScoreRequest]]:
        target = score.Target(
            "a#r1", "a", "scatter-basic", "matplotlib", "first", Path("p"), Path("c"), Path("d"), "light", "en", None
        )
        return [(target, REQUEST)] * count

    def test_calls_are_paced_and_priced(self) -> None:
        messages = FakeMessages([answer()] * 3)
        sleeps: list[float] = []

        async def sleep(seconds: float) -> None:
            sleeps.append(seconds)

        outcome = asyncio.run(
            score.score_all(
                scorer_with(messages),
                self.jobs(3),
                calls_per_minute=2,
                echo=lambda _: None,
                sleep=sleep,
                clock=lambda: 0.0,
            )
        )

        assert outcome.stopped is None and len(outcome.scored) == 3
        assert sleeps == [30.0, 30.0]  # the clock stands still, so every later start waits the whole interval
        assert all(item.cost_usd > 0 for item in outcome.scored)

    def test_the_budget_stops_before_the_next_call_could_pass_it(self) -> None:
        messages = FakeMessages([answer()] * 5)

        outcome = asyncio.run(
            score.score_all(
                scorer_with(messages), self.jobs(5), calls_per_minute=0, budget_usd=0.03, echo=lambda _: None
            )
        )

        assert outcome.stopped is not None and outcome.stopped.startswith("budget")
        assert 1 <= len(outcome.scored) < 5

    def test_a_rate_limit_stops_the_run_without_a_retry(self) -> None:
        response = httpx.Response(429, request=httpx.Request("POST", "https://vertex"))
        error = anthropic.RateLimitError(
            "Quota exceeded for metric: input_tokens_per_minute", response=response, body=None
        )
        messages = FakeMessages([], error=error)

        outcome = asyncio.run(
            score.score_all(scorer_with(messages), self.jobs(3), calls_per_minute=0, echo=lambda _: None)
        )

        assert outcome.scored == [] and len(messages.calls) == 1
        assert outcome.stopped is not None and "input_tokens_per_minute" in outcome.stopped

    def test_spread_and_estimate(self) -> None:
        assert score.spread(list(range(10)), 4) == [0, 2, 5, 7]
        assert score.spread([1, 2], 5) == [1, 2]
        assert score.estimate_usd("claude-opus-5-5", "eu", 0) == 0.0
        one, hundred = (score.estimate_usd("claude-opus-5-5", "eu", calls) for calls in (1, 100))
        assert 0.10 < one < 0.20 and 5.0 < hundred < 9.0


def scored(run: str, role: str, value: dict[str, Any]) -> score.Scored:
    target = score.Target(
        run,
        run.split("#")[0],
        "scatter-basic",
        "matplotlib",
        role,
        Path("p"),
        Path("c"),
        Path("d"),
        "light",
        "en",
        None,
    )
    return score.Scored(target, parse_answer(value), cost_usd=0.03, latency_s=20.0)


class TestSummary:
    def test_distributions_repair_gain_and_the_ladder(self) -> None:
        baseline = {"DE-01": 4, "DE-02": 2, "DE-03": 2}
        items = [
            scored("a#r1", "both", answer()),  # 100 at once
            scored("b#r1", "first", answer(**baseline, **{"VQ-01": 2})),
            scored("b#r1", "shipped", answer(**baseline)),  # 84 after the repair
            scored("c#r1", "first", answer(**baseline, **{"VQ-02": 0})),  # 49, capped
            scored("c#r1", "shipped", answer(**baseline, **{"VQ-02": 0})),
        ]
        records = [
            {
                "case_id": "a",
                "repeat": 1,
                "status": "ok",
                "passed": True,
                "advisory": [],
                "cost_usd": 0.005,
                "e2e_s": 18.0,
            },
            {
                "case_id": "b",
                "repeat": 1,
                "status": "ok",
                "passed": True,
                "advisory": [],
                "cost_usd": 0.01,
                "e2e_s": 30.0,
            },
            {
                "case_id": "c",
                "repeat": 1,
                "status": "needs_attention",
                "passed": True,
                "advisory": [],
                "cost_usd": 0.012,
                "e2e_s": 40.0,
            },
        ]

        summary = score.summarize(items, records, "claude-opus-5-5")

        assert summary["first"]["n"] == 3 and summary["shipped"]["n"] == 3
        assert summary["shipped"]["share_ge_80"] == pytest.approx(0.667, abs=0.001)
        assert summary["repair_gain"] == {
            "runs_repaired": 2,
            "improved": 1,
            "same": 1,
            "worse": 0,
            "mean": 4.0,
            "median": 4.0,
        }
        assert summary["ladder"]["90"] == {"runs": 3, "first_try": 1, "after_repair_1": 0, "would_need_advisor": 2}
        assert summary["ladder"]["80"] == {"runs": 3, "first_try": 1, "after_repair_1": 1, "would_need_advisor": 1}
        assert [(item["run"], item["score"]) for item in summary["clean_gates_low_score"]] == [("c#r1", 49)]
        assert summary["points_lost"]["DE-01"] == 16  # four renders at the default 4 of 8
        assert "| first | 3 |" in score.markdown(summary)

    def test_main_refuses_a_report_without_kept_attempts(self, tmp_path: Path) -> None:
        report = tmp_path / "run.json"
        report.write_text(json.dumps({"runs": [{"case_id": "x"}]}), encoding="utf-8")

        assert score.main([str(report)]) == 2


class TestAttemptRecorder:
    def test_keeps_every_render_of_a_turn_with_code_and_data(self, tmp_path: Path) -> None:
        recorder = AttemptRecorder(tmp_path / "attempts")
        entries: list[dict[str, Any]] = []
        job = RenderJob(
            job_id="j",
            language="python",
            library="matplotlib",
            source="code()",
            data_csv="a,b\n1,2\n",
            themes=("light",),
            timeout_s=60,
        )

        recorder.keep(job, RenderResult("j", {"light": ThemeOutput("light", 0, png=b"PNG1")}))  # outside a case
        recorder.begin("scatter-basic-matplotlib-r1-m1", entries)
        recorder.keep(job, RenderResult("j", {"light": ThemeOutput("light", 0, png=b"PNG1")}))
        recorder.keep(job, RenderResult("j", {"light": ThemeOutput("light", 1, png=None)}))
        recorder.end()

        assert [(item["turn"], item["render"], item["png"]) for item in entries] == [
            ("m1", 1, "attempts/scatter-basic-matplotlib-r1-m1-n1.png"),
            ("m1", 2, None),
        ]
        assert (tmp_path / "attempts/scatter-basic-matplotlib-r1-m1-n1.png").read_bytes() == b"PNG1"
        assert (tmp_path / "attempts/scatter-basic-matplotlib-r1-m1-n2.py.txt").read_text() == "code()"
        assert (tmp_path / "attempts/scatter-basic-matplotlib-r1.csv").read_text() == "a,b\n1,2\n"
        assert len(list((tmp_path / "attempts").glob("*.png"))) == 1

    def test_the_wrapper_returns_the_backends_result(self, tmp_path: Path) -> None:
        recorder = AttemptRecorder(tmp_path)
        result = RenderResult("j", {})

        class Inner:
            name = "fake"

            async def render(self, job: RenderJob) -> RenderResult:
                return result

        wrapped = recorder.wrap(Inner())
        job = RenderJob(
            job_id="j", language="python", library="matplotlib", source="", data_csv="", themes=("light",), timeout_s=1
        )

        assert wrapped.name == "fake"
        assert asyncio.run(wrapped.render(job)) is result
