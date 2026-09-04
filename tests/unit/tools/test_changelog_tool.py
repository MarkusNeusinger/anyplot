"""Unit tests for the changelog fragments tool.

The gate and the cut are what keep the shared file conflict-free, so every
rule is pinned here: the fragment format (what a stray line does), the merge
order, the cut against a synthetic changelog, the version-line bumps, and the
PR check against a throwaway git repository — the same call the CI job makes.
"""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

import pytest

from tools import changelog as cl


FRAGMENT = """### Added

- **A thing.** With a wrapped
  continuation line (#1).
- **Another thing.** Short (#1).

### Fixed

- **A slip.** Undone (#1).
"""

CHANGELOG = """# Changelog

Header prose.

## [Unreleased]

### Changed

- **An old-style entry.** Written before the fragments existed (#0).

## [0.1.0] — 2026-01-01 — First

### Added

- **The beginning.**
"""


def test_a_title_that_closes_on_the_continuation_line_is_accepted() -> None:
    """The reason the closing `**` is checked over the whole bullet, not the
    opening line: the entries in CHANGELOG.md wrap their titles like this."""
    wrapped = "### Added\n\n- **A title long enough to run\n  onto the next line** — and then the body (#1).\n"
    assert cl.parse_entries(wrapped, where="f.md")["Added"] == [
        "- **A title long enough to run\n  onto the next line** — and then the body (#1)."
    ]


def test_a_fragment_parses_into_categories_with_wrapped_bullets() -> None:
    entries = cl.parse_entries(FRAGMENT, where="f.md")
    assert list(entries) == ["Added", "Fixed"]
    assert entries["Added"] == [
        "- **A thing.** With a wrapped\n  continuation line (#1).",
        "- **Another thing.** Short (#1).",
    ]
    assert entries["Fixed"] == ["- **A slip.** Undone (#1)."]


@pytest.mark.parametrize(
    ("text", "complaint"),
    [
        ("### Broke\n\n- **x.**\n", "f.md:1: unknown category"),
        ("- **x.**\n", "f.md:1: a bullet before any"),
        ("### Added\n\n- plain bullet\n", "f.md:3: .*bold title"),
        ("### Added\n\nprose\n", "f.md:3: stray text"),
        ("### Added\n\n- **x.**\n\n### Added\n\n- **y.**\n", "f.md:5: .*twice"),
        # The bold title is never closed. Not catchable on the opening line —
        # a real title regularly runs onto the continuation line before its
        # `**` — so this is checked when the bullet ends, and the error names
        # the line the bullet OPENED on.
        ("### Added\n\n- **unterminated title\n", "f.md:3: .*never closed"),
        ("### Added\n\n- **still going\n  and going\n", "f.md:3: .*never closed"),
    ],
)
def test_a_malformed_fragment_names_its_line(text: str, complaint: str) -> None:
    with pytest.raises(cl.ChangelogError, match=complaint):
        cl.parse_entries(text, where="f.md")


def test_a_bullet_is_identified_by_its_title_whatever_the_line_breaks() -> None:
    """The identity is the title's words, so a reflow of the very line it runs over keeps it."""
    assert cl.bullet_title("- **A title that runs onto the\n  next line.** Its body.") == (
        "- **A title that runs onto the next line.**"
    )
    assert cl.bullet_title("- **A title that runs\n  onto the next line.** Its body, corrected.") == (
        "- **A title that runs onto the next line.**"
    )


@pytest.mark.parametrize(
    "bullet", ["- **A thing.** Done (#NNN).", "- **A thing.** Done (#NNNNN).", "- **A thing.** Done\n  (#NNN)."]
)
def test_the_unfilled_placeholder_is_refused(bullet: str) -> None:
    with pytest.raises(cl.ChangelogError, match="placeholder"):
        cl.check_placeholder(bullet + "\n", where="f.md")


@pytest.mark.parametrize(
    "bullet",
    [
        "- **A thing.** Done (#11215).",
        "- **A thing.** Done.",  # the reference is appended when the PR opens
        "- **A thing.** The `(#NNN)` placeholder, quoted — prose about it, not a reference.",
    ],
)
def test_a_number_no_number_and_a_quoted_placeholder_all_pass(bullet: str) -> None:
    cl.check_placeholder(bullet + "\n", where="f.md")


