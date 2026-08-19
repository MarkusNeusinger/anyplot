"""
Tests for SEO helper functions.

Directly tests the pure helper functions in api/routers/seo.py.
"""

import json
import re
from datetime import datetime
from unittest.mock import MagicMock

from api.routers.seo import (
    _HOME_JSONLD,
    _META_DESCRIPTION_LIMIT,
    TEMPLATE_LAST_CHANGED,
    _build_home_body,
    _build_impl_html,
    _build_llms_full,
    _build_sitemap_xml,
    _build_spec_hub_html,
    _jsonld_script,
    _lastmod,
    _meta_description,
    _render_asset_list,
    _render_bot_html,
    _render_picture,
    _sized_srcset,
    _spec_index_entries,
    _spec_links_html,
)
from core.constants import LANGUAGES_METADATA, LIBRARIES_METADATA


def _extract_jsonld(page: str) -> dict:
    """Pull the JSON-LD payload back out of a rendered bot page."""
    match = re.search(r'<script type="application/ld\+json">(.*?)</script>', page, re.S)
    assert match, "page has no JSON-LD script"
    return json.loads(match.group(1))


def _mock_impl(library_id: str, language: str, preview: str | None = "https://gcs/preview.png") -> MagicMock:
    impl = MagicMock()
    impl.library_id = library_id
    impl.library = MagicMock()
    impl.library.language = language
    impl.preview_url = preview
    # Concrete values — the JSON-LD builder serializes these, and a MagicMock
    # auto-attribute is neither JSON-serializable nor orderable.
    impl.preview_url_light = preview
    impl.preview_url_dark = None
    impl.preview_html_light = None
    impl.preview_html_dark = None
    impl.quality_score = 90.0
    impl.updated = None
    return impl


def _mock_spec(impls: list) -> MagicMock:
    spec = MagicMock()
    spec.id = "scatter-basic"
    spec.title = "Basic Scatter Plot"
    spec.description = "Points on <axes> & friends"
    spec.tags = {"plot_type": "scatter", "features": ["error-bars"]}
    spec.impls = impls
    return spec


class TestLastmod:
    """lastmod describes the page, which is not the same as the row behind it."""

    def test_a_record_newer_than_the_template_wins(self) -> None:
        dt = datetime(2099, 3, 15)
        assert _lastmod(dt) == "<lastmod>2099-03-15</lastmod>"

    def test_an_older_record_is_lifted_to_the_template_date(self) -> None:
        """The row has not moved, but the page it renders into has."""
        stamp = TEMPLATE_LAST_CHANGED.strftime("%Y-%m-%d")
        assert _lastmod(datetime(2024, 12, 1, 10, 30, 0)) == f"<lastmod>{stamp}</lastmod>"

    def test_without_a_record_date_the_template_date_still_applies(self) -> None:
        """The page was last modified at least when its template was."""
        stamp = TEMPLATE_LAST_CHANGED.strftime("%Y-%m-%d")
        assert _lastmod(None) == f"<lastmod>{stamp}</lastmod>"


