"""The ADK pin: exact version, the 2.x entry points, and no `agents` module shadowing this package.

ADK ships weekly and its feature flags drift between releases, so the design pins
it exactly (docs/concepts/agent-network.md, "Risks and mitigations"). An upgrade is
a deliberate PR that changes pyproject.toml and the version below together.
"""

import importlib.metadata
import tomllib
from pathlib import Path

import pytest

import agents


ADK_VERSION = "2.11.0"
REPO_ROOT = Path(__file__).resolve().parents[3]


def _installed(distribution: str) -> str | None:
    try:
        return importlib.metadata.version(distribution)
    except importlib.metadata.PackageNotFoundError:
        return None


requires_adk = pytest.mark.skipif(
    _installed("google-adk") is None, reason="google-adk is not installed (uv sync --extra agents)"
)


def test_pyproject_pins_adk_exactly() -> None:
    extras = tomllib.loads((REPO_ROOT / "pyproject.toml").read_text())["project"]["optional-dependencies"]

    assert extras["agents"][0] == f"google-adk=={ADK_VERSION}"
    assert extras["agents-eval"][0] == f"google-adk[eval]=={ADK_VERSION}"


def test_agents_extra_carries_the_claude_backend() -> None:
    """ADK's `anthropic_llm` imports `AsyncAnthropicVertex`; its credentials need the `vertex` extra."""
    extras = tomllib.loads((REPO_ROOT / "pyproject.toml").read_text())["project"]["optional-dependencies"]

    for extra in ("agents", "agents-eval"):
        assert any(requirement.startswith("anthropic[vertex]") for requirement in extras[extra])
        assert not any(requirement.startswith("openai-agents") for requirement in extras[extra])


def test_lock_has_no_openai_agents() -> None:
    """`openai-agents` installs a top-level `agents` module that would shadow this package."""
    assert 'name = "openai-agents"' not in (REPO_ROOT / "uv.lock").read_text()


def test_agents_resolves_to_this_repository() -> None:
    assert Path(agents.__file__).resolve().parent == REPO_ROOT / "agents"


@requires_adk
def test_installed_adk_is_the_pinned_version() -> None:
    assert _installed("google-adk") == ADK_VERSION


@requires_adk
def test_adk_2x_entry_points_import() -> None:
    from google.adk import Agent, Context, Event, Workflow

    assert all(isinstance(cls, type) for cls in (Agent, Context, Event, Workflow))
