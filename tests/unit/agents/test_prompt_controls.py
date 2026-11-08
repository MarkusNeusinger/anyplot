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
AGENT = ROOT / "agents" / "anyplot" / "agent.py"  # writes the session block, which names the step's button
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


def components_from(root: str) -> list[Path]:
    """`root` and every component of `agent-chat/` it renders, also through another one, such as the data
    panel's full view `DataView.tsx`, which it imports on demand.

    The `.ts` modules are left out: their texts serve the whole page (`messages.ts` also names the admin
    fan-out's `.plot_all()`), and a button has its label in a component.
    """
    found = [AGENT_CHAT / root]
    for path in found:
        for name in _COMPONENT_IMPORT.findall(path.read_text(encoding="utf-8")):
            component = AGENT_CHAT / f"{name}.tsx"
            if component.exists() and component not in found:
                found.append(component)
    return found


def data_card_components() -> list[Path]:
    """`DataPanel.tsx` and the components it renders."""
    return components_from("DataPanel.tsx")


def composer_components() -> list[Path]:
    """`Composer.tsx` and the components it renders, such as the attachment chip."""
    return components_from("Composer.tsx")


def status_line_components() -> list[Path]:
    """`ChatFrame.tsx`, whose line at the frame's foot holds `.stop()`, `.start_over()` and `.feedback()`."""
    return components_from("ChatFrame.tsx")


def remembered_components() -> list[Path]:
    """`Remembered.tsx`: the remembered decisions' count on a chapter line and their list under it."""
    return components_from("Remembered.tsx")


def bullet_of(part: str) -> str:
    """The text of one bullet of "The page's controls", which stands on one line."""
    section = controls_section()
    start = section.index(f"\n- {part}:")
    return section[start : section.find("\n", start + 1)]


def buttons_of(components: list[Path]) -> set[str]:
    """The labels of the buttons of these components, read from the code without its comments."""
    labels: set[str] = set()
    for path in components:
        code = _COMMENT.sub("", path.read_text(encoding="utf-8").replace("&apos;", "'"))
        labels.update(alone or quoted for alone, quoted in _BUTTON_TEXT.findall(code))
    return labels


def data_card_buttons() -> set[str]:
    """The labels of the data card's buttons."""
    return buttons_of(data_card_components())


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


def test_the_data_panel_bullet_names_exactly_the_buttons_of_the_data_card() -> None:
    """The other direction: the data panel's bullet names each button of the card, so the root knows them all,
    and names no button the card lost (`.confirm()` and the formula's `.send()` left it for the composer, and the
    text box with `.parse()`, `.open()`, `.replace()` and `.keep()` left it for the message box's attachment).

    The bullet, not the whole section: `.open()` of the result cards and the composer is in the section already.
    """
    buttons = data_card_buttons()
    bullet = controls_of("The data panel")

    # The reading still finds them, `.change()` on the bindings line among them.
    assert {".view_all()", ".use()", ".discard()", ".undo()", ".change()"} <= buttons
    assert not {".parse()", ".open()", ".replace()", ".keep()"} & buttons
    assert sorted(buttons - bullet) == []
    assert sorted(bullet - buttons) == []


def test_the_data_panel_bullet_keeps_the_card_open_and_folds_older_versions() -> None:
    """Since the v4 chapters (2026-11-07) the live data card stays open in both steps: the pinned header above
    the thread, whose `.show()` and `.hide()` opened and closed the card, went, and every older data version
    folds to its label, which opens it read-only. The bullet says so, the folded version has no button the
    bullet would have to name, and no header is left that the root could send the user to. The card's number is
    the session's own, the one the session block lists, so "v2" names one table to the user and to the root."""
    section = controls_section()
    start = section.index("\n- The data panel:")
    bullet = section[start : section.find("\n", start + 1)]

    assert "open in both steps" in bullet
    assert "which opens it read-only, with nothing to press" in bullet
    assert "open and close the card" not in bullet
    assert "the same number the session block lists" in bullet
    assert "which is not the number the session block lists" not in bullet
    assert buttons_of([AGENT_CHAT / "FoldedData.tsx"]) == set()
    assert not (AGENT_CHAT / "PinnedData.tsx").exists()


def test_the_composer_bullet_names_exactly_the_buttons_of_the_composer() -> None:
    """The same for the composer, its row and the data line above the box (`.example_data()` and `.open()`
    as links): a button added to it fails here until the bullet names it, and a button it lost fails until
    the bullet drops it: `.confirm()`, which `.create_plot()` took into its own click, `.send()`, which
    Enter replaced, and `.stop()`, which moved to the line at the chat's foot. The plot button's labels
    carry an arrow (`'.update_plot() →'`), which the label pattern reads past."""
    buttons = buttons_of(composer_components())
    bullet = controls_of("The composer")

    assert {".create_plot()", ".update_plot()", ".plot_all()", ".example_data()", ".open()"} <= buttons
    assert not {".confirm()", ".send()", ".stop()"} & buttons
    assert sorted(buttons - bullet) == []
    assert sorted(bullet - buttons) == []


