"""The matrix harness over the two hand-written fixtures, with scripted models and the fake renderer.

The models are the real `VertexClaude` over a fake Anthropic client (every call
reports 100 input and 20 output tokens), so the token booking and the cost come from
the same attribution lines a real run writes. Nothing here calls a model or a renderer.
"""

import asyncio
import json
import os
from pathlib import Path
from typing import Any
from unittest.mock import patch

import pytest

from agents.anyplot.render.backends.fake import FakeBackend, FakeOutcome
from agents.anyplot.run_queue import RunQueue
from agents.anyplot.services import Services
from agents.evals import matrix
from agents.evals.cases import load_cases, select_cases
from agents.evals.matrix import (
    EXIT_OK,
    EXIT_REGRESSION,
    EXIT_SETUP,
    EXIT_STOPPED,
    MatrixConfig,
    configure,
    parse_args,
    parse_events,
    run_matrix,
)
from agents.main import Runtime

from ..runtime.fakes import ROOT_REPLY, SCATTER_PLAN, VERDICT_OK
from .conftest import check_html


CALL_COST = (100 * 0.10 + 20 * 0.50) / 1e6 * 1.10  # one scripted call on claude-haiku-5-5 at eu list price
BAD_PLAN: dict[str, Any] = {
    "edits": [{"find": "this text is not in the code", "replace": "df = load_user_data()"}],
    "title": "Revenue by Quarter",
    "changes": ["Plotted your data"],
}
EMPTY_PLAN: dict[str, Any] = {"edits": [], "changes": []}


def two_fixtures() -> list:
    cases = select_cases(load_cases(promoted_dir=Path("/nonexistent")), "bar-grouped-seaborn,scatter-basic-matplotlib")
    assert [case.case_id for case in cases] == ["bar-grouped-seaborn", "scatter-basic-matplotlib"]
    return cases


def runtime() -> Runtime:
    """One run at a time, without the one-start-a-minute window between the cases."""
    return Runtime(queue=RunQueue(concurrency=1, per_minute=1_000, max_wait_s=600))


def script() -> dict[str, list[Any]]:
    """bar-grouped: two plans whose edit matches nothing; scatter-basic: the working plan and a passing review."""
    return {
        "root": [
            {"call": "plot_pipeline", "args": {}},
            {"text": "The plot could not be made."},
            {"call": "plot_pipeline", "args": {}},
            {"text": ROOT_REPLY},
        ],
        "adapter": [{"json": BAD_PLAN}, {"json": BAD_PLAN}, {"json": SCATTER_PLAN}],
        "reviewer": [{"json": VERDICT_OK}],
    }


def config(tmp_path: Path, **fields: Any) -> MatrixConfig:
    fields.setdefault("cases", "bar-grouped-seaborn,scatter-basic-matplotlib")
    return MatrixConfig(out=tmp_path, **fields)


async def test_two_fixtures_through_the_real_flow(
    tmp_path: Path, services: Services, swap_models, backend: FakeBackend
) -> None:
    swap_models("anthropic-vertex", script())

    result = await run_matrix(
        two_fixtures(), config(tmp_path), services=services, runtime=runtime(), echo=lambda _: None
    )

    assert result.exit_code == EXIT_OK and result.diff is None
    bar, scatter = result.report["runs"]

    assert (scatter["status"], scatter["attempts"], scatter["passed"], scatter["accept_match"]) == ("ok", 1, True, True)
    assert scatter["llm_calls"] == 4
    assert scatter["llm_calls_by_agent"] == {"adapter_matplotlib": 1, "anyplot": 2, "reviewer": 1}
    assert scatter["tokens"]["prompt"] == 400 and scatter["tokens"]["candidates"] == 80
    assert scatter["cost_usd"] == pytest.approx(4 * CALL_COST)
    assert scatter["model_versions"] == ["claude-haiku-5-5"]
    assert scatter["reviewer"] == {"verdict": "ok", "defects": []}
    assert scatter["gate_failures"] == {} and scatter["adapter_outcomes"] == {"plan": 1}
    assert len(scatter["render_s"]) == 1 and scatter["render_wall_s"] == [0.0]
    assert 0 < scatter["ttfe_s"] <= scatter["e2e_s"]
    assert scatter["png"] == "renders/scatter-basic-matplotlib-r1.png"
    assert (tmp_path / scatter["png"]).read_bytes().startswith(b"\x89PNG")

    assert (bar["status"], bar["reason"], bar["attempts"]) == ("failed", "validation", 2)
    assert bar["passed"] is False and bar["accept_match"] is False  # it expects accepted, the run rejected
    assert bar["edit_apply_failures"] >= 2 and bar["adapter_outcomes"] == {"plan": 2}
    assert bar["llm_calls"] == 4 and bar["cost_usd"] == pytest.approx(4 * CALL_COST)
    assert bar["png"] is None and bar["render_s"] == []

    summary = result.report["summary"]
    assert (summary["pass_rate"], summary["accept_match_rate"]) == (0.5, 0.5)
    assert summary["cost_total_usd"] == pytest.approx(8 * CALL_COST)
    assert summary["cost_per_success_usd"] == pytest.approx(8 * CALL_COST)
    assert [job.library for job in backend.jobs] == ["matplotlib"]  # bar-grouped never reached the renderer

    stamp = result.report["stamp"]
    assert (stamp["provider"], stamp["model"], stamp["location"], stamp["case_count"]) == (
        "anthropic-vertex",
        "claude-haiku-5-5",
        "eu",
        2,
    )
    assert result.report_path.name == f"{stamp['date']}-claude-haiku-5-5.json"
    assert json.loads(result.report_path.read_text())["runs"][1]["case_id"] == "scatter-basic-matplotlib"
    assert "## Runs that did not pass" in result.summary_path.read_text()


