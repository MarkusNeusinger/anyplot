"""The pipeline acts only on its own pull requests, in every workflow that takes one.

`automation/scripts/pr_guard.py` decides which pull requests those are (its
own tests: `tests/unit/automation/scripts/test_pr_guard.py`). Here the steps
that stage and run it are run for real, under `bash -e` (what Actions runs) and
`bash -eo pipefail`, with a fake `gh` and a `git` that logs its calls:

- the staging step is one text everywhere and takes the guard and the library
  list from the workflow's own commit, never from the working tree;
- a refused pull request leaves no outputs, fetches nothing, gets no label,
  comment, merge or dispatch, and leaves one error line and one summary line
  with a fixed reason code;
- the listings (the watchdog's, impl-generate's existing-PR lookup) skip a pull
  request that is not the pipeline's own;
- impl-merge merges only the head it checked, or GitHub's merge of main into it.

The last class scans every workflow, so a new one that takes a pull request,
or a new listing, cannot leave the guard out without a test failing.
"""

from __future__ import annotations

import ast
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest
import yaml

from automation.scripts import pr_guard, regen_pick_pairs
from tests.unit.workflows.pr_guard_support import (
    CONSTANTS,
    GUARD,
    HEAD_SHA,
    LIBRARIES,
    commit_guard_sources,
    own_fields,
    own_pr,
    stage_guard,
)


REPO_ROOT = Path(__file__).resolve().parents[3]
WORKFLOWS = REPO_ROOT / ".github" / "workflows"
STAGE = "Stage the pull request guard"
CHECK_STEP = "Check the pull request is the pipeline's own"
REPO = "owner/repo"
BRANCH = "implementation/spec-a/plotly"
REAL_GIT = shutil.which("git") or "git"
PIPEFAIL = ("bash", "-eo", "pipefail", "-c")
BASH_E = ("bash", "-e", "-c")
SHELLS = pytest.mark.parametrize("shell", [BASH_E, PIPEFAIL], ids=["bash-e", "pipefail"])
EXPRESSION = re.compile(r"\$\{\{\s*(.+?)\s*\}\}")

# Logs every call as one JSON line. `pr view` prints $GH_PR_JSON (a state read
# prints $GH_STATE), `pr list` $GH_LIST_JSON, `api` $GH_API_JSON, `issue list`
# $GH_ISSUES_JSON and `issue view` $GH_ISSUE_TITLE; a `pr create` prints a new
# pull request's URL. GH_FAIL=1 fails every call.
FAKE_GH = """#!/usr/bin/env python3
import json, os, sys
args = sys.argv[1:]
with open(os.environ["GH_LOG"], "a", encoding="utf-8") as f:
    f.write(json.dumps(args) + "\\n")
if os.environ.get("GH_FAIL") == "1":
    print("HTTP 502", file=sys.stderr)
    sys.exit(1)
key = " ".join(args[:2])
fields = args[args.index("--json") + 1] if "--json" in args else ""

def asked(entry):
    # As gh does: only the fields the call asked for, so a list that drops one shows.
    wanted = fields.split(",")
    return {k: v for k, v in entry.items() if k in wanted} if isinstance(entry, dict) else entry

if key == "pr view":
    if fields == "state":
        print(os.environ.get("GH_STATE", "OPEN"))
    elif "-q" in args and args[args.index("-q") + 1] == ".labels[].name":
        for label in json.loads(os.environ.get("GH_PR_JSON", "{}")).get("labels", []):
            print(label["name"])
    else:
        print(json.dumps(asked(json.loads(os.environ.get("GH_PR_JSON", "{}")))))
elif key == "pr list":
    listed = json.loads(os.environ.get("GH_LIST_JSON", "[]"))
    print(json.dumps([asked(entry) for entry in listed] if fields else listed))
elif key == "issue list":
    print(os.environ.get("GH_ISSUES_JSON", "[]"))
elif key == "issue view":
    print(os.environ.get("GH_ISSUE_TITLE", ""))
elif key == "pr create":
    print("https://github.com/owner/repo/pull/124")
elif key == "run list":
    print(os.environ.get("GH_RUNS_JSON", "[]"))
elif args[:1] == ["api"]:
    joined = " ".join(args)
    if "/actions/" in joined:
        sys.exit(1)
    if "/contents/" in joined:
        # A file of this repository at a ref, from $GH_CONTENTS_DIR.
        path = joined.split("/contents/", 1)[1].split("?", 1)[0].split(" ", 1)[0]
        source = os.path.join(os.environ.get("GH_CONTENTS_DIR", "/nonexistent"), path)
        if not os.path.isfile(source):
            print("HTTP 404", file=sys.stderr)
            sys.exit(1)
        sys.stdout.write(open(source, encoding="utf-8").read())
        sys.exit(0)
    print(os.environ.get("GH_API_JSON", "[]"))
"""
# Logs its arguments, then runs the real git.
FAKE_GIT = f"""#!/bin/sh
printf '%s\\n' "$*" >> "$SHIM_GIT_LOG"
exec {REAL_GIT} "$@"
"""
# The runner's python3 in the jobs that stage the guard is the image's own: it
# sees none of this repository's packages. The interpreter the virtual
# environment was made from is such a one (the project is installed into the
# environment, not into it), started without user site-packages and without
# PYTHON* variables. Its working directory is on its path, as on the runner.
BASE_PYTHON = getattr(sys, "_base_executable", None) or sys.executable
FAKE_PYTHON = f"""#!/bin/sh
exec {BASE_PYTHON} -s -E "$@"
"""
WRITES = {
    "pr edit",
    "pr comment",
    "pr close",
    "pr merge",
    "pr update-branch",
    "pr create",
    "pr ready",
    "pr review",
    "label create",
    "issue edit",
    "issue comment",
    "workflow run",
}


def _workflow(filename: str) -> dict[Any, Any]:
    return yaml.safe_load((WORKFLOWS / filename).read_text(encoding="utf-8"))


def _jobs(filename: str) -> dict[str, dict[str, Any]]:
    return _workflow(filename)["jobs"]


def _step(filename: str, name: str, job: str | None = None) -> dict[str, Any]:
    jobs = _jobs(filename)
    steps = [s for j, body in jobs.items() if job in (None, j) for s in body.get("steps", [])]
    (step,) = [s for s in steps if s.get("name") == name]
    return step


def _render(script: str, context: dict[str, str] | None = None) -> str:
    context = {"github.repository": REPO, "github.run_id": "1", **(context or {})}

    def substitute(match: re.Match[str]) -> str:
        assert match.group(1) in context, f"unexpected expression: {match.group(1)}"
        return context[match.group(1)]

    return EXPRESSION.sub(substitute, script)


def _gh_calls(log: Path) -> list[list[str]]:
    return [json.loads(line) for line in log.read_text(encoding="utf-8").splitlines()] if log.exists() else []


def _writes(calls: list[list[str]]) -> list[list[str]]:
    return [c for c in calls if " ".join(c[:2]) in WRITES]


class Run:
    """One step run: its result, `gh` calls, `git` calls, outputs and summary."""

    def __init__(self, tmp: Path, result: subprocess.CompletedProcess[str]) -> None:
        self.result = result
        self.rc = result.returncode
        self.log = result.stdout + result.stderr
        self.gh = _gh_calls(tmp / "gh.log")
        git_log = tmp / "git.log"
        self.git = git_log.read_text(encoding="utf-8").splitlines() if git_log.exists() else []
        out = tmp / "github_output"
        self.outputs = (
            dict(line.split("=", 1) for line in out.read_text(encoding="utf-8").splitlines() if "=" in line)
            if out.exists()
            else {}
        )
        summary = tmp / "step_summary"
        self.summary = summary.read_text(encoding="utf-8") if summary.exists() else ""

    def errors(self) -> list[str]:
        return [line for line in self.result.stdout.splitlines() if line.startswith("::error::")]


def _run(
    script: str,
    tmp: Path,
    *,
    cwd: Path | None = None,
    shell=PIPEFAIL,
    stage: bool = True,
    fake_gh: str = FAKE_GH,
    **env: str,
) -> Run:
    """Run a step script as Actions does, behind a staged guard, with fake `gh`, `git`, `python3` and `sleep`."""
    assert "${{" not in script
    bin_dir = tmp / "bin"
    bin_dir.mkdir(exist_ok=True)
    fakes = (("gh", fake_gh), ("git", FAKE_GIT), ("python3", FAKE_PYTHON), ("sleep", "#!/bin/sh\nexit 0\n"))
    for name, body in fakes:
        (bin_dir / name).write_text(body, encoding="utf-8")
        (bin_dir / name).chmod(0o755)
    runner = tmp / "runner"
    runner.mkdir(exist_ok=True)
    if stage:
        stage_guard(runner)
    for name in ("gh.log", "git.log", "github_output", "step_summary"):
        (tmp / name).unlink(missing_ok=True)
    base = {k: v for k, v in os.environ.items() if not k.startswith(("GIT_", "GH_", "GITHUB_", "RUNNER_"))}
    result = subprocess.run(
        [*shell, script],
        cwd=cwd or tmp,
        env={
            **base,
            "PATH": f"{bin_dir}{os.pathsep}{os.environ['PATH']}",
            "GH_LOG": str(tmp / "gh.log"),
            "SHIM_GIT_LOG": str(tmp / "git.log"),
            "GH_TOKEN": "unused",
            "RUNNER_TEMP": str(runner),
            "GITHUB_OUTPUT": str(tmp / "github_output"),
            "GITHUB_STEP_SUMMARY": str(tmp / "step_summary"),
            **env,
        },
        capture_output=True,
        text=True,
    )
    return Run(tmp, result)


def _git_env(tmp: Path) -> dict[str, str]:
    config = tmp / "gitconfig"
    config.touch()
    env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
    env.update(
        GIT_CONFIG_GLOBAL=str(config),
        GIT_CONFIG_NOSYSTEM="1",
        GIT_AUTHOR_NAME="t",
        GIT_AUTHOR_EMAIL="t@example.invalid",
        GIT_COMMITTER_NAME="t",
        GIT_COMMITTER_EMAIL="t@example.invalid",
    )
    return env


def _git(cwd: Path, env: dict[str, str], *args: str) -> str:
    return subprocess.run(
        [REAL_GIT, *args], cwd=cwd, env=env, check=True, capture_output=True, text=True
    ).stdout.strip()


# Pull requests that are not the pipeline's own, each with the code the guard names.
FOREIGN = [
    pytest.param(
        {"isCrossRepository": True, "headRepositoryOwner": {"login": "elsewhere"}}, "cross_repository", id="fork"
    ),
    pytest.param({"isCrossRepository": None}, "missing_field", id="null-cross-repository"),
    pytest.param({"headRepositoryOwner": None}, "missing_field", id="no-owner"),
    pytest.param({"headRepository": {"name": "other"}}, "cross_repository", id="other-repository"),
    pytest.param({"author": {"login": "someone"}}, "author_mismatch", id="other-author"),
    pytest.param({"baseRefName": "release"}, "base_mismatch", id="other-base"),
    pytest.param({"headRefName": f"{BRANCH}/extra"}, "branch_shape", id="extra-segment"),
    pytest.param({"headRefName": "implementation/Spec-A/plotly"}, "branch_shape", id="uppercase"),
    pytest.param({"headRefName": "implementation/../plotly"}, "branch_shape", id="traversal"),
    pytest.param({"headRefName": "implementation/$(x)/plotly"}, "branch_shape", id="shell"),
    pytest.param({"headRefName": "implementation/spec-a/notalib"}, "unknown_library", id="unknown-library"),
    pytest.param({"number": 8}, "number_mismatch", id="other-number"),
]


def _foreign(change: dict[str, Any], number: int = 7) -> dict[str, Any]:
    return {**own_pr(number, BRANCH, body="**Parent Issue:** #42\n**Model:** haiku"), **change}


