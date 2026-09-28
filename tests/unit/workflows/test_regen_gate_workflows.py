"""Content guards for the regen gate wiring in the impl-* workflows.

The decision itself is unit-tested in tests/unit/automation/scripts/
test_regen_gate.py. These tests pin the workflow-side invariants that have no
local execution loop: a regeneration never gets `ai-rejected` (the repair
loop's exhaustion path deletes the live implementation from main), the
watchdog neither rescues regenerations into repair nor ignores their
never-started reviews, and "is this a regeneration" is read from origin/main.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from datetime import datetime, timedelta, timezone
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
        # The predecessor source reaches the reviewer only through the sanitizer.
        assert 'git show "origin/main:${IMPL_FILE}" > /tmp/anyplot-prev-impl-raw' in ctx
        assert "sanitize-source" in ctx
        assert 'git show "origin/main:${IMPL_FILE}" > "/tmp/anyplot-prev-impl${EXT}"' not in ctx

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


def _step_names(filename: str) -> list[str | None]:
    return [s.get("name") for s in _steps(filename)]


def _metadata_writer_script() -> str:
    """The update_metadata.py heredoc of impl-review's metadata step, as run."""
    run = _step("impl-review.yml", "Update metadata and implementation header")["run"]
    return run.split("cat > /tmp/update_metadata.py << 'EOF'\n", 1)[1].split("\nEOF\n", 1)[0]