async def test_outputs_include_both_gallery_pages(tmp_path: Path, services: Services, swap_models) -> None:
    swap_models("anthropic-vertex", script())

    result = await run_matrix(
        two_fixtures(), config(tmp_path), services=services, runtime=runtime(), echo=lambda _: None
    )

    gallery = result.gallery_path.read_text()
    checker = check_html(gallery)
    assert checker.doctype and checker.errors == [] and checker.stack == []
    assert gallery.count('class="card"') == 1  # only scatter-basic shipped a render
    assert "claude" not in gallery.lower()
    every = (tmp_path / "gallery-all.html").read_text()
    assert check_html(every).errors == [] and "bar-grouped-seaborn" in every


async def test_gate_failures_and_a_padded_canvas_do_not_pass(
    tmp_path: Path, services: Services, swap_models, backend: FakeBackend
) -> None:
    backend.script = lambda job, theme: FakeOutcome(size=(3100, 1800))
    swap_models(
        "anthropic-vertex",
        {
            "root": [{"call": "plot_pipeline", "args": {}}, {"text": ROOT_REPLY}],
            "adapter": [{"json": SCATTER_PLAN}, {"json": EMPTY_PLAN}],
            "reviewer": [],
        },
    )
    cases = select_cases(load_cases(promoted_dir=Path("/nonexistent")), "scatter-basic-matplotlib")

    result = await run_matrix(
        cases, config(tmp_path, cases="scatter-basic-matplotlib"), services=services, runtime=runtime(), echo=print
    )

    (record,) = result.report["runs"]
    assert (record["status"], record["attempts"]) == ("needs_attention", 2)
    assert record["padded"] is True and record["passed"] is False
    assert record["gate_failures"] == {"R3": 2}
    assert record["reviewer"]["verdict"] is None  # a padded canvas is never reviewed
    assert record["residual_defects"][0] == "canvas padded after render (light)"


async def test_a_regression_against_the_baseline_exits_non_zero(
    tmp_path: Path, services: Services, swap_models
) -> None:
    swap_models("anthropic-vertex", script())
    first = await run_matrix(
        two_fixtures(), config(tmp_path / "a"), services=services, runtime=runtime(), echo=lambda _: None
    )
    baseline = json.loads(first.report_path.read_text())
    baseline["runs"][0]["passed"] = True  # pretend bar-grouped passed in the baseline
    baseline["summary"]["pass_rate"] = 1.0

    swap_models("anthropic-vertex", script())
    second = await run_matrix(
        two_fixtures(),
        config(tmp_path / "b", baseline=baseline, baseline_path=Path("baseline.json")),
        services=Services(backend_factory=FakeBackend, judge_factory=services.judge_factory),
        runtime=runtime(),
        echo=lambda _: None,
    )

    assert second.exit_code == EXIT_REGRESSION
    assert second.diff is not None and second.diff.flipped == [("bar-grouped-seaborn#1", True, False)]
    assert "Against the baseline" in second.summary_path.read_text()

    swap_models("anthropic-vertex", script())
    same = await run_matrix(
        two_fixtures(),
        config(tmp_path / "c", baseline=json.loads(first.report_path.read_text())),
        services=Services(backend_factory=FakeBackend, judge_factory=services.judge_factory),
        runtime=runtime(),
        echo=lambda _: None,
    )
    assert same.exit_code == EXIT_OK and same.diff is not None and same.diff.flipped == []


