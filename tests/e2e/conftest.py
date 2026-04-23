"""
E2E test fixtures with real PostgreSQL database.

Uses a separate 'test' database to isolate test data from production.
Each test gets its own schema for complete isolation, allowing parallel execution.
Tests are skipped if DATABASE_URL is not set or database is unreachable.

Connection modes:
- Local: Direct DATABASE_URL from .env (auto-derives test database)
- CI: DATABASE_URL via Cloud SQL Proxy (localhost:5432 -> Cloud SQL)
- Explicit: TEST_DATABASE_URL for custom test database
"""

import asyncio
import os
import uuid

import pytest
import pytest_asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from core.database.models import Base


CONNECTION_TIMEOUT = 10  # seconds - skip tests if DB unreachable

# Test data constants
TEST_IMAGE_URL = "https://storage.googleapis.com/anyplot-images/test/plot.png"


def _get_database_url():
    """Get test database URL, defaulting to 'test' database on same instance."""
    from dotenv import load_dotenv

    load_dotenv()

    # Prefer explicit TEST_DATABASE_URL
    database_url = os.environ.get("TEST_DATABASE_URL")

    if not database_url:
        # Derive from DATABASE_URL by replacing database name with 'test'
        prod_url = os.environ.get("DATABASE_URL")
        if not prod_url:
            return None
        # Replace database name at end of URL (e.g., /anyplot -> /test)
        database_url = prod_url.rsplit("/", 1)[0] + "/test"

    # Ensure async driver
    if database_url.startswith("postgresql://"):
        database_url = database_url.replace("postgresql://", "postgresql+asyncpg://")
    elif database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql+asyncpg://")

    return database_url


@pytest_asyncio.fixture(scope="function")
async def pg_engine_with_schema():
    """
    Create PostgreSQL engine for test database with isolated schema.

    Each test gets its own schema (test_<uuid>) for complete isolation,
    allowing tests to run in parallel without conflicts.
    Skips tests if database is unreachable.

    Returns tuple of (engine, schema_name).
    """
    database_url = _get_database_url()
    if not database_url:
        pytest.skip("DATABASE_URL not set - skipping PostgreSQL E2E tests")

    # Generate unique schema name for this test
    schema_name = f"test_{uuid.uuid4().hex[:8]}"

    engine = create_async_engine(database_url, echo=False, connect_args={"timeout": CONNECTION_TIMEOUT})

    try:
        async with asyncio.timeout(CONNECTION_TIMEOUT + 2):
            async with engine.begin() as conn:
                # Create isolated schema for this test
                await conn.execute(text(f"CREATE SCHEMA IF NOT EXISTS {schema_name}"))
                await conn.execute(text(f"SET search_path TO {schema_name}"))
                # Create tables in this schema
                await conn.run_sync(Base.metadata.create_all)
    except (TimeoutError, asyncio.TimeoutError, OSError) as e:
        await engine.dispose()
        pytest.skip(f"Database unreachable (timeout) - skipping E2E tests: {e}")
    except Exception as e:
        await engine.dispose()
        pytest.skip(f"Database connection failed - skipping E2E tests: {e}")

    yield engine, schema_name

    # Cleanup: Drop the test schema
    try:
        async with engine.begin() as conn:
            await conn.execute(text(f"DROP SCHEMA IF EXISTS {schema_name} CASCADE"))
    except Exception:
        pass  # Ignore cleanup errors
    await engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def pg_engine(pg_engine_with_schema):
    """Get just the engine from pg_engine_with_schema."""
    engine, _ = pg_engine_with_schema
    return engine


@pytest_asyncio.fixture(scope="function")
async def pg_session(pg_engine_with_schema):
    """Create session for test database with isolated schema."""
    engine, schema_name = pg_engine_with_schema

    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session() as session:
        # Set search_path to the test schema
        await session.execute(text(f"SET search_path TO {schema_name}"))
        yield session
        await session.rollback()


