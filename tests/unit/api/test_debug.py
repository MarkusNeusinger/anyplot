"""
Tests for api/routers/debug.py — debug status endpoint.

Covers the GET /debug/status endpoint including:
- Empty database response
- Specs with implementations (library stats, coverage)
- Low score detection
- Missing preview detection
- Missing tags detection
- Oldest specs ordering
- System health fields
"""

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from api.cache import clear_cache
from api.main import app, fastapi_app
from api.routers.debug import require_admin
from core.config import settings
from core.constants import SUPPORTED_LIBRARIES
from core.database import get_db


DB_CONFIG_PATCH = "api.dependencies.is_db_configured"


@pytest.fixture(autouse=True)
def _clear_cache():
    """Clear the global cache before each test."""
    clear_cache()


@pytest.fixture
def db_client():
    """Test client with mocked database dependency (require_db needs get_db + is_db_configured)."""
    mock_session = AsyncMock()

    async def mock_get_db():
        yield mock_session

    fastapi_app.dependency_overrides[get_db] = mock_get_db
    # Bypass admin auth in tests — require_admin behaviour is asserted separately
    # in `TestRequireAdmin` below.
    fastapi_app.dependency_overrides[require_admin] = lambda: None

    with patch(DB_CONFIG_PATCH, return_value=True):
        client = TestClient(app)
        yield client, mock_session

    fastapi_app.dependency_overrides.clear()


@pytest.fixture
def auth_client():
    """Test client WITHOUT the require_admin override — exercises the real gate.

    Used by TestRequireAdmin to assert /debug/* fail-closed behaviour.
    """
    mock_session = AsyncMock()

    async def mock_get_db():
        yield mock_session

    fastapi_app.dependency_overrides[get_db] = mock_get_db
    # NB: do NOT override require_admin — we want the real gate.

    with patch(DB_CONFIG_PATCH, return_value=True):
        client = TestClient(app)
        yield client

    fastapi_app.dependency_overrides.clear()


def _make_impl(
    library_id="matplotlib",
    language_id="python",
    quality_score=92.5,
    preview_url="https://example.com/plot.png",
    updated=None,
    generated_by=None,
    review_weaknesses=None,
):
    """Helper to create a mock implementation."""
    impl = MagicMock()
    impl.library_id = library_id
    impl.language_id = language_id
    impl.quality_score = quality_score
    impl.preview_url = preview_url
    impl.updated = updated
    impl.generated_by = generated_by
    impl.review_weaknesses = review_weaknesses or []
    return impl


def _make_spec(spec_id="scatter-basic", title="Basic Scatter Plot", impls=None, tags=None, updated=None):
    """Helper to create a mock spec."""
    spec = MagicMock()
    spec.id = spec_id
    spec.title = title
    spec.impls = impls or []
    spec.tags = tags if tags is not None else {"plot_type": ["scatter"]}
    spec.updated = updated
    return spec


