"""
Repository classes for database access.

Provides abstraction layer between API and database models.
"""

from typing import Generic, TypeVar

from sqlalchemy import String, cast, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload, undefer

from core.database.models import Impl, Library, Spec


T = TypeVar("T")


# =============================================================================
# Field Validation - Allowed fields for update operations
# =============================================================================
# These sets define which fields can be updated via the update() methods.
# This prevents accidental modification of internal fields like 'id'.

SPEC_UPDATABLE_FIELDS = frozenset(
    {"title", "description", "applications", "data", "notes", "created", "updated", "issue", "suggested", "tags"}
)

LIBRARY_UPDATABLE_FIELDS = frozenset({"name", "version", "documentation_url", "description"})

IMPL_UPDATABLE_FIELDS = frozenset(
    {
        "code",
        # Theme-aware preview variants (Phase B+C schema)
        "preview_url_light",
        "preview_url_dark",
        "preview_html_light",
        "preview_html_dark",
        "python_version",
        "library_version",
        "tested",
        "quality_score",
        "generated_at",
        "updated",
        "generated_by",
        "issue",
        "workflow_run",
        "review_strengths",
        "review_weaknesses",
        "review_image_description",
        "review_criteria_checklist",
        "review_verdict",
        "impl_tags",
    }
)


class BaseRepository(Generic[T]):
    """Base repository with shared CRUD operations.

    Subclasses set ``model`` and ``updatable_fields`` class attributes and
    inherit get_by_id, create, update, and delete.  Entity-specific queries
    (get_all, upsert, …) are defined per-subclass.
    """

    model: type[T]
    updatable_fields: frozenset[str]

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, entity_id: str) -> T | None:
        """Get an entity by its primary-key *id* column."""
        result = await self.session.execute(select(self.model).where(self.model.id == entity_id))
        return result.scalar_one_or_none()

    async def create(self, data: dict) -> T:
        """Create a new entity from a dict of attributes."""
        entity = self.model(**data)
        self.session.add(entity)
        await self.session.commit()
        await self.session.refresh(entity)
        return entity

    def _apply_updates(self, entity: T, data: dict) -> None:
        """Set only the fields present in *updatable_fields*."""
        for key, value in data.items():
            if key in self.updatable_fields:
                setattr(entity, key, value)

    async def update(self, entity_id: str, data: dict) -> T | None:
        """Update an existing entity. Returns None if not found."""
        entity = await self.get_by_id(entity_id)
        if not entity:
            return None
        self._apply_updates(entity, data)
        await self.session.commit()
        await self.session.refresh(entity)
        return entity

    async def delete(self, entity_id: str) -> bool:
        """Delete an entity by ID. Returns True if deleted, False if not found."""
        entity = await self.get_by_id(entity_id)
        if not entity:
            return False
        await self.session.delete(entity)
        await self.session.commit()
        return True


class SpecRepository(BaseRepository[Spec]):
    """Repository for Spec operations."""

    model = Spec
    updatable_fields = SPEC_UPDATABLE_FIELDS

    async def get_by_id(self, spec_id: str) -> Spec | None:
        """Get a spec by ID with implementations and library info.

        Loads review_image_description and review_criteria_checklist (needed for detail display).
        Code and tested remain deferred — use /specs/{id}/{lib}/code for code.
        """
        result = await self.session.execute(
            select(Spec)
            .where(Spec.id == spec_id)
            .options(
                selectinload(Spec.impls).selectinload(Impl.library),
                selectinload(Spec.impls).undefer(Impl.review_image_description).undefer(Impl.review_criteria_checklist),
            )
        )
        return result.scalar_one_or_none()

    async def get_by_id_with_code(self, spec_id: str) -> Spec | None:
        """Like get_by_id, but additionally eager-loads Impl.code.

        Use this when the caller needs `impl.code` on every implementation
        (e.g. the MCP `get_specification` tool). Touching `impl.code` after
        `get_by_id` raises MissingGreenlet on AsyncSession because the column
        is deferred and the lazy-load would emit a sync SELECT.
        """
        impls_loader = selectinload(Spec.impls)
        result = await self.session.execute(
            select(Spec)
            .where(Spec.id == spec_id)
            .options(
                impls_loader.selectinload(Impl.library),
                impls_loader.undefer(Impl.review_image_description)
                .undefer(Impl.review_criteria_checklist)
                .undefer(Impl.code),
            )
        )
        return result.scalar_one_or_none()

    async def get_all(self) -> list[Spec]:
        """Get all specs with their implementations and library.

        Lightweight: `Impl.code` stays deferred. Most callers (specs/plots/
        seo/insights/stats/debug routers) only need the listing surface;
        eager-loading every code blob would be a multi-MB regression.
        Callers that iterate `spec.impls` and read `impl.code` on an async
        session must use `get_all_with_code()` to avoid MissingGreenlet.
        """
        impls_loader = selectinload(Spec.impls)
        result = await self.session.execute(select(Spec).options(impls_loader.selectinload(Impl.library)))
        return list(result.scalars().all())

    async def get_all_with_code(self) -> list[Spec]:
        """Get all specs with implementations (code + library eager-loaded).

        Use this for paths that read `impl.code` on every implementation —
        currently only the MCP `list_specs` and `search_specs` tools.
        Touching `impl.code` after `get_all()` raises MissingGreenlet on
        AsyncSession because the column is deferred and the lazy-load would
        emit a sync SELECT.
        """
        impls_loader = selectinload(Spec.impls)
        result = await self.session.execute(
            select(Spec).options(impls_loader.selectinload(Impl.library), impls_loader.undefer(Impl.code))
        )
        return list(result.scalars().all())

    async def get_ids(self) -> list[str]:
        """Get all spec IDs."""
        result = await self.session.execute(select(Spec.id).order_by(Spec.id))
        return [row[0] for row in result.fetchall()]

    async def search_by_tags(self, tags: list[str]) -> list[Spec]:
        """Search specs by tags. Eager-loads impls + library + code.

        impl.library and impl.code are both required by MCP
        search_specs_by_tags (server.py iterates impls and reads both); not
        eager-loading them on an async session raises MissingGreenlet.
        """
        filters = []
        for tag in tags:
            filters.append(cast(Spec.tags, String).contains(f'"{tag}"'))

        impls_loader = selectinload(Spec.impls)
        result = await self.session.execute(
            select(Spec)
            .where(or_(*filters))
            .options(impls_loader.selectinload(Impl.library), impls_loader.undefer(Impl.code))
        )
        return list(result.scalars().all())

    async def upsert(self, spec_data: dict) -> Spec:
        """Create or update a spec by ID."""
        spec_id = spec_data.get("id")
        if not spec_id:
            raise ValueError("spec_data must include 'id' field")

        existing = await self.get_by_id(spec_id)
        if existing:
            self._apply_updates(existing, spec_data)
            await self.session.commit()
            await self.session.refresh(existing)
            return existing
        return await self.create(spec_data)


