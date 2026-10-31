"""Adopt mode of impl-generate.yml, and its pass-through in bulk-generate.yml.

With `source_ref` set, impl-generate takes the implementation file from that ref of
origin instead of running Claude ("Adopt implementation from source ref"). The step
renders the file in both themes with the generator's commands, checks the canvas with
core.canvas, and commits and pushes that one file to the implementation branch. Every
later step runs as for a generated file. An adopted run is always a forced regeneration
(`regen:forced`), and a source failure (file missing on the ref, failed render) is never
retried and never counts toward the 3-attempt cap, because a retry reads the same file.
`source_model` names the model that wrote the adopted file: it becomes the metadata's
`generated_by`, next to `adopted_from: <ref> (<sha>)`, and every retry keeps it.

The step scripts run here for real against a throwaway origin, under `bash -e` (the
Actions default) and `bash -eo pipefail`, with fake `node`, `gh`, `uv` and `yq` where
the real ones would need a browser or the network. The rest are content guards.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest
import yaml

from automation.scripts import review_retest


REPO_ROOT = Path(__file__).resolve().parents[3]
WORKFLOWS_DIR = REPO_ROOT / ".github" / "workflows"
EXPRESSION = re.compile(r"\$\{\{\s*(.+?)\s*\}\}")
SHELLS = [["bash", "-e", "-c"], ["bash", "-eo", "pipefail", "-c"]]

ADOPT_STEP = "Adopt implementation from source ref"
CLAUDE_STEP = "Run Claude Code to generate implementation"
RETRY_STEP = "Retry Claude (on failure)"
OVERLAY_STEP = "Overlay prompts/ from trigger ref (branch-level prompt iteration)"
EXISTING_STEP = "Check for existing implementation (regeneration)"
HANDLER_STEP = "Handle generation failure"
BULK_STEP = "Dispatch impl-generate for each matrix item (paced)"
REGEN_GATE_EXPR = (
    "${{ (github.event_name == 'workflow_dispatch' && (inputs.regen_gate == false || inputs.source_ref != ''))"
    " && 'false' || 'true' }}"
)
# Values both workflows reject without echoing them. The newline ones would inject a
# workflow command into the runner's output if the error line printed them.
BAD_REFS = [
    "gemini/muix 9",
    "-x",
    "../main",
    "a..b",
    "$(id)",
    "main;id",
    "`id`",
    "a'b",
    "x" * 81,
    "main\n::error::injected",
]
BAD_MODELS = ["gemini 4", "-x", ".x", "a/b", "$(id)", "a;id", "`id`", "a'b", "a:b", "G" * 41, "x\n::warning::injected"]
REF_PATTERN = "^[A-Za-z0-9][A-Za-z0-9._/-]{0,79}$"
MODEL_PATTERN = "^[A-Za-z0-9][A-Za-z0-9._-]{0,39}$"

SPEC = "spec-a"
LANG_EXT = {
    "matplotlib": ("python", ".py"),
    "muix": ("javascript", ".tsx"),
    "d3": ("javascript", ".js"),
    "ggplot2": ("r", ".R"),
    "makie": ("julia", ".jl"),
}


def _impl(library: str, spec: str = SPEC) -> str:
    language, ext = LANG_EXT[library]
    return f"plots/{spec}/implementations/{language}/{library}{ext}"


PY_IMPL = _impl("matplotlib")
JS_IMPL = _impl("muix")
OTHER_IMPL = _impl("matplotlib", "spec-b")

# A Python implementation that renders like a real one: it asserts the generator's
# render command (`MPLBACKEND=Agg ... python -P`) and writes plot-{theme}.png in its cwd.
PY_RENDER = """import os
import sys

from PIL import Image

assert sys.flags.safe_path, "rendered without -P"
assert os.environ.get("MPLBACKEND") == "Agg"
theme = os.environ["ANYPLOT_THEME"]
Image.new("RGB", (WIDTH, HEIGHT), (250, 248, 241)).save(f"plot-{theme}.png")
"""


def _py_render(width: int = 3200, height: int = 1800, marker: str = "") -> str:
    return PY_RENDER.replace("WIDTH", str(width)).replace("HEIGHT", str(height)) + marker


# The JS render harness needs Chromium; the fake logs its call and writes what the
# harness writes: plot-{theme}.png at the canvas size, and plot-{theme}.html.
FAKE_NODE = """#!/bin/sh
printf '%s|%s|%s\\n' "$PWD" "$ANYPLOT_THEME" "$*" >> "$NODE_LOG"
if [ -n "$NODE_FAIL" ]; then echo "snippet threw" >&2; exit 1; fi
"$TEST_PYTHON" -c "import sys; from PIL import Image; Image.new('RGB', (3200, 1800), (1, 2, 3)).save(sys.argv[1])" \\
  "plot-$ANYPLOT_THEME.png"
printf '<html></html>\\n' > "plot-$ANYPLOT_THEME.html"
"""
# Logs its call; an install makes numpy importable for the venv shim (NUMPY_MARKER),
# unless UV_FAIL fails it or UV_NOOP succeeds without installing anything.
FAKE_UV = """#!/bin/sh
printf '%s\\n' "$*" >> "$UV_LOG"
[ -n "$UV_FAIL" ] && exit 1
[ -z "$UV_NOOP" ] && touch "$NUMPY_MARKER"
exit 0
"""
# Records every call as one JSON array per line; `gh api` answers the failure count.
FAKE_GH = """#!/bin/sh
"$TEST_PYTHON" -c 'import json, sys; print(json.dumps(sys.argv[1:]))' "$@" >> "$GH_LOG"
case "$1" in
  api) echo "0 0" ;;
