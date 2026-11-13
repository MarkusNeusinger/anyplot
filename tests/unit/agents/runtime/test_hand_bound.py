"""The bindings the user set by hand reach the root's next turn as the user's choice (`session_state.USER_BOUND`).

Persona round of 2026-11-11: after the user had rebound a role by a click, the root saw bindings that differed from
what it had said and wrote "I was wrong earlier". The session block now lists the pairs the user set, for one turn.
"""

from collections.abc import AsyncIterator, Iterator
from typing import Any

import httpx
import pytest

from agents.anyplot.agent import USER_BOUND_LINE
from agents.anyplot.run_queue import RunQueue
from agents.anyplot.schemas import Binding
from agents.anyplot.services import Services
from agents.anyplot.session_state import BINDINGS, USER_BOUND, user_bound
from agents.main import Runtime, _hand_bound, app, get_runtime

from .test_service_flow import HEADERS, _session_state, open_session


X = Binding(role="x", column="Study Hours")
Y = Binding(role="y", column="Exam Score")
SWAPPED = [{"role": "x", "column": "Exam Score"}, {"role": "y", "column": "Study Hours"}]


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


def block(request: Any) -> str:
    system = request.config.system_instruction
    return system if isinstance(system, str) else "\n".join(part.text or "" for part in system.parts or [])


def test_the_note_holds_the_pairs_the_user_set_and_drops_the_ones_taken_back() -> None:
    after = [{"role": "x", "column": "Exam Score"}, {"role": "y", "column": "Study Hours"}]

    assert _hand_bound(None, [X, Y], after) == after
    # A second click changes y alone: x stays the user's from the first one.
    later = [{"role": "x", "column": "Exam Score"}, {"role": "y", "column": "Attendance"}]
    assert _hand_bound(after, [Binding(**pair) for pair in after], later) == later
    # Set back to what the session held before the first click: by hand again, so these pairs are the user's too.
    back = [X.model_dump(), Y.model_dump()]
    noted = _hand_bound(after, [Binding(**pair) for pair in after], back)
    assert user_bound({USER_BOUND: noted}, [X, Y]) == [X, Y]
    assert _hand_bound("not a list", [X, Y], [X.model_dump(), Y.model_dump()]) == []


def test_only_the_pairs_still_in_force_are_the_users() -> None:
    state = {USER_BOUND: SWAPPED}
    swapped = [Binding(**pair) for pair in SWAPPED]

    assert user_bound(state, swapped) == swapped
    # The root, or a new paste, has since bound y to another column: that pair is no longer the user's.
    assert user_bound(state, [swapped[0], Binding(role="y", column="Attendance")]) == [swapped[0]]
    assert user_bound({}, swapped) == [] and user_bound({USER_BOUND: "x"}, swapped) == []


async def test_a_new_paste_drops_the_note(client: httpx.AsyncClient, swap_models) -> None:
    """The bindings of a new paste are the parse's: what the user set by hand was for the data it replaces."""
    swap_models("gemini", {"root": [{"text": "unused"}]})
    sid = await open_session(client)
    assert (await client.put(f"/v1/sessions/{sid}/bindings", headers=HEADERS, json=SWAPPED)).status_code == 200

    pasted = await client.post(f"/v1/sessions/{sid}/dataset", headers=HEADERS, json={"text": "a,b\n1,2\n3,4\n5,7\n"})

    assert pasted.status_code == 200, pasted.text
    assert (await _session_state(client, sid)).get(USER_BOUND) is None


async def test_the_roots_next_turn_reads_the_pairs_as_the_users_choice_and_the_turn_after_does_not(
    client: httpx.AsyncClient, swap_models
) -> None:
    fake = swap_models("gemini", {"root": [{"text": "x is now the score."}, {"text": "Still so."}]})
    sid = await open_session(client)
    held = (await _session_state(client, sid))[BINDINGS]
    # The page's echo of the bindings in force is no choice of the user's.
    assert (await client.put(f"/v1/sessions/{sid}/bindings", headers=HEADERS, json=held)).status_code == 200
    assert (await _session_state(client, sid)).get(USER_BOUND) is None

    assert (await client.put(f"/v1/sessions/{sid}/bindings", headers=HEADERS, json=SWAPPED)).status_code == 200
    assert (await _session_state(client, sid))[USER_BOUND] == SWAPPED
    await client.post(f"/v1/sessions/{sid}/messages", headers=HEADERS, json={"text": "what is on x now?"})

    first = block(fake.requests[0])
    assert USER_BOUND_LINE.format(count=2) in first
    assert "<user_data>\nx: Exam Score\ny: Study Hours\n</user_data>" in first
    assert (await _session_state(client, sid)).get(USER_BOUND) is None  # read by a turn that ended well

    await client.post(f"/v1/sessions/{sid}/messages", headers=HEADERS, json={"text": "and now?"})
    assert "set by hand" not in block(fake.requests[1])
