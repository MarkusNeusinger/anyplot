"""The README, the AI workflow page and the About page say what the code does; this test keeps them saying it.

Text that describes a mechanism drifts from it without a sound: a rubric gains a criterion, a bound moves, the
default model changes, and the README goes on claiming the old value to every reader who checks it against the
code. So each number or name those texts state about the system is read here from its source in code, and must still
stand where the text states it; every relative link must resolve to a tracked file, and every in-page anchor to a
heading. A change to a mechanism then fails this test until the text follows (`/write-docs`, "Sync duties").

The matching is deliberately loose about the prose and strict about the claim: a value must stand right beside its
keyword ("starts at 90", "one repair round"), so a sentence can be reworded freely as long as that phrase stays,
while a wider window would let a neighbouring number ("two reviews" next to "repair round") pass for the claim.
Values are read with `ast` from the agents' source, never by importing it, so the test needs no ADK.

One claim has no offline source: the number of pull requests merged from the owner's account. The texts state it as a
floor ("more than 950 pull requests from my account have merged"), and `MERGED_PRS_SNAPSHOT` below records the count
and the day it was taken. The floor must be a multiple of 50, below the snapshot and at most 50 below it, so it can
neither overclaim nor go stale by more than one step. The release procedure (`agentic/commands/release.md`, step 4)
counts again, updates the snapshot and raises the floor in the same commit.
"""

from __future__ import annotations

import ast
import re
import subprocess
from functools import cache
from pathlib import Path

import pytest

from core.constants import LIBRARIES_METADATA, QUALITY_THRESHOLD_APPROVAL, QUALITY_THRESHOLD_FINAL_APPROVAL
from core.defects import CRITERIA


ROOT = Path(__file__).resolve().parents[2]
README = ROOT / "README.md"
WORKFLOW_PAGE = ROOT / "docs" / "concepts" / "ai-workflow.md"
ABOUT_PAGE = ROOT / "app" / "src" / "pages" / "AboutPage.tsx"
SEO = ROOT / "api" / "routers" / "seo.py"
LINKED_DOCS = (README, WORKFLOW_PAGE)

# Pull requests merged from the owner's account, and when that was counted:
# `gh pr list --state merged --author MarkusNeusinger --limit 5000 --json number --jq length`.
# Updated by the release procedure (agentic/commands/release.md, step 4) together with the texts' floor.
MERGED_PRS_SNAPSHOT = (955, "2026-11-11")
PR_FLOOR_STEP = 50

NUMBER_WORDS = {
    1: "one",
    2: "two",
    3: "three",
    4: "four",
    5: "five",
    6: "six",
    7: "seven",
    8: "eight",
    9: "nine",
    10: "ten",
    11: "eleven",
    12: "twelve",
    13: "thirteen",
    14: "fourteen",
    15: "fifteen",
    16: "sixteen",
    17: "seventeen",
    18: "eighteen",
    19: "nineteen",
    20: "twenty",
}


# --- reading the texts --------------------------------------------------------------------------


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def section(markdown: str, heading: str) -> str:
    """The text of one `## heading` section, up to the next `## `."""
    start = markdown.index(f"\n## {heading}\n")
    end = markdown.find("\n## ", start + 1)
    return markdown[start : end if end != -1 else None]


def collapse(text: str) -> str:
    """Whitespace collapsed, so a value and its keyword on two wrapped lines still sit side by side."""
    return re.sub(r"\s+", " ", text)


def near(text: str, value: str, keyword: str, window: int = 3) -> bool:
    """Whether `value` stands as a whole word within `window` characters of `keyword`, case-insensitively.

    The window is the gap between the two, so the region searched also holds the value's own length on either side.
    """
    text = collapse(text)
    pattern = re.compile(rf"(?<![\w.]){re.escape(value)}(?![\w])", re.IGNORECASE)
    reach = window + len(value)
    for match in re.finditer(re.escape(keyword), text, re.IGNORECASE):
        if pattern.search(text, max(0, match.start() - reach), match.end() + reach):
            return True
    return False


def about_bot_body() -> str:
    """The About page's crawler copy (`_ABOUT_BOT_BODY` in seo.py) as one text.

    The copy is a run of string literals, one per source line, so a phrase that wraps between two literals is joined
    back together here; matching against seo.py as written would miss it.
    """
    body = read(SEO).split("\n_ABOUT_BOT_BODY = (", 1)[1].split("\n)\n", 1)[0]
    return re.sub(r"[\"']\s*\n\s*f?[\"']", "", body)


# --- reading the sources ------------------------------------------------------------------------


