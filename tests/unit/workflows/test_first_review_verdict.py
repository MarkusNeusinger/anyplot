"""impl-review owns the verdict, and a later review starts blind (P10, PR 1).

Three changes, each run for real where it can be:

1. "Hide the previous review (attempt 2 and later)" and "Restore the stored
   review": while the reviewer runs at attempt 2 or later, the implementation
   header reads `Quality: pending` and the metadata file (score and the whole
   previous review) is out of the workspace. Both come back before any later
   step reads them, whatever the review step did.
2. "Add preliminary verdict label (early)": a review below its threshold, at
   80 or more, whose every technical item is at its maximum is approved as it
   stands (nothing to repair). The checklist decides, never the absence of
   defect lines.
3. "Update metadata and implementation header": the stored `review.verdict` is
   what the early verdict step decided, not what the reviewer wrote.

The step scripts run under `bash -eo pipefail` in a throwaway git repository,
with the workflow-ref copy of the gate script where a runner has it
(`$RUNNER_TEMP/regen-tools/`), a fake `gh` and a no-op `sleep`.
"""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path
from typing import Any

import pytest

from automation.scripts.regen_gate import CRITERIA
from tests.unit.workflows.test_pipeline_retry_gaps import _calls, _code_only, _run, _step, _steps


REPO_ROOT = Path(__file__).parent.parent.parent.parent
GATE_SCRIPT = REPO_ROOT / "automation" / "scripts" / "regen_gate.py"
HIDE = "Hide the previous review (attempt 2 and later)"
RESTORE = "Restore the stored review"
REVIEW = "Run AI Quality Review"
EARLY = "Add preliminary verdict label (early)"
METADATA = "Update metadata and implementation header"
VERDICT = "Add verdict label and take action"
IMPL = "plots/spec-a/implementations/python/plotly.py"
META = "plots/spec-a/metadata/python/plotly.yaml"
HEADER = '""" anyplot.ai\nspec-a: A spec\nLibrary: plotly 6.0.0 | Python 3.13\nQuality: 88/100 | Updated: 2026-10-01\n"""\n\nimport plotly\n'
META_TEXT = "library: plotly\nquality_score: 88\nreview:\n  weaknesses:\n  - 'VQ-01 (both): small ticks'\n"
CATEGORY_KEYS = {
    "VQ": "visual_quality",
    "DE": "design_excellence",
    "SC": "spec_compliance",
    "DQ": "data_quality",
    "CQ": "code_quality",
    "LM": "library_mastery",
}
# The modal judgment scores of a first review (DE 6/4/4, LM 4/3): 70 + 21 = 91.
JUDGMENT = {"DE-01": 6, "DE-02": 4, "DE-03": 4, "LM-01": 4, "LM-02": 3}
STEP_ENV = {"SPEC_ID": "spec-a", "LIBRARY": "plotly", "LANGUAGE": "python", "EXT": ".py"}


def _checklist_json(scores: dict[str, int]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for cid, score in scores.items():
        cat = out.setdefault(CATEGORY_KEYS[cid[:2]], {"score": 0, "max": 0, "items": []})
        cat["items"].append(
            {"id": cid, "name": cid, "score": score, "max": CRITERIA[cid], "passed": True, "comment": ""}
        )
        cat["score"] += score
        cat["max"] += CRITERIA[cid]
    return out


def _git(cwd: Path, *args: str) -> str:
    return subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True, text=True).stdout


@pytest.fixture
def runner(tmp_path: Path) -> Path:
    """`$RUNNER_TEMP` with the workflow-ref copy of the gate script."""
    temp = tmp_path / "runner"
    (temp / "regen-tools").mkdir(parents=True)
    shutil.copyfile(GATE_SCRIPT, temp / "regen-tools" / "regen_gate.py")
    return temp


@pytest.fixture
def workspace(tmp_path: Path) -> Path:
    """A PR head checked out: the implementation with its stored score and the metadata file."""
    work = tmp_path / "work"
    for rel, text in ((IMPL, HEADER), (META, META_TEXT)):
        path = work / rel
        path.parent.mkdir(parents=True)
        path.write_text(text, encoding="utf-8")
    _git(work, "init", "-q")
    _git(work, "add", "-A")
    _git(work, "-c", "user.name=t", "-c", "user.email=t@example.invalid", "commit", "-q", "-m", "review 1")
    return work


