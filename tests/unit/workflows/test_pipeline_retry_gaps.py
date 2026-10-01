"""Recovery paths of the implementation pipeline, run for real where they can be.

Three gaps observed 2026-09-28..30:

1. impl-review scored a PR, then "Add quality score label" hit HTTP 502 twice
   (run 36712916551, PR #11984): every later step was skipped and nothing
   re-ran the review. "Re-dispatch review after a post-score failure" now
   re-reviews once on the run's own ref, or hands the PR to the watchdog.
2. impl-generate's auto-retry ran on main although a branch dispatched it
   (runs 36400546243/36402058602 → #11969–#11971).
3. impl-review's repair-exhaustion path ran `git push origin main`, which the
   main ruleset refuses; it could only ever target the live implementation of
   a forced regeneration, so it is gone.

The step scripts run under `bash -eo pipefail` like Actions runs them, with a
fake `gh` that records its calls and a no-op `sleep` on PATH. The rest are
content guards for wiring without a local execution loop.
"""

from __future__ import annotations

import os
import subprocess
from pathlib import Path
from typing import Any

import pytest
import yaml


REPO_ROOT = Path(__file__).parent.parent.parent.parent
WORKFLOWS_DIR = REPO_ROOT / ".github" / "workflows"
RESCUE_STEP = "Re-dispatch review after a post-score failure"
VERDICT_STEP = "Add verdict label and take action"
QUALITY_STEP = "Add quality score label"
MARKER = "<!-- review-retry:spec-a:plotly -->"

# Answers `pr view` with $GH_LABELS (fails with GH_FAIL_VIEW=1), `issue view`
# with $GH_ISSUE_LABELS (fails with GH_FAIL_ISSUE_VIEW=1), `api` with one
# $GH_MARKERS count per page (fails with GH_FAIL_API=1), `workflow run`,
# `pr comment` and `label create` with exit $GH_*_RC; an `issue edit
# --remove-label` fails with GH_FAIL_REMOVE=1. Logs every call.
FAKE_GH = """\
for arg in "$@"; do printf '%s\\n' "$arg"; done >> "$GH_LOG"
echo "--END--" >> "$GH_LOG"
case "$1 $2" in
  "pr view")
    [ "${GH_FAIL_VIEW:-0}" = "1" ] && { echo "HTTP 502" >&2; exit 1; }
    [ -n "$GH_LABELS" ] && printf '%s\\n' $GH_LABELS
    exit 0 ;;
  "issue view")
    [ "${GH_FAIL_ISSUE_VIEW:-0}" = "1" ] && { echo "HTTP 502" >&2; exit 1; }
    [ -n "$GH_ISSUE_LABELS" ] && printf '%s\\n' $GH_ISSUE_LABELS
    exit 0 ;;
  "issue edit")
    [ "${GH_FAIL_REMOVE:-0}" = "1" ] && [ "$4" = "--remove-label" ] && { echo "HTTP 502" >&2; exit 1; }
    exit 0 ;;
  "api --paginate")
    [ "${GH_FAIL_API:-0}" = "1" ] && { echo "HTTP 502" >&2; exit 1; }
    printf '%s\\n' ${GH_MARKERS:-0}
    exit 0 ;;
  "workflow run") exit "${GH_DISPATCH_RC:-0}" ;;
  "pr comment") exit "${GH_COMMENT_RC:-0}" ;;
  "label create") exit "${GH_LABEL_CREATE_RC:-0}" ;;
esac
exit 0
"""


def _steps(filename: str) -> list[dict[str, Any]]:
    workflow = yaml.safe_load((WORKFLOWS_DIR / filename).read_text(encoding="utf-8"))
    return [step for job in workflow["jobs"].values() for step in job.get("steps", [])]


def _step(filename: str, name: str) -> dict[str, Any]:
    matches = [s for s in _steps(filename) if s.get("name") == name]
    assert len(matches) == 1, f"expected exactly one step named {name!r} in {filename}"
    return matches[0]


def _code_only(script: str) -> str:
    return "\n".join(line for line in script.splitlines() if not line.lstrip().startswith("#"))


def _bin(tmp_path: Path) -> str:
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir(exist_ok=True)
    for name, body in (("gh", FAKE_GH), ("sleep", "exit 0\n")):
        path = bin_dir / name
        path.write_text("#!/bin/sh\n" + body, encoding="utf-8")
        path.chmod(0o755)
    return f"{bin_dir}{os.pathsep}{os.environ['PATH']}"


