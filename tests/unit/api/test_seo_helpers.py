"""
Tests for SEO helper functions.

Directly tests the pure helper functions in api/routers/seo.py.
"""

from datetime import datetime
from unittest.mock import MagicMock

import pytest

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
        assert "https://pyplots.ai/" in result
        assert "https://pyplots.ai/catalog" in result
        assert "https://pyplots.ai/mcp" in result
        assert "https://pyplots.ai/legal" in result
        assert "https://pyplots.ai/stats" in result
        assert "</urlset>" in result

    def test_spec_with_impls(self) -> None:
        impl = MagicMock()
        impl.library_id = "matplotlib"
        impl.updated = datetime(2025, 3, 15)

        spec = MagicMock()
        spec.id = "scatter-basic"
        spec.impls = [impl]
        spec.updated = datetime(2025, 3, 14)

        result = _build_sitemap_xml([spec])
        assert "https://pyplots.ai/scatter-basic" in result
        assert "https://pyplots.ai/scatter-basic/matplotlib" in result
        assert "<lastmod>2025-03-14</lastmod>" in result
        assert "<lastmod>2025-03-15</lastmod>" in result

    def test_spec_without_impls_excluded(self) -> None:
        spec = MagicMock()
        spec.id = "no-impls"
        spec.impls = []

        result = _build_sitemap_xml([spec])
        assert "no-impls" not in result

    def test_multiple_specs(self) -> None:
        impl1 = MagicMock()
        impl1.library_id = "matplotlib"
        impl1.updated = None

        spec1 = MagicMock()
        spec1.id = "scatter-basic"
        spec1.impls = [impl1]
        spec1.updated = None

        impl2 = MagicMock()
        impl2.library_id = "seaborn"
        impl2.updated = None

        spec2 = MagicMock()
        spec2.id = "bar-grouped"
        spec2.impls = [impl2]
        spec2.updated = None

        result = _build_sitemap_xml([spec1, spec2])
        assert "scatter-basic" in result
        assert "bar-grouped" in result
        assert "scatter-basic/matplotlib" in result
        assert "bar-grouped/seaborn" in result

    def test_html_escaping(self) -> None:
        """Spec IDs with special characters should be escaped."""
        impl = MagicMock()
        impl.library_id = "matplotlib"
        impl.updated = None

        spec = MagicMock()
        spec.id = "test&spec"
        spec.impls = [impl]
        spec.updated = None

        result = _build_sitemap_xml([spec])
        assert "test&amp;spec" in result

    def test_spec_with_none_updated(self) -> None:
        impl = MagicMock()
        impl.library_id = "matplotlib"
        impl.updated = None

        spec = MagicMock()
        spec.id = "scatter-basic"
        spec.impls = [impl]
        spec.updated = None

        result = _build_sitemap_xml([spec])
        # Should not have lastmod when updated is None
        assert "scatter-basic</loc></url>" in result


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
        result = BOT_HTML_TEMPLATE.format(
            title="t", description="d", image="i", url="https://pyplots.ai/"
        )
        assert 'rel="canonical"' in result
        assert "https://pyplots.ai/" in result
