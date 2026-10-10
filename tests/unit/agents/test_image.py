"""The agents image (agents/Dockerfile) and its deploy (agents/cloudbuild.yaml), held against the code.

Docker runs only in CI (`.github/workflows/ci-image.yml`, job `agents-image`) and Cloud
Build only after the merge, so these tests read the two files instead:

* **The COPY list.** Every non-Python file the service reads (the files an import of
  `agents.main` opens under the repository, every file in `agents/anyplot/prompts/` and
  the footer-strip fonts) must reach the runtime stage at its repository path under
  `/app`, because the readers resolve them from `__file__`: a runtime-stage COPY has to
  carry it there, and the root `.dockerignore`, an allowlist, has to admit it into the
  build context. A file that misses either fails the build at its import check, after
  the merge; this test fails before.
* **The deploy.** The model, judge and library substitutions default to the settings
  defaults, every `$NAME` in a step is a substitution or a Cloud Build built-in (a bash
  variable must be escaped as `$$NAME`, or Cloud Build refuses the whole config), every
  `AGENT_*` variable the deploy sets is a real setting, and the flags the design fixes
  are there.
"""

import importlib.metadata
import json
import os
import re
import shlex
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest
import yaml

from agents.anyplot import policy
from agents.anyplot.render import watermark
from agents.anyplot.settings import AgentSettings


REPO_ROOT = Path(__file__).resolve().parents[3]
DOCKERFILE = REPO_ROOT / "agents" / "Dockerfile"
DOCKERIGNORE = REPO_ROOT / ".dockerignore"
CLOUDBUILD = REPO_ROOT / "agents" / "cloudbuild.yaml"
RENDERER_CLOUDBUILD = REPO_ROOT / "agents" / "renderer" / "cloudbuild.yaml"

CLOUD_BUILD_BUILTINS = frozenset({"PROJECT_ID", "PROJECT_NUMBER", "BUILD_ID", "LOCATION"})
"""The built-in substitutions these configs use; anything else unescaped must be a `_NAME`."""

DEPLOYED_SETTINGS = frozenset(
    {
        "AGENT_PROVIDER",
        "AGENT_MODEL",
        "AGENT_JUDGE_MODEL",
        "AGENT_LOCATION",
        "AGENT_LIBRARIES",
        "AGENT_RENDERER",
        "AGENT_RENDER_URL",
        "AGENT_ALLOWED_CALLERS",
        "AGENT_SERVICE_URLS",
    }
)
"""The `AGENT_*` variables the deploy sets. The budgets and limits are left out on purpose:
the deployed code's settings defaults apply, so a budget change is a code change and a PR."""

_PROBE = """
import json, os, sys

opened = set()


def hook(event, args):
    if event == "open" and args and isinstance(args[0], (str, bytes, os.PathLike)):
        opened.add(os.path.realpath(os.fsdecode(args[0])))


sys.addaudithook(hook)
import agents.main

skip = tuple(os.path.realpath(prefix) + os.sep for prefix in {sys.prefix, sys.base_prefix})
print(json.dumps(sorted(path for path in opened if not path.startswith(skip))))
"""
"""Imports `agents.main` in a fresh interpreter and prints every file it opened outside the venv."""


def _adk_installed() -> bool:
    try:
        importlib.metadata.version("google-adk")
    except importlib.metadata.PackageNotFoundError:
        return False
    return True


requires_adk = pytest.mark.skipif(not _adk_installed(), reason="google-adk is not installed (uv sync --extra agents)")


# --- Dockerfile and .dockerignore --------------------------------------------------------


def _instructions(text: str) -> list[tuple[str, str]]:
    """The Dockerfile's instructions as `(KEYWORD, arguments)`, continuation lines joined, comments dropped."""
    instructions: list[tuple[str, str]] = []
    pending = ""
    for line in text.splitlines():
        stripped = line.strip()
        if not pending and (not stripped or stripped.startswith("#")):
            continue
        if stripped.endswith("\\"):
            pending += stripped[:-1] + " "
            continue
        full = (pending + stripped).strip()
        pending = ""
        keyword, _, arguments = full.partition(" ")
        instructions.append((keyword.upper(), arguments.strip()))
    return instructions


