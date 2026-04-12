"""
Tests for Settings.resolve_model method.

Tests model tier resolution for different CLIs.
"""

from unittest.mock import patch

import pytest

from core.config import Settings


class TestResolveModel:
    """Tests for Settings.resolve_model."""

    @pytest.fixture
    def settings(self) -> Settings:
        """Create a Settings instance with default model mappings."""
        with patch.dict("os.environ", {}, clear=False):
            return Settings(
                cli_model_claude_small="claude-haiku",
                cli_model_claude_medium="claude-sonnet",
                cli_model_claude_large="claude-opus",
                cli_model_copilot_small="gpt-4o-mini",
                cli_model_copilot_medium="gpt-4o",
                cli_model_copilot_large="o1",
                cli_model_gemini_small="gemini-flash",
                cli_model_gemini_medium="gemini-pro",
                cli_model_gemini_large="gemini-ultra",
            )

    def test_claude_small(self, settings: Settings) -> None:
        assert settings.resolve_model("claude", "small") == "claude-haiku"

    def test_claude_medium(self, settings: Settings) -> None:
        assert settings.resolve_model("claude", "medium") == "claude-sonnet"

    def test_claude_large(self, settings: Settings) -> None:
        assert settings.resolve_model("claude", "large") == "claude-opus"

    def test_copilot_small(self, settings: Settings) -> None:
        assert settings.resolve_model("copilot", "small") == "gpt-4o-mini"

    def test_copilot_large(self, settings: Settings) -> None:
        assert settings.resolve_model("copilot", "large") == "o1"

    def test_gemini_medium(self, settings: Settings) -> None:
        assert settings.resolve_model("gemini", "medium") == "gemini-pro"

    def test_unknown_cli_returns_tier(self) -> None:
        """Unknown CLI should return the tier unchanged (pass-through)."""
        with patch.dict("os.environ", {}, clear=False):
            s = Settings()
            assert s.resolve_model("unknown-cli", "small") == "small"

    def test_unknown_tier_returns_tier(self) -> None:
        """Unknown tier should return the tier unchanged (pass-through)."""
        with patch.dict("os.environ", {}, clear=False):
            s = Settings()
            assert s.resolve_model("claude", "xlarge") == "xlarge"

    def test_unknown_cli_and_tier(self) -> None:
        with patch.dict("os.environ", {}, clear=False):
            s = Settings()
            assert s.resolve_model("unknown", "unknown") == "unknown"

    def test_exact_model_name_passthrough(self) -> None:
        """When tier is an exact model name, it's returned as-is."""
        with patch.dict("os.environ", {}, clear=False):
            s = Settings()
            result = s.resolve_model("claude", "claude-3-opus-20240229")
            assert result == "claude-3-opus-20240229"
