"""
Tests for api/routers/agent.py — the admin-only agent chat BFF under /debug/agent.

The agents service is never reached: `get_agent_client` is overridden with an
httpx client on a MockTransport that records every upstream request.
"""

import asyncio
import hashlib
import hmac
import json
from collections.abc import AsyncIterator, Callable
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest
from fastapi.testclient import TestClient

from api.dependencies import require_db
from api.main import app, fastapi_app
from api.routers.agent import MAX_DATASET_BYTES, NOT_ENABLED, derive_user_id, get_agent_client, load_catalogue_snapshot
from api.routers.debug import AdminIdentity, require_admin_identity
from core.config import settings


SERVICE_URL = "http://localhost:8001"
KEY = "test-user-id-key"
ADMIN = AdminIdentity(email="admin@example.com", via="cf_access")
CLIENT_HEADERS = {"X-Anyplot-Client": "agent-chat/1"}


class FakeUpstream:
    """MockTransport handler that records requests and answers with `handler`."""

    def __init__(self) -> None:
        self.requests: list[httpx.Request] = []
        self.handler: Callable[[httpx.Request], httpx.Response] = lambda request: httpx.Response(200, json={})

    def __call__(self, request: httpx.Request) -> httpx.Response:
        self.requests.append(request)
        return self.handler(request)

    @property
    def last_json(self):
        return json.loads(self.requests[-1].content)


@pytest.fixture
def agent_on(monkeypatch):
    """The feature switched on and fully configured, pointing at localhost."""
    monkeypatch.setattr(settings, "agent_enabled", True)
    monkeypatch.setattr(settings, "agent_service_url", SERVICE_URL)
    monkeypatch.setattr(settings, "agent_user_id_key", KEY)


@pytest.fixture
def upstream():
    """A recording upstream, wired in through the `get_agent_client` override."""
    fake = FakeUpstream()

    async def mock_client() -> AsyncIterator[httpx.AsyncClient]:
        async with httpx.AsyncClient(transport=httpx.MockTransport(fake)) as client:
            yield client

    fastapi_app.dependency_overrides[get_agent_client] = mock_client
    yield fake
    fastapi_app.dependency_overrides.pop(get_agent_client, None)


@pytest.fixture
def client(agent_on, upstream):
    """Admin-authenticated client (gate overridden) with the feature on."""
    fastapi_app.dependency_overrides[require_admin_identity] = lambda: ADMIN
    yield TestClient(app)
    fastapi_app.dependency_overrides.clear()


def _make_spec(impls):
    spec = MagicMock()
    spec.id = "scatter-basic"
    spec.title = "Basic Scatter Plot"
    spec.description = "A scatter plot."
    spec.data = ["x (numeric): horizontal position", "y (numeric): vertical position"]
    spec.notes = ["Use transparency for overlap"]
    spec.impls = impls
    return spec


def _make_impl(library_id="matplotlib", code="import numpy as np  # noqa: F401\nx = 1\n", library_version="3.10.0"):
    impl = MagicMock()
    impl.library_id = library_id
    impl.code = code
    impl.library_version = library_version
    return impl


@pytest.fixture
def db_with_spec():
    """`require_db` overridden; the spec repository returns one spec with a matplotlib impl."""
    fastapi_app.dependency_overrides[require_db] = lambda: AsyncMock()
    repo = MagicMock()
    repo.get_by_id_with_code = AsyncMock(return_value=_make_spec([_make_impl()]))
    with patch("api.routers.agent.SpecRepository", return_value=repo):
        yield repo
    fastapi_app.dependency_overrides.pop(require_db, None)


def _sse_events(body: str) -> list[tuple[str, dict]]:
    """Parse an SSE body into (event, data) pairs, skipping keep-alive comments."""
    events = []
    for block in body.split("\n\n"):
        lines = [line for line in block.splitlines() if line and not line.startswith(":")]
        if not lines:
            continue
        event = next(line.removeprefix("event: ") for line in lines if line.startswith("event: "))
        data = "\n".join(line.removeprefix("data: ") for line in lines if line.startswith("data: "))
        events.append((event, json.loads(data)))
    return events


