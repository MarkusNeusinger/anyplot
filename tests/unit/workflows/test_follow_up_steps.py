"""The workflow side of follow-up regenerations (docs/workflows/overview.md).

impl-merge dispatches a repair round after a merge, impl-review a retry after
a keep for a regression, and impl-generate carries the mark into the
follow-up's PR body. Nothing here runs in a pull request before it merges
(claude-code-action refuses changed workflows), so these tests pin the wiring
and run both dispatch steps under bash with a stub ``gh`` that answers from a
JSON state file. The script's own decisions are tested in
tests/unit/automation/scripts/test_regen_follow_up.py.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import pytest
import yaml

from automation.scripts import regen_follow_up as fu
from automation.scripts import regen_gate as gate
from tests.unit.workflows.test_pipeline_retry_gaps import _code_only, _step, _steps
from tests.unit.workflows.test_render_hash_steps import SHELL_IDS, SHELLS


ROOT = Path(__file__).resolve().parents[3]
WORKFLOWS = ROOT / ".github" / "workflows"
SCRIPTS = ROOT / "automation" / "scripts"
MERGE_STEP = "Dispatch a follow-up regeneration (repair round)"
RETRY_STEP = "Dispatch a follow-up regeneration (retry)"
BOT = "github-actions[bot]"
HEAD = "implementation/bar-basic/altair"

# Answers from $GH_STATE: `pr list` (pulls), `pr view N --json state` (wb_state),
# `pr view` (view), `api …/issues/N/comments` (comments[N]), `pr comment`
# (comment_rc), `workflow run` (dispatch_rc). Logs every call as one JSON line.
FAKE_GH = """\
import json, os, sys
args = sys.argv[1:]
with open(os.environ["GH_LOG"], "a", encoding="utf-8") as log:
    log.write(json.dumps(args) + "\\n")
state = json.load(open(os.environ["GH_STATE"], encoding="utf-8"))
def out(text):
    sys.stdout.write(text)
    sys.exit(0)
if args[:2] == ["pr", "list"]:
    out(json.dumps(state["pulls"]))
if args[:2] == ["pr", "view"]:
    if args[args.index("--json") + 1] == "state":
        out(state.get("wb_state", "MERGED") + "\\n")
    out(json.dumps(state["view"]))
if args[0] == "api":
    number = args[2].split("/")[-2]
    out("".join(json.dumps(c) + "\\n" for c in state["comments"].get(number, [])))
if args[:2] == ["pr", "comment"]:
    sys.exit(state.get("comment_rc", 0))
if args[:2] == ["workflow", "run"]:
    sys.exit(state.get("dispatch_rc", 0))