def _run(
    script: str, cwd: Path, tmp_path: Path, **env: str
) -> tuple[subprocess.CompletedProcess[str], list[list[str]]]:
    assert "${{" not in script
    log = tmp_path / "gh_log"
    log.unlink(missing_ok=True)
    base = {k: v for k, v in os.environ.items() if not k.startswith(("GIT_", "GH_"))}
    result = subprocess.run(
        ["bash", "-eo", "pipefail", "-c", script],
        cwd=cwd,
        env={**base, "PATH": _bin(tmp_path), "GH_LOG": str(log), "GH_TOKEN": "unused", **env},
        capture_output=True,
        text=True,
    )
    calls = [c.splitlines() for c in log.read_text(encoding="utf-8").split("--END--\n") if c] if log.exists() else []
    return result, calls


def _calls(calls: list[list[str]], *prefix: str) -> list[list[str]]:
    return [c for c in calls if c[: len(prefix)] == list(prefix)]


# ---------------------------------------------------------------------------
# Gap 1: a review that failed after scoring
# ---------------------------------------------------------------------------


class TestPostScoreRescue:
    ENV = {
        "PR_NUM": "7",
        "SPEC_ID": "spec-a",
        "LIBRARY": "plotly",
        "SCORE": "86",
        "REPOSITORY": "owner/repo",
        "RUN_ID": "1",
        "MODEL": "sonnet",
        "REVIEW_MODEL_ALIAS": "opus",
        "WORKFLOW_REF": "fix/some-branch",
    }

    def _rescue(self, tmp_path: Path, **env: str) -> tuple[subprocess.CompletedProcess[str], list[list[str]]]:
        return _run(_step("impl-review.yml", RESCUE_STEP)["run"], tmp_path, tmp_path, **{**self.ENV, **env})

    def test_first_failure_re_reviews_once_on_the_run_ref(self, tmp_path):
        result, calls = self._rescue(tmp_path, GH_LABELS="regen quality:86")
        assert result.returncode == 1, result.stdout + result.stderr  # the run stays red
        runs = _calls(calls, "workflow", "run")
        assert runs == [
            [
                "workflow",
                "run",
                "impl-review.yml",
                "--ref",
                "fix/some-branch",
                "-f",
                "pr_number=7",
                "-f",
                "model=sonnet",
                "-f",
                "review_model=opus",
            ]
        ]
        assert len(_calls(calls, "pr", "comment")) == 1  # the marker
        assert not _calls(calls, "pr", "edit")

    def test_marker_comment_is_durable_before_the_dispatch(self, tmp_path):
        _, calls = self._rescue(tmp_path)
        kinds = [" ".join(c[:2]) for c in calls]
        assert kinds.index("pr comment") < kinds.index("workflow run")
        (comment,) = _calls(calls, "pr", "comment")
        assert MARKER in Path(comment[-1]).read_text(encoding="utf-8")

    def test_a_lost_marker_comment_never_dispatches(self, tmp_path):
        # Without a durable marker the re-review would have no budget record.
        result, calls = self._rescue(tmp_path, GH_COMMENT_RC="1")
        assert result.returncode == 1
        assert not _calls(calls, "workflow", "run")
        assert ["pr", "edit", "7", "--add-label", "ai-review-failed"] in calls

    def test_an_unreadable_budget_counts_as_spent(self, tmp_path):
        result, calls = self._rescue(tmp_path, GH_FAIL_API="1")
        assert result.returncode == 1
        assert len(_calls(calls, "api", "--paginate")) == 3  # retried
        assert not _calls(calls, "workflow", "run")
        assert ["pr", "edit", "7", "--add-label", "ai-review-failed"] in calls

    @pytest.mark.parametrize(("pages", "dispatches"), [("0 0 0", 1), ("0 1", 0), ("0 0 1", 0), ("1 1", 0)])
    def test_the_marker_is_counted_across_comment_pages(self, tmp_path, pages, dispatches):
        # `gh api --paginate --jq` prints one count per page.
        result, calls = self._rescue(tmp_path, GH_MARKERS=pages)
        assert result.returncode == 1
        assert len(_calls(calls, "workflow", "run")) == dispatches
        assert (["pr", "edit", "7", "--add-label", "ai-review-failed"] in calls) == (dispatches == 0)

    def test_a_non_numeric_budget_counts_as_spent(self, tmp_path):
        result, calls = self._rescue(tmp_path, GH_MARKERS="oops")
        assert result.returncode == 1
        assert not _calls(calls, "workflow", "run")
        assert ["pr", "edit", "7", "--add-label", "ai-review-failed"] in calls

    def test_empty_ref_falls_back_to_main(self, tmp_path):
        _, calls = self._rescue(tmp_path, WORKFLOW_REF="")
        (run,) = _calls(calls, "workflow", "run")
        assert run[3:5] == ["--ref", "main"]

    def test_spent_budget_hands_over_to_the_watchdog(self, tmp_path):
        result, calls = self._rescue(tmp_path, GH_MARKERS="1")
        assert result.returncode == 1
        assert not _calls(calls, "workflow", "run")
        assert ["pr", "edit", "7", "--add-label", "ai-review-failed"] in calls

    def test_failed_dispatch_hands_over_to_the_watchdog(self, tmp_path):
        result, calls = self._rescue(tmp_path, GH_DISPATCH_RC="1")
        assert result.returncode == 1
        assert len(_calls(calls, "workflow", "run")) == 3  # retried
        assert ["pr", "edit", "7", "--add-label", "ai-review-failed"] in calls

    def test_unreadable_labels_hand_over_to_the_watchdog(self, tmp_path):
        result, calls = self._rescue(tmp_path, GH_FAIL_VIEW="1")
        assert result.returncode == 1
        assert not _calls(calls, "workflow", "run")
        assert ["pr", "edit", "7", "--add-label", "ai-review-failed"] in calls

    @pytest.mark.parametrize("verdict", ["ai-approved", "ai-rejected", "regen:improved", "regen:kept"])
    def test_a_verdict_label_leaves_the_pr_alone(self, tmp_path, verdict):
        result, calls = self._rescue(tmp_path, GH_LABELS=f"quality:86 {verdict}")
        assert result.returncode == 1
        assert not _calls(calls, "workflow", "run")
        assert not _calls(calls, "pr", "edit")
        assert not _calls(calls, "pr", "comment")

    def test_a_similar_label_is_not_a_verdict(self, tmp_path):
        _, calls = self._rescue(tmp_path, GH_LABELS="quality:86 ai-approved-pending")
        assert len(_calls(calls, "workflow", "run")) == 1

    def test_runs_only_after_a_post_score_failure_without_a_verdict(self):
        step = _step("impl-review.yml", RESCUE_STEP)
        condition = step["if"]
        assert condition.startswith("failure() && ")
        assert "steps.score.outputs.has_output == 'true'" in condition
        assert "steps.early_verdict.conclusion != 'success'" in condition
        assert _step("impl-review.yml", "Add preliminary verdict label (early)")["id"] == "early_verdict"
        assert step["env"]["WORKFLOW_REF"] == "${{ github.ref_name }}"

    def test_sits_after_the_metadata_step_and_before_the_verdict(self):
        names = [s.get("name") for s in _steps("impl-review.yml")]
        at = names.index(RESCUE_STEP)
        assert names.index("Update metadata and implementation header") < at < names.index(VERDICT_STEP)

    def test_shares_the_marker_with_the_no_output_retry(self):
        marker = 'MARKER="<!-- review-retry:${SPEC_ID}:${LIBRARY} -->"'
        assert marker in _step("impl-review.yml", RESCUE_STEP)["run"]
        assert marker in _step("impl-review.yml", "Validate review output")["run"]


