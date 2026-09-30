"""Model routing in the implementation pipeline workflows.

impl-generate.yml resolves one generation model per (spec, library) pair: an
explicit `model` input always wins; without one ("auto", or the label trigger)
the pair's first implementation runs on opus and a regeneration on sonnet. The
resolved value is threaded into every repair of the PR and recorded in the PR
body (`**Model:** opus`), which rescues without a model read back. impl-review
resolves it too, only to forward it to repair.

The review model is impl-review's own: every quality review runs on opus
unless a manual dispatch pins `review_model` (carried by that run's own
auto-retry, and by nothing else). A generation pin never reaches the review.

The step scripts run for real here, against a throwaway git repository whose
`origin/main` holds a few implementations, with a fake `gh` on PATH. The rest
are content guards for wiring that has no local execution loop.
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

from automation.scripts import review_retest


REPO_ROOT = Path(__file__).parent.parent.parent.parent
WORKFLOWS_DIR = REPO_ROOT / ".github" / "workflows"
EXPRESSION = re.compile(r"\$\{\{\s*(.+?)\s*\}\}")
MODELS = {"auto", "haiku", "sonnet", "opus"}
REVIEW_MODELS = {"haiku", "sonnet", "opus"}
NO_MAIN_WARNING = "::warning::origin/main unavailable — routing assumes a first run (opus)"
REVIEW_ALIAS = "${{ steps.pr.outputs.review_model_alias }}"
GENERATION_MODEL = "${{ steps.pr.outputs.model }}"
SELF_RETRY_STEPS = ("Validate review output", "Handle review failure")

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

LANG_EXT = {
    "matplotlib": ("python", ".py"),
    "plotly": ("python", ".py"),
    "ggplot2": ("r", ".R"),
    "muix": ("javascript", ".tsx"),
}


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
    if not path.exists():
        return {}
    return dict(line.split("=", 1) for line in path.read_text(encoding="utf-8").splitlines() if "=" in line)


def _fake_gh(tmp_path: Path, body: str) -> str:
    """Install a `gh` stub running `body` (POSIX sh); return the PATH to use."""
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir(exist_ok=True)
    gh = bin_dir / "gh"
    gh.write_text("#!/bin/sh\n" + body, encoding="utf-8")
    gh.chmod(0o755)
    return f"{bin_dir}{os.pathsep}{os.environ['PATH']}"


def _exec(script: str, cwd: Path, tmp_path: Path, **env: str) -> subprocess.CompletedProcess[str]:
    """Run a step script the way Actions does; outputs land in tmp_path."""
    assert "${{" not in script, "render the expressions first"
    for name in ("github_output", "step_summary"):
        (tmp_path / name).unlink(missing_ok=True)
    return subprocess.run(
        ["bash", "-eo", "pipefail", "-c", script],
        cwd=cwd,
        env=_clean_env(
            GITHUB_OUTPUT=str(tmp_path / "github_output"), GITHUB_STEP_SUMMARY=str(tmp_path / "step_summary"), **env
        ),
        capture_output=True,
        text=True,
    )


def _run_script(script: str, cwd: Path, tmp_path: Path, **env: str) -> dict[str, str]:
    result = _exec(script, cwd, tmp_path, **env)
    assert result.returncode == 0, result.stdout + result.stderr
    return _outputs(tmp_path / "github_output")


def _git_repo(root: Path, *, with_origin_main: bool) -> Path:
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
    if with_origin_main:
        git("update-ref", "refs/remotes/origin/main", "HEAD")
    (root / WORKING_TREE_ONLY).write_text("# local only\n", encoding="utf-8")
    return root


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    """A git repo whose `origin/main` holds ON_MAIN (and nothing else)."""
    return _git_repo(tmp_path / "repo", with_origin_main=True)


@pytest.fixture
def repo_without_main(tmp_path: Path) -> Path:
    """The same repo with no `origin/main` and no `origin` remote to fetch it from."""
    return _git_repo(tmp_path / "repo", with_origin_main=False)


# ---------------------------------------------------------------------------
# impl-generate
# ---------------------------------------------------------------------------


def _extract_inputs_script(
    *, library: str, model: str, label_trigger: bool, spec: str, regen_gate: str = "true"
) -> tuple[str, dict[str, str]]:
    dispatch = not label_trigger
    context = {
        "github.event_name": "workflow_dispatch" if dispatch else "issues",
        "inputs.specification_id": spec if dispatch else "",
        "inputs.library": library if dispatch else "",
        "inputs.issue_number": "",
        "inputs.model": model if dispatch else "",
        "github.event.issue.number": "" if dispatch else "42",
    }
    env = {
        "LABEL_NAME": "" if dispatch else f"generate:{library}",
        "ISSUE_TITLE": "" if dispatch else f"[{spec}] Some plot",
        "REGEN_GATE": regen_gate,
    }
    return _render(_step("impl-generate.yml", "Extract inputs")["run"], context), env


def _run_extract_inputs(
    repo: Path,
    tmp_path: Path,
    *,
    library: str,
    model: str = "auto",
    label_trigger: bool = False,
    spec: str = "spec-a",
    regen_gate: str = "true",
) -> dict[str, str]:
    """Run impl-generate's "Extract inputs" step and return its outputs."""
    script, env = _extract_inputs_script(
        library=library, model=model, label_trigger=label_trigger, spec=spec, regen_gate=regen_gate
    )
    return _run_script(script, repo, tmp_path, **env)


