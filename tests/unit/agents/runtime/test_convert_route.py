"""The agents service's file conversion route, `POST /v1/sessions/{sid}/dataset/convert`, over the fake backend.

The route reads nothing itself: the backend converts (`FakeBackend.convert`, scripted here),
and the route turns the outcome into the page's answer or a refusal code, counts the user's
conversions on their own window, holds one conversion per user, and logs no content.
"""

import asyncio
import base64
import json
from collections.abc import AsyncIterator, Iterator
from typing import Any

import httpx
import pytest

from agents.anyplot.plugins.ledger import MESSAGE_WINDOW_S, UsageBook
from agents.anyplot.render.backends.fake import FakeBackend
from agents.anyplot.render.contract import ConvertJob, ConvertOutput, DataRunUnsupported
from agents.anyplot.services import Services
from agents.anyplot.settings import AgentSettings, get_settings
from agents.main import Runtime, app, get_runtime
from agents.renderer.wire import ConvertMeta

from .test_run_queue import Clock
from .test_service_flow import HEADERS, USER, open_session, permissive_queue


WORKBOOK = b"PK\x03\x04" + b"\0" * 64


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


@pytest.fixture
def clock(services: Services) -> Clock:
    fake = Clock()
    services.usage = UsageBook(clock=fake)
    return fake


def convert(client: httpx.AsyncClient, sid: str, data: bytes = WORKBOOK, **extra: Any) -> Any:
    body = {"data_base64": base64.b64encode(data).decode(), **extra}
    return client.post(f"/v1/sessions/{sid}/dataset/convert", headers=HEADERS, json=body)


def lines(caplog: pytest.LogCaptureFixture, hook: str) -> list[dict[str, Any]]:
    found = []
    for record in caplog.records:
        try:
            line = json.loads(record.getMessage())
        except ValueError:
            continue
        if isinstance(line, dict) and line.get("hook") == hook:
            found.append(line)
    return found