class TestLaterReviewsStartBlind:
    def _hide(self, workspace: Path, tmp_path: Path, runner: Path):
        return _run(_step("impl-review.yml", HIDE)["run"], workspace, tmp_path, RUNNER_TEMP=str(runner), **STEP_ENV)

    def _restore(self, workspace: Path, tmp_path: Path, runner: Path):
        script = _step("impl-review.yml", RESTORE)["run"]
        return _run(script, workspace, tmp_path, RUNNER_TEMP=str(runner), **STEP_ENV)

    def test_the_reviewer_sees_neither_the_score_nor_the_stored_review(self, workspace, tmp_path, runner):
        result, _ = self._hide(workspace, tmp_path, runner)
        assert result.returncode == 0, result.stdout + result.stderr
        source = (workspace / IMPL).read_text(encoding="utf-8")
        assert "Quality: pending | Updated: 2026-10-01" in source and "88" not in source
        assert not (workspace / META).exists()
        # Nowhere under the workspace: the reviewer can read every file in it.
        assert not [p for p in workspace.rglob("*.yaml") if ".git" not in p.parts]
        assert (runner / "hidden-review" / "metadata.yaml").read_text(encoding="utf-8") == META_TEXT
        assert "header Quality: pending, stored review hidden=true" in result.stdout

    def test_restore_puts_both_back_exactly(self, workspace, tmp_path, runner):
        self._hide(workspace, tmp_path, runner)
        result, _ = self._restore(workspace, tmp_path, runner)
        assert result.returncode == 0, result.stdout + result.stderr
        assert (workspace / IMPL).read_text(encoding="utf-8") == HEADER
        assert (workspace / META).read_text(encoding="utf-8") == META_TEXT
        assert _git(workspace, "status", "--porcelain") == ""
        assert not (runner / "hidden-review" / "metadata.yaml").exists()

    def test_nothing_is_committed(self, workspace, tmp_path, runner):
        head = _git(workspace, "rev-parse", "HEAD")
        self._hide(workspace, tmp_path, runner)
        self._restore(workspace, tmp_path, runner)
        assert _git(workspace, "rev-parse", "HEAD") == head

    def test_a_lost_stash_is_restored_from_the_branch(self, workspace, tmp_path, runner):
        self._hide(workspace, tmp_path, runner)
        (runner / "hidden-review" / "metadata.yaml").unlink()
        result, _ = self._restore(workspace, tmp_path, runner)
        assert result.returncode == 0, result.stdout + result.stderr
        assert (workspace / META).read_text(encoding="utf-8") == META_TEXT

    def test_restore_without_a_hide_changes_nothing(self, workspace, tmp_path, runner):
        result, _ = self._restore(workspace, tmp_path, runner)
        assert result.returncode == 0, result.stdout + result.stderr
        assert _git(workspace, "status", "--porcelain") == ""

    def test_a_missing_gate_script_still_hides_the_stored_review(self, workspace, tmp_path, runner):
        (runner / "regen-tools" / "regen_gate.py").unlink()
        result, _ = self._hide(workspace, tmp_path, runner)
        assert result.returncode == 0, result.stdout + result.stderr
        assert "::warning::could not reset the Quality header" in result.stdout
        assert not (workspace / META).exists()

    def test_a_metadata_file_that_never_existed_is_fine(self, workspace, tmp_path, runner):
        _git(workspace, "rm", "-q", META)
        _git(workspace, "-c", "user.name=t", "-c", "user.email=t@example.invalid", "commit", "-q", "-m", "no meta")
        assert self._hide(workspace, tmp_path, runner)[0].returncode == 0
        assert self._restore(workspace, tmp_path, runner)[0].returncode == 0
        assert not (workspace / META).exists()

    def test_wiring(self):
        names = [s.get("name") for s in _steps("impl-review.yml")]
        # Hidden right before the review, restored before any step reads the files again.
        assert names.index(HIDE) == names.index(REVIEW) - 1
        assert names.index(REVIEW) < names.index(RESTORE) < names.index("Extract quality score")
        assert names.index(RESTORE) < names.index(METADATA)
        hide, restore = _step("impl-review.yml", HIDE), _step("impl-review.yml", RESTORE)
        # Attempt 2 and later only: a first review has nothing to hide.
        assert hide["if"] == "steps.attempts.outputs.count != '0'"
        assert restore["if"] == "always() && steps.attempts.outputs.count != '0'"
        # Neither can fail the job.
        assert hide["continue-on-error"] is True and restore["continue-on-error"] is True
        assert "git commit" not in hide["run"] and "git add" not in hide["run"]
        assert "sanitize-source --pending" in hide["run"]

    def test_the_metadata_step_has_a_last_net(self):
        script = _step("impl-review.yml", METADATA)["run"]
        net = '[ -f "$METADATA_FILE" ] || git checkout -- "$METADATA_FILE" 2>/dev/null || true'
        assert script.index('git checkout -B "$BRANCH" "origin/$BRANCH"') < script.index(net)
        assert script.index(net) < script.index('if [ -f "$METADATA_FILE" ]; then')


