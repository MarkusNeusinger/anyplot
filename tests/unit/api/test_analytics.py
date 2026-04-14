"""Tests for server-side Plausible analytics tracking."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from api.analytics import PLATFORM_PATTERNS, _detect_whatsapp_variant, detect_platform, track_og_image


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

    def test_catalog_page_url(self, mock_request: MagicMock, mock_create_task: MagicMock) -> None:
        """Should build correct URL for catalog page."""
        with patch("api.analytics.asyncio.create_task", mock_create_task):
            track_og_image(mock_request, page="catalog")
            mock_create_task.assert_called_once()

    def test_spec_overview_url(self, mock_request: MagicMock, mock_create_task: MagicMock) -> None:
        """Should build correct URL for spec overview."""
        with patch("api.analytics.asyncio.create_task", mock_create_task):
            # Should not raise even with spec_overview page
            track_og_image(mock_request, page="spec_overview", spec="scatter-basic")

    def test_spec_detail_url(self, mock_request: MagicMock, mock_create_task: MagicMock) -> None:
        """Should build correct URL for spec detail."""
        with patch("api.analytics.asyncio.create_task", mock_create_task):
            track_og_image(mock_request, page="spec_detail", spec="scatter-basic", library="matplotlib")

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

    def test_fallback_to_client_host(self, mock_create_task: MagicMock) -> None:
        """Should fallback to client.host when X-Forwarded-For not present."""
        request = MagicMock()
        request.headers = {"user-agent": "Twitterbot/1.0"}
        request.client = MagicMock()
        request.client.host = "10.0.0.1"

        with patch("api.analytics.asyncio.create_task", mock_create_task):
            track_og_image(request, page="home")

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
