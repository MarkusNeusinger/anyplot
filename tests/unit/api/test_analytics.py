"""Tests for the vendor table of the machine reads (`api/analytics.py`)."""

import pytest

from api.analytics import detect_ai_agent


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