class TestNoScoreRetryBudget:
    """ "Validate review output" reads the same budget the same way."""

    ENV = {
        "PR_NUM": "7",
        "SPEC_ID": "spec-a",
        "LIBRARY": "plotly",
        "REPOSITORY": "owner/repo",
        "RUN_ID": "1",
        "MODEL": "sonnet",
        "REVIEW_MODEL_ALIAS": "opus",
    }

    def _validate(self, tmp_path: Path, **env: str) -> tuple[subprocess.CompletedProcess[str], list[list[str]]]:
        script = _step("impl-review.yml", "Validate review output")["run"]
        return _run(script, tmp_path, tmp_path, **{**self.ENV, **env})

    def test_first_failure_retries_once(self, tmp_path):
        result, calls = self._validate(tmp_path, GH_MARKERS="0 0")
        assert result.returncode == 1
        assert len(_calls(calls, "api", "repos/owner/repo/dispatches")) == 1
        assert not _calls(calls, "pr", "edit")

    @pytest.mark.parametrize("env", [{"GH_MARKERS": "0 1"}, {"GH_FAIL_API": "1"}])
    def test_spent_or_unreadable_budget_never_retries(self, tmp_path, env):
        result, calls = self._validate(tmp_path, **env)
        assert result.returncode == 1
        assert not _calls(calls, "api", "repos/owner/repo/dispatches")
        assert ["pr", "edit", "7", "--add-label", "ai-review-failed"] in calls
        (comment,) = _calls(calls, "pr", "comment")
        assert comment[3:5] == ["--body", MARKER]  # the log holds one line per body line

    def test_the_final_failure_comment_is_retried(self, tmp_path):
        result, calls = self._validate(tmp_path, GH_FAIL_API="1", GH_COMMENT_RC="1")
        assert result.returncode == 1
        assert ["pr", "edit", "7", "--add-label", "ai-review-failed"] in calls
        assert len(_calls(calls, "pr", "comment")) == 3


