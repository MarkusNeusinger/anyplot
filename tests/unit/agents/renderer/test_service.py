"""Tests for agents/renderer/main.py and auth.py: the caller check, the /render contract, the slot and /status."""

import asyncio
import base64
import json
import time
from collections.abc import AsyncIterator, Iterator
from pathlib import Path
from typing import Any

import httpx
import pytest

from agents.renderer import main as main_module
from agents.renderer.auth import decode_claims
from agents.renderer.executor import ExecutorConfig, SandboxExecutor, Unavailable
from agents.renderer.main import Renderer, app, get_renderer
from agents.renderer.settings import RendererSettings, get_settings
from agents.renderer.wire import RendererStatus, RenderResponse

from .conftest import FakeLauncher
from .helpers import AGENTS_SA, SLEEPER, URL, FakeExecutor, id_token, job


GOOD = id_token(aud=URL, email=AGENTS_SA)


def body(**overrides: Any) -> dict[str, Any]:
    return {**job(themes=("light", "dark")).model_dump(mode="json"), **overrides}


@pytest.fixture
def settings() -> RendererSettings:
    return RendererSettings(
        environment="production", audiences=[URL], allowed_callers=[AGENTS_SA], min_mem_available_mb=0
    )


@pytest.fixture
def fake() -> FakeExecutor:
    return FakeExecutor()


@pytest.fixture
def renderer(settings: RendererSettings, fake: FakeExecutor) -> Renderer:
    return Renderer(settings, fake)


@pytest.fixture
def overrides(settings: RendererSettings, renderer: Renderer) -> Iterator[None]:
    app.dependency_overrides[get_settings] = lambda: settings
    app.dependency_overrides[get_renderer] = lambda: renderer
    yield
    app.dependency_overrides.clear()


@pytest.fixture
async def client(overrides: None) -> AsyncIterator[httpx.AsyncClient]:
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url=URL) as client:
        yield client


def auth(token: str = GOOD) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


