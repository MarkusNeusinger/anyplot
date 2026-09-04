"""Changelog fragments: one file per PR under `changelog.d/`, folded into
`CHANGELOG.md` when a release is cut.

Why fragments. Every PR adds its bullets under `[Unreleased]` of the one shared
file, so sibling PRs conflict each other exactly there and only there — three
times in one night on 2026-09-02/03, each time a hand-resolved rebase for text
neither branch disagreed about. A union merge driver (`.gitattributes`) heals
the LOCAL rebase for pure additions, but GitHub's own mergeability check ignores
merge drivers, and a branch that MOVES changelog lines comes out of a union
rebase with the block duplicated. Fragments remove the shared spot altogether: a
PR adds `changelog.d/<slug>.md` and touches nothing else; the release cut folds
every fragment — plus whatever `[Unreleased]` still holds from before the
fragments existed — under the new version heading, bumps the version files,
repoints the compare links and deletes the fragments.

A fragment is a slice of the CHANGELOG in the CHANGELOG's own format —
`### <Category>` headings over bold-titled bullets — so the assembled section
reads exactly as if it had been written there, and ONE parser serves the
fragments and the `[Unreleased]` section alike. Standard library only, so the
CI gate runs it without the project's extras.

What the cut does NOT do is anyplot's two aggregate lines: the italic
`*Catalog: …*` at the end of the section and the single `**Dependencies:**`
bullet that stands in for the window's Dependabot bumps. Both summarize what
happened between releases rather than what any one PR said, so they stay where
`agentic/commands/release.md` puts them — written by hand at cut time, into the
section this tool has just laid out.

Three verbs (`python -m tools.changelog …`, see `__main__`):

* `check [--base REF]` — every fragment parses and carries no unfilled `(#NNN)`
  placeholder; with `--base`, the diff against REF must carry a fragment (or be
  a release cut, or catalogue-only) and must not ADD bullets to `[Unreleased]`
  directly (correcting one that is already there is fine — a bullet is
  identified by its bold title, not by its full text).
* `preview` — the merged `[Unreleased]` as the next cut would write it.
* `release VERSION --title …` — the cut itself.
"""

from __future__ import annotations

import re
import subprocess
from collections import Counter
from dataclasses import dataclass
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
FRAGMENT_DIR_NAME = "changelog.d"
CHANGELOG_NAME = "CHANGELOG.md"

# Keep a Changelog's own order; the file has used Added, Changed, Removed and
# Fixed so far, and a fragment may only name one of these six.
CATEGORIES = ("Added", "Changed", "Deprecated", "Removed", "Fixed", "Security")

# What a PR may touch without a fragment: the catalogue itself. The automated
# plot pipeline (spec-create, impl-generate/review/repair/merge, spec
# auto-polish, daily-regen) writes nothing outside `plots/`, and its output is
# the exempt class the release summarizes in one italic *Catalog* line rather
# than per PR — hundreds of them per window. The CI job skips the two bot
# authors as well, so a pipeline PR passes on either count.
EXEMPT_PREFIXES = ("plots/",)

UNRELEASED_HEADING = "## [Unreleased]"
SKIP_LABEL = "skip-changelog"

COMPARE_BASE = "https://github.com/MarkusNeusinger/anyplot/compare"

_VERSION_HEADING = re.compile(r"^## \[(\d+\.\d+\.\d+)\]")
_CATEGORY_LINE = re.compile(r"^### (\S+)\s*$")
# The bold title, over the WHOLE bullet: it regularly runs onto the continuation
# line before its closing `**`, so DOTALL and the non-greedy body are both load-bearing.
_BOLD_TITLE = re.compile(r"- \*\*.+?\*\*", re.DOTALL)
# The unfilled reference placeholder, in any width of N. Quoted in backticks it
# is a fragment TALKING about the placeholder (this rule's own entry does), which
# is prose like any other — only a bare one is a reference nobody filled in.
_PLACEHOLDER = re.compile(r"(?<!`)\(#N+\)(?!`)")
_SEMVER = re.compile(r"\d+\.\d+\.\d+")
_DATE = re.compile(r"\d{4}-\d{2}-\d{2}")
_UNRELEASED_LINK = re.compile(r"^\[Unreleased\]: (\S+)/compare/v(\d+\.\d+\.\d+)\.\.\.HEAD$", re.M)

