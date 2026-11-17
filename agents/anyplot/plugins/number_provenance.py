"""NumberProvenance: a figure in the root's final reply must stand in a source; under `enforce` an unsourced one is
asked for once, then the reply is withheld, and under `log`, the default, it is only counted.

The root prompt forbids a figure no tool produced in four places, and replies still stated totals, shares and fit
results that no tool had computed, beside plots that were right. A figure in a reply comes from a tool result or the
user's own input, is computed by a tool, or the reply says that it is not known. This plugin checks the figures a
reply writes in ASCII or full-width digits, in code and by number shapes only (`figures.py`), for every model: beside
the letters of a script written with spaces between words, and of Chinese, Japanese, Korean, Thai, Lao, Khmer and
Myanmar. A figure spelled out in words or written in other digits is not read, and a token whose marks fit no number
(`3.10.1`) is counted as `unread`, never a reason to ask again or to withhold:

* `after_model_callback` reads the root's final text reply (no tool call, not partial, not a fixed refusal) and
  checks each of its figures against the sources of the request the root answered (`ledger.root_request`, which
  ReplyLanguage keeps), each under its closed kind (`figures.SOURCE_KINDS`, most trusted first): every tool result
  still in it (`tool_result`; of a plot result, the adapter's and the reviewer's notes as `plot_notes` and the drawn
  texts of each role as `drawn_text`, each role's `count` and its `requested_not_found`, the root's own expected
  texts, left out; the code `get_current_code` returns as `plot_code`), the session part of the system instruction (`session`, its plot memory
  as `memory`), the user's own messages (`user`), and the service's limits that the root's instructions state as
  facts (`service`, `service_limits`, built from the server's own constants, never from the prompt text). Never the
  static prompt, the root's own earlier replies or its tool arguments, and never another agent's relayed messages.
* Under `enforce`, a turn that ran no tool (`ledger.tools` empty) whose reply states an unsourced figure is asked for
  once more, the way RootRefusal and EmptyReply ask (`follow_up_request` with the tools, offered only while none
  ran): the reply as the root's previous turn and `REASK_LINE`, which names the figures. The answer takes the reply's
  place in place (`take_place`), so ShippedReply and ReplyLanguage, which follow, check it as any reply. Verdict
  `reasked`, and the ledger keeps `figures_reasked`.
* Once `figures_reasked` is set, the turn's final reply is checked again against the sources as they are then:
  at once for an answer in text, or after the tools an answer called, keyed on the flag, never on `ledger.tools`, so
  a figure still unsourced after a tool call is withheld too, and a reply without any figure still leaves its `clean`
  line. A reply that still states one is withheld: the turn fails with `unverified_figure` (`ledger.fail`), which the
  route sends as `error{code:"unverified_figure"}` and the page words in its own fixed line, and the reply's text is
  cleared in place, so neither the page, nor the root's next request, nor the scope judge's context ever holds it.
  Verdict `withheld`. A second ask that cannot be made (no kept request, no budget, a failed call, an empty answer)
  withholds the reply too, with its `reason`. A withheld reply fails the whole turn as any failure does
  (`agents/main.py`): a data change or a plot the second ask's tools made stays stored, while a library switch the
  turn asked for, `done.turn` and a paste's summary mark are dropped.
* A turn that ran a tool and was not asked again is only logged (`unsourced_logged`), and the reply stays as it is:
  a re-ask after a tool could store its change twice.
* The replies that ReplyLanguage's and the output guard's own re-asks write are checked by `replacement_allowed`,
  which both call before they use one: on a turn that ran no tool or was asked for its figures, under `enforce`, a
  replacement that states an unsourced figure the reply before it did not hold is not used, and that plugin keeps the
  reply it had (verdict `kept`, with `replacement` naming the re-ask). Otherwise the check of a replacement only logs.

`AGENT_NUMBER_PROVENANCE` switches the check: `log` (the default: every reply only logged, none asked for again,
withheld or kept out), `enforce` (as above) or `off`. `enforce` can fail a turn, so the lines of `log` count what it
would ask again or withhold before it is switched on. Every reply that states a figure leaves a content-free
attribution line (`number_provenance`, the verdict, the counts of figures read, unsourced, exempt, unread and sourced
only by magnitude, and the sourced ones by kind as `from_<kind>`), never a figure or a word; the verdict goes into
the turn's record. A failure of the check itself keeps the reply (verdict `error`). An eval may pass a collector
(`collect_figures`), which alone receives the unsourced figures as written; the service passes none and keeps no
figure anywhere.

Outside the check: a figure spelled out in words or scaled by a word; and a figure the root itself put into a
`change_request`, a `remember` item or `expected_texts`, which comes back through the plot's notes, its code, the
plot memory or its drawn texts: the check catches such a figure where it first appears in a reply, not its later
echo.
"""