class TestBuildSitemapXml:
    """Tests for _build_sitemap_xml."""

    def test_empty_specs(self) -> None:
        result = _build_sitemap_xml([])
        assert '<?xml version="1.0"' in result
        assert "<urlset" in result
        assert "<loc>https://anyplot.ai/</loc>" in result
        assert "<loc>https://anyplot.ai/plots</loc>" in result
        assert "<loc>https://anyplot.ai/specs</loc>" in result
        assert "<loc>https://anyplot.ai/libraries</loc>" in result
        assert "<loc>https://anyplot.ai/map</loc>" in result
        assert "<loc>https://anyplot.ai/palette</loc>" in result
        assert "<loc>https://anyplot.ai/about</loc>" in result
        assert "<loc>https://anyplot.ai/mcp</loc>" in result
        assert "<loc>https://anyplot.ai/legal</loc>" in result
        assert "<loc>https://anyplot.ai/stats</loc>" in result
        assert "</urlset>" in result

    def test_spec_with_impls(self) -> None:
        """Spec with impls should emit hub and detail URLs (no per-language tier)."""
        library = MagicMock()
        library.language = "python"

        impl = MagicMock()
        impl.library_id = "matplotlib"
        impl.library = library
        impl.updated = datetime(2025, 3, 15)

        spec = MagicMock()
        spec.id = "scatter-basic"
        spec.impls = [impl]
        spec.updated = datetime(2025, 3, 14)

        result = _build_sitemap_xml([spec])
        # Cross-language hub
        assert "<loc>https://anyplot.ai/scatter-basic</loc>" in result
        # Implementation detail
        assert "<loc>https://anyplot.ai/scatter-basic/python/matplotlib</loc>" in result
        # Language-overview URL is consolidated onto the hub via ?language=; it
        # must NOT appear as its own sitemap entry (duplicate content for Google).
        assert "<loc>https://anyplot.ai/scatter-basic/python</loc>" not in result
        # Legacy /python/{spec} path must NOT appear
        assert "https://anyplot.ai/python/scatter-basic" not in result
        # The record's own date is older than the template's, so the page's
        # lastmod is the template's — the page changed even though the row did not.
        stamp = TEMPLATE_LAST_CHANGED.strftime("%Y-%m-%d")
        assert f"<lastmod>{stamp}</lastmod>" in result
        assert "<lastmod>2025-03-14</lastmod>" not in result
        assert "<lastmod>2025-03-15</lastmod>" not in result

    def test_spec_without_impls_excluded(self) -> None:
        spec = MagicMock()
        spec.id = "no-impls"
        spec.impls = []

        result = _build_sitemap_xml([spec])
        assert "no-impls" not in result

    def test_multiple_specs(self) -> None:
        lib_mpl = MagicMock()
        lib_mpl.language = "python"
        impl1 = MagicMock()
        impl1.library_id = "matplotlib"
        impl1.library = lib_mpl
        impl1.updated = None

        spec1 = MagicMock()
        spec1.id = "scatter-basic"
        spec1.impls = [impl1]
        spec1.updated = None

        lib_sns = MagicMock()
        lib_sns.language = "python"
        impl2 = MagicMock()
        impl2.library_id = "seaborn"
        impl2.library = lib_sns
        impl2.updated = None

        spec2 = MagicMock()
        spec2.id = "bar-grouped"
        spec2.impls = [impl2]
        spec2.updated = None

        result = _build_sitemap_xml([spec1, spec2])
        assert "<loc>https://anyplot.ai/scatter-basic</loc>" in result
        assert "<loc>https://anyplot.ai/bar-grouped</loc>" in result
        assert "<loc>https://anyplot.ai/scatter-basic/python/matplotlib</loc>" in result
        assert "<loc>https://anyplot.ai/bar-grouped/python/seaborn</loc>" in result

    def test_no_language_overview_emitted(self) -> None:
        """Multiple impls sharing a language must NOT emit a /{spec}/{language} URL.

        Language filtering is served as /{spec}?language={language} (filtered hub,
        same canonical as the unfiltered hub), so sitemap entries for the
        language tier would create duplicate-content URLs for search engines.
        """
        library = MagicMock()
        library.language = "python"

        impl_mpl = MagicMock()
        impl_mpl.library_id = "matplotlib"
        impl_mpl.library = library
        impl_mpl.updated = None

        impl_sns = MagicMock()
        impl_sns.library_id = "seaborn"
        impl_sns.library = library
        impl_sns.updated = None

        spec = MagicMock()
        spec.id = "scatter-basic"
        spec.impls = [impl_mpl, impl_sns]
        spec.updated = None

        result = _build_sitemap_xml([spec])
        # No language-overview URL
        assert "<loc>https://anyplot.ai/scatter-basic/python</loc>" not in result
        # Hub + both implementations are present
        assert "<loc>https://anyplot.ai/scatter-basic</loc>" in result
        assert "<loc>https://anyplot.ai/scatter-basic/python/matplotlib</loc>" in result
        assert "<loc>https://anyplot.ai/scatter-basic/python/seaborn</loc>" in result

    def test_html_escaping(self) -> None:
        """Spec IDs with special characters should be escaped."""
        library = MagicMock()
        library.language = "python"

        impl = MagicMock()
        impl.library_id = "matplotlib"
        impl.library = library
        impl.updated = None

        spec = MagicMock()
        spec.id = "test&spec"
        spec.impls = [impl]
        spec.updated = None

        result = _build_sitemap_xml([spec])
        assert "test&amp;spec" in result

    def test_spec_with_none_updated(self) -> None:
        library = MagicMock()
        library.language = "python"

        impl = MagicMock()
        impl.library_id = "matplotlib"
        impl.library = library
        impl.updated = None

        spec = MagicMock()
        spec.id = "scatter-basic"
        spec.impls = [impl]
        spec.updated = None

        result = _build_sitemap_xml([spec])
        # A missing `updated` no longer means a missing lastmod: the page was
        # last modified at least when its template was, and saying nothing left
        # Google with no reason to recrawl pages whose rendering had changed.
        stamp = TEMPLATE_LAST_CHANGED.strftime("%Y-%m-%d")
        assert f"<loc>https://anyplot.ai/scatter-basic</loc><lastmod>{stamp}</lastmod></url>" in result


