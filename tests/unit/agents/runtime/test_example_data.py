"""Example data on request (owner request of 2026-11-01): "Beispieldaten" in the data field goes to the chat.

The dataset route answers a request for data with `422 data_request`, found by the rules of
`data/classify.py` before any model or by the transcriber's `asks_for_data`; the page sends
the text to the chat, where the root writes the code that generates the table and
`run_data_code` runs it with `source_language` `example`, so the data panel says plainly that
the table is generated example data. No model writes a row.
"""

import json
import logging
from collections.abc import AsyncIterator, Iterator
from typing import Any, get_args

import httpx
import pytest

from agents.anyplot import telemetry
from agents.anyplot.data.transcribe import TranscribedTable
from agents.anyplot.dataset_context import code_source
from agents.anyplot.models import FakeJudge, Transcription
from agents.anyplot.plugins.ledger import RequestLedger, ledger_for
from agents.anyplot.plugins.tool_safety import DataCodeSource, ToolSafetyPlugin
from agents.anyplot.services import Services
from agents.anyplot.session_state import DATASET_ID
from agents.anyplot.settings import get_settings
from agents.anyplot.tools.session import EXAMPLE_DATA_CHANGE, SOURCE_LANGUAGES, run_data_code
from agents.main import Runtime, app, get_runtime

from .fakes import default_script
from .test_data_code_tool import SNIPPET, context_for
from .test_service_flow import HEADERS, USER, attribution_lines, open_session, parse_sse, permissive_queue


@pytest.fixture
def runtime() -> Iterator[Runtime]:
    fresh = Runtime(queue=permissive_queue())
    app.dependency_overrides[get_runtime] = lambda: fresh
    yield fresh
    app.dependency_overrides.clear()


@pytest.fixture
async def client(runtime: Runtime, services: Services) -> AsyncIterator[httpx.AsyncClient]:
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://agents") as http:
        yield http


def _telemetry(caplog: pytest.LogCaptureFixture, event: str) -> list[dict[str, Any]]:
    lines = [json.loads(r.getMessage()) for r in caplog.records if r.name == telemetry.TELEMETRY_LOGGER]
    return [line for line in lines if line["event"] == event]


def _reading(columns: list[str], rows: list[list[str]], *, asks_for_data: bool) -> Transcription:
    table = TranscribedTable(columns=columns, rows=rows, asks_for_data=asks_for_data)
    return Transcription(table=table, tokens=90, input_tokens=70, output_tokens=20)