@pytest_asyncio.fixture(scope="function")
async def pg_db_with_data(pg_session):
    """
    Seed test database with sample data.

    Creates the same test data as tests/conftest.py:test_db_with_data
    but in the PostgreSQL test database (in an isolated schema).

    Uses atomic commit: libraries + specs flushed first (FK targets),
    then impls added and everything committed together.
    """
    from core.database.models import Impl, Language, Library, Spec

    # Seed languages (FK target for libraries.language_id / impls.language_id).
    # Alembic migration seeds this in prod; tests build schema via create_all, so we seed here.
    python_lang = Language(
        id="python",
        name="Python",
        file_extension=".py",
        runtime_version="3.14",
        documentation_url="https://python.org",
        description="Python programming language",
    )

    # Create libraries
    matplotlib_lib = Library(
        id="matplotlib",
        name="Matplotlib",
        version="3.10.0",
        documentation_url="https://matplotlib.org",
        description="Comprehensive library for visualizations",
    )
    seaborn_lib = Library(
        id="seaborn",
        name="Seaborn",
        version="0.13.0",
        documentation_url="https://seaborn.pydata.org",
        description="Statistical data visualization",
    )

    # Create specs
    scatter_spec = Spec(
        id="scatter-basic",
        title="Basic Scatter Plot",
        description="A basic scatter plot",
        applications=["data visualization", "correlation analysis"],
        data=["numeric"],
        notes=["Use for 2D data"],
        tags={"plot_type": ["scatter"], "domain": ["statistics"], "data_type": ["numeric"], "features": ["basic"]},
        issue=42,
        suggested="contributor",
    )
    bar_spec = Spec(
        id="bar-grouped",
        title="Grouped Bar Chart",
        description="A grouped bar chart",
        applications=["comparisons"],
        data=["categorical", "numeric"],
        notes=["Good for comparing categories"],
        tags={"plot_type": ["bar"], "domain": ["statistics"], "data_type": ["categorical"], "features": ["grouped"]},
        issue=43,
        suggested="contributor2",
    )

    # Create implementations
    scatter_matplotlib = Impl(
        spec_id="scatter-basic",
        library_id="matplotlib",
        code="import matplotlib.pyplot as plt\n# scatter plot code",
        preview_url=TEST_IMAGE_URL.replace("plot", "scatter-matplotlib"),
        quality_score=92.5,
        generated_by="claude",
        python_version="3.13",
        library_version="3.10.0",
    )
    scatter_seaborn = Impl(
        spec_id="scatter-basic",
        library_id="seaborn",
        code="import seaborn as sns\n# scatter plot code",
        preview_url=TEST_IMAGE_URL.replace("plot", "scatter-seaborn"),
        quality_score=95.0,
        generated_by="claude",
        python_version="3.13",
        library_version="0.13.0",
    )
    bar_matplotlib = Impl(
        spec_id="bar-grouped",
        library_id="matplotlib",
        code="import matplotlib.pyplot as plt\n# bar chart code",
        preview_url=TEST_IMAGE_URL.replace("plot", "bar-matplotlib"),
        quality_score=88.0,
        generated_by="claude",
        python_version="3.13",
        library_version="3.10.0",
    )

    # Add FK targets first (languages, then libraries and specs)
    pg_session.add(python_lang)
    await pg_session.flush()  # Language must exist before libraries reference it
    pg_session.add_all([matplotlib_lib, seaborn_lib])
    pg_session.add_all([scatter_spec, bar_spec])
    await pg_session.flush()  # Ensure FK targets exist before adding children

    # Add FK children (implementations)
    pg_session.add_all([scatter_matplotlib, scatter_seaborn, bar_matplotlib])
    await pg_session.commit()  # Single atomic commit

    # Expire all cached objects to ensure fresh loading with relationships
    pg_session.expire_all()

    yield pg_session