# One anchored pattern per version line, so a cut that finds anything but
# exactly one match stops instead of guessing. `app/package.json` is bumped in
# lockstep because the masthead falls back to it whenever the GitHub releases
# lookup is unavailable, and tests/unit/test_version_sync.py fails a PR where
# the two drift — the anchor is the two-space-indented top-level key, which no
# dependency line can match.
_VERSION_LINES: tuple[tuple[str, str, str], ...] = (
    ("pyproject.toml", r'^version = "\d+\.\d+\.\d+"$', 'version = "{version}"'),
    ("uv.lock", r'^(name = "anyplot"\n)version = "\d+\.\d+\.\d+"$', r'\g<1>version = "{version}"'),
    ("app/package.json", r'^  "version": "\d+\.\d+\.\d+",$', '  "version": "{version}",'),
)

Entries = dict[str, list[str]]


class ChangelogError(ValueError):
    """A fragment, the changelog or a PR violates the format; the message names where."""


# --- parsing -----------------------------------------------------------------


def parse_entries(text: str, *, where: str) -> Entries:
    """Parse `### Category` headings over `- **Title.** …` bullets.

    A bullet keeps its continuation lines (two-space indented, as the existing
    entries wrap; sub-bullets are indented the same way). Anything else is an
    error naming the line, because a stray line here would silently become
    part of a release section nobody proof-reads again.
    """
    entries: Entries = {}
    current: list[str] | None = None
    bullet: list[str] | None = None
    opened_at = 0

    def close() -> None:
        """Finish the bullet in hand, checking the one thing only the WHOLE
        bullet can answer: that its bold title is closed.

        Not checkable on the opening line — a title regularly runs onto the
        continuation line before its `**`, as the entries in CHANGELOG.md do.
        Left unchecked, `- **unterminated title` parsed as well-formed and the
        release published it unchanged (Copilot review)."""
        nonlocal bullet
        if bullet is not None and current is not None:
            text = "\n".join(bullet).rstrip()
            if not _BOLD_TITLE.match(text):
                raise ChangelogError(
                    f"{where}:{opened_at}: the bullet's bold title is never closed — "
                    "it opens with '- **' and needs the matching '**'"
                )
            current.append(text)
        bullet = None

    for n, line in enumerate(text.splitlines(), 1):
        if m := _CATEGORY_LINE.match(line):
            close()
            name = m.group(1)
            if name not in CATEGORIES:
                raise ChangelogError(f"{where}:{n}: unknown category '{name}' (one of {', '.join(CATEGORIES)})")
            if name in entries:
                raise ChangelogError(f"{where}:{n}: category '{name}' appears twice")
            current = entries[name] = []
        elif line.startswith("- "):
            close()
            if current is None:
                raise ChangelogError(f"{where}:{n}: a bullet before any '### Category' heading")
            if not line.startswith("- **"):
                raise ChangelogError(f"{where}:{n}: a bullet opens with its bold title: '- **Title.** …'")
            bullet = [line]
            opened_at = n
        elif not line.strip():
            if bullet is not None:
                bullet.append("")
        elif bullet is not None and line.startswith("  "):
            bullet.append(line)
        else:
            raise ChangelogError(
                f"{where}:{n}: stray text — only '### Category' headings, '- **…' bullets "
                "and their two-space-indented continuation lines belong here"
            )
    close()
    return entries


def bullet_title(bullet: str) -> str:
    """The bold title, whitespace-collapsed — a bullet's identity across edits.

    Two bullets are the same entry when they open with the same title, whatever
    the body behind it now says. That is what lets the gate below tell a
    CORRECTED bullet from an ADDED one, and the collapse is what makes it hold
    when the correction rewraps the lines the title itself runs over.
    """
    match = _BOLD_TITLE.match(bullet)
    return " ".join((match.group(0) if match else bullet).split())


