"""Step scripts give the same answer however the machine is loaded, and however many run at once.

Two ways the workflow tests, which run step scripts for real under
pytest-xdist, used to fail now and then on an unrelated change:

1. A label check of the form `echo "$LABELS" | grep -q "ai-approved"` can come
   back false although the label is there. Bash's `echo` writes a multi-line
   value one line per write(2) (a ptrace trace shows two calls for
   "ai-approved\\nquality:88": 12 bytes, then 11). `grep -q` stops at its first
   match and closes the pipe, so the second write can hit a closed pipe; `echo`
   dies of SIGPIPE, and under `pipefail` the pipeline's status is 141 instead
   of grep's 0. The tests run steps under `bash -eo pipefail`, so the verdict
   step fell through to "neither ai-approved nor ai-rejected" (CI run
   42620555017). Actions runs these steps with `bash -e`, where the pipeline's
   status is grep's, so a live run never lost a match; the check is written so
   that it cannot under either shell: `grep -q "ai-approved" <<< "$LABELS"`
   hands grep the same bytes with no writer that can be killed. A label list
   joined with spaces (`echo " $labels " | grep -q " x "`) is one line, so one
   write, and is safe as it is.
2. Steps kept scratch files under fixed `/tmp` paths, which every test on the
   machine shares; a regen gate summary left by one test was then posted by
   another. The gate's record and summary and the verdict step's scratch files
   now live in `$RUNNER_TEMP`, which the test helper gives each test on its
   own. The files the reviewer reads stay in `/tmp` (its Read tool is allowed
   there only), and the tests that run those steps move them per test.
"""

from __future__ import annotations

import json
import re
import shutil
from pathlib import Path

import pytest
import yaml

from tests.unit.workflows.test_pipeline_retry_gaps import _calls, _code_only, _run, _step


REPO_ROOT = Path(__file__).parent.parent.parent.parent
TOOLS = REPO_ROOT / "automation" / "scripts"
WORKFLOW_FILES = sorted((REPO_ROOT / ".github" / "workflows").glob("*.yml")) + sorted(
    (REPO_ROOT / ".github" / "actions").glob("*/action.yml")
)
VERDICT = "Add verdict label and take action"
GATE = "Regen gate"
STAGE = "Stage regen pair"
RECORD = "$RUNNER_TEMP/anyplot-regen-record.json"
SUMMARY = "$RUNNER_TEMP/anyplot-regen-summary.md"

# `echo`/`printf` of one quoted variable (`"$X"`, `"${X}"`, `"${X:-}"`), piped straight into a quiet grep.
ECHO_INTO_GREP_Q = re.compile(
    r'\b(?:echo|printf)\b[^|\n]*"\$(?:\w+|\{[^}"\n]+\})"[^|\n]*\|\s*grep\b(?:\s+-[\w-]+)*?\s+(?:-\w*q\w*|--quiet|--silent)\b'
)


def _racy_lines(text: str) -> list[tuple[int, str]]:
    """(first line number, command) of each racy pipeline; a trailing backslash joins the next line."""
    hits: list[tuple[int, str]] = []
    parts: list[str] = []
    start = 0
    for number, line in enumerate(text.splitlines(), start=1):
        if not parts and line.lstrip().startswith("#"):
            continue  # a comment ends at its newline, backslash or not
        if not parts:
            start = number
        if line.rstrip().endswith("\\"):
            parts.append(line.rstrip()[:-1])
            continue
        command = " ".join([*parts, line])
        parts = []
        if ECHO_INTO_GREP_Q.search(command):
            hits.append((start, command.strip()))
    return hits


@pytest.mark.parametrize(
    ("text", "flagged"),
    [
        ('if echo "$CURRENT_LABELS" | grep -q "ai-approved"; then', True),
        ('elif echo "${PRESENT}" | grep -qxF "$stale"; then', True),
        ('if echo "${LABELS:-}" | grep -q spec-ready; then', True),
        ("printf '%s\\n' \"$LABELS\" | grep -q spec-ready", True),
        ('echo "$X" | grep -x -q y', True),
        ('if echo "$LABELS" | \\\n     grep -q "ai-approved"; then', True),
        ('# echo "$LABELS" | grep -q "ai-approved" was racy', False),
        ('if grep -q "ai-approved" <<< "$CURRENT_LABELS"; then', False),
        ('if echo " $labels " | grep -q " regen:kept "; then', False),
        ('echo "$X" | grep -c y', False),
        ("gh pr view 7 --json labels -q '.labels[].name' | grep -qxF ai-review-paused", False),
    ],
)
def test_the_guard_flags_exactly_the_racy_form(text, flagged):
    assert bool(_racy_lines(text)) is flagged


@pytest.mark.parametrize(
    "path", WORKFLOW_FILES, ids=lambda p: p.name if p.parent.name == "workflows" else p.parent.name
)
def test_no_step_pipes_a_variable_into_a_quiet_grep(path):
    hits = [f"{path.name}:{number}: {command}" for number, command in _racy_lines(path.read_text(encoding="utf-8"))]
    assert not hits, 'use `grep -q PATTERN <<< "$VAR"` instead:\n' + "\n".join(hits)


