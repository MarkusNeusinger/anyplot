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


def _load(config: str) -> dict[str, Any]:
    loaded: dict[str, Any] = yaml.safe_load((REPO_ROOT / config).read_text(encoding="utf-8"))
    return loaded


def test_api_runs_as_the_caller_the_agents_service_accepts() -> None:
    """anyplot-api deploys as its dedicated account, and anyplot-agents admits exactly that account.

    A mismatch passes every PR check and both deploys, then the BFF gets 403 on every agent call.
    """
    api = _load("api/cloudbuild.yaml")
    runtime = api["substitutions"]["_RUNTIME_SERVICE_ACCOUNT"]
    deploy_args = [arg for step in api["steps"] for arg in step.get("args", [])]

    assert runtime == "anyplot-api@anyplot.iam.gserviceaccount.com"
    assert "--service-account=${_RUNTIME_SERVICE_ACCOUNT}" in deploy_args
    assert _load("agents/cloudbuild.yaml")["substitutions"]["_API_CALLER"] == runtime


def test_every_api_revision_gets_the_turnstile_secret() -> None:
    """Production refuses the bot-checked calls without it and keeps the public chat shut (api/turnstile.py).

    Bound on every deploy rather than by hand, so no revision can lose it; additive, so the hand-attached
    ORIGIN_SECRET survives the deploy.
    """
    deploy_args = [arg for step in _load("api/cloudbuild.yaml")["steps"] for arg in step.get("args", [])]
    secrets = [arg for arg in deploy_args if arg.startswith("--update-secrets=")]

    assert len(secrets) == 1 and not any(arg.startswith("--set-secrets") for arg in deploy_args)
    bindings = dict(pair.split("=", 1) for pair in secrets[0].removeprefix("--update-secrets=").split(","))
    assert bindings["TURNSTILE_SECRET_KEY"] == "TURNSTILE_SECRET_KEY:latest"


def test_the_api_smoke_runs_the_public_lane_probes() -> None:
    """The lane, the public status call and the bot check live in api/deploy_smoke_public.sh; the step must call it."""
    smoke = next(step for step in _load("api/cloudbuild.yaml")["steps"] if step.get("id") == "smoke")
    script = "\n".join(smoke["args"])

    assert (
        'ORIGIN_SECRET="$$ORIGIN_SECRET" bash api/deploy_smoke_public.sh "$$URL" "${_AGENT_ENABLED}" '
        '"${_AGENT_PUBLIC_ENABLED}"' in script
    )
    probes = (REPO_ROOT / "api" / "deploy_smoke_public.sh").read_text(encoding="utf-8")
    assert "X-Turnstile-Token: XXXX.DUMMY.TOKEN.XXXX" in probes and '"bot_check_failed"' in probes


def test_the_site_is_never_built_without_the_turnstile_site_key() -> None:
    """The API refuses chat sessions and feedback without a token, so a bundle without the key breaks them all."""
    app = _load("app/cloudbuild.yaml")
    steps = {step.get("id"): step for step in app["steps"]}

    assert "_VITE_TURNSTILE_SITE_KEY" in app["substitutions"]
    assert 'test -n "${_VITE_TURNSTILE_SITE_KEY}"' in "\n".join(steps["check-config"]["args"])
    assert steps["build-image"]["waitFor"] == ["check-config"]
    assert "VITE_TURNSTILE_SITE_KEY=${_VITE_TURNSTILE_SITE_KEY}" in steps["build-image"]["args"]


@pytest.mark.parametrize("config", CONFIGS)
def test_every_step_argument_fits_cloud_build(config: str) -> None:
    loaded = _load(config)
    too_long = [
        f"step {index} ({step.get('id', step.get('name'))}) arg {position}: {len(arg)} characters"
        for index, step in enumerate(loaded["steps"])
        for position, arg in enumerate(step.get("args", []))
        if len(arg) > ARG_LIMIT
    ]
    assert not too_long, f"Cloud Build refuses an argument over {ARG_LIMIT:,} characters: {too_long}"
