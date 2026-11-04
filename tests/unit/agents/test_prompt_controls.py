"""The controls root.md names exist in the chat page's code, so the root never sends the user to a missing button.

Live test of 2026-10-15: the root told the user to "choose a separator in the data panel", a setting the page
does not have. root.md now lists the page's controls ("The page's controls"); this test keeps that list true.

The other direction since 2026-11-04: the data panel's bullet had lost `.open()` and the file it takes, so the
root told a user who asked to load an Excel file that the page had no way to. Every button of the data card is
named in that bullet now, and a new one fails the test until the bullet names it.
"""

import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
PROMPT = ROOT / "agents" / "anyplot" / "prompts" / "root.md"
AGENT_CHAT = ROOT / "app" / "src" / "sections" / "agent-chat"
PAGE_SOURCES = [
    *sorted(AGENT_CHAT.glob("*.ts*")),  # the reactions live in a .ts
    ROOT / "app" / "src" / "pages" / "AgentChatPage.tsx",
]
_CONTROL = re.compile(r"`(\.[a-z_]+\((?:'[^']*')?\))`")
_LABEL = r"\.[a-z_]+\((?:'[^']*')?\)"
# The comments go before the labels are read: a `//` after a colon belongs to a URL (`https://`), a `/*` after a
# word, a quote or a `*` to a glob (`'image/*'`).
_COMMENT = re.compile(r"(?<![\w'\"*])/\*.*?\*/|(?<!:)//[^\n]*", re.DOTALL)
# A button's text is its label: the whole JSX text between a tag's `>` and the next `<` (`>.open()<`, also over
# lines), or the start of a string (`'.parse() …'`, `` `.filter() · ${count}` ``). A label inside a sentence
# ("decide on the table below first: .use() or .discard()") points to a button and is no button itself, and a
# chained call alone on its line (`.trim()`) follows no `>`. A quote after a word or a bracket closes a string.
_BUTTON_TEXT = re.compile(rf">\s*({_LABEL})\s*<|(?<![\w)\]])['\"`]({_LABEL})")
_COMPONENT_IMPORT = re.compile(r"""(?:src/sections/agent-chat/|\./)([A-Za-z]+)['"]""")


def controls_section() -> str:
    text = PROMPT.read_text(encoding="utf-8")
    start = text.index("## The page's controls")
    end = text.index("\n## ", start + 1)
    return text[start:end]


def controls_of(part: str) -> set[str]:
    """The controls one bullet of "The page's controls" names, such as "The data panel", also over wrapped lines."""
    section = controls_section()
    start = section.index(f"\n- {part}:")
    end = min(
        (at for at in (section.find("\n- ", start + 1), section.find("\n\n", start + 1)) if at != -1), default=None
    )
    return set(_CONTROL.findall(section[start:end]))


def page_code() -> str:
    """The rendered labels of the page: JSX writes `'` as `&apos;`, test files are left out."""
    return "\n".join(
        path.read_text(encoding="utf-8").replace("&apos;", "'") for path in PAGE_SOURCES if ".test." not in path.name
    )


def data_card_components() -> list[Path]:
    """`DataPanel.tsx` and every component of `agent-chat/` it renders, also through another one, such as
    the full view `DataView.tsx`, which it imports on demand.

    The `.ts` modules are left out: their texts serve the whole page (`messages.ts` also names the admin
    fan-out's `.plot_all()`), and a button of the card has its label in a component.
    """
    found = [AGENT_CHAT / "DataPanel.tsx"]
    for path in found:
        for name in _COMPONENT_IMPORT.findall(path.read_text(encoding="utf-8")):
            component = AGENT_CHAT / f"{name}.tsx"
            if component.exists() and component not in found:
                found.append(component)
    return found


def data_card_buttons() -> set[str]:
    """The labels of the data card's buttons, read from the code without its comments."""
    labels: set[str] = set()
    for path in data_card_components():
        code = _COMMENT.sub("", path.read_text(encoding="utf-8").replace("&apos;", "'"))
        labels.update(alone or quoted for alone, quoted in _BUTTON_TEXT.findall(code))
    return labels


def test_the_prompt_lists_controls() -> None:
    assert len(_CONTROL.findall(controls_section())) >= 20


def test_every_control_the_prompt_names_is_on_the_page() -> None:
    code = page_code()
    missing = [label for label in _CONTROL.findall(controls_section()) if label not in code]

    assert missing == []


def test_the_whole_prompt_names_only_controls_of_the_page() -> None:
    """A `.name()` anywhere in root.md is a button the user is told about, so it must exist too."""
    code = page_code()
    named = set(_CONTROL.findall(PROMPT.read_text(encoding="utf-8")))

    assert sorted(label for label in named if label not in code) == []


def test_every_button_of_the_data_card_is_in_the_data_panel_bullet() -> None:
    """The other direction: the data panel's bullet names each button of the card, so the root knows them all.

    The bullet, not the whole section: `.open()` of the result cards is in the section already, and was the
    one way into the data panel the root did not know.
    """
    buttons = data_card_buttons()

    assert {".open()", ".parse()", ".view_all()"} <= buttons  # the reading still finds them
    assert sorted(buttons - controls_of("The data panel")) == []
