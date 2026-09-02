"""The shared-secret origin gate (`api/origin_gate.py`).

Both Cloud Run services stand with `ingress=all`, so the raw `*.run.app`
address answers without ever touching Cloudflare — and every edge measure (the
bot challenge, the WAF, the cache that makes the `max-age=300` reads free) is
one URL away from being bypassed. A Cloudflare Transform Rule stamps
`X-Origin-Secret` onto everything it proxies for `api.anyplot.ai`; this suite
pins that the API requires it, that it is DORMANT until the secret is
configured (which is the rollback), and that the paths which must never be
locked out are not.
"""

from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

import api.main as api_main
from api.main import app
from api.origin_gate import ORIGIN_SECRET_HEADER, _matches, is_exempt
from core.config import settings


SECRET = "s3cret-from-the-edge"
EDGE = {ORIGIN_SECRET_HEADER: SECRET}

# A path the gate has an opinion about and that needs neither the database nor
# a seeded row to answer: /hello is a plain echo route, so a non-403 here means
# the request got through rather than that a fixture happened to exist.
OPEN_PATH = "/hello/gate"


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


@pytest.fixture
def armed(monkeypatch):
    """Turn the gate on for one test, the way Cloud Run's env does."""
    monkeypatch.setattr(settings, "origin_secret", SECRET)


class TestTheGateIsOffUntilASecretIsConfigured:
    """The default everywhere: local dev, the test suite, and production until
    step (c) of the rollout. Unsetting the variable is the rollback, and it
    must need no deploy — so `origin_secret` is read per request."""

    def test_no_secret_configured_by_default(self):
        assert settings.origin_secret is None

    def test_requests_pass_without_the_header(self, client: TestClient):
        assert client.get(OPEN_PATH).status_code == 200

    def test_requests_pass_even_with_a_wrong_header(self, client: TestClient):
        """What the window between the Transform Rule going live and the secret
        being set looks like from the service's side."""
        assert client.get(OPEN_PATH, headers={ORIGIN_SECRET_HEADER: "anything"}).status_code == 200

    def test_health_says_off(self, client: TestClient):
        assert client.get("/health").json()["origin_gate"] == "off"

    def test_health_says_off_seen_when_a_header_arrived(self, client: TestClient):
        """The verdict step (b) of the rollout is measured with: the rule goes
        live first, and every path that must keep working has to answer
        `off-seen` before the switch is thrown. A bare `off` would make arming
        a leap — above all for `anyplot.ai/api/*`, which reaches this service
        through a Cloudflare Worker whose subrequest may or may not carry the
        stamp."""
        res = client.get("/health", headers={ORIGIN_SECRET_HEADER: "anything"})
        assert res.json()["origin_gate"] == "off-seen"


class TestTheArmedGate:
    def test_the_edge_header_passes(self, client: TestClient, armed):
        assert client.get(OPEN_PATH, headers=EDGE).status_code == 200

    @pytest.mark.parametrize(
        "headers",
        [
            {},
            {ORIGIN_SECRET_HEADER: ""},
            {ORIGIN_SECRET_HEADER: "wrong"},
            {ORIGIN_SECRET_HEADER: SECRET[:-1]},
            {ORIGIN_SECRET_HEADER: SECRET + "x"},
        ],
        ids=["absent", "empty", "wrong", "truncated", "extended"],
    )
    def test_anything_else_is_refused(self, client: TestClient, armed, headers):
        res = client.get(OPEN_PATH, headers=headers)
        assert res.status_code == 403
        assert res.headers["cache-control"] == "private, no-store"

    def test_the_refusal_names_the_front_door_and_nothing_else(self, client: TestClient, armed):
        """Never the secret, never its length, never whether the caller was
        close."""
        detail = client.get(OPEN_PATH).json()["detail"]
        assert "api.anyplot.ai" in detail
        assert SECRET not in detail

    @pytest.mark.parametrize("method", ["get", "post", "put", "patch", "delete", "head"])
    def test_every_method_is_covered(self, client: TestClient, armed, method):
        """A gate that only saw GET would be one verb away from useless."""
        assert getattr(client, method)("/debug/status").status_code == 403

    def test_an_unknown_route_is_refused_before_it_404s(self, client: TestClient, armed):
        assert client.get("/no-such-route").status_code == 403

    def test_it_answers_before_the_admin_credential_is_looked_at(self, client: TestClient, armed):
        """The gate asks which door you came in at, not who you are — and it
        answers first. Break-glass over the direct URL needs BOTH headers."""
        assert client.get("/debug/status", headers={"X-Admin-Token": "whatever"}).status_code == 403