class TestRenderBotHtml:
    """Tests for _render_bot_html (the template wrapper every bot route uses)."""

    def test_has_required_meta_tags(self) -> None:
        result = _render_bot_html(
            title="Test Title",
            description="Test Description",
            image="https://example.com/image.png",
            url="https://example.com",
        )
        assert "og:title" in result
        assert "og:description" in result
        assert "og:image" in result
        assert "og:url" in result
        assert "twitter:card" in result
        assert "summary_large_image" in result
        assert "Test Title" in result
        assert "Test Description" in result

    def test_has_canonical(self) -> None:
        url = "https://anyplot.ai/"
        result = _render_bot_html(title="t", description="d", image="i", url=url)
        assert 'rel="canonical"' in result
        assert url in result

    def test_default_body_and_nav(self) -> None:
        result = _render_bot_html(title="t", description="d", image="i", url="u")
        assert "<h1>t</h1><p>d</p>" in result
        assert '<a href="https://anyplot.ai/plots">plots</a>' in result

    def test_custom_body_replaces_default(self) -> None:
        result = _render_bot_html(title="t", description="d", image="i", url="u", body="<h1>custom</h1>")
        assert "<h1>custom</h1>" in result
        assert "<h1>t</h1>" not in result
        # nav is still appended after custom bodies
        assert "<nav>" in result

    def test_body_with_braces_survives_format(self) -> None:
        """Code bodies contain {braces}; they must not be treated as format fields."""
        result = _render_bot_html(title="t", description="d", image="i", url="u", body="<pre>d = {'a': 1}</pre>")
        assert "d = {'a': 1}" in result

    def test_no_jsonld_by_default(self) -> None:
        result = _render_bot_html(title="t", description="d", image="i", url="u")
        assert "application/ld+json" not in result

    def test_indexable_pages_ask_for_large_image_previews(self) -> None:
        result = _render_bot_html(title="t", description="d", image="i", url="u")
        assert '<meta name="robots" content="max-image-preview:large" />' in result

    def test_noindex_replaces_the_robots_content(self) -> None:
        result = _render_bot_html(title="t", description="d", image="i", url="u", noindex=True)
        assert '<meta name="robots" content="noindex" />' in result
        assert "max-image-preview" not in result


class TestJsonldScript:
    """Tests for _jsonld_script."""

    def test_round_trips_payload(self) -> None:
        payload = {"@type": "Thing", "name": "scatter"}
        script = _jsonld_script(payload)
        assert script.strip().startswith('<script type="application/ld+json">')
        inner = re.search(r">(.*)</script>", script, re.S).group(1)  # type: ignore[union-attr]
        assert json.loads(inner) == payload

    def test_script_breakout_is_escaped(self) -> None:
        """DB-sourced text containing </script> must not close the element early."""
        payload = {"name": "evil</script><script>alert(1)</script>"}
        script = _jsonld_script(payload)
        # the only literal "</" left is the script tag's own closer
        assert script.count("</") == 1
        inner = re.search(r">(.*)</script>", script, re.S).group(1)  # type: ignore[union-attr]
        assert json.loads(inner) == payload


