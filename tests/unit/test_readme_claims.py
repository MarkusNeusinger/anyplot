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

The releases beside it are counted exactly, offline: the README's "N releases have shipped" must equal the version
headings of `CHANGELOG.md`, so cutting a release fails this test until the same release branch raises the number
(step 4 again).
"""

from __future__ import annotations

import ast
import datetime
import re
import subprocess
from functools import cache
from pathlib import Path

import pytest
import yaml

from core.constants import LIBRARIES_METADATA, QUALITY_THRESHOLD_APPROVAL, QUALITY_THRESHOLD_FINAL_APPROVAL
from core.defects import CRITERIA


ROOT = Path(__file__).resolve().parents[2]
README = ROOT / "README.md"
WORKFLOW_PAGE = ROOT / "docs" / "concepts" / "ai-workflow.md"
ABOUT_PAGE = ROOT / "app" / "src" / "pages" / "AboutPage.tsx"
# The words and numbers of the About page's figures (pipeline, rubric, timeline).
ABOUT_FIGURES = ROOT / "app" / "src" / "sections" / "about" / "figureData.ts"
SEO = ROOT / "api" / "routers" / "seo.py"
STYLE_GUIDE = ROOT / "docs" / "reference" / "style-guide.md"
AGENT_INTRO = ROOT / "app" / "src" / "sections" / "agent-chat" / "AgentIntro.tsx"
LINKED_DOCS = (README, WORKFLOW_PAGE)
CHAT_SECTION = "Use with my data (agent chat)"
GATE = "automation/scripts/regen_gate.py"

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


def annotated_kind(relative: str, name: str) -> tuple[str, dict[str, object]]:
    """The marker of a module-level `NAME = Annotated[T, Kind(...)]`: `Kind` (`Header`, `Path`, ...) and its literal
    keyword arguments.

    `module_constant` cannot read these: `Annotated[...]` is no literal.
    """
    for node in source_tree(relative).body:
        if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == name for t in node.targets):
            value = node.value
            if isinstance(value, ast.Subscript) and isinstance(value.slice, ast.Tuple):
                marker = value.slice.elts[-1]
                if isinstance(marker, ast.Call) and isinstance(marker.func, ast.Name):
                    literals: dict[str, object] = {
                        k.arg: k.value.value for k in marker.keywords if k.arg and isinstance(k.value, ast.Constant)
                    }
                    return marker.func.id, literals
            raise AssertionError(f"{relative}: {name} is no Annotated[T, Kind(...)]")
    raise AssertionError(f"{relative} has no module constant {name}")


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


def workflow_steps(name: str) -> list[dict[str, object]]:
    """Every step of a workflow under .github/workflows/, job after job, in the order the file lists them."""
    workflow = yaml.safe_load(read(ROOT / ".github" / "workflows" / name))
    return [step for job in workflow["jobs"].values() for step in job.get("steps", [])]


def step_names(name: str) -> list[object]:
    return [step.get("name") for step in workflow_steps(name)]


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


def test_the_chat_section_states_the_pipeline_bounds():
    """The chat's run bounds stand in the README's section on the chat, in its first bullet."""
    chat = section(read(README), CHAT_SECTION)
    attempts = field_default("agents/anyplot/settings.py", "AgentSettings", "max_attempts")
    reviews = module_constant("agents/anyplot/pipeline.py", "MAX_REVIEWS")
    assert isinstance(attempts, int) and isinstance(reviews, int)
    assert near(chat, NUMBER_WORDS[attempts - 1], "repair round"), f"{attempts - 1} repair round(s) by default"
    assert near(chat, NUMBER_WORDS[reviews], "reviews"), f"at most {reviews} reviews"


def test_highlights_state_the_session_idle_time():
    highlights = section(read(README), "Engineering highlights")
    idle = field_default("agents/anyplot/settings.py", "AgentSettings", "session_idle_s")
    assert isinstance(idle, int) and idle % 3600 == 0, "the idle time is no longer whole hours: reword the claim"
    hours = idle // 3600
    phrase = "an hour" if hours == 1 else f"{NUMBER_WORDS[hours]} hours"
    assert near(highlights, phrase, "idle"), f"sessions are dropped after {phrase} idle"


def test_highlights_state_the_patch_rule_not_an_absolute():
    """ "No generated plot is patched by hand" does not hold: the palette swap of May 2026 edited the plots' code
    catalogue-wide. The highlight states the rule a wrong plot follows instead.

    Nor does a fix to a prompt or a spec fix every plot it governs at once: it reaches a plot when that plot is next
    regenerated, which for a pair far back in the nightly queue can be a long way off.
    """
    highlights = collapse(section(read(README), "Engineering highlights"))
    assert "A wrong plot is fixed in its spec or in a rule and then regenerated, not patched by hand." in highlights, (
        "README.md: the review-loop highlight no longer states how a wrong plot is fixed"
    )
    assert "No generated plot is patched by hand" not in highlights, "README.md: the palette swap was a patch by hand"
    assert "A fix to a prompt or a spec reaches every plot it governs at that plot's next regeneration." in (
        highlights
    ), "README.md: the review-loop highlight no longer says when a fix reaches a plot"
    assert "fixes every plot it governs" not in highlights, "README.md: a fix reaches a plot at its next regeneration"


def test_highlights_put_the_public_chats_session_id_in_a_header():
    """The public chat reads its session id from a header, and no public route takes it from the path or the query.

    The admin chat's routes carry it in their path, which is why the highlight names the public chat; "the session id
    never appears in a URL" holds only once the admin chat's id leaves the path too.
    """
    public, admin = "api/routers/agent_public.py", "api/routers/agent.py"
    kind, keywords = annotated_kind(public, "SessionId")
    assert (kind, keywords.get("alias")) == ("Header", "X-Anyplot-Session"), f"{public}: SessionId is a {kind}"
    for node in ast.walk(source_tree(public)):
        if isinstance(node, ast.arg) and node.arg == "sid":
            assert isinstance(node.annotation, ast.Name) and node.annotation.id == "SessionId", (
                f"{public}: a function takes `sid` as something other than the SessionId header"
            )
    routes = re.findall(r'^@router\.\w+\("([^"]*)"', read(ROOT / public), re.MULTILINE)
    assert routes, f'{public} no longer declares its routes as @router.<method>("<path>")'
    assert not [route for route in routes if "sid" in route], f"{public}: a route carries the session id in its path"
    highlights = collapse(section(read(README), "Engineering highlights"))
    assert "the public chat's session id travels in a header, not in a URL" in highlights, (
        "README.md: the privacy highlight no longer says where the public chat's session id travels"
    )
    # The AI workflow page tells the same change as an example of a question that mattered.
    workflow = collapse(read(WORKFLOW_PAGE))
    assert "moved the public chat's session id out of its URLs" in workflow, (
        "ai-workflow.md: the security example no longer says that the public chat's session id left its URLs"
    )
    if annotated_kind(admin, "SessionId")[0] == "Path":
        assert "never appears in a URL" not in highlights, f"README.md: {admin} carries the session id in its path"
        assert "out of every URL" not in workflow, f"ai-workflow.md: {admin} carries the session id in its path"


def test_the_decision_count_is_the_number_of_highlights():
    """ "Six decisions I made" over the highlights and "Six of those decisions are below" count the highlights."""
    highlights = section(read(README), "Engineering highlights")
    bullets = len(re.findall(r"^- \*\*", highlights, re.MULTILINE))
    word = NUMBER_WORDS[bullets].capitalize()
    assert f"{word} decisions I made" in collapse(highlights), f"README.md: the highlights list {bullets} decisions"
    how = collapse(section(read(README), "How I build anyplot"))
    assert f"{word} of those decisions are [below](#engineering-highlights)" in how, (
        f"README.md 'How I build anyplot': {bullets} decisions are below, as the highlights list them"
    )


def test_highlights_name_the_model_every_pipeline_review_runs_on():
    """ "Pipeline reviews run on Opus": impl-review.yml's `review_model` input defaults to it, a review dispatched
    without one (generation, repair, the nightly resume) falls back to it, and no other workflow passes a review
    model. Only a manual dispatch can name another; the chat's own reviewer is no pipeline review."""
    review = read(ROOT / ".github" / "workflows" / "impl-review.yml")
    workflow = yaml.safe_load(review)
    triggers = workflow.get("on", workflow.get(True))  # YAML 1.1 reads the key `on` as true
    default = triggers["workflow_dispatch"]["inputs"]["review_model"]["default"]
    fallback = re.search(r'REVIEW_MODEL_ALIAS="\$\{REVIEW_MODEL_INPUT:-\$\{REVIEW_MODEL_PAYLOAD:-(\w+)\}\}"', review)
    assert fallback, "impl-review.yml no longer falls back to a review model when a dispatch names none"
    assert fallback.group(1) == default, (
        f"impl-review.yml: a review dispatched without a model runs on {fallback.group(1)}, the input's default is "
        f"{default}"
    )
    passing = sorted(
        path.name
        for path in (ROOT / ".github" / "workflows").glob("*.yml")
        if path.name != "impl-review.yml" and re.search(r"review_model\]?=", read(path))
    )
    assert not passing, (
        f"{passing} dispatch impl-review.yml with a review model: not every pipeline review is {default}"
    )
    highlights = section(read(README), "Engineering highlights")
    assert near(highlights, default.capitalize(), "reviews run on"), f"README.md: pipeline reviews run on {default}"


