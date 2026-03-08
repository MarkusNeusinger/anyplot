"""
Pydantic schemas for pyplots API.

Centralized schema definitions for request/response models.
"""

from typing import Any

from pydantic import BaseModel


class ImplementationResponse(BaseModel):
    """Implementation details for a single library."""

    library_id: str
    library_name: str
    preview_url: str | None = None
    preview_thumb: str | None = None
    preview_html: str | None = None
    quality_score: float | None = None
    code: str | None = None
    generated_at: str | None = None
    generated_by: str | None = None
    python_version: str | None = None
    library_version: str | None = None
    # Review fields
    review_strengths: list[str] = []
    review_weaknesses: list[str] = []
    review_image_description: str | None = None
    review_criteria_checklist: dict[str, Any] | None = None
    review_verdict: str | None = None
    # Implementation-level tags (issue #2434)
    impl_tags: dict[str, Any] | None = None


class SpecDetailResponse(BaseModel):
    """Detailed spec response with implementations."""

    id: str
    title: str
    description: str | None = None
    applications: list[str] = []
    data: list[str] = []
    notes: list[str] = []
    tags: dict[str, Any] | None = None
    issue: int | None = None
    suggested: str | None = None
    created: str | None = None
    updated: str | None = None
    implementations: list[ImplementationResponse] = []


class SpecListItem(BaseModel):
    """Spec list item with summary info."""

    id: str
    title: str
    description: str | None = None
    tags: dict[str, Any] | None = None
    library_count: int = 0


class ImageResponse(BaseModel):
    """Image/plot response for grid display."""

    spec_id: str
    library: str
    url: str | None = None
    thumb: str | None = None
    html: str | None = None
    code: str | None = None


class FilterCountsResponse(BaseModel):
    """Counts for filter categories."""

    # Spec-level filters
    lib: dict[str, int] = {}
    spec: dict[str, int] = {}
    plot: dict[str, int] = {}
    data: dict[str, int] = {}
    dom: dict[str, int] = {}
    feat: dict[str, int] = {}
    # Impl-level filters (issue #2434)
    dep: dict[str, int] = {}
    tech: dict[str, int] = {}
    pat: dict[str, int] = {}
    prep: dict[str, int] = {}
    style: dict[str, int] = {}


class FilteredPlotsResponse(BaseModel):
    """Response for filtered plots endpoint."""

    total: int
    images: list[dict[str, Any]]  # Image dicts with spec_id, library, url, thumb, etc.
    counts: dict[str, dict[str, int]]  # Category -> value -> count
    globalCounts: dict[str, dict[str, int]]  # Same structure for global counts
    orCounts: list[dict[str, int]]  # Per-group OR counts
    specTitles: dict[str, str] = {}  # Mapping spec_id -> title for search/tooltips
    offset: int = 0
    limit: int | None = None


class LibraryInfo(BaseModel):
    """Library information."""

    id: str
    name: str
    version: str | None = None
    documentation_url: str | None = None
    description: str | None = None


class StatsResponse(BaseModel):
    """Platform statistics."""

    specs: int
    plots: int
    libraries: int