def test_the_status_line_bullet_names_exactly_the_buttons_at_its_end() -> None:
    """The line at the chat's foot holds the actions that are not the step's: `.stop()`, a button of its
    own since nothing in the composer turns into it, `.start_over()` and the chat's `.feedback()`."""
    buttons = buttons_of(status_line_components())
    bullet = controls_of("The line at the chat's foot")

    assert buttons == {".stop()", ".start_over()", ".feedback()"}
    assert sorted(bullet ^ buttons) == []


def test_the_remembered_bullet_names_exactly_the_buttons_of_the_decisions_list() -> None:
    """Since the v4 chapters the remembered decisions stand on the latest `# plot` line as a count that unfolds
    their list under it; the list above the composer, its heading and the `.hide()` and `.show()` that folded it
    went. The bullet names each button of the list's component and none it lost, and no sentence of the section
    sends the user to a list above the composer."""
    buttons = buttons_of(remembered_components())
    bullet = controls_of("The remembered decisions")

    assert {".forget()", ".forget_all()"} <= buttons
    assert not {".hide()", ".show()"} & buttons
    assert sorted(buttons - bullet) == []
    assert sorted(bullet - buttons) == []
    assert "on the latest `# plot` line" in bullet_of("The remembered decisions")
    assert "above the composer" not in controls_section()


def test_the_remembered_bullet_says_where_the_decisions_stand_after_a_paste_with_other_columns() -> None:
    """Owner decision of 2026-11-08: after a paste that lacks a column the data before it was bound to, the new
    `# data` line holds the decisions until the next plot, counted as earlier ones and with `.forget_all()` beside
    them, so the root can point the user there. The words are the page's own."""
    remembered = (AGENT_CHAT / "Remembered.tsx").read_text(encoding="utf-8")
    bullet = bullet_of("The remembered decisions")

    assert "the new `# data` line, as `· 3 earlier decisions ▾ · .forget_all()`, until the next plot" in bullet
    assert "'earlier decision'" in remembered and "Forget all earlier decisions" in remembered


def test_the_prompt_says_what_the_page_shows_of_questions_and_kept_decisions() -> None:
    """The page marks a message that changed nothing as a question and starts the reply with a label of its own,
    and an open plot card names the remembered decisions it kept and added on its first line, while its label
    keeps the request it answered: the root knows both, so it never writes the label into its reply, and it can
    point the user to what a version kept. The words are the page's own."""
    messages = (AGENT_CHAT / "messages.ts").read_text(encoding="utf-8")
    labels = (AGENT_CHAT / "cardLabels.ts").read_text(encoding="utf-8")
    chapters = bullet_of("The data panel")
    card = bullet_of("Each result card")

    assert "`? answer · nothing changed`" in chapters
    assert "which the page adds by itself" in chapters
    assert "`· 2 questions`" in chapters
    assert "ANSWER_LABEL = 'answer · nothing changed'" in messages
    assert "kept 3" not in card
    assert "`kept: y = 7 line · x label · new: log scale on y`" in card
    assert "`kept ${" not in labels
    assert "`${part}: " in labels


def test_the_result_card_bullet_says_where_each_download_sits() -> None:
    """Persona tests found the root telling users that `.download()` for the PNG sits "below the image",
    while it is an icon over the image's top right corner (a word on the line under the image only on a
    phone), and the code's downloads stand in the code's line further down. The bullet names each place,
    and the card's code still has the PNG's download over the image and the phone's line of words."""
    section = controls_section()
    start = section.index("\n- Each result card:")
    bullet = section[start : section.find("\n", start + 1)]
    card = (AGENT_CHAT / "ResultCard.tsx").read_text(encoding="utf-8")

    assert "Over the image's top right corner" in bullet
    assert "on a phone, by their names in the line right under the image" in bullet
    assert "in the code's line: `.show_code()`" in bullet
    assert "`.download('data.csv')`" in bullet.split("in the code's line:")[1]
    assert "below the image" not in bullet
    assert ".expand()" not in bullet and ".collapse()" not in bullet
    assert 'title=".download()"' in card  # the icon over the image, its name on hover
    assert re.search(r">\s*\.download\(\)\s*<", card)  # the word on the phone's line


def test_the_prompt_names_no_confirm_button() -> None:
    """`.create_plot()` confirms the data in its own click, so no sentence of root.md, nor the session
    block, sends the user to a `.confirm()` that is gone, and the prompt says where the click is."""
    text = PROMPT.read_text(encoding="utf-8")

    assert re.findall(r"\bconfirm\(\)", text) == []
    assert re.findall(r"\bconfirm\(\)", AGENT.read_text(encoding="utf-8")) == []
    # By the box at every width: beside it from the page's `sm` up, under it on a phone.
    assert "the plot button by the message box (`.create_plot()`)" in text
    assert "plot button by the message box" in AGENT.read_text(encoding="utf-8")
    assert "beside the message box" not in text + AGENT.read_text(encoding="utf-8")


def test_the_prompt_never_has_a_reply_send_the_user_to_the_plot_button() -> None:
    """The line at the chat's foot names the plot button and what it waits for, so a reply never has to:
    root.md once told the root in four places to say "press `.create_plot()`" while its reply rules forbade
    it. No instruction asks for it now, and ShippedReply drops a sentence that names it anyway."""
    text = PROMPT.read_text(encoding="utf-8")

    assert re.findall(r"press(?:es|ing)? `\.(?:create|update)_plot\(\)`", text) == []
    assert "never tells the user to press the plot button" in text
