"""Server-side Plausible Analytics for og:image tracking, and the vendor table of the machine reads.

Tracks og:image requests from social media and messenger previews (Twitter,
WhatsApp, etc.), which run no JavaScript and can't be tracked client-side. A
preview means a person shared a link, so it is a human signal and goes to the
anyplot.ai site. A crawler's or an AI assistant's fetch of the same image is a
machine read: `api/machine_reads.py` writes its line and nothing goes to
Plausible.

`AI_AGENTS` is the vendor table both machine-read writers use
(`api/machine_reads.py`, and the `$machine_agent` map of `app/nginx.conf`).

Uses fire-and-forget pattern to avoid delaying responses.
"""

import asyncio
import logging
import re

import httpx
from fastapi import Request

from api.request_context import visitor_ip


logger = logging.getLogger(__name__)

PLAUSIBLE_ENDPOINT = "https://plausible.io/api/event"
DOMAIN = "anyplot.ai"

# Which assistant, and on whose behalf. The distinction is the point: a
# user-directed fetch means a person asked their assistant to open this page,
# which is a reader; an index crawler is building a corpus with no one waiting.
# Ordered most-specific first — matching is substring-based, and e.g.
# "claude-user" must never be shadowed by a broader "claude" pattern.
# Vendor taxonomy per each vendor's own crawler documentation. The nginx
# `$machine_agent` map repeats every token in this order
# (tests/unit/api/test_machine_reads_nginx.py), so a vendor added here needs
# its line there too.
AI_AGENTS: tuple[tuple[str, str, str], ...] = (
    # (user-agent substring, assistant, kind)
    ("claude-user", "claude", "user_directed"),
    ("claude-searchbot", "claude", "index"),
    ("claudebot", "claude", "training"),
    ("chatgpt-user", "chatgpt", "user_directed"),
    ("oai-searchbot", "chatgpt", "index"),
    ("gptbot", "chatgpt", "training"),
    ("perplexity-user", "perplexity", "user_directed"),
    ("perplexitybot", "perplexity", "index"),
    ("gemini-deep-research", "gemini", "user_directed"),
    ("gemininotebook", "gemini", "user_directed"),
    ("notebooklm", "gemini", "user_directed"),
    ("google-agent", "gemini", "user_directed"),
    ("googleagent", "gemini", "user_directed"),
    # Builds Vertex AI agents' grounding on the site owner's request. Before
    # the google entries; it contains neither "googlebot" nor "googleother".
    ("google-cloudvertexbot", "gemini", "index"),
    ("mistralai-user", "mistral", "user_directed"),
    ("mistralai-index", "mistral", "index"),
    ("meta-externalfetcher", "meta", "user_directed"),
    ("meta-webindexer", "meta", "index"),
    ("meta-externalagent", "meta", "training"),
    ("duckassistbot", "duckduckgo", "user_directed"),
    ("amzn-user", "amazon", "user_directed"),
    ("amzn-searchbot", "amazon", "index"),
    ("amazonbot", "amazon", "index"),
    ("grok-deepsearch", "grok", "user_directed"),
    ("grokbot", "grok", "user_directed"),
    ("xai-grok", "grok", "user_directed"),
    # xAI's search index. Before the bare "xai" below, which would otherwise
    # record it as a user-directed fetch (a live sample did exactly that).
    ("xai-searchbot", "grok", "index"),
    # The bare tokens the nginx map already serves (`~*grok`, `~*xai`): xAI's
    # fetcher was seen sending plain "Grok" and "xAI-Bot" without the grok
    # substring. Both were prerendered but never counted, because nothing above
    # matched them.
    # Last among the xAI patterns so the specific ones keep winning.
    ("grok", "grok", "user_directed"),
    ("xai", "grok", "user_directed"),
    ("youbot", "you", "index"),
    ("cohere-ai", "cohere", "user_directed"),
    # AI search indexes and training corpora that nginx does not prerender
    # (its `$is_bot` map leaves them on the SPA shell), so most of their reads
    # are nginx's lines. Bytespider is a welcome training crawler since the
    # robots.txt policy opened to every crawler. Keenable documents
    # Keenable-User (a person's agent asked) and Keenable-SearchBot; the bare
    # token also catches the "KeenableBot" UA seen in the request log.
    ("exasearchbot", "exa", "index"),
    ("keenable-user", "keenable", "user_directed"),
    ("keenable", "keenable", "index"),
    ("bytespider", "bytedance", "training"),
    ("ccbot", "commoncrawl", "training"),
    # SEO tools: crawlers that index the web for search-marketing products.
    # HaloBot is Haloscan's.
    ("semrushbot", "semrush", "seo"),
    ("ahrefsbot", "ahrefs", "seo"),
    ("dataforseobot", "dataforseo", "seo"),
    ("mj12bot", "majestic", "seo"),
    ("dotbot", "moz", "seo"),
    ("halobot", "haloscan", "seo"),
    # Classic search crawlers. Worth recording for the same reason the AI ones
    # are: crawl frequency per engine is otherwise only visible by sampling
    # Search Console's URL inspection one URL at a time, which is how the
    # months-long recrawl gap after the June 2026 outage stayed invisible.
    # Sogou by its spider's full token: its mobile browser, which people use,
    # also carries "sogou".
    ("qwantbot", "qwant", "search"),
    ("petalbot", "huawei", "search"),
    ("sogou web spider", "sogou", "search"),
    ("google-inspectiontool", "google", "inspection"),
    ("googleother", "google", "search"),
    ("googlebot", "google", "search"),
    ("bingbot", "bing", "search"),
    ("duckduckbot", "duckduckgo", "search"),
    ("yandexbot", "yandex", "search"),
    ("baiduspider", "baidu", "search"),
    # Last among the Apple patterns: "applebot" is a substring of
    # "applebot-extended", which is a robots.txt token rather than a real UA —
    # but ordering it here keeps the match correct if that ever changes.
    ("applebot", "apple", "search"),
)