def test_highlights_state_the_regen_gates_tolerance_and_adapt_route():
    """The gate's "a score at most a point lower" is the tolerance of its below-tolerance keep, and the code
    conversion that "passes on an unchanged render instead" is the adapt route, which merges under its own code
    and to which the tolerance never applies."""
    source = read(ROOT / GATE)
    tolerances = set(re.findall(r"\bscore < prev_rescored - (\d+):", source))
    assert len(tolerances) == 1, f"{GATE}: the below-tolerance keep compares against {sorted(tolerances)}"
    points = int(tolerances.pop())
    phrase = "a point" if points == 1 else f"{NUMBER_WORDS[points]} points"
    highlights = collapse(section(read(README), "Engineering highlights"))
    assert f"a score at most {phrase} lower" in highlights, (
        f"README.md: the gate keeps a score more than {phrase} lower"
    )
    codes = module_constant(GATE, "REASON_CODES")
    assert isinstance(codes, tuple) and "adapt_identity" in codes, (
        f"{GATE} no longer merges a conversion on render identity: the README's adapt route has to go"
    )
    assert "a code conversion for the chat passes on an unchanged render instead" in highlights, (
        "README.md: the gate highlight no longer names the adapt route, which merges without the tolerance"
    )


def test_highlights_state_the_render_hash_stop():
    """Generation and repair stage the hash in a step of its own that fails the run; the review stops on the hash
    before the reviewer runs; and a regeneration that stops keeps the live implementation under one of the gate's two
    render codes, one for a hash that does not match and one for a hash that is missing or unreadable."""
    for name in ("impl-generate.yml", "impl-repair.yml"):
        staged = [step for step in workflow_steps(name) if step.get("name") == "Stage the render hash"]
        assert len(staged) == 1, f"{name} no longer stages the render hash in a step of its own"
        assert not staged[0].get("continue-on-error"), f"{name}: a failed hash write no longer fails the run"
    names = step_names("impl-review.yml")
    for name in ("Stop on the render hash", "Run AI Quality Review"):
        assert name in names, f"impl-review.yml has no step '{name}'"
    assert names.index("Stop on the render hash") < names.index("Run AI Quality Review"), (
        "impl-review.yml: the render hash no longer stops the review before the reviewer runs"
    )
    codes = module_constant(GATE, "REASON_CODES")
    source = read(ROOT / GATE)
    for code in ("render_mismatch", "render_unverified"):
        assert isinstance(codes, tuple) and code in codes, f"{GATE} has no reason code {code}"
        assert re.search(rf'GateResult\(KEEP, "[^"]*", "{code}"\)', source), f"{GATE}: {code} no longer keeps"
    highlights = collapse(section(read(README), "Engineering highlights"))
    assert (
        "a review whose hash is missing or doesn't match the code at the pull request's head stops before it scores; "
        "a regeneration then keeps the live version"
    ) in highlights, "README.md: the render-hash highlight no longer says what stops a review"


