"""SEO endpoints (sitemap, bot-optimized pages)."""

import html
import json
import re
from datetime import datetime
from urllib.parse import quote, urlparse

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse, Response
from sqlalchemy.ext.asyncio import AsyncSession

from api.cache import cache_key, get_cache, get_or_set_cache, set_cache
from api.dependencies import optional_db
from core.config import settings
from core.constants import LANGUAGES_METADATA, LIBRARIES_METADATA
from core.database import ImplRepository, SpecRepository
from core.database.connection import get_db_context
from core.utils import strip_noqa_comments


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
        "  <url><loc>https://anyplot.ai/map</loc></url>",
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


# HTML template for search/social crawlers. Meta tags drive social previews;
# the {body} slot carries what search engines index (headings, code, links,
# JSON-LD) — an empty body reads as a thin page and wastes the crawl.
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
    <link rel="canonical" href="{url}" />{jsonld}
</head>
<body>
{body}
</body>
</html>"""

# Route through API for tracking (was: anyplot.ai/og-image.png)
DEFAULT_HOME_IMAGE = "https://api.anyplot.ai/og/home.png"
DEFAULT_PLOTS_IMAGE = "https://api.anyplot.ai/og/plots.png"
DEFAULT_DESCRIPTION = "library-agnostic, ai-powered plotting."

# Display names derived from the canonical registry — never hand-maintain
# name maps in routers (that is how the 9-library-era drift happened).
_LANGUAGE_NAMES = {lang["id"]: str(lang["name"]) for lang in LANGUAGES_METADATA}
_LIBRARY_NAMES = {lib["id"]: str(lib["name"]) for lib in LIBRARIES_METADATA}

# Site-wide footer nav on every bot page: crawlers that land deep on an impl
# page can reach the hub surfaces without executing the SPA.
_BOT_NAV_HTML = (
    "<nav>"
    '<a href="https://anyplot.ai/">anyplot.ai</a> · '
    '<a href="https://anyplot.ai/plots">plots</a> · '
    '<a href="https://anyplot.ai/specs">specs</a> · '
    '<a href="https://anyplot.ai/libraries">libraries</a> · '
    '<a href="https://anyplot.ai/map">map</a> · '
    '<a href="https://anyplot.ai/palette">palette</a> · '
    '<a href="https://anyplot.ai/mcp">mcp</a> · '
    '<a href="https://anyplot.ai/stats">stats</a> · '
    '<a href="https://anyplot.ai/about">about</a>'
    "</nav>"
)


def _jsonld_script(payload: dict) -> str:
    """Serialize a JSON-LD payload into a <script> element for the template head.

    `</` is emitted as `\\u003c/` so DB-sourced text (titles, descriptions)
    can never close the script element early; the escape is plain JSON and
    parses back to the identical string.
    """
    body = json.dumps(payload, ensure_ascii=False).replace("</", "\\u003c/")
    return f'\n    <script type="application/ld+json">{body}</script>'


def _render_bot_html(
    *, title: str, description: str, image: str, url: str, body: str = "", jsonld: dict | None = None
) -> str:
    """Render a bot-serving page.

    ``title``, ``description``, ``url`` and ``body`` must arrive HTML-escaped
    (same contract the bare template had); ``jsonld`` takes raw values —
    ``json.dumps`` handles its quoting.
    """
    return BOT_HTML_TEMPLATE.format(
        title=title,
        description=description,
        image=image,
        url=url,
        jsonld=_jsonld_script(jsonld) if jsonld else "",
        body=f"{body or f'<h1>{title}</h1><p>{description}</p>'}\n{_BOT_NAV_HTML}",
    )


def _impl_display_names(impl) -> tuple[str, str]:
    """(library display name, language display name) for an impl, falling back to raw ids."""
    language_id = impl.library.language if impl.library else ""
    return _LIBRARY_NAMES.get(impl.library_id, impl.library_id), _LANGUAGE_NAMES.get(language_id, language_id)


def _sorted_impls(spec) -> list:
    """Impls with a loaded library relation, in stable (language, library) order."""
    return sorted((i for i in spec.impls if i.library), key=lambda i: (i.library.language, i.library_id))


def _build_spec_hub_html(spec, image: str) -> str:
    """Full bot page for the cross-language spec hub /{spec_id}.

    Body carries the preview image and one link per implementation page;
    JSON-LD carries BreadcrumbList + ItemList so the hub↔impl structure is
    machine-readable.
    """
    spec_id_esc = html.escape(spec.id)
    title_esc = html.escape(spec.title)
    desc_esc = html.escape(spec.description or DEFAULT_DESCRIPTION)
    image_esc = html.escape(image, quote=True)
    hub_url = f"https://anyplot.ai/{spec.id}"

    impl_links = []
    impl_list_items = []
    for position, impl in enumerate(_sorted_impls(spec), start=1):
        lib_name, lang_name = _impl_display_names(impl)
        impl_url = f"{hub_url}/{impl.library.language}/{impl.library_id}"
        impl_links.append(
            f'<li><a href="{html.escape(impl_url, quote=True)}">'
            f"{title_esc} in {html.escape(lib_name)} ({html.escape(lang_name)})</a></li>"
        )
        impl_list_items.append(
            {"@type": "ListItem", "position": position, "name": f"{spec.title} — {lib_name}", "url": impl_url}
        )

    body = (
        f"<h1>{title_esc}</h1>"
        f"<p>{desc_esc}</p>"
        f'<img src="{image_esc}" alt="{title_esc}" width="1200" height="630" />'
        + (f"<h2>Implementations</h2><ul>{''.join(impl_links)}</ul>" if impl_links else "")
    )
    jsonld = {
        "@context": "https://schema.org",
        "@graph": [
            {
                "@type": "BreadcrumbList",
                "itemListElement": [
                    {"@type": "ListItem", "position": 1, "name": "anyplot.ai", "item": "https://anyplot.ai/"},
                    {"@type": "ListItem", "position": 2, "name": spec.title, "item": hub_url},
                ],
            },
            {"@type": "ItemList", "name": spec.title, "itemListElement": impl_list_items},
        ],
    }
    return _render_bot_html(
        title=f"{title_esc} | anyplot.ai",
        description=desc_esc,
        image=image_esc,
        url=f"https://anyplot.ai/{spec_id_esc}",
        body=body,
        jsonld=jsonld,
    )


def _build_impl_html(spec, impl, code: str | None, image: str) -> str:
    """Full bot page for an implementation detail /{spec_id}/{language}/{library}.

    Body carries the preview image, the implementation source in a <pre>
    block, and hub + sibling links; JSON-LD carries BreadcrumbList +
    SoftwareSourceCode.
    """
    language_id = impl.library.language
    lib_name, lang_name = _impl_display_names(impl)
    title_esc = html.escape(spec.title)
    lib_name_esc = html.escape(lib_name)
    desc_esc = html.escape(spec.description or DEFAULT_DESCRIPTION)
    image_esc = html.escape(image, quote=True)
    hub_url = f"https://anyplot.ai/{spec.id}"
    page_url = f"{hub_url}/{language_id}/{impl.library_id}"

    sibling_links = []
    for sibling in _sorted_impls(spec):
        if sibling.library_id == impl.library_id and sibling.library.language == language_id:
            continue
        sib_lib_name, sib_lang_name = _impl_display_names(sibling)
        sibling_url = f"{hub_url}/{sibling.library.language}/{sibling.library_id}"
        sibling_links.append(
            f'<li><a href="{html.escape(sibling_url, quote=True)}">'
            f"{title_esc} in {html.escape(sib_lib_name)} ({html.escape(sib_lang_name)})</a></li>"
        )

    body = (
        f"<h1>{title_esc} — {lib_name_esc}</h1>"
        f"<p>{desc_esc}</p>"
        f'<img src="{image_esc}" alt="{title_esc} rendered with {lib_name_esc}" width="1200" height="630" />'
        + (
            f"<h2>{html.escape(lang_name)} source ({lib_name_esc})</h2><pre><code>{html.escape(code)}</code></pre>"
            if code
            else ""
        )
        + f'<p>Part of <a href="{html.escape(hub_url, quote=True)}">{title_esc}</a> on anyplot.ai.</p>'
        + (f"<h2>Other implementations</h2><ul>{''.join(sibling_links)}</ul>" if sibling_links else "")
    )
    jsonld = {
        "@context": "https://schema.org",
        "@graph": [
            {
                "@type": "BreadcrumbList",
                "itemListElement": [
                    {"@type": "ListItem", "position": 1, "name": "anyplot.ai", "item": "https://anyplot.ai/"},
                    {"@type": "ListItem", "position": 2, "name": spec.title, "item": hub_url},
                    {"@type": "ListItem", "position": 3, "name": lib_name, "item": page_url},
                ],
            },
            {
                "@type": "SoftwareSourceCode",
                "name": f"{spec.title} — {lib_name}",
                "description": spec.description or DEFAULT_DESCRIPTION,
                "programmingLanguage": lang_name,
                "runtimePlatform": lib_name,
                "codeSampleType": "full solution",
                "url": page_url,
                "image": image,
            },
        ],
    }
    return _render_bot_html(
        title=f"{title_esc} - {lib_name_esc} | anyplot.ai",
        description=desc_esc,
        image=image_esc,
        url=html.escape(page_url, quote=True),
        body=body,
        jsonld=jsonld,
    )


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
        _render_bot_html(title="anyplot.ai", description=DEFAULT_DESCRIPTION, image=image_url, url=page_url)
    )


@router.get("/seo-proxy/plots")
async def seo_plots():
    """Bot-optimized plots page with correct og:tags."""
    return HTMLResponse(
        _render_bot_html(
            title="plots | anyplot.ai",
            description="Browse and filter visualization examples across 15 libraries in Python, R, Julia, and JavaScript: matplotlib, seaborn, plotly, bokeh, altair, plotnine, pygal, lets-plot, ggplot2, Makie.jl, Chart.js, D3.js, ECharts, Highcharts, MUI X Charts.",
            image=DEFAULT_PLOTS_IMAGE,
            url="https://anyplot.ai/plots",
        )
    )


@router.get("/seo-proxy/specs")
async def seo_specs():
    """Bot-optimized specs page with correct og:tags."""
    return HTMLResponse(
        _render_bot_html(
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
        _render_bot_html(
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
        _render_bot_html(
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
        _render_bot_html(
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
        _render_bot_html(
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
        _render_bot_html(
            title="imprint palette | anyplot.ai",
            description="Imprint — a colorblind-safe categorical palette of 8 hues plus 3 semantic anchors (amber, neutral, muted). Tuned for warm-paper rendering, validated against deuteranopia / protanopia / tritanopia. The palette every plot on anyplot.ai uses.",
            image=DEFAULT_HOME_IMAGE,
            url="https://anyplot.ai/palette",
        )
    )


@router.get("/seo-proxy/map")
async def seo_map():
    """Bot-optimized network map page with correct og:tags."""
    return HTMLResponse(
        _render_bot_html(
            title="Network Map | anyplot.ai",
            description=(
                "Interactive network map of plot specifications grouped by visual similarity — "
                "explore relationships across all anyplot.ai chart types."
            ),
            image=DEFAULT_HOME_IMAGE,
            url="https://anyplot.ai/map",
        )
    )


@router.get("/seo-proxy/stats")
async def seo_stats():
    """Bot-optimized stats page with correct og:tags."""
    return HTMLResponse(
        _render_bot_html(
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
            _render_bot_html(
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

    result = _build_spec_hub_html(spec, image)
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
    # Belt-and-braces redirect-target sanitisation:
    #   1. _SPEC_ID_RE.fullmatch() above already constrains spec_id to
    #      lowercase alphanum + hyphens.
    #   2. urllib.parse.quote() percent-encodes anything outside [-A-Za-z0-9],
    #      which is a CodeQL-recognised sanitizer for `py/url-redirection`.
    #   3. urlparse() + scheme/netloc check guarantees the assembled URL is
    #      a same-origin path (no `//evil.com` or `https://evil.com`).
    safe_spec = quote(spec_id, safe="-")
    target = "/seo-proxy/" + safe_spec
    parsed = urlparse(target)
    if parsed.scheme or parsed.netloc or not target.startswith("/seo-proxy/"):
        raise HTTPException(status_code=400, detail="Invalid redirect target")
    return RedirectResponse(url=target, status_code=301)


@router.get("/seo-proxy/{spec_id}/{language}/{library}")
async def seo_spec_implementation(
    spec_id: str, language: str, library: str, db: AsyncSession | None = Depends(optional_db)
):
    """Bot-optimized implementation detail."""
    if db is None:
        return HTMLResponse(
            _render_bot_html(
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

    if impl:
        code_impl = await ImplRepository(db).get_code(spec_id, library, language)
        code = strip_noqa_comments(code_impl.code) if code_impl and code_impl.code else None
        result = _build_impl_html(spec, impl, code, image)
    else:
        # Unknown language/library combination for a real spec: keep serving
        # the minimal meta-only page (bots may hold stale URLs after regens).
        result = _render_bot_html(
            title=f"{html.escape(spec.title)} - {html.escape(library)} | anyplot.ai",
            description=html.escape(spec.description or DEFAULT_DESCRIPTION),
            image=html.escape(image, quote=True),
            url=f"https://anyplot.ai/{html.escape(spec_id)}/{html.escape(language)}/{html.escape(library)}",
        )
    set_cache(key, result)
    return HTMLResponse(result)
