"""Tests for automation.scripts.regen_pick_pairs — daily-regen's pair mode.

The picker resumes the paused reviews and repairs first, then ages each
(spec, library) pair by its newest touch, the metadata ``updated`` or the
last real attempt (a merged or closed implementation PR, a failed
generation), keeps every pair touched within the attempt window out of the
queue, and postpones a spec whose issue just saw activity. The no-loop rule
is pinned here: a pair the gate kept, or whose generation failed, does not
come back the next night, an infrastructure failure or a generation Claude
stopped is no attempt, and a pick that cannot see its records fails closed.
A returning keep (a regression or a technical failure) holds its pair out for
the window and then lets it return at its age from before the keep, instead of
behind the whole catalogue; the second in a row ages the pair like a plain
keep. ``main`` runs against a fake ``gh`` the way the workflow calls it.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
import yaml

from automation.scripts import regen_gate
from automation.scripts import regen_pick_pairs as rp


NOW = datetime(2026, 10, 31, 2, 17, tzinfo=timezone.utc)
MIN_AGE = timedelta(hours=20)
WINDOW = timedelta(days=30)
LIBS = ["altair", "matplotlib", "plotly"]
SCRIPT = Path(rp.__file__)


def ts(days: float, now: datetime = NOW) -> str:
    return (now - timedelta(days=days)).strftime("%Y-%m-%dT%H:%M:%SZ")


def at(days: float) -> datetime:
    return NOW - timedelta(days=days)


def write_spec(root: Path, spec: str, metadata: dict[str, dict | str | None], issue: int | None = None) -> None:
    spec_dir = root / spec
    spec_dir.mkdir(parents=True)
    (spec_dir / "specification.md").write_text("# s\n", encoding="utf-8")
    (spec_dir / "specification.yaml").write_text(yaml.safe_dump({"issue": issue} if issue else {}), encoding="utf-8")
    for lib, data in metadata.items():
        lang = "javascript" if lib == "chartjs" else "python"
        meta = spec_dir / "metadata" / lang
        meta.mkdir(parents=True, exist_ok=True)
        text = data if isinstance(data, str) else yaml.safe_dump(data or {})
        (meta / f"{lib}.yaml").write_text(text, encoding="utf-8")


def records(**kw) -> rp.Records:
    return rp.Records(
        attempts=kw.get("attempts", {}),
        open_pairs=kw.get("open_pairs", set()),
        issue_activity=kw.get("issues", {}),
        held=kw.get("held", {}),
    )


def held(*keeps: tuple[int, float, str]) -> dict[int, tuple[datetime, str]]:
    """A pair's returning keeps for ``Records.held``: (PR, days ago, code) each."""
    return {number: (at(days), f"keep #{number} ({code})") for number, days, code in keeps}


def gate_comment(
    number: int, spec: str, lib: str, code: str = "regression", login: str = "github-actions", days: float = 1
) -> dict:
    """impl-review's verdict comment as ``gh pr list --json comments`` returns it."""
    record = {"v": 1, "pr": number, "spec": spec, "lib": lib, "verdict": "keep", "code": code}
    body = f"## Regeneration kept\n\n{regen_gate.render_record_marker(record)}\n"
    return {"author": {"login": login}, "createdAt": ts(days), "body": body}


def kept_pr(number: int, spec: str, lib: str, *comments: dict, days: float = 1) -> dict:
    """A kept regeneration as the gate-record listing returns it."""
    head = f"implementation/{spec}/{lib}"
    return {"number": number, "headRefName": head, "state": "CLOSED", "closedAt": ts(days), "comments": list(comments)}


def run_pick(cands, recs=None, issues=None, count=5, window=WINDOW, failures=None, max_reads=100):
    return rp.pick(cands, recs or records(), issues or {}, NOW, MIN_AGE, window, count, failures, max_reads)


def picked(picks: list[rp.Pick]) -> list[str]:
    return [f"{p.spec}/{p.library}" for p in picks]


def fail_comment(spec: str, lib: str, days: float, infra: bool = False) -> dict[str, str]:
    body = f"<!-- impl-fail:{spec}:{lib} -->\n" + (f"{rp.INFRA_TAG}\n" if infra else "") + "## Failed"
    return {"created_at": ts(days), "body": body}


class TestLoadCandidates:
    def test_reads_every_supported_pair_with_its_timestamp(self, tmp_path):
        write_spec(tmp_path, "a", {"altair": {"updated": ts(10)}, "plotly": {"created": ts(30)}}, issue=7)
        cands, issues = rp.load_candidates(tmp_path, LIBS)
        assert {(c.spec, c.library, c.metadata) for c in cands} == {("a", "altair", at(10)), ("a", "plotly", at(30))}
        assert issues == {"a": 7}

    def test_skips_unsupported_libraries_and_specs_without_specification(self, tmp_path):
        write_spec(tmp_path, "a", {"chartjs": {"updated": ts(10)}, "legacy": {"updated": ts(10)}})
        (tmp_path / "no-spec" / "metadata" / "python").mkdir(parents=True)
        (tmp_path / "no-spec" / "metadata" / "python" / "altair.yaml").write_text("updated: x\n", encoding="utf-8")
        assert rp.load_candidates(tmp_path, LIBS)[0] == []
        assert [c.library for c in rp.load_candidates(tmp_path, [*LIBS, "chartjs"])[0]] == ["chartjs"]

    def test_unparseable_timestamp_skips_the_pair_and_missing_one_keeps_it(self, tmp_path):
        write_spec(tmp_path, "a", {"altair": {"updated": "not a date"}, "plotly": {}, "matplotlib": "- a list\n"})
        cands, _ = rp.load_candidates(tmp_path, LIBS)
        assert [(c.library, c.metadata) for c in cands] == [("plotly", None)]


