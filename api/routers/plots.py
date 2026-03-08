"""Filter endpoint for plots."""

import logging
from collections.abc import Callable

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from api.cache import get_cache, set_cache
from api.dependencies import require_db
from api.exceptions import DatabaseQueryError
from api.schemas import FilteredPlotsResponse
from core.database import SpecRepository


logger = logging.getLogger(__name__)


router = APIRouter(tags=["plots"])


# =============================================================================
# Filter Category Extractors - Unified dispatch pattern for filter logic
# =============================================================================
# These extractors define how to get filter-matching values for each category.
# Each extractor takes (library, spec_tags, impl_tags) and returns a list of values.

FilterExtractor = Callable[[str, dict, dict], list[str]]

# Spec-level category extractors (match against spec tags)
_SPEC_EXTRACTORS: dict[str, Callable[[dict], list[str]]] = {
    "plot": lambda tags: tags.get("plot_type", []),
    "data": lambda tags: tags.get("data_type", []),
    "dom": lambda tags: tags.get("domain", []),
    "feat": lambda tags: tags.get("features", []),
}

# Impl-level category extractors (match against impl tags)
_IMPL_EXTRACTORS: dict[str, Callable[[dict], list[str]]] = {
    "dep": lambda tags: tags.get("dependencies", []),
    "tech": lambda tags: tags.get("techniques", []),
    "pat": lambda tags: tags.get("patterns", []),
    "prep": lambda tags: tags.get("dataprep", []),
    "style": lambda tags: tags.get("styling", []),
}


def _get_category_values(category: str, spec_id: str, library: str, spec_tags: dict, impl_tags: dict) -> list[str]:
    """
    Get the values for a category from the appropriate tag source.

    This unified function replaces the repeated if/elif chains throughout the module.

    Args:
        category: Filter category (lib, spec, plot, data, dom, feat, dep, tech, pat, prep, style)
        spec_id: Specification ID
        library: Library ID
        spec_tags: Spec-level tags dict
        impl_tags: Implementation-level tags dict

    Returns:
        List of values that match this category for the given image/spec/impl
    """
    if category == "lib":
        return [library]
    if category == "spec":
        return [spec_id]
    if category in _SPEC_EXTRACTORS:
        return _SPEC_EXTRACTORS[category](spec_tags)
    if category in _IMPL_EXTRACTORS:
        return _IMPL_EXTRACTORS[category](impl_tags)
    return []


def _category_matches_filter(
    category: str, values: list[str], spec_id: str, library: str, spec_tags: dict, impl_tags: dict
) -> bool:
    """
    Check if any of the filter values match the category's values.

    Args:
        category: Filter category
        values: Filter values to match against
        spec_id: Specification ID
        library: Library ID
        spec_tags: Spec-level tags dict
        impl_tags: Implementation-level tags dict

    Returns:
        True if any filter value matches, False otherwise
    """
    category_values = _get_category_values(category, spec_id, library, spec_tags, impl_tags)
    return any(v in category_values for v in values)


def _image_matches_groups(spec_id: str, library: str, groups: list[dict], spec_lookup: dict, impl_lookup: dict) -> bool:
    """Check if an image matches a set of filter groups."""
    if spec_id not in spec_lookup:
        return False
    spec_tags = spec_lookup[spec_id]["tags"]
    impl_tags = impl_lookup.get((spec_id, library), {})

    for group in groups:
        category = group["category"]
        values = group["values"]

        if not _category_matches_filter(category, values, spec_id, library, spec_tags, impl_tags):
            return False
    return True


def _increment_category_counts(counts: dict, spec_id: str, library: str, spec_tags: dict, impl_tags: dict) -> None:
    """Increment counts for all categories based on an image's spec/impl tags."""
    all_categories = ["lib", "spec", "plot", "data", "dom", "feat", "dep", "tech", "pat", "prep", "style"]
    for category in all_categories:
        for value in _get_category_values(category, spec_id, library, spec_tags, impl_tags):
            counts[category][value] = counts[category].get(value, 0) + 1


def _create_empty_counts() -> dict:
    """Create an empty counts dictionary with all categories initialized."""
    return {
        "lib": {},
        "spec": {},
        "plot": {},
        "data": {},
        "dom": {},
        "feat": {},
        # Impl-level tag counts (issue #2434)
        "dep": {},
        "tech": {},
        "pat": {},
        "prep": {},
        "style": {},
    }


def _sort_counts(counts: dict) -> dict:
    """Sort counts by value descending, then key ascending."""
    for category in counts:
        counts[category] = dict(sorted(counts[category].items(), key=lambda x: (-x[1], x[0])))
    return counts


def _calculate_global_counts(all_specs: list) -> dict:
    """Calculate global counts for all filter categories."""
    global_counts = _create_empty_counts()

    for spec_obj in all_specs:
        if not spec_obj.impls:
            continue
        spec_tags = spec_obj.tags or {}

        for impl in spec_obj.impls:
            if not impl.preview_url:
                continue

            impl_tags = impl.impl_tags or {}
            _increment_category_counts(global_counts, spec_obj.id, impl.library_id, spec_tags, impl_tags)

    return _sort_counts(global_counts)


