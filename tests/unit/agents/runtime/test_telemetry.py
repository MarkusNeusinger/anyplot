"""The usage telemetry (`agents/anyplot/telemetry.py`): content-free lines, closed sets, dedupe keys, the beacon."""

import ast
import json
import logging
import re
from collections.abc import AsyncIterator, Iterator
from pathlib import Path
from typing import Any, cast, get_args

import httpx
import pytest
from pydantic import ValidationError

from agents.anyplot import telemetry
from agents.anyplot.dev_fixture import snapshot_from_repo
from agents.anyplot.plugins.ledger import OUTCOMES_PER_MINUTE, RequestLedger
from agents.anyplot.render.contract import ThemeOutput
from agents.anyplot.run_queue import RunQueue
from agents.anyplot.services import Services
from agents.main import Runtime, app, get_runtime
from core.database.models import FEEDBACK_REACTIONS

from .fakes import default_script


USER = "adm_telemetry0000001"
HEADERS = {"X-Anyplot-User": USER, "X-Request-Id": "req-telemetry"}
COLUMN_CANARY = "CanaryColQ7"
CELL_CANARY = "CANARY-CELL-e41a"
NOTE_CANARY = "CANARY-NOTE-90bd"
FILE_CANARY = "CANARY-FILE-77c3"
MESSAGE_CANARY = "CANARY-MSG-1f0e"
CANARY_DATA = f"Source: survey {NOTE_CANARY}\n\n{COLUMN_CANARY},Exam Score,Student\n" + "".join(
    f"{hours},{50 + 2 * hours},{CELL_CANARY if hours == 3 else f'S{hours:02d}'}\n" for hours in range(1, 13)
)


@pytest.fixture
def runtime() -> Iterator[Runtime]:
    fresh = Runtime(queue=RunQueue(concurrency=1, per_minute=1_000, max_wait_s=600))
    app.dependency_overrides[get_runtime] = lambda: fresh
    yield fresh
    app.dependency_overrides.clear()


@pytest.fixture
async def client(runtime: Runtime, services: Services) -> AsyncIterator[httpx.AsyncClient]:
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://agents") as http:
        yield http


def telemetry_lines(caplog: pytest.LogCaptureFixture) -> list[dict[str, Any]]:
    return [json.loads(r.getMessage()) for r in caplog.records if r.name == telemetry.TELEMETRY_LOGGER]


def session_body(**extra: Any) -> dict[str, Any]:
    return {
        "user": USER,
        "spec_id": "scatter-basic",
        "library": "matplotlib",
        "locale": "en",
        "snapshot": snapshot_from_repo("scatter-basic", "matplotlib").model_dump(),
        **extra,
    }


async def open_session(client: httpx.AsyncClient, **extra: Any) -> str:
    response = await client.post("/v1/sessions", headers=HEADERS, json=session_body(**extra))
    assert response.status_code == 200, response.text
    return str(response.json()["session_id"])


async def plot_session(client: httpx.AsyncClient, **extra: Any) -> str:
    """A session with the canary table pasted, the default bindings confirmed and one plot asked for."""
    sid = await open_session(client, **extra)
    pasted = await client.post(f"/v1/sessions/{sid}/dataset", headers=HEADERS, json={"text": CANARY_DATA})
    assert pasted.status_code == 200, pasted.text
    assert (await client.post(f"/v1/sessions/{sid}/dataset/confirm", headers=HEADERS)).status_code == 200
    turn = await client.post(f"/v1/sessions/{sid}/messages", headers=HEADERS, json={"action": "create_plot"})
    assert turn.status_code == 200, turn.text
    return sid


def lines_of(caplog: pytest.LogCaptureFixture, event: str) -> list[dict[str, Any]]:
    return [line for line in telemetry_lines(caplog) if line["event"] == event]