class TestPick:
    def test_oldest_first_across_specs(self):
        cands = [
            rp.Candidate("a", "altair", at(40)),
            rp.Candidate("b", "plotly", at(90)),
            rp.Candidate("a", "plotly", at(60)),
        ]
        picks, eligible = run_pick(cands, count=2)
        assert picked(picks) == ["b/plotly", "a/plotly"]
        assert eligible == 3

    def test_a_kept_pair_waits_out_the_window(self):
        # The gate kept a/altair 10 days ago: `updated` is still 200 days old.
        cands = [rp.Candidate("a", "altair", at(200)), rp.Candidate("b", "plotly", at(60))]
        recs = records(attempts={("a", "altair"): (at(10), "kept PR")})
        assert picked(run_pick(cands, recs)[0]) == ["b/plotly"]

    def test_after_the_window_an_attempt_queues_behind_older_pairs(self):
        cands = [rp.Candidate("a", "altair", at(200)), rp.Candidate("b", "plotly", at(60))]
        recs = records(attempts={("a", "altair"): (at(45), "kept PR")})
        picks, _ = run_pick(cands, recs)
        assert picked(picks) == ["b/plotly", "a/altair"]
        assert picks[1].basis == "kept PR" and picks[1].touched == at(45)

    def test_a_recent_merge_is_inside_the_window_too(self):
        cands = [rp.Candidate("a", "altair", at(12)), rp.Candidate("a", "plotly", at(31))]
        assert picked(run_pick(cands)[0]) == ["a/plotly"]

    def test_window_zero_orders_only(self):
        cands = [rp.Candidate("a", "altair", at(2)), rp.Candidate("a", "plotly", at(1))]
        assert picked(run_pick(cands, window=timedelta(0))[0]) == ["a/altair", "a/plotly"]

    def test_open_pr_skips_only_its_pair(self):
        cands = [rp.Candidate("a", "altair", at(60)), rp.Candidate("a", "plotly", at(70))]
        assert picked(run_pick(cands, records(open_pairs={("a", "plotly")}))[0]) == ["a/altair"]

    def test_recent_issue_activity_postpones_every_pair_of_the_spec(self):
        cands = [rp.Candidate("a", "altair", at(60)), rp.Candidate("b", "altair", at(40))]
        recs = records(issues={1: at(0.3), 2: at(3)})
        assert picked(run_pick(cands, recs, {"a": 1, "b": 2})[0]) == ["b/altair"]

    def test_issue_activity_is_a_gate_not_an_age(self):
        cands = [rp.Candidate("a", "altair", at(60)), rp.Candidate("b", "altair", at(50))]
        picks, _ = run_pick(cands, records(issues={1: at(2)}), {"a": 1}, count=1)
        assert picked(picks) == ["a/altair"] and picks[0].touched == at(60)

    def test_no_timestamp_at_all_is_ancient(self):
        cands = [rp.Candidate("a", "altair", at(300)), rp.Candidate("b", "altair", None)]
        picks, _ = run_pick(cands, count=2)
        assert picked(picks) == ["b/altair", "a/altair"]
        assert picks[0].touched == rp.ANCIENT and picks[0].basis == "none"

    def test_ties_break_by_spec_then_library(self):
        cands = [rp.Candidate("b", "altair", at(90)), rp.Candidate("a", "plotly", at(90))]
        cands.append(rp.Candidate("a", "altair", at(90)))
        assert picked(run_pick(cands, count=3)[0]) == ["a/altair", "a/plotly", "b/altair"]


class TestFailedGenerations:
    def test_a_failed_generation_is_an_attempt(self):
        cands = [rp.Candidate("a", "altair", at(200)), rp.Candidate("a", "plotly", at(150))]
        cands.append(rp.Candidate("b", "altair", at(100)))
        asked: list[str] = []

        def failures(spec):
            asked.append(spec)
            return {"altair": at(3)} if spec == "a" else {}

        picks, eligible = run_pick(cands, count=2, failures=failures)
        # a/altair failed three days ago: out for the window; its sibling is not.
        assert picked(picks) == ["a/plotly", "b/altair"]
        assert eligible == 2
        assert asked == ["a", "b"]  # once per spec, only for the front of the queue

    def test_an_old_failure_re_ages_the_pair(self):
        cands = [rp.Candidate("a", "altair", at(200)), rp.Candidate("b", "altair", at(100))]
        picks, _ = run_pick(cands, count=2, failures=lambda spec: {"altair": at(40)} if spec == "a" else {})
        assert picked(picks) == ["b/altair", "a/altair"]
        assert picks[1].basis == "failed generation"

    def test_comments_count_only_real_failures(self):
        comments = [
            fail_comment("a", "altair", 5),
            fail_comment("a", "altair", 2, infra=True),  # infrastructure: no attempt
            fail_comment("a", "plotly", 1, infra=True),
            fail_comment("other", "altair", 1),  # another spec's marker
            {"created_at": ts(1), "body": "<!-- impl-paused-claude:a:plotly -->"},  # Claude stopped the session
        ]
        assert rp.failed_generations(comments, "a") == {"altair": at(5)}

    def test_unreadable_failures_leave_the_spec_out(self, capsys):
        cands = [rp.Candidate("a", "altair", at(200)), rp.Candidate("a", "plotly", at(190))]
        cands.append(rp.Candidate("b", "altair", at(100)))
        picks, eligible = run_pick(cands, count=3, failures=lambda spec: None if spec == "a" else {})
        # Fail closed: a's pairs may have failed last night.
        assert picked(picks) == ["b/altair"] and eligible == 1
        assert "::warning::Leaving a out of tonight" in capsys.readouterr().out

    def test_the_read_cap_stops_reading(self, capsys):
        cands = [rp.Candidate(spec, "altair", at(100 + i)) for i, spec in enumerate("abc")]
        asked: list[str] = []
        picks, _ = run_pick(cands, count=3, failures=lambda spec: asked.append(spec) or {}, max_reads=1)
        assert len(picks) == 3 and asked == ["c"]
        assert "::warning::Read the failed generations of 1 specs" in capsys.readouterr().out


