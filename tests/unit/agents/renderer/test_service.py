"""Tests for agents/renderer/main.py and auth.py: the caller check, the /render contract, the slot and /status."""

import asyncio
import base64
from collections.abc import AsyncIterator, Iterator
from typing import Any

import httpx
import pytest

from agents.renderer import main as main_module
from agents.renderer.auth import decode_claims
from agents.renderer.executor import Unavailable
from agents.renderer.main import Renderer, app, get_renderer
from agents.renderer.settings import RendererSettings, get_settings
from agents.renderer.wire import RendererStatus, RenderResponse

from .helpers import AGENTS_SA, URL, FakeExecutor, id_token, job


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