import json
import logging
import re
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass
from decimal import Decimal
from functools import cache
from typing import Any, Literal

from google.adk.agents.callback_context import CallbackContext
from google.adk.models.llm_request import LlmRequest
from google.adk.models.llm_response import LlmResponse
from google.adk.plugins.base_plugin import BasePlugin
from google.genai import types

from ..figures import Provenance, SourceKind, Sources, provenance
from ..memory import read_memory
from ..policy import fixed_replies
from ..services import get_services
from ..settings import get_settings
from .budget import ROOT_AGENT, book_response
from .empty_reply import is_empty, take_place
from .ledger import RequestLedger, attribution, budget_allows, ledger_for
from .reply_language import ask_root, follow_up_request, reply_text
from .tool_safety import NOTES_KEY, PIPELINE_TOOL, SHOWS_KEY


logger = logging.getLogger(__name__)

HOOK = "number_provenance"
"""The attribution hook. Each call writes it out as a literal, as every hook does, so the turn record's tests find
the hook and each verdict it writes in the source (`ledger.TURN_HOOKS`, `turn_record.HOOK_VERDICTS`)."""
UNVERIFIED_FIGURE = "unverified_figure"
"""The `error` code of a turn whose reply was withheld for a figure no source holds."""
REASK_LINE = (
    "Your last reply states figures that no tool result, no message of the user, no session block and no limit of "
    "the service holds: {figures}. Compute each one with a tool, such as query_data for a figure of the data, or give "
    "it as its source writes it, or say plainly that it is not known. Then write your reply again in full, in the "
    "same language."
)
Replacement = Literal["reply_language", "output_guard"]
"""The re-asks whose new reply `replacement_allowed` checks."""
CODE_TOOL = "get_current_code"
CODE_KEY = "code"
_RELAYED = re.compile(r"^\[[^\]\n]+\] ")
"""The start of another agent's relayed text in a user content (`[author] said:`), after ADK's preamble part."""
_FENCED = re.compile(r"<tool_notes>\n(.*)\n</tool_notes>", re.DOTALL)
REQUESTED_KEY = "requested_not_found"
"""The `shows` field that repeats the root's own expected texts: no source of a figure."""
DRAWN_KEY = "texts"


@dataclass(frozen=True)
class FigureCheck:
    """One check as an eval's collector receives it: the request, the verdict, whether the turn had run a tool, the
    attribution line's counts, the unsourced figures as written, and the re-ask whose replacement it checked."""

    request_id: str
    verdict: str
    tools: bool
    counts: dict[str, int]
    unsourced: tuple[str, ...]
    replacement: Replacement | None = None


COLLECTOR: ContextVar[Callable[[FigureCheck], None] | None] = ContextVar("number_provenance_collector", default=None)
"""The eval's collector (`collect_figures`); None in the service, which keeps no figure of a reply anywhere."""


@contextmanager
def collect_figures(collector: Callable[[FigureCheck], None]) -> Iterator[None]:
    """Hand every check made inside the block, in this context and the tasks it starts, to `collector`: for an eval on
    invented fixture data only. The previous collector is back on every exit."""
    token = COLLECTOR.set(collector)
    try:
        yield
    finally:
        COLLECTOR.reset(token)


def _collect(ledger: RequestLedger, verdict: str, found: Provenance, replacement: Replacement | None = None) -> None:
    collector = COLLECTOR.get()
    if collector is not None:
        check = FigureCheck(
            ledger.request_id, verdict, bool(ledger.tools), found.counts(), found.unsourced, replacement
        )
        collector(check)


