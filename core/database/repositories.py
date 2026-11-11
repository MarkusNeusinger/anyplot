"""
Repository classes for database access.

Provides abstraction layer between API and database models.
"""

from datetime import date, datetime, timezone
from typing import Any, Generic, TypeVar

from sqlalchemy import ColumnElement, String, and_, case, cast, func, or_, select, text, type_coerce, update
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlalchemy.dialects.postgresql import insert as postgresql_insert
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload, undefer

from core.constants import LIBRARY_LANGUAGES
from core.database.models import AgentFeedback, Feedback, Impl, Language, Library, LinkShare, Spec
from core.plot_votes import PLOT_VOTE_REACTIONS, VOTE_SORTS, naive_utc


T = TypeVar("T")

# Spec-level tag categories — the keys of the `tags` JSON object
# ({plot_type, data_type, domain, features}, see docs/reference/tagging-system.md).
SPEC_TAG_CATEGORIES = ("plot_type", "data_type", "domain", "features")


def _spec_category_filter(category: str, tags: list[str], dialect_name: str) -> ColumnElement[bool]:
    """Build one WHERE predicate: the spec's *category* list contains any of *tags*.

    On PostgreSQL each tag is a JSONB containment test
    (``tags @> '{"<category>": ["<tag>"]}'``) with `type_coerce`, not `cast`,
    so the left side stays the bare ``tags`` column and the ``ix_specs_tags``
    GIN index applies. Other dialects (SQLite in tests) extract the category's
    array as text with ``json_extract`` and LIKE-match the quoted tag, with
    LIKE metacharacters escaped (an unescaped LIKE once treated ``%`` and
    ``_`` in tag values as wildcards).
    """
    if category not in SPEC_TAG_CATEGORIES:
        raise ValueError(f"Unknown spec tag category '{category}'; expected one of {SPEC_TAG_CATEGORIES}")
    predicates: list[ColumnElement[bool]] = []
    if dialect_name == "postgresql":
        predicates.extend(type_coerce(Spec.tags, JSONB).contains({category: [tag]}) for tag in tags)
    else:
        category_json = cast(func.json_extract(Spec.tags, f"$.{category}"), String)
        predicates.extend(category_json.contains(f'"{tag}"', autoescape=True) for tag in tags)
    return or_(*predicates)


def _same_language(language: str) -> ColumnElement[bool]:
    """A feedback row in `language`, or one that names none: library ids are unique across languages, so a plot vote
    without a language is on the same image (the audit selector gives it the library's language as well)."""
    return or_(Feedback.language == language, Feedback.language.is_(None))


# =============================================================================
# Field Validation - Allowed fields for update operations
# =============================================================================
# These sets define which fields can be updated via the update() methods.
# This prevents accidental modification of internal fields like 'id'.

SPEC_UPDATABLE_FIELDS = frozenset(
    {"title", "description", "applications", "data", "notes", "created", "updated", "issue", "suggested", "tags"}
)

LIBRARY_UPDATABLE_FIELDS = frozenset({"name", "version", "documentation_url", "description"})
LANGUAGE_UPDATABLE_FIELDS = frozenset({"name", "file_extension", "runtime_version", "documentation_url", "description"})

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

