"""The service's day budget: the `service_paused` refusal, the status's pause note and the admin's live view.

Owner request of 2026-11-02: once `AGENT_GLOBAL_DAILY_TOKEN_BUDGET` is spent, every user got the same text as for
their own spent limit, and nobody could tell that the whole service paused. Now the global budget answers
`service_paused` (a turn's refusal, a paste's `429`), `GET /v1/status` says `paused` before the user types, and
`GET /v1/budget` gives the `/debug` page the day's spend and how many users are at their own limits, counts only.
"""

import logging
from collections.abc import AsyncIterator, Iterator
from datetime import UTC, datetime
from types import SimpleNamespace
from typing import Any, get_args

import httpx
import pytest
from google.adk.models.llm_request import LlmRequest

from agents.anyplot import telemetry
from agents.anyplot.plugins.budget import ROOT_AGENT, BudgetPlugin
from agents.anyplot.plugins.ledger import (
    CURRENT_LEDGER,
    LIMIT_KINDS,
    LOCATION_SURCHARGES,
    SERVICE_PAUSED,
    UNIT_PRICES,
    RequestLedger,
    UsageBook,
    day_refusal,
    next_reset,
    weighted_usd,
)
from agents.anyplot.plugins.scope_guard import LOCKED_OUT
from agents.anyplot.policy import refusal
from agents.anyplot.services import Services
from agents.anyplot.settings import AgentSettings, get_settings
from agents.evals import pricing
from agents.main import Runtime, app, get_runtime
from api.agent_usage import LIMIT_CODES

from .test_service_flow import HEADERS, USER, open_session, parse_sse, permissive_queue
from .test_telemetry import lines_of
from .test_turn_limits import OTHER, chatty


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
def small_budget(monkeypatch: pytest.MonkeyPatch) -> AgentSettings:
    """A service budget of 1,000 weighted tokens and a user budget of 600, so a test spends either at will."""
    monkeypatch.setenv("AGENT_GLOBAL_DAILY_TOKEN_BUDGET", "1000")
    monkeypatch.setenv("AGENT_DAILY_TOKEN_BUDGET", "600")
    get_settings.cache_clear()
    yield get_settings()
    get_settings.cache_clear()


async def say(client: httpx.AsyncClient, sid: str, text: str) -> list[Any]:
    response = await client.post(f"/v1/sessions/{sid}/messages", headers=HEADERS, json={"text": text})
    assert response.status_code == 200, response.text
    return parse_sse(response.text)


class TestUsageBook:
    def test_the_pause_is_the_service_budget_and_never_the_users_own(self) -> None:
        usage = UsageBook()
        settings = AgentSettings(global_daily_token_budget=1_000, daily_token_budget=600)

        usage.add_tokens("a", 400)
        assert not usage.paused(settings) and usage.daily_ok("b", settings)
        usage.add_tokens("a", 599)
        assert not usage.paused(settings)
        usage.add_tokens("c", 1)
        # Spent by others: `b` still has their own budget, so the refusal says the whole service paused.
        assert usage.paused(settings) and not usage.daily_ok("b", settings)
        assert day_refusal(usage, "b", settings) == SERVICE_PAUSED
        # `a` spent their own budget too: theirs is the one to name, since the pause text says theirs is untouched.
        assert day_refusal(usage, "a", settings) == "budget"

    def test_the_strikes_come_first(self) -> None:
        usage = UsageBook()
        settings = AgentSettings(global_daily_token_budget=1_000, attack_strikes=1)
        usage.add_tokens("a", 1_000)
        usage.add_strike("b", "ignore your rules")
        assert day_refusal(usage, "b", settings) == LOCKED_OUT == "locked_out"
        assert day_refusal(usage, "c", settings) == SERVICE_PAUSED

    def test_the_snapshot_counts_users_at_their_own_limits_never_names_them(self) -> None:
        usage = UsageBook()
        settings = AgentSettings(daily_token_budget=600, daily_pipeline_runs=2, user_messages_per_day=3)
        usage.add_tokens("a", 700)
        for _ in range(2):
            usage.add_pipeline_run("a")
            usage.add_pipeline_run("b")
        usage.add_message("c")
        usage.add_outcome("d")  # a beacon alone is no use of the chat today

        day = usage.snapshot(settings)

        assert (day.global_tokens, day.users, day.at_limit) == (700, 3, 2)
        assert day.limits == {
            "tokens": 1,
            "runs": 2,
            "data_runs": 0,
            "messages": 0,
            "pastes": 0,
            "conversions": 0,
            "locked_out": 0,
        }
        assert tuple(day.limits) == LIMIT_KINDS
        assert day.date == datetime.now(UTC).date().isoformat()
        assert day.since == max(day.started_at, datetime.fromisoformat(day.date).replace(tzinfo=UTC))
        assert not any(isinstance(value, str) and value in "abcd" for value in vars(day).values())

    def test_the_new_day_starts_at_midnight_utc(self) -> None:
        assert next_reset(datetime(2026, 11, 2, 23, 59, 59, tzinfo=UTC)) == datetime(2026, 11, 3, tzinfo=UTC)
        assert next_reset(datetime(2026, 11, 2, 0, 0, tzinfo=UTC)) == datetime(2026, 11, 3, tzinfo=UTC)