class TestBuildSpecHubHtml:
    """Tests for the enriched cross-language hub page."""

    def test_links_every_impl_and_carries_jsonld(self) -> None:
        spec = _mock_spec([_mock_impl("matplotlib", "python"), _mock_impl("ggplot2", "r")])
        page = _build_spec_hub_html(spec, "https://api.anyplot.ai/og/scatter-basic.png")

        assert '<a href="https://anyplot.ai/scatter-basic/python/matplotlib">' in page
        assert '<a href="https://anyplot.ai/scatter-basic/r/ggplot2">' in page
        # display names from core.constants, not raw ids
        assert "in Matplotlib (Python)" in page
        assert "in ggplot2 (R)" in page
        # the body shows the best actual render, not the og collage card —
        # the hub was the one page type where a machine could enumerate every
        # implementation link yet not reach a single plot image
        assert '<img src="https://gcs/preview_1200.png"' in page
        assert "Preview render from the Matplotlib implementation." in page
        assert '<img src="https://api.anyplot.ai/og/scatter-basic.png"' not in page
        # the collage card stays the social preview
        assert '<meta property="og:image" content="https://api.anyplot.ai/og/scatter-basic.png" />' in page
        # description is escaped
        assert "&lt;axes&gt; &amp; friends" in page

        jsonld = _extract_jsonld(page)
        breadcrumb, item_list = jsonld["@graph"]
        assert breadcrumb["@type"] == "BreadcrumbList"
        assert breadcrumb["itemListElement"][1]["item"] == "https://anyplot.ai/scatter-basic"
        assert item_list["@type"] == "ItemList"
        assert [i["url"] for i in item_list["itemListElement"]] == [
            "https://anyplot.ai/scatter-basic/python/matplotlib",
            "https://anyplot.ai/scatter-basic/r/ggplot2",
        ]
        # per-item render URLs: one hub fetch enumerates every plot image
        assert [i["image"] for i in item_list["itemListElement"]] == ["https://gcs/preview.png"] * 2

    def test_hub_without_previews_falls_back_to_card(self) -> None:
        spec = _mock_spec([_mock_impl("matplotlib", "python", preview=None)])
        page = _build_spec_hub_html(spec, "https://api.anyplot.ai/og/scatter-basic.png")
        assert '<img src="https://api.anyplot.ai/og/scatter-basic.png"' in page
        item_list = _extract_jsonld(page)["@graph"][1]
        assert "image" not in item_list["itemListElement"][0]


class TestBuildImplHtml:
    """Tests for the enriched implementation page."""

    def _page(self, code: str | None = "plt.scatter(x, y)  # x < y") -> str:
        impl = _mock_impl("matplotlib", "python")
        spec = _mock_spec([impl, _mock_impl("seaborn", "python"), _mock_impl("makie", "julia")])
        return _build_impl_html(spec, impl, code, "https://api.anyplot.ai/og/scatter-basic/python/matplotlib.png")

    def test_code_block_is_escaped(self) -> None:
        page = self._page("if x < 2:\n    plot()</script>")
        assert "<pre><code>if x &lt; 2:\n    plot()&lt;/script&gt;</code></pre>" in page

    def test_links_hub_and_siblings_but_not_self(self) -> None:
        page = self._page()
        assert '<a href="https://anyplot.ai/scatter-basic">' in page
        assert '<a href="https://anyplot.ai/scatter-basic/python/seaborn">' in page
        assert '<a href="https://anyplot.ai/scatter-basic/julia/makie">' in page
        assert "in Makie.jl (Julia)" in page
        assert '<a href="https://anyplot.ai/scatter-basic/python/matplotlib">' not in page

    def test_jsonld_software_source_code(self) -> None:
        jsonld = _extract_jsonld(self._page())
        breadcrumb, source = jsonld["@graph"]
        assert [i["name"] for i in breadcrumb["itemListElement"]] == ["anyplot.ai", "Basic Scatter Plot", "Matplotlib"]
        assert source["@type"] == "SoftwareSourceCode"
        assert source["programmingLanguage"] == "Python"
        assert source["url"] == "https://anyplot.ai/scatter-basic/python/matplotlib"
        # fields an assistant checks before reusing the code — these lived only
        # in the SPA's JSON-LD, which no crawler executes
        assert source["license"] == "https://opensource.org/licenses/MIT"
        assert source["codeRepository"] == "https://github.com/MarkusNeusinger/anyplot"
        assert source["isBasedOn"] == "https://anyplot.ai/scatter-basic"
        # tag bag flattens into keywords (string and list values alike)
        assert source["keywords"] == ["scatter", "error-bars"]

    def test_jsonld_keywords_are_deterministic_and_deduplicated(self) -> None:
        """Insertion order of the stored JSON must not leak into the output."""
        impl = _mock_impl("matplotlib", "python")
        spec = _mock_spec([impl])
        # Deliberately scrambled insertion order + a duplicate across categories
        spec.tags = {"features": ["basic", "scatter"], "domain": ["statistics"], "plot_type": "scatter"}
        page = _build_impl_html(spec, impl, "code()", "https://api.anyplot.ai/og/card.png")
        source = _extract_jsonld(page)["@graph"][1]
        # Canonical category order (plot_type before domain before features),
        # duplicate "scatter" kept only at its first canonical position
        assert source["keywords"] == ["scatter", "statistics", "basic"]

    def test_jsonld_image_is_the_render_not_the_card(self) -> None:
        source = _extract_jsonld(self._page())["@graph"][1]
        image = source["image"]
        assert image["@type"] == "ImageObject"
        assert image["contentUrl"] == "https://gcs/preview.png"
        assert image["thumbnailUrl"] == "https://gcs/preview_1200.png"

    def test_jsonld_without_render_keeps_card_image(self) -> None:
        impl = _mock_impl("matplotlib", "python", preview=None)
        spec = _mock_spec([impl])
        page = _build_impl_html(spec, impl, "code()", "https://api.anyplot.ai/og/card.png")
        source = _extract_jsonld(page)["@graph"][1]
        assert source["image"] == "https://api.anyplot.ai/og/card.png"

    def test_no_code_no_pre_block(self) -> None:
        page = self._page(code=None)
        assert "<pre>" not in page
        # page is still enriched otherwise
        assert '<a href="https://anyplot.ai/scatter-basic">' in page


