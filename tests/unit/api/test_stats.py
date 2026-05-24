"""
Tests for api/routers/stats.py — stats endpoint and _refresh_stats factory.

Covers:
- _refresh_stats() DB query path
- /stats endpoint with empty and populated specs
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from api.cache import clear_cache
from api.main import app, fastapi_app
from api.routers.stats import _refresh_stats
from core.database import get_db


DB_CONFIG_PATCH = "api.dependencies.is_db_configured"


async def _passthrough_cache(key, factory, **kwargs):
    """Helper: simulate cache miss — always call factory."""
    return await factory()


@pytest.fixture(autouse=True)
def _clear_cache():
    """Clear the global cache before each test."""
    clear_cache()


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


@pytest.fixture
def db_client():
    """Test client with mocked database dependency."""
    mock_session = AsyncMock()

    async def mock_get_db():
        yield mock_session

    fastapi_app.dependency_overrides[get_db] = mock_get_db

    with patch(DB_CONFIG_PATCH, return_value=True):
        client = TestClient(app)
        yield client, mock_session

    fastapi_app.dependency_overrides.clear()


class TestStatsRefreshFactory:
    """Tests for the _refresh_stats standalone factory function."""

    async def test_refresh_stats_queries_db(self) -> None:
        """_refresh_stats should derive stats from aggregate count queries.

        The stats endpoint was refactored to use lightweight COUNT/DISTINCT
        queries instead of loading every spec + impl + library row, so the
        mocks here exercise the new repository methods.
        """
        mock_spec_repo = MagicMock()
        mock_spec_repo.count_with_impls = AsyncMock(return_value=1)

        mock_lib_repo = MagicMock()
        mock_lib_repo.count_with_languages = AsyncMock(return_value=(1, 1))

        mock_impl_repo = MagicMock()
        mock_impl_repo.count_all = AsyncMock(return_value=1)
        mock_impl_repo.get_total_code_lines = AsyncMock(return_value=42)

        mock_db = AsyncMock()

        with (
            patch("api.routers.stats.get_db_context") as mock_ctx,
            patch("api.routers.stats.SpecRepository", return_value=mock_spec_repo),
            patch("api.routers.stats.LibraryRepository", return_value=mock_lib_repo),
            patch("api.routers.stats.ImplRepository", return_value=mock_impl_repo),
        ):
            mock_ctx.return_value.__aenter__ = AsyncMock(return_value=mock_db)
            mock_ctx.return_value.__aexit__ = AsyncMock(return_value=False)
            result = await _refresh_stats()

        assert result.specs == 1  # Only spec with impls
        assert result.plots == 1
        assert result.libraries == 1
        assert result.languages == 1  # Single mock library → one distinct language_id
        assert result.lines_of_code == 42


class TestStatsEndpoint:
    """Tests for the /stats endpoint _fetch branch."""

    def test_stats_with_empty_specs(self, db_client) -> None:
        """Stats should return specs=0, plots=0 when no implementations exist."""
        client, _ = db_client

        mock_spec_repo = MagicMock()
        mock_spec_repo.count_with_impls = AsyncMock(return_value=0)

        mock_lib_repo = MagicMock()
        mock_lib_repo.count_with_languages = AsyncMock(return_value=(1, 1))

        mock_impl_repo = MagicMock()
        mock_impl_repo.count_all = AsyncMock(return_value=0)
        mock_impl_repo.get_total_code_lines = AsyncMock(return_value=0)

        with (
            patch("api.routers.stats.get_or_set_cache", side_effect=_passthrough_cache),
            patch("api.routers.stats.SpecRepository", return_value=mock_spec_repo),
            patch("api.routers.stats.LibraryRepository", return_value=mock_lib_repo),
            patch("api.routers.stats.ImplRepository", return_value=mock_impl_repo),
        ):
            response = client.get("/stats")
            assert response.status_code == 200
            data = response.json()
            assert data["specs"] == 0
            assert data["plots"] == 0
            assert data["libraries"] == 1