class TestNothingToRepair:
    ENV = {"PR_NUM": "7", "SCORE": "88", "ATTEMPT_COUNT": "0", "IS_REGEN": "false", "GATE_VERDICT": ""}

    def _early(self, tmp_path: Path, runner: Path, checklist: dict[str, int] | None, **env: str):
        if checklist is not None:
            (tmp_path / "review_checklist.json").write_text(json.dumps(_checklist_json(checklist)), encoding="utf-8")
        out = tmp_path / "github_output"
        out.unlink(missing_ok=True)
        base = {**self.ENV, "GITHUB_OUTPUT": str(out), "RUNNER_TEMP": str(runner)}
        result, calls = _run(_step("impl-review.yml", EARLY)["run"], tmp_path, tmp_path, **{**base, **env})
        outputs = (
            dict(line.split("=", 1) for line in out.read_text(encoding="utf-8").splitlines()) if out.exists() else {}
        )
        return result, [c[-1] for c in _calls(calls, "pr", "edit")], outputs

    def test_a_clean_technical_sheet_below_the_threshold_is_approved(self, tmp_path, runner):
        result, labels, outputs = self._early(tmp_path, runner, {**CRITERIA, **JUDGMENT})
        assert result.returncode == 0, result.stdout + result.stderr
        assert labels == ["ai-approved"]
        assert outputs == {"nothing_to_repair": "true", "approved": "true"}
        assert "nothing to repair" in result.stdout

    @pytest.mark.parametrize("criterion", ["VQ-01", "SC-02", "DQ-01", "CQ-01"])
    def test_one_technical_deduction_takes_the_repair(self, tmp_path, runner, criterion):
        checklist = {**CRITERIA, **JUDGMENT, criterion: CRITERIA[criterion] - 1}
        _, labels, outputs = self._early(tmp_path, runner, checklist)
        assert labels == ["ai-rejected"]
        assert outputs == {"nothing_to_repair": "false", "approved": "false"}

    def test_below_80_takes_the_repair(self, tmp_path, runner):
        _, labels, outputs = self._early(tmp_path, runner, {**CRITERIA, **JUDGMENT}, SCORE="79")
        assert labels == ["ai-rejected"] and outputs["approved"] == "false"

    def test_no_checklist_is_the_plain_threshold(self, tmp_path, runner):
        _, labels, outputs = self._early(tmp_path, runner, None)
        assert labels == ["ai-rejected"]
        assert outputs == {"nothing_to_repair": "false", "approved": "false"}

    def test_no_gate_script_is_the_plain_threshold(self, tmp_path, runner):
        (runner / "regen-tools" / "regen_gate.py").unlink()
        result, labels, outputs = self._early(tmp_path, runner, {**CRITERIA, **JUDGMENT})
        assert result.returncode == 0, result.stdout + result.stderr
        assert labels == ["ai-rejected"] and outputs["nothing_to_repair"] == "false"

    def test_at_the_threshold_the_rule_is_not_consulted(self, tmp_path, runner):
        _, labels, outputs = self._early(tmp_path, runner, {**CRITERIA, **JUDGMENT, "VQ-01": 7}, SCORE="93")
        assert labels == ["ai-approved"]
        assert outputs == {"nothing_to_repair": "false", "approved": "true"}

    def test_the_cascade_is_unchanged(self, tmp_path, runner):
        script = _step("impl-review.yml", EARLY)["run"]
        assert "THRESHOLD=$((90 - ATTEMPT_COUNT * 10))" in script
        assert 'if [ "$THRESHOLD" -lt 50 ]; then THRESHOLD=50; fi' in script
        # After one repair the threshold is 80: 82 passes on the score alone.
        _, labels, outputs = self._early(
            tmp_path, runner, {**CRITERIA, **JUDGMENT, "VQ-01": 5}, SCORE="82", ATTEMPT_COUNT="1"
        )
        assert labels == ["ai-approved"] and outputs["nothing_to_repair"] == "false"

    @pytest.mark.parametrize(("gate", "approved"), [("merge", "true"), ("keep", "false")])
    def test_a_regeneration_reports_the_gates_verdict(self, tmp_path, runner, gate, approved):
        _, _, outputs = self._early(tmp_path, runner, None, IS_REGEN="true", GATE_VERDICT=gate)
        assert outputs == {"approved": approved}

    def test_the_rule_reads_the_checklist_not_the_defect_lines(self):
        script = _code_only(_step("impl-review.yml", EARLY)["run"])
        assert 'regen_gate.py" nothing-to-repair' in script
        assert "--checklist review_checklist.json" in script
        assert "review_weaknesses.json" not in script
        # Before the format check, which only warns and comes later.
        names = [s.get("name") for s in _steps("impl-review.yml")]
        assert names.index(EARLY) < names.index("Check review feedback format (never gating)")