class TestRegressionKeeps:
    """A returning keep holds the pair for the window, then it returns at its age."""

    HOLD = "keep #31 (regression)"

    def test_inside_the_window_the_pair_is_held(self):
        cands = [rp.Candidate("a", "altair", at(200)), rp.Candidate("b", "plotly", at(60))]
        recs = records(held={("a", "altair"): held((31, 10, "regression"))})
        picks, eligible = run_pick(cands, recs)
        assert picked(picks) == ["b/plotly"] and eligible == 1

    def test_after_the_window_it_returns_at_its_age(self):
        # The same keep as a plain attempt queues behind b/plotly
        # (test_after_the_window_an_attempt_queues_behind_older_pairs).
        cands = [rp.Candidate("a", "altair", at(200)), rp.Candidate("b", "plotly", at(60))]
        recs = records(held={("a", "altair"): held((31, 45, "regression"))})
        picks, _ = run_pick(cands, recs)
        assert picked(picks) == ["a/altair", "b/plotly"]
        assert picks[0].touched == at(200)
        assert picks[0].basis == f"metadata, back after {self.HOLD} of {at(45):%Y-%m-%d}"
        assert picks[1].basis == "metadata"

    def test_a_technical_keep_returns_too(self):
        cands = [rp.Candidate("a", "altair", at(200)), rp.Candidate("b", "plotly", at(60))]
        recs = records(held={("a", "altair"): held((31, 45, "canvas_failed"))})
        picks, _ = run_pick(cands, recs)
        assert picked(picks) == ["a/altair", "b/plotly"]
        assert picks[0].basis == f"metadata, back after keep #31 (canvas_failed) of {at(45):%Y-%m-%d}"

    def test_the_second_returning_keep_in_a_row_ages_the_pair(self):
        # First keep 80 days ago (returned), second 45 days ago: now the pair
        # ages from the second keep and queues behind b/plotly.
        cands = [rp.Candidate("a", "altair", at(200)), rp.Candidate("b", "plotly", at(60))]
        recs = records(held={("a", "altair"): held((31, 80, "regression"), (32, 45, "regression"))})
        picks, _ = run_pick(cands, recs)
        assert picked(picks) == ["b/plotly", "a/altair"]
        assert picks[1].touched == at(45) and picks[1].basis == "keep #32 (regression), 2 in a row"

    def test_the_second_in_a_row_counts_across_codes(self):
        cands = [rp.Candidate("a", "altair", at(200)), rp.Candidate("b", "plotly", at(60))]
        recs = records(held={("a", "altair"): held((31, 80, "script_crashed"), (32, 45, "regression"))})
        assert picked(run_pick(cands, recs)[0]) == ["b/plotly", "a/altair"]

    def test_the_second_in_a_row_inside_the_window_holds_like_a_plain_keep(self):
        cands = [rp.Candidate("a", "altair", at(200)), rp.Candidate("b", "plotly", at(60))]
        recs = records(held={("a", "altair"): held((31, 50, "regression"), (32, 10, "regression"))})
        picks, eligible = run_pick(cands, recs)
        assert picked(picks) == ["b/plotly"] and eligible == 1

    def test_an_attempt_between_two_keeps_ends_the_streak(self):
        # A merge, a failed generation or a plain keep between them: the second
        # keep is the first of a new streak and returns.
        cands = [rp.Candidate("a", "altair", at(200)), rp.Candidate("b", "plotly", at(60))]
        recs = records(
            attempts={("a", "altair"): (at(70), "kept PR")},
            held={("a", "altair"): held((31, 80, "regression"), (32, 45, "regression"))},
        )
        picks, _ = run_pick(cands, recs)
        assert picked(picks) == ["a/altair", "b/plotly"]
        assert picks[0].touched == at(70) and picks[0].basis.startswith("kept PR, back after keep #32")

    def test_a_third_returning_keep_starts_a_new_streak(self):
        cands = [rp.Candidate("a", "altair", at(200)), rp.Candidate("b", "plotly", at(60))]
        keeps = held((31, 120, "regression"), (32, 90, "regression"), (33, 45, "regression"))
        picks, _ = run_pick(cands, records(held={("a", "altair"): keeps}))
        # The second keep aged the pair (90 days ago); the third returns to that age.
        assert picked(picks) == ["a/altair", "b/plotly"]
        assert picks[0].touched == at(90) and "back after keep #33 (regression)" in picks[0].basis

    def test_the_age_is_the_one_from_before_the_keep(self):
        # An older plain keep still ages the pair; only the returning keep doesn't.
        cands = [rp.Candidate("a", "altair", at(200)), rp.Candidate("b", "plotly", at(120))]
        recs = records(
            attempts={("a", "altair"): (at(100), "kept PR")}, held={("a", "altair"): held((31, 40, "regression"))}
        )
        picks, _ = run_pick(cands, recs)
        assert picked(picks) == ["b/plotly", "a/altair"]
        assert picks[1].touched == at(100) and picks[1].basis.startswith("kept PR, back after")

    def test_a_newer_merge_ends_the_hold(self):
        # Merged after the keep: the metadata is the age and the window counts from it.
        cands = [rp.Candidate("a", "altair", at(40)), rp.Candidate("a", "plotly", at(12))]
        keep = held((31, 50, "regression"))
        recs = records(held={("a", "altair"): keep, ("a", "plotly"): keep})
        picks, _ = run_pick(cands, recs)
        assert picked(picks) == ["a/altair"] and picks[0].basis == "metadata"

    def test_a_later_failed_generation_ages_the_pair(self):
        cands = [rp.Candidate("a", "altair", at(200)), rp.Candidate("b", "plotly", at(60))]
        recs = records(held={("a", "altair"): held((31, 50, "regression"))})
        picks, _ = run_pick(cands, recs, failures=lambda spec: {"altair": at(35)} if spec == "a" else {})
        assert picked(picks) == ["b/plotly", "a/altair"]
        assert picks[1].touched == at(35) and picks[1].basis == "failed generation"

    def test_a_failure_older_than_the_keep_moves_the_age_only(self):
        cands = [rp.Candidate("a", "altair", at(200)), rp.Candidate("b", "plotly", at(120))]
        recs = records(held={("a", "altair"): held((31, 40, "regression"))})
        picks, _ = run_pick(cands, recs, failures=lambda spec: {"altair": at(100)} if spec == "a" else {})
        assert picked(picks) == ["b/plotly", "a/altair"]
        assert picks[1].touched == at(100) and picks[1].basis.startswith("failed generation, back after")

    def test_a_failure_between_two_keeps_read_late_lets_the_pair_return(self):
        # Without the failure the second keep ages the pair (35 days); the
        # failure read at the front of the queue ends the streak, so the pair
        # is back at the failure's age and pops right back out.
        cands = [rp.Candidate("a", "altair", at(200)), rp.Candidate("b", "plotly", at(33))]
        recs = records(held={("a", "altair"): held((31, 80, "regression"), (32, 35, "regression"))})
        picks, _ = run_pick(cands, recs, failures=lambda spec: {"altair": at(60)} if spec == "a" else {})
        assert picked(picks) == ["a/altair", "b/plotly"]
        assert picks[0].touched == at(60) and picks[0].basis.startswith("failed generation, back after keep #32")

    def test_a_failure_inside_the_window_drops_the_pair(self):
        cands = [rp.Candidate("a", "altair", at(200)), rp.Candidate("b", "plotly", at(60))]
        recs = records(held={("a", "altair"): held((31, 50, "regression"))})
        picks, eligible = run_pick(cands, recs, failures=lambda spec: {"altair": at(3)} if spec == "a" else {})
        assert picked(picks) == ["b/plotly"] and eligible == 1