class TestDebugStatus:
    """Tests for GET /debug/status endpoint."""

    def test_debug_status_empty_db(self, db_client) -> None:
        """Debug status with no specs should return zeros and empty lists."""
        client, _ = db_client

        mock_repo = MagicMock()
        mock_repo.get_all = AsyncMock(return_value=[])

        with patch("api.routers.debug.SpecRepository", return_value=mock_repo):
            response = client.get("/debug/status")

        assert response.status_code == 200
        data = response.json()
        assert data["total_specs"] == 0
        assert data["total_implementations"] == 0
        assert data["coverage_percent"] == 0
        assert data["specs"] == []
        assert data["low_score_specs"] == []
        assert data["missing_preview_specs"] == []
        assert data["missing_tags_specs"] == []
        assert data["oldest_specs"] == []
        assert len(data["library_stats"]) == len(SUPPORTED_LIBRARIES)

    def test_debug_status_with_specs_and_impls(self, db_client) -> None:
        """Debug status should compute library stats and coverage from specs/impls."""
        client, _ = db_client

        impl1 = _make_impl(library_id="matplotlib", quality_score=90.0)
        impl2 = _make_impl(library_id="seaborn", quality_score=95.0)
        spec = _make_spec(spec_id="scatter-basic", impls=[impl1, impl2])

        mock_repo = MagicMock()
        mock_repo.get_all = AsyncMock(return_value=[spec])

        with patch("api.routers.debug.SpecRepository", return_value=mock_repo):
            response = client.get("/debug/status")

        assert response.status_code == 200
        data = response.json()
        assert data["total_specs"] == 1
        assert data["total_implementations"] == 2
        # coverage = 2 / (1 * len(SUPPORTED_LIBRARIES)) * 100
        assert data["coverage_percent"] == round(2 / len(SUPPORTED_LIBRARIES) * 100, 1)

        # Check library stats
        lib_stats_by_id = {ls["id"]: ls for ls in data["library_stats"]}
        assert lib_stats_by_id["matplotlib"]["impl_count"] == 1
        assert lib_stats_by_id["matplotlib"]["avg_score"] == 90.0
        assert lib_stats_by_id["seaborn"]["impl_count"] == 1
        assert lib_stats_by_id["seaborn"]["avg_score"] == 95.0
        # Libraries with no impls should have count=0
        assert lib_stats_by_id["plotly"]["impl_count"] == 0
        assert lib_stats_by_id["plotly"]["avg_score"] is None

        # Check spec avg_score
        assert data["specs"][0]["avg_score"] == 92.5  # (90 + 95) / 2

    def test_debug_status_low_score_detection(self, db_client) -> None:
        """Specs with avg quality_score < 90 should appear in low_score_specs."""
        client, _ = db_client

        low_impl = _make_impl(library_id="matplotlib", quality_score=70.0)
        low_spec = _make_spec(spec_id="bad-chart", title="Bad Chart", impls=[low_impl])

        high_impl = _make_impl(library_id="matplotlib", quality_score=95.0)
        high_spec = _make_spec(spec_id="good-chart", title="Good Chart", impls=[high_impl])

        mock_repo = MagicMock()
        mock_repo.get_all = AsyncMock(return_value=[low_spec, high_spec])

        with patch("api.routers.debug.SpecRepository", return_value=mock_repo):
            response = client.get("/debug/status")

        data = response.json()
        low_ids = [s["id"] for s in data["low_score_specs"]]
        assert "bad-chart" in low_ids
        assert "good-chart" not in low_ids

    def test_debug_status_missing_preview(self, db_client) -> None:
        """Impls with no preview_url should appear in missing_preview_specs."""
        client, _ = db_client

        no_preview_impl = _make_impl(library_id="matplotlib", preview_url=None)
        spec = _make_spec(spec_id="no-preview", title="No Preview", impls=[no_preview_impl])

        mock_repo = MagicMock()
        mock_repo.get_all = AsyncMock(return_value=[spec])

        with patch("api.routers.debug.SpecRepository", return_value=mock_repo):
            response = client.get("/debug/status")

        data = response.json()
        assert len(data["missing_preview_specs"]) == 1
        assert data["missing_preview_specs"][0]["id"] == "no-preview"
        assert "matplotlib" in data["missing_preview_specs"][0]["issue"]

    def test_debug_status_missing_tags(self, db_client) -> None:
        """Specs with empty or missing tags should appear in missing_tags_specs."""
        client, _ = db_client

        impl = _make_impl()
        # Spec with tags that have empty values
        spec_empty_tags = _make_spec(
            spec_id="no-tags", title="No Tags", impls=[impl], tags={"plot_type": [], "domain": []}
        )
        # Spec with proper tags
        spec_with_tags = _make_spec(spec_id="has-tags", title="Has Tags", impls=[impl], tags={"plot_type": ["scatter"]})

        mock_repo = MagicMock()
        mock_repo.get_all = AsyncMock(return_value=[spec_empty_tags, spec_with_tags])

        with patch("api.routers.debug.SpecRepository", return_value=mock_repo):
            response = client.get("/debug/status")

        data = response.json()
        missing_ids = [s["id"] for s in data["missing_tags_specs"]]
        assert "no-tags" in missing_ids
        assert "has-tags" not in missing_ids

    def test_debug_status_oldest_specs(self, db_client) -> None:
        """Oldest specs should be detected from updated timestamps."""
        client, _ = db_client

        old_time = datetime(2024, 1, 1, tzinfo=timezone.utc)
        recent_time = datetime(2026, 4, 1, tzinfo=timezone.utc)

        impl_old = _make_impl(updated=old_time)
        spec_old = _make_spec(spec_id="old-spec", title="Old Spec", impls=[impl_old], updated=old_time)

        impl_new = _make_impl(updated=recent_time)
        spec_new = _make_spec(spec_id="new-spec", title="New Spec", impls=[impl_new], updated=recent_time)

        mock_repo = MagicMock()
        mock_repo.get_all = AsyncMock(return_value=[spec_old, spec_new])

        with patch("api.routers.debug.SpecRepository", return_value=mock_repo):
            response = client.get("/debug/status")

        data = response.json()
        assert len(data["oldest_specs"]) >= 1
        oldest_ids = [s["id"] for s in data["oldest_specs"]]
        assert "old-spec" in oldest_ids
        # The old spec should have "days ago" in its value
        old_entry = next(s for s in data["oldest_specs"] if s["id"] == "old-spec")
        assert "days ago" in old_entry["value"]

    def test_debug_status_daily_impls_shape(self, db_client) -> None:
        """daily_impls should always contain 30 zero-filled entries, ordered oldest → newest."""
        client, _ = db_client

        recent_time = datetime.now(timezone.utc)
        impl = _make_impl(updated=recent_time)
        spec = _make_spec(impls=[impl])

        mock_repo = MagicMock()
        mock_repo.get_all = AsyncMock(return_value=[spec])

        with patch("api.routers.debug.SpecRepository", return_value=mock_repo):
            response = client.get("/debug/status")

        data = response.json()
        assert len(data["daily_impls"]) == 30
        dates = [p["date"] for p in data["daily_impls"]]
        assert dates == sorted(dates)  # ascending
        # Today's bucket should have 1 count
        today = recent_time.date().isoformat()
        today_point = next(p for p in data["daily_impls"] if p["date"] == today)
        assert today_point["impls_updated"] == 1

    def test_debug_status_recent_activity(self, db_client) -> None:
        """recent_activity should return impls sorted by updated DESC, capped at 15,
        and surface each impl's language so the frontend can build correct deep links
        (regression: Python + R impls were both linked as /{spec}/python/{library}
        before, which sent R/ggplot2 clicks to the Python language overview).
        """
        client, _ = db_client

        older = datetime(2026, 3, 1, tzinfo=timezone.utc)
        newer = datetime(2026, 4, 20, tzinfo=timezone.utc)
        impl_py = _make_impl(library_id="matplotlib", updated=older, generated_by="claude-opus-4-6")
        impl_r = _make_impl(library_id="ggplot2", language_id="r", updated=newer, generated_by="claude-opus-4-7")
        spec = _make_spec(impls=[impl_py, impl_r])

        mock_repo = MagicMock()
        mock_repo.get_all = AsyncMock(return_value=[spec])

        with patch("api.routers.debug.SpecRepository", return_value=mock_repo):
            response = client.get("/debug/status")

        data = response.json()
        activity = data["recent_activity"]
        assert len(activity) == 2
        assert activity[0]["library_id"] == "ggplot2"
        assert activity[0]["language_id"] == "r"
        assert activity[0]["generated_by"] == "claude-opus-4-7"
        assert activity[1]["library_id"] == "matplotlib"
        assert activity[1]["language_id"] == "python"

    def test_debug_status_common_weaknesses(self, db_client) -> None:
        """common_weaknesses should aggregate review_weaknesses case-insensitively, top 10."""
        client, _ = db_client

        impl1 = _make_impl(library_id="matplotlib", review_weaknesses=["Grid too bright", "Missing legend"])
        impl2 = _make_impl(library_id="seaborn", review_weaknesses=["grid too bright", "  Missing Legend  "])
        impl3 = _make_impl(library_id="plotly", review_weaknesses=["Grid too bright"])
        spec = _make_spec(impls=[impl1, impl2, impl3])

        mock_repo = MagicMock()
        mock_repo.get_all = AsyncMock(return_value=[spec])

        with patch("api.routers.debug.SpecRepository", return_value=mock_repo):
            response = client.get("/debug/status")

        data = response.json()
        weaknesses = {w["text"]: w["count"] for w in data["common_weaknesses"]}
        assert weaknesses["grid too bright"] == 3
        assert weaknesses["missing legend"] == 2

    def test_debug_ping_returns_latency(self, db_client) -> None:
        """GET /debug/ping should report database_connected and a numeric response time."""
        client, mock_session = db_client
        mock_session.execute = AsyncMock(return_value=MagicMock())

        response = client.get("/debug/ping")

        assert response.status_code == 200
        data = response.json()
        assert data["database_connected"] is True
        assert isinstance(data["response_time_ms"], (int, float))
        assert data["response_time_ms"] >= 0
        assert data["timestamp"]

    def test_debug_ping_reports_db_failure(self, db_client) -> None:
        """If the DB query fails, ping should report database_connected=False."""
        client, mock_session = db_client
        mock_session.execute = AsyncMock(side_effect=RuntimeError("db unreachable"))

        response = client.get("/debug/ping")

        assert response.status_code == 200
        assert response.json()["database_connected"] is False

    def test_debug_status_system_health(self, db_client) -> None:
        """System health should report database_connected=True and valid fields."""
        client, _ = db_client

        mock_repo = MagicMock()
        mock_repo.get_all = AsyncMock(return_value=[])

        with patch("api.routers.debug.SpecRepository", return_value=mock_repo):
            response = client.get("/debug/status")

        data = response.json()
        system = data["system"]
        assert system["database_connected"] is True
        assert system["api_response_time_ms"] >= 0
        assert system["timestamp"]  # Non-empty ISO timestamp
        assert system["total_specs_in_db"] == 0
        assert system["total_impls_in_db"] == 0