# --- the staging step ------------------------------------------------------------------------


def _staging_steps() -> list[tuple[str, str, dict[str, Any]]]:
    return [
        (path.name, job, step)
        for path in sorted(WORKFLOWS.glob("*.yml"))
        for job, body in _jobs(path.name).items()
        for step in body.get("steps", [])
        if step.get("name") == STAGE
    ]


class TestStagingStep:
    def test_one_text_everywhere(self):
        steps = _staging_steps()
        assert len(steps) >= 6
        texts = {step["run"] for _, _, step in steps}
        assert len(texts) == 1, [f"{w}:{j}" for w, j, s in steps]

    # The two spellings of "main, never the pull request's merge commit" for a
    # job a pull-request event starts: one decides by the event, one is fixed.
    PULL_REQUEST_EVENT_REFS = (
        "${{ github.event_name == 'pull_request' && 'origin/main' || github.sha }}",
        "origin/${{ github.event.repository.default_branch }}",
    )

    def test_the_ref_is_the_workflows_own_commit_or_main(self):
        """On a pull-request event the workflow's commit is the pull request's merge commit."""
        for filename, job, step in _staging_steps():
            on = _workflow(filename).get("on") or _workflow(filename).get(True)
            ref = step["env"]["GUARD_REF"]
            if "pull_request" in on:
                assert ref in self.PULL_REQUEST_EVENT_REFS, (filename, job, ref)
            else:
                assert ref == "${{ github.sha }}", (filename, job)

    @pytest.mark.parametrize(
        ("event", "ref"), [("pull_request", "origin/main"), ("workflow_dispatch", "<sha>"), ("schedule", "<sha>")]
    )
    def test_the_event_ref_names_main_on_the_pull_request_event(self, event, ref):
        """The `&& ||` expression, evaluated: swapping its branches would stage from the merge commit."""
        expression = self.PULL_REQUEST_EVENT_REFS[0]
        match = re.fullmatch(
            r"\$\{\{ github\.event_name == 'pull_request' && '([^']+)' \|\| github\.sha \}\}", expression
        )
        assert match is not None
        assert (match.group(1) if event == "pull_request" else "<sha>") == ref

    def test_the_library_list_comes_from_the_registry(self):
        (text,) = {step["run"] for _, _, step in _staging_steps()}
        assert "from core.constants import SUPPORTED_LIBRARIES" in text
        for library in LIBRARIES.split():
            assert library not in text

    @staticmethod
    def _stage(tmp_path: Path, shell, constants: str | None = None) -> tuple[Run, Path]:
        """Stage from a commit whose constants are `constants` (the repository's when None)."""
        repo = tmp_path / "repo"
        repo.mkdir()
        env = _git_env(tmp_path)
        _git(repo, env, "init", "-q", "-b", "main")
        sha = commit_guard_sources(repo, env)
        if constants is not None:
            (repo / "core" / "constants.py").write_text(constants, encoding="utf-8")
            _git(repo, env, "commit", "-q", "-am", "constants")
            sha = _git(repo, env, "rev-parse", "HEAD")
        # The working tree holds something else; the staged copies must not be it.
        (repo / "automation" / "scripts" / "pr_guard.py").write_text("raise SystemExit(0)\n", encoding="utf-8")
        (repo / "core" / "constants.py").write_text('SUPPORTED_LIBRARIES = frozenset(["tree"])\n', encoding="utf-8")
        run = _run(_step("impl-review.yml", STAGE)["run"], tmp_path, cwd=repo, shell=shell, stage=False, GUARD_REF=sha)
        return run, tmp_path / "runner" / "pr-guard"

    @SHELLS
    def test_stages_the_committed_guard_never_the_working_tree(self, tmp_path, shell):
        run, staged = self._stage(tmp_path, shell)
        assert run.rc == 0, run.log
        assert (staged / "pr_guard.py").read_bytes() == GUARD.read_bytes()
        assert (staged / "libraries").read_text(encoding="utf-8").split() == LIBRARIES.split()

    @SHELLS
    def test_the_library_list_comes_from_the_staged_constants(self, tmp_path, shell):
        """A list the repository's own package does not hold: only the staged copy can have given it."""
        run, staged = self._stage(tmp_path, shell, 'SUPPORTED_LIBRARIES = frozenset(["zeta", "alpha"])\n')
        assert run.rc == 0, run.log
        assert (staged / "libraries").read_text(encoding="utf-8").split() == ["alpha", "zeta"]

    @SHELLS
    @pytest.mark.parametrize(
        "constants",
        [
            "import anyplot_package_nobody_installed\nSUPPORTED_LIBRARIES = frozenset(['altair'])\n",
            "from core import palette\nSUPPORTED_LIBRARIES = frozenset(['altair'])\n",
        ],
        ids=["third-party-import", "sibling-import"],
    )
    def test_constants_that_need_more_than_themselves_stop_the_job(self, tmp_path, shell, constants):
        """On the runner, the staged file stands alone: an import it cannot satisfy is a refusal, loudly."""
        run, staged = self._stage(tmp_path, shell, constants)
        assert run.rc == 1, run.log
        assert len(run.errors()) == 1 and run.errors()[0].startswith("::error::guard_failed")
        assert not (staged / "libraries").exists()

    def test_the_staging_interpreter_cannot_see_the_repositorys_packages(self, tmp_path):
        """The check of the tests above: the runner-like python3 finds no `core` of its own."""
        run = _run('cd "$RUNNER_TEMP" && python3 -c "import core"', tmp_path, stage=False)
        assert run.rc != 0 and "ModuleNotFoundError" in run.log

    @SHELLS
    def test_a_ref_without_the_guard_stops_the_job(self, tmp_path, shell):
        repo = tmp_path / "repo"
        repo.mkdir()
        env = _git_env(tmp_path)
        _git(repo, env, "init", "-q", "-b", "main")
        (repo / "x").write_text("x\n", encoding="utf-8")
        _git(repo, env, "add", "x")
        _git(repo, env, "commit", "-q", "-m", "no guard")
        sha = _git(repo, env, "rev-parse", "HEAD")
        run = _run(_step("impl-review.yml", STAGE)["run"], tmp_path, cwd=repo, shell=shell, stage=False, GUARD_REF=sha)
        assert run.rc == 1
        assert run.errors() == [run.errors()[0]] and run.errors()[0].startswith("::error::guard_failed")
        assert "guard_failed" in run.summary
        assert not (tmp_path / "runner" / "pr-guard" / "pr_guard.py").exists()


# --- impl-review: "Extract PR info" ------------------------------------------------------------


@pytest.fixture
def review_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    repo.mkdir()
    env = _git_env(tmp_path)
    _git(repo, env, "init", "-q", "-b", "main")
    commit_guard_sources(repo, env)
    _git(repo, env, "update-ref", "refs/remotes/origin/main", "HEAD")
    return repo


def _extract(tmp: Path, cwd: Path, pr: dict[str, Any] | None, *, shell=PIPEFAIL, number: str = "7", **env: str) -> Run:
    script = _step("impl-review.yml", "Extract PR info")["run"]
    return _run(
        script,
        tmp,
        cwd=cwd,
        shell=shell,
        REPOSITORY=REPO,
        PR_NUMBER=number,
        GH_PR_JSON=json.dumps(pr),
        MODEL_INPUT="",
        MODEL_PAYLOAD="",
        REVIEW_MODEL_INPUT="",
        REVIEW_MODEL_PAYLOAD="",
        **env,
    )


def _assert_refused(run: Run, code: str, number: str = "7", outputs: dict[str, str] | None = None) -> None:
    """No outputs (but `outputs`), no writes, one error line and one summary line with the fixed code."""
    assert run.rc != 0, run.log
    assert run.outputs == (outputs or {})
    errors = run.errors()
    assert len(errors) == 1, run.log
    assert errors[0].startswith(f"::error::PR #{number} refused ({code}): not one of the pipeline's own pull requests")
    assert run.summary.count("refused") == 1 and f"PR #{number} refused: `{code}`" in run.summary
    assert _writes(run.gh) == []


def _code_only(script: str) -> str:
    return "\n".join(line for line in script.splitlines() if not line.lstrip().startswith("#"))


class TestImplReview:
    @SHELLS
    @pytest.mark.parametrize(("change", "code"), FOREIGN)
    def test_a_refused_pull_request_leaves_nothing_and_fetches_nothing(
        self, tmp_path, review_repo, shell, change, code
    ):
        run = _extract(tmp_path, review_repo, _foreign(change), shell=shell)
        _assert_refused(run, code)
        assert [c[:2] for c in run.gh] == [["pr", "view"]]
        assert run.git == []  # no fetch, no routing, nothing read from the pull request
        # Nothing the pull request carries reaches the log.
        assert "$(x)" not in run.log and "Parent Issue" not in run.log and "haiku" not in run.log

    @pytest.mark.parametrize("number", ["", "0", "7 ", "#7", "7;true", "https://github.com/x/y/pull/7", "1" * 11])
    def test_a_bad_number_is_refused_before_gh_is_asked(self, tmp_path, review_repo, number):
        run = _extract(tmp_path, review_repo, own_pr(7, BRANCH), number=number)
        assert run.rc != 0 and run.outputs == {} and run.gh == [] and run.git == []
        assert len(run.errors()) == 1 and "(bad_number)" in run.errors()[0]

    def test_an_unreadable_pull_request_is_refused(self, tmp_path, review_repo):
        run = _extract(tmp_path, review_repo, own_pr(7, BRANCH), GH_FAIL="1")
        _assert_refused(run, "pr_unreadable")
        assert len(run.gh) == 3 and run.git == []

    def test_a_guard_that_does_not_answer_refuses(self, tmp_path, review_repo):
        (tmp_path / "runner").mkdir()
        staged = stage_guard(tmp_path / "runner")
        (staged / "pr_guard.py").write_text("raise SystemExit(3)\n", encoding="utf-8")
        run = _extract(tmp_path, review_repo, own_pr(7, BRANCH), stage=False)
        _assert_refused(run, "guard_failed")

    @SHELLS
    def test_the_pipelines_own_pull_request_passes(self, tmp_path, review_repo, shell):
        run = _extract(tmp_path, review_repo, own_pr(7, BRANCH, body="**Parent Issue:** #42"), shell=shell)
        assert run.rc == 0, run.log
        assert run.errors() == []
        assert {k: run.outputs[k] for k in ("pr_number", "specification_id", "library", "branch", "head_sha")} == {
            "pr_number": "7",
            "specification_id": "spec-a",
            "library": "plotly",
            "branch": BRANCH,
            "head_sha": HEAD_SHA,
        }
        assert run.outputs["issue_number"] == "42"

    def test_the_check_comes_before_anything_the_pull_request_carries_is_used(self):
        script = _code_only(_step("impl-review.yml", "Extract PR info")["run"])
        check = script.index('"$G/pr_guard.py" check')
        for use in ("git ", "GITHUB_OUTPUT", "BODY=", "HEAD_REF=", "SPEC_ID=", "LIBRARY=", "grep "):
            assert check < script.index(use), use
        assert "cut -d" not in script

    def test_the_checkout_takes_the_checked_head(self):
        step = _step("impl-review.yml", "Checkout PR code")
        assert step["env"]["HEAD_SHA"] == "${{ steps.pr.outputs.head_sha }}"
        assert 'git fetch origin "$HEAD_SHA"' in step["run"] and 'git checkout "$HEAD_SHA"' in step["run"]

    def test_nothing_after_a_refusal_writes_to_the_pull_request(self):
        """A refusal fails the step; only `always()` / `failure()` steps run after it."""
        for step in _jobs("impl-review.yml")["review"]["steps"]:
            condition = str(step.get("if", ""))
            if "always()" in condition:
                assert "steps.pr.outputs.specification_id != ''" in condition, step["name"]
            if "failure()" in condition:
                # Needs a review that ran, which a refused pull request never reaches.
                assert "steps.review.conclusion == 'success'" in condition, step["name"]


