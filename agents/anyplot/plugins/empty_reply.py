"""EmptyReply: a final response of the root without text is asked for once more; still none ends the turn as `no_reply`.

A persona test of 2026-11-06 pasted a table with a note and got no assistant turn at all: the root's final
response held no text (no content, an empty part, or thoughts only), the stream translator sends no `message` for
an empty text (`agents/stream.py`), so the turn sent `done` alone, and the route marked the paste as summarized.
ADK's own empty-response policy marks a `STOP` without content as an error only after the model callbacks, and the
translator sends no such error. This plugin checks it in code:

* `after_model_callback` reads a final response of the root: not partial, no function call, and no text outside
  thoughts (`reply_language.reply_text` is None).
* While the turn has not asked yet (`ledger.empty_reasked`) and the request budget allows a call, it asks the root
  model once more: the same request (`ledger.root_request`, which ReplyLanguage keeps) with `RETRY_LINE` after it.
  The request keeps its tools only while the turn has run none (`ledger.tools` empty): an empty first reply may still
  need to read the data, while after a tool a second call of a tool that stores something (`prepare_data` within its
  per-turn cap, `set_bindings`, which has none) would apply it twice. The answer takes the empty response's place in
  place (its content, finish reason, error, usage, model version and turn flag) and is never returned, so
  ShippedReply and ReplyLanguage, which follow, check it as any reply: a returned response would end the plugin chain
  before them. An answer that calls a tool goes on in ADK's flow: the tool runs and the root is called again. The
  extra call is booked like any other (`budget.book_response`). Verdict `reasked`.
* When the second ask brings no text and no tool call either, raises, or cannot be made (no kept request, no budget
  left), the turn fails with `no_reply` (`ledger.fail`): the route ends it with `error{code:"no_reply"}`, which the
  page shows as the turn with "send your message again", and a paste the turn was to summarize stays unsummarized
  (`agents/main.py`), so the next turn summarizes it. Verdict `no_reply`, with the `reason` (`empty`, `error`,
  `no_request`, `budget`, and `check_failed` when the check itself failed on a response that is still empty).
* A turn that already carries its answer (`carries_answer`) never fails this way: a shipped plot is on the page, the
  page carries out a requested library switch, and a change a tool stored in the session (data, bindings, a language,
  a kept plot request, a forgotten memory entry; `stored_in_turn`, from the record of the turn's calls, which
  ToolSafety writes from each tool's own answer, also one whose result it then refused) reaches the page with the
  turn's `done`. Sending the message again would apply such a change a
  second time. Its empty closing reply is asked for again all the same, and stays empty without an error (verdict
  `empty_kept`).
* The retry line is a `user` turn of its own after the request's last one, which may be the user's message or the
  tool results: the Claude Messages API combines consecutive user turns into one (Claude is the production root). The
  Gemini arm has not been tried live with this shape; a call it refuses is the `error` reason, so the turn ends as
  `no_reply` (or `empty_kept`), never silent.
* A response that stays empty is still the event ADK builds and stores: its empty-response policy marks it with the
  `MODEL_RETURNED_NO_CONTENT` error code after the callbacks. The event holds no text, so neither the root's next
  request, nor the judge's context (`scope_guard.session_turns`), nor the stream translator reads anything from it;
  it is left as ADK stores it rather than edited against ADK's own policy.

The attribution lines (`empty_reply`) are content-free. The plugin never raises; a failure of the check itself keeps
the response as it was and, when that response is still empty, fails the turn as `no_reply` all the same.
"""

import logging

from google.adk.agents.callback_context import CallbackContext
from google.adk.models.llm_request import LlmRequest
from google.adk.models.llm_response import LlmResponse
from google.adk.plugins.base_plugin import BasePlugin
from google.genai import types

from ..services import get_services
from ..settings import get_settings
from .budget import ROOT_AGENT, book_response
from .ledger import RequestLedger, attribution, budget_allows, ledger_for
from .reply_language import ask_root, follow_up_request, reply_text


logger = logging.getLogger(__name__)

NO_REPLY = "no_reply"
"""The `error` code of a turn whose root wrote no text, twice."""
RETRY_LINE = (
    "Your last answer came back empty: the user saw no reply. Answer the user's last message now, as your "
    "instructions say."
)
STATE_TOOLS = frozenset(
    {"prepare_data", "generate_data", "run_data_code", "set_bindings", "set_language", "keep_plot_request", "forget"}
)
"""The root's tools that store a change in the session when they answer `ok`: the data, the bindings, the language,
a kept plot request, the plot memory. `switch_plot` asks the page for a switch (`ledger.switch_request`) instead. A
`plot_pipeline` call that kept the first plot's request (a `not_ready` run, a refusal before the run) is none of them:
such a turn's answer is its reply, which a summary turn owes, so an empty one still ends as `no_reply` unless the
page got the `plot` event (`stream.Translator.plot_sent`)."""
STORED_OUTCOMES = frozenset({"changed", "viewed", "kept"})
"""The outcomes of a call of `STATE_TOOLS` that stored something (`ledger.CallOutcome`): a change, a view of the
plot, a kept request."""