class TestRequireAdmin:
    """Tests for the /debug/* admin auth gate (fail-closed behaviour).

    The gate (`api/routers/debug.require_admin`) protects /debug/status and
    /debug/ping behind a shared `X-Admin-Token` header. When `settings.admin_token`
    is unset the endpoints are disabled (503) so a misconfigured prod deploy
    fails closed; with the secret set, missing/wrong headers return 401.
    """

    def test_status_503_when_admin_token_unset(self, auth_client) -> None:
        """admin_token unset → 503 (disabled, fail-closed)."""
        with patch.object(settings, "admin_token", None):
            response = auth_client.get("/debug/status")
        assert response.status_code == 503
        assert "not configured" in response.json()["message"].lower()

    def test_ping_503_when_admin_token_unset(self, auth_client) -> None:
        """admin_token unset → 503 on /debug/ping too."""
        with patch.object(settings, "admin_token", None):
            response = auth_client.get("/debug/ping")
        assert response.status_code == 503

    def test_status_401_when_token_set_and_header_missing(self, auth_client) -> None:
        """admin_token set, no header → 401."""
        with patch.object(settings, "admin_token", "supersecret"):
            response = auth_client.get("/debug/status")
        assert response.status_code == 401
        assert "invalid admin token" in response.json()["message"].lower()

    def test_status_401_when_token_set_and_header_wrong(self, auth_client) -> None:
        """admin_token set, wrong header value → 401."""
        with patch.object(settings, "admin_token", "supersecret"):
            response = auth_client.get("/debug/status", headers={"X-Admin-Token": "wrong"})
        assert response.status_code == 401

    def test_status_200_when_token_set_and_header_correct(self, auth_client) -> None:
        """admin_token set, correct header → 200."""
        mock_repo = MagicMock()
        mock_repo.get_all = AsyncMock(return_value=[])
        with (
            patch.object(settings, "admin_token", "supersecret"),
            patch("api.routers.debug.SpecRepository", return_value=mock_repo),
        ):
            response = auth_client.get("/debug/status", headers={"X-Admin-Token": "supersecret"})
        assert response.status_code == 200

    def test_ping_200_when_token_set_and_header_correct(self, auth_client) -> None:
        """admin_token set, correct header → 200 on /debug/ping too."""
        with patch.object(settings, "admin_token", "supersecret"):
            response = auth_client.get("/debug/ping", headers={"X-Admin-Token": "supersecret"})
        # ping mocks the DB session (returns truthy on execute), so it should 200
        assert response.status_code == 200

    def test_cache_invalidate_unaffected_by_admin_token(self, auth_client) -> None:
        """`/debug/cache/invalidate` has its own token gate (cache_invalidate_token);
        the admin_token gate must NOT apply to it."""
        with (
            patch.object(settings, "admin_token", None),
            patch.object(settings, "cache_invalidate_token", "cachesecret"),
        ):
            # Without X-Admin-Token, cache invalidate still works given correct X-Cache-Token.
            response = auth_client.post("/debug/cache/invalidate", headers={"X-Cache-Token": "cachesecret"})
        assert response.status_code == 200