# --- impl-repair -------------------------------------------------------------------------------


class TestImplRepair:
    REFUSED = {"refused": "true"}

    def _check(self, tmp: Path, pr: dict[str, Any], *, shell=PIPEFAIL, **env: str) -> Run:
        values = {
            "REPOSITORY": REPO,
            "PR_NUMBER": "7",
            "SPEC_ID_INPUT": "spec-a",
            "LIBRARY_INPUT": "plotly",
            "ATTEMPT_INPUT": "2",
        }
        return _run(
            _step("impl-repair.yml", CHECK_STEP)["run"], tmp, shell=shell, GH_PR_JSON=json.dumps(pr), **values | env
        )

    @SHELLS
    @pytest.mark.parametrize(("change", "code"), FOREIGN)
    def test_a_refused_pull_request_is_never_fetched(self, tmp_path, shell, change, code):
        run = self._check(tmp_path, _foreign(change), shell=shell)
        # A decided refusal says so, which keeps the failure handler off the pull request.
        _assert_refused(run, code, outputs=self.REFUSED)
        assert run.git == []

    @pytest.mark.parametrize(("spec", "library"), [("spec-b", "plotly"), ("spec-a", "altair")])
    def test_inputs_that_differ_from_the_branch_are_refused(self, tmp_path, spec, library):
        run = self._check(tmp_path, own_pr(7, BRANCH), SPEC_ID_INPUT=spec, LIBRARY_INPUT=library)
        _assert_refused(run, "input_mismatch", outputs=self.REFUSED)

    @pytest.mark.parametrize("attempt", ["", "0", "10", "2;x", "a"])
    def test_an_attempt_that_is_no_small_number_is_refused(self, tmp_path, attempt):
        run = self._check(tmp_path, own_pr(7, BRANCH), ATTEMPT_INPUT=attempt)
        _assert_refused(run, "bad_input", outputs=self.REFUSED)
        assert run.gh == []

    def test_an_unreadable_pull_request_is_no_decided_refusal(self, tmp_path):
        """The failure handler checks it again itself; one of the pipeline's own then gets its retry."""
        _assert_refused(self._check(tmp_path, own_pr(7, BRANCH), GH_FAIL="1"), "pr_unreadable")

    @SHELLS
    def test_the_pipelines_own_pull_request_passes(self, tmp_path, shell):
        run = self._check(tmp_path, own_pr(7, BRANCH), shell=shell)
        assert run.rc == 0, run.log
        assert run.outputs == {"allowed": "true", "branch": BRANCH, "head_sha": HEAD_SHA}

    def test_the_checkout_uses_the_checked_branch_and_follows_the_check(self):
        names = [s.get("name") for s in _jobs("impl-repair.yml")["repair"]["steps"]]
        assert names.index(STAGE) < names.index(CHECK_STEP) < names.index("Checkout PR branch")
        checkout = _step("impl-repair.yml", "Checkout PR branch")
        assert checkout["env"]["BRANCH"] == "${{ steps.guard.outputs.branch }}"
        assert "gh " not in checkout["run"]

    def test_the_failure_handler_stays_off_a_refused_pull_request(self):
        handler = _step("impl-repair.yml", "Handle repair failure")
        assert handler["if"] == "failure() && steps.guard.outputs.refused != 'true'"
        assert handler["env"]["GUARD_ALLOWED"] == "${{ steps.guard.outputs.allowed }}"
        assert handler["env"]["GUARD_REF"] == "${{ github.sha }}"

    def _handler(self, tmp: Path, pr: dict[str, Any], *, stage: bool = True, allowed: str = "", **env: str) -> Run:
        """ "Handle repair failure" after a crash with no gate and no stop, its retry budget unspent."""
        values = {
            "GUARD_ALLOWED": allowed,
            "GUARD_REF": "a" * 40,
            "PR_NUM": "7",
            "SPEC_ID": "spec-a",
            "LIBRARY": "plotly",
            "ATTEMPT": "2",
            "MODEL": "sonnet",
            "REPOSITORY": REPO,
            "RUN_ID": "1",
            "CLAUDE_STOPPED": "false",
            "GATE": "",
            "RENDER_HASH_OUTCOME": "",
            # The retry-marker read: no earlier marker comment.
            "GH_API_JSON": "0",
        }
        script = _step("impl-repair.yml", "Handle repair failure")["run"].replace("/tmp/", f"{tmp}/")
        return _run(script, tmp, stage=stage, GH_PR_JSON=json.dumps(pr), **values | env)

    @staticmethod
    def _retried(run: Run) -> bool:
        return [c[:3] for c in run.gh if c[:2] == ["workflow", "run"]] == [["workflow", "run", "impl-repair.yml"]]

    @SHELLS
    def test_a_run_that_failed_before_the_check_still_retries_the_pipelines_own(self, tmp_path, shell):
        run = self._handler(tmp_path, own_pr(7, BRANCH), shell=shell)
        assert run.rc == 0, run.log
        assert self._retried(run)
        assert ["pr", "edit", "7", "--add-label", "ai-rejected"] in run.gh

    def test_a_run_that_never_staged_the_guard_stages_it_from_its_own_commit(self, tmp_path):
        """The credentials or the checkout failed: the handler fetches the guard at GUARD_REF itself."""
        contents = tmp_path / "contents"
        for source, rel in ((GUARD, "automation/scripts/pr_guard.py"), (CONSTANTS, "core/constants.py")):
            (contents / rel).parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, contents / rel)
        run = self._handler(tmp_path, own_pr(7, BRANCH), stage=False, GH_CONTENTS_DIR=str(contents))
        assert run.rc == 0, run.log
        fetched = [c for c in run.gh if c[:1] == ["api"] and "/contents/" in " ".join(c)]
        assert len(fetched) == 2 and all(f"?ref={'a' * 40}" in " ".join(c) for c in fetched)
        assert self._retried(run)

    @pytest.mark.parametrize(("change", "code"), FOREIGN)
    def test_a_pull_request_the_handler_cannot_pass_gets_nothing(self, tmp_path, change, code):
        run = self._handler(tmp_path, _foreign(change))
        assert run.rc == 0, run.log
        assert _writes(run.gh) == []
        assert "could not be checked now" in run.log

    def test_a_guard_that_cannot_be_staged_gets_nothing(self, tmp_path):
        run = self._handler(tmp_path, own_pr(7, BRANCH), stage=False, GH_CONTENTS_DIR=str(tmp_path / "none"))
        assert run.rc == 0 and _writes(run.gh) == []

    def test_an_unreadable_pull_request_gets_nothing(self, tmp_path):
        run = self._handler(tmp_path, own_pr(7, BRANCH), GH_FAIL="1")
        assert run.rc == 0 and _writes(run.gh) == []

    def test_a_checked_pull_request_needs_no_second_check(self, tmp_path):
        run = self._handler(tmp_path, _foreign({"isCrossRepository": True}), allowed="true")
        assert self._retried(run)
        assert not [c for c in run.gh if c[:2] == ["pr", "view"]]

    def test_the_feedback_is_the_reviewers_comment_only(self, tmp_path):
        comments = [
            {"user": {"login": "claude[bot]", "type": "Bot"}, "body": "## AI Review - Attempt 1/3\nthe review"},
            {"user": {"login": "github-actions[bot]", "type": "Bot"}, "body": "## AI Review - Final Status"},
            {"user": {"login": "someone", "type": "User"}, "body": "## AI Review - Attempt 2/3\nother text"},
            {"user": {"login": "claude", "type": "User"}, "body": "## AI Review - Attempt 2/3\nother text"},
        ]
        out = tmp_path / "feedback"
        out.mkdir()
        script = _step("impl-repair.yml", "Extract AI feedback from PR")["run"].replace("/tmp/", f"{out}/")
        run = _run(script, tmp_path, REPOSITORY=REPO, PR_NUM="7", GH_API_JSON=json.dumps(comments))
        assert run.rc == 0, run.log
        assert (out / "ai_feedback.md").read_text(encoding="utf-8") == "## AI Review - Attempt 1/3\nthe review\n"
        (call,) = run.gh
        assert call[:3] == ["api", "--paginate", "repos/owner/repo/issues/7/comments?per_page=100"]


# --- impl-merge --------------------------------------------------------------------------------


class TestImplMergeConditions:
    def _conditions(self, tmp: Path, shell=PIPEFAIL, **env: str) -> Run:
        values = {
            "EVENT_NAME": "pull_request",
            "EVENT_ACTION": "labeled",
            "EVENT_LABEL": "ai-approved",
            "EVENT_PR_BRANCH": BRANCH,
            "EVENT_PR_HEAD_REPO": REPO,
            "EVENT_PR_NUMBER": "7",
            "INPUT_PR_NUMBER": "",
            "GH_REPO": REPO,
        }
        script = _step("impl-merge.yml", "Check conditions")["run"].replace("/tmp/", f"{tmp}/")
        return _run(script, tmp, shell=shell, **values | env)

    @SHELLS
    def test_a_label_event_from_another_repository_stops_before_the_checkout(self, tmp_path, shell):
        run = self._conditions(tmp_path, shell=shell, EVENT_PR_HEAD_REPO="elsewhere/repo")
        assert run.rc == 1 and run.outputs == {} and run.gh == []
        assert len(run.errors()) == 1 and "(cross_repository)" in run.errors()[0]

    def test_a_label_event_from_this_repository_runs_without_the_branch_in_the_outputs(self, tmp_path):
        run = self._conditions(tmp_path, EVENT_PR_HEAD_REPO="Owner/Repo")
        assert run.rc == 0, run.log
        assert run.outputs == {"pr_number": "7", "should_run": "true"}

    def test_another_label_is_a_quiet_skip(self, tmp_path):
        run = self._conditions(tmp_path, EVENT_LABEL="quality:90", EVENT_PR_HEAD_REPO="elsewhere/repo")
        assert run.rc == 0 and run.outputs == {"should_run": "false"} and run.errors() == []

    @pytest.mark.parametrize("cross", [True, None, "false"])
    def test_a_dispatch_for_a_pull_request_not_from_this_repository_is_refused(self, tmp_path, cross):
        data = {"headRefName": BRANCH, "labels": [{"name": "ai-approved"}], "isCrossRepository": cross}
        run = self._conditions(
            tmp_path, EVENT_NAME="workflow_dispatch", INPUT_PR_NUMBER="7", GH_PR_JSON=json.dumps(data)
        )
        assert run.rc == 1 and run.outputs == {}
        assert len(run.errors()) == 1 and "(cross_repository)" in run.errors()[0]

    def test_a_write_back_dispatch_stays_a_quiet_skip(self, tmp_path):
        """Every dispatch runs both jobs; the merge job must not go red for the write-back PR."""
        data = {"headRefName": "review-writeback/spec-a/plotly/12", "labels": [], "isCrossRepository": False}
        run = self._conditions(
            tmp_path, EVENT_NAME="workflow_dispatch", INPUT_PR_NUMBER="9", GH_PR_JSON=json.dumps(data)
        )
        assert run.rc == 0 and run.outputs == {"should_run": "false"} and run.errors() == []

    @pytest.mark.parametrize("number", ["7;true", "https://github.com/x/y/pull/7", ""])
    def test_a_dispatch_with_a_bad_number_asks_gh_nothing(self, tmp_path, number):
        run = self._conditions(tmp_path, EVENT_NAME="workflow_dispatch", INPUT_PR_NUMBER=number)
        assert run.rc == 1 and run.gh == [] and "(bad_number)" in run.errors()[0]

    def test_the_guard_runs_after_the_checkout_and_before_the_first_read_of_the_branch(self):
        names = [s.get("name") for s in _jobs("impl-merge.yml")["merge"]["steps"]]
        assert names[:4] == ["Check conditions", "Checkout repository", STAGE, CHECK_STEP]
        for name in ("Extract info from branch", "Validate PR completeness before merge"):
            assert _step("impl-merge.yml", name, "merge")["env"]["BRANCH"] == "${{ steps.guard.outputs.branch }}"
        validate = _step("impl-merge.yml", "Validate PR completeness before merge", "merge")
        assert validate["env"]["HEAD_SHA"] == "${{ steps.guard.outputs.head_sha }}"
        assert 'REF="$HEAD_SHA"' in validate["run"]
        assert "steps.check.outputs.branch" not in (WORKFLOWS / "impl-merge.yml").read_text(encoding="utf-8")

    @pytest.mark.parametrize(("change", "code"), FOREIGN)
    def test_the_guard_step_refuses(self, tmp_path, change, code):
        run = _run(
            _step("impl-merge.yml", CHECK_STEP, "merge")["run"],
            tmp_path,
            REPOSITORY=REPO,
            PR_NUMBER="7",
            GH_PR_JSON=json.dumps(_foreign(change)),
        )
        _assert_refused(run, code)

    def test_the_guard_step_passes_the_pipelines_own(self, tmp_path):
        run = _run(
            _step("impl-merge.yml", CHECK_STEP, "merge")["run"],
            tmp_path,
            REPOSITORY=REPO,
            PR_NUMBER="7",
            GH_PR_JSON=json.dumps(own_pr(7, BRANCH)),
        )
        assert run.rc == 0, run.log
        assert run.outputs == {
            "branch": BRANCH,
            "head_sha": HEAD_SHA,
            "specification_id": "spec-a",
            "library": "plotly",
        }


