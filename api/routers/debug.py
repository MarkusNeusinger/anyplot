"""Debug endpoints for internal monitoring."""

from __future__ import annotations

import secrets
import time
from collections import Counter
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from api.cache import clear_cache, get_cache_stats
from api.dependencies import require_db
from core.config import settings
from core.constants import SUPPORTED_LIBRARIES
from core.database import SpecRepository


router = APIRouter(prefix="/debug", tags=["debug"])


def require_admin(x_admin_token: str | None = Header(default=None)) -> None:
    """Gate sensitive /debug/* endpoints behind a shared secret.

    Without this gate, /debug/status and /debug/ping reflect quality scores,
    weakness aggregates, and DB latency to the public internet. When
    settings.admin_token is unset the endpoint is disabled (503), so a
    misconfigured prod deploy fails closed instead of fails open.
    """
    expected = settings.admin_token
    if not expected:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Debug endpoints not configured")
    if not secrets.compare_digest(x_admin_token or "", expected):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid admin token")


# Threshold for identifying specs that weren't auto-approved (matches workflow ai-approved threshold)
LOW_SCORE_THRESHOLD = 90


# ============================================================================
# Response Models
# ============================================================================


class SpecStatusItem(BaseModel):
    """Status for a single specification with library scores."""

    id: str
    title: str
    updated: str | None
    avg_score: float | None = None
    # Library scores - None means no implementation
    altair: float | None = None
    bokeh: float | None = None
    highcharts: float | None = None
    letsplot: float | None = None
    matplotlib: float | None = None
    plotly: float | None = None
    plotnine: float | None = None
    pygal: float | None = None
    seaborn: float | None = None


class LibraryStats(BaseModel):
    """Statistics for a single library."""

    id: str
    name: str
    impl_count: int
    avg_score: float | None
    min_score: float | None
    max_score: float | None


class ProblemSpec(BaseModel):
    """A spec with issues."""

    id: str
    title: str
    issue: str  # Description of the problem
    value: str | None = None  # Optional value (e.g., score, date)


class SystemHealth(BaseModel):
    """System health information."""

    database_connected: bool
    api_response_time_ms: float
    timestamp: str
    total_specs_in_db: int
    total_impls_in_db: int


class DailyImplPoint(BaseModel):
    """Count of implementations updated on a single day."""

    date: str  # ISO "YYYY-MM-DD"
    impls_updated: int


class RecentActivity(BaseModel):
    """A single recent implementation update entry."""

    spec_id: str
    spec_title: str
    library_id: str
    quality_score: float | None
    generated_by: str | None
    updated: str  # ISO datetime


class WeaknessCount(BaseModel):
    """Aggregated occurrence of a weakness string across all impls."""

    text: str
    count: int


class DebugStatusResponse(BaseModel):
    """Debug dashboard data."""

    # Summary
    total_specs: int
    total_implementations: int
    coverage_percent: float

    # Library statistics
    library_stats: list[LibraryStats]

    # Problem areas
    low_score_specs: list[ProblemSpec]  # Specs with avg score < 85
    oldest_specs: list[ProblemSpec]  # 10 oldest specs
    missing_preview_specs: list[ProblemSpec]  # Specs with missing GCS images
    missing_tags_specs: list[ProblemSpec]  # Specs without tags

    # Daily activity / recency / weakness trends
    daily_impls: list[DailyImplPoint]  # Last 30 days, filled with 0 for empty days
    recent_activity: list[RecentActivity]  # Last 15 impl updates (DESC)
    common_weaknesses: list[WeaknessCount]  # Top 10 weakness strings

    # System health
    system: SystemHealth

    # All specs for table
    specs: list[SpecStatusItem]


# ============================================================================
# Endpoint
# ============================================================================


