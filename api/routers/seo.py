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
from api.routers.stats import _compute_stats, _refresh_stats
from api.schemas import StatsResponse
from core import palette
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


# The date the bot-facing page template last changed materially. `lastmod`
# describes the PAGE, not the row behind it, and those drift apart: on
# 2026-08-18 every implementation page gained the real render, both themes, the
# interactive version and a rewritten meta description, while no `updated`
# column moved. The sitemap consequently told Google nothing had changed, and
# Google — which had last fetched some of these pages three weeks earlier — had
# no reason to come back and see any of it.
#
# Bump this ONLY when the rendered page genuinely changes for every URL. It is
# a claim to search engines that ~3,900 pages changed at once; making it
# casually is how a site teaches Google to stop trusting its lastmod.
TEMPLATE_LAST_CHANGED = datetime(2026, 8, 18)


def _lastmod(dt: datetime | None) -> str:
    """Format the later of the record's own date and the template's, as <lastmod>.

    Always returns an element. A record without its own date still has a page,
    and that page was last modified at least when its template was — emitting
    nothing there was the same lost recrawl signal in a smaller form.
    """
    latest = max(dt, TEMPLATE_LAST_CHANGED) if dt else TEMPLATE_LAST_CHANGED
    return f"<lastmod>{latest.strftime('%Y-%m-%d')}</lastmod>"


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
    <meta name="robots" content="{robots_content}" />
    <meta property="og:title" content="{title}" />
    <meta property="og:description" content="{description}" />
    <meta property="og:image" content="{image}" />
    <meta property="og:image:width" content="1200" />
    <meta property="og:image:height" content="630" />
    <meta property="og:image:alt" content="{title}" />
    <meta property="og:url" content="{og_url}" />
    <meta property="og:type" content="website" />
    <meta property="og:site_name" content="anyplot.ai" />
    <meta property="og:locale" content="en_US" />
    <meta name="twitter:card" content="summary_large_image" />
    <meta name="twitter:site" content="@MarkusNeusinger" />
    <meta name="twitter:creator" content="@MarkusNeusinger" />
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

# Counts and lists for homepage copy, derived from the registry so the text
# can never drift from the actual catalog.
_LIBRARY_COUNT = len(LIBRARIES_METADATA)
_LANGUAGE_LIST = ", ".join(_LANGUAGE_NAMES.values())
_LIBRARY_LIST = ", ".join(_LIBRARY_NAMES.values())

# Homepage copy sized for SERP display: title ~50-60 chars, description
# ~150 chars. The previous 10-char title / 39-char description read as a
# thin page to search engines (audit 2026-07-16).
HOME_TITLE = f"anyplot.ai — AI-generated plot catalog for {_LIBRARY_COUNT} libraries"
HOME_DESCRIPTION = (
    "The open plot catalogue: every chart starts as a library-agnostic spec; "
    f"AI drafts implementations across {_LIBRARY_COUNT} libraries in {_LANGUAGE_LIST}."
)

# Site-level structured data served to crawlers on the homepage. Mirrors the
# three JSON-LD blocks in app/index.html (WebApplication, WebSite +
# SearchAction, Organization) — bots routed to /seo-proxy/ never execute the
# SPA, so schemas living only in index.html are invisible to Googlebot.
# SearchAction: /plots?spec= is the only term-carrying catalog param the SPA
# supports (exact-match spec filter, see parseUrlFilters in
# app/src/hooks/useUrlSync.ts); there is no free-text search URL, so the
# template mirrors index.html and inherits its exact-match limitation.
_HOME_JSONLD = {
    "@context": "https://schema.org",
    "@graph": [
        {
            "@type": "WebApplication",
            "name": "anyplot.ai",
            "url": "https://anyplot.ai",
            "description": HOME_DESCRIPTION,
            "applicationCategory": "DeveloperApplication",
            "operatingSystem": "Any",
            "offers": {"@type": "Offer", "price": "0", "priceCurrency": "USD"},
            "author": {
                "@type": "Person",
                "name": "Markus Neusinger",
                "url": "https://www.linkedin.com/in/markus-neusinger/",
            },
            "keywords": [name.lower() for name in _LANGUAGE_NAMES.values()]
            + [name.lower() for name in _LIBRARY_NAMES.values()]
            + ["plotting", "data visualization", "charts", "code examples", "colorblind-safe", "imprint palette"],
            "isAccessibleForFree": True,
        },
        {
            "@type": "WebSite",
            "name": "anyplot.ai",
            "url": "https://anyplot.ai",
            "potentialAction": {
                "@type": "SearchAction",
                "target": {"@type": "EntryPoint", "urlTemplate": "https://anyplot.ai/plots?spec={search_term_string}"},
                "query-input": "required name=search_term_string",
            },
        },
        {
            "@type": "Organization",
            "name": "anyplot",
            "url": "https://anyplot.ai",
            "logo": "https://anyplot.ai/og-image.png",
            "description": (
                f"Open plot catalogue with AI-generated implementations across {_LIBRARY_COUNT} "
                f"libraries in {_LANGUAGE_LIST}."
            ),
            "sameAs": ["https://github.com/MarkusNeusinger/anyplot", "https://www.linkedin.com/in/markus-neusinger/"],
        },
    ],
}

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


# Google truncates the SERP snippet around 155 characters and rewrites what it
# cannot use. Spec descriptions in this catalogue run to a median of 395 (max
# 801), so the sentence that decides the click was never the one being written.
_META_DESCRIPTION_LIMIT = 155


