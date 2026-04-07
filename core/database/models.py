"""
SQLAlchemy ORM models for pyplots.

Defines database tables for specs, libraries, and impls.
"""

from datetime import datetime
from typing import Any, Optional
from uuid import uuid4

from sqlalchemy import BigInteger, CheckConstraint, DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, deferred, mapped_column, relationship
from sqlalchemy.sql import func

from core.constants import LIBRARIES_METADATA
from core.database.connection import Base
from core.database.types import StringArray, UniversalJSON, UniversalUUID


# =============================================================================
# Model Constants
# =============================================================================

# Maximum length for spec IDs (e.g., "scatter-regression-linear" = 27 chars)
MAX_SPEC_ID_LENGTH = 100

# Maximum length for library IDs (e.g., "highcharts" = 10 chars)
MAX_LIBRARY_ID_LENGTH = 50

# Valid review verdicts
REVIEW_VERDICTS = ("APPROVED", "REJECTED")


class Spec(Base):
    """Plot specification - library-agnostic definition of a plot type."""

    __tablename__ = "specs"

    # Identification - with max length constraint
    id: Mapped[str] = mapped_column(String(MAX_SPEC_ID_LENGTH), primary_key=True)  # e.g., "scatter-basic"
    title: Mapped[str] = mapped_column(String(255), nullable=False)

    # From spec.md
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # Prose text
    applications: Mapped[list[str]] = mapped_column(StringArray, default=list)  # Use cases
    data: Mapped[list[str]] = mapped_column(StringArray, default=list)  # Data requirements
    notes: Mapped[list[str]] = mapped_column(StringArray, default=list)  # Optional hints

    # From metadata.yaml
    created: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)  # When spec was first created
    updated: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)  # When spec was last modified
    issue: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # GitHub issue number
    suggested: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)  # GitHub username
    tags: Mapped[Optional[dict[str, Any]]] = mapped_column(
        UniversalJSON, nullable=True
    )  # {plot_type, data_type, domain, features}

    # System
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

    # Relationships
    impls: Mapped[list["Impl"]] = relationship("Impl", back_populates="spec", cascade="all, delete-orphan")


class Library(Base):
    """Supported plotting library."""

    __tablename__ = "libraries"

    id: Mapped[str] = mapped_column(String, primary_key=True)  # e.g., "matplotlib"
    name: Mapped[str] = mapped_column(String, nullable=False)  # e.g., "Matplotlib"
    version: Mapped[Optional[str]] = mapped_column(String, nullable=True)  # Current version
    documentation_url: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # Short description

    # Relationships
    impls: Mapped[list["Impl"]] = relationship("Impl", back_populates="library", cascade="all, delete-orphan")


class Impl(Base):
    """Library-specific implementation of a spec."""

    __tablename__ = "impls"

    # Identification
    id: Mapped[str] = mapped_column(UniversalUUID, primary_key=True, default=lambda: str(uuid4()))
    spec_id: Mapped[str] = mapped_column(String, ForeignKey("specs.id", ondelete="CASCADE"), nullable=False)
    library_id: Mapped[str] = mapped_column(String, ForeignKey("libraries.id", ondelete="CASCADE"), nullable=False)

    # Code (deferred — ~13 MB total, only loaded when explicitly accessed or undeferred)
    code: Mapped[Optional[str]] = deferred(mapped_column(Text, nullable=True))  # Python source

    # Previews (filled by workflow, synced from metadata YAML)
    preview_url: Mapped[Optional[str]] = mapped_column(String, nullable=True)  # Full PNG
    preview_html: Mapped[Optional[str]] = mapped_column(String, nullable=True)  # Interactive HTML

    # Creation versions (filled by workflow)
    python_version: Mapped[Optional[str]] = mapped_column(String, nullable=True)  # e.g., "3.13"
    library_version: Mapped[Optional[str]] = mapped_column(String, nullable=True)  # e.g., "3.9.0"

    # Test matrix (deferred — unused by any endpoint)
    tested: Mapped[Optional[list]] = deferred(mapped_column(UniversalJSON, nullable=True))

    # Quality & Generation - quality_score constrained to 0-100 range
    quality_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    generated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)  # First generation
    updated: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)  # Last update
    generated_by: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)  # Model ID
    issue: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # GitHub Issue
    workflow_run: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)  # GitHub Actions run ID

    # Review feedback (structured arrays from impl-review)
    review_strengths: Mapped[list[str]] = mapped_column(StringArray, default=list)  # What's good
    review_weaknesses: Mapped[list[str]] = mapped_column(StringArray, default=list)  # What needs work

    # Extended review data (deferred — ~12 MB total, only needed on detail pages)
    review_image_description: Mapped[Optional[str]] = deferred(
        mapped_column(Text, nullable=True)
    )  # AI's visual description
    review_criteria_checklist: Mapped[Optional[dict[str, Any]]] = deferred(
        mapped_column(UniversalJSON, nullable=True)
    )  # Detailed scoring
    review_verdict: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)  # "APPROVED" or "REJECTED"

    # Implementation-level tags (from impl-review)
    impl_tags: Mapped[Optional[dict[str, Any]]] = mapped_column(
        UniversalJSON, nullable=True
    )  # {dependencies, techniques, patterns, dataprep, styling}

    # System
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

    # Relationships
    spec: Mapped["Spec"] = relationship("Spec", back_populates="impls")
    library: Mapped["Library"] = relationship("Library", back_populates="impls")

    # Unique constraint and check constraints
    __table_args__ = (
        UniqueConstraint("spec_id", "library_id", name="uq_impl"),
        # Quality score must be between 0 and 100
        CheckConstraint(
            "quality_score IS NULL OR (quality_score >= 0 AND quality_score <= 100)", name="ck_quality_score_range"
        ),
        # Review verdict must be APPROVED or REJECTED if set
        CheckConstraint(
            "review_verdict IS NULL OR review_verdict IN ('APPROVED', 'REJECTED')", name="ck_review_verdict_valid"
        ),
    )


# Seed data for libraries (re-exported from core.constants)
LIBRARIES_SEED = LIBRARIES_METADATA
