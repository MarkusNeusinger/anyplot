"""
Insights endpoints for pyplots platform.

Public analytics and discovery features that leverage aggregated database data:
- Dashboard: Rich platform statistics and visualizations
- Plot of the Day: Daily featured high-quality implementation
- Related Plots: Tag-based similarity recommendations
"""

from __future__ import annotations

import hashlib
from collections import Counter, defaultdict
from datetime import date, datetime, timezone

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from api.cache import cache_key, get_or_set_cache
from api.dependencies import require_db
from core.constants import SUPPORTED_LIBRARIES
from core.database import ImplRepository, SpecRepository
from core.database.connection import get_db_context
from core.utils import strip_noqa_comments


router = APIRouter(prefix="/insights", tags=["insights"])


# =============================================================================
# Response Models
# =============================================================================


class LibraryDashboardStats(BaseModel):
    """Per-library statistics for the dashboard."""

    id: str
    name: str
    impl_count: int
    avg_score: float | None
    min_score: float | None
    max_score: float | None
    score_buckets: dict[str, int]  # "50-55": 2, "90-95": 45, etc.
    loc_buckets: dict[str, int]  # "0-20": 5, "20-40": 12, etc.
    avg_loc: float | None


class CoverageCell(BaseModel):
    """Single cell in coverage heatmap."""

    score: float | None = None
    has_impl: bool = False


class CoverageRow(BaseModel):
    """One spec row in coverage heatmap."""

    spec_id: str
    title: str
    libraries: dict[str, CoverageCell]


class TopImpl(BaseModel):
    """A top-rated implementation."""

    spec_id: str
    spec_title: str
    library_id: str
    quality_score: float
    preview_url: str | None = None


class TimelinePoint(BaseModel):
    """Monthly implementation count."""

    month: str  # "2025-01"
    count: int


class DashboardResponse(BaseModel):
    """Full dashboard statistics."""

    total_specs: int
    total_implementations: int
    total_interactive: int
    total_lines_of_code: int
    avg_quality_score: float | None
    coverage_percent: float

    library_stats: list[LibraryDashboardStats]
    coverage_matrix: list[CoverageRow]
    top_implementations: list[TopImpl]
    tag_distribution: dict[str, dict[str, int]]
    score_distribution: dict[str, int]
    timeline: list[TimelinePoint]


class PlotOfTheDayResponse(BaseModel):
    """Daily featured plot."""

    spec_id: str
    spec_title: str
    description: str | None = None
    library_id: str
    library_name: str
    quality_score: float
    preview_url: str | None = None
    image_description: str | None = None
    code: str | None = None
    date: str


class RelatedSpecItem(BaseModel):
    """A related spec with similarity info."""

    id: str
    title: str
    preview_url: str | None = None
    library_id: str | None = None
    similarity: float
    shared_tags: list[str]


class RelatedSpecsResponse(BaseModel):
    """Related specs for a given spec."""

    related: list[RelatedSpecItem]


# =============================================================================
# Shared helpers
# =============================================================================

LIBRARY_NAMES = {
    "altair": "Altair",
    "bokeh": "Bokeh",
    "highcharts": "Highcharts",
    "letsplot": "lets-plot",
    "matplotlib": "Matplotlib",
    "plotly": "Plotly",
    "plotnine": "plotnine",
    "pygal": "Pygal",
    "seaborn": "Seaborn",
}