def _meta_description(text: str | None) -> str:
    """Trim a description to what a search result will actually display.

    Only the meta/OG tag is trimmed; the visible body copy and the JSON-LD keep
    the full text, because those are content rather than snippet.

    Ends on the last full sentence that fits — but only where that lands past
    the halfway mark. A description opening with a short sentence ("A Smith
    chart.") would otherwise yield a snippet of a dozen characters, wasting the
    slot that decides the click; below that threshold a word-boundary trim of
    the full text carries more information. The word-boundary fallback also
    keeps the trim off mid-word, and running on raw text rather than an escaped
    string means it can never cut through an HTML entity.
    """
    text = " ".join((text or "").split())
    if len(text) <= _META_DESCRIPTION_LIMIT:
        return text

    window = text[: _META_DESCRIPTION_LIMIT + 1]
    for stop in (". ", "! ", "? "):
        end = window.rfind(stop)
        if end >= _META_DESCRIPTION_LIMIT // 2:
            return text[: end + 1]

    cut = window.rfind(" ")
    if cut <= 0:
        return text[:_META_DESCRIPTION_LIMIT].rstrip() + "\u2026"
    return text[:cut].rstrip(" ,;:\u2014-") + "\u2026"


def _jsonld_script(payload: dict) -> str:
    """Serialize a JSON-LD payload into a <script> element for the template head.

    `</` is emitted as `\\u003c/` so DB-sourced text (titles, descriptions)
    can never close the script element early; the escape is plain JSON and
    parses back to the identical string.
    """
    body = json.dumps(payload, ensure_ascii=False).replace("</", "\\u003c/")
    return f'\n    <script type="application/ld+json">{body}</script>'


