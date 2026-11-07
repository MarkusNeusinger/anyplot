"""The data operations of 2026-11-07 through the root's `prepare_data`: a computed column, and a gap the chat names.

Persona tests of 2026-11-06: five of ten personas got no plot because `prepare_data` could not multiply, take a log,
a lag difference or a moving average, or empty missing codes, and the root told them to fix the data in their file.
`compute`, `diff`, `rolling` and `blank` close those gaps (`data/prepare.py`); a change no operation can make is the
`unsupported` operation, which answers a fixed sentence in the session language and counts the gap by its family.
"""

import json
import logging
from collections.abc import AsyncIterator, Iterator
from typing import Any

import httpx
import pytest

from agents.anyplot import telemetry
from agents.anyplot.policy import refusal
from agents.anyplot.services import Services
from agents.anyplot.session_state import read_session
from agents.main import Runtime, app, get_runtime

from .test_service_flow import HEADERS, _session_state, open_session, parse_sse, permissive_queue, tool_responses


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


FILL = {"op": "unsupported", "family": "fill_values"}
REQUEST_CANARY = "CANARY-GAP-5d21"


def chat_turns(caplog: pytest.LogCaptureFixture) -> list[dict[str, Any]]:
    lines = [json.loads(r.getMessage()) for r in caplog.records if r.name == telemetry.TELEMETRY_LOGGER]
    return [line for line in lines if line["event"] == "chat_turn"]


async def test_a_gap_answers_the_fixed_sentence_changes_nothing_and_is_counted(
    client: httpx.AsyncClient, swap_models, caplog: pytest.LogCaptureFixture
) -> None:
    caplog.set_level(logging.INFO)
    sentence = refusal("unsupported_fill_values", "de")
    fake = swap_models(
        "gemini", {"root": [{"call": "prepare_data", "args": {"operations": [FILL]}}, {"text": sentence}]}
    )
    sid = await open_session(client)
    assert (await client.put(f"/v1/sessions/{sid}/language", headers=HEADERS, json={"language": "de"})).is_success
    before = read_session(await _session_state(client, sid))

    response = await client.post(
        f"/v1/sessions/{sid}/messages", headers=HEADERS, json={"text": f"Fülle die Lücken auf {REQUEST_CANARY}"}
    )

    answer = tool_responses(fake, "prepare_data")[0]
    assert answer == {"status": "error", "code": "unsupported_operation", "family": "fill_values", "message": sentence}
    assert sentence.startswith("Ich kann keine Werte ergänzen")
    after = read_session(await _session_state(client, sid))
    assert before is not None and after is not None and after.dataset_id == before.dataset_id
    assert "dataset" not in parse_sse(response.text)[-1][1]
    (turn,) = chat_turns(caplog)
    assert turn["capability_gap"] == ["fill_values"] and turn["prep_ops"] == []
    assert REQUEST_CANARY not in json.dumps(turn)


async def test_a_gap_beside_a_change_changes_nothing_either(client: httpx.AsyncClient, swap_models) -> None:
    """A call that names a gap is refused as a whole: the rename beside it does not run."""
    rename = {"op": "rename", "column": "Exam Score", "name": "Score"}
    fake = swap_models(
        "gemini", {"root": [{"call": "prepare_data", "args": {"operations": [rename, FILL]}}, {"text": "."}]}
    )
    sid = await open_session(client)

    response = await client.post(f"/v1/sessions/{sid}/messages", headers=HEADERS, json={"text": "rename and fill"})

    assert tool_responses(fake, "prepare_data")[0]["code"] == "unsupported_operation"
    assert "dataset" not in parse_sse(response.text)[-1][1]


async def test_a_computed_column_is_the_next_version_with_its_expression(
    client: httpx.AsyncClient, swap_models, caplog: pytest.LogCaptureFixture
) -> None:
    caplog.set_level(logging.INFO)
    compute = {
        "op": "compute",
        "name": "Score per hour",
        "expression": "s / h",
        "inputs": {"s": "Exam Score", "h": "Study Hours"},
    }
    fake = swap_models("gemini", {"root": [{"call": "prepare_data", "args": {"operations": [compute]}}, {"text": "."}]})
    sid = await open_session(client)

    response = await client.post(f"/v1/sessions/{sid}/messages", headers=HEADERS, json={"text": "score per hour"})

    answer = tool_responses(fake, "prepare_data")[0]
    assert answer["status"] == "ok" and answer["version"] == 2
    done = parse_sse(response.text)[-1][1]
    assert done["dataset"]["changes"] == ["added column Score per hour: s / h with s = Exam Score, h = Study Hours"]
    (turn,) = chat_turns(caplog)
    assert turn["prep_ops"] == ["compute"] and turn["capability_gap"] == []