@dataclass(frozen=True)
class Changelog:
    """`CHANGELOG.md` split at its `[Unreleased]` section."""

    head: str
    """Everything up to and including the `## [Unreleased]` line."""
    unreleased: str
    """The section body — empty between a cut and the first old-style entry."""
    rest: str
    """From the newest version heading to the end, untouched by a cut."""

    @property
    def newest_version(self) -> str | None:
        m = _VERSION_HEADING.match(self.rest)
        return m.group(1) if m else None


def split_changelog(text: str) -> Changelog:
    lines = text.splitlines(keepends=True)
    start = next((i for i, line in enumerate(lines) if line.rstrip("\n") == UNRELEASED_HEADING), None)
    if start is None:
        raise ChangelogError(f"{CHANGELOG_NAME}: no '{UNRELEASED_HEADING}' heading")
    end = next((i for i in range(start + 1, len(lines)) if lines[i].startswith("## ")), len(lines))
    return Changelog("".join(lines[: start + 1]), "".join(lines[start + 1 : end]), "".join(lines[end:]))


# --- fragments ---------------------------------------------------------------


@dataclass(frozen=True)
class Fragment:
    path: Path
    entries: Entries


def _git(root: Path, *args: str, required: bool = False) -> str:
    """Stdout of a git command in `root`.

    The gate's calls are `required`: a failure there (an unfetched base ref, a
    missing merge-base) must stop the check, because an empty diff would
    otherwise read as "nothing changed" and let the PR pass. Only the
    fragment-date lookup is best-effort and gets the empty string instead.
    """
    try:
        done = subprocess.run(["git", *args], cwd=root, capture_output=True, text=True, check=False)
    except OSError as e:
        if required:
            raise ChangelogError(f"git {' '.join(args)}: {e}") from e
        return ""
    if done.returncode != 0:
        if required:
            raise ChangelogError(f"git {' '.join(args)} failed: {done.stderr.strip() or done.returncode}")
        return ""
    return done.stdout


def _added_at(root: Path, path: Path) -> float:
    """Commit time of the commit that added `path`; an uncommitted fragment is the newest of all."""
    stamp = _git(root, "log", "--diff-filter=A", "--format=%ct", "-1", "--", str(path.relative_to(root))).strip()
    return float(stamp) if stamp else float("inf")


def check_placeholder(text: str, *, where: str) -> None:
    """Refuse `(#NNN)` left standing where a number was meant to go.

    The reference itself is optional at write time — the number does not exist
    until the PR does, and `/pull_request` appends it once it opens. What is
    never right is the placeholder shipped as written: it reads as a reference
    in the released section and points nowhere. So: a number, or nothing, but
    not the letter N.
    """
    for n, line in enumerate(text.splitlines(), 1):
        if match := _PLACEHOLDER.search(line):
            raise ChangelogError(
                f"{where}:{n}: '{match.group(0)}' is the unfilled placeholder — put the PR number in, "
                "or take the reference out (it is appended when the PR opens)"
            )


def load_fragments(root: Path = REPO_ROOT) -> list[Fragment]:
    """Every `changelog.d/*.md` but the README, newest first.

    Newest first mirrors the rule the shared file had ("a new bullet goes on
    top of its category"), so the cut section reads in the same order the
    old one did. The order comes from the commit that added the fragment,
    not the file name, so a slug never has to encode a date.
    """
    directory = root / FRAGMENT_DIR_NAME
    fragments: list[Fragment] = []
    for path in sorted(directory.glob("*.md")):
        if path.name == "README.md":
            continue
        where = str(path.relative_to(root))
        text = path.read_text(encoding="utf-8")
        entries = parse_entries(text, where=where)
        if not any(entries.values()):
            raise ChangelogError(f"{where}: no bullets")
        check_placeholder(text, where=where)
        fragments.append(Fragment(path, entries))
    return sorted(fragments, key=lambda f: (-_added_at(root, f.path), f.path.name))