def _render_bot_html(
    *,
    title: str,
    description: str,
    image: str,
    url: str,
    og_url: str | None = None,
    body: str = "",
    jsonld: dict | None = None,
    noindex: bool = False,
) -> str:
    """Render a bot-serving page.

    Contract per argument:
    - ``title``, ``description``, ``image``, ``url``: text/URL values that
      must arrive HTML-escaped (same contract the bare template had). ``url``
      is the canonical.
    - ``og_url``: the Open Graph URL, defaulting to ``url``. They are separate
      because they answer different questions: the canonical is what Google
      should consolidate on, while og:url is where a shared card sends its
      reader — so a filtered view canonicalises to the bare page but still
      shares as itself. Google ignores og:url for canonicalisation.
    - ``body``: a trusted, fully-built HTML fragment inserted verbatim (plus
      the site nav). Callers must escape any DB-sourced text BEFORE
      interpolating it into the fragment.
    - ``jsonld``: raw (unescaped) values; ``json.dumps`` handles quoting and
      ``_jsonld_script`` neutralizes ``</``.
    """
    # max-image-preview:large — without it Google Images/Discover cap the
    # preview at thumbnail size, which for an image catalogue is on-mission
    # traffic left on the table. Irrelevant on noindex pages.
    return BOT_HTML_TEMPLATE.format(
        title=title,
        description=description,
        image=image,
        url=url,
        og_url=og_url if og_url is not None else url,
        robots_content="noindex" if noindex else "max-image-preview:large",
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


def _spec_index_entries(specs: list) -> list[tuple[str, str]]:
    """(spec_id, title) for every spec with at least one implementation, title-sorted.

    Same inclusion rule as the sitemap: specs without implementations have
    nothing to show and are left out.
    """
    return sorted(((s.id, s.title or s.id) for s in specs if s.impls), key=lambda e: (e[1].lower(), e[0]))


async def _refresh_spec_index() -> list[tuple[str, str]]:
    """Standalone factory for background spec-index refresh (creates own DB session)."""
    async with get_db_context() as db:
        repo = SpecRepository(db)
        specs = await repo.get_all()
    return _spec_index_entries(specs)


async def _get_spec_index(db: AsyncSession) -> list[tuple[str, str]]:
    """Cached (spec_id, title) index backing crawlable link lists and the homepage spec count."""

    async def _fetch() -> list[tuple[str, str]]:
        repo = SpecRepository(db)
        return _spec_index_entries(await repo.get_all())

    return await get_or_set_cache(
        cache_key("seo_spec_index"),
        _fetch,
        refresh_after=settings.cache_refresh_after,
        refresh_factory=_refresh_spec_index,
    )


def _spec_links_html(spec_index: list[tuple[str, str]]) -> str:
    """Crawlable link list to every spec hub.

    /plots and /specs are the catalog surfaces crawlers reach from the site
    nav; without server-rendered links every hub page is an orphan in the
    internal link graph (reachable only via sitemap.xml), which hurts
    discovery and PageRank flow (audit 2026-07-16).
    """
    if not spec_index:
        return ""
    items = "".join(
        f'<li><a href="https://anyplot.ai/{html.escape(spec_id, quote=True)}">{html.escape(title)}</a></li>'
        for spec_id, title in spec_index
    )
    return f"<h2>All plot specifications</h2><ul>{items}</ul>"


def _build_home_body(spec_count: int | None) -> str:
    """Real body copy for the bot homepage (was a one-line default body).

    All claims derive from the canonical registry (core/constants.py) or the
    live spec index — nothing hand-maintained that could drift.
    """
    count_phrase = f"{spec_count} plot specifications" if spec_count else "hundreds of plot specifications"
    return (
        "<h1>anyplot.ai — the open plot catalogue</h1>"
        f"<p>anyplot.ai is an open catalog of {count_phrase}. Every plot begins as a "
        "library-agnostic specification; AI drafts an implementation for each supported "
        "library, reviews it, and publishes the result with full source code.</p>"
        f"<p>The catalog covers {_LIBRARY_COUNT} libraries across {_LANGUAGE_LIST}: "
        f"{_LIBRARY_LIST}. Every implementation ships with light and dark theme previews, "
        "uses the colorblind-safe Imprint palette, and can be browsed, copied, and adapted freely.</p>"
        '<p>Browse the catalog on the <a href="https://anyplot.ai/plots">plots</a> page, jump to any '
        'chart type via the <a href="https://anyplot.ai/specs">spec index</a>, or connect an AI '
        'assistant through the <a href="https://anyplot.ai/mcp">Model Context Protocol (MCP) server</a>.</p>'
    )


def _build_spec_hub_html(spec, image: str) -> str:
    """Full bot page for the cross-language spec hub /{spec_id}.

    Body carries the preview image and one link per implementation page;
    JSON-LD carries BreadcrumbList + ItemList so the hub↔impl structure is
    machine-readable.
    """
    spec_id_esc = html.escape(spec.id)
    title_esc = html.escape(spec.title)
    desc_esc = html.escape(spec.description or DEFAULT_DESCRIPTION)
    meta_desc_esc = html.escape(_meta_description(spec.description or DEFAULT_DESCRIPTION))
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
        item = {"@type": "ListItem", "position": position, "name": f"{spec.title} — {lib_name}", "url": impl_url}
        # Per-item render URL: one hub fetch enumerates every plot image
        # instead of costing a follow-up request per implementation.
        if impl.preview_url_light:
            item["image"] = impl.preview_url_light
        impl_list_items.append(item)

    # The body shows the best actual render, not the 1200x630 og collage card:
    # the hub is the sitemap'd, most-shared URL, and until now it was the one
    # page type where a machine could enumerate 15 implementation links yet
    # not reach a single plot image (AI-access audit 2026-08-19). The collage
    # card stays the og:image — link previews are what it was made for.
    best_impl = max(
        (i for i in spec.impls if i.preview_url_light), key=lambda i: (i.quality_score or 0, i.library_id), default=None
    )
    if best_impl:
        best_lib_name, _ = _impl_display_names(best_impl)
        plot_img = (
            _render_picture(best_impl, title_esc)
            + f"<p>Preview render from the {html.escape(best_lib_name)} implementation.</p>"
        )
    else:
        plot_img = f'<img src="{image_esc}" alt="{title_esc}" width="1200" height="630" />'

    body = f"<h1>{title_esc}</h1><p>{desc_esc}</p>{plot_img}" + (
        f"<h2>Implementations</h2><ul>{''.join(impl_links)}</ul>" if impl_links else ""
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
        description=meta_desc_esc,
        image=image_esc,
        url=f"https://anyplot.ai/{spec_id_esc}",
        body=body,
        jsonld=jsonld,
    )


def _sized_srcset(full_url: str) -> str:
    """Offer the pipeline's width derivatives for a full-size render URL.

    `plot-light.png` is written alongside `plot-light_400.png`, `_800` and
    `_1200`, and the suffix is the actual pixel width. The original is left out:
    its width differs per plot, so it has no honest `w` descriptor.
    """
    stem = full_url[:-4] if full_url.endswith(".png") else full_url
    return ", ".join(f"{stem}_{w}.png {w}w" for w in (400, 800, 1200))


def _thumb_1200(full_url: str) -> str:
    """The 1200px derivative for a full-size render URL (the original's width
    varies per plot, so 1200 is the largest honest fixed size)."""
    return full_url[:-4] + "_1200.png" if full_url.endswith(".png") else full_url


def _render_picture(impl, alt: str) -> str:
    """The actual plot render, both themes, at a size a consumer can choose.

    ``alt`` must arrive HTML-escaped — the same contract ``_render_bot_html``
    carries, and for the same reason: escaping here instead would double-escape
    the callers that already do it, turning a quoted spec title into a visible
    ``&amp;quot;``. ``html.escape`` defaults to ``quote=True``, so a caller that
    follows the contract is attribute-safe.
    """
    light_default = html.escape(_thumb_1200(impl.preview_url_light), quote=True)
    source = ""
    if impl.preview_url_dark:
        dark_set = html.escape(_sized_srcset(impl.preview_url_dark), quote=True)
        source = f'<source srcset="{dark_set}" media="(prefers-color-scheme: dark)" />'
    # src is the 1200px variant so a naive consumer does not pull a 4766px file;
    # the full original is reachable through the link the body adds beside this.
    return (
        f"<picture>{source}"
        f'<img src="{light_default}" srcset="{html.escape(_sized_srcset(impl.preview_url_light), quote=True)}"'
        f' alt="{alt}" />'
        f"</picture>"
        f"{_render_asset_list(impl)}"
    )


def _render_asset_list(impl) -> str:
    """Name every asset this implementation has, and say which is which.

    The <picture> above already offers both themes, but only through a media
    query — an agent parsing the page cannot tell from that which file is the
    dark one, or that an interactive version exists at all. Two thirds of the
    catalogue has one (plotly, altair, bokeh, pygal, lets-plot and every
    JavaScript library), it is publicly fetchable, and until now nothing in the
    machine-facing page mentioned it.
    """
    items = []
    for url, label in (
        (impl.preview_url_light, "Full-resolution render, light theme"),
        (impl.preview_url_dark, "Full-resolution render, dark theme"),
        (impl.preview_html_light, "Interactive version, light theme"),
        (impl.preview_html_dark, "Interactive version, dark theme"),
    ):
        if url:
            items.append(f'<li><a href="{html.escape(url, quote=True)}">{label}</a></li>')
    return f"<h2>Renders</h2><ul>{''.join(items)}</ul>" if items else ""


def _build_source_code_node(spec, impl, lib_name: str, lang_name: str, page_url: str, hub_url: str, image: str) -> dict:
    """SoftwareSourceCode JSON-LD for an implementation page.

    Mirrors the SPA's node in app/src/pages/SpecPage.tsx (license, author,
    codeRepository, isBasedOn) — crawlers never execute the SPA, so a field
    living only there is invisible to every bot. `license` in particular is
    the one field an assistant checks before copying the code.

    `image` is the actual render as an ImageObject, not the 1200x630 og card
    the meta tags carry: in that card the plot is a thumbnail inside branding
    chrome, and structured-data consumers were being handed the chrome while
    the body served the real plot (AI-access audit 2026-08-19). The card
    remains the og:image — link previews are the surface it was made for.
    """
    node = {
        "@type": "SoftwareSourceCode",
        "name": f"{spec.title} — {lib_name}",
        "description": spec.description or DEFAULT_DESCRIPTION,
        "programmingLanguage": lang_name,
        "runtimePlatform": lib_name,
        "codeSampleType": "full solution",
        "codeRepository": "https://github.com/MarkusNeusinger/anyplot",
        "license": "https://opensource.org/licenses/MIT",
        "author": {"@type": "Organization", "name": "anyplot", "url": "https://anyplot.ai"},
        "isBasedOn": hub_url,
        "url": page_url,
        "image": image,
    }
    if impl.preview_url_light:
        node["image"] = {
            "@type": "ImageObject",
            "contentUrl": impl.preview_url_light,
            "thumbnailUrl": _thumb_1200(impl.preview_url_light),
            "encodingFormat": "image/png",
            "caption": f"{spec.title} rendered with {lib_name}",
            "license": "https://opensource.org/licenses/MIT",
        }
    if impl.updated:
        node["dateModified"] = impl.updated.date().isoformat()
    keywords = _spec_keywords(spec)
    if keywords:
        node["keywords"] = keywords
    return node


# Canonical walk order for the tag bag — dict insertion order varies by
# source/roundtrip, and keywords built from it would make the JSON-LD
# non-deterministic across renders (noisy for caches and diff-consumers).
_TAG_CATEGORY_ORDER = ("plot_type", "data_type", "domain", "features")


def _spec_keywords(spec) -> list[str]:
    """Flatten the spec's tag bag into a deduplicated, deterministically ordered keyword list."""
    tags = spec.tags or {}
    ordered_keys = [k for k in _TAG_CATEGORY_ORDER if k in tags]
    ordered_keys += sorted(k for k in tags if k not in _TAG_CATEGORY_ORDER)
    keywords: list[str] = []
    seen: set[str] = set()
    for key in ordered_keys:
        values = tags[key]
        for value in [values] if isinstance(values, str) else values if isinstance(values, list) else []:
            keyword = str(value)
            if keyword not in seen:
                seen.add(keyword)
                keywords.append(keyword)
    return keywords


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
    meta_desc_esc = html.escape(_meta_description(spec.description or DEFAULT_DESCRIPTION))
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

    # og:image stays the 1200x630 social card — it is what a shared link needs.
    # The body carries the actual render, because in that card the plot is a
    # small thumbnail inside branding chrome: fine for a link preview, useless
    # to an assistant asked to show the plot. Attribution is not lost, the plot
    # title itself reads "{spec} · {language} · {library} · anyplot.ai".
    #
    # The pipeline already writes _400/_800/_1200 derivatives beside every
    # render, and their suffix is the true pixel width (verified across square
    # and wide plots in four languages). The full-size original is NOT in the
    # srcset: its width varies per plot — 2400, 3200, 4766 — so no honest `w`
    # descriptor exists for it. It is linked separately instead.
    if impl.preview_url_light:
        plot_img = _render_picture(impl, f"{title_esc} rendered with {lib_name_esc}")
    else:
        plot_img = f'<img src="{image_esc}" alt="{title_esc} rendered with {lib_name_esc}" width="1200" height="630" />'

    body = (
        f"<h1>{title_esc} — {lib_name_esc}</h1>"
        f"<p>{desc_esc}</p>"
        f"{plot_img}"
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
            _build_source_code_node(spec, impl, lib_name, lang_name, page_url, hub_url, image),
        ],
    }
    return _render_bot_html(
        title=f"{title_esc} - {lib_name_esc} | anyplot.ai",
        description=meta_desc_esc,
        image=image_esc,
        url=html.escape(page_url, quote=True),
        body=body,
        jsonld=jsonld,
    )


