"""Tests for the share counter (`api/shared_links.py`) and its two endpoints.

What is under test: who counts as having shared a link, that nothing but a
closed set of names reaches the table, that only the production service
counts, and that the public numbers leave out what the owner's section shows.
"""

import asyncio
from collections.abc import Iterator
from datetime import date, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.exc import ProgrammingError

from api import shared_links
from api.cache import clear_cache
from api.main import app, fastapi_app
from api.routers.debug import require_admin
from api.shared_links import (
    OTHER,
    SHARE_PLATFORMS,
    TOP_PLOTS,
    WINDOW_DAYS,
    SharedLinksDetail,
    read_detail,
    record_share,
    share_platform,
    window_start,
)
from core.config import settings
from core.database import get_db
from core.database.models import SHARE_PAGES


TODAY = date(2026, 11, 11)
SLACK = "Slackbot-LinkExpanding 1.0 (+https://api.slack.com/robots)"
BROWSER = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/149.0.0.0 Safari/537.36"


def _request(user_agent: str, **headers: str) -> MagicMock:
    """A fetch of a preview image through the edge; *headers* by their lowercase names, `_` for `-`."""
    request = MagicMock()
    request.url.path = "/og/home.png"
    request.headers = {
        "user-agent": user_agent,
        "host": "api.anyplot.ai",
        **{name.replace("_", "-"): value for name, value in headers.items()},
    }
    return request


class TestSharePlatform:
    """The platform is one name of a closed set, read from the user agent."""

    @pytest.mark.parametrize(
        ("user_agent", "platform"),
        [
            ("Twitterbot/1.0", "twitter"),
            ("facebookexternalhit/1.1 (+http://www.facebook.com/externalhit_uatext.php)", "facebook"),
            ("LinkedInBot/1.0 (compatible; Mozilla/5.0; Apache-HttpClient +http://www.linkedin.com)", "linkedin"),
            ("Pinterestbot/1.0", "pinterest"),
            ("redditbot/1.0", "reddit"),
            ("Tumblr/14.0.835.186", "tumblr"),
            ("http.rb/5.1.1 (Mastodon/4.2.0; +https://mastodon.social/)", "mastodon"),
            (SLACK, "slack"),
            # The image itself comes through Slack's image proxy, which carries no "slackbot".
            ("Slack-ImgProxy (+https://api.slack.com/robots)", "slack"),
            ("Mozilla/5.0 (compatible; Discordbot/2.0; +https://discordapp.com)", "discord"),
            # Telegram's own user agent names Twitter: it must not be counted there.
            ("TelegramBot (like TwitterBot)", "telegram"),
            ("Viber/16.0", "viber"),
            # Microsoft's preview service, as it arrives; Skype closed in May 2025.
            (
                "Mozilla/5.0 (Windows NT 6.1; WOW64) SkypeUriPreview Preview/0.5 skype-url-preview@microsoft.com",
                "teams",
            ),
            ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) Microsoft Teams", "teams"),
            ("Snapchat/12.0", "snapchat"),
            ("github-camo (f7b8fdd5)", "github"),
            ("Mozilla/5.0 (compatible; Embedly/0.2; +http://support.embed.ly/)", "embedly"),
            ("Quora Link Preview/1.0", "quora"),
            ("TWITTERBOT/1.0", "twitter"),
            # Apple's Messages borrows both names at once: neither Facebook nor Twitter.
            (
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_1) AppleWebKit/601.2.4 (KHTML, like Gecko) "
                "Version/9.0.1 Safari/601.2.4 facebookexternalhit/1.1 Facebot Twitterbot/1.0",
                "imessage",
            ),
        ],
    )
    def test_names_a_preview_platform(self, user_agent: str, platform: str) -> None:
        assert share_platform(user_agent) == platform

    @pytest.mark.parametrize(
        ("user_agent", "platform"),
        [
            # The real app sends its full version; Signal and others borrow the bare name.
            ("WhatsApp/2.23.18.78 i", "whatsapp"),
            ("WhatsApp/2.21.22.23 A", "whatsapp"),
            ("WhatsApp/2.2587.9 W", "whatsapp"),
            ("WhatsApp", "whatsapp-lite"),
            ("WhatsApp/2", "whatsapp-lite"),
            ("whatsapp/2.23", "whatsapp-lite"),
            # WhatsApp is asked first, whatever else the string carries.
            ("WhatsApp/2.23.18.78 i Twitterbot", "whatsapp"),
        ],
    )
    def test_tells_whatsapp_from_the_apps_that_borrow_its_name(self, user_agent: str, platform: str) -> None:
        assert share_platform(user_agent) == platform

    @pytest.mark.parametrize(
        "user_agent",
        [
            BROWSER,
            "",
            "curl/8.5.0",
            "python-requests/2.32",
            # A search engine is no preview platform. The counter never sees one, because
            # `detect_ai_agent` takes it first; on its own it is nobody this table knows.
            "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)",
            "Mozilla/5.0 (compatible; YandexBot/3.0)",
            # An app the table does not know yet.
            "Bluesky Cardyb/1.1; +mailto:support@bsky.app",
        ],
    )
    def test_everything_else_is_other(self, user_agent: str) -> None:
        assert share_platform(user_agent) == OTHER

    def test_no_user_agent_text_can_become_a_platform(self) -> None:
        """Whatever a client writes, the answer is a name this module spelled itself."""
        names = {*SHARE_PLATFORMS, OTHER}
        for user_agent in ("'; DROP TABLE link_shares; --", "x" * 5000, "slackbot\nplatform=evil", "ＷhatsApp"):
            assert share_platform(user_agent) in names

    def test_every_platform_name_fits_the_column(self) -> None:
        assert {"whatsapp", "whatsapp-lite", "slack", "teams", "github"} <= SHARE_PLATFORMS
        for name in (*SHARE_PLATFORMS, OTHER):
            assert 0 < len(name) <= 32
            assert name == name.lower()

    def test_an_apple_device_preview_is_other_for_now(self) -> None:
        """Seen in the request log, about ten a week: Apple's on-device link preview. Which app asked is
        not in the user agent, so it has no platform name yet; `other` on /debug is where it shows."""
        assert share_platform("NetworkingExtension/8621.1.15.11.7 Network/5569.42.2 iOS/26.1") == OTHER