def test_the_placeholder_complaint_names_the_fragment_file(tmp_path: Path) -> None:
    (tmp_path / cl.FRAGMENT_DIR_NAME).mkdir()
    (tmp_path / cl.FRAGMENT_DIR_NAME / "topic.md").write_text(
        "### Added\n\n- **A thing.** Done (#NNNNN).\n", encoding="utf-8"
    )
    with pytest.raises(cl.ChangelogError, match=r"changelog\.d/topic\.md:3: .*placeholder"):
        cl.load_fragments(tmp_path)


def test_merge_puts_fragments_above_the_old_section_in_category_order() -> None:
    older = cl.Fragment(Path("a.md"), {"Fixed": ["- **old fix.**"], "Added": ["- **old add.**"]})
    newer = cl.Fragment(Path("b.md"), {"Added": ["- **new add.**"]})
    merged = cl.merge({"Added": ["- **file add.**"], "Changed": ["- **file change.**"]}, [newer, older])
    assert list(merged) == ["Added", "Changed", "Fixed"]
    assert merged["Added"] == ["- **new add.**", "- **old add.**", "- **file add.**"]
    assert cl.render(merged) == (
        "### Added\n\n- **new add.**\n- **old add.**\n- **file add.**\n\n"
        "### Changed\n\n- **file change.**\n\n"
        "### Fixed\n\n- **old fix.**\n\n"
    )


def test_the_cut_empties_unreleased_and_leaves_older_sections_byte_identical() -> None:
    fragment = cl.Fragment(Path("f.md"), cl.parse_entries(FRAGMENT, where="f.md"))
    text = cl.cut_release(CHANGELOG, [fragment], version="0.2.0", date="2026-08-30", title="Second")
    head, heading, rest = text.partition("## [0.2.0] — 2026-08-30 — Second\n\n")
    assert heading, text
    assert head == "# Changelog\n\nHeader prose.\n\n## [Unreleased]\n\n"
    section, _, older = rest.partition("## [0.1.0]")
    assert section == (
        "### Added\n\n- **A thing.** With a wrapped\n  continuation line (#1).\n- **Another thing.** Short (#1).\n\n"
        "### Changed\n\n- **An old-style entry.** Written before the fragments existed (#0).\n\n"
        "### Fixed\n\n- **A slip.** Undone (#1).\n\n"
    )
    assert "## [0.1.0]" + older == CHANGELOG[CHANGELOG.index("## [0.1.0]") :]
    # A second cut of the same text finds nothing pending.
    with pytest.raises(cl.ChangelogError, match="nothing to release"):
        cl.cut_release(text, [], version="0.3.0", date="2026-08-31", title="Third")


@pytest.mark.parametrize(
    ("version", "date", "title", "complaint"),
    [
        ("0.1.0", "2026-08-30", "t", "not above"),
        ("0.0.9", "2026-08-30", "t", "not above"),
        ("1.0", "2026-08-30", "t", "MAJOR"),
        ("0.2.0", "30.08.2026", "t", "YYYY"),
        ("0.2.0", "2026-08-30", " ", "title"),
    ],
)
def test_the_cut_refuses_a_bad_heading(version: str, date: str, title: str, complaint: str) -> None:
    with pytest.raises(cl.ChangelogError, match=complaint):
        cl.cut_release(CHANGELOG, [], version=version, date=date, title=title)


PYPROJECT = '[project]\nname = "anyplot"\nversion = "0.1.0"\n'
UV_LOCK = '[[package]]\nname = "other"\nversion = "0.1.0"\n\n[[package]]\nname = "anyplot"\nversion = "0.1.0"\n'
# A dependency pinned at the same version, at the same nesting, is the trap the
# anchor has to survive: only the top-level key is two spaces deep.
PACKAGE_JSON = (
    '{\n  "name": "anyplot-website",\n  "version": "0.1.0",\n  "dependencies": {\n    "react": "0.1.0"\n  }\n}\n'
)