def test_highlights_say_the_figure_check_counts_only_while_it_defaults_to_log():
    """ "It ships counting only" holds while `number_provenance` defaults to `log`, which logs every reply and asks
    for none again or withholds it; the day `enforce` becomes the default, the bullet fails here until it follows."""
    default = field_default("agents/anyplot/settings.py", "AgentSettings", "number_provenance")
    highlights = collapse(section(read(README), "Engineering highlights"))
    assert ("It ships counting only" in highlights) == (default == "log"), (
        f"README.md: the figure check defaults to {default!r}, and the highlight says it ships counting only or not"
    )


def test_highlights_say_every_release_runs_the_chats_evals():
    """Step 6 of the release procedure always runs the chat's prep and scope evals before step 7 opens the release
    pull request, and gives the regression that only a sibling pull request's eval caught as its reason."""
    release = read(ROOT / "agentic" / "commands" / "release.md")
    step = re.search(r"^6\. \*\*Run the agent evals\*\*(.*?)^7\. ", release, re.MULTILINE | re.DOTALL)
    assert step, "release.md no longer runs the agent evals as step 6, before the release pull request"
    text = collapse(step.group(1))
    assert "**Always:**" in text, "release.md step 6 no longer names the evals that always run"
    always = text.split("**Always:**", 1)[1].split("**When ", 1)[0]
    for suite in ("agents.evals.prep", "agents.evals.scope"):
        assert suite in always, f"release.md step 6 no longer always runs {suite}"
    assert "only because a sibling PR ran its eval" in text, "release.md step 6 no longer gives its reason"
    highlights = collapse(section(read(README), "Engineering highlights"))
    assert "Every release runs the chat's evals first" in highlights, "README.md: every release runs the evals"
    assert "only because another pull request happened to run them" in highlights, "README.md: the evals' reason"


