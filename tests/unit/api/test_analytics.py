"""Tests for server-side Plausible analytics tracking."""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from api.analytics import (
    DOMAIN,
    PLATFORM_PATTERNS,
    _detect_whatsapp_variant,
    detect_ai_agent,
    detect_platform,
    track_og_image,
)


class TestDetectPlatform:
    """Tests for platform detection from User-Agent."""

    def test_detects_twitter(self) -> None:
        """Should detect Twitter bot."""
        assert detect_platform("Twitterbot/1.0") == "twitter"

    def test_detects_whatsapp_ios(self) -> None:
        """Should detect real WhatsApp iOS."""
        assert detect_platform("WhatsApp/2.23.18.78 i") == "whatsapp"

    def test_detects_whatsapp_android(self) -> None:
        """Should detect real WhatsApp Android."""
        assert detect_platform("WhatsApp/2.21.22.23 A") == "whatsapp"

    def test_detects_whatsapp_desktop(self) -> None:
        """Should detect real WhatsApp Desktop."""
        assert detect_platform("WhatsApp/2.2336.9 N") == "whatsapp"

    def test_detects_whatsapp_lite_for_spoofed_ua(self) -> None:
        """Should detect spoofed WhatsApp User-Agent as whatsapp-lite.

        Some apps (Signal, others) use simplified 'WhatsApp' User-Agent to bypass rate limits.
        We can't know for sure which app, so we label it 'whatsapp-lite'.
        See: https://github.com/signalapp/Signal-Android/issues/10060
        """
        # Simplified UA without full version -> whatsapp-lite
        assert detect_platform("WhatsApp") == "whatsapp-lite"
        assert detect_platform("WhatsApp/2") == "whatsapp-lite"
        assert detect_platform("WhatsApp/2.1") == "whatsapp-lite"  # Only 2-part version

    def test_detects_facebook(self) -> None:
        """Should detect Facebook."""
        assert detect_platform("facebookexternalhit/1.1") == "facebook"

    def test_detects_linkedin(self) -> None:
        """Should detect LinkedIn."""
        assert detect_platform("LinkedInBot/1.0") == "linkedin"

    def test_detects_slack(self) -> None:
        """Should detect Slack."""
        assert detect_platform("Slackbot-LinkExpanding 1.0") == "slack"

    def test_detects_discord(self) -> None:
        """Should detect Discord."""
        assert detect_platform("Mozilla/5.0 (compatible; Discordbot/2.0)") == "discord"

    def test_detects_telegram(self) -> None:
        """Should detect Telegram."""
        assert detect_platform("TelegramBot/1.0") == "telegram"

    def test_detects_teams(self) -> None:
        """Should detect Microsoft Teams."""
        assert detect_platform("Mozilla/5.0 Microsoft Teams") == "teams"

    def test_detects_google(self) -> None:
        """Should detect Googlebot."""
        assert detect_platform("Mozilla/5.0 (compatible; Googlebot/2.1)") == "google"

    def test_returns_unknown_for_regular_browser(self) -> None:
        """Should return unknown for regular browsers."""
        assert detect_platform("Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/91.0") == "unknown"

    def test_returns_unknown_for_empty_string(self) -> None:
        """Should return unknown for empty User-Agent."""
        assert detect_platform("") == "unknown"

    def test_case_insensitive(self) -> None:
        """Should match case-insensitively."""
        assert detect_platform("TWITTERBOT/1.0") == "twitter"
        assert detect_platform("twitterbot/1.0") == "twitter"

    def test_all_platforms_have_patterns(self) -> None:
        """Should have 25 platform patterns in dict (whatsapp variants handled separately)."""
        # 27 total platforms: 25 in PLATFORM_PATTERNS + whatsapp + whatsapp-lite (special handling)
        assert len(PLATFORM_PATTERNS) == 25