sys.exit(0)
"""


def _workflow(name: str) -> dict[str, Any]:
    return yaml.safe_load((WORKFLOWS / name).read_text(encoding="utf-8"))


@pytest.mark.parametrize("name", ["impl-generate.yml", "impl-review.yml", "impl-merge.yml"])
def test_the_changed_workflows_load(name):
    workflow = _workflow(name)
    assert workflow["jobs"]


# --- impl-generate ---------------------------------------------------------------


class TestImplGenerate:
    def test_the_inputs_exist_and_stay_within_githubs_limit(self):
        inputs = _workflow("impl-generate.yml")[True]["workflow_dispatch"]["inputs"]
        assert inputs["follow_up"]["default"] == "" and inputs["follow_up_note"]["default"] == ""
        assert len(inputs) <= 10  # the classic workflow_dispatch limit

    def test_the_input_is_checked_before_use(self):
        script = _step("impl-generate.yml", "Extract inputs")["run"]
        assert '[[ "$FOLLOW_UP_INPUT" =~ ^(repair|retry):([1-9][0-9]{0,9})$ ]] || bad_input follow_up' in script
        assert 'echo "follow_up_kind=$FOLLOW_UP_KIND" >> $GITHUB_OUTPUT' in script

    def test_the_body_line_is_the_one_the_dispatcher_reads(self):
        script = _step("impl-generate.yml", "Create Pull Request")["run"]
        line = "**Follow-up of:** #${FOLLOW_UP_OF} (${FOLLOW_UP_KIND})"
        assert line in script
        for kind in gate.FOLLOW_UP_KINDS:
            rendered = line.replace("${FOLLOW_UP_OF}", "14231").replace("${FOLLOW_UP_KIND}", kind)
            assert fu.body_follow_up(f"**Model:** sonnet\n{rendered}\n") == (14231, kind)

    def test_the_note_never_becomes_a_change_request(self):
        script = _code_only(_step("impl-generate.yml", "Create Pull Request")["run"])
        assert "**Regression note:** ${NOTE_LINE}" in script
        assert "**Change request:** ${NOTE" not in script
        staged = _step("impl-generate.yml", "Stage the follow-up note (retry)")
        assert "/tmp/anyplot-follow-up-note.txt" in staged["run"]
        assert "anyplot-change-request" not in staged["run"]
        prompt = (ROOT / "prompts" / "workflow-prompts" / "impl-generate-claude.md").read_text(encoding="utf-8")
        assert "/tmp/anyplot-follow-up-note.txt" in prompt

    def test_the_crash_retry_forwards_the_mark(self):
        step = _step("impl-generate.yml", "Handle generation failure")
        assert step["env"]["FOLLOW_UP"] == "${{ inputs.follow_up }}"
        assert step["env"]["FOLLOW_UP_NOTE"] == "${{ inputs.follow_up_note }}"
        retry = step["run"][step["run"].index("dispatch_retry() {") :]
        retry = retry[: retry.index("\n}")]
        assert '-f follow_up="${FOLLOW_UP}"' in retry
        assert '-f follow_up_note="${FOLLOW_UP_NOTE}"' in retry


# --- impl-review -----------------------------------------------------------------


class TestImplReviewWiring:
    def test_the_tools_include_the_dispatcher(self):
        assert "automation/scripts/regen_follow_up.py" in _step("impl-review.yml", "Checkout PR code")["run"]

    def test_regen_context_reads_the_body_line_without_failing_the_step(self):
        script = _step("impl-review.yml", "Regen context")["run"]
        assert 'regen_follow_up.py" parse-body < "$PR_BODY" \\\n' in script
        assert "|| echo \"::warning::the PR body's follow-up line could not be read" in script
        assert 'PR_BODY="$RUNNER_TEMP/' in script  # never under /tmp, where the reviewer reads

    def test_the_gate_records_the_predecessor(self):
        step = _step("impl-review.yml", "Regen gate")
        assert step["env"]["FOLLOW_UP_OF"] == "${{ steps.regen_ctx.outputs.follow_up_of }}"
        assert 'FLAGS+=(--follow-up-of "$FOLLOW_UP_OF" --follow-up-kind "$FOLLOW_UP_KIND")' in step["run"]

    def test_a_repair_round_never_writes_back_and_a_retry_does(self):
        """A retry heals a write-back the kept attempt lost; a repair round keeps the winner's review."""
        step = _step("impl-review.yml", "Write back the re-score (regen keep)")
        assert step["if"].endswith("&& steps.regen_ctx.outputs.follow_up_kind != 'repair'")
        verdict = _step("impl-review.yml", "Add verdict label and take action")
        assert verdict["env"]["FOLLOW_UP_KIND"] == "${{ steps.regen_ctx.outputs.follow_up_kind }}"
        assert '[ "$FOLLOW_UP_KIND" = "repair" ] && WB_STATUS=follow_up' in verdict["run"]
        assert "opened|unchanged|no_rescore|invalid|stale|failed|follow_up) ;;" in verdict["run"]
        assert "follow_up" in gate.WRITEBACK_CODES

    def test_the_retry_step_is_last_switched_and_never_fails_the_run(self):
        steps = _steps("impl-review.yml")
        assert steps[-1]["name"] == RETRY_STEP
        step = steps[-1]
        assert step["if"].startswith("vars.REGEN_RETRY == 'true' && ")
        for part in ("steps.gate.outputs.verdict == 'keep'", "steps.gate.outputs.follow_up_trigger == 'retry'"):
            assert part in step["if"]
        assert "always()" not in step["if"]  # after a failed keep bookkeeping, no retry
        assert step["continue-on-error"] is True

    def test_the_retry_waits_for_the_write_back_then_marks_then_dispatches(self):
        script = _code_only(_step("impl-review.yml", RETRY_STEP)["run"])
        order = [
            'if [ "$WB_STATUS" = "opened" ]; then',
            'regen_follow_up.py" plan --kind retry',
            'regen_gate.py" retry-note',
            'gh pr comment "$PR_NUM" --body-file',
            "gh workflow run impl-generate.yml",
        ]
        positions = [script.index(part) for part in order]
        assert positions == sorted(positions)
        assert '-f follow_up="retry:${PR_NUM}" -f follow_up_note="$NOTE"' in script
        assert '-f change_request="$CR"' in script
        assert '-f change_request="$NOTE"' not in script


