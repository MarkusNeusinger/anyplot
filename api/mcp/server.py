"""
FastMCP server for anyplot.

Provides tools for AI assistants to search plot specifications and fetch implementation code.
"""

import os
from typing import Any

from fastmcp import FastMCP
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from api.schemas import ImplementationResponse, SpecDetailResponse, SpecListItem
from core.database import ImplRepository, LibraryRepository, SpecRepository, is_db_configured


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


# Enable stateless HTTP mode via environment variable (recommended approach)
# This allows horizontal scaling without session affinity
os.environ.setdefault("FASTMCP_STATELESS_HTTP", "true")

# Initialize FastMCP server
mcp_server = FastMCP("anyplot")


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

        # Apply pagination
        paginated_specs = specs[offset : offset + limit]

        # Convert to SpecListItem format
        result = []
        for spec in paginated_specs:
            impl_count = len([impl for impl in spec.impls if impl.code is not None])
            item = SpecListItem(
                id=spec.id, title=spec.title, description=spec.description, tags=spec.tags, library_count=impl_count
            )
            result.append({**item.model_dump(), "website_url": f"{ANYPLOT_WEBSITE_URL}/python/{spec.id}"})

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

        # Build filter dict (spec-level tags)
        filters: dict[str, list[str]] = {}
        if plot_type:
            filters["plot_type"] = plot_type
        if data_type:
            filters["data_type"] = data_type
        if domain:
            filters["domain"] = domain
        if features:
            filters["features"] = features

        # Flatten filter values into a single tag list for repository search
        tag_values: list[str] = [tag for tags in filters.values() for tag in tags]

        # Search by spec-level tags
        specs = await repo.search_by_tags(tag_values) if tag_values else await repo.get_all()

        # Apply impl-level filtering if needed
        if library or dependencies or techniques or patterns or dataprep or styling:
            filtered_specs = []
            for spec in specs:
                # Check if spec has implementations matching impl-level filters
                matching_impls = []
                for impl in spec.impls:
                    if impl.code is None:
                        continue

                    # Filter by library
                    if library and impl.library.id not in library:
                        continue

                    # Filter by impl tags
                    if dependencies and not any(
                        dep in (impl.impl_tags.get("dependencies", []) or []) for dep in dependencies
                    ):
                        continue
                    if techniques and not any(
                        tech in (impl.impl_tags.get("techniques", []) or []) for tech in techniques
                    ):
                        continue
                    if patterns and not any(pat in (impl.impl_tags.get("patterns", []) or []) for pat in patterns):
                        continue
                    if dataprep and not any(dp in (impl.impl_tags.get("dataprep", []) or []) for dp in dataprep):
                        continue
                    if styling and not any(style in (impl.impl_tags.get("styling", []) or []) for style in styling):
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
            impl_count = len([impl for impl in spec.impls if impl.code is not None])
            item = SpecListItem(
                id=spec.id, title=spec.title, description=spec.description, tags=spec.tags, library_count=impl_count
            )
            result.append({**item.model_dump(), "website_url": f"{ANYPLOT_WEBSITE_URL}/python/{spec.id}"})

        return result
    finally:
        await session.close()


