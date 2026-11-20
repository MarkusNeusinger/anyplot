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
from pathlib import Path
from typing import Any

import pytest
import yaml

from automation.scripts import pr_guard, regen_pick_pairs
from tests.unit.workflows.pr_guard_support import (
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
if key == "pr view":
    print(os.environ.get("GH_STATE", "OPEN") if fields == "state" else os.environ.get("GH_PR_JSON", "{}"))
elif key == "pr list":
    print(os.environ.get("GH_LIST_JSON", "[]"))
elif key == "issue list":
    print(os.environ.get("GH_ISSUES_JSON", "[]"))
elif key == "issue view":
    print(os.environ.get("GH_ISSUE_TITLE", ""))
elif key == "pr create":
    print("https://github.com/owner/repo/pull/124")
elif args[:1] == ["api"]:
    if "/actions/" in " ".join(args):
        sys.exit(1)
    print(os.environ.get("GH_API_JSON", "[]"))
"""
# Logs its arguments, then runs the real git.
FAKE_GIT = f"""#!/bin/sh
printf '%s\\n' "$*" >> "$SHIM_GIT_LOG"
exec {REAL_GIT} "$@"
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


def _run(script: str, tmp: Path, *, cwd: Path | None = None, shell=PIPEFAIL, stage: bool = True, **env: str) -> Run:
    """Run a step script as Actions does, behind a staged guard, with fake `gh`, `git` and `sleep`."""
    assert "${{" not in script
    bin_dir = tmp / "bin"
    bin_dir.mkdir(exist_ok=True)
    for name, body in (("gh", FAKE_GH), ("git", FAKE_GIT), ("sleep", "#!/bin/sh\nexit 0\n")):
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
    pytest.param({"headRefName": f"{BRANCH}/extra"}, "branch_shape", id="extra-segment"),
    pytest.param({"headRefName": "implementation/Spec-A/plotly"}, "branch_shape", id="uppercase"),
    pytest.param({"headRefName": "implementation/../plotly"}, "branch_shape", id="traversal"),
    pytest.param({"headRefName": "implementation/$(touch pwned)/plotly"}, "branch_shape", id="shell"),
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

    def test_the_ref_is_the_workflows_own_commit_or_main(self):
        """On a pull-request event the workflow's commit is the pull request's merge commit."""
        for filename, job, step in _staging_steps():
            on = _workflow(filename).get("on") or _workflow(filename).get(True)
            ref = step["env"]["GUARD_REF"]
            if "pull_request" in on:
                assert "github.sha" not in ref or "'origin/main'" in ref, (filename, job)
                assert "main" in ref or "default_branch" in ref, (filename, job)
            else:
                assert ref == "${{ github.sha }}", (filename, job)

    def test_the_library_list_comes_from_the_registry(self):
        (text,) = {step["run"] for _, _, step in _staging_steps()}
        assert "from core.constants import SUPPORTED_LIBRARIES" in text
        for library in LIBRARIES.split():
            assert library not in text

    @SHELLS
    def test_stages_the_committed_guard_never_the_working_tree(self, tmp_path, shell):
        repo = tmp_path / "repo"
        repo.mkdir()
        env = _git_env(tmp_path)
        _git(repo, env, "init", "-q", "-b", "main")
        sha = commit_guard_sources(repo, env)
        # The working tree holds something else; the staged copy must not be it.
        (repo / "automation" / "scripts" / "pr_guard.py").write_text("raise SystemExit(0)\n", encoding="utf-8")
        run = _run(_step("impl-review.yml", STAGE)["run"], tmp_path, cwd=repo, shell=shell, stage=False, GUARD_REF=sha)
        assert run.rc == 0, run.log
        staged = tmp_path / "runner" / "pr-guard"
        assert (staged / "pr_guard.py").read_bytes() == GUARD.read_bytes()
        assert (staged / "libraries").read_text(encoding="utf-8").split() == LIBRARIES.split()

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


def _assert_refused(run: Run, code: str, number: str = "7") -> None:
    """No outputs, no writes, one error line and one summary line with the fixed code."""
    assert run.rc != 0, run.log
    assert run.outputs == {}
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
        assert "pwned" not in run.log and "Parent Issue" not in run.log and "haiku" not in run.log

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
        script = _step("impl-review.yml", "Checkout PR code")["run"]
        assert "${{ steps.pr.outputs.head_sha }}" in script

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
    def _check(self, tmp: Path, pr: dict[str, Any], *, shell=PIPEFAIL, **env: str) -> Run:
        values = {"REPOSITORY": REPO, "PR_NUMBER": "7", "SPEC_ID_INPUT": "spec-a", "LIBRARY_INPUT": "plotly"}
        return _run(
            _step("impl-repair.yml", CHECK_STEP)["run"], tmp, shell=shell, GH_PR_JSON=json.dumps(pr), **values | env
        )

    @SHELLS
    @pytest.mark.parametrize(("change", "code"), FOREIGN)
    def test_a_refused_pull_request_is_never_fetched(self, tmp_path, shell, change, code):
        run = self._check(tmp_path, _foreign(change), shell=shell)
        _assert_refused(run, code)
        assert run.git == []

    @pytest.mark.parametrize(("spec", "library"), [("spec-b", "plotly"), ("spec-a", "altair")])
    def test_inputs_that_differ_from_the_branch_are_refused(self, tmp_path, spec, library):
        run = self._check(tmp_path, own_pr(7, BRANCH), SPEC_ID_INPUT=spec, LIBRARY_INPUT=library)
        _assert_refused(run, "input_mismatch")

    @SHELLS
    def test_the_pipelines_own_pull_request_passes(self, tmp_path, shell):
        run = self._check(tmp_path, own_pr(7, BRANCH), shell=shell)
        assert run.rc == 0, run.log
        assert run.outputs == {"allowed": "true", "branch": BRANCH}

    def test_the_checkout_uses_the_checked_branch_and_follows_the_check(self):
        names = [s.get("name") for s in _jobs("impl-repair.yml")["repair"]["steps"]]
        assert names.index(STAGE) < names.index(CHECK_STEP) < names.index("Checkout PR branch")
        checkout = _step("impl-repair.yml", "Checkout PR branch")
        assert checkout["env"]["BRANCH"] == "${{ steps.guard.outputs.branch }}"
        assert "gh " not in checkout["run"]

    def test_the_failure_handler_runs_only_for_a_checked_pull_request(self):
        handler = _step("impl-repair.yml", "Handle repair failure")
        assert handler["if"] == "failure() && steps.guard.outputs.allowed == 'true'"

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
    def _conditions(self, tmp: Path, **env: str) -> Run:
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
        return _run(script, tmp, **values | env)

    @SHELLS
    def test_a_label_event_from_another_repository_stops_before_the_checkout(self, tmp_path, shell):
        run = self._conditions(tmp_path, EVENT_PR_HEAD_REPO="elsewhere/repo")
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

    def move_main(self) -> None:
        _git(self.work, self.env, "checkout", "-q", "main")
        self.commit(self.work, {"core/y.py": "y = 2\n"}, "main moves")
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

    def test_a_commit_pushed_on_top_is_not_merged(self, origin):
        origin.commit(origin.work, {"plots/spec-a/implementations/python/plotly.py": "import os\n"}, "later")
        run = origin.run(origin.push_branch())
        assert run.rc == 1 and self._merges(run) == []
        assert len(run.errors()) == 1 and "not merged" in run.errors()[0]

    def test_a_merge_that_carries_a_change_of_its_own_is_not_merged(self, origin):
        origin.move_main()
        _git(origin.work, origin.env, "merge", "-q", "--no-ff", "--no-commit", "main")
        (origin.work / "core" / "z.py").write_text("z = 3\n", encoding="utf-8")
        _git(origin.work, origin.env, "add", "-A")
        _git(origin.work, origin.env, "commit", "-q", "-m", "merge main")
        run = origin.run(origin.push_branch())
        assert run.rc == 1 and self._merges(run) == []

    def test_a_merge_of_something_not_on_main_is_not_merged(self, origin):
        _git(origin.work, origin.env, "checkout", "-q", "-b", "side", "main")
        origin.commit(origin.work, {"core/side.py": "s = 1\n"}, "side")
        _git(origin.work, origin.env, "checkout", "-q", BRANCH)
        _git(origin.work, origin.env, "merge", "-q", "--no-ff", "--no-edit", "side")
        run = origin.run(origin.push_branch())
        assert run.rc == 1 and self._merges(run) == []

    def test_a_pull_request_that_no_longer_passes_the_guard_is_not_merged(self, origin):
        run = origin.run(origin.validated, isCrossRepository=True)
        assert run.rc == 1 and self._merges(run) == []


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

    @pytest.mark.parametrize(
        ("change", "retried"),
        [
            pytest.param({"isCrossRepository": True}, True, id="foreign-pr-is-no-open-pr"),
            pytest.param({"headRefName": "implementation/spec-a/plotlyx"}, True, id="prefix-match-is-no-open-pr"),
            pytest.param({"headRefName": "implementation/spec-b/plotly"}, True, id="another-pair-is-no-open-pr"),
            pytest.param({}, False, id="own-open-pr-blocks-the-retry"),
        ],
    )
    def test_a_generation_retry_counts_only_the_pipelines_own_open_pull_request(self, tmp_path, change, retried):
        """Section B: whether the pair has an open PR, read from a `head:` search."""
        issues = [{"number": 42, "labels": [{"name": "generate:plotly"}], "updatedAt": STALE}]
        # The fake answers every `pr list` with this one PR, section A's listing included.
        pr = {**own_pr(5, BRANCH, labels=[{"name": "ai-approved"}], updatedAt=STALE), **change}
        run = _scan(tmp_path, [pr], DRY_RUN="true", GH_ISSUES_JSON=json.dumps(issues), GH_ISSUE_TITLE="[spec-a] A spec")
        assert run.rc == 0, run.log
        dispatch = "[dry-run] Issue #42: generate (stuck pending) plotly → gh workflow run impl-generate.yml"
        assert (dispatch in run.log) is retried


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

# Reads a pull request by number (the scan the brief names), or picks them from a list.
READS_A_PULL_REQUEST = re.compile(r"gh pr view|pr_number|gh pr list")
# A job takes a pull request by number from its trigger.
NUMBER_FROM_TRIGGER = re.compile(r"inputs\.pr_number|client_payload\.pr_number|github\.event\.pull_request\.number")
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
)


