"""
Tests for core/config.py.

Tests the Settings configuration class and environment variable handling.
"""

import os
from unittest.mock import patch

from core.config import Settings


class TestSettings:
    """Tests for Settings class."""

    def test_default_environment(self) -> None:
        """Should default to development environment."""
        with patch.dict(os.environ, {}, clear=True):
            settings = Settings()
            assert settings.environment == "development"

    def test_custom_environment(self) -> None:
        """Should accept custom environment."""
        with patch.dict(os.environ, {"ENVIRONMENT": "production"}, clear=True):
            settings = Settings()
            assert settings.environment == "production"

    def test_database_url_from_env(self) -> None:
        """Should read DATABASE_URL from environment."""
        test_url = "postgresql+asyncpg://user:pass@localhost:5432/db"
        with patch.dict(os.environ, {"DATABASE_URL": test_url}, clear=True):
            settings = Settings()
            assert settings.database_url == test_url

    def test_instance_connection_name_from_env(self) -> None:
        """Should read INSTANCE_CONNECTION_NAME from environment."""
        test_name = "project:region:instance"
        with patch.dict(os.environ, {"INSTANCE_CONNECTION_NAME": test_name}, clear=True):
            settings = Settings()
            assert settings.instance_connection_name == test_name

    def test_gcs_bucket_from_env(self) -> None:
        """Should read GCS_BUCKET from environment."""
        with patch.dict(os.environ, {"GCS_BUCKET": "test-bucket"}, clear=True):
            settings = Settings()
            assert settings.gcs_bucket == "test-bucket"

    def test_gcs_bucket_default(self) -> None:
        """Should have default GCS bucket."""
        with patch.dict(os.environ, {}, clear=True):
            settings = Settings(_env_file=None)
            assert settings.gcs_bucket == "anyplot-images"

    def test_github_token_from_env(self) -> None:
        """Should read GITHUB_TOKEN from environment."""
        with patch.dict(os.environ, {"GITHUB_TOKEN": "ghp_test123"}, clear=True):
            settings = Settings()
            assert settings.github_token == "ghp_test123"


class TestSettingsProperties:
    """Tests for Settings property methods."""

    def test_is_production(self) -> None:
        """Should return True when environment is production."""
        with patch.dict(os.environ, {"ENVIRONMENT": "production"}, clear=True):
            settings = Settings()
            assert settings.is_production is True
            assert settings.is_development is False
            assert settings.is_test is False

    def test_is_development(self) -> None:
        """Should return True when environment is development."""
        with patch.dict(os.environ, {"ENVIRONMENT": "development"}, clear=True):
            settings = Settings()
            assert settings.is_production is False
            assert settings.is_development is True
            assert settings.is_test is False

    def test_is_test(self) -> None:
        """Should return True when environment is test."""
        with patch.dict(os.environ, {"ENVIRONMENT": "test"}, clear=True):
            settings = Settings()
            assert settings.is_production is False
            assert settings.is_development is False
            assert settings.is_test is True

    def test_is_database_configured_with_database_url(self) -> None:
        """Should return True when DATABASE_URL is set."""
        test_url = "postgresql+asyncpg://localhost/db"
        with patch.dict(os.environ, {"DATABASE_URL": test_url}, clear=True):
            settings = Settings()
            assert settings.is_database_configured is True

    def test_is_database_configured_with_instance_name(self) -> None:
        """Should return True when INSTANCE_CONNECTION_NAME is set."""
        with patch.dict(os.environ, {"INSTANCE_CONNECTION_NAME": "project:region:instance"}, clear=True):
            settings = Settings()
            assert settings.is_database_configured is True

    def test_is_database_configured_with_both(self) -> None:
        """Should return True when both database configs are set."""
        with patch.dict(
            os.environ,
            {
                "DATABASE_URL": "postgresql+asyncpg://localhost/db",
                "INSTANCE_CONNECTION_NAME": "project:region:instance",
            },
            clear=True,
        ):
            settings = Settings()
            assert settings.is_database_configured is True

    def test_is_database_configured_with_neither(self) -> None:
        """Should return False when no database config is set."""
        with patch.dict(os.environ, {}, clear=True):
            settings = Settings(_env_file=None)
            assert settings.is_database_configured is False

    def test_has_google_cloud_with_credentials(self) -> None:
        """Should return True when google cloud credentials are set."""
        with patch.dict(os.environ, {"GOOGLE_APPLICATION_CREDENTIALS": "/path/to/creds.json"}, clear=True):
            settings = Settings()
            assert settings.has_google_cloud is True

    def test_has_google_cloud_without_credentials(self) -> None:
        """Should return False when google cloud credentials are not set."""
        with patch.dict(os.environ, {}, clear=True):
            settings = Settings(_env_file=None)
            assert settings.has_google_cloud is False


class TestSettingsDefaults:
    """Tests for Settings default values."""

    def test_default_cors_origins(self) -> None:
        """Should have default CORS origins."""
        with patch.dict(os.environ, {}, clear=True):
            settings = Settings()
            assert isinstance(settings.cors_origins, list)
            assert len(settings.cors_origins) > 0

    def test_default_cache_ttl(self) -> None:
        """Should have default cache TTL."""
        with patch.dict(os.environ, {}, clear=True):
            settings = Settings()
            assert settings.cache_ttl == 86400  # 24 hours

    def test_custom_cache_ttl(self) -> None:
        """Should accept custom cache TTL."""
        with patch.dict(os.environ, {"CACHE_TTL": "600"}, clear=True):
            settings = Settings()
            assert settings.cache_ttl == 600


class TestSettingsSingleton:
    """Tests for settings singleton pattern."""

    def test_settings_import(self) -> None:
        """Should be able to import settings instance."""
        from core.config import settings

        assert isinstance(settings, Settings)

    def test_settings_is_singleton(self) -> None:
        """Settings should be a single instance."""
        from core.config import settings as settings1
        from core.config import settings as settings2

        assert settings1 is settings2
