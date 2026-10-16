"""The usage telemetry (`agents/anyplot/telemetry.py`): content-free lines, closed sets, dedupe keys, the beacon."""

import json
import logging
from collections.abc import AsyncIterator, Iterator
from typing import Any, get_args

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


async def open_session(client: httpx.AsyncClient) -> str:
    response = await client.post(
        "/v1/sessions",
        headers=HEADERS,
        json={
            "user": USER,
            "spec_id": "scatter-basic",
            "library": "matplotlib",
            "locale": "en",
            "snapshot": snapshot_from_repo("scatter-basic", "matplotlib").model_dump(),
        },
    )
    assert response.status_code == 200, response.text
    return str(response.json()["session_id"])


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

    lines = telemetry_lines(caplog)
    assert [line["event"] for line in lines] == ["data_input", "pipeline_run", "chat_turn", "outcome"]
    raw = json.dumps(lines)
    for canary in (COLUMN_CANARY, CELL_CANARY, NOTE_CANARY, FILE_CANARY, MESSAGE_CANARY, USER, sid, "Exam Score"):
        assert canary not in raw, canary
    for line in lines:
        assert line["log_type"] == "agent_telemetry" and line["schema"] == 1 and line["source"] == "live"
        assert "user" not in line and "request_id" not in line
        assert line["spec_id"] == "scatter-basic" and line["library"] == "matplotlib"
        assert len(line["session"]) == 16 and line["session"] == lines[0]["session"]

    data_input, run, chat_turn, outcome = lines
    assert data_input["outcome"] == "ok" and data_input["format"] == "csv" and data_input["entry"] == "file"
    assert data_input["file_name"] is True and data_input["notes"] is True and data_input["text_cols"] == 1
    assert data_input["rows_bucket"] == "11_100" and data_input["cols_bucket"] == "3_5"
    assert data_input["spec_fit"] == "direct" and data_input["turn"] == 0
    assert run["run_index"] == 1 and run["status"] == "ok" and run["turn"] == 1
    assert [step["step"] for step in run["steps"]] == ["adapter", "reviewer"]
    assert chat_turn["kind"] == "plot" and chat_turn["action"] == "text" and chat_turn["turn"] == 1
    assert chat_turn["tools"] == ["plot_pipeline"] and chat_turn["manual_binding_changed"] is True
    assert {step["step"] for step in chat_turn["steps"]} >= {"root", "adapter", "reviewer"}
    assert outcome["action"] == "copied_code" and outcome["version"] == 1 and outcome["turn"] == 1
    assert len({line["idempotency_key"] for line in lines}) == 4


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
    try:
        telemetry.set_source("harness")
        record = telemetry.write(telemetry.Outcome, ledger, action="saved_session")
    finally:
        telemetry.set_source("live")
    assert record is not None and record["source"] == "harness"