def _create_pr_body(tmp_path: Path, *, model: str) -> str:
    """Run impl-generate's "Create Pull Request" step and return the body it sends."""
    body_file = tmp_path / "pr_body.md"
    path = _fake_gh(
        tmp_path,
        'if [ "$1 $2" = "pr list" ]; then exit 0; fi\n'
        'if [ "$1 $2" = "pr create" ]; then\n'
        "  while [ $# -gt 0 ]; do\n"
        '    if [ "$1" = "--body" ]; then printf "%s" "$2" > "$GH_BODY_FILE"; fi\n'
        "    shift\n"
        "  done\n"
        '  echo "https://github.com/owner/repo/pull/123"\n'
        "  exit 0\n"
        "fi\n"
        "exit 1\n",
    )
    script = _render(
        _step("impl-generate.yml", "Create Pull Request")["run"],
        {"github.repository": "owner/repo", "github.run_id": "1"},
    )
    outputs = _run_script(
        script,
        tmp_path,
        tmp_path,
        PATH=path,
        GH_BODY_FILE=str(body_file),
        GH_TOKEN="unused",
        MODEL=model,
        SPEC_ID="spec-a",
        LANGUAGE="python",
        LIBRARY="plotly",
        EXT=".py",
        ISSUE="42",
        BRANCH="implementation/spec-a/plotly",
    )
    assert outputs["pr_number"] == "123"
    return body_file.read_text(encoding="utf-8")


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
        outputs = _run_extract_inputs(repo, tmp_path, library=library, model=model)
        assert outputs["model"] == model
        assert outputs["model_reason"] == "explicit input"

    def test_empty_model_routes_like_auto(self, repo, tmp_path):
        assert _run_extract_inputs(repo, tmp_path, library="plotly", model="")["model"] == "opus"
        assert _run_extract_inputs(repo, tmp_path, library="matplotlib", model="")["model"] == "sonnet"

    @pytest.mark.parametrize(("library", "expected"), [("matplotlib", "sonnet"), ("plotly", "opus")])
    def test_label_trigger_routes(self, repo, tmp_path, library, expected):
        outputs = _run_extract_inputs(repo, tmp_path, library=library, label_trigger=True)
        assert outputs["specification_id"] == "spec-a"
        assert outputs["library"] == library
        assert outputs["model"] == expected

    @pytest.mark.parametrize(
        ("library", "model", "reason"),
        [("plotly", "opus", "first implementation"), ("matplotlib", "sonnet", "regeneration")],
    )
    def test_reason_reaches_outputs_and_run_summary(self, repo, tmp_path, library, model, reason):
        outputs = _run_extract_inputs(repo, tmp_path, library=library)
        assert (outputs["model"], outputs["model_reason"]) == (model, reason)
        summary = (tmp_path / "step_summary").read_text(encoding="utf-8")
        assert f"**Model:** {model} ({reason})" in summary

    @pytest.mark.parametrize(
        ("library", "model", "expected", "reason"),
        [
            ("matplotlib", "auto", "opus", "forced regeneration"),  # on main, gate opted out
            ("plotly", "auto", "opus", "first implementation"),  # nothing to force on a first run
            ("matplotlib", "sonnet", "sonnet", "explicit input"),  # an explicit model still wins
        ],
    )
    def test_forced_regeneration_routes_to_opus(self, repo, tmp_path, library, model, expected, reason):
        outputs = _run_extract_inputs(repo, tmp_path, library=library, model=model, regen_gate="false")
        assert (outputs["model"], outputs["model_reason"]) == (expected, reason)

    def test_regen_gate_expression_matches_the_existing_check(self):
        """Routing and the regen labels must agree on what a forced regeneration is."""
        routing = _step("impl-generate.yml", "Extract inputs")["env"]["REGEN_GATE"]
        existing = _step("impl-generate.yml", "Check for existing implementation (regeneration)")["env"]["REGEN_GATE"]
        assert routing == existing

    def test_routing_fails_without_origin_main(self, repo_without_main, tmp_path):
        script, env = _extract_inputs_script(library="plotly", model="auto", label_trigger=False, spec="spec-a")
        result = _exec(script, repo_without_main, tmp_path, **env)
        assert result.returncode != 0
        assert "::error::origin/main unavailable — cannot route the model" in result.stdout
        assert "model" not in _outputs(tmp_path / "github_output")

    def test_explicit_model_needs_no_origin_main(self, repo_without_main, tmp_path):
        assert _run_extract_inputs(repo_without_main, tmp_path, library="plotly", model="sonnet")["model"] == "sonnet"


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
        "name",
        [
            "Create library metadata file",
            "Create Pull Request",
            "Post preview to issue",
            "Trigger review workflow",
            "Handle generation failure",
        ],
    )
    def test_consumers_get_the_resolved_model(self, name):
        assert _step("impl-generate.yml", name)["env"]["MODEL"] == "${{ steps.inputs.outputs.model }}"

    def test_retry_forwards_the_resolved_model_explicitly(self):
        script = _step("impl-generate.yml", "Handle generation failure")["run"]
        assert '-f model="${MODEL}"' in script

    def test_preview_comment_shows_model_and_reason(self):
        step = _step("impl-generate.yml", "Post preview to issue")
        assert step["env"]["MODEL_REASON"] == "${{ steps.inputs.outputs.model_reason }}"
        assert "**Model:** ${MODEL} (${MODEL_REASON})" in step["run"]

    @pytest.mark.parametrize("model", ["opus", "haiku"])
    def test_pr_body_records_the_model_on_its_own_line(self, tmp_path, model):
        body = _create_pr_body(tmp_path, model=model)
        assert f"**Model:** {model}" in body.splitlines()


