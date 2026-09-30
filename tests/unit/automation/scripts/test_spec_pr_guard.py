"""Tests for automation.scripts.spec_pr_guard — the file allowlist spec-create's merge job enforces.

The guard is the only thing between an `approved` label and an unattended
merge of whatever the spec PR carries, so every refusal path is pinned here:
it must refuse anything it is not sure about, and it must pass exactly the
shape spec-create produces.
"""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

import pytest

from automation.scripts.spec_pr_guard import GuardError, allowed_path_re, check_raw_diff, main


SPEC = "scatter-basic"
ZERO = "0" * 40
BLOB = "a" * 40


def entry(path: str, status: str = "A", old_mode: str = "000000", new_mode: str = "100644") -> str:
    old_sha = ZERO if old_mode == "000000" else BLOB
    new_sha = ZERO if new_mode == "000000" else BLOB
    return f":{old_mode} {new_mode} {old_sha} {new_sha} {status}\0{path}\0"


class TestAllowedPaths:
    @pytest.mark.parametrize(
        "path",
        [
            "plots/scatter-basic/specification.md",
            "plots/scatter-basic/specification.yaml",
            "plots/scatter-basic/implementations/.gitkeep",
            "plots/scatter-basic/metadata/.gitkeep",
            "plots/scatter-basic/implementations/python/.gitkeep",
            "plots/scatter-basic/metadata/python/.gitkeep",
        ],
    )
    def test_the_spec_create_shape_is_allowed(self, path: str) -> None:
        assert allowed_path_re(SPEC).fullmatch(path)

    @pytest.mark.parametrize(
        "path",
        [
            "plots/other-spec/specification.md",  # another spec
            "plots/scatter-basic-extra/specification.md",  # a spec id that merely starts the same
            "plots/scatter-basic/specification.yml",
            "plots/scatter-basic/implementations/python/matplotlib.py",
            "plots/scatter-basic/metadata/python/matplotlib.yaml",
            "plots/scatter-basic/implementations/python/deep/.gitkeep",  # two levels below
            "plots/scatter-basic/implementations/Python/.gitkeep",  # not lowercase
            "plots/scatter-basic/.gitkeep",
            ".github/workflows/spec-create.yml",
            "changelog.d/x.md",
            "plots/scatter-basic/specification.md/../../../core/x.py",
        ],
    )
    def test_anything_else_is_refused(self, path: str) -> None:
        assert not allowed_path_re(SPEC).fullmatch(path)

    @pytest.mark.parametrize("spec_id", ["", "Scatter", "scatter_basic", "../core", "a.*", "-scatter", "scatter-"])
    def test_an_invalid_spec_id_is_an_error_not_a_pattern(self, spec_id: str) -> None:
        with pytest.raises(GuardError):
            allowed_path_re(spec_id)


class TestCheckRawDiff:
    def test_a_new_spec_passes(self) -> None:
        raw = entry(f"plots/{SPEC}/specification.md") + entry(f"plots/{SPEC}/specification.yaml")
        assert check_raw_diff(raw, SPEC) == []

    @pytest.mark.parametrize("missing", ["specification.md", "specification.yaml"])
    def test_a_spec_pr_without_both_files_is_a_violation(self, missing: str) -> None:
        present = "specification.yaml" if missing == "specification.md" else "specification.md"
        raw = entry(f"plots/{SPEC}/{present}") + entry(f"plots/{SPEC}/metadata/python/.gitkeep")
        violations = check_raw_diff(raw, SPEC)
        assert len(violations) == 1
        assert f"plots/{SPEC}/{missing}: missing" in violations[0]

    def test_placeholders_and_a_modified_spec_pass(self) -> None:
        raw = (
            entry(f"plots/{SPEC}/specification.md", status="M", old_mode="100644")
            + entry(f"plots/{SPEC}/specification.yaml", status="M", old_mode="100644")
            + entry(f"plots/{SPEC}/implementations/python/.gitkeep")
            + entry(f"plots/{SPEC}/metadata/python/.gitkeep")
        )
        assert check_raw_diff(raw, SPEC) == []

    def test_one_stray_file_is_a_violation(self) -> None:
        raw = (
            entry(f"plots/{SPEC}/specification.md")
            + entry(f"plots/{SPEC}/specification.yaml")
            + entry(".github/workflows/ci-tests.yml", "M", "100644")
        )
        (violation,) = check_raw_diff(raw, SPEC)
        assert '".github/workflows/ci-tests.yml"' in violation
        assert "outside" in violation

    @pytest.mark.parametrize(
        ("status", "old_mode", "new_mode"),
        [
            ("A", "000000", "100755"),  # executable
            ("A", "000000", "120000"),  # symlink
            ("A", "000000", "160000"),  # submodule
            ("M", "100755", "100644"),  # executable bit dropped from a file that had it
            ("T", "100644", "120000"),  # type change
            ("D", "100644", "000000"),  # deletion
        ],
    )
    def test_only_regular_added_or_modified_files_pass(self, status: str, old_mode: str, new_mode: str) -> None:
        raw = entry(f"plots/{SPEC}/specification.md", status, old_mode, new_mode) + entry(
            f"plots/{SPEC}/specification.yaml"
        )
        assert len(check_raw_diff(raw, SPEC)) == 1

    def test_an_empty_diff_is_a_violation(self) -> None:
        assert check_raw_diff("", SPEC) == ["the pull request changes no files"]

    def test_a_path_is_quoted_so_it_cannot_break_out_of_the_comment(self) -> None:
        raw = (
            entry("x`\n## injected")
            + entry(f"plots/{SPEC}/specification.md")
            + entry(f"plots/{SPEC}/specification.yaml")
        )
        (violation,) = check_raw_diff(raw, SPEC)
        assert violation.startswith('"x\\u0060\\n## injected"')
        assert "`" not in violation and "\n" not in violation

    @pytest.mark.parametrize(
        "raw",
        [
            ":000000 100644 A\0plots/scatter-basic/specification.md\0",  # too few fields
            "000000 100644 a b A\0plots/scatter-basic/specification.md\0",  # no leading colon
            entry(f"plots/{SPEC}/specification.md") + ":000000 100644 a b A\0",  # dangling entry
        ],
    )
    def test_an_unparseable_diff_is_an_error_not_a_pass(self, raw: str) -> None:
        with pytest.raises(GuardError):
            check_raw_diff(raw, SPEC)


