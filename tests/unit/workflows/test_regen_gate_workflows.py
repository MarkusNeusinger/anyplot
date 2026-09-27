"""Content guards for the regen gate wiring in the impl-* workflows.

The decision itself is unit-tested in tests/unit/automation/scripts/
test_regen_gate.py. These tests pin the workflow-side invariants that have no
local execution loop: a regeneration never gets `ai-rejected` (the repair
loop's exhaustion path deletes the live implementation from main), the
watchdog neither rescues regenerations into repair nor ignores their
never-started reviews, and "is this a regeneration" is read from origin/main.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import yaml


WORKFLOWS_DIR = Path(__file__).parent.parent.parent.parent / ".github" / "workflows"
REGEN_BLOCK_START = 'if [ "$IS_REGEN" = "true" ]; then'


def _steps(filename: str) -> list[dict[str, Any]]:
    workflow = yaml.safe_load((WORKFLOWS_DIR / filename).read_text(encoding="utf-8"))
    return [step for job in workflow["jobs"].values() for step in job.get("steps", [])]


def _step(filename: str, name: str) -> dict[str, Any]:
    matches = [s for s in _steps(filename) if s.get("name") == name]
    assert len(matches) == 1, f"expected exactly one step named {name!r} in {filename}"
    return matches[0]


def _code_only(script: str) -> str:
    """Drop shell comment lines so prose mentioning a label does not count."""
    return "\n".join(line for line in script.splitlines() if not line.lstrip().startswith("#"))


def _regen_block(script: str) -> str:
    """The top-level `if [ "$IS_REGEN" = "true" ]` block of a step script."""
    start = script.index(REGEN_BLOCK_START)
    end = script.index("\n  exit 0\nfi\n", start)
    return script[start:end]


class TestImplReviewRegenBranch:
    def test_early_verdict_regen_branch_never_adds_ai_rejected(self):
        block = _code_only(_regen_block(_step("impl-review.yml", "Add preliminary verdict label (early)")["run"]))
        assert "ai-rejected" not in block
        assert "regen:kept" in block

    def test_early_verdict_adds_regen_improved_before_ai_approved(self):
        block = _code_only(_regen_block(_step("impl-review.yml", "Add preliminary verdict label (early)")["run"]))
        improved = block.index('add_label "regen:improved"')
        approved = block.index('add_label "ai-approved"')
        assert improved < approved

    def test_verdict_step_regen_branch_never_adds_ai_rejected_or_repairs(self):
        block = _code_only(_regen_block(_step("impl-review.yml", "Add verdict label and take action")["run"]))
        assert "ai-rejected" not in block
        assert "impl-repair" not in block
        assert "--delete-branch" in block
        assert "impl:${LIBRARY}:done" in block

    def test_verdict_merge_branch_reasserts_ai_approved_before_dispatch(self):
        block = _code_only(_regen_block(_step("impl-review.yml", "Add verdict label and take action")["run"]))
        approved = block.index('gh pr edit "$PR_NUM" --add-label "ai-approved"')
        dispatch = block.index("gh workflow run impl-merge.yml")
        assert approved < dispatch

    def test_blind_score_never_sees_the_stored_score(self):
        prompt = _step("impl-review.yml", "Run AI Quality Review")["with"]["prompt"]
        assert "PREVIOUS_SCORE" not in prompt
        assert "prev_stored" not in prompt
        ctx = _step("impl-review.yml", "Regen context")["run"]
        assert "--omit-scores" in ctx

    def test_regen_branch_comes_before_the_cascade(self):
        script = _step("impl-review.yml", "Add verdict label and take action")["run"]
        assert script.index(REGEN_BLOCK_START) < script.index('grep -q "ai-rejected"')

    def test_regen_detection_reads_origin_main(self):
        script = _step("impl-review.yml", "Detect regeneration")["run"]
        assert 'git cat-file -e "origin/main:plots/$SPEC_ID/implementations/$LANGUAGE/$LIBRARY$EXT"' in script
        # The `regen` label is a marker only; just `regen:forced` opts out.
        assert 'grep -qx "regen"' not in script
        assert 'grep -qx "regen:forced"' in script

    def test_gate_runs_before_any_verdict_label(self):
        names = [s.get("name") for s in _steps("impl-review.yml")]
        assert names.index("Regen gate") < names.index("Add preliminary verdict label (early)")

    def test_metadata_update_skipped_on_kept_regen(self):
        cond = _step("impl-review.yml", "Update metadata and implementation header")["if"]
        assert "steps.gate.outputs.verdict == 'merge'" in cond

    def test_gate_step_emits_notice_and_fails_closed(self):
        script = _step("impl-review.yml", "Regen gate")["run"]
        assert "regen_gate.py" in script
        assert "verdict=keep" in script  # crash fallback


class TestWatchdog:
    SCRIPT = _step("watchdog-stuck-jobs.yml", "Scan and dispatch")["run"]

    def test_case5_marker_regex_allows_regen_labels(self):
        m = re.search(r"grep -vE '(\^\([^']*\))'", self.SCRIPT)
        assert m, "Case 5 marker filter not found"
        pattern = re.compile(m.group(1))
        assert pattern.search("regen")
        assert pattern.search("regen:forced")
        assert pattern.search("watchdog:review-bootstrap")
        assert not pattern.search("regen:kept")
        assert not pattern.search("quality:88")

    def test_repair_cases_skip_regenerations(self):
        assert self.SCRIPT.count('[[ "$is_regen" == "false" ]]') == 3

    def test_improved_without_ai_approved_is_flagged(self):
        # regen:improved alone must not silence the "no regen verdict" warning.
        assert " (regen:kept|ai-approved|ai-review-failed) " in self.SCRIPT
        assert "regen:improved|regen:kept" not in self.SCRIPT

    def test_case0_recloses_kept_regens(self):
        case0 = self.SCRIPT[self.SCRIPT.index("# Case 0") : self.SCRIPT.index("# Case 1")]
        assert 'grep -q " regen:kept "' in case0
        assert "gh pr close" in case0


class TestImplGenerate:
    def test_failure_handler_skips_failed_label_on_regen(self):
        script = _step("impl-generate.yml", "Handle generation failure")["run"]
        regen = script.index('if [ -n "$REGEN_LABEL" ]; then\n    # Regeneration: the implementation on main')
        failed = script.index('--add-label "impl:${LIBRARY}:failed"')
        assert regen < failed

    def test_retry_forwards_regen_gate(self):
        script = _step("impl-generate.yml", "Handle generation failure")["run"]
        assert '-f regen_gate="${REGEN_GATE}"' in script


class TestDailyRegen:
    def test_pick_uses_spec_issue_activity_as_attempt_record(self):
        workflow = yaml.safe_load((WORKFLOWS_DIR / "daily-regen.yml").read_text(encoding="utf-8"))
        pick = workflow["jobs"]["pick"]
        assert pick["permissions"]["issues"] == "read"
        step = next(s for s in pick["steps"] if s.get("id") == "pick")
        assert "GH_TOKEN" in step["env"]
        assert "MIN_AGE_HOURS" in step["env"]
        script = step["run"]
        assert '"gh", "issue", "list"' in script
        assert '"--limit", "1000"' in script
        assert "specification.yaml" in script
        # The closed-PR window (limit 200) is gone for good.
        assert '"--label", "regen"' not in script
        # Fallback to metadata `updated` when the listing fails.
        assert "picking by metadata 'updated' only" in script