@router.get("/robots.txt")
async def get_robots():
    """Serve robots.txt for the API backend.

    The read API is deliberately open. The previous blanket `Disallow: /`
    (with only `/og/` excepted) told every robots-compliant agent that the
    REST endpoints, `/openapi.json` and the MCP transport were off-limits —
    on the very host `app/public/robots.txt` and llms.txt advertise as the
    machine interface to the catalogue (AI-access audit 2026-08-19). The API
    is public, read-only and cached; there is nothing to protect by
    forbidding it, and compliant AI assistants were the only clients the
    Disallow actually stopped.

    Only surfaces that are useless or hazardous to crawl stay disallowed:
    `/debug` (internal diagnostics) and `/proxy` (a parameterised fetch
    proxy — crawling it just re-downloads GCS objects through the API).

    `Disallow` lines are placed before the `Allow: /` catch-all: first-match
    parsers stop at the first matching rule, so the specific exclusions must
    precede the blanket allow — the same ordering rule `app/public/robots.txt`
    documents. Specificity-compliant crawlers reach the same answer either way.
    """
    return Response(content="User-agent: *\nDisallow: /debug\nDisallow: /proxy\nAllow: /\n", media_type="text/plain")


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


def _build_llms_full(specs: list) -> str:
    """Whole-catalogue index for AI agents: one line per spec, one fetch.

    llms.txt names the surfaces; this is the llmstxt.org companion file that
    makes the catalogue enumerable without walking the 400 KB sitemap or
    fetching every hub page. The header documents the retrieval recipes that
    work for EVERY client — the prerendered pages are user-agent-gated, these
    URLs are not (AI-access audit 2026-08-19).
    """
    lines = [
        "# anyplot — full catalogue index",
        "#",
        "# One line per plot specification:",
        "# spec_id | title | hub page | implementations as {language}/{library}",
        "# (plug an implementation's {language}/{library} straight into the render URL below)",
        "#",
        "# Retrieval recipes (any HTTP client, no crawler user agent needed):",
        "#   source code:  https://api.anyplot.ai/specs/{spec_id}/{library}/code",
        "#   spec detail:  https://api.anyplot.ai/specs/{spec_id}",
        "#   render (PNG): https://storage.googleapis.com/anyplot-images/plots/{spec_id}/{language}/{library}/plot-light.png",
        "#                 dark theme: plot-dark.png; responsive widths: plot-light_400.png / _800 / _1200; WebP: plot-light.webp",
        "#   OpenAPI: https://api.anyplot.ai/openapi.json - MCP endpoint: https://api.anyplot.ai/mcp/",
        "",
    ]
    # {language}/{library} rather than the bare library id: the render URL
    # template needs both segments, and without the language every consumer
    # had to make a second /specs/{id} call just to build an image URL
    # (live verification 2026-08-19).
    for spec in sorted((s for s in specs if s.impls), key=lambda s: s.id):
        libraries = ",".join(sorted(f"{i.language_id}/{i.library_id}" for i in spec.impls))
        title = " ".join((spec.title or spec.id).split())
        lines.append(f"{spec.id} | {title} | https://anyplot.ai/{spec.id} | {libraries}")
    return "\n".join(lines) + "\n"


