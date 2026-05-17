"""Unit tests for the /feedback router (issue #5662).

Uses dependency overrides + mock repository to exercise guard logic in isolation
from the database. Integration coverage (real persistence, rate limiting against
SQLite) lives in tests/integration/api/test_api_endpoints.py.
"""

from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from api.cache import clear_cache
from api.main import app, fastapi_app
from core.database import get_db


DB_CONFIG_PATCH = "api.dependencies.is_db_configured"


@pytest.fixture(autouse=True)
def _clear_cache():
    clear_cache()


@pytest.fixture
def client():
    """TestClient with a mocked DB session injected via dependency_overrides."""
    mock_session = AsyncMock()

    async def mock_get_db():
        yield mock_session

    fastapi_app.dependency_overrides[get_db] = mock_get_db

    with patch(DB_CONFIG_PATCH, return_value=True):
        yield TestClient(app)

    fastapi_app.dependency_overrides.clear()


class TestFeedbackRouter:
    def test_honeypot_returns_ok_without_persisting(self, client):
        """Should silently 200 when the hidden honeypot field is populated, and never touch the repo."""
        with patch("api.routers.feedback.FeedbackRepository") as repo_cls:
            response = client.post("/feedback", json={"message": "spam", "website": "http://evil.example"})

        assert response.status_code == 200
        assert response.json() == {"status": "ok"}
        repo_cls.assert_not_called()

    def test_empty_message_returns_400(self, client):
        response = client.post("/feedback", json={"message": "   "})
        assert response.status_code == 400

    def test_message_over_500_chars_returns_400(self, client):
        response = client.post("/feedback", json={"message": "x" * 501})
        assert response.status_code == 400

    def test_invalid_reaction_returns_400(self, client):
        response = client.post("/feedback", json={"message": "hello", "reaction": "fire"})
        assert response.status_code == 400

    def test_invalid_email_returns_400(self, client):
        response = client.post("/feedback", json={"message": "hello", "email": "no-at-symbol"})
        assert response.status_code == 400

    def test_happy_path_calls_repo_create(self, client):
        """Valid payload should sanitize fields and forward them to FeedbackRepository.create."""
        instance = AsyncMock()
        instance.count_recent_by_ip = AsyncMock(return_value=0)
        instance.create = AsyncMock(return_value=None)

        with patch("api.routers.feedback.FeedbackRepository", return_value=instance):
            response = client.post(
                "/feedback",
                json={
                    "message": "  Looks great!  ",
                    "reaction": "heart",
                    "email": "user@example.com",
                    "path": "/scatter-basic",
                    "spec_id": "scatter-basic",
                    "viewport": "1920x1080",
                    "session_id": "abc-123",
                },
                headers={"x-forwarded-for": "198.51.100.7"},
            )

        assert response.status_code == 200
        assert response.json() == {"status": "ok"}
        instance.create.assert_awaited_once()
        kwargs = instance.create.await_args.args[0]
        assert kwargs["message"] == "Looks great!"  # trimmed
        assert kwargs["reaction"] == "heart"
        assert kwargs["email"] == "user@example.com"
        assert kwargs["spec_id"] == "scatter-basic"
        assert kwargs["ip_hash"]  # sha256 hex, not raw IP
        assert "198.51.100.7" not in kwargs["ip_hash"]

    def test_rate_limit_returns_429(self, client):
        """Should return 429 when the rate-limit query reports too many recent entries."""
        instance = AsyncMock()
        instance.count_recent_by_ip = AsyncMock(return_value=5)
        instance.create = AsyncMock(return_value=None)

        with patch("api.routers.feedback.FeedbackRepository", return_value=instance):
            response = client.post("/feedback", json={"message": "hi"}, headers={"x-forwarded-for": "198.51.100.8"})

        assert response.status_code == 429
        instance.create.assert_not_awaited()