async def test_a_whole_session_writes_the_four_events_and_none_of_its_content(
    client: httpx.AsyncClient, swap_models, caplog: pytest.LogCaptureFixture
) -> None:
    """The canary: distinctive column names, cells, notes, file name and message never reach a telemetry line."""
    caplog.set_level(logging.INFO)
    swap_models("gemini", default_script())
    sid = await open_session(client)
    pasted = await client.post(
        f"/v1/sessions/{sid}/dataset", headers=HEADERS, json={"text": CANARY_DATA, "source": f"{FILE_CANARY}.csv"}
    )
    assert pasted.status_code == 200, pasted.text
    defaults = pasted.json()["bindings"]
    # The page echoes the defaults after every paste: no manual change.
    assert (await client.put(f"/v1/sessions/{sid}/bindings", headers=HEADERS, json=defaults)).status_code == 200
    assert telemetry.marks(sid).manual_binding_changed is False
    # The user's own choice: x and y swapped.
    bindings = [{"role": "x", "column": "Exam Score"}, {"role": "y", "column": COLUMN_CANARY}]
    assert (await client.put(f"/v1/sessions/{sid}/bindings", headers=HEADERS, json=bindings)).status_code == 200
    assert telemetry.marks(sid).manual_binding_changed is True
    assert (await client.post(f"/v1/sessions/{sid}/dataset/confirm", headers=HEADERS)).status_code == 200
    turn = await client.post(
        f"/v1/sessions/{sid}/messages", headers=HEADERS, json={"text": f"Please plot it {MESSAGE_CANARY}"}
    )
    assert "event: plot" in turn.text
    beacon = await client.post(
        f"/v1/sessions/{sid}/outcome", headers=HEADERS, json={"action": "copied_code", "version": 1}
    )
    assert beacon.status_code == 204
    again = await client.post(  # a second click on the same button is a second row, not a duplicate
        f"/v1/sessions/{sid}/outcome",
        headers={**HEADERS, "X-Request-Id": "req-telemetry-2"},
        json={"action": "copied_code", "version": 1},
    )
    assert again.status_code == 204

    lines = telemetry_lines(caplog)
    assert [line["event"] for line in lines] == ["data_input", "pipeline_run", "chat_turn", "outcome", "outcome"]
    raw = json.dumps(lines)
    for canary in (COLUMN_CANARY, CELL_CANARY, NOTE_CANARY, FILE_CANARY, MESSAGE_CANARY, USER, sid, "Exam Score"):
        assert canary not in raw, canary
    for line in lines:
        assert line["log_type"] == "agent_telemetry" and line["schema"] == 1 and line["source"] == "live"
        assert "user" not in line and "request_id" not in line
        assert line["spec_id"] == "scatter-basic" and line["library"] == "matplotlib"
        assert len(line["session"]) == 16 and line["session"] == lines[0]["session"]

    data_input, run, chat_turn, outcome, _ = lines
    assert data_input["outcome"] == "ok" and data_input["format"] == "csv" and data_input["entry"] == "file"
    assert data_input["file_name"] is True and data_input["notes"] is True and data_input["text_cols"] == 1
    assert data_input["rows_bucket"] == "11_100" and data_input["cols_bucket"] == "3_5"
    assert data_input["spec_fit"] == "direct" and data_input["turn"] == 0
    assert run["run_index"] == 1 and run["status"] == "ok" and run["turn"] == 1
    assert [step["step"] for step in run["steps"]] == ["adapter", "reviewer"]
    # The fields of 2026-10-30, in the conftest's checklist flow (no self-review, no ship-best, no score).
    assert (run["stages"], run["round_scores"], run["plot_language"], run["readiness"]) == (
        ["reviewer_ok"],
        ["unscored"],
        "en",
        "coupled",  # the catalogue file draws its own sample data, which the adapter replaces
    )
    assert (run["loader_notes"], run["edit_failures"], run["validator_rules"], run["adaptation_rules"]) == (
        [],
        [],
        [],
        [],
    )
    assert (run["reviewer_mode"], run["ship_best"], run["self_review"], run["repair_self_review"]) == (
        "checklist",
        False,
        False,
        False,
    )
    assert re.fullmatch(r"[0-9a-f]{16}", run["adapter_prompt"]) and re.fullmatch(
        r"[0-9a-f]{16}", run["reviewer_prompt"]
    )
    assert all(isinstance(step["thoughts"], int) for step in run["steps"])
    assert chat_turn["kind"] == "plot" and chat_turn["action"] == "text" and chat_turn["turn"] == 1
    assert chat_turn["tools"] == ["plot_pipeline"] and chat_turn["manual_binding_changed"] is True
    assert {step["step"] for step in chat_turn["steps"]} >= {"root", "adapter", "reviewer"}
    # The turn's first typed message had its language detected (the fake judge's `en`): read after the run, the
    # line says so; read before it, it said `default`.
    assert chat_turn["plot_language"] == "en" and chat_turn["language_source"] == "detected"
    assert outcome["action"] == "copied_code" and outcome["version"] == 1 and outcome["turn"] == 1
    assert len({line["idempotency_key"] for line in lines}) == 5