class TestRecordShare:
    """Who is counted, and that only the production service counts."""

    @pytest.fixture
    def counted(self) -> Iterator[AsyncMock]:
        """The background write, replaced: what it was called with is what would be counted."""
        with patch.object(shared_links, "_count", new_callable=AsyncMock) as write:
            yield write

    @staticmethod
    async def _settle() -> None:
        for write in list(shared_links._WRITES):
            await write

    async def test_counts_a_preview_platform_in_production(self, counted: AsyncMock) -> None:
        with patch.object(settings, "environment", "production"), patch.object(shared_links, "datetime") as clock:
            clock.now.return_value.date.return_value = TODAY
            record_share(
                _request(SLACK), page="spec_detail", spec_id="scatter-basic", language="python", library_id="matplotlib"
            )
            await self._settle()

        counted.assert_awaited_once_with(TODAY, "slack", False, "spec_detail", "scatter-basic", "python", "matplotlib")

    async def test_counts_an_unknown_client_as_other(self, counted: AsyncMock) -> None:
        with patch.object(settings, "environment", "production"):
            record_share(_request(BROWSER), page="home")
            await self._settle()

        assert counted.await_args.args[1:] == (OTHER, False, "home", "", "", "")

    @pytest.mark.parametrize(
        ("headers", "verified"),
        [
            ({"x_verified_bot_category": "Page Preview"}, True),
            # A category the API's list does not know yet is still Cloudflare's word.
            ({"x_verified_bot_category": "Something New"}, True),
            ({}, False),
            ({"x_verified_bot_category": " "}, False),
            # nginx's copy of the verdict counts on its own hop paths only, and an image is none.
            ({"x_prerender_bot_category": "Page Preview"}, False),
            # The raw origin is not behind the edge, so the header there is the caller's own.
            ({"x_verified_bot_category": "Page Preview", "host": "anyplot-api-abc-ez.a.run.app"}, False),
        ],
        ids=["verified", "unlisted-category", "no-verdict", "blank", "hop-copy", "raw-origin"],
    )
    async def test_records_whether_cloudflare_verified_the_fetcher(
        self, counted: AsyncMock, headers: dict[str, str], verified: bool
    ) -> None:
        """The user agent is the client's own claim; the edge's verdict is not, and it is all that is left
        to tell a platform from a client signing as it once the user agent is dropped."""
        with patch.object(settings, "environment", "production"):
            record_share(_request(SLACK, **headers), page="home")
            await self._settle()

        assert counted.await_args.args[1:3] == ("slack", verified)

    @pytest.mark.parametrize("environment", ["development", "test", "staging"])
    async def test_counts_nothing_outside_production(self, counted: AsyncMock, environment: str) -> None:
        """A test or a local request for an image is no share. Until 2026-11-11 both sent a real event."""
        with patch.object(settings, "environment", environment):
            record_share(_request(SLACK), page="home")
            await self._settle()

        counted.assert_not_called()

    @pytest.mark.parametrize(
        "user_agent",
        [
            "Mozilla/5.0 (compatible; ClaudeBot/1.0)",
            "Mozilla/5.0 (compatible; Googlebot/2.1)",
            "Mozilla/5.0 (compatible; PerplexityBot/1.0)",
            "Mozilla/5.0 (compatible; AhrefsBot/7.0; +http://ahrefs.com/robot/)",
        ],
    )
    async def test_a_crawler_fetch_is_a_machine_read_not_a_share(self, counted: AsyncMock, user_agent: str) -> None:
        with patch.object(settings, "environment", "production"):
            record_share(_request(user_agent), page="spec_overview", spec_id="scatter-basic")
            await self._settle()

        counted.assert_not_called()

    async def test_counts_only_the_pages_that_have_a_preview_image(self, counted: AsyncMock) -> None:
        with patch.object(settings, "environment", "production"):
            record_share(_request(SLACK), page="legal")
            await self._settle()

        counted.assert_not_called()

    async def test_a_failed_write_reaches_nobody(self) -> None:
        """The image is already out. A missing table is the case that will happen: the migration
        reaches production after the merge, which can be later than the deploy."""
        missing = ProgrammingError("INSERT", {}, Exception('relation "link_shares" does not exist'))

        class Broken:
            async def __aenter__(self) -> None:
                raise missing

            async def __aexit__(self, *exc: object) -> None:
                return None

        with (
            patch.object(settings, "environment", "production"),
            patch.object(shared_links, "get_db_context", return_value=Broken()),
            patch.object(shared_links.logger, "warning") as warned,
        ):
            record_share(_request(SLACK), page="home")
            await self._settle()

        warned.assert_called_once()
        # The exception's class, never its text: the statement and its values stay out of the log.
        assert warned.call_args.args[1] == "ProgrammingError"
        assert not shared_links._WRITES

    async def test_the_write_holds_no_address_and_no_user_agent(self, counted: AsyncMock) -> None:
        """A row is a count and the seven values that name it: nothing of the request goes further."""
        request = _request(
            SLACK,
            cf_connecting_ip="203.0.113.7",
            x_forwarded_for="203.0.113.7, 10.0.0.1",
            x_verified_bot_category="Page Preview",
        )
        request.client.host = "203.0.113.7"
        with patch.object(settings, "environment", "production"):
            record_share(request, page="plots")
            await self._settle()

        written = " ".join(str(value) for value in counted.await_args.args)
        assert "203.0.113.7" not in written
        assert "Slackbot" not in written and "LinkExpanding" not in written
        # The verdict is kept as yes or no, never as the category Cloudflare named.
        assert "Page Preview" not in written
        assert len(counted.await_args.args) == 7


