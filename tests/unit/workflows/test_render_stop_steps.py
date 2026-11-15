"""What impl-review does after a render hash mismatch (rule P2b).

"Check the render hash" writes `stop=true` when the staged renders were made
from other code than the PR head holds (test_render_hash_steps.py). The step
"Stop on a render hash mismatch" then stops the review:

- A first generation gets the label `ai-render-mismatch` and stays open; no
  review, no score, no header commit. The watchdog rescues nothing that
  carries the label and reports it.
- A regeneration runs no review either; the regen gate keeps the live
  implementation (`render_mismatch`), and the keep path closes the PR.

These tests run the step scripts with a stub `gh`, and pin the `if:` wiring
that no local run reaches: which steps a stop switches off, and which three
the keep path switches on.
"""

from __future__ import annotations

import json
import re
import shutil
from pathlib import Path
from typing import Any

import pytest
import yaml

from automation.scripts import regen_gate, regen_pick_pairs, render_hash
from tests.unit.workflows.test_pipeline_retry_gaps import VERDICT_STEP, _calls, _code_only, _run, _step, _steps


ROOT = Path(__file__).resolve().parents[3]
TOOLS = ROOT / "automation" / "scripts"
WORKFLOWS = ROOT / ".github" / "workflows"
REVIEW = "impl-review.yml"
CHECK = "Check the render hash"
STOP = "Stop on a render hash mismatch"
CLEAR = "Clear the ai-render-mismatch label"
GATE = "Regen gate"
EARLY = "Add preliminary verdict label (early)"
RUN_REVIEW = "Run AI Quality Review"
STOPPED = "steps.render_stop.outputs.stopped != 'true'"
KEEP = "steps.render_stop.outputs.keep == 'true'"
# Between the stop and the regen gate: every step that reads the renders,
# prepares the review or runs it.
SWITCHED_OFF = [
    "Verify both theme renders exist",
    "Canvas dimension gate",
    "Adaptability check (record-only)",
    "Readiness check",
    "React with eyes emoji",
    "Hide the previous review",
    RUN_REVIEW,
]
# The keep path of a stopped regeneration. Nothing else: no step between them
# may be able to fail it.
SWITCHED_ON = [GATE, EARLY, VERDICT_STEP]
ENV = {"PR_NUM": "7", "SPEC_ID": "spec-a", "LIBRARY": "plotly"}


def _names() -> list[str]:
    return [str(s.get("name")) for s in _steps(REVIEW)]


def _stop(tmp_path: Path, **env: str):
    output, summary = tmp_path / "output", tmp_path / "summary"
    result, calls = _run(
        str(_step(REVIEW, STOP)["run"]),
        tmp_path,
        tmp_path,
        GITHUB_OUTPUT=str(output),
        GITHUB_STEP_SUMMARY=str(summary),
        **ENV,
        **env,
    )
    return result, calls, output.read_text(encoding="utf-8") if output.exists() else ""


class TestStopStep:
    def test_a_first_generation_gets_the_label_and_nothing_else(self, tmp_path):
        result, calls, output = _stop(tmp_path, IS_REGEN="false")
        assert result.returncode == 0, result.stdout + result.stderr
        assert output == "stopped=true\n"
        assert _calls(calls, "pr", "edit") == [["pr", "edit", "7", "--add-label", render_hash.STOP_LABEL]]
        (created,) = _calls(calls, "label", "create")
        assert created[2] == render_hash.STOP_LABEL
        # No comment (the check posted it), no close, no dispatch, and never the label the watchdog rescues.
        assert len(calls) == 2
        assert "ai-review-failed" not in _code_only(str(_step(REVIEW, STOP)["run"]))
        assert "::warning::render_stop spec=spec-a lib=plotly pr=7 regeneration=false" in result.stdout

    def test_a_regeneration_asks_for_the_keep_and_calls_nothing(self, tmp_path):
        result, calls, output = _stop(tmp_path, IS_REGEN="true")
        assert result.returncode == 0, result.stdout + result.stderr
        assert output == "stopped=true\nkeep=true\n"
        assert calls == []
        assert "regeneration=true" in result.stdout and "render_mismatch" in result.stdout

    def test_a_label_that_cannot_be_added_fails_the_job_after_the_stop_is_written(self, tmp_path):
        """The review must stay stopped whatever the API does, so the output comes first."""
        result, calls, output = _stop(tmp_path, IS_REGEN="false", GH_FAIL_ADD_LABEL=render_hash.STOP_LABEL)
        assert result.returncode == 1
        assert output == "stopped=true\n"
        assert len(_calls(calls, "pr", "edit")) == 3
        assert "::error::ai-render-mismatch could not be added to PR #7" in result.stdout

    def test_a_label_that_already_exists_is_fine(self, tmp_path):
        result, _, output = _stop(tmp_path, IS_REGEN="false", GH_LABEL_CREATE_RC="1")
        assert result.returncode == 0 and output == "stopped=true\n"

    def test_the_first_line_of_the_script_writes_the_output(self):
        lines = [line.strip() for line in _code_only(str(_step(REVIEW, STOP)["run"])).splitlines() if line.strip()]
        assert lines[0] == 'echo "stopped=true" >> "$GITHUB_OUTPUT"'


