"""The readiness self-check's copy in impl-generate.yml and impl-repair.yml, and its distance from the gate's scan.

"Prepare the readiness self-check" puts a bare copy of the agent chat's
validator, from the workflow's own ref, at the path the prompts name, before
the session starts. The session runs `readiness_scan.py check` from it (Step 3c
of impl-generate-claude.md, Step 5b of impl-repair-claude.md). The step never
fails the job.

The session can write anywhere on the runner, this copy included. So the
record that the regen gate reads must never come from it: "Readiness scan
(record-only)" makes its own copy after the session and names no path of this
one. Both are pinned here, by reading the scripts and by running them, under
`bash -e` and `bash -eo pipefail`, against a scratch origin.
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

import pytest

from tests.unit.workflows.test_adapt_generate_steps import SHELLS, _env, _git, _names, _step, _workflow
from tests.unit.workflows.test_readiness_scan_steps import SCANNER, SHELL_IDS, STEP, Runner


ROOT = Path(__file__).resolve().parents[3]
PREPARE = "Prepare the readiness self-check"
SESSION_TOOLS = "/tmp/anyplot-readiness"
WORKFLOWS = ["impl-generate.yml", "impl-repair.yml"]
SESSIONS = {
    "impl-generate.yml": ("Run Claude Code to generate implementation", "Retry Claude (on failure)"),
    "impl-repair.yml": ("Run Claude Code to repair implementation", "Retry Claude (on failure)"),
}
PROMPTS = {
    "impl-generate.yml": ROOT / "prompts" / "workflow-prompts" / "impl-generate-claude.md",
    "impl-repair.yml": ROOT / "prompts" / "workflow-prompts" / "impl-repair-claude.md",
}
HOSTILE_SCANNER = (
    'import os\nopen(os.environ[\'STUB_LOG\'], \'a\').write(\'{"args": ["SESSION-COPY"], "module": "x"}\\n\')\n'
)


def _archived(script: str) -> list[str]:
    """The paths of a step's `git archive "$GITHUB_SHA" … | tar` line."""
    match = re.search(r'git archive "\$GITHUB_SHA" (.+?) \| tar ', script.replace("\\\n", " "), re.DOTALL)
    assert match, "the step no longer extracts the validator with git archive"
    return match.group(1).split()


# --- wiring ------------------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("workflow", "condition"),
    [
        ("impl-generate.yml", "steps.inputs.outputs.language == 'python' && steps.inputs.outputs.source_ref == ''"),
        ("impl-repair.yml", "steps.lang.outputs.language == 'python'"),
    ],
)
def test_the_copy_is_made_right_before_the_session_and_never_fails_the_job(workflow, condition):
    names = _names(workflow)
    session, retry = SESSIONS[workflow]
    assert names.index(PREPARE) + 1 == names.index(session) < names.index(retry)
    step = _step(workflow, PREPARE)
    assert step["if"] == condition  # Python only; adopt mode starts no session
    assert step["continue-on-error"] is True and step["timeout-minutes"] == 2
    assert "id" not in step  # no later step can key a decision on it
    assert "exit 1" not in str(step["run"])


@pytest.mark.parametrize("workflow", WORKFLOWS)
def test_the_session_gets_the_same_validator_as_the_gates_scan(workflow):
    """Both copies come from the workflow's ref, path for path, so the session sees what the record will see."""
    prepare, scan = str(_step(workflow, PREPARE)["run"]), str(_step(workflow, STEP)["run"])
    assert _archived(prepare) == _archived(scan)
    assert ': > "$TOOLS/agents/__init__.py"; : > "$TOOLS/agents/anyplot/__init__.py"' in prepare


def test_both_workflows_prepare_the_same_copy():
    generate, repair = (_step(workflow, PREPARE) for workflow in WORKFLOWS)
    assert generate["run"] == repair["run"]
    assert generate["env"] == repair["env"] == {"TOOLS": SESSION_TOOLS}


@pytest.mark.parametrize("workflow", WORKFLOWS)
def test_the_prompt_runs_the_check_from_that_copy(workflow):
    prompt = PROMPTS[workflow].read_text(encoding="utf-8")
    command = f".venv/bin/python -I {SESSION_TOOLS}/automation/scripts/readiness_scan.py check"
    assert command in prompt
    assert "--spec-id {SPEC_ID} --library {LIBRARY}" in prompt


# --- the gate's scan never reads the session's copy ------------------------------------------------


def _code(script: str) -> str:
    return "\n".join(line for line in script.splitlines() if not line.lstrip().startswith("#"))


def _reads(script: str) -> set[str]:
    """Every shell variable a step script reads."""
    return set(re.findall(r"\$\{?([A-Za-z_]\w*)", _code(script)))


def _assigns(script: str) -> set[str]:
    return set(re.findall(r"(?:^|[;\s])([A-Za-z_]\w*)=", _code(script), re.MULTILINE))


@pytest.mark.parametrize("workflow", WORKFLOWS)
def test_the_gates_scan_names_no_path_of_the_sessions_copy(workflow):
    scan = _step(workflow, STEP)
    text = "\n".join([str(scan["run"]), *(str(value) for value in (scan.get("env") or {}).values())])
    assert SESSION_TOOLS not in text and "anyplot-readiness" not in text
    # Its own copy, made afresh from the workflow's ref after the session.
    script = str(scan["run"])
    assert 'TOOLS="$RUNNER_TEMP/readiness-tools"' in script
    assert script.index('rm -rf "$TOOLS"') < script.index('git archive "$GITHUB_SHA"')