@router.get("/status", response_model=DebugStatusResponse, dependencies=[Depends(require_admin)])
async def get_debug_status(request: Request, db: AsyncSession = Depends(require_db)) -> DebugStatusResponse:
    """
    Get comprehensive debug dashboard data.

    Includes:
    - All specs with quality scores per library
    - Library statistics (avg/min/max scores, coverage)
    - Problem specs (low scores, old, missing data)
    - System health info
    """
    start_time = time.time()

    repo = SpecRepository(db)
    all_specs = await repo.get_all()

    # ========================================================================
    # Build specs list and collect statistics
    # ========================================================================

    specs_status: list[SpecStatusItem] = []
    total_implementations = 0

    # Library aggregates
    library_scores: dict[str, list[float]] = {lib: [] for lib in SUPPORTED_LIBRARIES}
    library_counts: dict[str, int] = dict.fromkeys(SUPPORTED_LIBRARIES, 0)  # type: ignore[arg-type]

    # Problem tracking
    missing_preview: list[ProblemSpec] = []
    missing_tags: list[ProblemSpec] = []

    # Daily activity / recency / weakness tracking
    daily_counter: Counter[str] = Counter()
    weakness_counter: Counter[str] = Counter()
    activity_items: list[RecentActivity] = []

    for spec in all_specs:
        # Build library score map for this spec
        spec_scores: dict[str, float | None] = dict.fromkeys(SUPPORTED_LIBRARIES, None)
        spec_score_values: list[float] = []

        for impl in spec.impls:
            lib_id = impl.library_id
            score = impl.quality_score

            spec_scores[lib_id] = score
            total_implementations += 1
            library_counts[lib_id] += 1

            if score is not None:
                library_scores[lib_id].append(score)
                spec_score_values.append(score)

            # Check for missing preview
            if not impl.preview_url:
                missing_preview.append(ProblemSpec(id=spec.id, title=spec.title, issue=f"Missing preview for {lib_id}"))

            # Daily activity + recent activity
            if impl.updated:
                daily_counter[impl.updated.date().isoformat()] += 1
                activity_items.append(
                    RecentActivity(
                        spec_id=spec.id,
                        spec_title=spec.title,
                        library_id=lib_id,
                        quality_score=score,
                        generated_by=impl.generated_by,
                        updated=impl.updated.isoformat(),
                    )
                )

            # Weakness tally (normalize: strip + casefold)
            for w in impl.review_weaknesses or []:
                key = (w or "").strip()
                if key:
                    weakness_counter[key.casefold()] += 1

        # Calculate average score for this spec
        avg_score = sum(spec_score_values) / len(spec_score_values) if spec_score_values else None

        # Find most recent update
        timestamps = [spec.updated] if spec.updated else []
        timestamps.extend(impl.updated for impl in spec.impls if impl.updated)
        most_recent = max(timestamps) if timestamps else None

        # Check for missing tags
        if not spec.tags or not any(spec.tags.values()):
            missing_tags.append(ProblemSpec(id=spec.id, title=spec.title, issue="No tags defined"))

        specs_status.append(
            SpecStatusItem(
                id=spec.id,
                title=spec.title,
                updated=most_recent.isoformat() if most_recent else None,
                avg_score=round(avg_score, 1) if avg_score else None,
                altair=spec_scores.get("altair"),
                bokeh=spec_scores.get("bokeh"),
                highcharts=spec_scores.get("highcharts"),
                letsplot=spec_scores.get("letsplot"),
                matplotlib=spec_scores.get("matplotlib"),
                plotly=spec_scores.get("plotly"),
                plotnine=spec_scores.get("plotnine"),
                pygal=spec_scores.get("pygal"),
                seaborn=spec_scores.get("seaborn"),
            )
        )

    # Sort by updated (most recent first)
    specs_status.sort(key=lambda s: (s.updated or "", s.id), reverse=True)

    # ========================================================================
    # Library Statistics
    # ========================================================================

    library_names = {
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

    lib_stats: list[LibraryStats] = []
    for lib_id in sorted(SUPPORTED_LIBRARIES):
        scores = library_scores[lib_id]
        lib_stats.append(
            LibraryStats(
                id=lib_id,
                name=library_names.get(lib_id, lib_id),
                impl_count=library_counts[lib_id],
                avg_score=round(sum(scores) / len(scores), 1) if scores else None,
                min_score=round(min(scores), 1) if scores else None,
                max_score=round(max(scores), 1) if scores else None,
            )
        )

    # Sort by impl_count descending
    lib_stats.sort(key=lambda x: x.impl_count, reverse=True)

    # ========================================================================
    # Problem Specs
    # ========================================================================

    # Low score specs (avg < LOW_SCORE_THRESHOLD)
    low_score_specs: list[ProblemSpec] = []
    for spec in specs_status:
        if spec.avg_score is not None and spec.avg_score < LOW_SCORE_THRESHOLD:
            low_score_specs.append(
                ProblemSpec(id=spec.id, title=spec.title, issue="Low average score", value=f"{spec.avg_score:.1f}")
            )
    low_score_specs.sort(key=lambda x: float(x.value or 0))  # Lowest first

    # Oldest specs (by updated timestamp) — only consider specs with a timestamp
    specs_with_updated = [s for s in specs_status if s.updated]
    specs_by_age = sorted(specs_with_updated, key=lambda s: s.updated or "")
    oldest_specs: list[ProblemSpec] = []
    for spec in specs_by_age[:10]:  # 10 oldest
        if spec.updated:
            try:
                dt = datetime.fromisoformat(spec.updated.replace("Z", "+00:00"))
                # Ensure dt is timezone-aware
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=timezone.utc)
                age_days = (datetime.now(timezone.utc) - dt).days
                oldest_specs.append(
                    ProblemSpec(id=spec.id, title=spec.title, issue="Old spec", value=f"{age_days} days ago")
                )
            except ValueError:
                # Skip specs with unparseable timestamps
                pass

    # ========================================================================
    # Daily activity (last 30 days, zero-filled)
    # ========================================================================

    today = datetime.now(timezone.utc).date()
    daily_impls: list[DailyImplPoint] = []
    for offset in range(29, -1, -1):
        day = (today - timedelta(days=offset)).isoformat()
        daily_impls.append(DailyImplPoint(date=day, impls_updated=daily_counter.get(day, 0)))

    # ========================================================================
    # Recent activity (top 15 by updated DESC)
    # ========================================================================

    activity_items.sort(key=lambda a: a.updated, reverse=True)
    recent_activity = activity_items[:15]

    # ========================================================================
    # Common weaknesses (top 10)
    # ========================================================================

    common_weaknesses = [WeaknessCount(text=text, count=count) for text, count in weakness_counter.most_common(10)]

    # ========================================================================
    # System Health
    # ========================================================================

    response_time_ms = (time.time() - start_time) * 1000
    coverage = (total_implementations / (len(all_specs) * 9) * 100) if all_specs else 0

    system_health = SystemHealth(
        database_connected=True,
        api_response_time_ms=round(response_time_ms, 2),
        timestamp=datetime.now(timezone.utc).isoformat(),
        total_specs_in_db=len(all_specs),
        total_impls_in_db=total_implementations,
    )

    # ========================================================================
    # Return Response
    # ========================================================================

    return DebugStatusResponse(
        total_specs=len(all_specs),
        total_implementations=total_implementations,
        coverage_percent=round(coverage, 1),
        library_stats=lib_stats,
        low_score_specs=low_score_specs[:20],  # Limit to 20
        oldest_specs=oldest_specs,
        missing_preview_specs=missing_preview[:20],  # Limit to 20
        missing_tags_specs=missing_tags[:20],  # Limit to 20
        daily_impls=daily_impls,
        recent_activity=recent_activity,
        common_weaknesses=common_weaknesses,
        system=system_health,
        specs=specs_status,
    )