class TestVerdictStepSaysWhy:
    ENV = {
        "PR_NUM": "7",
        "SPEC_ID": "spec-a",
        "LIBRARY": "plotly",
        "LANGUAGE": "python",
        "EXT": ".py",
        "SCORE": "88",
        "ATTEMPT": "1",
        "ATTEMPT_COUNT": "0",
        "ISSUE_NUMBER": "42",
        "REPOSITORY": "owner/repo",
        "RUN_ID": "1",
        "MODEL": "opus",
        "IS_REGEN": "false",
        "GH_LABELS": "ai-approved quality:88",
    }

    def _verdict(self, tmp_path: Path, **env: str):
        return _run(_step("impl-review.yml", VERDICT)["run"], tmp_path, tmp_path, **{**self.ENV, **env})

    def test_a_nothing_to_repair_approval_is_explained_and_merged(self, tmp_path):
        result, calls = self._verdict(tmp_path, NOTHING_TO_REPAIR="true")
        assert result.returncode == 0, result.stdout + result.stderr
        (comment,) = _calls(calls, "pr", "comment")
        body = "\n".join(comment[comment.index("--body") + 1 :])
        assert "Approved as it stands" in body
        assert "Score 88 is below the threshold of 90" in body
        assert "every technical criterion (VQ, SC, DQ, CQ) is at its maximum" in body
        assert ["workflow", "run", "impl-merge.yml", "-f", "pr_number=7"] in calls
        assert not _calls(calls, "workflow", "run", "impl-repair.yml")

    def test_a_lost_comment_never_holds_up_the_merge(self, tmp_path):
        result, calls = self._verdict(tmp_path, NOTHING_TO_REPAIR="true", GH_COMMENT_RC="1")
        assert result.returncode == 0, result.stdout + result.stderr
        assert ["workflow", "run", "impl-merge.yml", "-f", "pr_number=7"] in calls

    @pytest.mark.parametrize("env", [{"NOTHING_TO_REPAIR": "false"}, {"NOTHING_TO_REPAIR": ""}, {"SCORE": "93"}])
    def test_an_ordinary_approval_posts_no_comment(self, tmp_path, env):
        result, calls = self._verdict(tmp_path, **{"NOTHING_TO_REPAIR": "true", **env})
        assert result.returncode == 0, result.stdout + result.stderr
        assert not _calls(calls, "pr", "comment")
        assert ["workflow", "run", "impl-merge.yml", "-f", "pr_number=7"] in calls


class TestStoredVerdict:
    """The metadata step stores the workflow's decision as review.verdict."""

    def test_the_early_verdict_is_handed_to_the_metadata_writer(self):
        step = _step("impl-review.yml", METADATA)
        assert step["env"]["REVIEW_APPROVED"] == "${{ steps.early_verdict.outputs.approved }}"
        assert step["env"].get("NOTHING_TO_REPAIR") is None
        verdict = _step("impl-review.yml", VERDICT)
        assert verdict["env"]["NOTHING_TO_REPAIR"] == "${{ steps.early_verdict.outputs.nothing_to_repair }}"

    @pytest.mark.parametrize(
        ("approved", "written", "stored"),
        [
            ("true", "REJECTED", "APPROVED"),
            ("false", "APPROVED", "REJECTED"),  # #12028's first review wrote APPROVED at 88
            ("true", None, "APPROVED"),  # the reviewer writes no verdict (PR 2)
            ("", "APPROVED", "APPROVED"),  # the early step did not get that far: the file stands in
            ("", None, None),
        ],
    )
    def test_the_workflows_decision_replaces_the_reviewers(self, tmp_path, approved, written, stored):
        script = _step("impl-review.yml", METADATA)["run"]
        python = script.split("cat > /tmp/update_metadata.py << 'EOF'\n", 1)[1].split("\nEOF\n", 1)[0]
        start = python.index("if Path('review_verdict.txt').exists():")
        end = python.index("if Path('review_impl_tags.json').exists():")
        if written is not None:
            (tmp_path / "review_verdict.txt").write_text(written + "\n", encoding="utf-8")
        program = "import os\nfrom pathlib import Path\nverdict = None\n" + python[start:end] + "\nprint(verdict)\n"
        result = subprocess.run(
            ["python3", "-c", program],
            cwd=tmp_path,
            env={"REVIEW_APPROVED": approved, "PATH": "/usr/bin:/bin"},
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, result.stderr
        assert result.stdout.strip() == str(stored)