class MergeOrigin:
    """A bare origin whose implementation branch holds the checked commit, and the job's clone of it."""

    def __init__(self, tmp: Path) -> None:
        self.tmp = tmp
        self.env = _git_env(tmp)
        seed, self.origin, self.work, self.ws = tmp / "seed", tmp / "origin.git", tmp / "work", tmp / "ws"
        seed.mkdir()
        _git(seed, self.env, "init", "-q", "-b", "main")
        self.commit(seed, {"core/x.py": "x = 1\n"}, "main")
        subprocess.run([REAL_GIT, "clone", "-q", "--bare", str(seed), str(self.origin)], env=self.env, check=True)
        subprocess.run([REAL_GIT, "clone", "-q", str(self.origin), str(self.work)], env=self.env, check=True)
        _git(self.work, self.env, "checkout", "-q", "-b", BRANCH)
        self.commit(self.work, {"plots/spec-a/implementations/python/plotly.py": "import plotly\n"}, "feat")
        _git(self.work, self.env, "push", "-q", "origin", BRANCH)
        self.validated = _git(self.work, self.env, "rev-parse", "HEAD")
        subprocess.run([REAL_GIT, "clone", "-q", str(self.origin), str(self.ws)], env=self.env, check=True)

    def commit(self, repo: Path, files: dict[str, str], message: str) -> str:
        for rel, text in files.items():
            (repo / rel).parent.mkdir(parents=True, exist_ok=True)
            (repo / rel).write_text(text, encoding="utf-8")
        _git(repo, self.env, "add", "-A")
        _git(repo, self.env, "commit", "-q", "-m", message)
        return _git(repo, self.env, "rev-parse", "HEAD")

    def move_main(self, name: str = "y") -> None:
        _git(self.work, self.env, "checkout", "-q", "main")
        self.commit(self.work, {f"core/{name}.py": f"{name} = 2\n"}, "main moves")
        _git(self.work, self.env, "push", "-q", "origin", "main")
        _git(self.work, self.env, "checkout", "-q", BRANCH)

    def push_branch(self) -> str:
        _git(self.work, self.env, "push", "-q", "-f", "origin", BRANCH)
        return _git(self.work, self.env, "rev-parse", "HEAD")

    def run(self, head: str, **change: Any) -> Run:
        script = _step("impl-merge.yml", "Merge PR to main (with retry)", "merge")["run"]
        script = script.replace("/tmp/", f"{self.tmp}/")
        pr = {**own_pr(7, BRANCH), "headRefOid": head, **change}
        return _run(
            script,
            self.tmp,
            cwd=self.ws,
            PR_NUM="7",
            REPOSITORY=REPO,
            HAS_ADMIN_TOKEN="true",
            BRANCH=BRANCH,
            VALIDATED_SHA=self.validated,
            SPEC_ID="spec-a",
            LIBRARY="plotly",
            GH_PR_JSON=json.dumps(pr),
        )


class TestImplMergeHead:
    @pytest.fixture
    def origin(self, tmp_path: Path) -> MergeOrigin:
        return MergeOrigin(tmp_path)

    @staticmethod
    def _merges(run: Run) -> list[list[str]]:
        return [c for c in run.gh if c[:2] == ["pr", "merge"]]

    def test_the_checked_head_is_merged_by_its_sha(self, origin):
        run = origin.run(origin.validated)
        assert run.rc == 0, run.log
        (merge,) = self._merges(run)
        assert merge[merge.index("--match-head-commit") + 1] == origin.validated

    def test_githubs_merge_of_main_into_the_checked_head_is_merged(self, origin):
        origin.move_main()
        _git(origin.work, origin.env, "merge", "-q", "--no-ff", "--no-edit", "main")
        head = origin.push_branch()
        run = origin.run(head)
        assert run.rc == 0, run.log
        (merge,) = self._merges(run)
        assert merge[merge.index("--match-head-commit") + 1] == head

    def test_two_merges_of_main_in_one_run_are_merged(self, origin):
        """main moved twice, so `update-branch` merged twice: the retry the loop exists for."""
        for name in ("y", "w"):
            origin.move_main(name)
            _git(origin.work, origin.env, "merge", "-q", "--no-ff", "--no-edit", "main")
        head = origin.push_branch()
        run = origin.run(head)
        assert run.rc == 0, run.log
        (merge,) = self._merges(run)
        assert merge[merge.index("--match-head-commit") + 1] == head

    def _refused(self, run: Run, why: str) -> None:
        assert run.rc == 1 and self._merges(run) == []
        assert len(run.errors()) == 1 and "not merged" in run.errors()[0] and why in run.errors()[0], run.log

    def test_a_commit_pushed_on_top_is_not_merged(self, origin):
        origin.commit(origin.work, {"plots/spec-a/implementations/python/plotly.py": "import os\n"}, "later")
        self._refused(origin.run(origin.push_branch()), "is not a merge")

    def _altered_merge(self, origin: MergeOrigin, name: str) -> None:
        origin.move_main(name)
        _git(origin.work, origin.env, "merge", "-q", "--no-ff", "--no-commit", "main")
        (origin.work / "core" / f"{name}-extra.py").write_text("z = 3\n", encoding="utf-8")
        _git(origin.work, origin.env, "add", "-A")
        _git(origin.work, origin.env, "commit", "-q", "-m", "merge main")

    @pytest.mark.parametrize(("merges", "merged"), [(8, True), (9, False)])
    def test_the_chain_is_bounded_at_eight_merges(self, origin, merges, merged):
        for i in range(merges):
            origin.move_main(f"m{i}")
            _git(origin.work, origin.env, "merge", "-q", "--no-ff", "--no-edit", "main")
        run = origin.run(origin.push_branch())
        if merged:
            assert run.rc == 0, run.log
        else:
            self._refused(run, "not within 8 merges of main")

    def test_a_merge_that_carries_a_change_of_its_own_is_not_merged(self, origin):
        self._altered_merge(origin, "y")
        self._refused(origin.run(origin.push_branch()), "is not the clean merge of its parents")

    def test_a_chain_with_one_altered_merge_is_not_merged(self, origin):
        self._altered_merge(origin, "y")
        origin.move_main("w")
        _git(origin.work, origin.env, "merge", "-q", "--no-ff", "--no-edit", "main")
        self._refused(origin.run(origin.push_branch()), "is not the clean merge of its parents")

    def test_a_merge_of_something_not_on_main_is_not_merged(self, origin):
        _git(origin.work, origin.env, "checkout", "-q", "-b", "side", "main")
        origin.commit(origin.work, {"core/side.py": "s = 1\n"}, "side")
        _git(origin.work, origin.env, "checkout", "-q", BRANCH)
        _git(origin.work, origin.env, "merge", "-q", "--no-ff", "--no-edit", "side")
        self._refused(origin.run(origin.push_branch()), "merges a commit that is not on main")

    def test_a_pull_request_that_no_longer_passes_the_guard_is_not_merged(self, origin):
        run = origin.run(origin.validated, isCrossRepository=True)
        self._refused(run, "no longer passes the guard (reason=cross_repository)")


# A `gh` that keeps the pull request's state in $MERGE_STATE and its head on
# the origin's branch, mirrored to refs/pull/7/head as GitHub keeps it.
# `pr update-branch` merges main into the branch the way GitHub does (parents:
# the head, then main) once main moved; the first `pr merge` merges, deletes
# the branch and loses its answer (a 502). After a merge, MERGED_VIEWS=fail
# makes every `pr view` fail and MERGED_VIEWS=state only the state probe;
# `view_failures` in the state fails that many `pr view` calls of any kind,
# and FULL_VIEW_FAILS=1 every read of the whole pull request. A second
# `pr merge` answers "already merged" with exit $ALREADY_MERGED_RC.
FAKE_GH_MERGE = """#!/usr/bin/env python3
import json, os, subprocess, sys
args = sys.argv[1:]
with open(os.environ["GH_LOG"], "a", encoding="utf-8") as f:
    f.write(json.dumps(args) + "\\n")
path = os.environ["MERGE_STATE"]
st = json.load(open(path))
origin, branch, work = os.environ["MERGE_ORIGIN"], os.environ["MERGE_BRANCH"], os.environ["MERGE_WORK"]

def git(*a, cwd=origin):
    return subprocess.run(["git", "-C", cwd, *a], check=True, capture_output=True, text=True).stdout.strip()

def head():
    r = subprocess.run(["git", "-C", origin, "rev-parse", "-q", "--verify", "refs/heads/" + branch],
                       capture_output=True, text=True)
    return r.stdout.strip() or st["last_head"]

def save():
    json.dump(st, open(path, "w"))

def bad_gateway():
    print("HTTP 502: Bad Gateway", file=sys.stderr)
    sys.exit(1)

key = " ".join(args[:2])
fields = args[args.index("--json") + 1] if "--json" in args else ""
views = os.environ.get("MERGED_VIEWS", "")
if key == "pr view":
    if st.get("view_failures", 0) > 0:
        st["view_failures"] -= 1
        save()
        bad_gateway()
    if st["merged"] and (views == "fail" or (views == "state" and fields == "state")):
        bad_gateway()
    if fields != "state" and os.environ.get("FULL_VIEW_FAILS") == "1":
        bad_gateway()
    state = "MERGED" if st["merged"] else "OPEN"
    if fields == "state":
        print(state)
    else:
        pr = json.loads(os.environ["GH_PR_JSON"])
        entry = {**pr, "state": state, "headRefOid": head()}
        print(json.dumps({k: v for k, v in entry.items() if k in fields.split(",")}))
elif key == "pr update-branch":
    if st["merged"]:
        sys.exit(1)
    if os.environ.get("UPDATE_MOVES_MAIN") == "1" and not st.get("updated"):
        git("fetch", "-q", "origin", cwd=work)
        git("checkout", "-q", "-B", "update", "origin/" + branch, cwd=work)
        git("merge", "-q", "--no-ff", "-m", "Merge branch 'main'", "origin/main", cwd=work)
        git("push", "-q", "origin", "update:refs/heads/" + branch, cwd=work)
        git("update-ref", "refs/pull/7/head", head())
        st["updated"] = True
        save()
elif key == "pr merge":
    target = args[args.index("--match-head-commit") + 1]
    if st["merged"]:
        print("! Pull request owner/repo#7 was already merged", file=sys.stderr)
        sys.exit(int(os.environ.get("ALREADY_MERGED_RC", "1")))
    if target != head():
        print("GraphQL: Head branch was modified. Review and try the merge again.", file=sys.stderr)
        sys.exit(1)
    st.update(merged=True, last_head=head(), merges=st.get("merges", 0) + 1)
    st["view_failures"] = int(os.environ.get("VIEW_FAILS_AFTER_MERGE", "0"))
    save()
    git("update-ref", "refs/pull/7/head", head())
    git("update-ref", "-d", "refs/heads/" + branch)
    bad_gateway()
"""


