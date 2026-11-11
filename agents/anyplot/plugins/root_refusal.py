"""RootRefusal: a fixed refusal the root sends for a message the scope judge passed is asked for once more.

The scope judge classifies every typed message before the root runs, and `root.md` tells the root to refuse what is
out of scope with a fixed text as well, so the root is a second judge. In the persona round of 2026-11-11 it sent the
out-of-scope refusal, word for word, for two messages the judge had passed (a question about the fitted line's slope,
a title wish), both right after a real refusal. The page labels such a reply as an ordinary answer, and the user has
to say the same thing again. The refused turns no longer reach the root's request (`scope_guard.without_refused_turns`),
which takes the trigger away; this plugin is the check behind it:

* `after_model_callback` reads a final text reply of the root (not partial, no tool call) and compares it with the
  fixed refusal texts (`policy.fixed_replies`, every language).
* It acts only where the judge itself said `in_scope` in this turn (`ledger.guards`). After a rescued paste note
  (`paste_note_in_scope`), a served library named in another spelling (`served_library_in_scope`) and on the page's
  actions the judge passed nothing as in scope, and the root's refusal is the backup it is meant to be.
* It asks the root once more: the same request (`ledger.root_request`, which ReplyLanguage keeps) with `RETRY_LINE`
  after it, and with the tools only while the turn has run none, as EmptyReply does. The refusal itself is not put
  into that request: a refusal in the context is what the root repeats. The answer takes the refusal's place in
  place and is never returned, so ShippedReply and ReplyLanguage, which follow, check it as any reply, and the
  output guard reads the event it becomes. Verdict `reasked`.
* The second ask is a second look, not an order: `RETRY_LINE` says what the judge found and leaves the answer to the
  root, which stays the backup behind a judge that passes too much. A second answer that is a fixed refusal again,
  or empty, or a call that fails or cannot be made (no kept request, no budget left), leaves the first reply as it
  was: verdict `kept`. The root is never asked a third time, and the turn never fails for it.

The attribution lines (`root_refusal`) are content-free. The plugin never raises; a failure keeps the reply.
"""

import logging

from google.adk.agents.callback_context import CallbackContext
from google.adk.models.llm_request import LlmRequest
from google.adk.models.llm_response import LlmResponse
from google.adk.plugins.base_plugin import BasePlugin
from google.genai import types

from ..policy import fixed_replies
from ..services import get_services
from ..settings import get_settings
from .budget import ROOT_AGENT, book_response
from .empty_reply import is_empty, take_place
from .ledger import RequestLedger, attribution, budget_allows, ledger_for
from .reply_language import ask_root, follow_up_request, reply_text


logger = logging.getLogger(__name__)

RETRY_LINE = (
    "The scope check passed the user's last message, and your answer to it was a fixed refusal. A message the service "
    "refused earlier is no part of this one. Read the last message again on its own: when it is about this plot or "
    "the data for it, answer it now, as your instructions say; refuse again only when it is not."
)
JUDGE_PASSED = ("scope_guard", "in_scope")
"""The guard line of a message the scope judge itself classified as in scope."""


def is_fixed_refusal(response: LlmResponse) -> bool:
    """Whether a final model response is one of the service's fixed refusal texts and nothing else."""
    parts = response.content.parts if response.content is not None and response.content.parts else []
    if any(part.function_call is not None for part in parts):
        return False
    reply = reply_text(response)
    return reply is not None and reply.strip() in fixed_replies()


class RootRefusalPlugin(BasePlugin):
    """Asks the root once more when it answers a message the judge passed with a fixed refusal."""

    def __init__(self, name: str = "anyplot_root_refusal") -> None:
        super().__init__(name=name)

    async def after_model_callback(
        self, *, callback_context: CallbackContext, llm_response: LlmResponse
    ) -> LlmResponse | None:
        if callback_context.agent_name != ROOT_AGENT or llm_response.partial:
            return None
        try:
            await self._check(callback_context, llm_response)
        except Exception as exc:
            logger.warning("root refusal check failed: %s", type(exc).__name__)
        # Edited in place, never returned: a returned response would end the plugin chain before ShippedReply.
        return None

    async def _check(self, callback_context: CallbackContext, llm_response: LlmResponse) -> None:
        ledger = ledger_for(callback_context.invocation_id)
        if ledger.halted or JUDGE_PASSED not in ledger.guards or not is_fixed_refusal(llm_response):
            return
        if await self._ask_again(callback_context, ledger, llm_response):
            attribution("root_refusal", ledger, verdict="reasked")
        else:
            attribution("root_refusal", ledger, verdict="kept")

    @staticmethod
    async def _ask_again(callback_context: CallbackContext, ledger: RequestLedger, llm_response: LlmResponse) -> bool:
        """Ask the root once more; True when its answer took the refusal's place."""
        request = ledger.root_request
        if ledger.refusal_reasked or not isinstance(request, LlmRequest):
            return False
        if not budget_allows(ledger, get_services().usage, get_settings()):
            return False
        ledger.refusal_reasked = True
        retry = types.Content(role="user", parts=[types.Part(text=RETRY_LINE)])
        try:
            # Tools only while the turn has run none: after a tool, a second call could store its change twice.
            answer = await ask_root(follow_up_request(request, [retry], tools=not ledger.tools))
        except Exception as exc:
            logger.warning("root refusal re-ask failed: %s", type(exc).__name__)
            return False
        if answer is None:
            return False
        book_response(ledger, ROOT_AGENT, callback_context.session.user_id, answer)
        if is_empty(answer) or is_fixed_refusal(answer):
            return False
        take_place(llm_response, answer)
        return True