@cache
def source_tree(relative: str) -> ast.Module:
    return ast.parse(read(ROOT / relative))


def module_constant(relative: str, name: str) -> object:
    """A module-level `NAME = <literal>` of a source file."""
    for node in source_tree(relative).body:
        if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == name for t in node.targets):
            return ast.literal_eval(node.value)
    raise AssertionError(f"{relative} has no module constant {name}")


def field_default(relative: str, class_name: str, field: str) -> object:
    """The default of a class attribute `field: T = <literal>` or `field: T = Field(default=<literal>)`."""
    for node in ast.walk(source_tree(relative)):
        if not (isinstance(node, ast.ClassDef) and node.name == class_name):
            continue
        for item in node.body:
            if isinstance(item, ast.AnnAssign) and isinstance(item.target, ast.Name) and item.target.id == field:
                value = item.value
                if isinstance(value, ast.Call):
                    keyword = next((k for k in value.keywords if k.arg == "default"), None)
                    assert keyword is not None, f"{class_name}.{field} has no literal default"
                    value = keyword.value
                return ast.literal_eval(value)
    raise AssertionError(f"{relative} has no {class_name}.{field}")


def review_bar() -> tuple[int, int]:
    """The first review's bar and the drop per repair, from impl-review.yml's threshold formula."""
    workflow = read(ROOT / ".github" / "workflows" / "impl-review.yml")
    match = re.search(r"THRESHOLD=\$\(\(\s*(\d+)\s*-\s*ATTEMPT_COUNT\s*\*\s*(\d+)\s*\)\)", workflow)
    assert match, "impl-review.yml no longer computes THRESHOLD as <start> - ATTEMPT_COUNT * <step>"
    return int(match.group(1)), int(match.group(2))


def review_floor() -> int:
    """The lowest bar, from the clamp impl-review.yml applies right after the threshold formula."""
    workflow = read(ROOT / ".github" / "workflows" / "impl-review.yml")
    floors = set(re.findall(r'if \[ "\$THRESHOLD" -lt (\d+) \]; then THRESHOLD=(\d+); fi', workflow))
    assert floors, "impl-review.yml no longer clamps THRESHOLD to a floor"
    assert len(floors) == 1, f"impl-review.yml clamps THRESHOLD to more than one floor: {sorted(floors)}"
    ((below, floor),) = floors
    assert below == floor, f"impl-review.yml clamps below {below} to {floor}"
    return int(floor)


def model_display_name(model_id: str) -> str:
    """`claude-haiku-5-5` as the README names it: `Claude Haiku 5.5`."""
    words = model_id.split("-")
    name = [w.capitalize() for w in words if not w.isdigit()]
    version = ".".join(w for w in words if w.isdigit())
    return " ".join([*name, version])


def mcp_tool_count() -> int:
    return len(re.findall(r"^@mcp_server\.tool\(", read(ROOT / "api" / "mcp" / "server.py"), re.MULTILINE))


@cache
def tracked_files() -> frozenset[str]:
    listing = subprocess.run(
        ["git", "ls-files", "-z"], cwd=ROOT, capture_output=True, check=True, text=True
    ).stdout.split("\0")
    return frozenset(path for path in listing if path)


# --- the sources themselves agree ---------------------------------------------------------------


def test_the_bar_in_the_workflow_is_the_one_in_core_constants():
    start, step = review_bar()
    assert start == QUALITY_THRESHOLD_APPROVAL
    assert (QUALITY_THRESHOLD_APPROVAL - QUALITY_THRESHOLD_FINAL_APPROVAL) % step == 0
    assert review_floor() == QUALITY_THRESHOLD_FINAL_APPROVAL


# --- (a) links ----------------------------------------------------------------------------------


def _links(path: Path) -> list[str]:
    # `[text](target)` and `![alt](target)`, the target up to a space or the closing bracket.
    return re.findall(r"\]\(([^)\s]+)\)", read(path))


def _slug(heading: str) -> str:
    """GitHub's anchor for a heading: lowercase, punctuation dropped, spaces to hyphens."""
    text = re.sub(r"[`*_\[\]()]", "", heading).strip().lower()
    text = re.sub(r"[^\w\- ]", "", text)
    return text.replace(" ", "-")