class TestRequireAdminCfAccess:
    """Tests for the Cloudflare Access JWT path of `require_admin`.

    The browser path forwards `Cf-Access-Jwt-Assertion` from the Cloudflare
    edge. We mock `_verify_cf_access_jwt` so these tests don't need a real
    RS256 signature or JWKS network round-trip.
    """

    _ALLOWED = "meakeiok@gmail.com"
    _DENIED = "stranger@example.com"

    def test_status_200_when_jwt_email_allowed(self, auth_client) -> None:
        """Valid JWT + email on allow-list → 200, no admin token needed."""
        mock_repo = MagicMock()
        mock_repo.get_all = AsyncMock(return_value=[])
        with (
            patch.object(settings, "admin_token", None),
            patch.object(settings, "admin_allowed_emails", [self._ALLOWED]),
            patch("api.routers.debug._verify_cf_access_jwt", return_value=self._ALLOWED),
            patch("api.routers.debug.SpecRepository", return_value=mock_repo),
        ):
            response = auth_client.get("/debug/status", headers={"Cf-Access-Jwt-Assertion": "any.jwt.here"})
        assert response.status_code == 200

    def test_status_403_when_jwt_email_not_allowed(self, auth_client) -> None:
        """Valid JWT but email not on allow-list → 403, no fall-through."""
        with (
            patch.object(settings, "admin_token", "supersecret"),
            patch.object(settings, "admin_allowed_emails", [self._ALLOWED]),
            patch("api.routers.debug._verify_cf_access_jwt", return_value=self._DENIED),
        ):
            response = auth_client.get("/debug/status", headers={"Cf-Access-Jwt-Assertion": "any.jwt.here"})
        assert response.status_code == 403
        assert self._DENIED in response.json()["message"]

    def test_status_503_when_jwt_invalid_and_token_unset(self, auth_client) -> None:
        """Invalid JWT + admin_token unset → falls through to 503 (fail-closed)."""
        with (
            patch.object(settings, "admin_token", None),
            patch("api.routers.debug._verify_cf_access_jwt", return_value=None),
        ):
            response = auth_client.get("/debug/status", headers={"Cf-Access-Jwt-Assertion": "garbage"})
        assert response.status_code == 503

    def test_status_200_when_jwt_invalid_but_token_correct(self, auth_client) -> None:
        """Invalid JWT + correct X-Admin-Token → 200 (break-glass fall-through)."""
        mock_repo = MagicMock()
        mock_repo.get_all = AsyncMock(return_value=[])
        with (
            patch.object(settings, "admin_token", "supersecret"),
            patch("api.routers.debug._verify_cf_access_jwt", return_value=None),
            patch("api.routers.debug.SpecRepository", return_value=mock_repo),
        ):
            response = auth_client.get(
                "/debug/status", headers={"Cf-Access-Jwt-Assertion": "garbage", "X-Admin-Token": "supersecret"}
            )
        assert response.status_code == 200