def test_the_review_keeps_the_stored_score_out_of_its_working_tree_and_its_prompt():
    """The README's review step, the About page and its crawler copy say what keeps a reviewer from an earlier score:
    impl-review.yml hides the stored review before the reviewer runs, and its prompt carries no stored score.

    Not "blind to any earlier score": the branch history and the pull request stay reachable to a reviewer that goes
    looking, and nothing mechanical closes those (docs/workflows/overview.md).
    """
    names = step_names("impl-review.yml")
    for name in ("Hide the previous review", "Run AI Quality Review"):
        assert name in names, f"impl-review.yml has no step '{name}'"
    assert names.index("Hide the previous review") < names.index("Run AI Quality Review"), (
        "impl-review.yml: the stored review is no longer hidden before the reviewer runs"
    )
    review = next(step for step in workflow_steps("impl-review.yml") if step.get("name") == "Run AI Quality Review")
    inputs = review.get("with")
    prompt = inputs.get("prompt") if isinstance(inputs, dict) else None
    assert isinstance(prompt, str), "impl-review.yml: the review step no longer passes its prompt as `with: prompt`"
    assert "PREVIOUS_SCORE" not in prompt and "prev_stored" not in prompt, "impl-review.yml: the prompt has a score"
    step = re.search(r"^4\. \*\*Review\.\*\*(.*?)^5\. ", read(README), re.MULTILINE | re.DOTALL)
    assert step, "README.md no longer has the pipeline's review step"
    for name, text in (("README.md", step.group(1)), ("AboutPage.tsx", read(ABOUT_PAGE)), ("seo.py", about_bot_body())):
        prose = collapse(text)
        assert "with the stored score kept out of its working tree and its prompt" in prose, (
            f"{name}: the review no longer says where the stored score is kept out"
        )
        assert "blind to any earlier score" not in prose, f"{name}: the review is not blind; see the docstring"


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
    # The pipeline diagram writes both in digits, and so does the sentence on who set the rubric. On the page the
    # diagram's words live in the figures' data module, each detail in one string with its action. The test reads
    # the steps' own entries there, so a comment in that file that quotes a detail cannot stand in for the figure.
    steps = {entry["step"]: entry.get("does") for entry in _figure_entries("PIPELINE_STEPS")}
    criteria, repairs_done = f"ai scores ({len(CRITERIA)} criteria)", f"ai repairs (up to {repairs} times)"
    assert steps.get("review") == criteria, f"figureData.ts: the review step reads {steps.get('review')!r}"
    assert steps.get("fix") == repairs_done, f"figureData.ts: the fix step reads {steps.get('fix')!r}"
    bot = collapse(about_bot_body()).lower()
    assert criteria in bot, "seo.py: the diagram's criteria"
    assert repairs_done in bot, "seo.py: the diagram's repairs"
    for name, text in (("AboutPage.tsx", read(ABOUT_PAGE)), ("seo.py", about_bot_body())):
        assert f"ai helped turn it into {len(CRITERIA)} criteria and their points." in collapse(text).lower(), (
            f"{name}: the rubric has {len(CRITERIA)} criteria"
        )


def test_about_page_rubric_bar_has_the_points_of_the_quality_criteria():
    """The rubric bar's six parts are the point table of prompts/quality-criteria.md, in its order.

    The page names a part as its review section does ("design" for Design Excellence), so a name must be the table's
    category or its first word. The caption's total and criteria come from the criteria registry.
    """
    criteria_doc = read(ROOT / "prompts" / "quality-criteria.md")
    table = criteria_doc[criteria_doc.index("### Point Distribution") :].split("**Total**", 1)[0]
    categories = [(name, int(points)) for name, points in re.findall(r"^\| ([A-Z][\w ]+?) \| (\d+) \|", table, re.M)]
    figures = read(ABOUT_FIGURES)
    block = figures[figures.index("export const RUBRIC_PARTS") :].split("];", 1)[0]
    parts = [(name, int(points)) for name, points in re.findall(r"\['([a-z ]+)', (\d+)\]", block)]
    assert len(parts) == len(categories) == 6, f"figureData.ts: {parts}; quality-criteria.md: {categories}"
    for (name, points), (category, table_points) in zip(parts, categories, strict=True):
        assert category.lower() == name or category.lower().startswith(f"{name} "), (
            f"figureData.ts: '{name}' stands where quality-criteria.md has '{category}'"
        )
        assert points == table_points, f"figureData.ts: {name} has {table_points} points, not {points}"
    total = sum(table_points for _, table_points in categories)
    assert total == sum(CRITERIA.values()), "quality-criteria.md: the point table and the criteria disagree"
    assert f"'// rubric · {total} points · {len(CRITERIA)} criteria'" in figures, (
        f"figureData.ts: the rubric's caption says {total} points and {len(CRITERIA)} criteria"
    )


def _figure_entries(name: str) -> list[dict[str, str]]:
    """The entries of the array `name` in figureData.ts, each written `{ key: '...', ... }`, as dicts."""
    figures = collapse(read(ABOUT_FIGURES))
    block = figures[figures.index(f"export const {name}") :].split("];", 1)[0]
    return [dict(re.findall(r"(\w+): '([^']*)'", entry)) for entry in re.findall(r"\{([^{}]*)\}", block)]


def _origin_events() -> list[dict[str, str]]:
    """The origin timeline's points as figureData.ts writes them: `{ when: '...', version: '...', what: '...' }`."""
    return _figure_entries("ORIGIN_EVENTS")