def _runtime_stage() -> list[tuple[str, str]]:
    """The instructions after the last FROM: the stage Cloud Run runs."""
    instructions = _instructions(DOCKERFILE.read_text(encoding="utf-8"))
    last_from = max(index for index, (keyword, _) in enumerate(instructions) if keyword == "FROM")
    return instructions[last_from + 1 :]


def _copied_paths() -> list[tuple[str, str]]:
    """`(source, destination)` of every runtime-stage COPY from the build context, both repo-relative.

    The destination is the path under WORKDIR /app; a COPY of a directory maps the
    whole tree, so `("agents/", "agents/")` carries every file below it.
    """
    pairs: list[tuple[str, str]] = []
    for keyword, arguments in _runtime_stage():
        if keyword != "COPY":
            continue
        tokens = shlex.split(arguments)
        if any(token.startswith("--from") for token in tokens):
            continue
        operands = [token for token in tokens if not token.startswith("--")]
        *sources, destination = operands
        destination = destination.removeprefix("./")
        for source in sources:
            if source.endswith("/"):
                pairs.append((source, destination))
            elif destination.endswith("/"):
                pairs.append((source, destination + Path(source).name))
            else:
                pairs.append((source, destination))
    return pairs


def _lands_at_its_own_path(relative: str, pairs: list[tuple[str, str]]) -> bool:
    for source, destination in pairs:
        if source.endswith("/"):
            if relative.startswith(source) and destination == source:
                return True
        elif relative == source and destination == source:
            return True
    return False


def _pattern(pattern: str) -> re.Pattern[str]:
    """A `.dockerignore` pattern as a regex: `**` spans directories, `*` and `?` stay within one."""
    out: list[str] = []
    index = 0
    while index < len(pattern):
        if pattern.startswith("**/", index):
            out.append("(?:.*/)?")
            index += 3
        elif pattern.startswith("**", index):
            out.append(".*")
            index += 2
        elif pattern[index] == "*":
            out.append("[^/]*")
            index += 1
        elif pattern[index] == "?":
            out.append("[^/]")
            index += 1
        elif pattern[index] == "[":
            end = pattern.index("]", index)
            out.append(pattern[index : end + 1])
            index = end + 1
        else:
            out.append(re.escape(pattern[index]))
            index += 1
    return re.compile("".join(out) + r"\Z")


def dockerignore_admits(relative: str) -> bool:
    """Whether the root `.dockerignore` lets `relative` into the build context.

    Docker's rule: a pattern matches a path when it matches the path or one of its
    parent directories, and the last matching pattern wins; a `!` pattern re-admits.
    """
    parts = relative.split("/")
    candidates = ["/".join(parts[: count + 1]) for count in range(len(parts))]
    admitted = True
    for line in DOCKERIGNORE.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        negate = line.startswith("!")
        regex = _pattern(line.removeprefix("!").strip().strip("/"))
        if any(regex.match(candidate) for candidate in candidates):
            admitted = negate
    return admitted


@pytest.fixture(scope="module")
def opened_at_import() -> set[str]:
    """The repo-relative non-Python files an import of `agents.main` opens, in a fresh interpreter."""
    env = {name: value for name, value in os.environ.items() if not name.upper().startswith("AGENT_")}
    env["PYTHON_DOTENV_DISABLED"] = "1"
    result = subprocess.run(
        [sys.executable, "-c", _PROBE], cwd=REPO_ROOT, env=env, capture_output=True, text=True, timeout=120, check=False
    )
    assert result.returncode == 0, result.stderr[-2000:]
    root = str(REPO_ROOT.resolve()) + os.sep
    opened: set[str] = set()
    for path in json.loads(result.stdout.strip().splitlines()[-1]):
        if not path.startswith(root) or not Path(path).is_file():
            continue
        relative = path[len(root) :]
        if "__pycache__" in relative or relative.endswith((".py", ".pyc")):
            continue
        opened.add(relative)
    return opened


def _read_by_the_service() -> set[str]:
    """The files the service reads lazily too: every own prompt file and both fonts."""
    root = REPO_ROOT.resolve()
    files = {path.resolve() for path in policy.PROMPTS_DIR.iterdir() if path.is_file()}
    files |= {path.resolve() for path in watermark.FONT_FILES.values()}
    return {str(path.relative_to(root)) for path in files}