# Every route with a request that passes validation, for the "all dark" sweep.
ALL_ROUTES = [
    ("GET", "/debug/agent/status", None),
    ("GET", "/debug/agent/eligibility?spec=scatter-basic&library=matplotlib", None),
    ("POST", "/debug/agent/sessions", {"spec_id": "scatter-basic", "library": "matplotlib", "locale": "en"}),
    ("POST", "/debug/agent/sessions/s1/library", {"spec_id": "scatter-basic", "library": "seaborn"}),
    ("POST", "/debug/agent/sessions/s1/dataset", {"text": "a,b\n1,2\n"}),
    ("PUT", "/debug/agent/sessions/s1/bindings", [{"role": "x", "column": "a"}]),
    ("POST", "/debug/agent/sessions/s1/messages", {"action": "create_plot"}),
    ("POST", "/debug/agent/sessions/s1/cancel", None),
    ("GET", "/debug/agent/sessions/s1/artifacts/plot-light.png", None),
    ("DELETE", "/debug/agent/sessions/s1", None),
]


class TestGateAndKillSwitch:
    def test_401_without_auth_even_when_disabled(self, upstream) -> None:
        """The admin gate answers before the kill switch: the deploy smoke reads 401."""
        with patch.object(settings, "admin_token", "supersecret"), patch.object(settings, "agent_enabled", False):
            response = TestClient(app).get("/debug/agent/status")
        assert response.status_code == 401
        assert upstream.requests == []

    def test_401_without_auth_when_enabled(self, agent_on, upstream) -> None:
        with patch.object(settings, "admin_token", "supersecret"):
            response = TestClient(app).get("/debug/agent/status", headers={"X-Admin-Token": "wrong"})
        assert response.status_code == 401
        assert upstream.requests == []

    def test_real_token_gate_passes_through(self, agent_on, upstream) -> None:
        """With the real gate, a correct admin token reaches upstream under the token user id."""
        upstream.handler = lambda request: httpx.Response(200, json={"libraries": ["matplotlib"]})
        with patch.object(settings, "admin_token", "supersecret"):
            response = TestClient(app).get("/debug/agent/status", headers={"X-Admin-Token": "supersecret"})
        assert response.status_code == 200
        token_user = derive_user_id(KEY.encode(), AdminIdentity(email=None, via="token"))
        assert upstream.requests[0].headers["X-Anyplot-User"] == token_user

    @pytest.mark.parametrize(("method", "path", "body"), ALL_ROUTES)
    def test_every_route_404_when_disabled(self, client, upstream, monkeypatch, method, path, body) -> None:
        monkeypatch.setattr(settings, "agent_enabled", False)
        response = client.request(method, path, json=body, headers=CLIENT_HEADERS)
        assert response.status_code == 404
        assert response.json() == {"detail": NOT_ENABLED}
        assert upstream.requests == []

    @pytest.mark.parametrize("unset", ["agent_service_url", "agent_user_id_key"])
    def test_404_when_enabled_but_unconfigured(self, client, upstream, monkeypatch, unset) -> None:
        monkeypatch.setattr(settings, unset, None)
        response = client.get("/debug/agent/status")
        assert response.status_code == 404
        assert response.json() == {"detail": NOT_ENABLED}
        assert upstream.requests == []