def test_about_page_timeline_dates_each_release_as_the_changelog_does():
    """Each release on the origin timeline stands in CHANGELOG.md under its version and date, and the first is the
    oldest version heading, which is what makes it the first GitHub release."""
    headings = re.findall(r"^## \[([\d.]+)\] — (\d{4}-\d{2}-\d{2}) — (.+)$", read(ROOT / "CHANGELOG.md"), re.M)
    dated = {version: (date, title) for version, date, title in headings}
    releases = [event for event in _origin_events() if "version" in event]
    assert len(releases) == 5, f"figureData.ts: the timeline has {len(releases)} releases, not 5"

    def squash(text: str) -> str:
        return re.sub(r"[^a-z0-9&/]", "", text.lower())

    changelog = read(ROOT / "CHANGELOG.md")
    for event in releases:
        assert event["version"] in dated, f"figureData.ts: CHANGELOG.md has no release {event['version']}"
        date, title = dated[event["version"]]
        assert event["when"] == date, f"figureData.ts: {event['version']} came out on {date}, not {event['when']}"
        if event["what"] == "use with my data":
            # The release is titled "Your data"; its notes open with the page the label names.
            notes = changelog.split(f"## [{event['version']}]", 1)[1].split("\n## [", 1)[0]
            first_entry = next(line for line in notes.splitlines() if line.startswith("- **"))
            assert f'"{event["what"]}"' in first_entry, f"CHANGELOG.md: {event['version']} does not open with it"
        elif event["what"] != "first github release":
            # "julia & javascript · 15 libraries" in "Julia & JavaScript, 15 libraries & the Imprint palette".
            for part in event["what"].split(" · "):
                assert squash(part) in squash(title), f"figureData.ts: '{part}' is not in the heading '{title}'"
    first = next(event for event in releases if event["what"] == "first github release")
    assert first["version"] == headings[-1][0], f"CHANGELOG.md's oldest release is {headings[-1][0]}"


def test_about_page_timeline_dates_the_start_and_the_chat_as_the_page_does():
    """The timeline's month of the start is the origin's own, and the chat's release follows its opening day."""
    events = {event["what"]: event["when"] for event in _origin_events()}
    year, month = events["pyplots.ai"].split("-")
    page = collapse(read(ABOUT_PAGE))
    assert f"it started in {_MONTHS[int(month) - 1]} {year} as pyplots.ai" in page, (
        "AboutPage.tsx: the timeline starts in the origin's month"
    )
    # The agent design document gives the day the chat opened, and the page's chat section and its crawler copy give
    # that day's month. The timeline gives the release that carries the chat, which came out the day after; a
    # release dated before the opening would be wrong.
    public = re.search(
        r"Public since (\d{4}-\d{2}-\d{2}) as an experimental page",
        read(ROOT / "docs" / "concepts" / "agent-network.md"),
    )
    assert public is not None, "agent-network.md no longer dates the chat's opening"
    opening = datetime.date.fromisoformat(public[1])
    month = f"{_MONTHS[opening.month - 1]} {opening.year}".lower()
    for name, text in (("AboutPage.tsx", page), ("seo.py", collapse(about_bot_body()))):
        assert f"open to everyone since {month}." in text.lower(), f"{name}: the chat opened to everyone in {month}"
    release = datetime.date.fromisoformat(events["use with my data"])
    assert datetime.timedelta(0) <= release - opening <= datetime.timedelta(days=7), (
        f"figureData.ts: the release of {release} does not follow the opening of {opening}"
    )


def test_about_page_and_its_bot_copy_state_the_chats_repair_bounds():
    """The chat's second paragraph bounds a run as the README's chat section does: the agents' settings and
    pipeline."""
    attempts = field_default("agents/anyplot/settings.py", "AgentSettings", "max_attempts")
    reviews = module_constant("agents/anyplot/pipeline.py", "MAX_REVIEWS")
    assert isinstance(attempts, int) and isinstance(reviews, int)
    phrase = f"one repair and {NUMBER_WORDS[reviews]} reviews at most"
    assert attempts - 1 == 1, f"a run repairs {attempts - 1} times by default: reword '{phrase}'"
    for name, text in (("AboutPage.tsx", read(ABOUT_PAGE)), ("seo.py", about_bot_body())):
        assert f"whether a repair is due: {phrase}." in collapse(text).lower(), (
            f"{name}: one repair and {reviews} reviews at most, as the agents' settings bound a run"
        )