def merge(existing: Entries, fragments: list[Fragment]) -> Entries:
    """Keep a Changelog's category order; within one, the fragments go above what `[Unreleased]` already held."""
    merged: Entries = {}
    for category in CATEGORIES:
        bullets = [b for f in fragments for b in f.entries.get(category, [])] + existing.get(category, [])
        if bullets:
            merged[category] = bullets
    return merged


def render(entries: Entries) -> str:
    """The section body as the file writes it: a heading, a blank line, the bullets, a blank line."""
    return "".join(f"### {c}\n\n" + "\n".join(entries[c]) + "\n\n" for c in CATEGORIES if entries.get(c))


def unreleased(root: Path = REPO_ROOT) -> Entries:
    """The merged `[Unreleased]` — the section in the file plus every fragment."""
    parts = split_changelog((root / CHANGELOG_NAME).read_text(encoding="utf-8"))
    existing = parse_entries(parts.unreleased, where=f"{CHANGELOG_NAME} [Unreleased]")
    return merge(existing, load_fragments(root))


# --- the cut -----------------------------------------------------------------


@dataclass(frozen=True)
class Release:
    """A planned cut: file contents to write and fragments to delete — nothing touched yet."""

    version: str
    writes: dict[Path, str]
    deletes: tuple[Path, ...]


def _semver(version: str) -> tuple[int, ...]:
    return tuple(int(part) for part in version.split("."))


def repoint_compare_links(text: str, *, version: str) -> str:
    """Move `[Unreleased]` to the new tag and add the new version's compare link.

    The link block at the bottom of the file carries one line per bracketed
    heading, and `agentic/commands/release.md` calls keeping it in step "easy to
    forget" — which is exactly the kind of step a tool should hold instead of a
    checklist. A file without an `[Unreleased]:` line keeps none: the block is
    optional, and inventing one would be a change the release never asked for.
    """
    match = _UNRELEASED_LINK.search(text)
    if match is None:
        return text
    previous = match.group(2)
    if previous == version:
        raise ChangelogError(f"the [Unreleased] compare link already points at v{version}")
    return _UNRELEASED_LINK.sub(
        f"[Unreleased]: {COMPARE_BASE}/v{version}...HEAD\n[{version}]: {COMPARE_BASE}/v{previous}...v{version}",
        text,
        count=1,
    )


def cut_release(text: str, fragments: list[Fragment], *, version: str, date: str, title: str) -> str:
    """The new `CHANGELOG.md`: `[Unreleased]` emptied, the merged entries under the version heading."""
    if not _SEMVER.fullmatch(version):
        raise ChangelogError(f"version '{version}' is not MAJOR.MINOR.PATCH")
    if not _DATE.fullmatch(date):
        raise ChangelogError(f"date '{date}' is not YYYY-MM-DD")
    if not title.strip():
        raise ChangelogError("a release heading carries a title (`## [x.y.z] — date — title`)")
    parts = split_changelog(text)
    newest = parts.newest_version
    if newest and _semver(version) <= _semver(newest):
        raise ChangelogError(f"version {version} is not above the newest section, {newest}")
    entries = merge(parse_entries(parts.unreleased, where=f"{CHANGELOG_NAME} [Unreleased]"), fragments)
    if not entries:
        raise ChangelogError("nothing to release: no fragments, and [Unreleased] is empty")
    heading = f"## [{version}] — {date} — {title.strip()}\n\n"
    return repoint_compare_links(parts.head + "\n" + heading + render(entries) + parts.rest, version=version)


def bump_version_files(root: Path, *, version: str, date: str) -> dict[Path, str]:
    """New contents of the version-carrying files; exactly one line each, or the cut stops."""
    writes: dict[Path, str] = {}
    for name, pattern, replacement in _VERSION_LINES:
        path = root / name
        text = writes.get(path) or path.read_text(encoding="utf-8")
        new, n = re.subn(pattern, replacement.format(version=version, date=date), text, flags=re.M)
        if n != 1:
            raise ChangelogError(f"{name}: expected exactly one line matching {pattern!r}, found {n}")
        writes[path] = new
    return writes


