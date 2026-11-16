"""The crawler copy of `/agent` must say what the page says.

A recognised crawler or AI assistant that follows a link to https://anyplot.ai/agent reads `/seo-proxy/agent`
(`api/routers/seo.py`), never the explainer a browser renders (`app/src/sections/agent-chat/AgentIntro.tsx`). The
copy restates the page's title, description, example pairs and terms of use, and the legal page sends readers to
`/agent` for those terms. A change on one side alone would leave a crawler or an assistant quoting terms the page no
longer states, and no other test would notice: the page's tests run in the browser's world and the copy's in the
API's. So the strings are read from the source here, the way `test_agent_intro_examples.py` reads the examples.
"""

from __future__ import annotations

import re

from api.routers import seo
from tests.unit.test_agent_intro_examples import AGENT_INTRO, example_pairs


SOURCE = AGENT_INTRO.read_text(encoding="utf-8")

TERMS_BLOCK = re.compile(r"const AGENT_TERMS: \[string, ReactNode\]\[\] = \[(?P<body>.*?)\n\];", re.DOTALL)
TERM_LABEL = re.compile(r"\[\s*(?P<q>['\"])(?P<label>[^'\"]+)(?P=q),")
STRING_TERM = re.compile(
    r"\[\s*(?P<q>['\"])(?P<label>[^'\"]+)(?P=q),\s*(?P<p>['\"])(?P<text>.*?)(?P=p),?\s*\]", re.DOTALL
)


def string_constant(name: str) -> str:
    """An exported string constant of AgentIntro.tsx, in either quote."""
    match = re.search(rf"export const {name} =\s*(?P<q>['\"])(?P<value>.*?)(?P=q);", SOURCE, re.DOTALL)
    assert match is not None, f"AgentIntro.tsx has no `export const {name} = '…';`"
    return match["value"]


def terms_block() -> str:
    block = TERMS_BLOCK.search(SOURCE)
    assert block is not None, "AgentIntro.tsx has no `const AGENT_TERMS: [string, ReactNode][] = [...];`"
    return block["body"]


def test_the_title_and_description_are_the_pages():
    assert seo.AGENT_INTRO_TITLE == string_constant("AGENT_INTRO_TITLE")
    assert seo.AGENT_INTRO_DESCRIPTION == string_constant("AGENT_INTRO_DESCRIPTION")


def test_the_paragraph_around_the_description_is_the_pages():
    # The page writes its paragraph out in JSX, across lines; with the whitespace folded, the copy's
    # sentences before and after the description stand in it word for word.
    page = " ".join(SOURCE.split())
    assert seo.AGENT_INTRO_OPENING in page
    assert seo.AGENT_INTRO_CLOSING in page


def test_the_terms_are_the_pages_word_for_word():
    body = terms_block()
    labels = [match["label"] for match in TERM_LABEL.finditer(body)]
    sentences = {match["label"]: match["text"] for match in STRING_TERM.finditer(body)}
    # Every line but the privacy link is a sentence; a line written in another shape would otherwise be
    # skipped without a sound.
    assert labels == ["status", "limits", "your code", "privacy"], labels
    assert list(sentences) == ["status", "limits", "your code"], list(sentences)
    assert tuple(sentences.items()) == seo.AGENT_TERMS


def test_the_privacy_line_leads_where_the_pages_does():
    body = terms_block()
    assert seo.AGENT_PRIVACY_LINK in body
    assert "`${paths.legal}#assistant`" in body
    assert '<a href="https://anyplot.ai/legal#assistant">' in seo._AGENT_BOT_BODY


def test_the_examples_are_the_pages():
    assert tuple(example_pairs()) == seo.AGENT_INTRO_EXAMPLES
