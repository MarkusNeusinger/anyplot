"""Model routing in the implementation pipeline workflows.

impl-generate.yml resolves one model per (spec, library) pair: an explicit
`model` input always wins; without one ("auto", or the label trigger) the pair's
first implementation runs on opus and a regeneration on sonnet. The resolved
value is threaded into the review and every repair of the PR.

The routing script runs for real here, against a throwaway git repository whose
`origin/main` holds a few implementations. The rest are content guards for
wiring that has no local execution loop.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
from pathlib import Path
from typing import Any

import pytest
import yaml


REPO_ROOT = Path(__file__).parent.parent.parent.parent
WORKFLOWS_DIR = REPO_ROOT / ".github" / "workflows"
EXPRESSION = re.compile(r"\$\{\{\s*(.+?)\s*\}\}")
MODELS = {"auto", "haiku", "sonnet", "opus"}

# Implementations present on the fake origin/main.
ON_MAIN = (
    "plots/spec-a/implementations/python/matplotlib.py",
    "plots/spec-a/implementations/r/ggplot2.R",
    "plots/spec-a/implementations/julia/makie.jl",
    "plots/spec-a/implementations/javascript/d3.js",
    "plots/spec-a/implementations/javascript/muix.tsx",
)
# Present in the working tree only: must not count as "already on main".
WORKING_TREE_ONLY = "plots/spec-a/implementations/python/seaborn.py"


def _workflow(filename: str) -> dict[Any, Any]:
    return yaml.safe_load((WORKFLOWS_DIR / filename).read_text(encoding="utf-8"))


def _steps(filename: str) -> list[dict[str, Any]]:
    return [step for job in _workflow(filename)["jobs"].values() for step in job.get("steps", [])]


def _step(filename: str, name: str) -> dict[str, Any]:
    matches = [s for s in _steps(filename) if s.get("name") == name]
    assert len(matches) == 1, f"expected exactly one step named {name!r} in {filename}"
    return matches[0]


def _dispatch_inputs(filename: str) -> dict[str, Any]:
    workflow = _workflow(filename)
    on = workflow.get("on") or workflow.get(True)  # YAML reads a bare `on:` as True
    return on["workflow_dispatch"]["inputs"]


def _render(script: str, context: dict[str, str]) -> str:
    """Substitute `${{ expr }}` the way Actions does before the shell runs."""

    def substitute(match: re.Match[str]) -> str:
        expr = match.group(1)
        assert expr in context, f"unexpected expression in the script: {expr}"
        return context[expr]

    return EXPRESSION.sub(substitute, script)


def _clean_env(**extra: str) -> dict[str, str]:
    env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
    env.update(extra)
    return env


def _outputs(path: Path) -> dict[str, str]:
    return dict(line.split("=", 1) for line in path.read_text(encoding="utf-8").splitlines() if "=" in line)


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    """A git repo whose `origin/main` holds ON_MAIN (and nothing else)."""
    root = tmp_path / "repo"
    root.mkdir()
    env = _clean_env()

    def git(*args: str) -> None:
        subprocess.run(["git", *args], cwd=root, env=env, check=True, capture_output=True)

    git("init", "-q")
    for rel in ON_MAIN:
        path = root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("# impl\n", encoding="utf-8")
    git("add", "-A")
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
        "main",
    )
    git("update-ref", "refs/remotes/origin/main", "HEAD")
    (root / WORKING_TREE_ONLY).write_text("# local only\n", encoding="utf-8")
    return root


def _run_extract_inputs(
    repo: Path, tmp_path: Path, *, library: str, model: str = "auto", label_trigger: bool = False, spec: str = "spec-a"
) -> dict[str, str]:
    """Run impl-generate's "Extract inputs" step and return its outputs."""
    dispatch = not label_trigger
    context = {
        "github.event_name": "workflow_dispatch" if dispatch else "issues",
        "inputs.specification_id": spec if dispatch else "",
        "inputs.library": library if dispatch else "",
        "inputs.issue_number": "",
        "inputs.model": model if dispatch else "",
        "github.event.issue.number": "" if dispatch else "42",
    }
    script = _render(_step("impl-generate.yml", "Extract inputs")["run"], context)
    return _run_script(
        script,
        repo,
        tmp_path,
        LABEL_NAME="" if dispatch else f"generate:{library}",
        ISSUE_TITLE="" if dispatch else f"[{spec}] Some plot",
    )


