"""Implementation PRs never change dependency files.

#9398 (qrcode-basic, makie) ran `Pkg.add`, committed the re-resolved
Manifest.toml and Project.toml with its implementation, and moved Makie from
0.22.10 to 0.21.9 for every Julia implementation. impl-generate.yml now fails a
generation whose commit changes a dependency file, and impl-merge.yml refuses to
merge an implementation PR that does, which also covers repair and review
commits. The merge gate runs here against a scratch origin with a stub `gh`.
"""

from __future__ import annotations

import os
import re
import subprocess
from pathlib import Path
from typing import Any

import pytest
import yaml


WORKFLOWS_DIR = Path(__file__).resolve().parents[3] / ".github" / "workflows"
SPEC, LIB = "qrcode-basic", "makie"
BRANCH = f"implementation/{SPEC}/{LIB}"
IMPL = f"plots/{SPEC}/implementations/julia/{LIB}.jl"
META = f"plots/{SPEC}/metadata/julia/{LIB}.yaml"
DEPENDENCY_FILES = [
    "pyproject.toml",
    "uv.lock",
    "package.json",
    "package-lock.json",
    "Project.toml",
    "Manifest.toml",
    ".python-version",
]
GUARD_RE = re.compile(r"grep -E '(\(\^\|/\)\([^']*\)\$)'")

FAKE_GH = """#!/bin/sh
printf '%s\\n' "$*" >> "$FAKE_GH_LOG"
case "$*" in
  *"--json state"*) echo OPEN ;;
esac
exit 0
"""


def _script(workflow: str, name: str) -> str:
    data = yaml.safe_load((WORKFLOWS_DIR / workflow).read_text(encoding="utf-8"))
    (step,) = [s for job in data["jobs"].values() for s in job.get("steps", []) if s.get("name") == name]
    return str(step["run"])


GENERATE = _script("impl-generate.yml", "Create library metadata file")
MERGE = _script("impl-merge.yml", "Validate PR completeness before merge")
# impl-generate's guard, cut out of its long step: from the diff to the end of its `if`.
GENERATE_GUARD = GENERATE[
    GENERATE.index("CHANGED=$(git diff --no-renames --name-only origin/main...HEAD)") : GENERATE.index(
        "# Restore plot files after git operations"
    )
]


def test_both_guards_match_the_same_dependency_files() -> None:
    (generate,) = GUARD_RE.findall(GENERATE)
    (merge,) = GUARD_RE.findall(MERGE)
    assert generate == merge
    for name in DEPENDENCY_FILES:
        assert re.search(merge, name), name
        assert re.search(merge, f"app/{name}"), name
    assert not re.search(merge, IMPL)
    assert not re.search(merge, META)


def test_generate_checks_the_pushed_commit_before_writing_metadata() -> None:
    guard = GENERATE.index("git diff --no-renames --name-only origin/main...HEAD")
    assert GENERATE.index('git checkout -B "$BRANCH" "origin/$BRANCH"') < guard
    assert guard < GENERATE.index('git add "$METADATA_FILE"')


def _env(tmp: Path, **extra: str) -> dict[str, str]:
    """No user or system git config (signing, hooks) and no inherited GIT_* state."""
    empty = tmp / "gitconfig"
    empty.touch()
    env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
    env.update(GIT_CONFIG_GLOBAL=str(empty), GIT_CONFIG_NOSYSTEM="1", **extra)
    return env


