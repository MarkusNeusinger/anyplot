"""The adaptability smoke-run steps of impl-generate.yml and impl-repair.yml (PR 2 contract, sections 1.6 and 3).

Both steps are record-only: they run `core.smoke_run` from the workflow's own ref, write
their JSON under `$RUNNER_TEMP/adapt`, and never fail the job. The upload steps stage the
results privately under `staging/.../adapt/`, after clearing an earlier run's. The step
scripts run here against a scratch origin, with a stub `core/smoke_run.py` in the workflow
ref, a different one on the implementation branch (the generator could have written it),
and a stub `gsutil`, under `bash -e` (the Actions default) and `bash -eo pipefail`.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest
import yaml


WORKFLOWS_DIR = Path(__file__).resolve().parents[3] / ".github" / "workflows"
SMOKE_STEP = "Adaptability smoke run (record-only)"
SPEC, LIB = "bar-grouped", "matplotlib"
IMPL = f"plots/{SPEC}/implementations/python/{LIB}.py"
SPEC_FILE = f"plots/{SPEC}/specification.md"
SHELLS = [["bash", "-e", "-c"], ["bash", "-eo", "pipefail", "-c"]]

STUB_RUNNER = '''"""Stub core.smoke_run: logs its call, writes --out and the pair renders, exits with STUB_EXIT."""
import json
import os
import pathlib
import sys

args = sys.argv[1:]
call = {"args": args, "pythonpath": os.environ.get("PYTHONPATH"), "module": __file__}
if "--prev" in args:
    call["prev_text"] = pathlib.Path(args[args.index("--prev") + 1]).read_text()
with open(os.environ["STUB_LOG"], "a") as handle:
    handle.write(json.dumps(call) + "\\n")
if "--out" in args:
    pathlib.Path(args[args.index("--out") + 1]).write_text(json.dumps({"stub": args[0]}))
if args[0] == "pair":
    root = pathlib.Path(args[args.index("--out-dir") + 1])
    for side in ("new", "prev"):
        (root / side).mkdir(parents=True, exist_ok=True)
        (root / side / "plot-light.png").write_bytes(b"png")
sys.exit(int(os.environ.get("STUB_EXIT", "0")))
'''
BRANCH_RUNNER = """import os, sys
open(os.environ["STUB_LOG"], "a").write('{"args": ["BRANCH-CORE"]}\\n')
sys.exit(0)
"""
FAKE_GSUTIL = """#!/bin/sh
printf '%s\\n' "$*" >> "$GSUTIL_LOG"
case "$*" in
  *"cp "*"adapt/new-smoke.json"*) [ -n "$GSUTIL_FAIL_CP" ] && exit 1 ;;
  *"rm "*) [ -n "$GSUTIL_RM_MISSES" ] && exit 1 ;;
