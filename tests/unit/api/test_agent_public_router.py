"""
Tests for api/routers/agent_public.py — the public lane of the agent chat under /agent.

The lane calls the admin lane's route functions (tests/unit/api/test_agent_router.py covers
their behaviour), so these tests cover what is the lane's own: the door, the anonymous
identity and its network, the session id in a header, the routes it leaves out, the field
allowlist of its status, and its two capacity guards. The agents service is never reached
(a MockTransport records every upstream request); no test reaches a bucket or a database.
"""

import base64
import json
import logging
import re
from collections.abc import AsyncIterator
from unittest.mock import AsyncMock, patch

import httpx
import pytest
from fastapi.routing import APIRoute
from fastapi.testclient import TestClient
from starlette.requests import Request

from agents.main import ANON_PATTERN, NETWORK_PATTERN
from api.main import app, fastapi_app
from api.routers import agent, agent_public
from api.routers.agent import NOT_ENABLED, AgentContext, get_agent_client, get_case_bucket
from api.routers.agent_public import (
    ANON_ID_PATTERN,
    PUBLIC_STREAMS,
    FeedbackLimiter,
    client_network,
    get_feedback_limiter,
)
from api.routers.debug import AdminIdentity, require_admin_identity
from core.config import settings
from core.database import get_db


SERVICE_URL = "http://localhost:8001"
TAB = "3f9d6c1e-8a2b-4c7d-9e0f-1a2b3c4d5e6f"
SID = "sid-public-000000000001"
CLIENT_IP = "203.0.113.7"
HEADERS = {"X-Anyplot-Client": "agent-chat/1", "X-Anyplot-Anon": TAB, "CF-Connecting-IP": CLIENT_IP}
SESSION = {**HEADERS, "X-Anyplot-Session": SID}
CREATE = {"spec_id": "scatter-basic", "library": "matplotlib", "locale": "en"}

# Every public route with a request that passes validation, for the "closed door" sweep.
PUBLIC_ROUTES = [
    ("GET", "/agent/lane", None),
    ("GET", "/agent/status", None),
    ("GET", "/agent/eligibility?spec=scatter-basic&library=matplotlib", None),
    ("POST", "/agent/sessions", CREATE),
    ("DELETE", "/agent/session", None),
    ("POST", "/agent/session/library", {"spec_id": "scatter-basic", "library": "seaborn"}),
    ("GET", "/agent/session/memory", None),
    ("DELETE", "/agent/session/memory", None),
    ("DELETE", "/agent/session/memory/m1", None),
    ("POST", "/agent/session/dataset", {"text": "a,b\n1,2"}),
    ("POST", "/agent/session/dataset/convert", {"data_base64": base64.b64encode(b"PK\x03\x04").decode()}),
    ("PUT", "/agent/session/bindings", [{"role": "x", "column": "a"}]),
    ("PUT", "/agent/session/language", {"language": "de"}),
    ("POST", "/agent/session/dataset/confirm", None),
    ("POST", "/agent/session/dataset/undo", None),
    ("POST", "/agent/session/dataset/to_long", None),
    ("GET", "/agent/session/dataset/data.csv", None),
    ("POST", "/agent/session/messages", {"action": "create_plot"}),
    ("POST", "/agent/session/cancel", None),
    ("POST", "/agent/session/outcome", {"action": "copied_code"}),
    ("POST", "/agent/session/versions/1/render", {"theme": "dark"}),
    ("GET", "/agent/session/artifacts/plot-light.png?v=1", None),
    ("GET", "/agent/session/bundle", None),
    ("POST", "/agent/session/feedback", {"reaction": "thumbs_up", "include_data": False, "result_version": 1}),
]
ADMIN_ONLY = {
    "/debug/agent/budget",
    "/debug/agent/sessions/{sid}/dataset/copy",
    "/debug/agent/cases",
    "/debug/agent/cases/{case_id}",
    "/debug/agent/cases/{case_id}/files/{name}",
}
"""The admin lane's routes the public lane leaves out: the fan-out's copy, the day budget, the feedback triage."""


class FakeUpstream:
    """MockTransport handler that records requests and answers with `handler`."""

    def __init__(self) -> None:
        self.requests: list[httpx.Request] = []
        self.handler = lambda request: httpx.Response(200, json={})

    def __call__(self, request: httpx.Request) -> httpx.Response:
        self.requests.append(request)
        return self.handler(request)


@pytest.fixture
def agent_on(monkeypatch):
    """The master switch on and configured; the public door stays as each test sets it."""
    monkeypatch.setattr(settings, "agent_enabled", True)
    monkeypatch.setattr(settings, "agent_service_url", SERVICE_URL)
    monkeypatch.setattr(settings, "agent_user_id_key", "test-user-id-key")