async def test_the_budget_stops_the_matrix(tmp_path: Path, services: Services, swap_models) -> None:
    swap_models("anthropic-vertex", script())

    result = await run_matrix(
        two_fixtures(),
        config(tmp_path, budget_usd=CALL_COST),  # the first case alone costs four calls
        services=services,
        runtime=runtime(),
        echo=lambda _: None,
    )

    assert result.exit_code == EXIT_STOPPED
    assert result.report["stopped"] == "budget" and len(result.report["runs"]) == 1
    assert "Stopped early" in result.summary_path.read_text()


async def test_save_baseline_writes_the_model_file(tmp_path: Path, services: Services, swap_models) -> None:
    swap_models("anthropic-vertex", script())

    result = await run_matrix(
        two_fixtures(),
        config(tmp_path, save_baseline=True, baselines_dir=tmp_path / "baselines"),
        services=services,
        runtime=runtime(),
        echo=lambda _: None,
    )

    assert result.baseline_written == tmp_path / "baselines" / "claude-haiku-5-5.json"
    assert matrix.load_baseline(result.baseline_written)["summary"]["passed"] == 1


def test_parse_events_times_each_event_by_its_chunk() -> None:
    chunks = [
        (10.0, b'event: ready\ndata: {"v":"anyplot/1"}\n\n'),
        (10.5, b'event: status\ndata: {"step":"queued","position":1,"waiting":1}\n\n'),
        (11.0, b'event: status\ndata: {"step":"adapting","attempt":1}\n\nevent: do'),
        (12.0, 'ne\ndata: {"llm_calls":4,"tokens":10,"note":"é"}\n\n'.encode()),
    ]

    events = parse_events(chunks, started=9.0)

    assert [(at, name) for at, name, _ in events] == [(1.0, "ready"), (1.5, "status"), (2.0, "status"), (3.0, "done")]
    assert events[-1][2]["note"] == "é"


def test_configure_picks_the_provider_defaults_and_keeps_the_rest() -> None:
    environ: dict[str, str] = {"AGENT_RENDERER": "fake", "AGENT_DEV_FIXTURE": "scatter-basic-matplotlib"}
    configure(parse_args(["--provider", "gemini"]), environ)

    assert (environ["AGENT_PROVIDER"], environ["AGENT_MODEL"], environ["AGENT_JUDGE_MODEL"]) == (
        "gemini",
        "gemini-3.8-flash",
        "gemini-3.5-flash-lite",
    )
    assert environ["AGENT_RENDERER"] == "fake"  # the environment's renderer stays when no flag names one
    assert environ["ENVIRONMENT"] == "development" and environ["PYTHON_DOTENV_DISABLED"] == "1"
    assert "AGENT_DEV_FIXTURE" not in environ
    assert environ["AGENT_RUNS_PER_MINUTE"] == "60"

    claude: dict[str, str] = {"ENVIRONMENT": "test"}
    configure(parse_args(["--model", "claude-haiku-5-5", "--renderer", "remote", "--render-url", "https://r"]), claude)
    assert (claude["AGENT_PROVIDER"], claude["AGENT_JUDGE_MODEL"]) == ("anthropic-vertex", "claude-haiku-5-5")
    assert (claude["AGENT_RENDERER"], claude["AGENT_RENDER_URL"], claude["ENVIRONMENT"]) == (
        "remote",
        "https://r",
        "test",
    )


def test_configure_refuses_contradictions() -> None:
    with pytest.raises(matrix.SetupError, match="needs --renderer remote"):
        configure(parse_args(["--renderer", "fake", "--render-url", "https://r"]), {})
    with pytest.raises(matrix.SetupError, match="cannot tell the provider"):
        configure(parse_args(["--model", "llama-9"]), {})
    with pytest.raises(SystemExit):
        parse_args(["--repeats", "0"])


def test_main_exits_2_when_no_case_matches(tmp_path: Path) -> None:
    with patch.dict(os.environ):
        code = matrix.main(["--cases", "no-such-case-*", "--renderer", "fake", "--out", str(tmp_path)])

    assert code == EXIT_SETUP
    assert not any(tmp_path.iterdir())  # nothing ran, nothing was written


def test_interrupt_writes_the_partial_report(tmp_path: Path, services: Services, swap_models) -> None:
    swap_models("anthropic-vertex", script())

    async def interrupted() -> None:
        task = asyncio.ensure_future(
            run_matrix(two_fixtures(), config(tmp_path), services=services, runtime=runtime(), echo=lambda _: None)
        )
        await asyncio.sleep(0)
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task

    asyncio.run(interrupted())

    (report_path,) = tmp_path.glob("*.json")
    assert json.loads(report_path.read_text())["stopped"] == "interrupted"