def test_about_page_and_its_bot_copy_claim_no_regeneration_on_a_library_release():
    """No workflow runs on a library's release: a nightly job regenerates the oldest implementations."""
    workflow = read(ROOT / ".github" / "workflows" / "daily-regen.yml")
    triggers = workflow.split("\non:\n", 1)[1].split("\n\n", 1)[0]
    cron = re.search(r"^\s+schedule:\s*\n\s+- cron: '([^']+)'", triggers, re.MULTILINE)
    assert cron, "daily-regen.yml no longer runs on a schedule"
    assert cron.group(1).split()[2:] == ["*", "*", "*"], f"daily-regen.yml no longer runs every day: {cron.group(1)}"
    for name, text in (("AboutPage.tsx", read(ABOUT_PAGE)), ("seo.py", about_bot_body())):
        prose = collapse(text).lower()
        assert "ships a new release" not in prose, f"{name}: no workflow re-runs the pipeline on a library release"
        assert "every night a job regenerates the oldest implementations" in prose, f"{name}: the nightly job"


def test_about_page_and_its_bot_copy_name_only_the_checks_a_workflow_runs():
    """Before the review, impl-generate.yml requires both renders, and impl-review.yml checks that both exist and
    gates the canvas size."""
    generate = read(ROOT / ".github" / "workflows" / "impl-generate.yml")
    review = read(ROOT / ".github" / "workflows" / "impl-review.yml")
    assert "implementation failed to produce both theme renders" in generate, (
        "impl-generate.yml no longer stops when the code produced no render"
    )
    assert "- name: Verify both theme renders exist" in review, "impl-review.yml no longer checks for both renders"
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
    # The README's pipeline steps name the same checks: generation stops without both renders, and the review step
    # lists the renders and the canvas. Only those sentences: the quality bar's "a blank image ... scores 0" is a rule
    # of the rubric the reviewer applies, not a check a workflow runs.
    generation = re.search(r"^3\. \*\*Generation\.\*\*(.*?)^4\. ", read(README), re.MULTILINE | re.DOTALL)
    assert generation, "README.md no longer has the pipeline's generation step"
    assert "renders it in both themes; without both renders it stops." in collapse(generation.group(1)), (
        "README.md: the generation step no longer says that it stops without both renders"
    )
    step = re.search(r"^4\. \*\*Review\.\*\*(.*?)^5\. ", read(README), re.MULTILINE | re.DOTALL)
    assert step, "README.md no longer has the pipeline's review step"
    checks = collapse(step.group(1)).split(" An AI reviewer ", 1)[0]
    assert "first runs automated checks: both renders exist and the canvas has its target size." in checks, (
        "README.md: the review step no longer lists the renders and the canvas as its automated checks"
    )
    if not blank_checked:
        assert not re.search(r"\bblank\b", checks, re.IGNORECASE), "README.md: no workflow checks for a blank image"


def test_the_pipeline_step_says_only_the_owners_label_merges_a_spec():
    """Step 2: spec-create.yml's merge job runs on the `approved` label only when the repository owner added it."""
    workflow = yaml.safe_load(read(ROOT / ".github" / "workflows" / "spec-create.yml"))
    condition = workflow["jobs"]["merge"]["if"]
    assert "||" not in condition, "spec-create.yml's merge job no longer requires every condition of its if:"
    conditions = {part.strip() for part in condition.split("&&")}
    for required in ("github.event.label.name == 'approved'", "github.event.sender.login == github.repository_owner"):
        assert required in conditions, f"spec-create.yml's merge job no longer requires {required}"
    step = re.search(r"^2\. \*\*Specification\.\*\*(.*?)^3\. ", read(README), re.MULTILINE | re.DOTALL)
    assert step, "README.md no longer has the pipeline's specification step"
    assert (
        "I approve it on the issue; since September 2026 the merge job ignores the label from any other account."
        in collapse(step.group(1))
    ), "README.md: the specification step no longer says that only the owner's label merges a spec"


def test_about_page_and_its_bot_copy_state_the_owners_year_as_the_readme_does():
    match = re.search(r"since (\d{4}) I've built", collapse(section(read(README), "How I build anyplot")))
    assert match, "README.md 'How I build anyplot' no longer says since when the owner has built data systems"
    for name, text in (("AboutPage.tsx", read(ABOUT_PAGE)), ("seo.py", read(SEO))):
        assert near(text, match.group(1), "since"), f"{name}: since {match.group(1)}, as the README says"


def test_the_readme_introduces_the_owner_as_the_about_page_does():
    """The README's "a physicist and data analyst" is the About page's "physicist by training, senior data analyst by
    trade", and "senior" is the AI workflow page's "then senior data analyst".

    Text held to text, as the year above: neither has a source in code.
    """
    intro = collapse(section(read(README), "How I build anyplot"))
    assert "a physicist and data analyst:" in intro, (
        "README.md 'How I build anyplot' no longer names the owner's trades"
    )
    assert "working in data and AI" not in intro, "README.md: the About page names the trades, not a field"
    assert "data analyst, then senior data analyst" in collapse(read(WORKFLOW_PAGE)), (
        "ai-workflow.md 'What I bring' no longer says the owner became a senior data analyst"
    )
    for name, text in (("AboutPage.tsx", read(ABOUT_PAGE)), ("seo.py", about_bot_body())):
        assert "physicist by training, senior data analyst by trade" in collapse(text).lower(), (
            f"{name}: physicist by training, senior data analyst by trade, as the README and ai-workflow.md say"
        )


