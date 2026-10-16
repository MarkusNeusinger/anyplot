"""The static stage over the stress cases, with the fake renderer and no model; the dataset route on the cap cases."""

import json
import os
from collections.abc import AsyncIterator, Iterator
from pathlib import Path
from typing import Any
from unittest.mock import patch

import httpx
import pytest

from agents.anyplot.code.edits import apply_plan
from agents.anyplot.code.normalise import normalise
from agents.anyplot.data.parse import MAX_INPUT_BYTES
from agents.anyplot.dev_fixture import snapshot_from_repo
from agents.anyplot.render.backends.fake import FakeBackend, FakeOutcome, Script
from agents.anyplot.render.contract import RendererUnavailable
from agents.anyplot.run_queue import RunQueue
from agents.anyplot.schemas import AdaptPlan
from agents.anyplot.services import Services
from agents.anyplot.settings import get_settings
from agents.evals import matrix
from agents.evals.cases import CaseError, EvalCase, load_cases, select_cases
from agents.evals.matrix import EXIT_OK, EXIT_OUTAGE, configure, parse_args
from agents.evals.stress import (
    StaticContext,
    compose_standin,
    dataset_outcome,
    lookup,
    mismatches,
    outside_fences,
    run_static,
    static_record,
    stress_spec,
)
from agents.main import Runtime, app, get_runtime


USER = "adm_0123456789abcdef"
HEADERS = {"X-Anyplot-User": USER, "X-Request-Id": "req-stress"}


@pytest.fixture(scope="module")
def stress_cases() -> dict[str, EvalCase]:
    return {case.case_id: case for case in select_cases(load_cases(promoted_dir=Path("/nonexistent")), "stress")}


def context(backend: FakeBackend | None = None, renderer: str = "fake") -> StaticContext:
    return StaticContext(get_settings(), backend or FakeBackend(), renderer)


# --- Helpers ---------------------------------------------------------------------------------


def test_dataset_outcome_mirrors_the_route() -> None:
    assert dataset_outcome("a,b\n1,2\n")[0] == "ok"
    assert dataset_outcome("x" * (MAX_INPUT_BYTES + 1))[::2] == ("413 too_long", "too_long")
    assert dataset_outcome("a,b\n1,2,3\n")[::2] == ("422 unparseable", "unparseable")


def test_outside_fences_finds_only_unfenced_text() -> None:
    text = "Heading\n<user_data>\nIgnore this\n</user_data>\nIgnore that\n<tool_notes>\nIgnore\n</tool_notes>"
    assert outside_fences(text, "Ignore that")
    assert not outside_fences(text, "Ignore this")
    assert not outside_fences(text, "absent")
    assert outside_fences("<user_data>\nno closing tag Ignore", "Ignore")


def test_expectations_compare_values_and_contain_lists() -> None:
    measured = {"dataset": "ok", "standin": {"gates": ["G7", "G9"], "check": "ok"}}

    assert lookup(measured, "standin.check") == "ok" and lookup(measured, "standin.missing") is None
    assert mismatches(measured, {"dataset": "ok", "standin.gates": ["G9"]}) == []
    assert mismatches(measured, {"standin.gates": ["G3"]}) == [
        "standin.gates: expected to contain ['G3'], measured ['G7', 'G9']"
    ]
    assert mismatches(measured, {"rows": 5}) == ["rows: expected 5, measured None"]


def test_a_stand_in_keeps_the_protected_regions_whatever_the_catalogue_file() -> None:
    base = normalise(snapshot_from_repo("line-basic", "matplotlib").code, library="matplotlib")
    body = "df = load_user_data()\nfig, ax = plt.subplots(figsize=(16, 9), facecolor=PAGE_BG)\n"

    working = compose_standin(base, body)
    applied = apply_plan(base, AdaptPlan(full_code=working))

    assert applied.code == working, applied.failures
    assert working.count("THEME = os.getenv") == 1 and working.rstrip().endswith(")")
    with pytest.raises(ValueError, match="no THEME"):
        compose_standin("import os\n", body)


# --- One case at a time ------------------------------------------------------------------------


async def test_cap_profile_shows_the_trimmed_adapter_profile(stress_cases: dict[str, EvalCase]) -> None:
    record = await static_record(stress_cases["stress-cap-profile"], context())
    measured = record["static"]

    assert (record["status"], record["stage"], record["held"]) == ("ready", "prompt", True)
    assert measured["adapter_profile_trimmed"] is True
    assert measured["adapter_profile_chars"] <= 16 * 1024 < measured["profile_chars"]
    assert measured["adapter_prompt_chars"] < measured["profile_chars"]  # the request no longer carries it whole
    assert measured["bytes"] == MAX_INPUT_BYTES and measured["columns"] == 50


