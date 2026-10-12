"""
Tests for database ORM models.

Tests model instantiation, defaults, and constraints.
"""

import re
from datetime import datetime
from typing import Any

import pytest
from sqlalchemy import CheckConstraint
from sqlalchemy.ext.asyncio import AsyncSession

from core.database.models import (
    AGENT_CASE_EXPECTED,
    FEEDBACK_REACTIONS,
    FEEDBACK_STATUSES,
    MAX_LIBRARY_ID_LENGTH,
    MAX_SPEC_ID_LENGTH,
    REVIEW_VERDICTS,
    AgentFeedback,
    Feedback,
    Impl,
    Library,
    Spec,
)


def _check_literals(model: Any, name: str) -> list[str]:
    """The quoted values a named CHECK constraint of `model` allows, in order."""
    constraint = next(
        item for item in model.__table__.constraints if isinstance(item, CheckConstraint) and item.name == name
    )
    return re.findall(r"'([^']*)'", str(constraint.sqltext))


class TestCheckConstraintParity:
    """The CHECK texts and the module tuples are written by hand; these keep each pair equal."""

    @pytest.mark.parametrize(
        ("model", "name", "values"),
        [
            (AgentFeedback, "ck_agent_feedback_reaction_valid", FEEDBACK_REACTIONS),
            (AgentFeedback, "ck_agent_feedback_status_valid", FEEDBACK_STATUSES),
            (AgentFeedback, "ck_agent_feedback_expected_valid", AGENT_CASE_EXPECTED),
            (Feedback, "ck_feedback_reaction_valid", FEEDBACK_REACTIONS),
            (Feedback, "ck_feedback_status_valid", FEEDBACK_STATUSES),
        ],
    )
    def test_check_lists_the_tuple(self, model, name, values) -> None:
        assert tuple(_check_literals(model, name)) == values


class TestAgentFeedbackModel:
    """Tests for the AgentFeedback model (the agent chat's feedback cases)."""

    @pytest.mark.asyncio
    async def test_persist_applies_the_orm_defaults(self, test_session: AsyncSession) -> None:
        row = AgentFeedback(
            id="20261012T143005Z-1a2b3c4d",
            manifest_schema=1,
            created_at=datetime(2026, 10, 12, 14, 30, 5),
            case_uri="gs://anyplot-agent-cases/cases/20261012T143005Z-1a2b3c4d/",
            user_hash="adm_0123456789abcdef",
            session_hash="fedcba9876543210",
            reaction="bug",
            include_data=False,
            result_version=1,
            files=["plot.py", "manifest.json"],
        )
        test_session.add(row)
        await test_session.commit()
        await test_session.refresh(row)

        assert row.status == "new"
        assert row.tags == []
        assert row.files == ["plot.py", "manifest.json"]
        assert row.include_data is False
        assert row.updated_at is not None
        assert row.promoted_at is None
        assert row.superseded_by is None


class TestModelConstants:
    """Tests for model constants."""

    def test_max_spec_id_length(self) -> None:
        assert MAX_SPEC_ID_LENGTH == 100

    def test_max_library_id_length(self) -> None:
        assert MAX_LIBRARY_ID_LENGTH == 50

    def test_review_verdicts(self) -> None:
        assert "APPROVED" in REVIEW_VERDICTS
        assert "REJECTED" in REVIEW_VERDICTS
        assert len(REVIEW_VERDICTS) == 2


class TestSpecModel:
    """Tests for Spec model."""

    def test_create_minimal(self) -> None:
        spec = Spec(id="scatter-basic", title="Basic Scatter")
        assert spec.id == "scatter-basic"
        assert spec.title == "Basic Scatter"
        assert spec.description is None
        assert spec.issue is None

    def test_create_with_fields(self) -> None:
        spec = Spec(
            id="scatter-basic",
            title="Basic Scatter",
            description="A scatter plot",
            applications=["data viz"],
            data=["numeric"],
            notes=["Use for 2D"],
            tags={"plot_type": ["scatter"]},
            issue=42,
            suggested="user1",
        )
        assert spec.description == "A scatter plot"
        assert spec.applications == ["data viz"]
        assert spec.tags == {"plot_type": ["scatter"]}
        assert spec.issue == 42

    @pytest.mark.asyncio
    async def test_persist_and_retrieve(self, test_session: AsyncSession) -> None:
        spec = Spec(id="test-spec", title="Test Spec", description="test")
        test_session.add(spec)
        await test_session.commit()

        from sqlalchemy import select

        result = await test_session.execute(select(Spec).where(Spec.id == "test-spec"))
        retrieved = result.scalar_one()
        assert retrieved.title == "Test Spec"


class TestLibraryModel:
    """Tests for Library model."""

    def test_create_minimal(self) -> None:
        lib = Library(id="matplotlib", name="Matplotlib")
        assert lib.id == "matplotlib"
        assert lib.version is None

    def test_create_with_fields(self) -> None:
        lib = Library(
            id="matplotlib",
            name="Matplotlib",
            version="3.10.0",
            documentation_url="https://matplotlib.org",
            description="Plotting library",
        )
        assert lib.version == "3.10.0"
        assert lib.documentation_url == "https://matplotlib.org"


class TestImplModel:
    """Tests for Impl model."""

    def test_create_minimal(self) -> None:
        impl = Impl(spec_id="scatter-basic", library_id="matplotlib")
        assert impl.spec_id == "scatter-basic"
        assert impl.library_id == "matplotlib"
        assert impl.code is None
        assert impl.quality_score is None
        assert impl.review_verdict is None

    def test_create_with_review_fields(self) -> None:
        impl = Impl(
            spec_id="scatter-basic",
            library_id="matplotlib",
            quality_score=92.5,
            review_strengths=["clean code"],
            review_weaknesses=["needs labels"],
            review_verdict="APPROVED",
            impl_tags={"techniques": ["annotations"]},
        )
        assert impl.quality_score == 92.5
        assert impl.review_verdict == "APPROVED"
        assert impl.impl_tags == {"techniques": ["annotations"]}

    @pytest.mark.asyncio
    async def test_default_id_generated(self, test_session: AsyncSession) -> None:
        """IDs are auto-generated on insert."""
        lib = Library(id="matplotlib", name="Matplotlib")
        spec1 = Spec(id="s1", title="Spec 1")
        spec2 = Spec(id="s2", title="Spec 2")
        test_session.add_all([lib, spec1, spec2])
        await test_session.commit()

        impl1 = Impl(spec_id="s1", library_id="matplotlib")
        impl2 = Impl(spec_id="s2", library_id="matplotlib")
        test_session.add_all([impl1, impl2])
        await test_session.commit()
        assert impl1.id is not None
        assert impl2.id is not None
        assert impl1.id != impl2.id

    @pytest.mark.asyncio
    async def test_persist_with_foreign_keys(self, test_session: AsyncSession) -> None:
        lib = Library(id="matplotlib", name="Matplotlib")
        spec = Spec(id="scatter-basic", title="Basic Scatter")
        test_session.add_all([lib, spec])
        await test_session.commit()

        impl = Impl(spec_id="scatter-basic", library_id="matplotlib", code="import matplotlib", quality_score=90.0)
        test_session.add(impl)
        await test_session.commit()

        from sqlalchemy import select

        result = await test_session.execute(select(Impl).where(Impl.spec_id == "scatter-basic"))
        retrieved = result.scalar_one()
        assert retrieved.quality_score == 90.0
