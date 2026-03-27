"""SEO endpoints (sitemap, bot-optimized pages)."""

import html
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse, Response
from sqlalchemy.ext.asyncio import AsyncSession

from api.cache import cache_key, get_cache, get_or_set_cache, set_cache
from api.dependencies import optional_db
from core.config import settings
from core.database import SpecRepository
from core.database.connection import get_db_context


router = APIRouter(tags=["seo"])


def _lastmod(dt: datetime | None) -> str:
    """Format datetime as <lastmod> XML element, or empty string if None."""
    return f"<lastmod>{dt.strftime('%Y-%m-%d')}</lastmod>" if dt else ""


def _build_sitemap_xml(specs: list) -> str:
    """Build sitemap XML string from specs."""
    xml_lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">',
        "  <url><loc>https://pyplots.ai/</loc></url>",
        "  <url><loc>https://pyplots.ai/catalog</loc></url>",
        "  <url><loc>https://pyplots.ai/mcp</loc></url>",
        "  <url><loc>https://pyplots.ai/legal</loc></url>",
    ]

    for spec in specs:
        if spec.impls:
            spec_id = html.escape(spec.id)
            xml_lines.append(f"  <url><loc>https://pyplots.ai/{spec_id}</loc>{_lastmod(spec.updated)}</url>")
            for impl in spec.impls:
                library_id = html.escape(impl.library_id)
                xml_lines.append(
                    f"  <url><loc>https://pyplots.ai/{spec_id}/{library_id}</loc>{_lastmod(impl.updated)}</url>"
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
    <meta property="og:site_name" content="pyplots.ai" />
    <meta name="twitter:card" content="summary_large_image" />
    <meta name="twitter:title" content="{title}" />
    <meta name="twitter:description" content="{description}" />
    <meta name="twitter:image" content="{image}" />
    <link rel="canonical" href="{url}" />
</head>
<body><h1>{title}</h1><p>{description}</p></body>
</html>"""

# Route through API for tracking (was: pyplots.ai/og-image.png)
DEFAULT_HOME_IMAGE = "https://api.pyplots.ai/og/home.png"
DEFAULT_CATALOG_IMAGE = "https://api.pyplots.ai/og/catalog.png"
DEFAULT_DESCRIPTION = "library-agnostic, ai-powered python plotting."


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

    Includes root, catalog page, and all specs with implementations.
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
    page_url = f"https://pyplots.ai/?{query_string}" if query_string else "https://pyplots.ai/"

    return HTMLResponse(
        BOT_HTML_TEMPLATE.format(title="pyplots.ai", description=DEFAULT_DESCRIPTION, image=image_url, url=page_url)
    )


@router.get("/seo-proxy/catalog")
async def seo_catalog():
    """Bot-optimized catalog page with correct og:tags."""
    return HTMLResponse(
        BOT_HTML_TEMPLATE.format(
            title="Catalog | pyplots.ai",
            description="Browse all Python plotting specifications alphabetically. Find matplotlib, seaborn, plotly, bokeh, altair examples.",
            image=DEFAULT_CATALOG_IMAGE,
            url="https://pyplots.ai/catalog",
        )
    )


@router.get("/seo-proxy/legal")
async def seo_legal():
    """Bot-optimized legal page with correct og:tags."""
    return HTMLResponse(
        BOT_HTML_TEMPLATE.format(
            title="Legal | pyplots.ai",
            description="Legal notice, privacy policy, and transparency information for pyplots.ai",
            image=DEFAULT_HOME_IMAGE,
            url="https://pyplots.ai/legal",
        )
    )


@router.get("/seo-proxy/mcp")
async def seo_mcp():
    """Bot-optimized MCP page with correct og:tags."""
    return HTMLResponse(
        BOT_HTML_TEMPLATE.format(
            title="MCP Server | pyplots.ai",
            description="Connect your AI assistant to pyplots via the Model Context Protocol (MCP).",
            image=DEFAULT_HOME_IMAGE,
            url="https://pyplots.ai/mcp",
        )
    )


@router.get("/seo-proxy/{spec_id}")
async def seo_spec_overview(spec_id: str, db: AsyncSession | None = Depends(optional_db)):
    """Bot-optimized spec overview page with collage og:image."""
    if db is None:
        # Fallback when DB unavailable
        return HTMLResponse(
            BOT_HTML_TEMPLATE.format(
                title=f"{html.escape(spec_id)} | pyplots.ai",
                description=DEFAULT_DESCRIPTION,
                image=DEFAULT_HOME_IMAGE,
                url=f"https://pyplots.ai/{html.escape(spec_id)}",
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

    # Use collage og:image if implementations exist, otherwise default
    has_previews = any(i.preview_url for i in spec.impls)
    image = f"https://api.pyplots.ai/og/{spec_id}.png" if has_previews else DEFAULT_HOME_IMAGE

    result = BOT_HTML_TEMPLATE.format(
        title=f"{html.escape(spec.title)} | pyplots.ai",
        description=html.escape(spec.description or DEFAULT_DESCRIPTION),
        image=html.escape(image, quote=True),
        url=f"https://pyplots.ai/{html.escape(spec_id)}",
    )
    set_cache(key, result)
    return HTMLResponse(result)


@router.get("/seo-proxy/{spec_id}/{library}")
async def seo_spec_implementation(spec_id: str, library: str, db: AsyncSession | None = Depends(optional_db)):
    """Bot-optimized spec implementation page with branded og:image."""
    if db is None:
        # Fallback when DB unavailable
        return HTMLResponse(
            BOT_HTML_TEMPLATE.format(
                title=f"{html.escape(spec_id)} - {html.escape(library)} | pyplots.ai",
                description=DEFAULT_DESCRIPTION,
                image=DEFAULT_HOME_IMAGE,
                url=f"https://pyplots.ai/{html.escape(spec_id)}/{html.escape(library)}",
            )
        )

    key = cache_key("seo", spec_id, library)
    cached = get_cache(key)
    if cached:
        return HTMLResponse(cached)

    repo = SpecRepository(db)
    spec = await repo.get_by_id(spec_id)
    if not spec:
        raise HTTPException(status_code=404, detail="Spec not found")

    # Find the implementation for this library
    impl = next((i for i in spec.impls if i.library_id == library), None)
    # Use branded og:image endpoint if implementation has preview
    image = f"https://api.pyplots.ai/og/{spec_id}/{library}.png" if impl and impl.preview_url else DEFAULT_HOME_IMAGE

    result = BOT_HTML_TEMPLATE.format(
        title=f"{html.escape(spec.title)} - {html.escape(library)} | pyplots.ai",
        description=html.escape(spec.description or DEFAULT_DESCRIPTION),
        image=html.escape(image, quote=True),
        url=f"https://pyplots.ai/{html.escape(spec_id)}/{html.escape(library)}",
    )
    set_cache(key, result)
    return HTMLResponse(result)