class TestCsrf:
    BODY = {"spec_id": "scatter-basic", "library": "matplotlib", "locale": "en"}

    def test_403_without_client_header(self, client, upstream, db_with_spec) -> None:
        response = client.post("/debug/agent/sessions", json=self.BODY)
        assert response.status_code == 403
        assert response.json() == {"detail": "client_header_required"}
        assert upstream.requests == []

    def test_403_with_wrong_client_header(self, client, upstream, db_with_spec) -> None:
        response = client.post("/debug/agent/sessions", json=self.BODY, headers={"X-Anyplot-Client": "agent-chat/2"})
        assert response.status_code == 403

    @pytest.mark.parametrize("origin", ["https://evil.example", "null", "http://localhost.evil.example:3000"])
    def test_403_with_foreign_origin(self, client, upstream, db_with_spec, origin) -> None:
        response = client.post("/debug/agent/sessions", json=self.BODY, headers={**CLIENT_HEADERS, "Origin": origin})
        assert response.status_code == 403
        assert response.json() == {"detail": "origin_not_allowed"}
        assert upstream.requests == []

    @pytest.mark.parametrize("origin", ["https://anyplot.ai", "http://localhost:3000", "http://localhost:5199"])
    def test_allowed_origins_pass(self, client, upstream, db_with_spec, origin) -> None:
        response = client.post("/debug/agent/sessions", json=self.BODY, headers={**CLIENT_HEADERS, "Origin": origin})
        assert response.status_code == 200

    def test_403_for_non_json_body(self, client, upstream, db_with_spec) -> None:
        response = client.post(
            "/debug/agent/sessions",
            content=json.dumps(self.BODY),
            headers={**CLIENT_HEADERS, "Content-Type": "text/plain"},
        )
        assert response.status_code == 403
        assert response.json() == {"detail": "json_required"}

    def test_json_with_charset_passes(self, client, upstream, db_with_spec) -> None:
        response = client.post(
            "/debug/agent/sessions",
            content=json.dumps(self.BODY),
            headers={**CLIENT_HEADERS, "Content-Type": "application/json; charset=utf-8"},
        )
        assert response.status_code == 200

    def test_request_id_is_readable_cross_origin(self, client, upstream) -> None:
        """The dev app on another port can read the reference id the BFF returns."""
        response = client.get("/debug/agent/status", headers={"Origin": "http://localhost:3000"})
        assert "x-request-id" in response.headers["access-control-expose-headers"].lower()

    def test_delete_needs_client_header_but_no_content_type(self, client, upstream) -> None:
        assert client.delete("/debug/agent/sessions/s1").status_code == 403
        response = client.delete("/debug/agent/sessions/s1", headers=CLIENT_HEADERS)
        assert response.status_code == 204
        assert upstream.requests[-1].method == "DELETE"

    def test_get_needs_no_client_header(self, client, upstream) -> None:
        assert client.get("/debug/agent/status").status_code == 200


class TestIdentity:
    def test_user_id_is_stable_and_keyed(self) -> None:
        first = derive_user_id(b"key-a", ADMIN)
        assert first == derive_user_id(b"key-a", ADMIN)
        assert first.startswith("adm_") and len(first) == 20
        assert first != derive_user_id(b"key-b", ADMIN)
        assert first != derive_user_id(b"key-a", AdminIdentity(email="other@example.com", via="cf_access"))
        expected = "adm_" + hmac.new(b"key-a", b"admin@example.com", hashlib.sha256).hexdigest()[:16]
        assert first == expected

    def test_token_path_shares_one_id(self) -> None:
        token = AdminIdentity(email=None, via="token")
        assert derive_user_id(b"k", token) == "adm_" + hmac.new(b"k", b"token", hashlib.sha256).hexdigest()[:16]

    def test_upstream_headers_and_request_id(self, client, upstream) -> None:
        response = client.get("/debug/agent/status")
        sent = upstream.requests[0]
        assert str(sent.url) == f"{SERVICE_URL}/v1/status"
        assert sent.headers["X-Anyplot-User"] == derive_user_id(KEY.encode(), ADMIN)
        assert sent.headers["X-Request-Id"] == response.headers["X-Request-Id"]
        assert "Authorization" not in sent.headers  # localhost: no ID token
        assert response.headers["Cache-Control"] == "private, no-store"

    def test_id_token_for_remote_service(self, client, upstream, monkeypatch) -> None:
        monkeypatch.setattr(settings, "agent_service_url", "https://anyplot-agents-abc.a.run.app/")
        with patch("api.routers.agent._fetch_id_token", return_value="id-token") as fetch:
            client.get("/debug/agent/status")
        fetch.assert_called_once_with("https://anyplot-agents-abc.a.run.app")
        assert upstream.requests[0].headers["Authorization"] == "Bearer id-token"
        assert str(upstream.requests[0].url) == "https://anyplot-agents-abc.a.run.app/v1/status"

    def test_id_token_failure_is_upstream_error(self, client, upstream, monkeypatch) -> None:
        from google.auth.exceptions import DefaultCredentialsError

        monkeypatch.setattr(settings, "agent_service_url", "https://anyplot-agents-abc.a.run.app")
        with patch("api.routers.agent._fetch_id_token", side_effect=DefaultCredentialsError("no adc")):
            response = client.get("/debug/agent/status")
        assert response.status_code == 502
        assert response.json() == {"detail": "upstream", "ref": response.headers["X-Request-Id"]}
        assert upstream.requests == []