class TestBuildLlmsFull:
    """Tests for the llms-full.txt catalogue index."""

    def test_one_line_per_spec_with_sorted_libraries(self) -> None:
        spec = _mock_spec([_mock_impl("seaborn", "python"), _mock_impl("ggplot2", "r")])
        text = _build_llms_full([spec])
        assert "scatter-basic | Basic Scatter Plot | https://anyplot.ai/scatter-basic | ggplot2,seaborn" in text

    def test_specs_without_impls_are_skipped(self) -> None:
        empty = _mock_spec([])
        empty.id = "unpublished"
        text = _build_llms_full([empty, _mock_spec([_mock_impl("matplotlib", "python")])])
        assert "unpublished" not in text
        assert "scatter-basic" in text

    def test_header_documents_ua_independent_retrieval(self) -> None:
        """The header is the point: recipes that work without a crawler UA."""
        text = _build_llms_full([])
        assert "https://api.anyplot.ai/specs/{spec_id}/{library}/code" in text
        assert "https://storage.googleapis.com/anyplot-images/plots/" in text
        assert "https://api.anyplot.ai/openapi.json" in text


class TestSpecIndex:
    """Tests for the spec-hub link index behind /seo-proxy/{,plots,specs}."""

    def _spec(self, spec_id: str, title: str, impls: list | None = None) -> MagicMock:
        spec = MagicMock()
        spec.id = spec_id
        spec.title = title
        spec.impls = [MagicMock()] if impls is None else impls
        return spec

    def test_entries_are_title_sorted_and_skip_implless_specs(self) -> None:
        specs = [
            self._spec("violin-basic", "Violin Plot"),
            self._spec("bar-grouped", "Grouped Bar Chart"),
            self._spec("empty-spec", "Empty Spec", impls=[]),
        ]
        assert _spec_index_entries(specs) == [("bar-grouped", "Grouped Bar Chart"), ("violin-basic", "Violin Plot")]

    def test_entries_fall_back_to_id_without_title(self) -> None:
        assert _spec_index_entries([self._spec("bar-grouped", "")]) == [("bar-grouped", "bar-grouped")]

    def test_links_html_links_every_hub_and_escapes(self) -> None:
        html_out = _spec_links_html([("bar-grouped", "Grouped Bar Chart"), ("x", "a < b & c")])
        assert '<a href="https://anyplot.ai/bar-grouped">Grouped Bar Chart</a>' in html_out
        assert "a &lt; b &amp; c" in html_out
        assert "<h2>All plot specifications</h2>" in html_out

    def test_links_html_empty_index(self) -> None:
        assert _spec_links_html([]) == ""