async def _refresh_llms_full() -> str:
    """Standalone factory for background llms-full refresh (creates own DB session)."""
    async with get_db_context() as db:
        repo = SpecRepository(db)
        specs = await repo.get_all()
    return _build_llms_full(specs)


@router.get("/llms-full.txt")
async def get_llms_full(db: AsyncSession | None = Depends(optional_db)):
    """Serve the full catalogue index (llmstxt.org llms-full.txt convention).

    nginx serves anyplot.ai/llms-full.txt from this endpoint the same way it
    proxies the prerendered pages, so the file is reachable on the site's own
    origin for every client.
    """
    if db is None:
        return Response(content=_build_llms_full([]), media_type="text/plain; charset=utf-8")

    async def _fetch() -> str:
        repo = SpecRepository(db)
        specs = await repo.get_all()
        return _build_llms_full(specs)

    text = await get_or_set_cache(
        cache_key("llms_full_txt"),
        _fetch,
        refresh_after=settings.cache_refresh_after,
        refresh_factory=_refresh_llms_full,
    )
    return Response(content=text, media_type="text/plain; charset=utf-8")


# =============================================================================
# Bot SEO Proxy Endpoints
# These endpoints serve HTML with correct meta tags for social media bots.
# nginx proxies bot requests here based on User-Agent detection.
# =============================================================================


@router.get("/seo-proxy/")
async def seo_home(request: Request, db: AsyncSession | None = Depends(optional_db)):
    """Bot-optimized home page: og:tags, site-level JSON-LD, and real body copy.

    Passes query params (e.g., ?lib=plotly&dom=statistics) to og:image URL for tracking.
    """
    # Pass filter params to og:image URL for tracking shared filtered URLs
    # Use html.escape to prevent XSS via query params
    query_string = html.escape(str(request.query_params), quote=True) if request.query_params else ""
    image_url = f"{DEFAULT_HOME_IMAGE}?{query_string}" if query_string else DEFAULT_HOME_IMAGE
    # The canonical never carries the filter params. It used to, which made every
    # filter combination self-canonicalising: /?spec=point-basic was indexed as a
    # page in its own right, competing with the home page it is a view of.
    #
    # og:url is a different question and keeps them. Facebook and LinkedIn use it
    # as the destination of a shared card, so dropping the params there would
    # land every shared filter link on the bare home page — defeating the same
    # "tracking shared filtered URLs" this handler parameterises og:image for.
    # Google does not use og:url for canonicalisation, so the two can differ.
    page_url = "https://anyplot.ai/"
    og_page_url = f"https://anyplot.ai/?{query_string}" if query_string else page_url

    spec_count = len(await _get_spec_index(db)) if db is not None else None
    return HTMLResponse(
        _render_bot_html(
            title=html.escape(HOME_TITLE),
            description=html.escape(HOME_DESCRIPTION),
            image=image_url,
            url=page_url,
            og_url=og_page_url,
            body=_build_home_body(spec_count),
            jsonld=_HOME_JSONLD,
        )
    )


@router.get("/seo-proxy/plots")
async def seo_plots(db: AsyncSession | None = Depends(optional_db)):
    """Bot-optimized plots page: og:tags plus a crawlable link to every spec hub."""
    description = (
        f"Browse and filter visualization examples across {_LIBRARY_COUNT} libraries "
        f"in {_LANGUAGE_LIST}: {_LIBRARY_LIST}."
    )
    body = ""
    if db is not None:
        body = f"<h1>plots</h1><p>{description}</p>{_spec_links_html(await _get_spec_index(db))}"
    return HTMLResponse(
        _render_bot_html(
            title="plots | anyplot.ai",
            description=description,
            image=DEFAULT_PLOTS_IMAGE,
            url="https://anyplot.ai/plots",
            body=body,
        )
    )