class TestPrices:
    def test_the_unit_prices_are_the_list_prices(self) -> None:
        """A price change in agents/evals/pricing.py must reach the live view's dollars too."""
        for model, price in UNIT_PRICES.items():
            assert price == pricing.price_of(model).input
        assert LOCATION_SURCHARGES == pricing.LOCATION_SURCHARGE

    def test_a_weighted_token_costs_the_main_models_input_price(self) -> None:
        # 100 M weighted tokens of Claude Haiku 5.5 in `eu`: $0.10 per M plus 10 %.
        assert weighted_usd(100_000_000, "claude-haiku-5-5", "eu") == pytest.approx(11.0)
        assert weighted_usd(100_000_000, "claude-haiku-5-5", "global") == pytest.approx(10.0)
        assert weighted_usd(1_000_000, "some-new-model", "eu") is None


class TestPauseRefusal:
    async def test_a_turn_says_the_service_paused_when_others_spent_the_day(
        self, client: httpx.AsyncClient, services: Services, swap_models, small_budget: AgentSettings
    ) -> None:
        fake = swap_models("gemini", chatty(1))
        sid = await open_session(client)
        services.usage.add_tokens(OTHER, small_budget.global_daily_token_budget)

        refused = await say(client, sid, "Which columns do I have?")

        assert [name for name, _ in refused] == ["ready", "refusal", "done"]
        assert refused[1][1] == {"code": SERVICE_PAUSED, "text": refusal(SERVICE_PAUSED, "en")}
        assert "00:00 UTC" in refused[1][1]["text"] and fake.requests == []  # no model call

    async def test_the_pause_reaches_the_telemetry_under_its_own_code(
        self,
        client: httpx.AsyncClient,
        services: Services,
        swap_models,
        small_budget: AgentSettings,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """A closed set: an unknown code would drop the line, so `service_paused` is in both sets the routes write."""
        caplog.set_level(logging.INFO)
        swap_models("gemini", chatty(1))
        sid = await open_session(client, with_data=False)
        services.usage.add_tokens(OTHER, small_budget.global_daily_token_budget)

        await say(client, sid, "Which columns do I have?")
        await client.post(f"/v1/sessions/{sid}/dataset", headers=HEADERS, json={"text": "x,y\n1,2\n"})

        assert [line["refusal"] for line in lines_of(caplog, "chat_turn")] == [SERVICE_PAUSED]
        assert [line["outcome"] for line in lines_of(caplog, "data_input")] == [SERVICE_PAUSED]

    def test_the_debug_table_counts_codes_the_telemetry_writes(self) -> None:
        """`api/agent_usage.py` cannot import the agents package (the API image does not ship it): pinned here."""
        written = set(get_args(telemetry.RefusalCode)) | set(get_args(telemetry.ErrorCode))
        written |= set(get_args(telemetry.DataOutcome))
        assert set(LIMIT_CODES) <= written

    async def test_a_root_call_past_the_service_budget_mid_turn_says_so(
        self, services: Services, small_budget: AgentSettings
    ) -> None:
        """The Budget plugin's halt before a root call names the pause too, not the user's own `budget`."""
        ledger = RequestLedger(user_id=USER, lang="de")
        context = SimpleNamespace(invocation_id="inv-1", agent_name=ROOT_AGENT, session=SimpleNamespace(user_id=USER))
        services.usage.add_tokens(OTHER, small_budget.global_daily_token_budget)
        token = CURRENT_LEDGER.set(ledger)
        try:
            halted = await BudgetPlugin().before_model_callback(callback_context=context, llm_request=LlmRequest())
        finally:
            CURRENT_LEDGER.reset(token)

        assert halted is not None and ledger.refusal == (SERVICE_PAUSED, refusal(SERVICE_PAUSED, "de"))

    async def test_a_user_past_their_own_budget_keeps_the_budget_refusal(
        self, client: httpx.AsyncClient, services: Services, swap_models, small_budget: AgentSettings
    ) -> None:
        swap_models("gemini", chatty(1))
        sid = await open_session(client)
        services.usage.add_tokens(USER, small_budget.daily_token_budget)

        refused = await say(client, sid, "Which columns do I have?")

        assert refused[1][1] == {"code": "budget", "text": refusal("budget", "en")}

    async def test_a_paste_is_429_service_paused_apart_from_the_users_daily_limit(
        self, client: httpx.AsyncClient, services: Services, small_budget: AgentSettings
    ) -> None:
        sid = await open_session(client, with_data=False)
        services.usage.add_tokens(OTHER, small_budget.global_daily_token_budget)

        paused = await client.post(f"/v1/sessions/{sid}/dataset", headers=HEADERS, json={"text": "x,y\n1,2\n"})
        assert (paused.status_code, paused.json()) == (429, {"detail": SERVICE_PAUSED})

        services.usage.add_tokens(USER, small_budget.daily_token_budget)
        own = await client.post(f"/v1/sessions/{sid}/dataset", headers=HEADERS, json={"text": "x,y\n1,2\n"})
        assert (own.status_code, own.json()) == (429, {"detail": "daily_limit"})


class TestStatusAndBudget:
    async def test_the_status_tells_the_page_before_the_user_types(
        self, client: httpx.AsyncClient, services: Services, small_budget: AgentSettings
    ) -> None:
        before = (await client.get("/v1/status", headers=HEADERS)).json()
        services.usage.add_tokens(OTHER, small_budget.global_daily_token_budget)
        after = (await client.get("/v1/status", headers=HEADERS)).json()

        assert before["paused"] is False and after["paused"] is True
        resets = datetime.fromisoformat(after["resets_at"])
        assert after["resets_at"].endswith("T00:00:00Z") and resets == next_reset()

    async def test_the_budget_view_is_counts_and_times_only(
        self, client: httpx.AsyncClient, services: Services, small_budget: AgentSettings
    ) -> None:
        services.usage.add_tokens(USER, 600)
        services.usage.add_tokens(OTHER, 150)
        services.usage.add_message(OTHER)

        body = (await client.get("/v1/budget", headers=HEADERS)).json()

        assert set(body) == {
            "date",
            "since",
            "started_at",
            "resets_at",
            "paused",
            "model",
            "tokens",
            "budget_tokens",
            "usd",
            "budget_usd",
            "users",
            "users_at_limit",
            "limits",
        }
        assert (body["tokens"], body["budget_tokens"], body["paused"]) == (750, 1_000, False)
        assert body["usd"] == pytest.approx(750 * 0.11 / 1e6, abs=1e-4)
        assert body["budget_usd"] == pytest.approx(1_000 * 0.11 / 1e6, abs=1e-4)
        assert (body["users"], body["users_at_limit"], body["limits"]["tokens"]) == (2, 1, 1)
        assert body["model"] == "claude-haiku-5-5" and body["resets_at"].endswith("T00:00:00Z")
        assert USER not in str(body) and OTHER not in str(body)