@cache
def service_limits() -> tuple[Decimal, ...]:
    """The service's limits that the root's instructions state as facts, from the constants that hold them: the file
    sizes in MB, the rows and columns of a table, the lengths of a request, a remembered decision, an expected text, a
    language name, a label and a data snippet, the rows and columns a question returns, the values of one condition,
    the literals of a snippet, the points and rows a formula makes. A prompt test registers every such figure of
    `root.md` here or as an example. Imported late: these modules build on much of the package."""
    from ..code.validate import MAX_DATA_LITERAL_NUMBERS, MAX_LITERAL_NUMBERS
    from ..data.generate import DEFAULT_POINTS, MAX_GRID_ROWS, MAX_POINTS
    from ..data.parse import MAX_COMPUTED_BYTES
    from ..data.parse import MAX_INPUT_BYTES as MAX_PASTE_BYTES
    from ..data.prepare import MAX_ANY_VALUES
    from ..data.query import DEFAULT_QUERY_ROWS, MAX_QUERY_COLUMNS, MAX_QUERY_ROWS
    from ..language import MAX_LANGUAGE_CHARS
    from ..render.convert import MAX_INPUT_BYTES as MAX_FILE_BYTES
    from ..schemas import (
        MAX_CELL_CHARS,
        MAX_CHANGE_REQUEST_CHARS,
        MAX_COLUMNS,
        MAX_DECISION_CHARS,
        MAX_EXPECTED_TEXT_CHARS,
        MAX_ROWS,
    )
    from .tool_safety import MAX_DATA_CODE_CHARS

    counts = (
        MAX_ROWS,
        MAX_COLUMNS,
        MAX_CHANGE_REQUEST_CHARS,
        MAX_DECISION_CHARS,
        MAX_EXPECTED_TEXT_CHARS,
        MAX_LANGUAGE_CHARS,
        MAX_CELL_CHARS,
        MAX_DATA_CODE_CHARS,
        MAX_QUERY_ROWS,
        DEFAULT_QUERY_ROWS,
        MAX_QUERY_COLUMNS,
        MAX_ANY_VALUES,
        MAX_LITERAL_NUMBERS,
        MAX_DATA_LITERAL_NUMBERS,
        MAX_POINTS,
        DEFAULT_POINTS,
        MAX_GRID_ROWS,
    )
    megabyte = Decimal(1024 * 1024)
    sizes = (MAX_PASTE_BYTES, MAX_FILE_BYTES, MAX_COMPUTED_BYTES)
    return tuple(sorted({Decimal(count) for count in counts} | {Decimal(size) / megabyte for size in sizes}))


def session_part(request: LlmRequest) -> str | None:
    """The session block of the root's request: the last part of its system instruction, after the static policy
    (`agent.add_session_context`); None while the instruction has no part beside the policy."""
    instruction = request.config.system_instruction if request.config is not None else None
    if isinstance(instruction, types.Content) and instruction.parts and len(instruction.parts) > 1:
        return instruction.parts[-1].text or None
    return None


def _relayed(content: types.Content) -> bool:
    """Whether a user content is another agent's message as ADK relays it: a preamble, then quoted parts."""
    texts = [part.text for part in content.parts or [] if part.text and not part.thought]
    return len(texts) > 1 and all(_RELAYED.match(text) for text in texts[1:])


def _fenced(text: str) -> Any:
    """The JSON inside a result's `<tool_notes>` fence, or None when there is none."""
    match = _FENCED.search(text)
    try:
        return json.loads(match[1]) if match else None
    except ValueError:
        return None


def _add_shows(sources: Sources, text: str) -> None:
    """A plot result's `shows` block: the drawn texts of each role (`texts`, `first` and `last`) as `drawn_text`,
    the review's verdict and score (server-built) as a tool result, each role's `count` and the root's own expected
    texts not at all."""
    shown = _fenced(text)
    if not isinstance(shown, dict):
        sources.add_text(text, "drawn_text")
        return
    for key, value in shown.items():
        if key == DRAWN_KEY:
            if isinstance(value, dict):
                for role in value.values():
                    if isinstance(role, dict):
                        for part in ("texts", "first", "last"):
                            if part in role:
                                sources.add_json(role[part], "drawn_text")
        elif key != REQUESTED_KEY:
            sources.add_json(value, "tool_result")


