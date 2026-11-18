"""The merge audit of the open-pr skill: what it reports for a merge, and its exit code.

Every test builds a throwaway repository under `tmp_path` and runs the script the way an agent runs
it, as a process inside that repository. Nothing here touches this checkout.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[3]
SCRIPT = REPO_ROOT / ".claude" / "skills" / "open-pr" / "scripts" / "merge_audit.py"

# Far enough apart that a change to the title line and an added closing paragraph are two hunks.
BASE_DOC = "\n".join(["title: draft", *[f"line {n}" for n in range(1, 13)], "closing"]) + "\n"
CLOSING = "main adds a closing paragraph"


# A developer's own signing key or hooks must not decide whether the throwaway commits succeed.
_GIT_SETTINGS = ["user.name=t", "user.email=t@example.com", "commit.gpgsign=false", "core.hooksPath=/dev/null"]


def _git(repo: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    command = ["git", "-C", str(repo), *[part for setting in _GIT_SETTINGS for part in ("-c", setting)], *args]
    return subprocess.run(command, check=check, capture_output=True, text=True)


def _commit(repo: Path, message: str, files: dict[str, str]) -> None:
    for name, text in files.items():
        (repo / name).write_text(text, encoding="utf-8")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", message)


def _audit(repo: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run([sys.executable, str(SCRIPT), *args], cwd=repo, capture_output=True, text=True, check=False)


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    """`main` and `feature` both change the title; `main` also adds a paragraph and changes a second file."""
    path = tmp_path / "repo"
    path.mkdir()
    _git(path, "init", "-q", "-b", "main")
    _commit(path, "base", {"doc.md": BASE_DOC, "other.txt": "one\n"})
    _git(path, "branch", "start")
    _git(path, "checkout", "-q", "-b", "feature")
    _commit(path, "feature title", {"doc.md": BASE_DOC.replace("title: draft", "title: feature")})
    _git(path, "checkout", "-q", "main")
    _commit(
        path,
        "main title, closing paragraph, other file",
        {"doc.md": BASE_DOC.replace("title: draft", "title: main") + CLOSING + "\n", "other.txt": "one\ntwo\n"},
    )
    _git(path, "checkout", "-q", "feature")
    return path


def _merge_main_with_conflict(repo: Path) -> None:
    merged = _git(repo, "merge", "--no-edit", "main", check=False)
    assert merged.returncode != 0, "the fixture's merge is meant to conflict"


def test_a_whole_file_taken_from_one_side_is_reported_as_a_loss_outside_the_conflict(repo: Path) -> None:
    """`git checkout --ours <file>` drops the other side's clean hunk in that file: the case the audit exists for."""
    _merge_main_with_conflict(repo)
    _git(repo, "checkout", "--ours", "doc.md")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "--no-edit")

    done = _audit(repo, "start")

    assert done.returncode == 1, done.stdout + done.stderr
    assert "DROPPED OUTSIDE A CONFLICT in doc.md: 1 line(s) the merged-in side added" in done.stdout
    assert f"| {CLOSING}" in done.stdout
    # The title line is the conflict itself: reported, but as the resolution's choice.
    assert "resolved against the merged-in side in doc.md: 1 line(s) of the conflict itself" in done.stdout
    assert "1 merge(s) with something to look at" in done.stdout


def test_a_conflict_resolved_inside_its_markers_is_clean(repo: Path) -> None:
    """Taking one side of the conflicting line and keeping the other side's clean hunk is no finding."""
    _merge_main_with_conflict(repo)
    resolved = BASE_DOC.replace("title: draft", "title: feature") + CLOSING + "\n"
    (repo / "doc.md").write_text(resolved, encoding="utf-8")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "--no-edit")

    done = _audit(repo, "start")

    assert done.returncode == 0, done.stdout + done.stderr
    assert "DROPPED OUTSIDE A CONFLICT" not in done.stdout
    assert "resolved against the merged-in side in doc.md: 1 line(s) of the conflict itself" in done.stdout
    assert "0 merge(s) with something to look at" in done.stdout