def _calculate_contextual_counts(filtered_images: list[dict], spec_id_to_tags: dict, impl_lookup: dict) -> dict:
    """Calculate contextual counts from filtered images."""
    counts = _create_empty_counts()

    for img in filtered_images:
        spec_id = img["spec_id"]
        library = img["library"]
        spec_tags = spec_id_to_tags.get(spec_id, {})
        impl_tags = impl_lookup.get((spec_id, library), {})

        _increment_category_counts(counts, spec_id, library, spec_tags, impl_tags)

    return _sort_counts(counts)


def _calculate_or_counts(
    filter_groups: list[dict], all_images: list[dict], spec_id_to_tags: dict, spec_lookup: dict, impl_lookup: dict
) -> list[dict]:
    """Calculate OR preview counts for each filter group.

    Args:
        filter_groups: List of filter group dictionaries defining categories and values.
        all_images: List of image dictionaries to evaluate against the filter groups.
        spec_id_to_tags: Mapping from specification IDs to their associated tag metadata.
        spec_lookup: Mapping from specification IDs to full specification metadata.
        impl_lookup: Mapping from (spec_id, library) pairs to implementation-level tags.

    Returns:
        List of dicts, one per filter group, mapping values to matching image counts.
    """
    or_counts: list[dict] = []

    for group_idx, group in enumerate(filter_groups):
        # Get all other groups (excluding this one)
        other_groups = [g for i, g in enumerate(filter_groups) if i != group_idx]

        # Filter images with only the other groups' filters
        images_with_other_filters = [
            img
            for img in all_images
            if _image_matches_groups(img["spec_id"], img["library"], other_groups, spec_lookup, impl_lookup)
        ]

        # Count each value for this group's category
        category = group["category"]
        group_counts: dict[str, int] = {}

        for img in images_with_other_filters:
            spec_id = img["spec_id"]
            library = img["library"]
            spec_tags = spec_id_to_tags.get(spec_id, {})
            impl_tags = impl_lookup.get((spec_id, library), {})

            # Use unified value extractor
            for value in _get_category_values(category, spec_id, library, spec_tags, impl_tags):
                group_counts[value] = group_counts.get(value, 0) + 1

        # Sort by count descending
        group_counts = dict(sorted(group_counts.items(), key=lambda x: (-x[1], x[0])))
        or_counts.append(group_counts)

    return or_counts


def _parse_filter_groups(request: Request) -> list[dict]:
    """
    Parse query parameters into filter groups.

    Args:
        request: FastAPI request object

    Returns:
        List of filter group dicts with category and values
    """
    filter_groups: list[dict] = []
    query_params = request.query_params.multi_items()

    # Valid filter categories (spec-level and impl-level)
    valid_categories = (
        "lib",
        "spec",
        "plot",
        "data",
        "dom",
        "feat",
        # Impl-level categories (issue #2434)
        "dep",
        "tech",
        "pat",
        "prep",
        "style",
    )
    for key, value in query_params:
        if key in valid_categories and value:
            values = [v.strip() for v in value.split(",") if v.strip()]
            if values:
                filter_groups.append({"category": key, "values": values})

    return filter_groups


def _build_cache_key(filter_groups: list[dict], *, offset: int = 0, limit: int | None = None) -> str:
    """
    Build cache key from filter groups and pagination params.

    Args:
        filter_groups: List of filter group dicts
        offset: Pagination offset
        limit: Pagination limit

    Returns:
        Cache key string
    """
    if not filter_groups:
        base = "filter:all"
    else:
        cache_parts = [f"{g['category']}={','.join(sorted(g['values']))}" for g in filter_groups]
        base = f"filter:{':'.join(cache_parts)}"

    if limit is not None or offset:
        base += f":o={offset}:l={limit}"
    return base


def _build_spec_lookup(all_specs: list) -> dict:
    """
    Build lookup dictionary of spec_id -> (spec_obj, tags).

    Args:
        all_specs: List of Spec objects

    Returns:
        Dict mapping spec_id to spec object and tags
    """
    spec_lookup: dict = {}
    for spec_obj in all_specs:
        if spec_obj.impls:
            spec_lookup[spec_obj.id] = {"spec": spec_obj, "tags": spec_obj.tags or {}}
    return spec_lookup


def _build_impl_lookup(all_specs: list) -> dict:
    """
    Build lookup dictionary of (spec_id, library_id) -> impl_tags.

    Args:
        all_specs: List of Spec objects

    Returns:
        Dict mapping (spec_id, library_id) tuple to impl_tags dict
    """
    impl_lookup: dict = {}
    for spec_obj in all_specs:
        if not spec_obj.impls:
            continue
        for impl in spec_obj.impls:
            if impl.preview_url:
                impl_lookup[(spec_obj.id, impl.library_id)] = impl.impl_tags or {}
    return impl_lookup


