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
        if name.upper().startswith("AGENT_") or name.upper() in ("ENVIRONMENT", "GOOGLE_CLOUD_PROJECT", "K_SERVICE"):
            monkeypatch.delenv(name)
    get_settings.cache_clear()


class TestDefaults:
    def test_defaults_are_the_pinned_production_values(self) -> None:
        settings = AgentSettings()

        assert settings.provider == "anthropic-vertex"
        assert settings.model == "claude-haiku-5-5"
        assert settings.judge_model == "claude-haiku-5-5"
        assert settings.location == "eu"
        assert settings.project == "anyplot"
        assert settings.judge_timeout_s == 4.0
        assert settings.render_concurrency == 2
        assert settings.service_urls == []
        assert settings.dev_fixture is None
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
        assert settings.environment == "production"  # unset never skips the caller check
        assert settings.is_development is False

    def test_development_is_refused_on_cloud_run(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("ENVIRONMENT", "development")
        monkeypatch.setenv("K_SERVICE", "anyplot-agents")

        with pytest.raises(ValidationError, match="refused on Cloud Run"):
            AgentSettings()

    @pytest.mark.parametrize("model", ["claude-opus-5-5", "claude-sonnet-5-5", "claude-fable-5-1"])
    def test_claude_models_without_forced_tool_use_are_refused(self, model: str) -> None:
        with pytest.raises(ValidationError, match="not a supported Claude model"):
            AgentSettings(model=model)

    def test_get_settings_is_cached(self) -> None:
        assert get_settings() is get_settings()


class TestEnvironmentOverrides:
    def test_agent_prefixed_variables_override_the_defaults(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("AGENT_PROVIDER", "gemini")
        monkeypatch.setenv("AGENT_MODEL", "gemini-3.9-flash")
        monkeypatch.setenv("AGENT_JUDGE_MODEL", "gemini-3.6-flash-lite")
        monkeypatch.setenv("AGENT_LOCATION", "global")
        monkeypatch.setenv("ENVIRONMENT", "development")  # the fake renderer is refused in production
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
        monkeypatch.setenv("AGENT_LIBRARIES", "seaborn, matplotlib")
        monkeypatch.setenv("AGENT_ALLOWED_CALLERS", "api@anyplot.iam.gserviceaccount.com")

        settings = AgentSettings()

        assert settings.libraries == ["seaborn", "matplotlib"]
        assert settings.allowed_callers == ["api@anyplot.iam.gserviceaccount.com"]

    def test_list_settings_accept_a_json_array(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("AGENT_LIBRARIES", '["seaborn"]')

        assert AgentSettings().libraries == ["seaborn"]

    def test_environment_is_read_without_the_prefix(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("ENVIRONMENT", "Production")
        monkeypatch.setenv("AGENT_ENVIRONMENT", "development")

        assert AgentSettings().environment == "production"

    def test_project_falls_back_to_google_cloud_project(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("GOOGLE_CLOUD_PROJECT", "sandbox-project")

        assert AgentSettings().project == "sandbox-project"

    def test_agent_project_wins_over_google_cloud_project(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("GOOGLE_CLOUD_PROJECT", "sandbox-project")
        monkeypatch.setenv("AGENT_PROJECT", "anyplot-eval")

        assert AgentSettings().project == "anyplot-eval"

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


class TestProviderValidator:
    def test_gemini_provider_with_gemini_models(self) -> None:
        settings = AgentSettings(provider="gemini", model="gemini-3.8-flash", judge_model="gemini-3.5-flash-lite")

        assert (settings.provider, settings.model, settings.judge_model) == (
            "gemini",
            "gemini-3.8-flash",
            "gemini-3.5-flash-lite",
        )

    @pytest.mark.parametrize(
        ("provider", "field", "model"),
        [
            ("gemini", "model", "claude-haiku-5-5"),
            ("anthropic-vertex", "model", "gemini-3.8-flash"),
            ("anthropic-vertex", "judge_model", "gemini-3.5-flash-lite"),
        ],
    )
    def test_model_must_match_the_provider(self, provider: str, field: str, model: str) -> None:
        with pytest.raises(ValidationError, match="does not match AGENT_PROVIDER"):
            AgentSettings(**{"provider": provider, field: model})

    def test_switching_the_provider_alone_is_refused(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """The defaults are Claude ids, so AGENT_PROVIDER=gemini needs AGENT_MODEL and AGENT_JUDGE_MODEL too."""
        monkeypatch.setenv("AGENT_PROVIDER", "gemini")

        with pytest.raises(ValidationError, match="AGENT_MODEL='claude-haiku-5-5'"):
            AgentSettings()

    def test_unknown_provider_is_refused(self) -> None:
        with pytest.raises(ValidationError):
            AgentSettings(provider="openai")


class TestDevFixture:
    def test_fixture_is_allowed_in_development(self) -> None:
        settings = AgentSettings(dev_fixture="scatter-basic-matplotlib", environment="development")
        assert settings.dev_fixture == "scatter-basic-matplotlib"

    def test_fixture_is_refused_when_environment_is_unset(self) -> None:
        with pytest.raises(ValidationError, match="AGENT_DEV_FIXTURE"):
            AgentSettings(dev_fixture="scatter-basic-matplotlib")

    def test_blank_fixture_is_unset(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("AGENT_DEV_FIXTURE", " ")

        assert AgentSettings().dev_fixture is None

    @pytest.mark.parametrize("environment", ["production", "test"])
    def test_fixture_is_refused_outside_development(self, environment: str) -> None:
        with pytest.raises(ValidationError, match="AGENT_DEV_FIXTURE"):
            AgentSettings(dev_fixture="scatter-basic-matplotlib", environment=environment)

    @pytest.mark.parametrize("case", ["../etc", "Scatter", "a/b", "-x"])
    def test_fixture_id_must_be_a_slug(self, case: str) -> None:
        with pytest.raises(ValidationError):
            AgentSettings(dev_fixture=case)


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

    @pytest.mark.parametrize("environment", ["development", "test"])
    def test_fake_renderer_is_allowed_in_development_and_test(self, environment: str) -> None:
        assert AgentSettings(renderer="fake", environment=environment).renderer == "fake"

    @pytest.mark.parametrize("environment", ["production", "staging"])
    def test_fake_renderer_is_refused_elsewhere(self, environment: str) -> None:
        """The fake backend runs no code, so a production misconfiguration would ship fixture plots."""
        with pytest.raises(ValidationError, match="AGENT_RENDERER=fake"):
            AgentSettings(renderer="fake", environment=environment)

    def test_unknown_renderer_is_refused(self) -> None:
        with pytest.raises(ValidationError):
            AgentSettings(renderer="subprocess")


class TestOtherValidators:
    def test_unknown_library_is_refused(self) -> None:
        with pytest.raises(ValidationError, match="unknown libraries"):
            AgentSettings(libraries=["matplotlib", "excel"])

    def test_library_without_a_runtime_is_refused(self) -> None:
        """A catalogue library without a phase-1 runtime must not be reported as enabled."""
        with pytest.raises(ValidationError, match="no runtime"):
            AgentSettings(libraries=["matplotlib", "plotly"])

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