async def test_the_attribution_lines_still_carry_the_user_and_the_telemetry_lines_never(
    client: httpx.AsyncClient, swap_models, caplog: pytest.LogCaptureFixture
) -> None:
    """The sink takes `log_type="agent_telemetry"` only: the user id stays in the debug lines."""
    caplog.set_level(logging.INFO)
    swap_models("gemini", default_script())
    sid = await open_session(client)
    await client.post(f"/v1/sessions/{sid}/dataset", headers=HEADERS, json={"text": CANARY_DATA})
    attribution = [json.loads(r.getMessage()) for r in caplog.records if r.name == "anyplot.agents.attribution"]
    assert attribution and all("log_type" not in line for line in attribution)
    assert any(line.get("user") == USER for line in attribution)
    assert all("user" not in line for line in telemetry_lines(caplog))


async def test_refused_pastes_write_their_outcome_and_cause(
    client: httpx.AsyncClient, caplog: pytest.LogCaptureFixture
) -> None:
    caplog.set_level(logging.INFO)
    sid = await open_session(client)
    ragged = f"a,b\n1,2\n3,4,{CELL_CANARY}\n"
    assert (await client.post(f"/v1/sessions/{sid}/dataset", headers=HEADERS, json={"text": ragged})).status_code == 422
    code = "import numpy as np\nx = np.linspace(0, 10, 100)\ny = np.sin(x)\n"
    assert (await client.post(f"/v1/sessions/{sid}/dataset", headers=HEADERS, json={"text": code})).status_code == 422

    first, second = telemetry_lines(caplog)
    assert (first["outcome"], first["cause"], first["format"]) == ("unparseable", "unparseable", "other")
    assert (second["outcome"], second["format"]) == ("code", "code")
    assert first["idempotency_key"] != second["idempotency_key"]
    assert CELL_CANARY not in json.dumps([first, second])


async def test_the_beacon_takes_closed_values_only(client: httpx.AsyncClient) -> None:
    sid = await open_session(client)
    url = f"/v1/sessions/{sid}/outcome"
    assert (await client.post(url, headers=HEADERS, json={"action": "feedback", "reaction": "bug"})).status_code == 204
    for body in (
        {"action": "copied_code", "reaction": "bug"},  # a reaction goes with feedback only
        {"action": "shared_on_twitter"},
        {"action": "feedback", "reaction": "love"},
        {"action": "copied_code", "version": "1"},
        {"action": "copied_code", "note": MESSAGE_CANARY},
        {"action": "copied_code", "version": 1000},
    ):
        assert (await client.post(url, headers=HEADERS, json=body)).status_code == 422, body
    gone = await client.post("/v1/sessions/nope/outcome", headers=HEADERS, json={"action": "copied_code"})
    assert gone.status_code == 404
    unknown = await client.post(url, headers=HEADERS, json={"action": "copied_code", "version": 7})
    assert (unknown.status_code, unknown.json()["detail"]) == (404, "not_found")


async def test_two_actions_never_share_a_key(client: httpx.AsyncClient, caplog: pytest.LogCaptureFixture) -> None:
    """The key holds the action and the version besides the request id: even under one request id (a proxy that
    reuses it) two different actions on one version stay two rows."""
    caplog.set_level(logging.INFO)
    sid = await open_session(client)
    for action in ("saved_session", "feedback"):
        response = await client.post(f"/v1/sessions/{sid}/outcome", headers=HEADERS, json={"action": action})
        assert response.status_code == 204
    keys = [line["idempotency_key"] for line in telemetry_lines(caplog) if line["event"] == "outcome"]
    assert len(keys) == 2 and keys[0] != keys[1]


async def test_the_beacon_is_rate_limited_per_user(client: httpx.AsyncClient) -> None:
    sid = await open_session(client)
    url = f"/v1/sessions/{sid}/outcome"
    codes = [(await client.post(url, headers=HEADERS, json={"action": "downloaded_png"})).status_code]
    for _ in range(OUTCOMES_PER_MINUTE):
        codes.append((await client.post(url, headers=HEADERS, json={"action": "downloaded_png"})).status_code)
    assert codes[:OUTCOMES_PER_MINUTE] == [204] * OUTCOMES_PER_MINUTE
    assert codes[-1] == 429


# --- Closed sets ----------------------------------------------------------------------------

BASELINES: dict[type[telemetry._Event], dict[str, Any]] = {
    telemetry.DataInput: {"format": "csv", "entry": "paste", "outcome": "ok", "size_bucket": "lt1k"},
    telemetry.ChatTurn: {"kind": "talk", "action": "text"},
    telemetry.PipelineRun: {"run_index": 1, "base": "catalogue", "status": "ok"},
    telemetry.Outcome: {"action": "copied_code"},
    telemetry.StepTokens: {"step": "root"},
}