@pytest.mark.parametrize("workflow", WORKFLOWS)
def test_no_channel_carries_the_sessions_copy_to_the_gates_scan(workflow):
    """Not by name, and not through a variable: no `$GITHUB_ENV` line, no job or workflow `env`, nothing inherited.

    Each script reads only what it assigns itself, its own step's `env`, and two runner values, so a variable
    another step exported (`echo "X=$TOOLS" >> "$GITHUB_ENV"`, then `${X:-$TOOLS}`) fails here.
    """
    text = (ROOT / ".github" / "workflows" / workflow).read_text(encoding="utf-8")
    assert text.count("anyplot-readiness") == 1  # the prepare step's own `env`, nowhere else
    document = _workflow(workflow)
    assert "env" not in document and all("env" not in job for job in document["jobs"].values())
    runner_values = {"RUNNER_TEMP", "GITHUB_SHA"}
    for name in (PREPARE, STEP):
        step = _step(workflow, name)
        script = str(step["run"])
        foreign = _reads(script) - _assigns(script) - set(step.get("env") or {}) - runner_values
        assert foreign == set(), (name, foreign)
    assert not re.search(r"GITHUB_(ENV|OUTPUT|PATH|STATE)", str(_step(workflow, PREPARE)["run"]))


def _prepare(runner: Runner, workflow: str, shell: list[str], tools: Path, *, sha: str | None = None):
    script = str(_step(workflow, PREPARE)["run"])
    assert "${{" not in script
    return subprocess.run(
        [*shell, script],
        cwd=runner.ws,
        env=_env(GITHUB_SHA=sha or runner.sha, TOOLS=str(tools)),
        capture_output=True,
        text=True,
    )


def _files(root: Path) -> list[str]:
    return sorted(str(path.relative_to(root)) for path in root.rglob("*") if path.is_file())


@pytest.mark.parametrize("shell", SHELLS, ids=SHELL_IDS)
@pytest.mark.parametrize("workflow", WORKFLOWS)
class TestPrepareStep:
    def test_the_copy_is_the_bare_validator_from_the_workflow_ref(self, tmp_path, shell, workflow):
        runner = Runner(tmp_path, regeneration=True)
        tools = tmp_path / "anyplot-readiness"
        (tools / "stale").mkdir(parents=True)
        (tools / "stale" / "left.py").write_text("x", encoding="utf-8")
        # The workspace's own validator differs from the ref's in every file, as a checkout of another branch would.
        tracked = _git(runner.ws, "ls-files", "agents", "core", "automation").splitlines()
        for relative in tracked:
            (runner.ws / relative).write_text(f"BRANCH {relative}\n", encoding="utf-8")
        result = _prepare(runner, workflow, shell, tools)
        assert result.returncode == 0, result.stdout + result.stderr
        assert f"::notice::readiness self-check: the validator from {runner.sha} is at {tools}" in result.stdout
        assert _files(tools) == [
            "agents/__init__.py",
            "agents/anyplot/__init__.py",
            "agents/anyplot/code/__init__.py",
            "agents/anyplot/code/readiness.py",
            "agents/anyplot/language.py",
            "agents/anyplot/schemas.py",
            "automation/scripts/readiness_record.py",
            SCANNER,
            "core/__init__.py",
        ]
        # The ref's scanner, not the one the branch carries; the package files are empty, not the agent runtime.
        assert "Stub readiness_scan" in (tools / SCANNER).read_text(encoding="utf-8")
        assert [(tools / name).read_text() for name in ("agents/__init__.py", "agents/anyplot/__init__.py")] == ["", ""]
        # Every other file, validator modules included, is byte for byte the ref's.
        for relative in _files(tools):
            if relative not in ("agents/__init__.py", "agents/anyplot/__init__.py"):
                ref = subprocess.run(
                    ["git", "-C", str(runner.ws), "show", f"{runner.sha}:{relative}"],
                    capture_output=True,
                    env=_env(),
                    check=True,
                ).stdout
                assert (tools / relative).read_bytes() == ref, relative

    def test_without_the_workflow_ref_there_is_no_copy_and_no_failure(self, tmp_path, shell, workflow):
        runner = Runner(tmp_path, regeneration=True)
        tools = tmp_path / "anyplot-readiness"
        result = _prepare(runner, workflow, shell, tools, sha="0" * 40)
        assert result.returncode == 0, result.stdout + result.stderr
        assert "::warning::the readiness self-check could not copy the validator from " in result.stdout
        assert not tools.exists()

    def test_a_copy_the_session_changed_never_reaches_the_record(self, tmp_path, shell, workflow):
        """The session rewrites the scanner of its copy; the gate's scan still runs the workflow ref's own."""
        runner = Runner(tmp_path, regeneration=True)
        tools = tmp_path / "anyplot-readiness"
        assert _prepare(runner, workflow, shell, tools).returncode == 0
        (tools / SCANNER).write_text(HOSTILE_SCANNER, encoding="utf-8")
        (tools / "agents" / "__init__.py").write_text("raise SystemExit('session')\n", encoding="utf-8")
        result = runner.run(workflow, shell)
        assert result.returncode == 0, result.stdout + result.stderr
        (call,) = runner.calls()
        assert call["args"][0] == "scan"
        assert call["module"] == str(runner.runner_temp / "readiness-tools" / SCANNER)
        assert call["package_files"] == ["", ""]
        assert runner.record.exists()