# ---------------------------------------------------------------------------
# impl-review
# ---------------------------------------------------------------------------


def _run_review(
    repo: Path,
    tmp_path: Path,
    *,
    library: str,
    model_input: str = "",
    payload: str = "",
    body: str = "",
    review_input: str = "",
    review_payload: str = "",
) -> subprocess.CompletedProcess[str]:
    """Run impl-review's "Extract PR info" step against a fake `gh`."""
    pr = {"headRefName": f"implementation/spec-a/{library}", "headRefOid": "0" * 40, "body": body}
    path = _fake_gh(tmp_path, f"cat <<'EOF'\n{json.dumps(pr)}\nEOF\n")
    # The step parks gh's output under /tmp; keep the test inside tmp_path.
    script = _step("impl-review.yml", "Extract PR info")["run"].replace("/tmp/", f"{tmp_path}/")
    return _exec(
        script,
        repo,
        tmp_path,
        PATH=path,
        GH_TOKEN="unused",
        PR_NUMBER="7",
        MODEL_INPUT=model_input,
        MODEL_PAYLOAD=payload,
        REVIEW_MODEL_INPUT=review_input,
        REVIEW_MODEL_PAYLOAD=review_payload,
    )


def _review_model(repo: Path, tmp_path: Path, **kwargs: str) -> str:
    """The generation model impl-review resolves (and forwards to repair)."""
    result = _run_review(repo, tmp_path, **kwargs)
    assert result.returncode == 0, result.stdout + result.stderr
    return _outputs(tmp_path / "github_output")["model"]


def _review_outputs(repo: Path, tmp_path: Path, **kwargs: str) -> dict[str, str]:
    result = _run_review(repo, tmp_path, **kwargs)
    assert result.returncode == 0, result.stdout + result.stderr
    return _outputs(tmp_path / "github_output")


