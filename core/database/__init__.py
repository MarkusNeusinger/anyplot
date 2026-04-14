"""
Database module for anyplot.

Provides database connection, models, and repositories.
"""

from core.database.connection import (
    AsyncSessionLocal,
    Base,
    close_db,
    engine,
    get_db,
    get_db_context,
    init_db,
    is_db_configured,
)
from core.database.models import LIBRARIES_SEED, Impl, Library, Spec
from core.database.repositories import BaseRepository, ImplRepository, LibraryRepository, SpecRepository


__all__ = [
    # Connection
    "engine",
    "AsyncSessionLocal",
    "Base",
    "get_db",
    "get_db_context",
    "init_db",
    "close_db",
    "is_db_configured",
    # Models
    "Spec",
    "Library",
    "Impl",
    "LIBRARIES_SEED",
    # Repositories
    "BaseRepository",
    "SpecRepository",
    "LibraryRepository",
    "ImplRepository",
]
