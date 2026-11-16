"""The crawler copy of `/agent` must say what the page says.

A recognised crawler or AI assistant that follows a link to https://anyplot.ai/agent reads `/seo-proxy/agent`
(`api/routers/seo.py`), never the explainer a browser renders (`app/src/sections/agent-chat/AgentIntro.tsx`). The
copy restates the page's title, description, example pairs and terms of use, and `/agent` is where those terms live.
A change on one side alone would leave a crawler or an assistant quoting terms the page no longer states, and no
other test would notice: the page's tests run in the browser's world and the copy's in the API's. So the strings are read from the source here, the way `test_agent_intro_examples.py` reads the examples.
"""

from __future__ import annotations

import html
import re

from api.routers import seo
from tests.unit.test_agent_intro_examples import AGENT_INTRO, example_pairs


SOURCE = AGENT_INTRO.read_text(encoding="utf-8")
LEGAL_PAGE = AGENT_INTRO.parents[2] / "pages" / "LegalPage.tsx"

TERMS_BLOCK = re.compile(r"const AGENT_TERMS: \[string, ReactNode\]\[\] = \[(?P<body>.*?)\n\];", re.DOTALL)
TERM_LABEL = re.compile(r"\[\s*(?P<q>['\"])(?P<label>[^'\"]+)(?P=q),")
STRING_TERM = re.compile(
    r"\[\s*(?P<q>['\"])(?P<label>[^'\"]+)(?P=q),\s*(?P<p>['\"])(?P<text>.*?)(?P=p),?\s*\]", re.DOTALL
)
PARAGRAPH_OPEN = '<Box component="p"'
BOX_TAG = re.compile(r"<(?P<close>/?)Box\b[^>]*?(?P<self>/?)>")
JSX_CHILD = re.compile(r"(<[^>]*>|\{' '\})")


def string_constant(name: str) -> str:
    """An exported string constant of AgentIntro.tsx, in either quote."""
    match = re.search(rf"export const {name} =\s*(?P<q>['\"])(?P<value>.*?)(?P=q);", SOURCE, re.DOTALL)
    assert match is not None, f"AgentIntro.tsx has no `export const {name} = '…';`"
    return match["value"]


def terms_block() -> str:
    block = TERMS_BLOCK.search(SOURCE)
    assert block is not None, "AgentIntro.tsx has no `const AGENT_TERMS: [string, ReactNode][] = [...];`"
    return block["body"]


def page_paragraph() -> str:
    """The children of the explainer's one `<Box component="p">`, up to its own closing tag.

    The paragraph holds a link and a code span, each a `<Box>` of its own, so its end is found by
    counting the boxes that open and close inside it, not at the first `</Box>`.
    """
    assert SOURCE.count(PARAGRAPH_OPEN) == 1, 'AgentIntro.tsx should have exactly one `<Box component="p"`'
    start = SOURCE.index(">", SOURCE.index(PARAGRAPH_OPEN)) + 1
    depth = 1
    for tag in BOX_TAG.finditer(SOURCE, start):
        if tag["close"]:
            depth -= 1
        elif not tag["self"]:
            depth += 1
        if depth == 0:
            return SOURCE[start : tag.start()]
    raise AssertionError('the explainer\'s `<Box component="p">` is never closed')


def jsx_run(text: str) -> str:
    """One run of JSX text between two tags, as JSX renders it.

    The rule is JSX's own: a line loses its leading spaces unless it is the run's first and its
    trailing spaces unless it is the run's last, an empty line drops out, and the lines left are
    joined with one space. Whitespace that holds a line break next to a tag thus renders as nothing.
    """
    lines = text.replace("\t", " ").split("\n")
    kept = []
    for index, line in enumerate(lines):
        if index > 0:
            line = line.lstrip(" ")
        if index < len(lines) - 1:
            line = line.rstrip(" ")
        if line:
            kept.append(line)
    return " ".join(kept)


def jsx_text(children: str) -> str:
    """The text a JSX fragment renders: tags drop out, `{' '}` is a space, entities are decoded."""
    parts = []
    for part in JSX_CHILD.split(children):
        if part == "{' '}":
            parts.append(" ")
        elif not part.startswith("<"):
            parts.append(jsx_run(part))
    return html.unescape("".join(parts))


def served_paragraph() -> str:
    """The text of the crawler copy's paragraph, its link and code span unwrapped."""
    paragraph = re.search(r"<p>(?P<inner>.*?)</p>", seo._AGENT_BOT_BODY, re.DOTALL)
    assert paragraph is not None, "the crawler copy of /agent has no paragraph"
    return html.unescape(re.sub(r"<[^>]+>", "", paragraph["inner"]))


def test_the_title_and_description_are_the_pages():
    assert seo.AGENT_INTRO_TITLE == string_constant("AGENT_INTRO_TITLE")
    assert seo.AGENT_INTRO_DESCRIPTION == string_constant("AGENT_INTRO_DESCRIPTION")


def copy_paragraph() -> str:
    """The copy's paragraph from its constants: the opening, the description, the model, the closing."""
    return " ".join(
        (seo.AGENT_INTRO_OPENING, seo.AGENT_INTRO_DESCRIPTION, seo.AGENT_INTRO_MODEL, seo.AGENT_INTRO_CLOSING)
    )


def test_the_paragraph_around_the_description_is_the_pages():
    # The page writes its paragraph out in JSX, across lines and around a link and a code span,
    # rather than from the description constant; read as JSX renders it, it is the copy's opening
    # sentence, the description, the model's sentence and the closing sentence, so neither side can
    # drift from the other.
    assert jsx_text(page_paragraph()) == copy_paragraph()


def test_the_model_is_the_one_the_legal_page_names():
    # The legal page's row on the model says where a visitor's text goes; the explainer names the same
    # provider and location, so a change of either reaches both.
    legal = LEGAL_PAGE.read_text(encoding="utf-8")
    named = seo.AGENT_INTRO_MODEL.removeprefix("the model is ").removesuffix(".")
    assert f"goes to {named} under" in legal, named


def test_the_copy_serves_the_paragraph_and_the_terms():
    # The served body is built from the constants above; a slip in the builder would otherwise pass
    # every comparison of the constants with the page.
    assert served_paragraph() == copy_paragraph()
    labels = [match["label"] for match in TERM_LABEL.finditer(terms_block())]
    assert re.findall(r"<dt>([^<]*)</dt>", seo._AGENT_BOT_BODY) == labels
    for label, text in seo.AGENT_TERMS:
        term = f"<dt>{html.escape(label, quote=False)}</dt><dd>{html.escape(text, quote=False)}</dd>"
        assert term in seo._AGENT_BOT_BODY, label


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