@pytest.mark.parametrize("path", LINKED_DOCS, ids=lambda p: p.name)
def test_every_relative_link_resolves_to_a_tracked_file(path: Path):
    tracked = tracked_files()
    broken = []
    for target in _links(path):
        if re.match(r"^[a-z]+:", target) or target.startswith("#"):
            continue
        relative = (path.parent / target.split("#", 1)[0]).resolve().relative_to(ROOT).as_posix()
        is_file = relative in tracked
        is_dir = any(file.startswith(f"{relative.rstrip('/')}/") for file in tracked)
        if not (is_file or is_dir):
            broken.append(target)
    assert not broken, f"{path.name} links to untracked paths: {broken}"


@pytest.mark.parametrize("path", LINKED_DOCS, ids=lambda p: p.name)
def test_every_in_page_anchor_names_a_heading(path: Path):
    text = read(path)
    slugs = {_slug(line.lstrip("#")) for line in text.splitlines() if line.startswith("#")}
    missing = [t for t in _links(path) if t.startswith("#") and t[1:] not in slugs]
    assert not missing, f"{path.name} links to anchors without a heading: {missing}"


# --- (b) claims ---------------------------------------------------------------------------------


def test_highlights_state_the_rubric_and_the_bar():
    highlights = section(read(README), "Engineering highlights")
    start, step = review_bar()
    assert near(highlights, str(len(CRITERIA)), "criteri"), f"the rubric has {len(CRITERIA)} criteria"
    assert near(highlights, str(start), "starts at"), f"the first review's bar starts at {start}"
    assert near(highlights, str(step), "points per repair"), f"the bar drops {step} points per repair"


def test_highlights_state_the_pipeline_bounds():
    highlights = section(read(README), "Engineering highlights")
    attempts = field_default("agents/anyplot/settings.py", "AgentSettings", "max_attempts")
    reviews = module_constant("agents/anyplot/pipeline.py", "MAX_REVIEWS")
    assert isinstance(attempts, int) and isinstance(reviews, int)
    assert near(highlights, NUMBER_WORDS[attempts - 1], "repair round"), f"{attempts - 1} repair round(s) by default"
    assert near(highlights, NUMBER_WORDS[reviews], "reviews"), f"at most {reviews} reviews"


def test_highlights_state_the_session_idle_time():
    highlights = section(read(README), "Engineering highlights")
    idle = field_default("agents/anyplot/settings.py", "AgentSettings", "session_idle_s")
    assert isinstance(idle, int) and idle % 3600 == 0, "the idle time is no longer whole hours: reword the claim"
    hours = idle // 3600
    phrase = "an hour" if hours == 1 else f"{NUMBER_WORDS[hours]} hours"
    assert near(highlights, phrase, "idle"), f"sessions are dropped after {phrase} idle"


def test_architecture_names_the_default_model():
    architecture = section(read(README), "Architecture")
    model = field_default("agents/anyplot/settings.py", "AgentSettings", "model")
    assert isinstance(model, str)
    assert model_display_name(model) in architecture, f"the agents run on {model_display_name(model)}"


def test_the_intro_counts_the_registry_libraries():
    intro = read(README).split("\n## ", 1)[0]
    assert near(intro, str(len(LIBRARIES_METADATA)), "plotting librar"), (
        f"the registry has {len(LIBRARIES_METADATA)} libraries"
    )


def test_about_page_and_its_bot_copy_state_the_rubric_bar_and_mcp_tools():
    start, step = review_bar()
    floor = review_floor()
    repairs = (start - floor) // step
    for name, text in (("AboutPage.tsx", read(ABOUT_PAGE)), ("seo.py", read(SEO))):
        assert near(text, f"{sum(CRITERIA.values())}-point", "rubric"), f"{name}: the rubric's points"
        assert near(text, str(len(CRITERIA)), "criteria"), f"{name}: the rubric's criteria"
        assert near(text, str(start), "first review needs"), f"{name}: the first review's bar"
        assert near(text, NUMBER_WORDS[repairs], "times"), f"{name}: {repairs} repairs"
        assert near(text, str(step), "points per repair"), f"{name}: the bar drops {step} points per repair"
        assert near(text, str(floor), "at the last review"), f"{name}: the last review's bar is {floor}"
        # 5, not 3: seo.py splits "Six tools" over two string literals (`Six " "tools`).
        assert near(text, NUMBER_WORDS[mcp_tool_count()], "tools", window=5), f"{name}: {mcp_tool_count()} MCP tools"