@pytest.fixture
def lane_open(agent_on, monkeypatch):
    monkeypatch.setattr(settings, "agent_public_enabled", True)


@pytest.fixture
def upstream():
    fake = FakeUpstream()

    async def mock_client() -> AsyncIterator[httpx.AsyncClient]:
        async with httpx.AsyncClient(transport=httpx.MockTransport(fake)) as client:
            yield client

    fastapi_app.dependency_overrides[get_agent_client] = mock_client
    yield fake
    fastapi_app.dependency_overrides.pop(get_agent_client, None)


@pytest.fixture(autouse=True)
def isolated(monkeypatch):
    """No database, no bucket, a fresh feedback limiter and no open stream for every test.

    In CI the test job exports the production `DATABASE_URL`, so a route that takes the
    database without these overrides would open a session there.
    """

    async def mock_get_db():
        yield AsyncMock()

    async def no_engine() -> None:
        raise AssertionError("router tests must never build an engine")

    monkeypatch.setattr("core.database.connection.init_db", no_engine)
    limiter = FeedbackLimiter()
    fastapi_app.dependency_overrides[get_db] = mock_get_db
    fastapi_app.dependency_overrides[get_feedback_limiter] = lambda: limiter
    fastapi_app.dependency_overrides[get_case_bucket] = lambda: AsyncMock()
    PUBLIC_STREAMS.open = 0
    with patch("api.dependencies.is_db_configured", return_value=True):
        yield limiter
    fastapi_app.dependency_overrides.clear()


@pytest.fixture
def client(lane_open, upstream):
    return TestClient(app)


def _call(client: TestClient, method: str, path: str, body, headers: dict[str, str]) -> httpx.Response:
    return client.request(method, path, json=body, headers=headers)


class TestDoor:
    @pytest.mark.parametrize(("method", "path", "body"), PUBLIC_ROUTES)
    def test_every_route_answers_404_while_the_door_is_closed(self, agent_on, upstream, method, path, body) -> None:
        response = _call(TestClient(app), method, path, body, SESSION)

        assert response.status_code == 404
        assert response.json() == {"detail": NOT_ENABLED}
        assert upstream.requests == []

    def test_the_master_switch_closes_the_door_too(self, lane_open, upstream, monkeypatch) -> None:
        monkeypatch.setattr(settings, "agent_enabled", False)

        assert TestClient(app).get("/agent/lane").status_code == 404

    def test_in_production_the_door_needs_the_origin_gate(self, lane_open, upstream, monkeypatch) -> None:
        """The per-IP limits trust CF-Connecting-IP, which only the origin gate keeps honest."""
        monkeypatch.setattr(settings, "environment", "production")
        monkeypatch.setattr(settings, "origin_secret", None)
        assert TestClient(app).get("/agent/lane").status_code == 404

        monkeypatch.setattr(settings, "origin_secret", "edge-secret")
        armed = TestClient(app).get("/agent/lane", headers={"X-Origin-Secret": "edge-secret"})
        assert armed.status_code == 200 and armed.json() == {"open": True}

    def test_lane_says_open_without_an_identity_or_an_upstream_call(self, client, upstream) -> None:
        response = client.get("/agent/lane")

        assert response.status_code == 200 and response.json() == {"open": True}
        assert response.headers["Cache-Control"] == "public, max-age=60"
        assert upstream.requests == []

    def test_the_admin_lane_stays_open_while_the_public_door_is_closed(self, agent_on, upstream) -> None:
        upstream.handler = lambda request: httpx.Response(200, json={"libraries": ["matplotlib"]})
        fastapi_app.dependency_overrides[require_admin_identity] = lambda: AdminIdentity(
            email="admin@example.com", via="cf_access"
        )

        response = TestClient(app).get("/debug/agent/status")

        assert response.status_code == 200
        assert upstream.requests[0].headers["X-Anyplot-Tier"] == "admin"