class TestClearStep:
    """A review that starts checks the hash again, so the label of an earlier stop goes first."""

    def _clear(self, tmp_path: Path, **env: str):
        return _run(str(_step(REVIEW, CLEAR)["run"]), tmp_path, tmp_path, PR_NUM="7", **env)

    def test_the_label_goes_when_it_is_there(self, tmp_path):
        result, calls = self._clear(tmp_path, GH_LABELS=f"quality:85 {render_hash.STOP_LABEL}")
        assert result.returncode == 0, result.stdout + result.stderr
        assert _calls(calls, "pr", "edit") == [["pr", "edit", "7", "--remove-label", render_hash.STOP_LABEL]]

    @pytest.mark.parametrize(
        "env",
        [
            {"GH_LABELS": "quality:85"},
            {"GH_FAIL_VIEW": "1"},
            {"GH_LABELS": "ai-render-mismatch", "GH_FAIL_PR_REMOVE": "1"},
        ],
        ids=["absent", "unreadable-labels", "remove-fails"],
    )
    def test_it_never_fails_the_review(self, tmp_path, env):
        result, calls = self._clear(tmp_path, **env)
        assert result.returncode == 0, result.stdout + result.stderr
        assert len(_calls(calls, "pr", "edit")) == (1 if "GH_FAIL_PR_REMOVE" in env else 0)

    def test_it_runs_before_the_check(self):
        names = _names()
        assert names.index(CLEAR) < names.index(CHECK)
        assert "if" not in _step(REVIEW, CLEAR)


# --- the keep path of a stopped regeneration: gate, early verdict, verdict -----------------------

GATE_ENV = {
    **ENV,
    "SCORE": "",
    "PREV_STORED": "88",
    "PREV_RENDERS": "missing",
    "CONTEXT_OUTCOME": "success",
    "CHANGE_REQUEST_PRESENT": "false",
    "MODEL_ID": "n/a",
    "CRITERIA_VERSION": "n/a",
    "PROMPTS_TREE": "n/a",
    "PREV_MODEL": "n/a",
    "PREV_CRITERIA_VERSION": "n/a",
    "LANGUAGE": "python",
    "EXT": ".py",
    "REVIEW_SKIPPED": "",
    "ADAPT_ROUTE": "",
}


def _gate(tmp_path: Path, **env: str):
    """The "Regen gate" step in an empty directory: no review ran, so none of its files exist."""
    runner = tmp_path / "runner"
    (runner / "regen-tools").mkdir(parents=True, exist_ok=True)
    shutil.copy(TOOLS / "regen_gate.py", runner / "regen-tools" / "regen_gate.py")
    work = tmp_path / "work"
    work.mkdir(exist_ok=True)
    output = tmp_path / "gate_output"
    output.unlink(missing_ok=True)
    result, _ = _run(
        str(_step(REVIEW, GATE)["run"]),
        work,
        tmp_path,
        RUNNER_TEMP=str(runner),
        GITHUB_OUTPUT=str(output),
        **{**GATE_ENV, **env},
    )
    outputs = dict(line.split("=", 1) for line in output.read_text(encoding="utf-8").splitlines() if "=" in line)
    return result, outputs, runner


