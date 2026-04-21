"""SEO endpoints (sitemap, bot-optimized pages)."""

import html
import re
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse, Response
from sqlalchemy.ext.asyncio import AsyncSession

from api.cache import cache_key, get_cache, get_or_set_cache, set_cache
from api.dependencies import optional_db
from core.config import settings
from core.database import SpecRepository
from core.database.connection import get_db_context


router = APIRouter(tags=["seo"])

# Canonical spec-id shape — lowercase alphanumerics with hyphen separators.
# Same pattern enforced in automation/scripts/sync_to_postgres.py. Used here to
# constrain user-controlled path segments before they land in Location headers.
_SPEC_ID_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")


def _lastmod(dt: datetime | None) -> str:
    """Format datetime as <lastmod> XML element, or empty string if None."""
    return f"<lastmod>{dt.strftime('%Y-%m-%d')}</lastmod>" if dt else ""


def _build_sitemap_xml(specs: list) -> str:
    """Build sitemap XML string from specs.

    Emits two URL tiers per spec:
      - /{spec_id}                       Cross-language hub (canonical overview)
      - /{spec_id}/{language}/{library}  Implementation detail

    The /{spec_id}/{language} tier is intentionally omitted: language filtering
    is served as /{spec_id}?language={language} (filtered hub, same canonical),
    so listing it would create duplicate-content entries for Google.
    """
    xml_lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">',
        "  <url><loc>https://anyplot.ai/</loc></url>",
        "  <url><loc>https://anyplot.ai/plots</loc></url>",
        "  <url><loc>https://anyplot.ai/specs</loc></url>",
        "  <url><loc>https://anyplot.ai/libraries</loc></url>",
        "  <url><loc>https://anyplot.ai/palette</loc></url>",
        "  <url><loc>https://anyplot.ai/about</loc></url>",
        "  <url><loc>https://anyplot.ai/mcp</loc></url>",
        "  <url><loc>https://anyplot.ai/legal</loc></url>",
        "  <url><loc>https://anyplot.ai/stats</loc></url>",
    ]

    for spec in specs:
        if not spec.impls:
            continue
        spec_id = html.escape(spec.id)
        xml_lines.append(f"  <url><loc>https://anyplot.ai/{spec_id}</loc>{_lastmod(spec.updated)}</url>")
        for impl in spec.impls:
            if not impl.library:
                continue
            language_esc = html.escape(impl.library.language)
            library_id = html.escape(impl.library_id)
            xml_lines.append(
                f"  <url><loc>https://anyplot.ai/{spec_id}/{language_esc}/{library_id}</loc>"
                f"{_lastmod(impl.updated)}</url>"
            )

    xml_lines.append("</urlset>")
    return "\n".join(xml_lines)


_STATIC_SITEMAP = _build_sitemap_xml([])


async def _refresh_sitemap() -> str:
    """Standalone factory for background sitemap refresh (creates own DB session)."""
    async with get_db_context() as db:
        repo = SpecRepository(db)
        specs = await repo.get_all()
    return _build_sitemap_xml(specs)


# Minimal HTML template for social media bots (meta tags are what matters)
BOT_HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8" />
    <title>{title}</title>
    <meta name="description" content="{description}" />
    <meta property="og:title" content="{title}" />
    <meta property="og:description" content="{description}" />
    <meta property="og:image" content="{image}" />
    <meta property="og:url" content="{url}" />
    <meta property="og:type" content="website" />
    <meta property="og:site_name" content="anyplot.ai" />
    <meta name="twitter:card" content="summary_large_image" />
    <meta name="twitter:title" content="{title}" />
    <meta name="twitter:description" content="{description}" />
    <meta name="twitter:image" content="{image}" />
    <link rel="canonical" href="{url}" />
