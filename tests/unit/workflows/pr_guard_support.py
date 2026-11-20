"""What the step tests need to run a step behind the pull request guard.

Every job that takes a pull request stages `automation/scripts/pr_guard.py`
and the library list under `$RUNNER_TEMP/pr-guard` ("Stage the pull request
guard") and checks each pull request against them before it reads the pull
request's content. A step test that runs a later step stages the same files
with `stage_guard`, and gives its fake pull requests the fields the guard
reads with `own_fields`; without them the guard refuses, as it should.
"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path
from typing import Any

from core.constants import SUPPORTED_LIBRARIES


REPO_ROOT = Path(__file__).resolve().parents[3]
GUARD = REPO_ROOT / "automation" / "scripts" / "pr_guard.py"
CONSTANTS = REPO_ROOT / "core" / "constants.py"
LIBRARIES = " ".join(sorted(SUPPORTED_LIBRARIES))
HEAD_SHA = "a" * 40


def own_fields(repo: str = "owner/repo", head_sha: str = HEAD_SHA) -> dict[str, Any]:
    """The fields besides number and branch that make a fake pull request the pipeline's own in `repo`."""
    owner, name = repo.split("/")
    return {
        "isCrossRepository": False,
        "headRepository": {"name": name},
        "headRepositoryOwner": {"login": owner},
        "headRefOid": head_sha,
        "author": {"login": "app/github-actions", "is_bot": True},
        "baseRefName": "main",
    }


def own_pr(number: int, branch: str, repo: str = "owner/repo", **extra: Any) -> dict[str, Any]:
    return {"number": number, "headRefName": branch, **own_fields(repo), **extra}


def stage_guard(runner_temp: Path) -> Path:
    """`$RUNNER_TEMP/pr-guard` as "Stage the pull request guard" leaves it."""
    staged = runner_temp / "pr-guard"
    (staged / "core").mkdir(parents=True, exist_ok=True)
    shutil.copyfile(GUARD, staged / "pr_guard.py")
    shutil.copyfile(CONSTANTS, staged / "core" / "constants.py")
    (staged / "libraries").write_text(LIBRARIES + "\n", encoding="utf-8")
    return staged


def commit_guard_sources(repo: Path, env: dict[str, str]) -> str:
    """Commit the guard and the constants into the git repository `repo`; return the commit (a GUARD_REF)."""
    for source, rel in ((GUARD, "automation/scripts/pr_guard.py"), (CONSTANTS, "core/constants.py")):
        target = repo / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)

    def git(*args: str) -> str:
        return subprocess.run(
            ["git", *args], cwd=repo, env=env, check=True, capture_output=True, text=True
        ).stdout.strip()

    git("add", "automation/scripts/pr_guard.py", "core/constants.py")
    git(
        "-c",
        "user.name=test",
        "-c",
        "user.email=test@example.invalid",
        "-c",
        "commit.gpgsign=false",
        "commit",
        "-q",
        "-m",
        "guard sources",
    )
    return git("rev-parse", "HEAD")
