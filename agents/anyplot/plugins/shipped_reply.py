"""ShippedReply: the closing reply after a shipped plot never asks for `.confirm()`.

A shipped plot (`ok`, `needs_attention`) was drawn from the data the user confirmed: the
pipeline refuses unconfirmed data (`not_ready`, `data_unconfirmed`), the result says
`data_confirmed: true` (`tool_safety.fence_pipeline_notes`), and `root.md` forbids asking for
`.confirm()` in that reply. A feedback case still had the root tell the user after an `ok`
plot that the data was not confirmed and to press `.confirm()`. A prompt rule that failed
gets a code check:

* `after_model_callback` reads the root's final text reply (no tool call, not partial,
  not a fixed refusal) when the turn shipped a plot (`ledger.shipped_in_turn`), and looks
  for the button's name, `.confirm()`, which is the same in every language. Each sentence
  that names it is dropped, so the user sees the rest of the reply word for word. The
  reply is edited in place and the callback returns None, so ReplyLanguage, which follows,
  still checks the edited reply's language.
* It writes a content-free attribution line (`shipped_reply`, verdict `dropped` with the
  number of sentences, or `kept` when every sentence names the button and nothing would be
  left, so the reply stays as it was).

Drop rather than ask the root again: dropping costs no model call and changes nothing else.
After a shipped plot no sentence that names `.confirm()` is right, and every other sentence
stays as the model wrote it, so a notice the reply must carry (a loader note, a requested
text the plot lacks) is never reworded or lost, which a re-ask, a new generation of the
whole reply, cannot promise. The limit: a separate sentence that says the data is not
confirmed without naming the button stays, because no code check reads that claim in
every language. The plugin never raises; a failure keeps the reply as it was.
"""

import logging
import re

from google.adk.agents.callback_context import CallbackContext
from google.adk.models.llm_response import LlmResponse
from google.adk.plugins.base_plugin import BasePlugin

from ..policy import fixed_replies
from .budget import ROOT_AGENT
from .ledger import attribution, ledger_for
from .reply_language import reply_text


logger = logging.getLogger(__name__)

CONFIRM = re.compile(r"\bconfirm\(\)", re.IGNORECASE)
"""The data panel's button as a reply names it (`.confirm()`, also without the dot); `reconfirm()` is no match."""
_BREAK = re.compile(r"((?<=[.!?…])[ \t]+|(?<=[。！？])[ \t]*)")
"""Between two sentences of one line: after a full stop, a question or exclamation mark and a space, or after
a CJK one. A dot inside `.confirm()` or `3.5` is followed by no space, so it never ends a sentence."""
_BARE_MARKER = re.compile(r"^\s*(?:[-*+•]|\d+[.)])?\s*$")
"""A line with no sentence left: empty, or only a list marker."""


def drop_confirm(text: str) -> tuple[str, int]:
    """`text` without its sentences that name `.confirm()`, and how many it dropped.

    Lines are kept apart (a list, paragraphs), a line left with only its list marker goes, and
    so does the blank line a dropped paragraph leaves behind.
    """
    lines: list[str] = []
    dropped = 0
    for line in text.split("\n"):
        if not CONFIRM.search(line):
            lines.append(line)
            continue
        parts = _BREAK.split(line)
        sentences, breaks = parts[0::2], [*parts[1::2], ""]
        kept = ""
        for sentence, gap in zip(sentences, breaks, strict=True):
            if CONFIRM.search(sentence):
                dropped += 1
                continue
            kept += sentence + gap
        kept = kept.rstrip()
        if not _BARE_MARKER.match(kept):
            lines.append(kept)
    joined = re.sub(r"\n{3,}", "\n\n", "\n".join(lines)).strip()
    return joined, dropped


def replace_reply(response: LlmResponse, text: str) -> None:
    """Put `text` in place of the response's reply text, in its first text part; thoughts stay as they are."""
    if response.content is None or not response.content.parts:
        return
    parts = []
    placed = False
    for part in response.content.parts:
        if part.text and not part.thought:
            if not placed:
                parts.append(part.model_copy(update={"text": text}))
                placed = True
            continue
        parts.append(part)
    response.content.parts = parts


class ShippedReplyPlugin(BasePlugin):
    """Drops the sentences of the root's reply after a shipped plot that ask for `.confirm()`."""

    def __init__(self, name: str = "anyplot_shipped_reply") -> None:
        super().__init__(name=name)

    async def after_model_callback(
        self, *, callback_context: CallbackContext, llm_response: LlmResponse
    ) -> LlmResponse | None:
        if callback_context.agent_name != ROOT_AGENT or llm_response.partial:
            return None
        try:
            self._check(callback_context, llm_response)
        except Exception as exc:
            logger.warning("shipped reply check failed: %s", type(exc).__name__)
        # Edited in place, never returned: a returned response would end the plugin chain before ReplyLanguage.
        return None

    def _check(self, callback_context: CallbackContext, llm_response: LlmResponse) -> None:
        ledger = ledger_for(callback_context.invocation_id)
        if not ledger.shipped_in_turn or ledger.halted:
            return
        reply = reply_text(llm_response)
        if reply is None or reply in fixed_replies() or not CONFIRM.search(reply):
            return
        edited, dropped = drop_confirm(reply)
        if not edited:
            attribution("shipped_reply", ledger, verdict="kept", sentences=dropped)
            return
        replace_reply(llm_response, edited)
        attribution("shipped_reply", ledger, verdict="dropped", sentences=dropped)