class FakeRepository:
    """The two reads of `LinkShareRepository`, over rows held in a list."""

    def __init__(self, rows: list[tuple[date, str, bool, str, str, str, int]]) -> None:
        self.rows = rows  # (day, platform, verified, spec_id, language, library_id, fetches)

    async def by_day_and_platform(self, since: date, until: date) -> list[tuple[date, str, bool, int]]:
        totals: dict[tuple[date, str, bool], int] = {}
        for day, platform, verified, _spec, _language, _library, fetches in self.rows:
            if since <= day <= until:
                totals[day, platform, verified] = totals.get((day, platform, verified), 0) + fetches
        return [(*key, fetches) for key, fetches in sorted(totals.items())]

    async def top_plots(
        self, since: date, until: date, *, without_platform: str, limit: int
    ) -> list[tuple[str, str, str, int]]:
        totals: dict[tuple[str, str, str], int] = {}
        for day, platform, _verified, spec_id, language, library_id, fetches in self.rows:
            if since <= day <= until and platform != without_platform and spec_id:
                key = (spec_id, language, library_id)
                totals[key] = totals.get(key, 0) + fetches
        ranked = sorted(totals.items(), key=lambda item: (-item[1], item[0]))
        return [(*key, fetches) for key, fetches in ranked[:limit]]