@router.get("/seo-proxy/specs")
async def seo_specs(db: AsyncSession | None = Depends(optional_db)):
    """Bot-optimized specs page: og:tags plus a crawlable link to every spec hub."""
    description = (
        "Browse all plot specifications alphabetically — every chart type in the anyplot.ai "
        f"catalog, implemented across {_LIBRARY_COUNT} libraries in {_LANGUAGE_LIST}."
    )
    body = ""
    if db is not None:
        body = f"<h1>specs</h1><p>{description}</p>{_spec_links_html(await _get_spec_index(db))}"
    return HTMLResponse(
        _render_bot_html(
            title="specs | anyplot.ai",
            description=description,
            image=DEFAULT_PLOTS_IMAGE,
            url="https://anyplot.ai/specs",
            body=body,
        )
    )


def _build_libraries_body() -> str:
    """Real bot body for /libraries, derived from the canonical registry.

    The page was a 29-word stub even though its entire content already sits in
    core/constants.py (AI-access audit 2026-08-19) — a crawler following
    llms.txt's "the fifteen supported plotting libraries" link found no such
    list. Registry-derived, so it can never drift from the actual catalog.
    """
    sections = [
        f"<h1>{_LIBRARY_COUNT} plotting libraries across {len(LANGUAGES_METADATA)} languages</h1>",
        "<p>Every plot specification on anyplot.ai is implemented once per library below. "
        'Browse renders per library in the <a href="https://anyplot.ai/plots">gallery</a>.</p>',
    ]
    for lang in LANGUAGES_METADATA:
        libs = [lib for lib in LIBRARIES_METADATA if lib["language_id"] == lang["id"]]
        if not libs:
            continue
        items = "".join(
            f'<li><a href="{html.escape(str(lib["documentation_url"]), quote=True)}">'
            f"{html.escape(str(lib['name']))}</a> {html.escape(str(lib['version']))} — "
            f"{html.escape(str(lib['description']))}</li>"
            for lib in libs
        )
        sections.append(f"<h2>{html.escape(str(lang['name']))}</h2><ul>{items}</ul>")
    return "".join(sections)


_LIBRARIES_BOT_BODY = _build_libraries_body()


@router.get("/seo-proxy/libraries")
async def seo_libraries():
    """Bot-optimized libraries page: the full registry, not just og:tags."""
    return HTMLResponse(
        _render_bot_html(
            title="libraries | anyplot.ai",
            description="All supported plotting libraries across languages.",
            image=DEFAULT_PLOTS_IMAGE,
            url="https://anyplot.ai/libraries",
            body=_LIBRARIES_BOT_BODY,
        )
    )


# Mirrors the load-bearing facts of app/src/pages/LegalPage.tsx — keep the two
# in sync when operator, analytics, or hosting details change.
_LEGAL_BOT_BODY = (
    "<h1>Legal notice</h1>"
    "<p>Operator: Markus Neusinger "
    '(<a href="https://github.com/MarkusNeusinger">GitHub</a>, '
    '<a href="https://x.com/MarkusNeusinger">X</a>). Full legal notice with '
    'contact details on the <a href="https://anyplot.ai/legal">interactive page</a>.</p>'
    "<h2>Privacy</h2>"
    "<p>Analytics: Plausible Analytics (EU, proxied) — no cookies, no personal data collected. "
    "Hosting: Google Cloud Run (Netherlands).</p>"
    "<h2>Transparency</h2>"
    "<p>The whole stack — specs, pipeline, API and frontend — is open source at "
    '<a href="https://github.com/MarkusNeusinger/anyplot">github.com/MarkusNeusinger/anyplot</a>; '
    "the catalogue content is MIT-licensed.</p>"
)


@router.get("/seo-proxy/legal")
async def seo_legal():
    """Bot-optimized legal page: operator, privacy and transparency facts."""
    return HTMLResponse(
        _render_bot_html(
            title="Legal | anyplot.ai",
            description="Legal notice, privacy policy, and transparency information for anyplot.ai",
            image=DEFAULT_HOME_IMAGE,
            url="https://anyplot.ai/legal",
            body=_LEGAL_BOT_BODY,
        )
    )


# The /mcp page's entire audience is AI agents, yet its bot rendering carried
# only a title and one-line description — no endpoint URL, no tool list, no
# setup snippet; everything useful sat behind JS in app/src/pages/McpPage.tsx
# (AI-access audit 2026-08-19). Keep this body in sync with the MCP tools in
# api/mcp/server.py and the human page in McpPage.tsx.
_MCP_BOT_BODY = (
    "<h1>anyplot MCP server</h1>"
    "<p>Query the plot catalogue from an AI assistant via the Model Context "
    "Protocol. Transport: Streamable HTTP at "
    '<a href="https://api.anyplot.ai/mcp/">https://api.anyplot.ai/mcp/</a> '
    "(POST JSON-RPC; the endpoint requires an MCP client and answers plain GET "
    "with an error by design). No authentication, read-only.</p>"
    "<h2>Setup</h2>"
    "<pre><code>claude mcp add --transport http anyplot https://api.anyplot.ai/mcp/</code></pre>"
    "<h2>Tools</h2>"
    "<ul>"
    "<li><code>list_specs(limit, offset)</code> — all plot specifications with tags and library counts</li>"
    "<li><code>search_specs_by_tags(plot_type, data_type, domain, features, library, ...)</code>"
    " — filter the catalogue by spec- and implementation-level tags</li>"
    "<li><code>get_spec_detail(spec_id, libraries?)</code> — one spec with its implementations"
    " (full source code; filter by library ids to keep the payload small)</li>"
    "<li><code>get_implementation(spec_id, library)</code> — one implementation: runnable code,"
    " light/dark render URLs, quality score, review data</li>"
    "<li><code>list_libraries()</code> — the supported plotting libraries</li>"
    "<li><code>get_tag_values(category)</code> — the vocabulary of any tag category</li>"
    "</ul>"
    "<p>Prefer plain HTTP? The same catalogue is served by the "
    '<a href="https://api.anyplot.ai/openapi.json">JSON API</a> and indexed in '
    '<a href="https://anyplot.ai/llms-full.txt">llms-full.txt</a>; retrieval '
    'recipes live in <a href="https://anyplot.ai/llms.txt">llms.txt</a>.</p>'
)


