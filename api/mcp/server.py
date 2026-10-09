"""
FastMCP server for anyplot.

Provides tools for AI assistants to search plot specifications and fetch implementation code.
"""

import os
from collections import Counter
from typing import Any

from fastmcp import FastMCP
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from api.schemas import ImplementationResponse, SpecDetailResponse, SpecListItem
from api.version import APP_VERSION
from core.database import ImplRepository, LibraryRepository, SpecRepository, is_db_configured
from core.database.models import Impl
from core.utils import strip_noqa_comments


# Website URL for linking to anyplot.ai
ANYPLOT_WEBSITE_URL = "https://anyplot.ai"

# MCP-specific database engine (created lazily)
# This is separate from FastAPI's engine to avoid greenlet context issues
_mcp_engine = None
_mcp_session_factory = None


def _get_mcp_engine():
    """Create a dedicated engine for MCP handlers."""
    global _mcp_engine, _mcp_session_factory

    if _mcp_engine is not None:
        return _mcp_engine

    database_url = os.getenv("DATABASE_URL", "")
    if not database_url:
        raise ValueError("DATABASE_URL not configured")

    # Ensure async driver
    if database_url.startswith("postgresql://"):
        database_url = database_url.replace("postgresql://", "postgresql+asyncpg://")
    elif database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql+asyncpg://")

    # Use NullPool for MCP to avoid connection state issues across requests
    _mcp_engine = create_async_engine(database_url, poolclass=NullPool)
    _mcp_session_factory = async_sessionmaker(_mcp_engine, class_=AsyncSession, expire_on_commit=False)

    return _mcp_engine


async def get_mcp_db_session() -> AsyncSession:
    """
    Get database session for MCP handlers.

    Uses a dedicated engine to avoid greenlet context issues
    that occur when Streamable HTTP transport runs in a different
    async context than FastAPI's main event loop.
    """
    _get_mcp_engine()  # Ensure engine is created

    if _mcp_session_factory is None:
        raise ValueError("Database not configured. Check DATABASE_URL.")

    return _mcp_session_factory()


# Stateless HTTP mode is passed explicitly to http_app() in api/main.py.
# The former `os.environ.setdefault("FASTMCP_STATELESS_HTTP", "true")` here
# never worked: `from fastmcp import FastMCP` above had already instantiated
# fastmcp's Settings from the environment, so the late setdefault was read by
# nobody — sessions stayed instance-pinned despite the comment claiming
# otherwise (verified live: initialize returned an mcp-session-id and requests
# without it got HTTP 400; AI-access audit 2026-08-19).

# Initialize FastMCP server. Without an explicit version, serverInfo reports
# the fastmcp PACKAGE version — clients saw "3.4.5" while /health said the app
# is 3.1.0 (live verification 2026-08-19).
mcp_server = FastMCP("anyplot", version=APP_VERSION)


@mcp_server.tool()
async def list_specs(limit: int = 100, offset: int = 0) -> list[dict[str, Any]]:
    """
    List all plot specifications.

    Args:
        limit: Maximum number of specs to return (default: 100)
        offset: Number of specs to skip (default: 0)

    Returns:
        List of spec summaries with id, title, description, tags, and library_count
    """
    if not is_db_configured():
        raise ValueError("Database not configured. Check DATABASE_URL or INSTANCE_CONNECTION_NAME.")

    session = await get_mcp_db_session()
    try:
        repo = SpecRepository(session)
        specs = await repo.get_all()
        # `code` is deferred (multi-MB across the catalog); library_count only
        # needs code *presence*, so probe the non-NULL ids instead of loading blobs.
        ids_with_code = await ImplRepository(session).get_ids_with_code()

        # Apply pagination
        paginated_specs = specs[offset : offset + limit]

        # Convert to SpecListItem format
        result = []
        for spec in paginated_specs:
            impl_count = len([impl for impl in spec.impls if impl.id in ids_with_code])
            item = SpecListItem(
                id=spec.id, title=spec.title, description=spec.description, tags=spec.tags, library_count=impl_count
            )
            result.append({**item.model_dump(), "website_url": f"{ANYPLOT_WEBSITE_URL}/{spec.id}"})

        return result
    finally:
        await session.close()