@pytest.mark.parametrize("model", list(BASELINES))
def test_no_field_takes_free_text(model: type[telemetry._Event]) -> None:
    """Enum closure: every field of every event refuses a free text, as a value and inside a list."""
    model(**BASELINES[model])
    for name in model.model_fields:
        if name == "event":
            continue
        for value in (f"free text {MESSAGE_CANARY}", [f"free text {MESSAGE_CANARY}"], {"text": MESSAGE_CANARY}):
            with pytest.raises(ValidationError):
                model(**{**BASELINES[model], name: value})


def test_an_unknown_field_is_refused() -> None:
    with pytest.raises(ValidationError):
        telemetry.ChatTurn.model_validate({"kind": "talk", "action": "text", "message": MESSAGE_CANARY})


def test_an_invalid_event_writes_no_line(caplog: pytest.LogCaptureFixture) -> None:
    caplog.set_level(logging.INFO)
    ledger = RequestLedger(session_id="s1", spec_id="scatter-basic", library="matplotlib", turn=1)
    assert telemetry.write(telemetry.ChatTurn, ledger, kind=MESSAGE_CANARY, action="text") is None
    assert telemetry_lines(caplog) == []
    assert MESSAGE_CANARY not in caplog.text


def test_an_envelope_value_outside_its_set_writes_no_line(caplog: pytest.LogCaptureFixture) -> None:
    caplog.set_level(logging.INFO)
    ledger = RequestLedger(session_id="s1", spec_id=f"Not A Spec {MESSAGE_CANARY}", library="matplotlib")
    assert telemetry.write(telemetry.Outcome, ledger, action="copied_code") is None
    assert MESSAGE_CANARY not in caplog.text


def test_the_reactions_are_the_feedback_reactions() -> None:
    assert get_args(telemetry.Reaction) == FEEDBACK_REACTIONS


def test_the_run_reasons_are_the_pipeline_reasons() -> None:
    from agents.anyplot.schemas import FailureReason, NotReadyReason

    assert get_args(telemetry.FailureReason) == get_args(FailureReason)
    assert get_args(telemetry.NotReadyReason) == get_args(NotReadyReason)


async def test_a_plot_before_the_data_is_ready_is_a_not_ready_run(
    client: httpx.AsyncClient, swap_models, caplog: pytest.LogCaptureFixture
) -> None:
    caplog.set_level(logging.INFO)
    swap_models("gemini", default_script())
    sid = await open_session(client)
    await client.post(f"/v1/sessions/{sid}/dataset", headers=HEADERS, json={"text": CANARY_DATA})
    # No `.confirm()`: the pipeline answers not_ready, and the telemetry still counts the attempt.
    await client.post(f"/v1/sessions/{sid}/messages", headers=HEADERS, json={"action": "create_plot"})
    runs = [line for line in telemetry_lines(caplog) if line["event"] == "pipeline_run"]
    assert [(run["status"], run["reason"], run["run_index"]) for run in runs] == [("not_ready", "data_unconfirmed", 1)]


def test_the_prep_ops_are_the_operations() -> None:
    from agents.anyplot.data.prepare import Operation

    union = get_args(get_args(Operation)[0])
    assert {get_args(member.model_fields["op"].annotation)[0] for member in union} == telemetry.PREP_OPS


def test_the_tool_names_are_the_root_tools() -> None:
    from agents.anyplot.agent import ROOT_TOOLS

    names = {getattr(tool, "name", None) or getattr(tool, "__name__", "") for tool in ROOT_TOOLS}
    assert names == telemetry.TOOL_NAMES


# --- Keys, buckets, helpers -----------------------------------------------------------------


def test_the_session_hash_is_salted() -> None:
    import hashlib

    key = telemetry.session_key("abc")
    assert key == telemetry.session_key("abc") and len(key) == 16
    assert key not in (hashlib.sha256(b"abc").hexdigest()[:16], hashlib.sha256(b"abc").hexdigest()[:12])


def test_the_attribution_hash_is_salted_and_not_the_telemetry_hash() -> None:
    import hashlib

    from agents.anyplot.plugins.ledger import session_hash

    plain = hashlib.sha256(b"abc").hexdigest()
    assert len(session_hash("abc")) == 12 and session_hash("abc") == session_hash("abc")
    assert session_hash("abc") not in (plain[:12], telemetry.session_key("abc")[:12])
    assert session_hash("") == ""