class TestReturningKeeps:
    def test_a_workflow_record_with_a_return_code_counts(self):
        pulls = [
            kept_pr(31, "a", "altair", gate_comment(31, "a", "altair")),
            kept_pr(32, "a", "plotly", gate_comment(32, "a", "plotly", login="github-actions[bot]")),  # REST shape
            kept_pr(33, "b", "altair", gate_comment(33, "b", "altair", code="no_visible_improvement")),
            kept_pr(34, "b", "plotly"),  # no record at all
            kept_pr(35, "c", "altair", gate_comment(35, "c", "altair", code="script_crashed")),
            kept_pr(36, "c", "plotly", gate_comment(36, "c", "plotly", code="adapt_regression")),
        ]
        assert rp.returning_keeps(pulls) == {31: "regression", 32: "regression", 35: "script_crashed"}

    def test_a_record_must_be_the_workflows_and_name_its_pr_and_pair(self):
        pulls = [
            kept_pr(41, "a", "altair", gate_comment(41, "a", "altair", login="someone")),  # a pasted marker
            kept_pr(42, "a", "plotly", gate_comment(12515, "a", "plotly")),  # copied from another PR
            kept_pr(43, "b", "altair", gate_comment(43, "b", "plotly")),  # another pair
            {
                "number": 44,
                "headRefName": "review-writeback/b/plotly/44",
                "comments": [gate_comment(44, "b", "plotly")],
            },
            {"headRefName": "implementation/c/altair", "comments": [gate_comment(45, "c", "altair")]},  # no number
        ]
        assert rp.returning_keeps(pulls) == {}

    def test_the_first_workflow_record_wins(self):
        first = gate_comment(51, "a", "altair", code="below_tolerance", days=3)
        later = gate_comment(51, "a", "altair", days=1)
        assert rp.returning_keeps([kept_pr(51, "a", "altair", later, first)]) == {}

    def test_an_invalid_record_is_no_record(self):
        record = {"v": 1, "pr": 61, "spec": "a", "lib": "altair", "verdict": "keep", "code": "made_up"}
        forged = {"author": {"login": "github-actions"}, "createdAt": ts(2)}
        forged["body"] = f"<!-- regen-gate-record:v1 {json.dumps(record, separators=(',', ':'))} -->"
        assert rp.returning_keeps([kept_pr(61, "a", "altair", forged)]) == {}
        # ...so a valid record after it is the first one.
        both = kept_pr(61, "a", "altair", forged, gate_comment(61, "a", "altair"))
        assert rp.returning_keeps([both]) == {61: "regression"}

    @pytest.mark.parametrize("comments", [2, None, "text", {"body": "x"}])
    def test_an_unexpected_comments_shape_is_no_record(self, comments):
        """A count or any other non-list costs the return, never the night."""
        good = kept_pr(71, "a", "altair", gate_comment(71, "a", "altair"))
        odd = {"number": 72, "headRefName": "implementation/a/plotly", "state": "CLOSED", "comments": comments}
        assert rp.returning_keeps([odd, good, "not a pull"]) == {71: "regression"}

    def test_the_return_codes_are_the_regression_and_the_technical_keeps(self):
        judged = {"no_visible_improvement", "no_defect_improvement", "below_tolerance", "score_zero"}
        assert set(regen_gate.REASON_CODES) - {"merge", "adapt_identity"} == rp.RETURN_CODES | judged | {
            "adapt_regression"
        }
        assert "adapt_regression" not in rp.RETURN_CODES and not judged & rp.RETURN_CODES


class TestFoldPulls:
    def test_a_returning_keep_holds_instead_of_aging(self):
        recs = records()
        kept_31 = pr("implementation/a/altair", "CLOSED", 31, ("regen:kept",), closedAt=ts(5))
        rp.fold_pulls(
            [
                kept_31,
                kept_31,  # the same PR from the second listing: one keep
                pr("implementation/a/altair", "CLOSED", 30, ("regen:kept",), closedAt=ts(40)),
                pr("implementation/a/plotly", "CLOSED", 32, ("regen:kept",), closedAt=ts(6)),
                pr("implementation/b/altair", "MERGED", 33, (), closedAt=ts(7)),  # a merge never holds
                pr("implementation/b/plotly", "CLOSED", 34, (), closedAt=ts(8)),  # closed, not kept
            ],
            recs,
            returning={30: "canvas_failed", 31: "regression", 33: "regression", 34: "regression"},
        )
        assert recs.held == {("a", "altair"): held((31, 5, "regression"), (30, 40, "canvas_failed"))}
        assert recs.attempts == {
            ("a", "plotly"): (at(6), "kept PR"),
            ("b", "altair"): (at(7), "merged PR"),
            ("b", "plotly"): (at(8), "closed PR"),
        }

    def test_open_blocks_closed_and_merged_count(self):
        recs = records()
        rp.fold_pulls(
            [
                {"headRefName": "implementation/a/altair", "state": "MERGED", "closedAt": ts(9), "updatedAt": ts(1)},
                {"headRefName": "implementation/a/altair", "state": "CLOSED", "closedAt": ts(40), "labels": []},
                {
                    "headRefName": "implementation/a/plotly",
                    "state": "CLOSED",
                    "closedAt": ts(3),
                    "labels": [{"name": "regen"}, {"name": "regen:kept"}],
                },
                {"headRefName": "implementation/b/plotly", "state": "OPEN", "updatedAt": ts(1)},
                {"headRefName": "review-writeback/a/altair/12", "state": "MERGED", "closedAt": ts(0)},
                {"headRefName": "implementation/a/altair/extra", "state": "CLOSED", "closedAt": ts(0)},
            ],
            recs,
        )
        assert recs.attempts == {("a", "altair"): (at(9), "merged PR"), ("a", "plotly"): (at(3), "kept PR")}
        assert recs.open_pairs == {("b", "plotly")}
        assert recs.paused == []

    def test_paused_prs_become_resumes(self):
        recs = records()
        review = {
            "number": 21,
            "headRefName": "implementation/a/plotly",
            "state": "OPEN",
            "updatedAt": ts(2),
            "labels": [{"name": "ai-review-paused"}],
        }
        repair = {
            "number": 22,
            "headRefName": "implementation/b/altair",
            "state": "OPEN",
            "updatedAt": ts(3),
            "labels": [{"name": n} for n in ("ai-rejected", "ai-attempt-1", "ai-attempt-2", "ai-repair-paused")],
        }
        # A paused PR that is closed meanwhile is an attempt, not a resume.
        closed = {**review, "number": 23, "headRefName": "implementation/c/plotly", "state": "CLOSED"}
        rp.fold_pulls([review, repair, closed, review], recs)  # the same PR twice: listed once
        assert recs.open_pairs == {("a", "plotly"), ("b", "altair")}
        assert recs.paused == [
            rp.Resume(21, "review", "a", "plotly", 1, at(2)),
            rp.Resume(22, "repair", "b", "altair", 2, at(3)),
        ]
        assert [r.pr for r in rp.resumes(recs, 5)] == [22, 21]  # oldest first
        assert [r.pr for r in rp.resumes(recs, 1)] == [22]

    def test_issues(self):
        recs = records()
        rp.fold_issues([{"number": 3, "updatedAt": ts(2)}, {"number": "x", "updatedAt": ts(1)}], recs)
        assert recs.issue_activity == {3: at(2)}


# Answers each listing the picker makes from a JSON file named after it, and an
# issue's comments (`api … --jq …`) from comments-<issue>.jsonl; a listing
# whose file is missing fails like an API error. Logs every call.
FAKE_GH = """#!/bin/sh
echo "$*" >> "$GH_LOG"
case "$*" in
  *"head:implementation/"*) f=prs.json ;;
  *"state,comments"*"regen:kept"*) f=gates.json ;;
  *"regen:kept"*) f=kept.json ;;
  "issue list"*) f=issues.json ;;
  "api --paginate repos/o/r/issues/"*) n=${3#repos/o/r/issues/}; f=comments-${n%%/*}.jsonl ;;
  *) exit 1 ;;
esac
[ -f "$GH_DATA/$f" ] || { echo "HTTP 502" >&2; exit 1; }
cat "$GH_DATA/$f"
"""