@mcp_server.tool()
async def search_specs_by_tags(
    plot_type: list[str] | None = None,
    data_type: list[str] | None = None,
    domain: list[str] | None = None,
    features: list[str] | None = None,
    library: list[str] | None = None,
    dependencies: list[str] | None = None,
    techniques: list[str] | None = None,
    patterns: list[str] | None = None,
    dataprep: list[str] | None = None,
    styling: list[str] | None = None,
    limit: int = 100,
) -> list[dict[str, Any]]:
    """
    Search plot specifications by tag filters.

    Tag Categories (Spec-level):
        - plot_type: Type of plot (scatter, bar, line, heatmap, etc.)
        - data_type: Data requirements (numeric, categorical, timeseries, etc.)
        - domain: Application domain (statistics, finance, science, etc.)
        - features: Plot features (interactive, 3d, animated, etc.)

    Tag Categories (Impl-level, filters by library implementations):
        - library: Filter by available library (matplotlib, seaborn, plotly, etc.)
        - dependencies: External packages used (scipy, sklearn, etc.)
        - techniques: Visualization techniques (colorbar, annotations, etc.)
        - patterns: Code patterns (data-generation, explicit-figure, etc.)
        - dataprep: Data preparation techniques (normalization, aggregation, etc.)
        - styling: Visual styling approaches (publication-ready, minimal, etc.)

    Filter logic (both levels): several values in one category match if ANY
    of them is present (OR); several categories must ALL match (AND). A
    spec-level value only matches the category it is passed in, so
    plot_type=["finance"] does not match a spec whose domain is finance.
    Impl-level filters require at least one implementation that satisfies
    all of them.

    Args:
        plot_type: Filter by plot type tags
        data_type: Filter by data type tags
        domain: Filter by domain tags
        features: Filter by feature tags
        library: Filter by available library implementations
        dependencies: Filter by implementation dependencies
        techniques: Filter by visualization techniques
        patterns: Filter by code patterns
        dataprep: Filter by data preparation techniques
        styling: Filter by styling approaches
        limit: Maximum number of specs to return (default: 100)

    Returns:
        List of matching spec summaries
    """
    if not is_db_configured():
        raise ValueError("Database not configured. Check DATABASE_URL or INSTANCE_CONNECTION_NAME.")

    session = await get_mcp_db_session()
    try:
        repo = SpecRepository(session)

        # Spec-level filters, passed per category: OR within one, AND across
        # them. The previous flatten-and-OR matched any value in any category,
        # so plot_type=["scatter"] + domain=["finance"] returned the union of
        # both and plot_type=["finance"] matched finance *domains* (AI-access
        # research, 2026-10-08). `code` stays deferred on both paths — the
        # loops below only need code *presence*, probed via non-NULL ids.
        filters: dict[str, list[str]] = {}
        if plot_type:
            filters["plot_type"] = plot_type
        if data_type:
            filters["data_type"] = data_type
        if domain:
            filters["domain"] = domain
        if features:
            filters["features"] = features

        specs = await repo.search_by_tag_filters(filters) if filters else await repo.get_all()
        ids_with_code = await ImplRepository(session).get_ids_with_code()

        # Apply impl-level filtering if needed
        if library or dependencies or techniques or patterns or dataprep or styling:
            filtered_specs = []
            for spec in specs:
                # Check if spec has implementations matching impl-level filters
                matching_impls = []
                for impl in spec.impls:
                    if impl.id not in ids_with_code:
                        continue

                    # Filter by library
                    if library and impl.library.id not in library:
                        continue

                    # Filter by impl tags. impl_tags itself may be NULL (impls
                    # that predate tagging or whose review produced no tags).
                    impl_tags = impl.impl_tags or {}
                    if dependencies and not any(
                        dep in (impl_tags.get("dependencies", []) or []) for dep in dependencies
                    ):
                        continue
                    if techniques and not any(tech in (impl_tags.get("techniques", []) or []) for tech in techniques):
                        continue
                    if patterns and not any(pat in (impl_tags.get("patterns", []) or []) for pat in patterns):
                        continue
                    if dataprep and not any(dp in (impl_tags.get("dataprep", []) or []) for dp in dataprep):
                        continue
                    if styling and not any(style in (impl_tags.get("styling", []) or []) for style in styling):
                        continue

                    matching_impls.append(impl)

                # Include spec if it has matching implementations
                if matching_impls:
                    filtered_specs.append(spec)

            specs = filtered_specs

        # Apply limit
        specs = specs[:limit]

        # Convert to SpecListItem format
        result = []
        for spec in specs:
            impl_count = len([impl for impl in spec.impls if impl.id in ids_with_code])
            item = SpecListItem(
                id=spec.id, title=spec.title, description=spec.description, tags=spec.tags, library_count=impl_count
            )
            result.append({**item.model_dump(), "website_url": f"{ANYPLOT_WEBSITE_URL}/{spec.id}"})

        return result
    finally:
        await session.close()


# Fields of ImplementationResponse the MCP tools leave out: the legacy
# single-theme preview fields duplicate the light variants, `updated` is never
# set here, and the review checklist and image description are pipeline
# internals (~10 KB per implementation) that an assistant adapting code never
# needs — they alone made an unfiltered get_spec_detail about 0.5 MB.
_MCP_IMPL_EXCLUDE = {"preview_url", "preview_html", "updated", "review_image_description", "review_criteria_checklist"}