def _write_version_files(root: Path) -> None:
    (root / "pyproject.toml").write_text(PYPROJECT, encoding="utf-8")
    (root / "uv.lock").write_text(UV_LOCK, encoding="utf-8")
    (root / "app").mkdir(exist_ok=True)
    (root / "app" / "package.json").write_text(PACKAGE_JSON, encoding="utf-8")


def test_the_version_lines_are_bumped_exactly_once_each(tmp_path: Path) -> None:
    _write_version_files(tmp_path)
    writes = cl.bump_version_files(tmp_path, version="0.2.0", date="2026-08-30")
    assert writes[tmp_path / "pyproject.toml"] == PYPROJECT.replace("0.1.0", "0.2.0")
    # Only the project's own package block moves, not the other package at the same version.
    assert writes[tmp_path / "uv.lock"] == UV_LOCK.replace(
        '"anyplot"\nversion = "0.1.0"', '"anyplot"\nversion = "0.2.0"'
    )
    # …and in package.json only the top-level key, never the dependency pin.
    assert writes[tmp_path / "app" / "package.json"] == PACKAGE_JSON.replace('"version": "0.1.0"', '"version": "0.2.0"')
    assert '"react": "0.1.0"' in writes[tmp_path / "app" / "package.json"]
    (tmp_path / "pyproject.toml").write_text('name = "anyplot"\n', encoding="utf-8")
    with pytest.raises(cl.ChangelogError, match="pyproject.toml: expected exactly one"):
        cl.bump_version_files(tmp_path, version="0.2.0", date="2026-08-30")


LINKS = (
    "[Unreleased]: https://github.com/MarkusNeusinger/anyplot/compare/v0.1.0...HEAD\n"
    "[0.1.0]: https://github.com/MarkusNeusinger/anyplot/releases/tag/v0.1.0\n"
)


def test_the_compare_links_follow_the_cut() -> None:
    """`release.md` calls this step easy to forget, which is why it is not a step."""
    out = cl.repoint_compare_links(CHANGELOG + "\n" + LINKS, version="0.2.0")
    assert "[Unreleased]: https://github.com/MarkusNeusinger/anyplot/compare/v0.2.0...HEAD\n" in out
    assert "[0.2.0]: https://github.com/MarkusNeusinger/anyplot/compare/v0.1.0...v0.2.0\n" in out
    assert "[0.1.0]: https://github.com/MarkusNeusinger/anyplot/releases/tag/v0.1.0\n" in out


def test_a_changelog_without_a_link_block_keeps_none() -> None:
    assert cl.repoint_compare_links(CHANGELOG, version="0.2.0") == CHANGELOG


# --- the PR gate, against a real (throwaway) repository ----------------------


def _git(root: Path, *args: str, when: str | None = None) -> str:
    env = {**os.environ, "GIT_AUTHOR_DATE": when or "", "GIT_COMMITTER_DATE": when or ""}
    if when is None:
        env.pop("GIT_AUTHOR_DATE"), env.pop("GIT_COMMITTER_DATE")
    done = subprocess.run(
        ["git", "-c", "user.name=t", "-c", "user.email=t@example.org", "-c", "commit.gpgsign=false", *args],
        cwd=root,
        env=env,
        check=True,
        capture_output=True,
        text=True,
    )
    return done.stdout


def _commit_all(root: Path, message: str, when: str | None = None) -> None:
    _git(root, "add", "-A")
    _git(root, "commit", "-q", "-m", message, when=when)


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    """A throwaway repository: `main` with a changelog, the fragment README, a source file — and `topic` checked out."""
    _git(tmp_path, "init", "-q", "-b", "main")
    (tmp_path / "CHANGELOG.md").write_text(CHANGELOG, encoding="utf-8")
    (tmp_path / "changelog.d").mkdir()
    (tmp_path / "changelog.d" / "README.md").write_text("# fragments\n", encoding="utf-8")
    (tmp_path / "core.py").write_text("x = 1\n", encoding="utf-8")
    (tmp_path / "plots" / "scatter-basic").mkdir(parents=True)
    (tmp_path / "plots" / "scatter-basic" / "specification.md").write_text("# spec\n", encoding="utf-8")
    _write_version_files(tmp_path)
    _commit_all(tmp_path, "base")
    _git(tmp_path, "checkout", "-q", "-b", "topic")
    return tmp_path