class TestDockerignoreMatcher:
    """The matcher above, on paths whose fate the root `.dockerignore` states in its comments."""

    @pytest.mark.parametrize(
        "relative",
        ["agents/main.py", "core/palette.py", "prompts/library/seaborn.md", "prompts/quality-criteria.md", "uv.lock"],
    )
    def test_admits(self, relative: str) -> None:
        assert dockerignore_admits(relative)

    @pytest.mark.parametrize(
        "relative",
        [
            "agents/evals/fixtures/cases/scatter-basic-matplotlib/data.csv",
            "agents/evals/.cases/case-1/data.csv",
            "agents/anyplot/__pycache__/agent.cpython-313.pyc",
            "plots/scatter-basic/specification.md",
            "prompts/workflow-prompts/impl-generate-claude.md",
            ".env",
            "agents/.env",
            "app/package.json",
        ],
    )
    def test_refuses(self, relative: str) -> None:
        assert not dockerignore_admits(relative)


class TestCopyList:
    def test_runtime_stage_works_in_app(self) -> None:
        assert ("WORKDIR", "/app") in _runtime_stage()

    @requires_adk
    def test_the_import_probe_sees_the_prompt_sources_and_the_fonts(self, opened_at_import: set[str]) -> None:
        """Guard the probe itself: an audit hook that recorded nothing would pass the test below vacuously."""
        expected = {
            "agents/anyplot/prompts/root.md",
            "agents/anyplot/prompts/refusals.yaml",
            "agents/anyplot/render/fonts/JetBrainsMono-Regular.ttf",
            f"prompts/{policy.STYLE_GUIDE}",
            f"prompts/{policy.QUALITY_CRITERIA}",
            "prompts/library/matplotlib.md",
        }
        assert expected <= opened_at_import

    @requires_adk
    def test_every_file_the_service_reads_reaches_the_image(self, opened_at_import: set[str]) -> None:
        pairs = _copied_paths()
        needed = opened_at_import | _read_by_the_service()

        not_copied = sorted(path for path in needed if not _lands_at_its_own_path(path, pairs))
        not_admitted = sorted(path for path in needed if not dockerignore_admits(path))

        assert not not_copied, f"agents/Dockerfile copies these to no path under /app the service reads: {not_copied}"
        assert not not_admitted, f"the root .dockerignore keeps these out of the build context: {not_admitted}"

    def test_the_eval_harness_stays_out_of_the_image(self) -> None:
        """Its promoted cases hold users' data (agents/evals/.cases)."""
        assert not dockerignore_admits("agents/evals/.cases/x/data.csv")
        assert all(not source.startswith("agents/evals") for source, _ in _copied_paths())

    def test_installs_the_agents_extra_and_serves_uvicorn_as_a_user(self) -> None:
        text = DOCKERFILE.read_text(encoding="utf-8")
        runtime = _runtime_stage()

        assert "uv sync --frozen --extra agents" in text
        assert [arguments for keyword, arguments in _instructions(text) if keyword == "FROM"] == [
            "python:3.13-slim AS builder",
            "python:3.13-slim",
        ]
        users = [arguments for keyword, arguments in runtime if keyword == "USER"]
        assert users and users[-1] not in ("root", "0")
        command = json.loads(next(arguments for keyword, arguments in runtime if keyword == "CMD"))
        assert command == [".venv/bin/uvicorn", "agents.main:app", "--host", "0.0.0.0", "--port", "8080"]


# --- Cloud Build -------------------------------------------------------------------------


def _config(path: Path) -> dict[str, Any]:
    loaded = yaml.safe_load(path.read_text(encoding="utf-8"))
    assert isinstance(loaded, dict)
    return loaded


def _step(config: dict[str, Any], step_id: str) -> str:
    step = next(step for step in config["steps"] if step.get("id") == step_id)
    return "\n".join(step["args"])


def _references(text: str) -> set[str]:
    """Every `$NAME` and `${NAME}` Cloud Build would substitute; `$$` is its escape for a literal `$`."""
    unescaped = text.replace("$$", "")
    return {match.group(1) or match.group(2) for match in re.finditer(r"\$(?:\{(\w+)\}|(\w+))", unescaped)}


def _env_vars(deploy: str) -> dict[str, str]:
    flag = re.search(r'"--update-env-vars=\^\|\^([^"]*)"', deploy)
    assert flag, "the deploy sets its variables with one --update-env-vars=^|^... flag"
    return dict(item.split("=", 1) for item in flag.group(1).split("|"))


