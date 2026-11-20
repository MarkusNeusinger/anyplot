"""ReplacedTable: on the summary turn of a paste that replaced data, the root's request keeps the discussion and loses
the replaced table's facts.

Production, 2026-11-19 and 2026-11-20, three runs of three: a session held a table whose `day` column held dates and
the root's summary of it; the visitor pasted a table whose `day` held text, with the note "Convert the column day to
dates." The root answered with one model call and no tool that the column already held dates, naming the first table's
range. The session block of that turn carried the new table's profile and said that nothing said before described it
(`agent.REPLACED_DATA_LINE`), but the request still held the first table's `get_dataset_profile` result and the root's
summary of it, and the root answered from those.

On every model call of such a turn (`replacing_summary_turn`: a paste's summary turn, the condition the session block
uses, and `dataset_versions.replaced_earlier_data`), `before_model_callback` rewrites the root's request
(`without_replaced_table`):

* Everything before the current user turn loses the exchanges of the tools that read or change the table, or describe
  a plot drawn from it (`TABLE_TOOLS`): each such call goes, and so does its answer, both by the tool's name, so a call
  never stays without its answer nor an answer without its call, whatever ids the provider gave them. The root's
  thinking there goes too: it is the root's reading of the replaced table, never part of what the user saw, and with
  its call gone it would stand as a step without its act.
* Every user message and every text reply of the root stay: what the visitor wanted, what did not fit and why, and
  what the root offered. A visitor who changed the table and says "try again" is understood. The other tools' exchanges
  stay as well (`DISCUSSION_TOOLS`): they carry the visitor's decisions, never a fact of the table.
* The current user turn starts with `REPLACED_TABLE_LINE`, inside its first text part: the root's earlier replies
  still name the replaced table's values, and the line marks where the switch happened. Its own part would make the
  user's text read as another agent's relayed message to the reply check (`number_provenance._relayed`), whose test
  is a second text part that starts with a bracketed name, as the summary action's `[action]` line does.
* The current turn's own calls and answers stay as they are, so the next call of the turn sees what the root read and
  changed.

Only the request changes, as `scope_guard.without_refused_turns` changes it: the session's stored events, the user turn
the scope judge read and the judge's context of later turns stay as they were, and the next turn's request holds the
earlier exchanges again, unmarked. The plugin runs after ADK's `ContextFilterPlugin` and edits the same request object
in place, which `ledger.root_request` keeps: the reply checks' second asks and the number-provenance sources read the
filtered contents. A failure inside it leaves the request as it was and logs the error's class only.
"""

import logging
from collections.abc import Mapping
from typing import Any

from google.adk.agents.callback_context import CallbackContext
from google.adk.models.llm_request import LlmRequest
from google.adk.models.llm_response import LlmResponse
from google.adk.plugins.base_plugin import BasePlugin
from google.genai import types

from ..dataset_versions import replaced_earlier_data
from ..services import get_services
from ..session_state import SessionView, read_session
from .budget import ROOT_AGENT
from .ledger import CURRENT_LEDGER, RequestLedger


logger = logging.getLogger(__name__)

REPLACED_TABLE_LINE = (
    "[server] A new paste replaced the table at this point. What was said above about the data's columns, values and "
    "dates describes the replaced table, not the one in force now; the user's wishes and decisions above still hold."
)
"""The server's line that starts the current user turn on the summary turn of a paste that replaced data. Marked as the
page's action lines are, with a bracketed name before the text, and fixed English with no figure in it: it becomes part
of the user's turn, which the reply check reads as a source of figures."""

TABLE_TOOLS: Mapping[str, str] = {
    "get_dataset_profile": "returns the table's rows, columns, cells and bindings",
    "prepare_data": "changes the table; its answer counts rows and names columns and values",
    "query_data": "answers a question with figures computed from the table",
    "generate_data": "stores a computed table and returns its size and columns",
    "run_data_code": "stores the table the code made and returns its size and columns",
    "set_bindings": "binds the table's columns; its answer names them in its warnings",
    "get_current_code": "returns the plot's code, which reads the table's columns, and the rows its data holds",
    "plot_pipeline": "returns what the plot drew from the table: its texts, axis ranges and notes",
}
"""The root's tools whose exchanges describe the table, or a plot drawn from it, each with what its answer holds: on
the summary turn of a paste that replaced data they describe the replaced table, so their exchanges leave the request.
The plot memory is the server's own and stays in the session block, as do the plot versions and the line that says
the latest plot drew the replaced data."""