class Origin:
    """A bare origin whose main pins dependencies, and a workspace on the implementation branch."""

    def __init__(self, tmp: Path) -> None:
        self.tmp = tmp
        self.origin = tmp / "origin.git"
        self.ws = tmp / "workspace"
        seed = tmp / "seed"
        seed.mkdir()
        self.git(seed, "init", "-q", "-b", "main")
        self.commit(seed, {"Manifest.toml": "Makie 0.22.10\n", "uv.lock": "matplotlib 3.11.2\n"}, "main")
        subprocess.run(["git", "clone", "-q", "--bare", str(seed), str(self.origin)], check=True, env=_env(tmp))
        subprocess.run(["git", "clone", "-q", str(self.origin), str(self.ws)], check=True, env=_env(tmp))
        self.git(self.ws, "checkout", "-q", "-b", BRANCH)
        self.commit(self.ws, {IMPL: "using CairoMakie\n", META: "library: makie\n"}, "feat(makie): implement")
        self.bin = tmp / "bin"
        self.bin.mkdir()
        (self.bin / "gh").write_text(FAKE_GH, encoding="utf-8")
        (self.bin / "gh").chmod(0o755)
        self.log = tmp / "gh.log"

    def git(self, repo: Path, *args: str) -> str:
        result = subprocess.run(
            ["git", "-C", str(repo), "-c", "user.name=t", "-c", "user.email=t@t", *args],
            capture_output=True,
            text=True,
            env=_env(self.tmp),
            check=True,
        )
        return result.stdout.strip()

    def commit(self, repo: Path, files: dict[str, str], message: str) -> None:
        for path, text in files.items():
            (repo / path).parent.mkdir(parents=True, exist_ok=True)
            (repo / path).write_text(text, encoding="utf-8")
        self.git(repo, "add", "-A")
        self.git(repo, "commit", "-q", "-m", message)

    def push(self) -> None:
        self.git(self.ws, "push", "-q", "origin", f"HEAD:refs/heads/{BRANCH}")

    def move_main(self, files: dict[str, str]) -> None:
        other = self.tmp / "other"
        subprocess.run(["git", "clone", "-q", str(self.origin), str(other)], check=True, env=_env(self.tmp))
        self.commit(other, files, "deps: bump")
        self.git(other, "push", "-q", "origin", "HEAD:refs/heads/main")

    def run_generate_guard(self) -> subprocess.CompletedProcess[str]:
        script = self.tmp / "guard.sh"
        script.write_text(GENERATE_GUARD, encoding="utf-8")
        return subprocess.run(
            ["bash", "--noprofile", "--norc", "-eo", "pipefail", str(script)],
            cwd=self.ws,
            env=_env(self.tmp),
            capture_output=True,
            text=True,
        )

    def run_merge_gate(self) -> subprocess.CompletedProcess[str]:
        script = self.tmp / "step.sh"
        script.write_text(MERGE.replace("/tmp/", f"{self.tmp}/"), encoding="utf-8")
        values: dict[str, Any] = {
            "PATH": f"{self.bin}{os.pathsep}{os.environ['PATH']}",
            "FAKE_GH_LOG": str(self.log),
            "GH_TOKEN": "unused",
            "SPEC_ID": SPEC,
            "LANGUAGE": "julia",
            "LIBRARY": LIB,
            "EXT": ".jl",
            "BRANCH": BRANCH,
            "PR_NUM": "9398",
            "REPOSITORY": "o/r",
        }
        # As Actions runs a `run:` step.
        return subprocess.run(
            ["bash", "--noprofile", "--norc", "-eo", "pipefail", str(script)],
            cwd=self.ws,
            env=_env(self.tmp, **values),
            capture_output=True,
            text=True,
        )

    def comments(self) -> list[str]:
        calls = self.log.read_text(encoding="utf-8").splitlines() if self.log.exists() else []
        return [call for call in calls if call.startswith("pr comment")]


@pytest.fixture
def origin(tmp_path: Path) -> Origin:
    return Origin(tmp_path)


def test_generate_guard_passes_an_implementation_only_commit(origin: Origin) -> None:
    result = origin.run_generate_guard()
    assert result.returncode == 0, result.stdout + result.stderr


def test_generate_guard_fails_a_commit_that_changes_a_lock_file(origin: Origin) -> None:
    origin.commit(origin.ws, {"Manifest.toml": "Makie 0.21.9\n"}, "Pkg.add")
    result = origin.run_generate_guard()
    assert result.returncode == 1
    assert "::error::The implementation commit changes dependency files: Manifest.toml" in result.stdout


def _rename_pin(origin: Origin) -> None:
    """Move the pinned Manifest.toml to a name the guard pattern does not match."""
    origin.git(origin.ws, "mv", "Manifest.toml", "Manifest.toml.bak")
    origin.git(origin.ws, "commit", "-q", "-m", "rename the pin away")


def test_generate_guard_fails_a_commit_that_renames_a_lock_file_away(origin: Origin) -> None:
    _rename_pin(origin)
    result = origin.run_generate_guard()
    assert result.returncode == 1
    assert "dependency files: Manifest.toml" in result.stdout


def test_generate_guard_fails_closed_when_the_diff_fails(origin: Origin) -> None:
    origin.commit(origin.ws, {"Manifest.toml": "Makie 0.21.9\n"}, "Pkg.add")
    origin.git(origin.ws, "update-ref", "-d", "refs/remotes/origin/main")
    result = origin.run_generate_guard()
    assert result.returncode != 0
    assert "::error::" not in result.stdout


def test_merge_gate_passes_an_implementation_only_pr(origin: Origin) -> None:
    origin.push()
    result = origin.run_merge_gate()
    assert result.returncode == 0, result.stdout + result.stderr
    assert origin.comments() == []


def test_merge_gate_refuses_a_pr_that_changes_a_lock_file(origin: Origin) -> None:
    origin.commit(origin.ws, {"Manifest.toml": "Makie 0.21.9\n", "Project.toml": "QRCoders\n"}, "Pkg.add")
    origin.push()
    result = origin.run_merge_gate()
    assert result.returncode == 1
    assert "::error::PR #9398 changes dependency files: Manifest.toml Project.toml" in result.stdout
    (comment,) = origin.comments()
    assert comment.startswith("pr comment 9398 --body **Merge blocked:**")
    assert "Manifest.toml Project.toml" in comment


def test_merge_gate_refuses_a_pr_that_renames_a_lock_file_away(origin: Origin) -> None:
    _rename_pin(origin)
    origin.push()
    result = origin.run_merge_gate()
    assert result.returncode == 1
    assert "::error::PR #9398 changes dependency files: Manifest.toml" in result.stdout
    (comment,) = origin.comments()
    assert "Manifest.toml" in comment


def test_merge_gate_ignores_lock_changes_that_came_from_main(origin: Origin) -> None:
    origin.push()
    origin.move_main({"uv.lock": "matplotlib 3.11.3\n"})
    origin.git(origin.ws, "pull", "-q", "--no-rebase", "--no-edit", "origin", "main")
    origin.push()
    result = origin.run_merge_gate()
    assert result.returncode == 0, result.stdout + result.stderr
    assert origin.comments() == []
