"""The agents image (agents/Dockerfile) and its deploy (agents/cloudbuild.yaml), held against the code.

Docker runs only in CI (`.github/workflows/ci-image.yml`, job `agents-image`) and Cloud
Build only after the merge, so these tests read the two files instead:

* **The COPY list.** Every non-Python file the service reads (the files an import of
  `agents.main` opens under the repository, every file in `agents/anyplot/prompts/` and
  the footer-strip fonts) must reach the runtime stage at its repository path under
  `/app`, because the readers resolve them from `__file__`: a runtime-stage COPY has to
  carry it there, and the root `.dockerignore`, an allowlist, has to admit it into the
  build context. The Dockerfile's build check must read every one of them, so a file
  that misses either fails the build, after the merge; these tests fail before.
* **The deploy.** The model, judge and library substitutions default to the settings
  defaults, every `$NAME` in a step is a substitution or a Cloud Build built-in (a bash
  variable must be escaped as `$$NAME`, or Cloud Build refuses the whole config), every
  `AGENT_*` variable the deploy sets is a real setting, and the flags the design fixes
  are there. The deploy step's script runs as Cloud Build would run it, against a fake
  `gcloud`, so its refusals and the variables it writes are tested, not only read.
"""

import importlib.metadata
import json
import os
import re
import shlex
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest
import yaml

from agents.anyplot import policy
from agents.anyplot.render import harness, watermark
from agents.anyplot.settings import AgentSettings


REPO_ROOT = Path(__file__).resolve().parents[3]
DOCKERFILE = REPO_ROOT / "agents" / "Dockerfile"
RENDERER_DOCKERFILE = REPO_ROOT / "agents" / "renderer" / "Dockerfile"
DOCKERIGNORE = REPO_ROOT / ".dockerignore"
CLOUDBUILD = REPO_ROOT / "agents" / "cloudbuild.yaml"
RENDERER_CLOUDBUILD = REPO_ROOT / "agents" / "renderer" / "cloudbuild.yaml"

CLOUD_BUILD_BUILTINS = frozenset({"PROJECT_ID", "PROJECT_NUMBER", "BUILD_ID", "LOCATION"})
"""The built-in substitutions these configs use; anything else unescaped must be a `_NAME`."""

API_CALLER = "239660669828-compute@developer.gserviceaccount.com"
"""anyplot-api's runtime identity, the Compute Engine default service account (api/cloudbuild.yaml sets none)."""

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
exec(sys.argv[1])

