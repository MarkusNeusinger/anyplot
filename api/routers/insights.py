"""
Insights endpoints for anyplot platform.

Public analytics and discovery features that leverage aggregated database data:
- Dashboard: Rich platform statistics and visualizations
- Plot of the Day: Daily featured high-quality implementation
- Related Plots: Tag-based similarity recommendations
- Visitors: unique visitors per day from Plausible
- Machine readers: verified crawler and AI assistant reads per day from the machine-read telemetry
"""

from __future__ import annotations

import asyncio
import hashlib
import logging
import random
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from zoneinfo import ZoneInfo

import httpx
from fastapi import APIRouter, Depends, Query
from fastapi.concurrency import run_in_threadpool
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from api.agent_usage import DATASET_PATTERN, usage_query
from api.cache import cache_key, get_or_set_cache
from api.dependencies import require_db
from api.machine_reads_query import MachineReadersResponse, empty_public, read_public
from api.shared_links import SharedLinksResponse, load_public
from core.config import settings
from core.constants import LIBRARY_NAMES, SUPPORTED_LIBRARIES
from core.database import ImplRepository, Spec, SpecRepository, is_db_configured
from core.database.connection import get_db_context
from core.utils import strip_noqa_comments


logger = logging.getLogger(__name__)


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
    spec_description: str | None = None
    library_id: str
    language: str
    quality_score: float
    # `preview_url` is the legacy single-theme field (a synonym for the light
    # variant). The stats page picks a thumbnail per theme, so both variants
    # have to travel with the payload — without `preview_url_dark` the grid
    # falls back to the light render on a dark page.
    preview_url: str | None = None
    preview_url_light: str | None = None
    preview_url_dark: str | None = None


class TimelinePoint(BaseModel):
    """Monthly implementation count."""

    month: str  # "2025-01"
    count: int


class DailyImplPoint(BaseModel):
    """Implementation updates on a single day (last-28-days timeline).

    Window matches the visitors chart on the stats page so the two strips
    read side-by-side. Distinct from `debug.DailyImplPoint` (which uses
    `impls_updated`) — kept separate because the public dashboard's consumer
    is the stats page bundle, not the admin debug view, and `count` is
    consistent with `TimelinePoint`.
    """

    date: str  # ISO "YYYY-MM-DD"
    count: int


# The Plausible site's reporting time zone, read through the Sites API on 2026-11-20. Plausible's
# `time:day` buckets and `date_range` dates are days of that zone, so the visitors tile takes its
# today there. It must match the site's setting in Plausible.
#
# `tzdata` is a direct dependency (pyproject.toml) for this zone: `zoneinfo` reads the system's
# time zone database first and falls back to that package, and the API's slim base image need not
# ship a system database. Without either, the fetch answers no days (`_fetch_plausible_visitors`).
PLAUSIBLE_TIMEZONE = "Europe/Zurich"

# The first full day of the `stayed_10s` event, in the site's time zone. The deploy that began
# sending it finished on 2026-11-14 at 22:17 UTC, 23:17 in Zurich, so that day holds only the
# visits of its last 43 minutes or so and would count too few.
ENGAGED_SINCE = date(2026, 11, 15)


class VisitorPoint(BaseModel):
    """One day of the site's visitors, sourced from Plausible: a day of `PLAUSIBLE_TIMEZONE`, not a UTC day.

    `engaged` is the day's unique visitors who had the site in front of them for ten seconds of a
    visit and used a pointer, a finger or a key in it, before the ten seconds or after them: the
    visitors with a `stayed_10s` event whose `input` is `yes`. A visitor who left within ten seconds
    or did nothing is a reader who found what they came for, or automated traffic that runs the
    page's scripts. It is never more than the day's `visitors`, and `None` for a day before
    `ENGAGED_SINCE` and for every day when Plausible did not answer that count.
    """

    date: str  # ISO "YYYY-MM-DD"
    visitors: int
    visits: int = 0
    engaged: int | None = None


class VisitorsResponse(BaseModel):
    """The site's visitors per day for the public stats page."""

    points: list[VisitorPoint]
    engaged_since: str = ENGAGED_SINCE.isoformat()