class LibraryRepository(BaseRepository[Library]):
    """Repository for Library operations."""

    model = Library
    updatable_fields = LIBRARY_UPDATABLE_FIELDS

    async def get_all(self) -> list[Library]:
        """Get all libraries ordered by name."""
        query = select(Library).order_by(Library.name)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def upsert(self, library_data: dict) -> Library:
        """Create or update a library by ID."""
        library_id = library_data.get("id")
        if not library_id:
            raise ValueError("library_data must include 'id' field")

        existing = await self.get_by_id(library_id)
        if existing:
            self._apply_updates(existing, library_data)
            await self.session.commit()
            await self.session.refresh(existing)
            return existing
        return await self.create(library_data)


class ImplRepository(BaseRepository[Impl]):
    """Repository for Impl operations."""

    model = Impl
    updatable_fields = IMPL_UPDATABLE_FIELDS

    async def get_total_code_lines(self) -> int:
        """Count total lines of code across all implementations (lightweight, no code loading)."""
        result = await self.session.execute(
            select(func.sum(func.length(Impl.code) - func.length(func.replace(Impl.code, "\n", "")) + 1)).where(
                Impl.code.isnot(None)
            )
        )
        return result.scalar_one() or 0

    async def get_loc_per_impl(self) -> list[tuple[str, int]]:
        """Get (library_id, line_count) for each implementation (lightweight, no code loading)."""
        loc_expr = func.length(Impl.code) - func.length(func.replace(Impl.code, "\n", "")) + 1
        result = await self.session.execute(select(Impl.library_id, loc_expr).where(Impl.code.isnot(None)))
        return [(row[0], row[1]) for row in result.all()]

    async def get_by_spec(self, spec_id: str) -> list[Impl]:
        """Get all implementations for a spec."""
        result = await self.session.execute(
            select(Impl).where(Impl.spec_id == spec_id).options(selectinload(Impl.library)).order_by(Impl.library_id)
        )
        return list(result.scalars().all())

    async def get_by_library(self, library_id: str) -> list[Impl]:
        """Get all implementations for a library."""
        result = await self.session.execute(
            select(Impl).where(Impl.library_id == library_id).options(selectinload(Impl.spec)).order_by(Impl.spec_id)
        )
        return list(result.scalars().all())

    async def get_code(self, spec_id: str, library_id: str, language_id: str = "python") -> Impl | None:
        """Get a specific implementation with only the code field undeferred."""
        result = await self.session.execute(
            select(Impl)
            .where(Impl.spec_id == spec_id, Impl.library_id == library_id, Impl.language_id == language_id)
            .options(undefer(Impl.code))
        )
        return result.scalar_one_or_none()

    async def get_by_spec_and_library(self, spec_id: str, library_id: str, language_id: str = "python") -> Impl | None:
        """Get a specific implementation by spec + language + library (includes all deferred fields).

        Defaults to language_id="python" so existing callers keep working. Pass ``language_id``
        explicitly to disambiguate when multiple languages exist for the same (spec, library).
        """
        # selectinload(Impl.library) — MCP get_implementation reads impl.library
        # on an async session; without eager-load it raises MissingGreenlet.
        result = await self.session.execute(
            select(Impl)
            .where(Impl.spec_id == spec_id, Impl.library_id == library_id, Impl.language_id == language_id)
            .options(
                selectinload(Impl.library),
                undefer(Impl.code),
                undefer(Impl.review_image_description),
                undefer(Impl.review_criteria_checklist),
            )
        )
        return result.scalar_one_or_none()

    async def upsert(self, spec_id: str, library_id: str, impl_data: dict, language_id: str = "python") -> Impl:
        """Create or update an implementation by (spec_id, language_id, library_id)."""
        existing = await self.get_by_spec_and_library(spec_id, library_id, language_id)
        if existing:
            self._apply_updates(existing, impl_data)
            await self.session.commit()
            await self.session.refresh(existing)
            return existing
        full_data = {**impl_data, "spec_id": spec_id, "library_id": library_id, "language_id": language_id}
        return await self.create(full_data)
