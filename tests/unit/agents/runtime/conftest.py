"""Shared fixtures: a hermetic development environment, fake services and scripted agent models."""

import os
from collections.abc import Iterator
from pathlib import Path

import pytest

from agents.anyplot.agent import ALL_AGENTS
from agents.anyplot.models import FakeJudge, make_content_config, make_model
from agents.anyplot.render.backends.fake import FakeBackend
from agents.anyplot.services import Services, set_services
from agents.anyplot.settings import AgentSettings, get_settings

from .fakes import FakeAnthropic, ScriptedLlm


REPO_ROOT = Path(__file__).resolve().parents[4]
CASES = REPO_ROOT / "agents" / "evals" / "fixtures" / "cases"


@pytest.fixture(autouse=True)
def development_env(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    """ENVIRONMENT=development and no AGENT_* overrides (CI sets ENVIRONMENT=test for the whole job)."""
    for name in list(os.environ):
        if name.upper().startswith("AGENT_") or name.upper() in ("GOOGLE_CLOUD_PROJECT", "K_SERVICE"):
            monkeypatch.delenv(name)
    monkeypatch.setenv("ENVIRONMENT", "development")
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


@pytest.fixture
def backend() -> FakeBackend:
    return FakeBackend()


@pytest.fixture
def judge() -> FakeJudge:
    return FakeJudge()


@pytest.fixture
def services(backend: FakeBackend, judge: FakeJudge) -> Iterator[Services]:
    current = Services(backend_factory=lambda: backend, judge_factory=lambda: judge)
    set_services(current)
    yield current
    set_services(None)


def _kind(name: str) -> str:
    return "root" if name == "anyplot" else "reviewer" if name == "reviewer" else "adapter"


@pytest.fixture
def swap_models() -> Iterator[object]:
    """Replace every agent's model (and config) for one test; restore them afterwards."""
    saved = [(agent, agent.model, agent.generate_content_config) for agent in ALL_AGENTS]

    def apply(provider: str, script: dict[str, list]) -> object:
        if provider == "gemini":
            settings = AgentSettings(provider="gemini", model="gemini-3.8-flash", judge_model="gemini-3.5-flash-lite")
            fake: object = ScriptedLlm(script=script)
            for agent in ALL_AGENTS:
                agent.model = fake
                agent.generate_content_config = make_content_config(_kind(agent.name), settings)
            return fake
        settings = AgentSettings()
        client = FakeAnthropic(script)
        for agent in ALL_AGENTS:
            model = make_model(_kind(agent.name), settings)
            model.__dict__["_anthropic_client"] = client
            agent.model = model
            agent.generate_content_config = make_content_config(_kind(agent.name), settings)
        return client

    yield apply
    for agent, model, config in saved:
        agent.model = model
        agent.generate_content_config = config
