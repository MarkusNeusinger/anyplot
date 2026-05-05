"""
Centralized configuration management using Pydantic Settings.

All environment variables are defined here with type validation,
defaults, and documentation.
"""

from typing import Annotated, Any

from pydantic import field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.

    Environment variables are loaded from .env file if present.
    """

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", case_sensitive=False, extra="ignore")

    # =============================================================================
    # DATABASE
    # =============================================================================

    database_url: str | None = None
    """PostgreSQL connection URL (postgresql+asyncpg://user:pass@host:5432/dbname)"""

    instance_connection_name: str | None = None
    """Cloud SQL instance connection name (for Cloud Run deployment)"""

    db_user: str = "postgres"
    """Database user"""

    db_pass: str = ""
    """Database password"""

    db_name: str = "anyplot"
    """Database name"""

    # =============================================================================
    # GOOGLE CLOUD
    # =============================================================================

    gcs_bucket: str = "anyplot-images"
    """Google Cloud Storage bucket for plot images"""

    google_application_credentials: str | None = None
    """Path to Google Cloud service account credentials JSON"""

    # =============================================================================
    # APPLICATION
    # =============================================================================

    environment: str = "development"
    """Environment: development, staging, or production"""

    base_url: str = "https://anyplot.ai"
    """Base URL for the application (used in sitemaps, etc.)"""

    api_version: str = "1.0.0"
    """API version"""

    # =============================================================================
    # GITHUB
    # =============================================================================

    github_token: str | None = None
    """GitHub personal access token for API access"""

    github_repository: str = "MarkusNeusinger/anyplot"
    """GitHub repository in format owner/repo"""

    # =============================================================================
    # API KEYS (for AI services)
    # =============================================================================

    anthropic_api_key: str | None = None
    """Anthropic API key for Claude"""

    openai_api_key: str | None = None
    """OpenAI API key"""

    google_ai_api_key: str | None = None
    """Google AI API key for Gemini"""

    # =============================================================================
    # AI MODEL CONFIGURATION
    # =============================================================================

    claude_model: str = "claude-3-5-sonnet-20240620"
    """Claude model to use for code generation and review"""

    claude_max_tokens: int = 4000
    """Maximum tokens for Claude code generation responses"""

    claude_review_max_tokens: int = 2000
    """Maximum tokens for Claude review responses"""

    # =============================================================================
    # CLI MODEL TIER CONFIGURATION
    # =============================================================================
    # Model tiers (small/medium/large) map to CLI-specific model names.
    # Override these to use different models for each tier.

    cli_model_claude_small: str = "haiku"
    """Claude model for 'small' tier (fast/cheap tasks)"""

    cli_model_claude_medium: str = "sonnet"
    """Claude model for 'medium' tier (balanced tasks)"""

    cli_model_claude_large: str = "opus"
    """Claude model for 'large' tier (complex tasks)"""

    cli_model_copilot_small: str = "gpt-4o-mini"
    """Copilot model for 'small' tier"""

    cli_model_copilot_medium: str = "gpt-4o"
    """Copilot model for 'medium' tier"""

    cli_model_copilot_large: str = "o1"
    """Copilot model for 'large' tier"""

    cli_model_gemini_small: str = "gemini-2.0-flash"
    """Gemini model for 'small' tier"""

    cli_model_gemini_medium: str = "gemini-2.0-flash-thinking"
    """Gemini model for 'medium' tier"""

    cli_model_gemini_large: str = "gemini-2.5-pro"
    """Gemini model for 'large' tier"""

    # =============================================================================
    # CACHE
    # =============================================================================

    cache_ttl: int = 86400
    """Cache TTL in seconds (24h hard expiry). Combined with cache_refresh_after for stale-while-revalidate:
    entries older than cache_refresh_after trigger a background refresh while the user still gets an instant response."""

    cache_refresh_after: int = 3600
    """Trigger background cache refresh after this many seconds (default: 1h)"""

    cache_maxsize: int = 1000
    """Maximum number of cache entries"""

    cache_invalidate_token: str | None = None
    """Shared secret required by the POST /debug/cache/invalidate endpoint.
    When unset, the endpoint is disabled (503). Set via Secret Manager in Cloud Run
    and as a GitHub Actions secret so sync-postgres can invalidate the cache after
    writing new data to PostgreSQL."""

    admin_token: str | None = None
    """Shared secret required by sensitive /debug/* endpoints (status, ping).
    When unset, those endpoints return 503 instead of leaking quality scores,
    weakness aggregates, and DB latency to the public internet. Set via Secret
    Manager in Cloud Run; pass via the `X-Admin-Token` request header."""

    cf_access_team_domain: str | None = None
    """Cloudflare Access team domain, e.g. `anyplot.cloudflareaccess.com`.
    Used as the JWT issuer and for fetching JWKS keys at
    `https://{team_domain}/cdn-cgi/access/certs`. When unset, the JWT path in
    require_admin is skipped (token-only mode)."""

    cf_access_aud: str | None = None
    """Cloudflare Access Application AUD tag (UUID from the Zero Trust
    dashboard). Validated as the JWT `aud` claim."""

    admin_allowed_emails: Annotated[list[str], NoDecode] = []
    """Email addresses allowed to authenticate via Cloudflare Access for
    /debug/* endpoints. Defaults to an empty list — must be set explicitly
    in production. Accepts either a JSON array (`["a@b.com","c@d.com"]`)
    or a comma-separated string (`a@b.com,c@d.com`) when set via env var.
    `NoDecode` keeps pydantic-settings from JSON-parsing the env value
    before our field_validator runs (so a comma-separated string is OK)."""

    @field_validator("admin_allowed_emails", mode="before")
    @classmethod
    def _parse_admin_allowed_emails(cls, value: Any) -> Any:
        """Allow `ADMIN_ALLOWED_EMAILS=foo@bar.com,baz@qux.com` in addition to
        the JSON-array form pydantic-settings expects by default. A bare
        string with no commas is treated as a single-element list."""
        import json

        if isinstance(value, str):
            stripped = value.strip()
            if not stripped:
                return []
            if stripped.startswith("["):
                return json.loads(stripped)
            return [item.strip() for item in stripped.split(",") if item.strip()]
        return value

    # =============================================================================
    # CORS
    # =============================================================================

    cors_origins: list[str] = [
        "http://localhost:5173",
        "http://localhost:5174",
        "http://localhost:3000",
        "https://anyplot.ai",
        "https://www.anyplot.ai",
    ]
    """Allowed CORS origins"""

    # =============================================================================
    # HELPER METHODS
    # =============================================================================

    @property
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.environment.lower() == "production"

    @property
    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.environment.lower() == "development"

    @property
    def is_test(self) -> bool:
        """Check if running in test environment."""
        return self.environment.lower() == "test"

    @property
    def is_database_configured(self) -> bool:
        """
        Check if database configuration is present.

        Note: This only verifies config presence, not connectivity or validity.
        Use core.database.is_db_configured() for runtime checks.
        """
        return bool(self.database_url or self.instance_connection_name)

    @property
    def has_google_cloud(self) -> bool:
        """Check if Google Cloud is configured."""
        return bool(self.google_application_credentials or self.instance_connection_name)

    def resolve_model(self, cli: str, tier: str) -> str:
        """Resolve a model tier (small/medium/large) to the actual model name for a CLI.

        Args:
            cli: The CLI tool name ("claude", "copilot", or "gemini")
            tier: The model tier ("small", "medium", or "large")

        Returns:
            The actual model name for the specified CLI and tier.
            If the tier is not recognized, returns the tier unchanged (pass-through).
        """
        mapping = {
            "claude": {
                "small": self.cli_model_claude_small,
                "medium": self.cli_model_claude_medium,
                "large": self.cli_model_claude_large,
            },
            "copilot": {
                "small": self.cli_model_copilot_small,
                "medium": self.cli_model_copilot_medium,
                "large": self.cli_model_copilot_large,
            },
            "gemini": {
                "small": self.cli_model_gemini_small,
                "medium": self.cli_model_gemini_medium,
                "large": self.cli_model_gemini_large,
            },
        }
        return mapping.get(cli, {}).get(tier, tier)


# Global settings instance
# Import this from other modules: from core.config import settings
settings = Settings()