class DashboardResponse(BaseModel):
    """Full dashboard statistics."""

    total_specs: int
    total_implementations: int
    total_interactive: int
    total_lines_of_code: int
    avg_quality_score: float | None
    coverage_percent: float
    # Number of supported libraries — the denominator behind `coverage_percent`
    # and the per-spec coverage cells. Served so clients never hardcode it.
    total_libraries: int

    library_stats: list[LibraryDashboardStats]
    coverage_matrix: list[CoverageRow]
    top_implementations: list[TopImpl]
    tag_distribution: dict[str, dict[str, int]]
    score_distribution: dict[str, int]
    timeline: list[TimelinePoint]
    daily_impls: list[DailyImplPoint]  # Last 28 days, zero-filled


class PlotOfTheDayResponse(BaseModel):
    """Daily featured plot."""

    spec_id: str
    spec_title: str
    description: str | None = None
    library_id: str
    library_name: str
    language: str
    quality_score: float
    preview_url: str | None = None
    preview_url_light: str | None = None
    preview_url_dark: str | None = None
    image_description: str | None = None
    code: str | None = None
    library_version: str | None = None
    python_version: str | None = None
    language_version: str | None = None
    date: str


class RelatedSpecItem(BaseModel):
    """A related spec with similarity info."""

    id: str
    title: str
    preview_url: str | None = None
    preview_url_light: str | None = None
    preview_url_dark: str | None = None
    library_id: str | None = None
    language: str | None = None
    similarity: float
    shared_tags: list[str]


class RelatedSpecsResponse(BaseModel):
    """Related specs for a given spec."""

    related: list[RelatedSpecItem]


# =============================================================================
# Shared helpers
# =============================================================================


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
    library_counts = dict.fromkeys(SUPPORTED_LIBRARIES, 0)

    tag_counter: dict[str, Counter[str]] = defaultdict(Counter)
    monthly_counts: Counter[str] = Counter()
    daily_counts: Counter[str] = Counter()
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
                            spec_description=spec.description,
                            library_id=lib_id,
                            language=impl.library.language if impl.library else "python",
                            quality_score=score,
                            preview_url=impl.preview_url,
                            preview_url_light=impl.preview_url_light,
                            preview_url_dark=impl.preview_url_dark,
                        )
                    )

            # Timeline from generated_at (datetime field, not string)
            gen_dt = impl.generated_at
            if gen_dt:
                monthly_counts[gen_dt.strftime("%Y-%m")] += 1

            # Daily-impls timeline matches the debug page: count by `updated`
            # so any re-generation/quality re-review of an existing impl is
            # reflected on the day it actually moved, not on its first build.
            upd_dt = impl.updated
            if upd_dt:
                daily_counts[upd_dt.date().isoformat()] += 1

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

    # Daily impls for the last 28 days, zero-filled. Window matches the
    # visitors chart on the stats page so the two strips read side-by-side.
    today = datetime.now(timezone.utc).date()
    daily_impls = [
        DailyImplPoint(
            date=(today - timedelta(days=offset)).isoformat(),
            count=daily_counts.get((today - timedelta(days=offset)).isoformat(), 0),
        )
        for offset in range(27, -1, -1)
    ]

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
        total_libraries=len(SUPPORTED_LIBRARIES),
        library_stats=lib_stats,
        coverage_matrix=coverage_rows,
        top_implementations=top_impls,
        tag_distribution={cat: dict(counter.most_common(20)) for cat, counter in sorted(tag_counter.items())},
        score_distribution=score_dist,
        timeline=timeline,
        daily_impls=daily_impls,
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


POTD_FEATURED_MIN_SCORE = 92.0
"""Implementations at or above this score, of specs that are not a `-basic` variant, form the featured pool."""
POTD_EPOCH = date(2026, 1, 1)
"""Day 0 of the rotation: day N picks the (N mod pool size)-th spec of the current cycle's order."""

PotdCandidate = tuple[str, str, str, str, str, float, str, str | None]
"""(spec_id, spec_title, description, library_id, language, quality_score, preview_url, preview_url_dark)."""


