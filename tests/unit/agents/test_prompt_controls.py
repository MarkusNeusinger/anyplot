"""The controls root.md names exist in the chat page's code, so the root never sends the user to a missing button.

Live test of 2026-10-15: the root told the user to "choose a separator in the data panel", a setting the page
does not have. root.md now lists the page's controls ("The page's controls"); this test keeps that list true.
"""

import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
PROMPT = ROOT / "agents" / "anyplot" / "prompts" / "root.md"
PAGE_SOURCES = [
    *sorted((ROOT / "app" / "src" / "sections" / "agent-chat").glob("*.ts*")),  # the reactions live in a .ts
    ROOT / "app" / "src" / "pages" / "AgentChatPage.tsx",
]
_CONTROL = re.compile(r"`(\.[a-z_]+\((?:'[^']*')?\))`")


def controls_section() -> str:
    text = PROMPT.read_text(encoding="utf-8")
    start = text.index("## The page's controls")
    end = text.index("\n## ", start + 1)
    return text[start:end]


def page_code() -> str:
    """The rendered labels of the page: JSX writes `'` as `&apos;`, test files are left out."""
    return "\n".join(
        path.read_text(encoding="utf-8").replace("&apos;", "'") for path in PAGE_SOURCES if ".test." not in path.name
    )


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