esac
exit 0
"""
FAKE_YQ = """#!/bin/sh
echo 42
"""


def _workflow(filename: str) -> dict[Any, Any]:
    workflow: dict[Any, Any] = yaml.safe_load((WORKFLOWS_DIR / filename).read_text(encoding="utf-8"))
    return workflow


def _steps(filename: str) -> list[dict[str, Any]]:
    return [step for job in _workflow(filename)["jobs"].values() for step in job.get("steps", [])]


def _step(filename: str, name: str) -> dict[str, Any]:
    matches = [step for step in _steps(filename) if step.get("name") == name]
    assert len(matches) == 1, f"expected exactly one step named {name!r} in {filename}"
    return matches[0]


def _names(filename: str) -> list[str]:
    return [str(step.get("name")) for step in _steps(filename)]


def _dispatch_inputs(filename: str) -> dict[str, Any]:
    workflow = _workflow(filename)
    on: dict[str, Any] = workflow.get("on") or workflow[True]  # YAML reads a bare `on:` as True
    inputs: dict[str, Any] = on["workflow_dispatch"]["inputs"]
    return inputs


def _render(script: str, context: dict[str, str]) -> str:
    """Substitute `${{ expr }}` the way Actions does before the shell runs."""

    def substitute(match: re.Match[str]) -> str:
        expr = match.group(1)
        assert expr in context, f"unexpected expression in the script: {expr}"
        return context[expr]

    return EXPRESSION.sub(substitute, script)


def _env(**extra: str) -> dict[str, str]:
    """No user or system git config and no inherited GIT_* state."""
    env = {key: value for key, value in os.environ.items() if not key.startswith(("GIT_", "PYTHONPATH"))}
    env.update(GIT_CONFIG_NOSYSTEM="1", GIT_CONFIG_GLOBAL=os.devnull, **extra)
    return env


def _git(repo: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(repo), "-c", "user.name=t", "-c", "user.email=t@t", "-c", "commit.gpgsign=false", *args],
        capture_output=True,
        text=True,
        env=_env(),
        check=True,
    )
    return result.stdout.strip()


def _write(root: Path, files: dict[str, str | None]) -> None:
    """Write files; None deletes one."""
    for rel, text in files.items():
        path = root / rel
        if text is None:
            path.unlink()
            continue
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")


def _outputs(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}
    return dict(line.split("=", 1) for line in path.read_text(encoding="utf-8").splitlines() if "=" in line)


def _executable(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    path.chmod(0o755)


# Refs on the fake origin, each a branch off main that changes the files named.
SOURCE_BRANCHES: dict[str, dict[str, str | None]] = {
    "gemini/adopt": {
        PY_IMPL: _py_render(marker="# adopted\n"),
        JS_IMPL: "// adopted\nexport default function Chart() { return null; }\n",
        OTHER_IMPL: "# another pair, never taken\n",
        "prompts/note.md": "a prompt change on the source branch\n",
    },
    "gemini/no-file": {PY_IMPL: None, JS_IMPL: None},
    "gemini/broken": {PY_IMPL: "raise SystemExit(3)\n"},
    "gemini/silent": {PY_IMPL: "print('rendered nothing')\n"},
    "gemini/drift": {PY_IMPL: _py_render(width=3000)},
    "gemini/not-png": {
        PY_IMPL: "import os\nopen(f\"plot-{os.environ['ANYPLOT_THEME']}.png\", 'w').write('not a png')\n"
    },
}


class Origin:
    """A bare origin (main plus the source branches) and a workspace on the implementation branch."""

    def __init__(self, tmp: Path, library: str = "matplotlib") -> None:
        self.tmp = tmp
        self.library = library
        self.language, self.ext = LANG_EXT[library]
        self.branch = f"implementation/{SPEC}/{library}"
        seed = tmp / "seed"
        seed.mkdir()
        _git(seed, "init", "-q", "-b", "main")
        _write(
            seed,
            {
                "core/__init__.py": "",
                "core/canvas.py": (REPO_ROOT / "core" / "canvas.py").read_text(encoding="utf-8"),
                f"plots/{SPEC}/specification.md": "# spec\n",
                PY_IMPL: _py_render(marker="# main\n"),
                JS_IMPL: "// main\nexport default function Chart() { return null; }\n",
                OTHER_IMPL: "# another pair\n",
                "prompts/note.md": "main's prompt\n",
            },
        )
        _git(seed, "add", "-A")
        _git(seed, "commit", "-q", "-m", "main")
        for name, files in SOURCE_BRANCHES.items():
            _git(seed, "checkout", "-q", "-b", name, "main")
            _write(seed, files)
            _git(seed, "add", "-A")
            _git(seed, "commit", "-q", "-m", name)
        _git(seed, "tag", "adopt-tag", "gemini/adopt")
        _git(seed, "checkout", "-q", "main")
        self.origin = tmp / "origin.git"
        subprocess.run(["git", "clone", "-q", "--bare", str(seed), str(self.origin)], check=True, env=_env())
        # GitHub serves any reachable commit by its SHA; a local bare repo needs this setting.
        _git(self.origin, "config", "uploadpack.allowAnySHA1InWant", "true")
        self.ws = tmp / "ws"
        subprocess.run(["git", "clone", "-q", str(self.origin), str(self.ws)], check=True, env=_env())
        # "Create implementation branch": a fresh branch from origin/main.
        _git(self.ws, "checkout", "-q", "-b", self.branch, "origin/main")
        # The runner's venv: `.venv/bin/python` and an activate script that puts it first.
        venv_bin = self.ws / ".venv" / "bin"
        _executable(
            venv_bin / "python",
            "#!/bin/sh\n"
            'if [ -n "$NO_NUMPY" ] && [ ! -f "$NUMPY_MARKER" ] && [ "$1" = "-c" ] && [ "$2" = "import numpy" ]; then\n'
            "  exit 1\n"
            "fi\n"
            f'exec "{sys.executable}" "$@"\n',
        )
        (venv_bin / "activate").write_text(f'PATH="{venv_bin}:$PATH"\nexport PATH\n', encoding="utf-8")
        self.bin = tmp / "bin"
        _executable(self.bin / "node", FAKE_NODE)
        _executable(self.bin / "uv", FAKE_UV)
        self.output = tmp / "github_output"
        self.summary = tmp / "step_summary"
        self.node_log = tmp / "node.log"
        self.uv_log = tmp / "uv.log"

    @property
    def impl(self) -> str:
        return _impl(self.library)

    @property
    def impl_dir(self) -> Path:
        return self.ws / "plots" / SPEC / "implementations" / self.language

    def sha(self, ref: str) -> str:
        return _git(self.origin, "rev-parse", ref)

    def run(self, shell: list[str], source_ref: str, **extra: str) -> subprocess.CompletedProcess[str]:
        script = str(_step("impl-generate.yml", ADOPT_STEP)["run"])
        assert "${{" not in script
        return subprocess.run(
            [*shell, script],
            cwd=self.ws,
            env=_env(
                PATH=f"{self.bin}{os.pathsep}{os.environ['PATH']}",
                GITHUB_WORKSPACE=str(self.ws),
                GITHUB_OUTPUT=str(self.output),
                GITHUB_STEP_SUMMARY=str(self.summary),
                SOURCE_REF=source_ref,
                SPEC_ID=SPEC,
                LANGUAGE=self.language,
                LIBRARY=self.library,
                EXT=self.ext,
                BRANCH=self.branch,
                NODE_LOG=str(self.node_log),
                UV_LOG=str(self.uv_log),
                NUMPY_MARKER=str(self.tmp / "numpy-installed"),
                TEST_PYTHON=sys.executable,
                **extra,
            ),
            capture_output=True,
            text=True,
        )

    def outputs(self) -> dict[str, str]:
        return _outputs(self.output)

    def pushed(self) -> bool:
        return bool(_git(self.origin, "branch", "--list", self.branch))

    def pushed_files(self) -> list[str]:
        return _git(self.origin, "diff", "--name-only", "main", self.branch).splitlines()

    def pushed_text(self, path: str) -> str:
        return _git(self.origin, "show", f"{self.branch}:{path}") + "\n"

    def pushed_message(self) -> str:
        return _git(self.origin, "log", "-1", "--format=%B", self.branch)

    def node_calls(self) -> list[list[str]]:
        if not self.node_log.exists():
            return []
        return [line.split("|", 2) for line in self.node_log.read_text(encoding="utf-8").splitlines()]


# --- wiring ------------------------------------------------------------------------------------


class TestInputs:
    @pytest.mark.parametrize("filename", ["impl-generate.yml", "bulk-generate.yml"])
    def test_source_ref_is_an_optional_string_that_defaults_to_generating(self, filename: str) -> None:
        source_ref = _dispatch_inputs(filename)["source_ref"]
        assert source_ref["type"] == "string"
        assert source_ref["required"] is False
        assert source_ref["default"] == ""

    @pytest.mark.parametrize("filename", ["impl-generate.yml", "bulk-generate.yml"])
    def test_source_model_is_an_optional_string_that_defaults_to_naming_the_ref(self, filename: str) -> None:
        source_model = _dispatch_inputs(filename)["source_model"]
        assert source_model["type"] == "string"
        assert source_model["required"] is False
        assert source_model["default"] == ""
        assert "gemini-4-argon" in source_model["description"]

    @pytest.mark.parametrize("name", ["source_ref", "source_model"])
    def test_bulk_generate_hands_the_raw_inputs_to_its_steps(self, name: str) -> None:
        for step in (BULK_STEP, "Preview generation plan"):
            assert _step("bulk-generate.yml", step)["env"][name.upper()] == f"${{{{ inputs.{name} }}}}"


class TestWiring:
    def test_adopt_runs_after_branch_and_regeneration_detection_and_before_claude_and_metadata(self) -> None:
        names = _names("impl-generate.yml")
        adopt = names.index(ADOPT_STEP)
        assert names.index("Create implementation branch") < names.index(EXISTING_STEP) < adopt
        assert names.index("Ensure implementation directories exist") < adopt
        assert adopt < names.index(CLAUDE_STEP) < names.index("Create library metadata file")

    def test_adopt_runs_only_with_a_source_ref(self) -> None:
        step = _step("impl-generate.yml", ADOPT_STEP)
        assert step["id"] == "adopt"
        assert step["if"] == "steps.inputs.outputs.source_ref != ''"
        assert "continue-on-error" not in step  # a failed adoption fails the job
        assert step["env"]["SOURCE_REF"] == "${{ steps.inputs.outputs.source_ref }}"

    def test_both_claude_steps_and_the_prompt_overlay_skip_in_adopt_mode(self) -> None:
        assert _step("impl-generate.yml", CLAUDE_STEP)["if"] == "steps.inputs.outputs.source_ref == ''"
        assert (
            _step("impl-generate.yml", RETRY_STEP)["if"]
            == "steps.claude.outcome == 'failure' && steps.inputs.outputs.source_ref == ''"
            " && steps.claude_cost.outputs.limit_reached != 'true'"
        )
        assert _step("impl-generate.yml", OVERLAY_STEP)["if"].endswith("&& steps.inputs.outputs.source_ref == ''")

    @pytest.mark.parametrize("name", ["Extract inputs", EXISTING_STEP, HANDLER_STEP])
    def test_adopting_always_opts_out_of_the_regen_gate(self, name: str) -> None:
        """One expression in all three places: source_ref forces like regen_gate=false."""
        assert _step("impl-generate.yml", name)["env"]["REGEN_GATE"] == REGEN_GATE_EXPR

    def test_only_extract_inputs_and_the_regen_gate_read_the_raw_input(self) -> None:
        """Everything else reads the validated `steps.inputs.outputs.source_ref` and `.source_model`."""
        for step in _steps("impl-generate.yml"):
            name = step.get("name")
            env = dict(step.get("env") or {})
            env.pop("REGEN_GATE", None)
            if name == "Extract inputs":
                assert env.pop("SOURCE_REF_INPUT") == "${{ inputs.source_ref }}"
                assert env.pop("SOURCE_MODEL_INPUT") == "${{ inputs.source_model }}"
            rest = {key: value for key, value in step.items() if key != "env"}
            dumped = json.dumps([rest, env])
            assert "inputs.source_ref" not in dumped, name
            assert "inputs.source_model" not in dumped, name

    @pytest.mark.parametrize(
        "name", ["Create library metadata file", "Create Pull Request", "Post preview to issue", HANDLER_STEP]
    )
    def test_consumers_get_the_validated_source_ref(self, name: str) -> None:
        assert _step("impl-generate.yml", name)["env"]["SOURCE_REF"] == "${{ steps.inputs.outputs.source_ref }}"

    @pytest.mark.parametrize(
        "name",
        [ADOPT_STEP, "Create library metadata file", "Create Pull Request", "Post preview to issue", HANDLER_STEP],
    )
    def test_consumers_get_the_validated_source_model(self, name: str) -> None:
        assert _step("impl-generate.yml", name)["env"]["SOURCE_MODEL"] == "${{ steps.inputs.outputs.source_model }}"

    def test_the_handler_reads_the_adopt_cause_and_the_pr_and_metadata_the_source_sha(self) -> None:
        assert _step("impl-generate.yml", HANDLER_STEP)["env"]["ADOPT_CAUSE"] == "${{ steps.adopt.outputs.cause }}"
        for name in ("Create Pull Request", "Create library metadata file"):
            assert _step("impl-generate.yml", name)["env"]["SOURCE_SHA"] == "${{ steps.adopt.outputs.sha }}"

    def test_the_render_commands_are_the_generators(self) -> None:
        """Step 3 of impl-generate-claude.md: the same commands, from the implementation directory."""
        script = str(_step("impl-generate.yml", ADOPT_STEP)["run"])
        prompt = (REPO_ROOT / "prompts" / "workflow-prompts" / "impl-generate-claude.md").read_text(encoding="utf-8")
        assert "MPLBACKEND=Agg ANYPLOT_THEME=light python -P {LIBRARY}.py" in prompt
        assert 'MPLBACKEND=Agg ANYPLOT_THEME="$theme" python -P "${LIBRARY}.py"' in script
        assert 'ANYPLOT_THEME=light node "$GITHUB_WORKSPACE/automation/js-render/render.mjs" {LIBRARY}{EXT}' in prompt
        assert (
            'ANYPLOT_THEME="$theme" node "$GITHUB_WORKSPACE/automation/js-render/render.mjs" "${LIBRARY}${EXT}"'
            in script
        )
        assert '.venv/bin/python -m core.canvas "${IMPL_DIR}/plot-${theme}.png" --library "$LIBRARY"' in script


# --- "Extract inputs" ---------------------------------------------------------------------------


def _routing_repo(tmp_path: Path) -> Path:
    """A repo whose origin/main holds the matplotlib implementation of spec-a."""
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init", "-q")
    _write(repo, {PY_IMPL: "# impl\n"})
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "main")
    _git(repo, "update-ref", "refs/remotes/origin/main", "HEAD")
    return repo


def _extract_inputs(
    tmp_path: Path,
    *,
    source_ref: str,
    source_model: str = "",
    regen_gate: str = "true",
    library: str = "matplotlib",
    model: str = "auto",
) -> subprocess.CompletedProcess[str]:
    context = {
        "github.event_name": "workflow_dispatch",
        "inputs.specification_id": SPEC,
        "inputs.library": library,
        "inputs.issue_number": "",
        "inputs.model": model,
        "github.event.issue.number": "",
    }
    script = _render(str(_step("impl-generate.yml", "Extract inputs")["run"]), context)
    for name in ("github_output", "step_summary"):
        (tmp_path / name).unlink(missing_ok=True)
    return subprocess.run(
        ["bash", "-eo", "pipefail", "-c", script],
        cwd=_routing_repo(tmp_path) if not (tmp_path / "repo").exists() else tmp_path / "repo",
        env=_env(
            GITHUB_OUTPUT=str(tmp_path / "github_output"),
            GITHUB_STEP_SUMMARY=str(tmp_path / "step_summary"),
            LABEL_NAME="",
            ISSUE_TITLE="",
            REGEN_GATE=regen_gate,
            SOURCE_REF_INPUT=source_ref,
            SOURCE_MODEL_INPUT=source_model,
        ),
        capture_output=True,
        text=True,
    )


class TestExtractInputs:
    @pytest.mark.parametrize(
        ("source_ref", "expected"),
        [
            ("", ""),
            ("main", "main"),
            ("origin/main", "main"),  # this checkout's name for it; origin calls it main
            ("gemini/muix-9", "gemini/muix-9"),
            ("origin/gemini/muix-9", "gemini/muix-9"),
            ("v3.4.0", "v3.4.0"),
            ("0123456789abcdef0123456789abcdef01234567", "0123456789abcdef0123456789abcdef01234567"),
        ],
    )
    def test_source_ref_is_normalized_and_exported(self, tmp_path: Path, source_ref: str, expected: str) -> None:
        result = _extract_inputs(tmp_path, source_ref=source_ref)
        assert result.returncode == 0, result.stdout + result.stderr
        assert _outputs(tmp_path / "github_output")["source_ref"] == expected

    @pytest.mark.parametrize("source_ref", [*BAD_REFS, "origin/"])
    def test_anything_but_a_ref_name_stops_the_run(self, tmp_path: Path, source_ref: str) -> None:
        """ "origin/" alone too: the REGEN_GATE expressions read the raw input, so it may never mean "generate".
        The rejected value is never echoed: a newline in it would start a workflow command."""
        result = _extract_inputs(tmp_path, source_ref=source_ref)
        assert result.returncode != 0
        assert "::error::source_ref is not a branch, tag or commit SHA" in result.stdout
        assert source_ref not in result.stdout
        assert "injected" not in result.stdout
        assert "source_ref" not in _outputs(tmp_path / "github_output")

    def test_adopting_names_the_source_and_keeps_the_repair_model(self, tmp_path: Path) -> None:
        # source_ref makes the REGEN_GATE expression 'false': a forced regeneration routes to opus.
        result = _extract_inputs(tmp_path, source_ref="gemini/muix-9", regen_gate="false")
        assert result.returncode == 0, result.stdout + result.stderr
        outputs = _outputs(tmp_path / "github_output")
        assert (outputs["model"], outputs["model_reason"]) == ("opus", "forced regeneration")
        summary = (tmp_path / "step_summary").read_text(encoding="utf-8")
        assert "**Generation:** adopted from `gemini/muix-9`" in summary
        assert "**Repair model:** opus (forced regeneration)" in summary
        assert "**Model:**" not in summary
        assert "::notice::Adopting python/matplotlib for spec-a" in result.stdout
        assert "generation: adopted from gemini/muix-9" in result.stdout

    def test_an_explicit_model_still_threads_to_repair(self, tmp_path: Path) -> None:
        result = _extract_inputs(tmp_path, source_ref="main", regen_gate="false", model="sonnet")
        assert result.returncode == 0, result.stdout + result.stderr
        assert _outputs(tmp_path / "github_output")["model"] == "sonnet"

    def test_without_a_source_ref_the_notice_names_the_model(self, tmp_path: Path) -> None:
        result = _extract_inputs(tmp_path, source_ref="")
        assert result.returncode == 0, result.stdout + result.stderr
        assert "**Model:** sonnet (regeneration)" in (tmp_path / "step_summary").read_text(encoding="utf-8")
        assert "::notice::Generating python/matplotlib" in result.stdout

    @pytest.mark.parametrize("source_model", ["gemini-4-argon", "claude-opus-4.7", "gpt_5", "G" * 40])
    def test_a_source_model_is_exported_and_named(self, tmp_path: Path, source_model: str) -> None:
        result = _extract_inputs(tmp_path, source_ref="gemini/muix-9", source_model=source_model, regen_gate="false")
        assert result.returncode == 0, result.stdout + result.stderr
        outputs = _outputs(tmp_path / "github_output")
        assert (outputs["source_ref"], outputs["source_model"]) == ("gemini/muix-9", source_model)
        assert outputs["model"] == "opus"  # still the repair model
        summary = (tmp_path / "step_summary").read_text(encoding="utf-8")
        assert f"**Generation:** adopted from `gemini/muix-9` by {source_model}" in summary
        assert "**Repair model:** opus (forced regeneration)" in summary
        assert f"generation: adopted from gemini/muix-9 by {source_model}, repair model: opus" in result.stdout

    def test_without_a_source_model_nothing_is_named(self, tmp_path: Path) -> None:
        result = _extract_inputs(tmp_path, source_ref="gemini/muix-9", regen_gate="false")
        assert result.returncode == 0, result.stdout + result.stderr
        assert _outputs(tmp_path / "github_output")["source_model"] == ""
        assert " by " not in (tmp_path / "step_summary").read_text(encoding="utf-8")

    @pytest.mark.parametrize("source_ref", ["gemini/muix-9", ""])
    @pytest.mark.parametrize("source_model", BAD_MODELS)
    def test_anything_but_a_model_name_stops_the_run(self, tmp_path: Path, source_model: str, source_ref: str) -> None:
        """Checked before anything else reads it, with or without source_ref, and never echoed."""
        result = _extract_inputs(tmp_path, source_ref=source_ref, source_model=source_model)
        assert result.returncode != 0
        assert "::error::source_model is not a model name" in result.stdout
        assert source_model not in result.stdout
        assert "injected" not in result.stdout
        assert "source_model" not in _outputs(tmp_path / "github_output")

    def test_a_source_model_without_a_source_ref_is_dropped_with_a_warning(self, tmp_path: Path) -> None:
        result = _extract_inputs(tmp_path, source_ref="", source_model="gemini-4-argon")
        assert result.returncode == 0, result.stdout + result.stderr
        assert "::warning::source_model 'gemini-4-argon' ignored" in result.stdout
        outputs = _outputs(tmp_path / "github_output")
        assert (outputs["source_ref"], outputs["source_model"]) == ("", "")
        assert "**Model:** sonnet (regeneration)" in (tmp_path / "step_summary").read_text(encoding="utf-8")
        assert "gemini-4-argon" not in (tmp_path / "step_summary").read_text(encoding="utf-8")


# --- "Adopt implementation from source ref" ----------------------------------------------------


@pytest.mark.parametrize("shell", SHELLS, ids=["bash-e", "pipefail"])
class TestAdoptStep:
    def test_a_python_file_is_taken_rendered_and_pushed_alone(self, tmp_path: Path, shell: list[str]) -> None:
        origin = Origin(tmp_path)
        # A change staged before the step (the prompts overlay stages one) must stay out.
        _write(origin.ws, {"prompts/note.md": "overlaid\n"})
        _git(origin.ws, "add", "prompts/note.md")
        result = origin.run(shell, "gemini/adopt")
        assert result.returncode == 0, result.stdout + result.stderr
        sha = origin.sha("gemini/adopt")
        assert origin.outputs() == {"sha": sha}
        assert origin.pushed_files() == [PY_IMPL]  # not OTHER_IMPL, not prompts/
        assert origin.pushed_text(PY_IMPL) == SOURCE_BRANCHES["gemini/adopt"][PY_IMPL]
        message = origin.pushed_message()
        assert message.startswith("feat(matplotlib): implement spec-a\n")
        assert f"Adopted from gemini/adopt ({sha}); no generation model." in message
        for theme in ("light", "dark"):
            assert (origin.impl_dir / f"plot-{theme}.png").is_file()  # left for the later steps, never committed
        assert result.stdout.count("::notice::canvas_gate library=matplotlib status=pass") == 2
        assert f"::notice::Adopted {PY_IMPL} from gemini/adopt ({sha})" in result.stdout
        assert f"from `gemini/adopt` ({sha})" in origin.summary.read_text(encoding="utf-8")

    def test_the_commit_notice_and_summary_name_the_source_model(self, tmp_path: Path, shell: list[str]) -> None:
        origin = Origin(tmp_path)
        result = origin.run(shell, "gemini/adopt", SOURCE_MODEL="gemini-4-argon")
        assert result.returncode == 0, result.stdout + result.stderr
        sha = origin.sha("gemini/adopt")
        message = origin.pushed_message()
        assert f"Adopted from gemini/adopt ({sha}), written by gemini-4-argon outside the pipeline." in message
        assert "no generation model" not in message
        assert f"::notice::Adopted {PY_IMPL} from gemini/adopt ({sha}), written by gemini-4-argon" in result.stdout
        assert f"from `gemini/adopt` ({sha}), written by gemini-4-argon" in origin.summary.read_text(encoding="utf-8")

    def test_a_js_file_renders_through_the_harness_in_both_themes(self, tmp_path: Path, shell: list[str]) -> None:
        origin = Origin(tmp_path, library="muix")
        result = origin.run(shell, "gemini/adopt")
        assert result.returncode == 0, result.stdout + result.stderr
        harness = f"{origin.ws}/automation/js-render/render.mjs muix.tsx"
        assert origin.node_calls() == [
            [str(origin.impl_dir), "light", harness],
            [str(origin.impl_dir), "dark", harness],
        ]
        assert sorted(path.name for path in origin.impl_dir.glob("plot-*")) == [
            "plot-dark.html",
            "plot-dark.png",
            "plot-light.html",
            "plot-light.png",
        ]
        assert origin.pushed_files() == [JS_IMPL]
        assert result.stdout.count("::notice::canvas_gate library=muix status=pass") == 2
        assert not origin.uv_log.exists()  # numpy was there

    def test_the_helper_venv_gets_numpy_for_the_canvas_check(self, tmp_path: Path, shell: list[str]) -> None:
        origin = Origin(tmp_path, library="muix")
        result = origin.run(shell, "gemini/adopt", NO_NUMPY="1")
        assert result.returncode == 0, result.stdout + result.stderr
        assert origin.uv_log.read_text(encoding="utf-8").splitlines() == ["pip install --python .venv/bin/python numpy"]

    @pytest.mark.parametrize("uv_env", [{"UV_FAIL": "1"}, {"UV_NOOP": "1"}], ids=["install-fails", "still-missing"])
    def test_numpy_that_cannot_be_installed_is_the_runners_failure(
        self, tmp_path: Path, shell: list[str], uv_env: dict[str, str]
    ) -> None:
        """Never mistaken for drift, never pushed unchecked, and no cause: the ordinary retry path."""
        origin = Origin(tmp_path, library="muix")
        result = origin.run(shell, "gemini/adopt", NO_NUMPY="1", **uv_env)
        assert result.returncode == 1
        assert "::error::numpy could not be installed for the canvas check" in result.stdout
        assert "cause" not in origin.outputs()
        assert not origin.pushed()

    def test_a_crashing_canvas_check_is_never_read_as_drift(self, tmp_path: Path, shell: list[str]) -> None:
        origin = Origin(tmp_path)
        _write(origin.ws, {"core/canvas.py": "raise ImportError('broken runner')\n"})
        result = origin.run(shell, "gemini/adopt")
        assert result.returncode == 1
        assert "::error::the canvas check crashed on plot-light.png (exit 1)" in result.stdout
        assert "off the canvas target" not in result.stdout
        assert "cause" not in origin.outputs()
        assert not origin.pushed()

    def test_an_unreachable_origin_is_the_runners_failure(self, tmp_path: Path, shell: list[str]) -> None:
        """A transport failure must not read as a missing ref, which would never be retried."""
        origin = Origin(tmp_path)
        _git(origin.ws, "remote", "set-url", "origin", str(tmp_path / "gone.git"))
        result = origin.run(shell, "gemini/adopt")
        assert result.returncode == 1
        assert "::error::origin is unreachable; cannot fetch source_ref 'gemini/adopt'" in result.stdout
        assert "cause" not in origin.outputs()

    @pytest.mark.parametrize("ref", ["adopt-tag", "sha"])
    def test_a_tag_or_a_commit_sha_works_like_a_branch(self, tmp_path: Path, shell: list[str], ref: str) -> None:
        origin = Origin(tmp_path)
        source_ref = origin.sha("gemini/adopt") if ref == "sha" else ref
        result = origin.run(shell, source_ref)
        assert result.returncode == 0, result.stdout + result.stderr
        assert origin.pushed_text(PY_IMPL) == SOURCE_BRANCHES["gemini/adopt"][PY_IMPL]

    def test_a_file_identical_to_main_still_gets_its_adopt_commit(self, tmp_path: Path, shell: list[str]) -> None:
        origin = Origin(tmp_path)
        result = origin.run(shell, "main")
        assert result.returncode == 0, result.stdout + result.stderr
        assert origin.pushed_files() == []
        assert _git(origin.origin, "rev-list", "--count", f"main..{origin.branch}") == "1"
        assert f"Adopted from main ({origin.sha('main')})" in origin.pushed_message()

    def test_drift_warns_and_leaves_the_fix_to_review_and_repair(self, tmp_path: Path, shell: list[str]) -> None:
        origin = Origin(tmp_path)
        result = origin.run(shell, "gemini/drift")
        assert result.returncode == 0, result.stdout + result.stderr
        assert "::notice::canvas_gate library=matplotlib status=fail actual=3000x1800 target=3200x1800" in result.stdout
        assert "::warning::plot-light.png is off the canvas target" in result.stdout
        assert origin.pushed_files() == [PY_IMPL]

    @pytest.mark.parametrize(
        ("source_ref", "message"),
        [
            ("gemini/no-file", f"::error::{PY_IMPL} does not exist on source_ref gemini/no-file ("),
            ("gemini/nope", "::error::source_ref 'gemini/nope' not found on origin"),
        ],
    )
    def test_a_missing_file_or_ref_fails_before_any_render(
        self, tmp_path: Path, shell: list[str], source_ref: str, message: str
    ) -> None:
        origin = Origin(tmp_path)
        result = origin.run(shell, source_ref)
        assert result.returncode == 1
        assert message in result.stdout
        assert origin.outputs()["cause"] == "missing"
        assert not origin.pushed()
        assert not list(origin.impl_dir.glob("plot-*"))
        assert (origin.ws / PY_IMPL).read_text(encoding="utf-8").endswith("# main\n")  # main's file untouched

    @pytest.mark.parametrize(
        ("source_ref", "message"),
        [
            ("gemini/broken", f"::error::{PY_IMPL} failed to render the light theme"),
            ("gemini/silent", f"::error::{PY_IMPL} rendered no plot-light.png"),
            ("gemini/not-png", f"::error::plot-light.png of {PY_IMPL} is not a readable PNG"),
        ],
    )
    def test_a_file_that_does_not_render_fails_without_a_push(
        self, tmp_path: Path, shell: list[str], source_ref: str, message: str
    ) -> None:
        origin = Origin(tmp_path)
        result = origin.run(shell, source_ref)
        assert result.returncode == 1
        assert message in result.stdout
        assert origin.outputs()["cause"] == "render"
        assert not origin.pushed()

    def test_a_js_render_that_throws_fails_without_a_push(self, tmp_path: Path, shell: list[str]) -> None:
        origin = Origin(tmp_path, library="muix")
        result = origin.run(shell, "gemini/adopt", NODE_FAIL="1")
        assert result.returncode == 1
        assert f"::error::{JS_IMPL} failed to render the light theme" in result.stdout
        assert origin.outputs()["cause"] == "render"
        assert not origin.pushed()

    @pytest.mark.parametrize("library", ["ggplot2", "makie"])
    def test_r_and_julia_are_refused_before_the_fetch(self, tmp_path: Path, shell: list[str], library: str) -> None:
        origin = Origin(tmp_path, library=library)
        result = origin.run(shell, "gemini/adopt")
        assert result.returncode == 1
        assert "::error::Adopt mode renders Python and JavaScript implementations only" in result.stdout
        assert origin.outputs() == {"cause": "unsupported"}
        assert not origin.pushed()


# --- "Create library metadata file": generated_by and adopted_from ---------------------------------


SOURCE_SHA = "8cfea568c" + "0" * 31


def _metadata_writer() -> str:
    """The step's inline Python writer, from `.venv/bin/python3 -c "` to its closing quote."""
    script = str(_step("impl-generate.yml", "Create library metadata file")["run"])
    start = script.index('.venv/bin/python3 -c "\nimport os, yaml\n')
    end = script.index('\n"\n', start) + 2
    return script[start:end]