def _merge_run(
    origin: MergeOrigin,
    *,
    shell=PIPEFAIL,
    update: bool = False,
    views: str = "",
    already_rc: str = "1",
    merged_at: str | None = None,
    pull_ref: bool = True,
    validated: str | None = None,
    view_failures: int = 0,
    view_fails_after_merge: int = 0,
    full_view_fails: bool = False,
) -> tuple[Run, dict]:
    """Run the merge step against a stateful `gh` (FAKE_GH_MERGE).

    `merged_at`: the pull request is already merged at that head when the run
    starts (by a person or an earlier run), its branch gone, and refs/pull/7/head
    there unless `pull_ref` is false. `validated`: the commit this run's guard
    checked (the branch's head by default).
    """
    tmp = origin.tmp
    if update:
        origin.move_main("y")
    state = {"merged": False, "last_head": "", "view_failures": view_failures}
    if merged_at is not None:
        state.update(merged=True, last_head=merged_at)
        if pull_ref:
            _git(origin.origin, origin.env, "update-ref", "refs/pull/7/head", merged_at)
        _git(origin.origin, origin.env, "update-ref", "-d", f"refs/heads/{BRANCH}")
    state_file = tmp / "merge-state.json"
    state_file.write_text(json.dumps(state), encoding="utf-8")
    update_clone = tmp / "update-clone"
    subprocess.run([REAL_GIT, "clone", "-q", str(origin.origin), str(update_clone)], env=origin.env, check=True)
    script = _step("impl-merge.yml", "Merge PR to main (with retry)", "merge")["run"].replace("/tmp/", f"{tmp}/")
    run = _run(
        script,
        tmp,
        cwd=origin.ws,
        shell=shell,
        PR_NUM="7",
        REPOSITORY=REPO,
        HAS_ADMIN_TOKEN="true",
        BRANCH=BRANCH,
        VALIDATED_SHA=validated or origin.validated,
        SPEC_ID="spec-a",
        LIBRARY="plotly",
        GH_PR_JSON=json.dumps(own_pr(7, BRANCH)),
        MERGE_STATE=str(state_file),
        MERGE_ORIGIN=str(origin.origin),
        MERGE_BRANCH=BRANCH,
        MERGE_WORK=str(update_clone),
        MERGED_VIEWS=views,
        UPDATE_MOVES_MAIN="1" if update else "0",
        ALREADY_MERGED_RC=already_rc,
        FULL_VIEW_FAILS="1" if full_view_fails else "0",
        VIEW_FAILS_AFTER_MERGE=str(view_fails_after_merge),
        GIT_CONFIG_GLOBAL=origin.env["GIT_CONFIG_GLOBAL"],
        GIT_AUTHOR_NAME="t",
        GIT_AUTHOR_EMAIL="t@example.invalid",
        GIT_COMMITTER_NAME="t",
        GIT_COMMITTER_EMAIL="t@example.invalid",
        fake_gh=FAKE_GH_MERGE,
    )
    return run, json.loads(state_file.read_text(encoding="utf-8"))


def _merge_calls(run: Run) -> list[list[str]]:
    return [c for c in run.gh if c[:2] == ["pr", "merge"]]


MERGED_NOTICE = "is merged at the checked commit or GitHub's merges of main into it"


class TestImplMergeFoundMerged:
    """A pull request that is merged when the step looks: post-merge steps only for a head this run checked."""

    @pytest.fixture
    def origin(self, tmp_path: Path) -> MergeOrigin:
        return MergeOrigin(tmp_path)

    @SHELLS
    def test_merged_at_the_checked_head(self, origin, shell):
        run, _ = _merge_run(origin, shell=shell, merged_at=origin.validated)
        assert run.rc == 0, run.log
        assert MERGED_NOTICE in run.log and _merge_calls(run) == []
        assert not [c for c in run.gh if c[:2] == ["pr", "update-branch"]]

    def test_merged_at_githubs_merges_of_main_on_top(self, origin):
        heads = []
        for name in ("y", "w"):
            origin.move_main(name)
            _git(origin.work, origin.env, "merge", "-q", "--no-ff", "--no-edit", "main")
            heads.append(_git(origin.work, origin.env, "rev-parse", "HEAD"))
        _git(origin.work, origin.env, "push", "-q", "-f", "origin", f"HEAD:refs/heads/{BRANCH}")
        run, _ = _merge_run(origin, merged_at=heads[-1])
        assert run.rc == 0, run.log
        assert MERGED_NOTICE in run.log and _merge_calls(run) == []
        assert any("refs/pull/7/head" in line for line in run.git)

    @SHELLS
    def test_merged_at_a_head_this_run_did_not_check_stops_before_the_post_merge_steps(self, origin, shell):
        other = origin.commit(origin.work, {"plots/spec-a/implementations/python/plotly.py": "import os\n"}, "other")
        _git(origin.work, origin.env, "push", "-q", "-f", "origin", f"HEAD:refs/heads/{BRANCH}")
        run, _ = _merge_run(origin, shell=shell, merged_at=other)
        assert run.rc == 1 and _merge_calls(run) == []
        (error,) = run.errors()
        assert error.startswith("::error::PR #7 is merged, but not at the checked commit")
        assert "no post-merge step runs for it" in error

    def test_a_merged_head_that_cannot_be_fetched_is_retried_and_never_taken(self, origin):
        other = origin.commit(origin.work, {"plots/spec-a/implementations/python/plotly.py": "import os\n"}, "other")
        _git(origin.work, origin.env, "push", "-q", "-f", "origin", f"HEAD:refs/heads/{BRANCH}")
        run, _ = _merge_run(origin, merged_at=other, pull_ref=False)
        assert run.rc == 1 and _merge_calls(run) == []
        assert run.log.count("::notice::Merge attempt") == 5
        assert run.errors() == ["::error::Merge failed after 5 attempts"]

    def test_a_re_dispatch_after_an_earlier_run_merged_goes_on(self, origin):
        """The re-dispatch that recovers failed post-merge steps: its guard checked the merged head itself."""
        merged = origin.commit(origin.work, {"plots/spec-a/implementations/python/plotly.py": "import os\n"}, "fix")
        _git(origin.work, origin.env, "push", "-q", "-f", "origin", f"HEAD:refs/heads/{BRANCH}")
        run, _ = _merge_run(origin, merged_at=merged, validated=merged)
        assert run.rc == 0, run.log
        assert MERGED_NOTICE in run.log and _merge_calls(run) == []


class TestImplMergeUnreadableHead:
    @pytest.fixture
    def origin(self, tmp_path: Path) -> MergeOrigin:
        return MergeOrigin(tmp_path)

    def test_an_unreadable_head_before_any_merge_call_sends_none(self, origin):
        run, state = _merge_run(origin, full_view_fails=True)
        assert run.rc == 1 and not state["merged"]
        assert _merge_calls(run) == []
        assert run.errors() == ["::error::Merge failed after 5 attempts"]

    @SHELLS
    @pytest.mark.parametrize("update", [False, True], ids=["head-unchanged", "head-an-update-merge"])
    @pytest.mark.parametrize("already_rc", ["0", "1"], ids=["already-merged-exit-0", "already-merged-exit-1"])
    def test_after_a_lost_answer_the_call_is_sent_again_and_already_merged_is_confirmed(
        self, origin, shell, update, already_rc
    ):
        # Attempt 2: the three state probes and the head read fail. The merge call goes out
        # again with the checked commit, answers "already merged", and the merged head is then
        # read and checked before the post-merge steps.
        run, state = _merge_run(origin, shell=shell, update=update, already_rc=already_rc, view_fails_after_merge=4)
        assert run.rc == 0, run.log
        assert state["merges"] == 1
        first, second = _merge_calls(run)
        assert second[second.index("--match-head-commit") + 1] == origin.validated
        assert MERGED_NOTICE in run.log


class TestImplMergeLostAnswer:
    """`gh pr merge` merged on the server, but its answer was lost; the branch is gone with it."""

    @pytest.fixture
    def origin(self, tmp_path: Path) -> MergeOrigin:
        return MergeOrigin(tmp_path)

    @SHELLS
    @pytest.mark.parametrize("update", [False, True], ids=["head-unchanged", "head-an-update-merge"])
    @pytest.mark.parametrize("already_rc", ["0", "1"], ids=["already-merged-exit-0", "already-merged-exit-1"])
    def test_a_merged_pull_request_whose_head_can_be_read_ends_as_merged(self, origin, shell, update, already_rc):
        """Only the state probe fails: the next read of the whole pull request finds it merged at the head it named."""
        run, state = _merge_run(origin, shell=shell, update=update, views="state", already_rc=already_rc)
        assert run.rc == 0, run.log
        assert state["merged"] and state["merges"] == 1
        assert run.errors() == [] and MERGED_NOTICE in run.log

    @pytest.mark.parametrize("update", [False, True], ids=["head-unchanged", "head-an-update-merge"])
    def test_a_merge_that_can_never_be_confirmed_fails_the_step(self, origin, update):
        """Every read fails after the merge: no post-merge step runs on a head nobody could check."""
        run, state = _merge_run(origin, update=update, views="fail")
        assert run.rc == 1 and state["merges"] == 1
        assert run.errors() == ["::error::Merge failed after 5 attempts"]


# --- results are written only onto the head that was checked ----------------------------------


class WriteOrigin:
    """A bare origin whose implementation branch holds the reviewed commit, and the job's checkout of it."""

    META = "plots/spec-a/metadata/python/plotly.yaml"

    def __init__(self, tmp: Path) -> None:
        self.tmp = tmp
        self.env = _git_env(tmp)
        seed, self.origin, self.ws = tmp / "seed", tmp / "origin.git", tmp / "ws"
        seed.mkdir()
        _git(seed, self.env, "init", "-q", "-b", "main")
        (seed / self.META).parent.mkdir(parents=True)
        (seed / self.META).write_text("quality_score: null\n", encoding="utf-8")
        impl = seed / "plots" / "spec-a" / "implementations" / "python" / "plotly.py"
        impl.parent.mkdir(parents=True)
        impl.write_text("import plotly\n", encoding="utf-8")
        _git(seed, self.env, "add", "-A")
        _git(seed, self.env, "commit", "-q", "-m", "generated")
        _git(seed, self.env, "branch", BRANCH)
        subprocess.run([REAL_GIT, "clone", "-q", "--bare", str(seed), str(self.origin)], env=self.env, check=True)
        subprocess.run([REAL_GIT, "clone", "-q", str(self.origin), str(self.ws)], env=self.env, check=True)
        self.head = _git(self.ws, self.env, "rev-parse", f"origin/{BRANCH}")
        _git(self.ws, self.env, "checkout", "-q", self.head)

    def push_elsewhere(self) -> str:
        """Another run or a person pushes to the branch; returns the new head."""
        other = self.tmp / "other"
        if not other.exists():
            subprocess.run(
                [REAL_GIT, "clone", "-q", "-b", BRANCH, str(self.origin), str(other)], env=self.env, check=True
            )
        _git(other, self.env, "commit", "-q", "--allow-empty", "-m", "pushed meanwhile")
        _git(other, self.env, "push", "-q", "origin", f"HEAD:refs/heads/{BRANCH}")
        return _git(other, self.env, "rev-parse", "HEAD")

    def branch_head(self) -> str:
        return _git(self.origin, self.env, "rev-parse", f"refs/heads/{BRANCH}")