class TestIdentity:
    @pytest.mark.parametrize("anon", [None, "", "short", "x" * 65, "has space in it, no thanks", "a.b/c" * 6])
    def test_a_request_without_a_tab_id_is_refused(self, client, upstream, anon) -> None:
        headers = {key: value for key, value in HEADERS.items() if key != "X-Anyplot-Anon"}
        if anon is not None:
            headers["X-Anyplot-Anon"] = anon

        response = client.get("/agent/status", headers=headers)

        assert response.status_code == 400 and response.json() == {"detail": "anon_required"}
        assert upstream.requests == []

    def test_upstream_gets_the_tab_id_the_network_and_the_public_tier(self, client, upstream) -> None:
        client.get("/agent/status", headers=HEADERS)

        sent = upstream.requests[0].headers
        assert (sent["X-Anyplot-Anon"], sent["X-Anyplot-Network"], sent["X-Anyplot-Tier"]) == (TAB, CLIENT_IP, "public")
        assert "X-Anyplot-User" not in sent

    @pytest.mark.parametrize(
        ("headers", "network"),
        [
            ({"cf-connecting-ip": "203.0.113.7"}, "203.0.113.7"),
            ({"cf-connecting-ip": "2001:db8:1:2:aaaa:bbbb:cccc:dddd"}, "2001:db8:1:2::/64"),
            ({"cf-connecting-ip": "2001:DB8:1:2::1"}, "2001:db8:1:2::/64"),
            ({"cf-connecting-ip": "::ffff:192.0.2.1"}, "192.0.2.1"),
            ({"cf-connecting-ip": "not-an-address"}, "unknown"),
            ({"x-forwarded-for": "198.51.100.1, 192.0.2.9"}, "192.0.2.9"),
        ],
    )
    def test_the_network_is_the_ipv4_address_or_the_ipv6_64(self, headers, network) -> None:
        scope = {
            "type": "http",
            "headers": [(key.encode(), value.encode()) for key, value in headers.items()],
            "client": ("10.0.0.1", 1234),
        }

        assert client_network(Request(scope)) == network
        assert re.fullmatch(NETWORK_PATTERN, network)  # what the agents service accepts

    def test_the_tab_id_patterns_agree_with_the_agents_service(self) -> None:
        assert ANON_ID_PATTERN == ANON_PATTERN


class TestRoutes:
    def test_the_session_id_travels_in_a_header_never_in_the_url(self, client, upstream) -> None:
        response = client.post("/agent/session/dataset", json={"text": "a,b\n1,2"}, headers=SESSION)

        assert response.status_code == 200
        assert SID not in str(response.request.url)
        assert upstream.requests[0].url.path == f"/v1/sessions/{SID}/dataset"

    def test_a_session_route_without_the_session_header_is_refused(self, client, upstream) -> None:
        response = client.post("/agent/session/dataset/confirm", headers=HEADERS)

        assert response.status_code == 422
        assert upstream.requests == []

    def test_a_session_opens_for_the_tab_id_and_never_as_a_fanout(self, client, upstream) -> None:
        roles = [{"name": "x", "kinds": ["numeric"], "required": True, "variadic": False, "description": "x"}]
        upstream.handler = lambda request: httpx.Response(
            200, json={"session_id": SID, "eligibility": {}, "roles": roles}
        )
        with patch("api.routers.agent.load_catalogue_snapshot", AsyncMock(return_value=_snapshot())):
            opened = client.post("/agent/sessions", json=CREATE, headers=HEADERS)
            fanout = client.post("/agent/sessions", json={**CREATE, "source": "fanout"}, headers=HEADERS)

        assert opened.status_code == 200 and opened.json()["session_id"] == SID
        assert opened.json()["roles"] == roles  # the spec's roles, for the header's columns ⓘ
        sent = json.loads(upstream.requests[0].content)
        assert sent["user"] == TAB and "source" not in sent
        assert fanout.status_code == 422 and len(upstream.requests) == 1

    @pytest.mark.parametrize(
        ("method", "path"),
        [
            ("GET", "/agent/budget"),
            ("GET", "/agent/cases"),
            ("POST", "/agent/session/dataset/copy"),
            ("POST", "/agent/sessions/abc/dataset/copy"),
        ],
    )
    def test_the_admin_only_routes_do_not_exist(self, client, upstream, method, path) -> None:
        response = client.request(method, path, json={"from_session": "abc"}, headers=SESSION)

        assert response.status_code in (404, 405)
        assert upstream.requests == []

    def test_every_admin_route_is_decided_for_the_public_lane(self) -> None:
        """A new admin route fails here until it is mapped onto the public lane or named admin-only."""
        admin = {
            (method, route.path)
            for route in agent.router.routes
            if isinstance(route, APIRoute)
            for method in route.methods
        }
        public = {
            (method, route.path)
            for route in agent_public.router.routes
            if isinstance(route, APIRoute)
            for method in route.methods
        }
        mapped = {
            (method, path.replace("/debug/agent/sessions/{sid}", "/agent/session").replace("/debug/agent", "/agent"))
            for method, path in admin
            if path not in ADMIN_ONLY
        }

        assert public - {("GET", "/agent/lane")} == mapped

    def test_eligibility_is_the_same_for_everyone_so_browsers_keep_it(self, client, upstream) -> None:
        upstream.handler = lambda request: httpx.Response(200, json={"eligible": True, "status": "clean"})

        response = client.get("/agent/eligibility?spec=scatter-basic&library=matplotlib", headers=HEADERS)

        assert response.status_code == 200 and response.json()["eligible"] is True
        assert response.headers["Cache-Control"] == "public, max-age=300"
        assert upstream.requests[0].url.path == "/v1/eligibility"

    def test_status_passes_only_the_named_fields(self, client, upstream) -> None:
        upstream.handler = lambda request: httpx.Response(
            200, json={"libraries": ["matplotlib"], "paused": False, "waiting": 1, "users_today": 7}
        )

        response = client.get("/agent/status", headers=HEADERS)

        assert response.json() == {"libraries": ["matplotlib"], "paused": False, "waiting": 1, "enabled": True}

    def test_a_state_change_needs_the_client_header(self, client, upstream) -> None:
        headers = {key: value for key, value in SESSION.items() if key != "X-Anyplot-Client"}

        response = client.post("/agent/session/dataset/confirm", headers=headers)

        assert response.status_code == 403 and response.json() == {"detail": "client_header_required"}
        assert upstream.requests == []