def run_main(tmp_path: Path, data: dict[str, str], count: int = 3, *extra: str):
    bin_dir, data_dir = tmp_path / "bin", tmp_path / "data"
    bin_dir.mkdir()
    data_dir.mkdir()
    (bin_dir / "gh").write_text(FAKE_GH, encoding="utf-8")
    (bin_dir / "gh").chmod(0o755)
    for name, text in data.items():
        (data_dir / name).write_text(text, encoding="utf-8")
    out, summary = tmp_path / "out", tmp_path / "summary"
    env = {
        **os.environ,
        "PATH": f"{bin_dir}{os.pathsep}{os.environ['PATH']}",
        "GH_LOG": str(tmp_path / "gh.log"),
        "GH_DATA": str(data_dir),
        "GITHUB_OUTPUT": str(out),
        "GITHUB_STEP_SUMMARY": str(summary),
    }
    args = ["--count", str(count), "--min-age-hours", "20", "--repo", "o/r", "--libraries", " ".join(LIBS), *extra]
    result = subprocess.run(
        [sys.executable, str(SCRIPT), *args, "--plots", str(tmp_path / "plots")],
        env=env,
        capture_output=True,
        text=True,
    )
    outputs = dict(line.split("=", 1) for line in out.read_text().splitlines()) if out.exists() else {}
    return result, outputs, summary.read_text() if summary.exists() else ""


class TestMain:
    def _plots(self, tmp_path: Path) -> None:
        self.now = datetime.now(timezone.utc)
        plots = tmp_path / "plots"
        write_spec(
            plots, "a-spec", {"altair": {"updated": ts(190, self.now)}, "plotly": {"updated": ts(160, self.now)}}, 11
        )
        write_spec(
            plots,
            "b-spec",
            {"altair": {"updated": ts(180, self.now)}, "matplotlib": {"updated": ts(170, self.now)}},
            12,
        )

    def test_writes_pairs_specs_and_summary(self, tmp_path):
        self._plots(tmp_path)
        prs = [{"headRefName": "implementation/b-spec/matplotlib", "state": "OPEN", "updatedAt": ts(0.1, self.now)}]
        kept = [
            {
                "headRefName": "implementation/a-spec/altair",
                "state": "CLOSED",
                "closedAt": ts(40, self.now),
                "labels": [{"name": "regen:kept"}],
            }
        ]
        comments = [
            {"created_at": ts(5, self.now), "body": "<!-- impl-fail:b-spec:altair -->\n<!-- impl-fail-cause:infra -->"}
        ]
        result, outputs, summary = run_main(
            tmp_path,
            {
                "prs.json": json.dumps(prs),
                "kept.json": json.dumps(kept),
                "issues.json": json.dumps([{"number": 11, "updatedAt": ts(7, self.now)}]),
                "comments-11.jsonl": "",
                "comments-12.jsonl": "\n".join(json.dumps(c) for c in comments),
            },
        )
        assert result.returncode == 0, result.stdout + result.stderr
        # b-spec/matplotlib has an open PR; a-spec/altair was kept 40 days ago,
        # so it queues last; b-spec/altair's infrastructure failure is no attempt.
        assert json.loads(outputs["pairs_json"]) == [
            {"spec": "b-spec", "library": "altair"},
            {"spec": "a-spec", "library": "plotly"},
            {"spec": "a-spec", "library": "altair"},
        ]
        assert json.loads(outputs["specs_json"]) == ["b-spec", "a-spec"]
        assert outputs["specs"] == "b-spec a-spec" and outputs["count"] == "3"
        assert "| 3 | `a-spec` | `altair` |" in summary and "kept PR" in summary
        log = (tmp_path / "gh.log").read_text()
        assert "repos/o/r/issues/12/comments?per_page=100" in log and "run list" not in log

    def test_a_keep_on_a_regression_returns_at_its_age(self, tmp_path):
        without, with_records = tmp_path / "without", tmp_path / "with"
        self._plots(without)
        self._plots(with_records)
        kept = [
            {
                "number": 31,
                "headRefName": "implementation/a-spec/altair",
                "state": "CLOSED",
                "closedAt": ts(40, self.now),
                "labels": [{"name": "regen:kept"}],
            }
        ]
        gates = [kept_pr(31, "a-spec", "altair", gate_comment(31, "a-spec", "altair"))]
        data = {"prs.json": json.dumps(kept), "kept.json": json.dumps(kept), "issues.json": "[]"}
        data |= {"comments-11.jsonl": "", "comments-12.jsonl": ""}
        # Without its gate record (the listing fails) the keep ages the pair: it queues last.
        result, outputs, _ = run_main(without, data, 4)
        assert "::warning::Could not list kept regenerations' gate records" in result.stdout
        assert json.loads(outputs["pairs_json"])[-1] == {"spec": "a-spec", "library": "altair"}
        # With it, a-spec/altair is back at its metadata age, the oldest of all.
        result, outputs, summary = run_main(with_records, data | {"gates.json": json.dumps(gates)}, 4)
        assert result.returncode == 0, result.stdout + result.stderr
        assert json.loads(outputs["pairs_json"])[0] == {"spec": "a-spec", "library": "altair"}
        assert (
            f"| 1 | `a-spec` | `altair` | {ts(190, self.now)} | metadata, back after keep #31 (regression) of"
            in summary
        )
        assert "returning keeps for 1 pair(s)" in result.stdout

    def test_the_window_comes_from_the_argument(self, tmp_path):
        self._plots(tmp_path)
        kept = [{"headRefName": "implementation/a-spec/altair", "state": "CLOSED", "closedAt": ts(40, self.now)}]
        data = {"prs.json": "[]", "kept.json": json.dumps(kept), "issues.json": "[]"}
        data |= {"comments-11.jsonl": "", "comments-12.jsonl": ""}
        _, outputs, _ = run_main(tmp_path, data, 5, "--attempt-window-days", "60")
        # Kept 40 days ago is inside a 60-day window.
        pairs = {(p["spec"], p["library"]) for p in json.loads(outputs["pairs_json"])}
        assert pairs == {("a-spec", "plotly"), ("b-spec", "altair"), ("b-spec", "matplotlib")}

    def _paused(self) -> dict[str, str]:
        prs = [
            {
                "number": 21,
                "headRefName": "implementation/a-spec/plotly",
                "state": "OPEN",
                "updatedAt": ts(2, self.now),
                "labels": [{"name": "ai-review-paused"}],
            },
            {
                "number": 22,
                "headRefName": "implementation/b-spec/altair",
                "state": "OPEN",
                "updatedAt": ts(3, self.now),
                "labels": [{"name": "ai-rejected"}, {"name": "ai-attempt-2"}, {"name": "ai-repair-paused"}],
            },
        ]
        data = {"prs.json": json.dumps(prs), "kept.json": "[]", "issues.json": "[]"}
        return data | {"comments-11.jsonl": "", "comments-12.jsonl": ""}

    def test_paused_prs_are_resumed_before_new_pairs(self, tmp_path):
        self._plots(tmp_path)
        result, outputs, summary = run_main(tmp_path, self._paused(), 3)
        assert result.returncode == 0, result.stdout + result.stderr
        # Both resumes count against the night's three; their pairs are open, so
        # the one new pair is the oldest of the rest.
        assert json.loads(outputs["resume_json"]) == [
            {"pr": 22, "kind": "repair", "spec": "b-spec", "library": "altair", "attempt": 2},
            {"pr": 21, "kind": "review", "spec": "a-spec", "library": "plotly", "attempt": 1},
        ]
        assert outputs["resume_count"] == "2"
        assert json.loads(outputs["pairs_json"]) == [{"spec": "a-spec", "library": "altair"}]
        assert outputs["count"] == "1"
        assert "Pair mode: 2 resumed, 1 new pair(s) of 3" in summary and "| repair | #22 |" in summary

    def test_resumes_can_take_the_whole_night(self, tmp_path):
        self._plots(tmp_path)
        _, outputs, _ = run_main(tmp_path, self._paused(), 1)
        assert json.loads(outputs["resume_json"])[0]["pr"] == 22
        assert outputs["resume_count"] == "1" and outputs["count"] == "0" and outputs["pairs_json"] == "[]"

    def test_a_failed_implementation_pr_listing_stops_the_pick(self, tmp_path):
        """The loop guard: without it a kept, closed or paused pair would be picked again."""
        self._plots(tmp_path)
        result, outputs, _ = run_main(tmp_path, {"kept.json": "[]", "issues.json": "[]"}, 1)
        assert result.returncode == 1
        assert "::error::Pair mode stops: the implementation PRs could not be listed" in result.stdout
        assert outputs == {}

    def test_the_other_listings_degrade_with_a_warning(self, tmp_path):
        self._plots(tmp_path)
        result, outputs, _ = run_main(tmp_path, {"prs.json": "[]", "comments-12.jsonl": ""}, 1)
        assert result.returncode == 0, result.stdout + result.stderr
        assert result.stdout.count("::warning::Could not list") == 3  # kept, gate records, issues
        # a-spec's comments cannot be read: it is left out, b-spec/altair is next.
        assert "::warning::Could not read the comments of issue #11" in result.stdout
        assert json.loads(outputs["pairs_json"]) == [{"spec": "b-spec", "library": "altair"}]

    def test_nothing_eligible_writes_an_empty_pick(self, tmp_path):
        (tmp_path / "plots").mkdir()
        result, outputs, _ = run_main(tmp_path, {"prs.json": "[]", "kept.json": "[]", "issues.json": "[]"})
        assert result.returncode == 0, result.stdout + result.stderr
        assert outputs == {
            "resume_json": "[]",
            "resume_count": "0",
            "pairs_json": "[]",
            "specs": "",
            "specs_json": "[]",
            "count": "0",
        }

    @pytest.mark.parametrize(("count", "window"), [(0, "30"), (-1, "30"), (1, "-1")])
    def test_refuses_bad_numbers(self, tmp_path, count, window):
        (tmp_path / "plots").mkdir()
        result, _, _ = run_main(tmp_path, {}, count, "--attempt-window-days", window)
        assert result.returncode == 1 and "::error::" in result.stdout