@router.get("/seo-proxy/mcp")
async def seo_mcp():
    """Bot-optimized MCP page: endpoint, setup snippet and tool list, not just og:tags."""
    return HTMLResponse(
        _render_bot_html(
            title="MCP Server | anyplot.ai",
            description="Connect your AI assistant to anyplot via the Model Context Protocol (MCP).",
            image=DEFAULT_HOME_IMAGE,
            url="https://anyplot.ai/mcp",
            body=_MCP_BOT_BODY,
        )
    )


# Mirrors app/src/pages/AboutPage.tsx — the pipeline story is the page's
# content; counts derive from the registry so they cannot drift.
_ABOUT_BOT_BODY = (
    "<h1>About anyplot</h1>"
    f"<p>anyplot.ai is a catalogue of plotting examples across {_LIBRARY_COUNT} libraries "
    f"in {_LANGUAGE_LIST}. Plot ideas come from humans; AI drafts the specification, "
    "generates code for every library, and reviews each implementation. Humans approve "
    "specs and tune the rules.</p>"
    "<h2>Pipeline</h2>"
    "<p>idea → spec (AI-drafted, human-approved) → code (AI-generated per library) → "
    "review (AI-evaluated). When a library ships a new release the pipeline re-runs; when a "
    "better example pattern emerges the spec is updated and every library regenerates. "
    "Generated code is never patched by hand.</p>"
    "<h2>Open</h2>"
    "<p>Source, specs and pipeline live at "
    '<a href="https://github.com/MarkusNeusinger/anyplot">github.com/MarkusNeusinger/anyplot</a> '
    '(MIT). Machine access is documented in <a href="https://anyplot.ai/llms.txt">llms.txt</a>; '
    "propose a new plot type via a "
    '<a href="https://github.com/MarkusNeusinger/anyplot/issues/new?labels=spec-request">spec request</a>.</p>'
)


@router.get("/seo-proxy/about")
async def seo_about():
    """Bot-optimized about page: the pipeline story, not just og:tags."""
    return HTMLResponse(
        _render_bot_html(
            title="About | anyplot.ai",
            description="About anyplot.ai — library-agnostic, AI-powered plotting.",
            image=DEFAULT_HOME_IMAGE,
            url="https://anyplot.ai/about",
            body=_ABOUT_BOT_BODY,
        )
    )


# Hex values come straight from core/palette.py — the single source of truth —
# so the bot page can never disagree with what the plots actually use.
_PALETTE_SLOT_NAMES = ("green", "lavender", "blue", "ochre", "red", "cyan", "rose", "lime")
_PALETTE_BOT_BODY = (
    "<h1>imprint — the anyplot palette</h1>"
    "<p>A colorblind-safe categorical palette of 8 hues plus 3 semantic anchors, tuned for "
    "warm-paper rendering and validated against deuteranopia, protanopia and tritanopia. "
    "Every plot in the catalogue uses it.</p>"
    "<h2>Categorical hues (slot order)</h2>"
    "<ol>"
    + "".join(
        f"<li>{name} <code>{hex_value}</code></li>"
        for name, hex_value in zip(_PALETTE_SLOT_NAMES, palette.IMPRINT, strict=True)
    )
    + "</ol>"
    "<h2>Semantic anchors (outside the categorical pool)</h2>"
    "<ul>"
    f"<li>amber <code>{palette.AMBER}</code> — warning / caution</li>"
    f"<li>neutral — theme-adaptive ink: <code>{palette.neutral_for('light')}</code> light / "
    f"<code>{palette.neutral_for('dark')}</code> dark</li>"
    f"<li>muted — theme-adaptive soft ink: <code>{palette.muted_for('light')}</code> light / "
    f"<code>{palette.muted_for('dark')}</code> dark</li>"
    "</ul>"
    "<p>Copy-paste snippets for Python, R, Julia and JavaScript are on the "
    '<a href="https://anyplot.ai/palette">interactive page</a>.</p>'
)


