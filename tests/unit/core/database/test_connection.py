"""Tests for core.database.connection module."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest


class TestIsDbConfigured:
    """Tests for is_db_configured function."""

    def test_configured_with_database_url(self, monkeypatch):
        """Returns True when DATABASE_URL is set."""
        monkeypatch.setenv("DATABASE_URL", "postgresql://localhost/test")
        monkeypatch.setenv("INSTANCE_CONNECTION_NAME", "")

        # Reload module to pick up new env vars
        import importlib

        import core.database.connection as conn

        importlib.reload(conn)

        assert conn.is_db_configured() is True

    def test_configured_with_instance_connection_name(self, monkeypatch):
        """Returns True when INSTANCE_CONNECTION_NAME is set."""
        monkeypatch.setenv("DATABASE_URL", "")
        monkeypatch.setenv("INSTANCE_CONNECTION_NAME", "project:region:instance")

        import importlib

        import core.database.connection as conn

        importlib.reload(conn)

        assert conn.is_db_configured() is True

    def test_not_configured(self, monkeypatch):
        """Returns False when neither is set."""
        monkeypatch.setenv("DATABASE_URL", "")
        monkeypatch.setenv("INSTANCE_CONNECTION_NAME", "")

        import importlib

        import core.database.connection as conn

        importlib.reload(conn)

        assert conn.is_db_configured() is False


class TestCreateDirectEngine:
    """Tests for _create_direct_engine function."""

    def test_creates_engine_with_asyncpg(self, monkeypatch):
        """Should create engine with asyncpg driver."""
        monkeypatch.setenv("DATABASE_URL", "postgresql://user:pass@localhost/db")
        monkeypatch.setenv("ENVIRONMENT", "development")

        import importlib

        import core.database.connection as conn

        importlib.reload(conn)

        with patch("core.database.connection.create_async_engine") as mock_create:
            mock_engine = MagicMock()
            mock_create.return_value = mock_engine

            engine = conn._create_direct_engine()

            mock_create.assert_called_once()
            call_args = mock_create.call_args
            assert "postgresql+asyncpg://" in call_args[0][0]
            assert engine == mock_engine

    def test_converts_postgres_to_asyncpg(self, monkeypatch):
        """Should convert postgres:// to postgresql+asyncpg://."""
        monkeypatch.setenv("DATABASE_URL", "postgres://user:pass@localhost/db")
        monkeypatch.setenv("ENVIRONMENT", "development")

        import importlib

        import core.database.connection as conn

        importlib.reload(conn)

        with patch("core.database.connection.create_async_engine") as mock_create:
            mock_engine = MagicMock()
            mock_create.return_value = mock_engine

            conn._create_direct_engine()

            call_args = mock_create.call_args
            assert "postgresql+asyncpg://" in call_args[0][0]

    def test_uses_null_pool_in_test_environment(self, monkeypatch):
        """Should use NullPool in test environment."""
        monkeypatch.setenv("DATABASE_URL", "postgresql://user:pass@localhost/db")
        monkeypatch.setenv("ENVIRONMENT", "test")

        import importlib

        import core.database.connection as conn

        importlib.reload(conn)

        with patch("core.database.connection.create_async_engine") as mock_create:
            mock_engine = MagicMock()
            mock_create.return_value = mock_engine

            conn._create_direct_engine()

            call_args = mock_create.call_args
            assert call_args[1].get("poolclass") is not None

    def test_uses_pool_in_production(self, monkeypatch):
        """Should use connection pool in production."""
        monkeypatch.setenv("DATABASE_URL", "postgresql://user:pass@localhost/db")
        monkeypatch.setenv("ENVIRONMENT", "production")

        import importlib

        import core.database.connection as conn

        importlib.reload(conn)

        with patch("core.database.connection.create_async_engine") as mock_create:
            mock_engine = MagicMock()
            mock_create.return_value = mock_engine

            conn._create_direct_engine()

            call_args = mock_create.call_args
            assert call_args[1].get("pool_size") == 5
            assert call_args[1].get("max_overflow") == 10