def test_a_pr_with_a_fragment_passes(repo: Path) -> None:
    (repo / "core.py").write_text("x = 2\n", encoding="utf-8")
    (repo / "changelog.d" / "topic.md").write_text(FRAGMENT, encoding="utf-8")
    _commit_all(repo, "change")
    assert cl.check_pr("main", root=repo) == []


def test_a_pr_without_a_fragment_fails_and_names_the_way_out(repo: Path) -> None:
    (repo / "core.py").write_text("x = 2\n", encoding="utf-8")
    _commit_all(repo, "change")
    (problem,) = cl.check_pr("main", root=repo)
    assert "no changelog fragment" in problem
    assert cl.SKIP_LABEL in problem


def test_a_catalogue_only_pr_needs_no_fragment(repo: Path) -> None:
    """What the automated plot pipeline produces, and what a release summarizes
    in one italic *Catalog* line rather than per PR."""
    (repo / "plots" / "scatter-basic" / "specification.md").write_text("# spec, revised\n", encoding="utf-8")
    _commit_all(repo, "spec")
    assert cl.check_pr("main", root=repo) == []


def test_a_pipeline_pr_that_strays_outside_plots_still_needs_one(repo: Path) -> None:
    """The exemption is the path, not the author — a pipeline PR that edits a
    workflow has left the class the *Catalog* line covers."""
    (repo / "plots" / "scatter-basic" / "specification.md").write_text("# spec, revised\n", encoding="utf-8")
    (repo / "core.py").write_text("x = 2\n", encoding="utf-8")
    _commit_all(repo, "spec and code")
    (problem,) = cl.check_pr("main", root=repo)
    assert "no changelog fragment" in problem


def test_a_branch_with_no_changes_passes(repo: Path) -> None:
    assert cl.check_pr("main", root=repo) == []


def test_an_unknown_base_stops_the_gate_instead_of_passing_it(repo: Path) -> None:
    """An unfetched base would diff as empty and read as 'nothing changed' — the one silent pass the gate must not have."""
    (repo / "core.py").write_text("x = 2\n", encoding="utf-8")
    _commit_all(repo, "change")
    with pytest.raises(cl.ChangelogError, match="git diff .*origin/nowhere"):
        cl.check_pr("origin/nowhere", root=repo)


def test_a_bullet_written_into_unreleased_directly_is_refused(repo: Path) -> None:
    """Even next to a proper fragment: the shared spot is what the fragments retire."""
    text = (repo / "CHANGELOG.md").read_text(encoding="utf-8")
    text = text.replace("### Changed\n\n", "### Changed\n\n- **Sneaked in.** Not a fragment.\n")
    (repo / "CHANGELOG.md").write_text(text, encoding="utf-8")
    (repo / "changelog.d" / "topic.md").write_text(FRAGMENT, encoding="utf-8")
    _commit_all(repo, "both")
    (problem,) = cl.check_pr("main", root=repo)
    assert "belongs in a fragment" in problem
    assert "Sneaked in" in problem


def test_a_second_bullet_under_a_title_unreleased_already_holds_is_refused(repo: Path) -> None:
    """Identity by title has to COUNT: a copy of an entry already there is added too."""
    old = "- **An old-style entry.** Written before the fragments existed (#0).\n"
    text = (repo / "CHANGELOG.md").read_text(encoding="utf-8")
    text = text.replace(old, old + "- **An old-style entry.** Sneaked in under a title already there.\n")
    (repo / "CHANGELOG.md").write_text(text, encoding="utf-8")
    (repo / "changelog.d" / "topic.md").write_text(FRAGMENT, encoding="utf-8")
    _commit_all(repo, "a second bullet under the same title")
    (problem,) = cl.check_pr("main", root=repo)
    assert "belongs in a fragment" in problem
    assert "Sneaked in" in problem