@router.get("/seo-proxy/palette")
async def seo_palette():
    """Bot-optimized palette page: the actual hex values, not just og:tags."""
    return HTMLResponse(
        _render_bot_html(
            title="imprint palette | anyplot.ai",
            description="Imprint — a colorblind-safe categorical palette of 8 hues plus 3 semantic anchors (amber, neutral, muted). Tuned for warm-paper rendering, validated against deuteranopia / protanopia / tritanopia. The palette every plot on anyplot.ai uses.",
            image=DEFAULT_HOME_IMAGE,
            url="https://anyplot.ai/palette",
            body=_PALETTE_BOT_BODY,
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
async def seo_stats(db: AsyncSession | None = Depends(optional_db)):
    """Bot-optimized stats page: the live catalogue counts, not just og:tags.

    Uses the same cache key the /stats endpoint populates (and the startup
    prewarm fills), so this adds no extra DB load. Without a DB the body
    degrades to the registry-derived counts.
    """
    if db is not None:

        async def _fetch() -> StatsResponse:
            return await _compute_stats(db)

        stats = await get_or_set_cache(
            cache_key("stats"), _fetch, refresh_after=settings.cache_refresh_after, refresh_factory=_refresh_stats
        )
        body = (
            "<h1>anyplot in numbers</h1>"
            "<ul>"
            f"<li>{stats.specs} plot specifications</li>"
            f"<li>{stats.plots} rendered implementations</li>"
            f"<li>{stats.libraries} libraries across {stats.languages} languages</li>"
            "</ul>"
        )
    else:
        body = (
            f"<h1>anyplot in numbers</h1><p>{_LIBRARY_COUNT} libraries across {len(LANGUAGES_METADATA)} languages.</p>"
        )
    body += (
        '<p>Live machine-readable counts: <a href="https://api.anyplot.ai/stats">api.anyplot.ai/stats</a>; '
        "per-library quality scores and coverage on the "
        '<a href="https://anyplot.ai/stats">interactive page</a>.</p>'
    )
    return HTMLResponse(
        _render_bot_html(
            title="Stats | anyplot.ai",
            description="Platform statistics: library scores, coverage, tags, and top implementations.",
            image=DEFAULT_HOME_IMAGE,
            url="https://anyplot.ai/stats",
            body=body,
        )
    )


# =============================================================================
# Spec routes — new structure: /{spec_id}, /{spec_id}/{language}, /{spec_id}/{language}/{library}
# =============================================================================


@router.get("/seo-proxy/{spec_id}")
async def seo_spec_hub(spec_id: str, db: AsyncSession | None = Depends(optional_db)):
    """Bot-optimized cross-language spec hub."""
    if db is None:
        # Degraded mode: without the catalogue we cannot tell a real spec from
        # an invented one, so this page must not be indexable — serving it
        # otherwise recreates the defect #10453 removed, an indexable
        # near-duplicate for any string anyone tries.
        return HTMLResponse(
            _render_bot_html(
                title=f"{html.escape(spec_id)} | anyplot.ai",
                description=DEFAULT_DESCRIPTION,
                image=DEFAULT_HOME_IMAGE,
                url=f"https://anyplot.ai/{html.escape(spec_id)}",
                noindex=True,
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
    """Permanent redirect: language-overview URLs are consolidated onto the hub.

    The /{spec_id}/{language} tier was consolidated into /{spec_id} to eliminate
    duplicate content. Bots following this endpoint get a 301 to the public hub
    URL; humans get the SPA redirect configured in app/src/routes/index.tsx. The
    `language` query parameter is dropped because the hub's canonical tag does
    not include it — Google should consolidate the page, not a filtered variant.
    """
    del language  # referenced for route matching only; deliberately not forwarded
    if not _SPEC_ID_RE.fullmatch(spec_id):
        raise HTTPException(status_code=404, detail="Spec not found")
    # The Location must be the PUBLIC url, not this router's internal path.
    # nginx serves crawlers by prepending /seo-proxy to the incoming request
    # URI (`proxy_pass $seo_backend/seo-proxy$request_uri`), so a Location of
    # /seo-proxy/{spec} is fetched by the bot as anyplot.ai/seo-proxy/{spec},
    # arrives here as /seo-proxy/seo-proxy/{spec}, and re-matches this very
    # route with spec_id="seo-proxy" and language="{spec}" -- which redirects
    # again, forever. Googlebot recorded the loop as 48 "Redirect error" URLs.
    #
    # Belt-and-braces redirect-target sanitisation:
    #   1. _SPEC_ID_RE.fullmatch() above already constrains spec_id to
    #      lowercase alphanum + hyphens, and requires it to be non-empty.
    #   2. urllib.parse.quote() percent-encodes anything outside [-A-Za-z0-9],
    #      which is a CodeQL-recognised sanitizer for `py/url-redirection`.
    #   3. urlparse() + scheme/netloc check guarantees the assembled URL is
    #      a same-origin path, and the explicit "//" rejection keeps it from
    #      being read as a protocol-relative url (`//evil.com`).
    safe_spec = quote(spec_id, safe="-")
    target = "/" + safe_spec
    parsed = urlparse(target)
    if parsed.scheme or parsed.netloc or not target.startswith("/") or target.startswith("//"):
        raise HTTPException(status_code=400, detail="Invalid redirect target")
    return RedirectResponse(url=target, status_code=301)


@router.get("/seo-proxy/{spec_id}/{language}/{library}")
async def seo_spec_implementation(
    spec_id: str, language: str, library: str, db: AsyncSession | None = Depends(optional_db)
):
    """Bot-optimized implementation detail."""
    if db is None:
        # Same reasoning as the hub route — unverifiable, so not indexable.
        return HTMLResponse(
            _render_bot_html(
                title=f"{html.escape(spec_id)} - {html.escape(library)} | anyplot.ai",
                description=DEFAULT_DESCRIPTION,
                image=DEFAULT_HOME_IMAGE,
                url=f"https://anyplot.ai/{html.escape(spec_id)}/{html.escape(language)}/{html.escape(library)}",
                noindex=True,
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
    if impl is None:
        # The spec exists but this language/library pair does not. This used to
        # serve a 200 with a minimal meta-only page, so that bots holding stale
        # URLs after a regen still got something — but neither segment is
        # validated anywhere, so every {spec}/{any string}/{any string} URL was
        # an indexable page carrying its own self-referencing canonical. That is
        # an unbounded supply of thin near-duplicates competing with the real
        # catalogue for the same crawl budget, and it kept 161 URLs from the
        # highcharts Python->JS migration (#8516) indexed months after the
        # implementations were deleted. They are worth 10 clicks per 28 days
        # between them, so they are dropped rather than redirected.
        raise HTTPException(status_code=404, detail="Implementation not found")

    image = f"https://api.anyplot.ai/og/{spec_id}/{language}/{library}.png" if impl.preview_url else DEFAULT_HOME_IMAGE
    code_impl = await ImplRepository(db).get_code(spec_id, library, language)
    code = strip_noqa_comments(code_impl.code) if code_impl and code_impl.code else None
    result = _build_impl_html(spec, impl, code, image)
    set_cache(key, result)
    return HTMLResponse(result)