class TestImplReviewModel:
    """The generation model impl-review resolves and forwards to repair.

    impl-generate always sends its resolved model; rescues send none. The
    review itself runs on the review model (TestImplReviewReviewModel).
    """

    @pytest.mark.parametrize(("model_input", "payload"), [("", "opus"), ("", "haiku"), ("sonnet", ""), ("opus", "")])
    def test_threaded_or_explicit_model_wins(self, repo, tmp_path, model_input, payload):
        # plotly is a first run, so routing alone would say opus.
        assert _review_model(repo, tmp_path, library="plotly", model_input=model_input, payload=payload) == (
            model_input or payload
        )

    @pytest.mark.parametrize(("model_input", "payload"), [("auto", ""), ("", ""), ("", "auto")])
    @pytest.mark.parametrize(
        ("library", "expected"), [("matplotlib", "sonnet"), ("muix", "sonnet"), ("plotly", "opus"), ("seaborn", "opus")]
    )
    def test_rescue_without_a_model_routes(self, repo, tmp_path, model_input, payload, library, expected):
        result = _run_review(repo, tmp_path, library=library, model_input=model_input, payload=payload)
        assert result.returncode == 0, result.stdout + result.stderr
        outputs = _outputs(tmp_path / "github_output")
        assert outputs["library"] == library
        assert outputs["model"] == expected

    def test_library_match_is_exact(self, repo, tmp_path):
        # "d3" is on main; a library whose name only starts the same is not.
        assert _review_model(repo, tmp_path, library="d3") == "sonnet"
        assert _review_model(repo, tmp_path, library="d") == "opus"

    @pytest.mark.parametrize(("library", "pinned"), [("plotly", "haiku"), ("matplotlib", "opus")])
    def test_body_marker_beats_routing(self, repo, tmp_path, library, pinned):
        body = f"## Implementation\n\n**File:** `x`\n\n**Model:** {pinned}\r\n\n**Parent Issue:** #42"
        assert _review_model(repo, tmp_path, library=library, model_input="auto", body=body) == pinned

    @pytest.mark.parametrize(("model_input", "payload"), [("sonnet", ""), ("", "sonnet")])
    def test_body_marker_loses_to_input_and_payload(self, repo, tmp_path, model_input, payload):
        body = "**Model:** haiku"
        assert _review_model(repo, tmp_path, library="plotly", model_input=model_input, payload=payload, body=body) == (
            "sonnet"
        )

    def test_body_marker_must_be_a_whole_line_with_a_known_model(self, repo, tmp_path):
        body = "Note: **Model:** haiku was used\n**Model:** gpt\n**Model:** haiku (pinned)"
        assert _review_model(repo, tmp_path, library="matplotlib", body=body) == "sonnet"  # routing

    def test_pr_body_round_trips_into_a_rescue_review(self, repo, tmp_path):
        body = _create_pr_body(tmp_path, model="haiku")
        # plotly is a first run: routing would say opus, the recorded pin says haiku.
        assert _review_model(repo, tmp_path, library="plotly", body=body) == "haiku"

    def test_missing_origin_main_warns_and_assumes_a_first_run(self, repo_without_main, tmp_path):
        result = _run_review(repo_without_main, tmp_path, library="matplotlib")
        assert result.returncode == 0, result.stdout + result.stderr
        assert NO_MAIN_WARNING in result.stdout
        assert _outputs(tmp_path / "github_output")["model"] == "opus"


def _run_self_retry(tmp_path: Path, name: str, *, model: str, review_alias: str) -> list[list[str]]:
    """Run one of impl-review's self-retry steps (first failure) and return its `gh` calls.

    Each call is the list of its arguments. The fake `gh` reports no earlier
    retry marker, so the step takes the auto-retry branch.
    """
    log = tmp_path / "gh_log"
    log.unlink(missing_ok=True)
    path = _fake_gh(
        tmp_path,
        'for arg in "$@"; do printf "%s\\n" "$arg"; done >> "$GH_LOG"\n'
        'echo "--END--" >> "$GH_LOG"\n'
        'if [ "$1 $2" = "api --paginate" ]; then echo 0; fi\n'
        "exit 0\n",
    )
    result = _exec(
        _step("impl-review.yml", name)["run"],
        tmp_path,
        tmp_path,
        PATH=path,
        GH_LOG=str(log),
        GH_TOKEN="unused",
        PR_NUM="7",
        SPEC_ID="spec-a",
        LIBRARY="plotly",
        REPOSITORY="owner/repo",
        RUN_ID="1",
        MODEL=model,
        REVIEW_MODEL_ALIAS=review_alias,
    )
    # Both steps end red after dispatching on purpose: the retry is its own run.
    assert result.returncode == 1, result.stdout + result.stderr
    return [call.splitlines() for call in log.read_text(encoding="utf-8").split("--END--\n") if call]


def _dispatch_payload(calls: list[list[str]]) -> dict[str, str]:
    """The `-f key=value` fields of the single repository_dispatch call."""
    dispatches = [call for call in calls if "repos/owner/repo/dispatches" in call]
    assert len(dispatches) == 1, calls
    args = dispatches[0]
    return dict(args[i + 1].split("=", 1) for i, arg in enumerate(args) if arg == "-f")