ROWS = [
    (TODAY, "whatsapp", False, "scatter-basic", "python", "matplotlib", 3),
    (TODAY, "slack", True, "scatter-basic", "", "", 1),
    (TODAY, "slack", False, "scatter-basic", "", "", 1),
    (TODAY, OTHER, False, "", "", "", 38),
    (TODAY, OTHER, True, "", "", "", 2),
    (TODAY - timedelta(days=1), "whatsapp", False, "", "", "", 1),
    (TODAY - timedelta(days=1), OTHER, False, "scatter-basic", "python", "matplotlib", 9),
    (TODAY - timedelta(days=WINDOW_DAYS - 1), "linkedin", True, "heatmap-basic", "r", "ggplot2", 4),
    # The day before the window, and a day after today: neither is in it.
    (TODAY - timedelta(days=WINDOW_DAYS), "twitter", True, "scatter-basic", "", "", 50),
    (TODAY + timedelta(days=1), "twitter", True, "scatter-basic", "", "", 60),
]


class TestReadDetail:
    """The window's numbers: what is a share, and what is only shown to the owner."""

    async def test_window_is_28_utc_days_ending_today(self) -> None:
        assert window_start(TODAY) == date(2026, 10, 15)
        detail = await read_detail(FakeRepository([]), TODAY)  # type: ignore[arg-type]
        assert detail.status == "ok"
        assert [day.date for day in detail.days] == [
            (date(2026, 10, 15) + timedelta(days=offset)).isoformat() for offset in range(28)
        ]
        assert all(day.shares == 0 for day in detail.days)
        assert detail.total == 0 and detail.platforms == [] and detail.top == [] and detail.other == 0
        assert detail.verified == {}

    async def test_other_is_kept_apart_from_every_number(self) -> None:
        detail = await read_detail(FakeRepository(ROWS), TODAY)  # type: ignore[arg-type]

        assert detail.other == 49
        assert detail.total == 10  # 3 + 2 + 1 + 4, and nothing of the 49
        assert detail.days[-1].shares == 5 and detail.days[-2].shares == 1 and detail.days[0].shares == 4
        assert [(entry.platform, entry.shares) for entry in detail.platforms] == [
            ("linkedin", 4),
            ("whatsapp", 4),
            ("slack", 2),
        ]

    async def test_verified_is_counted_per_platform_and_changes_no_other_number(self) -> None:
        """A share counts whatever the verdict: WhatsApp fetches from the sender's phone, which nobody verifies."""
        detail = await read_detail(FakeRepository(ROWS), TODAY)  # type: ignore[arg-type]

        assert detail.verified == {"linkedin": 4, OTHER: 2, "slack": 1}  # whatsapp has none, so it is absent
        assert detail.total == 10 and detail.other == 49

    async def test_top_plots_are_pages_shared_by_named_platforms(self) -> None:
        detail = await read_detail(FakeRepository(ROWS), TODAY)  # type: ignore[arg-type]

        assert [(plot.spec_id, plot.language, plot.library, plot.shares) for plot in detail.top] == [
            ("heatmap-basic", "r", "ggplot2", 4),
            ("scatter-basic", "python", "matplotlib", 3),  # not 12: the 9 are `other`
            ("scatter-basic", None, None, 2),  # the hub, an entry of its own
        ]

    async def test_lists_at_most_five_plots(self) -> None:
        rows = [(TODAY, "slack", True, f"spec-{index}", "", "", index + 1) for index in range(TOP_PLOTS + 3)]
        detail = await read_detail(FakeRepository(rows), TODAY)  # type: ignore[arg-type]
        assert len(detail.top) == TOP_PLOTS
        assert detail.top[0].shares == TOP_PLOTS + 3


@pytest.fixture(autouse=True)
def fresh_cache() -> Iterator[None]:
    clear_cache()
    yield
    clear_cache()
    fastapi_app.dependency_overrides.clear()


DETAIL = SharedLinksDetail(
    status="ok",
    total=10,
    days=[],
    platforms=[{"platform": "whatsapp", "shares": 4}],  # type: ignore[list-item]
    top=[{"spec_id": "scatter-basic", "shares": 2}],  # type: ignore[list-item]
    other=49,
    verified={"slack": 1, OTHER: 2},
)


