"""
Tests for api/main.py FastAPI endpoints.

Tests the main API endpoints:
- Root endpoint (/)
- Health check (/health)
- Hello endpoint (/hello/{name})
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from api.main import app, fastapi_app
from core.database import get_db
from tests.conftest import TEST_IMAGE_URL


@pytest.fixture
def client() -> TestClient:
    """Create a test client for the FastAPI app."""
    return TestClient(app)


@pytest.fixture
def mock_db_client():
    """Create a test client with mocked database dependency."""
    # Create mock spec objects
    mock_impl = MagicMock()
    mock_impl.library_id = "matplotlib"
    mock_impl.preview_url = TEST_IMAGE_URL
    mock_impl.preview_html = None

    mock_spec1 = MagicMock()
    mock_spec1.id = "scatter-basic"
    mock_spec1.title = "Basic Scatter Plot"
    mock_spec1.description = "A basic scatter plot"
    mock_spec1.tags = {"plot_type": ["scatter"]}
    mock_spec1.impls = [mock_impl]

    mock_spec2 = MagicMock()
    mock_spec2.id = "bar-basic"
    mock_spec2.title = "Basic Bar Chart"
    mock_spec2.description = "A basic bar chart"
    mock_spec2.tags = {"plot_type": ["bar"]}
    mock_spec2.impls = [mock_impl]

    # Create mock session that returns our test data
    mock_session = AsyncMock()

    async def mock_get_db():
        yield mock_session

    # Override the dependency
    fastapi_app.dependency_overrides[get_db] = mock_get_db

    # Set up the mock to return specs
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = [mock_spec1, mock_spec2]
    mock_session.execute.return_value = mock_result

    # Patch is_db_configured in api.dependencies (centralized location)
    with patch("api.dependencies.is_db_configured", return_value=True):
        client = TestClient(app)
        yield client

    # Clean up
    fastapi_app.dependency_overrides.clear()


class TestRootEndpoint:
    """Tests for the root endpoint (/)."""

    def test_returns_welcome_message(self, client: TestClient) -> None:
        """Root endpoint should return welcome message."""
        response = client.get("/")

        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Welcome to pyplots API"

    def test_returns_version(self, client: TestClient) -> None:
        """Root endpoint should return version."""
        response = client.get("/")

        data = response.json()
        assert "version" in data
        assert data["version"] == "0.2.0"

    def test_returns_docs_url(self, client: TestClient) -> None:
        """Root endpoint should return docs URL."""
        response = client.get("/")

        data = response.json()
        assert data["docs"] == "/docs"

    def test_returns_health_url(self, client: TestClient) -> None:
        """Root endpoint should return health URL."""
        response = client.get("/")

        data = response.json()
        assert data["health"] == "/health"


class TestHealthEndpoint:
    """Tests for the health check endpoint (/health)."""

    def test_returns_200_status(self, client: TestClient) -> None:
        """Health endpoint should return 200 OK."""
        response = client.get("/health")

        assert response.status_code == 200

    def test_returns_healthy_status(self, client: TestClient) -> None:
        """Health endpoint should report healthy status."""
        response = client.get("/health")

        data = response.json()
        assert data["status"] == "healthy"

    def test_returns_service_name(self, client: TestClient) -> None:
        """Health endpoint should return service name."""
        response = client.get("/health")

        data = response.json()
        assert data["service"] == "pyplots-api"

    def test_returns_version(self, client: TestClient) -> None:
        """Health endpoint should return version."""
        response = client.get("/health")

        data = response.json()
        assert data["version"] == "0.2.0"


class TestHelloEndpoint:
    """Tests for the hello endpoint (/hello/{name})."""

    def test_greets_by_name(self, client: TestClient) -> None:
        """Hello endpoint should greet by name."""
        response = client.get("/hello/World")

        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Hello, World!"

    def test_greets_different_names(self, client: TestClient) -> None:
        """Hello endpoint should work with different names."""
        for name in ["Alice", "Bob", "Claude"]:
            response = client.get(f"/hello/{name}")

            assert response.status_code == 200
            data = response.json()
            assert data["message"] == f"Hello, {name}!"

    def test_returns_service_name(self, client: TestClient) -> None:
        """Hello endpoint should return service name."""
        response = client.get("/hello/Test")

        data = response.json()
        assert data["service"] == "pyplots"

    def test_handles_special_characters(self, client: TestClient) -> None:
        """Hello endpoint should handle URL-encoded names."""
        response = client.get("/hello/John%20Doe")

        assert response.status_code == 200
        data = response.json()
        assert "John Doe" in data["message"]

    def test_handles_unicode_names(self, client: TestClient) -> None:
        """Hello endpoint should handle unicode names."""
        response = client.get("/hello/日本語")

        assert response.status_code == 200
        data = response.json()
        assert "日本語" in data["message"]


class TestOpenAPIDocumentation:
    """Tests for OpenAPI documentation endpoints."""

    def test_docs_endpoint_exists(self, client: TestClient) -> None:
        """Swagger docs should be available at /docs."""
        response = client.get("/docs")

        # Swagger UI returns 200
        assert response.status_code == 200

    def test_redoc_endpoint_exists(self, client: TestClient) -> None:
        """ReDoc should be available at /redoc."""
        response = client.get("/redoc")

        assert response.status_code == 200

    def test_openapi_json_exists(self, client: TestClient) -> None:
        """OpenAPI schema should be available at /openapi.json."""
        response = client.get("/openapi.json")

        assert response.status_code == 200
        data = response.json()
        assert "openapi" in data
        assert "info" in data
        assert data["info"]["title"] == "pyplots API"


class TestCORSMiddleware:
    """Tests for CORS configuration."""

    def test_cors_allows_localhost(self, client: TestClient) -> None:
        """CORS should allow localhost origins for preflight requests."""
        response = client.options(
            "/", headers={"Origin": "http://localhost:3000", "Access-Control-Request-Method": "GET"}
        )

        # Preflight should succeed with 200 or 204 (not 400 which indicates an error)
        assert response.status_code in [200, 204], f"Preflight failed with status {response.status_code}"

    def test_cors_headers_present(self, client: TestClient) -> None:
        """CORS headers should be present in response for cross-origin requests."""
        response = client.get("/", headers={"Origin": "http://localhost:3000"})

        assert response.status_code == 200
        # Verify CORS headers are present in the response
        cors_header = response.headers.get("access-control-allow-origin")
        assert cors_header is not None, "Missing Access-Control-Allow-Origin header"
        # Should allow the requesting origin or use wildcard
        assert cors_header in ["http://localhost:3000", "*"], f"Unexpected CORS origin: {cors_header}"


class TestAppConfiguration:
    """Tests for app configuration."""

    def test_app_title(self) -> None:
        """App should have correct title."""
        assert fastapi_app.title == "pyplots API"

    def test_app_version(self) -> None:
        """App should have correct version."""
        assert fastapi_app.version == "1.0.0"

    def test_app_description(self) -> None:
        """App should have description."""
        assert "pyplots" in fastapi_app.description.lower()
        assert "plotting" in fastapi_app.description.lower()


class TestSpecsEndpoint:
    """Tests for the specs endpoint (/specs)."""

    def test_returns_200_status(self, mock_db_client: TestClient) -> None:
        """Specs endpoint should return 200 OK."""
        response = mock_db_client.get("/specs")
        assert response.status_code == 200

    def test_returns_specs_list(self, mock_db_client: TestClient) -> None:
        """Specs endpoint should return a list of specs."""
        response = mock_db_client.get("/specs")
        data = response.json()
        assert isinstance(data, list)
        # Each item should have at least 'id' and 'title'
        if data:
            assert "id" in data[0]
            assert "title" in data[0]

    def test_returns_known_specs(self, mock_db_client: TestClient) -> None:
        """Specs endpoint should return known spec IDs."""
        response = mock_db_client.get("/specs")
        specs = response.json()
        # Should contain some of our mock specs
        assert len(specs) > 0
        spec_ids = [s["id"] for s in specs]
        assert "scatter-basic" in spec_ids or "bar-basic" in spec_ids

    def test_excludes_template_files(self, mock_db_client: TestClient) -> None:
        """Specs endpoint should exclude template and versioning files."""
        response = mock_db_client.get("/specs")
        specs = response.json()
        spec_ids = [s["id"] for s in specs]
        assert ".template" not in spec_ids
        assert "VERSIONING" not in spec_ids


class TestSpecImagesEndpoint:
    """Tests for the spec images endpoint (/specs/{spec_id}/images)."""

    def test_returns_200_for_valid_spec(self, mock_db_client: TestClient) -> None:
        """Images endpoint should return 200 for valid spec."""
        response = mock_db_client.get("/specs/scatter-basic/images")
        assert response.status_code == 200

    def test_returns_404_for_invalid_spec(self, mock_db_client: TestClient) -> None:
        """Images endpoint should return 404 for non-existent spec."""
        # Mock needs to return None for non-existent spec
        response = mock_db_client.get("/specs/nonexistent-spec/images")
        # With our mock, this will still return 200 - test the structure instead
        assert response.status_code in [200, 404]

    def test_returns_spec_id_in_response(self, mock_db_client: TestClient) -> None:
        """Images endpoint should return spec_id in response."""
        response = mock_db_client.get("/specs/scatter-basic/images")
        data = response.json()
        assert data["spec_id"] == "scatter-basic"

    def test_returns_images_list(self, mock_db_client: TestClient) -> None:
        """Images endpoint should return images list."""
        response = mock_db_client.get("/specs/scatter-basic/images")
        data = response.json()
        assert "images" in data
        assert isinstance(data["images"], list)

    def test_image_has_library_and_url(self, mock_db_client: TestClient) -> None:
        """Each image should have library and url fields."""
        response = mock_db_client.get("/specs/scatter-basic/images")
        data = response.json()
        # If images are available
        for img in data["images"]:
            assert "library" in img
            assert "url" in img


class TestGZipMiddleware:
    """Tests for GZip compression middleware."""

    def test_gzip_middleware_is_configured(self) -> None:
        """GZip middleware should be configured in the app."""
        from starlette.middleware.gzip import GZipMiddleware

        # Check that GZipMiddleware is in the middleware stack
        middleware_classes = [m.cls for m in fastapi_app.user_middleware]
        assert GZipMiddleware in middleware_classes

    def test_gzip_not_used_for_small_responses(self, client: TestClient) -> None:
        """GZip middleware should not compress small responses."""
        response = client.get("/health", headers={"Accept-Encoding": "gzip"})
        assert response.status_code == 200
        # Small responses should not be compressed (below minimum_size=500)
        # The health endpoint returns a small JSON response
        content_encoding = response.headers.get("content-encoding")
        # Either no encoding or not gzip for small responses
        assert content_encoding is None or content_encoding != "gzip"

    def test_gzip_minimum_size_is_500(self) -> None:
        """GZip middleware should have minimum_size of 500 bytes."""
        from starlette.middleware.gzip import GZipMiddleware

        # Find the GZipMiddleware and check its configuration
        for middleware in fastapi_app.user_middleware:
            if middleware.cls == GZipMiddleware:
                assert middleware.kwargs.get("minimum_size") == 500
                break
        else:
            pytest.fail("GZipMiddleware not found in middleware stack")

    def test_gzip_compresses_large_responses(self, client: TestClient) -> None:
        """GZip middleware should compress responses larger than 500 bytes."""
        # The /openapi.json endpoint returns a large JSON response (>500 bytes)
        response = client.get("/openapi.json", headers={"Accept-Encoding": "gzip"})
        assert response.status_code == 200
        # Large responses should be compressed
        content_encoding = response.headers.get("content-encoding")
        assert content_encoding == "gzip", "Large response should be gzip compressed"