class TestImplReviewReviewModel:
    """Every review runs on opus; only `review_model` (input, or the own retry's payload) pins another."""

    @pytest.mark.parametrize("library", ["plotly", "matplotlib"])  # a first run, a regeneration
    @pytest.mark.parametrize(
        "generation",
        [
            {},
            {"model_input": "auto"},
            {"model_input": "sonnet"},
            {"model_input": "haiku"},
            {"payload": "sonnet"},
            {"payload": "haiku"},
            {"body": "**Model:** sonnet"},
            {"body": "**Model:** haiku"},
        ],
    )
    def test_every_review_runs_on_opus(self, repo, tmp_path, library, generation):
        """A Sonnet regeneration, or any other generation pin, is reviewed on opus."""
        assert _review_outputs(repo, tmp_path, library=library, **generation)["review_model_alias"] == "opus"

    @pytest.mark.parametrize(
        ("review_input", "review_payload", "expected"),
        [
            ("sonnet", "", "sonnet"),
            ("haiku", "", "haiku"),
            ("opus", "", "opus"),
            ("", "haiku", "haiku"),
            ("", "sonnet", "sonnet"),
            ("sonnet", "haiku", "sonnet"),  # the input beats the payload
            ("opus", "haiku", "opus"),
        ],
    )
    def test_review_pin(self, repo, tmp_path, review_input, review_payload, expected):
        outputs = _review_outputs(
            repo, tmp_path, library="matplotlib", review_input=review_input, review_payload=review_payload
        )
        assert outputs["review_model_alias"] == expected

    def test_review_pin_leaves_the_generation_model_alone(self, repo, tmp_path):
        outputs = _review_outputs(repo, tmp_path, library="plotly", model_input="sonnet", review_input="haiku")
        assert (outputs["model"], outputs["review_model_alias"]) == ("sonnet", "haiku")
        outputs = _review_outputs(repo, tmp_path, library="matplotlib", review_payload="haiku")
        assert (outputs["model"], outputs["review_model_alias"]) == ("sonnet", "haiku")  # routed regeneration

    @pytest.mark.parametrize("review_payload", ["gpt", "auto", "Opus", "claude-opus-5"])
    def test_unknown_review_model_falls_back_to_opus(self, repo, tmp_path, review_payload):
        result = _run_review(repo, tmp_path, library="matplotlib", review_payload=review_payload)
        assert result.returncode == 0, result.stdout + result.stderr
        assert _outputs(tmp_path / "github_output")["review_model_alias"] == "opus"
        assert f"::warning::unknown review model '{review_payload}' — using opus" in result.stdout

    def test_summary_and_notice_name_both_models(self, repo, tmp_path):
        result = _run_review(repo, tmp_path, library="matplotlib")
        assert result.returncode == 0, result.stdout + result.stderr
        summary = (tmp_path / "step_summary").read_text(encoding="utf-8")
        assert "**Review model:** opus" in summary
        assert "**Generation model:** sonnet (routing; forwarded to repair)" in summary
        assert "review model: opus, generation model: sonnet from routing" in result.stdout

    def test_pin_covers_the_own_auto_retry(self, repo, tmp_path):
        """A pinned review's auto-retry is a repository_dispatch with no inputs: the payload carries the pin."""
        first = _review_outputs(repo, tmp_path, library="matplotlib", review_input="haiku")
        calls = _run_self_retry(
            tmp_path, "Handle review failure", model=first["model"], review_alias=first["review_model_alias"]
        )
        payload = _dispatch_payload(calls)
        retry = _review_outputs(
            repo,
            tmp_path,
            library="matplotlib",
            payload=payload["client_payload[model]"],
            review_payload=payload["client_payload[review_model]"],
        )
        assert (retry["model"], retry["review_model_alias"]) == ("sonnet", "haiku")