class TestHomePage:
    """Tests for the bot homepage body and site-level JSON-LD."""

    def test_body_uses_spec_count_when_known(self) -> None:
        body = _build_home_body(324)
        assert "324 plot specifications" in body
        assert "Matplotlib" in body  # library list from the canonical registry
        assert '<a href="https://anyplot.ai/mcp">' in body

    def test_body_without_spec_count(self) -> None:
        body = _build_home_body(None)
        assert "hundreds of plot specifications" in body

    def test_jsonld_mirrors_index_html_site_schemas(self) -> None:
        """WebSite + SearchAction and Organization must match app/index.html."""
        types = {node["@type"]: node for node in _HOME_JSONLD["@graph"]}
        assert {"WebApplication", "WebSite", "Organization"} <= set(types)
        action = types["WebSite"]["potentialAction"]
        assert action["@type"] == "SearchAction"
        # /plots?spec= is the only term-carrying catalog param the SPA supports
        assert action["target"]["urlTemplate"] == "https://anyplot.ai/plots?spec={search_term_string}"
        assert types["Organization"]["url"] == "https://anyplot.ai"
        assert types["WebSite"]["url"] == "https://anyplot.ai"


class TestDisplayNameMaps:
    """The registry-derived name maps must cover the full canonical registry."""

    def test_language_names_cover_registry(self) -> None:
        from api.routers.seo import _LANGUAGE_NAMES

        assert set(_LANGUAGE_NAMES) == {lang["id"] for lang in LANGUAGES_METADATA}

    def test_library_names_cover_registry(self) -> None:
        from api.routers.seo import _LIBRARY_NAMES

        assert set(_LIBRARY_NAMES) == {lib["id"] for lib in LIBRARIES_METADATA}


class TestMetaDescription:
    """Trimming spec descriptions down to what a search result will display."""

    def test_short_text_is_untouched(self) -> None:
        text = "A vertical bar chart for categorical data."
        assert _meta_description(text) == text

    def test_none_and_empty_are_empty(self) -> None:
        assert _meta_description(None) == ""
        assert _meta_description("   ") == ""

    def test_whitespace_is_normalised(self) -> None:
        assert _meta_description("two\n\n  words") == "two words"

    def test_long_text_fits_the_snippet(self) -> None:
        text = "word " * 200
        result = _meta_description(text)
        assert len(result) <= _META_DESCRIPTION_LIMIT + 1  # +1 for the ellipsis

    def test_prefers_a_sentence_boundary_in_range(self) -> None:
        """Ends on the last full sentence that still fits, not the first."""
        first = "A vertical bar chart that displays categorical data with rectangular bars."
        second = "Heights are proportional to values."
        text = f"{first} {second} " + "Detail that runs well past the snippet limit. " * 5
        result = _meta_description(text)
        assert result == f"{first} {second}"
        assert len(result) <= _META_DESCRIPTION_LIMIT

    def test_single_overlong_sentence_is_not_kept_whole(self) -> None:
        """A sentence end past the limit must not be selected."""
        text = "One enormous clause " * 20 + "and then a stop."
        result = _meta_description(text)
        assert len(result) <= _META_DESCRIPTION_LIMIT + 1
        assert result.endswith("\u2026")

    def test_falls_back_to_a_word_boundary(self) -> None:
        text = "word " * 200  # no sentence punctuation anywhere
        result = _meta_description(text)
        assert result.endswith("\u2026")
        assert not result.rstrip("\u2026").endswith(" ")
        # never splits a word
        assert all(chunk == "word" for chunk in result.rstrip("\u2026").split())

    def test_short_opening_sentence_does_not_win(self) -> None:
        """A sentence ending before the halfway mark is not worth the whole slot."""
        text = "A Smith chart. " + "It maps complex impedance onto a normalised polar grid " * 5
        result = _meta_description(text)
        assert result != "A Smith chart."
        assert len(result) > _META_DESCRIPTION_LIMIT // 2
        assert result.endswith("\u2026")

    def test_never_cuts_a_dangling_separator(self) -> None:
        text = "alpha beta gamma, " * 40
        result = _meta_description(text)
        assert ",\u2026" not in result

    def test_runs_before_escaping_so_entities_stay_intact(self) -> None:
        """The trim operates on raw text; escaping afterwards can't be cut mid-entity."""
        import html as html_module

        text = "Ampersands & angle brackets <like this> " * 20
        escaped = html_module.escape(_meta_description(text))
        # A truncated entity would leave a bare & followed by a non-entity run
        assert re.search(r"&(?!amp;|lt;|gt;|quot;|#x27;)", escaped) is None