def test_about_page_and_its_bot_copy_claim_no_regeneration_on_a_library_release():
    """No workflow runs on a library's release: a nightly job regenerates the oldest implementations."""
    workflow = read(ROOT / ".github" / "workflows" / "daily-regen.yml")
    triggers = workflow.split("\non:\n", 1)[1].split("\n\n", 1)[0]
    cron = re.search(r"^\s+schedule:\s*\n\s+- cron: '([^']+)'", triggers, re.MULTILINE)
    assert cron, "daily-regen.yml no longer runs on a schedule"
    assert cron.group(1).split()[2:] == ["*", "*", "*"], f"daily-regen.yml no longer runs every day: {cron.group(1)}"
    for name, text in (("AboutPage.tsx", read(ABOUT_PAGE)), ("seo.py", read(SEO))):
        prose = collapse(text).lower()
        assert "ships a new release" not in prose, f"{name}: no workflow re-runs the pipeline on a library release"
        assert "every night a job regenerates the oldest implementations" in prose, f"{name}: the nightly job"


def test_about_page_and_its_bot_copy_name_only_the_checks_a_workflow_runs():
    """Before the review, impl-generate.yml requires both renders and impl-review.yml gates the canvas size."""
    generate = read(ROOT / ".github" / "workflows" / "impl-generate.yml")
    review = read(ROOT / ".github" / "workflows" / "impl-review.yml")
    assert "implementation failed to produce both theme renders" in generate, (
        "impl-generate.yml no longer stops when the code produced no render"
    )
    assert "- name: Canvas dimension gate" in review, "impl-review.yml no longer gates the canvas size"
    # core/canvas.py has a blank-image check (AR-04), but no workflow calls it.
    workflows = sorted((ROOT / ".github" / "workflows").glob("*.yml"))
    blank_checked = any(re.search(r"check_blank|is_blank_png", read(path)) for path in workflows)
    for name, text in (("AboutPage.tsx", read(ABOUT_PAGE)), ("seo.py", about_bot_body())):
        prose = collapse(text).lower()
        assert "automated checks come first: the code runs, the canvas has its size." in prose, f"{name}: the checks"
        if not blank_checked:
            # A word of its own: `target="_blank"` is no claim.
            assert not re.search(r"\bblank\b", prose), f"{name}: no workflow checks for a blank image"
    # The README's pipeline step lists the same checks. Only that sentence: the quality bar's "a blank image ...
    # scores 0" is a rule of the rubric the reviewer applies, not a check a workflow runs.
    step = re.search(r"^4\. \*\*Review\.\*\*(.*?)^5\. ", read(README), re.MULTILINE | re.DOTALL)
    assert step, "README.md no longer has the pipeline's review step"
    checks = collapse(step.group(1)).split(" An AI reviewer ", 1)[0]
    assert "first runs automated checks:" in checks, "README.md: the review step no longer lists its automated checks"
    if not blank_checked:
        assert not re.search(r"\bblank\b", checks, re.IGNORECASE), "README.md: no workflow checks for a blank image"


def test_about_page_and_its_bot_copy_state_the_owners_year_as_the_readme_does():
    match = re.search(r"since (\d{4}) I've built", collapse(section(read(README), "How I build anyplot")))
    assert match, "README.md 'How I build anyplot' no longer says since when the owner has built data systems"
    for name, text in (("AboutPage.tsx", read(ABOUT_PAGE)), ("seo.py", read(SEO))):
        assert near(text, match.group(1), "since"), f"{name}: since {match.group(1)}, as the README says"


# English month names, fixed: `calendar.month_name` follows the locale.
_MONTHS = (
    "January",
    "February",
    "March",
    "April",
    "May",
    "June",
    "July",
    "August",
    "September",
    "October",
    "November",
    "December",
)


def test_about_page_and_its_bot_copy_date_the_rename_as_the_changelog_does():
    """The origin's month of the rename to anyplot.ai is the month of the CHANGELOG's relaunch release."""
    heading = re.search(
        r"^## \[[\d.]+\] — (\d{4})-(\d{2})-\d{2} — anyplot\.ai Relaunch$", read(ROOT / "CHANGELOG.md"), re.MULTILINE
    )
    assert heading, "CHANGELOG.md no longer has the release that relaunched the site as anyplot.ai"
    year, month = heading.group(1), _MONTHS[int(heading.group(2)) - 1]
    # Without case: the bot copy starts the sentence with a capital, the page does not.
    phrase = f"in {month} {year} it became anyplot.ai.".lower()
    for name, text in (("AboutPage.tsx", read(ABOUT_PAGE)), ("seo.py", about_bot_body())):
        assert phrase in collapse(text).lower(), (
            f"{name}: the origin dates the rename to {month} {year}, as CHANGELOG.md does"
        )