# The verdict labels the early verdict step may have set.
VERDICT_LABELS = [{"name": n} for n in ("quality:91", "ai-approved", "regen:improved")]


class TestReviewWritesOntoTheCheckedHead:
    """ "Update metadata and implementation header" writes the review only onto the commit it reviewed."""

    STEP = "Update metadata and implementation header"

    def _script(self, meanwhile: str = "") -> str:
        """The step's checkout and its commit-and-push, with the metadata update in between replaced."""
        script = _step("impl-review.yml", self.STEP)["run"]
        checkout = 'git checkout -B "$BRANCH" "origin/$BRANCH"\n'
        head = script[: script.index(checkout) + len(checkout)]
        # The remote stays the test's origin.
        head = re.sub(r'git remote set-url origin "[^"]*"\n', "", head)
        push = script[script.index("# Commit and push") :]
        update = f'echo "quality_score: 91" > "$METADATA_FILE"\n{meanwhile}\n'
        return _render(head + update + push)

    def _run(self, origin: WriteOrigin, *, shell=PIPEFAIL, meanwhile: str = "") -> Run:
        return _run(
            self._script(meanwhile),
            origin.tmp,
            cwd=origin.ws,
            shell=shell,
            PR_NUM="7",
            HEAD_SHA=origin.head,
            SPEC_ID="spec-a",
            LIBRARY="plotly",
            LANGUAGE="python",
            EXT=".py",
            BRANCH=BRANCH,
            REVIEW_CARRIED="false",
            GH_PR_JSON=json.dumps({**own_pr(7, BRANCH), "labels": VERDICT_LABELS}),
            GIT_CONFIG_GLOBAL=origin.env["GIT_CONFIG_GLOBAL"],
            GIT_CONFIG_NOSYSTEM="1",
        )

    @SHELLS
    def test_the_reviewed_head_gets_the_review_as_before(self, tmp_path, shell):
        origin = WriteOrigin(tmp_path)
        run = self._run(origin, shell=shell)
        assert run.rc == 0, run.log
        new = origin.branch_head()
        assert new != origin.head and _git(origin.origin, origin.env, "rev-parse", f"{new}^") == origin.head
        assert "head_moved" not in run.outputs and _writes(run.gh) == []

    @SHELLS
    def test_a_branch_that_moved_during_the_review_gets_nothing(self, tmp_path, shell):
        origin = WriteOrigin(tmp_path)
        moved = origin.push_elsewhere()
        run = self._run(origin, shell=shell)
        assert run.rc == 1 and run.outputs == {"head_moved": "true"}
        assert origin.branch_head() == moved
        (error,) = run.errors()
        assert error == (
            f"::error::{BRANCH} is at {moved[:12]}, not at the reviewed {origin.head[:12]}: "
            "nothing was written; the review must run again on the new head"
        )
        # The verdict labels this run set come off; the score label stays.
        removed = sorted(c[c.index("--remove-label") + 1] for c in run.gh if c[:2] == ["pr", "edit"])
        assert removed == ["ai-approved", "regen:improved"]

    @SHELLS
    def test_a_branch_that_moves_before_the_push_is_not_overwritten(self, tmp_path, shell):
        origin = WriteOrigin(tmp_path)
        other = tmp_path / "other"
        subprocess.run(
            [REAL_GIT, "clone", "-q", "-b", BRANCH, str(origin.origin), str(other)], env=origin.env, check=True
        )
        meanwhile = (
            f'git -C "{other}" -c user.name=o -c user.email=o@o commit -q --allow-empty -m meanwhile\n'
            f'git -C "{other}" push -q origin HEAD:{BRANCH}'
        )
        run = self._run(origin, shell=shell, meanwhile=meanwhile)
        assert run.rc == 1 and run.outputs == {"head_moved": "true"}
        assert origin.branch_head() == _git(other, origin.env, "rev-parse", "HEAD")
        assert len(run.errors()) == 1

    def test_the_push_is_a_plain_push(self):
        script = _code_only(_step("impl-review.yml", self.STEP)["run"])
        pushes = re.findall(r"git push[^\n]*", script)
        assert pushes == ['git push origin "$BRANCH"; then']
        assert "--force" not in script and "push -f" not in script

    def test_a_refused_write_asks_for_one_review_of_the_new_head(self):
        """The re-review rescue runs for it; the verdict step, which dispatches merge or repair, does not."""
        rescue = _step("impl-review.yml", "Re-dispatch review after a post-score failure")
        assert "steps.metadata.outputs.head_moved == 'true'" in rescue["if"]
        verdict = _step("impl-review.yml", "Add verdict label and take action")
        assert "always()" not in verdict["if"] and "failure()" not in verdict["if"]


class TestRepairStartsFromTheCheckedHead:
    def _checkout(self, origin: WriteOrigin, head_sha: str, shell=PIPEFAIL) -> Run:
        _git(origin.ws, origin.env, "checkout", "-q", "main")
        return _run(
            _step("impl-repair.yml", "Checkout PR branch")["run"],
            origin.tmp,
            cwd=origin.ws,
            shell=shell,
            BRANCH=BRANCH,
            HEAD_SHA=head_sha,
            GITHUB_ENV=str(origin.tmp / "github_env"),
        )

    @SHELLS
    def test_the_checked_head_is_repaired(self, tmp_path, shell):
        origin = WriteOrigin(tmp_path)
        run = self._checkout(origin, origin.head, shell)
        assert run.rc == 0, run.log
        assert f"start_sha={origin.head}" in (tmp_path / "github_env").read_text(encoding="utf-8")

    @SHELLS
    def test_a_branch_that_moved_after_the_check_is_refused_before_the_session(self, tmp_path, shell):
        origin = WriteOrigin(tmp_path)
        moved = origin.push_elsewhere()
        run = self._checkout(origin, origin.head, shell)
        assert run.rc == 1
        assert run.errors() == [
            f"::error::{BRANCH} is at {moved[:12]}, not at the checked {origin.head[:12]}: "
            "no repair on a commit the guard did not check"
        ]

    def test_the_guard_hands_on_the_checked_head(self):
        assert (
            _step("impl-repair.yml", "Checkout PR branch")["env"]["HEAD_SHA"] == "${{ steps.guard.outputs.head_sha }}"
        )


# --- impl-review-retry -------------------------------------------------------------------------


class TestImplReviewRetry:
    def _rescue(self, tmp: Path, pr: dict[str, Any], **env: str) -> Run:
        values = {"REPOSITORY": REPO, "PR_NUM": "7", "BRANCH": BRANCH, "HEAD_REPO": REPO}
        pr = {**pr, "labels": [{"name": "ai-review-failed"}]}
        return _run(
            _step("impl-review-retry.yml", "Re-dispatch review")["run"], tmp, GH_PR_JSON=json.dumps(pr), **values | env
        )

    def test_a_label_event_from_another_repository_asks_gh_nothing(self, tmp_path):
        run = self._rescue(tmp_path, own_pr(7, BRANCH), HEAD_REPO="elsewhere/repo")
        assert run.rc == 1 and run.gh == []
        assert len(run.errors()) == 1 and "(cross_repository)" in run.errors()[0]

    @pytest.mark.parametrize(("change", "code"), FOREIGN)
    def test_a_refused_pull_request_is_neither_labelled_nor_dispatched(self, tmp_path, change, code):
        _assert_refused(self._rescue(tmp_path, _foreign(change)), code)

    def test_the_pipelines_own_pull_request_is_rescued_once(self, tmp_path):
        run = self._rescue(tmp_path, own_pr(7, BRANCH))
        assert run.rc == 0, run.log
        assert [c[:2] for c in _writes(run.gh)] == [
            ["label", "create"],
            ["pr", "edit"],
            ["pr", "edit"],
            ["workflow", "run"],
        ]

    def test_another_branch_is_a_quiet_skip_that_does_not_print_it(self, tmp_path):
        run = self._rescue(tmp_path, own_pr(7, BRANCH), BRANCH="feature/x$(id)")
        assert run.rc == 0 and run.gh == [] and "feature" not in run.log

    def test_the_guard_comes_from_main_never_the_merge_commit(self):
        job = _jobs("impl-review-retry.yml")["rescue"]
        checkout = job["steps"][0]
        assert checkout["with"]["ref"] == "${{ github.event.repository.default_branch }}"
        assert checkout["with"]["persist-credentials"] is False
        assert _workflow("impl-review-retry.yml")["permissions"]["contents"] == "read"


# --- the watchdog ------------------------------------------------------------------------------


def _scan(tmp: Path, prs: list[dict[str, Any]], **env: str) -> Run:
    script = _step("watchdog-stuck-jobs.yml", "Scan and dispatch")["run"]
    values = {"GH_REPO": REPO, "STALE_HOURS": "4", "DRY_RUN": "false", "REGEN_PAIRS": ""}
    return _run(script, tmp, GH_LIST_JSON=json.dumps(prs), **values | env)


STALE = "2026-01-01T00:00:00Z"