class TestCallerCheck:
    async def test_no_token_is_unauthenticated(self, client: httpx.AsyncClient) -> None:
        for headers in ({}, {"Authorization": "Bearer not-a-jwt"}, {"Authorization": "Basic abc"}):
            response = await client.get("/status", headers=headers)
            assert response.status_code == 401 and response.json() == {"detail": "unauthenticated"}

    @pytest.mark.parametrize(
        "claims",
        [
            {"aud": "https://elsewhere.run.app", "email": AGENTS_SA},
            {"aud": URL, "email": "someone@example.com"},
            {"aud": URL},
            {"aud": ["https://elsewhere.run.app"], "email": AGENTS_SA},
        ],
    )
    async def test_a_token_for_another_audience_or_caller_is_forbidden(
        self, client: httpx.AsyncClient, claims: dict[str, Any]
    ) -> None:
        response = await client.post("/render", json=body(), headers=auth(id_token(**claims)))

        assert response.status_code == 403 and response.json() == {"detail": "forbidden"}

    async def test_the_agents_service_account_passes(self, client: httpx.AsyncClient) -> None:
        assert (await client.get("/status", headers=auth())).status_code == 200
        assert (await client.get("/status", headers=auth(id_token(aud=[URL], email=AGENTS_SA)))).status_code == 200

    async def test_an_owner_user_token_passes_once_its_client_id_and_email_are_listed(
        self, client: httpx.AsyncClient, settings: RendererSettings
    ) -> None:
        """A user's ID token names the OAuth client of gcloud or ADC as its audience, never the URL."""
        gcloud_client = "32555940559.apps.googleusercontent.com"
        token = id_token(aud=gcloud_client, email="owner@example.com")
        assert (await client.get("/status", headers=auth(token))).status_code == 403

        settings.audiences.append(gcloud_client)
        settings.allowed_callers.append("owner@example.com")

        assert (await client.get("/status", headers=auth(token))).status_code == 200

    async def test_development_skips_the_check(self, client: httpx.AsyncClient, settings: RendererSettings) -> None:
        settings.environment = "development"

        assert (await client.get("/status")).status_code == 200

    def test_development_is_refused_on_cloud_run(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("ENVIRONMENT", "development")
        monkeypatch.setenv("K_SERVICE", "anyplot-renderer")

        with pytest.raises(ValueError, match="refused on Cloud Run"):
            RendererSettings()

    async def test_x_serverless_authorization_wins_over_authorization(self, client: httpx.AsyncClient) -> None:
        """With both headers Cloud Run checks only X-Serverless-Authorization; Authorization reaches us unverified."""
        forged = auth(id_token(aud=URL, email=AGENTS_SA))
        invoker = {"X-Serverless-Authorization": f"Bearer {id_token(aud=URL, email='editor@example.com')}"}

        refused = await client.get("/status", headers={**forged, **invoker})
        alone = await client.get("/status", headers={"X-Serverless-Authorization": f"Bearer {GOOD}"})
        empty = await client.get("/status", headers={**forged, "X-Serverless-Authorization": ""})

        assert refused.status_code == 403 and refused.json() == {"detail": "forbidden"}
        assert alone.status_code == 200
        assert empty.status_code == 401  # present but empty: never falls back to Authorization

    def test_decode_claims_ignores_the_signature(self) -> None:
        claims = decode_claims(f"Bearer {GOOD}")
        assert claims is not None and claims["aud"] == URL and claims["email"] == AGENTS_SA
        assert decode_claims(f"bearer {GOOD}") == claims
        assert decode_claims("Bearer a.b") is None
        assert decode_claims("Bearer a.!!!.c") is None


class TestRender:
    async def test_the_contract_round_trips(self, client: httpx.AsyncClient, fake: FakeExecutor) -> None:
        response = await client.post("/render", json=body(), headers=auth())

        assert response.status_code == 200 and response.headers["cache-control"] == "no-store"
        answer = RenderResponse.model_validate_json(response.content)
        assert answer.job_id == "job123" and set(answer.outputs) == {"light", "dark"}
        light = answer.outputs["light"]
        assert light.exit_code == 0 and light.png_base64 is not None
        assert base64.b64decode(light.png_base64).startswith(b"\x89PNG")
        assert answer.timings.total_s >= answer.timings.slot_wait_s >= 0
        assert fake.calls == [("job123", "light"), ("job123", "dark")]  # one theme after the other

    async def test_an_invalid_job_is_refused_without_echoing_it(self, client: httpx.AsyncClient) -> None:
        for bad in (
            body(job_id="../escape", source="SECRET-CELL-VALUE"),
            body(language="r", source="SECRET-CELL-VALUE"),
            body(themes=["light", "light"], source="SECRET-CELL-VALUE"),
            body(timeout_s=600, source="SECRET-CELL-VALUE"),
            body(extra="x", source="SECRET-CELL-VALUE"),
        ):
            response = await client.post("/render", json=bad, headers=auth())
            assert response.status_code == 422 and response.json() == {"detail": "invalid_job"}
            assert "SECRET" not in response.text

    async def test_renders_are_serial(self, client: httpx.AsyncClient, fake: FakeExecutor) -> None:
        responses = await asyncio.gather(*(client.post("/render", json=body(), headers=auth()) for _ in range(3)))

        assert [response.status_code for response in responses] == [200, 200, 200]
        assert fake.max_active == 1

    async def test_a_request_that_cannot_get_the_slot_is_busy(
        self, client: httpx.AsyncClient, fake: FakeExecutor, settings: RendererSettings
    ) -> None:
        settings.slot_wait_s = 0.05
        fake.gate = asyncio.Event()
        first = asyncio.create_task(client.post("/render", json=body(), headers=auth()))
        while fake.active == 0:
            await asyncio.sleep(0.01)

        second = await client.post("/render", json=body(), headers=auth())
        fake.gate.set()

        assert second.status_code == 503 and second.json() == {"detail": "busy"}
        assert (await first).status_code == 200

    async def test_low_memory_refuses_before_any_sandbox(
        self, client: httpx.AsyncClient, fake: FakeExecutor, settings: RendererSettings, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        settings.min_mem_available_mb = 1024
        monkeypatch.setattr(main_module, "mem_available_mb", lambda: 700)

        response = await client.post("/render", json=body(), headers=auth())

        assert response.status_code == 503 and response.json() == {"detail": "low_memory"}
        assert fake.calls == []

    async def test_an_unreadable_memory_signal_does_not_block(
        self, client: httpx.AsyncClient, settings: RendererSettings, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        settings.min_mem_available_mb = 1024
        monkeypatch.setattr(main_module, "mem_available_mb", lambda: None)

        assert (await client.post("/render", json=body(), headers=auth())).status_code == 200

    async def test_an_executor_refusal_is_a_503_with_its_code(
        self, client: httpx.AsyncClient, fake: FakeExecutor
    ) -> None:
        fake.error = Unavailable("stuck")

        response = await client.post("/render", json=body(), headers=auth())

        assert response.status_code == 503 and response.json() == {"detail": "stuck"}

    async def test_an_unexpected_error_is_a_json_500_without_its_message(
        self, client: httpx.AsyncClient, fake: FakeExecutor, caplog: pytest.LogCaptureFixture
    ) -> None:
        """A plain-text 500 read as a front-end error, so the backend re-ran the hostile job."""
        fake.error = OverflowError("SECRET-CELL-VALUE")

        response = await client.post("/render", json=body(), headers=auth())

        assert response.status_code == 500 and response.json() == {"detail": "internal"}
        assert "SECRET" not in response.text and "SECRET" not in caplog.text
        assert "OverflowError" in caplog.text

    async def test_the_volume_must_be_in_place_on_cloud_run(
        self, client: httpx.AsyncClient, fake: FakeExecutor, renderer: Renderer
    ) -> None:
        renderer.volume = False

        response = await client.post("/render", json=body(), headers=auth())
        status = RendererStatus.model_validate((await client.get("/status", headers=auth())).json())

        assert response.status_code == 503 and response.json() == {"detail": "volume_missing"}
        assert fake.calls == [] and status.volume is False

    def test_the_volume_is_checked_only_on_cloud_run(
        self, settings: RendererSettings, fake: FakeExecutor, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        checks: list[tuple[Path, int]] = []

        def check(runs_dir: Path, max_bytes: int) -> bool:
            checks.append((runs_dir, max_bytes))
            return False

        monkeypatch.setattr(main_module, "runs_volume_ok", check)

        assert Renderer(settings, fake).volume is None and checks == []
        on_cloud_run = settings.model_copy(update={"cloud_run_service": "anyplot-renderer"})
        assert Renderer(on_cloud_run, fake).volume is False
        assert checks == [(Path("/tmp/runs"), 1024 * 1024 * 1024)]

    async def test_a_stuck_launcher_ends_the_instance_on_cloud_run(
        self, client: httpx.AsyncClient, fake: FakeExecutor, settings: RendererSettings
    ) -> None:
        exits: list[bool] = []
        stuck = Renderer(
            settings.model_copy(update={"cloud_run_service": "anyplot-renderer"}),
            fake,
            terminate=lambda: exits.append(True),
        )
        stuck.volume = None
        app.dependency_overrides[get_renderer] = lambda: stuck
        fake.stuck = 1
        fake.error = Unavailable("stuck")

        first = await client.post("/render", json=body(), headers=auth())
        second = await client.post("/render", json=body(), headers=auth())

        assert first.status_code == second.status_code == 503
        assert exits == [True]  # once

    async def test_a_stuck_launcher_off_cloud_run_keeps_the_process(
        self, client: httpx.AsyncClient, fake: FakeExecutor, renderer: Renderer
    ) -> None:
        exits: list[bool] = []
        renderer.terminate = lambda: exits.append(True)
        fake.stuck = 1

        await client.post("/render", json=body(), headers=auth())

        assert exits == []


class TestCancellation:
    """uvicorn does not cancel a handler whose client left; the route must notice and stop the sandbox."""

    @pytest.fixture
    def real(self, settings: RendererSettings, config: ExecutorConfig) -> Iterator[Renderer]:
        renderer = Renderer(settings, SandboxExecutor(config))
        app.dependency_overrides[get_settings] = lambda: settings
        app.dependency_overrides[get_renderer] = lambda: renderer
        yield renderer
        app.dependency_overrides.clear()

    async def test_a_client_that_goes_away_stops_the_sandbox(self, real: Renderer, launcher: FakeLauncher) -> None:
        payload = json.dumps(job(SLEEPER).model_dump(mode="json")).encode()
        received: list[str] = []

        async def receive() -> dict[str, Any]:
            if not received:
                received.append("body")
                return {"type": "http.request", "body": payload, "more_body": False}
            for _ in range(200):
                if launcher.launches():
                    break
                await asyncio.sleep(0.05)
            await asyncio.sleep(0.2)
            return {"type": "http.disconnect"}

        sent: list[dict[str, Any]] = []

        async def send(message: dict[str, Any]) -> None:
            sent.append(message)

        scope = {
            "type": "http",
            "asgi": {"version": "3.0"},
            "http_version": "1.1",
            "method": "POST",
            "scheme": "https",
            "path": "/render",
            "raw_path": b"/render",
            "query_string": b"",
            "root_path": "",
            "headers": [
                (b"host", b"renderer"),
                (b"content-type", b"application/json"),
                (b"authorization", f"Bearer {GOOD}".encode()),
            ],
            "client": ("127.0.0.1", 50000),
            "server": ("renderer", 443),
        }
        started = time.monotonic()

        await asyncio.wait_for(app(scope, receive, send), 30)

        assert time.monotonic() - started < 20  # not the 30 s the sleeper asked for
        assert len(launcher.launches()) == 1 and launcher.deletes() == launcher.launches()
        assert sent[0]["status"] == 499
        assert real.slot.in_flight == 0 and real.executor.stuck == 0

    async def test_the_cancel_route_stops_a_running_render(self, real: Renderer, launcher: FakeLauncher) -> None:
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url=URL) as client:
            pending = asyncio.create_task(
                client.post("/render", json=job(SLEEPER).model_dump(mode="json"), headers=auth())
            )
            for _ in range(200):
                if launcher.launches():
                    break
                await asyncio.sleep(0.05)

            cancelled = await client.post("/render/job123/cancel", headers=auth())
            answer = await asyncio.wait_for(pending, 20)
            again = await client.post("/render/job123/cancel", headers=auth())

        assert cancelled.status_code == 200 and cancelled.json() == {"cancelled": 1}
        assert answer.status_code == 499 and answer.json() == {"detail": "cancelled"}
        assert again.json() == {"cancelled": 0}
        assert launcher.deletes() == launcher.launches() and real.slot.in_flight == 0

    async def test_the_cancel_route_checks_the_caller_and_the_id(self, real: Renderer) -> None:
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url=URL) as client:
            anonymous = await client.post("/render/job123/cancel")
            bad = await client.post("/render/..%2Fescape/cancel", headers=auth())

        assert anonymous.status_code == 401
        assert bad.status_code in (404, 422)


class TestStatus:
    async def test_status_reports_the_slot_and_the_memory_signal(
        self, client: httpx.AsyncClient, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(main_module, "mem_available_mb", lambda: 3500)

        response = await client.get("/status", headers=auth())

        status = RendererStatus.model_validate(response.json())
        assert status.name == "anyplot-renderer" and status.version
        assert (status.in_flight, status.waiting, status.stuck) == (0, 0, 0)
        assert status.mem_available_mb == 3500 and status.sandbox is True

    def test_the_default_renderer_uses_the_sandbox_executor(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("RENDERER_ALLOWED_CALLERS", f"{AGENTS_SA}, owner@example.com")
        monkeypatch.setenv("RENDERER_AUDIENCES", URL)

        renderer = get_renderer()

        assert type(renderer.executor).__name__ == "SandboxExecutor"
        assert renderer.settings.allowed_callers == [AGENTS_SA, "owner@example.com"]
        assert renderer.settings.audiences == [URL]
        assert renderer.settings.environment == "production"