def _write_metadata(tmp_path: Path, *, source_ref: str, source_model: str, source_sha: str) -> str:
    """Run the writer with the step's shell variables; return the file it wrote."""
    metadata = tmp_path / "muix.yaml"
    writer = _render(_metadata_writer(), {"github.run_id": "1"}).replace(".venv/bin/python3", sys.executable, 1)
    variables = {
        "LIBRARY": "muix",
        "SPEC_ID": SPEC,
        "LANGUAGE": "javascript",
        "TIMESTAMP": "2026-10-23T00:00:00Z",
        "ISSUE": "42",
        "LANGUAGE_VERSION": "22.22.3",
        "LIBRARY_VERSION": "9.16.0",
        "HAS_HTML": "true",
        "METADATA_FILE": str(metadata),
        "MODEL": "opus",
        "SOURCE_REF": source_ref,
        "SOURCE_MODEL": source_model,
        "SOURCE_SHA": source_sha,
    }
    prelude = "".join(f"{name}='{value}'\n" for name, value in variables.items())
    result = subprocess.run(["bash", "-eo", "pipefail", "-c", prelude + writer], capture_output=True, text=True)
    assert result.returncode == 0, result.stdout + result.stderr
    return metadata.read_text(encoding="utf-8")


@pytest.mark.parametrize(
    ("source_ref", "source_model", "generated_by"),
    [("gemini/muix-9", "gemini-4-argon", "gemini-4-argon"), ("gemini/muix-9", "", "adopted:gemini/muix-9")],
)
def test_metadata_of_an_adopted_file_names_its_author_and_source(
    tmp_path: Path, source_ref: str, source_model: str, generated_by: str
) -> None:
    text = _write_metadata(tmp_path, source_ref=source_ref, source_model=source_model, source_sha=SOURCE_SHA)
    # The 2026-10-23 backfill of the MUI X 9 files has the same two lines.
    assert f"generated_by: {generated_by}\nadopted_from: {source_ref} ({SOURCE_SHA})\n" in text
    meta = yaml.safe_load(text)
    assert (meta["generated_by"], meta["adopted_from"]) == (generated_by, f"{source_ref} ({SOURCE_SHA})")
    keys = list(meta)
    assert keys[keys.index("generated_by") + 1] == "adopted_from"
    # Every other key is the one a generated file gets.
    assert tuple(key for key in keys if key != "adopted_from") == review_retest.IMPL_GENERATE_METADATA_KEYS