class TestKeepPath:
    def test_the_gate_keeps_without_any_review_file(self, tmp_path):
        result, outputs, runner = _gate(tmp_path, RENDER_MISMATCH="true")
        assert result.returncode == 0, result.stdout + result.stderr
        assert (outputs["verdict"], outputs["code"]) == ("keep", "render_mismatch")
        assert " verdict=keep code=render_mismatch " in result.stdout and "script_crashed" not in result.stdout
        record = json.loads((runner / "anyplot-regen-record.json").read_text(encoding="utf-8"))
        assert (record["verdict"], record["code"], record["pr"]) == ("keep", "render_mismatch", 7)
        assert regen_gate.validate_record(record) == []
        assert "not made from the code at the PR head" in (runner / "anyplot-regen-summary.md").read_text()

    @pytest.mark.parametrize("flag", ["", "false"])
    def test_without_the_stop_the_gate_gets_no_flag(self, tmp_path, flag):
        result, outputs, _ = _gate(tmp_path, RENDER_MISMATCH=flag)
        assert result.returncode == 0, result.stdout + result.stderr
        assert outputs["code"] == "no_score"

    def test_the_early_verdict_marks_the_keep(self, tmp_path):
        env = {"PR_NUM": "7", "SCORE": "", "ATTEMPT_COUNT": "0", "IS_REGEN": "true", "GATE_VERDICT": "keep"}
        output = tmp_path / "output"
        result, calls = _run(str(_step(REVIEW, EARLY)["run"]), tmp_path, tmp_path, GITHUB_OUTPUT=str(output), **env)
        assert result.returncode == 0, result.stdout + result.stderr
        assert _calls(calls, "pr", "edit") == [["pr", "edit", "7", "--add-label", "regen:kept"]]
        assert output.read_text(encoding="utf-8") == "approved=false\n"

    def _verdict(self, tmp_path: Path, **env: str):
        """Gate, then the verdict step with what the gate left in $RUNNER_TEMP."""
        gate, outputs, runner = _gate(tmp_path, RENDER_MISMATCH="true")
        assert gate.returncode == 0, gate.stdout + gate.stderr
        work = tmp_path / "work"
        result, calls = _run(
            str(_step(REVIEW, VERDICT_STEP)["run"]),
            work,
            tmp_path,
            RUNNER_TEMP=str(runner),
            **{
                **ENV,
                "LANGUAGE": "python",
                "EXT": ".py",
                "SCORE": "",
                "ATTEMPT": "1",
                "ATTEMPT_COUNT": "0",
                "ISSUE_NUMBER": "",
                "REPOSITORY": "o/r",
                "RUN_ID": "1",
                "MODEL": "sonnet",
                "IS_REGEN": "true",
                "GATE_VERDICT": outputs["verdict"],
                "GATE_REASON": outputs["reason"],
                "GATE_CODE": outputs["code"],
                "PREV_STORED": "88",
                "MODEL_ID": "n/a",
                "WB_STATUS": "",
                "WB_PR": "",
                "WB_SCORE": "",
                "NOTHING_TO_REPAIR": "",
                "REVIEW_SKIPPED": "",
                "ADAPT_COUNTED": "",
                "ADAPT_OVERRULED": "",
                **env,
            },
        )
        return result, calls

    def test_the_verdict_step_closes_the_pr_and_says_that_no_review_ran(self, tmp_path):
        result, calls = self._verdict(tmp_path, RENDER_STOPPED="true")
        assert result.returncode == 0, result.stdout + result.stderr
        assert ["pr", "close", "7", "--delete-branch"] in calls
        assert not _calls(calls, "workflow", "run")  # no merge, no repair
        (comment,) = _calls(calls, "pr", "comment")
        body = Path(comment[-1]).read_text(encoding="utf-8")
        assert "## :leftwards_arrow_with_hook: Regeneration kept the live implementation" in body
        assert "No review ran: the staged renders of this PR were not made from the code at its head" in body
        assert "This PR is closed without merging" in body
        assert "compared this render" not in body and "(score " not in body
        assert (
            "**Stored review:** unchanged (the gate has no re-score of the live implementation: render_mismatch)."
            in body
        )
        (marker,) = regen_gate.parse_record_markers(body)
        assert (marker["code"], marker["verdict"], marker["writeback"]) == ("render_mismatch", "keep", "no_rescore")

    def test_without_the_flag_the_comment_is_the_ordinary_keep(self, tmp_path):
        """The control: the same run as an ordinary keep after a review, whose write-back is missing."""
        result, calls = self._verdict(tmp_path, RENDER_STOPPED="", SCORE="85")
        assert result.returncode == 0, result.stdout + result.stderr
        (comment,) = _calls(calls, "pr", "comment")
        body = Path(comment[-1]).read_text(encoding="utf-8")
        assert "The regen gate compared this render (score 85) with the implementation on main" in body
        assert "No review ran" not in body and "the write-back failed" in body