DISCUSSION_TOOLS: Mapping[str, str] = {
    "get_spec_brief": "returns the catalogue plot's text, the same for any table",
    "set_language": "records the visitor's choice of a language",
    "keep_plot_request": "keeps the visitor's plot wish; its answer says only whether it was kept",
    "forget": "takes an entry out of the plot memory; its answer is a count of entries",
    "switch_plot": "records the visitor's choice of another library",
}
"""The root's tools whose exchanges stay: each carries a decision of the visitor's or a fact of the catalogue plot,
never a fact of the table. Together with `TABLE_TOOLS` they name every tool of the root."""


def summary_turn(view: SessionView, ledger: RequestLedger | None) -> bool:
    """Whether a model call belongs to a paste's summary turn: the paste is not summarized yet, or the route marked the
    turn as its summary (`RequestLedger.summary_turn`), which holds for every call of the turn, also after the root's
    own change of the data made a version that is no paste. The session block lists the paste's profile on such a call
    (`agent.session_context`), and this filter reads the same condition."""
    return view.summary_pending or (ledger is not None and ledger.summary_turn)


def replacing_summary_turn(state: Any, session_id: str) -> bool:
    """Whether a model call of the root belongs to the summary turn of a paste that replaced data the session held
    before (`summary_turn` and `dataset_versions.replaced_earlier_data`): the turn whose session block ends its pasted
    line with `agent.REPLACED_DATA_LINE`."""
    view = read_session(state)
    if view is None or not summary_turn(view, CURRENT_LEDGER.get()):
        return False
    return replaced_earlier_data(get_services().datasets, session_id, view)


def _is_user_turn(content: types.Content) -> bool:
    """A user content that is no tool's answer: what a user, the page or the service wrote."""
    return content.role == "user" and not any(part.function_response is not None for part in content.parts or [])


def _stays(part: types.Part) -> bool:
    """Whether a part before the current user turn stays in the request on such a turn."""
    if part.function_call is not None:
        return part.function_call.name not in TABLE_TOOLS
    if part.function_response is not None:
        return part.function_response.name not in TABLE_TOOLS
    if part.thought:
        return False
    # A thought signature with nothing beside it is the remains of the root's thinking.
    return not (part.thought_signature and not part.text and part.inline_data is None and part.file_data is None)


def _discussion(contents: list[types.Content]) -> list[types.Content]:
    """`contents` without the table's exchanges and the root's thinking. A content left without a part goes, and two
    replies of the root that now follow each other become one content, so the turns still alternate where they did."""
    kept: list[types.Content] = []
    for content in contents:
        parts = [part for part in content.parts or [] if _stays(part)]
        if not parts:
            continue
        if content.role == "model" and kept and kept[-1].role == "model":
            kept[-1] = types.Content(role="model", parts=[*(kept[-1].parts or []), *parts])
        else:
            kept.append(types.Content(role=content.role, parts=parts))
    return kept


def _marked(content: types.Content) -> types.Content:
    """The current user turn with `REPLACED_TABLE_LINE` in front of the text of its first part, as a copy."""
    parts = list(content.parts or [])
    first = parts[0] if parts else None
    if first is not None and first.text is not None and not first.thought:
        if first.text.startswith(REPLACED_TABLE_LINE):
            return content
        parts[0] = first.model_copy(update={"text": f"{REPLACED_TABLE_LINE}\n\n{first.text}"})
        return types.Content(role=content.role, parts=parts)
    return types.Content(role=content.role, parts=[types.Part(text=REPLACED_TABLE_LINE), *parts])


def without_replaced_table(contents: list[types.Content]) -> list[types.Content]:
    """The root's request on the summary turn of a paste that replaced data: before the current user turn (the last
    user content that is no tool's answer) the discussion without the table's exchanges (`_discussion`), then that
    turn with `REPLACED_TABLE_LINE` at its start, then the turn's own calls as they are. A request with nothing before
    the current user turn stays as it is: no earlier word describes any table, so there is no switch to mark."""
    current = next((index for index in range(len(contents) - 1, -1, -1) if _is_user_turn(contents[index])), None)
    if current is None or current == 0:
        return contents
    return [*_discussion(contents[:current]), _marked(contents[current]), *contents[current + 1 :]]


class ReplacedTablePlugin(BasePlugin):
    """Takes the replaced table's facts out of the root's request on the summary turn of a paste that replaced data."""

    def __init__(self, name: str = "anyplot_replaced_table") -> None:
        super().__init__(name=name)

    async def before_model_callback(
        self, *, callback_context: CallbackContext, llm_request: LlmRequest
    ) -> LlmResponse | None:
        if callback_context.agent_name != ROOT_AGENT:
            return None
        try:
            if replacing_summary_turn(callback_context.state, callback_context.session.id):
                # In place: `ledger.root_request` is this object, and the reply checks read its contents.
                llm_request.contents = without_replaced_table(llm_request.contents)
        except Exception as exc:  # the turn goes on with the request as ADK built it
            logger.warning("replaced table filter failed: %s", type(exc).__name__)
        return None