class TestWatchdog:
    def test_only_the_pipelines_own_pull_request_is_dispatched(self, tmp_path):
        """Label-less and stale, all four would be Case 5; only #7 is the pipeline's own."""
        prs = [
            own_pr(7, BRANCH, labels=[], updatedAt=STALE),
            {**own_pr(8, BRANCH, labels=[], updatedAt=STALE), "isCrossRepository": True},
            own_pr(9, "implementation/spec-a/notalib", labels=[], updatedAt=STALE),
            {**own_pr(10, BRANCH, labels=[], updatedAt=STALE), "isCrossRepository": None},
        ]
        run = _scan(tmp_path, prs)
        assert run.rc == 0, run.log
        dispatched = [c for c in run.gh if c[:2] == ["workflow", "run"]]
        assert dispatched == [["workflow", "run", "impl-review.yml", "-f", "pr_number=7"]]
        assert [c[2] for c in run.gh if c[:2] == ["pr", "edit"]] == ["7"]
        for number, code in ((8, "cross_repository"), (9, "unknown_library"), (10, "missing_field")):
            assert f"PR #{number}: skipped ({code}), not one of the pipeline's own pull requests" in run.log
        # A skip is no warning: a foreign pull request does not raise one on every scan.
        assert not [line for line in run.log.splitlines() if line.startswith("::warning::")]
        assert "3 open implementation PR(s) skipped" in run.summary

    def test_the_listing_asks_for_what_the_guard_reads(self, tmp_path):
        run = _scan(tmp_path, [])
        (listing,) = [c for c in run.gh if c[:2] == ["pr", "list"]]
        fields = listing[listing.index("--json") + 1].split(",")
        assert set(pr_guard.REQUIRED_FIELDS) <= set(fields)

    def test_a_guard_that_does_not_answer_skips_the_scan_of_pull_requests_only(self, tmp_path):
        (tmp_path / "runner" / "pr-guard").mkdir(parents=True)
        stage_guard(tmp_path / "runner")
        (tmp_path / "runner" / "pr-guard" / "libraries").write_text("\n", encoding="utf-8")
        script = _step("watchdog-stuck-jobs.yml", "Scan and dispatch")["run"]
        prs = [own_pr(7, BRANCH, labels=[], updatedAt=STALE)]
        values = {"GH_REPO": REPO, "STALE_HOURS": "4", "DRY_RUN": "false", "REGEN_PAIRS": ""}
        run = _run(script, tmp_path, stage=False, GH_LIST_JSON=json.dumps(prs), **values)
        assert run.rc == 0, run.log
        assert _writes(run.gh) == []
        assert "could not be checked against the pull request guard" in run.log
        assert "::notice::Watchdog scan complete" in run.log

    # Both places of section B that ask whether a pair has an open PR.
    SECTION_B = pytest.mark.parametrize(
        ("label", "why"),
        [("generate:plotly", "stuck pending"), ("impl:plotly:failed", "failed")],
        ids=["generate-label", "failed-label"],
    )

    @pytest.mark.parametrize(
        ("change", "retried"),
        [
            pytest.param({"isCrossRepository": True}, True, id="foreign-pr-is-no-open-pr"),
            pytest.param({"author": {"login": "someone"}}, True, id="foreign-author-is-no-open-pr"),
            pytest.param({"headRefName": "implementation/spec-a/plotlyx"}, True, id="prefix-match-is-no-open-pr"),
            pytest.param({"headRefName": "implementation/spec-b/plotly"}, True, id="another-pair-is-no-open-pr"),
            pytest.param({}, False, id="own-open-pr-blocks-the-retry"),
        ],
    )
    @SECTION_B
    def test_a_generation_retry_counts_only_the_pipelines_own_open_pull_request(
        self, tmp_path, change, retried, label, why
    ):
        """Section B: whether the pair has an open PR, read from a `head:` search."""
        issues = [{"number": 42, "labels": [{"name": label}], "updatedAt": STALE}]
        # The fake answers every `pr list` with this one PR, section A's listing included.
        pr = {**own_pr(5, BRANCH, labels=[{"name": "ai-approved"}], updatedAt=STALE), **change}
        run = _scan(tmp_path, [pr], DRY_RUN="true", GH_ISSUES_JSON=json.dumps(issues), GH_ISSUE_TITLE="[spec-a] A spec")
        assert run.rc == 0, run.log
        dispatch = f"[dry-run] Issue #42: generate ({why}) plotly → gh workflow run impl-generate.yml"
        assert (dispatch in run.log) is retried

    @SECTION_B
    @pytest.mark.parametrize(
        "title", ["[Spec-A] x", "[spec-a/../b] x", "[spec a] x", "[$(x)] x", "[spec-a;b] x", "[-a] x", "no brackets"]
    )
    def test_a_title_without_a_spec_id_in_the_catalogues_shape_starts_nothing(self, tmp_path, label, why, title):
        issues = [{"number": 42, "labels": [{"name": label}], "updatedAt": STALE}]
        run = _scan(tmp_path, [], DRY_RUN="true", GH_ISSUES_JSON=json.dumps(issues), GH_ISSUE_TITLE=title)
        assert run.rc == 0, run.log
        assert "cannot resolve spec_id from title" in run.log
        assert "impl-generate.yml" not in run.log and "$(x)" not in run.log

    @SECTION_B
    def test_a_label_without_a_registered_library_starts_nothing(self, tmp_path, label, why):
        issues = [{"number": 42, "labels": [{"name": label.replace("plotly", "notalib")}], "updatedAt": STALE}]
        run = _scan(tmp_path, [], DRY_RUN="true", GH_ISSUES_JSON=json.dumps(issues), GH_ISSUE_TITLE="[spec-a] x")
        assert run.rc == 0, run.log
        assert "names no registered library" in run.log and "impl-generate.yml" not in run.log

    def test_a_generation_retry_waits_for_its_run_by_title(self, tmp_path):
        """The run list is matched in jq with the values as arguments; the count is read only as digits."""
        issues = [{"number": 42, "labels": [{"name": "generate:plotly"}], "updatedAt": STALE}]
        runs = [{"displayTitle": "Generate: plotly for spec-a", "createdAt": "2999-01-01T00:00:00Z"}]
        run = _scan(
            tmp_path, [], GH_ISSUES_JSON=json.dumps(issues), GH_ISSUE_TITLE="[spec-a] x", GH_RUNS_JSON=json.dumps(runs)
        )
        assert run.rc == 0, run.log
        assert ["issue", "edit", "42", "--add-label", "watchdog:retried-plotly"] in run.gh

    def test_every_listing_of_the_scan_goes_through_the_guard(self):
        """Two listings, the scan's and the one inside `open_own_prs`; both call sites of B use the function."""
        script = _code_only(_step("watchdog-stuck-jobs.yml", "Scan and dispatch")["run"])
        assert len(re.findall(r"gh pr list\b", script)) == 2
        assert script.count('open_pr=$(open_own_prs "$spec_id" "$lib")') == 2


# --- impl-generate's inputs --------------------------------------------------------------------


class TestImplGenerateInputs:
    """Dispatch inputs and event values reach "Extract inputs" through env:, shape-checked before first use."""

    DISPATCH = {
        "EVENT_NAME": "workflow_dispatch",
        "SPEC_ID_INPUT": "spec-a",
        "LIBRARY_INPUT": "plotly",
        "ISSUE_INPUT": "42",
        "MODEL_INPUT": "sonnet",
        "REGEN_GATE_INPUT": "true",
        "EVENT_ISSUE_NUMBER": "",
        "LABEL_NAME": "",
        "ISSUE_TITLE": "",
        "REGEN_GATE": "true",
        "SOURCE_REF_INPUT": "",
        "SOURCE_MODEL_INPUT": "",
    }

    def _extract(self, tmp: Path, *, shell=PIPEFAIL, **change: str) -> Run:
        script = _step("impl-generate.yml", "Extract inputs")["run"]
        return _run(script, tmp, shell=shell, **self.DISPATCH | change)

    @SHELLS
    @pytest.mark.parametrize(
        ("name", "value", "input_name"),
        [
            ("SPEC_ID_INPUT", "spec-a$(x)", "specification_id"),
            ("SPEC_ID_INPUT", "spec-a\nb", "specification_id"),
            ("SPEC_ID_INPUT", "Spec-A", "specification_id"),
            ("SPEC_ID_INPUT", "-spec", "specification_id"),
            ("SPEC_ID_INPUT", "../spec", "specification_id"),
            ("LIBRARY_INPUT", "notalib", "library"),
            ("LIBRARY_INPUT", "plotly;x", "library"),
            ("ISSUE_INPUT", "42;x", "issue_number"),
            ("ISSUE_INPUT", "0", "issue_number"),
            ("MODEL_INPUT", "gpt", "model"),
            ("REGEN_GATE_INPUT", "yes", "regen_gate"),
        ],
    )
    def test_a_value_without_its_shape_stops_the_job(self, tmp_path, shell, name, value, input_name):
        run = self._extract(tmp_path, shell=shell, **{name: value})
        assert run.rc == 1 and run.outputs == {}
        assert run.errors() == [
            f"::error::bad_input: {input_name} does not have its expected shape; nothing was generated"
        ]
        assert "$(x)" not in run.log and ";x" not in run.log

    @pytest.mark.parametrize(
        ("title", "label"),
        [("[spec--a] x", "generate:plotly"), ("[spec-a] x", "generate:notalib"), ("[spec-a] x", "generate:")],
    )
    def test_the_label_trigger_is_checked_the_same_way(self, tmp_path, title, label):
        run = self._extract(
            tmp_path,
            EVENT_NAME="issues",
            SPEC_ID_INPUT="",
            LIBRARY_INPUT="",
            MODEL_INPUT="",
            EVENT_ISSUE_NUMBER="42",
            ISSUE_TITLE=title,
            LABEL_NAME=label,
        )
        assert run.rc == 1 and run.outputs == {}

    def test_no_input_reaches_the_script_as_text(self):
        """Every value the step reads from a dispatch or an event is in env:, none in the script."""
        step = _step("impl-generate.yml", "Extract inputs")
        assert "${{" not in step["run"]
        for name in ("specification_id", "library", "issue_number", "model", "regen_gate"):
            assert f"${{{{ inputs.{name} }}}}" in step["env"].values(), name
        assert "${{ github.event.issue.number }}" in step["env"].values()


# --- impl-generate's lookup of an existing pull request ---------------------------------------


class TestImplGenerateLookup:
    def _create(self, tmp: Path, listed: list[dict[str, Any]]) -> Run:
        script = _render(_step("impl-generate.yml", "Create Pull Request")["run"])
        return _run(
            script,
            tmp,
            REPOSITORY=REPO,
            MODEL="opus",
            SPEC_ID="spec-a",
            LANGUAGE="python",
            LIBRARY="plotly",
            EXT=".py",
            ISSUE="42",
            BRANCH=BRANCH,
            REGEN_LABEL="",
            PREV_STORED="n/a",
            CHANGE_REQUEST="",
            SOURCE_REF="",
            SOURCE_MODEL="",
            SOURCE_SHA="",
            GH_LIST_JSON=json.dumps(listed),
        )

    @pytest.mark.parametrize(("change", "code"), [p for p in FOREIGN if p.id not in ("other-number",)])
    def test_a_pull_request_that_is_not_the_pipelines_own_is_never_taken_over(self, tmp_path, change, code):
        run = self._create(tmp_path, [_foreign(change, number=99)])
        assert run.rc == 0, run.log
        assert run.outputs["pr_number"] == "124"  # its own, new pull request
        assert [c[:2] for c in run.gh] == [["pr", "list"], ["pr", "create"]]

    def test_the_pipelines_own_open_pull_request_is_reused(self, tmp_path):
        run = self._create(tmp_path, [own_pr(99, BRANCH)])
        assert run.rc == 0, run.log
        assert run.outputs["pr_number"] == "99"
        assert [c[:2] for c in run.gh] == [["pr", "list"]]

    def test_a_guard_that_does_not_answer_adopts_nothing(self, tmp_path):
        script = _render(_step("impl-generate.yml", "Create Pull Request")["run"])
        env = {
            "REPOSITORY": REPO,
            "MODEL": "opus",
            "SPEC_ID": "spec-a",
            "LANGUAGE": "python",
            "LIBRARY": "plotly",
            "EXT": ".py",
            "ISSUE": "",
            "BRANCH": BRANCH,
            "GH_LIST_JSON": json.dumps([own_pr(99, BRANCH)]),
        }
        run = _run(script, tmp_path, stage=False, **env)
        assert run.outputs["pr_number"] == "124"


# --- every workflow that takes a pull request ---------------------------------------------------

# What the scan covers, and no more (docs/workflows/overview.md says the same):
# a workflow reads a pull request when its text has `gh pr view`, `gh pr list`,
# `gh pr checkout`, `gh pr diff`, `pr_number`, a `/pulls` API path,
# `refs/pull/` or `head_ref`; a job takes a pull request number from
# `inputs.pr_number`, `client_payload.pr_number`,
# `github.event.pull_request.number` or a `needs.<job>.outputs.pr_number`. A
# number under another name, or a read through another API call, is not found.
READS_A_PULL_REQUEST = re.compile(r"gh pr (view|list|checkout|diff)|pr_number|/pulls\b|refs/pull/|head_ref")
NUMBER_FROM_TRIGGER = re.compile(
    r"inputs\.pr_number|client_payload\.pr_number|github\.event\.pull_request\.number"
    r"|needs\.[A-Za-z0-9_-]+\.outputs\.pr_number"
)
# The only checkout refs allowed before the guard: none (the workflow's own
# commit), or the default branch.
CHECKOUT_REFS_BEFORE_THE_GUARD = ("", "${{ github.event.repository.default_branch }}")
GUARD_RUN = re.compile(r'pr_guard\.py" (check|filter)|"\$PR_GUARD" filter')
# Jobs that take a pull request of another of the pipeline's shapes, each with
# the check that stands in for the guard there and must stay in the job.
OTHER_CONTRACTS = {
    # review-writeback/<spec>/<library>/<n>: the bot's author, this
    # repository, the label and the gate record (regen_writeback.check_pr).
    ("impl-merge.yml", "writeback"): "regen_writeback.py check-pr",
    # specification/<spec-id>: the Claude app's author, this repository, the
    # spec files only (spec_pr_guard.py).
    ("spec-create.yml", "merge"): "spec_pr_guard.py",
    ("spec-create.yml", "create"): "select(.isCrossRepository == false)",
}
# daily-regen's pair pick lists PRs in Python; regen_pick_pairs runs each
# listing through pr_guard (TestTheScriptsListings).
SCRIPT_GUARDS = ("regen_pick_pairs.py",)
# Before the guard, a job may read a pull request, never fetch it, check it out or write to it.
BEFORE_THE_GUARD = re.compile(
    r"git fetch|git checkout|gh pr (checkout|diff|edit|comment|close|merge|ready|review|update-branch|create)"
    r"|gh label|gh issue (edit|comment|close)|gh workflow run|gh api [^\n]*(-f |-X |--method)"
)
# What filters a `gh pr list` by repository.
REPOSITORY_FILTERS = (
    'pr_guard.py" filter',
    "own_prs",
    "select(.isCrossRepository == false)",
    "jq -r '.isCrossRepository'",
    # The write-back contract's own identity (regen_writeback.own_open_writebacks).
    '"$TOOL" own-open',
)
# Listings that only hold work back and never pick a pull request to act on:
# they count every pull request, a fork's included (a fork's open edit is one
# the held-back work could race). Each must stay a bare count.
HOLD_BACK_ONLY = {("daily-regen.yml", "Skip-gate — open PRs touching this spec?")}
# A `gh pr list` in command position (not inside a message), any flag spelling.
LISTING = re.compile(r"(?:^|[\s(|;&])gh pr list(?=\s)")