class TestQualityLabelStep:
    ENV = {"PR_NUM": "7", "SCORE": "86"}

    def test_every_call_is_retried(self, tmp_path):
        script = _step("impl-review.yml", QUALITY_STEP)["run"]
        # The add fails three times, then lands.
        counter = tmp_path / "count"
        gh = (
            f'if [ "$1 $2" = "pr edit" ]; then n=$(cat {counter} 2>/dev/null || echo 0); n=$((n+1)); '
            f"echo $n > {counter}; [ $n -lt 4 ] && exit 1; fi\n"
        )
        path = _bin(tmp_path)
        (tmp_path / "bin" / "gh").write_text("#!/bin/sh\n" + gh + FAKE_GH, encoding="utf-8")
        result = subprocess.run(
            ["bash", "-eo", "pipefail", "-c", script],
            cwd=tmp_path,
            env={**os.environ, "PATH": path, "GH_LOG": str(tmp_path / "log"), **self.ENV},
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, result.stdout + result.stderr
        assert counter.read_text().strip() == "4"

    def test_stale_labels_are_removed_and_the_score_added(self, tmp_path):
        script = _step("impl-review.yml", QUALITY_STEP)["run"]
        # The fake answers `--jq` reads with the raw label list; the step's
        # jq filter is gh's job, so only the calls matter here.
        result, calls = _run(script, tmp_path, tmp_path, GH_LABELS="quality:73", **self.ENV)
        assert result.returncode == 0, result.stdout + result.stderr
        assert ["pr", "edit", "7", "--remove-label", "quality:73"] in calls
        assert ["pr", "edit", "7", "--add-label", "quality:86"] in calls

    def test_label_creation_is_idempotent_and_retried(self, tmp_path):
        script = _step("impl-review.yml", QUALITY_STEP)["run"]
        result, calls = _run(script, tmp_path, tmp_path, GH_LABEL_CREATE_RC="1", **self.ENV)
        creates = _calls(calls, "label", "create")
        assert len(creates) == 4
        assert all(c[2:4] == ["quality:86", "--force"] for c in creates)
        # A creation that never lands does not gate by itself: the add decides.
        assert result.returncode == 0, result.stdout + result.stderr
        assert ["pr", "edit", "7", "--add-label", "quality:86"] in calls

    def test_unreadable_labels_fail_the_step(self, tmp_path):
        result, calls = _run(
            _step("impl-review.yml", QUALITY_STEP)["run"], tmp_path, tmp_path, GH_FAIL_VIEW="1", **self.ENV
        )
        assert result.returncode == 1
        assert len(_calls(calls, "pr", "view")) == 4
        assert not _calls(calls, "pr", "edit")


def test_watchdog_case5_treats_a_lone_quality_label_as_a_marker():
    """Scored, no verdict, no ai-review-failed: only Case 5 can pick the PR up."""
    script = _step("watchdog-stuck-jobs.yml", "Scan and dispatch")["run"]
    case5 = script[script.index("# Case 5") :]
    assert "grep -vE '^(watchdog:|regen$|regen:forced$|quality:[0-9]+$)'" in case5


# ---------------------------------------------------------------------------
# Gap 2: impl-generate's auto-retry keeps the dispatching ref
# ---------------------------------------------------------------------------


class TestGenerateRetryRef:
    def test_retry_dispatches_on_the_trigger_ref(self):
        step = _step("impl-generate.yml", "Handle generation failure")
        assert step["env"]["TRIGGER_REF"] == "${{ github.ref_name }}"
        script = step["run"]
        body = script[script.index("dispatch_retry() {") :]
        assert body.index('gh workflow run impl-generate.yml --ref "${TRIGGER_REF:-main}"') < body.index("\n}")

    def test_the_handler_dispatches_only_through_dispatch_retry(self):
        # Manual-retry hints inside comment bodies are indented deeper and are
        # for humans; the only executed dispatch is dispatch_retry's.
        code = _code_only(_step("impl-generate.yml", "Handle generation failure")["run"])
        executed = [line for line in code.splitlines() if line.startswith("  gh workflow run impl-generate.yml")]
        assert executed == ['  gh workflow run impl-generate.yml --ref "${TRIGGER_REF:-main}" \\']


# ---------------------------------------------------------------------------
# Gap 3: repair exhaustion never writes to main
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("workflow", sorted(p.name for p in WORKFLOWS_DIR.glob("impl-*.yml")))
def test_no_impl_workflow_pushes_to_main(workflow):
    for step in _steps(workflow):
        code = _code_only(step.get("run", ""))
        assert "git push origin main" not in code, (workflow, step.get("name"))
        assert "git push origin HEAD:main" not in code, (workflow, step.get("name"))


def _origin_with(tmp_path: Path, files: tuple[str, ...]) -> Path:
    """A workspace clone whose origin/main holds `files`."""
    env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}

    def git(cwd: Path, *args: str) -> None:
        subprocess.run(["git", *args], cwd=cwd, env=env, check=True, capture_output=True)

    seed = tmp_path / "seed"
    seed.mkdir()
    git(seed, "init", "-q", "-b", "main")
    (seed / "README").write_text("x\n", encoding="utf-8")
    for rel in files:
        (seed / rel).parent.mkdir(parents=True, exist_ok=True)
        (seed / rel).write_text("# impl\n", encoding="utf-8")
    git(seed, "add", "-A")
    git(seed, "-c", "user.name=t", "-c", "user.email=t@x.invalid", "-c", "commit.gpgsign=false", "commit", "-qm", "s")
    git(tmp_path, "clone", "-q", "--bare", str(seed), "origin.git")
    work = tmp_path / "work"
    git(tmp_path, "clone", "-q", str(tmp_path / "origin.git"), "work")
    return work