class TestConvertRoute:
    async def test_a_workbook_comes_back_as_text_and_nothing_is_stored(
        self, client: httpx.AsyncClient, backend: FakeBackend, caplog: pytest.LogCaptureFixture
    ) -> None:
        caplog.set_level("INFO")
        sid = await open_session(client, with_data=False)

        response = await convert(client, sid, sheet="Gehälter 2024")

        assert response.status_code == 200 and response.headers["cache-control"] == "private, no-store"
        assert response.json() == {
            "text": "x,y\n0,0\n1,1\n2,4\n3,9\n",
            "format": "csv",
            "kind": "xlsx",
            "rows": 4,
            "columns": 2,
            "sheet": "Sheet1",
            "sheets": ["Sheet1"],
            "sheet_count": 1,
            "warnings": {},
            "dropped": [],
        }
        (job,) = backend.convert_jobs
        assert job.data == WORKBOOK and job.sheet == "Gehälter 2024" and job.timeout_s == 10.0
        confirm = await client.post(f"/v1/sessions/{sid}/dataset/confirm", headers=HEADERS)
        assert confirm.json() == {"detail": "no_dataset"}  # the conversion stored nothing
        (line,) = lines(caplog, "data_convert")
        assert line["outcome"] == "ok" and line["kind"] == "xlsx" and line["bytes"] == len(WORKBOOK)
        assert "Gehälter" not in json.dumps(line) and "x,y" not in json.dumps(line)

    @pytest.mark.parametrize(
        ("output", "body"),
        [
            (
                ConvertOutput(exit_code=16, refusal="too_many_rows", measured=21_000, limit=20_000),
                {"detail": "file_too_many_rows", "measured": 21_000, "limit": 20_000},
            ),
            (ConvertOutput(exit_code=11, refusal="encrypted"), {"detail": "file_encrypted"}),
            (ConvertOutput(exit_code=None, timed_out=True, reason="timeout"), {"detail": "file_timeout"}),
            (ConvertOutput(exit_code=None, reason="memory", measured=200, limit=300), {"detail": "file_too_complex"}),
            (ConvertOutput(exit_code=1), {"detail": "file_unreadable"}),
            (ConvertOutput(exit_code=8), {"detail": "file_unreadable"}),
            # A reader that died without its status.json (SIGABRT on an allocation): too much, not unreadable.
            (ConvertOutput(exit_code=-6), {"detail": "file_too_complex"}),
            (ConvertOutput(exit_code=134), {"detail": "file_too_complex"}),
            (
                ConvertOutput(exit_code=23, refusal="formulas_only", measured=4),
                {"detail": "file_formulas_only", "measured": 4},
            ),
        ],
    )
    async def test_a_refusal_has_its_code_and_a_broken_cap_its_numbers(
        self, client: httpx.AsyncClient, backend: FakeBackend, output: ConvertOutput, body: dict[str, Any]
    ) -> None:
        backend.convert_script = lambda job: output
        sid = await open_session(client, with_data=False)

        response = await convert(client, sid)

        assert (response.status_code, response.json()) == (422, body)

    async def test_a_renderer_without_conversions_is_convert_unavailable(
        self, client: httpx.AsyncClient, backend: FakeBackend
    ) -> None:
        def unsupported(job: ConvertJob) -> ConvertOutput:
            raise DataRunUnsupported("no /convert route")

        backend.convert_script = unsupported
        sid = await open_session(client, with_data=False)

        response = await convert(client, sid)

        assert (response.status_code, response.json()) == (503, {"detail": "convert_unavailable"})

    @pytest.mark.parametrize(
        ("data_base64", "status", "detail"),
        [
            ("!!!!", 422, "invalid"),
            # One byte over 5 MiB still fits the field's base64 length, so the decoded size refuses it.
            (base64.b64encode(b"\0" * (5 * 1024 * 1024 + 1)).decode(), 413, "too_long"),
            ("A" * (8 * 1024 * 1024), 422, None),  # over the field's cap: FastAPI's own validation
        ],
        ids=["not base64", "one byte over", "over the field"],
    )
    async def test_a_bad_body_is_refused_before_the_backend(
        self, client: httpx.AsyncClient, backend: FakeBackend, data_base64: str, status: int, detail: str | None
    ) -> None:
        sid = await open_session(client, with_data=False)

        response = await client.post(
            f"/v1/sessions/{sid}/dataset/convert", headers=HEADERS, json={"data_base64": data_base64}
        )

        assert response.status_code == status
        if detail is not None:
            assert response.json() == {"detail": detail}
        assert backend.convert_jobs == []

    async def test_conversions_have_their_own_window_and_leave_the_pastes_alone(
        self, client: httpx.AsyncClient, clock: Clock, services: Services, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("AGENT_USER_CONVERSIONS_PER_MINUTE", "2")
        get_settings.cache_clear()
        sid = await open_session(client, with_data=False)

        assert (await convert(client, sid)).status_code == 200
        assert (await convert(client, sid)).status_code == 200
        refused = await convert(client, sid)

        assert (refused.status_code, refused.json()) == (429, {"detail": "rate_limited"})
        assert services.usage.user_conversions(USER) == 2 and services.usage.user_pastes(USER) == 0
        clock.advance(MESSAGE_WINDOW_S)
        assert (await convert(client, sid)).status_code == 200

    async def test_one_conversion_per_user_at_a_time(
        self, client: httpx.AsyncClient, backend: FakeBackend, runtime: Runtime
    ) -> None:
        sid = await open_session(client, with_data=False)
        runtime.converting.add(USER)

        response = await convert(client, sid)

        assert (response.status_code, response.json()) == (409, {"detail": "run_active"})
        runtime.converting.discard(USER)
        assert (await convert(client, sid)).status_code == 200 and USER not in runtime.converting

    async def test_a_busy_slot_is_capacity(
        self, client: httpx.AsyncClient, services: Services, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("AGENT_CONVERT_SLOT_WAIT_S", "0.05")
        get_settings.cache_clear()
        sid = await open_session(client, with_data=False)
        await services.backend.slots.acquire("run")  # a pipeline render holds the one slot
        try:
            response = await convert(client, sid)
        finally:
            services.backend.slots.release()

        assert (response.status_code, response.json()) == (503, {"detail": "capacity"})

    async def test_a_conversion_waits_behind_a_waiting_pipeline_render(self, services: Services) -> None:
        slots = services.backend.slots
        await slots.acquire("run")
        order: list[str] = []

        async def take(lane: Any, name: str) -> None:
            await slots.acquire(lane)
            order.append(name)
            slots.release()

        conversion = asyncio.create_task(take("toggle", "convert"))
        await asyncio.sleep(0)
        render = asyncio.create_task(take("run", "render"))
        await asyncio.sleep(0)
        slots.release()
        await asyncio.gather(conversion, render)

        assert order == ["render", "convert"]

    def test_the_defaults(self) -> None:
        settings = AgentSettings()
        assert (settings.user_conversions_per_minute, settings.user_conversions_per_day) == (5, 30)
        assert (settings.convert_timeout_s, settings.convert_slot_wait_s) == (10.0, 20.0)


def test_the_fake_backend_meta_is_a_valid_wire_meta() -> None:
    output = asyncio.run(FakeBackend().convert(ConvertJob(job_id="c1", data=b"x")))
    assert isinstance(output.meta, ConvertMeta)