def test_metadata_of_a_generated_file_has_no_adopted_from(tmp_path: Path) -> None:
    meta = yaml.safe_load(_write_metadata(tmp_path, source_ref="", source_model="", source_sha=""))
    assert meta["generated_by"] == "claude-opus"
    assert tuple(meta) == review_retest.IMPL_GENERATE_METADATA_KEYS


# --- "Handle generation failure" ----------------------------------------------------------------


class Handler:
    """The failure handler against a fake `gh`, in a git repo without origin (nothing live unless labelled)."""

    def __init__(self, tmp: Path) -> None:
        self.cwd = tmp / "repo"
        self.cwd.mkdir()
        _git(self.cwd, "init", "-q")
        self.bin = tmp / "bin"
        _executable(self.bin / "gh", FAKE_GH)
        self.log = tmp / "gh.log"
        step = _step("impl-generate.yml", HANDLER_STEP)
        self.script = _render(str(step["run"]), {"github.repository": "owner/repo", "github.run_id": "1"})
        self.constants = {key: str(step["env"][key]) for key in ("CAMPAIGN_WINDOW_H", "INFRA_WINDOW_CAP")}

    def run(
        self, *, source_ref: str, adopt_cause: str, regen_label: str = "", source_model: str = ""
    ) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["bash", "-eo", "pipefail", "-c", self.script],
            cwd=self.cwd,
            env=_env(
                PATH=f"{self.bin}{os.pathsep}{os.environ['PATH']}",
                GH_LOG=str(self.log),
                TEST_PYTHON=sys.executable,
                GH_TOKEN="unused",
                SPEC_ID=SPEC,
                LIBRARY="muix",
                ISSUE="42",
                MODEL="opus",
                CHANGE_REQUEST="",
                CLAUDE_RETRY_OUTCOME="skipped",
                CLAUDE_EXEC_FILE="",
                GCP_AUTH_OUTCOME="",
                GCLOUD_OUTCOME="",
                GCS_OUTCOME="",
                PR_OUTCOME="",
                REVIEW_DISPATCH_OUTCOME="",
                REGEN_LABEL=regen_label,
                LANGUAGE="javascript",
                EXT=".tsx",
                REGEN_GATE="false" if source_ref else "true",
                SOURCE_REF=source_ref,
                SOURCE_MODEL=source_model,
                ADOPT_CAUSE=adopt_cause,
                TRIGGER_REF="main",
                RUN_URL="https://github.com/owner/repo/actions/runs/1",
                **self.constants,
            ),
            capture_output=True,
            text=True,
        )

    def calls(self) -> list[list[str]]:
        if not self.log.exists():
            return []
        return [json.loads(line) for line in self.log.read_text(encoding="utf-8").splitlines()]

    def comments(self) -> list[str]:
        return [call[call.index("--body") + 1] for call in self.calls() if call[:2] == ["issue", "comment"]]

    def label_edits(self) -> list[tuple[str, str]]:
        return [(call[3], call[4]) for call in self.calls() if call[:2] == ["issue", "edit"]]

    def dispatches(self) -> list[list[str]]:
        return [call for call in self.calls() if call[:2] == ["workflow", "run"]]


