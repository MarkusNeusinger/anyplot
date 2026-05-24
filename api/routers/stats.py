"""Stats endpoint."""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from api.cache import cache_key, get_or_set_cache
from api.dependencies import optional_db
from api.schemas import StatsResponse
from core.config import settings
from core.constants import LANGUAGES_METADATA, LIBRARIES_METADATA
from core.database import ImplRepository, LibraryRepository, SpecRepository
from core.database.connection import get_db_context


router = APIRouter(tags=["stats"])


async def _compute_stats(db: AsyncSession) -> StatsResponse:
    """Build the stats response using lightweight aggregate queries.

    Previously this loaded every Spec (with selectinload(Impl) and
    selectinload(Impl.library)) and every Library row just to take ``len()``
    over them, which made cold-cache /stats one of the slowest reads on the
    site — the user-visible NumbersStrip ("languages / libraries / specs"
    under the hero) waited on that. Aggregate COUNT/DISTINCT queries avoid
    transferring all those rows.
    """
    spec_repo = SpecRepository(db)
    lib_repo = LibraryRepository(db)
    impl_repo = ImplRepository(db)

    specs_with_impls = await spec_repo.count_with_impls()
    total_impls = await impl_repo.count_all()
    library_count, distinct_languages = await lib_repo.count_with_languages()
    total_loc = await impl_repo.get_total_code_lines()

    languages = distinct_languages or len(LANGUAGES_METADATA)
    return StatsResponse(
        specs=specs_with_impls, plots=total_impls, libraries=library_count, languages=languages, lines_of_code=total_loc
    )


async def _refresh_stats() -> StatsResponse:
    """Standalone factory for background refresh (creates own DB session)."""
    async with get_db_context() as db:
        return await _compute_stats(db)


@router.get("/stats", response_model=StatsResponse)
async def get_stats(db: AsyncSession | None = Depends(optional_db)):
    """
    Get platform statistics.

    Returns counts of specs, implementations (plots), libraries, and languages.
    """
    if db is None:
        return StatsResponse(specs=0, plots=0, libraries=len(LIBRARIES_METADATA), languages=len(LANGUAGES_METADATA))

    async def _fetch() -> StatsResponse:
        return await _compute_stats(db)

    return await get_or_set_cache(
        cache_key("stats"), _fetch, refresh_after=settings.cache_refresh_after, refresh_factory=_refresh_stats
    )
