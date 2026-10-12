"""
Integration tests for repository classes.

Tests actual database operations with SQLite in-memory database.
Tests Repository layer interaction with database (no HTTP layer).
"""

from datetime import datetime

import pytest

from core.database.repositories import (
    AgentFeedbackRepository,
    FeedbackRepository,
    ImplRepository,
    LibraryRepository,
    SpecRepository,
)


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

    async def test_count_with_impls(self, test_db_with_data):
        """Aggregate count of specs that have at least one impl — used by /stats."""
        repo = SpecRepository(test_db_with_data)
        count = await repo.count_with_impls()
        # Both fixture specs (scatter-basic, bar-grouped) have impls.
        assert count == 2

    async def test_count_with_impls_empty(self, test_session):
        """Empty database returns 0, not None — caller adds to other counts."""
        repo = SpecRepository(test_session)
        assert await repo.count_with_impls() == 0

    async def test_search_by_tag_filters(self, test_db_with_data):
        """AND across categories, OR within one, each value scoped to its category."""
        repo = SpecRepository(test_db_with_data)

        both = await repo.search_by_tag_filters({"plot_type": ["scatter"], "domain": ["statistics"]})
        assert [s.id for s in both] == ["scatter-basic"]

        # Both fixtures share domain=statistics; plot_type narrows, it does not widen
        either = await repo.search_by_tag_filters({"plot_type": ["scatter", "bar"], "domain": ["statistics"]})
        assert sorted(s.id for s in either) == ["bar-grouped", "scatter-basic"]

        # "statistics" is a domain, not a plot type
        assert await repo.search_by_tag_filters({"plot_type": ["statistics"]}) == []

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

    async def test_count_with_languages(self, test_db_with_data):
        """Return (library_count, distinct_language_count) — used by /stats."""
        repo = LibraryRepository(test_db_with_data)
        library_count, language_count = await repo.count_with_languages()
        # Both fixture libraries default to language_id="python", so 2 libs / 1 lang.
        assert library_count == 2
        assert language_count == 1

    async def test_count_with_languages_empty(self, test_session):
        """Empty database returns (0, 0)."""
        repo = LibraryRepository(test_session)
        assert await repo.count_with_languages() == (0, 0)

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

    async def test_count_all(self, test_db_with_data):
        """Aggregate count of all impls — used by /stats."""
        repo = ImplRepository(test_db_with_data)
        # Fixture creates 3 impls (scatter+matplotlib, scatter+seaborn, bar+matplotlib).
        assert await repo.count_all() == 3

    async def test_count_all_empty(self, test_session):
        """Empty database returns 0."""
        repo = ImplRepository(test_session)
        assert await repo.count_all() == 0

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

    async def test_count_recent_by_ip_messages_only(self, test_session):
        """Reaction-only rows are skipped when counting message-bearing entries."""
        from datetime import datetime, timedelta, timezone

        repo = FeedbackRepository(test_session)

        await repo.create({"message": "one", "ip_hash": "aaa"})
        await repo.create({"reaction": "thumbs_up", "ip_hash": "aaa"})
        await repo.create({"reaction": "thumbs_down", "ip_hash": "aaa"})

        # tz-naive UTC, as the repository contract asks (created_at is TIMESTAMP WITHOUT TIME ZONE).
        since = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(minutes=1)
        assert await repo.count_recent_by_ip("aaa", since) == 3
        assert await repo.count_recent_by_ip("aaa", since, messages_only=True) == 1

    async def test_has_plot_vote(self, test_session):
        """A session's earlier 👍/👎 on the same implementation is found; others are not."""
        repo = FeedbackRepository(test_session)
        vote = {"spec_id": "scatter-basic", "library_id": "matplotlib", "language": "python", "session_id": "s1"}
        await repo.create({**vote, "reaction": "thumbs_up"})
        await repo.create({**vote, "reaction": "bug", "library_id": "plotly"})

        assert await repo.has_plot_vote("s1", "scatter-basic", "matplotlib", "python") is True
        assert await repo.has_plot_vote("s1", "scatter-basic", "matplotlib", None) is True
        assert await repo.has_plot_vote("s1", "scatter-basic", "matplotlib", "r") is False
        assert await repo.has_plot_vote("s1", "scatter-basic", "plotly", "python") is False
        assert await repo.has_plot_vote("s2", "scatter-basic", "matplotlib", "python") is False

    async def test_reaction_counts_per_implementation(self, test_session):
        """Counts 👍/👎 per (spec, library), newest row per session wins."""
        from datetime import datetime, timedelta

        repo = FeedbackRepository(test_session)
        base = datetime(2026, 9, 10, 12, 0, 0)
        vote = {"spec_id": "scatter-basic", "library_id": "matplotlib", "language": "python"}

        # Session s1 changes its mind: 👍 then 👎 — only the 👎 counts.
        await repo.create({**vote, "reaction": "thumbs_up", "session_id": "s1", "created_at": base})
        await repo.create(
            {**vote, "reaction": "thumbs_down", "session_id": "s1", "created_at": base + timedelta(seconds=5)}
        )
        # Session s2 and a session-less row both like it.
        await repo.create({**vote, "reaction": "thumbs_up", "session_id": "s2", "created_at": base})
        await repo.create({**vote, "reaction": "thumbs_up", "created_at": base})
        # Other implementation, other spec, page-level widget row: all ignored.
        await repo.create({**vote, "library_id": "plotly", "reaction": "thumbs_up", "session_id": "s3"})
        await repo.create({**vote, "spec_id": "bar-basic", "reaction": "thumbs_up", "session_id": "s3"})
        await repo.create({"spec_id": "scatter-basic", "reaction": "thumbs_up", "session_id": "s3"})
        await repo.create({**vote, "reaction": "bug", "session_id": "s4"})

        counts = await repo.reaction_counts("scatter-basic", "matplotlib")
        assert counts == {"thumbs_up": 2, "thumbs_down": 1}

        assert await repo.reaction_counts("scatter-basic", "matplotlib", language="python") == counts
        assert await repo.reaction_counts("scatter-basic", "matplotlib", language="r") == {
            "thumbs_up": 0,
            "thumbs_down": 0,
        }
        assert await repo.reaction_counts("scatter-basic", "plotly") == {"thumbs_up": 1, "thumbs_down": 0}