class TestInitDbSync:
    """Tests for init_db_sync function."""

    def test_skips_if_already_initialized(self, monkeypatch):
        """Should skip initialization if engine exists."""
        import importlib

        import core.database.connection as conn

        importlib.reload(conn)

        # Set engine to non-None
        conn.engine = MagicMock()

        with patch.object(conn, "_create_direct_engine") as mock_create:
            conn.init_db_sync()
            mock_create.assert_not_called()

        # Cleanup
        conn.engine = None

    def test_creates_direct_engine_with_database_url(self, monkeypatch):
        """Should create direct engine when DATABASE_URL is set."""
        monkeypatch.setenv("DATABASE_URL", "postgresql://localhost/test")
        monkeypatch.setenv("INSTANCE_CONNECTION_NAME", "")

        import importlib

        import core.database.connection as conn

        importlib.reload(conn)
        conn.engine = None  # Ensure clean state
        conn._sync_session_factory = None  # Reset sync session factory

        with patch.object(conn, "_create_direct_engine_sync") as mock_create:
            mock_engine = MagicMock()
            mock_create.return_value = mock_engine

            conn.init_db_sync()

            mock_create.assert_called_once()
            assert conn.engine == mock_engine

        # Cleanup
        conn.engine = None
        conn._sync_session_factory = None

    def test_warns_when_no_config(self, monkeypatch, caplog):
        """Should warn when no database configuration found."""
        monkeypatch.setenv("DATABASE_URL", "")
        monkeypatch.setenv("INSTANCE_CONNECTION_NAME", "")

        import importlib

        import core.database.connection as conn

        importlib.reload(conn)
        conn.engine = None

        conn.init_db_sync()

        assert conn.engine is None


class TestInitDb:
    """Tests for init_db async function."""

    @pytest.mark.asyncio
    async def test_skips_if_already_initialized(self, monkeypatch):
        """Should skip initialization if engine exists."""
        import importlib

        import core.database.connection as conn

        importlib.reload(conn)

        conn.engine = MagicMock()

        with patch.object(conn, "_create_direct_engine") as mock_create:
            await conn.init_db()
            mock_create.assert_not_called()

        conn.engine = None

    @pytest.mark.asyncio
    async def test_creates_direct_engine(self, monkeypatch):
        """Should create direct engine with DATABASE_URL."""
        monkeypatch.setenv("DATABASE_URL", "postgresql://localhost/test")
        monkeypatch.setenv("INSTANCE_CONNECTION_NAME", "")

        import importlib

        import core.database.connection as conn

        importlib.reload(conn)
        conn.engine = None
        conn.AsyncSessionLocal = None

        with patch.object(conn, "_create_direct_engine") as mock_create:
            mock_engine = MagicMock()
            mock_create.return_value = mock_engine

            await conn.init_db()

            mock_create.assert_called_once()

        conn.engine = None
        conn.AsyncSessionLocal = None


class TestCloseDbSync:
    """Tests for close_db_sync function."""

    def test_disposes_engine(self, monkeypatch):
        """Should dispose engine and reset globals."""
        import importlib

        import core.database.connection as conn

        importlib.reload(conn)

        mock_engine = MagicMock()
        conn.engine = mock_engine
        conn._sync_session_factory = MagicMock()

        conn.close_db_sync()

        mock_engine.dispose.assert_called_once()
        assert conn.engine is None
        assert conn._sync_session_factory is None

    def test_closes_connector(self, monkeypatch):
        """Should close Cloud SQL connector."""
        import importlib

        import core.database.connection as conn

        importlib.reload(conn)

        mock_connector = MagicMock()
        conn._connector = mock_connector
        conn.engine = None

        conn.close_db_sync()

        mock_connector.close.assert_called_once()
        assert conn._connector is None


class TestCloseDb:
    """Tests for close_db async function."""

    @pytest.mark.asyncio
    async def test_disposes_engine(self, monkeypatch):
        """Should dispose engine and reset globals."""
        import importlib

        import core.database.connection as conn

        importlib.reload(conn)

        mock_engine = AsyncMock()
        conn.engine = mock_engine
        conn.AsyncSessionLocal = MagicMock()

        await conn.close_db()

        mock_engine.dispose.assert_called_once()
        assert conn.engine is None
        assert conn.AsyncSessionLocal is None

    @pytest.mark.asyncio
    async def test_closes_connector(self, monkeypatch):
        """Should close Cloud SQL connector via its async close."""
        import importlib

        import core.database.connection as conn

        importlib.reload(conn)

        mock_connector = MagicMock()
        mock_connector.close_async = AsyncMock()
        conn._connector = mock_connector
        conn.engine = None

        await conn.close_db()

        mock_connector.close_async.assert_awaited_once()
        assert conn._connector is None