class TestHandler:
    @pytest.mark.parametrize("cause", ["missing", "render", "unsupported"])
    def test_a_source_failure_is_never_retried_counted_or_marked_failed(self, tmp_path: Path, cause: str) -> None:
        handler = Handler(tmp_path)
        result = handler.run(source_ref="gemini/muix-9", adopt_cause=cause, regen_label="regen:forced")
        assert result.returncode == 0, result.stdout + result.stderr
        assert handler.dispatches() == []
        assert not [call for call in handler.calls() if call[0] == "api"]  # the attempt counter is never read
        (comment,) = handler.comments()
        assert comment.startswith("<!-- impl-adopt-fail:spec-a:muix -->\n")
        assert "<!-- impl-fail:" not in comment  # never counted toward the 3-attempt cap
        assert f"## :inbox_tray: muix Adoption Failed ({cause})" in comment
        assert "The implementation on main is unchanged and stays live." in comment
        assert (
            "gh workflow run impl-generate.yml -f specification_id=spec-a -f library=muix -f issue_number=42"
            " -f source_ref=gemini/muix-9" in comment
        )
        assert handler.label_edits() == [
            ("--remove-label", "generate:muix"),
            ("--remove-label", "impl:muix:pending"),
            ("--add-label", "impl:muix:done"),
        ]

    def test_a_source_failure_of_a_new_pair_leaves_it_unmarked(self, tmp_path: Path) -> None:
        handler = Handler(tmp_path)
        result = handler.run(source_ref="gemini/muix-9", adopt_cause="missing")
        assert result.returncode == 0, result.stdout + result.stderr
        assert handler.dispatches() == []
        assert "The pair has no implementation on main yet." in handler.comments()[0]
        assert all("impl:muix:failed" not in label and "done" not in label for _, label in handler.label_edits())

    def test_a_later_failure_retries_and_keeps_adopting(self, tmp_path: Path) -> None:
        """Metadata, upload or PR failed after the file was taken: the ordinary path, source_ref kept."""
        handler = Handler(tmp_path)
        result = handler.run(source_ref="gemini/muix-9", adopt_cause="", regen_label="regen:forced")
        assert result.returncode == 0, result.stdout + result.stderr
        (comment,) = handler.comments()
        assert comment.startswith("<!-- impl-fail:spec-a:muix -->\n")
        (dispatch,) = handler.dispatches()
        assert dispatch[2:5] == ["impl-generate.yml", "--ref", "main"]
        assert "source_ref=gemini/muix-9" in dispatch
        assert "regen_gate=false" in dispatch
        assert "model=opus" in dispatch

    def test_an_ordinary_retry_stays_an_ordinary_generation(self, tmp_path: Path) -> None:
        handler = Handler(tmp_path)
        result = handler.run(source_ref="", adopt_cause="")
        assert result.returncode == 0, result.stdout + result.stderr
        (dispatch,) = handler.dispatches()
        assert "source_ref=" in dispatch
        assert "source_model=" in dispatch
        assert "regen_gate=true" in dispatch

    def test_a_retry_keeps_the_source_model(self, tmp_path: Path) -> None:
        handler = Handler(tmp_path)
        result = handler.run(
            source_ref="gemini/muix-9", source_model="gemini-4-argon", adopt_cause="", regen_label="regen:forced"
        )
        assert result.returncode == 0, result.stdout + result.stderr
        (dispatch,) = handler.dispatches()
        assert "source_ref=gemini/muix-9" in dispatch
        assert "source_model=gemini-4-argon" in dispatch

    def test_a_source_failure_names_the_source_model_in_its_rerun_command(self, tmp_path: Path) -> None:
        handler = Handler(tmp_path)
        result = handler.run(source_ref="gemini/muix-9", source_model="gemini-4-argon", adopt_cause="render")
        assert result.returncode == 0, result.stdout + result.stderr
        assert handler.dispatches() == []
        assert " -f source_ref=gemini/muix-9 -f source_model=gemini-4-argon\n" in handler.comments()[0]

    def test_the_manual_retry_hints_keep_the_source_ref_and_model(self) -> None:
        script = str(_step("impl-generate.yml", HANDLER_STEP)["run"])
        hint = "-f model=${MODEL}${SOURCE_REF:+ -f source_ref=${SOURCE_REF}}${SOURCE_MODEL:+ -f source_model=${SOURCE_MODEL}}"
        assert script.count(hint) == 2  # the infrastructure pause and the retry cap


