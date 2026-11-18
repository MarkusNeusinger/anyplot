"""Every entry of the decision log has the fixed form and names its source.

`docs/decisions/` holds one file per decision of the owner. An entry is only worth something while it
can be found and checked: found by its date and its four lines, checked through the pull request or
the file its "Where" line names. This test holds the form; it cannot tell whether an entry is true,
which is what the owner's read of the pull request is for.
"""

from __future__ import annotations

import re
from datetime import date
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[2]
LOG = ROOT / "docs" / "decisions"

FILE_NAME = re.compile(r"^(\d{4}-\d{2}-\d{2})-[a-z0-9]+(?:-[a-z0-9]+)*\.md$")
FIELDS = ("Date", "Proposed", "Decided", "Where")
FIELD_LINE = re.compile(r"^- (\w+):(?: (.*))?$")
PULL_REQUEST = re.compile(r"(?<![\w/])#\d+\b")
BACKTICKED = re.compile(r"`([^`\s]+)`")
# A backticked word is meant as a file when it has a folder or an extension; `main` or `approved` is neither.
FILE_LIKE = re.compile(r"^(?:[\w.-]+/)+[\w.-]+$|^[\w.-]+\.\w+$")


def entries(log: Path = LOG) -> list[Path]:
    return sorted(path for path in log.glob("*.md") if path.name != "README.md")


def parse(text: str) -> tuple[list[tuple[str, str]], list[str]]:
    """The `- Name: text` lines with the indented lines that continue them, and every line that is neither.

    The first line is the title and is not looked at here. A blank line ends a field, so indented text
    after one belongs to nothing.
    """
    fields: list[tuple[str, str]] = []
    stray: list[str] = []
    open_field = False
    for line in text.splitlines()[1:]:
        start = FIELD_LINE.match(line)
        if start:
            fields.append((start.group(1), (start.group(2) or "").strip()))
            open_field = True
        elif not line.strip():
            open_field = False
        elif open_field and line.startswith("  "):
            name, value = fields[-1]
            fields[-1] = (name, f"{value} {line.strip()}".strip())
        else:
            stray.append(line.strip())
            open_field = False
    return fields, stray


def is_file_of(root: Path, candidate: str) -> bool:
    target = (root / candidate).resolve()
    return target.is_file() and target.is_relative_to(root.resolve())


def problems(path: Path, root: Path = ROOT) -> list[str]:
    """What keeps an entry from being found or checked; empty for a sound one."""
    found: list[str] = []

    name = FILE_NAME.match(path.name)
    day: date | None = None
    if not name:
        found.append("the name is YYYY-MM-DD-<short-slug>.md, lowercase with hyphens")
    else:
        try:
            day = date.fromisoformat(name.group(1))
        except ValueError:
            found.append(f"the name's date {name.group(1)} is no day of the calendar")

    text = path.read_text(encoding="utf-8")
    first = text.splitlines()[0] if text.strip() else ""
    if not (first.startswith("# ") and first[2:].strip()):
        found.append("the first line is the title, `# The decision as one short sentence`")

    fields, stray = parse(text)
    if stray:
        found.append(f"a line is neither one of the four lines nor an indented continuation: {stray[0][:60]!r}")
    names = tuple(field for field, _ in fields)
    if names != FIELDS:
        found.append(
            f"the lines are {', '.join(FIELDS)}, each once and in this order; found {', '.join(names) or 'none'}"
        )
        return found
    values = dict(fields)
    found.extend(f"`{field}` is empty" for field in FIELDS if not values[field])

    if day and values["Date"] != day.isoformat():
        found.append(f"`Date` says {values['Date']} and the file's name says {day.isoformat()}")

    where = values["Where"]
    files = [token for token in BACKTICKED.findall(where) if FILE_LIKE.match(token)]
    missing = [candidate for candidate in files if not is_file_of(root, candidate)]
    if missing:
        found.append(f"`Where` names what is no file of this repository: {', '.join(missing)}")
    elif where and not PULL_REQUEST.search(where) and not files:
        found.append("`Where` names no pull request (#12345) and no file of this repository in backticks")
    return found


def test_the_log_has_its_readme_and_at_least_one_entry() -> None:
    assert (LOG / "README.md").is_file(), "docs/decisions/README.md says what the log is and how to add to it"
    assert entries(), "the decision log holds no entry"


@pytest.mark.parametrize("path", entries(), ids=lambda path: path.name)
def test_an_entry_has_the_fixed_form_and_a_source(path: Path) -> None:
    assert problems(path) == [], f"docs/decisions/{path.name}"


