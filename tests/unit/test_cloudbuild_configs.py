"""Every Cloud Build config of the repository stays inside Cloud Build's own limits.

Cloud Build refuses the whole build, before its first step runs, when one step argument is longer than 10,000
characters ("invalid build: invalid .steps field: build step 7 arg 1 too long (max: 10000)"). PB-2a's plotly
probe took the renderer's inline smoke step to 11,347 characters; every PR check passed, the agents service
deployed, and the renderer did not (build dc1cf3ae, 2026-11-01). The length is measured on the config as
written, before Cloud Build substitutes `$NAME` and `${NAME}`.
"""

import subprocess
from pathlib import Path
from typing import Any

import pytest
import yaml


REPO_ROOT = Path(__file__).resolve().parents[2]
ARG_LIMIT = 10_000
# Every tracked config at any depth; git, not a recursive glob, because a checkout's untracked
# `.claude/worktrees/` and `node_modules/` hold copies that are not this tree's configs.
CONFIGS = sorted(
    subprocess.run(
        ["git", "ls-files", "--", "*cloudbuild*.yaml", "*cloudbuild*.yml"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.split()
)


def test_every_deploy_config_is_checked() -> None:
    assert {
        "agents/cloudbuild.yaml",
        "agents/renderer/cloudbuild.yaml",
        "api/cloudbuild.yaml",
        "app/cloudbuild.yaml",
    } <= set(CONFIGS)


@pytest.mark.parametrize("config", CONFIGS)
def test_every_step_argument_fits_cloud_build(config: str) -> None:
    loaded: dict[str, Any] = yaml.safe_load((REPO_ROOT / config).read_text(encoding="utf-8"))
    too_long = [
        f"step {index} ({step.get('id', step.get('name'))}) arg {position}: {len(arg)} characters"
        for index, step in enumerate(loaded["steps"])
        for position, arg in enumerate(step.get("args", []))
        if len(arg) > ARG_LIMIT
    ]
    assert not too_long, f"Cloud Build refuses an argument over {ARG_LIMIT:,} characters: {too_long}"