class TestRequireAdminIdentity:
    def test_jwt_path_returns_email(self) -> None:
        with (
            patch.object(settings, "admin_allowed_emails", ["admin@example.com"]),
            patch("api.routers.debug._verify_cf_access_jwt", return_value="admin@example.com"),
        ):
            identity = require_admin_identity(x_admin_token=None, cf_access_jwt="any.jwt")
        assert identity == AdminIdentity(email="admin@example.com", via="cf_access")

    def test_token_path_returns_token_identity(self) -> None:
        with patch.object(settings, "admin_token", "supersecret"):
            identity = require_admin_identity(x_admin_token="supersecret", cf_access_jwt=None)
        assert identity == AdminIdentity(email=None, via="token")


class TestSnapshot:
    async def test_snapshot_from_repository(self) -> None:
        repo = MagicMock()
        repo.get_by_id_with_code = AsyncMock(return_value=_make_spec([_make_impl(), _make_impl("seaborn", "y = 2")]))
        with patch("api.routers.agent.SpecRepository", return_value=repo):
            snapshot = await load_catalogue_snapshot(AsyncMock(), "scatter-basic", "matplotlib")
        assert snapshot is not None
        assert snapshot.model_dump() == {
            "spec_id": "scatter-basic",
            "title": "Basic Scatter Plot",
            "description": "A scatter plot.",
            "data_roles": ["x (numeric): horizontal position", "y (numeric): vertical position"],
            "notes": ["Use transparency for overlap"],
            "code": "import numpy as np\nx = 1\n",
            "library_version": "3.10.0",
        }
        repo.get_by_id_with_code.assert_awaited_once_with("scatter-basic")

    @pytest.mark.parametrize("spec", [None, _make_spec([_make_impl("seaborn")]), _make_spec([_make_impl(code=None)])])
    async def test_missing_spec_or_impl_or_code(self, spec) -> None:
        repo = MagicMock()
        repo.get_by_id_with_code = AsyncMock(return_value=spec)
        with patch("api.routers.agent.SpecRepository", return_value=repo):
            assert await load_catalogue_snapshot(AsyncMock(), "scatter-basic", "matplotlib") is None

    def test_create_session_forwards_only_allowlisted_fields(self, client, upstream, db_with_spec) -> None:
        upstream.handler = lambda request: httpx.Response(200, json={"session_id": "s1", "eligibility": "clean"})
        response = client.post(
            "/debug/agent/sessions",
            json={"spec_id": "scatter-basic", "library": "matplotlib", "locale": "de-CH"},
            headers=CLIENT_HEADERS,
        )
        assert response.status_code == 200
        assert response.json() == {"session_id": "s1", "eligibility": "clean"}
        sent = upstream.last_json
        assert set(sent) == {"user", "spec_id", "library", "locale", "snapshot"}
        assert sent["user"] == derive_user_id(KEY.encode(), ADMIN)
        assert sent["locale"] == "de-CH"
        assert sent["snapshot"]["code"] == "import numpy as np\nx = 1\n"

    def test_create_session_404_without_snapshot(self, client, upstream, db_with_spec) -> None:
        db_with_spec.get_by_id_with_code.return_value = None
        response = client.post(
            "/debug/agent/sessions",
            json={"spec_id": "nope", "library": "matplotlib", "locale": "en"},
            headers=CLIENT_HEADERS,
        )
        assert response.status_code == 404
        assert response.json()["detail"] == "not_found"
        assert upstream.requests == []

    def test_switch_library_sends_fresh_snapshot(self, client, upstream, db_with_spec) -> None:
        db_with_spec.get_by_id_with_code.return_value = _make_spec([_make_impl("seaborn", "sns = 1")])
        response = client.post(
            "/debug/agent/sessions/s1/library",
            json={"spec_id": "scatter-basic", "library": "seaborn"},
            headers=CLIENT_HEADERS,
        )
        assert response.status_code == 200
        assert str(upstream.requests[0].url) == f"{SERVICE_URL}/v1/sessions/s1/library"
        assert upstream.last_json["library"] == "seaborn"
        assert upstream.last_json["snapshot"]["code"] == "sns = 1"