class TestCloudBuild:
    def test_substitution_defaults(self) -> None:
        defaults = AgentSettings.model_fields

        assert _config(CLOUDBUILD)["substitutions"] == {
            "_SERVICE_NAME": "anyplot-agents",
            "_REGION": "europe-west4",
            "_SERVICE_ACCOUNT": "anyplot-agents@anyplot.iam.gserviceaccount.com",
            "_ALLOWED_CALLERS": "",
            "_AUDIENCES": "",
            "_RENDER_URL": "",
            "_PROVIDER": defaults["provider"].default,
            "_MODEL": defaults["model"].default,
            "_JUDGE_MODEL": defaults["judge_model"].default,
            "_LIBRARIES": ",".join(defaults["libraries"].default),
            "_MIN_INSTANCES": "0",
            "_SMOKE_AUTH": "true",
        }

    @pytest.mark.parametrize("path", [CLOUDBUILD, RENDERER_CLOUDBUILD], ids=["agents", "renderer"])
    def test_every_reference_is_a_substitution_or_a_builtin(self, path: Path) -> None:
        """Cloud Build refuses a config that names an undefined substitution or defines an unused one."""
        config = _config(path)
        text = "\n".join(
            [arg for step in config["steps"] for arg in step.get("args", [])] + list(config.get("images", []))
        )
        references = _references(text)
        user = {name for name in references if name.startswith("_")}

        assert references - user <= CLOUD_BUILD_BUILTINS, "escape bash variables as $$NAME"
        assert user == set(config["substitutions"])

    def test_deploy_flags(self) -> None:
        deploy = _step(_config(CLOUDBUILD), "deploy")

        for flag in (
            "gcloud run deploy ${_SERVICE_NAME}",
            "--execution-environment=gen2",
            "--no-allow-unauthenticated",
            "--service-account=${_SERVICE_ACCOUNT}",
            "--min-instances=${_MIN_INSTANCES}",
            "--max-instances=1",
            "--concurrency=20",
            "--timeout=900",
            "TRAFFIC=(--no-traffic)",
            "--tag=candidate",
            "--revision-suffix=b$BUILD_ID",
        ):
            assert flag in deploy, flag
        for absent in ("--allow-unauthenticated", "--sandbox-launcher", "--set-env-vars", "--set-secrets"):
            assert absent not in deploy, absent

    def test_deploy_environment(self) -> None:
        env = _env_vars(_step(_config(CLOUDBUILD), "deploy"))

        assert env["ENVIRONMENT"] == "production"
        assert env["AGENT_RENDERER"] == "remote"
        assert env["AGENT_LOCATION"] == env["GOOGLE_CLOUD_LOCATION"] == "eu"
        assert env["AGENT_PROVIDER"] == "${_PROVIDER}"
        assert env["AGENT_MODEL"] == "${_MODEL}"
        assert env["AGENT_JUDGE_MODEL"] == "${_JUDGE_MODEL}"
        assert env["AGENT_LIBRARIES"] == "${_LIBRARIES}"
        assert env["AGENT_RENDER_URL"] == "${_RENDER_URL}"
        assert env["AGENT_ALLOWED_CALLERS"] == "${_ALLOWED_CALLERS}"
        assert env["ADK_CAPTURE_MESSAGE_CONTENT_IN_SPANS"] == "false"
        agent_vars = {name for name in env if name.startswith("AGENT_")}
        assert agent_vars == DEPLOYED_SETTINGS
        assert all(name.removeprefix("AGENT_").lower() in AgentSettings.model_fields for name in agent_vars)

    def test_smoke_and_promote(self) -> None:
        config = _config(CLOUDBUILD)
        smoke = _step(config, "smoke")

        assert '"$$URL/v1/status"' in smoke
        assert 'test "$$code" = "403"' in smoke
        assert '--impersonate-service-account="${_SERVICE_ACCOUNT}"' in smoke
        assert '"${_PROVIDER}" "${_MODEL}" "${_LIBRARIES}"' in smoke
        assert "--to-revisions=${_SERVICE_NAME}-b$BUILD_ID=100" in _step(config, "promote")
        assert next(step for step in config["steps"] if step["id"] == "promote")["waitFor"] == ["smoke"]