# --- the same paths in process ------------------------------------------------


class FakeRunner:
    """Stands in for ``subprocess.run``: answers each ``gh`` call the picker makes from ``data``.

    The keys are ``prs``, ``kept``, ``gates``, ``issues`` and ``comments-<issue>``;
    a value that is an exception is raised, and a missing key fails like an API
    error.
    """

    def __init__(self, data: dict[str, str | BaseException]):
        self.data = data
        self.calls: list[list[str]] = []

    @staticmethod
    def key(args: list[str]) -> str:
        joined = " ".join(args)
        if "head:implementation/" in joined:
            return "prs"
        if "regen:kept" in joined and "comments" in args[args.index("--json") + 1].split(","):
            return "gates"
        if "regen:kept" in joined:
            return "kept"
        if args[1:3] == ["issue", "list"]:
            return "issues"
        if args[1:3] == ["api", "--paginate"] and "/comments" in args[3]:
            return "comments-" + args[3].split("/issues/")[1].split("/")[0]
        return "unknown"

    def __call__(self, args: list[str], **kwargs) -> subprocess.CompletedProcess:
        assert args[0] == "gh" and kwargs == {"check": True, "capture_output": True, "text": True}
        self.calls.append(args)
        value = self.data.get(self.key(args))
        if value is None:
            raise subprocess.CalledProcessError(1, args, stderr="HTTP 502")
        if isinstance(value, BaseException):
            raise value
        return subprocess.CompletedProcess(args, 0, stdout=value, stderr="")


@pytest.fixture
def runner(monkeypatch):
    def install(data: dict[str, str | BaseException]) -> FakeRunner:
        fake = FakeRunner(data)
        monkeypatch.setattr(rp.subprocess, "run", fake)
        return fake

    return install


def pr(branch: str, state: str, number: int = 1, labels: tuple[str, ...] = (), **times: str) -> dict:
    return {"number": number, "headRefName": branch, "state": state, "labels": [{"name": n} for n in labels], **times}


class TestLoadCandidatesEdges:
    @pytest.mark.parametrize(
        "spec_yaml",
        [
            None,  # no specification.yaml at all
            "issue: [unclosed\n",  # not YAML
            "- a list\n",  # YAML, but no mapping
            "issue: '7'\n",  # not a number
        ],
    )
    def test_a_spec_without_a_readable_issue_number_is_still_a_candidate(self, tmp_path, spec_yaml):
        write_spec(tmp_path, "a", {"altair": {"updated": ts(10)}}, issue=7)
        if spec_yaml is None:
            (tmp_path / "a" / "specification.yaml").unlink()
        else:
            (tmp_path / "a" / "specification.yaml").write_text(spec_yaml, encoding="utf-8")
        cands, issues = rp.load_candidates(tmp_path, LIBS)
        assert [c.library for c in cands] == ["altair"] and issues == {}

    def test_unreadable_metadata_and_stray_entries_are_skipped(self, tmp_path):
        write_spec(tmp_path, "a", {"altair": "updated: [unclosed\n", "plotly": {"updated": ts(10)}})
        (tmp_path / ".hidden").mkdir()
        (tmp_path / ".hidden" / "specification.md").write_text("# s\n", encoding="utf-8")
        (tmp_path / "README.md").write_text("not a spec\n", encoding="utf-8")
        assert [(c.spec, c.library) for c in rp.load_candidates(tmp_path, LIBS)[0]] == [("a", "plotly")]