skip = tuple(os.path.realpath(prefix) + os.sep for prefix in {sys.prefix, sys.base_prefix})
print(json.dumps(sorted(path for path in opened if not path.startswith(skip))))
"""
"""Runs the code in its first argument in a fresh interpreter and prints every file it opened outside the venv."""


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


def _opened_by(code: str) -> set[str]:
    """The repo-relative non-Python files `code` opens, in a fresh interpreter without `AGENT_*` variables."""
    env = {name: value for name, value in os.environ.items() if not name.upper().startswith("AGENT_")}
    env["PYTHON_DOTENV_DISABLED"] = "1"
    result = subprocess.run(
        [sys.executable, "-c", _PROBE, code],
        cwd=REPO_ROOT,
        env=env,
        capture_output=True,
        text=True,
        timeout=120,
        check=False,
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


@pytest.fixture(scope="module")
def opened_at_import() -> set[str]:
    """The repo-relative non-Python files an import of `agents.main` opens."""
    return _opened_by("import agents.main")


def _build_check() -> str:
    """The code of the runtime stage's `RUN .venv/bin/python -c "..."`, the build's check for missing files."""
    for keyword, arguments in _runtime_stage():
        tokens = shlex.split(arguments)
        if keyword == "RUN" and tokens[:2] == [".venv/bin/python", "-c"]:
            return tokens[2]
    raise AssertionError('agents/Dockerfile has no `RUN .venv/bin/python -c "..."` build check')


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
            "agents/anyplot/.adk/session.db",
            "agents/anyplot/.adk/artifacts/plot.png",
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

    @requires_adk
    def test_the_build_check_reads_every_file_the_service_reads(self) -> None:
        """A missing prompt or font fails the build, not the first request: the judge rubrics, read on first use, too."""
        code = _build_check()
        assert "import agents.main" in code

        unread = sorted(_read_by_the_service() - _opened_by(code))

        assert not unread, (
            f"the build check in agents/Dockerfile never reads {unread}, so the image could ship without them"
        )

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


class TestRendererImage:
    """The renderer image (agents/renderer/Dockerfile) against the harness's fallback fonts; CI builds it."""

    def test_the_renderer_image_installs_every_fallback_family_before_the_cache_bake(self) -> None:
        instructions = _instructions(RENDERER_DOCKERFILE.read_text(encoding="utf-8"))
        starts = [index for index, (keyword, _) in enumerate(instructions) if keyword == "FROM"]
        stages = {
            instructions[start][1]: instructions[start + 1 : end]
            for start, end in zip(starts, [*starts[1:], len(instructions)], strict=True)
        }
        fonts = " ".join(arguments for keyword, arguments in stages["python:3.13-slim AS fonts"] if keyword == "RUN")
        runtime = stages["python:3.13-slim"]

        # The file stem of each family: `Noto Sans CJK JP` is a face of NotoSansCJK-*.ttc.
        stems = [name.replace(" ", "").removesuffix("JP") for name in harness.FALLBACK_FAMILIES]
        assert not [stem for stem in stems if not re.search(rf"(?<![\w-]){stem}(?![\w])", fonts)]
        assert "NotoSansCJK-Bold.ttc" in fonts  # matplotlib synthesises no bold: a bold CJK title needs this face
        assert "/usr/share/doc/fonts-noto-core/copyright" in fonts
        assert "/usr/share/doc/fonts-noto-cjk/copyright" in fonts

        copy = runtime.index(("COPY", "--from=fonts /fonts/noto /usr/share/fonts/noto"))
        bake = next(index for index, (keyword, arguments) in enumerate(runtime) if "harness.check_fonts()" in arguments)
        assert copy < bake and runtime[bake][0] == "RUN"
        assert ("COPY", "--from=fonts /fonts/doc /usr/share/doc/fonts-noto") in runtime


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


def _substituted(text: str, values: dict[str, str]) -> str:
    """`text` as Cloud Build hands it to a step: `$$` becomes `$`, `$NAME` and `${NAME}` become their value."""

    def replace(match: re.Match[str]) -> str:
        if match.group(0) == "$$":
            return "$"
        return values[match.group(1) or match.group(2)]

    return re.sub(r"\$\$|\$\{(\w+)\}|\$(\w+)", replace, text)


FAKE_GCLOUD = """#!/bin/sh
if [ "$1 $2 $3" = "run services describe" ]; then
  if [ -n "$FAKE_SERVICE_URL" ]; then echo "$FAKE_SERVICE_URL"; exit 0; fi
  echo "ERROR: (gcloud.run.services.describe) Cannot find service [anyplot-agents]" >&2
  exit 1
fi
if [ "$1 $2" = "run deploy" ]; then printf '%s\\n' "$@" > "$DEPLOY_ARGS"; exit 0; fi
echo "unexpected gcloud call: $*" >&2
exit 2
"""
"""Answers `run services describe` with `$FAKE_SERVICE_URL` (or not found) and records the `run deploy` arguments."""

RENDER_URL = "https://anyplot-renderer-abc-ez.a.run.app"
SERVICE_URL = "https://anyplot-agents-abc-ez.a.run.app"