def test_idempotency_keys_repeat_for_the_same_line_only() -> None:
    first = telemetry.idempotency_key("s", 1, "run1", "pipeline_run")
    assert first == telemetry.idempotency_key("s", 1, "run1", "pipeline_run")
    assert first != telemetry.idempotency_key("s", 1, "run2", "pipeline_run")
    assert first != telemetry.idempotency_key("s", 2, "run1", "pipeline_run")


def test_a_rerun_node_keeps_its_run_index() -> None:
    telemetry.forget("sess-x")
    assert telemetry.run_index("sess-x", "inv-1") == 1
    assert telemetry.run_index("sess-x", "inv-1") == 1  # ADK re-ran the node: the same line, the same key
    assert telemetry.run_index("sess-x", "inv-2") == 2
    telemetry.forget("sess-x")


def test_a_converted_file_kind_survives_a_refused_paste() -> None:
    telemetry.forget("sess-z")
    telemetry.converted("sess-z", kind="xlsx", sheets=3)
    first = telemetry.InputFacts.for_paste("sess-z", size=10, source=True, confirmed=False)
    retry = telemetry.InputFacts.for_paste("sess-z", size=10, source=True, confirmed=False)  # after a 429
    assert (first.format, first.sheets) == (retry.format, retry.sheets) == ("xlsx", 3)
    telemetry.clear_converted("sess-z")  # the paste passed its limits
    assert telemetry.InputFacts.for_paste("sess-z", size=10, source=True, confirmed=False).format is None
    telemetry.forget("sess-z")


def test_the_turn_marks_are_taken_once() -> None:
    telemetry.forget("sess-y")
    telemetry.marks("sess-y").undo = True
    telemetry.note_binding_warnings("sess-y", ["CANARY: not a known sentence"])
    assert telemetry.take_turn_marks("sess-y") == {
        "undo": True,
        "to_long": False,
        "manual_binding_changed": False,
        "binding_warnings": ["other"],
    }
    assert telemetry.take_turn_marks("sess-y")["undo"] is False
    telemetry.forget("sess-y")


@pytest.mark.parametrize(
    ("reply", "asked"),
    [("Shall I make it dark?", True), ("Fertig. Soll ich die Achsen tauschen?**", True), ("Done.", False), ("", False)],
)
def test_a_question_is_a_bool(reply: str, asked: bool) -> None:
    assert telemetry.ends_with_question(reply) is asked


def test_buckets() -> None:
    assert [telemetry.size_bucket(n) for n in (10, 5_000, 50_000, 500_000, 2_000_000)] == [
        "lt1k",
        "1k_10k",
        "10k_100k",
        "100k_1m",
        "ge1m",
    ]
    assert [telemetry.missing_bucket(m, 100) for m in (0, 4, 30, 31)] == ["none", "lt5", "5_30", "gt30"]
    assert [telemetry.categories_bucket(n) for n in (5, 6, 50, 51)] == ["le5", "6_12", "13_50", "gt50"]
    assert [telemetry.score_bucket(s) for s in (None, 49, 69, 75, 89, 90)] == [
        None,
        "lt50",
        "50_69",
        "70_79",
        "80_89",
        "90_plus",
    ]


@pytest.mark.parametrize(
    ("stderr", "kwargs", "expected"),
    [
        ('  File "plot.py", line 3\nSyntaxError: invalid syntax', {}, "syntax"),
        (f"Traceback\nKeyError: '{CELL_CANARY}'", {}, "key"),
        ("Traceback\nNameError: name 'x' is not defined", {}, "name"),
        ("", {"timed_out": True}, "timeout"),
        ("", {"reason": "memory"}, "memory"),
        ("Traceback\nZeroDivisionError: division by zero", {}, "other"),
    ],
)
def test_sandbox_failures_are_classes(stderr: str, kwargs: dict[str, Any], expected: str) -> None:
    output = ThemeOutput(theme="light", exit_code=1, stderr_tail=stderr, **kwargs)
    assert telemetry.sandbox_failure(output) == expected


def test_a_clean_render_is_no_failure() -> None:
    assert telemetry.sandbox_failure(ThemeOutput(theme="light", exit_code=0, png=b"png")) is None


def test_input_formats() -> None:
    assert telemetry.input_format("json_records") == "json"
    assert telemetry.input_format("json_records", warnings=["fields_beside_records_to_notes"]) == "api_json"
    assert telemetry.input_format("semicolon") == "semicolon"
    assert telemetry.input_format("csv", convert_kind="xlsx") == "xlsx"
    assert telemetry.input_format(None) == "other"