def test_about_page_and_its_bot_copy_date_the_start_as_the_readme_does():
    """The origin, and the builder's own account, start in the month the README counts the owner's merged pull
    requests from.

    Text held to text, so the two cannot drift apart; neither proves the date, which is the first commit's.
    """
    since = re.search(r"Since (\w+ \d{4}), more than", collapse(section(read(README), "How I build anyplot")))
    assert since, "README.md 'How I build anyplot' no longer says since when the owner's pull requests have merged"
    for phrase in (
        f"it started in {since.group(1)} as pyplots.ai",
        f"I have built it alone since {since.group(1)},",
        f"I have built it with AI agents since {since.group(1)}.",
    ):
        for name, text in (("AboutPage.tsx", read(ABOUT_PAGE)), ("seo.py", about_bot_body())):
            assert phrase.lower() in collapse(text).lower(), f"{name}: '{phrase}', as the README says"


def test_about_page_and_its_bot_copy_name_the_default_model():
    """The stack names the data assistant's model, as the README's architecture does."""
    model = field_default("agents/anyplot/settings.py", "AgentSettings", "model")
    assert isinstance(model, str)
    for name, text in (("AboutPage.tsx", read(ABOUT_PAGE)), ("seo.py", about_bot_body())):
        assert model_display_name(model) in collapse(text), (
            f"{name}: the data assistant runs on {model_display_name(model)}"
        )


# A GitHub address of a file on main, as the About page and its bot copy write it, with its heading anchor.
_GITHUB_BLOB = re.compile(
    r"(?:\$\{GITHUB_URL\}|https://github\.com/MarkusNeusinger/anyplot)/blob/main/([\w./-]+)(#[\w-]+)?"
)


def test_about_page_links_name_tracked_files_and_existing_headings():
    """A renamed heading or a moved doc fails here instead of breaking a link on the site."""
    tracked = tracked_files()
    for name, text in (("AboutPage.tsx", read(ABOUT_PAGE)), ("seo.py", read(SEO))):
        links = set(_GITHUB_BLOB.findall(text))
        # The three the "how it is built" section links, so this test cannot pass on a page that lost them.
        for expected in (
            ("README.md", "#how-i-build-anyplot"),
            ("README.md", "#engineering-highlights"),
            ("docs/concepts/ai-workflow.md", ""),
        ):
            assert expected in links, f"{name} no longer links {''.join(expected)}"
        for path, anchor in links:
            assert path in tracked, f"{name} links {path}, which is not a tracked file"
            if anchor:
                markdown = read(ROOT / path)
                slugs = {_slug(line.lstrip("#")) for line in markdown.splitlines() if line.startswith("#")}
                assert anchor[1:] in slugs, f"{name} links {path}{anchor}, which names no heading there"


def test_the_workflow_page_floor_on_recorded_decisions_holds():
    page = read(WORKFLOW_PAGE)
    match = re.search(r"more than (\d+) times", collapse(page))
    assert match, "ai-workflow.md no longer states its floor on recorded owner decisions"
    recorded = len(
        re.findall(r"owner (?:decision|rule|request)", read(ROOT / "docs" / "concepts" / "agent-network.md"), re.I)
    )
    assert recorded > int(match.group(1)), f"agent-network.md names {recorded} owner decisions, rules or requests"


def test_merged_pull_request_claims_are_sane_floors():
    """The owner's merged pull requests, stated as a floor that the recorded snapshot bounds (module docstring)."""
    count, taken = MERGED_PRS_SNAPSHOT
    # The claim itself, whatever precedes the number; "more than" and "over" are the floors.
    claim = re.compile(r"(\S+ \S+ )?(\d[\d,]*) pull requests from my account have merged", re.IGNORECASE)
    for path in LINKED_DOCS:
        matches = list(claim.finditer(collapse(read(path))))
        assert matches, f"{path.name} no longer states the merged pull requests from the owner's account"
        for match in matches:
            assert re.search(r"(?:more than|over) $", match.group(1) or "", re.IGNORECASE), (
                f"{path.name}: '{match.group(0)}' is no floor; write 'more than N' or 'over N'"
            )
            floor = int(match.group(2).replace(",", ""))
            assert floor % PR_FLOOR_STEP == 0, f"{path.name}: the floor {floor} is no multiple of {PR_FLOOR_STEP}"
            assert floor < count, f"{path.name}: the floor {floor} overclaims the {count} counted on {taken}"
            assert count - floor <= PR_FLOOR_STEP, (
                f"{path.name}: the floor {floor} is stale against the {count} counted on {taken}; "
                f"raise it to {(count - 1) // PR_FLOOR_STEP * PR_FLOOR_STEP}"
            )
