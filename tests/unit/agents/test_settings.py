"""Tests for agents/anyplot/settings.py."""

import os

import pytest
from pydantic import ValidationError

from agents.anyplot.settings import AgentSettings, get_settings


@pytest.fixture(autouse=True)
def clean_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Start every test from an environment without agent settings.

    CI sets ENVIRONMENT=test for the whole job, and a developer shell may export
    AGENT_* values; neither may leak into the default assertions.
    """
    for name in list(os.environ):
        if name.upper().startswith("AGENT_") or name.upper() == "ENVIRONMENT":
            monkeypatch.delenv(name)
    get_settings.cache_clear()


class TestDefaults:
    def test_defaults_are_the_pinned_production_values(self) -> None:
        settings = AgentSettings()

        assert settings.model == "gemini-3.8-flash"
        assert settings.judge_model == "gemini-3.5-flash-lite"
        assert settings.location == "eu"
        assert settings.libraries == ["matplotlib", "seaborn"]
        assert settings.renderer == "sandbox"
        assert settings.max_llm_calls == 12
        assert settings.request_token_budget == 80_000
        assert settings.daily_token_budget == 1_000_000
        assert settings.daily_pipeline_runs == 40
        assert settings.global_daily_token_budget == 3_000_000
        assert settings.render_timeout_s == 60
        assert settings.request_deadline_s == 180
        assert settings.soft_deadline_s == 140
        assert settings.allowed_callers == []
        assert settings.environment == "development"

    def test_get_settings_is_cached(self) -> None:
        assert get_settings() is get_settings()


class TestEnvironmentOverrides:
    def test_agent_prefixed_variables_override_the_defaults(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("AGENT_MODEL", "gemini-3.9-flash")
        monkeypatch.setenv("AGENT_JUDGE_MODEL", "gemini-3.6-flash-lite")
        monkeypatch.setenv("AGENT_LOCATION", "global")
        monkeypatch.setenv("AGENT_RENDERER", "fake")
        monkeypatch.setenv("AGENT_MAX_LLM_CALLS", "7")
        monkeypatch.setenv("AGENT_SOFT_DEADLINE_S", "120")

        settings = AgentSettings()

        assert settings.model == "gemini-3.9-flash"
        assert settings.judge_model == "gemini-3.6-flash-lite"
        assert settings.location == "global"
        assert settings.renderer == "fake"
        assert settings.max_llm_calls == 7
        assert settings.soft_deadline_s == 120

    def test_list_settings_accept_comma_separated_values(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("AGENT_LIBRARIES", "matplotlib, seaborn,plotly")
        monkeypatch.setenv("AGENT_ALLOWED_CALLERS", "api@anyplot.iam.gserviceaccount.com")

        settings = AgentSettings()

        assert settings.libraries == ["matplotlib", "seaborn", "plotly"]
        assert settings.allowed_callers == ["api@anyplot.iam.gserviceaccount.com"]

    def test_list_settings_accept_a_json_array(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("AGENT_LIBRARIES", '["seaborn"]')

        assert AgentSettings().libraries == ["seaborn"]

    def test_environment_is_read_without_the_prefix(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("ENVIRONMENT", "Production")
        monkeypatch.setenv("AGENT_ENVIRONMENT", "development")

        assert AgentSettings().environment == "production"

    def test_duplicate_libraries_are_dropped_in_order(self) -> None:
        assert AgentSettings(libraries=["seaborn", "matplotlib", "seaborn"]).libraries == ["seaborn", "matplotlib"]


class TestLocationValidator:
    @pytest.mark.parametrize("location", ["eu", "us", "global", " EU "])
    def test_multi_regions_are_accepted(self, location: str) -> None:
        assert AgentSettings(location=location).location == location.strip().lower()

    @pytest.mark.parametrize("location", ["europe-west4", "us-central1", "europe", ""])
    def test_regional_or_unknown_locations_are_refused(self, location: str) -> None:
        with pytest.raises(ValidationError, match="must be eu, us or global"):
            AgentSettings(location=location)

    def test_regional_location_from_the_environment_is_refused(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("AGENT_LOCATION", "europe-west4")

        with pytest.raises(ValidationError, match="europe-west4"):
            AgentSettings()


class TestModelValidator:
    @pytest.mark.parametrize("field", ["model", "judge_model"])
    @pytest.mark.parametrize("alias", ["gemini-flash-latest", "gemini-flash-lite-latest", "latest"])
    def test_latest_aliases_are_refused(self, field: str, alias: str) -> None:
        with pytest.raises(ValidationError, match="floating alias"):
            AgentSettings(**{field: alias})

    def test_alias_from_the_environment_is_refused(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("AGENT_MODEL", "gemini-flash-latest")

        with pytest.raises(ValidationError, match="floating alias"):
            AgentSettings()

    @pytest.mark.parametrize("field", ["model", "judge_model"])
    def test_empty_model_id_is_refused(self, field: str) -> None:
        with pytest.raises(ValidationError, match="model id is required"):
            AgentSettings(**{field: "  "})


class TestRendererValidator:
    def test_local_renderer_is_allowed_in_development(self) -> None:
        assert AgentSettings(renderer="local", environment="development").renderer == "local"

    @pytest.mark.parametrize("environment", ["production", "staging", "test"])
    def test_local_renderer_is_refused_outside_development(self, environment: str) -> None:
        with pytest.raises(ValidationError, match="AGENT_RENDERER=local"):
            AgentSettings(renderer="local", environment=environment)

    def test_local_renderer_with_production_environment_variables_is_refused(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("ENVIRONMENT", "production")
        monkeypatch.setenv("AGENT_RENDERER", "local")

        with pytest.raises(ValidationError, match="AGENT_RENDERER=local"):
            AgentSettings()

    @pytest.mark.parametrize("renderer", ["sandbox", "remote"])
    def test_production_renderers_are_allowed_in_production(self, renderer: str) -> None:
        assert AgentSettings(renderer=renderer, environment="production").renderer == renderer

    def test_unknown_renderer_is_refused(self) -> None:
        with pytest.raises(ValidationError):
            AgentSettings(renderer="subprocess")


class TestOtherValidators:
    def test_unknown_library_is_refused(self) -> None:
        with pytest.raises(ValidationError, match="unknown libraries"):
            AgentSettings(libraries=["matplotlib", "excel"])

    def test_empty_library_list_is_refused(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("AGENT_LIBRARIES", "")

        with pytest.raises(ValidationError):
            AgentSettings()

    def test_soft_deadline_must_be_below_the_request_deadline(self) -> None:
        with pytest.raises(ValidationError, match="AGENT_SOFT_DEADLINE_S"):
            AgentSettings(soft_deadline_s=180, request_deadline_s=180)

    @pytest.mark.parametrize("field", ["max_llm_calls", "request_token_budget", "render_timeout_s"])
    def test_limits_must_be_positive(self, field: str) -> None:
        with pytest.raises(ValidationError):
            AgentSettings(**{field: 0})
