"""Spec endpoints."""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from api.cache import cache_key, get_cache, get_or_set_cache, set_cache
from api.dependencies import require_db
from api.exceptions import raise_not_found
from api.schemas import ImplementationResponse, SpecDetailResponse, SpecListItem
from core.config import settings
from core.database import SpecRepository
from core.database.connection import get_db_context
from core.utils import strip_noqa_comments


router = APIRouter(tags=["specs"])


async def _refresh_specs_list() -> list[SpecListItem]:
    """Standalone factory for background refresh (creates own DB session)."""
    async with get_db_context() as db:
        repo = SpecRepository(db)
        specs = await repo.get_all()
        return [
            SpecListItem(
                id=spec.id,
                title=spec.title,
                description=spec.description,
                tags=spec.tags,
                library_count=len(spec.impls),
            )
            for spec in specs
            if spec.impls
        ]


@router.get("/specs", response_model=list[SpecListItem])
async def get_specs(db: AsyncSession = Depends(require_db)):
    """
    Get list of all specs with metadata.

    Returns only specs that have at least one implementation.
    """

    async def _fetch() -> list[SpecListItem]:
        repo = SpecRepository(db)
        specs = await repo.get_all()
        return [
            SpecListItem(
                id=spec.id,
                title=spec.title,
                description=spec.description,
                tags=spec.tags,
                library_count=len(spec.impls),
            )
            for spec in specs
            if spec.impls
        ]

    return await get_or_set_cache(
        cache_key("specs_list"), _fetch, refresh_after=settings.cache_refresh_after, refresh_factory=_refresh_specs_list
    )


@router.get("/specs/{spec_id}", response_model=SpecDetailResponse)
async def get_spec(spec_id: str, db: AsyncSession = Depends(require_db)):
    """
    Get detailed spec information including all implementations.

    Args:
        spec_id: The specification ID (e.g., 'scatter-basic')

    Returns:
        Full spec details with all library implementations and preview URLs
    """

    key = cache_key("spec", spec_id)
    cached = get_cache(key)
    if cached:
        return cached

    repo = SpecRepository(db)
    spec = await repo.get_by_id(spec_id)

    if not spec:
        raise_not_found("Spec", spec_id)

    # Only return spec if it has implementations
    if not spec.impls:
        raise_not_found("Spec with implementations", spec_id)

    impls = [
        ImplementationResponse(
            library_id=impl.library_id,
            library_name=impl.library.name if impl.library else impl.library_id,
            preview_url=impl.preview_url,
            preview_html=impl.preview_html,
            quality_score=impl.quality_score,
            code=strip_noqa_comments(impl.code),
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
        for impl in spec.impls
    ]

    result = SpecDetailResponse(
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
        implementations=impls,
    )
    set_cache(key, result)
    return result


@router.get("/specs/{spec_id}/images")
async def get_spec_images(spec_id: str, db: AsyncSession = Depends(require_db)):
    """
    Get plot images for a specification across all libraries.

    Returns preview_url and preview_html from database.
    """

    key = cache_key("spec_images", spec_id)
    cached = get_cache(key)
    if cached:
        return cached

    repo = SpecRepository(db)
    spec = await repo.get_by_id(spec_id)

    if not spec:
        raise_not_found("Spec", spec_id)

    if not spec.impls:
        raise_not_found("Spec with implementations", spec_id)

    images = [
        {"library": impl.library_id, "url": impl.preview_url, "html": impl.preview_html}
        for impl in spec.impls
        if impl.preview_url  # Only include if there's a preview
    ]

    result = {"spec_id": spec_id, "images": images}
    set_cache(key, result)
    return result