class TestGetDb:
    """Tests for get_db async generator."""

    @pytest.mark.asyncio
    async def test_yields_none_when_not_configured(self, monkeypatch):
        """Should yield None when database not configured."""
        monkeypatch.setenv("DATABASE_URL", "")
        monkeypatch.setenv("INSTANCE_CONNECTION_NAME", "")

        import importlib

        import core.database.connection as conn

        importlib.reload(conn)
        conn.engine = None
        conn.AsyncSessionLocal = None

        async for session in conn.get_db():
            assert session is None

    @pytest.mark.asyncio
    async def test_yields_session_and_commits(self, monkeypatch):
        """Should yield session and commit on success."""
        import importlib

        import core.database.connection as conn

        importlib.reload(conn)

        mock_session = AsyncMock()
        mock_session_class = MagicMock()
        mock_session_class.return_value.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session_class.return_value.__aexit__ = AsyncMock(return_value=None)

        conn.engine = MagicMock()
        conn.AsyncSessionLocal = mock_session_class

        async for session in conn.get_db():
            assert session == mock_session

        mock_session.commit.assert_called_once()

        conn.engine = None
        conn.AsyncSessionLocal = None

    @pytest.mark.asyncio
    async def test_initializes_db_if_needed(self, monkeypatch):
        """Should initialize database if engine is None."""
        monkeypatch.setenv("DATABASE_URL", "")
        monkeypatch.setenv("INSTANCE_CONNECTION_NAME", "")

        import importlib

        import core.database.connection as conn

        importlib.reload(conn)
        conn.engine = None
        conn.AsyncSessionLocal = None

        # Should call init_db and yield None when not configured
        with patch.object(conn, "init_db", new=AsyncMock()) as mock_init:
            async for session in conn.get_db():
                assert session is None

            mock_init.assert_called_once()


class TestGetDbContext:
    """Tests for get_db_context async context manager."""

    @pytest.mark.asyncio
    async def test_raises_when_not_configured(self, monkeypatch):
        """Should raise RuntimeError when database not configured."""
        monkeypatch.setenv("DATABASE_URL", "")
        monkeypatch.setenv("INSTANCE_CONNECTION_NAME", "")

        import importlib

        import core.database.connection as conn

        importlib.reload(conn)
        conn.engine = None
        conn.AsyncSessionLocal = None

        with pytest.raises(RuntimeError, match="Database not configured"):
            async with conn.get_db_context():
                pass

    @pytest.mark.asyncio
    async def test_yields_session_and_commits(self, monkeypatch):
        """Should yield session and commit on success."""
        import importlib

        import core.database.connection as conn

        importlib.reload(conn)

        mock_session = AsyncMock()
        mock_session_class = MagicMock()
        mock_session_class.return_value.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session_class.return_value.__aexit__ = AsyncMock(return_value=None)

        conn.engine = MagicMock()
        conn.AsyncSessionLocal = mock_session_class

        async with conn.get_db_context() as session:
            assert session == mock_session

        mock_session.commit.assert_called_once()

        conn.engine = None
        conn.AsyncSessionLocal = None

    @pytest.mark.asyncio
    async def test_rollback_on_exception(self, monkeypatch):
        """Should rollback on exception."""
        import importlib

        import core.database.connection as conn

        importlib.reload(conn)

        mock_session = AsyncMock()
        mock_session_class = MagicMock()
        mock_session_class.return_value.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session_class.return_value.__aexit__ = AsyncMock(return_value=None)

        conn.engine = MagicMock()
        conn.AsyncSessionLocal = mock_session_class

        with pytest.raises(ValueError):
            async with conn.get_db_context():
                raise ValueError("test error")

        mock_session.rollback.assert_called_once()

        conn.engine = None
        conn.AsyncSessionLocal = None


