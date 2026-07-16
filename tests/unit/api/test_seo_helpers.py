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
    _build_home_body,
    _build_impl_html,
    _build_sitemap_xml,
    _build_spec_hub_html,
    _jsonld_script,
    _lastmod,
    _render_bot_html,
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
    return impl


def _mock_spec(impls: list) -> MagicMock:
    spec = MagicMock()
    spec.id = "scatter-basic"
    spec.title = "Basic Scatter Plot"
    spec.description = "Points on <axes> & friends"
    spec.impls = impls
    return spec


class TestLastmod:
    """Tests for _lastmod helper."""

    def test_with_datetime(self) -> None:
        dt = datetime(2025, 3, 15)
        result = _lastmod(dt)
        assert result == "<lastmod>2025-03-15</lastmod>"

    def test_with_none(self) -> None:
        assert _lastmod(None) == ""

    def test_with_different_date(self) -> None:
        dt = datetime(2024, 12, 1, 10, 30, 0)
        result = _lastmod(dt)
        assert result == "<lastmod>2024-12-01</lastmod>"


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
        assert "<lastmod>2025-03-14</lastmod>" in result
        assert "<lastmod>2025-03-15</lastmod>" in result

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
        # Should not have lastmod when updated is None
        assert "<loc>https://anyplot.ai/scatter-basic</loc></url>" in result


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
        # preview image in the body
        assert '<img src="https://api.anyplot.ai/og/scatter-basic.png"' in page
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

    def test_no_code_no_pre_block(self) -> None:
        page = self._page(code=None)
        assert "<pre>" not in page
        # page is still enriched otherwise
        assert '<a href="https://anyplot.ai/scatter-basic">' in page


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