def plan_release(*, version: str, date: str, title: str, root: Path = REPO_ROOT) -> Release:
    changelog = root / CHANGELOG_NAME
    fragments = load_fragments(root)
    writes = {
        changelog: cut_release(
            changelog.read_text(encoding="utf-8"), fragments, version=version, date=date, title=title
        )
    }
    writes.update(bump_version_files(root, version=version, date=date))
    return Release(version, writes, tuple(f.path for f in fragments))


def apply_release(release: Release) -> None:
    for path, text in release.writes.items():
        path.write_text(text, encoding="utf-8")
    for path in release.deletes:
        path.unlink()


# --- the PR gate -------------------------------------------------------------


def _changed_files(root: Path, base: str) -> dict[str, str]:
    """`path → status letter` for everything HEAD changed since it branched off `base`."""
    out = _git(root, "diff", "--name-status", "--no-renames", f"{base}...HEAD", required=True)
    changed: dict[str, str] = {}
    for line in out.splitlines():
        status, _, path = line.partition("\t")
        if path:
            changed[path] = status[:1]
    return changed


def _bullets(section: str) -> list[str]:
    return [b for bullets in parse_entries(section, where=f"{CHANGELOG_NAME} [Unreleased]").values() for b in bullets]


def _added_bullets(before: str, after: str) -> list[str]:
    """The bullets `after` holds beyond `before`, by the identity `bullet_title` gives them.

    Counted, not set-differenced. Two bullets may legitimately carry the same
    title, and a set of titles would let a second copy of one the section
    already holds pass unseen — the gate has to notice the COPY as much as the
    newcomer (Copilot review).
    """
    held = Counter(bullet_title(b) for b in _bullets(before))
    seen: Counter[str] = Counter()
    added: list[str] = []
    for bullet in _bullets(after):
        title = bullet_title(bullet)
        seen[title] += 1
        if seen[title] > held[title]:
            added.append(bullet)
    return added


def check_pr(base: str, *, root: Path = REPO_ROOT) -> list[str]:
    """Why HEAD, as a PR against `base`, fails the fragment rule — empty when it passes.

    Passes when the PR touches `changelog.d/` at all (a fragment added, an old
    one corrected), when it is the release cut (a version heading the base
    lacks — the cut moves bullets OUT and needs no fragment of its own), or
    when everything it touches is exempt (catalogue-only, `plots/`). Fails when
    it carries no fragment, and — independently — when it ADDS a bullet to
    `[Unreleased]`: that is the shared spot the fragments exist to retire.

    Added, not merely different. A bullet is identified by its bold title
    (`bullet_title`), so re-wording the body of an entry the base already
    carries — a typo in a shipped line, a sharper clause — is a change and
    passes; only a title the base does not have — or one more copy of a title
    it has — is a new entry and is refused into a fragment. Set-of-bullets
    identity could not tell the two apart and refused both.
    """
    changed = _changed_files(root, base)
    problems: list[str] = []
    release_cut = False
    if changed.get(CHANGELOG_NAME) == "M":
        merge_base = _git(root, "merge-base", base, "HEAD", required=True).strip()
        before = split_changelog(_git(root, "show", f"{merge_base}:{CHANGELOG_NAME}", required=True))
        after = split_changelog((root / CHANGELOG_NAME).read_text(encoding="utf-8"))
        release_cut = after.newest_version != before.newest_version
        for bullet in sorted(_added_bullets(before.unreleased, after.unreleased)):
            title = bullet.split("\n", 1)[0][:72]
            problems.append(f"{CHANGELOG_NAME} [Unreleased] gained a bullet — it belongs in a fragment: {title}…")
    touches_fragments = any(p.startswith(f"{FRAGMENT_DIR_NAME}/") for p in changed)
    exempt = bool(changed) and all(p.startswith(EXEMPT_PREFIXES) for p in changed)
    if changed and not (touches_fragments or release_cut or exempt):
        problems.insert(
            0,
            f"no changelog fragment: add {FRAGMENT_DIR_NAME}/<slug>.md (format: {FRAGMENT_DIR_NAME}/README.md), "
            f"or label the PR '{SKIP_LABEL}' if it truly changes nothing worth a line",
        )
    return problems
