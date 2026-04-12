"""
Extended tests for analytics module.

Covers edge cases and additional platform patterns.
"""

import pytest

from api.analytics import (
    PLATFORM_PATTERNS,
    _detect_whatsapp_variant,
    detect_platform,
)


class TestDetectWhatsappVariant:
    """Tests for _detect_whatsapp_variant edge cases."""

    def test_no_whatsapp(self) -> None:
        assert _detect_whatsapp_variant("Mozilla/5.0") is None

    def test_real_whatsapp_ios(self) -> None:
        assert _detect_whatsapp_variant("WhatsApp/2.23.18.78 i") == "whatsapp"

    def test_real_whatsapp_android(self) -> None:
        assert _detect_whatsapp_variant("WhatsApp/2.21.22.23 A") == "whatsapp"

    def test_signal_spoofed_simple(self) -> None:
        assert _detect_whatsapp_variant("WhatsApp") == "whatsapp-lite"

    def test_signal_spoofed_short_version(self) -> None:
        assert _detect_whatsapp_variant("WhatsApp/2") == "whatsapp-lite"

    def test_signal_spoofed_two_part_version(self) -> None:
        assert _detect_whatsapp_variant("WhatsApp/2.23") == "whatsapp-lite"

    def test_case_insensitive(self) -> None:
        assert _detect_whatsapp_variant("whatsapp/2.23.18.78 i") == "whatsapp"


class TestDetectPlatformExtended:
    """Additional platform detection tests for full coverage."""

    def test_slack(self) -> None:
        assert detect_platform("Slackbot 1.0 (+https://api.slack.com/robots)") == "slack"

    def test_discord(self) -> None:
        assert detect_platform("Mozilla/5.0 (compatible; Discordbot/2.0)") == "discord"

    def test_telegram(self) -> None:
        assert detect_platform("TelegramBot/1.0") == "telegram"

    def test_linkedin(self) -> None:
        assert detect_platform("LinkedInBot/1.0") == "linkedin"

    def test_pinterest(self) -> None:
        assert detect_platform("Pinterestbot/1.0") == "pinterest"

    def test_reddit(self) -> None:
        assert detect_platform("redditbot/1.0") == "reddit"

    def test_google(self) -> None:
        assert detect_platform("Mozilla/5.0 (compatible; Googlebot/2.1)") == "google"

    def test_bing(self) -> None:
        assert detect_platform("Mozilla/5.0 (compatible; bingbot/2.0)") == "bing"

    def test_mastodon(self) -> None:
        assert detect_platform("http.rb/5.0.0 (Mastodon/4.0; +https://instance.social/)") == "mastodon"

    def test_viber(self) -> None:
        assert detect_platform("Viber/13.0") == "viber"

    def test_skype(self) -> None:
        assert detect_platform("SkypeUriPreview") == "skype"

    def test_teams(self) -> None:
        assert detect_platform("Mozilla/5.0 Microsoft Teams") == "teams"

    def test_snapchat(self) -> None:
        assert detect_platform("Snapchat/10.0") == "snapchat"

    def test_yandex(self) -> None:
        assert detect_platform("Mozilla/5.0 (compatible; YandexBot/3.0)") == "yandex"

    def test_duckduckgo(self) -> None:
        assert detect_platform("DuckDuckBot/1.0") == "duckduckgo"

    def test_baidu(self) -> None:
        assert detect_platform("Mozilla/5.0 (compatible; Baiduspider/2.0)") == "baidu"

    def test_apple(self) -> None:
        assert detect_platform("Applebot/0.1") == "apple"

    def test_embedly(self) -> None:
        assert detect_platform("Embedly/0.2") == "embedly"

    def test_quora(self) -> None:
        assert detect_platform("Quora Link Preview/1.0") == "quora"

    def test_tumblr(self) -> None:
        assert detect_platform("Tumblr/14.0") == "tumblr"

    def test_unknown_agent(self) -> None:
        assert detect_platform("Some Random Bot/1.0") == "unknown"

    def test_empty_agent(self) -> None:
        assert detect_platform("") == "unknown"

    def test_whatsapp_takes_priority(self) -> None:
        """WhatsApp detection happens before general pattern matching."""
        assert detect_platform("WhatsApp/2.23.18.78 i") == "whatsapp"

    def test_platform_patterns_not_empty(self) -> None:
        """Ensure we have a comprehensive set of platform patterns."""
        assert len(PLATFORM_PATTERNS) >= 20