class TestTheExemptPaths:
    """Two paths, no prefixes. `/health` is how the deploy smoke reaches the
    candidate revision on its `run.app` tag URL, which by definition never
    passes the edge, so gating it would make every deploy fail closed.
    `/debug/cache/invalidate` is the one legitimate caller with no front door —
    `sync-postgres.yml` posts to the direct URL because Cloudflare's bot
    challenge answers an unauthenticated curl POST with a 403 HTML page; that
    endpoint carries its own token."""

    def test_the_gate_is_really_armed_for_this_test(self, client: TestClient, armed):
        assert client.get(OPEN_PATH).status_code == 403

    def test_health_is_never_gated(self, client: TestClient, armed):
        assert client.get("/health").status_code == 200

    def test_the_cache_flush_is_never_gated(self, client: TestClient, armed):
        """503 is the answer with no CACHE_INVALIDATE_TOKEN configured — its
        own fail-closed gate, reached rather than pre-empted."""
        assert client.post("/debug/cache/invalidate").status_code == 503

    def test_the_prerendered_pages_ARE_gated(self, client: TestClient, armed):
        """Deliberately not exempt (Copilot review): the site's nginx fetches
        them over `https://api.anyplot.ai`, so they carry the header, while an
        exemption would leave the API's most expensive reads open on the direct
        URL — a cache miss or an unknown id queries the repositories, and a
        crawler user agent schedules an outbound Plausible event per request."""
        assert client.get("/seo-proxy/legal").status_code == 403

    @pytest.mark.parametrize(
        ("path", "exempt"),
        [
            ("/health", True),
            ("/debug/cache/invalidate", True),
            ("/seo-proxy", False),
            ("/seo-proxy/", False),
            ("/seo-proxy/specs", False),
            ("/healthz", False),
            ("/debug/cache", False),
            ("/debug/status", False),
            ("/specs", False),
        ],
    )
    def test_the_exemption_list_is_exactly_these_two_paths(self, path, exempt):
        assert is_exempt(path, "GET") is exempt


class TestCORS:
    def test_a_preflight_is_never_refused(self, client: TestClient, armed):
        """A browser cannot attach a custom header to a preflight, so a gate
        that refused one would break every cross-origin call on the site
        instead of protecting anything. `CORSMiddleware` sits outside the gate
        and answers the preflight before it gets there, so this holds twice
        over — the explicit exemption is what keeps it true if the stack order
        ever moves."""
        assert is_exempt(OPEN_PATH, "OPTIONS")

        preflight = client.options(
            OPEN_PATH,
            headers={
                "Origin": "https://anyplot.ai",
                "Access-Control-Request-Method": "GET",
                "Access-Control-Request-Headers": "x-admin-token",
            },
        )
        assert preflight.status_code == 200
        assert preflight.headers["access-control-allow-origin"] == "https://anyplot.ai"

    def test_a_refused_request_still_carries_the_cors_headers(self, client: TestClient, armed):
        """So the browser reports a 403 rather than an opaque network error —
        which is why the middleware sits INSIDE CORSMiddleware."""
        refused = client.get(OPEN_PATH, headers={"Origin": "https://anyplot.ai"})
        assert refused.status_code == 403
        assert refused.headers["access-control-allow-origin"] == "https://anyplot.ai"


class TestARefusalCostsNothing:
    """The gate has to sit OUTSIDE the analytics middleware.

    An asset path plus a crawler user agent makes the counter fire an outbound
    Plausible request per request. If the gate were inside it, a caller on the
    direct `run.app` URL could turn each of its OWN refusals into one —
    unthrottled, and to a third-party endpoint. A refused request must cost
    nothing at all.
    """

    CRAWLER = {"User-Agent": "Mozilla/5.0 (compatible; ClaudeBot/1.0)"}
    ASSET = "/specs/scatter-basic/matplotlib/code"

    def test_a_refused_asset_read_reports_nothing(self, client: TestClient, armed):
        with patch.object(api_main, "track_asset_fetch") as assets:
            assert client.get(self.ASSET, headers=self.CRAWLER).status_code == 403
            assert assets.call_count == 0

    def test_a_refused_crawler_page_reports_nothing_either(self, client: TestClient, armed):
        """The prerendered pages are the ones an unthrottled caller would pick:
        every request with a crawler user agent schedules an outbound event."""
        with patch.object(api_main, "track_bot_fetch") as pages:
            assert client.get("/seo-proxy/legal", headers=self.CRAWLER).status_code == 403
            assert pages.call_count == 0

    def test_with_the_header_the_crawler_page_counts(self, client: TestClient, armed):
        with patch.object(api_main, "track_bot_fetch") as pages:
            client.get("/seo-proxy/legal", headers=self.CRAWLER | EDGE)
            assert pages.call_count == 1

    def test_with_the_header_the_read_counts_again(self, client: TestClient, armed):
        """The gate suppresses a refusal, not the measurement."""
        with patch.object(api_main, "track_asset_fetch") as assets:
            client.get(self.ASSET, headers=self.CRAWLER | EDGE)
            assert assets.call_count == 1