def detect_ai_agent(user_agent: str) -> tuple[str, str] | None:
    """Return (assistant, kind) for a known AI or search agent, else None.

    Matching is substring-based on the lowercased UA, first match wins, so
    AI_AGENTS is ordered most-specific first.
    """
    ua = user_agent.lower()
    for pattern, assistant, kind in AI_AGENTS:
        if pattern in ua:
            return assistant, kind
    return None


# Hold strong references to in-flight fire-and-forget tasks.
# asyncio only weak-references tasks, so without this set the GC can collect
# them mid-flight and silently drop analytics events.
_BACKGROUND_TASKS: set[asyncio.Task] = set()

# All platforms from nginx.conf bot detection (27 total)
# Order matters for some patterns - more specific patterns checked first via _detect_whatsapp_or_signal()
PLATFORM_PATTERNS = {
    # Social Media
    "twitter": "twitterbot",
    "facebook": "facebookexternalhit",
    "linkedin": "linkedinbot",
    "pinterest": "pinterestbot",
    "reddit": "redditbot",
    "tumblr": "tumblr",
    "mastodon": "mastodon",
    # Messaging Apps (whatsapp handled specially - see _detect_whatsapp_or_signal)
    "slack": "slackbot",
    "discord": "discordbot",
    "telegram": "telegrambot",
    "viber": "viber",
    "skype": "skypeuripreview",
    "teams": "microsoft teams",
    "snapchat": "snapchat",
    # Search Engines
    "google": "googlebot",
    "bing": "bingbot",
    "yandex": "yandexbot",
    "duckduckgo": "duckduckbot",
    "baidu": "baiduspider",
    "apple": "applebot",
    # Link Preview Services
    "embedly": "embedly",
    "quora": "quora link preview",
    "outbrain": "outbrain",
    "rogerbot": "rogerbot",
    "showyoubot": "showyoubot",
}

# Real WhatsApp User-Agent has version + platform suffix: "WhatsApp/2.23.18.78 i" or "WhatsApp/2.21.22.23 A"
# Signal uses WhatsApp User-Agent to bypass rate limits but sends simpler format: "WhatsApp" or "WhatsApp/2"
# Pattern matches: WhatsApp/X.Y.Z (at least 3-part version) followed by platform indicator (i/A/N/W or more text)
# See: https://github.com/signalapp/Signal-Android/issues/10060
REAL_WHATSAPP_PATTERN = re.compile(r"whatsapp/\d+\.\d+\.\d+", re.IGNORECASE)


def _detect_whatsapp_variant(user_agent: str) -> str | None:
    """Distinguish real WhatsApp from apps spoofing WhatsApp User-Agent.

    Some apps (Signal, others) use 'WhatsApp' User-Agent to bypass rate limits.
    Real WhatsApp includes full version: 'WhatsApp/2.23.18.78 i' (iOS) or 'WhatsApp/2.21.22.23 A' (Android).
    Spoofers send simpler format: 'WhatsApp' or 'WhatsApp/2'.

    Returns:
        'whatsapp' for verified real WhatsApp, 'whatsapp-lite' for simplified/spoofed UA, None if neither.
    """
    ua_lower = user_agent.lower()
    if "whatsapp" not in ua_lower:
        return None

    # Real WhatsApp has 3+ part version (e.g., WhatsApp/2.23.18.78)
    if REAL_WHATSAPP_PATTERN.search(user_agent):
        return "whatsapp"

    # Has "whatsapp" but no full version - could be Signal or other spoofers
    return "whatsapp-lite"


