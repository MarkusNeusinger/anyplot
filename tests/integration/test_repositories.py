"""
Integration tests for repository classes.

Tests actual database operations with SQLite in-memory database.
Tests Repository layer interaction with database (no HTTP layer).
"""

import pytest

from core.database.repositories import FeedbackRepository, ImplRepository, LibraryRepository, SpecRepository


pytestmark = pytest.mark.integration


class TestSpecRepository:
    """Integration tests for SpecRepository."""

    async def test_get_all(self, test_db_with_data):
        """Should fetch all specs with implementations."""
        repo = SpecRepository(test_db_with_data)
        specs = await repo.get_all()

        assert len(specs) == 2
        spec_ids = {spec.id for spec in specs}
        assert spec_ids == {"bar-grouped", "scatter-basic"}

        # Check implementations
        scatter_spec = next(s for s in specs if s.id == "scatter-basic")
        assert len(scatter_spec.impls) == 2

    async def test_get_by_id(self, test_db_with_data):
        """Should fetch spec by ID with implementations and library info."""
        repo = SpecRepository(test_db_with_data)
        spec = await repo.get_by_id("scatter-basic")

        assert spec is not None
        assert spec.id == "scatter-basic"
        assert spec.title == "Basic Scatter Plot"
        assert len(spec.impls) == 2
        assert spec.impls[0].library.name in ["Matplotlib", "Seaborn"]

    async def test_get_by_id_not_found(self, test_db_with_data):
        """Should return None for non-existent spec."""
        repo = SpecRepository(test_db_with_data)
        spec = await repo.get_by_id("nonexistent")

        assert spec is None

    async def test_get_by_id_with_code(self, test_db_with_data):
        """Should eager-load Impl.code so reading it after the call doesn't lazy-load."""
        repo = SpecRepository(test_db_with_data)
        spec = await repo.get_by_id_with_code("scatter-basic")

        assert spec is not None
        assert len(spec.impls) == 2
        # Touching code on every impl must not trigger a deferred SELECT.
        for impl in spec.impls:
            assert impl.code is not None
            assert isinstance(impl.code, str)

    async def test_get_by_id_with_code_not_found(self, test_db_with_data):
        """Should return None for non-existent spec."""
        repo = SpecRepository(test_db_with_data)
        spec = await repo.get_by_id_with_code("nonexistent")

        assert spec is None

    async def test_get_ids(self, test_db_with_data):
        """Should fetch all spec IDs in order."""
        repo = SpecRepository(test_db_with_data)
        ids = await repo.get_ids()

        assert len(ids) == 2
        assert ids == ["bar-grouped", "scatter-basic"]

    async def test_search_by_tags(self, test_db_with_data):
        """Should search specs by tags."""
        repo = SpecRepository(test_db_with_data)

        # Search for scatter plots
        scatter_specs = await repo.search_by_tags(["scatter"])
        assert len(scatter_specs) == 1
        assert scatter_specs[0].id == "scatter-basic"

        # Search for bar plots
        bar_specs = await repo.search_by_tags(["bar"])
        assert len(bar_specs) == 1
        assert bar_specs[0].id == "bar-grouped"

    async def test_create(self, test_session):
        """Should create new spec."""
        repo = SpecRepository(test_session)

        spec_data = {
            "id": "line-timeseries",
            "title": "Time Series Line Plot",
            "description": "A line plot for time series data",
            "applications": ["trends", "time analysis"],
            "data": ["temporal", "numeric"],
            "notes": ["Good for trends"],
            "tags": {"plot_type": ["line"], "domain": ["statistics"]},
            "issue": 44,
            "suggested": "user123",
        }

        spec = await repo.create(spec_data)
        assert spec.id == "line-timeseries"
        assert spec.title == "Time Series Line Plot"
        assert spec.issue == 44

    async def test_update(self, test_db_with_data):
        """Should update existing spec."""
        repo = SpecRepository(test_db_with_data)

        updated = await repo.update("scatter-basic", {"title": "Updated Scatter Plot", "issue": 100})

        assert updated is not None
        assert updated.title == "Updated Scatter Plot"
        assert updated.issue == 100
        assert updated.id == "scatter-basic"  # ID unchanged

    async def test_update_not_found(self, test_db_with_data):
        """Should return None when updating non-existent spec."""
        repo = SpecRepository(test_db_with_data)
        result = await repo.update("nonexistent", {"title": "Test"})

        assert result is None

    async def test_delete(self, test_db_with_data):
        """Should delete spec and cascade delete implementations."""
        repo = SpecRepository(test_db_with_data)

        # Delete spec
        result = await repo.delete("scatter-basic")
        assert result is True

        # Verify deletion
        spec = await repo.get_by_id("scatter-basic")
        assert spec is None

    async def test_delete_not_found(self, test_db_with_data):
        """Should return False when deleting non-existent spec."""
        repo = SpecRepository(test_db_with_data)
        result = await repo.delete("nonexistent")

        assert result is False

    async def test_upsert_create(self, test_session):
        """Should create new spec via upsert."""
        repo = SpecRepository(test_session)

        spec_data = {
            "id": "heatmap-correlation",
            "title": "Correlation Heatmap",
            "description": "A heatmap showing correlations",
            "applications": ["correlation analysis"],
            "data": ["numeric"],
            "notes": ["Use correlation matrix"],
            "tags": {"plot_type": ["heatmap"]},
        }

        spec = await repo.upsert(spec_data)
        assert spec.id == "heatmap-correlation"
        assert spec.title == "Correlation Heatmap"

    async def test_upsert_update(self, test_db_with_data):
        """Should update existing spec via upsert."""
        repo = SpecRepository(test_db_with_data)

        spec_data = {"id": "scatter-basic", "title": "Updated via Upsert", "description": "New description"}

        spec = await repo.upsert(spec_data)
        assert spec.id == "scatter-basic"
        assert spec.title == "Updated via Upsert"