def _git(repo: Path, *args: str) -> str:
    env = {
        **os.environ,
        "GIT_AUTHOR_NAME": "t",
        "GIT_AUTHOR_EMAIL": "t@example.com",
        "GIT_COMMITTER_NAME": "t",
        "GIT_COMMITTER_EMAIL": "t@example.com",
    }
    return subprocess.run(["git", *args], cwd=repo, check=True, capture_output=True, text=True, env=env).stdout


@pytest.fixture
def repo(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """`main` with one file, and `specification/scatter-basic` checked out on top of it."""
    _git(tmp_path, "init", "-q", "-b", "main")
    (tmp_path / "README.md").write_text("x\n", encoding="utf-8")
    _git(tmp_path, "add", "-A")
    _git(tmp_path, "commit", "-q", "-m", "base")
    _git(tmp_path, "checkout", "-q", "-b", f"specification/{SPEC}")
    (tmp_path / "plots" / SPEC).mkdir(parents=True)
    (tmp_path / "plots" / SPEC / "specification.md").write_text("# spec\n", encoding="utf-8")
    (tmp_path / "plots" / SPEC / "specification.yaml").write_text("specification_id: scatter-basic\n", encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    return tmp_path


def _commit(repo: Path) -> str:
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "spec")
    return _git(repo, "rev-parse", "HEAD").strip()


class TestMain:
    def test_a_clean_spec_branch_exits_zero(self, repo: Path, capsys: pytest.CaptureFixture[str]) -> None:
        head = _commit(repo)
        assert main(["--spec-id", SPEC, "--head", head, "--base", "main"]) == 0
        assert capsys.readouterr().out == ""

    def test_a_stray_file_exits_one_and_names_it(self, repo: Path, capsys: pytest.CaptureFixture[str]) -> None:
        (repo / "README.md").write_text("changed\n", encoding="utf-8")
        head = _commit(repo)
        assert main(["--spec-id", SPEC, "--head", head, "--base", "main"]) == 1
        assert '"README.md"' in capsys.readouterr().out

    def test_an_executable_spec_file_exits_one(self, repo: Path) -> None:
        (repo / "plots" / SPEC / "specification.md").chmod(0o755)
        _git(repo, "config", "core.fileMode", "true")
        head = _commit(repo)
        assert main(["--spec-id", SPEC, "--head", head, "--base", "main"]) == 1

    def test_changes_already_on_main_do_not_count(self, repo: Path) -> None:
        """Three-dot diff: main moving on after the branch point is not the PR's change."""
        head = _commit(repo)
        _git(repo, "checkout", "-q", "main")
        (repo / "README.md").write_text("main moved on\n", encoding="utf-8")
        _commit(repo)
        assert main(["--spec-id", SPEC, "--head", head, "--base", "main"]) == 0

    def test_an_unknown_head_exits_two(self, repo: Path) -> None:
        _commit(repo)
        assert main(["--spec-id", SPEC, "--head", "b" * 40, "--base", "main"]) == 2

    @pytest.mark.parametrize("head", ["HEAD", "abc123", "B" * 40])
    def test_a_head_that_is_not_a_full_sha_exits_two(self, repo: Path, head: str) -> None:
        _commit(repo)
        assert main(["--spec-id", SPEC, "--head", head, "--base", "main"]) == 2

    def test_an_invalid_spec_id_exits_two(self, repo: Path) -> None:
        head = _commit(repo)
        assert main(["--spec-id", "../x", "--head", head, "--base", "main"]) == 2