def test_correcting_a_bullet_unreleased_already_carries_passes(repo: Path) -> None:
    """A re-worded entry is a CHANGED bullet, not an added one — the gate refuses only new titles."""
    text = (repo / "CHANGELOG.md").read_text(encoding="utf-8")
    text = text.replace("Written before the fragments existed (#0).", "Written before they existed, said better (#0).")
    (repo / "CHANGELOG.md").write_text(text, encoding="utf-8")
    (repo / "changelog.d" / "topic.md").write_text(FRAGMENT, encoding="utf-8")
    _commit_all(repo, "correct the wording")
    assert cl.check_pr("main", root=repo) == []


def test_a_correction_that_reflows_a_wrapped_title_is_not_a_new_bullet(repo: Path) -> None:
    """The one case a line-by-line identity gets wrong: the title itself runs over the wrap."""
    _git(repo, "checkout", "-q", "main")
    old = "- **An old-style entry.** Written before the fragments existed (#0)."
    wrapped = "- **An old-style entry with a title long enough to run onto the\n  next line.** Its body (#0)."
    base = (repo / "CHANGELOG.md").read_text(encoding="utf-8").replace(old, wrapped)
    (repo / "CHANGELOG.md").write_text(base, encoding="utf-8")
    _commit_all(repo, "a wrapped title")
    _git(repo, "checkout", "-q", "-b", "reflow")

    reflowed = (
        "- **An old-style entry with a title long enough to run\n  onto the next line.** Its body, corrected (#0)."
    )
    (repo / "CHANGELOG.md").write_text(base.replace(wrapped, reflowed), encoding="utf-8")
    (repo / "changelog.d" / "topic.md").write_text(FRAGMENT, encoding="utf-8")
    _commit_all(repo, "reflow the correction")
    assert cl.check_pr("main", root=repo) == []


def test_the_cut_orders_fragments_by_their_commit_and_passes_the_gate(repo: Path) -> None:
    """Newest first, an uncommitted fragment newest of all; the cut PR itself deletes fragments and passes."""
    _git(repo, "checkout", "-q", "main")  # two merged PRs left their fragments on main, in this order
    (repo / "changelog.d" / "first.md").write_text("### Added\n\n- **First.**\n", encoding="utf-8")
    _commit_all(repo, "first", when="2026-08-30T10:00:00+00:00")
    (repo / "changelog.d" / "second.md").write_text("### Added\n\n- **Second.**\n", encoding="utf-8")
    _commit_all(repo, "second", when="2026-08-30T10:00:01+00:00")
    _git(repo, "checkout", "-q", "-b", "cut")
    (repo / "changelog.d" / "third.md").write_text("### Added\n\n- **Third.**\n", encoding="utf-8")
    assert [f.path.name for f in cl.load_fragments(repo)] == ["third.md", "second.md", "first.md"]

    release = cl.plan_release(version="0.2.0", date="2026-08-30", title="Cut", root=repo)
    assert (repo / "changelog.d" / "first.md").exists(), "planning writes nothing"
    cl.apply_release(release)
    assert sorted(p.name for p in (repo / "changelog.d").iterdir()) == ["README.md"]
    changelog = (repo / "CHANGELOG.md").read_text(encoding="utf-8")
    assert "- **Third.**\n- **Second.**\n- **First.**\n\n### Changed\n\n- **An old-style entry.**" in changelog
    assert '"version": "0.2.0"' in (repo / "app" / "package.json").read_text(encoding="utf-8")
    _commit_all(repo, "release")
    assert cl.check_pr("main", root=repo) == []
    with pytest.raises(cl.ChangelogError, match="nothing to release"):
        cl.plan_release(version="0.3.0", date="2026-08-31", title="Again", root=repo)


def test_a_cut_that_folds_only_old_style_bullets_is_still_a_cut(repo: Path) -> None:
    """Before any fragment exists, [Unreleased] alone feeds the cut — no fragment deleted, yet no fragment demanded."""
    release = cl.plan_release(version="0.2.0", date="2026-08-30", title="Cut", root=repo)
    cl.apply_release(release)
    _commit_all(repo, "release")
    assert cl.check_pr("main", root=repo) == []