def _digest(text: str) -> int:
    return int(hashlib.sha256(text.encode()).hexdigest(), 16)


def _pick_potd(candidates: list[PotdCandidate], today: date) -> PotdCandidate:
    """The plot of the day: a rotation over the featured specs, then one of the spec's featured libraries.

    The featured pool holds implementations scored at least `POTD_FEATURED_MIN_SCORE` of
    specs that are not a `-basic` variant (a plain scatter or bar chart makes a dull
    front page); without any, every candidate qualifies. Each cycle of as many days as
    the pool has specs walks the specs in an order shuffled per cycle, so no spec
    repeats within a cycle while the catalogue stays the same; the library is then
    drawn per day among that spec's featured implementations, so the library varies too.
    """
    featured = [c for c in candidates if c[5] >= POTD_FEATURED_MIN_SCORE and not c[0].endswith("-basic")]
    by_spec: dict[str, list[PotdCandidate]] = {}
    for candidate in featured or candidates:
        by_spec.setdefault(candidate[0], []).append(candidate)
    cycle, offset = divmod((today - POTD_EPOCH).days, len(by_spec))
    order = sorted(by_spec, key=lambda spec: _digest(f"potd:{cycle}:{spec}"))
    spec_id = order[offset]
    impls = sorted(by_spec[spec_id], key=lambda c: c[3])
    return impls[_digest(f"potd:{today.isoformat()}:{spec_id}") % len(impls)]


async def _refresh_potd() -> PlotOfTheDayResponse | None:
    """Standalone factory for background refresh."""
    async with get_db_context() as db:
        return await _build_potd(SpecRepository(db), ImplRepository(db))


async def _build_potd(spec_repo: SpecRepository, impl_repo: ImplRepository) -> PlotOfTheDayResponse | None:
    """Select the plot of the day deterministically."""
    all_specs = await spec_repo.get_all()
    today = date.today().isoformat()

    # Collect candidates: implementations with quality_score >= 90 (lightweight, no code loaded)
    candidates: list[PotdCandidate] = []
    for spec in all_specs:
        for impl in spec.impls:
            if impl.quality_score is not None and impl.quality_score >= 90 and impl.preview_url:
                candidates.append(
                    (
                        spec.id,
                        spec.title,
                        spec.description or "",
                        impl.library_id,
                        # The row's own key, which the lookup of the pick's code below needs.
                        impl.language_id,
                        impl.quality_score,
                        impl.preview_url,
                        impl.preview_url_dark,
                    )
                )

    if not candidates:
        return None

    spec_id, spec_title, description, library_id, language, quality_score, preview_url, preview_url_dark = _pick_potd(
        candidates, date.fromisoformat(today)
    )

    # Load deferred fields (code, image_description) for just this one impl
    full_impl = await impl_repo.get_by_spec_and_library(spec_id, library_id, language)

    # Prefer preview URLs from the fresh per-impl load so they can't drift from
    # the code/metadata below; the candidate-snapshot values are the fallback.
    if full_impl:
        preview_url = full_impl.preview_url_light or preview_url
        preview_url_dark = full_impl.preview_url_dark or preview_url_dark

    return PlotOfTheDayResponse(
        spec_id=spec_id,
        spec_title=spec_title,
        description=description,
        library_id=library_id,
        library_name=LIBRARY_NAMES.get(library_id, library_id),
        language=language,
        quality_score=quality_score,
        preview_url=preview_url,
        preview_url_light=preview_url,
        preview_url_dark=preview_url_dark,
        image_description=full_impl.review_image_description if full_impl else None,
        code=strip_noqa_comments(full_impl.code) if full_impl and full_impl.code else None,
        library_version=full_impl.library_version if full_impl else None,
        python_version=full_impl.python_version if full_impl else None,
        language_version=(full_impl.language_version or full_impl.python_version) if full_impl else None,
        date=today,
    )