# --- impl-merge ------------------------------------------------------------------


class TestImplMergeWiring:
    def test_the_steps_end_the_merge_job_after_the_sync(self):
        names = [s.get("name") for s in _workflow("impl-merge.yml")["jobs"]["merge"]["steps"]]
        assert names[-3:] == ["Trigger database sync", "Set up Python (follow-up)", MERGE_STEP]

    def test_switched_after_a_promotion_and_never_fails_the_run(self):
        step = _step("impl-merge.yml", MERGE_STEP)
        python = _step("impl-merge.yml", "Set up Python (follow-up)")
        assert step["if"] == python["if"]
        for part in ("vars.REGEN_REPAIR_ROUND == 'true'", "steps.promote.outcome == 'success'"):
            assert part in step["if"]
        assert step["continue-on-error"] is True

    def test_the_tools_come_from_the_workflows_own_commit(self):
        step = _step("impl-merge.yml", MERGE_STEP)
        assert step["env"]["TOOLS_REF"] == "${{ github.event_name == 'pull_request' && 'origin/main' || github.sha }}"

    def test_marks_then_dispatches_without_a_change_request(self):
        script = _code_only(_step("impl-merge.yml", MERGE_STEP)["run"])
        assert script.index("plan --kind repair") < script.index("gh pr comment") < script.index("gh workflow run")
        assert '-f follow_up="repair:${PR_NUM}" -f follow_up_note=' in script
        assert "-f change_request= " in script


# --- the dispatch steps, run ----------------------------------------------------


def _bin(tmp_path: Path) -> str:
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir(exist_ok=True)
    gh = bin_dir / "gh"
    gh.write_text(f"#!{sys.executable}\n" + FAKE_GH, encoding="utf-8")
    gh.chmod(0o755)
    (bin_dir / "sleep").write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    (bin_dir / "sleep").chmod(0o755)
    # The regen tools need the repository's Python (PEP 758 syntax).
    (bin_dir / "python3").symlink_to(sys.executable)
    return f"{bin_dir}{os.pathsep}{os.environ['PATH']}"


def _record(**overrides: Any) -> dict[str, Any]:
    record = {"v": 1, "pr": 14000, "spec": "bar-basic", "lib": "altair", "verdict": "merge", "code": "merge"}
    record.update({"defect_lines": 2, "follow_up_trigger": "repair", **overrides})
    return record


def _state(record: dict[str, Any], **overrides: Any) -> dict[str, Any]:
    comment = {"login": BOT, "body": gate.render_record_marker(record), "created_at": _ago(hours=1)}
    state = {
        "pulls": [{"number": 14000, "createdAt": _ago(hours=2), "body": ""}],
        "view": {"number": 14000, "body": "**Model:** sonnet", "headRefName": HEAD},
        "comments": {"14000": [comment]},
    }
    state.update(overrides)
    return state


@pytest.fixture(params=SHELLS, ids=SHELL_IDS)
def shell(request: pytest.FixtureRequest) -> list[str]:
    """What Actions runs a step with (plain ``bash -e``), and the stricter pipefail."""
    return request.param


def _ago(**delta: float) -> str:
    """A creation time relative to now: the plan's window reads the real clock."""
    return (datetime.now(timezone.utc) - timedelta(**delta)).strftime("%Y-%m-%dT%H:%M:%SZ")


def _run(tmp_path: Path, step: dict[str, Any], state: dict[str, Any], cwd: Path, shell: list[str], **env: str):
    (tmp_path / "state.json").write_text(json.dumps(state), encoding="utf-8")
    log = tmp_path / "gh_log"
    log.unlink(missing_ok=True)
    for name in ("output", "summary"):
        (tmp_path / name).write_text("", encoding="utf-8")
    base = {k: v for k, v in os.environ.items() if not k.startswith(("GIT_", "GH_", "GITHUB_"))}
    result = subprocess.run(
        [*shell, step["run"]],
        cwd=cwd,
        env={
            **base,
            "PATH": _bin(tmp_path),
            "GH_LOG": str(log),
            "GH_STATE": str(tmp_path / "state.json"),
            "GH_TOKEN": "unused",
            "GITHUB_OUTPUT": str(tmp_path / "output"),
            "GITHUB_STEP_SUMMARY": str(tmp_path / "summary"),
            "RUNNER_TEMP": str(tmp_path / "runner"),
            "REPOSITORY": "owner/repo",
            "PR_NUM": "14000",
            "SPEC_ID": "bar-basic",
            "LIBRARY": "altair",
            **env,
        },
        capture_output=True,
        text=True,
    )
    calls = [json.loads(line) for line in log.read_text(encoding="utf-8").splitlines()] if log.exists() else []
    outputs = dict(line.split("=", 1) for line in (tmp_path / "output").read_text().splitlines() if "=" in line)
    return result, calls, outputs


