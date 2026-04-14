"""
FastAPI dependencies for anyplot API.

Reusable dependencies for database access, authentication, etc.
"""

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from api.exceptions import raise_database_not_configured
from core.database import get_db, is_db_configured


async def require_db(db: AsyncSession = Depends(get_db)) -> AsyncSession:
    """
    Dependency that requires database to be configured.

    Raises DatabaseNotConfiguredError 503 if database is not configured.
    Use this for endpoints that cannot function without a database.

    Args:
        db: Database session from get_db dependency

    Returns:
        Database session

    Raises:
        DatabaseNotConfiguredError: 503 Service Unavailable if database not configured

    Example:
        ```python
        @router.get("/specs")
        async def get_specs(db: AsyncSession = Depends(require_db)):
            # db is guaranteed to be configured
            ...
        ```
    """
    if not is_db_configured():
        raise_database_not_configured()
    return db


async def optional_db(db: AsyncSession = Depends(get_db)) -> AsyncSession | None:
    """
    Dependency that provides database session if configured, None otherwise.

    Use this for endpoints that can function with or without a database.

    Args:
        db: Database session from get_db dependency

    Returns:
        Database session if configured, None otherwise

    Example:
        ```python
        @router.get("/stats")
        async def get_stats(db: AsyncSession | None = Depends(optional_db)):
            if db is None:
                # Return default/fallback data
                return {"specs": 0, "plots": 0}
            # Use database
            ...
        ```
    """
    if not is_db_configured():
        return None
    return db