class TestBodies:
    @pytest.mark.parametrize(
        "body",
        [
            {"spec_id": "Scatter_Basic", "library": "matplotlib", "locale": "en"},
            {"spec_id": "scatter-basic", "library": "excel", "locale": "en"},
            {"spec_id": "scatter-basic", "library": "matplotlib", "locale": "en-US-x-private-way-too-long"},
            {"spec_id": "scatter-basic", "library": "matplotlib", "locale": "en", "user": "adm_forged"},
        ],
    )
    def test_session_body_validation(self, client, upstream, db_with_spec, body) -> None:
        response = client.post("/debug/agent/sessions", json=body, headers=CLIENT_HEADERS)
        assert response.status_code == 422
        assert upstream.requests == []

    def test_dataset_at_limit_is_forwarded(self, client, upstream) -> None:
        text = "a" * MAX_DATASET_BYTES
        response = client.post("/debug/agent/sessions/s1/dataset", json={"text": text}, headers=CLIENT_HEADERS)
        assert response.status_code == 200
        assert upstream.last_json == {"text": text}

    def test_dataset_over_limit_is_413(self, client, upstream) -> None:
        response = client.post(
            "/debug/agent/sessions/s1/dataset", json={"text": "a" * (MAX_DATASET_BYTES + 1)}, headers=CLIENT_HEADERS
        )
        assert response.status_code == 413
        assert response.json()["detail"] == "too_long"
        assert upstream.requests == []

    def test_dataset_limit_counts_utf8_bytes(self, client, upstream) -> None:
        text = "ä" * (MAX_DATASET_BYTES // 2 + 1)  # two bytes each
        response = client.post("/debug/agent/sessions/s1/dataset", json={"text": text}, headers=CLIENT_HEADERS)
        assert response.status_code == 413

    @pytest.mark.parametrize(
        ("method", "path", "raw_body"),
        [
            ("POST", "/debug/agent/sessions/s1/dataset", '{"text": "a\\ud800b"}'),
            ("POST", "/debug/agent/sessions/s1/messages", '{"text": "a\\ud800b"}'),
            ("PUT", "/debug/agent/sessions/s1/bindings", '[{"role": "x", "column": "a\\ud800b"}]'),
        ],
    )
    def test_lone_surrogate_never_reaches_upstream(self, client, upstream, method, path, raw_body) -> None:
        """JSON allows `"\\ud800"`, UTF-8 cannot carry it; Pydantic refuses it on every
        free-text field. (FastAPI's default 422 body echoes the input and cannot render
        a lone surrogate, so today's answer is a 500 — app-wide, not this router's.)"""
        response = TestClient(app, raise_server_exceptions=False).request(
            method, path, content=raw_body, headers={**CLIENT_HEADERS, "Content-Type": "application/json"}
        )
        assert response.status_code in (422, 500)
        assert upstream.requests == []

    def test_message_over_limit_is_413(self, client, upstream) -> None:
        response = client.post("/debug/agent/sessions/s1/messages", json={"text": "x" * 2001}, headers=CLIENT_HEADERS)
        assert response.status_code == 413
        assert response.json()["detail"] == "too_long"
        assert upstream.requests == []

    @pytest.mark.parametrize(
        "body", [{}, {"text": "hi", "action": "create_plot"}, {"action": "delete_everything"}, {"text": ""}]
    )
    def test_message_needs_exactly_one_of_text_or_action(self, client, upstream, body) -> None:
        response = client.post("/debug/agent/sessions/s1/messages", json=body, headers=CLIENT_HEADERS)
        assert response.status_code == 422
        assert upstream.requests == []

    def test_bindings_forwarded_as_list(self, client, upstream) -> None:
        bindings = [{"role": "x", "column": "Datum"}, {"role": "hue_group", "column": None}]
        response = client.put("/debug/agent/sessions/s1/bindings", json=bindings, headers=CLIENT_HEADERS)
        assert response.status_code == 200
        assert upstream.requests[0].method == "PUT"
        assert upstream.last_json == bindings

    @pytest.mark.parametrize(
        "bindings", [[{"role": "X", "column": "a"}], [{"role": "x", "column": "c" * 65}], [{"role": "x"}] * 51]
    )
    def test_bindings_validation(self, client, upstream, bindings) -> None:
        response = client.put("/debug/agent/sessions/s1/bindings", json=bindings, headers=CLIENT_HEADERS)
        assert response.status_code == 422
        assert upstream.requests == []

    def test_session_id_pattern(self, client, upstream) -> None:
        response = client.post("/debug/agent/sessions/s.1/cancel", headers=CLIENT_HEADERS)
        assert response.status_code == 422
        assert upstream.requests == []


UPSTREAM_SSE = (
    b"event: ready\n"
    b'data: {"v": 1, "run_id": "r1"}\n'
    b"\n"
    b": ping\n"
    b"\n"
    b"event: tool_call\n"
    b'data: {"name": "plot_pipeline", "args": {}}\n'
    b"\n"
    b"event: status\n"
    b'data: {"step": "adapting", "attempt": 1, "node_info": {"path": "x"}}\n'
    b"\n"
    b'data: {"text": "no event type"}\n'
    b"\n"
    b"event: message\n"
    b"data: not json\n"
    b"\n"
    b"event: error\n"
    b'data: {"code": "capacity", "ref": "upstream-ref", "error_details": "Traceback (most recent call last)"}\n'
    b"\n"
    b"event: done\n"
    b'data: {"llm_calls": 4, "tokens": 9000}\n'
    b"\n"
    b"event: message\n"
    b'data: {"text": "after done"}\n'
    b"\n"
)


class TestMessagesStream:
    def _post(self, client):
        return client.post("/debug/agent/sessions/s1/messages", json={"action": "create_plot"}, headers=CLIENT_HEADERS)

    def test_only_allowed_events_pass_in_order(self, client, upstream) -> None:
        upstream.handler = lambda request: httpx.Response(
            200, content=UPSTREAM_SSE, headers={"Content-Type": "text/event-stream"}
        )
        response = self._post(client)
        assert response.status_code == 200
        assert response.headers["content-type"].startswith("text/event-stream")
        ref = response.headers["X-Request-Id"]
        assert _sse_events(response.text) == [
            ("ready", {"v": 1, "run_id": "r1"}),
            ("status", {"step": "adapting", "attempt": 1}),
            ("error", {"code": "capacity", "ref": ref}),
            ("done", {"llm_calls": 4, "tokens": 9000}),
        ]
        sent = upstream.requests[0]
        assert str(sent.url) == f"{SERVICE_URL}/v1/sessions/s1/messages"
        assert sent.headers["Accept"] == "text/event-stream"
        assert upstream.last_json == {"action": "create_plot"}

    def test_unknown_error_code_becomes_internal(self, client, upstream) -> None:
        upstream.handler = lambda request: httpx.Response(
            200, content=b'event: error\ndata: {"code": "KeyError: secret"}\n\nevent: done\ndata: {}\n\n'
        )
        events = _sse_events(self._post(client).text)
        assert events[0] == ("error", {"code": "internal", "ref": events[0][1]["ref"]})

    def test_text_message_forwarded(self, client, upstream) -> None:
        upstream.handler = lambda request: httpx.Response(200, content=b"event: done\ndata: {}\n\n")
        client.post("/debug/agent/sessions/s1/messages", json={"text": "make it blue"}, headers=CLIENT_HEADERS)
        assert upstream.last_json == {"text": "make it blue"}

    def test_connection_failure_emits_error_then_done(self, client, upstream) -> None:
        def refuse(request):
            raise httpx.ConnectError("connection refused")

        upstream.handler = refuse
        response = self._post(client)
        assert response.status_code == 200
        assert _sse_events(response.text) == [
            ("error", {"code": "upstream", "ref": response.headers["X-Request-Id"]}),
            ("done", {}),
        ]

    def test_stream_without_done_emits_error_then_done(self, client, upstream) -> None:
        upstream.handler = lambda request: httpx.Response(
            200, content=b'event: status\ndata: {"step": "rendering"}\n\n'
        )
        events = _sse_events(self._post(client).text)
        assert [event for event, _ in events] == ["status", "error", "done"]
        assert events[1][1]["code"] == "upstream"

    def test_deadline_emits_error_then_done(self, client, upstream, monkeypatch) -> None:
        monkeypatch.setattr(settings, "agent_request_timeout_s", 0.2)

        async def slow_stream():
            yield b'event: status\ndata: {"step": "adapting"}\n\n'
            await asyncio.sleep(5)
            yield b"event: done\ndata: {}\n\n"

        upstream.handler = lambda request: httpx.Response(200, content=slow_stream())
        events = _sse_events(self._post(client).text)
        assert [event for event, _ in events] == ["status", "error", "done"]

    def test_upstream_409_is_an_http_status(self, client, upstream) -> None:
        upstream.handler = lambda request: httpx.Response(409, json={"detail": "run_active"})
        response = self._post(client)
        assert response.status_code == 409
        assert response.json() == {"detail": "run_active", "ref": response.headers["X-Request-Id"]}


class TestArtifacts:
    @pytest.mark.parametrize(
        ("name", "media_type"),
        [
            ("plot-light.png", "image/png"),
            ("plot-dark.png", "image/png"),
            ("plot.py", "text/x-python; charset=utf-8"),
            ("data.csv", "text/csv; charset=utf-8"),
        ],
    )
    def test_allowlisted_artifact_streams(self, client, upstream, name, media_type) -> None:
        upstream.handler = lambda request: httpx.Response(
            200, content=b"\x89PNG-bytes", headers={"Content-Type": "text/html"}
        )
        response = client.get(f"/debug/agent/sessions/s1/artifacts/{name}?v=2")
        assert response.status_code == 200
        assert response.content == b"\x89PNG-bytes"
        assert response.headers["content-type"] == media_type
        assert response.headers["Cache-Control"] == "private, no-store"
        assert response.headers["X-Content-Type-Options"] == "nosniff"
        assert str(upstream.requests[0].url) == f"{SERVICE_URL}/v1/sessions/s1/artifacts/{name}?v=2"

    @pytest.mark.parametrize("name", ["plot.html", "secret.txt", "plot-light.PNG", "..%2Fstatus"])
    def test_other_names_are_404_without_upstream_call(self, client, upstream, name) -> None:
        response = client.get(f"/debug/agent/sessions/s1/artifacts/{name}")
        assert response.status_code == 404
        assert upstream.requests == []

    def test_missing_artifact_maps_upstream_404(self, client, upstream) -> None:
        upstream.handler = lambda request: httpx.Response(404, json={"detail": "session_expired"})
        response = client.get("/debug/agent/sessions/s1/artifacts/plot.py")
        assert response.status_code == 404
        assert response.json() == {"detail": "session_expired", "ref": response.headers["X-Request-Id"]}


class TestUpstreamMapping:
    @pytest.mark.parametrize(
        ("status", "body", "expected_status", "expected_code"),
        [
            (404, {"detail": "session_expired"}, 404, "session_expired"),
            (422, {"detail": "not_eligible"}, 422, "not_eligible"),
            (403, {"detail": "data_refused"}, 403, "data_refused"),
            (422, {"detail": "Traceback: KeyError in /app/agents/x.py"}, 422, "invalid"),
            (409, {"detail": ["run_active"]}, 409, "conflict"),
            (418, None, 418, "rejected"),
            (401, None, 502, "upstream_auth"),
            (403, None, 502, "upstream_auth"),
            (500, {"detail": "boom"}, 500, "upstream"),
            (302, None, 502, "upstream"),
        ],
    )
    def test_status_and_generic_code(self, client, upstream, status, body, expected_status, expected_code) -> None:
        upstream.handler = lambda request: (
            httpx.Response(status, json=body) if body is not None else httpx.Response(status, text="<html>")
        )
        response = client.post("/debug/agent/sessions/s1/dataset", json={"text": "a,b"}, headers=CLIENT_HEADERS)
        assert response.status_code == expected_status
        assert response.json() == {"detail": expected_code, "ref": response.headers["X-Request-Id"]}
        assert "Traceback" not in response.text

    def test_unreachable_is_502(self, client, upstream) -> None:
        def time_out(request):
            raise httpx.ReadTimeout("slow")

        upstream.handler = time_out
        response = client.get("/debug/agent/status")
        assert response.status_code == 502
        assert response.json()["detail"] == "upstream"

    def test_non_json_success_is_502(self, client, upstream) -> None:
        upstream.handler = lambda request: httpx.Response(200, text="<html>ok</html>")
        assert client.get("/debug/agent/status").status_code == 502


class TestPassThroughRoutes:
    def test_status_adds_enabled(self, client, upstream) -> None:
        upstream.handler = lambda request: httpx.Response(
            200, json={"libraries": ["matplotlib", "seaborn"], "model": "m", "enabled": False}
        )
        response = client.get("/debug/agent/status")
        assert response.status_code == 200
        assert response.json() == {"libraries": ["matplotlib", "seaborn"], "model": "m", "enabled": True}

    def test_eligibility_forwards_query(self, client, upstream) -> None:
        upstream.handler = lambda request: httpx.Response(200, json={"eligible": True})
        response = client.get("/debug/agent/eligibility?spec=scatter-basic&library=seaborn")
        assert response.json() == {"eligible": True}
        assert upstream.requests[0].url.params == httpx.QueryParams({"spec": "scatter-basic", "library": "seaborn"})

    @pytest.mark.parametrize("query", ["spec=Bad_Spec&library=seaborn", "spec=scatter-basic&library=excel", ""])
    def test_eligibility_validation(self, client, upstream, query) -> None:
        assert client.get(f"/debug/agent/eligibility?{query}").status_code == 422
        assert upstream.requests == []

    def test_cancel_is_204(self, client, upstream) -> None:
        response = client.post("/debug/agent/sessions/s1/cancel", headers=CLIENT_HEADERS)
        assert response.status_code == 204
        assert response.headers["X-Request-Id"]
        assert str(upstream.requests[0].url) == f"{SERVICE_URL}/v1/sessions/s1/cancel"
