"""ReplyLanguage: a final reply of the root in another language than the session's is asked again, once.

The root writes in the session language (`language.py`); the prompt, the session block's
"Reply language" line and the action line say so, and a live test of 2026-10-14 still
saw an English summary in a German session (#12176). This plugin checks it in code:

* `before_model_callback` keeps the root's request on the ledger (`root_request`), so
  the re-ask has the same context.
* `after_model_callback` reads a final text reply of the root (no tool call, not
  partial, not a fixed refusal, which `policy.fixed_replies` lists and which an unknown
  session language gets in English by design), and `language_detect.mismatch` compares
  its language with the session's, when a paste, a message or a choice set it (never
  the default English, see `checked_language`). Only a sure guess counts (`language_detect.detect`
  returns None when unsure), and only for a session language the detector knows. On a
  mismatch it writes a content-free attribution line (`reply_language`, verdict
  `mismatch`, the expected and the found code), and, while the request budget allows a
  call, asks the root model once more, without tools, with the wrong reply as its
  previous turn and `REASK_LINE` naming the language (the server's English name for it,
  never the stored value). The new reply replaces the old one when the detector is sure
  it is in the session language (verdict `reasked`); otherwise, also when it is unsure, the first reply stays (verdict
  `reask_failed`). The extra call is booked like any other (`budget.book_response`).
  At most one re-ask per turn (`ledger.reply_reasked`).

`REASK` switches the re-ask off, leaving only the attribution line (an owner decision
pending on 2026-10-14: re-ask, or only log). The plugin never raises; a failure keeps
the reply as it was.
"""

import logging
from typing import Any

from google.adk.agents.callback_context import CallbackContext
from google.adk.models.llm_request import LlmRequest
from google.adk.models.llm_response import LlmResponse
from google.adk.plugins.base_plugin import BasePlugin
from google.genai import types

from ..language import english_name, is_valid
from ..language_detect import detect, expected_code, mismatch
from ..policy import fixed_replies
from ..services import get_services
from ..session_state import LANGUAGE, LANGUAGE_SOURCE
from ..settings import get_settings
from .budget import ROOT_AGENT, book_response, strip_tools
from .ledger import attribution, budget_allows, ledger_for


logger = logging.getLogger(__name__)

REASK = True
CHECKED_SOURCES = frozenset(("pasted", "detected", "chosen"))
"""The language sources the check holds a reply to (`checked_language`); never the default."""
REASK_LINE = (
    "Your last reply is not in {name}, the session language. Write the same reply again in {name}: the same "
    "content and length, column names, values and code unchanged. Answer with the reply only."
)


def reply_text(response: LlmResponse) -> str | None:
    """The text of a final reply: its text parts, None when it calls a tool or holds no text."""
    content = response.content
    if content is None or not content.parts:
        return None
    if any(part.function_call is not None for part in content.parts):
        return None
    texts = [part.text for part in content.parts if part.text and not part.thought]
    return "".join(texts).strip() or None


def checked_language(state: Any) -> str | None:
    """The session language to hold the reply to, None when the session is on the default.

    The default (English, source `default`) is no signal of what the user reads: a short
    first message that the judge could not place leaves it, and the root may rightly answer
    in the message's language then. A language set by a paste, a message or a choice is.
    """
    language, source = state.get(LANGUAGE), state.get(LANGUAGE_SOURCE)
    if not isinstance(language, str) or not is_valid(language) or source not in CHECKED_SOURCES:
        return None
    return language


def root_model() -> Any:
    """The root agent's model, imported late: `agent.py` builds this plugin."""
    from ..agent import root_agent

    return root_agent.canonical_model


def reask_request(request: LlmRequest, reply: str, name: str) -> LlmRequest:
    """A copy of the root's request with its wrong reply and the re-ask line after it, without tools."""
    config = request.config.model_copy(deep=True) if request.config is not None else types.GenerateContentConfig()
    copy = LlmRequest(
        model=request.model,
        contents=[
            *(content.model_copy(deep=True) for content in request.contents),
            types.Content(role="model", parts=[types.Part(text=reply)]),
            types.Content(role="user", parts=[types.Part(text=REASK_LINE.format(name=name))]),
        ],
        config=config,
    )
    copy.cache_config = request.cache_config
    strip_tools(copy)
    return copy


class ReplyLanguagePlugin(BasePlugin):
    """Checks the language of the root's final reply and asks once more on a sure mismatch."""

    def __init__(self, name: str = "anyplot_reply_language") -> None:
        super().__init__(name=name)

    async def before_model_callback(
        self, *, callback_context: CallbackContext, llm_request: LlmRequest
    ) -> LlmResponse | None:
        if callback_context.agent_name == ROOT_AGENT:
            ledger_for(callback_context.invocation_id).root_request = llm_request
        return None

    async def after_model_callback(
        self, *, callback_context: CallbackContext, llm_response: LlmResponse
    ) -> LlmResponse | None:
        if callback_context.agent_name != ROOT_AGENT or llm_response.partial:
            return None
        try:
            return await self._check(callback_context, llm_response)
        except Exception as exc:
            logger.warning("reply language check failed: %s", type(exc).__name__)
            return None

    async def _check(self, callback_context: CallbackContext, llm_response: LlmResponse) -> LlmResponse | None:
        ledger = ledger_for(callback_context.invocation_id)
        if ledger.halted or ledger.reply_reasked:
            return None
        reply = reply_text(llm_response)
        if reply is None or reply in fixed_replies():
            return None
        language = checked_language(callback_context.session.state)
        if language is None:
            return None
        found = mismatch(reply, language)
        expected = expected_code(language)
        name = english_name(language)
        if found is None or expected is None or name is None:
            return None
        attribution("reply_language", ledger, verdict="mismatch", expected=expected, found=found)
        request = ledger.root_request
        if not REASK or not isinstance(request, LlmRequest):
            return None
        if not budget_allows(ledger, get_services().usage, get_settings()):
            return None
        ledger.reply_reasked = True
        final: LlmResponse | None = None
        async for response in root_model().generate_content_async(reask_request(request, reply, name), stream=False):
            if not response.partial:
                final = response
        if final is None:
            return None
        book_response(ledger, ROOT_AGENT, callback_context.session.user_id, final)
        again = reply_text(final)
        # Only a reply surely in the session language replaces the first one: an unsure guess ("Done.") does not.
        if again is None or detect(again) != expected:
            attribution("reply_language", ledger, verdict="reask_failed", expected=expected, found=found)
            return None
        attribution("reply_language", ledger, verdict="reasked", expected=expected, found=found)
        return final
