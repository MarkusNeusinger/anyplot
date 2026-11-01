"""The admin tier (owner decision of 2026-11-01): its lane, its exemptions, and what keeps a fan-out fast.

The BFF asserts the tier with `X-Anyplot-Tier: admin`; the agents service trusts it only behind
its caller check, reads anything else as `public`, and then gives the admin's runs the run
queue's admin lane (the shared five slots, a cap of five runs instead of two) and exempts
them from the per-user day caps and the chat turns' minute. The global day budget binds
every tier. A model quota that outlasts the SDK's retries ends a run as `busy`, and the gates
run off the event loop the runs in flight share. The run's usage telemetry says how long it
waited and how close its user came to a limit, never who the user is.
"""

import asyncio
import json
import logging
import threading
from collections.abc import AsyncIterator, Iterator
from typing import Any

import anthropic
import httpx
import pytest
from google.adk.workflow._errors import DynamicNodeFailError
from google.genai import errors as genai_errors
from pydantic import ValidationError

from agents.anyplot import pipeline, telemetry, theme_render
from agents.anyplot.models import CLAUDE_MAX_RETRIES, AnthropicJudge, VertexClaude, error_chain, make_model, model_busy
from agents.anyplot.plugins.ledger import ATTRIBUTION_LOGGER, RequestLedger, UsageBook, budget_allows
from agents.anyplot.run_queue import RunQueue
from agents.anyplot.services import Services
from agents.anyplot.settings import AgentSettings, get_settings
from agents.main import Runtime, app, caller_tier, get_runtime

from .fakes import ROOT_REPLY, SCATTER_PLAN, VERDICT_OK, default_script
from .test_run_queue import Clock
from .test_run_queue_flow import GatedBackend, interleaved_runs, until
from .test_service_flow import HEADERS, create_plot, headers_for, open_session, parse_sse, render_theme
from .test_stream import token


OTHER = "adm_fedcba9876543210"
ADMIN_HEADERS = {**HEADERS, "X-Anyplot-Tier": "admin"}


def quota_error() -> anthropic.RateLimitError:
    """What the Anthropic SDK raises for a 429 its retries did not get past."""
    request = httpx.Request("POST", "https://eu-aiplatform.googleapis.com/v1/messages")
    return anthropic.RateLimitError("rate limited", response=httpx.Response(429, request=request), body=None)


@pytest.fixture
def backend() -> GatedBackend:
    """Fixture renders behind an open gate; a test that holds a run in flight closes it first."""
    gated = GatedBackend()
    gated.gate.set()
    return gated


@pytest.fixture
def clock() -> Clock:
    return Clock()


@pytest.fixture
def runtime(clock: Clock) -> Iterator[Runtime]:
    """The production limits but the start gap, which the fake clock would hold forever: five in flight, sixty
    waiting, two runs per public user and five per admin."""
    queue = RunQueue(
        concurrency=5, per_minute=6, max_wait_s=600, clock=clock, per_user=2, admin_per_user=5, start_gap_s=0
    )
    fresh = Runtime(queue=queue)
    app.dependency_overrides[get_runtime] = lambda: fresh
    yield fresh
    app.dependency_overrides.clear()


@pytest.fixture
async def client(runtime: Runtime, services: Services) -> AsyncIterator[httpx.AsyncClient]:
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://agents") as http:
        yield http


def attribution_lines(caplog: pytest.LogCaptureFixture, hook: str) -> list[dict[str, Any]]:
    lines = [json.loads(record.getMessage()) for record in caplog.records if record.name == ATTRIBUTION_LOGGER]
    return [line for line in lines if line.get("hook") == hook]