def test_a_cleanly_merged_file_changed_during_the_merge_is_reported(repo: Path) -> None:
    """A file with no conflict that differs from the mechanical merge was edited by hand or taken from a side."""
    _merge_main_with_conflict(repo)
    resolved = BASE_DOC.replace("title: draft", "title: feature") + CLOSING + "\n"
    (repo / "doc.md").write_text(resolved, encoding="utf-8")
    # `--ours` does nothing to a path without a conflict; the branch's version comes from `HEAD`.
    _git(repo, "checkout", "HEAD", "--", "other.txt")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "--no-edit")

    done = _audit(repo, "start")

    assert done.returncode == 1, done.stdout + done.stderr
    assert "CHANGED BY HAND OR A SIDE TAKEN (a mechanical merge has no conflict here): other.txt" in done.stdout
    assert "= the branch's version, whole" in done.stdout


def test_a_path_with_a_space_and_an_umlaut_is_reported_under_its_own_name(repo: Path) -> None:
    """git quotes such a path by default; a quoted name would not be found again in the trees."""
    name = "über uns.md"
    _git(repo, "checkout", "-q", "main")
    _commit(repo, "a page on main", {name: "eins\n"})
    _git(repo, "checkout", "-q", "feature")
    _merge_main_with_conflict(repo)
    resolved = BASE_DOC.replace("title: draft", "title: feature") + CLOSING + "\n"
    (repo / "doc.md").write_text(resolved, encoding="utf-8")
    (repo / name).write_text("zwei\n", encoding="utf-8")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "--no-edit")

    done = _audit(repo, "start")

    assert done.returncode == 1, done.stdout + done.stderr
    assert f"(a mechanical merge has no conflict here): {name}" in done.stdout


def test_a_change_against_a_deletion_is_named_as_a_conflict_without_markers(repo: Path) -> None:
    """Such a conflict leaves no markers in the file, so the audit says it cannot tell the hunks apart."""
    _git(repo, "checkout", "-q", "-b", "removes", "start")
    _git(repo, "rm", "-q", "other.txt")
    _git(repo, "commit", "-q", "-m", "remove the second file")
    merged = _git(repo, "merge", "--no-edit", "main", check=False)
    assert merged.returncode != 0, "main changed the file this branch deleted"
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "--no-edit")

    done = _audit(repo, "start")

    assert done.returncode == 1, done.stdout + done.stderr
    assert "CONFLICT WITHOUT MARKERS (a deletion, a rename or a binary file), compare by hand: other.txt" in done.stdout
    assert "DROPPED OUTSIDE A CONFLICT" not in done.stdout


def test_a_merge_without_a_conflict_has_nothing_lost(repo: Path) -> None:
    _git(repo, "checkout", "-q", "-b", "quiet", "start")
    _commit(repo, "a file of its own", {"own.txt": "own\n"})
    _git(repo, "merge", "-q", "--no-edit", "main")

    done = _audit(repo, "start")

    assert done.returncode == 0, done.stdout + done.stderr
    assert "1 merge commit(s) to audit" in done.stdout
    assert "nothing lost" in done.stdout


def test_a_branch_without_a_merge_is_an_empty_audit(repo: Path) -> None:
    done = _audit(repo, "start", "feature")

    assert done.returncode == 0, done.stdout + done.stderr
    assert "0 merge commit(s) to audit" in done.stdout


def test_a_missing_base_and_an_unknown_ref_are_usage_errors(repo: Path) -> None:
    """Exit 2 keeps "the audit did not run" apart from "the audit found something"."""
    assert _audit(repo).returncode == 2
    unknown = _audit(repo, "no-such-ref")
    assert unknown.returncode == 2
    assert "no-such-ref" in unknown.stderr
