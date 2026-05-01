"""Spec endpoints."""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from api.cache import cache_key, get_or_set_cache
from api.dependencies import require_db
from api.exceptions import raise_not_found
from api.schemas import ImplementationResponse, SpecDetailResponse, SpecListItem, SpecMapItem
from core.config import settings
from core.database import ImplRepository, SpecRepository
from core.database.connection import get_db_context
from core.utils import strip_noqa_comments


router = APIRouter(tags=["specs"])


async def _build_specs_list(db: AsyncSession) -> list[SpecListItem]:
    repo = SpecRepository(db)
    specs = await repo.get_all()
    return [
        SpecListItem(
            id=spec.id, title=spec.title, description=spec.description, tags=spec.tags, library_count=len(spec.impls)
        )
        for spec in specs
        if spec.impls
    ]


async def _build_specs_map(db: AsyncSession) -> list[SpecMapItem]:
    """One row per spec with its best-rated impl image + spec/impl tag bag for the /map page.

    Best-impl tiebreak: highest quality_score, then lexicographically *greatest* library_id
    (since `max()` picks the largest tuple — e.g. seaborn over matplotlib on a tie).
    Specs without any implementations are skipped (mirrors _build_specs_list).
    """
    repo = SpecRepository(db)
    specs = await repo.get_all()
    items: list[SpecMapItem] = []
    for spec in specs:
        if not spec.impls:
            continue
        # Prefer impls that actually have a preview URL — otherwise the map
        # would render blank-bordered nodes for specs whose top-quality impl
        # happens to have no thumbnail. Fall back to the full impl list only
        # when *no* impl has a preview (very rare, but keeps the spec on the map).
        with_preview = [i for i in spec.impls if i.preview_url_light or i.preview_url_dark]
        candidates = with_preview or list(spec.impls)
        best = max(candidates, key=lambda i: ((i.quality_score or 0.0), i.library_id))
        items.append(
            SpecMapItem(
                id=spec.id,
                title=spec.title,
                preview_url_light=best.preview_url_light,
                preview_url_dark=best.preview_url_dark,
                quality_score=best.quality_score,
                tags=spec.tags,
                impl_tags=best.impl_tags,
            )
        )
    return items


async def _build_spec_detail(db: AsyncSession, spec_id: str) -> SpecDetailResponse:
    repo = SpecRepository(db)
    spec = await repo.get_by_id(spec_id)

    if not spec:
        raise_not_found("Spec", spec_id)
    if not spec.impls:
        raise_not_found("Spec with implementations", spec_id)

    impls = [
        ImplementationResponse(
            library_id=impl.library_id,
            library_name=impl.library.name if impl.library else impl.library_id,
            language=impl.library.language if impl.library else "python",
            preview_url_light=impl.preview_url_light,
            preview_url_dark=impl.preview_url_dark,
            preview_html_light=impl.preview_html_light,
            preview_html_dark=impl.preview_html_dark,
            # Legacy single-theme fields (synonyms that resolve to the light variant)
            preview_url=impl.preview_url,
            preview_html=impl.preview_html,
            quality_score=impl.quality_score,
            code=None,  # Code loaded separately via /specs/{spec_id}/{library}/code
            generated_at=impl.generated_at.isoformat() if impl.generated_at else None,
            updated=impl.updated.isoformat() if impl.updated else None,
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

    return SpecDetailResponse(
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


async def _build_impl_code(db: AsyncSession, spec_id: str, library: str) -> dict:
    repo = ImplRepository(db)
    impl = await repo.get_code(spec_id, library)

    if not impl or not impl.code:
        raise_not_found("Implementation code", f"{spec_id}/{library}")

    return {"spec_id": spec_id, "library": library, "code": strip_noqa_comments(impl.code)}


async def _build_spec_images(db: AsyncSession, spec_id: str) -> dict:
    repo = SpecRepository(db)
    spec = await repo.get_by_id(spec_id)

    if not spec:
        raise_not_found("Spec", spec_id)
    if not spec.impls:
        raise_not_found("Spec with implementations", spec_id)

    images = [
        {"library": impl.library_id, "url": impl.preview_url, "html": impl.preview_html}
        for impl in spec.impls
        if impl.preview_url
    ]
    return {"spec_id": spec_id, "images": images}


@router.get("/specs", response_model=list[SpecListItem])
async def get_specs(db: AsyncSession = Depends(require_db)):
    """Get list of all specs with metadata (specs with at least one implementation)."""

    async def _fetch() -> list[SpecListItem]:
        return await _build_specs_list(db)

    async def _refresh() -> list[SpecListItem]:
        async with get_db_context() as fresh_db:
            return await _build_specs_list(fresh_db)

    return await get_or_set_cache(
        cache_key("specs_list"), _fetch, refresh_after=settings.cache_refresh_after, refresh_factory=_refresh
    )


@router.get("/specs/map", response_model=list[SpecMapItem])
async def get_specs_map(db: AsyncSession = Depends(require_db)):
    """Get one row per spec (best-impl image + tag bag) for the /map clustering page.

    NOTE: must stay declared before /specs/{spec_id} so the path-parameter route doesn't capture "map".
    """

    async def _fetch() -> list[SpecMapItem]:
        return await _build_specs_map(db)

    async def _refresh() -> list[SpecMapItem]:
        async with get_db_context() as fresh_db:
            return await _build_specs_map(fresh_db)

    return await get_or_set_cache(
        cache_key("specs_map"), _fetch, refresh_after=settings.cache_refresh_after, refresh_factory=_refresh
    )


@router.get("/specs/{spec_id}", response_model=SpecDetailResponse)
async def get_spec(spec_id: str, db: AsyncSession = Depends(require_db)):
    """Get detailed spec information including all implementations."""

    async def _fetch() -> SpecDetailResponse:
        return await _build_spec_detail(db, spec_id)

    async def _refresh() -> SpecDetailResponse:
        async with get_db_context() as fresh_db:
            return await _build_spec_detail(fresh_db, spec_id)

    return await get_or_set_cache(
        cache_key("spec", spec_id), _fetch, refresh_after=settings.cache_refresh_after, refresh_factory=_refresh
    )


@router.get("/specs/{spec_id}/{library}/code")
async def get_impl_code(spec_id: str, library: str, db: AsyncSession = Depends(require_db)):
    """Get implementation code for a specific spec + library (code field deferred in main query)."""

    async def _fetch() -> dict:
        return await _build_impl_code(db, spec_id, library)

    async def _refresh() -> dict:
        async with get_db_context() as fresh_db:
            return await _build_impl_code(fresh_db, spec_id, library)

    return await get_or_set_cache(
        cache_key("impl_code", spec_id, library),
        _fetch,
        refresh_after=settings.cache_refresh_after,
        refresh_factory=_refresh,
    )


@router.get("/specs/{spec_id}/images")
async def get_spec_images(spec_id: str, db: AsyncSession = Depends(require_db)):
    """Get plot images for a specification across all libraries."""

    async def _fetch() -> dict:
        return await _build_spec_images(db, spec_id)

    async def _refresh() -> dict:
        async with get_db_context() as fresh_db:
            return await _build_spec_images(fresh_db, spec_id)

    return await get_or_set_cache(
        cache_key("spec_images", spec_id), _fetch, refresh_after=settings.cache_refresh_after, refresh_factory=_refresh
    )