class TestTier:
    def test_only_exactly_admin_is_the_admin_tier(self) -> None:
        assert caller_tier("admin") == "admin"
        for value in (None, "", "public", "Admin", "ADMIN", "premium", "true"):
            assert caller_tier(value) == "public", value

    async def test_status_reports_the_callers_own_cap(self, client: httpx.AsyncClient) -> None:
        public = (await client.get("/v1/status", headers=HEADERS)).json()
        admin = (await client.get("/v1/status", headers=ADMIN_HEADERS)).json()
        other = (await client.get("/v1/status", headers={**HEADERS, "X-Anyplot-Tier": "root"})).json()

        assert (public["tier"], public["user_max_runs"]) == ("public", 2)
        assert (admin["tier"], admin["user_max_runs"]) == ("admin", 5)
        assert (other["tier"], other["user_max_runs"]) == ("public", 2)  # never a 422: an old BFF sends nothing

    async def test_status_follows_the_settings(self, services: Services, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("AGENT_ADMIN_USER_MAX_RUNS", "4")
        get_settings.cache_clear()
        fresh = Runtime()  # its queue comes from the settings on first use
        app.dependency_overrides[get_runtime] = lambda: fresh
        try:
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://agents") as http:
                admin = (await http.get("/v1/status", headers=ADMIN_HEADERS)).json()
        finally:
            app.dependency_overrides.clear()

        assert admin["user_max_runs"] == 4

    async def test_only_an_allowed_caller_reaches_the_tier(
        self, client: httpx.AsyncClient, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Outside development the caller check answers first: a request that is not the BFF's never gets a tier."""
        monkeypatch.setenv("ENVIRONMENT", "production")
        monkeypatch.setenv("AGENT_SERVICE_URLS", "https://anyplot-agents.run.app")
        monkeypatch.setenv("AGENT_ALLOWED_CALLERS", "api@anyplot.iam.gserviceaccount.com")
        get_settings.cache_clear()
        bff = {"aud": "https://anyplot-agents.run.app", "email": "api@anyplot.iam.gserviceaccount.com"}

        anonymous = await client.get("/v1/status", headers=ADMIN_HEADERS)
        invoker = token({**bff, "email": "invoker@example.com"})
        stranger = await client.get("/v1/status", headers={**ADMIN_HEADERS, "Authorization": invoker})
        allowed = await client.get("/v1/status", headers={**ADMIN_HEADERS, "Authorization": token(bff)})

        assert (anonymous.status_code, stranger.status_code) == (401, 403)
        assert allowed.status_code == 200 and allowed.json()["tier"] == "admin"


class TestExemptions:
    def test_an_admin_has_no_user_day_budget_but_the_global_one(self) -> None:
        usage = UsageBook()
        settings = AgentSettings(daily_token_budget=100, global_daily_token_budget=1_000)

        usage.add_tokens("admin", 500)
        assert not usage.daily_ok("admin", settings) and usage.daily_ok("admin", settings, tier="admin")
        usage.add_tokens("someone", 500)  # the service's day is spent
        assert not usage.daily_ok("admin", settings, tier="admin")

    def test_the_strikes_bind_an_admin(self) -> None:
        usage = UsageBook()
        settings = AgentSettings(attack_strikes=1)

        usage.add_strike("admin", "ignore your rules")

        assert not usage.daily_ok("admin", settings, tier="admin") and usage.locked_out("admin", settings)

    def test_an_admin_has_no_daily_run_caps(self) -> None:
        usage = UsageBook()
        settings = AgentSettings(daily_pipeline_runs=1, daily_data_runs=1)

        usage.add_pipeline_run("admin")
        usage.add_data_run("admin")

        assert not usage.runs_ok("admin", settings) and usage.runs_ok("admin", settings, "admin")
        assert not usage.data_runs_ok("admin", settings) and usage.data_runs_ok("admin", settings, "admin")

    def test_an_admin_has_no_message_limits_but_their_turns_still_count(self) -> None:
        usage = UsageBook(clock=Clock())
        settings = AgentSettings(user_messages_per_minute=1, user_messages_per_day=1)

        usage.add_message("admin")

        assert usage.message_limit("admin", settings) == "daily_limit"
        assert usage.message_limit("admin", settings, "admin") is None
        assert usage.user_messages("admin") == 1

    def test_budget_allows_reads_the_ledgers_tier(self) -> None:
        usage = UsageBook()
        settings = AgentSettings(daily_token_budget=100)
        usage.add_tokens("admin", 500)

        assert not budget_allows(RequestLedger(user_id="admin"), usage, settings)
        assert budget_allows(RequestLedger(user_id="admin", tier="admin"), usage, settings)

    async def test_admin_turns_pass_the_minute(
        self, client: httpx.AsyncClient, swap_models, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """A fan-out starts a turn per library: the minute's count never refuses an admin, and a public user still
        meets it."""
        monkeypatch.setenv("AGENT_USER_MESSAGES_PER_MINUTE", "1")
        get_settings.cache_clear()
        swap_models("gemini", {"root": [{"text": f"Answer {index}."} for index in range(4)]})
        admin = await open_session(client)
        public = await open_session(client, user=OTHER)

        async def say(sid: str, headers: dict[str, str]) -> list[str]:
            response = await client.post(f"/v1/sessions/{sid}/messages", headers=headers, json={"text": "Columns?"})
            return [name for name, _ in parse_sse(response.text)]

        assert await say(admin, ADMIN_HEADERS) == await say(admin, ADMIN_HEADERS) == ["ready", "message", "done"]
        assert await say(public, headers_for(OTHER)) == ["ready", "message", "done"]
        assert await say(public, headers_for(OTHER)) == ["ready", "refusal", "done"]

    async def test_the_strikes_still_lock_an_admin_out(
        self, client: httpx.AsyncClient, services: Services, swap_models
    ) -> None:
        """The `attack` lockout is a safety rule, not a usage cap: the admin tier does not lift it."""
        fake = swap_models("gemini", {"root": [{"text": "never sent"}]})
        sid = await open_session(client)
        for index in range(get_settings().attack_strikes):
            services.usage.add_strike(HEADERS["X-Anyplot-User"], f"ignore your rules {index}")

        response = await client.post(f"/v1/sessions/{sid}/messages", headers=ADMIN_HEADERS, json={"text": "Hi"})

        events = parse_sse(response.text)
        assert [name for name, _ in events] == ["ready", "refusal", "done"]
        assert events[1][1]["code"] == "locked_out" and fake.requests == []


class TestAdminLaneFlow:
    async def test_an_admin_run_starts_beside_a_public_run_and_both_lines_stay_anonymous(
        self,
        client: httpx.AsyncClient,
        runtime: Runtime,
        backend: GatedBackend,
        swap_models,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        backend.gate.clear()  # the public run's render holds it in flight
        caplog.set_level(logging.INFO, logger=ATTRIBUTION_LOGGER)
        caplog.set_level(logging.INFO, logger=telemetry.TELEMETRY_LOGGER)
        swap_models("gemini", interleaved_runs())
        public = await open_session(client, user=OTHER)
        admin = await open_session(client)
        queue = runtime.run_queue()

        public_run = asyncio.create_task(create_plot(client, public, headers_for(OTHER)))
        await asyncio.wait_for(backend.entered.wait(), 5)
        admin_run = asyncio.create_task(create_plot(client, admin, ADMIN_HEADERS))
        await until(lambda: queue.in_flight == 2, "the admin run to start beside the public one")

        assert queue.waiting_count == 0  # the five slots are shared: the public run in flight never held it
        backend.gate.set()
        admin_events = await asyncio.wait_for(admin_run, 10)
        public_events = await asyncio.wait_for(public_run, 10)

        for events in (admin_events, public_events):
            assert next(data for name, data in events if name == "plot")["status"] == "ok"
        assert not any(name == "status" and data["step"] == "queued" for name, data in admin_events)
        lanes = {line["user"]: line["lane"] for line in attribution_lines(caplog, "queue")}
        assert lanes == {OTHER: "normal", HEADERS["X-Anyplot-User"]: "admin"}
        renders = attribution_lines(caplog, "pipeline_render")
        assert len(renders) == 2 and all(line["slot_wait_s"] >= 0 for line in renders)
        # The run's usage telemetry (owner, 2026-11-01): its lane, its wait and how close its user came to a limit,
        # as numbers and buckets; neither user id, nor the user-id key's prefix, appears anywhere in a line.
        raw = [record.getMessage() for record in caplog.records if record.name == telemetry.TELEMETRY_LOGGER]
        runs = sorted((json.loads(line) for line in raw if '"pipeline_run"' in line), key=lambda line: line["lane"])
        assert [(run["lane"], run["queue_position"], run["queue_wait_ms"]) for run in runs] == [
            ("admin", 0, 0),
            ("public", 0, 0),
        ]
        assert all((run["user_runs_today"], run["user_tokens_today"]) == ("1", "lt25") for run in runs)
        assert not any(OTHER in line or HEADERS["X-Anyplot-User"] in line or "adm_" in line for line in raw)


class TestLimitTelemetry:
    """Whether anyone waits long or comes close to a limit, without saying who (owner, 2026-11-01)."""

    NEW_FIELDS = ("lane", "queue_wait_ms", "queue_position", "user_runs_today", "user_tokens_today")

    def test_the_runs_of_the_day_fall_into_the_owners_buckets(self) -> None:
        ordinals = {1: "1", 2: "2_5", 5: "2_5", 6: "6_10", 10: "6_10", 11: "11_20", 20: "11_20", 21: "21_30"}
        ordinals |= {30: "21_30", 31: "31_40", 40: "31_40", 41: "41_plus", 500: "41_plus"}

        assert {ordinal: telemetry.runs_today_bucket(ordinal) for ordinal in ordinals} == ordinals
        assert telemetry.runs_today_bucket(None) is None and telemetry.runs_today_bucket(0) is None

    def test_the_spent_budget_falls_into_the_owners_buckets(self) -> None:
        shares = {0.0: "lt25", 0.249: "lt25", 0.25: "25_50", 0.5: "50_75", 0.75: "75_90", 0.9: "90_100", 1.0: "90_100"}
        shares |= {1.01: "over", 3.0: "over"}

        assert {share: telemetry.tokens_today_bucket(share) for share in shares} == shares
        assert telemetry.tokens_today_bucket(None) is None

    def test_the_new_fields_validate(self) -> None:
        run = telemetry.PipelineRun(
            run_index=1,
            base="catalogue",
            status="ok",
            lane="admin",
            queue_wait_ms=31_400,
            queue_position=4,
            user_runs_today="2_5",
            user_tokens_today="over",
        )

        assert run.model_dump(include=set(self.NEW_FIELDS)) == {
            "lane": "admin",
            "queue_wait_ms": 31_400,
            "queue_position": 4,
            "user_runs_today": "2_5",
            "user_tokens_today": "over",
        }

    @pytest.mark.parametrize("field", NEW_FIELDS)
    def test_no_new_field_can_carry_an_id(self, field: str) -> None:
        """A closed set or a bounded integer: a user id, its hash or a key never validates."""
        for value in ("adm_0123456789abcdef", "0123456789abcdef", -1, 10**12):
            with pytest.raises(ValidationError):
                telemetry.PipelineRun(run_index=1, base="catalogue", status="ok", **{field: value})

    async def test_an_admins_run_limit_lands_in_the_chat_turn(
        self, client: httpx.AsyncClient, runtime: Runtime, swap_models, caplog: pytest.LogCaptureFixture
    ) -> None:
        """The limit refusals were recorded before; the admin lane's land in the same `chat_turn.error`."""
        caplog.set_level(logging.INFO, logger=telemetry.TELEMETRY_LOGGER)
        swap_models("gemini", {"root": [{"call": "plot_pipeline", "args": {}}, {"text": ROOT_REPLY}]})
        sid = await open_session(client)
        for index in range(5):  # the admin's five places, held by their other windows
            runtime.run_queue().submit(HEADERS["X-Anyplot-User"], f"s-other-{index}", lane="admin")

        events = await create_plot(client, sid, ADMIN_HEADERS)

        assert ("error", "run_limit") in [(name, data.get("code")) for name, data in events]
        turns = [json.loads(r.getMessage()) for r in caplog.records if r.name == telemetry.TELEMETRY_LOGGER]
        assert [turn["error"] for turn in turns if turn["event"] == "chat_turn"] == ["run_limit"]


class TestBusy:
    def test_a_quota_or_an_overload_is_told_apart_from_a_fault(self) -> None:
        quota = quota_error()
        gemini_quota = genai_errors.ClientError(429, {"error": {"code": 429, "status": "RESOURCE_EXHAUSTED"}})
        overloaded = anthropic.OverloadedError(
            "overloaded", response=httpx.Response(529, request=quota.request), body=None
        )
        wrapped = DynamicNodeFailError(message="node failed", error=quota, error_node_path="adapter")
        try:
            raise RuntimeError("the adapter failed") from overloaded
        except RuntimeError as exc:
            caused = exc
        unrelated = ValueError("an unrelated failure while handling it")
        unrelated.__context__ = quota  # what a raise inside the `except` of the quota leaves: an implicit context only
        unavailable = anthropic.InternalServerError(
            "unavailable", response=httpx.Response(503, request=quota.request), body=None
        )

        for busy in (quota, gemini_quota, overloaded, wrapped, caused):
            assert model_busy(busy), busy
        for fault in (unrelated, unavailable, ValueError("429")):
            assert not model_busy(fault), fault

    def test_the_error_chain_ends_at_the_innermost_cause(self) -> None:
        quota = quota_error()
        wrapped = DynamicNodeFailError(message="node failed", error=quota, error_node_path="adapter")

        assert error_chain(wrapped) == [wrapped, quota]
        assert error_chain(quota) == [quota]

    async def test_a_quota_after_the_retries_ends_the_run_as_busy(
        self, client: httpx.AsyncClient, swap_models, caplog: pytest.LogCaptureFixture
    ) -> None:
        caplog.set_level(logging.INFO, logger=ATTRIBUTION_LOGGER)
        swap_models(
            "gemini",
            {
                "root": [{"call": "plot_pipeline", "args": {}}, {"text": ROOT_REPLY}],
                "adapter": [{"raise": quota_error()}],
            },
        )
        sid = await open_session(client)

        events = await create_plot(client, sid, ADMIN_HEADERS)

        plot = next(data for name, data in events if name == "plot")
        assert (plot["status"], plot["reason"]) == ("failed", "busy")
        result = attribution_lines(caplog, "pipeline_result")[-1]
        assert (result["reason"], result["error"]) == ("busy", "RateLimitError")  # never ADK's wrapper

    async def test_any_other_failure_stays_an_error(self, client: httpx.AsyncClient, swap_models) -> None:
        swap_models(
            "gemini",
            {
                "root": [{"call": "plot_pipeline", "args": {}}, {"text": ROOT_REPLY}],
                "adapter": [{"raise": RuntimeError("boom")}],
            },
        )
        sid = await open_session(client)

        plot = next(data for name, data in await create_plot(client, sid) if name == "plot")

        assert (plot["status"], plot["reason"]) == ("failed", "error")

    def test_root_adapter_and_reviewer_retry_four_times_and_the_judge_never(self) -> None:
        settings = AgentSettings(location="global", project="anyplot-eval")

        for kind in ("root", "adapter", "reviewer"):
            model = make_model(kind, settings)
            assert isinstance(model, VertexClaude)
            assert model._anthropic_client.max_retries == CLAUDE_MAX_RETRIES == 4
        judge = AnthropicJudge(model="claude-haiku-5-5", project="anyplot-eval", region="global", timeout_s=4.0)
        assert judge._client.max_retries == 0


class TestGatesOffTheLoop:
    async def test_the_pipeline_and_the_theme_toggle_run_their_gates_in_a_worker_thread(
        self, client: httpx.AsyncClient, swap_models, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        loop_thread = threading.get_ident()
        threads: list[tuple[str, int]] = []

        def recording(where: str, evaluate: Any) -> Any:
            def wrapped(*args: Any, **kwargs: Any) -> Any:
                threads.append((where, threading.get_ident()))
                return evaluate(*args, **kwargs)

            return wrapped

        monkeypatch.setattr(pipeline, "evaluate", recording("pipeline", pipeline.evaluate))
        monkeypatch.setattr(theme_render, "evaluate", recording("toggle", theme_render.evaluate))
        swap_models("gemini", default_script(VERDICT_OK, [SCATTER_PLAN]))
        sid = await open_session(client)

        await create_plot(client, sid)
        assert (await render_theme(client, sid, "dark")).status_code == 200

        assert [where for where, _ in threads] == ["pipeline", "toggle"]
        assert all(thread != loop_thread for _, thread in threads)