def _implementation_payload(spec_id: str, impl: Impl) -> dict[str, Any]:
    """One implementation as the MCP tools return it.

    `# noqa` comments are stripped as the REST code endpoint does, and
    `spec_id` plus `website_url` are added so a result stands on its own.
    """
    response = ImplementationResponse(
        library_id=impl.library.id,
        library_name=impl.library.name,
        language=impl.library.language,
        preview_url_light=impl.preview_url_light,
        preview_url_dark=impl.preview_url_dark,
        preview_html_light=impl.preview_html_light,
        preview_html_dark=impl.preview_html_dark,
        quality_score=impl.quality_score,
        code=strip_noqa_comments(impl.code),
        generated_at=impl.generated_at.isoformat() if impl.generated_at else None,
        generated_by=impl.generated_by,
        python_version=impl.python_version,
        language_version=impl.language_version or impl.python_version,
        library_version=impl.library_version,
        review_strengths=impl.review_strengths or [],
        review_weaknesses=impl.review_weaknesses or [],
        review_verdict=impl.review_verdict,
        impl_tags=impl.impl_tags,
    )
    return {
        "spec_id": spec_id,
        **response.model_dump(exclude=_MCP_IMPL_EXCLUDE),
        "website_url": f"{ANYPLOT_WEBSITE_URL}/{spec_id}/{impl.library.language}/{impl.library.id}",
    }


@mcp_server.tool()
async def get_spec_detail(spec_id: str, libraries: list[str] | None = None) -> dict[str, Any]:
    """
    Get full specification details with implementations.

    Args:
        spec_id: The specification ID (e.g., "scatter-basic")
        libraries: Optional library ids to include (e.g. ["seaborn", "d3"]).
            Omit for all; an empty list also means all (agents commonly send []
            for "no filter", and answering it with zero implementations would
            read as a missing spec). The full response for a 15-library spec
            carries every implementation's complete source (~0.5 MB) — filter
            when only some libraries matter.

    Returns:
        Complete spec details including:
        - Spec metadata (title, description, tags, etc.)
        - The selected implementations with code and metadata
        - Data requirements
        - Applications and notes

    Raises:
        ValueError: If spec_id not found
    """
    if not is_db_configured():
        raise ValueError("Database not configured. Check DATABASE_URL or INSTANCE_CONNECTION_NAME.")

    session = await get_mcp_db_session()
    try:
        repo = SpecRepository(session)
        # get_by_id_with_code eager-loads Impl.code so the loop below can read
        # it without triggering a deferred-column lazy load (MissingGreenlet
        # on AsyncSession).
        spec = await repo.get_by_id_with_code(spec_id)

        if spec is None:
            raise ValueError(f"Specification '{spec_id}' not found")

        # The implementation dicts are attached AFTER model_dump: SpecDetailResponse
        # coerces its `implementations` into ImplementationResponse, which has
        # neither spec_id nor website_url, and that coercion silently dropped
        # the per-implementation URLs once (AI-access audit 2026-08-19).
        implementations = [
            _implementation_payload(spec_id, impl)
            for impl in spec.impls
            if impl.code is not None and (not libraries or impl.library.id in libraries)
        ]
        response = SpecDetailResponse(
            id=spec.id,
            title=spec.title,
            description=spec.description,
            applications=spec.applications or [],
            data=spec.data or [],
            notes=spec.notes or [],
            tags=spec.tags,
            issue=spec.issue,
            suggested=spec.suggested,
            created=spec.created.isoformat() if spec.created else None,
            updated=spec.updated.isoformat() if spec.updated else None,
        )
        return {
            **response.model_dump(),
            "implementations": implementations,
            "website_url": f"{ANYPLOT_WEBSITE_URL}/{spec_id}",
        }
    finally:
        await session.close()