def _writes(calls: list[list[str]]) -> list[list[str]]:
    return [c for c in calls if c[:2] in (["pr", "comment"], ["workflow", "run"])]


def _fields(call: list[str]) -> dict[str, str]:
    return dict(call[i + 1].split("=", 1) for i, arg in enumerate(call) if arg == "-f")


class TestRetryStepRun:
    @pytest.fixture
    def workspace(self, tmp_path: Path) -> Path:
        tools = tmp_path / "runner" / "regen-tools"
        tools.mkdir(parents=True)
        for name in ("regen_gate.py", "regen_follow_up.py"):
            shutil.copy(SCRIPTS / name, tools / name)
        ws = tmp_path / "ws"
        ws.mkdir()
        regen = {
            "prev_rescored": 85,
            "prev_checklist": {},
            "prev_weaknesses": [],
            "improvements": [],
            "regressions": [{"what": "lost the viridis ramp", "where_visible": "heatmap cells"}],
            "scenario_changed": False,
            "encodings_added": [],
            "change_request_applied": None,
        }
        (ws / "review_regen.json").write_text(json.dumps(regen), encoding="utf-8")
        return ws

    def _keep(self) -> dict[str, Any]:
        return _record(verdict="keep", code="regression", defect_lines=0, follow_up_trigger="retry")

    def _go(self, tmp_path, workspace, state, shell, **env):
        step = _step("impl-review.yml", RETRY_STEP)
        defaults = {"ISSUE_NUMBER": "900", "MODEL": "sonnet", "WB_STATUS": "opened", "WB_PR": "14001"}
        defaults.update({"CHANGE_REQUEST_PRESENT": "false", "WORKFLOW_REF": "main", "WAIT_ROUNDS": "2"})
        defaults.update({"WAIT_SECONDS": "0", **env})
        return _run(tmp_path, step, state, workspace, shell, **defaults)

    def test_marks_then_dispatches_with_the_note(self, tmp_path, workspace, shell):
        result, calls, outputs = self._go(tmp_path, workspace, _state(self._keep()), shell)
        assert result.returncode == 0, result.stderr
        comment, dispatch = _writes(calls)
        assert comment[:3] == ["pr", "comment", "14000"]
        assert fu.has_marker([{"login": BOT, "body": (tmp_path / "runner" / "follow-up-marker.md").read_text()}])
        fields = _fields(dispatch)
        assert fields["follow_up"] == "retry:14000"
        assert fields["regen_gate"] == "true"
        assert fields["model"] == "sonnet"
        assert "lost the viridis ramp (heatmap cells)" in fields["follow_up_note"]
        assert "viridis" not in fields["change_request"]
        assert outputs["reason"] == "dispatch"

    def test_an_open_write_back_means_no_retry(self, tmp_path, workspace, shell):
        result, calls, outputs = self._go(tmp_path, workspace, _state(self._keep(), wb_state="OPEN"), shell)
        assert result.returncode == 0, result.stderr
        assert _writes(calls) == []
        assert outputs["reason"] == "writeback_pending"
        assert not any(c[:2] == ["pr", "list"] for c in calls)

    def test_a_marked_pr_gets_no_second_retry(self, tmp_path, workspace, shell):
        state = _state(self._keep())
        marker = {"login": BOT, "body": fu.render_marker("retry", 14000, "bar-basic", "altair"), "created_at": "x"}
        state["comments"]["14000"].append(marker)
        result, calls, outputs = self._go(tmp_path, workspace, state, shell, WB_STATUS="unchanged")
        assert result.returncode == 0, result.stderr
        assert _writes(calls) == []
        assert outputs["reason"] == "already"

    def test_a_lost_marker_never_dispatches(self, tmp_path, workspace, shell):
        result, calls, outputs = self._go(tmp_path, workspace, _state(self._keep(), comment_rc=1), shell)
        assert result.returncode == 0, result.stderr
        assert [c[:2] for c in _writes(calls)] == [["pr", "comment"]] * 3
        assert outputs["reason"] == "marker_not_posted"

    def test_a_failed_dispatch_never_fails_the_run(self, tmp_path, workspace, shell):
        result, calls, outputs = self._go(tmp_path, workspace, _state(self._keep(), dispatch_rc=1), shell)
        assert result.returncode == 0, result.stderr
        assert outputs["reason"] == "dispatch_failed"
        assert "::warning::retry follow-up of PR #14000" in result.stdout