esac
exit 0
"""


def _workflow(filename: str) -> dict[str, Any]:
    return yaml.safe_load((WORKFLOWS_DIR / filename).read_text(encoding="utf-8"))


def _steps(filename: str) -> list[dict[str, Any]]:
    return [step for job in _workflow(filename)["jobs"].values() for step in job.get("steps", [])]


def _step(filename: str, name: str) -> dict[str, Any]:
    matches = [step for step in _steps(filename) if step.get("name") == name]
    assert len(matches) == 1, f"expected exactly one step named {name!r} in {filename}"
    return matches[0]


def _names(filename: str) -> list[str]:
    return [str(step.get("name")) for step in _steps(filename)]


def _env(**extra: str) -> dict[str, str]:
    """No user git config and no inherited GIT_* state."""
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


def _write(root: Path, files: dict[str, str]) -> None:
    for rel, text in files.items():
        (root / rel).parent.mkdir(parents=True, exist_ok=True)
        (root / rel).write_text(text, encoding="utf-8")


class Runner:
    """A workspace on the implementation branch, an origin/main, and the workflow ref holding the stub runner."""

    def __init__(self, tmp: Path, *, regeneration: bool) -> None:
        self.tmp = tmp
        seed = tmp / "seed"
        seed.mkdir()
        _git(seed, "init", "-q", "-b", "main")
        main_files = {"core/__init__.py": "", "core/smoke_run.py": STUB_RUNNER, SPEC_FILE: "# spec\n"}
        if regeneration:
            main_files[IMPL] = "PREDECESSOR\n"
        _write(seed, main_files)
        _git(seed, "add", "-A")
        _git(seed, "commit", "-q", "-m", "main")
        self.sha = _git(seed, "rev-parse", "HEAD")
        origin = tmp / "origin.git"
        subprocess.run(["git", "clone", "-q", "--bare", str(seed), str(origin)], check=True, env=_env())
        self.ws = tmp / "ws"
        subprocess.run(["git", "clone", "-q", str(origin), str(self.ws)], check=True, env=_env())
        _git(self.ws, "checkout", "-q", "-b", f"implementation/{SPEC}/{LIB}")
        _write(self.ws, {IMPL: "GENERATED\n", "core/smoke_run.py": BRANCH_RUNNER})
        _git(self.ws, "add", "-A")
        _git(self.ws, "commit", "-q", "-m", "feat: implement")
        python = self.ws / ".venv" / "bin" / "python"
        python.parent.mkdir(parents=True)
        python.write_text(f'#!/bin/sh\nexec "{sys.executable}" "$@"\n', encoding="utf-8")
        python.chmod(0o755)
        self.runner_temp = tmp / "runner"
        self.runner_temp.mkdir()
        self.log = tmp / "stub.jsonl"
        self.selfcheck = tmp / "anyplot-selfcheck.jsonl"

    @property
    def out(self) -> Path:
        return self.runner_temp / "adapt"

    def calls(self) -> list[dict[str, Any]]:
        if not self.log.exists():
            return []
        return [json.loads(line) for line in self.log.read_text(encoding="utf-8").splitlines()]

    def run(
        self, workflow: str, shell: list[str], *, sha: str | None = None, stub_exit: int = 0
    ) -> subprocess.CompletedProcess[str]:
        step = _step(workflow, SMOKE_STEP)
        script = str(step["run"])
        assert "${{" not in script
        script = script.replace("/tmp/anyplot-selfcheck.jsonl", str(self.selfcheck))
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


class TestWiring:
    def test_generate_runs_it_after_the_metadata_commit_and_before_the_png_processing(self) -> None:
        names = _names("impl-generate.yml")
        assert names.count(SMOKE_STEP) == 1
        index = names.index(SMOKE_STEP)
        assert names[index - 1] == "Create library metadata file"
        assert names[index + 1] == "Process plot images (light + dark)"
        assert index < names.index("Upload to GCS Staging")

    def test_repair_runs_it_after_the_repaired_image_and_before_the_upload(self) -> None:
        names = _names("impl-repair.yml")
        index = names.index(SMOKE_STEP)
        assert names[index - 1] == "Process repaired image"
        assert index < names.index("Upload repaired plot to GCS staging")

    @pytest.mark.parametrize(
        ("workflow", "condition"),
        [
            ("impl-generate.yml", "steps.inputs.outputs.language == 'python'"),
            ("impl-repair.yml", "success() && steps.lang.outputs.language == 'python'"),
        ],
    )
    def test_the_steps_are_record_only_and_python_only(self, workflow: str, condition: str) -> None:
        step = _step(workflow, SMOKE_STEP)
        assert step["id"] == "adapt_smoke"
        assert step["if"] == condition
        assert step["continue-on-error"] is True
        assert step["timeout-minutes"] == 20
        script = str(step["run"])
        assert "exit 1" not in script  # never a raw exit 1: the step records, it does not gate
        assert 'git archive "$GITHUB_SHA" core' in script  # the runner comes from the workflow's ref
        assert 'PYTHONPATH="$TOOLS" .venv/bin/python -P -m core.smoke_run' in script
        logical = script.replace("\\\n", " ").splitlines()
        invocations = [
            line
            for line in logical
            if ('"${RUN[@]}"' in line or "-m core.smoke_run" in line) and not line.strip().startswith("RUN=")
        ]
        assert invocations
        assert all(line.rstrip().endswith("|| true") for line in invocations), invocations

    def test_repair_runs_no_pair_and_no_predecessor(self) -> None:
        script = str(_step("impl-repair.yml", SMOKE_STEP)["run"])
        assert " pair " not in script and "origin/main" not in script and "prev" not in script

    def test_the_metadata_step_is_untouched(self) -> None:
        """Four tests read "Create library metadata file"; the smoke run lives in its own step (contract 9.2)."""
        assert "smoke_run" not in str(_step("impl-generate.yml", "Create library metadata file")["run"])


# --- the impl-generate step --------------------------------------------------------------------


@pytest.mark.parametrize("shell", SHELLS, ids=["bash-e", "pipefail"])
class TestGenerateStep:
    def test_a_regeneration_runs_new_pair_and_predecessor_from_the_workflow_ref(
        self, tmp_path: Path, shell: list[str]
    ) -> None:
        runner = Runner(tmp_path, regeneration=True)
        runner.selfcheck.write_text('{"attempt": 1}\n', encoding="utf-8")
        result = runner.run("impl-generate.yml", shell)
        assert result.returncode == 0, result.stdout + result.stderr
        calls = runner.calls()
        assert [call["args"][0] for call in calls] == ["run", "pair", "run"]
        tools = str(runner.runner_temp / "adapt-tools")
        assert all(call["pythonpath"] == tools for call in calls)
        assert all(call["module"] == f"{tools}/core/smoke_run.py" for call in calls)  # never the branch's core/
        out = str(runner.out)
        new, pair, prev = (call["args"] for call in calls)
        assert new == [
            "run",
            IMPL,
            "--spec",
            SPEC_FILE,
            "--spec-id",
            SPEC,
            "--library",
            LIB,
            "--out",
            f"{out}/new-smoke.json",
        ]
        assert pair[:5] == ["pair", "--new", IMPL, "--prev", f"{out}/prev-src/{LIB}.py"]
        assert pair[5:] == ["--library", LIB, "--out-dir", out, "--out", f"{out}/pair.json"]
        assert calls[1]["prev_text"] == "PREDECESSOR\n"  # origin/main's file, not the generated one
        assert prev == [
            "run",
            f"{out}/prev-src/{LIB}.py",
            "--spec",
            SPEC_FILE,
            "--spec-id",
            SPEC,
            "--library",
            LIB,
            "--skip-if-static-fails",
            "--out",
            f"{out}/prev-smoke.json",
        ]
        staged = sorted(str(path.relative_to(runner.out)) for path in runner.out.rglob("*") if path.is_file())
        assert staged == [
            "new-smoke.json",
            "new/plot-light.png",
            "pair.json",
            "prev-smoke.json",
            "prev/plot-light.png",
            "selfcheck.jsonl",
        ]
        assert (runner.out / "selfcheck.jsonl").read_text(encoding="utf-8") == '{"attempt": 1}\n'
        assert "::notice::adapt_smoke spec=bar-grouped lib=matplotlib staged=" in result.stdout

    def test_a_first_generation_runs_only_the_new_source(self, tmp_path: Path, shell: list[str]) -> None:
        runner = Runner(tmp_path, regeneration=False)
        result = runner.run("impl-generate.yml", shell)
        assert result.returncode == 0, result.stdout + result.stderr
        assert [call["args"][0] for call in runner.calls()] == ["run"]
        assert sorted(path.name for path in runner.out.iterdir()) == ["new-smoke.json"]  # no log, no prev-src

    @pytest.mark.parametrize("stub_exit", [1, 2])
    def test_a_failing_or_erroring_runner_never_fails_the_step(
        self, tmp_path: Path, shell: list[str], stub_exit: int
    ) -> None:
        runner = Runner(tmp_path, regeneration=True)
        result = runner.run("impl-generate.yml", shell, stub_exit=stub_exit)
        assert result.returncode == 0, result.stdout + result.stderr
        assert len(runner.calls()) == 3
        assert not (runner.out / "prev-src").exists()

    def test_without_the_workflow_ref_nothing_runs(self, tmp_path: Path, shell: list[str]) -> None:
        runner = Runner(tmp_path, regeneration=True)
        result = runner.run("impl-generate.yml", shell, sha="0" * 40)
        assert result.returncode == 0, result.stdout + result.stderr
        assert "::warning::adapt_smoke could not copy core/" in result.stdout
        assert runner.calls() == [] and not runner.out.exists()


# --- the impl-repair step ----------------------------------------------------------------------


@pytest.mark.parametrize("shell", SHELLS, ids=["bash-e", "pipefail"])
class TestRepairStep:
    def test_the_repaired_file_gets_one_run(self, tmp_path: Path, shell: list[str]) -> None:
        runner = Runner(tmp_path, regeneration=True)
        result = runner.run("impl-repair.yml", shell, stub_exit=1)
        assert result.returncode == 0, result.stdout + result.stderr
        (call,) = runner.calls()
        out = str(runner.out)
        assert call["args"] == [
            "run",
            IMPL,
            "--spec",
            SPEC_FILE,
            "--spec-id",
            SPEC,
            "--library",
            LIB,
            "--out",
            f"{out}/new-smoke.json",
        ]
        assert call["module"] == f"{runner.runner_temp}/adapt-tools/core/smoke_run.py"
        assert sorted(path.name for path in runner.out.iterdir()) == ["new-smoke.json"]

    def test_without_the_workflow_ref_nothing_runs(self, tmp_path: Path, shell: list[str]) -> None:
        runner = Runner(tmp_path, regeneration=True)
        result = runner.run("impl-repair.yml", shell, sha="0" * 40)
        assert result.returncode == 0 and runner.calls() == []


# --- staging -----------------------------------------------------------------------------------


class Staging:
    """An implementation directory with both theme renders, `$RUNNER_TEMP/adapt`, and a stub gsutil."""

    def __init__(self, tmp: Path, language: str = "python") -> None:
        self.ws = tmp / "ws"
        self.impl_dir = self.ws / "plots" / SPEC / "implementations" / language
        self.impl_dir.mkdir(parents=True)
        for theme in ("light", "dark"):
            (self.impl_dir / f"plot-{theme}.png").write_bytes(b"png")
        self.runner_temp = tmp / "runner"
        self.adapt = self.runner_temp / "adapt"
        self.adapt.mkdir(parents=True)
        bin_dir = tmp / "bin"
        bin_dir.mkdir()
        (bin_dir / "gsutil").write_text(FAKE_GSUTIL, encoding="utf-8")
        (bin_dir / "gsutil").chmod(0o755)
        self.path = f"{bin_dir}{os.pathsep}{os.environ['PATH']}"
        self.log = tmp / "gsutil.log"
        self.output = tmp / "github_output"
        self.language = language
        self.staging = f"gs://anyplot-images/staging/{SPEC}/{language}/{LIB}"

    def run(self, workflow: str, step: str, shell: list[str], **extra: str) -> list[str]:
        script = str(_step(workflow, step)["run"])
        assert "${{" not in script
        result = subprocess.run(
            [*shell, script],
            cwd=self.ws,
            env=_env(
                PATH=self.path,
                RUNNER_TEMP=str(self.runner_temp),
                GSUTIL_LOG=str(self.log),
                GITHUB_OUTPUT=str(self.output),
                SPEC_ID=SPEC,
                LIBRARY=LIB,
                LANGUAGE=self.language,
                **extra,
            ),
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, result.stdout + result.stderr
        self.stdout = result.stdout
        return self.log.read_text(encoding="utf-8").splitlines() if self.log.exists() else []


@pytest.mark.parametrize("shell", SHELLS, ids=["bash-e", "pipefail"])
class TestGenerateUpload:
    STEP = "Upload to GCS Staging"

    def test_stale_artifacts_go_first_then_this_runs_are_staged_privately(
        self, tmp_path: Path, shell: list[str]
    ) -> None:
        staging = Staging(tmp_path)
        (staging.adapt / "new-smoke.json").write_text("{}", encoding="utf-8")
        (staging.adapt / "prev").mkdir()
        (staging.adapt / "prev" / "plot-light.png").write_bytes(b"png")
        calls = staging.run("impl-generate.yml", self.STEP, shell)
        assert calls[0] == f"-m rm -r {staging.staging}/adapt"
        (upload,) = [call for call in calls if call.endswith(f"{staging.staging}/adapt/")]
        assert upload.startswith("-m -h Cache-Control:no-store cp -r ")
        assert f"{staging.adapt}/new-smoke.json" in upload and f"{staging.adapt}/prev" in upload
        assert not [call for call in calls if "acl" in call and "adapt" in call]  # never public
        assert any("plot-light" in call for call in calls)  # the renders still go up

    def test_a_cut_off_step_never_stages_the_predecessor_source(self, tmp_path: Path, shell: list[str]) -> None:
        staging = Staging(tmp_path)
        (staging.adapt / "new-smoke.json").write_text("{}", encoding="utf-8")
        (staging.adapt / "prev-src").mkdir()
        (staging.adapt / "prev-src" / f"{LIB}.py").write_text("PREDECESSOR\n", encoding="utf-8")
        calls = staging.run("impl-generate.yml", self.STEP, shell)
        assert not [call for call in calls if "prev-src" in call]
        assert not (staging.adapt / "prev-src").exists()

    def test_without_artifacts_only_the_stale_ones_go(self, tmp_path: Path, shell: list[str]) -> None:
        staging = Staging(tmp_path)
        calls = staging.run("impl-generate.yml", self.STEP, shell, GSUTIL_RM_MISSES="1")
        assert calls[0] == f"-m rm -r {staging.staging}/adapt"
        assert not [call for call in calls if "adapt/" in call]

    def test_a_failed_upload_warns_and_the_step_goes_on(self, tmp_path: Path, shell: list[str]) -> None:
        staging = Staging(tmp_path)
        (staging.adapt / "new-smoke.json").write_text("{}", encoding="utf-8")
        calls = staging.run("impl-generate.yml", self.STEP, shell, GSUTIL_FAIL_CP="1")
        assert "::warning::adapt artifacts not staged; impl-review records them as missing" in staging.stdout
        assert any("plot-light" in call for call in calls)


@pytest.mark.parametrize("shell", SHELLS, ids=["bash-e", "pipefail"])
class TestRepairUpload:
    STEP = "Upload repaired plot to GCS staging"

    def test_the_repaired_files_record_replaces_the_staged_one(self, tmp_path: Path, shell: list[str]) -> None:
        staging = Staging(tmp_path)
        (staging.adapt / "new-smoke.json").write_text("{}", encoding="utf-8")
        calls = staging.run("impl-repair.yml", self.STEP, shell)
        assert (
            f"-h Cache-Control:no-store cp {staging.adapt}/new-smoke.json {staging.staging}/adapt/new-smoke.json"
            in calls
        )
        assert not [call for call in calls if call.startswith("rm ")]

    def test_without_a_record_the_stale_one_goes(self, tmp_path: Path, shell: list[str]) -> None:
        staging = Staging(tmp_path)
        calls = staging.run("impl-repair.yml", self.STEP, shell, GSUTIL_RM_MISSES="1")
        assert calls[-1] == f"rm {staging.staging}/adapt/new-smoke.json"

    def test_a_failed_upload_removes_the_stale_record(self, tmp_path: Path, shell: list[str]) -> None:
        staging = Staging(tmp_path)
        (staging.adapt / "new-smoke.json").write_text("{}", encoding="utf-8")
        calls = staging.run("impl-repair.yml", self.STEP, shell, GSUTIL_FAIL_CP="1")
        assert calls[-1] == f"rm {staging.staging}/adapt/new-smoke.json"
        assert "::warning::adapt/new-smoke.json not staged" in staging.stdout

    def test_other_languages_touch_no_adapt_record(self, tmp_path: Path, shell: list[str]) -> None:
        staging = Staging(tmp_path, language="r")
        calls = staging.run("impl-repair.yml", self.STEP, shell)
        assert calls and not [call for call in calls if "adapt" in call]
