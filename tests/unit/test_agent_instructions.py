"""The agent instructions must keep pointing at things that exist.

`CLAUDE.md` and `.github/copilot-instructions.md` both open with the claim that
they stay in sync, and both are read as binding shorthand — CLAUDE.md is loaded
into every Claude Code session, copilot-instructions.md into every Copilot
review. Nothing checked either claim, and both drift the same quiet way: a path
moves, a link rots, a rule gets tightened in one file and not the other, and
the guide keeps reading as authoritative while it sends the next agent
somewhere that no longer exists.

Five cheap pins, none of which needs the database, the network or a checkout of
anything but this repository:

1. every backtick-quoted repo path in the agent-facing files resolves;
2. every relative Markdown link resolves, and every same-page anchor points at
   a heading that is there;
3. every skill the routing table names exists as `.claude/skills/<name>/SKILL.md`;
4. the rules that are supposed to be mirrored are present on BOTH sides;
5. `.claude/guardrails.md` stays a companion — every section it carries maps to
   a binding one-liner in CLAUDE.md, and the file says so about itself.

(4) is deliberately a keyword pin, not a text diff: the two files address
different audiences and paraphrase each other, so requiring byte equality would
force false uniformity. What it catches is a rule silently living in only one
of them.

This pins what the guides already say. It is not the place to introduce a rule
— write the rule in both guides first, then add its keywords here.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[2]

CLAUDE_MD = REPO_ROOT / "CLAUDE.md"
COPILOT_MD = REPO_ROOT / ".github" / "copilot-instructions.md"
GUARDRAILS_MD = REPO_ROOT / ".claude" / "guardrails.md"

AGENT_FILES = [
    CLAUDE_MD,
    COPILOT_MD,
    GUARDRAILS_MD,
    REPO_ROOT / "agentic" / "docs" / "project-guide.md",
    REPO_ROOT / "agentic" / "commands" / "prime.md",
]

_BACKTICKED = re.compile(r"`([^`\n]+)`")
_MD_LINK = re.compile(r"\[[^\]]*\]\(([^)\s]+)\)")
_HEADING = re.compile(r"^#+\s+(.*)$", re.M)
_FENCE = re.compile(r"^```.*?^```", re.M | re.S)

# A backticked span is only treated as a path when it looks like one and
# carries no shell or placeholder syntax. Everything else in backticks is a
# command, an identifier, a label, a header name or a value.
_PATH_SHAPED = re.compile(r"^[\w./@-]+$")
_FILE_SUFFIXES = {
    ".cff",
    ".conf",
    ".gz",
    ".html",
    ".jl",
    ".js",
    ".json",
    ".lock",
    ".md",
    ".mjs",
    ".mts",
    ".py",
    ".sh",
    ".toml",
    ".ts",
    ".tsx",
    ".txt",
    ".yaml",
    ".yml",
}

# Files with no extension are real paths too, and the suffix rule above drops
# them silently — `api/Dockerfile` and `app/Dockerfile` are named in the guides
# and would have gone unchecked (Copilot review). Matched on the basename, so
# `prism/r` and `app/app/src`, which are prose rather than locations, stay out.
_EXTENSIONLESS_FILES = {"CODEOWNERS", "Dockerfile", "LICENSE", "Makefile", "Procfile"}

# Paths the guides name deliberately although they are absent: templates that
# only exist once a developer copies them, and directories the rules define
# ahead of the first file that will live in them.
_KNOWN_ABSENT: set[str] = {".env", "app/.env"}

# Skill-shaped tokens that are NOT repository skills. `/update-config` is a
# Claude Code harness skill, which CLAUDE.md says in the same breath it names
# it; `/pull_request` and the other slash names under `agentic/commands/` are
# commands, resolved by the path pin instead.
_HARNESS_SKILLS = {"update-config"}
_SKILL_TOKEN = re.compile(r"`/([a-z][a-z0-9-]+)`")


def _looks_like_path(token: str) -> bool:
    """Only multi-segment paths are checked.

    A bare basename (`CHANGELOG.md`, `conftest.py`) is prose shorthand in these
    files, not a location claim — pinning those would force every mention to
    carry a full path and make the guides harder to read, which is the opposite
    of the point.
    """
    if not _PATH_SHAPED.match(token) or token.startswith(("http", "@")):
        return False
    if token in _KNOWN_ABSENT:
        return False
    # A `../`-relative fragment is a claim about a location relative to
    # something else in the same span — the symlink target in `.claude/commands/
    # → ../agentic/commands/` — and resolving it against the repository root
    # would be wrong. `test_the_commands_symlink_points_where_it_says` pins that
    # one properly, by following the link rather than by matching its text.
    if token.split("/")[0] in {".", ".."}:
        return False
    normalised = token.strip("/")
    if "/" not in normalised:
        return False
    if token.endswith("/") or Path(token).suffix in _FILE_SUFFIXES:
        return True
    return Path(token).name in _EXTENSIONLESS_FILES


def _candidate_paths(text: str) -> set[str]:
    """Every repo path claimed inside a code span.

    A span is split on whitespace before the shape test, because a span is not
    always one path: `` `.claude/commands/ → ../agentic/commands/` `` is a
    sentence about two of them, and treating it as a single token let the whole
    claim through unchecked (Copilot review). Fragments that are not
    path-shaped — the arrow, a command word, a flag — fail the test and drop
    out, which is what makes the split safe.
    """
    return {fragment for span in _BACKTICKED.findall(text) for fragment in span.split() if _looks_like_path(fragment)}


def _headings(text: str) -> set[str]:
    """The page's real headings, as GitHub anchors.

    Fenced blocks are stripped first. These files are full of shell snippets,
    and a `# Install uv` comment inside one is not a heading — counting it
    would let a dead same-page link pass by matching a line GitHub renders as
    code (Copilot review).
    """
    return {_anchor(h) for h in _HEADING.findall(_FENCE.sub("", text))}


def _anchor(heading: str) -> str:
    """GitHub's slug for a heading: lowercased, punctuation dropped, spaces to
    hyphens. Enough of the algorithm for the headings these files actually have.
    """
    slug = heading.strip().lower()
    slug = re.sub(r"[^\w\s-]", "", slug)
    return re.sub(r"\s", "-", slug)


def _flat(text: str) -> str:
    """Lowercased with runs of whitespace collapsed.

    Both guides hard-wrap their prose, so a rule's phrase is regularly split
    across two lines; matching the raw text would report a rule as missing
    purely because of where the line broke.
    """
    return re.sub(r"\s+", " ", text).lower()


@pytest.mark.parametrize("path", AGENT_FILES, ids=lambda p: p.name)
def test_agent_file_exists(path: Path) -> None:
    assert path.is_file(), f"{path} is referenced as an agent instruction file"


@pytest.mark.parametrize("agent_file", AGENT_FILES, ids=lambda p: p.name)
def test_backticked_paths_resolve(agent_file: Path) -> None:
    """Every backticked repo path in the agent instructions exists.

    A path that has moved makes the instruction actively misleading — the agent
    follows it, finds nothing, and improvises.
    """
    missing = sorted(
        token
        for token in _candidate_paths(agent_file.read_text(encoding="utf-8"))
        if not (REPO_ROOT / token.strip("/")).exists()
    )
    assert not missing, f"{agent_file.name} points at paths that do not exist: {missing}"


@pytest.mark.parametrize("agent_file", AGENT_FILES, ids=lambda p: p.name)
def test_markdown_links_resolve(agent_file: Path) -> None:
    """Relative links land on a file, and same-page anchors on a heading.

    Both forms rot silently: nothing renders an error, the link simply goes
    nowhere, and a reader who follows it concludes the guide is stale.
    """
    text = agent_file.read_text(encoding="utf-8")
    anchors = _headings(text)

    broken: list[str] = []
    for target in _MD_LINK.findall(text):
        if target.startswith(("http://", "https://", "mailto:")):
            continue
        if target.startswith("#"):
            if target[1:] not in anchors:
                broken.append(target)
            continue
        # Relative to the linking file, which is also how GitHub resolves it.
        # A leading slash reads as repo-root-relative to a human but as
        # site-root to GitHub's renderer, where it 404s — so it is reported,
        # not resolved generously.
        relative = target.split("#")[0]
        if not (agent_file.parent / relative).exists():
            broken.append(target)

    assert not broken, f"{agent_file.name} links to targets that do not exist: {broken}"


def test_the_commands_symlink_points_where_it_says() -> None:
    """CLAUDE.md documents `.claude/commands/ → ../agentic/commands/` as what
    makes slash-command resolution work, and tells agents not to write commands
    into `.claude/commands/` directly.

    The path pin only proves both ends exist. This follows the link, because
    the failure worth catching is the one where somebody replaces the symlink
    with a real directory: both paths still resolve, the guide still reads
    true, and every command written on either side quietly stops matching the
    other.
    """
    link = REPO_ROOT / ".claude" / "commands"
    assert link.is_symlink(), f"{link} is documented as a symlink"
    assert link.resolve() == (REPO_ROOT / "agentic" / "commands").resolve()


def test_every_named_skill_exists() -> None:
    """The routing table in CLAUDE.md sends work to `.claude/skills/<name>/`.

    A skill named there but never written is worse than no table: the agent
    invokes it, gets nothing, and proceeds without the verification loop the
    table promised.
    """
    named = set(_SKILL_TOKEN.findall(CLAUDE_MD.read_text(encoding="utf-8"))) - _HARNESS_SKILLS
    available = {p.name for p in (REPO_ROOT / ".claude" / "skills").iterdir() if p.is_dir()}
    commands = {p.stem for p in (REPO_ROOT / "agentic" / "commands").glob("*.md")}

    unknown = sorted(named - available - commands)
    assert not unknown, f"CLAUDE.md names skills or commands that do not exist: {unknown}"

    without_manual = sorted(
        name for name in named & available if not (REPO_ROOT / ".claude" / "skills" / name / "SKILL.md").is_file()
    )
    assert not without_manual, f"skill directories without a SKILL.md: {without_manual}"


# Rules that must reach BOTH audiences. Each entry is a human-readable name
# plus the keywords that identify the rule in either file's own wording; a rule
# counts as present when every keyword appears (case-insensitively).
#
# Every entry's keywords have to carry the rule's OBLIGATION, not only its
# subject. A pin on the topic alone stays green while the guides are rewritten
# to say the opposite, which is worse than no pin: the suite then reports that
# a rule is mirrored when what is mirrored is its subject matter (Copilot
# review, twice — the pipeline rule and the changelog rule).
MIRRORED_RULES = {
    "output is always English": ["always write in english"],
    "prose follows the Google style guide": [
        "prose follows the google developer documentation style guide",
        "docs/reference/style-guide.md",
    ],
    # The keywords carry the PROHIBITION as well as the duty: a fragment is
    # added AND no bullet is added to `CHANGELOG.md`. A pin on "changelog.d"
    # alone would stay green if a guide were rewritten to allow both. "new" is
    # part of the pin since 2026-09-04, when the gate learned to tell a
    # CORRECTED bullet from an added one — the prohibition is on adding, and
    # the phrase has to say so.
    "every PR adds a changelog fragment, never a new CHANGELOG.md bullet": [
        "changelog.d/<slug>.md",
        "never a new bullet in `changelog.md`",
        'changelog (fragment)"',
    ],
    "a release is condensed, never copied": ["condensed, never copied", "agentic/commands/release.md"],
    "never echo secret values": ["never echo secret"],
    "structural fix over symptomatic fix": ["structural fix over symptomatic fix"],
    # The repository's most consequential rule, and the one an agent that opens
    # and edits PRs is most able to break: specs and implementations go through
    # the workflows, and their PRs are merged by `impl-merge`, never by hand.
    #
    # The keywords carry the PROHIBITION, not just its subject. A bare
    # "manually merge" would stay green if both guides were rewritten to say
    # agents may do it — the pin would name the rule while protecting the
    # opposite of it (Copilot review). Both guides were normalised on "never"
    # so the negative phrase itself is what is matched.
    "never merge a pipeline PR by hand": ["never manually merge", "never bypass"],
}


@pytest.mark.parametrize("rule", sorted(MIRRORED_RULES), ids=lambda r: r.replace(" ", "-"))
def test_rule_is_mirrored_in_both_guides(rule: str) -> None:
    """A rule the repository relies on must not live in only one of the guides.

    CLAUDE.md never reaches Copilot, and copilot-instructions.md never reaches
    a Claude Code session; a rule in one file only is a rule half the agents
    never see.
    """
    keywords = MIRRORED_RULES[rule]
    claude = _flat(CLAUDE_MD.read_text(encoding="utf-8"))
    copilot = _flat(COPILOT_MD.read_text(encoding="utf-8"))

    missing_in = [
        name
        for name, text in (("CLAUDE.md", claude), ("copilot-instructions.md", copilot))
        if not all(keyword.lower() in text for keyword in keywords)
    ]
    assert not missing_in, f"rule {rule!r} is missing from: {', '.join(missing_in)}"


def test_each_guide_names_the_other_as_its_companion() -> None:
    """The sync claim is what the rest of this file enforces. If it is deleted,
    the mirroring stops being a promise and these tests stop meaning anything.

    Matched on the companion SENTENCE, not on the other file's name: each guide
    mentions the other elsewhere too — CLAUDE.md in the changelog rule, the
    Copilot guide in several sections — so a name check would stay green with
    both opening claims deleted (Copilot review).
    """
    claude = _flat(CLAUDE_MD.read_text(encoding="utf-8"))
    copilot = _flat(COPILOT_MD.read_text(encoding="utf-8"))

    assert "companion guide `.github/copilot-instructions.md`" in claude
    assert "companion guide `claude.md`" in copilot
    for name, text in (("CLAUDE.md", claude), ("copilot-instructions.md", copilot)):
        assert "both files must stay in sync" in text, f"{name} dropped the sync claim"


def test_guardrails_split_stays_subordinate() -> None:
    """The rationale file must stay a companion, never become the rule.

    Two ways this split rots: CLAUDE.md loses the pointer, so nobody finds the
    rationale; or `.claude/guardrails.md` starts reading like the authority, so
    a rule ends up living only there — where no session loads it.
    """
    claude = _flat(CLAUDE_MD.read_text(encoding="utf-8"))
    guardrails = _flat(GUARDRAILS_MD.read_text(encoding="utf-8"))

    assert ".claude/guardrails.md" in claude, "CLAUDE.md no longer points at the rationale file"
    assert "is the rule and this is the commentary" in guardrails, (
        "`.claude/guardrails.md` must state that CLAUDE.md wins — without it the "
        "companion file starts reading like the authority"
    )


# Every `##` section of `.claude/guardrails.md` → a phrase that must appear in
# CLAUDE.md, where the binding one-liner lives. The map is explicit on purpose:
# adding a section to the companion file fails the test until its rule is
# registered here, and registering it forces you to name the CLAUDE.md line it
# belongs to. A disclaimer sentence alone would not have caught that.
#
# The phrases are searched in the whole of CLAUDE.md rather than in one
# section, because this repository states its rules across "Important Rules"
# and "Development Workflow"; each anchor therefore carries the rule's
# OBLIGATION and not just its subject, so it cannot match some other mention.
#
# A section that carries several obligations registers all of them, not just
# the one its title is about (Copilot review): the delegation section adds the
# worktree line and the Edit/Write precedence to the model-tier rule, and a
# single "opus by default" anchor would stay green while either of those was
# deleted from CLAUDE.md and left living only in the companion file — exactly
# the drift these tests exist to catch.
GUARDRAIL_SECTION_ANCHORS = {
    "Delegated agents run on Opus by default": [
        "opus by default",
        "all `git` stays inside the agent's own worktree",
        "repo files are modified only with edit/write",
    ],
    "External-system writes need explicit, named authorization": ["explicit, named authorization"],
    "Modify repo files only with the Edit/Write tools": ["heredocs/sed", "outranks any harness or agent-mode reminder"],
}


def _guardrail_sections() -> list[str]:
    return re.findall(r"^## (.+)$", GUARDRAILS_MD.read_text(encoding="utf-8"), re.M)


def test_every_companion_section_is_registered() -> None:
    """A new section in the companion file must be registered, both ways.

    Unregistered section → a rule could live only where no session loads it.
    Registered but absent section → the map grants cover to nothing and rots.
    """
    sections = set(_guardrail_sections())
    registered = set(GUARDRAIL_SECTION_ANCHORS)
    assert not sections - registered, f"unregistered sections in guardrails.md: {sorted(sections - registered)}"
    assert not registered - sections, f"registered but missing from guardrails.md: {sorted(registered - sections)}"


@pytest.mark.parametrize("section", sorted(GUARDRAIL_SECTION_ANCHORS), ids=lambda s: s[:40])
def test_companion_section_has_a_binding_rule(section: str) -> None:
    """Every obligation a rationale section elaborates is stated in CLAUDE.md."""
    claude = _flat(CLAUDE_MD.read_text(encoding="utf-8"))
    missing = [anchor for anchor in GUARDRAIL_SECTION_ANCHORS[section] if anchor.lower() not in claude]
    assert not missing, f"guardrails.md § {section!r} elaborates rules CLAUDE.md no longer states: {missing}"
