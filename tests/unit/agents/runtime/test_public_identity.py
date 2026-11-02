"""The anonymous public caller (launch package of 2026-11-02): its salted id, its network, and the per-IP caps.

The public BFF sends the page's random tab id as `X-Anyplot-Anon` and the client's network as
`X-Anyplot-Network`. The service keys the caller on the tab id salted with its per-process salt,
binds it to the salted network for the day, and counts the network's tokens, pipeline runs and
sandbox runs against the per-IP caps; the run queue also caps the public lane's waiting entries.
"""

import asyncio
import re
from collections.abc import AsyncIterator, Awaitable, Iterator

import httpx
import pytest

from agents.anyplot.data.parse import ParsedDataset, parse_dataset
from agents.anyplot.data.store import DatasetStore, StoreFull, dataset_size
from agents.anyplot.plugins import ledger
from agents.anyplot.plugins.ledger import UsageBook, anonymous_user, day_refusal, network_key
from agents.anyplot.run_queue import QueueFull, QueueUserLimit, RunQueue
from agents.anyplot.services import Services
from agents.anyplot.settings import AgentSettings, get_settings
from agents.main import NETWORK_PATTERN, Runtime, app, caller_tier, get_runtime

from .test_run_queue import Clock
from .test_service_flow import snapshot_body


TAB = "3f9d6c1e-8a2b-4c7d-9e0f-1a2b3c4d5e6f"
OTHER_TAB = "0a1b2c3d-4e5f-4a7b-8c9d-0e1f2a3b4c5d"
NETWORK = "203.0.113.7"


def anon_headers(tab: str = TAB, network: str | None = NETWORK) -> dict[str, str]:
    headers = {"X-Anyplot-Anon": tab, "X-Anyplot-Tier": "public", "X-Request-Id": "req-anon"}
    if network is not None:
        headers["X-Anyplot-Network"] = network
    return headers


@pytest.fixture
def runtime() -> Iterator[Runtime]:
    fresh = Runtime(queue=RunQueue(concurrency=5, per_minute=1_000, max_wait_s=600, per_user=2, per_network=4))
    app.dependency_overrides[get_runtime] = lambda: fresh
    yield fresh
    app.dependency_overrides.clear()


@pytest.fixture
async def client(runtime: Runtime, services: Services) -> AsyncIterator[httpx.AsyncClient]:
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://agents") as http:
        yield http


async def open_anonymous_session(client: httpx.AsyncClient, headers: dict[str, str], tab: str = TAB) -> str:
    response = await client.post(
        "/v1/sessions",
        headers=headers,
        json={
            "user": tab,
            "spec_id": "scatter-basic",
            "library": "matplotlib",
            "locale": "en",
            "snapshot": snapshot_body(),
        },
    )
    assert response.status_code == 200, response.text
    sid: str = response.json()["session_id"]
    return sid