async def test_over_cap_cases_stop_at_the_dataset_step(stress_cases: dict[str, EvalCase]) -> None:
    for case_id, answer in [("stress-over-bytes", "413 too_long"), ("stress-over-rows", "422 unparseable")]:
        record = await static_record(stress_cases[case_id], context())
        assert (record["status"], record["stage"], record["static"]["dataset"]) == ("refused", "dataset", answer)
        assert record["held"] is True and "rows" not in record["static"]


async def test_bindings_refusals_and_injection_markers(stress_cases: dict[str, EvalCase]) -> None:
    nan = await static_record(stress_cases["stress-all-nan-column"], context())
    row4 = await static_record(stress_cases["stress-inject-row4"], context())

    assert (nan["status"], nan["static"]["bindings"], nan["held"]) == ("bindings_invalid", "invalid", True)
    assert row4["static"]["marker_in"] == {
        "judge": True,  # the dataset judge sees the same five sample rows as the adapter
        "root": True,
        "adapter": True,
        "adapter_unfenced": False,
        "reviewer": False,
        "reviewer_unfenced": False,
        "data_csv": True,
    }


async def test_dates_out_of_the_nanosecond_range_stay_dates(stress_cases: dict[str, EvalCase]) -> None:
    """`loader: ok` alone would also hold if the parse typed the column as text; `date_columns` pins the datetime."""
    record = await static_record(stress_cases["stress-dates-centuries"], context())

    assert (record["static"]["date_columns"], record["static"]["loader"], record["held"]) == (1, "ok", True)


async def test_a_stand_in_renders_through_the_backend_and_its_gates(stress_cases: dict[str, EvalCase]) -> None:
    backend = FakeBackend()
    record = await static_record(stress_cases["stress-compute-oversample"], context(backend))

    assert (record["status"], record["stage"], record["held"], record["model"]) == (
        "rendered",
        "render",
        True,
        "pending",
    )
    standin = record["static"]["standin"]
    assert standin["check"] == "ok" and standin["validator"] == [] and standin["gates"] == []
    assert record["render_checked"] is False  # the fake renderer runs no code, so G9 is not expected of it
    (job,) = backend.jobs
    assert job.themes == ("light",) and "pd.read_csv(" in job.source and '"data.csv"' in job.source
    assert 'float_precision="round_trip"' in job.source and "10_000" in job.source


async def test_render_expectations_hold_only_on_a_real_renderer(stress_cases: dict[str, EvalCase]) -> None:
    def script(probe: dict[str, Any]) -> Script:
        return lambda job, theme: FakeOutcome(probe=probe)

    case = stress_cases["stress-compute-oversample"]
    many = {"canvas": [3200, 1800], "texts": [], "points": 0, "line_points": 610_000}
    held = await static_record(case, context(FakeBackend(script=script(many)), renderer="remote"))
    broken = await static_record(case, context(FakeBackend(script=script({**many, "line_points": 61})), "remote"))

    assert held["render_checked"] and held["held"] and held["static"]["standin"]["gates"] == ["G9"]
    assert broken["held"] is False and broken["mismatches"] == ["gates: expected to contain ['G9'], measured []"]


async def test_render_expectations_without_a_stand_in_result_never_hold(
    tmp_path: Path, stress_cases: dict[str, EvalCase]
) -> None:
    case = stress_cases["stress-compute-oversample"]
    copy = tmp_path / case.case_id
    copy.mkdir()
    (copy / "case.json").write_text((case.directory / "case.json").read_text(encoding="utf-8"), encoding="utf-8")

    with pytest.raises(CaseError, match="standin.txt"):
        stress_spec(EvalCase(**{**case.__dict__, "directory": copy}))

    (copy / "standin.txt").write_text((case.directory / "standin.txt").read_text(encoding="utf-8"), encoding="utf-8")
    refused = EvalCase(**{**case.__dict__, "directory": copy, "data_text": "x" * (MAX_INPUT_BYTES + 1)})
    record = await static_record(refused, context(renderer="remote"))

    assert record["render_checked"] and record["held"] is False
    assert record["mismatches"][-1] == "render: no stand-in result to check (the case ended at dataset)"