class TestImplReviewProvenance:
    """Provenance and gate records (P6 A1). Every new step is non-gating."""

    def test_provenance_helper_is_copied_from_the_workflow_ref(self):
        script = _step("impl-review.yml", "Checkout PR code")["run"]
        copy = script[: script.index("git fetch origin")]
        assert "automation/scripts/review_provenance.py" in copy
        assert "automation/scripts/regen_gate.py" in copy

    def test_rules_version_is_recorded_after_the_overlay_and_before_the_review(self):
        names = _step_names("impl-review.yml")
        rules = names.index("Record rules version")
        assert names.index("Overlay prompts/ from trigger ref (branch-level prompt iteration)") < rules
        assert rules < names.index("Run AI Quality Review")
        step = _step("impl-review.yml", "Record rules version")
        assert step["continue-on-error"] is True
        assert 'review_provenance.py" criteria-version --root . --library' in step["run"]

    def test_model_is_resolved_right_after_the_review(self):
        names = _step_names("impl-review.yml")
        assert names.index("Resolve review model") == names.index("Run AI Quality Review") + 1
        step = _step("impl-review.yml", "Resolve review model")
        assert step["continue-on-error"] is True
        assert step["env"]["EXECUTION_FILE"] == "${{ steps.review.outputs.execution_file }}"
        assert 'review_provenance.py" model --execution-file "${EXECUTION_FILE:-}"' in step["run"]

    def test_an_unresolved_model_is_never_recorded_as_the_alias(self):
        # The alias moves between releases; an unresolved model is n/a in the
        # notice, record and pair, and absent from the metadata.
        step = _step("impl-review.yml", "Resolve review model")
        assert "--fallback" not in step["run"]
        assert "MODEL_ALIAS" not in step["env"]
        for name in ("Regen gate", "Stage regen pair"):
            assert (
                _step("impl-review.yml", name)["env"]["MODEL_ID"]
                == "${{ steps.review_model.outputs.model_id || 'n/a' }}"
            )
        metadata = _step("impl-review.yml", "Update metadata and implementation header")
        assert metadata["env"]["REVIEW_MODEL"] == "${{ steps.review_model.outputs.model_id }}"
        assert "format('claude-" not in (WORKFLOWS_DIR / "impl-review.yml").read_text(encoding="utf-8")

    def test_render_time_never_fails_the_download(self):
        step = _step("impl-review.yml", "Download plot images from staging")
        assert step["id"] == "staging"
        script = step["run"]
        assert "gsutil stat" in script
        assert '|| CREATED=""' in script
        assert 'echo "rendered_at=${RENDERED_AT}" >> "$GITHUB_OUTPUT"' in script

    def test_gate_passes_provenance_and_writes_a_record(self):
        script = _step("impl-review.yml", "Regen gate")["run"]
        for flag in (
            "--record-out",
            "--pr",
            "--model",
            "--criteria-version",
            "--prompts-tree",
            "--prev-model",
            "--prev-criteria-version",
        ):
            assert flag in script, flag
        fallback = script[script.index("; then\n") :]
        assert 'code: "script_crashed"' in fallback
        assert 'echo "code=script_crashed"' in fallback
        # Same notice shape as the script's own line (docs/workflows/overview.md).
        assert "code=script_crashed model=${MODEL_ID} criteria=${CRITERIA_VERSION} reason=" in fallback

    def test_regen_context_feeds_prev_provenance(self):
        env = _step("impl-review.yml", "Regen gate")["env"]
        assert "steps.regen_ctx.outputs.prev_model" in env["PREV_MODEL"]
        assert "steps.regen_ctx.outputs.prev_criteria_version" in env["PREV_CRITERIA_VERSION"]

    def test_regen_pair_artifact_is_staged_and_never_gating(self):
        names = _step_names("impl-review.yml")
        assert names.index("Regen gate") < names.index("Stage regen pair") < names.index("Upload regen pair")
        assert names.index("Upload regen pair") < names.index("Add preliminary verdict label (early)")
        stage = _step("impl-review.yml", "Stage regen pair")
        upload = _step("impl-review.yml", "Upload regen pair")
        assert stage["continue-on-error"] is True
        assert upload["continue-on-error"] is True
        assert "steps.regen.outputs.is_regen == 'true'" in stage["if"]
        assert 'DIR="$RUNNER_TEMP/regen-pair"' in stage["run"]
        assert upload["uses"].startswith("actions/upload-artifact@")
        assert upload["with"]["path"] == "${{ steps.pair.outputs.dir }}"
        assert upload["with"]["retention-days"] == 60
        assert upload["with"]["name"].startswith("regen-pair-${{ steps.pr.outputs.pr_number }}-")

    def test_metadata_writer_reads_provenance_through_os_environ_get(self):
        step = _step("impl-review.yml", "Update metadata and implementation header")
        for name in ("REVIEW_MODEL", "CRITERIA_VERSION", "RENDERED_AT"):
            assert name in step["env"], name
        script = _metadata_writer_script()
        for name in ("REVIEW_MODEL", "CRITERIA_VERSION", "RENDERED_AT"):
            assert f"os.environ.get('{name}', '')" in script, name
        assert "os.environ[" not in script

    def _run_writer(
        self, tmp_path: Path, env_extra: dict[str, str], review: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        (tmp_path / "update_metadata.py").write_text(_metadata_writer_script(), encoding="utf-8")
        meta = tmp_path / "meta.yaml"
        meta.write_text(
            yaml.safe_dump(
                {
                    "library": "matplotlib",
                    "created": "2026-05-28T00:00:00Z",
                    "quality_score": None,
                    "review": review if review is not None else {"strengths": [], "weaknesses": []},
                }
            ),
            encoding="utf-8",
        )
        (tmp_path / "review_strengths.json").write_text('["clean"]', encoding="utf-8")
        (tmp_path / "review_weaknesses.json").write_text('["legend small"]', encoding="utf-8")
        (tmp_path / "review_verdict.txt").write_text("APPROVED\n", encoding="utf-8")
        env = {k: v for k, v in os.environ.items() if k not in {"REVIEW_MODEL", "CRITERIA_VERSION", "RENDERED_AT"}}
        env.update(env_extra)
        subprocess.run(
            [sys.executable, "update_metadata.py", str(meta), "91", "2026-10-02T02:31:10Z"],
            cwd=tmp_path,
            env=env,
            check=True,
            capture_output=True,
        )
        return yaml.safe_load(meta.read_text(encoding="utf-8"))

    def test_metadata_writer_runs_with_provenance(self, tmp_path):
        data = self._run_writer(
            tmp_path,
            {
                "REVIEW_MODEL": "claude-opus-5-5",
                "CRITERIA_VERSION": "qc-e1373b1495.aqr-15492a059e.sg-7006008fc6.lib-e97ebfa5c3",
                "RENDERED_AT": "2026-10-02T01:58:44Z",
            },
        )
        assert data["quality_score"] == 91
        assert data["review"]["verdict"] == "APPROVED"
        assert data["review"]["model"] == "claude-opus-5-5"
        assert data["review"]["criteria_version"].startswith("qc-e1373b1495.")
        assert data["review"]["rendered_at"] == "2026-10-02T01:58:44Z"

    def test_metadata_writer_runs_without_provenance(self, tmp_path):
        data = self._run_writer(tmp_path, {"REVIEW_MODEL": "", "CRITERIA_VERSION": " "})
        assert data["quality_score"] == 91
        assert data["review"]["weaknesses"] == ["legend small"]
        for key in ("model", "criteria_version", "rendered_at"):
            assert key not in data["review"], key

    def test_metadata_writer_drops_the_previous_reviews_provenance(self, tmp_path):
        # A repair review starts from the metadata the first review wrote; a
        # value this review could not determine must not be credited to it.
        previous = {
            "strengths": ["old"],
            "weaknesses": ["old"],
            "model": "claude-opus-5-5",
            "criteria_version": "qc-0000000000.aqr-0000000000.sg-0000000000.lib-0000000000",
            "rendered_at": "2026-10-01T00:00:00Z",
        }
        data = self._run_writer(tmp_path, {"REVIEW_MODEL": "claude-sonnet-5", "CRITERIA_VERSION": ""}, previous)
        assert data["review"]["model"] == "claude-sonnet-5"
        assert "criteria_version" not in data["review"]
        assert "rendered_at" not in data["review"]

        data = self._run_writer(tmp_path, {}, previous)
        for key in ("model", "criteria_version", "rendered_at"):
            assert key not in data["review"], key

    def test_both_regen_comments_carry_the_gate_record(self):
        block = _regen_block(_step("impl-review.yml", "Add verdict label and take action")["run"])
        assert 'regen_gate.py" marker' in block
        merge_start = block.index('if [ "$GATE_VERDICT" = "merge" ]; then')
        merge = block[merge_start : block.index("exit 0", merge_start)]
        keep = block[block.index("exit 0", merge_start) :]
        assert '"$GATE_RECORD_MARKER"' in merge
        assert "/tmp/anyplot-regen-merged.md" in merge
        assert '"$GATE_RECORD_MARKER"' in keep[: keep.index("} > /tmp/anyplot-regen-kept.md")]

    def test_merge_path_comment_never_blocks_the_merge(self):
        block = _code_only(_regen_block(_step("impl-review.yml", "Add verdict label and take action")["run"]))
        comment = block.index('gh pr comment "$PR_NUM" --body-file /tmp/anyplot-regen-merged.md')
        dispatch = block.index("gh workflow run impl-merge.yml")
        assert comment < dispatch
        line_start = block.rindex("\n", 0, comment)
        assert block[line_start:comment].strip().startswith("GH_RETRY_LEVEL=warning gh_retry")
        after = block[comment : block.index("\n", block.index("\n", comment) + 1)]
        assert '|| echo "::warning::' in after
        assert "exit 1" not in after


class TestReviewFeedbackFormat:
    """P3: defect lines and suggestions. The workflow side has no local loop,
    so these pin the wiring: the canvas weakness is a defect line, the
    reviewer's self-check has its gate copy, the format check never gates,
    and the generator sees the C ids."""

    def test_canvas_weakness_is_a_defect_line(self):
        script = _step("impl-review.yml", "Canvas dimension gate")["run"]
        assert 'f"VQ-05 (both): Canvas dimensions drifted from required target. "' in script

    def test_self_check_copy_comes_from_the_workflow_ref(self):
        script = _step("impl-review.yml", "Checkout PR code")["run"]
        copy = script[: script.index("git fetch origin")]
        assert "cp automation/scripts/regen_gate.py /tmp/anyplot-regen-gate.py" in copy

    def test_format_check_never_gates_and_runs_before_the_metadata_step(self):
        names = _step_names("impl-review.yml")
        check = names.index("Check review feedback format (never gating)")
        assert check < names.index("Update metadata and implementation header")
        assert names.index("Regen gate") < check
        step = _step("impl-review.yml", "Check review feedback format (never gating)")
        assert step["continue-on-error"] is True
        script = step["run"]
        assert '"$RUNNER_TEMP/regen-tools/regen_gate.py" check-feedback --warn-only' in script
        assert "--weaknesses review_weaknesses.json --checklist review_checklist.json" in script
        assert '[ "$IS_REGEN" = "true" ] && [ -f review_regen.json ]' in script
        assert "--prev-weaknesses /tmp/anyplot-prev-weaknesses.json" in script
        # Monitoring only: it writes no file the metadata step reads.
        assert ">" not in _code_only(script).replace("->", "")

    def test_gate_step_needs_no_new_flag(self):
        """The gate reads review_checklist.json next to --regen-json (the repo root)."""
        script = _step("impl-review.yml", "Regen gate")["run"]
        assert "--regen-json review_regen.json" in script
        assert "--checklist" not in script

    def test_generator_context_passes_the_spec_file(self):
        script = _step("impl-generate.yml", "Extract previous review feedback (regeneration)")["run"]
        assert '--spec-file "plots/${SPEC_ID}/specification.md"' in script


class TestImplGenerateHeaderReset:
    """M3: the new file's header says `Quality: pending` before the review sees it."""

    SCRIPT = _step("impl-generate.yml", "Create library metadata file")["run"]

    def test_header_is_reset_before_the_metadata_commit(self):
        reset = self.SCRIPT.index("sanitize-source --pending")
        assert self.SCRIPT.index('git ls-files --error-unmatch "$IMPL_FILE"') < reset
        assert reset < self.SCRIPT.index('git commit -m "chore(${LIBRARY}): add metadata for ${SPEC_ID}"')
        assert '--source "$IMPL_FILE" --out "$IMPL_FILE"' in self.SCRIPT
        assert 'git add "$IMPL_FILE"' in self.SCRIPT

    def test_helper_comes_from_the_workflow_ref_and_never_fails_the_step(self):
        assert 'git show "${GITHUB_SHA}:automation/scripts/regen_gate.py"' in self.SCRIPT
        block = self.SCRIPT[self.SCRIPT.index("sanitize-source --pending") :]
        assert block.index("else\n") < block.index("::warning::could not reset the Quality header")


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

    def test_case1_never_redispatches_a_regen_review(self):
        case1 = self.SCRIPT[self.SCRIPT.index("# Case 1") : self.SCRIPT.index("# Case 2:")]
        regen_guard = case1.index('if [[ "$is_regen" == "true" ]]; then')
        dispatch = case1.index("impl-review.yml -f pr_number")
        assert regen_guard < dispatch
        # The regen branch only warns.
        regen_branch = case1[regen_guard : case1.index("elif", regen_guard)]
        assert "::warning::" in regen_branch
        assert "dispatch " not in regen_branch

    def test_regen_detection_also_uses_main_checkout(self):
        assert '[[ -f "$(impl_path "$spec_id" "$library")" ]]' in self.SCRIPT
        assert 'grep -q " regen:forced "' in self.SCRIPT

    def test_case0_recloses_kept_regens(self):
        case0 = self.SCRIPT[self.SCRIPT.index("# Case 0") : self.SCRIPT.index("# Case 1")]
        assert 'grep -q " regen:kept "' in case0
        assert "gh pr close" in case0


class TestImplGenerate:
    def test_failure_handler_skips_failed_label_on_regen(self):
        script = _step("impl-generate.yml", "Handle generation failure")["run"]
        regen = script.index('if [ "$IS_LIVE" = "true" ]; then\n    # Regeneration: the implementation on main')
        failed = script.index('--add-label "impl:${LIBRARY}:failed"')
        assert regen < failed

    def test_failure_handler_detects_live_impl_from_origin_main(self):
        # REGEN_LABEL comes from a later step; a setup failure before it must
        # still preserve done, so the handler re-detects on its own.
        script = _step("impl-generate.yml", "Handle generation failure")["run"]
        detect = script.index('git cat-file -e "origin/main:plots/$SPEC_ID/implementations/$LANGUAGE/$LIBRARY$EXT"')
        assert detect < script.index("dispatch_retry() {")
        code = _code_only(script)
        # Every live-implementation branch keys on IS_LIVE, never on the label alone.
        assert code.count('[ "$IS_LIVE" = "true" ]') == 3
        assert code.count('if [ -n "$REGEN_LABEL" ]; then') == 1  # only feeding IS_LIVE

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

    def test_pick_ages_specs_without_metadata_by_issue_activity(self, tmp_path):
        """Runs the pick script for real against a fake `gh` and a fake plots/ tree."""
        workflow = yaml.safe_load((WORKFLOWS_DIR / "daily-regen.yml").read_text(encoding="utf-8"))
        run = next(s for s in workflow["jobs"]["pick"]["steps"] if s.get("id") == "pick")["run"]
        script = run.split("<<'PY'\n", 1)[1].rsplit("\nPY", 1)[0]

        now = datetime.now(timezone.utc)
        recent = (now - timedelta(hours=2)).strftime("%Y-%m-%dT%H:%M:%SZ")
        old = (now - timedelta(days=30)).strftime("%Y-%m-%dT%H:%M:%SZ")
        older = (now - timedelta(days=60)).strftime("%Y-%m-%dT%H:%M:%SZ")

        def spec(name: str, issue: int | None, updated: str | None) -> None:
            meta = tmp_path / "plots" / name / "metadata" / "python"
            meta.mkdir(parents=True)
            (meta / "altair.yaml").write_text(yaml.safe_dump({"updated": updated} if updated else {}), encoding="utf-8")
            (tmp_path / "plots" / name / "specification.md").write_text("# s\n", encoding="utf-8")
            (tmp_path / "plots" / name / "specification.yaml").write_text(
                yaml.safe_dump({"issue": issue} if issue else {}), encoding="utf-8"
            )

        spec("a-no-meta-recent-issue", 1, None)  # issue touched 2 h ago → too fresh
        spec("b-no-meta-no-issue", None, None)  # neither → ancient, picked first
        spec("c-no-meta-old-issue", 3, None)  # issue 30 d ago → eligible, aged by it
        spec("d-old-meta-recent-issue", 4, older)  # metadata old, issue fresh → too fresh

        fake_bin = tmp_path / "bin"
        fake_bin.mkdir()
        issues = [
            {"number": 1, "updatedAt": recent},
            {"number": 3, "updatedAt": old},
            {"number": 4, "updatedAt": recent},
        ]
        gh = fake_bin / "gh"
        gh.write_text(f"#!/bin/sh\ncat <<'EOF'\n{json.dumps(issues)}\nEOF\n", encoding="utf-8")
        gh.chmod(0o755)

        out = tmp_path / "gh_output"
        env = {
            **os.environ,
            "PATH": f"{fake_bin}{os.pathsep}{os.environ['PATH']}",
            "GH_REPO": "owner/repo",
            "COUNT": "10",
            "MIN_AGE_HOURS": "20",
            "SPEC_OVERRIDE": "",
            "GITHUB_OUTPUT": str(out),
        }
        subprocess.run([sys.executable, "-c", script], cwd=tmp_path, env=env, check=True, capture_output=True)
        picks = json.loads(re.search(r"^specs_json=(.*)$", out.read_text(), re.M).group(1))
        assert picks == ["b-no-meta-no-issue", "c-no-meta-old-issue"]