class TestGetDbContextSync:
    """Tests for get_db_context_sync context manager."""

    def test_raises_when_not_configured(self, monkeypatch):
        """Should raise RuntimeError when database not configured."""
        monkeypatch.setenv("DATABASE_URL", "")
        monkeypatch.setenv("INSTANCE_CONNECTION_NAME", "")

        import importlib

        import core.database.connection as conn

        importlib.reload(conn)
        conn.engine = None
        conn._sync_session_factory = None

        with pytest.raises(RuntimeError, match="Database not configured for sync access"):
            with conn.get_db_context_sync():
                pass

    def test_yields_session_and_commits(self, monkeypatch):
        """Should yield session and commit on success."""
        import importlib

        import core.database.connection as conn

        importlib.reload(conn)

        mock_session = MagicMock()
        mock_factory = MagicMock(return_value=mock_session)

        conn.engine = MagicMock()
        conn._sync_session_factory = mock_factory

        with conn.get_db_context_sync() as session:
            assert session == mock_session

        mock_session.commit.assert_called_once()
        mock_session.close.assert_called_once()

        conn.engine = None
        conn._sync_session_factory = None

    def test_rollback_on_exception(self, monkeypatch):
        """Should rollback on exception."""
        import importlib

        import core.database.connection as conn

        importlib.reload(conn)

        mock_session = MagicMock()
        mock_factory = MagicMock(return_value=mock_session)

        conn.engine = MagicMock()
        conn._sync_session_factory = mock_factory

        with pytest.raises(ValueError):
            with conn.get_db_context_sync():
                raise ValueError("test error")

        mock_session.rollback.assert_called_once()
        mock_session.close.assert_called_once()

        conn.engine = None
        conn._sync_session_factory = None


class TestInitDbSyncWithCloudSql:
    """Tests for init_db_sync with Cloud SQL Connector."""

    def test_creates_sync_session_factory(self, monkeypatch):
        """Should create sync session factory with Cloud SQL."""
        monkeypatch.setenv("DATABASE_URL", "")
        monkeypatch.setenv("INSTANCE_CONNECTION_NAME", "project:region:instance")

        import importlib

        import core.database.connection as conn

        importlib.reload(conn)
        conn.engine = None
        conn._sync_session_factory = None

        mock_engine = MagicMock()
        mock_sessionmaker = MagicMock()

        with (
            patch.object(conn, "_create_cloud_sql_engine_sync", return_value=mock_engine),
            patch("sqlalchemy.orm.sessionmaker", return_value=mock_sessionmaker),
        ):
            conn.init_db_sync()

            assert conn.engine == mock_engine
            assert conn._sync_session_factory == mock_sessionmaker

        conn.engine = None
        conn._sync_session_factory = None


class TestInitDbWithCloudSql:
    """Tests for init_db with Cloud SQL Connector."""

    @pytest.mark.asyncio
    async def test_creates_async_cloud_sql_engine(self, monkeypatch):
        """Should create the async Cloud SQL engine (never the sync pg8000 one)."""
        monkeypatch.setenv("DATABASE_URL", "")
        monkeypatch.setenv("INSTANCE_CONNECTION_NAME", "project:region:instance")

        import importlib

        import core.database.connection as conn

        importlib.reload(conn)
        conn.engine = None
        conn.AsyncSessionLocal = None

        mock_engine = MagicMock()

        with (
            patch.object(conn, "_create_cloud_sql_engine_async", return_value=mock_engine) as mock_create_async,
            patch.object(conn, "_create_cloud_sql_engine_sync") as mock_create_sync,
        ):
            await conn.init_db()

            mock_create_async.assert_called_once()
            mock_create_sync.assert_not_called()
            assert conn.engine == mock_engine
            assert conn.AsyncSessionLocal is not None

        conn.engine = None
        conn.AsyncSessionLocal = None


class TestCreateCloudSqlEngineAsync:
    """Tests for _create_cloud_sql_engine_async function."""

    @pytest.mark.asyncio
    async def test_uses_async_creator_with_asyncpg(self, monkeypatch):
        """Should build an asyncpg engine with an async_creator, not a sync creator."""
        monkeypatch.setenv("DATABASE_URL", "")
        monkeypatch.setenv("INSTANCE_CONNECTION_NAME", "project:region:instance")

        import importlib

        import core.database.connection as conn

        importlib.reload(conn)

        mock_connector = MagicMock()
        mock_connector.connect_async = AsyncMock(return_value=MagicMock())

        with (
            patch("google.cloud.sql.connector.Connector", return_value=mock_connector) as mock_connector_cls,
            patch("core.database.connection.create_async_engine") as mock_create,
        ):
            engine = conn._create_cloud_sql_engine_async()

            # Connector is bound to the running event loop
            assert mock_connector_cls.call_args[1].get("loop") is not None
            assert engine == mock_create.return_value
            assert mock_create.call_args[0][0] == "postgresql+asyncpg://"
            kwargs = mock_create.call_args[1]
            assert "async_creator" in kwargs
            assert "creator" not in kwargs

            # The async creator awaits connect_async with the asyncpg driver
            await kwargs["async_creator"]()
            assert mock_connector.connect_async.await_args[0][1] == "asyncpg"

        conn._connector = None
