"""Tests for api/turnstile.py, the Cloudflare Turnstile verifier.

Cloudflare is never reached: a MockTransport stands in for siteverify and records what it was sent. The answers
mirror what siteverify returned for Cloudflare's documented test secrets (developers.cloudflare.com/turnstile/
troubleshooting/testing/), measured on 2026-11-04.
"""

from __future__ import annotations

from collections.abc import Callable
from urllib.parse import parse_qs

import httpx
import pytest

from api import turnstile
from core.config import Settings, settings


SECRET = "0x4AAAAAAAtest-secret-of-the-right-shape"
PASSED = {"success": True, "error-codes": [], "challenge_ts": "2026-11-04T12:27:15Z", "hostname": "anyplot.ai"}
TESTING_KEY_PASSED = {**PASSED, "hostname": "example.com", "metadata": {"result_with_testing_key": True}}


def answer(codes: list[str]) -> dict[str, object]:
    return {"success": False, "error-codes": codes, "messages": []}


class Siteverify:
    """A MockTransport handler that answers each call with the next of `replies` and records the forms it got."""

    def __init__(self, *replies: httpx.Response | Exception) -> None:
        self.replies = list(replies)
        self.forms: list[dict[str, list[str]]] = []
        self.urls: list[str] = []

    def __call__(self, request: httpx.Request) -> httpx.Response:
        self.forms.append(parse_qs(request.content.decode()))
        self.urls.append(str(request.url))
        reply = self.replies.pop(0)
        if isinstance(reply, Exception):
            raise reply
        return reply


def json_reply(body: object, status: int = 200) -> httpx.Response:
    return httpx.Response(status, json=body)


@pytest.fixture
def secret(monkeypatch: pytest.MonkeyPatch) -> str:
    monkeypatch.setattr(settings, "turnstile_secret_key", SECRET)
    monkeypatch.setattr(turnstile, "RETRY_DELAY_S", 0)
    return SECRET


@pytest.fixture
def production(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "environment", "production")


async def run(handler: Callable[[httpx.Request], httpx.Response], token: str | None) -> turnstile.Verdict:
    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        return await turnstile.verify(token, client)


