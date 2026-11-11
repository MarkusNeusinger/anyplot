"""The record-only readiness scan in impl-generate.yml and impl-repair.yml (P2b).

"Readiness scan (record-only)" copies the agent chat's validator and
automation/scripts/readiness_scan.py from the workflow's own ref, scans the
implementation and its predecessor from origin/main, and leaves
`$RUNNER_TEMP/adapt/readiness.json` beside the smoke run. It never fails the
job, and no copy of the predecessor is left behind (its header holds the
stored score).

The step scripts run here under `bash -e` and `bash -eo pipefail` against a
scratch origin. The workflow ref carries a stub scanner; the real one has its
own tests in tests/unit/automation/scripts/test_readiness_scan.py.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest

from tests.unit.workflows.test_adapt_generate_steps import (
    IMPL,
    LIB,
    SHELLS,
    SMOKE_STEP,
    SPEC,
    Staging,
    _env,
    _git,
    _names,
    _step,
    _write,
)


STEP = "Readiness scan (record-only)"
WORKFLOWS = ["impl-generate.yml", "impl-repair.yml"]
SCANNER = "automation/scripts/readiness_scan.py"
SHELL_IDS = ["bash-e", "pipefail"]

STUB_SCANNER = '''"""Stub readiness_scan: logs its call and the predecessor it was given, writes --out, exits with STUB_EXIT."""
import json
import os
import pathlib
import sys

args = sys.argv[1:]
prev = pathlib.Path(args[args.index("--prev") + 1])
call = {
    "args": args,
    "module": __file__,
    "isolated": bool(sys.flags.isolated),
    "prev_text": prev.read_text() if prev.exists() else None,
    "tree": sorted(str(p.relative_to(pathlib.Path(__file__).parents[2])) for p in pathlib.Path(__file__).parents[2].rglob("*") if p.is_file()),
    "package_files": [(pathlib.Path(__file__).parents[2] / p).read_text() for p in ("agents/__init__.py", "agents/anyplot/__init__.py")],
}
with open(os.environ["STUB_LOG"], "a") as handle:
    handle.write(json.dumps(call) + "\\n")
if int(os.environ.get("STUB_EXIT", "0")) == 0:
    pathlib.Path(args[args.index("--out") + 1]).write_text(json.dumps({"stub": True}))
sys.exit(int(os.environ.get("STUB_EXIT", "0")))
'''
BRANCH_SCANNER = "import os\nopen(os.environ['STUB_LOG'], 'a').write('{\"args\": [\"BRANCH-SCANNER\"]}\\n')\n"
VALIDATOR_TREE = {
    "agents/__init__.py": "raise SystemExit('the agent runtime was copied')\n",
    "agents/anyplot/__init__.py": "raise SystemExit('the agent runtime was copied')\n",
    "agents/anyplot/code/__init__.py": "",
    "agents/anyplot/code/readiness.py": "",
    "agents/anyplot/schemas.py": "",
    "agents/anyplot/language.py": "",
    "agents/anyplot/agent.py": "",
    "core/__init__.py": "",
    SCANNER: STUB_SCANNER,
}


class Runner:
    """A workspace on the implementation branch, an origin/main, and the workflow ref holding the stub scanner."""

    def __init__(self, tmp: Path, *, regeneration: bool) -> None:
        seed = tmp / "seed"
        seed.mkdir()
        _git(seed, "init", "-q", "-b", "main")
        _write(seed, {**VALIDATOR_TREE, **({IMPL: "PREDECESSOR\n"} if regeneration else {})})
        _git(seed, "add", "-A")
        _git(seed, "commit", "-q", "-m", "main")
        self.sha = _git(seed, "rev-parse", "HEAD")
        origin = tmp / "origin.git"
        subprocess.run(["git", "clone", "-q", "--bare", str(seed), str(origin)], check=True, env=_env())
        self.ws = tmp / "ws"
        subprocess.run(["git", "clone", "-q", str(origin), str(self.ws)], check=True, env=_env())
        _git(self.ws, "checkout", "-q", "-b", f"implementation/{SPEC}/{LIB}")
        # The branch carries its own scanner, as a generator could have written one.
        _write(self.ws, {IMPL: "GENERATED\n", SCANNER: BRANCH_SCANNER})
        _git(self.ws, "add", "-A")
        _git(self.ws, "commit", "-q", "-m", "feat: implement")
        python = self.ws / ".venv" / "bin" / "python"
        python.parent.mkdir(parents=True)
        python.write_text(f'#!/bin/sh\nexec "{sys.executable}" "$@"\n', encoding="utf-8")
        python.chmod(0o755)
        self.runner_temp = tmp / "runner"
        self.runner_temp.mkdir()
        self.log = tmp / "stub.jsonl"

    @property
    def record(self) -> Path:
        return self.runner_temp / "adapt" / "readiness.json"

    def calls(self) -> list[dict[str, Any]]:
        if not self.log.exists():
            return []
        return [json.loads(line) for line in self.log.read_text(encoding="utf-8").splitlines()]

    def run(self, workflow: str, shell: list[str], *, sha: str | None = None, stub_exit: int = 0):
        script = str(_step(workflow, STEP)["run"])
        assert "${{" not in script
        return subprocess.run(
            [*shell, script],
            cwd=self.ws,
            env=_env(
                RUNNER_TEMP=str(self.runner_temp),
                GITHUB_SHA=sha or self.sha,
                SPEC_ID=SPEC,
                LIBRARY=LIB,
                STUB_LOG=str(self.log),
                STUB_EXIT=str(stub_exit),
            ),
            capture_output=True,
            text=True,
        )


# --- wiring ------------------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("workflow", "condition"),
    [
        ("impl-generate.yml", "steps.inputs.outputs.language == 'python'"),
        ("impl-repair.yml", "success() && steps.lang.outputs.language == 'python'"),
    ],
)
def test_the_step_is_record_only_python_only_and_follows_the_smoke_run(workflow: str, condition: str) -> None:
    names = _names(workflow)
    step = _step(workflow, STEP)
    assert names[names.index(SMOKE_STEP) + 1] == STEP  # the smoke run clears $RUNNER_TEMP/adapt first
    assert step["if"] == condition
    assert step["continue-on-error"] is True and step["timeout-minutes"] == 5
    assert "id" not in step  # no later step can key a decision on it
    assert "exit 1" not in str(step["run"])


def test_generate_scans_before_the_upload_that_stages_the_adapt_folder() -> None:
    names = _names("impl-generate.yml")
    assert names.index("Create library metadata file") < names.index(STEP) < names.index("Upload to GCS Staging")


def test_both_workflows_run_the_same_scan() -> None:
    """The two scripts differ only in whose session the first comment names."""
    generate, repair = (str(_step(workflow, STEP)["run"]) for workflow in WORKFLOWS)
    assert generate.replace("the generator's", "the repair's") == repair


# --- the step ----------------------------------------------------------------------------------


@pytest.mark.parametrize("shell", SHELLS, ids=SHELL_IDS)
@pytest.mark.parametrize("workflow", WORKFLOWS)
class TestScanStep:
    def test_a_regeneration_is_scanned_against_main_by_the_workflow_refs_copy(self, tmp_path, shell, workflow):
        runner = Runner(tmp_path, regeneration=True)
        result = runner.run(workflow, shell)
        assert result.returncode == 0, result.stdout + result.stderr
        (call,) = runner.calls()
        tools = runner.runner_temp / "readiness-tools"
        assert call["module"] == str(tools / SCANNER)  # not the branch's scanner
        assert call["isolated"] is True  # -I: the workspace is not on the import path
        assert call["args"] == [
            "scan",
            "--new",
            IMPL,
            "--prev",
            str(runner.runner_temp / "readiness-prev-source"),
            "--spec-id",
            SPEC,
            "--library",
            LIB,
            "--out",
            str(runner.record),
        ]
        assert call["prev_text"] == "PREDECESSOR\n"
        assert json.loads(runner.record.read_text(encoding="utf-8")) == {"stub": True}
        # The predecessor's header holds its stored score: no copy stays on the runner.
        assert not (runner.runner_temp / "readiness-prev-source").exists()

    def test_only_the_validator_is_copied_not_the_agent_runtime(self, tmp_path, shell, workflow):
        runner = Runner(tmp_path, regeneration=True)
        assert runner.run(workflow, shell).returncode == 0
        (call,) = runner.calls()
        assert call["tree"] == [
            "agents/__init__.py",
            "agents/anyplot/__init__.py",
            "agents/anyplot/code/__init__.py",
            "agents/anyplot/code/readiness.py",
            "agents/anyplot/language.py",
            "agents/anyplot/schemas.py",
            SCANNER,
            "core/__init__.py",
        ]
        # The step writes the two package files itself, empty: regular packages win the import over
        # anything named `agents` in site-packages, and the ref's own files (the agent runtime) stay out.
        assert call["package_files"] == ["", ""]

    def test_a_first_generation_has_no_predecessor(self, tmp_path, shell, workflow):
        runner = Runner(tmp_path, regeneration=False)
        result = runner.run(workflow, shell)
        assert result.returncode == 0, result.stdout + result.stderr
        (call,) = runner.calls()
        assert call["prev_text"] is None
        assert runner.record.exists()

    def test_the_smoke_runs_records_stay_and_a_stale_readiness_record_goes(self, tmp_path, shell, workflow):
        runner = Runner(tmp_path, regeneration=True)
        runner.record.parent.mkdir()
        (runner.record.parent / "new-smoke.json").write_text("{}", encoding="utf-8")
        runner.record.write_text('{"stale": true}', encoding="utf-8")
        result = runner.run(workflow, shell, stub_exit=3)
        assert result.returncode == 0, result.stdout + result.stderr  # a failing scanner never fails the step
        assert "::warning::readiness_scan did not run; no readiness record is staged" in result.stdout
        assert not runner.record.exists()  # never the record of other code
        assert (runner.record.parent / "new-smoke.json").exists()
        assert not (runner.runner_temp / "readiness-prev-source").exists()

    def test_without_the_workflow_ref_nothing_runs(self, tmp_path, shell, workflow):
        runner = Runner(tmp_path, regeneration=True)
        result = runner.run(workflow, shell, sha="0" * 40)
        assert result.returncode == 0, result.stdout + result.stderr
        assert "::warning::readiness_scan could not copy the validator from " in result.stdout
        assert runner.calls() == [] and not runner.record.exists()


# --- impl-repair's upload ------------------------------------------------------------------------


@pytest.mark.parametrize("shell", SHELLS, ids=SHELL_IDS)
class TestRepairUpload:
    UPLOAD = "Upload repaired plot to GCS staging"

    def test_the_repaired_files_record_is_staged(self, tmp_path, shell):
        staging = Staging(tmp_path)
        (staging.adapt / "readiness.json").write_text("{}", encoding="utf-8")
        calls = staging.run("impl-repair.yml", self.UPLOAD, shell)
        assert (
            f"-h Cache-Control:no-store cp {staging.adapt}/readiness.json {staging.staging}/adapt/readiness.json"
            in calls
        )
        assert f"rm {staging.staging}/adapt/readiness.json" not in calls
        assert "::notice::Staged the repaired file's adapt/readiness.json" in staging.stdout

    def test_without_a_record_the_one_of_the_code_before_the_repair_goes(self, tmp_path, shell):
        staging = Staging(tmp_path)
        calls = staging.run("impl-repair.yml", self.UPLOAD, shell, GSUTIL_RM_MISSES="1")
        assert f"rm {staging.staging}/adapt/readiness.json" in calls
        assert not [call for call in calls if " cp " in call and "readiness.json" in call]

    def test_other_languages_touch_no_readiness_record(self, tmp_path, shell):
        staging = Staging(tmp_path, language="r")
        calls = staging.run("impl-repair.yml", self.UPLOAD, shell)
        assert calls and not [call for call in calls if "readiness" in call]
