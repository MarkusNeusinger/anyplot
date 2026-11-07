"""ShippedReply: the closing reply after a shipped plot never asks for `.confirm()`, and no reply names the plot button.

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
  still checks the edited reply's language. A reply ReplyLanguage asks for again comes from
  a direct model call that no plugin sees, so ReplyLanguage runs the same check
  (`scrub_shipped_reply`) on it before it replaces the first one.
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

The page has no `.confirm()` any more: `.create_plot()` confirms the data in its own click,
and neither `root.md` nor the session block names the old button. The check stays as the
backstop for a reply that still names it, which after a shipped plot is wrong twice over.

The plot button, in every turn: since the composer row has four fixed places, the line at the
chat's foot names the plot button and what it waits for, and `root.md` says a reply never
tells the user to press it (`.create_plot()`, `.update_plot()`, `.plot_all()`). The prompt had
told the root to say so in four places while its reply rules forbade it, so the rule gets the
same code check: every root reply, not only after a shipped plot, drops the sentences that name
one of the three, whose names are the same in every language, and logs `plot_button` with the
same verdicts. A reply in which every sentence names it stays whole, as above; a sentence that
says what to check without naming the button stays.
"""

import logging
import re
from collections.abc import Callable

from google.adk.agents.callback_context import CallbackContext
from google.adk.models.llm_response import LlmResponse
from google.adk.plugins.base_plugin import BasePlugin

from ..policy import fixed_replies
from .budget import ROOT_AGENT
from .ledger import RequestLedger, attribution, ledger_for
from .reply_language import reply_text


logger = logging.getLogger(__name__)

CONFIRM = re.compile(r"\bconfirm\(\)", re.IGNORECASE)
"""Step 1's button as a reply names it (`.confirm()`, also without the dot); `reconfirm()` is no match."""
PLOT_BUTTON = re.compile(r"\b(?:create_plot|update_plot|plot_all)\(\)", re.IGNORECASE)
"""The composer's plot button by any of its names (`.create_plot()`, `.update_plot()`, `.plot_all()`)."""
_CLOSERS = "\"'”’)\\]*_`"
_BREAK = re.compile(
    rf"((?<=[.!?…])[ \t]+|(?<=[.!?…][{_CLOSERS}])[ \t]+|(?<=[.!?…][{_CLOSERS}]{{2}})[ \t]+|(?<=[。！？])[ \t]*)"
)
"""Between two sentences of one line: after a full stop, a question or exclamation mark and a space, also when up
to two closing quotes, brackets or Markdown marks follow it (`."`, `.)`, `.**`), or after a CJK one. A dot inside
`.confirm()` or `3.5` is followed by no space, so it never ends a sentence."""
_MARKER = re.compile(r"^\s*(?:[-*+•]|\d+[.)])\s+")
"""A list item's marker at the start of a line, which a dropped first sentence must not take with it."""
_BARE_MARKER = re.compile(r"^\s*(?:[-*+•]|\d+[.)])?\s*$")
"""A line with no sentence left: empty, or only a list marker."""


def drop_sentences(text: str, pattern: re.Pattern[str]) -> tuple[str, int]:
    """`text` without its sentences that `pattern` finds, and how many it dropped.

    Lines are kept apart (a list, paragraphs), a line left with only its list marker goes, and
    so does the blank line a dropped paragraph leaves behind.
    """
    lines: list[str] = []
    dropped = 0
    for line in text.split("\n"):
        if not pattern.search(line):
            lines.append(line)
            continue
        marker = _MARKER.match(line)
        prefix = marker.group(0) if marker else ""
        parts = _BREAK.split(line[len(prefix) :])
        sentences, breaks = parts[0::2], [*parts[1::2], ""]
        kept = ""
        for sentence, gap in zip(sentences, breaks, strict=True):
            if pattern.search(sentence):
                dropped += 1
                continue
            kept += sentence + gap
        kept = (prefix + kept).rstrip()
        if not _BARE_MARKER.match(kept):
            lines.append(kept)
    joined = re.sub(r"\n{3,}", "\n\n", "\n".join(lines)).strip()
    return joined, dropped


def drop_confirm(text: str) -> tuple[str, int]:
    """`text` without its sentences that name `.confirm()`, and how many it dropped."""
    return drop_sentences(text, CONFIRM)


def drop_plot_button(text: str) -> tuple[str, int]:
    """`text` without its sentences that name the plot button, and how many it dropped."""
    return drop_sentences(text, PLOT_BUTTON)


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


def _scrubbed(text: str, drop: Callable[[str], tuple[str, int]], hook: str, ledger: RequestLedger) -> str:
    """`text` after `drop`, logged under `hook`; the text as it was when nothing would be left."""
    edited, dropped = drop(text)
    if not edited:
        attribution(hook, ledger, verdict="kept", sentences=dropped)
        return text
    attribution(hook, ledger, verdict="dropped", sentences=dropped)
    return edited


def scrub_shipped_reply(ledger: RequestLedger, response: LlmResponse) -> None:
    """Drop the `.confirm()` sentences of a root reply in a turn whose plot shipped, and the sentences that name
    the plot button in any turn, in place; never raises.

    The plugin's check, and ReplyLanguage's on the reply it asked for again, which no plugin sees.
    """
    try:
        if ledger.halted:
            return
        reply = reply_text(response)
        if reply is None or reply in fixed_replies():
            return
        edited = reply
        if ledger.shipped_in_turn and CONFIRM.search(edited):
            edited = _scrubbed(edited, drop_confirm, "shipped_reply", ledger)
        if PLOT_BUTTON.search(edited):
            edited = _scrubbed(edited, drop_plot_button, "plot_button", ledger)
        if edited != reply:
            replace_reply(response, edited)
    except Exception as exc:
        logger.warning("shipped reply check failed: %s", type(exc).__name__)


class ShippedReplyPlugin(BasePlugin):
    """Drops the sentences of the root's reply that ask for `.confirm()` after a shipped plot, or name the plot
    button in any turn."""

    def __init__(self, name: str = "anyplot_shipped_reply") -> None:
        super().__init__(name=name)

    async def after_model_callback(
        self, *, callback_context: CallbackContext, llm_response: LlmResponse
    ) -> LlmResponse | None:
        if callback_context.agent_name != ROOT_AGENT or llm_response.partial:
            return None
        scrub_shipped_reply(ledger_for(callback_context.invocation_id), llm_response)
        # Edited in place, never returned: a returned response would end the plugin chain before ReplyLanguage.
        return None