class TestJwksHelpers:
    """Direct tests for the JWKS helpers — `_jwks_client` and `_verify_cf_access_jwt`.

    The integration tests above mock `_verify_cf_access_jwt` wholesale, which
    is the right shape there but leaves the helpers themselves uncovered. These
    tests stub `pyjwt` so we can exercise every branch without needing a real
    Cloudflare Access deployment or RS256 key material.
    """

    @staticmethod
    def _reset_jwks_cache():
        from api.routers.debug import _jwks_client

        _jwks_client.cache_clear()

    def test_jwks_client_returns_none_when_team_domain_unset(self) -> None:
        """No team domain → no client (token-only mode)."""
        from api.routers.debug import _jwks_client

        self._reset_jwks_cache()
        with patch.object(settings, "cf_access_team_domain", None):
            assert _jwks_client() is None

    def test_jwks_client_constructs_with_team_domain(self) -> None:
        """Team domain set → returns a PyJWKClient pointed at /cdn-cgi/access/certs."""
        from api.routers.debug import _jwks_client

        self._reset_jwks_cache()
        sentinel = MagicMock()
        with (
            patch.object(settings, "cf_access_team_domain", "anyplot.cloudflareaccess.com"),
            patch("api.routers.debug.pyjwt.PyJWKClient", return_value=sentinel) as mock_ctor,
        ):
            result = _jwks_client()
        assert result is sentinel
        mock_ctor.assert_called_once_with("https://anyplot.cloudflareaccess.com/cdn-cgi/access/certs")
        self._reset_jwks_cache()

    def test_verify_cf_access_jwt_returns_none_when_unconfigured(self) -> None:
        """No JWKS client (team domain unset) → None, no exception."""
        from api.routers.debug import _verify_cf_access_jwt

        self._reset_jwks_cache()
        with patch.object(settings, "cf_access_team_domain", None):
            assert _verify_cf_access_jwt("some.jwt.token") is None

    def test_verify_cf_access_jwt_returns_none_when_aud_unset(self) -> None:
        """Team domain set but AUD unset → None (don't verify against missing aud)."""
        from api.routers.debug import _verify_cf_access_jwt

        self._reset_jwks_cache()
        with (
            patch.object(settings, "cf_access_team_domain", "anyplot.cloudflareaccess.com"),
            patch.object(settings, "cf_access_aud", None),
            patch("api.routers.debug.pyjwt.PyJWKClient", return_value=MagicMock()),
        ):
            assert _verify_cf_access_jwt("some.jwt.token") is None
        self._reset_jwks_cache()

    def test_verify_cf_access_jwt_returns_email_on_valid_token(self) -> None:
        """Valid signature + claims → email from `email` claim."""
        from api.routers.debug import _verify_cf_access_jwt

        self._reset_jwks_cache()
        mock_client = MagicMock()
        mock_client.get_signing_key_from_jwt.return_value = MagicMock(key="fake-key")
        with (
            patch.object(settings, "cf_access_team_domain", "anyplot.cloudflareaccess.com"),
            patch.object(settings, "cf_access_aud", "the-aud-uuid"),
            patch("api.routers.debug.pyjwt.PyJWKClient", return_value=mock_client),
            patch("api.routers.debug.pyjwt.decode", return_value={"email": "alice@example.com"}) as mock_decode,
        ):
            email = _verify_cf_access_jwt("good.jwt.token")
        assert email == "alice@example.com"
        # Confirm we passed the right audience and issuer to pyjwt.decode.
        kwargs = mock_decode.call_args.kwargs
        assert kwargs["audience"] == "the-aud-uuid"
        assert kwargs["issuer"] == "https://anyplot.cloudflareaccess.com"
        assert kwargs["algorithms"] == ["RS256"]
        self._reset_jwks_cache()

    def test_verify_cf_access_jwt_returns_none_on_pyjwt_error(self) -> None:
        """pyjwt raises (bad signature, expired, wrong aud, …) → None."""
        import jwt as pyjwt

        from api.routers.debug import _verify_cf_access_jwt

        self._reset_jwks_cache()
        mock_client = MagicMock()
        mock_client.get_signing_key_from_jwt.side_effect = pyjwt.PyJWTError("bad sig")
        with (
            patch.object(settings, "cf_access_team_domain", "anyplot.cloudflareaccess.com"),
            patch.object(settings, "cf_access_aud", "the-aud-uuid"),
            patch("api.routers.debug.pyjwt.PyJWKClient", return_value=mock_client),
        ):
            assert _verify_cf_access_jwt("bad.jwt.token") is None
        self._reset_jwks_cache()

    def test_verify_cf_access_jwt_returns_none_on_non_string_email_claim(self) -> None:
        """Defensive: claims with no email or non-str email → None."""
        from api.routers.debug import _verify_cf_access_jwt

        self._reset_jwks_cache()
        mock_client = MagicMock()
        mock_client.get_signing_key_from_jwt.return_value = MagicMock(key="fake-key")
        with (
            patch.object(settings, "cf_access_team_domain", "anyplot.cloudflareaccess.com"),
            patch.object(settings, "cf_access_aud", "the-aud-uuid"),
            patch("api.routers.debug.pyjwt.PyJWKClient", return_value=mock_client),
            patch("api.routers.debug.pyjwt.decode", return_value={"email": None}),
        ):
            assert _verify_cf_access_jwt("token") is None
        self._reset_jwks_cache()