def _run_script(script: str, repo: Path, tmp_path: Path, **env: str) -> dict[str, str]:
    """Run a step script in `repo` the way Actions does and return its outputs."""
    assert "${{" not in script, "render the expressions first"
    out = tmp_path / "github_output"
    out.unlink(missing_ok=True)
    result = subprocess.run(
        ["bash", "-eo", "pipefail", "-c", script],
        cwd=repo,
        env=_clean_env(GITHUB_OUTPUT=str(out), **env),
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    return _outputs(out)


class TestImplGenerateRouting:
    @pytest.mark.parametrize(
        ("library", "expected"),
        [
            ("matplotlib", "sonnet"),  # python, on main
            ("ggplot2", "sonnet"),  # .R
            ("makie", "sonnet"),  # .jl
            ("d3", "sonnet"),  # .js
            ("muix", "sonnet"),  # .tsx, not .js
            ("plotly", "opus"),  # not on main
            ("chartjs", "opus"),
            ("seaborn", "opus"),  # only in the working tree, not on origin/main
        ],
    )
    def test_auto_routes_first_runs_to_opus_and_regenerations_to_sonnet(self, repo, tmp_path, library, expected):
        assert _run_extract_inputs(repo, tmp_path, library=library)["model"] == expected

    def test_unknown_spec_is_a_first_run(self, repo, tmp_path):
        assert _run_extract_inputs(repo, tmp_path, library="matplotlib", spec="spec-new")["model"] == "opus"

    @pytest.mark.parametrize(
        ("library", "model"),
        [
            ("matplotlib", "opus"),  # regeneration pinned to opus
            ("matplotlib", "haiku"),
            ("plotly", "sonnet"),  # first run pinned to sonnet
            ("plotly", "haiku"),
        ],
    )
    def test_explicit_model_wins(self, repo, tmp_path, library, model):
        assert _run_extract_inputs(repo, tmp_path, library=library, model=model)["model"] == model

    def test_empty_model_routes_like_auto(self, repo, tmp_path):
        assert _run_extract_inputs(repo, tmp_path, library="plotly", model="")["model"] == "opus"
        assert _run_extract_inputs(repo, tmp_path, library="matplotlib", model="")["model"] == "sonnet"

    @pytest.mark.parametrize(("library", "expected"), [("matplotlib", "sonnet"), ("plotly", "opus")])
    def test_label_trigger_routes(self, repo, tmp_path, library, expected):
        outputs = _run_extract_inputs(repo, tmp_path, library=library, label_trigger=True)
        assert outputs["specification_id"] == "spec-a"
        assert outputs["library"] == library
        assert outputs["model"] == expected


class TestImplGenerateWiring:
    def test_checkout_runs_before_the_routing(self):
        names = [s.get("name") for s in _steps("impl-generate.yml")]
        assert names.index("Checkout repository") < names.index("Extract inputs")
        assert names.count("Checkout repository") == 1

    def test_only_extract_inputs_reads_the_raw_input(self):
        """Every consumer reads the resolved value, never `inputs.model` itself."""
        for step in _steps("impl-generate.yml"):
            if step.get("name") == "Extract inputs":
                continue
            assert "inputs.model" not in json.dumps(step), step.get("name")

    @pytest.mark.parametrize("name", ["Run Claude Code to generate implementation", "Retry Claude (on failure)"])
    def test_claude_steps_use_the_resolved_model(self, name):
        args = _step("impl-generate.yml", name)["with"]["claude_args"]
        assert args.startswith("--model ${{ steps.inputs.outputs.model }} ")

    @pytest.mark.parametrize(
        "name", ["Create library metadata file", "Trigger review workflow", "Handle generation failure"]
    )
    def test_metadata_review_and_retry_get_the_resolved_model(self, name):
        assert _step("impl-generate.yml", name)["env"]["MODEL"] == "${{ steps.inputs.outputs.model }}"

    def test_retry_forwards_the_resolved_model_explicitly(self):
        script = _step("impl-generate.yml", "Handle generation failure")["run"]
        assert '-f model="${MODEL}"' in script


def _run_review_extract(
    repo: Path, tmp_path: Path, *, library: str, model_input: str = "", payload: str = ""
) -> dict[str, str]:
    """Run impl-review's "Extract PR info" step against a fake `gh`."""
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir(exist_ok=True)
    pr = {"headRefName": f"implementation/spec-a/{library}", "headRefOid": "0" * 40, "body": "**Parent Issue:** #42"}
    gh = bin_dir / "gh"
    gh.write_text(f"#!/bin/sh\ncat <<'EOF'\n{json.dumps(pr)}\nEOF\n", encoding="utf-8")
    gh.chmod(0o755)
    # The step parks gh's output under /tmp; keep the test inside tmp_path.
    script = _step("impl-review.yml", "Extract PR info")["run"].replace("/tmp/", f"{tmp_path}/")
    return _run_script(
        script,
        repo,
        tmp_path,
        PATH=f"{bin_dir}{os.pathsep}{os.environ['PATH']}",
        GH_TOKEN="unused",
        PR_NUMBER="7",
        MODEL_INPUT=model_input,
        MODEL_PAYLOAD=payload,
    )


class TestImplReviewRescueRouting:
    """impl-generate always sends its resolved model; rescues send none."""

    @pytest.mark.parametrize(("model_input", "payload"), [("", "opus"), ("", "haiku"), ("sonnet", ""), ("opus", "")])
    def test_threaded_or_explicit_model_wins(self, repo, tmp_path, model_input, payload):
        # plotly is a first run, so routing alone would say opus.
        outputs = _run_review_extract(repo, tmp_path, library="plotly", model_input=model_input, payload=payload)
        assert outputs["model"] == (model_input or payload)

    @pytest.mark.parametrize(("model_input", "payload"), [("auto", ""), ("", ""), ("", "auto")])
    @pytest.mark.parametrize(
        ("library", "expected"), [("matplotlib", "sonnet"), ("muix", "sonnet"), ("plotly", "opus"), ("seaborn", "opus")]
    )
    def test_rescue_without_a_model_routes(self, repo, tmp_path, model_input, payload, library, expected):
        outputs = _run_review_extract(repo, tmp_path, library=library, model_input=model_input, payload=payload)
        assert outputs["library"] == library
        assert outputs["model"] == expected

    def test_library_match_is_exact(self, repo, tmp_path):
        # "d3" is on main; a library whose name only starts the same is not.
        assert _run_review_extract(repo, tmp_path, library="d3")["model"] == "sonnet"
        assert _run_review_extract(repo, tmp_path, library="d")["model"] == "opus"


LANG_EXT = {
    "matplotlib": ("python", ".py"),
    "plotly": ("python", ".py"),
    "ggplot2": ("r", ".R"),
    "muix": ("javascript", ".tsx"),
}


def _run_repair_resolve(repo: Path, tmp_path: Path, *, library: str, model_input: str) -> dict[str, str]:
    language, ext = LANG_EXT[library]
    return _run_script(
        _step("impl-repair.yml", "Resolve model")["run"],
        repo,
        tmp_path,
        MODEL_INPUT=model_input,
        SPEC_ID="spec-a",
        LIBRARY=library,
        LANGUAGE=language,
        EXT=ext,
    )


class TestImplRepairRouting:
    @pytest.mark.parametrize(
        ("library", "expected"),
        [("matplotlib", "sonnet"), ("ggplot2", "sonnet"), ("muix", "sonnet"), ("plotly", "opus")],
    )
    @pytest.mark.parametrize("model_input", ["auto", ""])
    def test_rescue_without_a_model_routes(self, repo, tmp_path, library, expected, model_input):
        assert _run_repair_resolve(repo, tmp_path, library=library, model_input=model_input)["model"] == expected

    @pytest.mark.parametrize("model_input", ["haiku", "sonnet", "opus"])
    def test_threaded_model_wins(self, repo, tmp_path, model_input):
        assert _run_repair_resolve(repo, tmp_path, library="plotly", model_input=model_input)["model"] == model_input

    def test_resolution_runs_before_claude_and_after_language(self):
        names = [s.get("name") for s in _steps("impl-repair.yml")]
        assert (
            names.index("Derive language + extension from library")
            < names.index("Resolve model")
            < names.index("Run Claude Code to repair implementation")
        )

    def test_consumers_read_the_resolved_model(self):
        for name in ["Run Claude Code to repair implementation", "Retry Claude (on failure)"]:
            assert _step("impl-repair.yml", name)["with"]["claude_args"].startswith(
                "--model ${{ steps.model.outputs.model }} "
            )
        assert _step("impl-repair.yml", "Re-trigger review")["env"]["MODEL"] == "${{ steps.model.outputs.model }}"
        # A crash before "Resolve model" still hands the retry a valid choice.
        assert (
            _step("impl-repair.yml", "Handle repair failure")["env"]["MODEL"]
            == "${{ steps.model.outputs.model || inputs.model || 'auto' }}"
        )
        for step in _steps("impl-repair.yml"):
            if step.get("name") not in {"Resolve model", "Handle repair failure"}:
                assert "inputs.model" not in json.dumps(step), step.get("name")


class TestModelInputs:
    @pytest.mark.parametrize(
        "filename", ["impl-generate.yml", "bulk-generate.yml", "daily-regen.yml", "impl-review.yml", "impl-repair.yml"]
    )
    def test_model_input_defaults_to_auto(self, filename):
        model = _dispatch_inputs(filename)["model"]
        assert model["default"] == "auto"
        assert model["options"][0] == "auto"
        assert set(model["options"]) == MODELS

    @pytest.mark.parametrize(
        ("filename", "step"),
        [
            ("bulk-generate.yml", "Dispatch impl-generate for each matrix item (paced)"),
            ("daily-regen.yml", "Dispatch bulk-generate with change_requests"),
        ],
    )
    def test_forwarded_model_falls_back_to_auto(self, filename, step):
        assert _step(filename, step)["env"]["MODEL"] == "${{ inputs.model || 'auto' }}"

    @pytest.mark.parametrize(
        "filename", ["impl-generate.yml", "bulk-generate.yml", "daily-regen.yml", "impl-review.yml", "impl-repair.yml"]
    )
    def test_no_silent_sonnet_fallback(self, filename):
        """A missing model means "route", never a hardcoded sonnet."""
        text = (WORKFLOWS_DIR / filename).read_text(encoding="utf-8")
        assert "|| 'sonnet'" not in text
        assert ":-sonnet}" not in text

    def test_daily_regen_run_name_shows_auto(self):
        assert "github.event.inputs.model || 'auto'" in _workflow("daily-regen.yml")["run-name"]

    def test_babysit_queue_defaults_to_auto(self):
        script = (REPO_ROOT / ".claude" / "skills" / "babysit-pipeline" / "run_queue.sh").read_text(encoding="utf-8")
        assert 'MODEL="${MODEL:-auto}"' in script


class TestDailyRegenPreflight:
    @pytest.mark.parametrize(
        "name", ["Spec polish (autonomous, opens PR with auto-merge)", "Cross-library similarity audit"]
    )
    def test_preflight_steps_run_on_sonnet(self, name):
        args = _step("daily-regen.yml", name)["with"]["claude_args"]
        assert args.startswith("--model sonnet ")

    def test_no_step_runs_on_haiku(self):
        for step in _steps("daily-regen.yml"):
            assert "haiku" not in step.get("with", {}).get("claude_args", ""), step.get("name")
        assert "--model haiku" not in (WORKFLOWS_DIR / "daily-regen.yml").read_text(encoding="utf-8")
