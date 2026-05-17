"""Language endpoints."""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from api.cache import cache_key, get_or_set_cache
from api.dependencies import optional_db
from core.config import settings
from core.constants import LANGUAGES_METADATA
from core.database import LanguageRepository
from core.database.connection import get_db_context


router = APIRouter(tags=["languages"])


def _serialize(language) -> dict:
    return {
        "id": language.id,
        "name": language.name,
        "file_extension": language.file_extension,
        "runtime_version": language.runtime_version,
        "documentation_url": language.documentation_url,
        "description": language.description,
    }


async def _refresh_languages() -> dict:
    """Standalone factory for background refresh (creates own DB session)."""
    async with get_db_context() as db:
        repo = LanguageRepository(db)
        languages = await repo.get_all()
        return {"languages": [_serialize(lang) for lang in languages]}


@router.get("/languages")
async def get_languages(db: AsyncSession | None = Depends(optional_db)):
    """
    Get list of all supported implementation languages.

    Returns language information including display name, file extension,
    runtime version, documentation URL, and a one-line description. Used by
    the frontend to render language chips on library cards and the
    clickable language tooltip on plot cards (deep-link to upstream docs).
    """
    if db is None:
        return {"languages": LANGUAGES_METADATA}

    async def _fetch() -> dict:
        repo = LanguageRepository(db)
        languages = await repo.get_all()
        return {"languages": [_serialize(lang) for lang in languages]}

    return await get_or_set_cache(
        cache_key("languages"), _fetch, refresh_after=settings.cache_refresh_after, refresh_factory=_refresh_languages
    )
