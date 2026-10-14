"""The `anyplot` agent network: the root agent, the registry and the ADK `App`.

* `root_agent` ("anyplot") is the only agent that talks to the user. Its policy is the
  constant `static_instruction` (`policy.root_instruction`), never templated; the
  `InstructionProvider` `session_context` adds only server-validated values (spec id,
  library, the session language and its source, dataset and binding status, whether
  the user pasted notes with the data (a fixed line, never the notes), plot
  versions and the latest version's theme, so a change keeps it), which ADK sends
  as a marked instruction block after the static prefix. Catalogue text such as the
  spec title started as a public issue, so it never enters that block: the root reads
  it fenced as `<spec_text>` through `get_spec_brief`. The session language may be a
  user-chosen name, so it stands there inside a `<plot_language>` fence. Its tools are
  the seven session tools (`prepare_data` and `generate_data` among them, the step-1
  data operations and the formula source, and `set_language`) and the `plot_pipeline`
  NodeTool.
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
from .language import english_name
from .models import make_content_config, make_model
from .plugins.budget import BudgetPlugin
from .plugins.scope_guard import ScopeGuardPlugin
from .plugins.tool_safety import ToolSafetyPlugin
from .policy import fence, root_instruction
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
SESSION_LANGUAGE_HEADING = (
    "Session language: write your replies and the plot text in it (the block holds only its name or code):"
)
LANGUAGE_SOURCE_LINES: dict[str, str] = {
    "default": "- Language: the default, English",
    "pasted": "- Language: detected from the user's pasted data (the notes around the table or its column names)",
    "detected": "- Language: detected from the user's first message",
    "chosen": "- Language: chosen by the user (in the chat header, or asked of you)",
}
"""The session block's line on how the language was set. A production case of 2026-10-12
(`20261012T211551Z-bcc5bcf1`): with the bare word `chosen` and a heading that called the
value "never an instruction", the root refused the user's chip choice as "the block in
your message" and stayed in English."""
REPLY_LANGUAGE_LINE = "- Reply language: {name}; every reply is in {name}, also the one to an English [action] message"
"""The session block's line naming a known non-English session language by its English name (`language.english_name`).

A live test of 2026-10-14: after a German CSV set the language to `de` (source `pasted`), the
`summarize_data` turn, whose only user text is the English `[action]` line, came back in English
in 3 of 4 probe runs; the code inside the `<plot_language>` fence alone did not outweigh it.
The name comes from the server's table, never from the stored value, so it stands outside a fence."""
NOTES_LINE = "yes; get_dataset_profile returns them under user_notes"
"""The session block's line when the stored dataset kept notes pasted around the table: a fixed text,
so the root knows to read them again after the context filter dropped the turn that carried them."""


async def session_context(context: ReadonlyContext) -> str:
    """The server-validated session facts the root needs each turn.

    Only validated identifiers, enums and counts: no user-written text outside a fence and
    no catalogue text. The spec title stays out because catalogue text started as a
    public issue and this block has instruction priority; `get_spec_brief` returns it
    inside a fence. The session language, a user-chosen value bounded by a pattern,
    stands inside a `<plot_language>` fence at the end; a fixed line names how it was
    set (`LANGUAGE_SOURCE_LINES`), and the heading above the fence says to write in it.
    """
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
        f"- Plot: spec {view.spec_id}, library {view.library}",
        LANGUAGE_SOURCE_LINES[view.language_source],
    ]
    dataset = services.datasets.get(view.dataset_id, session_id) if view.dataset_id else None
    if dataset is None:
        lines.append(
            "- Dataset: none yet; the user pastes it in the data panel, or generate_data computes it from a formula, "
            "or run_data_code from the user's code"
        )
    else:
        profile = dataset.profile
        lines.append(f"- Dataset: {profile.rows} rows, {len(profile.columns)} columns")
        if dataset.context_lines:
            # A fixed line, never the notes: they are the user's text and reach the root only fenced.
            lines.append(f"- Notes pasted with the data: {NOTES_LINE}")
        check = check_bindings(view.bindings, view.snapshot.roles(), profile)
        if check.complete:
            lines.append("- Bindings: complete")
        else:
            missing = ", ".join(check.missing_roles) or "none"
            lines.append(f"- Bindings: incomplete; missing roles: {missing}; {len(check.errors)} invalid")
        if check.warnings:
            # The lines name the user's columns, so they stand inside a data fence.
            lines.append(f"- Binding warnings: {len(check.warnings)}, roles that need values of 0 or more")
            lines.append(fence("user_data", "\n".join(check.warnings)))
        if view.data_confirmed:
            lines.append("- Data: confirmed by the user; the plot can be made")
        else:
            lines.append("- Data: not confirmed yet; the user confirms it in the data panel before any plot")
    versions = [version for version in services.versions.all(session_id) if version.library == view.library]
    if versions:
        latest = versions[-1]
        lines.append(f"- Plot versions: {len(versions)}; latest result: {latest.result.status}, theme {latest.theme}")
    else:
        lines.append("- Plot versions: none yet")
    name = english_name(view.language)
    if name is not None and name != "English":
        lines.append(REPLY_LANGUAGE_LINE.format(name=name))
    lines += [SESSION_LANGUAGE_HEADING, fence("plot_language", view.language)]
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