def test_spec_fit() -> None:
    assert telemetry.spec_fit(complete=True, bound=2, reshape=False) == "direct"
    assert telemetry.spec_fit(complete=True, bound=2, reshape=True) == "needs_reshape"
    assert telemetry.spec_fit(complete=False, bound=1, reshape=False) == "missing_role"
    assert telemetry.spec_fit(complete=False, bound=0, reshape=False) == "incompatible"


def test_the_harness_tags_its_lines(caplog: pytest.LogCaptureFixture) -> None:
    caplog.set_level(logging.INFO)
    ledger = RequestLedger(session_id="s1", spec_id="scatter-basic", library="matplotlib")
    with telemetry.harness():
        record = telemetry.write(telemetry.Outcome, ledger, action="saved_session")
    after = telemetry.write(telemetry.Outcome, ledger, action="saved_session")
    assert record is not None and record["source"] == "harness"
    assert after is not None and after["source"] == "live"


async def test_a_live_request_beside_a_harness_run_stays_live() -> None:
    """The source is a context variable: a harness run in another task of the same loop tags only its own lines."""
    import asyncio

    ledger = RequestLedger(session_id="s1", spec_id="scatter-basic", library="matplotlib")
    inside, release = asyncio.Event(), asyncio.Event()
    records: list[dict[str, Any] | None] = []

    async def harness_run() -> None:
        with telemetry.harness():
            records.append(telemetry.write(telemetry.Outcome, ledger, action="copied_code"))
            inside.set()
            await release.wait()

    task = asyncio.create_task(harness_run())
    await inside.wait()
    live = telemetry.write(telemetry.Outcome, ledger, action="copied_image")
    release.set()
    await task
    assert records[0] is not None and records[0]["source"] == "harness"
    assert live is not None and live["source"] == "live"


def test_the_harness_source_is_restored_after_a_failure() -> None:
    ledger = RequestLedger(session_id="s1", spec_id="scatter-basic", library="matplotlib")
    with pytest.raises(RuntimeError), telemetry.harness():
        raise RuntimeError("the eval run failed")
    record = telemetry.write(telemetry.Outcome, ledger, action="saved_session")
    assert record is not None and record["source"] == "live"


# --- The fields of 2026-10-30 ---------------------------------------------------------------


async def test_every_line_of_a_fanout_session_is_filed_as_fanout(
    client: httpx.AsyncClient, swap_models, caplog: pytest.LogCaptureFixture
) -> None:
    """The admin's fan-out marks the session at its opening; every event of it carries the source, so each
    `source = 'live'` filter (the views, the /debug card) leaves the test sessions out."""
    caplog.set_level(logging.INFO)
    swap_models("gemini", default_script())
    sid = await plot_session(client, source="fanout")
    assert (
        await client.post(f"/v1/sessions/{sid}/outcome", headers=HEADERS, json={"action": "copied_code"})
    ).is_success
    live = await open_session(client)
    assert (
        await client.post(f"/v1/sessions/{live}/outcome", headers=HEADERS, json={"action": "copied_code"})
    ).is_success

    lines = telemetry_lines(caplog)
    fanout, (plain,) = lines[:-1], lines[-1:]
    assert [line["event"] for line in fanout] == ["data_input", "pipeline_run", "chat_turn", "outcome"]
    assert {line["source"] for line in fanout} == {"fanout"} and plain["source"] == "live"
    # The harness keeps its own source, also for a fan-out session.
    ledger = RequestLedger(session_id="s1", spec_id="scatter-basic", library="matplotlib", fanout=True)
    with telemetry.harness():
        record = telemetry.write(telemetry.Outcome, ledger, action="saved_session")
    assert record is not None and record["source"] == "harness"


@pytest.mark.parametrize("source", ["live", "harness", "Fanout", MESSAGE_CANARY, ""])
async def test_the_session_source_is_a_closed_set(client: httpx.AsyncClient, source: str) -> None:
    response = await client.post("/v1/sessions", headers=HEADERS, json=session_body(source=source))
    assert response.status_code == 422