@mcp_server.tool()
async def get_spec_detail(spec_id: str) -> dict[str, Any]:
    """
    Get full specification details with all implementations.

    Args:
        spec_id: The specification ID (e.g., "scatter-basic")

    Returns:
        Complete spec details including:
        - Spec metadata (title, description, tags, etc.)
        - All available implementations with code and metadata
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
        spec = await repo.get_by_id(spec_id)

        if spec is None:
            raise ValueError(f"Specification '{spec_id}' not found")

        # Build implementations list
        implementations = []
        for impl in spec.impls:
            if impl.code is None:
                continue

            impl_response = ImplementationResponse(
                library_id=impl.library.id,
                library_name=impl.library.name,
                language=impl.library.language,
                preview_url=impl.preview_url,
                preview_html=impl.preview_html,
                quality_score=impl.quality_score,
                code=impl.code,
                generated_at=impl.generated_at.isoformat() if impl.generated_at else None,
                generated_by=impl.generated_by,
                python_version=impl.python_version,
                library_version=impl.library_version,
                review_strengths=impl.review_strengths or [],
                review_weaknesses=impl.review_weaknesses or [],
                review_image_description=impl.review_image_description,
                review_criteria_checklist=impl.review_criteria_checklist,
                review_verdict=impl.review_verdict,
                impl_tags=impl.impl_tags,
            )
            implementations.append(
                {
                    **impl_response.model_dump(),
                    "website_url": f"{ANYPLOT_WEBSITE_URL}/{spec_id}/{impl.library.language}/{impl.library.id}",
                }
            )

        # Build full spec response
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
            implementations=implementations,
        )

        return {**response.model_dump(), "website_url": f"{ANYPLOT_WEBSITE_URL}/python/{spec_id}"}
    finally:
        await session.close()


@mcp_server.tool()
async def get_implementation(spec_id: str, library: str) -> dict[str, Any]:
    """
    Get implementation code for a specific library.

    Args:
        spec_id: The specification ID (e.g., "scatter-basic")
        library: The library name (e.g., "matplotlib", "seaborn", "plotly")

    Returns:
        Implementation details including:
        - Python code
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

        # Get implementation
        impl = await impl_repo.get_by_spec_and_library(spec_id, library)
        if impl is None or impl.code is None:
            raise ValueError(f"Implementation for '{spec_id}' in library '{library}' not found")

        # Build response
        response = ImplementationResponse(
            library_id=impl.library.id,
            library_name=impl.library.name,
            language=impl.library.language,
            preview_url=impl.preview_url,
            preview_html=impl.preview_html,
            quality_score=impl.quality_score,
            code=impl.code,
            generated_at=impl.generated_at.isoformat() if impl.generated_at else None,
            generated_by=impl.generated_by,
            python_version=impl.python_version,
            library_version=impl.library_version,
            review_strengths=impl.review_strengths or [],
            review_weaknesses=impl.review_weaknesses or [],
            review_image_description=impl.review_image_description,
            review_criteria_checklist=impl.review_criteria_checklist,
            review_verdict=impl.review_verdict,
            impl_tags=impl.impl_tags,
        )

        return {
            **response.model_dump(),
            "website_url": f"{ANYPLOT_WEBSITE_URL}/{spec_id}/{impl.library.language}/{library}",
        }
    finally:
        await session.close()


@mcp_server.tool()
async def list_libraries() -> list[dict[str, Any]]:
    """
    List all supported plotting libraries.

    Returns:
        List of libraries with id, name, and description
    """
    if not is_db_configured():
        raise ValueError("Database not configured. Check DATABASE_URL or INSTANCE_CONNECTION_NAME.")

    session = await get_mcp_db_session()
    try:
        repo = LibraryRepository(session)
        libraries = await repo.get_all()

        result = []
        for lib in libraries:
            result.append({"id": lib.id, "name": lib.name, "description": lib.description})

        return result
    finally:
        await session.close()


@mcp_server.tool()
async def get_tag_values(category: str) -> list[str]:
    """
    Get all available values for a specific tag category.

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
        List of unique tag values in that category

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

        # Collect unique tag values
        values = set()

        if category in spec_categories:
            # Spec-level tags
            for spec in specs:
                if spec.tags and category in spec.tags:
                    tag_list = spec.tags[category]
                    if isinstance(tag_list, list):
                        values.update(tag_list)
        else:
            # Impl-level tags
            for spec in specs:
                for impl in spec.impls:
                    if impl.impl_tags and category in impl.impl_tags:
                        tag_list = impl.impl_tags[category]
                        if isinstance(tag_list, list):
                            values.update(tag_list)

        return sorted(values)
    finally:
        await session.close()
