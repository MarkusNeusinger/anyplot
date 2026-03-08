"""
Tests for api/routers/ endpoints.

Tests the modular router endpoints.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from api.main import app, fastapi_app
from api.routers.plots import (
    _calculate_contextual_counts,
    _calculate_global_counts,
    _calculate_or_counts,
    _image_matches_groups,
)
from core.database import get_db
from tests.conftest import TEST_IMAGE_URL, TEST_THUMB_URL


# Path to patch is_db_configured - it's now in api.dependencies
DB_CONFIG_PATCH = "api.dependencies.is_db_configured"


@pytest.fixture
def client() -> TestClient:
    """Create a test client for the FastAPI app."""
    return TestClient(app)


@pytest.fixture
def db_client():
    """Create a test client with mocked database dependency.

    This fixture overrides get_db to return a mock session and
    patches is_db_configured to return True, enabling proper
    testing of endpoints that use optional_db.
    """
    mock_session = AsyncMock()

    async def mock_get_db():
        yield mock_session

    fastapi_app.dependency_overrides[get_db] = mock_get_db

    with patch(DB_CONFIG_PATCH, return_value=True):
        client = TestClient(app)
        yield client, mock_session

    fastapi_app.dependency_overrides.clear()


@pytest.fixture
def mock_spec():
    """Create a mock spec with implementation."""
    mock_impl = MagicMock()
    mock_impl.library_id = "matplotlib"
    mock_impl.library = MagicMock()
    mock_impl.library.name = "Matplotlib"
    mock_impl.preview_url = TEST_IMAGE_URL
    mock_impl.preview_thumb = TEST_THUMB_URL
    mock_impl.preview_html = None
    mock_impl.quality_score = 92.5
    mock_impl.code = "import matplotlib.pyplot as plt"
    mock_impl.generated_at = None
    mock_impl.generated_by = "claude"
    mock_impl.python_version = "3.13"
    mock_impl.library_version = "3.10.0"
    # Review fields (must be proper types, not MagicMock)
    mock_impl.review_image_description = "A scatter plot showing data points"
    mock_impl.review_criteria_checklist = {"visual_quality": {"score": 36, "max": 40}}
    mock_impl.review_verdict = "APPROVED"
    mock_impl.review_strengths = ["Clean code", "Good visualization"]
    mock_impl.review_weaknesses = ["Could use better labels"]
    # Implementation-level tags
    mock_impl.impl_tags = {"patterns": ["data-generation"], "styling": ["alpha-blending"]}

    mock_spec = MagicMock()
    mock_spec.id = "scatter-basic"
    mock_spec.title = "Basic Scatter Plot"
    mock_spec.description = "A basic scatter plot"
    mock_spec.applications = ["data visualization"]
    mock_spec.data = ["numeric"]
    mock_spec.notes = ["Use for 2D data"]
    mock_spec.tags = {
        "plot_type": ["scatter"],
        "domain": ["statistics"],
        "data_type": ["numeric"],
        "features": ["basic"],
    }
    mock_spec.issue = 42
    mock_spec.suggested = "contributor"
    mock_spec.created = None  # Must be None or datetime, not MagicMock
    mock_spec.updated = None  # Must be None or datetime, not MagicMock
    mock_spec.impls = [mock_impl]

    return mock_spec


@pytest.fixture
def mock_lib():
    """Create a mock library."""
    mock_lib = MagicMock()
    mock_lib.id = "matplotlib"
    mock_lib.name = "Matplotlib"
    mock_lib.version = "3.10.0"
    mock_lib.documentation_url = "https://matplotlib.org"
    mock_lib.description = "Comprehensive library for visualizations"
    return mock_lib


class TestStatsRouter:
    """Tests for stats router."""

    def test_stats_without_db(self, client: TestClient) -> None:
        """Stats should return zeros when DB not configured."""
        with patch(DB_CONFIG_PATCH, return_value=False):
            response = client.get("/stats")
            assert response.status_code == 200
            data = response.json()
            assert data["specs"] == 0
            assert data["plots"] == 0
            assert "libraries" in data

    def test_stats_with_db(self, db_client, mock_spec, mock_lib) -> None:
        """Stats should return counts when DB is configured."""
        client, _ = db_client

        mock_spec_repo = MagicMock()
        mock_spec_repo.get_all = AsyncMock(return_value=[mock_spec])

        mock_lib_repo = MagicMock()
        mock_lib_repo.get_all = AsyncMock(return_value=[mock_lib])

        with (
            patch("api.routers.stats.get_cache", return_value=None),
            patch("api.routers.stats.set_cache"),
            patch("api.routers.stats.SpecRepository", return_value=mock_spec_repo),
            patch("api.routers.stats.LibraryRepository", return_value=mock_lib_repo),
        ):
            response = client.get("/stats")
            assert response.status_code == 200
            data = response.json()
            assert data["specs"] == 1
            assert data["plots"] == 1
            assert data["libraries"] == 1

    def test_stats_cached(self, db_client) -> None:
        """Stats should return cached response when available."""
        client, _ = db_client
        cached_response = {"specs": 5, "plots": 10, "libraries": 9}

        with patch("api.routers.stats.get_cache", return_value=cached_response):
            response = client.get("/stats")
            assert response.status_code == 200
            data = response.json()
            assert data["specs"] == 5
            assert data["plots"] == 10


class TestLibrariesRouter:
    """Tests for libraries router."""

    def test_libraries_without_db(self, client: TestClient) -> None:
        """Libraries should return seed data when DB not configured."""
        with patch(DB_CONFIG_PATCH, return_value=False):
            response = client.get("/libraries")
            assert response.status_code == 200
            data = response.json()
            assert "libraries" in data
            assert len(data["libraries"]) > 0

    def test_library_images_without_db(self, client: TestClient) -> None:
        """Library images should return 503 when DB not configured."""
        with patch(DB_CONFIG_PATCH, return_value=False):
            response = client.get("/libraries/matplotlib/images")
            assert response.status_code == 503

    def test_library_images_invalid_library(self, client: TestClient) -> None:
        """Library images should return 404 for invalid library."""
        mock_spec_repo = MagicMock()
        mock_spec_repo.get_all = AsyncMock(return_value=[])

        with (
            patch(DB_CONFIG_PATCH, return_value=True),
            patch("api.routers.libraries.get_cache", return_value=None),
            patch("api.routers.libraries.set_cache"),
            patch("api.routers.libraries.SpecRepository", return_value=mock_spec_repo),
        ):
            response = client.get("/libraries/invalid_lib/images")
            assert response.status_code == 404

    def test_libraries_with_db(self, db_client, mock_lib) -> None:
        """Libraries should return data from DB when configured."""
        client, _ = db_client

        mock_lib_repo = MagicMock()
        mock_lib_repo.get_all = AsyncMock(return_value=[mock_lib])

        with (
            patch("api.routers.libraries.get_cache", return_value=None),
            patch("api.routers.libraries.set_cache"),
            patch("api.routers.libraries.LibraryRepository", return_value=mock_lib_repo),
        ):
            response = client.get("/libraries")
            assert response.status_code == 200
            data = response.json()
            assert "libraries" in data
            assert len(data["libraries"]) == 1
            assert data["libraries"][0]["id"] == "matplotlib"

    def test_libraries_cache_hit(self, db_client) -> None:
        """Libraries should return cached data when available."""
        client, _ = db_client

        cached_data = {"libraries": [{"id": "cached_lib", "name": "Cached"}]}

        with patch("api.routers.libraries.get_cache", return_value=cached_data):
            response = client.get("/libraries")
            assert response.status_code == 200
            data = response.json()
            assert data["libraries"][0]["id"] == "cached_lib"

    def test_library_images_with_db(self, db_client, mock_spec) -> None:
        """Library images should return images from DB."""
        client, _ = db_client

        mock_spec_repo = MagicMock()
        mock_spec_repo.get_all = AsyncMock(return_value=[mock_spec])

        with (
            patch("api.routers.libraries.get_cache", return_value=None),
            patch("api.routers.libraries.set_cache"),
            patch("api.routers.libraries.SpecRepository", return_value=mock_spec_repo),
        ):
            response = client.get("/libraries/matplotlib/images")
            assert response.status_code == 200
            data = response.json()
            assert data["library"] == "matplotlib"
            assert len(data["images"]) == 1
            assert data["images"][0]["spec_id"] == "scatter-basic"

    def test_library_images_cache_hit(self, db_client) -> None:
        """Library images should return cached data when available."""
        client, _ = db_client

        cached_data = {"library": "matplotlib", "images": [{"spec_id": "cached"}]}

        with patch("api.routers.libraries.get_cache", return_value=cached_data):
            response = client.get("/libraries/matplotlib/images")
            assert response.status_code == 200
            data = response.json()
            assert data["images"][0]["spec_id"] == "cached"


class TestSpecsRouter:
    """Tests for specs router."""

    def test_specs_without_db(self, client: TestClient) -> None:
        """Specs should return 503 when DB not configured."""
        with patch(DB_CONFIG_PATCH, return_value=False):
            response = client.get("/specs")
            assert response.status_code == 503

    def test_spec_detail_without_db(self, client: TestClient) -> None:
        """Spec detail should return 503 when DB not configured."""
        with patch(DB_CONFIG_PATCH, return_value=False):
            response = client.get("/specs/scatter-basic")
            assert response.status_code == 503

    def test_spec_images_without_db(self, client: TestClient) -> None:
        """Spec images should return 503 when DB not configured."""
        with patch(DB_CONFIG_PATCH, return_value=False):
            response = client.get("/specs/scatter-basic/images")
            assert response.status_code == 503

    def test_specs_with_db(self, client: TestClient, mock_spec) -> None:
        """Specs should return data from DB when configured."""
        mock_spec_repo = MagicMock()
        mock_spec_repo.get_all = AsyncMock(return_value=[mock_spec])

        with (
            patch(DB_CONFIG_PATCH, return_value=True),
            patch("api.routers.specs.get_cache", return_value=None),
            patch("api.routers.specs.set_cache"),
            patch("api.routers.specs.SpecRepository", return_value=mock_spec_repo),
        ):
            response = client.get("/specs")
            assert response.status_code == 200
            data = response.json()
            assert isinstance(data, list)
            assert len(data) == 1
            assert data[0]["id"] == "scatter-basic"

    def test_spec_detail_with_db(self, client: TestClient, mock_spec) -> None:
        """Spec detail should return spec from DB."""
        mock_spec_repo = MagicMock()
        mock_spec_repo.get_by_id = AsyncMock(return_value=mock_spec)

        with (
            patch(DB_CONFIG_PATCH, return_value=True),
            patch("api.routers.specs.get_cache", return_value=None),
            patch("api.routers.specs.set_cache"),
            patch("api.routers.specs.SpecRepository", return_value=mock_spec_repo),
        ):
            response = client.get("/specs/scatter-basic")
            assert response.status_code == 200
            data = response.json()
            assert data["id"] == "scatter-basic"

    def test_spec_detail_not_found(self, client: TestClient) -> None:
        """Spec detail should return 404 when not found."""
        mock_spec_repo = MagicMock()
        mock_spec_repo.get_by_id = AsyncMock(return_value=None)

        with (
            patch(DB_CONFIG_PATCH, return_value=True),
            patch("api.routers.specs.get_cache", return_value=None),
            patch("api.routers.specs.SpecRepository", return_value=mock_spec_repo),
        ):
            response = client.get("/specs/nonexistent")
            assert response.status_code == 404


class TestDownloadRouter:
    """Tests for download router."""

    def test_download_without_db(self, client: TestClient) -> None:
        """Download should return 503 when DB not configured."""
        with patch(DB_CONFIG_PATCH, return_value=False):
            response = client.get("/download/scatter-basic/matplotlib")
            assert response.status_code == 503

    def test_download_spec_not_found(self, client: TestClient) -> None:
        """Download should return 404 when spec not found."""
        mock_spec_repo = MagicMock()
        mock_spec_repo.get_by_id = AsyncMock(return_value=None)

        with (
            patch(DB_CONFIG_PATCH, return_value=True),
            patch("api.routers.download.SpecRepository", return_value=mock_spec_repo),
        ):
            response = client.get("/download/nonexistent/matplotlib")
            assert response.status_code == 404

    def test_download_impl_not_found(self, client: TestClient, mock_spec) -> None:
        """Download should return 404 when implementation not found."""
        mock_spec.impls = []
        mock_spec_repo = MagicMock()
        mock_spec_repo.get_by_id = AsyncMock(return_value=mock_spec)

        with (
            patch(DB_CONFIG_PATCH, return_value=True),
            patch("api.routers.download.SpecRepository", return_value=mock_spec_repo),
        ):
            response = client.get("/download/scatter-basic/seaborn")
            assert response.status_code == 404

    def test_download_success(self, client: TestClient, mock_spec) -> None:
        """Download should return image when spec and impl found."""

        mock_spec_repo = MagicMock()
        mock_spec_repo.get_by_id = AsyncMock(return_value=mock_spec)

        # Mock httpx response
        mock_response = MagicMock()
        mock_response.content = b"fake image content"
        mock_response.raise_for_status = MagicMock()

        mock_httpx_client = AsyncMock()
        mock_httpx_client.get = AsyncMock(return_value=mock_response)
        mock_httpx_client.__aenter__ = AsyncMock(return_value=mock_httpx_client)
        mock_httpx_client.__aexit__ = AsyncMock(return_value=None)

        with (
            patch(DB_CONFIG_PATCH, return_value=True),
            patch("api.routers.download.SpecRepository", return_value=mock_spec_repo),
            patch("api.routers.download.httpx.AsyncClient", return_value=mock_httpx_client),
        ):
            response = client.get("/download/scatter-basic/matplotlib")
            assert response.status_code == 200
            assert response.headers["content-type"] == "image/png"
            assert "attachment" in response.headers["content-disposition"]
            assert response.content == b"fake image content"

    def test_download_gcs_error(self, client: TestClient, mock_spec) -> None:
        """Download should return 502 when GCS fetch fails."""
        import httpx

        mock_spec_repo = MagicMock()
        mock_spec_repo.get_by_id = AsyncMock(return_value=mock_spec)

        mock_httpx_client = AsyncMock()
        mock_httpx_client.get = AsyncMock(side_effect=httpx.HTTPError("GCS error"))
        mock_httpx_client.__aenter__ = AsyncMock(return_value=mock_httpx_client)
        mock_httpx_client.__aexit__ = AsyncMock(return_value=None)

        with (
            patch(DB_CONFIG_PATCH, return_value=True),
            patch("api.routers.download.SpecRepository", return_value=mock_spec_repo),
            patch("api.routers.download.httpx.AsyncClient", return_value=mock_httpx_client),
        ):
            response = client.get("/download/scatter-basic/matplotlib")
            assert response.status_code == 502


class TestSeoRouter:
    """Tests for SEO router."""

    def test_robots_txt(self, client: TestClient) -> None:
        """robots.txt should block crawlers from all routes."""
        response = client.get("/robots.txt")
        assert response.status_code == 200
        assert response.headers["content-type"] == "text/plain; charset=utf-8"
        content = response.text
        assert "User-agent: *" in content
        assert "Disallow: /" in content

    def test_sitemap_structure(self, client: TestClient) -> None:
        """Sitemap should return valid XML structure."""
        with patch(DB_CONFIG_PATCH, return_value=False):
            response = client.get("/sitemap.xml")
            assert response.status_code == 200
            assert response.headers["content-type"] == "application/xml"
            content = response.text
            assert '<?xml version="1.0"' in content
            assert "<urlset" in content
            # Check for homepage URL as proper XML element
            assert "<loc>https://pyplots.ai/</loc>" in content

    def test_sitemap_with_db(self, db_client, mock_spec) -> None:
        """Sitemap should include specs and implementations from DB."""
        client, _ = db_client

        mock_spec_repo = MagicMock()
        mock_spec_repo.get_all = AsyncMock(return_value=[mock_spec])

        with (
            patch("api.routers.seo.get_cache", return_value=None),
            patch("api.routers.seo.set_cache"),
            patch("api.routers.seo.SpecRepository", return_value=mock_spec_repo),
        ):
            response = client.get("/sitemap.xml")
            assert response.status_code == 200
            # URL format: /, /catalog, /{spec_id}, /{spec_id}/{library_id}
            assert "https://pyplots.ai/catalog" in response.text
            # Overview page
            assert "https://pyplots.ai/scatter-basic</loc>" in response.text
            # Implementation page
            assert "https://pyplots.ai/scatter-basic/matplotlib</loc>" in response.text


class TestSeoProxyRouter:
    """Tests for SEO proxy endpoints (bot-optimized pages)."""

    def test_seo_home(self, client: TestClient) -> None:
        """SEO home page should return HTML with og:tags."""
        response = client.get("/seo-proxy/")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
        assert "og:title" in response.text
        assert "pyplots.ai" in response.text
        assert "og:image" in response.text
        assert "twitter:card" in response.text

    def test_seo_catalog(self, client: TestClient) -> None:
        """SEO catalog page should return HTML with og:tags."""
        response = client.get("/seo-proxy/catalog")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
        assert "Catalog" in response.text
        assert "og:title" in response.text
        assert "https://pyplots.ai/catalog" in response.text

    def test_seo_spec_overview_without_db(self, client: TestClient) -> None:
        """SEO spec overview should return fallback HTML when DB unavailable."""
        with patch(DB_CONFIG_PATCH, return_value=False):
            response = client.get("/seo-proxy/scatter-basic")
            assert response.status_code == 200
            assert "og:title" in response.text
            assert "scatter-basic" in response.text
            assert "api.pyplots.ai/og/home.png" in response.text  # Default image via API

    def test_seo_spec_overview_with_db(self, db_client, mock_spec) -> None:
        """SEO spec overview should return HTML with spec title from DB."""
        client, _ = db_client

        mock_spec_repo = MagicMock()
        mock_spec_repo.get_by_id = AsyncMock(return_value=mock_spec)

        with patch("api.routers.seo.SpecRepository", return_value=mock_spec_repo):
            response = client.get("/seo-proxy/scatter-basic")
            assert response.status_code == 200
            assert "Basic Scatter Plot" in response.text
            assert "og:title" in response.text
            assert "https://pyplots.ai/scatter-basic" in response.text

    def test_seo_spec_overview_not_found(self, db_client) -> None:
        """SEO spec overview should return 404 when spec not found."""
        client, _ = db_client

        mock_spec_repo = MagicMock()
        mock_spec_repo.get_by_id = AsyncMock(return_value=None)

        with patch("api.routers.seo.SpecRepository", return_value=mock_spec_repo):
            response = client.get("/seo-proxy/nonexistent-spec")
            assert response.status_code == 404

    def test_seo_spec_implementation_without_db(self, client: TestClient) -> None:
        """SEO spec implementation should return fallback HTML when DB unavailable."""
        with patch(DB_CONFIG_PATCH, return_value=False):
            response = client.get("/seo-proxy/scatter-basic/matplotlib")
            assert response.status_code == 200
            assert "og:title" in response.text
            assert "scatter-basic" in response.text
            assert "matplotlib" in response.text
            assert "api.pyplots.ai/og/home.png" in response.text  # Default image via API

    def test_seo_spec_implementation_with_preview_url(self, db_client, mock_spec) -> None:
        """SEO spec implementation should use preview_url from implementation."""
        client, _ = db_client

        mock_spec_repo = MagicMock()
        mock_spec_repo.get_by_id = AsyncMock(return_value=mock_spec)

        with patch("api.routers.seo.SpecRepository", return_value=mock_spec_repo):
            response = client.get("/seo-proxy/scatter-basic/matplotlib")
            assert response.status_code == 200
            assert "Basic Scatter Plot" in response.text
            assert "matplotlib" in response.text
            # Should have actual preview URL from implementation
            assert TEST_IMAGE_URL in response.text or "og:image" in response.text

    def test_seo_spec_implementation_not_found(self, db_client) -> None:
        """SEO spec implementation should return 404 when spec not found."""
        client, _ = db_client

        mock_spec_repo = MagicMock()
        mock_spec_repo.get_by_id = AsyncMock(return_value=None)

        with patch("api.routers.seo.SpecRepository", return_value=mock_spec_repo):
            response = client.get("/seo-proxy/nonexistent-spec/matplotlib")
            assert response.status_code == 404

    def test_seo_spec_implementation_fallback_image(self, db_client, mock_spec) -> None:
        """SEO spec implementation should use default image when impl has no preview."""
        client, _ = db_client

        # Create a spec with implementation that has no preview_url
        mock_impl_no_preview = MagicMock()
        mock_impl_no_preview.library_id = "seaborn"
        mock_impl_no_preview.preview_url = None

        mock_spec_no_preview = MagicMock()
        mock_spec_no_preview.id = "scatter-basic"
        mock_spec_no_preview.title = "Basic Scatter Plot"
        mock_spec_no_preview.description = "A basic scatter plot"
        mock_spec_no_preview.impls = [mock_impl_no_preview]

        mock_spec_repo = MagicMock()
        mock_spec_repo.get_by_id = AsyncMock(return_value=mock_spec_no_preview)

        with patch("api.routers.seo.SpecRepository", return_value=mock_spec_repo):
            response = client.get("/seo-proxy/scatter-basic/seaborn")
            assert response.status_code == 200
            assert "api.pyplots.ai/og/home.png" in response.text  # Default image via API


class TestOgImagesRouter:
    """Tests for OG image generation endpoints."""

    def test_get_home_og_image(self, client: TestClient) -> None:
        """Should return static og:image for home page."""
        with patch("api.routers.og_images.track_og_image"):
            with patch("api.routers.og_images._get_static_og_image", return_value=b"fake-image"):
                response = client.get("/og/home.png")
                assert response.status_code == 200
                assert response.headers["content-type"] == "image/png"
                assert "max-age=86400" in response.headers["cache-control"]

    def test_get_home_og_image_with_filters(self, client: TestClient) -> None:
        """Should pass filter params to tracking."""
        with patch("api.routers.og_images.track_og_image") as mock_track:
            with patch("api.routers.og_images._get_static_og_image", return_value=b"fake-image"):
                response = client.get("/og/home.png?lib=plotly&dom=statistics")
                assert response.status_code == 200
                mock_track.assert_called_once()
                call_kwargs = mock_track.call_args[1]
                assert call_kwargs["page"] == "home"
                assert call_kwargs["filters"] == {"lib": "plotly", "dom": "statistics"}

    def test_get_catalog_og_image(self, client: TestClient) -> None:
        """Should return static og:image for catalog page."""
        with patch("api.routers.og_images.track_og_image") as mock_track:
            with patch("api.routers.og_images._get_static_og_image", return_value=b"fake-image"):
                response = client.get("/og/catalog.png")
                assert response.status_code == 200
                assert response.headers["content-type"] == "image/png"
                mock_track.assert_called_once()
                call_kwargs = mock_track.call_args[1]
                assert call_kwargs["page"] == "catalog"

    def test_get_static_og_image_file_not_found(self, client: TestClient) -> None:
        """Should return 500 when static image file not found."""
        import api.routers.og_images as og_module

        # Reset cached image
        og_module._STATIC_OG_IMAGE = None

        with patch("api.routers.og_images.track_og_image"):
            with patch("pathlib.Path.read_bytes", side_effect=FileNotFoundError("not found")):
                response = client.get("/og/home.png")
                assert response.status_code == 500

        # Reset for other tests
        og_module._STATIC_OG_IMAGE = None

    def test_get_branded_impl_image_no_db(self, client: TestClient) -> None:
        """Should return 503 when DB not available."""
        with patch(DB_CONFIG_PATCH, return_value=False):
            response = client.get("/og/scatter-basic/matplotlib.png")
            assert response.status_code == 503

    def test_get_branded_impl_image_spec_not_found(self, db_client) -> None:
        """Should return 404 when spec not found."""
        client, _ = db_client

        mock_spec_repo = MagicMock()
        mock_spec_repo.get_by_id = AsyncMock(return_value=None)

        with patch("api.routers.og_images.SpecRepository", return_value=mock_spec_repo):
            response = client.get("/og/nonexistent/matplotlib.png")
            assert response.status_code == 404

    def test_get_branded_impl_image_impl_not_found(self, db_client, mock_spec) -> None:
        """Should return 404 when implementation not found."""
        client, _ = db_client

        mock_spec_repo = MagicMock()
        mock_spec_repo.get_by_id = AsyncMock(return_value=mock_spec)

        with patch("api.routers.og_images.SpecRepository", return_value=mock_spec_repo):
            # Request a library that doesn't exist in mock_spec
            response = client.get("/og/scatter-basic/nonexistent.png")
            assert response.status_code == 404

    def test_get_branded_impl_image_cached(self, db_client) -> None:
        """Should return cached image when available."""
        client, _ = db_client

        cached_bytes = b"fake png data"
        with patch("api.routers.og_images.get_cache", return_value=cached_bytes):
            response = client.get("/og/scatter-basic/matplotlib.png")
            assert response.status_code == 200
            assert response.headers["content-type"] == "image/png"
            assert response.content == cached_bytes

    def test_get_spec_collage_no_db(self, client: TestClient) -> None:
        """Should return 503 when DB not available."""
        with patch(DB_CONFIG_PATCH, return_value=False):
            response = client.get("/og/scatter-basic.png")
            assert response.status_code == 503

    def test_get_spec_collage_spec_not_found(self, db_client) -> None:
        """Should return 404 when spec not found."""
        client, _ = db_client

        mock_spec_repo = MagicMock()
        mock_spec_repo.get_by_id = AsyncMock(return_value=None)

        with patch("api.routers.og_images.SpecRepository", return_value=mock_spec_repo):
            response = client.get("/og/nonexistent.png")
            assert response.status_code == 404

    def test_get_spec_collage_no_previews(self, db_client) -> None:
        """Should return 404 when no implementations have previews."""
        client, _ = db_client

        mock_impl = MagicMock()
        mock_impl.library_id = "matplotlib"
        mock_impl.preview_url = None  # No preview

        mock_spec = MagicMock()
        mock_spec.id = "scatter-basic"
        mock_spec.impls = [mock_impl]

        mock_spec_repo = MagicMock()
        mock_spec_repo.get_by_id = AsyncMock(return_value=mock_spec)

        with patch("api.routers.og_images.SpecRepository", return_value=mock_spec_repo):
            response = client.get("/og/scatter-basic.png")
            assert response.status_code == 404

    def test_get_spec_collage_cached(self, db_client) -> None:
        """Should return cached collage when available."""
        client, _ = db_client

        cached_bytes = b"fake collage png data"
        with patch("api.routers.og_images.get_cache", return_value=cached_bytes):
            response = client.get("/og/scatter-basic.png")
            assert response.status_code == 200
            assert response.headers["content-type"] == "image/png"
            assert response.content == cached_bytes

    def test_get_branded_impl_image_success(self, db_client, mock_spec) -> None:
        """Should generate branded image when not cached."""
        client, _ = db_client

        fake_image_bytes = b"fake source image"
        fake_branded_bytes = b"fake branded png"

        mock_spec_repo = MagicMock()
        mock_spec_repo.get_by_id = AsyncMock(return_value=mock_spec)

        with (
            patch("api.routers.og_images.get_cache", return_value=None),
            patch("api.routers.og_images.set_cache"),
            patch("api.routers.og_images.SpecRepository", return_value=mock_spec_repo),
            patch("api.routers.og_images._fetch_image", new_callable=AsyncMock, return_value=fake_image_bytes),
            patch("api.routers.og_images.create_branded_og_image", return_value=fake_branded_bytes),
        ):
            response = client.get("/og/scatter-basic/matplotlib.png")
            assert response.status_code == 200
            assert response.headers["content-type"] == "image/png"
            assert response.headers["cache-control"] == "public, max-age=3600"
            assert response.content == fake_branded_bytes

    def test_get_spec_collage_success(self, db_client) -> None:
        """Should generate collage when not cached."""
        client, _ = db_client

        # Create mock implementations with different quality scores
        mock_impls = []
        for i, lib in enumerate(["matplotlib", "seaborn", "plotly"]):
            impl = MagicMock()
            impl.library_id = lib
            impl.preview_url = f"https://example.com/{lib}.png"
            impl.quality_score = 90 - i * 5  # 90, 85, 80
            mock_impls.append(impl)

        mock_spec = MagicMock()
        mock_spec.id = "scatter-basic"
        mock_spec.impls = mock_impls

        mock_spec_repo = MagicMock()
        mock_spec_repo.get_by_id = AsyncMock(return_value=mock_spec)

        fake_collage_bytes = b"fake collage png"

        with (
            patch("api.routers.og_images.get_cache", return_value=None),
            patch("api.routers.og_images.set_cache"),
            patch("api.routers.og_images.SpecRepository", return_value=mock_spec_repo),
            patch("api.routers.og_images._fetch_image", new_callable=AsyncMock, return_value=b"fake image"),
            patch("api.routers.og_images.create_og_collage", return_value=fake_collage_bytes),
        ):
            response = client.get("/og/scatter-basic.png")
            assert response.status_code == 200
            assert response.headers["content-type"] == "image/png"
            assert response.headers["cache-control"] == "public, max-age=3600"
            assert response.content == fake_collage_bytes

    def test_get_branded_impl_image_cached_has_cache_control(self, db_client) -> None:
        """Cached response should include Cache-Control header."""
        client, _ = db_client

        cached_bytes = b"fake png data"
        with patch("api.routers.og_images.get_cache", return_value=cached_bytes):
            response = client.get("/og/scatter-basic/matplotlib.png")
            assert response.status_code == 200
            assert response.headers["cache-control"] == "public, max-age=3600"

    def test_get_spec_collage_cached_has_cache_control(self, db_client) -> None:
        """Cached collage response should include Cache-Control header."""
        client, _ = db_client

        cached_bytes = b"fake collage png data"
        with patch("api.routers.og_images.get_cache", return_value=cached_bytes):
            response = client.get("/og/scatter-basic.png")
            assert response.status_code == 200
            assert response.headers["cache-control"] == "public, max-age=3600"


class TestPlotsRouter:
    """Tests for plots filter router."""

    def test_filter_without_db(self, client: TestClient) -> None:
        """Filter should return 503 when DB not configured."""
        with patch(DB_CONFIG_PATCH, return_value=False):
            response = client.get("/plots/filter")
            assert response.status_code == 503

    def test_filter_with_params_without_db(self, client: TestClient) -> None:
        """Filter with params should return 503 when DB not configured."""
        with patch(DB_CONFIG_PATCH, return_value=False):
            response = client.get("/plots/filter?lib=matplotlib")
            assert response.status_code == 503

    def test_filter_with_db(self, client: TestClient, mock_spec) -> None:
        """Filter should return images from DB."""
        mock_spec_repo = MagicMock()
        mock_spec_repo.get_all = AsyncMock(return_value=[mock_spec])

        with (
            patch(DB_CONFIG_PATCH, return_value=True),
            patch("api.routers.plots.get_cache", return_value=None),
            patch("api.routers.plots.set_cache"),
            patch("api.routers.plots.SpecRepository", return_value=mock_spec_repo),
        ):
            response = client.get("/plots/filter")
            assert response.status_code == 200
            data = response.json()
            assert "images" in data
            assert "counts" in data
            assert data["total"] == 1

    def test_filter_with_lib_param(self, client: TestClient, mock_spec) -> None:
        """Filter with lib param should filter by library."""
        mock_spec_repo = MagicMock()
        mock_spec_repo.get_all = AsyncMock(return_value=[mock_spec])

        with (
            patch(DB_CONFIG_PATCH, return_value=True),
            patch("api.routers.plots.get_cache", return_value=None),
            patch("api.routers.plots.set_cache"),
            patch("api.routers.plots.SpecRepository", return_value=mock_spec_repo),
        ):
            response = client.get("/plots/filter?lib=matplotlib")
            assert response.status_code == 200
            data = response.json()
            assert data["total"] == 1

    def test_filter_cached(self, client: TestClient) -> None:
        """Filter should return cached response when available."""
        cached_response = MagicMock()
        cached_response.total = 5
        cached_response.images = []
        cached_response.counts = {}
        cached_response.globalCounts = {}
        cached_response.orCounts = []
        cached_response.specTitles = {}
        cached_response.offset = 0
        cached_response.limit = None

        with (
            patch(DB_CONFIG_PATCH, return_value=True),
            patch("api.routers.plots.get_cache", return_value=cached_response),
        ):
            response = client.get("/plots/filter")
            assert response.status_code == 200

    def test_filter_with_limit(self, client: TestClient, mock_spec) -> None:
        """Filter with limit should return limited images but total of all."""
        # Add a second impl to have 2 images
        mock_impl2 = MagicMock()
        mock_impl2.library_id = "seaborn"
        mock_impl2.preview_url = TEST_IMAGE_URL
        mock_impl2.preview_thumb = TEST_THUMB_URL
        mock_impl2.preview_html = None
        mock_impl2.quality_score = 85.0
        mock_impl2.impl_tags = {}
        mock_spec.impls.append(mock_impl2)

        mock_spec_repo = MagicMock()
        mock_spec_repo.get_all = AsyncMock(return_value=[mock_spec])

        with (
            patch(DB_CONFIG_PATCH, return_value=True),
            patch("api.routers.plots.get_cache", return_value=None),
            patch("api.routers.plots.set_cache"),
            patch("api.routers.plots.SpecRepository", return_value=mock_spec_repo),
        ):
            response = client.get("/plots/filter?limit=1")
            assert response.status_code == 200
            data = response.json()
            assert len(data["images"]) == 1
            assert data["total"] == 2
            assert data["limit"] == 1
            assert data["offset"] == 0

    def test_filter_with_offset(self, client: TestClient, mock_spec) -> None:
        """Filter with offset should skip images."""
        mock_impl2 = MagicMock()
        mock_impl2.library_id = "seaborn"
        mock_impl2.preview_url = TEST_IMAGE_URL
        mock_impl2.preview_thumb = TEST_THUMB_URL
        mock_impl2.preview_html = None
        mock_impl2.quality_score = 85.0
        mock_impl2.impl_tags = {}
        mock_spec.impls.append(mock_impl2)

        mock_spec_repo = MagicMock()
        mock_spec_repo.get_all = AsyncMock(return_value=[mock_spec])

        with (
            patch(DB_CONFIG_PATCH, return_value=True),
            patch("api.routers.plots.get_cache", return_value=None),
            patch("api.routers.plots.set_cache"),
            patch("api.routers.plots.SpecRepository", return_value=mock_spec_repo),
        ):
            response = client.get("/plots/filter?offset=1")
            assert response.status_code == 200
            data = response.json()
            assert len(data["images"]) == 1
            assert data["total"] == 2
            assert data["offset"] == 1

    def test_filter_with_limit_and_offset(self, client: TestClient, mock_spec) -> None:
        """Filter with limit and offset combined."""
        mock_impl2 = MagicMock()
        mock_impl2.library_id = "seaborn"
        mock_impl2.preview_url = TEST_IMAGE_URL
        mock_impl2.preview_thumb = TEST_THUMB_URL
        mock_impl2.preview_html = None
        mock_impl2.quality_score = 85.0
        mock_impl2.impl_tags = {}
        mock_impl3 = MagicMock()
        mock_impl3.library_id = "plotly"
        mock_impl3.preview_url = TEST_IMAGE_URL
        mock_impl3.preview_thumb = TEST_THUMB_URL
        mock_impl3.preview_html = None
        mock_impl3.quality_score = 80.0
        mock_impl3.impl_tags = {}
        mock_spec.impls.extend([mock_impl2, mock_impl3])

        mock_spec_repo = MagicMock()
        mock_spec_repo.get_all = AsyncMock(return_value=[mock_spec])

        with (
            patch(DB_CONFIG_PATCH, return_value=True),
            patch("api.routers.plots.get_cache", return_value=None),
            patch("api.routers.plots.set_cache"),
            patch("api.routers.plots.SpecRepository", return_value=mock_spec_repo),
        ):
            response = client.get("/plots/filter?offset=1&limit=1")
            assert response.status_code == 200
            data = response.json()
            assert len(data["images"]) == 1
            assert data["total"] == 3
            assert data["offset"] == 1
            assert data["limit"] == 1

    def test_filter_default_returns_all(self, client: TestClient, mock_spec) -> None:
        """Filter without pagination params returns all images (backward compat)."""
        mock_spec_repo = MagicMock()
        mock_spec_repo.get_all = AsyncMock(return_value=[mock_spec])

        with (
            patch(DB_CONFIG_PATCH, return_value=True),
            patch("api.routers.plots.get_cache", return_value=None),
            patch("api.routers.plots.set_cache"),
            patch("api.routers.plots.SpecRepository", return_value=mock_spec_repo),
        ):
            response = client.get("/plots/filter")
            assert response.status_code == 200
            data = response.json()
            assert len(data["images"]) == data["total"]
            assert data["offset"] == 0
            assert data["limit"] is None


class TestPlotsHelperFunctions:
    """Tests for plots.py helper functions."""

    def test_image_matches_groups_empty(self) -> None:
        """Empty groups should match any image."""
        spec_lookup = {"scatter-basic": {"tags": {"plot_type": ["scatter"]}}}
        assert _image_matches_groups("scatter-basic", "matplotlib", [], spec_lookup, {}) is True

    def test_image_matches_groups_lib_match(self) -> None:
        """Library filter should match correct library."""
        spec_lookup = {"scatter-basic": {"tags": {}}}
        groups = [{"category": "lib", "values": ["matplotlib"]}]
        assert _image_matches_groups("scatter-basic", "matplotlib", groups, spec_lookup, {}) is True

    def test_image_matches_groups_lib_no_match(self) -> None:
        """Library filter should not match wrong library."""
        spec_lookup = {"scatter-basic": {"tags": {}}}
        groups = [{"category": "lib", "values": ["seaborn"]}]
        assert _image_matches_groups("scatter-basic", "matplotlib", groups, spec_lookup, {}) is False

    def test_image_matches_groups_spec_match(self) -> None:
        """Spec filter should match correct spec."""
        spec_lookup = {"scatter-basic": {"tags": {}}}
        groups = [{"category": "spec", "values": ["scatter-basic"]}]
        assert _image_matches_groups("scatter-basic", "matplotlib", groups, spec_lookup, {}) is True

    def test_image_matches_groups_plot_type_match(self) -> None:
        """Plot type filter should match correct tag."""
        spec_lookup = {"scatter-basic": {"tags": {"plot_type": ["scatter"]}}}
        groups = [{"category": "plot", "values": ["scatter"]}]
        assert _image_matches_groups("scatter-basic", "matplotlib", groups, spec_lookup, {}) is True

    def test_image_matches_groups_data_type_match(self) -> None:
        """Data type filter should match correct tag."""
        spec_lookup = {"scatter-basic": {"tags": {"data_type": ["numeric"]}}}
        groups = [{"category": "data", "values": ["numeric"]}]
        assert _image_matches_groups("scatter-basic", "matplotlib", groups, spec_lookup, {}) is True

    def test_image_matches_groups_domain_match(self) -> None:
        """Domain filter should match correct tag."""
        spec_lookup = {"scatter-basic": {"tags": {"domain": ["statistics"]}}}
        groups = [{"category": "dom", "values": ["statistics"]}]
        assert _image_matches_groups("scatter-basic", "matplotlib", groups, spec_lookup, {}) is True

    def test_image_matches_groups_features_match(self) -> None:
        """Features filter should match correct tag."""
        spec_lookup = {"scatter-basic": {"tags": {"features": ["basic"]}}}
        groups = [{"category": "feat", "values": ["basic"]}]
        assert _image_matches_groups("scatter-basic", "matplotlib", groups, spec_lookup, {}) is True

    def test_image_matches_groups_spec_not_in_lookup(self) -> None:
        """Spec not in lookup should not match."""
        spec_lookup = {}
        assert _image_matches_groups("unknown", "matplotlib", [], spec_lookup, {}) is False

    def test_image_matches_groups_dep_match(self) -> None:
        """Dependencies filter should match impl_tags."""
        spec_lookup = {"scatter-basic": {"tags": {}}}
        impl_lookup = {("scatter-basic", "matplotlib"): {"dependencies": ["scipy", "sklearn"]}}
        groups = [{"category": "dep", "values": ["scipy"]}]
        assert _image_matches_groups("scatter-basic", "matplotlib", groups, spec_lookup, impl_lookup) is True

    def test_image_matches_groups_dep_no_match(self) -> None:
        """Dependencies filter should not match if not in impl_tags."""
        spec_lookup = {"scatter-basic": {"tags": {}}}
        impl_lookup = {("scatter-basic", "matplotlib"): {"dependencies": ["scipy"]}}
        groups = [{"category": "dep", "values": ["networkx"]}]
        assert _image_matches_groups("scatter-basic", "matplotlib", groups, spec_lookup, impl_lookup) is False

    def test_image_matches_groups_tech_match(self) -> None:
        """Techniques filter should match impl_tags."""
        spec_lookup = {"scatter-basic": {"tags": {}}}
        impl_lookup = {("scatter-basic", "matplotlib"): {"techniques": ["annotations", "colorbar"]}}
        groups = [{"category": "tech", "values": ["annotations"]}]
        assert _image_matches_groups("scatter-basic", "matplotlib", groups, spec_lookup, impl_lookup) is True

    def test_image_matches_groups_pat_match(self) -> None:
        """Patterns filter should match impl_tags."""
        spec_lookup = {"scatter-basic": {"tags": {}}}
        impl_lookup = {("scatter-basic", "matplotlib"): {"patterns": ["data-generation", "iteration-over-groups"]}}
        groups = [{"category": "pat", "values": ["data-generation"]}]
        assert _image_matches_groups("scatter-basic", "matplotlib", groups, spec_lookup, impl_lookup) is True

    def test_image_matches_groups_prep_match(self) -> None:
        """Dataprep filter should match impl_tags."""
        spec_lookup = {"scatter-basic": {"tags": {}}}
        impl_lookup = {("scatter-basic", "matplotlib"): {"dataprep": ["kde", "binning"]}}
        groups = [{"category": "prep", "values": ["kde"]}]
        assert _image_matches_groups("scatter-basic", "matplotlib", groups, spec_lookup, impl_lookup) is True

    def test_image_matches_groups_style_match(self) -> None:
        """Styling filter should match impl_tags."""
        spec_lookup = {"scatter-basic": {"tags": {}}}
        impl_lookup = {("scatter-basic", "matplotlib"): {"styling": ["alpha-blending", "minimal-chrome"]}}
        groups = [{"category": "style", "values": ["alpha-blending"]}]
        assert _image_matches_groups("scatter-basic", "matplotlib", groups, spec_lookup, impl_lookup) is True

    def test_image_matches_groups_impl_not_in_lookup(self) -> None:
        """Impl not in lookup should not match impl-level filters."""
        spec_lookup = {"scatter-basic": {"tags": {}}}
        impl_lookup = {}  # Empty - no impl data
        groups = [{"category": "dep", "values": ["scipy"]}]
        assert _image_matches_groups("scatter-basic", "matplotlib", groups, spec_lookup, impl_lookup) is False

    def test_calculate_global_counts(self) -> None:
        """Global counts should tally all implementations."""
        mock_impl = MagicMock()
        mock_impl.library_id = "matplotlib"
        mock_impl.preview_url = TEST_IMAGE_URL

        mock_spec = MagicMock()
        mock_spec.id = "scatter-basic"
        mock_spec.tags = {"plot_type": ["scatter"], "domain": ["statistics"]}
        mock_spec.impls = [mock_impl]

        counts = _calculate_global_counts([mock_spec])
        assert counts["lib"]["matplotlib"] == 1
        assert counts["spec"]["scatter-basic"] == 1
        assert counts["plot"]["scatter"] == 1
        assert counts["dom"]["statistics"] == 1

    def test_calculate_global_counts_with_impl_tags(self) -> None:
        """Global counts should include impl-level tags."""
        mock_impl = MagicMock()
        mock_impl.library_id = "matplotlib"
        mock_impl.preview_url = TEST_IMAGE_URL
        mock_impl.impl_tags = {
            "dependencies": ["scipy", "sklearn"],
            "techniques": ["annotations"],
            "patterns": ["data-generation"],
            "dataprep": ["kde"],
            "styling": ["alpha-blending"],
        }

        mock_spec = MagicMock()
        mock_spec.id = "scatter-basic"
        mock_spec.tags = {"plot_type": ["scatter"]}
        mock_spec.impls = [mock_impl]

        counts = _calculate_global_counts([mock_spec])
        # Spec-level counts
        assert counts["lib"]["matplotlib"] == 1
        assert counts["plot"]["scatter"] == 1
        # Impl-level counts
        assert counts["dep"]["scipy"] == 1
        assert counts["dep"]["sklearn"] == 1
        assert counts["tech"]["annotations"] == 1
        assert counts["pat"]["data-generation"] == 1
        assert counts["prep"]["kde"] == 1
        assert counts["style"]["alpha-blending"] == 1

    def test_calculate_global_counts_no_impls(self) -> None:
        """Spec without impls should not be counted."""
        mock_spec = MagicMock()
        mock_spec.id = "scatter-basic"
        mock_spec.impls = []

        counts = _calculate_global_counts([mock_spec])
        assert counts["lib"] == {}

    def test_calculate_global_counts_no_preview(self) -> None:
        """Impl without preview_url should not be counted."""
        mock_impl = MagicMock()
        mock_impl.library_id = "matplotlib"
        mock_impl.preview_url = None

        mock_spec = MagicMock()
        mock_spec.id = "scatter-basic"
        mock_spec.tags = {}
        mock_spec.impls = [mock_impl]

        counts = _calculate_global_counts([mock_spec])
        assert counts["lib"] == {}

    def test_calculate_contextual_counts(self) -> None:
        """Contextual counts should tally filtered images."""
        images = [
            {"spec_id": "scatter-basic", "library": "matplotlib"},
            {"spec_id": "scatter-basic", "library": "seaborn"},
        ]
        spec_tags = {"scatter-basic": {"plot_type": ["scatter"]}}
        impl_lookup = {}  # Empty impl_lookup for this test

        counts = _calculate_contextual_counts(images, spec_tags, impl_lookup)
        assert counts["lib"]["matplotlib"] == 1
        assert counts["lib"]["seaborn"] == 1
        assert counts["spec"]["scatter-basic"] == 2
        assert counts["plot"]["scatter"] == 2

    def test_calculate_contextual_counts_with_impl_tags(self) -> None:
        """Contextual counts should include impl-level tags."""
        images = [
            {"spec_id": "scatter-basic", "library": "matplotlib"},
            {"spec_id": "scatter-basic", "library": "seaborn"},
        ]
        spec_tags = {"scatter-basic": {"plot_type": ["scatter"]}}
        impl_lookup = {
            ("scatter-basic", "matplotlib"): {
                "dependencies": ["scipy"],
                "techniques": ["annotations"],
                "patterns": ["data-generation"],
                "dataprep": ["kde"],
                "styling": ["alpha-blending"],
            },
            ("scatter-basic", "seaborn"): {
                "dependencies": ["scipy", "sklearn"],
                "techniques": ["colorbar"],
                "patterns": ["data-generation"],
                "dataprep": [],
                "styling": [],
            },
        }

        counts = _calculate_contextual_counts(images, spec_tags, impl_lookup)
        # Spec-level counts
        assert counts["plot"]["scatter"] == 2
        # Impl-level counts
        assert counts["dep"]["scipy"] == 2
        assert counts["dep"]["sklearn"] == 1
        assert counts["tech"]["annotations"] == 1
        assert counts["tech"]["colorbar"] == 1
        assert counts["pat"]["data-generation"] == 2
        assert counts["prep"]["kde"] == 1
        assert counts["style"]["alpha-blending"] == 1

    def test_calculate_or_counts_empty_groups(self) -> None:
        """Empty groups should return empty or_counts."""
        counts = _calculate_or_counts([], [], {}, {}, {})
        assert counts == []

    def test_calculate_or_counts_single_group(self) -> None:
        """Single group should count all matching images."""
        groups = [{"category": "lib", "values": ["matplotlib"]}]
        images = [
            {"spec_id": "scatter-basic", "library": "matplotlib"},
            {"spec_id": "scatter-basic", "library": "seaborn"},
        ]
        spec_lookup = {"scatter-basic": {"tags": {}}}
        spec_tags = {"scatter-basic": {}}
        impl_lookup = {}

        counts = _calculate_or_counts(groups, images, spec_tags, spec_lookup, impl_lookup)
        assert len(counts) == 1
        # Each library appears once across all images
        assert counts[0]["matplotlib"] == 1
        assert counts[0]["seaborn"] == 1

    def test_calculate_or_counts_spec_category(self) -> None:
        """OR counts for spec category."""
        groups = [{"category": "spec", "values": ["scatter-basic"]}]
        images = [{"spec_id": "scatter-basic", "library": "matplotlib"}]
        spec_lookup = {"scatter-basic": {"tags": {}}}
        spec_tags = {"scatter-basic": {}}
        impl_lookup = {}
        counts = _calculate_or_counts(groups, images, spec_tags, spec_lookup, impl_lookup)
        assert counts[0]["scatter-basic"] == 1

    def test_calculate_or_counts_plot_category(self) -> None:
        """OR counts for plot category."""
        groups = [{"category": "plot", "values": ["scatter"]}]
        images = [{"spec_id": "scatter-basic", "library": "matplotlib"}]
        spec_lookup = {"scatter-basic": {"tags": {"plot_type": ["scatter"]}}}
        spec_tags = {"scatter-basic": {"plot_type": ["scatter"]}}
        impl_lookup = {}
        counts = _calculate_or_counts(groups, images, spec_tags, spec_lookup, impl_lookup)
        assert counts[0]["scatter"] == 1

    def test_calculate_or_counts_data_category(self) -> None:
        """OR counts for data category."""
        groups = [{"category": "data", "values": ["numeric"]}]
        images = [{"spec_id": "scatter-basic", "library": "matplotlib"}]
        spec_lookup = {"scatter-basic": {"tags": {"data_type": ["numeric"]}}}
        spec_tags = {"scatter-basic": {"data_type": ["numeric"]}}
        impl_lookup = {}
        counts = _calculate_or_counts(groups, images, spec_tags, spec_lookup, impl_lookup)
        assert counts[0]["numeric"] == 1

    def test_calculate_or_counts_dom_category(self) -> None:
        """OR counts for dom category."""
        groups = [{"category": "dom", "values": ["statistics"]}]
        images = [{"spec_id": "scatter-basic", "library": "matplotlib"}]
        spec_lookup = {"scatter-basic": {"tags": {"domain": ["statistics"]}}}
        spec_tags = {"scatter-basic": {"domain": ["statistics"]}}
        impl_lookup = {}
        counts = _calculate_or_counts(groups, images, spec_tags, spec_lookup, impl_lookup)
        assert counts[0]["statistics"] == 1

    def test_calculate_or_counts_feat_category(self) -> None:
        """OR counts for feat category."""
        groups = [{"category": "feat", "values": ["basic"]}]
        images = [{"spec_id": "scatter-basic", "library": "matplotlib"}]
        spec_lookup = {"scatter-basic": {"tags": {"features": ["basic"]}}}
        spec_tags = {"scatter-basic": {"features": ["basic"]}}
        impl_lookup = {}
        counts = _calculate_or_counts(groups, images, spec_tags, spec_lookup, impl_lookup)
        assert counts[0]["basic"] == 1

    def test_calculate_or_counts_dep_category(self) -> None:
        """OR counts for dep (dependencies) category."""
        groups = [{"category": "dep", "values": ["scipy"]}]
        images = [{"spec_id": "scatter-basic", "library": "matplotlib"}]
        spec_lookup = {"scatter-basic": {"tags": {}}}
        spec_tags = {"scatter-basic": {}}
        impl_lookup = {("scatter-basic", "matplotlib"): {"dependencies": ["scipy", "sklearn"]}}
        counts = _calculate_or_counts(groups, images, spec_tags, spec_lookup, impl_lookup)
        assert counts[0]["scipy"] == 1
        assert counts[0]["sklearn"] == 1

    def test_calculate_or_counts_tech_category(self) -> None:
        """OR counts for tech (techniques) category."""
        groups = [{"category": "tech", "values": ["annotations"]}]
        images = [{"spec_id": "scatter-basic", "library": "matplotlib"}]
        spec_lookup = {"scatter-basic": {"tags": {}}}
        spec_tags = {"scatter-basic": {}}
        impl_lookup = {("scatter-basic", "matplotlib"): {"techniques": ["annotations", "colorbar"]}}
        counts = _calculate_or_counts(groups, images, spec_tags, spec_lookup, impl_lookup)
        assert counts[0]["annotations"] == 1
        assert counts[0]["colorbar"] == 1

    def test_calculate_or_counts_pat_category(self) -> None:
        """OR counts for pat (patterns) category."""
        groups = [{"category": "pat", "values": ["data-generation"]}]
        images = [{"spec_id": "scatter-basic", "library": "matplotlib"}]
        spec_lookup = {"scatter-basic": {"tags": {}}}
        spec_tags = {"scatter-basic": {}}
        impl_lookup = {("scatter-basic", "matplotlib"): {"patterns": ["data-generation"]}}
        counts = _calculate_or_counts(groups, images, spec_tags, spec_lookup, impl_lookup)
        assert counts[0]["data-generation"] == 1

    def test_calculate_or_counts_prep_category(self) -> None:
        """OR counts for prep (dataprep) category."""
        groups = [{"category": "prep", "values": ["kde"]}]
        images = [{"spec_id": "scatter-basic", "library": "matplotlib"}]
        spec_lookup = {"scatter-basic": {"tags": {}}}
        spec_tags = {"scatter-basic": {}}
        impl_lookup = {("scatter-basic", "matplotlib"): {"dataprep": ["kde", "binning"]}}
        counts = _calculate_or_counts(groups, images, spec_tags, spec_lookup, impl_lookup)
        assert counts[0]["kde"] == 1
        assert counts[0]["binning"] == 1

    def test_calculate_or_counts_style_category(self) -> None:
        """OR counts for style (styling) category."""
        groups = [{"category": "style", "values": ["alpha-blending"]}]
        images = [{"spec_id": "scatter-basic", "library": "matplotlib"}]
        spec_lookup = {"scatter-basic": {"tags": {}}}
        spec_tags = {"scatter-basic": {}}
        impl_lookup = {("scatter-basic", "matplotlib"): {"styling": ["alpha-blending"]}}
        counts = _calculate_or_counts(groups, images, spec_tags, spec_lookup, impl_lookup)
        assert counts[0]["alpha-blending"] == 1

    def test_image_matches_groups_spec_no_match(self) -> None:
        """Spec filter should not match wrong spec_id."""
        spec_lookup = {"scatter-basic": {"tags": {}}}
        groups = [{"category": "spec", "values": ["bar-basic"]}]
        assert _image_matches_groups("scatter-basic", "matplotlib", groups, spec_lookup, {}) is False

    def test_image_matches_groups_plot_no_match(self) -> None:
        """Plot type filter should not match wrong type."""
        spec_lookup = {"scatter-basic": {"tags": {"plot_type": ["scatter"]}}}
        groups = [{"category": "plot", "values": ["bar"]}]
        assert _image_matches_groups("scatter-basic", "matplotlib", groups, spec_lookup, {}) is False

    def test_image_matches_groups_data_no_match(self) -> None:
        """Data type filter should not match wrong type."""
        spec_lookup = {"scatter-basic": {"tags": {"data_type": ["numeric"]}}}
        groups = [{"category": "data", "values": ["categorical"]}]
        assert _image_matches_groups("scatter-basic", "matplotlib", groups, spec_lookup, {}) is False

    def test_image_matches_groups_dom_no_match(self) -> None:
        """Domain filter should not match wrong domain."""
        spec_lookup = {"scatter-basic": {"tags": {"domain": ["statistics"]}}}
        groups = [{"category": "dom", "values": ["finance"]}]
        assert _image_matches_groups("scatter-basic", "matplotlib", groups, spec_lookup, {}) is False

    def test_image_matches_groups_feat_no_match(self) -> None:
        """Features filter should not match wrong feature."""
        spec_lookup = {"scatter-basic": {"tags": {"features": ["basic"]}}}
        groups = [{"category": "feat", "values": ["advanced"]}]
        assert _image_matches_groups("scatter-basic", "matplotlib", groups, spec_lookup, {}) is False

    def test_image_matches_groups_tech_no_match(self) -> None:
        """Techniques filter should not match if not in impl_tags."""
        spec_lookup = {"scatter-basic": {"tags": {}}}
        impl_lookup = {("scatter-basic", "matplotlib"): {"techniques": ["annotations"]}}
        groups = [{"category": "tech", "values": ["colorbar"]}]
        assert _image_matches_groups("scatter-basic", "matplotlib", groups, spec_lookup, impl_lookup) is False

    def test_image_matches_groups_pat_no_match(self) -> None:
        """Patterns filter should not match if not in impl_tags."""
        spec_lookup = {"scatter-basic": {"tags": {}}}
        impl_lookup = {("scatter-basic", "matplotlib"): {"patterns": ["data-generation"]}}
        groups = [{"category": "pat", "values": ["iteration-over-groups"]}]
        assert _image_matches_groups("scatter-basic", "matplotlib", groups, spec_lookup, impl_lookup) is False

    def test_image_matches_groups_prep_no_match(self) -> None:
        """Dataprep filter should not match if not in impl_tags."""
        spec_lookup = {"scatter-basic": {"tags": {}}}
        impl_lookup = {("scatter-basic", "matplotlib"): {"dataprep": ["kde"]}}
        groups = [{"category": "prep", "values": ["binning"]}]
        assert _image_matches_groups("scatter-basic", "matplotlib", groups, spec_lookup, impl_lookup) is False

    def test_image_matches_groups_style_no_match(self) -> None:
        """Styling filter should not match if not in impl_tags."""
        spec_lookup = {"scatter-basic": {"tags": {}}}
        impl_lookup = {("scatter-basic", "matplotlib"): {"styling": ["alpha-blending"]}}
        groups = [{"category": "style", "values": ["minimal-chrome"]}]
        assert _image_matches_groups("scatter-basic", "matplotlib", groups, spec_lookup, impl_lookup) is False