def _add_notes(sources: Sources, text: str) -> None:
    """A plot result's `notes` block: the adapter's `changes` and the reviewer's `residual_defects`, model-written."""
    notes = _fenced(text)
    if notes is None:
        sources.add_text(text, "plot_notes")
    else:
        sources.add_json(notes, "plot_notes")


def _add_response(sources: Sources, name: str | None, response: Any) -> None:
    if not isinstance(response, dict):
        sources.add_json(response, "tool_result")
        return
    for key, value in response.items():
        kind: SourceKind = "tool_result"
        if name == PIPELINE_TOOL and key == SHOWS_KEY and isinstance(value, str):
            _add_shows(sources, value)
            continue
        if name == PIPELINE_TOOL and key == NOTES_KEY and isinstance(value, str):
            _add_notes(sources, value)
            continue
        if name == CODE_TOOL and key == CODE_KEY and isinstance(value, str):
            kind = "plot_code"
        sources.add_json(value, kind)


def request_sources(request: LlmRequest, state: Any) -> Sources:
    """The numbers the root had from a source when it wrote the reply to `request`, each under its kind: the tool
    results, with a plot result's notes and drawn texts and the plot's code apart, the session block with its plot
    memory apart, the user's messages and the service's limits."""
    sources = Sources()
    for content in request.contents:
        parts = content.parts or []
        for part in parts:
            if part.function_response is not None:
                _add_response(sources, part.function_response.name, part.function_response.response)
        if content.role == "user" and not _relayed(content):
            for part in parts:
                if part.text and not part.thought:
                    sources.add_text(part.text, "user")
    block = session_part(request)
    if block:
        from ..agent import memory_block  # imported late: `agent.py` builds this plugin

        memory = memory_block(read_memory(state))
        if memory and memory in block:
            sources.add_text(memory, "memory")
            block = block.replace(memory, "")
        sources.add_text(block, "session")
    for limit in service_limits():
        sources.add_number(limit, 0, "service")
    return sources


def _sources(ledger: RequestLedger, state: Any) -> Sources:
    request = ledger.root_request
    return request_sources(request, state) if isinstance(request, LlmRequest) else Sources()


def withhold(ledger: RequestLedger, response: LlmResponse) -> None:
    """Fail the turn with `unverified_figure` and clear the reply's text in place: the stream sends the error, and the
    event ADK stores holds no text, so no later request or judge context reads the figure."""
    ledger.fail(UNVERIFIED_FIGURE)
    response.content = types.Content(role="model", parts=[])


def reask_line(found: Provenance) -> str:
    return REASK_LINE.format(figures=", ".join(f'"{text}"' for text in found.unsourced))


def replacement_allowed(ledger: RequestLedger, state: Any, replaced: str, replacement: str, *, of: Replacement) -> bool:
    """Whether a re-ask's new reply may take the place of `replaced`: False only under `enforce`, on a turn that ran no
    tool or was asked for its figures, when `replacement` states an unsourced figure that `replaced` did not hold.

    ReplyLanguage and the output guard call it before they use the reply their own re-ask wrote, a direct model call
    that no plugin sees; on False each keeps the reply it had. In every other case the check only logs. Never raises:
    a failure of the check lets the replacement through, as a failure of the plugin keeps its reply.
    """
    try:
        mode = get_settings().number_provenance
        if mode == "off" or ledger.halted:
            return True
        found = provenance(replacement, _sources(ledger, state))
        before = Sources()
        before.add_text(replaced, "tool_result")
        new = [figure for figure in found.missing if before.kind_of(figure) is None]
        if new and mode == "enforce" and (not ledger.tools or ledger.figures_reasked):
            attribution("number_provenance", ledger, verdict="kept", replacement=of, **found.counts())
            _collect(ledger, "kept", found, of)
            return False
        if found.unsourced:
            attribution("number_provenance", ledger, verdict="unsourced_logged", replacement=of, **found.counts())
            _collect(ledger, "unsourced_logged", found, of)
        elif found.checked or found.exempt:
            attribution("number_provenance", ledger, verdict="clean", replacement=of, **found.counts())
            _collect(ledger, "clean", found, of)
        return True
    except Exception as exc:
        logger.warning("number provenance check of a replacement failed: %s", type(exc).__name__)
        return True