def is_empty(response: LlmResponse) -> bool:
    """Whether a final model response carries nothing for the user: no function call and no text outside thoughts."""
    parts = response.content.parts if response.content is not None and response.content.parts else []
    if any(part.function_call is not None for part in parts):
        return False
    return reply_text(response) is None


def stored_in_turn(ledger: RequestLedger) -> bool:
    """Whether a root tool of the turn stored a change in the session, as the record of its calls says
    (`RequestLedger.tool_calls`, read from each tool's own answer): also when ToolSafety then refused the result for
    its keys or its size, since the change was stored all the same and reaches the page with the turn's `done`."""
    return any(call.tool in STATE_TOOLS and call.outcome in STORED_OUTCOMES for call in ledger.tool_calls)


def carries_answer(ledger: RequestLedger) -> bool:
    """Whether the turn gave the user something besides a reply: a shipped plot, a switch, a stored change."""
    return ledger.shipped_in_turn or ledger.switch_request is not None or stored_in_turn(ledger)


def take_place(response: LlmResponse, answer: LlmResponse) -> None:
    """Put `answer` in the empty response's place, in place, so the plugins after this one check the answer."""
    response.content = answer.content
    response.finish_reason = answer.finish_reason
    response.error_code = answer.error_code
    response.error_message = answer.error_message
    response.usage_metadata = answer.usage_metadata
    response.model_version = answer.model_version
    response.turn_complete = answer.turn_complete


class EmptyReplyPlugin(BasePlugin):
    """Asks the root once more for a final reply without text, and fails the turn as `no_reply` when it stays empty."""

    def __init__(self, name: str = "anyplot_empty_reply") -> None:
        super().__init__(name=name)

    async def after_model_callback(
        self, *, callback_context: CallbackContext, llm_response: LlmResponse
    ) -> LlmResponse | None:
        if callback_context.agent_name != ROOT_AGENT or llm_response.partial:
            return None
        try:
            await self._check(callback_context, llm_response)
        except Exception as exc:
            logger.warning("empty reply check failed: %s", type(exc).__name__)
            self._fail_closed(callback_context, llm_response)
        # Edited in place, never returned: a returned response would end the plugin chain before ShippedReply.
        return None

    @staticmethod
    def _fail_closed(callback_context: CallbackContext, llm_response: LlmResponse) -> None:
        """After a failure of the check itself, a response that is still empty ends the turn as `no_reply` all the same:
        otherwise the turn would send `done` alone, the lost turn this plugin exists for."""
        try:
            ledger = ledger_for(callback_context.invocation_id)
            if ledger.halted or not is_empty(llm_response) or carries_answer(ledger):
                return
            attribution("empty_reply", ledger, verdict=NO_REPLY, reason="check_failed")
            ledger.fail(NO_REPLY)
        except Exception as exc:
            logger.warning("empty reply fallback failed: %s", type(exc).__name__)

    async def _check(self, callback_context: CallbackContext, llm_response: LlmResponse) -> None:
        ledger = ledger_for(callback_context.invocation_id)
        if ledger.halted or not is_empty(llm_response):
            return
        reason = await self._ask_again(callback_context, ledger, llm_response)
        if reason is None:
            return
        if carries_answer(ledger):
            attribution("empty_reply", ledger, verdict="empty_kept", reason=reason)
            return
        attribution("empty_reply", ledger, verdict=NO_REPLY, reason=reason)
        ledger.fail(NO_REPLY)

    @staticmethod
    async def _ask_again(
        callback_context: CallbackContext, ledger: RequestLedger, llm_response: LlmResponse
    ) -> str | None:
        """Ask the root once more; None when its answer took the empty response's place, else why it did not."""
        request = ledger.root_request
        if ledger.empty_reasked:
            return "empty"  # the turn's one second ask came back empty too
        if not isinstance(request, LlmRequest):
            return "no_request"
        if not budget_allows(ledger, get_services().usage, get_settings()):
            return "budget"
        ledger.empty_reasked = True
        retry = types.Content(role="user", parts=[types.Part(text=RETRY_LINE)])
        try:
            # Tools only for an empty first reply: after a tool, a second call could store its change twice.
            answer = await ask_root(follow_up_request(request, [retry], tools=not ledger.tools))
        except Exception as exc:
            logger.warning("empty reply re-ask failed: %s", type(exc).__name__)
            return "error"
        if answer is None:
            return "error"
        book_response(ledger, ROOT_AGENT, callback_context.session.user_id, answer)
        if is_empty(answer):
            return "empty"
        take_place(llm_response, answer)
        attribution("empty_reply", ledger, verdict="reasked")
        return None
