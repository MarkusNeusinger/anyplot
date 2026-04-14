"""
Tests for api/routers/proxy.py - HTML proxy endpoint.

Tests URL validation, security checks, and HTML injection.
"""

import re
from unittest.mock import AsyncMock, patch

import httpx
import pytest
from fastapi.testclient import TestClient

from api.main import app
from api.routers.proxy import ALLOWED_BUCKET, ALLOWED_HOST, SIZE_REPORTER_SCRIPT, build_safe_gcs_url


@pytest.fixture
def client() -> TestClient:
    """Create a test client for the FastAPI app."""
    return TestClient(app)


class TestBuildSafeGcsUrl:
    """Tests for build_safe_gcs_url() security function."""

    def test_valid_gcs_url(self):
        """Valid GCS URL should be reconstructed."""
        url = "https://storage.googleapis.com/anyplot-images/plots/scatter-basic/matplotlib/plot.html"
        result = build_safe_gcs_url(url)
        assert result == url

    def test_valid_gcs_url_with_subdirectories(self):
        """Valid GCS URL with multiple subdirectories."""
        url = "https://storage.googleapis.com/anyplot-images/staging/scatter-basic/matplotlib/plot.html"
        result = build_safe_gcs_url(url)
        assert result == url

    def test_http_url_rejected(self):
        """HTTP (non-HTTPS) URLs should be rejected."""
        url = "http://storage.googleapis.com/anyplot-images/plots/scatter-basic/plot.html"
        result = build_safe_gcs_url(url)
        assert result is None

    def test_wrong_host_rejected(self):
        """URLs with wrong host should be rejected."""
        url = "https://evil.com/anyplot-images/plots/scatter-basic/plot.html"
        result = build_safe_gcs_url(url)
        assert result is None

    def test_subdomain_rejected(self):
        """URLs with subdomain of allowed host should be rejected."""
        url = "https://evil.storage.googleapis.com/anyplot-images/plots/plot.html"
        result = build_safe_gcs_url(url)
        assert result is None

    def test_wrong_bucket_rejected(self):
        """URLs with wrong bucket should be rejected."""
        url = "https://storage.googleapis.com/other-bucket/plots/scatter-basic/plot.html"
        result = build_safe_gcs_url(url)
        assert result is None

    def test_path_traversal_rejected(self):
        """Path traversal attempts should be rejected."""
        url = "https://storage.googleapis.com/anyplot-images/../other-bucket/plot.html"
        result = build_safe_gcs_url(url)
        assert result is None

    def test_double_dot_in_path_rejected(self):
        """Double dots anywhere in path should be rejected."""
        url = "https://storage.googleapis.com/anyplot-images/plots/..hidden/plot.html"
        result = build_safe_gcs_url(url)
        assert result is None

    def test_short_path_rejected(self):
        """Paths without file should be rejected."""
        url = "https://storage.googleapis.com/anyplot-images"
        result = build_safe_gcs_url(url)
        assert result is None

    def test_bucket_only_rejected(self):
        """Bucket without path should be rejected."""
        url = "https://storage.googleapis.com/anyplot-images/"
        result = build_safe_gcs_url(url)
        assert result is None

    def test_invalid_characters_rejected(self):
        """Paths with invalid characters should be rejected."""
        # Semicolon is not allowed
        url = "https://storage.googleapis.com/anyplot-images/plots/test;rm+-rf/plot.html"
        result = build_safe_gcs_url(url)
        assert result is None

    def test_space_in_path_rejected(self):
        """Paths with spaces should be rejected."""
        url = "https://storage.googleapis.com/anyplot-images/plots/test plot/plot.html"
        result = build_safe_gcs_url(url)
        assert result is None

    def test_query_string_stripped(self):
        """Query strings should be stripped (not in reconstructed URL)."""
        url = "https://storage.googleapis.com/anyplot-images/plots/scatter/plot.html?token=abc"
        result = build_safe_gcs_url(url)
        # Query is stripped by urlparse when we only use path
        assert result == "https://storage.googleapis.com/anyplot-images/plots/scatter/plot.html"

    def test_valid_characters_allowed(self):
        """Alphanumeric, hyphens, underscores, dots, slashes, plus are allowed."""
        url = "https://storage.googleapis.com/anyplot-images/plots/scatter-basic_v2/plot+extra.html"
        result = build_safe_gcs_url(url)
        assert result == url

    def test_empty_url_rejected(self):
        """Empty URL should be rejected."""
        result = build_safe_gcs_url("")
        assert result is None

    def test_malformed_url_rejected(self):
        """Malformed URL should be rejected."""
        result = build_safe_gcs_url("not-a-url")
        assert result is None

    def test_fragment_stripped(self):
        """URL fragments should be stripped."""
        url = "https://storage.googleapis.com/anyplot-images/plots/scatter/plot.html#section"
        result = build_safe_gcs_url(url)
        assert result == "https://storage.googleapis.com/anyplot-images/plots/scatter/plot.html"