class NumberProvenancePlugin(BasePlugin):
    """Checks the figures of the root's final reply against its sources; asks once, then withholds."""

    def __init__(self, name: str = "anyplot_number_provenance") -> None:
        super().__init__(name=name)

    async def after_model_callback(
        self, *, callback_context: CallbackContext, llm_response: LlmResponse
    ) -> LlmResponse | None:
        if callback_context.agent_name != ROOT_AGENT or llm_response.partial:
            return None
        try:
            await self._check(callback_context, llm_response)
        except Exception as exc:
            logger.warning("number provenance check failed: %s", type(exc).__name__)
            try:
                ledger = ledger_for(callback_context.invocation_id)
                attribution("number_provenance", ledger, verdict="error")
            except Exception as again:
                logger.warning("number provenance line failed: %s", type(again).__name__)
        # Edited in place, never returned: a returned response would end the plugin chain before ShippedReply.
        return None

    async def _check(self, callback_context: CallbackContext, llm_response: LlmResponse) -> None:
        mode = get_settings().number_provenance
        if mode == "off":
            return
        ledger = ledger_for(callback_context.invocation_id)
        if ledger.halted:
            return
        reply = reply_text(llm_response)
        if reply is None or reply in fixed_replies():
            return
        sources = _sources(ledger, callback_context.state)
        found = provenance(reply, sources)
        if not found.unsourced:
            # A reply without a figure leaves no line, unless the turn was asked for its figures: then the line shows
            # how that turn ended.
            if found.checked or found.exempt or ledger.figures_reasked:
                attribution("number_provenance", ledger, verdict="clean", **found.counts())
                _collect(ledger, "clean", found)
            return
        if mode == "log" or (ledger.tools and not ledger.figures_reasked):
            attribution("number_provenance", ledger, verdict="unsourced_logged", **found.counts())
            _collect(ledger, "unsourced_logged", found)
            return
        if ledger.figures_reasked:
            withhold(ledger, llm_response)
            attribution("number_provenance", ledger, verdict="withheld", reason="unsourced", **found.counts())
            _collect(ledger, "withheld", found)
            return
        reason = await self._ask_again(callback_context, ledger, llm_response, reply, found)
        if reason is not None:
            withhold(ledger, llm_response)
            attribution("number_provenance", ledger, verdict="withheld", reason=reason, **found.counts())
            _collect(ledger, "withheld", found)
            return
        attribution("number_provenance", ledger, verdict="reasked", **found.counts())
        _collect(ledger, "reasked", found)
        again = reply_text(llm_response)
        if again is None or again in fixed_replies():
            # A tool call goes on in ADK's flow, and the turn's next reply is checked under the flag.
            return
        second = provenance(again, sources)
        if second.unsourced:
            withhold(ledger, llm_response)
            attribution("number_provenance", ledger, verdict="withheld", reason="unsourced", **second.counts())
            _collect(ledger, "withheld", second)
        else:
            attribution("number_provenance", ledger, verdict="clean", **second.counts())
            _collect(ledger, "clean", second)

    @staticmethod
    async def _ask_again(
        callback_context: CallbackContext,
        ledger: RequestLedger,
        llm_response: LlmResponse,
        reply: str,
        found: Provenance,
    ) -> str | None:
        """Ask the root once more; None when its answer took the reply's place, else why it did not."""
        request = ledger.root_request
        if not isinstance(request, LlmRequest):
            return "no_request"
        if not budget_allows(ledger, get_services().usage, get_settings()):
            return "budget"
        ledger.figures_reasked = True
        turns = [
            types.Content(role="model", parts=[types.Part(text=reply)]),
            types.Content(role="user", parts=[types.Part(text=reask_line(found))]),
        ]
        try:
            # Tools only while the turn has run none: after a tool, a second call could store its change twice.
            answer = await ask_root(follow_up_request(request, turns, tools=not ledger.tools))
        except Exception as exc:
            logger.warning("number provenance re-ask failed: %s", type(exc).__name__)
            return "error"
        if answer is None:
            return "error"
        book_response(ledger, ROOT_AGENT, callback_context.session.user_id, answer)
        if is_empty(answer):
            return "empty"
        take_place(llm_response, answer)
        return None