class TestWhatsAppVariantDetection:
    """Tests for WhatsApp variant detection (real vs spoofed)."""

    def test_real_whatsapp_ios(self) -> None:
        """Real WhatsApp iOS should return 'whatsapp'."""
        assert _detect_whatsapp_variant("WhatsApp/2.23.18.78 i") == "whatsapp"

    def test_real_whatsapp_android(self) -> None:
        """Real WhatsApp Android should return 'whatsapp'."""
        assert _detect_whatsapp_variant("WhatsApp/2.21.22.23 A") == "whatsapp"

    def test_real_whatsapp_cfnetwork(self) -> None:
        """Real WhatsApp with CFNetwork should return 'whatsapp'."""
        assert _detect_whatsapp_variant("WhatsApp/2.18.31.32 CFNetwork/894 Darwin/17.4.0") == "whatsapp"

    def test_spoofed_simple(self) -> None:
        """Simplified WhatsApp UA should return 'whatsapp-lite'."""
        assert _detect_whatsapp_variant("WhatsApp") == "whatsapp-lite"

    def test_spoofed_with_major_version(self) -> None:
        """WhatsApp/2 (no full version) should return 'whatsapp-lite'."""
        assert _detect_whatsapp_variant("WhatsApp/2") == "whatsapp-lite"

    def test_spoofed_with_two_part_version(self) -> None:
        """WhatsApp/2.1 (only 2 parts) should return 'whatsapp-lite'."""
        assert _detect_whatsapp_variant("WhatsApp/2.1") == "whatsapp-lite"

    def test_non_whatsapp_returns_none(self) -> None:
        """Non-WhatsApp User-Agent should return None."""
        assert _detect_whatsapp_variant("Twitterbot/1.0") is None
        assert _detect_whatsapp_variant("Mozilla/5.0") is None
        assert _detect_whatsapp_variant("") is None

    def test_case_insensitive(self) -> None:
        """Should handle case-insensitive matching."""
        assert _detect_whatsapp_variant("WHATSAPP/2.23.18.78") == "whatsapp"
        assert _detect_whatsapp_variant("whatsapp/2.23.18.78") == "whatsapp"
        assert _detect_whatsapp_variant("WHATSAPP") == "whatsapp-lite"