class TestPublicEndpoint:
    """`GET /insights/shared-links`: the named platforms' shares, cached, never `other`."""

    def test_answers_the_public_numbers_without_other(self) -> None:
        async def detail(_repository: object) -> SharedLinksDetail:
            return DETAIL

        session = MagicMock()
        session.__aenter__ = AsyncMock(return_value=session)
        session.__aexit__ = AsyncMock(return_value=None)
        with (
            patch("api.routers.insights.is_db_configured", return_value=True),
            patch.object(shared_links, "get_db_context", return_value=session),
            patch.object(shared_links, "read_detail", side_effect=detail),
        ):
            response = TestClient(app).get("/insights/shared-links")

        assert response.status_code == 200
        body = response.json()
        assert body["status"] == "ok" and body["total"] == 10 and body["window_days"] == 28
        assert body["platforms"] == [{"platform": "whatsapp", "shares": 4}]
        assert body["top"] == [{"spec_id": "scatter-basic", "language": None, "library": None, "shares": 2}]
        assert "other" not in body and "verified" not in body

    def test_is_not_configured_without_a_database(self) -> None:
        with patch("api.routers.insights.is_db_configured", return_value=False):
            body = TestClient(app).get("/insights/shared-links").json()
        assert body["status"] == "not_configured" and body["total"] == 0 and body["days"] == []

    def test_a_failed_read_is_unavailable_and_is_not_kept(self) -> None:
        """Before the migration ran the table is missing: the tile says so, and the next load asks again."""
        calls = 0

        async def load() -> object:
            nonlocal calls
            calls += 1
            if calls == 1:
                raise ProgrammingError("SELECT", {}, Exception('relation "link_shares" does not exist'))
            return shared_links.SharedLinksResponse(status="ok", total=3)

        with (
            patch("api.routers.insights.is_db_configured", return_value=True),
            patch("api.routers.insights.load_public", side_effect=load),
        ):
            client = TestClient(app)
            first = client.get("/insights/shared-links").json()
            second = client.get("/insights/shared-links").json()

        assert first["status"] == "unavailable" and first["total"] == 0
        assert second["status"] == "ok" and second["total"] == 3


class TestDebugEndpoint:
    """`GET /debug/shared-links`: the same numbers plus `other`, for an admin only."""

    @staticmethod
    def _client(session: AsyncMock) -> TestClient:
        async def get_session():
            yield session

        fastapi_app.dependency_overrides[get_db] = get_session
        fastapi_app.dependency_overrides[require_admin] = lambda: None
        return TestClient(app)

    def test_shows_other_to_an_admin(self) -> None:
        async def detail(_repository: object) -> SharedLinksDetail:
            return DETAIL

        with (
            patch("api.dependencies.is_db_configured", return_value=True),
            patch("api.routers.debug.read_shared_links", side_effect=detail),
        ):
            body = self._client(AsyncMock()).get("/debug/shared-links").json()

        assert body["status"] == "ok" and body["other"] == 49 and body["total"] == 10
        assert body["verified"] == {"slack": 1, "other": 2}

    def test_is_unavailable_while_the_table_is_missing(self) -> None:
        async def missing(_repository: object) -> SharedLinksDetail:
            raise ProgrammingError("SELECT", {}, Exception('relation "link_shares" does not exist'))

        with (
            patch("api.dependencies.is_db_configured", return_value=True),
            patch("api.routers.debug.read_shared_links", side_effect=missing),
        ):
            response = self._client(AsyncMock()).get("/debug/shared-links")

        assert response.status_code == 200
        assert response.json() == {**SharedLinksDetail(status="unavailable").model_dump()}

    def test_refuses_a_visitor(self) -> None:
        with patch("api.dependencies.is_db_configured", return_value=True):
            response = TestClient(app).get("/debug/shared-links")
        assert response.status_code in (401, 403, 503)


def test_the_pages_are_the_four_with_a_preview_image() -> None:
    """The closed set the table's CHECK holds and the image router's calls name."""
    assert SHARE_PAGES == ("home", "plots", "spec_overview", "spec_detail")
    source = (asyncio.run(_router_source())).replace('"', "'")
    for page in SHARE_PAGES:
        assert f"page='{page}'" in source or f"'page': '{page}'" in source


async def _router_source() -> str:
    from pathlib import Path

    return Path("api/routers/og_images.py").read_text(encoding="utf-8")
