"""The `anyplot` agent network: the root agent, the registry and the ADK `App`.

* `root_agent` ("anyplot") is the only agent that talks to the user. Its policy is the
  constant `static_instruction` (`policy.root_instruction`), never templated; the
  `InstructionProvider` `session_context` adds only server-validated values (spec,
  library, reply language, dataset and binding status, plot versions), which ADK sends
  as a marked instruction block after the static prefix. Its tools are the four
  session tools and the `plot_pipeline` NodeTool.
* The adapters (one per enabled library) and the reviewer run only inside the
  pipeline through `ctx.run_node`, so a walk from the root would miss them;
  `ALL_AGENTS` lists every agent for the registry test.
* `app` carries the plugins in their fixed order, `ScopeGuard → Budget → ToolSafety →
  ContextFilter(6)`, behind the development-only fixture seed when
  `AGENT_DEV_FIXTURE` is set, and, on Claude only, a context-cache config so ADK
  marks Claude prompt-cache breakpoints. `adk web agents` finds `app` in this module.
"""

from typing import Any

from google.adk import Agent
from google.adk.agents.context_cache_config import ContextCacheConfig
from google.adk.agents.readonly_context import ReadonlyContext
from google.adk.apps import App
from google.adk.plugins.base_plugin import BasePlugin
from google.adk.plugins.context_filter_plugin import ContextFilterPlugin

from .data.bindings import check_bindings
from .dev_fixture import DevFixturePlugin
from .models import make_content_config, make_model
from .plugins.budget import BudgetPlugin
from .plugins.scope_guard import ScopeGuardPlugin
from .plugins.tool_safety import ToolSafetyPlugin
from .policy import root_instruction
from .services import get_services
from .session_state import read_session
from .settings import get_settings
from .sub_agents.adapter import ADAPTERS
from .sub_agents.reviewer import reviewer
from .tools.session import SESSION_TOOLS, plot_pipeline


APP_NAME = "anyplot"
ROOT_NAME = "anyplot"

# ADK wraps a BaseNode in `tools` into its NodeTool when the agent is constructed
# (`LlmAgent._pre_validate_tools`, a model validator); its `ToolUnion` alias does not
# list BaseNode, so the list is typed loosely here.
ROOT_TOOLS: list[Any] = [*SESSION_TOOLS, plot_pipeline]
CONTEXT_INVOCATIONS = 6
CLAUDE_CACHE_TTL_S = 300


async def session_context(context: ReadonlyContext) -> str:
    """The server-validated session facts the root needs each turn; no user-written text."""
    view = read_session(context.state)
    if view is None:
        return (
            'Session: no plot is open. Tell the user to open "Use with my data" on a plot page, '
            "and answer nothing else."
        )
    services = get_services()
    session_id = context.session.id
    lines = [
        "Session (set by the server):",
        f"- Plot: {view.snapshot.title} (spec {view.spec_id}), library {view.library}",
        f"- Reply language: {view.locale}",
    ]
    dataset = services.datasets.get(view.dataset_id, session_id) if view.dataset_id else None
    if dataset is None:
        lines.append("- Dataset: none yet; the user pastes it in the data panel")
    else:
        profile = dataset.profile
        lines.append(f"- Dataset: {profile.rows} rows, {len(profile.columns)} columns")
        check = check_bindings(view.bindings, view.snapshot.roles(), profile)
        if check.complete:
            lines.append("- Bindings: complete")
        else:
            missing = ", ".join(check.missing_roles) or "none"
            lines.append(f"- Bindings: incomplete; missing roles: {missing}; {len(check.errors)} invalid")
    versions = [version for version in services.versions.all(session_id) if version.library == view.library]
    if versions:
        lines.append(f"- Plot versions: {len(versions)}; latest result: {versions[-1].result.status}")
    else:
        lines.append("- Plot versions: none yet")
    return "\n".join(lines)


root_agent = Agent(
    name=ROOT_NAME,
    description="The anyplot assistant for 'Use with my data': adapts one catalogue plot to the user's data.",
    model=make_model("root"),
    generate_content_config=make_content_config("root"),
    static_instruction=root_instruction(),
    instruction=session_context,
    tools=ROOT_TOOLS,
)

ALL_AGENTS: list[Agent] = [root_agent, *ADAPTERS.values(), reviewer]


def build_plugins() -> list[BasePlugin]:
    """The plugins in their fixed order, behind the fixture seed in development."""
    plugins: list[BasePlugin] = [
        ScopeGuardPlugin(),
        BudgetPlugin(),
        ToolSafetyPlugin(),
        ContextFilterPlugin(num_invocations_to_keep=CONTEXT_INVOCATIONS),
    ]
    settings = get_settings()
    if settings.dev_fixture and settings.is_development:
        plugins.insert(0, DevFixturePlugin(settings.dev_fixture))
    return plugins


def build_context_cache() -> ContextCacheConfig | None:
    """Prompt-cache breakpoints for Claude; none for Gemini.

    Without an App-level config ADK sends Claude no `cache_control`
    (`models/_prompt_cache.py`), so every adapter call would pay the full ~42K
    characters of its static instruction. With one, ADK marks the tools, the system
    instruction and the end of the conversation. Gemini keeps its implicit cache:
    there the same config would make ADK create explicit caches, a billed resource.
    The 5-minute lifetime is Claude's cheaper write; it covers the repair attempt and
    the next turn.
    """
    if get_settings().provider != "anthropic-vertex":
        return None
    return ContextCacheConfig(ttl_seconds=CLAUDE_CACHE_TTL_S)


app = App(name=APP_NAME, root_agent=root_agent, plugins=build_plugins(), context_cache_config=build_context_cache())
