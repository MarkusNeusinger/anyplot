"""
API integration tests with SQLite in-memory database.

Tests full API stack using FastAPI's dependency override mechanism
with SQLite in-memory database for fast, isolated testing.
"""

from unittest.mock import patch

import pytest
from httpx import ASGITransport, AsyncClient

from api.cache import clear_cache
from api.dependencies import get_db
from api.main import app, fastapi_app


pytestmark = pytest.mark.integration


@pytest.fixture
async def client(test_db_with_data):
    """
    Create test client with SQLite database override.

    Uses FastAPI's dependency_overrides to inject the test database
    session instead of the production database. Also patches
    is_db_configured to return True.
    """
    # Clear cache to ensure fresh data for each test
    clear_cache()

    async def override_get_db():
        yield test_db_with_data

    fastapi_app.dependency_overrides[get_db] = override_get_db

    # Patch is_db_configured to return True (it checks env vars, not dependencies)
    with patch("api.dependencies.is_db_configured", return_value=True):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            yield ac

    fastapi_app.dependency_overrides.clear()


class TestSpecsEndpoints:
    """Integration tests for /specs endpoints."""

    async def test_get_specs_with_db(self, client):
        """Should return all specs from database."""
        response = await client.get("/specs")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 2
        assert data[0]["id"] in ["scatter-basic", "bar-grouped"]

    async def test_get_spec_detail(self, client):
        """Should return spec detail with implementations."""
        response = await client.get("/specs/scatter-basic")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "scatter-basic"
        assert data["title"] == "Basic Scatter Plot"
        assert "implementations" in data
        assert len(data["implementations"]) == 2

    async def test_get_spec_not_found(self, client):
        """Should return 404 for non-existent spec."""
        response = await client.get("/specs/nonexistent")

        assert response.status_code == 404

    async def test_get_spec_images(self, client):
        """Should return images for spec."""
        response = await client.get("/specs/scatter-basic/images")

        assert response.status_code == 200
        data = response.json()
        assert "images" in data
        assert len(data["images"]) == 2


class TestLibrariesEndpoints:
    """Integration tests for /libraries endpoints."""

    async def test_get_libraries(self, client):
        """Should return all libraries."""
        response = await client.get("/libraries")

        assert response.status_code == 200
        data = response.json()
        assert "libraries" in data
        assert len(data["libraries"]) == 2

    async def test_get_library_images(self, client):
        """Should return images for library."""
        response = await client.get("/libraries/matplotlib/images")

        assert response.status_code == 200
        data = response.json()
        assert "images" in data
        assert len(data["images"]) == 2

    async def test_get_library_images_invalid(self, client):
        """Should return 404 for invalid library."""
        response = await client.get("/libraries/invalid/images")

        assert response.status_code == 404


class TestStatsEndpoints:
    """Integration tests for /stats endpoint."""

    async def test_get_stats(self, client):
        """Should return statistics from database."""
        response = await client.get("/stats")

        assert response.status_code == 200
        data = response.json()
        assert data["specs"] == 2
        assert data["plots"] == 3  # 2 scatter + 1 bar
        assert data["libraries"] == 2


class TestPlotsFilterEndpoints:
    """Integration tests for /plots/filter endpoint."""

    async def test_filter_no_params(self, client):
        """Should return all images when no filters."""
        response = await client.get("/plots/filter")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 3
        assert len(data["images"]) == 3

    async def test_filter_by_library(self, client):
        """Should filter by library."""
        response = await client.get("/plots/filter?lib=matplotlib")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 2  # scatter-matplotlib + bar-matplotlib
        assert all(img["library"] == "matplotlib" for img in data["images"])

    async def test_filter_by_spec(self, client):
        """Should filter by spec."""
        response = await client.get("/plots/filter?spec=scatter-basic")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 2  # scatter-matplotlib + scatter-seaborn
        assert all(img["spec_id"] == "scatter-basic" for img in data["images"])

    async def test_filter_by_plot_type(self, client):
        """Should filter by plot type tag."""
        response = await client.get("/plots/filter?plot=scatter")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 2

    async def test_filter_combined(self, client):
        """Should filter by multiple parameters (AND logic)."""
        response = await client.get("/plots/filter?lib=matplotlib&plot=scatter")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1  # Only scatter-matplotlib
        assert data["images"][0]["library"] == "matplotlib"
        assert data["images"][0]["spec_id"] == "scatter-basic"


class TestDownloadEndpoints:
    """Integration tests for /download endpoint (image proxy)."""

    async def test_download_spec_not_found(self, client):
        """Should return 404 for non-existent spec."""
        response = await client.get("/download/nonexistent/matplotlib")

        assert response.status_code == 404

    async def test_download_impl_not_found(self, client):
        """Should return 404 for non-existent implementation."""
        response = await client.get("/download/scatter-basic/plotly")

        assert response.status_code == 404


class TestSeoEndpoints:
    """Integration tests for SEO endpoints."""

    async def test_robots_txt(self, client):
        """Should return robots.txt blocking crawlers from all routes."""
        response = await client.get("/robots.txt")
        assert response.status_code == 200
        assert response.headers["content-type"] == "text/plain; charset=utf-8"
        assert "User-agent: *" in response.text
        assert "Disallow: /" in response.text

    async def test_sitemap(self, client):
        """Should return sitemap XML with spec URLs."""
        response = await client.get("/sitemap.xml")

        assert response.status_code == 200
        assert response.headers["content-type"] == "application/xml"
        content = response.text
        assert "scatter-basic" in content
        assert "bar-grouped" in content


class TestHealthEndpoints:
    """Integration tests for health endpoints."""

    async def test_root(self, client):
        """Should return API info."""
        response = await client.get("/")

        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Welcome to anyplot API"
        assert "version" in data

    async def test_health_check(self, client):
        """Should return healthy status."""
        response = await client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "anyplot-api"

    async def test_hello(self, client):
        """Should return personalized greeting."""
        response = await client.get("/hello/World")

        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Hello, World!"