class PingResponse(BaseModel):
    """Lightweight DB round-trip measurement for response-time polling."""

    database_connected: bool
    response_time_ms: float
    timestamp: str


@router.get("/ping", response_model=PingResponse, dependencies=[Depends(require_admin)])
async def ping(db: AsyncSession = Depends(require_db)) -> PingResponse:
    """Ping the database with SELECT 1 and report round-trip latency.

    Intended for the debug dashboard's rolling response-time chart — cheap enough
    to poll every few seconds.
    """
    start = time.time()
    connected = True
    try:
        await db.execute(text("SELECT 1"))
    except Exception:
        connected = False
    return PingResponse(
        database_connected=connected,
        response_time_ms=round((time.time() - start) * 1000, 2),
        timestamp=datetime.now(timezone.utc).isoformat(),
    )


class CacheInvalidateResponse(BaseModel):
    cleared: int
    maxsize: int
    ttl: int


@router.post("/cache/invalidate", response_model=CacheInvalidateResponse)
async def invalidate_cache(x_cache_token: str | None = Header(default=None)) -> CacheInvalidateResponse:
    """Flush the in-memory response cache.

    Called by sync-postgres at the end of a successful sync so clients see
    fresh data without waiting for TTL expiry. Requires the shared token
    `CACHE_INVALIDATE_TOKEN` in the `X-Cache-Token` header; returns 503 if
    no token is configured on the server.
    """
    expected = settings.cache_invalidate_token
    if not expected:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Cache invalidation not configured")
    # Constant-time compare to avoid byte-by-byte token recovery via timing.
    if not secrets.compare_digest(x_cache_token or "", expected):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid cache token")

    stats_before = get_cache_stats()
    clear_cache()
    return CacheInvalidateResponse(
        cleared=stats_before["size"], maxsize=stats_before["maxsize"], ttl=stats_before["ttl"]
    )