def _run_deploy(tmp_path: Path, service_url: str | None, **overrides: str) -> tuple[int, str, list[str] | None]:
    """Run the deploy step's script with the config's substitutions plus `overrides`.

    Returns the exit code, the output, and the arguments of `gcloud run deploy`, or
    None when the step never got that far.
    """
    config = _config(CLOUDBUILD)
    step = next(step for step in config["steps"] if step.get("id") == "deploy")
    values = {**config["substitutions"], **overrides, "PROJECT_ID": "anyplot", "BUILD_ID": "build-1"}
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    gcloud = bin_dir / "gcloud"
    gcloud.write_text(FAKE_GCLOUD, encoding="utf-8")
    gcloud.chmod(0o755)
    deploy_args = tmp_path / "deploy-args"
    env = {
        "PATH": f"{bin_dir}{os.pathsep}{os.environ['PATH']}",
        "FAKE_SERVICE_URL": service_url or "",
        "DEPLOY_ARGS": str(deploy_args),
    }
    result = subprocess.run(
        [step["entrypoint"], *(_substituted(arg, values) for arg in step["args"])],
        cwd=tmp_path,
        env=env,
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    deployed = deploy_args.read_text(encoding="utf-8").splitlines() if deploy_args.exists() else None
    return result.returncode, result.stdout + result.stderr, deployed


def _deployed_env(deployed: list[str]) -> dict[str, str]:
    flag = next(arg for arg in deployed if arg.startswith("--update-env-vars=^|^"))
    return dict(item.split("=", 1) for item in flag.removeprefix("--update-env-vars=^|^").split("|"))


class TestCloudBuild:
    def test_substitution_defaults(self) -> None:
        defaults = AgentSettings.model_fields

        assert _config(CLOUDBUILD)["substitutions"] == {
            "_SERVICE_NAME": "anyplot-agents",
            "_REGION": "europe-west4",
            "_SERVICE_ACCOUNT": "anyplot-agents@anyplot.iam.gserviceaccount.com",
            "_API_CALLER": API_CALLER,
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
            "--timeout=1200",
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
        assert env["AGENT_ALLOWED_CALLERS"] == "${_API_CALLER},${_SERVICE_ACCOUNT}"
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


requires_bash = pytest.mark.skipif(shutil.which("bash") is None, reason="the deploy step is a bash script")


@requires_bash
class TestDeployStep:
    """The deploy step's script, substituted and run as Cloud Build would, against a fake `gcloud`."""

    def test_deploys_a_candidate_the_bff_and_the_smoke_may_call(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        code, output, deployed = _run_deploy(tmp_path, SERVICE_URL, _RENDER_URL=RENDER_URL)

        assert code == 0, output
        assert deployed is not None and "--no-traffic" in deployed
        env = _deployed_env(deployed)
        assert env["AGENT_RENDER_URL"] == RENDER_URL
        assert env["AGENT_SERVICE_URLS"] == SERVICE_URL
        # The variables are valid settings, and the caller list holds both identities.
        for name in [name for name in os.environ if name.upper().startswith("AGENT_")]:
            monkeypatch.delenv(name)
        for name, value in env.items():
            monkeypatch.setenv(name, value)
        settings = AgentSettings()
        assert settings.allowed_callers == [API_CALLER, "anyplot-agents@anyplot.iam.gserviceaccount.com"]
        assert settings.render_url == RENDER_URL

    def test_creates_a_missing_service_with_traffic(self, tmp_path: Path) -> None:
        """gcloud refuses `--no-traffic` on a new service; nothing calls it before AGENT_ENABLED is true."""
        code, output, deployed = _run_deploy(tmp_path, None, _RENDER_URL=RENDER_URL)

        assert code == 0, output
        assert deployed is not None and "--no-traffic" not in deployed
        assert _deployed_env(deployed)["AGENT_SERVICE_URLS"] == ""

    @pytest.mark.parametrize(
        ("overrides", "message"),
        [
            ({"_RENDER_URL": ""}, "_RENDER_URL is empty"),
            ({"_RENDER_URL": RENDER_URL, "_API_CALLER": ""}, "_API_CALLER must be"),
            ({"_RENDER_URL": RENDER_URL, "_API_CALLER": "owner@example.com"}, "_API_CALLER must be"),
            (
                {
                    "_RENDER_URL": RENDER_URL,
                    "_API_CALLER": f"{API_CALLER},anyplot-agents@anyplot.iam.gserviceaccount.com",
                },
                "_API_CALLER must be one email",
            ),
        ],
        ids=["no-renderer", "no-api-caller", "not-a-service-account", "a-list"],
    )
    def test_refuses_before_deploying(self, tmp_path: Path, overrides: dict[str, str], message: str) -> None:
        """`--update-env-vars` names both variables on every build, so a bad value would replace a good one."""
        code, output, deployed = _run_deploy(tmp_path, SERVICE_URL, **overrides)

        assert code != 0 and message in output, output
        assert deployed is None
