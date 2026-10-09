"""Log canary: a full run with canary strings in the message and the data leaves none of them in any log record."""

import logging
from collections.abc import Iterator

import httpx
import pytest

from agents.anyplot.dev_fixture import snapshot_from_repo
from agents.anyplot.services import Services
from agents.main import Runtime, app, get_runtime

from .conftest import CASES
from .fakes import default_script


MESSAGE_CANARY = "CANARY-MSG-91f2"
CELL_CANARY = "CANARY-CELL-5b7d"
USER = "adm_canary0000000001"
HEADERS = {"X-Anyplot-User": USER, "X-Request-Id": "req-canary"}


@pytest.fixture
def runtime() -> Iterator[Runtime]:
    fresh = Runtime()
    app.dependency_overrides[get_runtime] = lambda: fresh
    yield fresh
    app.dependency_overrides.clear()


async def test_no_content_in_logs(
    runtime: Runtime, services: Services, swap_models, caplog: pytest.LogCaptureFixture
) -> None:
    caplog.set_level(logging.DEBUG)
    for name in ("anyplot", "agents", "anyplot.agents.attribution"):
        logging.getLogger(name).setLevel(logging.DEBUG)
    swap_models("gemini", default_script())
    data = (CASES / "scatter-basic-matplotlib" / "data.csv").read_text().replace("S07", CELL_CANARY)
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://agents") as client:
        created = await client.post(
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
        sid = created.json()["session_id"]
        assert (
            await client.post(f"/v1/sessions/{sid}/dataset", headers=HEADERS, json={"text": data})
        ).status_code == 200
        response = await client.post(
            f"/v1/sessions/{sid}/messages", headers=HEADERS, json={"text": f"Please plot it {MESSAGE_CANARY}"}
        )
        assert '"plot"' in response.text or "event: plot" in response.text

    records = [record.getMessage() for record in caplog.records]
    assert any('"hook": "model"' in message for message in records), "the attribution log ran"
    leaked = [message for message in records if MESSAGE_CANARY in message or CELL_CANARY in message]
    assert leaked == []
    assert not any("Exam Score" in message for message in records)
