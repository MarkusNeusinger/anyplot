"""
Async SQLAlchemy database connection for anyplot.

Supports two connection modes:
1. Cloud SQL Connector (recommended for Cloud Run) - uses INSTANCE_CONNECTION_NAME
2. Direct connection via DATABASE_URL (for local development)
"""

import asyncio
import logging
import os
import re
import threading
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager, contextmanager
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.pool import NullPool


logger = logging.getLogger(__name__)

# Environment variables
INSTANCE_CONNECTION_NAME = os.getenv("INSTANCE_CONNECTION_NAME", "")
DATABASE_URL = os.getenv("DATABASE_URL", "")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASS = os.getenv("DB_PASS", "")
DB_NAME = os.getenv("DB_NAME", "anyplot")
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")

# Database pool defaults
DEFAULT_POOL_SIZE = 5
DEFAULT_MAX_OVERFLOW = 10

# Global instances
engine = None
AsyncSessionLocal: Optional[async_sessionmaker] = None
_sync_session_factory = None
_connector = None

# Thread safety locks for lazy initialization
# Note: asyncio.Lock is created lazily to avoid event loop binding issues at module import
_async_init_lock: Optional[asyncio.Lock] = None
_sync_init_lock = threading.Lock()


def _get_async_lock() -> asyncio.Lock:
    """Get or create the async initialization lock.

    Creates the lock lazily to avoid event loop binding issues
    when the module is imported before an event loop exists.
    """
    global _async_init_lock
    if _async_init_lock is None:
        _async_init_lock = asyncio.Lock()
    return _async_init_lock


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models."""

    pass


def _normalize_db_url(url: str, target_driver: str) -> str:
    """Replace any PostgreSQL URL scheme with ``postgresql+<target_driver>://``.

    Handles ``postgresql://``, ``postgres://``, and ``postgresql+<driver>://`` prefixes.
    """
    return re.sub(r"^postgres(?:ql)?(?:\+\w+)?://", f"postgresql+{target_driver}://", url)


def _create_cloud_sql_engine_sync():
    """Create sync engine using Cloud SQL Python Connector with pg8000.

    Used for GitHub Actions scripts where async Cloud SQL Connector has event loop issues.
    """
    global _connector

    from google.cloud.sql.connector import Connector, IPTypes
    from sqlalchemy import create_engine

    _connector = Connector()

    def get_conn():
        return _connector.connect(
            INSTANCE_CONNECTION_NAME, "pg8000", user=DB_USER, password=DB_PASS, db=DB_NAME, ip_type=IPTypes.PUBLIC
        )

    engine = create_engine(
        "postgresql+pg8000://",
        creator=get_conn,
        pool_size=DEFAULT_POOL_SIZE,
        max_overflow=DEFAULT_MAX_OVERFLOW,
        pool_pre_ping=True,
        echo=ENVIRONMENT == "development",
    )

    logger.info(f"Created Cloud SQL engine: {INSTANCE_CONNECTION_NAME} (PUBLIC IP)")
    return engine


def _create_direct_engine():
    """Create sync engine using direct DATABASE_URL connection."""
    url = _normalize_db_url(DATABASE_URL, "asyncpg")

    # Use NullPool for testing to avoid connection issues
    poolclass = NullPool if ENVIRONMENT == "test" else None

    # Build engine kwargs - NullPool doesn't support pool_size/max_overflow
    engine_kwargs = {"echo": ENVIRONMENT == "development"}
    if poolclass:
        engine_kwargs["poolclass"] = poolclass
    else:
        engine_kwargs["pool_size"] = DEFAULT_POOL_SIZE
        engine_kwargs["max_overflow"] = DEFAULT_MAX_OVERFLOW
        engine_kwargs["pool_pre_ping"] = True

    engine = create_async_engine(url, **engine_kwargs)

    # Log without exposing password
    safe_url = url.split("@")[-1] if "@" in url else "local"
    logger.info(f"Created direct database engine: {safe_url}")
    return engine


def _create_direct_engine_sync():
    """Create sync engine using direct DATABASE_URL connection (for sync scripts)."""
    from sqlalchemy import create_engine

    url = _normalize_db_url(DATABASE_URL, "pg8000")

    engine_kwargs = {
        "echo": ENVIRONMENT == "development",
        "pool_size": DEFAULT_POOL_SIZE,
        "max_overflow": DEFAULT_MAX_OVERFLOW,
        "pool_pre_ping": True,
    }

    engine = create_engine(url, **engine_kwargs)

    # Log without exposing password
    safe_url = url.split("@")[-1] if "@" in url else "local"
    logger.info(f"Created direct sync database engine: {safe_url}")
    return engine


def init_db_sync() -> None:
    """
    Initialize sync database connection (for scripts like sync_to_postgres.py).

    Uses sync drivers for both local (psycopg2) and Cloud SQL (pg8000).
    """
    global engine, _sync_session_factory

    if _sync_session_factory is not None:
        return  # Already initialized

    from sqlalchemy.orm import sessionmaker

    if DATABASE_URL:
        # Use sync engine for local development
        engine = _create_direct_engine_sync()
        _sync_session_factory = sessionmaker(engine, expire_on_commit=False)
    elif INSTANCE_CONNECTION_NAME:
        # Use sync pg8000 driver for Cloud SQL Connector
        engine = _create_cloud_sql_engine_sync()
        _sync_session_factory = sessionmaker(engine, expire_on_commit=False)
    else:
        logger.warning("No database configuration found - running without database")
        return


async def init_db() -> None:
    """
    Initialize async database connection (for FastAPI).

    Priority:
    1. DATABASE_URL (direct connection) - for local development
    2. Cloud SQL Connector (INSTANCE_CONNECTION_NAME) - for Cloud Run
    """
    global engine, AsyncSessionLocal

    if engine is not None:
        return  # Already initialized

    # Prefer direct connection for local development
    if DATABASE_URL:
        engine = _create_direct_engine()
    elif INSTANCE_CONNECTION_NAME:
        # For async, use sync pg8000 wrapped - Cloud Run should use DATABASE_URL
        engine = _create_cloud_sql_engine_sync()
        logger.warning("Using sync Cloud SQL engine - consider using DATABASE_URL for async support")
    else:
        logger.warning("No database configuration found - running without database")
        return

    AsyncSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


def close_db_sync() -> None:
    """Close sync database connections and cleanup."""
    global engine, _sync_session_factory, _connector

    if engine:
        engine.dispose()
        engine = None
        _sync_session_factory = None
        logger.info("Database engine disposed")

    if _connector:
        _connector.close()
        _connector = None
        logger.info("Cloud SQL connector closed")


async def close_db() -> None:
    """Close async database connections and cleanup."""
    global engine, AsyncSessionLocal, _connector

    if engine:
        await engine.dispose()
        engine = None
        AsyncSessionLocal = None
        logger.info("Database engine disposed")

    if _connector:
        _connector.close()  # Use sync close
        _connector = None
        logger.info("Cloud SQL connector closed")


async def get_db() -> AsyncGenerator[AsyncSession | None, None]:
    """
    Dependency that provides a database session.

    Yields:
        AsyncSession if database is configured, None otherwise
    """
    # Thread-safe lazy initialization using asyncio.Lock
    if engine is None:
        async with _get_async_lock():
            # Double-check after acquiring lock
            if engine is None:
                await init_db()

    if AsyncSessionLocal is None:
        yield None
        return

    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


@asynccontextmanager
async def get_db_context() -> AsyncGenerator[AsyncSession, None]:
    """
    Context manager for database session (for scripts).

    Usage:
        async with get_db_context() as session:
            # Use session here
    """
    # Thread-safe lazy initialization using asyncio.Lock
    if engine is None:
        async with _get_async_lock():
            # Double-check after acquiring lock
            if engine is None:
                await init_db()

    if AsyncSessionLocal is None:
        raise RuntimeError("Database not configured")

    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


def is_db_configured() -> bool:
    """Check if database is configured (credentials available)."""
    return bool(INSTANCE_CONNECTION_NAME or DATABASE_URL)


@contextmanager
def get_db_context_sync():
    """
    Sync context manager for database session (for scripts in GitHub Actions).

    Usage:
        with get_db_context_sync() as session:
            # Use session here
    """
    # Thread-safe lazy initialization using threading.Lock
    if engine is None:
        with _sync_init_lock:
            # Double-check after acquiring lock
            if engine is None:
                init_db_sync()

    if _sync_session_factory is None:
        raise RuntimeError("Database not configured for sync access")

    session = _sync_session_factory()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
