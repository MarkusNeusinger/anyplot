"""
Tests for SEO helper functions.

Directly tests the pure helper functions in api/routers/seo.py.
"""

from datetime import datetime
from unittest.mock import MagicMock

from api.routers.seo import BOT_HTML_TEMPLATE, _build_sitemap_xml, _lastmod


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


class TestBotHtmlTemplate:
    """Tests for the BOT_HTML_TEMPLATE."""

    def test_template_has_required_meta_tags(self) -> None:
        result = BOT_HTML_TEMPLATE.format(
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

    def test_template_has_canonical(self) -> None:
        url = "https://anyplot.ai/"
        result = BOT_HTML_TEMPLATE.format(title="t", description="d", image="i", url=url)
        assert 'rel="canonical"' in result
        assert url in result