class TestLibraryRepository:
    """Integration tests for LibraryRepository."""

    async def test_get_all(self, test_db_with_data):
        """Should fetch all libraries."""
        repo = LibraryRepository(test_db_with_data)
        libraries = await repo.get_all()

        assert len(libraries) == 2
        assert libraries[0].id == "matplotlib"
        assert libraries[1].id == "seaborn"

    async def test_get_by_id(self, test_db_with_data):
        """Should fetch library by ID."""
        repo = LibraryRepository(test_db_with_data)
        library = await repo.get_by_id("matplotlib")

        assert library is not None
        assert library.id == "matplotlib"
        assert library.name == "Matplotlib"
        assert library.version == "3.10.0"

    async def test_get_by_id_not_found(self, test_db_with_data):
        """Should return None for non-existent library."""
        repo = LibraryRepository(test_db_with_data)
        library = await repo.get_by_id("nonexistent")

        assert library is None

    async def test_create(self, test_session):
        """Should create new library."""
        repo = LibraryRepository(test_session)

        library_data = {
            "id": "plotly",
            "name": "Plotly",
            "version": "5.18.0",
            "documentation_url": "https://plotly.com",
            "description": "Interactive plotting library",
        }

        library = await repo.create(library_data)
        assert library.id == "plotly"
        assert library.name == "Plotly"

    async def test_update(self, test_db_with_data):
        """Should update existing library."""
        repo = LibraryRepository(test_db_with_data)

        updated = await repo.update("matplotlib", {"version": "3.11.0"})

        assert updated is not None
        assert updated.version == "3.11.0"
        assert updated.id == "matplotlib"

    async def test_delete(self, test_db_with_data):
        """Should delete library."""
        repo = LibraryRepository(test_db_with_data)

        result = await repo.delete("seaborn")
        assert result is True

        # Verify deletion
        library = await repo.get_by_id("seaborn")
        assert library is None

    async def test_upsert_create(self, test_session):
        """Should create new library via upsert."""
        repo = LibraryRepository(test_session)

        library_data = {"id": "bokeh", "name": "Bokeh", "version": "3.4.0", "documentation_url": "https://bokeh.org"}

        library = await repo.upsert(library_data)
        assert library.id == "bokeh"
        assert library.name == "Bokeh"

    async def test_upsert_update(self, test_db_with_data):
        """Should update existing library via upsert."""
        repo = LibraryRepository(test_db_with_data)

        library_data = {"id": "matplotlib", "version": "3.12.0"}

        library = await repo.upsert(library_data)
        assert library.id == "matplotlib"
        assert library.version == "3.12.0"


