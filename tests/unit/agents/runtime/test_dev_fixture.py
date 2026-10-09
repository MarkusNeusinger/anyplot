"""The development fixture seed and ADK's loader finding the app (what `adk web agents` does)."""

from pathlib import Path

import pytest
from google.adk.apps import App
from google.adk.sessions import InMemorySessionService

from agents.anyplot.data.bindings import check_bindings
from agents.anyplot.dev_fixture import DevFixturePlugin, FixtureError, load_case, seed_delta, snapshot_from_repo
from agents.anyplot.services import Services
from agents.anyplot.session_state import BINDINGS, DATASET_ID, SPEC_ID, read_session
from agents.anyplot.settings import AgentSettings


AGENTS_DIR = Path(__file__).resolve().parents[4] / "agents"


@pytest.mark.parametrize(
    ("case_id", "spec_id", "library"),
    [("scatter-basic-matplotlib", "scatter-basic", "matplotlib"), ("bar-grouped-seaborn", "bar-grouped", "seaborn")],
)
def test_cases_load_and_seed_eligible_sessions(case_id: str, spec_id: str, library: str, services: Services) -> None:
    case = load_case(case_id)
    delta = seed_delta(case, "s1", AgentSettings())

    assert (case.spec_id, case.library) == (spec_id, library)
    assert delta[SPEC_ID] == spec_id and delta[DATASET_ID]
    view = read_session(delta)
    stored = services.datasets.get(delta[DATASET_ID], "s1")
    assert view is not None and stored is not None
    assert check_bindings(view.bindings, view.snapshot.roles(), stored.profile).complete
    assert delta[BINDINGS] == [binding.model_dump() for binding in case.bindings]


def test_snapshot_from_repo_matches_the_catalogue_shape() -> None:
    snapshot = snapshot_from_repo("bar-grouped", "seaborn")

    assert snapshot.title == "Grouped Bar Chart"
    assert snapshot.library_version == "0.13.2"
    assert snapshot.data_roles[0].startswith("`category` (categorical)")
    assert "# noqa" not in snapshot.code


@pytest.mark.parametrize("case_id", ["../../etc", "missing-case"])
def test_unknown_or_unsafe_case_is_refused(case_id: str) -> None:
    with pytest.raises(FixtureError):
        load_case(case_id)


def test_plugin_refuses_outside_development(monkeypatch: pytest.MonkeyPatch) -> None:
    from agents.anyplot.settings import get_settings

    monkeypatch.setenv("ENVIRONMENT", "production")
    get_settings.cache_clear()
    with pytest.raises(FixtureError):
        DevFixturePlugin("scatter-basic-matplotlib")


async def test_plugin_seeds_a_new_session_once(services: Services) -> None:
    from types import SimpleNamespace

    from google.genai import types

    sessions = InMemorySessionService()
    session = await sessions.create_session(app_name="anyplot", user_id="u", session_id="s9")
    plugin = DevFixturePlugin("scatter-basic-matplotlib")
    context = SimpleNamespace(session=session, session_service=sessions, invocation_id="inv")
    message = types.Content(role="user", parts=[types.Part(text="Create the plot")])

    assert await plugin.on_user_message_callback(invocation_context=context, user_message=message) is None
    stored = await sessions.get_session(app_name="anyplot", user_id="u", session_id="s9")
    assert stored.state[SPEC_ID] == "scatter-basic"
    events = len(stored.events)
    await plugin.on_user_message_callback(
        invocation_context=SimpleNamespace(**{**vars(context), "session": stored}), user_message=message
    )
    again = await sessions.get_session(app_name="anyplot", user_id="u", session_id="s9")
    assert len(again.events) == events


def test_adk_loader_finds_the_app_with_its_plugins(monkeypatch: pytest.MonkeyPatch) -> None:
    """What `adk web agents` does: list the agents directory and load `anyplot` as a top-level package."""
    from google.adk.cli.utils.agent_loader import AgentLoader

    # ADK walks up from the agent directory looking for a .env; never load one in tests.
    monkeypatch.setenv("ADK_DISABLE_LOAD_DOTENV", "1")
    monkeypatch.setenv("AGENT_DEV_FIXTURE", "scatter-basic-matplotlib")
    monkeypatch.setenv("AGENT_RENDERER", "fake")
    from agents.anyplot.settings import get_settings

    get_settings.cache_clear()
    monkeypatch.chdir(AGENTS_DIR.parent)
    loader = AgentLoader(str(AGENTS_DIR))

    assert loader.list_agents() == ["anyplot"]
    loaded = loader.load_agent("anyplot")

    assert isinstance(loaded, App)
    assert loaded.name == "anyplot" and loaded.root_agent.name == "anyplot"
    assert [type(plugin).__name__ for plugin in loaded.plugins] == [
        "DevFixturePlugin",
        "ScopeGuardPlugin",
        "BudgetPlugin",
        "ToolSafetyPlugin",
        "ContextFilterPlugin",
    ]