async def test_the_turn_records_the_language_it_detected(
    client: httpx.AsyncClient, swap_models, judge, caplog: pytest.LogCaptureFixture
) -> None:
    """Review of 2026-10-30: the line read the language before the run, so the turn that detected German said
    `en`/`default`. Read after the run, it names what the turn set; a later choice outside the table is `other`."""
    from agents.anyplot.models import JudgeVerdict

    caplog.set_level(logging.INFO)
    swap_models("gemini", {"root": [{"text": "Gern."}, {"text": "Okay."}, {"text": "Okay."}]})
    judge.script = [JudgeVerdict(verdict="in_scope", lang="de"), JudgeVerdict(verdict="in_scope", lang="en")]
    sid = await open_session(client)
    assert (await client.post(f"/v1/sessions/{sid}/messages", headers=HEADERS, json={"text": "Mach es"})).is_success
    chosen = await client.put(f"/v1/sessions/{sid}/language", headers=HEADERS, json={"language": "Swedish"})
    assert chosen.status_code == 200
    assert (await client.post(f"/v1/sessions/{sid}/messages", headers=HEADERS, json={"text": "go on"})).is_success

    first, second = lines_of(caplog, "chat_turn")
    assert (first["plot_language"], first["language_source"]) == ("de", "detected")
    assert (second["plot_language"], second["language_source"]) == ("other", "chosen")
    assert "Swedish" not in json.dumps(telemetry_lines(caplog))


@pytest.mark.parametrize(
    ("language", "code"),
    [("en", "en"), ("Deutsch", "de"), ("German", "de"), ("JA", "ja"), ("Polski", "pl"), ("sv", "other"), (None, None)],
)
def test_the_plot_language_is_a_closed_code(language: str | None, code: str | None) -> None:
    assert telemetry.plot_language(language) == code
    assert telemetry.plot_language(f"Klingon {MESSAGE_CANARY}"[:40]) == "other"


def test_the_plot_languages_are_the_named_languages() -> None:
    from agents.anyplot.language import COMMON_LANGUAGES, ENGLISH_NAMES

    assert set(get_args(telemetry.PlotLanguage)) == {*ENGLISH_NAMES, "other"}
    assert set(COMMON_LANGUAGES) <= set(get_args(telemetry.PlotLanguage))


async def test_a_run_records_its_attempts_and_their_causes_without_their_text(
    client: httpx.AsyncClient, swap_models, caplog: pytest.LogCaptureFixture, monkeypatch: pytest.MonkeyPatch
) -> None:
    """An edit that matches nothing, then a banned import, then the plan that works: the stages in order, the
    failure kind and the rule id, and none of the plan's text."""
    from agents.anyplot.settings import get_settings

    from .fakes import SCATTER_PLAN

    monkeypatch.setenv("AGENT_MAX_ATTEMPTS", "3")
    get_settings.cache_clear()
    caplog.set_level(logging.INFO)
    missing = {**SCATTER_PLAN, "edits": [{"find": f"{MESSAGE_CANARY} not in the code", "replace": "x"}]}
    first, *rest = SCATTER_PLAN["edits"]
    importing = {**first, "replace": f"import subprocess  # {CELL_CANARY}\n{first['replace']}"}
    banned = {**SCATTER_PLAN, "edits": [importing, *rest]}
    swap_models("gemini", default_script(plans=[missing, banned, SCATTER_PLAN]))
    await plot_session(client)

    (run,) = lines_of(caplog, "pipeline_run")
    assert run["status"] == "ok"
    assert run["stages"] == ["edit_apply", "validator", "reviewer_ok"]
    assert (run["edit_failures"], run["validator_rules"]) == (["zero_match"], ["banned-import"])
    assert run["round_scores"] == ["unscored", "unscored", "unscored"]
    raw = json.dumps(telemetry_lines(caplog))
    for canary in (MESSAGE_CANARY, CELL_CANARY, "subprocess", COLUMN_CANARY):
        assert canary not in raw, canary


def test_round_scores_keep_the_round_number_by_position() -> None:
    from agents.anyplot.pipeline import Run, _round_scores
    from agents.anyplot.schemas import Round

    run = Run(view=cast(Any, None), dataset=cast(Any, None))
    run.rounds = [Round(attempt=1, outcome="render_failed"), Round(attempt=2, outcome="ok")]
    run.round_scores = {2: 86}
    assert _round_scores(run) == ["unscored", "80_89"]
    run.round_scores = {1: 72, 2: 93}
    assert _round_scores(run) == ["70_79", "90_plus"]


def test_unknown_ids_are_other_and_never_drop_a_line() -> None:
    rules = telemetry.closed_set(
        ["banned-import", f"new-rule-{MESSAGE_CANARY}", "banned-import"], get_args(telemetry.ValidatorRule)
    )
    assert rules == ["banned-import", "other"]
    assert telemetry.build(telemetry.PipelineRun, run_index=1, base="catalogue", status="ok", validator_rules=rules)
    assert telemetry.readiness("blocked") is None and telemetry.readiness("coupled") == "coupled"


def test_the_edit_failures_are_the_edit_failure_kinds() -> None:
    from agents.anyplot.code.edits import FAILURE_KINDS

    assert set(get_args(telemetry.EditFailure)) == {*FAILURE_KINDS, "other"}


