"""The weekly regen review's collector: rows, flags, sample and digest, without GitHub."""

from __future__ import annotations

import importlib.util
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pytest

from automation.scripts import review_retest_metrics as metrics
from automation.scripts.regen_gate import render_record_marker


REPO_ROOT = Path(__file__).resolve().parents[3]
SCRIPT = REPO_ROOT / ".claude" / "skills" / "review-regen-week" / "collect_week.py"


@pytest.fixture(scope="module")
def cw():
    spec = importlib.util.spec_from_file_location("collect_week", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _record(**overrides: Any) -> dict[str, Any]:
    record = {
        "v": 1,
        "pr": 100,
        "spec": "bar-basic",
        "lib": "matplotlib",
        "model": "claude-opus-5",
        "prev_model": "claude-opus-5",
        "prev_stored": 88,
        "prev_rescored": 85,
        "new": 87,
        "verdict": "merge",
        "code": "merge",
        "improvements": {"total": 1, "visible": 1, "carriers": 1, "carriers_pn": 0, "unverified": 0, "code": 0},
        "regressions": 0,
        "at": "2026-10-07T03:00:00Z",
    }
    record.update(overrides)
    return record


def _review_body(score: int, deduct: str | None = None, defect: bool = True) -> str:
    items = []
    for cid in metrics.CRITERIA_IDS:
        top = 4
        value = top - 1 if cid == deduct else top
        items.append(f"- [x] {cid}: item ({value}/{top})")
    weakness = f"- {deduct} (both): too small → larger." if deduct and defect else "- Suggestion: none."
    return (
        f"## AI Review - Attempt 1/3\n\n### Score: {score}/100\n\n"
        + "\n".join(items)
        + f"\n\n### Weaknesses\n{weakness}\n\n### Verdict\n"
    )


def _comments(record: dict[str, Any] | None, review: str | None) -> list[dict[str, Any]]:
    comments = []
    if review:
        comments.append({"login": "claude[bot]", "at": "2026-10-07T03:00:00Z", "body": review})
    if record:
        body = "## Regeneration\n[impl-review](https://github.com/o/r/actions/runs/4242)\n\n" + render_record_marker(
            record
        )
        comments.append({"login": "github-actions[bot]", "at": "2026-10-07T03:01:00Z", "body": body})
    return comments


def _pull(
    number: int = 100, lib: str = "matplotlib", labels: tuple[str, ...] = ("regen", "regen:improved"), state="MERGED"
):
    return {
        "number": number,
        "headRefName": f"implementation/bar-basic/{lib}",
        "labels": [{"name": name} for name in labels],
        "state": state,
        "createdAt": "2026-10-07T02:30:00Z",
    }


PAIR = [{"name": "regen-pair-100-1", "expired": False}]


class TestRows:
    def test_merge_with_a_carrier_has_no_flags(self, cw):
        row = cw.build_row(_pull(), _comments(_record(), _review_body(87)), None, PAIR)
        assert row["verdict"] == "merge" and row["review_run"] == 4242
        assert row["flags"] == []
        assert row["renders"]["light"].endswith("/plots/bar-basic/python/matplotlib/plot-light.png")

    def test_render_url_uses_the_library_language(self, cw):
        assert "/plots/bar-basic/r/ggplot2/" in cw.render_urls("bar-basic", "ggplot2")["dark"]

    def test_merge_without_carrier_or_code_fix_is_flagged(self, cw):
        record = _record(improvements={"carriers": 0, "carriers_pn": 0, "code": 0})
        row = cw.build_row(_pull(), _comments(record, None), None, PAIR)
        assert "merge_without_carrier" in row["flags"]

    def test_code_path_merge_is_not_flagged(self, cw):
        record = _record(improvements={"carriers": 0, "carriers_pn": 0, "code": 1})
        row = cw.build_row(_pull(), _comments(record, None), None, PAIR)
        assert "merge_without_carrier" not in row["flags"]

    def test_merge_carried_only_by_p_items(self, cw):
        record = _record(improvements={"carriers": 2, "carriers_pn": 2, "code": 0})
        assert "merge_pn_only" in cw.build_row(_pull(), _comments(record, None), None, PAIR)["flags"]

    def test_silent_deduction_from_the_review_comment(self, cw):
        silent = cw.build_row(_pull(), _comments(_record(), _review_body(87, "VQ-01", defect=False)), None, PAIR)
        named = cw.build_row(_pull(), _comments(_record(), _review_body(87, "VQ-01", defect=True)), None, PAIR)
        assert silent["silent"] == ["VQ-01"] and "silent" in silent["flags"]
        assert named["silent"] == [] and "silent" not in named["flags"]

    def test_keep_with_a_big_drop_and_a_stranded_writeback(self, cw):
        record = _record(
            verdict="keep", code="no_defect_improvement", prev_stored=96, prev_rescored=81, writeback="opened"
        )
        pull = _pull(labels=("regen", "regen:kept"), state="CLOSED")
        stranded = cw.build_row(pull, _comments(record, None), {"number": 5, "merged": False}, PAIR)
        merged = cw.build_row(pull, _comments(record, None), {"number": 5, "merged": True}, PAIR)
        assert {"big_drop", "writeback_stranded"} <= set(stranded["flags"])
        assert "writeback_stranded" not in merged["flags"]

    @pytest.mark.parametrize(
        ("prev_model", "stored", "flagged"),
        [
            ("claude-opus-5", 85, True),  # same judge: 4 points is a real change
            ("claude-sonnet-4-6", 90, False),  # the Opus offset alone
            ("claude-sonnet-4-6", 96, True),  # far past the offset
            ("n/a", 90, False),
        ],
    )
    def test_big_drop_depends_on_the_judge(self, cw, prev_model, stored, flagged):
        record = _record(
            verdict="keep", code="no_defect_improvement", prev_model=prev_model, prev_stored=stored, prev_rescored=81
        )
        row = cw.build_row(_pull(labels=("regen", "regen:kept")), _comments(record, None), None, PAIR)
        assert ("big_drop" in row["flags"]) is flagged

    def test_writeback_failure_codes_are_flagged(self, cw):
        record = _record(verdict="keep", code="no_visible_improvement", writeback="invalid")
        row = cw.build_row(_pull(labels=("regen", "regen:kept")), _comments(record, None), None, PAIR)
        assert "writeback_invalid" in row["flags"]

    def test_no_rescore_is_not_a_writeback_failure(self, cw):
        record = _record(verdict="keep", code="regen_json_invalid", writeback="no_rescore")
        row = cw.build_row(_pull(labels=("regen", "regen:kept")), _comments(record, None), None, PAIR)
        assert "regen_json_invalid" in row["flags"]
        assert not [f for f in row["flags"] if f.startswith("writeback_")]

    def test_open_pr_without_record_is_stuck_and_forced_is_not(self, cw):
        stuck = cw.build_row(_pull(labels=("regen",), state="OPEN"), [], None, [])
        forced = cw.build_row(_pull(labels=("regen:forced",), state="OPEN"), [], None, [])
        assert "stuck" in stuck["flags"]
        assert forced["forced"] and forced["flags"] == []

    def test_a_fresh_open_pr_is_pending_not_stuck(self, cw):
        now = datetime(2026, 10, 7, 4, 0, tzinfo=timezone.utc)  # 90 minutes after createdAt
        row = cw.build_row(_pull(labels=("regen",), state="OPEN"), [], None, [], now=now)
        assert row["flags"] == ["pending"]

    def test_a_record_from_before_carriers_is_not_a_merge_without_carrier(self, cw):
        record = _record(improvements={"total": 1, "visible": 1})
        row = cw.build_row(_pull(), _comments(record, None), None, PAIR)
        assert "merge_without_carrier" not in row["flags"]

    def test_a_merged_writeback_wins_over_a_closed_attempt(self, cw):
        listed = [
            {"number": 12, "headRefName": "review-writeback/bar-basic/d3/100", "state": "MERGED", "mergedAt": "x"},
            {"number": 11, "headRefName": "review-writeback/bar-basic/d3/100", "state": "CLOSED", "mergedAt": None},
            {"number": 13, "headRefName": "feature/other", "state": "OPEN", "mergedAt": None},
        ]
        assert cw.map_writebacks(listed) == {100: {"number": 12, "state": "MERGED", "merged": True}}

    def test_a_marker_posted_by_someone_else_is_ignored(self, cw):
        comments = [{"login": "someone", "at": "1", "body": render_record_marker(_record())}]
        assert cw.gate_record(comments) == (None, None)

    def test_missing_pair_artifact_is_flagged(self, cw):
        assert "no_pair_artifact" in cw.build_row(_pull(), _comments(_record(), None), None, [])["flags"]


class TestAggregate:
    def _rows(self, cw):
        rows = []
        for i, (lib, new) in enumerate([("altair", 91), ("bokeh", 84), ("d3", 84)]):
            record = _record(pr=200 + i, lib=lib, new=new)
            rows.append(cw.build_row(_pull(200 + i, lib), _comments(record, _review_body(new)), None, PAIR))
        return rows

    def test_identical_vectors_within_a_spec(self, cw):
        groups = cw.identical_vectors(self._rows(cw))
        assert groups == [{"spec": "bar-basic", "libs": ["altair", "bokeh", "d3"]}]

    def test_summary_counts(self, cw):
        summary = cw.summarize(self._rows(cw), {"daily-regen.yml": {"success": 1}}, None)
        assert summary["merges"] == 3 and summary["merge_rate"] == 1.0
        assert summary["at_or_above_90"] == 1 and summary["flags"]["high_score"] == 1
        assert summary["rescore_drift_mean"] == -3.0

    def test_sample_is_seeded_and_includes_every_must(self, cw):
        rows = self._rows(cw)
        rows[1]["carriers_pn"] = 1  # a merge carried by a P item is always in the sample
        first, second = cw.render_sample(rows, "2026-10-01"), cw.render_sample(rows, "2026-10-01")
        assert first == second and 201 in first

    def test_markdown_digest_with_last_week(self, cw):
        rows = self._rows(cw)
        summary = cw.summarize(rows, {}, 12.5)
        text = cw.render_markdown(summary, rows, [200], previous=summary)
        assert "| Merge rate | 5–50 % | 100 % | 100 % |" in text
        assert "| #200 ◆ | bar-basic / altair |" in text
        assert "$12" in text or "$13" in text

    def test_records_without_newer_keys_render_as_dashes(self, cw):
        record = _record(improvements={"carriers": 1})
        row = cw.build_row(_pull(), _comments(record, None), None, PAIR)
        text = cw.render_markdown(cw.summarize([row], {}, None), [row], [], None)
        assert "1 (–, –)" in text and "None" not in text


def test_only_open_prs_come_back_from_last_week(cw):
    rows = [
        {"pr": 1, "state": "MERGED", "verdict": "merge"},
        {"pr": 2, "state": "CLOSED", "verdict": None, "forced": True},  # a finished forced regen
        {"pr": 3, "state": "OPEN", "verdict": None},
    ]
    assert cw.previously_reported(rows) == {1, 2}


def test_a_missing_previous_file_fails_fast(cw, tmp_path):
    with pytest.raises(SystemExit):
        cw.main(["--since", "2026-10-01", "--out", str(tmp_path / "w.json"), "--previous", str(tmp_path / "nope.json")])


def test_previous_summary_with_missing_keys_still_renders(cw, tmp_path):
    rows = []
    summary = cw.summarize(rows, {}, None)
    text = cw.render_markdown(summary, rows, [], previous={"regen_prs": 3})
    assert "| Regen PRs (specs) |" in text
    json.dumps(summary)  # the summary is what --out stores