class TestTheDataField:
    async def test_a_request_the_rules_read_goes_to_the_chat_before_any_model(
        self, client: httpx.AsyncClient, services: Services, judge: FakeJudge, caplog: pytest.LogCaptureFixture
    ) -> None:
        """The owner's two texts of 2026-11-01 ended in "no table found"; now neither costs a model call or a paste."""
        caplog.set_level(logging.INFO)
        sid = await open_session(client, with_data=False)

        for text in ("Beispieldaten", "generiere Zufallszahlen mit Kategorien", "example data, 3 groups, 20 rows"):
            refused = await client.post(f"/v1/sessions/{sid}/dataset", headers=HEADERS, json={"text": text})
            assert (refused.status_code, refused.json()) == (422, {"detail": "data_request"}), text

        assert judge.calls == [] and judge.transcribe_calls == [] and len(services.datasets) == 0
        assert services.usage.user_pastes(USER) == 0
        assert [line["outcome"] for line in attribution_lines(caplog, "data_transcribe")] == ["data_request"] * 3
        inputs = _telemetry(caplog, "data_input")
        assert [(line["format"], line["outcome"], line["cause"]) for line in inputs] == [
            ("data_request", "data_request", None)
        ] * 3

    async def test_the_transcriber_names_a_request_the_rules_miss(
        self, client: httpx.AsyncClient, services: Services, judge: FakeJudge, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Data described in words, in any language: the call that already reads free text says so."""
        caplog.set_level(logging.INFO)
        sid = await open_session(client, with_data=False)
        text = "monthly sales for 4 regions"
        # Whatever table comes with the answer is not the text's: it is dropped, never shown.
        judge.transcriptions = [_reading(["month", "sales"], [["Jan", "12"]], asks_for_data=True)]

        refused = await client.post(f"/v1/sessions/{sid}/dataset", headers=HEADERS, json={"text": text})

        assert (refused.status_code, refused.json()) == (422, {"detail": "data_request"})
        assert len(judge.transcribe_calls) == 1 and len(services.datasets) == 0
        assert services.usage.user_pastes(USER) == 1  # it reached a model
        (line,) = attribution_lines(caplog, "data_transcribe")
        assert line["outcome"] == "data_request" and line["judge_tokens"] == 90
        (data_input,) = _telemetry(caplog, "data_input")
        assert (data_input["format"], data_input["outcome"], data_input["cause"]) == (
            "data_request",
            "data_request",
            "transcribed_data_request",
        )

    async def test_text_with_its_own_values_is_never_sent_away(
        self, client: httpx.AsyncClient, judge: FakeJudge
    ) -> None:
        """A table in words stays the transcriber's, whatever its answer says about a request."""
        sid = await open_session(client, with_data=False)
        judge.transcriptions = [
            _reading(["region", "sales"], [["north", "12"], ["south", "14"], ["east", "9"]], asks_for_data=True),
            _reading(["text"], [["sales: north 12, south 14, east 9"]], asks_for_data=True),
        ]

        read = await client.post(
            f"/v1/sessions/{sid}/dataset", headers=HEADERS, json={"text": "sales: north 12, south 14, east 9"}
        )
        assert read.status_code == 200 and read.json()["transcribed"] is True

        no_table = await client.post(
            f"/v1/sessions/{sid}/dataset", headers=HEADERS, json={"text": "sales: north 12, south 14, east 9"}
        )
        assert no_table.status_code == 422 and no_table.json()["detail"] == "unparseable"

    async def test_a_request_the_chat_could_not_take_keeps_the_old_answer(
        self, client: httpx.AsyncClient, judge: FakeJudge
    ) -> None:
        sid = await open_session(client, with_data=False)
        text = "Umsätze pro Monat und Filiale, bitte. " * 60
        judge.transcriptions = [_reading(["text"], [[text[:200]]], asks_for_data=True)]

        refused = await client.post(f"/v1/sessions/{sid}/dataset", headers=HEADERS, json={"text": text})

        assert refused.status_code == 422 and refused.json()["detail"] == "unparseable"


class TestTheTool:
    async def test_example_data_is_named_as_such_in_the_change_line_and_the_source(
        self, client: httpx.AsyncClient, services: Services
    ) -> None:
        sid = await open_session(client, with_data=False)
        context = await context_for(client, sid, "inv-example-1")

        done = await run_data_code(SNIPPET, "example", context)

        assert done["status"] == "ok", done
        line = f"{EXAMPLE_DATA_CHANGE}: 4 rows, 2 columns"
        assert line in done["changes"] and ledger_for("inv-example-1").dataset_changes == [line]
        assert ledger_for("inv-example-1").example_data is True
        stored = services.datasets.get(context.state[DATASET_ID], sid)
        assert stored is not None and stored.code == SNIPPET
        assert stored.source is not None and stored.source.startswith("generated example data, made up by Python code")

    async def test_the_users_own_code_keeps_its_line(self, client: httpx.AsyncClient) -> None:
        sid = await open_session(client, with_data=False)
        context = await context_for(client, sid, "inv-example-2")

        done = await run_data_code(SNIPPET, "python", context)

        assert done["status"] == "ok" and EXAMPLE_DATA_CHANGE not in done["changes"]
        assert ledger_for("inv-example-2").example_data is False

    def test_tool_safety_takes_the_same_sources_as_the_tool(self) -> None:
        assert set(get_args(DataCodeSource)) == SOURCE_LANGUAGES
        check = ToolSafetyPlugin.check
        assert check("run_data_code", {"code": SNIPPET, "source_language": "example"}, "anyplot") is None
        assert check("run_data_code", {"code": SNIPPET, "source_language": "examples"}, "anyplot") is not None

    def test_the_source_line_of_example_data_names_no_translation(self) -> None:
        source = code_source("import numpy as np\nrng = np.random.default_rng(42)\ndf = None\n", "example")
        assert source.startswith("generated example data, made up by Python code; calls: np.random.default_rng")
        assert "translated" not in source
        assert code_source("df = (", "example") == "generated example data, made up by Python code"


class TestTheTurn:
    async def test_a_turn_that_makes_example_data_reports_it_and_its_kind(
        self, client: httpx.AsyncClient, swap_models, caplog: pytest.LogCaptureFixture
    ) -> None:
        """The data panel's request as the user's turn: `done` carries version 1 with its code and its line."""
        caplog.set_level(logging.INFO)
        turn = default_script()
        turn["root"] = [
            {"call": "get_spec_brief", "args": {}},
            {"call": "run_data_code", "args": {"code": SNIPPET, "source_language": "example"}},
            {"text": "Ich habe Beispieldaten erzeugt: 4 Zeilen, 2 Spalten. Prüfe sie und bestätige mit .confirm()."},
        ]
        swap_models("anthropic-vertex", turn)
        sid = await open_session(client, with_data=False)

        response = await client.post(f"/v1/sessions/{sid}/messages", headers=HEADERS, json={"text": "Beispieldaten"})
        name, done = parse_sse(response.text)[-1]

        assert name == "done" and done["data_confirmed"] is False
        assert done["dataset"]["version"] == 1 and done["dataset"]["code"] == SNIPPET
        assert done["dataset"]["changes"] == [f"{EXAMPLE_DATA_CHANGE}: 4 rows, 2 columns"]
        (chat_turn,) = _telemetry(caplog, "chat_turn")
        assert chat_turn["kind"] == "example" and "run_data_code" in chat_turn["tools"]
        data_code = attribution_lines(caplog, "data_code")
        assert data_code and data_code[0]["language"] == "example"


def test_turn_kind_example_outranks_code_but_not_a_plot() -> None:
    ledger = RequestLedger(tools=["get_spec_brief", "run_data_code"], example_data=True)
    assert telemetry.turn_kind(ledger) == "example"
    assert telemetry.turn_kind(RequestLedger(tools=["run_data_code"])) == "code"
    assert telemetry.turn_kind(RequestLedger(tools=["run_data_code", "plot_pipeline"], example_data=True)) == "plot"
    assert "example" in get_args(telemetry.TurnKind) and get_settings().data_code