@router.get("/plot-of-the-day", response_model=PlotOfTheDayResponse | None)
async def get_plot_of_the_day(db: AsyncSession = Depends(require_db)) -> PlotOfTheDayResponse | None:
    """
    Get the featured plot of the day.

    Deterministically selects a high-quality implementation (score >= 90) based on
    today's date, preferring the featured pool (score >= 92, no `-basic` spec) and
    rotating through its specs without repeats (`_pick_potd`). Returns the same
    result for the entire day.
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


@dataclass(frozen=True, eq=False)
class _RelatedEntry:
    """One spec as the related-plots ranking reads it: plain values, no ORM objects.

    `preview` is the best-scored implementation that has a preview, as
    `(preview_url, preview_url_light, preview_url_dark, library_id, language)`.
    """

    id: str
    title: str
    spec_tags: frozenset[str]
    impl_tags: dict[str, frozenset[str]]
    all_tags: frozenset[str]
    preview: tuple[str | None, str | None, str | None, str, str | None] | None

    def tags(self, mode: str, library: str | None) -> frozenset[str]:
        """The tags to compare: spec tags, plus impl tags in full mode (one library's, or all)."""
        if mode != "full":
            return self.spec_tags
        if library:
            return self.spec_tags | self.impl_tags.get(library, frozenset())
        return self.all_tags


def _related_entry(spec: Spec) -> _RelatedEntry:
    spec_tags = frozenset(_flatten_tags(spec.tags))
    # Union per library: the unique key is (spec, language, library), so one library may appear twice.
    impl_tags: dict[str, frozenset[str]] = {}
    for impl in spec.impls:
        if impl.impl_tags and isinstance(impl.impl_tags, dict):
            impl_tags[impl.library_id] = impl_tags.get(impl.library_id, frozenset()) | _flatten_tags(impl.impl_tags)
    impls_with_preview = [i for i in spec.impls if i.preview_url]
    best = max(impls_with_preview, key=lambda i: i.quality_score or 0) if impls_with_preview else None
    return _RelatedEntry(
        id=spec.id,
        title=spec.title,
        spec_tags=spec_tags,
        impl_tags=impl_tags,
        all_tags=spec_tags.union(*impl_tags.values()),
        preview=(
            (
                best.preview_url,
                best.preview_url_light,
                best.preview_url_dark,
                best.library_id,
                best.library.language if best.library else None,
            )
            if best
            else None
        ),
    )


async def _load_related_index(repo: SpecRepository) -> list[_RelatedEntry]:
    return [_related_entry(spec) for spec in await repo.get_all()]


async def _refresh_related_index() -> list[_RelatedEntry]:
    """Standalone factory for background refresh."""
    async with get_db_context() as db:
        return await _load_related_index(SpecRepository(db))


def _build_related(
    index: list[_RelatedEntry], spec_id: str, limit: int, mode: str, library: str | None = None
) -> RelatedSpecsResponse:
    """Find related specs using Jaccard similarity on tags.

    mode="spec": only spec-level tags (for overview page)
    mode="full": spec + impl tags for the given library (for impl detail page)
    """
    target = next((entry for entry in index if entry.id == spec_id), None)
    if target is None:
        return RelatedSpecsResponse(related=[])

    target_tags = target.tags(mode, library)
    if not target_tags:
        return RelatedSpecsResponse(related=[])

    # Compute similarity for all other specs
    scored: list[tuple[float, list[str], _RelatedEntry]] = []
    for spec in index:
        if spec.id == spec_id:
            continue
        other_tags = spec.tags(mode, library)
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
        # Group by rounded similarity, shuffle within groups
        seed = int(hashlib.md5(spec_id.encode()).hexdigest(), 16) % (2**32)  # noqa: S324
        rng = random.Random(seed)
        rng.shuffle(top_pool)
        # Re-sort but with jitter: high similarity still wins, just not deterministic order
        top_pool.sort(key=lambda x: x[0] + rng.uniform(0, 0.05), reverse=True)

    # Build response with best-quality preview per spec
    related: list[RelatedSpecItem] = []
    for similarity, shared_tags, spec in top_pool[:limit]:
        preview_url, preview_url_light, preview_url_dark, library_id, language = spec.preview or (None,) * 5
        related.append(
            RelatedSpecItem(
                id=spec.id,
                title=spec.title,
                preview_url=preview_url,
                preview_url_light=preview_url_light,
                preview_url_dark=preview_url_dark,
                library_id=library_id,
                language=language,
                similarity=round(similarity, 3),
                shared_tags=shared_tags,
            )
        )

    return RelatedSpecsResponse(related=related)


@router.get("/related/{spec_id}", response_model=RelatedSpecsResponse)
async def get_related_specs(
    spec_id: str,
    limit: int = Query(default=6, ge=1, le=24),
    mode: str = Query(default="spec", pattern="^(spec|full)$"),
    library: str | None = Query(default=None),
    db: AsyncSession = Depends(require_db),
) -> RelatedSpecsResponse:
    """
    Get specs related to the given spec, based on tag similarity.

    mode=spec: only spec-level tags (plot_type, domain, etc.)
    mode=full: spec tags + impl tags for the given library
    library: in full mode, use this library's impl_tags (required for accurate tag matching)

    The catalogue is cached once as a plain-value index under a single key and every
    request ranks against it in memory. A response cache keyed per spec, library, mode
    and limit had thousands of keys, which evicted each other from the shared cache, so
    nearly every call reloaded all specs from the database.
    """
    repo = SpecRepository(db)

    async def _fetch_index() -> list[_RelatedEntry]:
        return await _load_related_index(repo)

    index = await get_or_set_cache(
        cache_key("insights", "related_index"),
        _fetch_index,
        refresh_after=settings.cache_refresh_after,
        refresh_factory=_refresh_related_index,
    )
    return _build_related(index, spec_id, limit, mode, library)


# =============================================================================
# 4. Plausible Visitors
# =============================================================================


# The visitors the stats page draws: a `stayed_10s` event with `input=yes`. The tracker sends
# that once per visit at most, at ten seconds when the visitor did something before them, or at
# the first input after them (`app/src/analytics/stay.ts`). The filter names the event, not its
# goal: a goal filter matches the goal's display name in the dashboard, so renaming the goal there
# would break the count. Both gave the same per-day counts on the live API on 2026-11-20.
#
# A `yes` also carries `actions`, the kinds of input that made it count, joined with `+` in a fixed
# order (`move+press+wheel`; `STAY_ACTIONS` in `app/src/analytics/stay.ts`). Should one kind start
# to fire by itself, `["is_not", "event:props:actions", ["<kind>"]]` added here leaves out the
# visitors whose only kind it is, and `["contains", "event:props:actions", ["<kind>"]]` finds every
# visit with it. Events sent before `actions` was deployed have none and stay counted.
STAYED_WITH_INPUT = [["is", "event:name", ["stayed_10s"]], ["is", "event:props:input", ["yes"]]]

# A Plausible day's metrics as numbers, by ISO date.
_PlausibleDays = dict[str, list[float | None]]


def _number(value: object) -> float | None:
    """A metric as a number, or `None` for anything else, such as a rate with nothing to divide."""
    return float(value) if isinstance(value, int | float) and not isinstance(value, bool) else None


def _count(metrics: list[float | None] | None, index: int) -> int:
    """A count from a day's metrics: zero for a day without a row, and for a metric it lacks or that is no number."""
    value = metrics[index] if metrics is not None and index < len(metrics) else None
    return max(0, int(value or 0))


async def _plausible_days(client: httpx.AsyncClient, query: dict[str, object]) -> _PlausibleDays:
    """One Stats API v2 query by `time:day`: each day's metrics, by its ISO date.

    Raises when the call fails, Plausible refuses the query, or the answer is not the documented shape.
    """
    resp = await client.post(
        settings.plausible_api_url,
        headers={"Authorization": f"Bearer {settings.plausible_api_key}", "Content-Type": "application/json"},
        json=query,
    )
    resp.raise_for_status()
    days: _PlausibleDays = {}
    # Plausible v2 response: {"results": [{"dimensions": ["YYYY-MM-DD"], "metrics": [...]}, ...]}
    for row in resp.json().get("results", []):
        dims = row.get("dimensions") or []
        metrics = row.get("metrics") or []
        if not dims or not metrics:
            continue
        # The time:day dimension can come back as "YYYY-MM-DD" or an ISO datetime —
        # normalize to a plain ISO date so the join with the zero-filled axis works.
        days[str(dims[0])[:10]] = [_number(value) for value in metrics]
    return days


def _failure(exc: BaseException) -> str:
    """What a failed query says in the log: for a refused one its status and the start of Plausible's answer,
    which names a filter it cannot answer; otherwise the kind of error."""
    if isinstance(exc, httpx.HTTPStatusError):
        return f"HTTP {exc.response.status_code}: {exc.response.text[:300]}"
    return type(exc).__name__


async def _fetch_plausible_visitors() -> VisitorsResponse:
    """Query the Plausible Stats API v2 for visitors, visits and engaged visitors per day (last 28d).

    Two queries over the same days, sent together: unique visitors and visits, and the unique visitors
    with `STAYED_WITH_INPUT`, a day's `engaged` from `ENGAGED_SINCE` on. The stats page draws those once
    every day of its window has them: a crawler farm that runs the page's scripts inflates the visitors,
    seldom stays ten seconds and does nothing when it does, so it leaves the engaged ones alone. When the
    second query fails, no day has engaged visitors and the page draws the unique visitors.

    The 28-day window ends on today (inclusive) so the rightmost bar reflects
    current-day traffic as a partial day, matching how Plausible's dashboard
    "Last 28 days" view renders. Its days are the Plausible site's (`PLAUSIBLE_TIMEZONE`),
    so today is taken there: just after midnight in that zone, the UTC date is still yesterday's.

    Note: we deliberately do NOT use Plausible's `"28d"` preset because it
    maps to `[today-28, today-1]` (the source uses `last = today - 1 day`,
    see plausible/analytics PR #5282), which excludes today and left the
    rightmost chart bar permanently at 0. An explicit `[today-27, today]`
    custom range pulls today's partial row in.

    Returns an empty `points` list when the API key is not configured, the time
    zone cannot be resolved, or the first query fails — the stats page treats `points: []` as "no data" and
    renders a placeholder instead of an all-zero chart, so we can distinguish
    real zeros (Plausible returned 0 visitors for a day) from missing data.
    On a successful fetch the response is zero-filled across all 28 days so
    the chart has a stable 28-bar width even for days Plausible has no row for.
    """
    if not settings.plausible_api_key:
        return VisitorsResponse(points=[])

    totals: _PlausibleDays | BaseException
    engaged: _PlausibleDays | BaseException
    try:
        # The zone is resolved inside the error handling: a time zone database that cannot be found
        # answers no days, as an outage does, and not an error of the endpoint.
        today = datetime.now(ZoneInfo(PLAUSIBLE_TIMEZONE)).date()
        start = today - timedelta(days=27)
        window: dict[str, object] = {
            "site_id": settings.plausible_site_id,
            "date_range": [start.isoformat(), today.isoformat()],
            "dimensions": ["time:day"],
        }
        async with httpx.AsyncClient(timeout=10.0) as client:
            totals, engaged = await asyncio.gather(
                _plausible_days(client, {**window, "metrics": ["visitors", "visits"]}),
                _plausible_days(client, {**window, "metrics": ["visitors"], "filters": STAYED_WITH_INPUT}),
                return_exceptions=True,
            )
    except Exception as exc:  # no time zone, or the client itself failed: neither query has an answer
        totals = engaged = exc
    if isinstance(totals, BaseException):
        logger.warning(
            "Plausible visitors fetch failed (returning empty series): %s", _failure(totals), exc_info=totals
        )
        return VisitorsResponse(points=[])
    engaged_days = None if isinstance(engaged, BaseException) else engaged
    if isinstance(engaged, BaseException):
        logger.warning(
            "Plausible engaged visitors fetch failed (no day has engaged visitors): %s",
            _failure(engaged),
            exc_info=engaged,
        )

    points = []
    for offset in range(27, -1, -1):
        day = today - timedelta(days=offset)
        key = day.isoformat()
        visitors = _count(totals.get(key), 0)
        engaged_count = None
        if engaged_days is not None and day >= ENGAGED_SINCE:
            # A day without a row in a query that answered had no such visitor; a count above the
            # day's unique visitors cannot be, and is cut to them.
            engaged_count = min(visitors, _count(engaged_days.get(key), 0))
        points.append(
            VisitorPoint(date=key, visitors=visitors, visits=_count(totals.get(key), 1), engaged=engaged_count)
        )
    return VisitorsResponse(points=points)


@router.get("/visitors", response_model=VisitorsResponse)
async def get_visitors() -> VisitorsResponse:
    """Get visitors, visits and engaged visitors per day for the last 28 days (Plausible Stats API).

    A point's `engaged` is its unique visitors who stayed ten seconds of a visit and did something
    in it, before the ten seconds or after them; `None` before `engaged_since` (`ENGAGED_SINCE`)
    and for every day when Plausible did not answer that count.

    Cached for ~1h via stale-while-revalidate so we stay well under Plausible's
    600-req/h rate limit even under traffic spikes on the public stats page.
    """
    return await get_or_set_cache(
        cache_key("insights", "visitors", "28d"),
        _fetch_plausible_visitors,
        refresh_after=3600,
        refresh_factory=_fetch_plausible_visitors,
    )


# =============================================================================
# 5. Machine readers
# =============================================================================


def _read_machine_readers(dataset: str) -> MachineReadersResponse:
    """The tile's numbers from BigQuery; raises when the client cannot start or the query fails."""
    return read_public(usage_query(dataset), dataset)


@router.get("/machine-readers", response_model=MachineReadersResponse)
async def get_machine_readers() -> MachineReadersResponse:
    """Verified crawler and AI assistant reads per UTC day for the last 28 days (machine-read telemetry).

    Counts only, from the content-free lines in BigQuery (`api/machine_reads_query.py`,
    `docs/reference/machine-readers.md`). `not_configured` while `MACHINE_READS_DATASET` is unset or no dataset
    name; `unavailable` when BigQuery does not answer, never kept, so the next load tries again. An answer is kept
    and refreshed in the background after an hour; a failed refresh keeps the last answer.
    """
    dataset = settings.machine_reads_dataset
    if not dataset or not DATASET_PATTERN.fullmatch(dataset):
        return empty_public("not_configured")

    async def _fetch() -> MachineReadersResponse:
        return await run_in_threadpool(_read_machine_readers, dataset)

    try:
        return await get_or_set_cache(
            cache_key("insights", "machine-readers", "28d"), _fetch, refresh_after=3600, refresh_factory=_fetch
        )
    except Exception as exc:  # a cold miss that failed: answered, never kept
        logger.warning("machine readers query failed: %s", type(exc).__name__)
        return empty_public("unavailable")


# =============================================================================
# 6. Shared links
# =============================================================================


@router.get("/shared-links", response_model=SharedLinksResponse)
async def get_shared_links() -> SharedLinksResponse:
    """Links to the site shared per UTC day for the last 28 days, by platform, and the most shared specs and libraries.

    Counts only, from the share counters (`api/shared_links.py`, `docs/reference/plausible.md`): a share is the
    fetch of a page's preview image by a messenger or a social network. Fetches by other clients are not in these
    numbers. Every platform says which part of its shares Cloudflare verified; the rest counts all the same, because
    an app that fetches from the sender's phone is never verified. `not_configured` without a database; `unavailable` when it does not answer or the table is not there
    yet, never kept, so the next load tries again. An answer is kept and refreshed in the background after an
    hour; a failed refresh keeps the last answer.
    """
    if not is_db_configured():
        return SharedLinksResponse(status="not_configured")
    try:
        return await get_or_set_cache(
            cache_key("insights", "shared-links", "28d"), load_public, refresh_after=3600, refresh_factory=load_public
        )
    except Exception as exc:  # a cold miss that failed: answered, never kept
        logger.warning("shared links query failed: %s", type(exc).__name__)
        return SharedLinksResponse(status="unavailable")
