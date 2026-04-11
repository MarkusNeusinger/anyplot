"""
Tests for api/routers/debug.py — debug status endpoint.

Covers the GET /debug/status endpoint including:
- Empty database response
- Specs with implementations (library stats, coverage)
- Low score detection
- Missing preview detection
- Missing tags detection
- Oldest specs ordering
- System health fields
"""

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from api.cache import clear_cache
from api.main import app, fastapi_app
from core.database import get_db


DB_CONFIG_PATCH = "api.dependencies.is_db_configured"


@pytest.fixture(autouse=True)
def _clear_cache():
    """Clear the global cache before each test."""
    clear_cache()


@pytest.fixture
def db_client():
    """Test client with mocked database dependency (require_db needs get_db + is_db_configured)."""
    mock_session = AsyncMock()

    async def mock_get_db():
        yield mock_session

    fastapi_app.dependency_overrides[get_db] = mock_get_db

    with patch(DB_CONFIG_PATCH, return_value=True):
        client = TestClient(app)
        yield client, mock_session

    fastapi_app.dependency_overrides.clear()


def _make_impl(library_id="matplotlib", quality_score=92.5, preview_url="https://example.com/plot.png", updated=None):
    """Helper to create a mock implementation."""
    impl = MagicMock()
    impl.library_id = library_id
    impl.quality_score = quality_score
    impl.preview_url = preview_url
    impl.updated = updated
    return impl


def _make_spec(spec_id="scatter-basic", title="Basic Scatter Plot", impls=None, tags=None, updated=None):
    """Helper to create a mock spec."""
    spec = MagicMock()
    spec.id = spec_id
    spec.title = title
    spec.impls = impls or []
    spec.tags = tags if tags is not None else {"plot_type": ["scatter"]}
    spec.updated = updated
    return spec