def _collect_all_images(all_specs: list) -> list[dict]:
    """
    Collect all plot images from specs with implementations.

    Args:
        all_specs: List of Spec objects

    Returns:
        List of image dicts with spec_id, library, quality, url, thumb, html, and title
    """
    all_images: list[dict] = []
    for spec_obj in all_specs:
        if not spec_obj.impls:
            continue
        for impl in spec_obj.impls:
            if impl.preview_url:
                all_images.append(
                    {
                        "spec_id": spec_obj.id,
                        "library": impl.library_id,
                        "quality": impl.quality_score,
                        "url": impl.preview_url,
                        "thumb": impl.preview_thumb,
                        "html": impl.preview_html,
                        "title": spec_obj.title,
                    }
                )
    return all_images


def _filter_images(
    all_images: list[dict], filter_groups: list[dict], spec_lookup: dict, impl_lookup: dict
) -> list[dict]:
    """
    Filter images based on filter groups.

    Args:
        all_images: List of all image dicts
        filter_groups: List of filter group dicts
        spec_lookup: Spec lookup dictionary
        impl_lookup: Impl tags lookup dictionary

    Returns:
        Filtered list of image dicts
    """
    return [
        img
        for img in all_images
        if _image_matches_groups(img["spec_id"], img["library"], filter_groups, spec_lookup, impl_lookup)
    ]


@router.get("/plots/filter", response_model=FilteredPlotsResponse)
async def get_filtered_plots(
    request: Request,
    db: AsyncSession = Depends(require_db),
    limit: int | None = Query(None, ge=1),
    offset: int = Query(0, ge=0),
):
    """
    Get filtered plot images with counts for all filter categories.

    Filter logic:
    - Multiple values in same param: OR (lib=matplotlib,seaborn)
    - Multiple params with same name: AND (lib=matplotlib&lib=seaborn)
    - Different categories: AND (lib=matplotlib&plot=scatter)

    Query params (comma-separated for OR, multiple params for AND):
    - lib: Library filter (matplotlib, seaborn, etc.)
    - spec: Spec ID filter (scatter-basic, etc.)
    - plot: Plot type tag (scatter, bar, line, etc.)
    - data: Data type tag (numeric, categorical, etc.)
    - dom: Domain tag (statistics, finance, etc.)
    - feat: Features tag (basic, 3d, interactive, etc.)
    - dep: Impl dependencies filter (scipy, sklearn, etc.)
    - tech: Impl techniques filter (twin-axes, colorbar, etc.)
    - pat: Impl patterns filter (data-generation, etc.)
    - prep: Impl dataprep filter (kde, binning, etc.)
    - style: Impl styling filter (minimal-chrome, etc.)

    Returns:
        FilteredPlotsResponse with images, counts, and orCounts per group
    """
    # Parse query parameters
    filter_groups = _parse_filter_groups(request)

    # Check cache
    cache_key = _build_cache_key(filter_groups, offset=offset, limit=limit)
    try:
        cached = get_cache(cache_key)
        if cached:
            return cached
    except Exception as e:
        # Cache failures are non-fatal, log and continue
        logger.warning("Cache read failed for key %s: %s", cache_key, e)

    # Fetch data from database
    try:
        repo = SpecRepository(db)
        all_specs = await repo.get_all()
    except SQLAlchemyError as e:
        logger.error("Database query failed in get_filtered_plots: %s", e)
        raise DatabaseQueryError("fetch_specs", str(e)) from e

    # Build data structures
    spec_lookup = _build_spec_lookup(all_specs)
    impl_lookup = _build_impl_lookup(all_specs)
    all_images = _collect_all_images(all_specs)
    spec_id_to_tags = {spec_id: spec_data["tags"] for spec_id, spec_data in spec_lookup.items()}

    # Filter images
    filtered_images = _filter_images(all_images, filter_groups, spec_lookup, impl_lookup)

    # Calculate counts (always from ALL filtered images, not paginated)
    global_counts = _calculate_global_counts(all_specs)
    counts = _calculate_contextual_counts(filtered_images, spec_id_to_tags, impl_lookup)
    or_counts = _calculate_or_counts(filter_groups, all_images, spec_id_to_tags, spec_lookup, impl_lookup)

    # Build spec_id -> title mapping for search/tooltips
    spec_titles = {spec_id: data["spec"].title for spec_id, data in spec_lookup.items() if data["spec"].title}

    # Apply pagination
    paginated = filtered_images[offset : offset + limit] if limit else filtered_images[offset:]

    # Build and cache response
    result = FilteredPlotsResponse(
        total=len(filtered_images),
        images=paginated,
        counts=counts,
        globalCounts=global_counts,
        orCounts=or_counts,
        specTitles=spec_titles,
        offset=offset,
        limit=limit,
    )

    try:
        set_cache(cache_key, result)
    except Exception as e:
        # Cache failures are non-fatal, log and continue
        logger.warning("Cache write failed for key %s: %s", cache_key, e)

    return result