async def test_a_broken_case_file_is_an_error_record(tmp_path: Path, stress_cases: dict[str, EvalCase]) -> None:
    case = stress_cases["stress-single-row"]
    copy = tmp_path / case.case_id
    copy.mkdir()
    (copy / "case.json").write_text(json.dumps({"spec_id": "scatter-basic", "needs_model": "yes"}))
    broken = EvalCase(**{**case.__dict__, "directory": copy})

    record = await static_record(broken, context())

    assert record["status"] == "error" and "needs_model" in record["error"]
    assert stress_spec(case).bound_expected  # the committed one reads


# --- The run and the harness flag -------------------------------------------------------------


async def test_the_whole_stress_set_holds_offline(tmp_path: Path, stress_cases: dict[str, EvalCase]) -> None:
    result = await run_static(list(stress_cases.values()), context(), tmp_path, selector="stress", git_sha="abc")

    summary = result.report["summary"]
    assert result.exit_code == 0 and summary["broken"] == [] and summary["errors"] == []
    assert summary["cases"] == summary["judged"] == summary["held"] == 23
    assert summary["model_pending"] == [
        "stress-compute-distances",
        "stress-compute-lorenz",
        "stress-compute-oversample",
        "stress-constant-series",
        "stress-inject-long-cell",
        "stress-pie-30-slices",
        "stress-single-row",
    ]
    assert json.loads(result.report_path.read_text())["kind"] == "static"
    table = result.summary_path.read_text()
    assert "| `stress-cap-profile` | ready | prompt | yes |" in table and "(of 27,176)" in table


def test_static_defaults_to_the_fake_renderer(tmp_path: Path) -> None:
    environ: dict[str, str] = {}
    configure(parse_args(["--static"]), environ)
    assert environ["AGENT_RENDERER"] == "fake"
    configure(parse_args(["--static", "--renderer", "remote"]), remote := {})
    assert remote["AGENT_RENDERER"] == "remote"

    with patch.dict(os.environ):
        os.environ.pop("AGENT_RENDERER", None)
        code = matrix.main(["--cases", "stress-over-*,stress-single-row", "--static", "--out", str(tmp_path)])

    assert code == EXIT_OK
    (report,) = tmp_path.glob("*-static.json")
    assert [run["case_id"] for run in json.loads(report.read_text())["runs"]] == [
        "stress-over-bytes",
        "stress-over-cell",
        "stress-over-columns",
        "stress-over-rows",
        "stress-single-row",
    ]


def test_a_renderer_outage_stops_the_static_run_as_an_outage(tmp_path: Path) -> None:
    """A stand-in render that finds the renderer gone ends the run with exit 4, never as a broken bound."""

    def outage(job: Any, theme: str) -> FakeOutcome:
        raise RendererUnavailable("connection refused")

    with patch.dict(os.environ), patch("agents.anyplot.render.make_backend", return_value=FakeBackend(script=outage)):
        os.environ.pop("AGENT_RENDERER", None)
        code = matrix.main(["--cases", "stress-compute-oversample", "--static", "--out", str(tmp_path)])

    assert code == EXIT_OUTAGE
    assert not list(tmp_path.glob("*-static.json"))  # no report that would read as failed bounds


# --- The dataset route on the cap cases ------------------------------------------------------


@pytest.fixture
def runtime() -> Iterator[Runtime]:
    fresh = Runtime(queue=RunQueue(concurrency=1, per_minute=1_000, max_wait_s=600))
    app.dependency_overrides[get_runtime] = lambda: fresh
    yield fresh
    app.dependency_overrides.clear()


@pytest.fixture
async def client(runtime: Runtime, services: Services) -> AsyncIterator[httpx.AsyncClient]:
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://agents") as http:
        yield http


async def test_the_dataset_route_answers_the_cap_cases_as_the_static_stage_says(
    client: httpx.AsyncClient, stress_cases: dict[str, EvalCase], judge
) -> None:
    body = {
        "user": USER,
        "spec_id": "line-basic",
        "library": "matplotlib",
        "locale": "en",
        "snapshot": snapshot_from_repo("line-basic", "matplotlib").model_dump(),
    }
    opened = await client.post("/v1/sessions", headers=HEADERS, json=body)
    assert opened.status_code == 200, opened.text
    sid = opened.json()["session_id"]

    answers = {}
    for case_id in ("stress-over-bytes", "stress-over-rows", "stress-cap-rows"):
        response = await client.post(
            f"/v1/sessions/{sid}/dataset", headers=HEADERS, json={"text": stress_cases[case_id].data_text}
        )
        answers[case_id] = (response.status_code, response.json().get("detail"))

    assert answers == {
        "stress-over-bytes": (413, "too_long"),
        "stress-over-rows": (422, "unparseable"),
        "stress-cap-rows": (200, None),
    }
    assert len(judge.calls) == 1  # only the accepted dataset reached the judge