class TestFoldPullsEdges:
    def test_other_states_and_unnumbered_pauses(self):
        recs = records()
        rp.fold_pulls(
            [
                pr("implementation/a/altair", "DRAFT", closedAt=ts(1)),  # neither open nor done
                {"headRefName": "implementation/a/plotly", "state": "OPEN", "labels": [{"name": "ai-review-paused"}]},
                pr("implementation/b/plotly", "OPEN", 9, ("ai-repair-paused", "ai-attempt-x")),
                {"headRefName": None, "state": "MERGED"},
                pr("implementation/c/plotly", "MERGED", 3),  # no timestamp: no attempt
            ],
            recs,
        )
        assert recs.attempts == {}
        assert recs.open_pairs == {("a", "plotly"), ("b", "plotly")}
        # The unnumbered pause blocks its pair but can't be resumed; a malformed
        # attempt label falls back to attempt 1, a missing time to ANCIENT.
        assert recs.paused == [rp.Resume(9, "repair", "b", "plotly", 1, rp.ANCIENT)]

    def test_both_pause_labels_resume_the_repair(self):
        """PAUSED_LABELS lists the repair first; a resumed repair reviews again anyway."""
        recs = records()
        rp.fold_pulls([pr("implementation/a/plotly", "OPEN", 5, ("ai-review-paused", "ai-repair-paused"))], recs)
        assert [r.kind for r in recs.paused] == ["repair"]


class TestGhJson:
    def test_a_list_comes_back(self, runner):
        fake = runner({"issues": '[{"number": 1}]'})
        assert rp._gh_json(["issue", "list"], "issues") == [{"number": 1}]
        assert fake.calls == [["gh", "issue", "list"]]

    @pytest.mark.parametrize(
        "answer",
        [None, "not json", FileNotFoundError("gh"), subprocess.CalledProcessError(1, ["gh"], stderr="HTTP 502")],
    )
    def test_a_failure_warns_and_yields_none(self, runner, capsys, answer):
        runner({} if answer is None else {"issues": answer})
        assert rp._gh_json(["issue", "list"], "issues") is None
        assert capsys.readouterr().out.startswith("::warning::Could not list issues (")

    def test_a_non_list_yields_none(self, runner, capsys):
        runner({"issues": '{"message": "Not Found"}'})
        assert rp._gh_json(["issue", "list"], "issues") is None
        assert capsys.readouterr().out == ""


class TestReadRecords:
    def test_folds_every_listing(self, runner, capsys):
        fake = runner(
            {
                "prs": json.dumps(
                    [
                        pr("implementation/a/altair", "MERGED", closedAt=ts(9)),
                        pr("implementation/a/plotly", "OPEN", 7, ("ai-review-paused",), updatedAt=ts(1)),
                    ]
                ),
                "kept": json.dumps(
                    [
                        pr("implementation/b/altair", "CLOSED", 8, ("regen:kept",), closedAt=ts(200)),
                        pr("implementation/b/plotly", "CLOSED", 9, ("regen:kept",), closedAt=ts(20)),
                    ]
                ),
                "gates": json.dumps(
                    [
                        kept_pr(8, "b", "altair", gate_comment(8, "b", "altair", code="no_defect_improvement")),
                        kept_pr(9, "b", "plotly", gate_comment(9, "b", "plotly")),
                    ]
                ),
                "issues": json.dumps([{"number": 11, "updatedAt": ts(2)}]),
            }
        )
        recs = rp.read_records("o/r")
        assert set(recs.attempts) == {("a", "altair"), ("b", "altair")}
        assert recs.attempts[("b", "altair")][1] == "kept PR"
        assert recs.held == {("b", "plotly"): held((9, 20, "regression"))}
        assert recs.open_pairs == {("a", "plotly")} and [r.pr for r in recs.paused] == [7]
        assert set(recs.issue_activity) == {11}
        assert (
            "Attempt records for 2 pair(s), 1 open PR(s) (1 paused), returning keeps for 1 pair(s), "
            "activity for 1 issue(s)" in capsys.readouterr().out
        )
        prs_call, kept_call, gates_call, issues_call = fake.calls
        assert prs_call[prs_call.index("--json") + 1] == "number,headRefName,state,updatedAt,closedAt,labels"
        assert prs_call[prs_call.index("--state") + 1] == "all" and "--repo" in prs_call and "o/r" in prs_call
        assert kept_call[kept_call.index("--state") + 1] == "closed"
        assert gates_call[gates_call.index("--json") + 1] == "number,headRefName,state,comments"
        assert gates_call[gates_call.index("--state") + 1] == "closed"
        assert gates_call[gates_call.index("--label") + 1] == "regen:kept" and "o/r" in gates_call
        assert issues_call[issues_call.index("--json") + 1] == "number,updatedAt"

    @pytest.mark.parametrize("prs", [None, '{"message": "rate limited"}'])
    def test_no_implementation_prs_is_an_error(self, runner, prs):
        fake = runner({"kept": "[]", "issues": "[]"} | ({} if prs is None else {"prs": prs}))
        with pytest.raises(rp.ListingError, match="implementation PRs could not be listed"):
            rp.read_records("o/r")
        assert len(fake.calls) == 1  # nothing else is read

    def test_the_other_listings_are_best_effort(self, runner, capsys):
        runner({"prs": json.dumps([pr("implementation/a/altair", "CLOSED", closedAt=ts(5))])})
        recs = rp.read_records("o/r")
        assert recs.attempts == {("a", "altair"): (at(5), "closed PR")} and recs.issue_activity == {}
        assert recs.held == {}
        out = capsys.readouterr().out
        assert "Could not list kept regenerations (" in out and "Could not list issues" in out
        assert "Could not list kept regenerations' gate records" in out

    def test_without_gate_records_a_keep_ages_its_pair(self, runner):
        """A lost gate-record listing loses only the returns, never the kept attempt."""
        kept = json.dumps([pr("implementation/b/plotly", "CLOSED", 9, ("regen:kept",), closedAt=ts(20))])
        runner({"prs": "[]", "kept": kept, "issues": "[]"})
        recs = rp.read_records("o/r")
        assert recs.attempts == {("b", "plotly"): (at(20), "kept PR")} and recs.held == {}


