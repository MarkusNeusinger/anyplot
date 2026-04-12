"""
Tests for database repository classes.

Uses in-memory SQLite to test repository operations.
"""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from core.database.models import Impl, Library, Spec
from core.database.repositories import (
    IMPL_UPDATABLE_FIELDS,
    LIBRARY_UPDATABLE_FIELDS,
    SPEC_UPDATABLE_FIELDS,
    BaseRepository,
    ImplRepository,
    LibraryRepository,
    SpecRepository,
)


# ===== Field Validation Constants =====


class TestUpdatableFieldConstants:
    """Tests for the updatable field sets."""

    def test_spec_fields_includes_core(self) -> None:
        assert "title" in SPEC_UPDATABLE_FIELDS
        assert "description" in SPEC_UPDATABLE_FIELDS
        assert "tags" in SPEC_UPDATABLE_FIELDS

    def test_spec_fields_excludes_id(self) -> None:
        assert "id" not in SPEC_UPDATABLE_FIELDS

    def test_library_fields(self) -> None:
        assert "name" in LIBRARY_UPDATABLE_FIELDS
        assert "version" in LIBRARY_UPDATABLE_FIELDS
        assert "id" not in LIBRARY_UPDATABLE_FIELDS

    def test_impl_fields_includes_review(self) -> None:
        assert "quality_score" in IMPL_UPDATABLE_FIELDS
        assert "review_strengths" in IMPL_UPDATABLE_FIELDS
        assert "review_weaknesses" in IMPL_UPDATABLE_FIELDS
        assert "review_verdict" in IMPL_UPDATABLE_FIELDS
        assert "impl_tags" in IMPL_UPDATABLE_FIELDS

    def test_impl_fields_excludes_keys(self) -> None:
        assert "id" not in IMPL_UPDATABLE_FIELDS
        assert "spec_id" not in IMPL_UPDATABLE_FIELDS
        assert "library_id" not in IMPL_UPDATABLE_FIELDS


# ===== Repository Tests with In-Memory SQLite =====


class TestSpecRepository:
    """Tests for SpecRepository."""

    @pytest.mark.asyncio
    async def test_get_all_empty(self, test_session: AsyncSession) -> None:
        repo = SpecRepository(test_session)
        specs = await repo.get_all()
        assert specs == []

    @pytest.mark.asyncio
    async def test_create_and_get(self, test_session: AsyncSession) -> None:
        repo = SpecRepository(test_session)
        spec = await repo.create({"id": "scatter-basic", "title": "Basic Scatter"})
        assert spec.id == "scatter-basic"
        assert spec.title == "Basic Scatter"

        retrieved = await repo.get_by_id("scatter-basic")
        assert retrieved is not None
        assert retrieved.title == "Basic Scatter"

    @pytest.mark.asyncio
    async def test_get_by_id_not_found(self, test_session: AsyncSession) -> None:
        repo = SpecRepository(test_session)
        result = await repo.get_by_id("nonexistent")
        assert result is None

    @pytest.mark.asyncio
    async def test_get_ids(self, test_session: AsyncSession) -> None:
        repo = SpecRepository(test_session)
        await repo.create({"id": "bar-basic", "title": "Basic Bar"})
        await repo.create({"id": "scatter-basic", "title": "Basic Scatter"})

        ids = await repo.get_ids()
        assert ids == ["bar-basic", "scatter-basic"]

    @pytest.mark.asyncio
    async def test_upsert_creates(self, test_session: AsyncSession) -> None:
        repo = SpecRepository(test_session)
        spec = await repo.upsert({"id": "new-spec", "title": "New Spec"})
        assert spec.id == "new-spec"
        assert spec.title == "New Spec"

    @pytest.mark.asyncio
    async def test_upsert_updates(self, test_session: AsyncSession) -> None:
        repo = SpecRepository(test_session)
        await repo.create({"id": "existing", "title": "Original"})
        spec = await repo.upsert({"id": "existing", "title": "Updated"})
        assert spec.title == "Updated"

    @pytest.mark.asyncio
    async def test_upsert_without_id_raises(self, test_session: AsyncSession) -> None:
        repo = SpecRepository(test_session)
        with pytest.raises(ValueError, match="must include 'id'"):
            await repo.upsert({"title": "No ID"})

    @pytest.mark.asyncio
    async def test_update(self, test_session: AsyncSession) -> None:
        repo = SpecRepository(test_session)
        await repo.create({"id": "s1", "title": "Original"})
        updated = await repo.update("s1", {"title": "Updated", "description": "New desc"})
        assert updated is not None
        assert updated.title == "Updated"
        assert updated.description == "New desc"

    @pytest.mark.asyncio
    async def test_update_nonexistent(self, test_session: AsyncSession) -> None:
        repo = SpecRepository(test_session)
        result = await repo.update("nonexistent", {"title": "X"})
        assert result is None

    @pytest.mark.asyncio
    async def test_update_ignores_non_updatable(self, test_session: AsyncSession) -> None:
        repo = SpecRepository(test_session)
        await repo.create({"id": "s1", "title": "Original"})
        updated = await repo.update("s1", {"id": "new-id", "title": "Updated"})
        assert updated.id == "s1"  # ID should not change
        assert updated.title == "Updated"

    @pytest.mark.asyncio
    async def test_delete(self, test_session: AsyncSession) -> None:
        repo = SpecRepository(test_session)
        await repo.create({"id": "s1", "title": "To Delete"})
        assert await repo.delete("s1") is True
        assert await repo.get_by_id("s1") is None

    @pytest.mark.asyncio
    async def test_delete_nonexistent(self, test_session: AsyncSession) -> None:
        repo = SpecRepository(test_session)
        assert await repo.delete("nonexistent") is False


