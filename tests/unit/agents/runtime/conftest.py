"""Shared fixtures: a hermetic development environment, fake services and scripted agent models."""

import inspect
import logging
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

_FRAME_HELPERS = (inspect.currentframe, logging.currentframe)
"""The two standard-library helpers as they are when the tests are collected, before any test ran."""


@pytest.fixture(autouse=True)
def stdlib_frame_helpers() -> Iterator[None]:
    """Put `inspect.currentframe` and `logging.currentframe` back after every test.

    A harness step that runs in this process (`main_data`, `main_convert`, a plot run) replaces both with helpers
    that answer None, and has no way back: in the sandbox the process ends with the step. In a test worker the
    next test would inherit them, and a library that walks frames fails there: plotnine looks for the plot's
    namespace that way and raises "call-stack is not that deep!". Which test meets it depends on the order the
    workers happen to take, so it shows as a failure that comes and goes.
    """
    yield
    inspect.currentframe, logging.currentframe = _FRAME_HELPERS


@pytest.fixture(autouse=True)
def development_env(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    """ENVIRONMENT=development and no AGENT_* overrides (CI sets ENVIRONMENT=test for the whole job)."""
    for name in list(os.environ):
        if name.upper().startswith("AGENT_") or name.upper() in ("GOOGLE_CLOUD_PROJECT", "K_SERVICE"):
            monkeypatch.delenv(name)
    monkeypatch.setenv("ENVIRONMENT", "development")
    # These flow tests script the checklist reviewer's `Verdict` and count attempts without a
    # self-review; the live catalogue flow (the defaults) has its own tests in test_catalogue_flow.py.
    for name, value in CHECKLIST_FLOW.items():
        monkeypatch.setenv(name, value)
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


CHECKLIST_FLOW = {
    "AGENT_REVIEWER_MODE": "checklist",
    "AGENT_SELF_REVIEW": "false",
    "AGENT_SHIP_BEST": "false",
    "AGENT_SOFT_DEADLINE_S": "140",
    "AGENT_REQUEST_DEADLINE_S": "180",
    "AGENT_ROOT_EFFORT": "low",
    "AGENT_ADAPTER_EFFORT": "medium",
    "AGENT_REVIEWER_EFFORT": "low",
    "AGENT_REVIEWER_THINKING_BUDGET": "0",
    "AGENT_CHECK_RETRY": "false",
}
"""The flow before 2026-10-13, which most runtime tests script, with the deadlines their timing fakes fit
and the efforts their request assertions expect."""


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