# --- wiring --------------------------------------------------------------------------------------


class TestWiring:
    def test_the_stop_follows_the_check_and_keys_on_its_output(self):
        names = _names()
        assert names[names.index(CHECK) + 1] == STOP
        step = _step(REVIEW, STOP)
        assert (step["id"], step["if"]) == ("render_stop", "steps.render_hash.outputs.stop == 'true'")
        assert "continue-on-error" not in step
        assert step["env"]["IS_REGEN"] == "${{ steps.regen.outputs.is_regen }}"
        # Regeneration or not is known before the stop.
        assert names.index("Detect regeneration") < names.index(STOP)

    @pytest.mark.parametrize("name", SWITCHED_OFF)
    def test_a_stop_switches_off(self, name):
        names = _names()
        assert names.index(STOP) < names.index(name) < names.index(GATE)
        assert STOPPED in _step(REVIEW, name)["if"], name

    def test_nothing_else_between_the_stop_and_the_gate_reads_the_renders_or_reviews(self):
        """A step added there later has to decide: this list is every step that still runs after a stop."""
        names = _names()
        between = names[names.index(STOP) + 1 : names.index(GATE)]
        still_running = [n for n in between if STOPPED not in str(_step(REVIEW, n).get("if", ""))]
        review_keyed = [n for n in still_running if "steps.review." in str(_step(REVIEW, n).get("if", ""))]
        assert sorted(set(still_running) - set(review_keyed)) == [
            "Contract check (record-only)",
            "Download previous production renders (regen)",
            "Record review start time",
            "Record rules version",
            "Restore the stored review",
        ]

    @pytest.mark.parametrize("name", SWITCHED_ON)
    def test_the_keep_path_switches_on(self, name):
        assert _step(REVIEW, name)["if"].rstrip(")").endswith(KEEP), name

    def test_the_gate_still_needs_a_regeneration(self):
        assert _step(REVIEW, GATE)["if"].startswith("steps.regen.outputs.is_regen == 'true' && (")
        assert _step(REVIEW, GATE)["env"]["RENDER_MISMATCH"] == "${{ steps.render_stop.outputs.keep }}"
        script = str(_step(REVIEW, GATE)["run"])
        flag = '[ "$RENDER_MISMATCH" = "true" ] && FLAGS+=(--render-mismatch)'
        assert script.index(flag) < script.index('python3 "$RUNNER_TEMP/regen-tools/regen_gate.py" decide')

    @pytest.mark.parametrize(
        "name",
        [
            "Update metadata and implementation header",
            "Write back the re-score (regen keep)",
            "Re-dispatch review after a post-score failure",
            "Stage regen pair",
            "Add quality score label",
            "Add carried quality score label",
            # Only the metadata step needs it, and its network call could fail the keep.
            "Install Python dependencies for metadata update",
        ],
    )
    def test_a_stop_never_reaches(self, name):
        """No header commit, no score, no stored review, and no second review of the same staging."""
        assert "render_stop" not in _step(REVIEW, name)["if"], name

    def test_only_the_stop_and_the_gate_steps_read_the_outputs(self):
        text = (WORKFLOWS / REVIEW).read_text(encoding="utf-8")
        assert set(re.findall(r"steps\.render_hash\.outputs\.(\w+)", text)) == {"stop"}
        assert set(re.findall(r"steps\.render_stop\.outputs\.(\w+)", text)) == {"stopped", "keep"}

    def test_the_names_agree_across_the_workflows_and_the_scripts(self):
        stop = _code_only(str(_step(REVIEW, STOP)["run"]))
        assert f'--add-label "{render_hash.STOP_LABEL}"' in stop
        assert f'--remove-label "{render_hash.STOP_LABEL}"' in str(_step(REVIEW, CLEAR)["run"])
        assert render_hash.KEEP_CODE in regen_gate.REASON_CODES
        assert render_hash.KEEP_CODE in regen_pick_pairs.RETURN_CODES

    def test_the_watchdog_skips_the_label_and_reports_it(self):
        script = str(_step("watchdog-stuck-jobs.yml", "Scan and dispatch")["run"])
        skip = script.index(f'grep -q " {render_hash.STOP_LABEL} "')
        block = script[skip : script.index("fi", skip)]
        assert "::warning::PR #$num: review stopped on a render hash mismatch" in block and "continue" in block
        # Before every case that rescues: none of them may see the PR.
        assert skip < script.index("# Case 0:") < script.index("# Case 1:") < script.index("# Case 2:")

    def test_generating_the_pair_again_replaces_the_stopped_pr(self):
        """What the stop comment tells the reader: impl-generate deletes the pair's branch, which closes its PR."""
        script = str(_step("impl-generate.yml", "Create implementation branch")["run"])
        delete = 'git push origin --delete "$BRANCH"'
        assert script.index(delete) < script.index('git checkout -b "$BRANCH" origin/main')
        result = render_hash.Comparison("mismatch", staged="a" * 64, head="b" * 64, form=render_hash.FORM_CODE)
        text = render_hash.comment(result, "c" * 40, "", spec_id="spec-a", library="plotly")
        assert "replaces this PR's branch, which closes this PR, and opens a new one" in text
        assert "gh workflow run bulk-generate.yml -f specification_id=spec-a -f library=plotly" in text