class TestImplReviewWiring:
    def test_review_runs_on_the_review_model(self):
        args = _step("impl-review.yml", "Run AI Quality Review")["with"]["claude_args"]
        assert args.startswith(f"--model {REVIEW_ALIAS} ")

    def test_no_claude_step_runs_on_the_generation_model(self):
        for step in _steps("impl-review.yml"):
            args = (step.get("with") or {}).get("claude_args", "")
            assert not re.search(r"steps\.pr\.outputs\.model\b", args), step.get("name")

    @pytest.mark.parametrize("name", SELF_RETRY_STEPS)
    def test_self_retries_get_both_models(self, name):
        env = _step("impl-review.yml", name)["env"]
        assert env["REVIEW_MODEL_ALIAS"] == REVIEW_ALIAS
        assert env["MODEL"] == GENERATION_MODEL

    @pytest.mark.parametrize("name", SELF_RETRY_STEPS)
    def test_self_retry_dispatch_forwards_both_models(self, tmp_path, name):
        payload = _dispatch_payload(_run_self_retry(tmp_path, name, model="haiku", review_alias="sonnet"))
        assert payload["event_type"] == "review-pr"
        assert payload["client_payload[pr_number]"] == "7"
        assert payload["client_payload[model]"] == "haiku"
        assert payload["client_payload[review_model]"] == "sonnet"

    def test_repair_dispatch_forwards_the_generation_model_only(self):
        step = _step("impl-review.yml", "Add verdict label and take action")
        assert step["env"]["MODEL"] == GENERATION_MODEL
        assert "REVIEW_MODEL_ALIAS" not in step["env"]
        assert '-f model="$MODEL"' in step["run"]
        assert "review_model" not in step["run"]

    def test_review_model_env_stays_the_resolved_id(self):
        """`REVIEW_MODEL` is the resolved id (claude-opus-*); the alias never takes that name.

        Its consumers store it as `review.model`: the metadata writer on the
        merge path and the re-score write-back on a keep (P9b).
        """
        found = []
        for step in _steps("impl-review.yml"):
            value = (step.get("env") or {}).get("REVIEW_MODEL")
            if value is None:
                continue
            found.append(step.get("name"))
            assert "steps.pr.outputs" not in value, step.get("name")
            assert value == "${{ steps.review_model.outputs.model_id }}", step.get("name")
        assert found == ["Update metadata and implementation header", "Write back the re-score (regen keep)"]

    def test_no_other_workflow_forwards_a_review_model(self):
        """Repair, generation and every rescue re-dispatch review without one, so it runs on opus."""
        for path in sorted(WORKFLOWS_DIR.glob("*.yml")):
            if path.name == "impl-review.yml":
                continue
            text = path.read_text(encoding="utf-8")
            assert "client_payload[review_model]" not in text, path.name
            assert "review_model=" not in text, path.name


# ---------------------------------------------------------------------------
# impl-repair
# ---------------------------------------------------------------------------


def _run_repair(
    repo: Path, tmp_path: Path, *, library: str, model_input: str, body: str = "", gh_failures: int = 0
) -> subprocess.CompletedProcess[str]:
    """Run impl-repair's "Resolve model" step.

    The fake `gh pr view` fails its first `gh_failures` calls, then prints
    `body`; every call is counted in tmp_path/gh_calls. `sleep` is stubbed so
    the retry backoff costs no time.
    """
    language, ext = LANG_EXT[library]
    path = _fake_gh(
        tmp_path,
        'n=$(cat "$GH_CALLS" 2>/dev/null || echo 0); n=$((n + 1)); echo "$n" > "$GH_CALLS"\n'
        'if [ "$n" -le "$GH_FAILURES" ]; then echo "HTTP 502: Bad Gateway" >&2; exit 1; fi\n'
        f"cat <<'EOF'\n{body}\nEOF\n",
    )
    sleep = tmp_path / "bin" / "sleep"
    sleep.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    sleep.chmod(0o755)
    (tmp_path / "gh_calls").unlink(missing_ok=True)
    # The step parks gh's stderr under /tmp; keep the test inside tmp_path.
    script = _step("impl-repair.yml", "Resolve model")["run"].replace("/tmp/", f"{tmp_path}/")
    return _exec(
        script,
        repo,
        tmp_path,
        PATH=path,
        GH_CALLS=str(tmp_path / "gh_calls"),
        GH_FAILURES=str(gh_failures),
        GH_TOKEN="unused",
        PR_NUMBER="7",
        MODEL_INPUT=model_input,
        SPEC_ID="spec-a",
        LIBRARY=library,
        LANGUAGE=language,
        EXT=ext,
    )


def _gh_calls(tmp_path: Path) -> int:
    calls = tmp_path / "gh_calls"
    return int(calls.read_text(encoding="utf-8")) if calls.exists() else 0


def _repair_model(repo: Path, tmp_path: Path, **kwargs: str) -> str:
    result = _run_repair(repo, tmp_path, **kwargs)
    assert result.returncode == 0, result.stdout + result.stderr
    return _outputs(tmp_path / "github_output")["model"]


