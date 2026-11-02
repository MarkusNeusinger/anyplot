"""`GET /v1/sessions/{sid}/dataset/data.csv`: the data panel's full view reads the current version as stored.

The page shows every value exactly as the canonical CSV holds it (data-fidelity rule), so the route answers the
stored bytes and formats nothing again; it reads only, so a turn in flight does not block it.
"""

import asyncio
from collections.abc import AsyncIterator, Iterator
from typing import Any

import httpx
import pytest

from agents.anyplot.dev_fixture import snapshot_from_repo
from agents.anyplot.run_queue import RunQueue
from agents.anyplot.services import Services
from agents.anyplot.session_state import read_session
from agents.main import ActiveRun, Runtime, app, get_runtime


USER = "adm_csv0000000000001"
OTHER = "adm_csv0000000000002"
DATA = 'Study Hours,Note,Student\n0.12345678901234568,"a, b",Zoë 🌍\n2.000000000000001,,"line\nbreak"\n'
"""A float with 17 significant digits, a quoted comma, an empty cell, a line break and text beyond ASCII."""


def headers(user: str = USER) -> dict[str, str]:
    return {"X-Anyplot-User": user, "X-Request-Id": f"req-{user[-4:]}"}


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


async def open_session(client: httpx.AsyncClient, user: str = USER) -> str:
    body: dict[str, Any] = {
        "user": user,
        "spec_id": "scatter-basic",
        "library": "matplotlib",
        "locale": "en",
        "snapshot": snapshot_from_repo("scatter-basic", "matplotlib").model_dump(),
    }
    response = await client.post("/v1/sessions", headers=headers(user), json=body)
    assert response.status_code == 200, response.text
    return str(response.json()["session_id"])


async def stored_csv(runtime: Runtime, services: Services, sid: str) -> str:
    view = read_session((await runtime.session(USER, sid)).state)
    assert view is not None and view.dataset_id
    stored = services.datasets.get(view.dataset_id, sid)
    assert stored is not None
    return stored.csv


async def test_answers_the_stored_canonical_csv_byte_for_byte(client, runtime, services) -> None:
    sid = await open_session(client)
    pasted = await client.post(f"/v1/sessions/{sid}/dataset", headers=headers(), json={"text": DATA})
    assert pasted.status_code == 200, pasted.text

    response = await client.get(f"/v1/sessions/{sid}/dataset/data.csv", headers=headers())

    assert response.status_code == 200
    assert response.headers["content-type"] == "text/csv; charset=utf-8"
    assert response.headers["cache-control"] == "private, no-store"
    assert response.headers["x-content-type-options"] == "nosniff"
    assert response.content.decode("utf-8") == await stored_csv(runtime, services, sid)
    # Nothing rounded or folded: the 17 digits, the quoted comma and the line break come back as written.
    assert "0.12345678901234568" in response.text
    assert '"a, b"' in response.text
    assert '"line\nbreak"' in response.text


async def test_a_new_paste_is_the_current_version(client) -> None:
    sid = await open_session(client)
    for text in (DATA, "x,y\n1,2\n3,4\n"):
        assert (await client.post(f"/v1/sessions/{sid}/dataset", headers=headers(), json={"text": text})).is_success
    response = await client.get(f"/v1/sessions/{sid}/dataset/data.csv", headers=headers())
    assert response.text == "x,y\n1,2\n3,4\n"


async def test_no_data_yet_is_422_no_dataset(client) -> None:
    sid = await open_session(client)
    response = await client.get(f"/v1/sessions/{sid}/dataset/data.csv", headers=headers())
    assert response.status_code == 422
    assert response.json()["detail"] == "no_dataset"


async def test_another_users_session_is_not_found(client) -> None:
    sid = await open_session(client)
    assert (await client.post(f"/v1/sessions/{sid}/dataset", headers=headers(), json={"text": DATA})).is_success
    response = await client.get(f"/v1/sessions/{sid}/dataset/data.csv", headers=headers(OTHER))
    assert response.status_code == 404
    assert response.json()["detail"] == "session_expired"


async def test_a_turn_in_flight_does_not_block_the_read(client, runtime) -> None:
    sid = await open_session(client)
    assert (await client.post(f"/v1/sessions/{sid}/dataset", headers=headers(), json={"text": DATA})).is_success
    runtime.active[sid] = ActiveRun(abort=asyncio.Event(), user=USER, started=runtime.now())
    try:
        response = await client.get(f"/v1/sessions/{sid}/dataset/data.csv", headers=headers())
    finally:
        runtime.active.pop(sid, None)
    assert response.status_code == 200
