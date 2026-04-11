"""
Tests for api/routers/stats.py — stats endpoint and _refresh_stats factory.

Covers:
- _refresh_stats() with cached data (lines 21-29)
- _refresh_stats() with DB fallback (lines 31-39)
- _fetch() inner function deriving stats from cached responses (line 57-62)
- Stats with specs that have no implementations
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

    async def test_refresh_stats_derives_from_cached_data(self) -> None:
        """_refresh_stats should derive stats from cached specs_list and libraries."""
        # Create mock cached specs (each item needs .library_count)
        mock_spec_item_1 = MagicMock()
        mock_spec_item_1.library_count = 3
        mock_spec_item_2 = MagicMock()
        mock_spec_item_2.library_count = 2

        cached_specs = [mock_spec_item_1, mock_spec_item_2]
        cached_libs = {"libraries": [{"id": "matplotlib"}, {"id": "seaborn"}, {"id": "plotly"}]}

        def fake_get_cache(key):
            if "specs_list" in key:
                return cached_specs
            if "libraries" in key:
                return cached_libs
            return None

        with patch("api.routers.stats.get_cache", side_effect=fake_get_cache):
            result = await _refresh_stats()

        assert result.specs == 2
        assert result.plots == 5  # 3 + 2
        assert result.libraries == 3

    async def test_refresh_stats_falls_back_to_db(self) -> None:
        """_refresh_stats should query DB when no cached data is available."""
        mock_impl = MagicMock()
        mock_spec_with_impl = MagicMock()
        mock_spec_with_impl.impls = [mock_impl]
        mock_spec_no_impl = MagicMock()
        mock_spec_no_impl.impls = []

        mock_lib = MagicMock()

        mock_spec_repo = MagicMock()
        mock_spec_repo.get_all = AsyncMock(return_value=[mock_spec_with_impl, mock_spec_no_impl])

        mock_lib_repo = MagicMock()
        mock_lib_repo.get_all = AsyncMock(return_value=[mock_lib])

        mock_db = AsyncMock()

        with (
            patch("api.routers.stats.get_cache", return_value=None),
            patch("api.routers.stats.get_db_context") as mock_ctx,
            patch("api.routers.stats.SpecRepository", return_value=mock_spec_repo),
            patch("api.routers.stats.LibraryRepository", return_value=mock_lib_repo),
        ):
            mock_ctx.return_value.__aenter__ = AsyncMock(return_value=mock_db)
            mock_ctx.return_value.__aexit__ = AsyncMock(return_value=False)
            result = await _refresh_stats()

        assert result.specs == 1  # Only spec with impls
        assert result.plots == 1
        assert result.libraries == 1


class TestStatsFetchCachedDerivation:
    """Tests for the _fetch() inner function's cached-derivation branch."""

    def test_stats_derived_from_cached_specs_and_libs(self, db_client) -> None:
        """When specs_list and libraries are already cached, stats should be derived from them."""
        client, _ = db_client

        mock_spec_item = MagicMock()
        mock_spec_item.library_count = 4

        cached_specs = [mock_spec_item, mock_spec_item]
        cached_libs = {"libraries": [{"id": "matplotlib"}, {"id": "seaborn"}]}

        def fake_get_cache(key):
            if "specs_list" in key:
                return cached_specs
            if "libraries" in key:
                return cached_libs
            return None

        with (
            patch("api.routers.stats.get_or_set_cache", side_effect=_passthrough_cache),
            patch("api.routers.stats.get_cache", side_effect=fake_get_cache),
        ):
            response = client.get("/stats")
            assert response.status_code == 200
            data = response.json()
            assert data["specs"] == 2
            assert data["plots"] == 8  # 4 + 4
            assert data["libraries"] == 2

    def test_stats_with_empty_specs(self, db_client) -> None:
        """Stats should return specs=0, plots=0 when all specs lack implementations."""
        client, _ = db_client

        mock_spec_no_impl = MagicMock()
        mock_spec_no_impl.impls = []

        mock_spec_repo = MagicMock()
        mock_spec_repo.get_all = AsyncMock(return_value=[mock_spec_no_impl])

        mock_lib_repo = MagicMock()
        mock_lib_repo.get_all = AsyncMock(return_value=[MagicMock()])

        with (
            patch("api.routers.stats.get_or_set_cache", side_effect=_passthrough_cache),
            patch("api.routers.stats.get_cache", return_value=None),
            patch("api.routers.stats.SpecRepository", return_value=mock_spec_repo),
            patch("api.routers.stats.LibraryRepository", return_value=mock_lib_repo),
        ):
            response = client.get("/stats")
            assert response.status_code == 200
            data = response.json()
            assert data["specs"] == 0
            assert data["plots"] == 0
            assert data["libraries"] == 1