def test_the_gate_files_are_written_copied_and_read_in_one_job():
    workflow = yaml.safe_load((REPO_ROOT / ".github" / "workflows" / "impl-review.yml").read_text(encoding="utf-8"))
    jobs = {name: [s.get("name") for s in job.get("steps", [])] for name, job in workflow["jobs"].items()}
    (job,) = [name for name, steps in jobs.items() if VERDICT in steps]
    assert GATE in jobs[job] and STAGE in jobs[job]

    gate = _step("impl-review.yml", GATE)["run"]
    assert f'RECORD="{RECORD}"' in gate
    assert f'--summary-out "{SUMMARY}"' in gate
    assert f'> "{SUMMARY}"' in gate  # the crash fallback
    stage = _step("impl-review.yml", STAGE)["run"]
    assert f'cp "{RECORD}" "$DIR/gate-record.json"' in stage
    assert f'cp "{SUMMARY}" "$DIR/gate-summary.md"' in stage
    verdict = _step("impl-review.yml", VERDICT)["run"]
    assert f'SUMMARY_FILE="{SUMMARY}"' in verdict
    assert f'--record "{RECORD}"' in verdict
    assert "/tmp/" not in _code_only(verdict)


class TestKeptRegenUsesItsOwnFiles:
    """The kept-regen comment carries this run's gate summary and record, never another run's."""

    ENV = {
        "PR_NUM": "7",
        "SPEC_ID": "spec-a",
        "LIBRARY": "plotly",
        "LANGUAGE": "python",
        "EXT": ".py",
        "SCORE": "85",
        "ATTEMPT": "1",
        "ATTEMPT_COUNT": "0",
        "ISSUE_NUMBER": "",
        "REPOSITORY": "owner/repo",
        "RUN_ID": "1",
        "MODEL": "sonnet",
        "IS_REGEN": "true",
        "GATE_VERDICT": "keep",
        "GATE_CODE": "script_crashed",
        "PREV_STORED": "94",
        "MODEL_ID": "n/a",
        "WB_STATUS": "unchanged",
        "REVIEW_SKIPPED": "",
    }
    GATE_RECORD = {
        "v": 1,
        "pr": 7,
        "spec": "spec-a",
        "lib": "plotly",
        "model": "n/a",
        "criteria_version": "n/a",
        "verdict": "keep",
        "code": "script_crashed",
        "at": "2026-11-09T00:00:00Z",
    }

    @staticmethod
    def _runner(tmp_path: Path, name: str) -> Path:
        runner = tmp_path / name
        (runner / "regen-tools").mkdir(parents=True)
        shutil.copyfile(TOOLS / "regen_gate.py", runner / "regen-tools" / "regen_gate.py")
        return runner

    def _kept_comment(self, tmp_path: Path, runner: Path, **env: str) -> str:
        result, calls = _run(
            _step("impl-review.yml", VERDICT)["run"],
            tmp_path,
            tmp_path,
            **{**self.ENV, "RUNNER_TEMP": str(runner), **env},
        )
        assert result.returncode == 0, result.stdout + result.stderr
        assert ["pr", "close", "7", "--delete-branch"] in calls
        (comment,) = _calls(calls, "pr", "comment")
        return Path(comment[comment.index("--body-file") + 1]).read_text(encoding="utf-8")

    def test_the_comment_carries_this_runs_summary_and_record(self, tmp_path):
        runner = self._runner(tmp_path, "runner")
        (runner / "anyplot-regen-summary.md").write_text("**Reason:** this run's gate summary\n", encoding="utf-8")
        (runner / "anyplot-regen-record.json").write_text(json.dumps(self.GATE_RECORD), encoding="utf-8")
        body = self._kept_comment(tmp_path, runner)
        assert "**Reason:** this run's gate summary" in body
        (marker,) = [line for line in body.splitlines() if line.startswith("<!-- regen-gate-record:v1 ")]
        record = json.loads(marker.removeprefix("<!-- regen-gate-record:v1 ").removesuffix(" -->"))
        assert record == {**self.GATE_RECORD, "writeback": "unchanged"}

    def test_nothing_left_by_an_earlier_run_is_reused(self, tmp_path):
        first = self._runner(tmp_path, "first")
        (first / "anyplot-regen-record.json").write_text(json.dumps(self.GATE_RECORD), encoding="utf-8")
        body = self._kept_comment(tmp_path, first, GATE_REASON="the first run's reason")
        assert "**Reason:** the first run's reason" in body
        assert "regen-gate-record:v1" in body

        # A second run on the same machine: no gate summary and no record of its own.
        body = self._kept_comment(tmp_path, self._runner(tmp_path, "second"), GATE_REASON="the second run's reason")
        assert "**Reason:** the second run's reason" in body
        assert "the first run's reason" not in body
        assert "regen-gate-record:v1" not in body