def _references(workflow: dict[str, Any]) -> set[str]:
    return set(re.findall(r"steps\.([A-Za-z0-9_-]+)\.(?:outputs|outcome|conclusion)\b", yaml.safe_dump(workflow)))


@pytest.mark.parametrize(
    "filename", ["impl-review.yml", "impl-generate.yml", "impl-repair.yml", "watchdog-stuck-jobs.yml"]
)
def test_the_edited_workflows_parse_and_reference_only_steps_that_exist(filename):
    """Nothing runs these files before the merge, and a wrong step id only reads as an empty string."""
    workflow = yaml.safe_load((WORKFLOWS / filename).read_text(encoding="utf-8"))
    for job in workflow["jobs"].values():
        ids = {step["id"] for step in job.get("steps", []) if "id" in step}
        missing = _references({"job": job}) - ids
        assert not missing, f"{filename}: no step with id {sorted(missing)}"


@pytest.mark.parametrize(
    "filename", ["impl-review.yml", "impl-generate.yml", "impl-repair.yml", "watchdog-stuck-jobs.yml"]
)
def test_every_condition_of_the_edited_workflows_is_well_formed(filename):
    """A malformed `if:` fails the whole workflow file at load, which no local run shows.

    Not an expression parser: balanced parentheses, closed strings, and no
    operator at an end or doubled.
    """
    for condition in [str(s["if"]) for s in _steps(filename) if "if" in s]:
        bare = re.sub(r"'[^']*'", "''", condition)  # string literals hold no syntax
        assert "'" not in bare.replace("''", ""), condition
        assert bare.count("(") == bare.count(")"), condition
        assert not re.search(r"^\s*(&&|\|\|)|(&&|\|\||!|==|!=)\s*$", bare), condition
        # `cancelled()` is a call, so empty parentheses are fine.
        assert not re.search(r"(&&|\|\|)\s*(&&|\|\||\))|\(\s*(&&|\|\|)", bare), condition