def _reading_workflows() -> list[str]:
    """The workflows whose text, comments left out, reads a pull request."""
    return [
        p.name
        for p in sorted(WORKFLOWS.glob("*.yml"))
        if READS_A_PULL_REQUEST.search(_code_only(p.read_text(encoding="utf-8")))
    ]


def _run_scripts(filename: str) -> list[tuple[str, dict[str, Any]]]:
    return [(job, step) for job, body in _jobs(filename).items() for step in body.get("steps", []) if "run" in step]


def _listings(script: str) -> list[str]:
    """Each `gh pr list` command of a script, its continuation lines joined."""
    joined = re.sub(r"\\\n\s*", " ", _code_only(script))
    return [line[m.start() :].lstrip(" (|;&") for line in joined.splitlines() for m in LISTING.finditer(line)]


class TestEveryPullRequestReader:
    def test_the_scan_finds_the_pipelines_readers(self):
        """A check of the scan itself: it must not come back empty or miss a known reader."""
        found = set(_reading_workflows())
        assert {
            "impl-review.yml",
            "impl-repair.yml",
            "impl-merge.yml",
            "impl-review-retry.yml",
            "watchdog-stuck-jobs.yml",
            "impl-generate.yml",
            "daily-regen.yml",
            "spec-create.yml",
        } <= found

    @pytest.mark.parametrize("filename", _reading_workflows())
    def test_every_reader_stages_and_runs_the_guard(self, filename):
        text = (WORKFLOWS / filename).read_text(encoding="utf-8")
        steps = [step for _, step in _run_scripts(filename)]
        staged = any(step.get("name") == STAGE for step in steps)
        runs = any(GUARD_RUN.search(step["run"]) for step in steps)
        other = [check for (wf, _), check in OTHER_CONTRACTS.items() if wf == filename]
        assert (
            (staged and runs) or any(s in text for s in SCRIPT_GUARDS) or (other and all(c in text for c in other))
        ), (
            f"{filename} reads pull requests but neither stages and runs automation/scripts/pr_guard.py "
            "nor names its own check in OTHER_CONTRACTS"
        )

    @pytest.mark.parametrize(
        ("filename", "job"),
        [
            (filename, job)
            for filename in _reading_workflows()
            for job, body in _jobs(filename).items()
            if NUMBER_FROM_TRIGGER.search(json.dumps(body))
        ],
    )
    def test_a_job_checks_the_pull_request_before_it_fetches_or_writes_anything(self, filename, job):
        steps = _jobs(filename)[job].get("steps", [])
        if (filename, job) in OTHER_CONTRACTS:
            assert OTHER_CONTRACTS[filename, job] in json.dumps(steps), (filename, job)
            return
        names = [s.get("name") for s in steps]
        guard_at = next((i for i, s in enumerate(steps) if 'pr_guard.py" check' in s.get("run", "")), None)
        assert guard_at is not None, f"{filename}:{job} takes a pull request number but never runs the guard"
        assert STAGE in names[:guard_at], f"{filename}:{job} runs the guard before staging it"
        for step in steps[:guard_at]:
            assert not BEFORE_THE_GUARD.search(_code_only(step.get("run", ""))), (filename, job, step.get("name"))
            ref = str((step.get("with") or {}).get("ref", ""))
            assert ref in CHECKOUT_REFS_BEFORE_THE_GUARD, (filename, job, step.get("name"), ref)
        script = _code_only(steps[guard_at]["run"])
        check = script.index('pr_guard.py" check')
        for match in BEFORE_THE_GUARD.finditer(script):
            assert match.start() > check, (filename, job, match.group(0))
        # A refusal may say it refused (a fixed flag); nothing else is written before the check.
        output = script.replace('echo "refused=true" >> "$GITHUB_OUTPUT"', "").find("GITHUB_OUTPUT")
        assert output == -1 or output > check, (filename, job)

    @pytest.mark.parametrize("filename", [p.name for p in sorted(WORKFLOWS.glob("*.yml"))])
    def test_every_listing_filters_on_the_repository(self, filename):
        for job, step in _run_scripts(filename):
            listings = _listings(step["run"])
            if not listings:
                continue
            if (filename, step.get("name")) in HOLD_BACK_ONLY:
                for listing in listings:
                    assert "--json number --jq 'length'" in listing, (filename, listing)
                continue
            # A field list kept in a variable of the step counts as written out.
            variables = dict(re.findall(r'\b([A-Z_]+_FIELDS)="([^"]+)"', step["run"]))
            for listing in listings:
                for name, value in variables.items():
                    listing = listing.replace(f"${{{name}}}", value).replace(f"${name}", value)
                assert "isCrossRepository" in listing, (filename, job, listing)
            assert any(f in step["run"] for f in REPOSITORY_FILTERS), (filename, job, step.get("name"))

    def test_the_hold_back_listings_still_exist(self):
        for filename, name in HOLD_BACK_ONLY:
            assert _listings(_step(filename, name)["run"]), (filename, name)

    def test_a_listing_under_another_flag_spelling_is_found(self):
        script = 'X=$(gh pr list -R "$REPO" --json number | jq length)\necho "gh pr list failed"'
        assert _listings(script) == ['gh pr list -R "$REPO" --json number | jq length)']


# Expressions a `run:` script may hold: values that cannot carry text from
# outside (an issue, a pull request, a comment, a branch name, a dispatch).
SAFE_EXPRESSIONS = re.compile(
    r"github\.(sha|repository|run_id|event_name|event\.issue\.number|event\.pull_request\.number"
    r"|event\.pull_request\.(base|head)\.sha|event\.merge_group\.(base|head)_sha)"
    r"|runner\.temp|secrets\.[A-Za-z0-9_]+|vars\.[A-Za-z0-9_]+|steps\.guard\.outputs\.[a-z_]+"
)
# The pipeline's privileged workflows: none of these may paste anything else.
PIPELINE = re.compile(r"impl-.*|bulk-generate|daily-regen|watchdog-stuck-jobs|spec-create|report-validate")
# Elsewhere, values only this repository's writers set, listed so that a new
# one is a decision: the base branch of CI, a boolean input of CI, and the
# changed spec and implementation paths of a push to main.
KNOWN_ELSEWHERE = {
    ("ci-changelog.yml", "github.base_ref"),
    ("ci-tests.yml", "inputs.force_run"),
    ("sync-labels.yml", "steps.detect.outputs.specs"),
    ("sync-labels.yml", "steps.detect.outputs.impls"),
}


def _run_expressions() -> list[tuple[str, str, str]]:
    return [
        (path.name, str(step.get("name")), match.group(1))
        for path in sorted(WORKFLOWS.glob("*.yml"))
        for _, step in _run_scripts(path.name)
        for match in EXPRESSION.finditer(step["run"])
    ]


class TestNoOutsideTextInRunScripts:
    def test_no_run_script_pastes_a_value_that_can_carry_outside_text(self):
        """Such values go through `env:` and are checked for their shape there."""
        found = [
            (filename, name, expression)
            for filename, name, expression in _run_expressions()
            if not SAFE_EXPRESSIONS.fullmatch(expression)
            and (PIPELINE.fullmatch(filename.removesuffix(".yml")) or (filename, expression) not in KNOWN_ELSEWHERE)
        ]
        assert found == []

    def test_the_known_exceptions_still_exist(self):
        present = {(filename, expression) for filename, _, expression in _run_expressions()}
        assert KNOWN_ELSEWHERE <= present

    @pytest.mark.parametrize(
        "expression",
        [
            "inputs.specification_id",
            "github.event.issue.title",
            "github.event.comment.body",
            "github.head_ref",
            "github.event.pull_request.head.ref",
            "steps.pr.outputs.branch",
            "matrix.spec_id",
        ],
    )
    def test_values_that_can_carry_outside_text_are_not_safe(self, expression):
        assert not SAFE_EXPRESSIONS.fullmatch(expression)


class TestTheScriptsListings:
    def test_every_pr_listing_of_the_pick_goes_through_the_guard(self):
        """Each `_gh_json` call that lists pull requests sits inside `own_pulls`."""
        tree = ast.parse(Path(regen_pick_pairs.__file__).read_text(encoding="utf-8"))
        parents = {child: node for node in ast.walk(tree) for child in ast.iter_child_nodes(node)}
        listings = [
            node
            for node in ast.walk(tree)
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == "_gh_json"
            and "issue" not in ast.unparse(node.args[0])
        ]
        assert len(listings) == 3
        for call in listings:
            parent = parents[call]
            assert isinstance(parent, ast.Call) and getattr(parent.func, "id", "") == "own_pulls", ast.unparse(call)

    def test_the_pick_asks_for_what_the_guard_reads(self):
        source = Path(regen_pick_pairs.__file__).read_text(encoding="utf-8")
        assert 'guard_fields = ",".join(pr_guard.REQUIRED_FIELDS)' in source
        assert source.count("{guard_fields},") == 2

    def test_the_resume_dispatch_only_passes_on_what_the_pick_resumed(self):
        """daily-regen's resume job dispatches the pick's resumes, which the guard filtered; review and repair check again."""
        script = _step("daily-regen.yml", "Re-dispatch paused reviews and repairs")["run"]
        assert "needs.pick.outputs.resume_json" in json.dumps(
            _step("daily-regen.yml", "Re-dispatch paused reviews and repairs")
        )
        assert "gh pr list" not in script and "gh pr view" not in script


def test_the_guard_fields_of_the_shell_listings_are_the_checkers():
    """The watchdog spells out the fields the guard requires; they must stay the same list."""
    script = _step("watchdog-stuck-jobs.yml", "Scan and dispatch")["run"]
    (fields,) = re.findall(r'GUARD_FIELDS="([^"]+)"', script)
    assert tuple(fields.split(",")) == pr_guard.REQUIRED_FIELDS
    for filename, step in (
        ("impl-review.yml", "Extract PR info"),
        ("impl-repair.yml", CHECK_STEP),
        ("impl-merge.yml", CHECK_STEP),
        ("impl-generate.yml", "Create Pull Request"),
    ):
        script = _step(filename, step)["run"]
        assert ",".join(pr_guard.REQUIRED_FIELDS) in script, (filename, step)


def test_own_fields_match_the_required_fields():
    assert set(own_pr(1, BRANCH)) == set(pr_guard.REQUIRED_FIELDS)
    assert own_fields(REPO)["headRepositoryOwner"] == {"login": "owner"}