def _score_bucket(score: float) -> str:
    """Map a quality score (50-100) to a 5-step histogram bucket label."""
    clamped = max(50, min(score, 100))
    bucket = min(int((clamped - 50) // 5), 9)
    lo = 50 + bucket * 5
    hi = lo + 5
    return f"{lo}-{hi}"


def _flatten_tags(tags: dict | None) -> set[str]:
    """Flatten a spec's tags JSON into a set of 'category:value' strings."""
    if not tags:
        return set()
    flat: set[str] = set()
    for category, values in tags.items():
        if isinstance(values, list):
            for v in values:
                flat.add(f"{category}:{v}")
    return flat


def _parse_iso(s: str | None) -> datetime | None:
    """Parse an ISO datetime string, returning None on failure."""
    if not s:
        return None
    try:
        dt = datetime.fromisoformat(s.replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except Exception:
        return None


# =============================================================================
# 1. Dashboard
# =============================================================================


async def _refresh_dashboard() -> DashboardResponse:
    """Standalone factory for background refresh."""
    async with get_db_context() as db:
        return await _build_dashboard(SpecRepository(db), ImplRepository(db))


async def _build_dashboard(repo: SpecRepository, impl_repo: ImplRepository) -> DashboardResponse:
    """Build the full dashboard response from DB data."""
    all_specs = await repo.get_all()
    total_loc = await impl_repo.get_total_code_lines()
    loc_per_impl = await impl_repo.get_loc_per_impl()

    # Build LOC buckets per library (0-20, 20-40, ..., 380-400, 400+)
    loc_bucket_ranges = [(i, i + 20) for i in range(0, 400, 20)] + [(400, 999)]
    library_loc_buckets: dict[str, Counter[str]] = {lib: Counter() for lib in SUPPORTED_LIBRARIES}
    for lib_id, lines in loc_per_impl:
        if lib_id in library_loc_buckets:
            for lo, hi in loc_bucket_ranges:
                if lo <= lines < hi or (hi == 999 and lines >= lo):
                    label = f"{lo}-{hi}" if hi != 999 else f"{lo}+"
                    library_loc_buckets[lib_id][label] += 1
                    break

    # Avg LOC per library
    library_loc_lists: dict[str, list[int]] = {lib: [] for lib in SUPPORTED_LIBRARIES}
    for lib_id, lines in loc_per_impl:
        if lib_id in library_loc_lists:
            library_loc_lists[lib_id].append(lines)

    total_impls = 0
    total_interactive = 0
    all_scores: list[float] = []

    library_scores: dict[str, list[float]] = {lib: [] for lib in SUPPORTED_LIBRARIES}
    library_counts: dict[str, int] = dict.fromkeys(SUPPORTED_LIBRARIES, 0)  # type: ignore[arg-type]

    tag_counter: dict[str, Counter[str]] = defaultdict(Counter)
    monthly_counts: Counter[str] = Counter()
    score_buckets: Counter[str] = Counter()

    coverage_rows: list[CoverageRow] = []
    top_impls: list[TopImpl] = []

    for spec in all_specs:
        row_libs: dict[str, CoverageCell] = {}

        for impl in spec.impls:
            lib_id = impl.library_id
            score = impl.quality_score
            total_impls += 1
            if impl.preview_html:
                total_interactive += 1
            library_counts[lib_id] = library_counts.get(lib_id, 0) + 1
            row_libs[lib_id] = CoverageCell(score=score, has_impl=True)

            if score is not None:
                library_scores[lib_id].append(score)
                all_scores.append(score)
                score_buckets[_score_bucket(score)] += 1

                if score >= 95:
                    top_impls.append(
                        TopImpl(
                            spec_id=spec.id,
                            spec_title=spec.title,
                            library_id=lib_id,
                            quality_score=score,
                            preview_url=impl.preview_url,
                        )
                    )

            # Timeline from generated_at (datetime field, not string)
            gen_dt = impl.generated_at
            if gen_dt:
                monthly_counts[gen_dt.strftime("%Y-%m")] += 1

        coverage_rows.append(CoverageRow(spec_id=spec.id, title=spec.title, libraries=row_libs))

        # Tag distribution (spec-level + impl-level)
        if spec.tags:
            for category, values in spec.tags.items():
                if isinstance(values, list):
                    for v in values:
                        tag_counter[category][v] += 1
        for impl in spec.impls:
            if impl.impl_tags and isinstance(impl.impl_tags, dict):
                for category, values in impl.impl_tags.items():
                    if isinstance(values, list):
                        for v in values:
                            tag_counter[category][v] += 1

    # Build library stats
    lib_stats: list[LibraryDashboardStats] = []
    for lib_id in sorted(SUPPORTED_LIBRARIES):
        scores = library_scores[lib_id]
        buckets: Counter[str] = Counter()
        for s in scores:
            buckets[_score_bucket(s)] += 1
        lib_stats.append(
            LibraryDashboardStats(
                id=lib_id,
                name=LIBRARY_NAMES.get(lib_id, lib_id),
                impl_count=library_counts[lib_id],
                avg_score=round(sum(scores) / len(scores), 1) if scores else None,
                min_score=round(min(scores), 1) if scores else None,
                max_score=round(max(scores), 1) if scores else None,
                score_buckets=dict(buckets),
                loc_buckets=dict(library_loc_buckets[lib_id]),
                avg_loc=round(sum(library_loc_lists[lib_id]) / len(library_loc_lists[lib_id]), 1)
                if library_loc_lists[lib_id]
                else None,
            )
        )
    lib_stats.sort(key=lambda x: x.impl_count, reverse=True)

    # Top impls sorted by score desc, limit 20
    top_impls.sort(key=lambda x: x.quality_score, reverse=True)
    top_impls = top_impls[:20]

    # Score distribution — ensure all buckets present
    score_dist = {f"{50 + i * 5}-{55 + i * 5}": score_buckets.get(f"{50 + i * 5}-{55 + i * 5}", 0) for i in range(10)}

    # Timeline sorted by month
    timeline = [TimelinePoint(month=m, count=c) for m, c in sorted(monthly_counts.items())]

    # Coverage
    coverage = (total_impls / (len(all_specs) * len(SUPPORTED_LIBRARIES)) * 100) if all_specs else 0

    # Coverage matrix sorted by title
    coverage_rows.sort(key=lambda r: r.title.lower())

    return DashboardResponse(
        total_specs=len(all_specs),
        total_implementations=total_impls,
        total_interactive=total_interactive,
        total_lines_of_code=total_loc,
        avg_quality_score=round(sum(all_scores) / len(all_scores), 1) if all_scores else None,
        coverage_percent=round(coverage, 1),
        library_stats=lib_stats,
        coverage_matrix=coverage_rows,
        top_implementations=top_impls,
        tag_distribution={cat: dict(counter.most_common(20)) for cat, counter in sorted(tag_counter.items())},
        score_distribution=score_dist,
        timeline=timeline,
    )


@router.get("/dashboard", response_model=DashboardResponse)
async def get_dashboard(db: AsyncSession = Depends(require_db)) -> DashboardResponse:
    """
    Get rich platform statistics for the public stats dashboard.

    Includes per-library scores, coverage heatmap, top implementations,
    tag distribution, score histogram, and implementation timeline.
    """
    repo = SpecRepository(db)
    impl_repo = ImplRepository(db)

    async def _fetch() -> DashboardResponse:
        return await _build_dashboard(repo, impl_repo)

    return await get_or_set_cache(
        cache_key("insights", "dashboard"), _fetch, refresh_after=3600, refresh_factory=_refresh_dashboard
    )


# =============================================================================
# 2. Plot of the Day
# =============================================================================


async def _refresh_potd() -> PlotOfTheDayResponse | None:
    """Standalone factory for background refresh."""
    async with get_db_context() as db:
        return await _build_potd(SpecRepository(db), ImplRepository(db))


async def _build_potd(spec_repo: SpecRepository, impl_repo: ImplRepository) -> PlotOfTheDayResponse | None:
    """Select the plot of the day deterministically."""
    all_specs = await spec_repo.get_all()
    today = date.today().isoformat()

    # Collect candidates: implementations with quality_score >= 90 (lightweight, no code loaded)
    candidates: list[tuple[str, str, str, str | None, float, str | None]] = []
    for spec in all_specs:
        for impl in spec.impls:
            if impl.quality_score is not None and impl.quality_score >= 90 and impl.preview_url:
                candidates.append(
                    (spec.id, spec.title, spec.description or "", impl.library_id, impl.quality_score, impl.preview_url)
                )

    if not candidates:
        return None

    # Deterministic selection based on date
    seed = int(hashlib.md5(today.encode()).hexdigest(), 16)  # noqa: S324
    idx = seed % len(candidates)
    spec_id, spec_title, description, library_id, quality_score, preview_url = candidates[idx]

    # Load deferred fields (code, image_description) for just this one impl
    full_impl = await impl_repo.get_by_spec_and_library(spec_id, library_id)

    return PlotOfTheDayResponse(
        spec_id=spec_id,
        spec_title=spec_title,
        description=description,
        library_id=library_id,
        library_name=LIBRARY_NAMES.get(library_id, library_id),
        quality_score=quality_score,
        preview_url=preview_url,
        image_description=full_impl.review_image_description if full_impl else None,
        code=strip_noqa_comments(full_impl.code) if full_impl and full_impl.code else None,
        date=today,
    )


@router.get("/plot-of-the-day", response_model=PlotOfTheDayResponse | None)
async def get_plot_of_the_day(db: AsyncSession = Depends(require_db)) -> PlotOfTheDayResponse | None:
    """
    Get the featured plot of the day.

    Deterministically selects a high-quality implementation (score >= 90)
    based on today's date. Returns the same result for the entire day.
    """
    spec_repo = SpecRepository(db)
    impl_repo = ImplRepository(db)

    async def _fetch() -> PlotOfTheDayResponse | None:
        return await _build_potd(spec_repo, impl_repo)

    return await get_or_set_cache(
        cache_key("insights", "potd", date.today().isoformat()),
        _fetch,
        refresh_after=3600,
        refresh_factory=_refresh_potd,
    )


# =============================================================================
# 3. Related Plots
# =============================================================================


def _collect_impl_tags(spec: object, library: str | None = None) -> set[str]:
    """Collect spec-level tags + impl-level tags for a spec.

    If library is specified, only include that library's impl_tags.
    Otherwise, collect impl_tags from all implementations.
    """
    tags = _flatten_tags(spec.tags)
    for impl in spec.impls:
        if library and impl.library_id != library:
            continue
        if impl.impl_tags and isinstance(impl.impl_tags, dict):
            tags |= _flatten_tags(impl.impl_tags)
    return tags


async def _build_related(
    repo: SpecRepository, spec_id: str, limit: int, mode: str, library: str | None = None
) -> RelatedSpecsResponse:
    """Find related specs using Jaccard similarity on tags.

    mode="spec": only spec-level tags (for overview page)
    mode="full": spec + impl tags for the given library (for impl detail page)
    """
    all_specs = await repo.get_all()

    # Find target spec
    target = None
    for s in all_specs:
        if s.id == spec_id:
            target = s
            break
    if target is None:
        return RelatedSpecsResponse(related=[])

    # Build target tags based on mode
    if mode == "full":
        target_tags = _collect_impl_tags(target, library)
    else:
        target_tags = _flatten_tags(target.tags)
    if not target_tags:
        return RelatedSpecsResponse(related=[])

    # Compute similarity for all other specs
    scored: list[tuple[float, list[str], object]] = []
    for spec in all_specs:
        if spec.id == spec_id:
            continue
        # For other specs: use same library's impl_tags if available, else best match
        if mode == "full":
            other_tags = _collect_impl_tags(spec, library)
        else:
            other_tags = _flatten_tags(spec.tags)
        if not other_tags:
            continue
        intersection = target_tags & other_tags
        union = target_tags | other_tags
        similarity = len(intersection) / len(union) if union else 0
        if similarity > 0:
            shared = [t.split(":", 1)[1] for t in sorted(intersection)]
            scored.append((similarity, shared, spec))

    # Sort by similarity desc, then shuffle within same-score groups for variety
    scored.sort(key=lambda x: x[0], reverse=True)
    # Take top candidates (2x limit) and shuffle lightly to add variety
    top_pool = scored[: limit * 2]
    if len(top_pool) > limit:
        import random

        # Group by rounded similarity, shuffle within groups
        seed = int(hashlib.md5(spec_id.encode()).hexdigest(), 16) % (2**32)  # noqa: S324
        rng = random.Random(seed)
        rng.shuffle(top_pool)
        # Re-sort but with jitter: high similarity still wins, just not deterministic order
        top_pool.sort(key=lambda x: x[0] + rng.uniform(0, 0.05), reverse=True)

    # Build response with best-quality preview per spec
    related: list[RelatedSpecItem] = []
    for similarity, shared_tags, spec in top_pool[:limit]:
        impls_with_preview = [i for i in spec.impls if i.preview_url]
        best_impl = max(impls_with_preview, key=lambda i: i.quality_score or 0) if impls_with_preview else None
        related.append(
            RelatedSpecItem(
                id=spec.id,
                title=spec.title,
                preview_url=best_impl.preview_url if best_impl else None,
                library_id=best_impl.library_id if best_impl else None,
                similarity=round(similarity, 3),
                shared_tags=shared_tags,
            )
        )

    return RelatedSpecsResponse(related=related)


@router.get("/related/{spec_id}", response_model=RelatedSpecsResponse)
async def get_related_specs(
    spec_id: str,
    limit: int = Query(default=6, ge=1, le=12),
    mode: str = Query(default="spec", pattern="^(spec|full)$"),
    library: str | None = Query(default=None),
    db: AsyncSession = Depends(require_db),
) -> RelatedSpecsResponse:
    """
    Get specs related to the given spec, based on tag similarity.

    mode=spec: only spec-level tags (plot_type, domain, etc.)
    mode=full: spec tags + impl tags for the given library
    library: in full mode, use this library's impl_tags (required for accurate tag matching)
    """
    repo = SpecRepository(db)

    async def _fetch() -> RelatedSpecsResponse:
        return await _build_related(repo, spec_id, limit, mode, library)

    return await get_or_set_cache(cache_key("insights", "related", spec_id, str(limit), mode, library or ""), _fetch)