class TestIssueFailures:
    def test_reads_the_spec_issue_once_per_call(self, runner):
        comments = [
            fail_comment("a", "altair", 4),
            fail_comment("a", "plotly", 2, infra=True),
            fail_comment("b", "altair", 1),
        ]
        fake = runner({"comments-11": "\n".join(json.dumps(c) for c in comments) + "\n\n"})
        failures = rp.issue_failures("o/r", {"a": 11})
        assert failures("a") == {"altair": at(4)}
        (call,) = fake.calls
        assert call[3] == "repos/o/r/issues/11/comments?per_page=100"
        assert '"<!-- impl-fail:"' in call[call.index("--jq") + 1]

    def test_a_spec_without_an_issue_has_no_failures(self, runner):
        fake = runner({})
        assert rp.issue_failures("o/r", {})("a") == {}
        assert fake.calls == []

    @pytest.mark.parametrize("answer", [None, "{not json", OSError("gh")])
    def test_an_unreadable_issue_yields_none(self, runner, capsys, answer):
        runner({} if answer is None else {"comments-11": answer})
        assert rp.issue_failures("o/r", {"a": 11})("a") is None
        assert capsys.readouterr().out.startswith("::warning::Could not read the comments of issue #11 (")


class TestSummaryTable:
    def test_resumes_then_picks(self):
        resumed = [rp.Resume(22, "repair", "b", "altair", 2, at(3))]
        picks = [rp.Pick("a", "plotly", rp.ANCIENT, "none"), rp.Pick("a", "altair", at(40), "kept PR")]
        assert rp.summary_table(resumed, picks, 9, 3).splitlines() == [
            "### Pair mode: 1 resumed, 2 new pair(s) of 3 (9 eligible)",
            "",
            "| Resume | PR | Spec | Library |",
            "|--------|----|------|---------|",
            "| repair | #22 | `b` | `altair` |",
            "",
            "| # | Spec | Library | Age from | From |",
            "|---|------|---------|----------|------|",
            "| 1 | `a` | `plotly` | never | none |",
            f"| 2 | `a` | `altair` | {ts(40)} | kept PR |",
        ]

    def test_no_resumes_no_resume_table(self):
        table = rp.summary_table([], [], 0, 5)
        assert table.startswith("### Pair mode: 0 resumed, 0 new pair(s) of 5 (0 eligible)\n")
        assert "| Resume |" not in table


class TestMainInProcess:
    ARGS = ["--count", "3", "--min-age-hours", "20", "--repo", "o/r", "--libraries", " ".join(LIBS)]

    def _plots(self, tmp_path: Path) -> Path:
        now = datetime.now(timezone.utc)
        plots = tmp_path / "plots"
        write_spec(plots, "a-spec", {"altair": {"updated": ts(190, now)}, "plotly": {"updated": ts(160, now)}}, 11)
        write_spec(plots, "b-spec", {"altair": {"updated": ts(180, now)}}, 12)
        return plots

    def _env(self, monkeypatch, tmp_path: Path, summary: bool = True) -> Path:
        out = tmp_path / "out"
        monkeypatch.setenv("GITHUB_OUTPUT", str(out))
        if summary:
            monkeypatch.setenv("GITHUB_STEP_SUMMARY", str(tmp_path / "summary"))
        else:
            monkeypatch.delenv("GITHUB_STEP_SUMMARY", raising=False)
        return out

    def _outputs(self, out: Path) -> dict[str, str]:
        return dict(line.split("=", 1) for line in out.read_text(encoding="utf-8").splitlines())

    def test_writes_resumes_pairs_and_summary(self, tmp_path, monkeypatch, runner, capsys):
        plots = self._plots(tmp_path)
        out = self._env(monkeypatch, tmp_path)
        paused = pr("implementation/a-spec/plotly", "OPEN", 21, ("ai-review-paused",), updatedAt=ts(2))
        runner({"prs": json.dumps([paused]), "kept": "[]", "issues": "[]", "comments-11": "", "comments-12": ""})
        assert rp.main([*self.ARGS, "--plots", str(plots)]) == 0
        outputs = self._outputs(out)
        assert outputs["resume_json"] == '[{"pr":21,"kind":"review","spec":"a-spec","library":"plotly","attempt":1}]'
        assert outputs["resume_count"] == "1" and outputs["count"] == "2"
        assert json.loads(outputs["pairs_json"]) == [
            {"spec": "a-spec", "library": "altair"},
            {"spec": "b-spec", "library": "altair"},
        ]
        assert outputs["specs"] == "a-spec b-spec" and json.loads(outputs["specs_json"]) == ["a-spec", "b-spec"]
        assert "Pair mode: 1 resumed, 2 new pair(s) of 3" in (tmp_path / "summary").read_text(encoding="utf-8")
        log = capsys.readouterr().out
        assert "::notice::Resumed: ['#21 review']" in log and "a-spec/altair" in log

    def test_no_summary_file_without_the_variable(self, tmp_path, monkeypatch, runner):
        plots = self._plots(tmp_path)
        out = self._env(monkeypatch, tmp_path, summary=False)
        runner({"prs": "[]", "kept": "[]", "issues": "[]", "comments-11": "", "comments-12": ""})
        assert rp.main([*self.ARGS, "--plots", str(plots)]) == 0
        assert self._outputs(out)["count"] == "3" and not (tmp_path / "summary").exists()

    def test_the_listing_error_stops_before_any_output(self, tmp_path, monkeypatch, runner, capsys):
        plots = self._plots(tmp_path)
        out = self._env(monkeypatch, tmp_path)
        runner({})
        assert rp.main([*self.ARGS, "--plots", str(plots)]) == 1
        assert "::error::Pair mode stops: the implementation PRs could not be listed" in capsys.readouterr().out
        assert not out.exists()

    @pytest.mark.parametrize(
        "args",
        [
            ["--count", "0", "--min-age-hours", "20", "--repo", "o/r", "--libraries", "altair"],
            ["--count", "1", "--min-age-hours", "20", "--repo", "o/r", "--libraries", "altair"]
            + ["--attempt-window-days", "-1"],
            ["--count", "1", "--min-age-hours", "20", "--repo", "o/r", "--libraries", "  "],
        ],
    )
    def test_bad_arguments_stop_before_any_read(self, tmp_path, monkeypatch, runner, capsys, args):
        self._env(monkeypatch, tmp_path)
        fake = runner({})
        assert rp.main([*args, "--plots", str(tmp_path)]) == 1
        assert capsys.readouterr().out.startswith("::error::--count must be at least 1")
        assert fake.calls == []

    def test_the_max_issue_reads_argument_reaches_the_pick(self, tmp_path, monkeypatch, runner, capsys):
        plots = self._plots(tmp_path)
        self._env(monkeypatch, tmp_path)
        fake = runner({"prs": "[]", "kept": "[]", "issues": "[]", "comments-11": "", "comments-12": ""})
        assert rp.main([*self.ARGS, "--plots", str(plots), "--max-issue-reads", "1"]) == 0
        assert sum(1 for c in fake.calls if c[1] == "api") == 1
        assert "::warning::Read the failed generations of 1 specs" in capsys.readouterr().out