class TestPlotRender:
    """The body shows the plot itself, not the social card it sits inside."""

    BASE = "https://storage.googleapis.com/anyplot-images/plots/box-basic/python/altair"

    def _impl(self, dark: bool = True) -> MagicMock:
        impl = MagicMock()
        impl.preview_url_light = f"{self.BASE}/plot-light.png"
        impl.preview_url_dark = f"{self.BASE}/plot-dark.png" if dark else None
        return impl

    def test_srcset_offers_the_pipeline_widths(self) -> None:
        """The suffix IS the pixel width — verified against the live renders."""
        assert _sized_srcset(f"{self.BASE}/plot-light.png") == (
            f"{self.BASE}/plot-light_400.png 400w, "
            f"{self.BASE}/plot-light_800.png 800w, "
            f"{self.BASE}/plot-light_1200.png 1200w"
        )

    def test_the_full_size_original_is_not_in_the_srcset(self) -> None:
        """Its width varies per plot (2400, 3200, 4766) — no honest `w` exists."""
        srcset = _sized_srcset(f"{self.BASE}/plot-light.png")
        assert f"{self.BASE}/plot-light.png" not in srcset

    def test_default_src_is_the_middle_size(self) -> None:
        """A consumer ignoring srcset should not pull a 4766px file."""
        assert f'src="{self.BASE}/plot-light_1200.png"' in _render_picture(self._impl(), "alt")

    def test_dark_variant_is_offered(self) -> None:
        html_out = _render_picture(self._impl(), "alt")
        assert 'media="(prefers-color-scheme: dark)"' in html_out
        assert f"{self.BASE}/plot-dark_800.png 800w" in html_out

    def test_no_source_element_without_a_dark_render(self) -> None:
        assert "<source" not in _render_picture(self._impl(dark=False), "alt")

    def test_the_full_resolution_stays_reachable(self) -> None:
        """Left out of the srcset, so it needs its own way in."""
        assert f'<a href="{self.BASE}/plot-light.png">' in _render_picture(self._impl(), "alt")


class TestRenderAssetList:
    """A <picture> hides which file is which; the list says it in words."""

    BASE = "https://storage.googleapis.com/anyplot-images/plots/bar-basic/python/plotly"

    def _impl(self, interactive: bool = True) -> MagicMock:
        impl = MagicMock()
        impl.preview_url_light = f"{self.BASE}/plot-light.png"
        impl.preview_url_dark = f"{self.BASE}/plot-dark.png"
        impl.preview_html_light = f"{self.BASE}/plot-light.html" if interactive else None
        impl.preview_html_dark = f"{self.BASE}/plot-dark.html" if interactive else None
        impl.updated = None  # serialized into JSON-LD — must not be a MagicMock
        return impl

    def test_names_both_themes_explicitly(self) -> None:
        """A media query tells a browser which file to take, not a reader which is which."""
        out = _render_asset_list(self._impl())
        assert f'<a href="{self.BASE}/plot-light.png">Full-resolution render, light theme</a>' in out
        assert f'<a href="{self.BASE}/plot-dark.png">Full-resolution render, dark theme</a>' in out

    def test_exposes_the_interactive_version(self) -> None:
        """Two thirds of the catalogue has one and nothing machine-facing mentioned it."""
        out = _render_asset_list(self._impl())
        assert f'<a href="{self.BASE}/plot-light.html">Interactive version, light theme</a>' in out
        assert f'<a href="{self.BASE}/plot-dark.html">Interactive version, dark theme</a>' in out

    def test_a_quoted_spec_title_cannot_break_the_alt_attribute(self) -> None:
        """Verified through the real builder, not the helper in isolation.

        The helper takes pre-escaped text by contract; what matters is whether
        the caller honours it, so this drives _build_impl_html with a title that
        would break the attribute if it did not.
        """
        spec = MagicMock()
        spec.id = "bar-basic"
        spec.title = 'Bar "Chart" & <b>'
        spec.description = "d"
        library = MagicMock()
        library.language = "python"
        library.name = "Altair"
        impl = self._impl()
        impl.library = library
        impl.library_id = "altair"
        spec.impls = [impl]

        out = _build_impl_html(spec, impl, None, "https://api.anyplot.ai/og/x.png")
        assert 'alt="Bar &quot;Chart&quot; &amp; &lt;b&gt; rendered with Altair"' in out
        # and not double-escaped into visible noise
        assert "&amp;quot;" not in out

    def test_omits_what_an_implementation_does_not_have(self) -> None:
        """A static library must not be advertised as interactive."""
        out = _render_asset_list(self._impl(interactive=False))
        assert "Interactive version" not in out
        assert "Full-resolution render, light theme" in out