# --- bulk-generate ------------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("source_ref", "source_model"), [("gemini/muix-9", "gemini-4-argon"), ("gemini/muix-9", ""), ("", "")]
)
def test_bulk_generate_passes_source_ref_and_model_to_every_dispatch(
    tmp_path: Path, source_ref: str, source_model: str
) -> None:
    """spec-a has an issue (the `-f issue_number` branch), spec-b has none (the other branch)."""
    _write(tmp_path, {"plots/spec-a/specification.yaml": "issue: 42\n"})
    bin_dir = tmp_path / "bin"
    _executable(bin_dir / "gh", FAKE_GH)
    _executable(bin_dir / "yq", FAKE_YQ)
    log = tmp_path / "gh.log"
    matrix = {
        "include": [
            {"specification_id": "spec-a", "library": "muix"},
            {"specification_id": "spec-b", "library": "muix"},
        ]
    }
    script = _render(str(_step("bulk-generate.yml", BULK_STEP)["run"]), {"github.repository": "owner/repo"})
    result = subprocess.run(
        ["bash", "-e", "-c", script],
        cwd=tmp_path,
        env=_env(
            PATH=f"{bin_dir}{os.pathsep}{os.environ['PATH']}",
            GH_LOG=str(log),
            TEST_PYTHON=sys.executable,
            GH_TOKEN="unused",
            MATRIX=json.dumps(matrix),
            PACE_SECONDS="0",
            MODEL="auto",
            CHANGE_REQUESTS="{}",
            REGEN_GATE="true",
            SOURCE_REF=source_ref,
            SOURCE_MODEL=source_model,
        ),
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    calls = [json.loads(line) for line in log.read_text(encoding="utf-8").splitlines()]
    dispatches = [call for call in calls if call[:2] == ["workflow", "run"]]
    assert [call[call.index("-f") + 1] for call in dispatches] == ["specification_id=spec-a", "specification_id=spec-b"]
    assert "issue_number=42" in dispatches[0] and "issue_number=42" not in " ".join(dispatches[1])
    assert all(f"source_ref={source_ref}" in call for call in dispatches)
    assert all(f"source_model={source_model}" in call for call in dispatches)
    assert f"source_ref={source_ref or 'none'}, source_model={source_model or 'none'}" in result.stdout


def _bulk_preview(tmp_path: Path, *, source_ref: str, source_model: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["bash", "-e", "-c", str(_step("bulk-generate.yml", "Preview generation plan")["run"])],
        cwd=tmp_path,
        env=_env(
            MATRIX=json.dumps({"include": [{"specification_id": "spec-a", "library": "muix"}]}),
            COUNT="1",
            DRY_RUN="true",
            PACE_SECONDS="180",
            SOURCE_REF=source_ref,
            SOURCE_MODEL=source_model,
        ),
        capture_output=True,
        text=True,
    )


def test_bulk_preview_names_the_source_model(tmp_path: Path) -> None:
    result = _bulk_preview(tmp_path, source_ref="gemini/muix-9", source_model="gemini-4-argon")
    assert result.returncode == 0, result.stdout + result.stderr
    assert "taken from `gemini/muix-9` instead of being generated (written by gemini-4-argon)" in result.stdout
    assert "::warning::" not in result.stdout


def test_bulk_preview_warns_about_a_source_model_without_a_source_ref(tmp_path: Path) -> None:
    result = _bulk_preview(tmp_path, source_ref="", source_model="gemini-4-argon")
    assert result.returncode == 0, result.stdout + result.stderr
    assert "::warning::source_model is set without source_ref" in result.stdout
    assert "**Adopt mode:**" not in result.stdout


@pytest.mark.parametrize("source_ref", ["origin/gemini/muix-9", "main", "0123456789abcdef0123456789abcdef01234567"])
def test_bulk_preview_accepts_what_impl_generate_accepts(tmp_path: Path, source_ref: str) -> None:
    result = _bulk_preview(tmp_path, source_ref=source_ref, source_model="")
    assert result.returncode == 0, result.stdout + result.stderr


@pytest.mark.parametrize("source_ref", [*BAD_REFS, "origin/"])
def test_bulk_preview_stops_on_a_bad_ref_before_echoing_it(tmp_path: Path, source_ref: str) -> None:
    result = _bulk_preview(tmp_path, source_ref=source_ref, source_model="gemini-4-argon")
    assert result.returncode == 1
    assert result.stdout == (
        "::error::source_ref is not a branch, tag or commit SHA (letters, digits, . _ / -, at most 80 characters)\n"
    )


@pytest.mark.parametrize("source_model", BAD_MODELS)
def test_bulk_preview_stops_on_a_bad_model_before_echoing_it(tmp_path: Path, source_model: str) -> None:
    """The generate job needs this one, so no dispatch (and no dispatch notice) ever sees the value."""
    result = _bulk_preview(tmp_path, source_ref="gemini/muix-9", source_model=source_model)
    assert result.returncode == 1
    assert (
        result.stdout == "::error::source_model is not a model name (letters, digits, . _ -, at most 40 characters)\n"
    )


def test_bulk_dispatch_runs_only_after_the_preview_checked_the_inputs() -> None:
    generate = _workflow("bulk-generate.yml")["jobs"]["generate"]
    assert "preview" in generate["needs"]
    # A custom `if` without a status function keeps the implicit success() on `needs`.
    assert not re.search(r"\b(always|failure|cancelled)\(", generate["if"])


@pytest.mark.parametrize(("pattern", "name"), [(REF_PATTERN, "SOURCE_REF"), (MODEL_PATTERN, "SOURCE_MODEL")])
def test_both_workflows_check_with_the_same_pattern(pattern: str, name: str) -> None:
    impl = str(_step("impl-generate.yml", "Extract inputs")["run"])
    bulk = str(_step("bulk-generate.yml", "Preview generation plan")["run"])
    variable = "$SOURCE_REF" if name == "SOURCE_REF" else "$SOURCE_MODEL"
    assert f'[[ "{variable}" =~ {pattern} ]]' in impl
    assert f"=~ {pattern} ]]" in bulk