@mcp_server.tool()
async def get_implementation(spec_id: str, library: str) -> dict[str, Any]:
    """
    Get implementation code for a specific library.

    Args:
        spec_id: The specification ID (e.g., "scatter-basic")
        library: The library id (e.g., "matplotlib", "ggplot2", "makie", "d3" —
            any of the fifteen supported libraries across Python, R, Julia and
            JavaScript; ids are globally unique, so no language is needed)

    Returns:
        Implementation details including:
        - Runnable source code in the library's language
        - Quality score
        - Library metadata (version, generated date, etc.)
        - Preview image URLs
        - Review feedback (strengths, weaknesses)
        - Implementation tags (dependencies, techniques, patterns)

    Raises:
        ValueError: If spec_id or library not found, or implementation doesn't exist
    """
    if not is_db_configured():
        raise ValueError("Database not configured. Check DATABASE_URL or INSTANCE_CONNECTION_NAME.")

    session = await get_mcp_db_session()
    try:
        spec_repo = SpecRepository(session)
        library_repo = LibraryRepository(session)
        impl_repo = ImplRepository(session)

        # Validate spec exists
        spec = await spec_repo.get_by_id(spec_id)
        if spec is None:
            raise ValueError(f"Specification '{spec_id}' not found")

        # Validate library exists
        lib = await library_repo.get_by_id(library)
        if lib is None:
            valid_libraries = await library_repo.get_all()
            valid_names = [library_obj.id for library_obj in valid_libraries]
            raise ValueError(f"Library '{library}' not found. Valid libraries: {', '.join(valid_names)}")

        # Get implementation. The language comes from the library's own DB row —
        # the repository's language_id defaults to "python", which made every
        # R/Julia/JavaScript implementation (28% of the catalogue) answer a
        # false "not found" through this tool (AI-access audit 2026-08-19).
        impl = await impl_repo.get_by_spec_and_library(spec_id, library, lib.language)
        if impl is None or impl.code is None:
            raise ValueError(f"Implementation for '{spec_id}' in library '{library}' not found")

        return _implementation_payload(spec_id, impl)
    finally:
        await session.close()


@mcp_server.tool()
async def list_libraries() -> list[dict[str, Any]]:
    """
    List all supported plotting libraries.

    Returns:
        List of libraries with id, name, language (python, r, julia,
        javascript), framework (none or react), version, documentation_url and
        description — the same fields as the REST /libraries endpoint, so an
        assistant can pick a library by language without a second call.
    """
    if not is_db_configured():
        raise ValueError("Database not configured. Check DATABASE_URL or INSTANCE_CONNECTION_NAME.")

    session = await get_mcp_db_session()
    try:
        repo = LibraryRepository(session)
        libraries = await repo.get_all()
        return [
            {
                "id": lib.id,
                "name": lib.name,
                "language": lib.language,
                "framework": lib.framework,
                "version": lib.version,
                "documentation_url": lib.documentation_url,
                "description": lib.description,
            }
            for lib in libraries
        ]
    finally:
        await session.close()


@mcp_server.tool()
async def get_tag_values(category: str) -> list[dict[str, Any]]:
    """
    Get all available values for a specific tag category, with how often each occurs.

    Tag Categories:
        Spec-level (describe WHAT is visualized):
        - plot_type: scatter, bar, line, heatmap, histogram, box, violin, etc.
        - data_type: numeric, categorical, timeseries, geospatial, etc.
        - domain: statistics, finance, science, business, etc.
        - features: interactive, 3d, animated, correlation, etc.

        Impl-level (describe HOW code implements it):
        - dependencies: scipy, sklearn, statsmodels, etc.
        - techniques: colorbar, annotations, regression-line, etc.
        - patterns: data-generation, explicit-figure, subplot-layout, etc.
        - dataprep: normalization, aggregation, smoothing, etc.
        - styling: publication-ready, minimal, colorblind-safe, etc.

    Args:
        category: Tag category name (plot_type, data_type, domain, features,
                  dependencies, techniques, patterns, dataprep, styling)

    Returns:
        List of {value, count}, most frequent first (ties alphabetical). For
        spec-level categories the count is the number of specs carrying the
        value; for impl-level categories it is the number of implementations
        with code that carry it.

    Raises:
        ValueError: If category not recognized
    """
    # Define valid categories
    spec_categories = ["plot_type", "data_type", "domain", "features"]
    impl_categories = ["dependencies", "techniques", "patterns", "dataprep", "styling"]
    valid_categories = spec_categories + impl_categories

    if category not in valid_categories:
        raise ValueError(f"Invalid category '{category}'. Valid categories: {', '.join(valid_categories)}")

    if not is_db_configured():
        raise ValueError("Database not configured. Check DATABASE_URL or INSTANCE_CONNECTION_NAME.")

    session = await get_mcp_db_session()
    try:
        repo = SpecRepository(session)
        specs = await repo.get_all()

        counts: Counter[str] = Counter()
        if category in spec_categories:
            for spec in specs:
                tag_list = (spec.tags or {}).get(category)
                if isinstance(tag_list, list):
                    counts.update(set(tag_list))
        else:
            # Only implementations with code count, like library_count elsewhere.
            ids_with_code = await ImplRepository(session).get_ids_with_code()
            for spec in specs:
                for impl in spec.impls:
                    if impl.id not in ids_with_code:
                        continue
                    tag_list = (impl.impl_tags or {}).get(category)
                    if isinstance(tag_list, list):
                        counts.update(set(tag_list))

        return [
            {"value": value, "count": count} for value, count in sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))
        ]
    finally:
        await session.close()