class TestRepairStepRun:
    @pytest.fixture
    def repo(self, tmp_path: Path) -> Path:
        """A repository whose HEAD holds the two tools, like the workflow's own commit."""
        repo = tmp_path / "repo"
        (repo / "automation" / "scripts").mkdir(parents=True)
        for name in ("regen_gate.py", "regen_follow_up.py"):
            shutil.copy(SCRIPTS / name, repo / "automation" / "scripts" / name)
        git = ["git", "-c", "user.name=t", "-c", "user.email=t@t", "-C", str(repo)]
        subprocess.run([*git[:-2], "init", "-q", str(repo)], check=True)
        subprocess.run([*git, "add", "."], check=True)
        subprocess.run([*git, "commit", "-q", "-m", "tools"], check=True)
        return repo

    def _go(self, tmp_path, repo, state, shell, **env):
        step = _step("impl-merge.yml", MERGE_STEP)
        defaults = {"ISSUE": "900", "MODEL": "", "TOOLS_REF": "HEAD", "WORKFLOW_REF": "main", **env}
        return _run(tmp_path, step, state, repo, shell, **defaults)

    def test_a_merge_with_defect_lines_dispatches_a_repair_round(self, tmp_path, repo, shell):
        result, calls, outputs = self._go(tmp_path, repo, _state(_record()), shell)
        assert result.returncode == 0, result.stderr
        comment, dispatch = _writes(calls)
        assert comment[:3] == ["pr", "comment", "14000"]
        fields = _fields(dispatch)
        assert (fields["follow_up"], fields["follow_up_note"], fields["change_request"]) == ("repair:14000", "", "")
        assert (fields["model"], fields["regen_gate"], fields["issue_number"]) == ("auto", "true", "900")
        assert outputs["reason"] == "dispatch"

    def test_the_winners_model_carries_over(self, tmp_path, repo, shell):
        """A pinned batch gets its repair rounds on the model it ran on."""
        result, calls, _ = self._go(tmp_path, repo, _state(_record()), shell, MODEL="opus")
        assert result.returncode == 0, result.stderr
        assert _fields(_writes(calls)[-1])["model"] == "opus"

    @pytest.mark.parametrize(
        ("record", "reason"),
        [
            (_record(code="adapt_identity"), "not_eligible"),
            (_record(defect_lines=0, follow_up_trigger="none"), "not_eligible"),
            (_record(follow_up_of=13990, follow_up_kind="retry", follow_up_trigger="none"), "is_follow_up"),
        ],
    )
    def test_no_repair_round_without_a_trigger(self, tmp_path, repo, record, reason, shell):
        result, calls, outputs = self._go(tmp_path, repo, _state(record), shell)
        assert result.returncode == 0, result.stderr
        assert _writes(calls) == []
        assert outputs["reason"] == reason

    def test_a_recent_follow_up_of_the_pair_refuses(self, tmp_path, repo, shell):
        state = _state(_record())
        state["pulls"].append({"number": 13990, "createdAt": _ago(days=1), "body": ""})
        marker = {"login": BOT, "body": fu.render_marker("repair", 13990, "bar-basic", "altair"), "created_at": "x"}
        state["comments"]["13990"] = [marker]
        result, calls, outputs = self._go(tmp_path, repo, state, shell)
        assert _writes(calls) == []
        assert outputs["reason"] == "recent_follow_up"

    def test_missing_tools_dispatch_nothing(self, tmp_path, repo, shell):
        result, calls, outputs = self._go(tmp_path, repo, _state(_record()), shell, TOOLS_REF="no-such-ref")
        assert result.returncode == 0, result.stderr
        assert calls == []
        assert outputs["reason"] == "tools_unavailable"