class TestTrackOgImage:
    """Tests for og:image tracking function."""

    @pytest.fixture
    def mock_request(self) -> MagicMock:
        """Create a mock FastAPI request."""
        request = MagicMock()
        request.headers = {"user-agent": "Twitterbot/1.0", "x-forwarded-for": "1.2.3.4"}
        request.client = MagicMock()
        request.client.host = "127.0.0.1"
        return request

    @pytest.fixture
    def mock_create_task(self) -> MagicMock:
        """Create a mock for asyncio.create_task that properly closes coroutines.

        When asyncio.create_task is mocked, the coroutine passed to it is never
        executed. This causes 'coroutine was never awaited' warnings. This fixture
        creates a mock that closes the coroutine to prevent the warning.
        """

        def close_coroutine(coro: object) -> MagicMock:
            """Close the coroutine to prevent 'never awaited' warning."""
            if hasattr(coro, "close"):
                coro.close()
            return MagicMock()

        mock = MagicMock(side_effect=close_coroutine)
        return mock

    def test_creates_async_task(self, mock_request: MagicMock, mock_create_task: MagicMock) -> None:
        """Should create background task without blocking."""
        with patch("api.analytics.asyncio.create_task", mock_create_task):
            track_og_image(mock_request, page="home")
            mock_create_task.assert_called_once()

    def test_home_page_url(self, mock_request: MagicMock, mock_create_task: MagicMock) -> None:
        """Should build correct URL for home page."""
        with patch("api.analytics.asyncio.create_task", mock_create_task):
            track_og_image(mock_request, page="home")
            # Verify create_task was called with a coroutine
            mock_create_task.assert_called_once()

    def test_plots_page_url(self, mock_request: MagicMock, mock_create_task: MagicMock) -> None:
        """Should build correct URL for plots page."""
        with patch("api.analytics.asyncio.create_task", mock_create_task):
            track_og_image(mock_request, page="plots")
            mock_create_task.assert_called_once()

    def test_spec_overview_url(self, mock_request: MagicMock, mock_create_task: MagicMock) -> None:
        """Should build correct URL for spec overview."""
        with patch("api.analytics.asyncio.create_task", mock_create_task):
            # Should not raise even with spec_overview page
            track_og_image(mock_request, page="spec_overview", spec="scatter-basic")

    def test_spec_detail_url(self, mock_request: MagicMock, mock_create_task: MagicMock) -> None:
        """Should build correct URL for spec detail with language slot."""
        with patch("api.analytics.asyncio.create_task", mock_create_task):
            track_og_image(
                mock_request, page="spec_detail", spec="scatter-basic", language="python", library="matplotlib"
            )

    @pytest.mark.asyncio
    async def test_spec_detail_emits_language_url_and_prop(self) -> None:
        """Spec detail should emit /{spec}/{language}/{library} URL and language prop to Plausible."""
        from api.analytics import _send_plausible_event

        with patch("api.analytics.httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client

            await _send_plausible_event(
                user_agent="Twitterbot/1.0",
                client_ip="1.2.3.4",
                name="og_image_view",
                url="https://anyplot.ai/scatter-basic/python/matplotlib",
                props={
                    "page": "spec_detail",
                    "platform": "twitter",
                    "spec": "scatter-basic",
                    "language": "python",
                    "library": "matplotlib",
                },
            )

            payload = mock_client.post.call_args[1]["json"]
            assert payload["url"] == "https://anyplot.ai/scatter-basic/python/matplotlib"
            assert payload["props"]["language"] == "python"
            assert payload["props"]["library"] == "matplotlib"

    def test_fallback_url_when_spec_none(self, mock_request: MagicMock, mock_create_task: MagicMock) -> None:
        """Should fallback to home URL when spec is None for spec-based page."""
        with patch("api.analytics.asyncio.create_task", mock_create_task):
            # Should not raise - falls back to home URL
            track_og_image(mock_request, page="spec_overview", spec=None)

    def test_includes_filter_props(self, mock_request: MagicMock, mock_create_task: MagicMock) -> None:
        """Should include filter parameters in props."""
        with patch("api.analytics.asyncio.create_task", mock_create_task):
            track_og_image(mock_request, page="home", filters={"lib": "plotly", "dom": "statistics"})

    def test_uses_x_forwarded_for(self, mock_create_task: MagicMock) -> None:
        """Should use X-Forwarded-For header for client IP."""
        request = MagicMock()
        request.headers = {"user-agent": "Twitterbot/1.0", "x-forwarded-for": "5.6.7.8"}
        request.client = None

        with patch("api.analytics.asyncio.create_task", mock_create_task):
            track_og_image(request, page="home")

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        ("peer", "forwarded"),
        [
            # Behind Cloud Run the peer is the front end's private address: no header, not a wrong one.
            ("10.0.0.1", None),
            ("127.0.0.1", None),
            # A public peer (a direct caller) is the visitor.
            ("84.75.12.9", "84.75.12.9"),
        ],
    )
    async def test_falls_back_to_a_public_peer_only(self, peer: str, forwarded: str | None) -> None:
        """Without a usable header the socket peer is the visitor only when it is a public address."""
        request = MagicMock()
        request.headers = {"user-agent": "Twitterbot/1.0"}
        request.client = MagicMock()
        request.client.host = peer

        with patch("api.analytics.httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client
            track_og_image(request, page="home")
            await asyncio.sleep(0)

            headers = mock_client.post.call_args[1]["headers"]
            assert headers.get("X-Forwarded-For") == forwarded
            assert ("X-Forwarded-For" in headers) is (forwarded is not None)

    def test_handles_missing_client(self, mock_create_task: MagicMock) -> None:
        """Should handle missing client gracefully."""
        request = MagicMock()
        request.headers = {"user-agent": "Twitterbot/1.0"}
        request.client = None

        with patch("api.analytics.asyncio.create_task", mock_create_task):
            track_og_image(request, page="home")


class TestSendPlausibleEvent:
    """Tests for Plausible API call."""

    @pytest.mark.asyncio
    async def test_sends_correct_payload(self) -> None:
        """Should send correct payload to Plausible."""
        from api.analytics import _send_plausible_event

        with patch("api.analytics.httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client

            await _send_plausible_event(
                user_agent="Twitterbot/1.0",
                client_ip="1.2.3.4",
                name="og_image_view",
                url="https://anyplot.ai/",
                props={"page": "home", "platform": "twitter"},
            )

            mock_client.post.assert_called_once()
            call_kwargs = mock_client.post.call_args[1]
            assert call_kwargs["json"]["name"] == "og_image_view"
            assert call_kwargs["json"]["domain"] == "anyplot.ai"

    @pytest.mark.asyncio
    async def test_handles_network_error(self) -> None:
        """Should handle network errors gracefully."""
        from api.analytics import _send_plausible_event

        with patch("api.analytics.httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.post.side_effect = Exception("Network error")
            mock_client_class.return_value.__aenter__.return_value = mock_client

            # Should not raise
            await _send_plausible_event(
                user_agent="Twitterbot/1.0",
                client_ip="1.2.3.4",
                name="og_image_view",
                url="https://anyplot.ai/",
                props={},
            )


class TestDetectAiAgent:
    """Which assistant, and on whose behalf."""

    @pytest.mark.parametrize(
        ("user_agent", "expected"),
        [
            # The three Anthropic agents differ only by suffix and mean very
            # different things — a broader "claude" pattern would collapse them.
            ("Mozilla/5.0 (compatible; Claude-User/1.0)", ("claude", "user_directed")),
            ("Mozilla/5.0 (compatible; Claude-SearchBot/1.0)", ("claude", "index")),
            ("Mozilla/5.0 (compatible; ClaudeBot/1.0)", ("claude", "training")),
            ("Mozilla/5.0 (compatible; ChatGPT-User/1.0)", ("chatgpt", "user_directed")),
            ("Mozilla/5.0 (compatible; OAI-SearchBot/1.4)", ("chatgpt", "index")),
            ("Mozilla/5.0 (compatible; GPTBot/1.4)", ("chatgpt", "training")),
            ("MistralAI-User/1.0", ("mistral", "user_directed")),
            ("MistralAI-Index/1.0", ("mistral", "index")),
            ("Mozilla/5.0 (compatible; Amzn-User/1.0)", ("amazon", "user_directed")),
            ("Mozilla/5.0 (compatible; Amzn-SearchBot/1.0)", ("amazon", "index")),
            ("meta-externalfetcher/1.1", ("meta", "user_directed")),
            ("Mozilla/5.0 (compatible; Meta-WebIndexer/1.0)", ("meta", "index")),
            # DuckDuckGo's assistant and its search crawler are separate agents
            ("DuckAssistBot/1.2", ("duckduckgo", "user_directed")),
            ("Mozilla/5.0 (compatible; DuckDuckBot/1.1)", ("duckduckgo", "search")),
            # Gemini fetchers embed a full browser UA and identify by suffix
            ("Mozilla/5.0 (X11) Chrome/126.0 Safari/537.36 Google-GeminiNotebook", ("gemini", "user_directed")),
            ("Mozilla/5.0 (compatible; Gemini-Deep-Research)", ("gemini", "user_directed")),
            ("Mozilla/5.0 (compatible; Googlebot/2.1)", ("google", "search")),
            ("Mozilla/5.0 (compatible; Google-InspectionTool/1.0)", ("google", "inspection")),
            ("Mozilla/5.0 (compatible; bingbot/2.0)", ("bing", "search")),
            # The bare xAI tokens the nginx map serves: plain "Grok" (seen
            # 2026-08-19) and "xAI-Bot" without the grok substring (2026-08-28)
            # were prerendered but not counted until these patterns existed.
            ("Grok/1.0", ("grok", "user_directed")),
            ("Mozilla/5.0 (compatible; xAI-Bot/1.0)", ("grok", "user_directed")),
            # xAI's search index carries the bare "xai" token too; ordered before it,
            # it is an index read, not a person's fetch (a live sample read it as one).
            ("Mozilla/5.0 (compatible; xAI-SearchBot/1.0)", ("grok", "index")),
            ("Mozilla/5.0 AppleWebKit/537.36 (KHTML, like Gecko; compatible; Amazonbot/0.1)", ("amazon", "index")),
            (
                "meta-externalagent/1.1 (+https://developers.facebook.com/docs/sharing/webmasters/crawler)",
                ("meta", "training"),
            ),
            ("Mozilla/5.0 (compatible; AhrefsBot/7.0; +http://ahrefs.com/robot/)", ("ahrefs", "seo")),
            ("Mozilla/5.0 (compatible; SemrushBot/7~bl; +http://www.semrush.com/bot.html)", ("semrush", "seo")),
            ("Mozilla/5.0 (compatible; DataForSeoBot/1.0)", ("dataforseo", "seo")),
            ("Mozilla/5.0 (compatible; Google-CloudVertexBot; +https://cloud.google.com)", ("gemini", "index")),
            ("Mozilla/5.0 (compatible; ExaSearchBot/1.0)", ("exa", "index")),
            ("Keenable-User/1.0 (+https://keenable.ai/bot)", ("keenable", "user_directed")),
            ("Keenable-SearchBot/1.0 (+https://keenable.ai/bot)", ("keenable", "index")),
            ("Mozilla/5.0 (Linux; Android 5.0) AppleWebKit/537.36 (compatible; Bytespider)", ("bytedance", "training")),
            ("CCBot/2.0 (https://commoncrawl.org/faq/)", ("commoncrawl", "training")),
            ("Mozilla/5.0 (compatible; Qwantbot/2.1)", ("qwant", "search")),
            (
                "Mozilla/5.0 (compatible; PetalBot;+https://webmaster.petalsearch.com/site/petalbot)",
                ("huawei", "search"),
            ),
            ("Sogou web spider/4.0(+http://www.sogou.com/docs/help/webmasters.htm#07)", ("sogou", "search")),
            ("Mozilla/5.0 (compatible; MJ12bot/v1.4.8; http://mj12bot.com/)", ("majestic", "seo")),
            ("Mozilla/5.0 (compatible; DotBot/1.2; +https://opensiteexplorer.org/dotbot)", ("moz", "seo")),
            ("Mozilla/5.0 (compatible; HaloBot/1.0)", ("haloscan", "seo")),
        ],
    )
    def test_classifies(self, user_agent: str, expected: tuple[str, str]) -> None:
        assert detect_ai_agent(user_agent) == expected

    @pytest.mark.parametrize(
        "user_agent",
        [
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/126.0 Safari/537.36",
            "Twitterbot/1.0",
            "Slackbot-LinkExpanding 1.0",
            # Sogou's browser, which people use: only the spider's full token is a crawler.
            "Mozilla/5.0 (Linux; Android 10) AppleWebKit/537.36 Chrome/88.0 Mobile Safari/537.36 SogouMobileBrowser/5.38.6",
            "",
        ],
    )
    def test_ignores_humans_and_non_ai_bots(self, user_agent: str) -> None:
        """Link-preview and social bots are not agents reading the catalogue."""
        assert detect_ai_agent(user_agent) is None


class TestOgImageAudienceSplit:
    """A shared link is a human signal on anyplot.ai; a crawler's fetch is a machine read and never a Plausible event."""

    @staticmethod
    def _request(user_agent: str) -> MagicMock:
        request = MagicMock()
        request.headers = {"user-agent": user_agent}
        request.client.host = "203.0.113.7"
        return request

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "user_agent",
        ["Twitterbot/1.0", "facebookexternalhit/1.1", "Slackbot-LinkExpanding 1.0", "WhatsApp/2.23.18.78 i"],
    )
    async def test_a_shared_link_stays_with_the_human_numbers(self, user_agent: str) -> None:
        """A preview fetch means someone shared the page — that is a product signal."""
        with patch("api.analytics.httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client

            track_og_image(self._request(user_agent), page="spec_detail", spec="box-basic")
            await asyncio.sleep(0)

            payload = mock_client.post.call_args[1]["json"]
            assert payload["domain"] == DOMAIN
            assert "assistant" not in payload["props"]

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "user_agent",
        [
            "Mozilla/5.0 (compatible; Googlebot/2.1)",
            "Mozilla/5.0 (compatible; Claude-User/1.0)",
            "Mozilla/5.0 (compatible; GPTBot/1.4)",
            "Mozilla/5.0 (compatible; AhrefsBot/7.0)",
        ],
    )
    async def test_a_crawler_fetch_sends_nothing(self, user_agent: str) -> None:
        """Since /og/ is crawlable these arrive in volume. On anyplot.ai they would drown the sharing signal and
        inflate visitors; the machine-read line (api/machine_reads.py) records them instead."""
        with patch("api.analytics.httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client

            with patch("api.analytics.asyncio.create_task") as create_task:
                track_og_image(self._request(user_agent), page="spec_detail", spec="box-basic")
            await asyncio.sleep(0)

            create_task.assert_not_called()
            mock_client.post.assert_not_called()

    @pytest.mark.asyncio
    async def test_the_main_site_still_sees_the_real_agent(self) -> None:
        """A shared link is human behaviour and its platform detection matters."""
        with patch("api.analytics.httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client

            track_og_image(self._request("Twitterbot/1.0"), page="spec_detail", spec="box-basic")
            await asyncio.sleep(0)

            call = mock_client.post.call_args[1]
            assert call["json"]["domain"] == DOMAIN
            assert call["headers"]["User-Agent"] == "Twitterbot/1.0"


class TestVisitorIpValidation:
    """Plausible uses "the first VALID IP address from the list"; the API hands it a public one."""

    @staticmethod
    def _request(headers: dict[str, str]) -> MagicMock:
        request = MagicMock()
        request.headers = headers
        request.client.host = "127.0.0.1"
        return request

    @pytest.mark.parametrize(
        ("headers", "expected"),
        [
            # `unknown` is the classic proxy filler; skip it, do not forward it
            ({"x-forwarded-for": "unknown, 84.75.12.9"}, "84.75.12.9"),
            ({"cf-connecting-ip": "garbage", "x-forwarded-for": "84.75.12.9"}, "84.75.12.9"),
            ({"x-forwarded-for": "2a02:1210::1, 10.0.0.1"}, "2a02:1210::1"),
            # cf-connecting-ip first: Cloudflare overwrites it, so through the
            # edge it cannot be forged, while the forwarded list can.
            ({"cf-connecting-ip": "34.90.1.1", "x-forwarded-for": "84.75.12.9, 172.68.0.1, 34.90.1.1"}, "34.90.1.1"),
            # A direct client behind Cloudflare: both headers name the visitor
            ({"cf-connecting-ip": "84.75.12.9", "x-forwarded-for": "84.75.12.9"}, "84.75.12.9"),
            ({"cf-connecting-ip": "84.75.12.9"}, "84.75.12.9"),
            # A forged private address at the front of the list is skipped, not
            # handed to Plausible as the visitor.
            ({"x-forwarded-for": "10.0.0.9, 84.75.12.9"}, "84.75.12.9"),
            ({"cf-connecting-ip": "192.168.1.1", "x-forwarded-for": "84.75.12.9"}, "84.75.12.9"),
            # Documentation (TEST-NET), loopback, CGNAT, link-local, unique-local
            # and unspecified addresses are not public either; neither is multicast,
            # which `is_global` alone would let through.
            ({"x-forwarded-for": "203.0.113.7"}, ""),
            ({"x-forwarded-for": "100.64.0.1, 169.254.1.1, fd00::1, fe80::1, ::1, 0.0.0.0, 84.75.12.9"}, "84.75.12.9"),
            ({"x-forwarded-for": "224.0.0.1, 84.75.12.9"}, "84.75.12.9"),
            # Nothing usable anywhere, and the socket peer (127.0.0.1 here, Cloud
            # Run's front end in production) is not public either: no address.
            ({"x-forwarded-for": "nonsense"}, ""),
            ({}, ""),
        ],
    )
    def test_takes_the_first_public_address(self, headers: dict[str, str], expected: str) -> None:
        from api.request_context import visitor_ip

        assert visitor_ip(self._request(headers)) == expected