def _reading_workflows() -> list[str]:
    return [p.name for p in sorted(WORKFLOWS.glob("*.yml")) if READS_A_PULL_REQUEST.search(p.read_text("utf-8"))]


def _run_scripts(filename: str) -> list[tuple[str, dict[str, Any]]]:
    return [(job, step) for job, body in _jobs(filename).items() for step in body.get("steps", []) if "run" in step]


def _listings(script: str) -> list[str]:
    """Each `gh pr list` command of a script, its continuation lines joined."""
    joined = re.sub(r"\\\n\s*", " ", _code_only(script))
    return [line[m.start() :] for line in joined.splitlines() for m in re.finditer(r"gh pr list\s+--", line)]


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
            assert "pull_request.head" not in ref and "steps." not in ref, (filename, job, step.get("name"))
        script = _code_only(steps[guard_at]["run"])
        check = script.index('pr_guard.py" check')
        for match in BEFORE_THE_GUARD.finditer(script):
            assert match.start() > check, (filename, job, match.group(0))
        output = script.find("GITHUB_OUTPUT")
        assert output == -1 or output > check, (filename, job)

    @pytest.mark.parametrize("filename", [p.name for p in sorted(WORKFLOWS.glob("*.yml"))])
    def test_every_listing_filters_on_the_repository(self, filename):
        for job, step in _run_scripts(filename):
            listings = _listings(step["run"])
            if not listings:
                continue
            for listing in listings:
                assert "isCrossRepository" in listing or "GUARD_FIELDS" in listing, (filename, job, listing)
            assert any(f in step["run"] for f in REPOSITORY_FILTERS), (filename, job, step.get("name"))


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