def test_the_form_in_the_readme_is_the_form_the_test_holds(tmp_path: Path) -> None:
    readme = (LOG / "README.md").read_text(encoding="utf-8")
    block = re.search(r"```markdown\n(.*?)```", readme, re.DOTALL)
    assert block, "the README shows the form in a markdown block"
    shown = "\n".join(line[3:] if line.startswith("   ") else line for line in block.group(1).splitlines())
    day = re.search(r"^- Date: (\d{4}-\d{2}-\d{2})$", shown, re.MULTILINE)
    assert day, "the form in the README carries a date"

    assert problems(entry(tmp_path, shown + "\n", f"{day.group(1)}-the-form.md"), tmp_path) == []


SOUND = """# Replies are short

- Date: 2026-11-01
- Proposed: a reply that explains every step.
- Decided: a reply leads with the result,
  and asks only when it matters.
- Where: #12345
"""


def entry(folder: Path, text: str, name: str = "2026-11-01-replies-are-short.md") -> Path:
    path = folder / name
    path.write_text(text, encoding="utf-8")
    return path


def test_a_sound_entry_has_no_problem(tmp_path: Path) -> None:
    assert problems(entry(tmp_path, SOUND), tmp_path) == []
    assert problems(entry(tmp_path, SOUND.replace("\n", "\r\n")), tmp_path) == []


@pytest.mark.parametrize(
    "where",
    ["`docs/design.md`", "`RULES.md`", "#12345 and `docs/design.md`", "#12345, #12346", "#12345, on branch `main`"],
)
def test_a_pull_request_or_a_file_of_the_repository_is_a_source(tmp_path: Path, where: str) -> None:
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "design.md").write_text("# Design\n", encoding="utf-8")
    (tmp_path / "RULES.md").write_text("# Rules\n", encoding="utf-8")
    text = SOUND.replace("- Where: #12345", f"- Where: {where}")

    assert problems(entry(tmp_path, text), tmp_path) == []


BROKEN = [
    (("# Replies are short", "Replies are short"), None, "the first line is the title"),
    (("- Where: #12345\n", ""), None, "each once and in this order; found Date, Proposed, Decided"),
    (("- Where: #12345", "- Where: #12345\n- Date: 2026-11-02"), None, "each once and in this order"),
    (
        ("- Date: 2026-11-01\n- Proposed: a reply that explains every step.\n", "- Proposed: x.\n- Date: 2026-11-01\n"),
        None,
        "in this order; found Proposed, Date",
    ),
    (("- Proposed: a reply that explains every step.", "- Proposed:"), None, "`Proposed` is empty"),
    (("- Proposed: a reply that explains every step.", "- Proposed:   "), None, "`Proposed` is empty"),
    (("- Date: 2026-11-01", "- Date: 2026-11-02"), None, "`Date` says 2026-11-02 and the file's name says 2026-11-01"),
    (("  and asks only", "and asks only"), None, "neither one of the four lines nor an indented continuation"),
    (("- Where: #12345\n", "- Where: #12345\n\nAnd a story after it.\n"), None, "neither one of the four lines"),
    (("- Where: #12345\n", "- Where: #12345\n\n# A second title\n"), None, "neither one of the four lines"),
    (("- Where: #12345", "- Where: the owner said so in a session"), None, "`Where` names no pull request"),
    (("- Where: #12345", "- Where: `docs/gone.md`"), None, "is no file of this repository: docs/gone.md"),
    (("- Where: #12345", "- Where: #12345 and `docs/gone.md`"), None, "is no file of this repository: docs/gone.md"),
    (("- Where: #12345", "- Where: `docs/folder`"), None, "is no file of this repository: docs/folder"),
    (("- Where: #12345", "- Where: `../outside.md`"), None, "is no file of this repository: ../outside.md"),
    (None, "replies-are-short.md", "the name is YYYY-MM-DD-<short-slug>.md"),
    (None, "2026-11-01-Replies_short.md", "the name is YYYY-MM-DD-<short-slug>.md"),
    (None, "2026-13-01-replies-are-short.md", "is no day of the calendar"),
]


@pytest.mark.parametrize(("change", "name", "expected"), BROKEN)
def test_a_broken_entry_is_named(
    tmp_path: Path, change: tuple[str, str] | None, name: str | None, expected: str
) -> None:
    root = tmp_path / "repo"
    (root / "docs" / "folder").mkdir(parents=True)
    (tmp_path / "outside.md").write_text("# Outside the repository\n", encoding="utf-8")
    text = SOUND
    if change:
        assert change[0] in text
        text = text.replace(change[0], change[1])
    path = entry(root, text, name) if name else entry(root, text)

    assert any(expected in problem for problem in problems(path, root)), problems(path, root)