def test_the_real_data_case_names_the_lines_the_parser_finds_a_table_among():
    """The README's real-data case says pasted data works with notes, metadata or total rows around the table.

    `table_block` in the agents' parser is that rule: it finds the table among such lines and leaves them out, and its
    docstring names the three kinds. A parser that stops naming one fails here until the README follows.
    """
    intro = collapse(section(read(README), "How I build anyplot"))
    assert "pasted data has to work with notes, metadata or total rows around the table" in intro, (
        "README.md 'How I build anyplot' no longer states the rule its real-data case led to"
    )
    parser = "agents/anyplot/data/parse.py"
    functions = {node.name: node for node in source_tree(parser).body if isinstance(node, ast.FunctionDef)}
    assert "table_block" in functions, f"{parser} no longer defines table_block"
    doc = collapse(ast.get_docstring(functions["table_block"]) or "")
    for kind in ("metadata", "a note", "a total row"):
        assert kind in doc, f"{parser}: table_block no longer names {kind} among the lines around a table"


def test_about_page_and_its_bot_copy_date_the_platform_as_the_workflow_page_does():
    """The builder's platform built by hand, largely without AI, in the years the AI workflow page gives it.

    Text held to text: the platform is not in this repository.
    """
    match = re.search(
        r"from (\d{4}) to (\d{4}) I built and ran defichain-data, a platform for blockchain market data",
        collapse(read(WORKFLOW_PAGE)),
    )
    assert match, "ai-workflow.md 'What I bring' no longer dates the blockchain data platform"
    assert "largely without AI" in collapse(read(WORKFLOW_PAGE)), "ai-workflow.md: the platform was built without AI"
    phrase = f"from {match.group(1)} to {match.group(2)} I built and ran a platform for blockchain market data, "
    for name, text in (("AboutPage.tsx", read(ABOUT_PAGE)), ("seo.py", about_bot_body())):
        assert f"{phrase}largely without AI.".lower() in collapse(text).lower(), (
            f"{name}: the platform of {match.group(1)} to {match.group(2)}, as ai-workflow.md dates it"
        )


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
        f"I have built it alone and in my own time since {since.group(1)},",
    ):
        for name, text in (("AboutPage.tsx", read(ABOUT_PAGE)), ("seo.py", about_bot_body())):
            assert phrase.lower() in collapse(text).lower(), f"{name}: '{phrase}', as the README says"


def test_about_page_and_its_bot_copy_count_the_libraries_and_languages_in_the_origin():
    """The origin's "today it covers N libraries in M languages" counts the library registry."""
    libraries = len(LIBRARIES_METADATA)
    languages = len({library["language_id"] for library in LIBRARIES_METADATA})
    phrase = f"today it covers {NUMBER_WORDS[libraries]} libraries in {NUMBER_WORDS[languages]} languages"
    for name, text in (("AboutPage.tsx", read(ABOUT_PAGE)), ("seo.py", about_bot_body())):
        assert phrase in collapse(text).lower(), (
            f"{name}: the registry has {libraries} libraries in {languages} languages"
        )


def test_about_page_counts_the_palette_rounds():
    """The palette's "four rounds" are the variant rounds kept under docs/reference/palette-variants/ (v0, v1, ...).

    The crawler copy has no palette section, so only the page states it.
    """
    rounds = {
        path.split("/")[3] for path in tracked_files() if re.match(r"^docs/reference/palette-variants/v\d+/", path)
    }
    assert rounds, "docs/reference/palette-variants/ no longer keeps its rounds as v0, v1, ..."
    phrase = f"it took {NUMBER_WORDS[len(rounds)]} rounds: the colour-distance numbers"
    assert phrase in collapse(read(ABOUT_PAGE)), f"AboutPage.tsx: the palette took {len(rounds)} rounds"