class TestDebugStatus:
    """Tests for GET /debug/status endpoint."""

    def test_debug_status_empty_db(self, db_client) -> None:
        """Debug status with no specs should return zeros and empty lists."""
        client, _ = db_client

        mock_repo = MagicMock()
        mock_repo.get_all = AsyncMock(return_value=[])

        with patch("api.routers.debug.SpecRepository", return_value=mock_repo):
            response = client.get("/debug/status")

        assert response.status_code == 200
        data = response.json()
        assert data["total_specs"] == 0
        assert data["total_implementations"] == 0
        assert data["coverage_percent"] == 0
        assert data["specs"] == []
        assert data["low_score_specs"] == []
        assert data["missing_preview_specs"] == []
        assert data["missing_tags_specs"] == []
        assert data["oldest_specs"] == []
        assert len(data["library_stats"]) == 9  # All 9 supported libraries

    def test_debug_status_with_specs_and_impls(self, db_client) -> None:
        """Debug status should compute library stats and coverage from specs/impls."""
        client, _ = db_client

        impl1 = _make_impl(library_id="matplotlib", quality_score=90.0)
        impl2 = _make_impl(library_id="seaborn", quality_score=95.0)
        spec = _make_spec(spec_id="scatter-basic", impls=[impl1, impl2])

        mock_repo = MagicMock()
        mock_repo.get_all = AsyncMock(return_value=[spec])

        with patch("api.routers.debug.SpecRepository", return_value=mock_repo):
            response = client.get("/debug/status")

        assert response.status_code == 200
        data = response.json()
        assert data["total_specs"] == 1
        assert data["total_implementations"] == 2
        # coverage = 2 / (1 * 9) * 100 = 22.2%
        assert data["coverage_percent"] == 22.2

        # Check library stats
        lib_stats_by_id = {ls["id"]: ls for ls in data["library_stats"]}
        assert lib_stats_by_id["matplotlib"]["impl_count"] == 1
        assert lib_stats_by_id["matplotlib"]["avg_score"] == 90.0
        assert lib_stats_by_id["seaborn"]["impl_count"] == 1
        assert lib_stats_by_id["seaborn"]["avg_score"] == 95.0
        # Libraries with no impls should have count=0
        assert lib_stats_by_id["plotly"]["impl_count"] == 0
        assert lib_stats_by_id["plotly"]["avg_score"] is None

        # Check spec avg_score
        assert data["specs"][0]["avg_score"] == 92.5  # (90 + 95) / 2

    def test_debug_status_low_score_detection(self, db_client) -> None:
        """Specs with avg quality_score < 90 should appear in low_score_specs."""
        client, _ = db_client

        low_impl = _make_impl(library_id="matplotlib", quality_score=70.0)
        low_spec = _make_spec(spec_id="bad-chart", title="Bad Chart", impls=[low_impl])

        high_impl = _make_impl(library_id="matplotlib", quality_score=95.0)
        high_spec = _make_spec(spec_id="good-chart", title="Good Chart", impls=[high_impl])

        mock_repo = MagicMock()
        mock_repo.get_all = AsyncMock(return_value=[low_spec, high_spec])

        with patch("api.routers.debug.SpecRepository", return_value=mock_repo):
            response = client.get("/debug/status")

        data = response.json()
        low_ids = [s["id"] for s in data["low_score_specs"]]
        assert "bad-chart" in low_ids
        assert "good-chart" not in low_ids

    def test_debug_status_missing_preview(self, db_client) -> None:
        """Impls with no preview_url should appear in missing_preview_specs."""
        client, _ = db_client

        no_preview_impl = _make_impl(library_id="matplotlib", preview_url=None)
        spec = _make_spec(spec_id="no-preview", title="No Preview", impls=[no_preview_impl])

        mock_repo = MagicMock()
        mock_repo.get_all = AsyncMock(return_value=[spec])

        with patch("api.routers.debug.SpecRepository", return_value=mock_repo):
            response = client.get("/debug/status")

        data = response.json()
        assert len(data["missing_preview_specs"]) == 1
        assert data["missing_preview_specs"][0]["id"] == "no-preview"
        assert "matplotlib" in data["missing_preview_specs"][0]["issue"]

    def test_debug_status_missing_tags(self, db_client) -> None:
        """Specs with empty or missing tags should appear in missing_tags_specs."""
        client, _ = db_client

        impl = _make_impl()
        # Spec with tags that have empty values
        spec_empty_tags = _make_spec(
            spec_id="no-tags", title="No Tags", impls=[impl], tags={"plot_type": [], "domain": []}
        )
        # Spec with proper tags
        spec_with_tags = _make_spec(
            spec_id="has-tags", title="Has Tags", impls=[impl], tags={"plot_type": ["scatter"]}
        )

        mock_repo = MagicMock()
        mock_repo.get_all = AsyncMock(return_value=[spec_empty_tags, spec_with_tags])

        with patch("api.routers.debug.SpecRepository", return_value=mock_repo):
            response = client.get("/debug/status")

        data = response.json()
        missing_ids = [s["id"] for s in data["missing_tags_specs"]]
        assert "no-tags" in missing_ids
        assert "has-tags" not in missing_ids

    def test_debug_status_oldest_specs(self, db_client) -> None:
        """Oldest specs should be detected from updated timestamps."""
        client, _ = db_client

        old_time = datetime(2024, 1, 1, tzinfo=timezone.utc)
        recent_time = datetime(2026, 4, 1, tzinfo=timezone.utc)

        impl_old = _make_impl(updated=old_time)
        spec_old = _make_spec(spec_id="old-spec", title="Old Spec", impls=[impl_old], updated=old_time)

        impl_new = _make_impl(updated=recent_time)
        spec_new = _make_spec(spec_id="new-spec", title="New Spec", impls=[impl_new], updated=recent_time)

        mock_repo = MagicMock()
        mock_repo.get_all = AsyncMock(return_value=[spec_old, spec_new])

        with patch("api.routers.debug.SpecRepository", return_value=mock_repo):
            response = client.get("/debug/status")

        data = response.json()
        assert len(data["oldest_specs"]) >= 1
        oldest_ids = [s["id"] for s in data["oldest_specs"]]
        assert "old-spec" in oldest_ids
        # The old spec should have "days ago" in its value
        old_entry = next(s for s in data["oldest_specs"] if s["id"] == "old-spec")
        assert "days ago" in old_entry["value"]

    def test_debug_status_system_health(self, db_client) -> None:
        """System health should report database_connected=True and valid fields."""
        client, _ = db_client

        mock_repo = MagicMock()
        mock_repo.get_all = AsyncMock(return_value=[])

        with patch("api.routers.debug.SpecRepository", return_value=mock_repo):
            response = client.get("/debug/status")

        data = response.json()
        system = data["system"]
        assert system["database_connected"] is True
        assert system["api_response_time_ms"] >= 0
        assert system["timestamp"]  # Non-empty ISO timestamp
        assert system["total_specs_in_db"] == 0
        assert system["total_impls_in_db"] == 0
