"""Stats endpoint."""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from api.cache import cache_key, get_or_set_cache
from api.dependencies import optional_db
from api.schemas import StatsResponse
from core.config import settings
from core.constants import LIBRARIES_METADATA
from core.database import ImplRepository, LibraryRepository, SpecRepository
from core.database.connection import get_db_context


router = APIRouter(tags=["stats"])


async def _refresh_stats() -> StatsResponse:
    """Standalone factory for background refresh (creates own DB session)."""
    async with get_db_context() as db:
        spec_repo = SpecRepository(db)
        lib_repo = LibraryRepository(db)
        impl_repo = ImplRepository(db)
        specs = await spec_repo.get_all()
        libraries = await lib_repo.get_all()
        total_loc = await impl_repo.get_total_code_lines()

    specs_with_impls = [s for s in specs if s.impls]
    total_impls = sum(len(s.impls) for s in specs)
    return StatsResponse(
        specs=len(specs_with_impls), plots=total_impls, libraries=len(libraries), lines_of_code=total_loc
    )


@router.get("/stats", response_model=StatsResponse)
async def get_stats(db: AsyncSession | None = Depends(optional_db)):
    """
    Get platform statistics.

    Returns counts of specs, implementations (plots), and libraries.
    """
    if db is None:
        return StatsResponse(specs=0, plots=0, libraries=len(LIBRARIES_METADATA))

    async def _fetch() -> StatsResponse:
        spec_repo = SpecRepository(db)
        lib_repo = LibraryRepository(db)
        impl_repo = ImplRepository(db)
        specs = await spec_repo.get_all()
        libraries = await lib_repo.get_all()
        total_loc = await impl_repo.get_total_code_lines()

        specs_with_impls = [s for s in specs if s.impls]
        total_impls = sum(len(s.impls) for s in specs)
        return StatsResponse(
            specs=len(specs_with_impls), plots=total_impls, libraries=len(libraries), lines_of_code=total_loc
        )

    return await get_or_set_cache(
        cache_key("stats"), _fetch, refresh_after=settings.cache_refresh_after, refresh_factory=_refresh_stats
    )