def _case_row(case_id: str, **overrides) -> dict:
    """An `agent_feedback` row as `core.agent_cases.row_from_manifest` returns it."""
    stamp = datetime.strptime(case_id[:16], "%Y%m%dT%H%M%SZ")
    row = {
        "id": case_id,
        "manifest_schema": 1,
        "created_at": stamp,
        "case_uri": f"gs://anyplot-agent-cases/cases/{case_id}/",
        "user_hash": "adm_0123456789abcdef",
        "session_hash": "aaaaaaaaaaaaaaaa",
        "spec_id": "scatter-basic",
        "library_id": "matplotlib",
        "locale": "en",
        "reaction": "thumbs_down",
        "message": None,
        "include_data": True,
        "status": "new",
        "result_version": 3,
        "replaces": None,
        "model": "claude-haiku-5-5",
        "model_version": None,
        "judge_model": None,
        "prompt_hash": None,
        "pipeline_status": "ok",
        "attempts": 1,
        "tokens": None,
        "cost_estimate": None,
        "files": ["plot.py", "data.csv", "manifest.json"],
    }
    return {**row, **overrides}


A = "20261012T100000Z-0000000a"
B = "20261012T110000Z-0000000b"
C = "20261012T120000Z-0000000c"


class TestAgentFeedbackRepository:
    """Integration tests for AgentFeedbackRepository (the agent chat's feedback cases)."""

    async def test_create_case_applies_the_orm_defaults(self, test_session):
        entity = await AgentFeedbackRepository(test_session).create_case(_case_row(A))
        assert (entity.status, entity.tags, entity.superseded_by, entity.promoted_at) == ("new", [], None, None)
        assert entity.created_at == datetime(2026, 10, 12, 10, 0, 0)
        assert entity.updated_at is not None

    async def test_replaces_supersedes_the_row_of_the_same_session_and_version(self, test_session):
        repo = AgentFeedbackRepository(test_session)
        await repo.create_case(_case_row(A, status="in_progress", tags=["legend"]))
        await repo.create_case(_case_row(B, replaces=A))

        earlier = await repo.get_by_id(A)
        assert earlier.superseded_by == B
        # The earlier row keeps its triage state; the new one starts fresh.
        assert (earlier.status, earlier.tags) == ("in_progress", ["legend"])
        later = await repo.get_by_id(B)
        assert (later.status, later.tags, later.replaces, later.superseded_by) == ("new", [], A, None)

    @pytest.mark.parametrize("other", [{"result_version": 2}, {"session_hash": "bbbbbbbbbbbbbbbb"}])
    async def test_replaces_leaves_a_row_of_another_session_or_version(self, test_session, other):
        repo = AgentFeedbackRepository(test_session)
        await repo.create_case(_case_row(A, **other))
        await repo.create_case(_case_row(B, replaces=A))
        assert (await repo.get_by_id(A)).superseded_by is None
        assert (await repo.get_by_id(B)).replaces == A

    async def test_replaces_leaves_an_already_superseded_row(self, test_session):
        repo = AgentFeedbackRepository(test_session)
        await repo.create_case(_case_row(A))
        await repo.create_case(_case_row(C, replaces=A))
        await repo.create_case(_case_row(B, replaces=A))
        assert (await repo.get_by_id(A)).superseded_by == C
        assert (await repo.get_by_id(B)).superseded_by is None

    async def test_replaces_of_an_unknown_case_is_stored_and_supersedes_nothing(self, test_session):
        repo = AgentFeedbackRepository(test_session)
        entity = await repo.create_case(_case_row(B, replaces=A))
        assert (entity.replaces, entity.superseded_by) == (A, None)
        assert await repo.get_by_id(A) is None

    async def test_an_orphan_inserted_after_its_successor_arrives_superseded(self, test_session):
        """The backfill indexes A after the route inserted B naming A: one commit sets A's forward link."""
        repo = AgentFeedbackRepository(test_session)
        await repo.create_case(_case_row(B, replaces=A))
        entity = await repo.create_case(_case_row(A))
        assert entity.superseded_by == B

    async def test_a_chain_backfilled_in_id_order_links_every_step(self, test_session):
        """A, C in the table; the orphan B (replaces A, replaced by C) is backfilled: A -> B -> C."""
        repo = AgentFeedbackRepository(test_session)
        await repo.create_case(_case_row(A))
        await repo.create_case(_case_row(C, replaces=B))
        await repo.create_case(_case_row(B, replaces=A))
        assert (await repo.get_by_id(A)).superseded_by == B
        assert (await repo.get_by_id(B)).superseded_by == C
        assert (await repo.get_by_id(C)).superseded_by is None

    async def test_successor_of(self, test_session):
        repo = AgentFeedbackRepository(test_session)
        await repo.create_case(_case_row(B, replaces=A))
        await repo.create_case(_case_row(C, replaces=A))
        assert await repo.successor_of(A, "aaaaaaaaaaaaaaaa", 3) == B
        assert await repo.successor_of(A, "aaaaaaaaaaaaaaaa", 2) is None
        assert await repo.successor_of(A, "bbbbbbbbbbbbbbbb", 3) is None
        assert await repo.successor_of(B, "aaaaaaaaaaaaaaaa", 3) is None

    async def test_list_cases_newest_first_without_superseded_rows(self, test_session):
        repo = AgentFeedbackRepository(test_session)
        await repo.create_case(_case_row(A))
        await repo.create_case(_case_row(B, replaces=A))
        await repo.create_case(_case_row(C, session_hash="bbbbbbbbbbbbbbbb"))

        assert [row.id for row in await repo.list_cases()] == [C, B]
        assert [row.id for row in await repo.list_cases(include_superseded=True)] == [C, B, A]

    async def test_list_cases_filters(self, test_session):
        repo = AgentFeedbackRepository(test_session)
        await repo.create_case(_case_row(A, reaction="bug", status="done", spec_id="bar-basic", model_version="m1"))
        await repo.create_case(_case_row(B, reaction="thumbs_up", status="in_progress", library_id="seaborn"))
        await repo.create_case(_case_row(C, status="wont_solve"))

        async def ids(**filters):
            return [row.id for row in await repo.list_cases(**filters)]

        assert await ids(reaction="bug") == [A]
        assert await ids(status="done") == [A]
        assert await ids(status=("new", "in_progress")) == [B]
        assert await ids(spec_id="bar-basic") == [A]
        assert await ids(library_id="seaborn") == [B]
        assert await ids(model_version="m1") == [A]
        assert await ids(spec_id="scatter-basic", library_id="matplotlib") == [C]

    async def test_list_cases_tag_filter(self, test_session):
        repo = AgentFeedbackRepository(test_session)
        await repo.create_case(_case_row(A))
        await repo.create_case(_case_row(B))
        await repo.create_case(_case_row(C))
        await repo.update(A, {"tags": ["legend", "overlap"]})
        await repo.update(B, {"tags": ["legend-overlap"]})

        assert [row.id for row in await repo.list_cases(tag="legend")] == [A]
        assert [row.id for row in await repo.list_cases(tag="legend-overlap")] == [B]
        assert [row.id for row in await repo.list_cases(tag="overlap")] == [A]
        assert await repo.list_cases(tag="leg") == []

    async def test_list_cases_cursor_and_limit(self, test_session):
        repo = AgentFeedbackRepository(test_session)
        for case_id in (A, B, C):
            await repo.create_case(_case_row(case_id))

        assert [row.id for row in await repo.list_cases(limit=2)] == [C, B]
        assert [row.id for row in await repo.list_cases(before=B, limit=2)] == [A]
        assert await repo.list_cases(before=A) == []

    async def test_siblings(self, test_session):
        repo = AgentFeedbackRepository(test_session)
        await repo.create_case(_case_row(A))
        await repo.create_case(_case_row(B))
        await repo.create_case(_case_row(C, result_version=4))
        assert await repo.siblings("aaaaaaaaaaaaaaaa", 3, exclude_id=B) == [A]
        assert await repo.siblings("aaaaaaaaaaaaaaaa", 3, exclude_id=A) == [B]
        assert await repo.siblings("aaaaaaaaaaaaaaaa", 4, exclude_id=C) == []

    async def test_update_changes_only_the_triage_state(self, test_session):
        repo = AgentFeedbackRepository(test_session)
        await repo.create_case(_case_row(A))
        promoted_at = datetime(2026, 10, 12, 15, 0, 0)

        updated = await repo.update(
            A,
            {
                "status": "done",
                "tags": ["legend"],
                "expected": "rejected",
                "promoted_at": promoted_at,
                "replaces": B,
                "superseded_by": C,
                "reaction": "bug",
            },
        )

        assert (updated.status, updated.tags, updated.expected, updated.promoted_at) == (
            "done",
            ["legend"],
            "rejected",
            promoted_at,
        )
        assert (updated.replaces, updated.superseded_by, updated.reaction) == (None, None, "thumbs_down")

    async def test_list_all_oldest_first(self, test_session):
        repo = AgentFeedbackRepository(test_session)
        await repo.create_case(_case_row(C))
        await repo.create_case(_case_row(A))
        assert [row.id for row in await repo.list_all()] == [A, C]