class TestImplRepairModel:
    @pytest.mark.parametrize(
        ("library", "expected"),
        [("matplotlib", "sonnet"), ("ggplot2", "sonnet"), ("muix", "sonnet"), ("plotly", "opus")],
    )
    @pytest.mark.parametrize("model_input", ["auto", ""])
    def test_rescue_without_a_model_routes(self, repo, tmp_path, library, expected, model_input):
        assert _repair_model(repo, tmp_path, library=library, model_input=model_input) == expected

    @pytest.mark.parametrize("model_input", ["haiku", "sonnet", "opus"])
    def test_threaded_model_wins(self, repo, tmp_path, model_input):
        assert _repair_model(repo, tmp_path, library="plotly", model_input=model_input) == model_input

    @pytest.mark.parametrize(("library", "pinned"), [("plotly", "haiku"), ("matplotlib", "opus")])
    def test_body_marker_beats_routing(self, repo, tmp_path, library, pinned):
        body = f"**File:** `x`\n\n**Model:** {pinned}\n\n**Parent Issue:** #42"
        assert _repair_model(repo, tmp_path, library=library, model_input="auto", body=body) == pinned

    def test_body_marker_loses_to_input(self, repo, tmp_path):
        assert _repair_model(repo, tmp_path, library="plotly", model_input="sonnet", body="**Model:** haiku") == (
            "sonnet"
        )

    def test_missing_origin_main_warns_and_assumes_a_first_run(self, repo_without_main, tmp_path):
        result = _run_repair(repo_without_main, tmp_path, library="matplotlib", model_input="auto")
        assert result.returncode == 0, result.stdout + result.stderr
        assert NO_MAIN_WARNING in result.stdout
        assert _outputs(tmp_path / "github_output")["model"] == "opus"

    def test_body_lookup_retries_transient_failures(self, repo, tmp_path):
        # plotly is a first run: routing would say opus, the recorded pin says haiku.
        result = _run_repair(
            repo, tmp_path, library="plotly", model_input="auto", body="**Model:** haiku", gh_failures=2
        )
        assert result.returncode == 0, result.stdout + result.stderr
        assert _outputs(tmp_path / "github_output")["model"] == "haiku"
        assert _gh_calls(tmp_path) == 3
        assert "gh pr view failed (attempt 1/3): HTTP 502" in result.stdout
        assert "gh pr view failed (attempt 2/3)" in result.stdout

    def test_body_lookup_fails_closed_instead_of_rerouting(self, repo, tmp_path):
        result = _run_repair(
            repo, tmp_path, library="plotly", model_input="auto", body="**Model:** haiku", gh_failures=99
        )
        assert result.returncode != 0
        assert "::error::gh pr view failed after 3 attempts for PR #7" in result.stdout
        assert _gh_calls(tmp_path) == 3
        assert "model" not in _outputs(tmp_path / "github_output")

    def test_threaded_model_skips_the_body_lookup(self, repo, tmp_path):
        result = _run_repair(repo, tmp_path, library="plotly", model_input="sonnet", gh_failures=99)
        assert result.returncode == 0, result.stdout + result.stderr
        assert _outputs(tmp_path / "github_output")["model"] == "sonnet"
        assert _gh_calls(tmp_path) == 0

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


# ---------------------------------------------------------------------------
# Inputs, pacing, fixed models
# ---------------------------------------------------------------------------


class TestModelInputs:
    @pytest.mark.parametrize(
        "filename", ["impl-generate.yml", "bulk-generate.yml", "daily-regen.yml", "impl-review.yml", "impl-repair.yml"]
    )
    def test_model_input_defaults_to_auto(self, filename):
        model = _dispatch_inputs(filename)["model"]
        assert model["default"] == "auto"
        assert model["options"][0] == "auto"
        assert set(model["options"]) == MODELS

    def test_review_model_input_defaults_to_opus(self):
        review_model = _dispatch_inputs("impl-review.yml")["review_model"]
        assert review_model["type"] == "choice"
        assert review_model["default"] == "opus"
        assert review_model["options"][0] == "opus"
        assert set(review_model["options"]) == REVIEW_MODELS

    @pytest.mark.parametrize(
        "filename", ["impl-generate.yml", "bulk-generate.yml", "daily-regen.yml", "impl-repair.yml"]
    )
    def test_only_impl_review_declares_review_model(self, filename):
        assert "review_model" not in _dispatch_inputs(filename)

    def test_harness_production_is_the_review_default(self):
        """The retest harness's `models=production` measures what impl-review runs."""
        default = _dispatch_inputs("impl-review.yml")["review_model"]["default"]
        assert set(review_retest.PRODUCTION_MODELS) == {"fresh", "regen"}
        assert set(review_retest.PRODUCTION_MODELS.values()) == {default}
        for kind, model in review_retest.PRODUCTION_MODELS.items():
            assert (kind, model) in review_retest.COST_ESTIMATE

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


