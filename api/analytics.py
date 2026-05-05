"""Server-side Plausible Analytics for og:image tracking.

Tracks og:image requests from social media bots (Twitter, WhatsApp, etc.)
since bots don't execute JavaScript and can't be tracked client-side.

Uses fire-and-forget pattern to avoid delaying responses.
"""

import asyncio
import logging
import re

import httpx
from fastapi import Request


logger = logging.getLogger(__name__)

PLAUSIBLE_ENDPOINT = "https://plausible.io/api/event"
DOMAIN = "anyplot.ai"

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
    client_ip = request.headers.get("x-forwarded-for", request.client.host if request.client else "")
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