VALIDATORS = [
    Path(__file__).resolve().parents[4] / "agents" / "anyplot" / "code" / "validate.py",
    *sorted((Path(__file__).resolve().parents[4] / "agents" / "anyplot" / "code" / "profiles").glob("*/validate.py")),
]


def validator_rule_ids() -> set[str]:
    """Every rule id a validator writes: the first argument of each `add(...)` and `Finding(...)` that is a string, and
    the values of the `protected` tables whose rule goes to `add` by name."""
    ids: set[str] = set()
    for path in VALIDATORS:
        for node in ast.walk(ast.parse(path.read_text())):
            if not isinstance(node, ast.Call) or not node.args:
                continue
            name = node.func.attr if isinstance(node.func, ast.Attribute) else getattr(node.func, "id", None)
            first = node.args[0]
            if name in ("add", "Finding") and isinstance(first, ast.Constant) and isinstance(first.value, str):
                ids.add(first.value)
            elif isinstance(node.func, ast.Attribute) and node.func.attr == "append" and isinstance(first, ast.Tuple):
                head = first.elts[0] if first.elts else None
                if isinstance(head, ast.Constant) and isinstance(head.value, str) and "-" in head.value:
                    ids.add(head.value)
    return ids - {""}


def test_the_validator_rules_are_the_validators_rule_ids() -> None:
    """A rule a validator adds without the telemetry knowing it reads `other`: this names it."""
    found = validator_rule_ids() | {"literal-budget"}
    assert len(VALIDATORS) >= 4 and {"banned-import", "dataset-package", "markup-code"} <= found
    assert set(get_args(telemetry.ValidatorRule)) == {*found, "other"}


def test_the_reviewer_modes_and_readiness_are_the_settings() -> None:
    from agents.anyplot.code.readiness import ReadinessStatus
    from agents.anyplot.settings import ReviewerMode
    from agents.anyplot.sub_agents.reviewer import REVIEWER_MODES

    assert set(get_args(telemetry.ReviewerMode)) == set(get_args(ReviewerMode)) == set(REVIEWER_MODES)
    assert set(get_args(telemetry.Readiness)) == set(get_args(ReadinessStatus)) - {"blocked"}


def test_the_loader_codes_are_the_column_kinds() -> None:
    from dataclasses import fields

    from agents.anyplot.data.kinds import ColumnKinds
    from agents.anyplot.pipeline import LOADER_CODES

    assert LOADER_CODES == get_args(telemetry.LoaderNote)
    assert {item.name for item in fields(ColumnKinds)} - {"kinds"} == set(LOADER_CODES)


@pytest.mark.parametrize(
    ("library", "codes"),
    [("matplotlib", []), ("ggplot2", ["inexact", "offset"]), ("makie", ["submillisecond", "offset"])],
)
def test_the_loader_codes_ask_the_runtime_and_name_no_column(library: str, codes: list[str]) -> None:
    """Each runtime says which of the data's cells its loader changes; the line gets the codes, never the notes."""
    from agents.anyplot.data.kinds import ColumnKinds
    from agents.anyplot.pipeline import loader_codes
    from agents.anyplot.render.runtimes import runtime_for

    kinds = ColumnKinds(
        kinds={COLUMN_CANARY: "big-integer", "When": "datetime"},
        inexact={COLUMN_CANARY: 4},
        submillisecond={"When": 2},
        offset={"When": 7},
    )
    found = loader_codes(runtime_for(library), kinds)
    assert found == codes
    record = telemetry.build(telemetry.PipelineRun, run_index=1, base="catalogue", status="ok", loader_notes=found)
    assert record is not None and COLUMN_CANARY not in record.model_dump_json()
    assert loader_codes(runtime_for(library), ColumnKinds(kinds={"x": "integer"})) == []
    assert loader_codes(runtime_for(library), None) == []


def test_thoughts_are_a_part_of_the_output_and_unknown_for_the_judges() -> None:
    ledger = RequestLedger()
    ledger.book_step("adapter_matplotlib", model="gemini-3.8-flash", usage={"candidates": 40, "thoughts": 60}, cached=0)
    ledger.book_judge(100, 5)
    adapter, judge = telemetry.step_tokens(
        ledger.steps, steps=("adapter", "judge"), judge_model="gemini-3.5-flash-lite"
    )
    assert (adapter["output"], adapter["thoughts"]) == (100, 60)
    assert (judge["output"], judge["thoughts"]) == (5, None)
    assert telemetry.StepTokens(**adapter).thoughts == 60