</head>
<body><h1>{title}</h1><p>{description}</p></body>
</html>"""

# Route through API for tracking (was: anyplot.ai/og-image.png)
DEFAULT_HOME_IMAGE = "https://api.anyplot.ai/og/home.png"
DEFAULT_PLOTS_IMAGE = "https://api.anyplot.ai/og/plots.png"
DEFAULT_DESCRIPTION = "library-agnostic, ai-powered plotting."


@router.get("/robots.txt")
async def get_robots():
    """
    Serve robots.txt for API backend.

    Blocks all crawlers - APIs should not be indexed by search engines.
    Social media bots (WhatsApp, Twitter, etc.) are unaffected.
    """
    return Response(content="User-agent: *\nDisallow: /\n", media_type="text/plain")


@router.get("/sitemap.xml")
async def get_sitemap(db: AsyncSession | None = Depends(optional_db)):
    """
    Generate dynamic XML sitemap for SEO.

    Includes root, plots/specs pages, and all specs with implementations.
    """
    if db is None:
        return Response(content=_STATIC_SITEMAP, media_type="application/xml")

    async def _fetch() -> str:
        repo = SpecRepository(db)
        specs = await repo.get_all()
        return _build_sitemap_xml(specs)

    xml = await get_or_set_cache(
        cache_key("sitemap_xml"), _fetch, refresh_after=settings.cache_refresh_after, refresh_factory=_refresh_sitemap
    )
    return Response(content=xml, media_type="application/xml")


# =============================================================================
# Bot SEO Proxy Endpoints
# These endpoints serve HTML with correct meta tags for social media bots.
# nginx proxies bot requests here based on User-Agent detection.
# =============================================================================


@router.get("/seo-proxy/")
async def seo_home(request: Request):
    """Bot-optimized home page with correct og:tags.

    Passes query params (e.g., ?lib=plotly&dom=statistics) to og:image URL for tracking.
    """
    # Pass filter params to og:image URL for tracking shared filtered URLs
    # Use html.escape to prevent XSS via query params
    query_string = html.escape(str(request.query_params), quote=True) if request.query_params else ""
    image_url = f"{DEFAULT_HOME_IMAGE}?{query_string}" if query_string else DEFAULT_HOME_IMAGE
    page_url = f"https://anyplot.ai/?{query_string}" if query_string else "https://anyplot.ai/"

    return HTMLResponse(
        BOT_HTML_TEMPLATE.format(title="anyplot.ai", description=DEFAULT_DESCRIPTION, image=image_url, url=page_url)
    )


@router.get("/seo-proxy/plots")
async def seo_plots():
    """Bot-optimized plots page with correct og:tags."""
    return HTMLResponse(
        BOT_HTML_TEMPLATE.format(
            title="plots | anyplot.ai",
            description="Browse and filter Python visualization examples across 9 libraries: matplotlib, seaborn, plotly, bokeh, altair, plotnine, pygal, highcharts, lets-plot.",
            image=DEFAULT_PLOTS_IMAGE,
            url="https://anyplot.ai/plots",
        )
    )


@router.get("/seo-proxy/specs")
async def seo_specs():
    """Bot-optimized specs page with correct og:tags."""
    return HTMLResponse(
        BOT_HTML_TEMPLATE.format(
            title="specs | anyplot.ai",
            description="Browse all Python plotting specifications alphabetically.",
            image=DEFAULT_PLOTS_IMAGE,
            url="https://anyplot.ai/specs",
        )
    )


@router.get("/seo-proxy/libraries")
async def seo_libraries():
    """Bot-optimized libraries page with correct og:tags."""
    return HTMLResponse(
        BOT_HTML_TEMPLATE.format(
            title="libraries | anyplot.ai",
            description="All supported plotting libraries across languages.",
            image=DEFAULT_PLOTS_IMAGE,
            url="https://anyplot.ai/libraries",
        )
    )


@router.get("/seo-proxy/legal")
async def seo_legal():
    """Bot-optimized legal page with correct og:tags."""
    return HTMLResponse(
        BOT_HTML_TEMPLATE.format(
            title="Legal | anyplot.ai",
            description="Legal notice, privacy policy, and transparency information for anyplot.ai",
            image=DEFAULT_HOME_IMAGE,
            url="https://anyplot.ai/legal",
        )
    )


@router.get("/seo-proxy/mcp")
async def seo_mcp():
    """Bot-optimized MCP page with correct og:tags."""
    return HTMLResponse(
        BOT_HTML_TEMPLATE.format(
            title="MCP Server | anyplot.ai",
            description="Connect your AI assistant to anyplot via the Model Context Protocol (MCP).",
            image=DEFAULT_HOME_IMAGE,
            url="https://anyplot.ai/mcp",
        )
    )


@router.get("/seo-proxy/about")
async def seo_about():
    """Bot-optimized about page with correct og:tags."""
    return HTMLResponse(
        BOT_HTML_TEMPLATE.format(
            title="About | anyplot.ai",
            description="About anyplot.ai — library-agnostic, AI-powered plotting.",
            image=DEFAULT_HOME_IMAGE,
            url="https://anyplot.ai/about",
        )
    )


@router.get("/seo-proxy/palette")
async def seo_palette():
    """Bot-optimized palette page with correct og:tags."""
    return HTMLResponse(
        BOT_HTML_TEMPLATE.format(
            title="Palette | anyplot.ai",
            description="Color palette reference for anyplot.ai branding.",
            image=DEFAULT_HOME_IMAGE,
            url="https://anyplot.ai/palette",
        )
    )


@router.get("/seo-proxy/stats")
async def seo_stats():
    """Bot-optimized stats page with correct og:tags."""
    return HTMLResponse(
        BOT_HTML_TEMPLATE.format(
            title="Stats | anyplot.ai",
            description="Platform statistics: library scores, coverage, tags, and top implementations.",
            image=DEFAULT_HOME_IMAGE,
            url="https://anyplot.ai/stats",
        )
    )


# =============================================================================
# Spec routes — new structure: /{spec_id}, /{spec_id}/{language}, /{spec_id}/{language}/{library}
# =============================================================================


@router.get("/seo-proxy/{spec_id}")
async def seo_spec_hub(spec_id: str, db: AsyncSession | None = Depends(optional_db)):
    """Bot-optimized cross-language spec hub."""
    if db is None:
        return HTMLResponse(
            BOT_HTML_TEMPLATE.format(
                title=f"{html.escape(spec_id)} | anyplot.ai",
                description=DEFAULT_DESCRIPTION,
                image=DEFAULT_HOME_IMAGE,
                url=f"https://anyplot.ai/{html.escape(spec_id)}",
            )
        )

    key = cache_key("seo", spec_id)
    cached = get_cache(key)
    if cached:
        return HTMLResponse(cached)

    repo = SpecRepository(db)
    spec = await repo.get_by_id(spec_id)
    if not spec:
        raise HTTPException(status_code=404, detail="Spec not found")

    has_previews = any(i.preview_url for i in spec.impls)
    image = f"https://api.anyplot.ai/og/{spec_id}.png" if has_previews else DEFAULT_HOME_IMAGE

    result = BOT_HTML_TEMPLATE.format(
        title=f"{html.escape(spec.title)} | anyplot.ai",
        description=html.escape(spec.description or DEFAULT_DESCRIPTION),
        image=html.escape(image, quote=True),
        url=f"https://anyplot.ai/{html.escape(spec_id)}",
    )
    set_cache(key, result)
    return HTMLResponse(result)


@router.get("/seo-proxy/{spec_id}/{language}")
async def seo_spec_language(spec_id: str, language: str):
    """Permanent redirect: language-overview URLs now live on the hub with ?language=.

    The /{spec_id}/{language} tier was consolidated into /{spec_id} to eliminate
    duplicate content. Bots following this endpoint get a 301 to the hub proxy;
    humans get the SPA redirect configured in app/src/router.tsx. The `language`
    query parameter is dropped because the hub's canonical tag does not include
    it — Google should consolidate the page, not a filtered variant.
    """
    del language  # referenced for route matching only; deliberately not forwarded
    if not _SPEC_ID_RE.fullmatch(spec_id):
        raise HTTPException(status_code=404, detail="Spec not found")
    return RedirectResponse(url=f"/seo-proxy/{spec_id}", status_code=301)


@router.get("/seo-proxy/{spec_id}/{language}/{library}")
async def seo_spec_implementation(
    spec_id: str, language: str, library: str, db: AsyncSession | None = Depends(optional_db)
):
    """Bot-optimized implementation detail."""
    if db is None:
        return HTMLResponse(
            BOT_HTML_TEMPLATE.format(
                title=f"{html.escape(spec_id)} - {html.escape(library)} | anyplot.ai",
                description=DEFAULT_DESCRIPTION,
                image=DEFAULT_HOME_IMAGE,
                url=f"https://anyplot.ai/{html.escape(spec_id)}/{html.escape(language)}/{html.escape(library)}",
            )
        )

    key = cache_key("seo", spec_id, language, library)
    cached = get_cache(key)
    if cached:
        return HTMLResponse(cached)

    repo = SpecRepository(db)
    spec = await repo.get_by_id(spec_id)
    if not spec:
        raise HTTPException(status_code=404, detail="Spec not found")

    impl = next(
        (i for i in spec.impls if i.library_id == library and i.library and i.library.language == language), None
    )
    image = (
        f"https://api.anyplot.ai/og/{spec_id}/{language}/{library}.png"
        if impl and impl.preview_url
        else DEFAULT_HOME_IMAGE
    )

    result = BOT_HTML_TEMPLATE.format(
        title=f"{html.escape(spec.title)} - {html.escape(library)} | anyplot.ai",
        description=html.escape(spec.description or DEFAULT_DESCRIPTION),
        image=html.escape(image, quote=True),
        url=f"https://anyplot.ai/{html.escape(spec_id)}/{html.escape(language)}/{html.escape(library)}",
    )
    set_cache(key, result)
    return HTMLResponse(result)