class TestProxyHtmlEndpoint:
    """Tests for /proxy/html endpoint."""

    def test_invalid_url_returns_400(self, client):
        """Invalid URL should return 400 error."""
        response = client.get("/proxy/html", params={"url": "http://evil.com/page.html"})
        assert response.status_code == 400
        assert ALLOWED_HOST in response.json()["message"]

    def test_wrong_bucket_returns_400(self, client):
        """Wrong bucket should return 400 error."""
        response = client.get("/proxy/html", params={"url": "https://storage.googleapis.com/other-bucket/plot.html"})
        assert response.status_code == 400

    @patch("api.routers.proxy.httpx.AsyncClient")
    def test_valid_url_injects_script_before_body(self, mock_client_class, client):
        """Valid URL should inject script before </body>."""
        mock_response = AsyncMock()
        mock_response.text = "<html><body><h1>Test</h1></body></html>"
        mock_response.raise_for_status = lambda: None  # Sync method, no-op

        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_client_class.return_value = mock_client

        response = client.get(
            "/proxy/html", params={"url": "https://storage.googleapis.com/anyplot-images/plots/test/plot.html"}
        )

        assert response.status_code == 200
        assert "anyplot-size" in response.text
        assert SIZE_REPORTER_SCRIPT.strip() in response.text
        assert response.text.index("<script>") < response.text.index("</body>")

    @patch("api.routers.proxy.httpx.AsyncClient")
    def test_security_headers_present(self, mock_client_class, client):
        """Response should include security headers."""
        mock_response = AsyncMock()
        mock_response.text = "<html><body><h1>Test</h1></body></html>"
        mock_response.raise_for_status = lambda: None

        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_client_class.return_value = mock_client

        response = client.get(
            "/proxy/html", params={"url": "https://storage.googleapis.com/anyplot-images/plots/test/plot.html"}
        )

        assert response.status_code == 200
        assert response.headers.get("x-content-type-options") == "nosniff"
        assert response.headers.get("referrer-policy") == "strict-origin-when-cross-origin"

    @patch("api.routers.proxy.httpx.AsyncClient")
    def test_valid_url_injects_script_before_html_if_no_body(self, mock_client_class, client):
        """If no </body>, inject before </html>."""
        mock_response = AsyncMock()
        mock_response.text = "<html><h1>Test</h1></html>"
        mock_response.raise_for_status = lambda: None  # Sync method, no-op

        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_client_class.return_value = mock_client

        response = client.get(
            "/proxy/html", params={"url": "https://storage.googleapis.com/anyplot-images/plots/test/plot.html"}
        )

        assert response.status_code == 200
        assert "anyplot-size" in response.text
        assert response.text.index("<script>") < response.text.index("</html>")

    @patch("api.routers.proxy.httpx.AsyncClient")
    def test_valid_url_appends_script_if_no_body_or_html(self, mock_client_class, client):
        """If no </body> or </html>, append to end."""
        mock_response = AsyncMock()
        mock_response.text = "<div>Just content</div>"
        mock_response.raise_for_status = lambda: None  # Sync method, no-op

        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_client_class.return_value = mock_client

        response = client.get(
            "/proxy/html", params={"url": "https://storage.googleapis.com/anyplot-images/plots/test/plot.html"}
        )

        assert response.status_code == 200
        assert response.text.endswith("</script>\n")

    @patch("api.routers.proxy.httpx.AsyncClient")
    def test_http_error_from_upstream(self, mock_client_class, client):
        """HTTP error from upstream should return appropriate status."""
        # Create a proper mock response for HTTPStatusError
        mock_request = httpx.Request("GET", "https://storage.googleapis.com/test")
        mock_http_response = httpx.Response(404, request=mock_request)

        mock_response = AsyncMock()
        mock_response.status_code = 404

        def raise_status():
            raise httpx.HTTPStatusError("Not found", request=mock_request, response=mock_http_response)

        mock_response.raise_for_status = raise_status

        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_client_class.return_value = mock_client

        response = client.get(
            "/proxy/html", params={"url": "https://storage.googleapis.com/anyplot-images/plots/test/plot.html"}
        )

        assert response.status_code == 404
        assert "Failed to fetch HTML" in response.json()["message"]

    @patch("api.routers.proxy.httpx.AsyncClient")
    def test_connection_error_returns_502(self, mock_client_class, client):
        """Connection error should return 502."""
        mock_request = httpx.Request("GET", "https://storage.googleapis.com/test")

        mock_client = AsyncMock()
        mock_client.get = AsyncMock(side_effect=httpx.RequestError("Connection failed", request=mock_request))
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_client_class.return_value = mock_client

        response = client.get(
            "/proxy/html", params={"url": "https://storage.googleapis.com/anyplot-images/plots/test/plot.html"}
        )

        assert response.status_code == 502
        assert "Failed to connect to storage" in response.json()["message"]


class TestSizeReporterScript:
    """Tests for the injected SIZE_REPORTER_SCRIPT."""

    def test_script_uses_specific_origin(self):
        """Script should use specific origin, not wildcard."""
        assert "'*'" not in SIZE_REPORTER_SCRIPT
        assert '"*"' not in SIZE_REPORTER_SCRIPT
        # Use regex to verify postMessage uses specific origin, not substring check
        # This avoids CodeQL's "incomplete URL substring sanitization" false positive
        # Pattern matches: }, "https://anyplot.ai") - json.dumps() produces double quotes
        pattern = r'\},\s*"https://anyplot\.ai"\)'
        assert re.search(pattern, SIZE_REPORTER_SCRIPT), (
            'postMessage must use specific origin "https://anyplot.ai", not "*"'
        )

    def test_script_sends_anyplot_size_message(self):
        """Script should send anyplot-size message type."""
        assert "anyplot-size" in SIZE_REPORTER_SCRIPT

    def test_script_reports_width_and_height(self):
        """Script should report width and height."""
        assert "width:" in SIZE_REPORTER_SCRIPT
        assert "height:" in SIZE_REPORTER_SCRIPT


class TestConstants:
    """Tests for module constants."""

    def test_allowed_host(self):
        """ALLOWED_HOST should be GCS domain."""
        assert ALLOWED_HOST == "storage.googleapis.com"

    def test_allowed_bucket(self):
        """ALLOWED_BUCKET should be anyplot-images."""
        assert ALLOWED_BUCKET == "anyplot-images"