class TestIdentity:
    def test_the_salted_ids_are_stable_in_the_process_and_never_the_values_sent(self) -> None:
        assert anonymous_user(TAB) == anonymous_user(TAB) != anonymous_user(OTHER_TAB)
        assert anonymous_user(TAB).startswith("pub_") and len(anonymous_user(TAB)) == 20
        assert TAB not in anonymous_user(TAB)
        assert network_key(NETWORK) == network_key(NETWORK) != network_key("203.0.113.8")
        assert NETWORK not in network_key(NETWORK) and network_key(NETWORK).startswith("net_")

    def test_an_anonymous_caller_is_public_whatever_the_tier_header_says(self) -> None:
        assert caller_tier("admin", TAB) == "public"
        assert caller_tier("admin", None) == "admin"

    async def test_a_session_belongs_to_the_salted_tab_id(self, client: httpx.AsyncClient, services: Services) -> None:
        sid = await open_anonymous_session(client, anon_headers())

        mine = await client.get(f"/v1/sessions/{sid}/memory", headers=anon_headers())
        other = await client.get(f"/v1/sessions/{sid}/memory", headers=anon_headers(OTHER_TAB))
        raw = await client.get(f"/v1/sessions/{sid}/memory", headers={"X-Anyplot-User": TAB})

        assert mine.status_code == 200
        assert other.status_code == 404 and other.json() == {"detail": "session_expired"}
        assert raw.status_code == 404  # the tab id as a plain user id is somebody else
        assert services.usage.network_of(anonymous_user(TAB)) == network_key(NETWORK)

    async def test_one_network_holds_a_bounded_number_of_live_sessions(
        self, client: httpx.AsyncClient, services: Services, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("AGENT_IP_MAX_SESSIONS", "2")
        get_settings.cache_clear()
        tabs = [f"{index:02d}{TAB[2:]}" for index in range(3)]
        first = await open_anonymous_session(client, anon_headers(tabs[0]), tabs[0])
        await open_anonymous_session(client, anon_headers(tabs[1]), tabs[1])

        third = await client.post(
            "/v1/sessions",
            headers=anon_headers(tabs[2]),
            json={
                "user": tabs[2],
                "spec_id": "scatter-basic",
                "library": "matplotlib",
                "locale": "en",
                "snapshot": snapshot_body(),
            },
        )
        assert third.status_code == 429 and third.json() == {"detail": "session_limit"}
        # Another network is not this one's business, and a closed session frees its place.
        await open_anonymous_session(client, anon_headers(tabs[2], network="198.51.100.1"), tabs[2])
        assert (await client.delete(f"/v1/sessions/{first}", headers=anon_headers(tabs[0]))).status_code == 204
        await open_anonymous_session(client, anon_headers(tabs[0]), tabs[0])
        assert services.network_sessions(network_key(NETWORK)) == 2

    async def test_parallel_creates_never_pass_the_session_cap(
        self, client: httpx.AsyncClient, services: Services, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("AGENT_IP_MAX_SESSIONS", "1")
        get_settings.cache_clear()
        tabs = [f"{index:02d}{TAB[2:]}" for index in range(4)]

        def create(tab: str) -> Awaitable[httpx.Response]:
            body = {
                "user": tab,
                "spec_id": "scatter-basic",
                "library": "matplotlib",
                "locale": "en",
                "snapshot": snapshot_body(),
            }
            return client.post("/v1/sessions", headers=anon_headers(tab), json=body)

        answers = await asyncio.gather(*(create(tab) for tab in tabs))

        assert sorted(answer.status_code for answer in answers) == [200, 429, 429, 429]
        assert services.network_sessions(network_key(NETWORK)) == 1

    async def test_eligibility_binds_no_network(self, client: httpx.AsyncClient, services: Services) -> None:
        response = await client.get(
            "/v1/eligibility", params={"spec": "scatter-basic", "library": "matplotlib"}, headers=anon_headers()
        )

        assert response.status_code == 200
        assert services.usage.network_of(anonymous_user(TAB)) is None  # the plot page asks on every visit

    async def test_the_body_names_the_tab_id_as_sent(self, client: httpx.AsyncClient) -> None:
        body = {
            "user": anonymous_user(TAB),
            "spec_id": "scatter-basic",
            "library": "matplotlib",
            "locale": "en",
            "snapshot": snapshot_body(),
        }
        response = await client.post("/v1/sessions", headers=anon_headers(), json=body)

        assert response.status_code == 422 and response.json() == {"detail": "invalid"}

    @pytest.mark.parametrize(
        ("headers", "detail"),
        [
            (anon_headers(network=None), "network_required"),
            (anon_headers(network="203.0.113.7; DROP"), "network_required"),
            (anon_headers(tab="short"), "user_required"),
            ({**anon_headers(), "X-Anyplot-User": "adm_0123456789abcdef"}, "user_required"),
        ],
    )
    async def test_an_incomplete_anonymous_caller_is_refused(
        self, client: httpx.AsyncClient, headers: dict[str, str], detail: str
    ) -> None:
        response = await client.get("/v1/sessions/s-1/memory", headers=headers)

        assert response.status_code == 400 and response.json() == {"detail": detail}

    @pytest.mark.parametrize("network", ["2001:db8:1:2::/64", "unknown", "192.0.2.1"])
    def test_every_form_the_bff_sends_is_a_network(self, network: str) -> None:
        assert re.fullmatch(NETWORK_PATTERN, network)


class TestNetworkDay:
    def bound(self, book: UsageBook, *tabs: str, network: str = NETWORK) -> list[str]:
        users = [anonymous_user(tab) for tab in tabs]
        for user in users:
            book.bind_network(user, network_key(network))
        return users

    def test_the_tabs_of_one_network_share_its_token_budget(self) -> None:
        settings = AgentSettings(daily_token_budget=1_000, ip_daily_token_budget=1_500)
        book = UsageBook()
        first, second = self.bound(book, TAB, OTHER_TAB)

        book.add_tokens(first, 900)
        assert book.daily_ok(second, settings)  # 900 on the network, 0 of the second tab's own
        book.add_tokens(second, 600)

        assert book.network_tokens(first) == book.network_tokens(second) == 1_500
        assert not book.daily_ok(second, settings)  # its own 600 are fine; the network's 1,500 are spent
        assert day_refusal(book, second, settings) == "budget"  # never "service_paused": the service is not
        fresh = anonymous_user("9f9d6c1e-8a2b-4c7d-9e0f-1a2b3c4d5e6f")
        assert book.daily_ok(fresh, settings)  # unbound: no network to count against

    def test_the_tabs_of_one_network_share_its_pipeline_runs(self) -> None:
        settings = AgentSettings(daily_pipeline_runs=2, ip_daily_pipeline_runs=3)
        book = UsageBook()
        first, second = self.bound(book, TAB, OTHER_TAB)

        book.add_pipeline_run(first)
        book.add_pipeline_run(first)
        assert not book.runs_ok(first, settings) and book.runs_ok(second, settings)
        book.add_pipeline_run(second)

        assert not book.runs_ok(second, settings)  # one of its own, three on the network
        assert book.runs_ok(second, settings, tier="admin")

    def test_a_tab_that_moves_takes_its_new_network(self) -> None:
        book = UsageBook()
        (user,) = self.bound(book, TAB)
        book.add_tokens(user, 100)
        book.bind_network(user, network_key("198.51.100.1"))
        book.add_tokens(user, 10)

        assert book.network_tokens(user) == 10  # the old network keeps the 100 it booked
        assert book.user_tokens(user) == 110

    def test_the_tabs_of_one_network_share_its_pastes_minute_and_day(self) -> None:
        settings = AgentSettings(user_pastes_per_minute=2, user_pastes_per_day=3)
        clock = Clock()
        book = UsageBook(clock=clock)
        tabs = self.bound(book, *(f"{index:02d}{TAB[2:]}" for index in range(4)))

        for user in tabs[:2]:  # two tabs fill the network's minute: twice the per-user 2
            for _ in range(2):
                assert book.paste_limit(user, settings) is None
                book.add_paste(user)
        assert book.paste_limit(tabs[2], settings) == "rate_limited"  # a fresh tab, the same machine

        clock.advance(61)
        book.add_paste(tabs[2])
        book.add_paste(tabs[2])
        assert book.paste_limit(tabs[3], settings) == "daily_limit"  # six of the network's twice-three today
        assert book.paste_limit(anonymous_user(OTHER_TAB), settings) is None  # unbound: only its own caps

    def test_the_admin_and_other_named_callers_keep_their_own_windows(self) -> None:
        settings = AgentSettings(user_messages_per_minute=1, user_messages_per_day=5)
        book = UsageBook(clock=Clock())
        book.add_message("adm_0123456789abcdef")

        assert book.message_limit("adm_0123456789abcdef", settings) == "rate_limited"
        assert book.message_limit("adm_fedcba9876543210", settings) is None  # no network ties the two

    def test_a_turn_across_midnight_still_books_to_its_network(self, monkeypatch: pytest.MonkeyPatch) -> None:
        book = UsageBook()
        (user,) = self.bound(book, TAB)
        monkeypatch.setattr(ledger, "today", lambda: "2099-01-01")  # the UTC day turns while the turn runs

        book.add_tokens(user, 70)
        book.add_pipeline_run(user)

        assert book.network_of(user) == network_key(NETWORK)
        assert (book.network_tokens(user), book.network_runs(user)) == (70, 1)

    def test_the_bindings_stay_bounded_however_many_tab_ids_arrive(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(ledger, "MAX_BOUND_USERS", 3)
        book = UsageBook()
        users = [anonymous_user(f"{index:02d}{TAB[2:]}") for index in range(5)]
        for user in users:
            book.bind_network(user, network_key(NETWORK))
        book.bind_network(users[2], network_key(NETWORK))  # an active user binds again and stays

        assert [book.network_of(user) is not None for user in users] == [False, False, True, True, True]

    def test_a_caller_without_a_network_counts_only_as_itself(self) -> None:
        book = UsageBook()
        book.add_tokens("adm_0123456789abcdef", 50)
        book.add_pipeline_run("adm_0123456789abcdef")

        assert book.network_of("adm_0123456789abcdef") is None
        assert book.network_tokens("adm_0123456789abcdef") == 0 and book.network_runs("adm_0123456789abcdef") == 0


class TestDatasetBudget:
    def parsed(self, rows: int) -> ParsedDataset:
        return parse_dataset("a,b\n" + "".join(f"{index},{index * 2}\n" for index in range(rows)))

    def test_one_network_holds_at_most_its_share_of_the_store(self) -> None:
        owners = {"s-1": "net_a", "s-2": "net_a", "s-3": "net_b"}
        small = self.parsed(10)
        store = DatasetStore(owner_of=owners.get)
        size = store.owner_bytes("net_a")
        assert size == 0
        store.owner_max_bytes = 2 * dataset_size(small) + 1

        store.put("s-1", small)
        store.put("s-2", small)
        with pytest.raises(StoreFull, match="network"):
            store.put("s-1", small)  # a third version on the same network
        store.put("s-3", small)  # another network has its own share
        store.put("s-9", small)  # a session without a network has only the store's cap
        assert store.owner_bytes("net_a") == 2 * dataset_size(small)

    def test_the_services_tie_the_store_to_the_sessions_networks(self) -> None:
        services = Services()
        services.bind_session("s-1", "net_a")

        assert services.datasets.owner_of is not None and services.datasets.owner_of("s-1") == "net_a"
        assert services.datasets.owner_max_bytes == get_settings().ip_dataset_bytes
        services.purge_session("s-1")
        assert services.network_sessions("net_a") == 0


class TestQueue:
    def test_the_entries_of_one_network_are_capped_together(self) -> None:
        queue = RunQueue(concurrency=10, per_minute=1_000, max_wait_s=600, clock=Clock(), per_user=2, per_network=3)
        net = network_key(NETWORK)
        queue.submit("pub_a", "s-1", network=net)
        queue.submit("pub_a", "s-2", network=net)
        queue.submit("pub_b", "s-3", network=net)

        with pytest.raises(QueueUserLimit):
            queue.submit("pub_c", "s-4", network=net)  # a fresh tab, the same machine
        assert queue.submit("pub_c", "s-5", network=network_key("198.51.100.1")).running
        assert queue.submit("adm_x", "s-6", lane="admin").running  # an admin has no network
        assert queue.network_entries(net) == 3

    def test_the_public_lane_waits_in_at_most_its_share(self) -> None:
        queue = RunQueue(concurrency=1, per_minute=1_000, max_wait_s=600, clock=Clock(), public_waiting=2)
        queue.submit("pub_a", "s-0")  # runs
        queue.submit("pub_b", "s-1")
        queue.submit("pub_c", "s-2")

        with pytest.raises(QueueFull):
            queue.submit("pub_d", "s-3")
        admin = queue.submit("adm_x", "s-4", lane="admin")
        assert admin.waiting and queue.public_waiting_count == 2 and queue.waiting_count == 3

    def test_the_settings_size_both_caps(self) -> None:
        queue = RunQueue.from_settings(AgentSettings())

        assert (queue.per_network, queue.public_waiting) == (4, 10)

    def test_the_caps_must_be_positive(self) -> None:
        for cap in ({"per_network": 0}, {"public_waiting": 0}):
            with pytest.raises(ValueError, match="positive"):
                RunQueue(concurrency=1, per_minute=1, max_wait_s=1, **cap)


def test_the_defaults_double_the_per_user_caps() -> None:
    get_settings.cache_clear()
    settings = get_settings()

    assert settings.ip_max_runs == 2 * settings.user_max_runs
    assert settings.ip_daily_pipeline_runs == 2 * settings.daily_pipeline_runs
    assert settings.ip_daily_token_budget == 2 * settings.daily_token_budget
    assert settings.public_queue_max_waiting == 10