class TestCapacity:
    def test_a_turn_past_the_instances_stream_cap_never_reaches_upstream(self, client, upstream, monkeypatch) -> None:
        monkeypatch.setattr(settings, "agent_public_max_streams", 0)

        response = client.post("/agent/session/messages", json={"action": "create_plot"}, headers=SESSION)

        assert response.status_code == 503
        assert response.json()["detail"] == "capacity"
        assert upstream.requests == [] and PUBLIC_STREAMS.open == 0

    def test_a_turn_holds_its_slot_until_the_stream_ends(self, client, upstream) -> None:
        seen: list[int] = []

        def handler(request: httpx.Request) -> httpx.Response:
            seen.append(PUBLIC_STREAMS.open)
            body = 'event: ready\ndata: {"v": 1, "run_id": "r"}\n\nevent: done\ndata: {}\n\n'
            return httpx.Response(200, text=body, headers={"Content-Type": "text/event-stream"})

        upstream.handler = handler

        response = client.post("/agent/session/messages", json={"action": "create_plot"}, headers=SESSION)

        assert response.status_code == 200
        assert [line for line in response.text.splitlines() if line.startswith("event:")] == [
            "event: ready",
            "event: done",
        ]
        assert seen == [1] and PUBLIC_STREAMS.open == 0
        assert upstream.requests[0].url.path == f"/v1/sessions/{SID}/messages"


class TestFeedback:
    BODY = {"reaction": "thumbs_up", "include_data": False, "result_version": 1}

    def test_a_network_past_its_hourly_cases_is_refused_before_the_bundle(
        self, client, upstream, isolated, monkeypatch
    ) -> None:
        monkeypatch.setattr(settings, "agent_public_feedback_per_hour", 1)
        stored = AsyncMock(return_value={"case_id": "c1", "stored": []})
        with patch("api.routers.agent.submit_feedback", stored):
            first = client.post("/agent/session/feedback", json=self.BODY, headers=SESSION)
            second = client.post("/agent/session/feedback", json=self.BODY, headers=SESSION)
            other = client.post(
                "/agent/session/feedback", json=self.BODY, headers={**SESSION, "CF-Connecting-IP": "198.51.100.1"}
            )

        assert first.status_code == 201 and other.status_code == 201
        assert second.status_code == 429 and second.json()["detail"] == "rate_limited"
        assert stored.await_count == 2

    def test_a_stored_case_never_records_the_tab_id(self, client, upstream) -> None:
        stored = AsyncMock(return_value={"case_id": "c1", "stored": []})
        with patch("api.routers.agent.submit_feedback", stored):
            client.post("/agent/session/feedback", json=self.BODY, headers=SESSION)

        ctx: AgentContext = stored.await_args.args[2]
        assert ctx.user_id == TAB  # what goes upstream, where the agents service salts it
        assert ctx.case_user is not None and ctx.case_user.startswith("pub_") and TAB not in ctx.case_user

    def test_the_limiter_forgets_a_network_after_the_window(self) -> None:
        now = [0.0]
        limiter = FeedbackLimiter(window_s=60.0, clock=lambda: now[0])
        assert limiter.allow("192.0.2.1")
        now[0] = 61.0

        assert limiter.allow("192.0.2.2") and len(limiter.sent) == 1  # the first network's empty window is gone


def test_an_unreachable_upstream_is_logged_without_the_session_id(caplog) -> None:
    ctx = AgentContext(base_url=SERVICE_URL, user_id=TAB, request_id="ref-1", network=CLIENT_IP)
    with caplog.at_level(logging.WARNING, logger="api.routers.agent"):
        agent._log_unreachable(ctx, "POST", f"/sessions/{SID}/messages", httpx.ConnectError("down"))

    assert SID not in caplog.text and "/sessions/{sid}/messages" in caplog.text


def _snapshot() -> agent.CatalogueSnapshot:
    return agent.CatalogueSnapshot(
        spec_id="scatter-basic",
        title="Basic Scatter Plot",
        description="A scatter plot.",
        data_roles=["x (numeric)", "y (numeric)"],
        notes=[],
        code="x = 1\n",
        library_version="3.10.0",
    )