class TestRepairExhaustion:
    IMPL = "plots/spec-a/implementations/python/plotly.py"
    ENV = {
        "PR_NUM": "7",
        "SPEC_ID": "spec-a",
        "LIBRARY": "plotly",
        "LANGUAGE": "python",
        "EXT": ".py",
        "SCORE": "41",
        "ATTEMPT": "5",
        "ATTEMPT_COUNT": "4",
        "ISSUE_NUMBER": "42",
        "REPOSITORY": "owner/repo",
        "RUN_ID": "1",
        "MODEL": "opus",
        "IS_REGEN": "false",
        "GH_LABELS": "ai-rejected quality:41 ai-attempt-4",
        "GH_ISSUE_LABELS": "generate:plotly impl:plotly:pending impl:plotly:failed watchdog:retried-plotly",
    }

    def _exhaust(self, tmp_path: Path, files: tuple[str, ...], **env: str):
        work = _origin_with(tmp_path, files)
        head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=work, capture_output=True, text=True).stdout
        result, calls = _run(_step("impl-review.yml", VERDICT_STEP)["run"], work, tmp_path, **{**self.ENV, **env})
        after = subprocess.run(["git", "rev-parse", "HEAD"], cwd=work, capture_output=True, text=True).stdout
        assert after == head, "the exhaustion path must never commit"
        assert (work / self.IMPL).exists() == (self.IMPL in files)
        return result, calls

    def test_forced_regen_keeps_the_live_implementation(self, tmp_path):
        result, calls = self._exhaust(tmp_path, (self.IMPL,))
        assert result.returncode == 0, result.stdout + result.stderr
        assert "Implementation live on main: true" in result.stdout
        assert ["pr", "close", "7"] in calls
        assert ["issue", "edit", "42", "--add-label", "impl:plotly:done"] in calls
        assert ["issue", "edit", "42", "--add-label", "impl:plotly:failed"] not in calls
        assert ["issue", "edit", "42", "--remove-label", "impl:plotly:failed"] in calls
        assert ["issue", "edit", "42", "--remove-label", "watchdog:retried-plotly"] in calls
        (comment,) = _calls(calls, "pr", "comment")
        assert comment[-2] == "--body-file"
        assert "stays live" in Path(comment[-1]).read_text(encoding="utf-8")

    def test_forced_regen_may_complete_the_issue(self):
        script = _step("impl-review.yml", VERDICT_STEP)["run"]
        branch = script[script.index("All 4 repair attempts exhausted") :]
        assert '"$RUNNER_TEMP/regen-tools/close_issue_if_complete.py"' in branch

    def test_a_failed_comment_never_stops_the_bookkeeping(self, tmp_path):
        result, calls = self._exhaust(tmp_path, (), GH_COMMENT_RC="1")
        assert result.returncode == 1  # red, but only after everything else ran
        assert ["pr", "close", "7"] in calls
        assert ["issue", "edit", "42", "--add-label", "impl:plotly:failed"] in calls

    def test_fresh_pair_is_marked_failed(self, tmp_path):
        result, calls = self._exhaust(tmp_path, ())
        assert result.returncode == 0, result.stdout + result.stderr
        assert "Implementation live on main: false" in result.stdout
        assert ["issue", "edit", "42", "--add-label", "impl:plotly:failed"] in calls
        assert ["issue", "edit", "42", "--remove-label", "impl:plotly:pending"] in calls
        assert not any("impl:plotly:done" in c for c in calls)

    def test_fresh_pair_keeps_a_failed_label_it_did_not_ask_to_drop(self, tmp_path):
        _, calls = self._exhaust(tmp_path, ())
        removed = [c[-1] for c in calls if c[:2] == ["issue", "edit"] and "--remove-label" in c]
        assert removed == ["generate:plotly", "impl:plotly:pending"]

    def test_absent_stale_labels_are_not_removed(self, tmp_path):
        result, calls = self._exhaust(tmp_path, (), GH_ISSUE_LABELS="impl:plotly:pending")
        assert result.returncode == 0, result.stdout + result.stderr
        removed = [c[-1] for c in calls if c[:2] == ["issue", "edit"] and "--remove-label" in c]
        assert removed == ["impl:plotly:pending"]

    def test_a_failed_stale_label_removal_is_retried_and_ends_red(self, tmp_path):
        result, calls = self._exhaust(tmp_path, (), GH_FAIL_REMOVE="1")
        assert result.returncode == 1
        for label in ("generate:plotly", "impl:plotly:pending"):
            assert calls.count(["issue", "edit", "42", "--remove-label", label]) == 3
        # ... and only after the rest of the bookkeeping ran.
        assert ["issue", "edit", "42", "--add-label", "impl:plotly:failed"] in calls
        assert len(_calls(calls, "issue", "comment")) == 1

    def test_unreadable_issue_labels_end_red_after_a_blind_removal(self, tmp_path):
        result, calls = self._exhaust(tmp_path, (), GH_FAIL_ISSUE_VIEW="1")
        assert result.returncode == 1
        assert len(_calls(calls, "issue", "view")) == 3
        assert ["issue", "edit", "42", "--remove-label", "generate:plotly"] in calls
        assert ["issue", "edit", "42", "--remove-label", "impl:plotly:pending"] in calls
        assert len(_calls(calls, "issue", "comment")) == 1

    def test_pr_is_closed_before_the_issue_bookkeeping(self, tmp_path):
        _, calls = self._exhaust(tmp_path, ())
        kinds = [" ".join(c[:2]) for c in calls]
        assert kinds.index("pr close") < kinds.index("issue edit")

    def test_unreadable_main_sets_no_terminal_label_and_ends_red(self, tmp_path):
        work = _origin_with(tmp_path, ())
        subprocess.run(["git", "remote", "set-url", "origin", str(tmp_path / "gone.git")], cwd=work, check=True)
        result, calls = _run(_step("impl-review.yml", VERDICT_STEP)["run"], work, tmp_path, **self.ENV)
        assert result.returncode == 1, result.stdout + result.stderr
        assert "Implementation live on main: unknown" in result.stdout
        assert ["pr", "close", "7"] in calls
        assert not any(
            label in c for c in calls for label in ("impl:plotly:failed", "impl:plotly:done") if "--add-label" in c
        )
        assert len(_calls(calls, "issue", "comment")) == 1