class TestAdminAllowedEmailsParsing:
    """The admin_allowed_emails field accepts both comma-separated strings
    (operator-friendly for `.env` files) and JSON arrays (pydantic-settings
    default for list fields)."""

    def test_parses_comma_separated_string(self) -> None:
        from core.config import Settings

        s = Settings(admin_allowed_emails="a@x.com,b@y.com,  c@z.com  ")
        assert s.admin_allowed_emails == ["a@x.com", "b@y.com", "c@z.com"]

    def test_parses_json_array(self) -> None:
        from core.config import Settings

        s = Settings(admin_allowed_emails='["a@x.com","b@y.com"]')
        assert s.admin_allowed_emails == ["a@x.com", "b@y.com"]

    def test_empty_string_yields_empty_list(self) -> None:
        from core.config import Settings

        s = Settings(admin_allowed_emails="")
        assert s.admin_allowed_emails == []

    def test_default_is_empty_list(self) -> None:
        """Defaulting to an empty list prevents accidental authorization if the
        operator forgets to configure ADMIN_ALLOWED_EMAILS in production."""
        from core.config import Settings

        s = Settings()
        assert s.admin_allowed_emails == []


class TestFeedbackDebugEndpoints:
    """Coverage for /debug/feedback/* — analytics + triage (issue #5662 follow-up)."""

    def test_top_pages_rejects_invalid_reaction(self, db_client) -> None:
        client, _ = db_client
        response = client.get("/debug/feedback/top?reaction=fire")
        assert response.status_code == 400

    def test_top_pages_rejects_out_of_range_limit(self, db_client) -> None:
        client, _ = db_client
        response = client.get("/debug/feedback/top?reaction=thumbs_up&limit=999")
        assert response.status_code == 400

    def test_top_pages_returns_grouped_counts(self, db_client) -> None:
        client, _ = db_client
        repo = MagicMock()
        repo.top_paths_by_reaction = AsyncMock(
            return_value=[
                {"path": "/scatter-basic", "count": 7, "last_seen": "2026-05-18T12:00:00"},
                {"path": "/heatmap-basic", "count": 3, "last_seen": "2026-05-17T08:30:00"},
            ]
        )
        with patch("api.routers.debug.FeedbackRepository", return_value=repo):
            response = client.get("/debug/feedback/top?reaction=thumbs_up&limit=5")
        assert response.status_code == 200
        body = response.json()
        assert [entry["path"] for entry in body] == ["/scatter-basic", "/heatmap-basic"]
        assert body[0]["count"] == 7
        repo.top_paths_by_reaction.assert_awaited_once_with("thumbs_up", 5)

    def test_messages_filters_by_status(self, db_client) -> None:
        client, _ = db_client
        entry = MagicMock()
        entry.id = "abc-123"
        entry.message = "broken plot"
        entry.reaction = "bug"
        entry.contact = None
        entry.path = "/scatter-basic"
        entry.spec_id = "scatter-basic"
        entry.viewport = "1920x1080"
        entry.status = "new"
        entry.created_at = datetime(2026, 5, 18, 12, 0, 0)

        repo = MagicMock()
        repo.list_with_message = AsyncMock(return_value=[entry])
        with patch("api.routers.debug.FeedbackRepository", return_value=repo):
            response = client.get("/debug/feedback/messages?status=new&limit=10")
        assert response.status_code == 200
        body = response.json()
        assert len(body) == 1
        assert body[0]["status"] == "new"
        assert body[0]["message"] == "broken plot"
        repo.list_with_message.assert_awaited_once_with("new", 10)

    def test_messages_rejects_invalid_status(self, db_client) -> None:
        client, _ = db_client
        response = client.get("/debug/feedback/messages?status=archived")
        assert response.status_code == 400

    def test_messages_open_maps_to_new_and_in_progress(self, db_client) -> None:
        """`status=open` is the default debug-page filter — server-side pseudo
        value that expands to ('new', 'in_progress')."""
        client, _ = db_client
        repo = MagicMock()
        repo.list_with_message = AsyncMock(return_value=[])
        with patch("api.routers.debug.FeedbackRepository", return_value=repo):
            response = client.get("/debug/feedback/messages?status=open&limit=10")
        assert response.status_code == 200
        repo.list_with_message.assert_awaited_once_with(("new", "in_progress"), 10)

    def test_patch_status_happy_path(self, db_client) -> None:
        client, _ = db_client
        updated = MagicMock()
        updated.id = "abc-123"
        updated.message = "broken plot"
        updated.reaction = "bug"
        updated.contact = None
        updated.path = "/scatter-basic"
        updated.spec_id = "scatter-basic"
        updated.viewport = None
        updated.status = "done"
        updated.created_at = datetime(2026, 5, 18, 12, 0, 0, tzinfo=timezone.utc)

        repo = MagicMock()
        repo.update_status = AsyncMock(return_value=updated)
        with patch("api.routers.debug.FeedbackRepository", return_value=repo):
            response = client.patch("/debug/feedback/abc-123", json={"status": "done"})
        assert response.status_code == 200
        assert response.json()["status"] == "done"
        repo.update_status.assert_awaited_once_with("abc-123", "done")

    def test_patch_status_rejects_unknown_value(self, db_client) -> None:
        client, _ = db_client
        response = client.patch("/debug/feedback/abc-123", json={"status": "archived"})
        assert response.status_code == 400

    def test_patch_status_returns_404_when_missing(self, db_client) -> None:
        client, _ = db_client
        repo = MagicMock()
        repo.update_status = AsyncMock(return_value=None)
        with patch("api.routers.debug.FeedbackRepository", return_value=repo):
            response = client.patch("/debug/feedback/unknown", json={"status": "done"})
        assert response.status_code == 404