RUN_QUEUE = REPO_ROOT / ".claude" / "skills" / "babysit-pipeline" / "run_queue.sh"


def _queue_settings(tmp_path: Path, *args: str, **env: str) -> dict[str, str]:
    """Source run_queue.sh in its library mode and read back its settings."""
    queue = tmp_path / "queue"
    queue.mkdir(exist_ok=True)
    (queue / "full_queue.txt").touch()
    fake_repo = tmp_path / "fake-repo"  # ANYPLOT_REPO: nothing is resolved via git
    (fake_repo / "plots").mkdir(parents=True, exist_ok=True)
    script = (
        'RUN_QUEUE_LIB=1 source "$RUN_QUEUE" "$@"\n'
        'printf "SETTING_MODEL=%s\\nSETTING_SLOTS=%s\\nSETTING_STAGGER=%s\\n" "$MODEL" "$SLOTS" "$STAGGER"\n'
    )
    base = {k: v for k, v in _clean_env().items() if k not in {"MODEL", "STAGGER"}}
    base.update(RUN_QUEUE=str(RUN_QUEUE), ANYPLOT_REPO=str(fake_repo), **env)
    result = subprocess.run(
        ["bash", "-c", script, "run_queue.sh", str(queue), *args], env=base, capture_output=True, text=True
    )
    assert result.returncode == 0, result.stdout + result.stderr
    return {
        key.removeprefix("SETTING_"): value
        for key, _, value in (line.partition("=") for line in result.stdout.splitlines())
        if key.startswith("SETTING_")
    }


class TestBabysitQueueDefaults:
    """Under auto a gap backfill is all-Opus, so the unattended queue starts gently."""

    @pytest.mark.parametrize(
        ("env", "expected"),
        [
            ({}, {"MODEL": "auto", "SLOTS": "1", "STAGGER": "180"}),
            ({"MODEL": "opus"}, {"MODEL": "opus", "SLOTS": "1", "STAGGER": "180"}),
            ({"MODEL": "sonnet"}, {"MODEL": "sonnet", "SLOTS": "2", "STAGGER": "90"}),
            ({"MODEL": "haiku"}, {"MODEL": "haiku", "SLOTS": "2", "STAGGER": "90"}),
        ],
    )
    def test_defaults_follow_the_model(self, tmp_path, env, expected):
        assert _queue_settings(tmp_path, **env) == expected

    def test_slots_argument_and_stagger_env_still_override(self, tmp_path):
        assert _queue_settings(tmp_path, "3", STAGGER="60") == {"MODEL": "auto", "SLOTS": "3", "STAGGER": "60"}


class TestBulkGeneratePacing:
    PACE = "${{ inputs.pace_seconds || ((inputs.model == 'sonnet' || inputs.model == 'haiku') && '120' || '180') }}"

    def test_pace_input_has_no_fixed_default(self):
        assert _dispatch_inputs("bulk-generate.yml")["pace_seconds"]["default"] == ""

    @pytest.mark.parametrize("step", ["Preview generation plan", "Dispatch impl-generate for each matrix item (paced)"])
    def test_default_pace_is_180_for_opus_and_auto_120_otherwise(self, step):
        env = _step("bulk-generate.yml", step)["env"]
        assert env["PACE_SECONDS"] == self.PACE


class TestFixedModels:
    @pytest.mark.parametrize(
        "name", ["Spec polish (autonomous, opens PR with auto-merge)", "Cross-library similarity audit"]
    )
    def test_daily_regen_preflight_runs_on_sonnet(self, name):
        args = _step("daily-regen.yml", name)["with"]["claude_args"]
        assert args.startswith("--model sonnet ")

    def test_daily_regen_never_runs_on_haiku(self):
        for step in _steps("daily-regen.yml"):
            assert "haiku" not in step.get("with", {}).get("claude_args", ""), step.get("name")
        assert "--model haiku" not in (WORKFLOWS_DIR / "daily-regen.yml").read_text(encoding="utf-8")

    @pytest.mark.parametrize("filename", ["spec-create.yml", "report-validate.yml", "util-claude.yml"])
    def test_opus_workflows_stay_pinned(self, filename):
        claude_args = [s["with"]["claude_args"] for s in _steps(filename) if "claude_args" in (s.get("with") or {})]
        assert claude_args, f"no Claude step found in {filename}"
        for args in claude_args:
            assert args.startswith("--model opus "), args