def test_about_page_and_its_bot_copy_state_the_patch_coverage_target():
    """The stack's checks row names the patch-coverage target that codecov.yml sets."""
    patch = read(ROOT / "codecov.yml").split("\n    patch:\n", 1)[1].split("\n  ignore:", 1)[0]
    targets = set(re.findall(r"target: (\d+)%", patch))
    assert len(targets) == 1, f"codecov.yml sets more than one patch target, or none: {sorted(targets)}"
    (target,) = targets
    for name, text in (("AboutPage.tsx", read(ABOUT_PAGE)), ("seo.py", about_bot_body())):
        assert re.search(rf"an {target}(?: |&nbsp;)% patch-coverage target", collapse(text)), (
            f"{name}: the patch-coverage target is {target} %, as codecov.yml sets it"
        )


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
        # The three the "how it is built" section links and the chat's design document, so this test cannot pass
        # on a page that lost them.
        for expected in (
            ("README.md", "#how-i-build-anyplot"),
            ("README.md", "#engineering-highlights"),
            ("docs/concepts/ai-workflow.md", ""),
            ("docs/concepts/agent-network.md", ""),
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


def test_the_workflow_page_times_the_blank_site_as_the_readme_does():
    """The blank site of 2026-10-22 lasts as long on the AI workflow page as in the README's highlights."""
    readme = re.search(
        r"left anyplot\.ai blank for (\d+) minutes", collapse(section(read(README), "Engineering highlights"))
    )
    assert readme, "README.md's highlights no longer say how long anyplot.ai was blank"
    entry = re.search(
        r"^- \*\*2026-10-22, a blank site\.\*\*(.*?)(?=^- |\Z)", read(WORKFLOW_PAGE), re.MULTILINE | re.DOTALL
    )
    assert entry, "ai-workflow.md no longer has the entry on the blank site of 2026-10-22"
    page = re.search(r"rendered blank for about (\d+) minutes\.", collapse(entry.group(1)))
    assert page, "ai-workflow.md: the blank-site entry no longer says how long the site was blank"
    assert page.group(1) == readme.group(1), f"ai-workflow.md: {page.group(1)} minutes; README.md: {readme.group(1)}"
    assert "I noticed" not in entry.group(1), "ai-workflow.md: the entry states the outage, not when it was noticed"


def test_the_guardrails_and_the_dependabot_command_time_the_blank_site_as_the_readme_does():
    """The guardrails' incident and the Dependabot command give the blank site of 2026-10-22 the README's minutes.

    Both state how long the site was blank, never when it was noticed.
    """
    readme = re.search(
        r"left anyplot\.ai blank for (\d+) minutes", collapse(section(read(README), "Engineering highlights"))
    )
    assert readme, "README.md's highlights no longer say how long anyplot.ai was blank"
    for path in (ROOT / ".claude" / "guardrails.md", ROOT / "agentic" / "commands" / "dependabot.md"):
        text = collapse(read(path))
        minutes = set(re.findall(r"blank for about (\d+) minutes", text))
        assert minutes, f"{path.name} no longer says how long the site was blank"
        assert minutes == {readme.group(1)}, f"{path.name}: {sorted(minutes)} minutes; README.md: {readme.group(1)}"
        assert not re.search(r"\b(?:noticed about|unnoticed for about) \d+ minutes", text), (
            f"{path.name}: the incident states the outage, not when it was noticed"
        )


def test_the_readme_counts_the_releases_of_the_changelog():
    """The README's release count is the number of released versions in CHANGELOG.md (module docstring)."""
    released = len(re.findall(r"^## \[\d+\.\d+\.\d+\] — ", read(ROOT / "CHANGELOG.md"), re.MULTILINE))
    assert released, "CHANGELOG.md no longer has version headings of the form '## [X.Y.Z] — '"
    claims = re.findall(r"(\d+) releases have shipped", collapse(section(read(README), "How I build anyplot")))
    assert claims, "README.md 'How I build anyplot' no longer says how many releases have shipped"
    for claim in claims:
        assert int(claim) == released, f"README.md says {claim} releases have shipped; CHANGELOG.md has {released}"


def test_the_style_guide_keeps_a_crawler_copy_in_its_pages_voice():
    """Section 3.4 of the style guide lets a crawler copy keep its page's voice: the About page's copy says "I"."""
    voice = re.search(r"^### 3\.4 Voice & Tone\n(.*?)^#", read(STYLE_GUIDE), re.MULTILINE | re.DOTALL)
    assert voice, "style-guide.md no longer has section 3.4, Voice & Tone"
    rule = collapse(voice.group(1))
    assert "a crawler copy that mirrors a page keeps the page's voice" in rule, (
        "style-guide.md 3.4: a crawler copy keeps the voice of the page it mirrors"
    )
    assert "crawler copies describe the site in the third person" not in rule, (
        "style-guide.md 3.4: the About page's crawler copy speaks as 'I', like the page"
    )
    for name, text in (("AboutPage.tsx", read(ABOUT_PAGE)), ("seo.py", about_bot_body())):
        assert "; I decide, test and send back." in collapse(text), f"{name}: the builder speaks as 'I'"


def test_the_style_guide_assumes_no_single_language_of_the_catalogue():
    """Section 3.7's tutorial bullet names no one language while the library registry spans several."""
    languages = {library["language_id"] for library in LIBRARIES_METADATA}
    bullet = re.search(r"^- \*\*A tutorial platform\*\*\.(.*)$", read(STYLE_GUIDE), re.MULTILINE)
    assert bullet, "style-guide.md 3.7 no longer has the 'A tutorial platform' bullet"
    assert "you know how to run code in your language" in bullet.group(1), "style-guide.md 3.7: the tutorial bullet"
    if len(languages) > 1:
        named = sorted(lang for lang in languages if re.search(rf"\b{re.escape(lang)}\b", bullet.group(1), re.I))
        assert not named, f"style-guide.md 3.7 names {named}; the catalogue spans {len(languages)} languages"


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