class TestHealthReportsTheVerdictForTheRequestItWasAskedWith:
    """What makes the rollout measurable: every route into the service can be
    asked whether the header arrives, BEFORE the gate is armed."""

    @pytest.mark.parametrize(
        ("headers", "verdict"), [(EDGE, "ok"), ({}, "missing"), ({ORIGIN_SECRET_HEADER: "wrong"}, "mismatch")]
    )
    def test_verdict(self, client: TestClient, armed, headers, verdict):
        res = client.get("/health", headers=headers)
        assert res.status_code == 200
        assert res.json()["origin_gate"] == verdict


class TestANonAsciiHeaderIsRefused:
    """`secrets.compare_digest` raises TypeError when either `str` holds a
    non-ASCII character, and a header value reaches the middleware
    latin-1-decoded straight from the wire. Comparing as `str` would therefore
    hand any unauthenticated caller a one-byte way to turn every refusal into
    an unhandled 500 — the gate made expensive instead of cheap (Copilot
    review). The compare encodes both sides first.
    """

    # Passed as raw bytes: an HTTP client refuses to encode a non-ASCII str
    # header, so bytes are the only way one reaches the middleware at all.
    RAW = b"s3cret-from-the-edg\xe9"

    def test_a_non_ascii_header_is_a_403_not_a_500(self, client: TestClient, armed):
        res = client.get(OPEN_PATH, headers={ORIGIN_SECRET_HEADER: self.RAW})
        assert res.status_code == 403

    def test_health_calls_it_a_mismatch_not_a_500(self, client: TestClient, armed):
        res = client.get("/health", headers={ORIGIN_SECRET_HEADER: self.RAW})
        assert res.status_code == 200
        assert res.json()["origin_gate"] == "mismatch"

    def test_the_str_comparison_this_replaced_would_have_raised(self):
        """The proof that the two tests above measure something. Asserted on
        the primitive rather than on a response, because the exact byte the
        client puts on the wire is the transport's business — what matters is
        that a non-ASCII `str` is fatal to `compare_digest` and harmless to
        the encoded compare."""
        import secrets as stdlib_secrets

        seen = self.RAW.decode("latin-1")
        with pytest.raises(TypeError):
            stdlib_secrets.compare_digest(seen, SECRET)

        assert _matches(seen, seen) is True
        assert _matches(seen, SECRET) is False


class TestATrailingNewlineCannotLockEveryoneOut:
    """A Secret Manager version created with `echo` carries a trailing newline,
    Cloud Run injects the bytes verbatim, and an HTTP header physically cannot
    transport one — so every request would 403 and no value of the header could
    ever fix it. The setting strips."""

    def test_the_env_value_is_stripped(self, monkeypatch):
        from core.config import Settings

        monkeypatch.setenv("ORIGIN_SECRET", f"{SECRET}\n")
        assert Settings().origin_secret == SECRET

    def test_a_stripped_secret_matches_the_header(self, client: TestClient, monkeypatch):
        from core.config import Settings

        monkeypatch.setattr(settings, "origin_secret", Settings(origin_secret=f"  {SECRET}  ").origin_secret)
        assert client.get(OPEN_PATH, headers=EDGE).status_code == 200

    def test_an_all_whitespace_secret_leaves_the_gate_off(self, client: TestClient, monkeypatch):
        """Rather than arming it with a value nobody can present."""
        from core.config import Settings

        monkeypatch.setattr(settings, "origin_secret", Settings(origin_secret="   ").origin_secret)
        assert client.get(OPEN_PATH).status_code == 200

    def test_the_other_secret_manager_values_strip_too(self, monkeypatch):
        """Same failure mode, same fix, one PR earlier than the incident."""
        from core.config import Settings

        loaded = Settings(admin_token="tok\n", cache_invalidate_token="cache\n", cf_access_aud=" aud ")
        assert loaded.admin_token == "tok"
        assert loaded.cache_invalidate_token == "cache"
        assert loaded.cf_access_aud == "aud"