class TestLibraryRepository:
    """Tests for LibraryRepository."""

    @pytest.mark.asyncio
    async def test_create_and_get_all(self, test_session: AsyncSession) -> None:
        repo = LibraryRepository(test_session)
        await repo.create({"id": "matplotlib", "name": "Matplotlib"})
        await repo.create({"id": "seaborn", "name": "Seaborn"})

        libs = await repo.get_all()
        assert len(libs) == 2
        # Should be ordered by name
        assert libs[0].name == "Matplotlib"
        assert libs[1].name == "Seaborn"

    @pytest.mark.asyncio
    async def test_upsert_creates(self, test_session: AsyncSession) -> None:
        repo = LibraryRepository(test_session)
        lib = await repo.upsert({"id": "bokeh", "name": "Bokeh", "version": "3.0"})
        assert lib.id == "bokeh"
        assert lib.version == "3.0"

    @pytest.mark.asyncio
    async def test_upsert_updates(self, test_session: AsyncSession) -> None:
        repo = LibraryRepository(test_session)
        await repo.create({"id": "matplotlib", "name": "Matplotlib", "version": "3.9"})
        lib = await repo.upsert({"id": "matplotlib", "name": "Matplotlib", "version": "3.10"})
        assert lib.version == "3.10"

    @pytest.mark.asyncio
    async def test_upsert_without_id_raises(self, test_session: AsyncSession) -> None:
        repo = LibraryRepository(test_session)
        with pytest.raises(ValueError, match="must include 'id'"):
            await repo.upsert({"name": "No ID"})


class TestImplRepository:
    """Tests for ImplRepository."""

    @pytest.fixture
    async def setup_data(self, test_session: AsyncSession):
        """Set up test data for impl repository tests."""
        lib = Library(id="matplotlib", name="Matplotlib")
        test_session.add(lib)
        spec = Spec(id="scatter-basic", title="Basic Scatter")
        test_session.add(spec)
        await test_session.commit()
        return test_session

    @pytest.mark.asyncio
    async def test_upsert_creates(self, setup_data: AsyncSession) -> None:
        repo = ImplRepository(setup_data)
        impl = await repo.upsert("scatter-basic", "matplotlib", {"code": "print(1)", "quality_score": 90.0})
        assert impl.spec_id == "scatter-basic"
        assert impl.library_id == "matplotlib"
        assert impl.quality_score == 90.0

    @pytest.mark.asyncio
    async def test_upsert_updates(self, setup_data: AsyncSession) -> None:
        repo = ImplRepository(setup_data)
        await repo.upsert("scatter-basic", "matplotlib", {"code": "v1", "quality_score": 80.0})
        impl = await repo.upsert("scatter-basic", "matplotlib", {"code": "v2", "quality_score": 95.0})
        assert impl.quality_score == 95.0

    @pytest.mark.asyncio
    async def test_get_by_spec(self, setup_data: AsyncSession) -> None:
        repo = ImplRepository(setup_data)
        await repo.upsert("scatter-basic", "matplotlib", {"code": "test"})
        impls = await repo.get_by_spec("scatter-basic")
        assert len(impls) == 1
        assert impls[0].library_id == "matplotlib"

    @pytest.mark.asyncio
    async def test_get_by_library(self, setup_data: AsyncSession) -> None:
        repo = ImplRepository(setup_data)
        await repo.upsert("scatter-basic", "matplotlib", {"code": "test"})
        impls = await repo.get_by_library("matplotlib")
        assert len(impls) == 1
        assert impls[0].spec_id == "scatter-basic"

    @pytest.mark.asyncio
    async def test_get_code(self, setup_data: AsyncSession) -> None:
        repo = ImplRepository(setup_data)
        await repo.upsert("scatter-basic", "matplotlib", {"code": "import matplotlib"})
        impl = await repo.get_code("scatter-basic", "matplotlib")
        assert impl is not None
        assert impl.code == "import matplotlib"

    @pytest.mark.asyncio
    async def test_get_code_not_found(self, setup_data: AsyncSession) -> None:
        repo = ImplRepository(setup_data)
        impl = await repo.get_code("nonexistent", "matplotlib")
        assert impl is None

    @pytest.mark.asyncio
    async def test_get_by_spec_and_library(self, setup_data: AsyncSession) -> None:
        repo = ImplRepository(setup_data)
        await repo.upsert("scatter-basic", "matplotlib", {"code": "test", "review_verdict": "APPROVED"})
        impl = await repo.get_by_spec_and_library("scatter-basic", "matplotlib")
        assert impl is not None
        assert impl.review_verdict == "APPROVED"

    @pytest.mark.asyncio
    async def test_get_by_spec_and_library_not_found(self, setup_data: AsyncSession) -> None:
        repo = ImplRepository(setup_data)
        impl = await repo.get_by_spec_and_library("nonexistent", "matplotlib")
        assert impl is None

    @pytest.mark.asyncio
    async def test_get_total_code_lines(self, setup_data: AsyncSession) -> None:
        repo = ImplRepository(setup_data)
        await repo.upsert("scatter-basic", "matplotlib", {"code": "line1\nline2\nline3"})
        total = await repo.get_total_code_lines()
        assert total == 3

    @pytest.mark.asyncio
    async def test_get_total_code_lines_empty(self, test_session: AsyncSession) -> None:
        repo = ImplRepository(test_session)
        total = await repo.get_total_code_lines()
        assert total == 0

    @pytest.mark.asyncio
    async def test_get_loc_per_impl(self, setup_data: AsyncSession) -> None:
        repo = ImplRepository(setup_data)
        await repo.upsert("scatter-basic", "matplotlib", {"code": "line1\nline2"})
        loc = await repo.get_loc_per_impl()
        assert len(loc) == 1
        assert loc[0] == ("matplotlib", 2)