def detect_platform(user_agent: str) -> str:
    """Detect platform from User-Agent string.

    Args:
        user_agent: The User-Agent header value

    Returns:
        Platform name (e.g., 'twitter', 'whatsapp', 'whatsapp-lite') or 'unknown'
    """
    # Special handling for WhatsApp variants (some apps spoof WhatsApp UA)
    whatsapp_variant = _detect_whatsapp_variant(user_agent)
    if whatsapp_variant:
        return whatsapp_variant

    ua_lower = user_agent.lower()
    for platform, pattern in PLATFORM_PATTERNS.items():
        if pattern in ua_lower:
            return platform
    return "unknown"


async def _send_plausible_event(user_agent: str, client_ip: str, name: str, url: str, props: dict) -> None:
    """Internal: Send event to Plausible (called as background task).

    Args:
        user_agent: Original User-Agent header
        client_ip: Client IP for geolocation
        name: Event name
        url: Page URL
        props: Event properties
    """
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            await client.post(
                PLAUSIBLE_ENDPOINT,
                headers={"User-Agent": user_agent, "X-Forwarded-For": client_ip, "Content-Type": "application/json"},
                json={"name": name, "url": url, "domain": DOMAIN, "props": props},
            )
    except Exception as e:
        # warning (not debug) so prod outages of the Plausible pipeline are
        # actually visible — Cloud Run typically suppresses DEBUG, which made
        # full-pipeline failures invisible in incident triage.
        logger.warning("Plausible tracking failed (non-critical): %s", e)


def _handle_task_exception(task: asyncio.Task) -> None:
    """Handle exceptions from fire-and-forget tasks to prevent silent failures."""
    try:
        # This will re-raise any exception that occurred in the task
        task.result()
    except asyncio.CancelledError:
        pass  # Task was cancelled, not an error
    except Exception as e:
        logger.warning(f"Background analytics task failed: {e}")


def track_og_image(
    request: Request,
    page: str,
    spec: str | None = None,
    language: str | None = None,
    library: str | None = None,
    filters: dict[str, str] | None = None,
) -> None:
    """Track og:image request (fire-and-forget).

    Sends event to Plausible in background without blocking response.

    Args:
        request: FastAPI request for headers
        page: Page type ('home', 'plots', 'spec_overview', 'spec_detail')
        spec: Spec ID (optional)
        language: Language slug (optional) — e.g. "python"
        library: Library ID (optional)
        filters: Query params for filtered home page (e.g., {'lib': 'plotly', 'dom': 'statistics'})
    """
    user_agent = request.headers.get("user-agent", "")
    # Who fetched it decides whether this is an event at all. A social or
    # messenger preview means a person shared a link: a product signal that
    # belongs with the human numbers. A search or AI crawler fetching the same
    # image is not a share, and since robots.txt permits /og/ (#10472) those
    # arrive in volume; on the main site they would drown the sharing signal
    # and inflate visitor counts. detect_ai_agent recognises exactly the machine
    # side, and its read is a machine-read line (api/machine_reads.py) instead.
    if detect_ai_agent(user_agent) is not None:
        return
    client_ip = visitor_ip(request)
    platform = detect_platform(user_agent)

    # Build URL based on page type. Spec routes follow /{spec}/{language}/{library}.
    if page == "home":
        url = "https://anyplot.ai/"
    elif page == "plots":
        url = "https://anyplot.ai/plots"
    elif spec is not None and language and library:
        url = f"https://anyplot.ai/{spec}/{language}/{library}"
    elif spec is not None and language:
        url = f"https://anyplot.ai/{spec}/{language}"
    elif spec is not None:
        url = f"https://anyplot.ai/{spec}"
    else:
        # Fallback: missing spec for a spec-based page
        url = "https://anyplot.ai/"

    props: dict[str, str] = {"page": page, "platform": platform}
    if spec:
        props["spec"] = spec
    if language:
        props["language"] = language
    if library:
        props["library"] = library
    if filters:
        # Add each filter as separate prop (e.g., filter_lib, filter_dom)
        # This handles comma-separated values like lib=plotly,matplotlib
        for key, value in filters.items():
            props[f"filter_{key}"] = value

    # Fire-and-forget: create task without awaiting, but add exception handler.
    # Track via _BACKGROUND_TASKS so the GC cannot collect the task before it runs.
    task = asyncio.create_task(_send_plausible_event(user_agent, client_ip, "og_image_view", url, props))
    _BACKGROUND_TASKS.add(task)
    task.add_done_callback(_BACKGROUND_TASKS.discard)
    task.add_done_callback(_handle_task_exception)