class TestWithoutASecret:
    async def test_development_and_tests_skip_the_check(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(settings, "turnstile_secret_key", None)
        cloudflare = Siteverify()

        assert await run(cloudflare, None) == "skipped"
        assert cloudflare.forms == []
        assert turnstile.refusal("skipped") is None

    async def test_production_refuses_rather_than_skips(self, monkeypatch: pytest.MonkeyPatch, production) -> None:
        monkeypatch.setattr(settings, "turnstile_secret_key", None)
        cloudflare = Siteverify()

        assert await run(cloudflare, "a-real-looking-token") == "unconfigured"
        assert turnstile.refusal("unconfigured") == (503, "bot_check_unavailable")
        assert cloudflare.forms == []

    @pytest.mark.parametrize("raw", ["", "   ", "\n"])
    def test_a_blank_secret_reads_as_unset(self, monkeypatch: pytest.MonkeyPatch, raw: str) -> None:
        monkeypatch.setenv("TURNSTILE_SECRET_KEY", raw)
        assert Settings().turnstile_secret_key is None

    def test_the_secret_loses_the_newline_echo_would_add(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("TURNSTILE_SECRET_KEY", f"{SECRET}\n")
        assert Settings().turnstile_secret_key == SECRET


class TestVerify:
    async def test_a_passing_token_passes(self, secret) -> None:
        cloudflare = Siteverify(json_reply(PASSED))

        assert await run(cloudflare, "tok") == "passed"
        assert turnstile.refusal("passed") is None
        assert cloudflare.urls == [turnstile.SITEVERIFY_URL]

    async def test_the_request_carries_secret_token_and_idempotency_key_but_no_address(self, secret) -> None:
        cloudflare = Siteverify(json_reply(PASSED))

        await run(cloudflare, "tok")

        form = cloudflare.forms[0]
        assert form["secret"] == [SECRET] and form["response"] == ["tok"]
        assert len(form["idempotency_key"][0]) == 36
        assert "remoteip" not in form

    @pytest.mark.parametrize("token", [None, "", "x" * (turnstile.MAX_TOKEN_CHARS + 1)])
    async def test_a_missing_or_oversized_token_is_refused_without_asking(self, secret, token) -> None:
        cloudflare = Siteverify()

        assert await run(cloudflare, token) == "missing"
        assert turnstile.refusal("missing") == (403, "bot_check_failed")
        assert cloudflare.forms == []

    @pytest.mark.parametrize("codes", [["invalid-input-response"], ["timeout-or-duplicate"], [], ["something-new"]])
    async def test_a_refused_token_is_refused(self, secret, codes) -> None:
        cloudflare = Siteverify(json_reply(answer(codes)))

        assert await run(cloudflare, "tok") == "rejected"
        assert turnstile.refusal("rejected") == (403, "bot_check_failed")
        assert len(cloudflare.forms) == 1  # a refusal is final: no retry

    async def test_success_must_be_true_not_truthy(self, secret) -> None:
        cloudflare = Siteverify(json_reply({**PASSED, "success": "true"}))

        assert await run(cloudflare, "tok") == "rejected"

    @pytest.mark.parametrize("status", [201, 302, 400])
    async def test_success_passes_only_on_http_200(self, secret, status) -> None:
        cloudflare = Siteverify(json_reply(PASSED, status))

        assert await run(cloudflare, "tok") == "unavailable"

    @pytest.mark.parametrize("hostname", ["anyplot.ai", "www.anyplot.ai", "python.anyplot.ai"])
    async def test_production_passes_a_token_solved_on_the_site(self, secret, production, hostname) -> None:
        cloudflare = Siteverify(json_reply({**PASSED, "hostname": hostname}))

        assert await run(cloudflare, "tok") == "passed"

    @pytest.mark.parametrize("hostname", ["localhost", "evil-anyplot.ai", "anyplot.ai.example", None, 7])
    async def test_production_refuses_a_token_solved_elsewhere(self, secret, production, hostname) -> None:
        """The widget's hostname list is the first fence; this holds if a development host is ever added there."""
        cloudflare = Siteverify(json_reply({**PASSED, "hostname": hostname}))

        assert await run(cloudflare, "tok") == "rejected"

    async def test_outside_production_any_hostname_passes(self, secret) -> None:
        cloudflare = Siteverify(json_reply({**PASSED, "hostname": "localhost"}))

        assert await run(cloudflare, "tok") == "passed"

    @pytest.mark.parametrize("codes", [["invalid-input-secret"], ["missing-input-secret"], ["bad-request"]])
    async def test_a_refused_secret_is_the_servers_fault(self, secret, codes, caplog) -> None:
        cloudflare = Siteverify(json_reply(answer(codes)))

        assert await run(cloudflare, "tok") == "unconfigured"
        assert SECRET not in caplog.text and "tok" not in caplog.text

    @pytest.mark.parametrize(
        "reply",
        [
            TESTING_KEY_PASSED,
            {**answer(["invalid-input-response"]), "metadata": {"result_with_testing_key": True}},
            {**answer(["timeout-or-duplicate"]), "metadata": {"result_with_testing_key": True}},
        ],
    )
    async def test_a_test_secret_is_no_secret_in_production(self, secret, production, reply) -> None:
        """One passes every token and the others refuse every visitor, so the deploy smoke must not pass either."""
        cloudflare = Siteverify(json_reply(reply))

        assert await run(cloudflare, "XXXX.DUMMY.TOKEN.XXXX") == "unconfigured"

    async def test_a_test_secret_passes_outside_production(self, secret) -> None:
        """Its answer names `example.com`: outside production the hostname is not checked."""
        cloudflare = Siteverify(json_reply(TESTING_KEY_PASSED))

        assert await run(cloudflare, "XXXX.DUMMY.TOKEN.XXXX") == "passed"


class TestRetry:
    async def test_a_timeout_is_retried_once_with_the_same_idempotency_key(self, secret) -> None:
        cloudflare = Siteverify(httpx.ReadTimeout("slow"), json_reply(PASSED))

        assert await run(cloudflare, "tok") == "passed"
        assert len(cloudflare.forms) == 2
        assert cloudflare.forms[0]["idempotency_key"] == cloudflare.forms[1]["idempotency_key"]

    async def test_internal_error_is_retried_once(self, secret) -> None:
        cloudflare = Siteverify(json_reply(answer(["internal-error"])), json_reply(PASSED))

        assert await run(cloudflare, "tok") == "passed"

    @pytest.mark.parametrize(
        "replies",
        [
            (httpx.ConnectError("down"), httpx.ConnectError("down")),
            (httpx.ReadTimeout("slow"), httpx.ReadTimeout("slow")),
            (json_reply({}, 502), json_reply({}, 503)),
            (json_reply(answer(["internal-error"])), json_reply(answer(["internal-error"]))),
        ],
    )
    async def test_two_failed_attempts_fail_closed(self, secret, replies) -> None:
        cloudflare = Siteverify(*replies)

        assert await run(cloudflare, "tok") == "unavailable"
        assert turnstile.refusal("unavailable") == (503, "bot_check_unavailable")
        assert len(cloudflare.forms) == turnstile.ATTEMPTS == 2

    @pytest.mark.parametrize("reply", [httpx.Response(200, text="<html>"), json_reply([True])])
    async def test_an_answer_that_is_no_json_object_fails_closed(self, secret, reply) -> None:
        cloudflare = Siteverify(reply)

        assert await run(cloudflare, "tok") == "unavailable"


def test_enforced_follows_the_setting(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "turnstile_secret_key", None)
    assert turnstile.enforced() is False
    monkeypatch.setattr(settings, "turnstile_secret_key", SECRET)
    assert turnstile.enforced() is True