# The triage state of an agent feedback case; every other column copies its manifest.
AGENT_FEEDBACK_UPDATABLE_FIELDS = frozenset({"status", "tags", "expected", "promoted_at"})


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
        Callers that need code must fetch it explicitly (`ImplRepository.get_code`
        / `get_by_library_with_code`) or code presence via
        `ImplRepository.get_ids_with_code()` — touching `impl.code` on these
        results raises MissingGreenlet on AsyncSession.
        """
        impls_loader = selectinload(Spec.impls)
        result = await self.session.execute(select(Spec).options(impls_loader.selectinload(Impl.library)))
        return list(result.scalars().all())

    async def get_ids(self) -> list[str]:
        """Get all spec IDs."""
        result = await self.session.execute(select(Spec.id).order_by(Spec.id))
        return [row[0] for row in result.fetchall()]

    async def count_with_impls(self) -> int:
        """Count specs that have at least one implementation.

        Lightweight aggregate — avoids loading every spec + impl row just to
        compute the homepage `specifications` number (used by /stats).
        """
        result = await self.session.execute(select(func.count(func.distinct(Impl.spec_id))).select_from(Impl))
        return result.scalar_one() or 0

    async def search_by_tag_filters(self, filters: dict[str, list[str]]) -> list[Spec]:
        """Search specs by spec-level tag filters: OR within a category, AND across categories.

        *filters* maps a category (``plot_type``, ``data_type``, ``domain``,
        ``features``) to its accepted values. A spec matches when EVERY listed
        category contains at least one of its values, and a value only counts
        in the category it was passed in — ``{"plot_type": ["finance"]}`` does
        not match a spec whose *domain* is finance. Categories with an empty
        list are ignored, and no filters at all returns every spec.

        This is what MCP `search_specs_by_tags` documents; it replaced a
        flatten-and-OR search that matched any value in any category and so
        returned the union instead of the intersection. Eager-loads impls +
        library (server.py reads `impl.library.id` while filtering, and an
        async session raises MissingGreenlet on a lazy load) and keeps
        `Impl.code` deferred — callers only need code *presence*, resolved
        separately via `ImplRepository.get_ids_with_code()`.
        """
        dialect_name = self.session.get_bind().dialect.name
        predicates = [
            _spec_category_filter(category, values, dialect_name) for category, values in filters.items() if values
        ]
        query = select(Spec).options(selectinload(Spec.impls).selectinload(Impl.library))
        if predicates:
            query = query.where(and_(*predicates))
        result = await self.session.execute(query)
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

    async def count_with_languages(self) -> tuple[int, int]:
        """Return ``(library_count, distinct_language_count)`` in one round-trip.

        Used by /stats to avoid loading every Library row just to take ``len()``
        and ``len({lib.language_id})`` over the result set.
        """
        result = await self.session.execute(
            select(func.count(Library.id), func.count(func.distinct(Library.language_id)))
        )
        row = result.one()
        return int(row[0] or 0), int(row[1] or 0)

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


class LanguageRepository(BaseRepository[Language]):
    """Repository for Language operations."""

    model = Language
    updatable_fields = LANGUAGE_UPDATABLE_FIELDS

    async def get_all(self) -> list[Language]:
        """Get all languages ordered by name."""
        query = select(Language).order_by(Language.name)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def upsert(self, language_data: dict) -> Language:
        """Create or update a language by ID."""
        language_id = language_data.get("id")
        if not language_id:
            raise ValueError("language_data must include 'id' field")

        existing = await self.get_by_id(language_id)
        if existing:
            self._apply_updates(existing, language_data)
            await self.session.commit()
            await self.session.refresh(existing)
            return existing
        return await self.create(language_data)


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

    async def count_all(self) -> int:
        """Count all implementations (lightweight aggregate, no row loading)."""
        result = await self.session.execute(select(func.count(Impl.id)))
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

    async def get_by_library_with_code(self, library_id: str) -> list[Impl]:
        """Get all implementations for one library with `code` undeferred.

        Serves /libraries/{id}/images, which renders the code of a single
        library — undeferring code on an all-specs query would drag every
        other library's multi-MB blobs along.
        """
        result = await self.session.execute(
            select(Impl).where(Impl.library_id == library_id).options(undefer(Impl.code)).order_by(Impl.spec_id)
        )
        return list(result.scalars().all())

    async def get_ids_with_code(self) -> set[str]:
        """IDs of implementations whose `code` column is non-NULL.

        Lightweight presence probe (id column only, code is never detoasted)
        for listing surfaces that count or filter "real" implementations —
        MCP list_specs / search_specs_by_tags — without undeferring blobs.
        """
        result = await self.session.execute(select(Impl.id).where(Impl.code.isnot(None)))
        return {row[0] for row in result.all()}

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


class FeedbackRepository(BaseRepository[Feedback]):
    """Repository for in-app feedback entries (issue #5662). Message/reaction/contact
    are immutable once written; only `status` can change as admins triage entries,
    and `ip_hash` is cleared once its rate-limit window has passed
    (`clear_ip_hashes`).
    """

    model = Feedback
    updatable_fields = frozenset({"status"})

    async def clear_ip_hashes(self, prefix: str, before: datetime) -> int:
        """Null the `ip_hash` of every row created before `before` whose hash starts with `prefix`; the count.

        The feedback router stores a per-process salted hash (`api/routers/feedback.py`
        `_hash_ip`) only for its rate-limit and duplicate windows and clears it here once
        they have passed. `prefix` keeps the statement to the hashes of that scheme; the
        unsalted hashes of older rows were cleared once by hand on 2026-11-02 after a
        snapshot, so no migration is needed.
        `before` must be tz-naive UTC, like `feedback.created_at`."""
        result = await self.session.execute(
            update(Feedback)
            .where(Feedback.ip_hash.startswith(prefix, autoescape=True), Feedback.created_at < before)
            .values(ip_hash=None)
        )
        await self.session.commit()
        return int(getattr(result, "rowcount", 0) or 0)

    async def count_recent_by_ip(self, ip_hash: str, since: datetime, messages_only: bool = False) -> int:
        """Count entries from this IP hash since the given UTC datetime — used for rate limiting.
        `since` must be tz-naive UTC because feedback.created_at is TIMESTAMP WITHOUT TIME ZONE.
        With `messages_only`, reaction-only rows are left out so a handful of 👍/👎 taps
        never blocks the free-text form."""
        stmt = select(func.count(Feedback.id)).where(Feedback.ip_hash == ip_hash, Feedback.created_at >= since)
        if messages_only:
            stmt = stmt.where(Feedback.message.is_not(None))
        result = await self.session.execute(stmt)
        return result.scalar_one() or 0

    async def version_start(self, spec_id: str, library_id: str, language: str | None = None) -> datetime | None:
        """When the implementation's current version began: its `impls.updated`, naive UTC (`core.plot_votes`).

        None when the implementation has no `updated` or is not in the table: then it has one version, and every
        vote is on it. Without `language`, any language's row of the library counts; library ids are unique across
        languages, and the latest `updated` is taken should two rows ever share one.
        """
        stmt = select(func.max(Impl.updated)).where(Impl.spec_id == spec_id, Impl.library_id == library_id)
        if language is not None:
            stmt = stmt.where(Impl.language_id == language)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def has_plot_vote(
        self, session_id: str, spec_id: str, library_id: str, language: str | None, *, since: datetime | None = None
    ) -> bool:
        """True iff this session already left a 👍/👎 on this implementation at `since` or later.

        One vote per image per session: the router passes the current version's start (`version_start`) as
        `since` and drops a later vote from the same session on that version silently, so a visitor cannot flip
        up/down at will, and may rate the next version once. Without `since`, every version counts. A row
        without a language is on the same image (`_same_language`).
        """
        stmt = select(func.count(Feedback.id)).where(
            Feedback.session_id == session_id,
            Feedback.spec_id == spec_id,
            Feedback.library_id == library_id,
            Feedback.reaction.in_(PLOT_VOTE_REACTIONS),
        )
        if language is not None:
            stmt = stmt.where(_same_language(language))
        if since is not None:
            stmt = stmt.where(Feedback.created_at >= naive_utc(since))
        result = await self.session.execute(stmt)
        return (result.scalar_one() or 0) > 0

    async def reaction_counts(
        self,
        spec_id: str,
        library_id: str,
        language: str | None = None,
        *,
        since: datetime | None = None,
        before: datetime | None = None,
    ) -> dict[str, int]:
        """Count 👍/👎 for one implementation — `{"thumbs_up": n, "thumbs_down": n}`.

        A vote belongs to the version of the image it was cast on (`core.plot_votes`). Pass the current
        version's start (`version_start`) as `since` for that version's votes, or as `before` for those of every
        earlier version; with neither, every vote ever cast counts.

        The router refuses a second vote per session and version, but the table is append-only and rows from
        before that guard (or without it) may repeat, so within the window only the newest row per session
        counts. A session that rated an earlier version and the current one counts once on each side. Rows
        without a session id cannot be de-duplicated and count once each. `language` narrows the lookup when the
        same library id exists in more than one language; a row without a language stays in (`_same_language`).
        """
        filters = [
            Feedback.spec_id == spec_id,
            Feedback.library_id == library_id,
            Feedback.reaction.in_(PLOT_VOTE_REACTIONS),
        ]
        if language is not None:
            filters.append(_same_language(language))
        if since is not None:
            filters.append(Feedback.created_at >= naive_utc(since))
        if before is not None:
            filters.append(Feedback.created_at < naive_utc(before))
        # One partition per session; a session-less row is its own partition
        # (the primary key stands in for the missing session id). The id is
        # also the tiebreaker, so two rows sharing a created_at rank the same
        # way on every run.
        partition = func.coalesce(Feedback.session_id, cast(Feedback.id, String))
        ranked = (
            select(
                Feedback.reaction.label("reaction"),
                func.row_number()
                .over(partition_by=partition, order_by=(Feedback.created_at.desc(), Feedback.id.desc()))
                .label("rank"),
            )
            .where(*filters)
            .subquery()
        )
        result = await self.session.execute(
            select(ranked.c.reaction, func.count().label("count")).where(ranked.c.rank == 1).group_by(ranked.c.reaction)
        )
        counts = dict.fromkeys(PLOT_VOTE_REACTIONS, 0)
        for row in result.all():
            counts[row.reaction] = row.count
        return counts

    async def list_recent(self, limit: int = 100) -> list[Feedback]:
        """List most recent entries first — for admin/triage tooling."""
        result = await self.session.execute(select(Feedback).order_by(Feedback.created_at.desc()).limit(limit))
        return list(result.scalars().all())

    async def vote_counts_by_implementation(self, sort: str = "thumbs_down", limit: int = 25) -> list[dict]:
        """The plots with the most 👍/👎, one entry per implementation (spec × language × library).

        Used by the debug dashboard's vote list. Each entry carries the current version's `thumbs_up` and
        `thumbs_down` and the earlier versions' `earlier_thumbs_up` and `earlier_thumbs_down` (`core.plot_votes`),
        counted as `reaction_counts(…, since=…)` and `(…, before=…)` count them: on each side the newest vote per
        session, a session-less row once. `sort` (`VOTE_SORTS`) ranks by the current version's thumbs down, thumbs
        up or both together; the earlier versions' count of the same kind breaks a tie, then the newest vote.
        Page reactions of the floating widget name no implementation and are not in the list. Counts only: no
        message, contact or session id leaves the query.
        """
        if sort not in VOTE_SORTS:
            raise ValueError(f"sort must be one of {VOTE_SORTS}")
        version_start = (
            select(func.max(Impl.updated))
            .where(
                Impl.spec_id == Feedback.spec_id,
                Impl.library_id == Feedback.library_id,
                or_(Feedback.language.is_(None), Impl.language_id == Feedback.language),
            )
            .correlate(Feedback)
            .scalar_subquery()
        )
        votes = (
            select(
                Feedback.id.label("id"),
                Feedback.session_id.label("session_id"),
                Feedback.spec_id.label("spec_id"),
                Feedback.library_id.label("library_id"),
                Feedback.language.label("language"),
                Feedback.reaction.label("reaction"),
                Feedback.created_at.label("created_at"),
                # A NULL start (no implementation, or no `updated`) compares to NULL and lands in the else branch.
                case((Feedback.created_at < version_start, 1), else_=0).label("earlier"),
            )
            .where(
                Feedback.reaction.in_(PLOT_VOTE_REACTIONS),
                Feedback.spec_id.is_not(None),
                Feedback.library_id.is_not(None),
            )
            .subquery()
        )
        # One partition per session, image and side of the version start; the language stays out, as in
        # `reaction_counts`, because library ids are unique across languages.
        voter = func.coalesce(votes.c.session_id, cast(votes.c.id, String))
        ranked = select(
            votes,
            func.row_number()
            .over(
                partition_by=(voter, votes.c.spec_id, votes.c.library_id, votes.c.earlier),
                order_by=(votes.c.created_at.desc(), votes.c.id.desc()),
            )
            .label("rank"),
        ).subquery()

        def tally(reaction: str, earlier: int) -> ColumnElement[int]:
            hit = and_(ranked.c.reaction == reaction, ranked.c.earlier == earlier)
            return func.sum(case((hit, 1), else_=0))

        up, down = tally("thumbs_up", 0), tally("thumbs_down", 0)
        earlier_up, earlier_down = tally("thumbs_up", 1), tally("thumbs_down", 1)
        last_vote = func.max(ranked.c.created_at)
        keys = {
            "thumbs_down": (down, earlier_down),
            "thumbs_up": (up, earlier_up),
            "total": (up + down, earlier_up + earlier_down),
        }[sort]
        result = await self.session.execute(
            select(
                ranked.c.spec_id,
                ranked.c.library_id,
                func.max(ranked.c.language).label("language"),
                up.label("thumbs_up"),
                down.label("thumbs_down"),
                earlier_up.label("earlier_thumbs_up"),
                earlier_down.label("earlier_thumbs_down"),
                last_vote.label("last_vote"),
            )
            .where(ranked.c.rank == 1)
            .group_by(ranked.c.spec_id, ranked.c.library_id)
            .order_by(
                keys[0].desc(), keys[1].desc(), last_vote.desc(), ranked.c.spec_id.asc(), ranked.c.library_id.asc()
            )
            .limit(limit)
        )
        entries = []
        for row in result.all():
            language = row.language or LIBRARY_LANGUAGES.get(row.library_id)
            entries.append(
                {
                    "spec_id": row.spec_id,
                    "language": language,
                    "library_id": row.library_id,
                    "path": f"/{row.spec_id}/{language}/{row.library_id}" if language else f"/{row.spec_id}",
                    "thumbs_up": int(row.thumbs_up or 0),
                    "thumbs_down": int(row.thumbs_down or 0),
                    "earlier_thumbs_up": int(row.earlier_thumbs_up or 0),
                    "earlier_thumbs_down": int(row.earlier_thumbs_down or 0),
                    # created_at is TIMESTAMP WITHOUT TIME ZONE in UTC — tag it, so the browser doesn't read the
                    # naive ISO as local time.
                    "last_vote": row.last_vote.replace(tzinfo=timezone.utc).isoformat() if row.last_vote else None,
                }
            )
        return entries

    async def has_recent_duplicate(
        self, message: str, ip_hash: str | None, session_id: str | None, since: datetime
    ) -> bool:
        """True iff the same message text was submitted since `since` AND matches
        either the same IP hash or the same session id. The router uses this for
        silent spam-drop so bots can't tell the difference between accepted and
        suppressed submissions."""
        identity_filters = []
        if ip_hash:
            identity_filters.append(Feedback.ip_hash == ip_hash)
        if session_id:
            identity_filters.append(Feedback.session_id == session_id)
        if not identity_filters:
            return False
        result = await self.session.execute(
            select(func.count(Feedback.id)).where(
                Feedback.message == message, Feedback.created_at >= since, or_(*identity_filters)
            )
        )
        return (result.scalar_one() or 0) > 0

    async def list_with_message(self, status: str | tuple[str, ...] | None = None, limit: int = 50) -> list[Feedback]:
        """List entries that carry a free-text message, filtered optionally by status.

        `status` may be a single value, a tuple of values (matched with IN), or None
        for all statuses. The router uses the tuple form for the "open" pseudo-filter
        on /debug.
        """
        stmt = select(Feedback).where(Feedback.message.is_not(None))
        if isinstance(status, str):
            stmt = stmt.where(Feedback.status == status)
        elif status:
            stmt = stmt.where(Feedback.status.in_(status))
        stmt = stmt.order_by(Feedback.created_at.desc()).limit(limit)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def update_status(self, entry_id: str, new_status: str) -> Feedback | None:
        """Update only the triage status of one entry. Returns None if not found."""
        return await self.update(entry_id, {"status": new_status})


class AgentFeedbackRepository(BaseRepository[AgentFeedback]):
    """Rows of the agent chat's feedback cases; `create_case` applies the supersede rule in one commit.

    `update` changes only the triage state (`AGENT_FEEDBACK_UPDATABLE_FIELDS`); the columns a
    manifest fills are written once, and `superseded_by` only by `create_case`.
    """

    model = AgentFeedback
    updatable_fields = AGENT_FEEDBACK_UPDATABLE_FIELDS

    async def create_case(self, row: dict[str, Any]) -> AgentFeedback:
        """Insert the row and set both supersede links in ONE commit.

        Backwards: when the row names an earlier case in `replaces`, that row (same
        session hash and version, not yet superseded) gets `superseded_by = row.id`.
        Forwards: when a row already names this id in `replaces` (a successor the route
        inserted before the backfill reached this orphan), this row is inserted with
        `superseded_by = <that successor>`. On the route's path the forward lookup is a
        guaranteed no-op (the id was minted in this request), one SELECT. One commit, so
        an interrupted backfill never leaves a row half-linked: either the row with both
        links exists, or nothing does.

        On PostgreSQL the two directions are also serialized per session hash and
        version with a transaction-scoped advisory lock, released by the commit: without
        it, a backfill inserting an orphan A and a live request inserting its successor B
        at the same moment could each look up the other before either row is visible and
        commit unlinked. The SQLite engine of the tests runs one connection and skips it.
        """
        if self.session.get_bind().dialect.name == "postgresql":
            await self.session.execute(
                text("SELECT pg_advisory_xact_lock(hashtext(:key))"),
                {"key": f"{row['session_hash']}:{row['result_version']}"},
            )
        successor = await self.successor_of(row["id"], row["session_hash"], row["result_version"])
        entity = AgentFeedback(**row, superseded_by=successor)
        self.session.add(entity)
        if row.get("replaces"):
            await self.supersede(
                row["replaces"], by=entity.id, session_hash=row["session_hash"], result_version=row["result_version"]
            )
        await self.session.commit()
        await self.session.refresh(entity)
        return entity

    async def supersede(self, earlier_id: str, *, by: str, session_hash: str, result_version: int) -> bool:
        """Mark `earlier_id` superseded by `by` when it exists with that session hash and version and is
        not yet superseded; True when a row changed. No commit: `create_case` commits both links together.
        """
        stmt = (
            update(AgentFeedback)
            .where(
                AgentFeedback.id == earlier_id,
                AgentFeedback.session_hash == session_hash,
                AgentFeedback.result_version == result_version,
                AgentFeedback.superseded_by.is_(None),
            )
            .values(superseded_by=by)
        )
        result = await self.session.execute(stmt)
        return result.rowcount == 1

    async def successor_of(self, case_id: str, session_hash: str, result_version: int) -> str | None:
        """The oldest row that names `case_id` in `replaces` with the same session hash and version
        (`create_case`'s forward link), or None.
        """
        result = await self.session.execute(
            select(AgentFeedback.id)
            .where(
                AgentFeedback.replaces == case_id,
                AgentFeedback.session_hash == session_hash,
                AgentFeedback.result_version == result_version,
            )
            .order_by(AgentFeedback.id)
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def list_cases(
        self,
        *,
        reaction: str | None = None,
        status: str | tuple[str, ...] | None = None,
        spec_id: str | None = None,
        library_id: str | None = None,
        model_version: str | None = None,
        tag: str | None = None,
        include_superseded: bool = False,
        before: str | None = None,
        limit: int = 50,
    ) -> list[AgentFeedback]:
        """At most `limit` rows, newest first (`id DESC`: case ids sort by time).

        `status` may be one value or a tuple matched with IN (the route's `open`
        pseudo-filter). Superseded rows are left out unless `include_superseded`.
        `before` is an exclusive id cursor: only rows with a smaller id. The route asks
        for one row more than it shows, so it can tell whether a further page exists.
        """
        stmt = select(AgentFeedback)
        if reaction is not None:
            stmt = stmt.where(AgentFeedback.reaction == reaction)
        if isinstance(status, str):
            stmt = stmt.where(AgentFeedback.status == status)
        elif status:
            stmt = stmt.where(AgentFeedback.status.in_(status))
        if spec_id is not None:
            stmt = stmt.where(AgentFeedback.spec_id == spec_id)
        if library_id is not None:
            stmt = stmt.where(AgentFeedback.library_id == library_id)
        if model_version is not None:
            stmt = stmt.where(AgentFeedback.model_version == model_version)
        if tag is not None:
            stmt = stmt.where(self._has_tag(tag))
        if not include_superseded:
            stmt = stmt.where(AgentFeedback.superseded_by.is_(None))
        if before is not None:
            stmt = stmt.where(AgentFeedback.id < before)
        result = await self.session.execute(stmt.order_by(AgentFeedback.id.desc()).limit(limit))
        return list(result.scalars().all())

    def _has_tag(self, tag: str) -> ColumnElement[bool]:
        """The row's `tags` hold `tag`.

        On PostgreSQL an array containment (``tags @> ARRAY[tag]``) through `type_coerce`,
        so the ``ix_agent_feedback_tags`` GIN index applies; a plain ``contains`` on the
        `StringArray` column would compile to a LIKE against the array. Other dialects
        (SQLite in tests) store the list as JSON text, matched with LIKE on the quoted tag.
        """
        if self.session.get_bind().dialect.name == "postgresql":
            return type_coerce(AgentFeedback.tags, ARRAY(String)).contains([tag])
        return cast(AgentFeedback.tags, String).contains(f'"{tag}"', autoescape=True)

    async def siblings(self, session_hash: str, result_version: int, exclude_id: str) -> list[str]:
        """Ids of the other rows of the same session hash and version, oldest first (the detail's duplicate hint)."""
        result = await self.session.execute(
            select(AgentFeedback.id)
            .where(
                AgentFeedback.session_hash == session_hash,
                AgentFeedback.result_version == result_version,
                AgentFeedback.id != exclude_id,
            )
            .order_by(AgentFeedback.id)
        )
        return list(result.scalars().all())

    async def list_all(self) -> list[AgentFeedback]:
        """Every row, oldest first (the sync CLI; the table is small)."""
        result = await self.session.execute(select(AgentFeedback).order_by(AgentFeedback.id))
        return list(result.scalars().all())


class LinkShareRepository:
    """The share counters: one upsert per preview fetch, and the sums the tile reads.

    No `BaseRepository`: a row has no id of its own, its seven key columns are the key.
    """

    def __init__(self, session: AsyncSession):
        self.session = session

    async def count(
        self,
        *,
        day: date,
        platform: str,
        verified: bool,
        page: str,
        spec_id: str = "",
        language: str = "",
        library_id: str = "",
    ) -> None:
        """Add one fetch to its counter, in one statement; the caller commits.

        An `INSERT ... ON CONFLICT DO UPDATE` on the primary key, so two fetches
        of the same page in the same instant both count: a read followed by a
        write would lose one of them. PostgreSQL and the SQLite of the tests
        spell it the same way, each through its own dialect's `insert`.
        """
        insert = postgresql_insert if self.session.get_bind().dialect.name == "postgresql" else sqlite_insert
        statement = insert(LinkShare).values(
            day=day,
            platform=platform,
            verified=verified,
            page=page,
            spec_id=spec_id,
            language=language,
            library_id=library_id,
            fetches=1,
        )
        await self.session.execute(
            statement.on_conflict_do_update(
                index_elements=[
                    LinkShare.day,
                    LinkShare.platform,
                    LinkShare.verified,
                    LinkShare.page,
                    LinkShare.spec_id,
                    LinkShare.language,
                    LinkShare.library_id,
                ],
                set_={"fetches": LinkShare.fetches + 1},
            )
        )

    async def by_day_and_platform(self, since: date, until: date) -> list[tuple[date, str, bool, int]]:
        """The fetches of the days *since* to *until*, both included, oldest first.

        One entry per day, platform and verdict: (day, platform, verified, fetches).
        """
        result = await self.session.execute(
            select(LinkShare.day, LinkShare.platform, LinkShare.verified, func.sum(LinkShare.fetches))
            .where(LinkShare.day >= since, LinkShare.day <= until)
            .group_by(LinkShare.day, LinkShare.platform, LinkShare.verified)
            .order_by(LinkShare.day, LinkShare.platform, LinkShare.verified)
        )
        return [(day, platform, bool(verified), int(fetches)) for day, platform, verified, fetches in result.all()]

    async def top_plots(
        self, since: date, until: date, *, without_platform: str, limit: int
    ) -> list[tuple[str, str, str, int]]:
        """The most shared plot pages of the days *since* to *until*: (spec_id, language, library_id, fetches).

        The same days as `by_day_and_platform`, so the list and the daily sums
        describe one window. A spec's hub and each of its implementation pages
        are entries of their own (`language` and `library_id` are empty for
        the hub). Fetches of *without_platform* are left out. Ties go by id, so
        the order is stable.
        """
        fetches = func.sum(LinkShare.fetches)
        result = await self.session.execute(
            select(LinkShare.spec_id, LinkShare.language, LinkShare.library_id, fetches)
            .where(
                LinkShare.day >= since,
                LinkShare.day <= until,
                LinkShare.platform != without_platform,
                LinkShare.spec_id != "",
            )
            .group_by(LinkShare.spec_id, LinkShare.language, LinkShare.library_id)
            .order_by(fetches.desc(), LinkShare.spec_id, LinkShare.language, LinkShare.library_id)
            .limit(limit)
        )
        return [(spec_id, language, library_id, int(total)) for spec_id, language, library_id, total in result.all()]