class TestImplRepository:
    """Integration tests for ImplRepository."""

    async def test_get_by_spec(self, test_db_with_data):
        """Should fetch implementations for a spec."""
        repo = ImplRepository(test_db_with_data)
        impls = await repo.get_by_spec("scatter-basic")

        assert len(impls) == 2
        assert impls[0].library.name in ["Matplotlib", "Seaborn"]

    async def test_get_by_library(self, test_db_with_data):
        """Should fetch implementations for a library."""
        repo = ImplRepository(test_db_with_data)
        impls = await repo.get_by_library("matplotlib")

        assert len(impls) == 2
        assert all(impl.library_id == "matplotlib" for impl in impls)

    async def test_get_by_spec_and_library(self, test_db_with_data):
        """Should fetch specific implementation."""
        repo = ImplRepository(test_db_with_data)
        impl = await repo.get_by_spec_and_library("scatter-basic", "matplotlib")

        assert impl is not None
        assert impl.spec_id == "scatter-basic"
        assert impl.library_id == "matplotlib"
        assert impl.quality_score == 92.5

    async def test_get_by_spec_and_library_not_found(self, test_db_with_data):
        """Should return None for non-existent implementation."""
        repo = ImplRepository(test_db_with_data)
        impl = await repo.get_by_spec_and_library("scatter-basic", "plotly")

        assert impl is None

    async def test_create(self, test_db_with_data):
        """Should create new implementation."""
        repo = ImplRepository(test_db_with_data)

        impl_data = {
            "spec_id": "bar-grouped",
            "library_id": "seaborn",
            "code": "import seaborn as sns\n# bar chart code",
            "preview_url": "https://example.com/bar-seaborn.png",
            "quality_score": 90.0,
            "generated_by": "claude",
            "python_version": "3.13",
            "library_version": "0.13.0",
        }

        impl = await repo.create(impl_data)
        assert impl.spec_id == "bar-grouped"
        assert impl.library_id == "seaborn"
        assert impl.quality_score == 90.0

    async def test_update(self, test_db_with_data):
        """Should update existing implementation."""
        repo = ImplRepository(test_db_with_data)

        # Get an impl ID first
        impls = await repo.get_by_spec("scatter-basic")
        impl_id = impls[0].id

        updated = await repo.update(str(impl_id), {"quality_score": 99.0})

        assert updated is not None
        assert updated.quality_score == 99.0

    async def test_delete(self, test_db_with_data):
        """Should delete implementation."""
        repo = ImplRepository(test_db_with_data)

        # Get an impl ID first
        impls = await repo.get_by_spec("scatter-basic")
        impl_id = impls[0].id

        result = await repo.delete(str(impl_id))
        assert result is True

    async def test_upsert_create(self, test_db_with_data):
        """Should create new implementation via upsert."""
        repo = ImplRepository(test_db_with_data)

        impl = await repo.upsert("scatter-basic", "seaborn", {"code": "updated code", "quality_score": 96.0})
        assert impl.spec_id == "scatter-basic"
        assert impl.library_id == "seaborn"
        assert impl.quality_score == 96.0

    async def test_upsert_update(self, test_db_with_data):
        """Should update existing implementation via upsert."""
        repo = ImplRepository(test_db_with_data)

        impl = await repo.upsert("scatter-basic", "matplotlib", {"quality_score": 98.0})
        assert impl.spec_id == "scatter-basic"
        assert impl.library_id == "matplotlib"
        assert impl.quality_score == 98.0


class TestFeedbackRepository:
    """Integration tests for FeedbackRepository (issue #5662)."""

    async def test_create_and_list_recent(self, test_session):
        """Should persist an entry and return it via list_recent."""
        repo = FeedbackRepository(test_session)

        entry = await repo.create({"message": "Hello", "reaction": "thumbs_up", "ip_hash": "deadbeef"})
        assert entry.id is not None
        assert entry.message == "Hello"
        assert entry.reaction == "thumbs_up"

        recent = await repo.list_recent()
        assert len(recent) == 1
        assert recent[0].id == entry.id

    async def test_count_recent_by_ip(self, test_session):
        """Should count entries within the time window per ip_hash."""
        from datetime import datetime, timedelta, timezone

        repo = FeedbackRepository(test_session)

        await repo.create({"message": "one", "ip_hash": "aaa"})
        await repo.create({"message": "two", "ip_hash": "aaa"})
        await repo.create({"message": "three", "ip_hash": "bbb"})

        since = datetime.now(timezone.utc) - timedelta(minutes=1)
        assert await repo.count_recent_by_ip("aaa", since) == 2
        assert await repo.count_recent_by_ip("bbb", since) == 1
        assert await repo.count_recent_by_ip("ccc", since) == 0
