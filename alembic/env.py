"""
Alembic environment configuration for async migrations.

Supports two connection modes:
1. DATABASE_URL - Direct connection (local development)
2. INSTANCE_CONNECTION_NAME - Cloud SQL Connector (GitHub Actions, Cloud Run)
"""

import asyncio
import os
from logging.config import fileConfig
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from alembic import context


# Load environment variables from this checkout's .env only. A bare
# load_dotenv() walks up past a git worktree into the main checkout's .env, and
# Alembic would then run migrations against that DATABASE_URL.
load_dotenv(Path(__file__).resolve().parents[1] / ".env")

# Import models to register them with Base.metadata (required for autogenerate)
# These imports ARE used - SQLAlchemy needs them loaded to detect schema changes
from core.database import Base, Impl, Library, Spec  # noqa: E402, F401


# Alembic Config object
config = context.config

# Environment variables
DATABASE_URL = os.getenv("DATABASE_URL", "")
INSTANCE_CONNECTION_NAME = os.getenv("INSTANCE_CONNECTION_NAME", "")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASS = os.getenv("DB_PASS", "")
DB_NAME = os.getenv("DB_NAME", "anyplot")

# Override sqlalchemy.url with DATABASE_URL from environment (for direct connections)
if DATABASE_URL:
    # Escape % characters for configparser (double them)
    config.set_main_option("sqlalchemy.url", DATABASE_URL.replace("%", "%%"))

# Setup logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Target metadata for autogenerate
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """
    Run migrations in 'offline' mode.

    Configures the context with just a URL and not an Engine.
    Calls to context.execute() emit the given string to the script output.
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url, target_metadata=target_metadata, literal_binds=True, dialect_opts={"paramstyle": "named"}
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    """Run migrations with the given connection."""
    context.configure(connection=connection, target_metadata=target_metadata)

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_with_cloud_sql() -> None:
    """Run migrations using Cloud SQL Connector (sync pg8000 driver)."""
    from google.cloud.sql.connector import Connector, IPTypes
    from sqlalchemy import create_engine

    connector = Connector()

    def get_conn():
        return connector.connect(
            INSTANCE_CONNECTION_NAME, "pg8000", user=DB_USER, password=DB_PASS, db=DB_NAME, ip_type=IPTypes.PUBLIC
        )

    engine = create_engine("postgresql+pg8000://", creator=get_conn, poolclass=pool.NullPool)

    try:
        with engine.connect() as connection:
            do_run_migrations(connection)
    finally:
        engine.dispose()
        connector.close()


async def run_async_migrations() -> None:
    """Run migrations in 'online' mode with async engine (DATABASE_URL only)."""
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}), prefix="sqlalchemy.", poolclass=pool.NullPool
    )

    try:
        async with connectable.connect() as connection:
            await connection.run_sync(do_run_migrations)
    finally:
        await connectable.dispose()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    if INSTANCE_CONNECTION_NAME and not DATABASE_URL:
        # Use Cloud SQL Connector with sync pg8000 driver
        run_migrations_with_cloud_sql()
    else:
        # Use async with DATABASE_URL
        asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
