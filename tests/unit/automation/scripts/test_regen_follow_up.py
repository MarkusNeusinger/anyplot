"""Follow-up regenerations: repair rounds and retries (docs/workflows/overview.md).

The gate side lives in ``regen_gate.py``: the defect-line count, the trigger,
the record keys and the retry note. The dispatcher side lives in
``regen_follow_up.py``: the PR-body line, the marker comment, and the plan
that decides a dispatch from the record, the marks and the pair's recent
pull requests, and refuses whenever it cannot read one of them.
"""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import pytest

from automation.scripts import regen_follow_up as fu
from automation.scripts import regen_gate as gate
from tests.unit.automation.scripts.test_regen_gate import NEW_CHECKLIST, _checklist_json, _regen


NOW = datetime(2026, 11, 24, 12, 0, tzinfo=timezone.utc)
BOT = "github-actions[bot]"


def _ago(**delta: float) -> str:
    return (NOW - timedelta(**delta)).strftime("%Y-%m-%dT%H:%M:%SZ")


def _record(**overrides: Any) -> dict[str, Any]:
    record = {"v": 1, "pr": 14000, "spec": "bar-basic", "lib": "altair", "verdict": "merge", "code": "merge"}
    record.update({"defect_lines": 2, "follow_up_trigger": "repair"})
    record.update(overrides)
    return {k: v for k, v in record.items() if v is not None}


def _gate_comment(record: dict[str, Any], login: str = BOT, at: str | None = None) -> dict[str, Any]:
    return {
        "login": login,
        "body": f"## Gate\n\n{gate.render_record_marker(record)}",
        "created_at": at or _ago(hours=1),
    }


def _marker_comment(kind: str = "repair", pr: int = 14000, login: str = BOT) -> dict[str, Any]:
    return {"login": login, "body": fu.render_marker(kind, pr, "bar-basic", "altair"), "created_at": _ago(minutes=5)}


def _plan(kind: str = "repair", body: str = "", comments=None, history=(), window_days: int = fu.WINDOW_DAYS):
    comments = [_gate_comment(_record())] if comments is None else comments
    return fu.plan_follow_up(kind, 14000, body, comments, list(history), NOW, window_days)


# --- the gate's trigger --------------------------------------------------------


class TestTrigger:
    @pytest.mark.parametrize(
        ("verdict", "code", "defects", "of", "expected"),
        [
            ("merge", "merge", 1, None, "repair"),
            ("merge", "merge", 3, None, "repair"),
            ("merge", "merge", 0, None, "none"),  # nothing named to fix
            ("merge", "merge", None, None, "none"),  # an unreadable review triggers nothing
            ("merge", "adapt_identity", 2, None, "none"),  # an adapt-route merge keeps its identity
            ("keep", "regression", 0, None, "retry"),
            ("keep", "regression", None, None, "retry"),
            ("keep", "below_tolerance", 2, None, "none"),
            ("keep", "readiness_regression", 0, None, "none"),
            ("keep", "adapt_regression", 0, None, "none"),
            ("keep", "no_defect_improvement", 2, None, "none"),
            ("merge", "merge", 2, 13999, "none"),  # a follow-up is never followed up
            ("keep", "regression", 0, 13999, "none"),
            ("merge", "merge", True, None, "none"),  # a bool is not a count
        ],
    )
    def test_table(self, verdict, code, defects, of, expected):
        assert gate.follow_up_trigger(verdict, code, defects, of) == expected

    def test_defect_lines_count_only_defects(self):
        lines = ["VQ-02 (light): x → y. Likely cause: z.", "Suggestion: try a ramp", "an older note", 7]
        assert gate.count_defect_lines(lines) == 1
        assert gate.count_defect_lines([]) == 0
        assert gate.count_defect_lines({"a": 1}) is None

    def test_a_missing_or_broken_weaknesses_file_counts_nothing(self, tmp_path):
        assert gate.load_defect_lines(tmp_path / "review_weaknesses.json") is None
        broken = tmp_path / "broken.json"
        broken.write_text("{", encoding="utf-8")
        assert gate.load_defect_lines(broken) is None


class TestRecordKeys:
    def test_the_keys_validate(self):
        assert gate.validate_record(_record()) == []
        assert gate.validate_record(_record(follow_up_of=13999, follow_up_kind="retry", follow_up_trigger="none")) == []

    @pytest.mark.parametrize(
        ("overrides", "error"),
        [
            ({"defect_lines": -1}, "record.defect_lines must be a count"),
            ({"defect_lines": "2"}, "record.defect_lines must be a count"),
            ({"follow_up_trigger": "again"}, "record.follow_up_trigger is not one of FOLLOW_UP_TRIGGERS"),
            ({"follow_up_of": 13999}, "record.follow_up_of and record.follow_up_kind come together"),
            ({"follow_up_kind": "retry"}, "record.follow_up_of and record.follow_up_kind come together"),
            ({"follow_up_of": 0, "follow_up_kind": "retry"}, "record.follow_up_of must be a PR number"),
            ({"follow_up_of": 1, "follow_up_kind": "redo"}, "record.follow_up_kind is not one of FOLLOW_UP_KINDS"),
        ],
    )
    def test_malformed_keys_fail(self, overrides, error):
        assert error in gate.validate_record(_record(**overrides))

    def test_a_record_without_the_keys_still_validates_and_triggers_nothing(self):
        old = _record(defect_lines=None, follow_up_trigger=None)
        assert gate.validate_record(old) == []
        assert fu.plan_follow_up("repair", 14000, "", [_gate_comment(old)], [], NOW).reason == "not_eligible"

    def test_build_record_adds_the_keys_only_when_given(self):
        result = gate.decide(gate.GateInput(spec_id="bar-basic", score=None, regen=None))
        plain = gate.build_record(result, spec_id="bar-basic", library="altair", score=None, prev_stored=None)
        assert not {"defect_lines", "follow_up_trigger", "follow_up_of", "follow_up_kind"} & set(plain)
        full = gate.build_record(
            result,
            spec_id="bar-basic",
            library="altair",
            score=None,
            prev_stored=None,
            defect_lines=0,
            follow_up_trigger="none",
            follow_up_of=13999,
            follow_up_kind="repair",
        )
        assert {k: full[k] for k in ("defect_lines", "follow_up_trigger", "follow_up_of", "follow_up_kind")} == {
            "defect_lines": 0,
            "follow_up_trigger": "none",
            "follow_up_of": 13999,
            "follow_up_kind": "repair",
        }
        assert gate.validate_record(full) == []


class TestDecideCli:
    def _args(self, tmp_path: Path, weaknesses: list[str] | None, *extra: str) -> list[str]:
        regen = tmp_path / "review_regen.json"
        regen.write_text(json.dumps(_regen(prev_rescored=80)), encoding="utf-8")
        (tmp_path / "review_checklist.json").write_text(json.dumps(_checklist_json(NEW_CHECKLIST)), encoding="utf-8")
        if weaknesses is not None:
            (tmp_path / "review_weaknesses.json").write_text(json.dumps(weaknesses), encoding="utf-8")
        prev = tmp_path / "prev-weaknesses.json"
        prev.write_text(json.dumps([{"id": "W2", "text": "VQ-03 (both): hollow circles", "class": "defect"}]))
        return [
            "decide",
            "--spec-id",
            "bubble-basic",
            "--library",
            "altair",
            "--score",
            "81",
            "--regen-json",
            str(regen),
            "--weaknesses-json",
            str(prev),
            "--prev-renders",
            "available",
            "--record-out",
            str(tmp_path / "record.json"),
            *extra,
        ]

    def _run(self, tmp_path, monkeypatch, weaknesses, *extra) -> tuple[dict[str, Any], str]:
        out = tmp_path / "gh_output"
        monkeypatch.setenv("GITHUB_OUTPUT", str(out))
        assert gate.main(self._args(tmp_path, weaknesses, *extra)) == 0
        return json.loads((tmp_path / "record.json").read_text()), out.read_text()

    def test_a_merge_with_a_defect_line_triggers_a_repair(self, tmp_path, monkeypatch):
        record, outputs = self._run(tmp_path, monkeypatch, ["VQ-01 (dark): ticks 7 pt", "Suggestion: x"])
        assert (record["verdict"], record["defect_lines"], record["follow_up_trigger"]) == ("merge", 1, "repair")
        assert "follow_up_of" not in record
        assert "follow_up_trigger=repair" in outputs.splitlines()
        assert "defect_lines=1" in outputs.splitlines()
        assert gate.validate_record(record) == []

    def test_only_suggestions_trigger_nothing(self, tmp_path, monkeypatch):
        record, outputs = self._run(tmp_path, monkeypatch, ["Suggestion: x"])
        assert (record["defect_lines"], record["follow_up_trigger"]) == (0, "none")

    def test_no_weaknesses_file_triggers_nothing(self, tmp_path, monkeypatch):
        record, outputs = self._run(tmp_path, monkeypatch, None)
        assert "defect_lines" not in record
        assert record["follow_up_trigger"] == "none"
        assert "defect_lines=n/a" in outputs.splitlines()

    def test_a_follow_up_names_its_predecessor_and_triggers_nothing(self, tmp_path, monkeypatch):
        record, _ = self._run(
            tmp_path, monkeypatch, ["VQ-01 (dark): x"], "--follow-up-of", "13999", "--follow-up-kind", "repair"
        )
        assert (record["follow_up_of"], record["follow_up_kind"], record["follow_up_trigger"]) == (
            13999,
            "repair",
            "none",
        )

    @pytest.mark.parametrize("extra", [("--follow-up-of", "13999"), ("--follow-up-kind", "retry")])
    def test_half_a_follow_up_is_none(self, tmp_path, monkeypatch, extra):
        record, _ = self._run(tmp_path, monkeypatch, ["VQ-01 (dark): x"], *extra)
        assert "follow_up_of" not in record
        assert record["follow_up_trigger"] == "repair"


# --- the retry note ------------------------------------------------------------


class TestRetryNote:
    def test_names_each_regression_on_one_line(self):
        note = gate.retry_note([{"what": "lost the viridis ramp", "where_visible": "heatmap cells"}], 14231)
        assert note == (
            "#14231 was kept because the review found it worse than the live version here: "
            "lost the viridis ramp (heatmap cells). Keep these as the live version has them."
        )

    def test_plain_text_only(self):
        note = gate.retry_note([{"what": "legend `loc`\nmoved <!-- x --> -->", "where_visible": ""}], 1)
        assert "\n" not in note and "`" not in note and "<!--" not in note and "-->" not in note
        assert "legend loc moved x" in note

    def test_caps_items_and_length(self):
        items = [{"what": f"item {i} " + "x" * 400, "where_visible": "w"} for i in range(5)]
        note = gate.retry_note(items, 7)
        assert note.count("item ") == gate.NOTE_ITEMS
        assert "; and 2 more." in note
        assert len(note) < gate.NOTE_ITEMS * gate.NOTE_ITEM_LIMIT + 200

    def test_nothing_to_name_is_empty(self):
        assert gate.retry_note([], 7) == ""
        assert gate.retry_note([{"what": "   ", "where_visible": "x"}], 7) == ""

    def test_cli_uses_the_gates_own_regressions(self, tmp_path, capsys):
        regen = tmp_path / "review_regen.json"
        regen.write_text(json.dumps(_regen(scenario_changed=True)), encoding="utf-8")
        args = ["retry-note", "--regen-json", str(regen), "--spec-id", "bar-basic", "--pr", "9"]
        assert gate.main(args) == 0
        assert "data scenario replaced on a -basic spec" in capsys.readouterr().out
        # A change request the review says it applied may swap the scenario: no regression, no note.
        regen.write_text(json.dumps(_regen(scenario_changed=True, change_request_applied=True)), encoding="utf-8")
        assert gate.main([*args, "--change-request-present"]) == 1

    def test_cli_without_a_regression_exits_1(self, tmp_path):
        regen = tmp_path / "review_regen.json"
        regen.write_text(json.dumps(_regen()), encoding="utf-8")
        assert gate.main(["retry-note", "--regen-json", str(regen), "--spec-id", "bar-basic"]) == 1
        assert gate.main(["retry-note", "--regen-json", str(tmp_path / "missing.json"), "--spec-id", "x"]) == 1


# --- the marks -----------------------------------------------------------------


class TestMarks:
    @pytest.mark.parametrize(
        ("body", "expected"),
        [
            ("**Model:** sonnet\n\n**Follow-up of:** #14231 (retry)\n", (14231, "retry")),
            ("**Follow-up of:** #7 (repair)\r\n**Model:** x", (7, "repair")),
            ("**Follow-up of:** #7 (redo)", None),
            ("**Follow-up of:** #0 (repair)", None),
            ("text **Follow-up of:** #7 (repair)", None),  # only a line of its own counts
            ("", None),
            (None, None),
        ],
    )
    def test_body_line(self, body, expected):
        assert fu.body_follow_up(body) == expected

    def test_the_marker_is_found_only_from_the_workflow(self):
        assert fu.has_marker([_marker_comment()])
        assert not fu.has_marker([_marker_comment(login="someone")])
        assert not fu.has_marker([{"login": BOT, "body": "no marker"}])

    def test_the_marker_holds_tokens_only(self):
        text = fu.render_marker("retry", 14231, "bar-basic", "altair")
        assert text.startswith("**Follow-up regeneration (retry).**")
        payload = json.loads(fu.MARKER_RE.search(text).group(1))
        assert payload == {"kind": "retry", "pr": 14231, "spec": "bar-basic", "lib": "altair"}
        for bad in (("redo", 1, "a", "b"), ("retry", 0, "a", "b"), ("retry", 1, "A B", "b"), ("retry", 1, "a", "-->")):
            with pytest.raises(ValueError):
                fu.render_marker(*bad)


# --- the plan ------------------------------------------------------------------


class TestPlan:
    def test_an_eligible_merge_dispatches(self):
        assert _plan() == fu.Plan(True, "dispatch")

    def test_an_eligible_keep_dispatches_a_retry(self):
        keep = _record(verdict="keep", code="regression", defect_lines=0, follow_up_trigger="retry")
        assert _plan("retry", comments=[_gate_comment(keep)]).dispatch

    def test_the_kind_must_match_the_decision(self):
        assert _plan("retry").reason == "not_eligible"
        keep = _record(verdict="keep", code="regression", follow_up_trigger="retry")
        assert _plan("repair", comments=[_gate_comment(keep)]).reason == "not_eligible"

    def test_eligibility_is_recomputed_not_read(self):
        """A record whose stored trigger disagrees with its decision triggers by the decision."""
        lying = _record(code="adapt_identity", follow_up_trigger="repair")
        assert _plan(comments=[_gate_comment(lying)]).reason == "not_eligible"

    @pytest.mark.parametrize("defects", [0, None])
    def test_no_defect_line_no_repair(self, defects):
        assert _plan(comments=[_gate_comment(_record(defect_lines=defects))]).reason == "not_eligible"

    def test_a_follow_up_is_never_followed_up(self):
        assert _plan(body="**Follow-up of:** #13999 (retry)").reason == "is_follow_up"
        record = _record(follow_up_of=13999, follow_up_kind="repair", follow_up_trigger="none")
        assert _plan(comments=[_gate_comment(record)]).reason == "is_follow_up"

    def test_only_the_workflows_record_counts(self):
        assert _plan(comments=[]).reason == "no_record"
        assert _plan(comments=[_gate_comment(_record(), login="someone")]).reason == "no_record"

    def test_the_first_record_by_the_workflow_wins(self):
        first = _gate_comment(_record(verdict="keep", code="regression"), at=_ago(hours=3))
        later = _gate_comment(_record(), at=_ago(hours=1))
        assert _plan(comments=[later, first]).reason == "not_eligible"

    def test_a_marked_pr_gets_no_second_follow_up(self):
        assert _plan(comments=[_gate_comment(_record()), _marker_comment()]).reason == "already"
        # A pasted marker is not the workflow's.
        assert _plan(comments=[_gate_comment(_record()), _marker_comment(login="someone")]).dispatch

    def test_a_recent_follow_up_of_the_pair_refuses(self):
        marked = {"number": 13990, "created_at": _ago(days=2), "body": "", "comments": [_marker_comment(pr=13990)]}
        assert _plan(history=[marked]).reason == "recent_follow_up"
        # A follow-up whose body line survived counts the same, even when its predecessor's marker did not.
        follow_up = {"number": 13995, "created_at": _ago(days=1), "body": "**Follow-up of:** #13990 (repair)"}
        assert _plan(history=[follow_up]).reason == "recent_follow_up"

    def test_the_window_ends(self):
        old = {"number": 13000, "created_at": _ago(days=8), "body": "", "comments": [_marker_comment(pr=13000)]}
        assert _plan(history=[old]).dispatch
        assert _plan(history=[old], window_days=9).reason == "recent_follow_up"

    def test_an_unreadable_creation_time_counts_as_recent(self):
        odd = {"number": 13000, "created_at": "yesterday", "body": "", "comments": [_marker_comment(pr=13000)]}
        assert _plan(history=[odd]).reason == "recent_follow_up"

    def test_the_pr_itself_in_the_history_is_not_a_recent_follow_up(self):
        itself = {"number": 14000, "created_at": _ago(hours=2), "body": "**Follow-up of:** #1 (repair)"}
        assert _plan(history=[itself]).dispatch

    def test_an_unknown_kind_is_a_bug(self):
        with pytest.raises(ValueError):
            _plan("redo")


# --- the reads -----------------------------------------------------------------


class FakeGh:
    """Answers the three reads ``read_inputs`` makes; ``fail`` names one to fail."""

    def __init__(self, *, pulls, view, comments, fail: str = ""):
        self.pulls, self.view, self.comments, self.fail = pulls, view, comments, fail
        self.calls: list[list[str]] = []

    def __call__(self, args: list[str]) -> str:
        self.calls.append(args)
        what = "list" if args[:2] == ["pr", "list"] else "view" if args[:2] == ["pr", "view"] else "comments"
        if what == self.fail:
            raise fu.ReadError(f"gh {what} failed")
        if what == "list":
            return json.dumps(self.pulls)
        if what == "view":
            return json.dumps(self.view)
        number = int(args[2].split("/")[-2])
        return "".join(json.dumps(c) + "\n" for c in self.comments.get(number, []))


def _fake(**overrides: Any) -> FakeGh:
    fields: dict[str, Any] = {
        "pulls": [
            {"number": 14000, "createdAt": _ago(hours=3), "body": ""},
            {"number": 13990, "createdAt": _ago(days=2), "body": ""},
            {"number": 12000, "createdAt": _ago(days=40), "body": ""},
        ],
        "view": {"number": 14000, "body": "**Model:** sonnet", "headRefName": "implementation/bar-basic/altair"},
        "comments": {14000: [_gate_comment(_record())], 13990: []},
    }
    fields.update(overrides)
    return FakeGh(**fields)


def _plan_cli(monkeypatch, tmp_path, fake: FakeGh, kind: str = "repair") -> dict[str, str]:
    monkeypatch.setattr(fu, "_gh", fake)
    out = tmp_path / "gh_output"
    monkeypatch.setenv("GITHUB_OUTPUT", str(out))
    args = ["plan", "--kind", kind, "--pr", "14000", "--spec-id", "bar-basic", "--library", "altair"]
    assert fu.main([*args, "--repo", "owner/repo"]) == 0
    return dict(line.split("=", 1) for line in out.read_text().splitlines())


class TestPlanCli:
    def test_dispatch_reads_only_the_window(self, monkeypatch, tmp_path):
        fake = _fake()
        assert _plan_cli(monkeypatch, tmp_path, fake) == {"dispatch": "true", "reason": "dispatch"}
        read = [c[2] for c in fake.calls if c[0] == "api"]
        assert read == [
            "repos/owner/repo/issues/13990/comments?per_page=100",
            "repos/owner/repo/issues/14000/comments?per_page=100",
        ]
        listing = next(c for c in fake.calls if c[:2] == ["pr", "list"])
        assert listing[listing.index("--head") + 1] == "implementation/bar-basic/altair"
        assert listing[listing.index("--state") + 1] == "all"

    @pytest.mark.parametrize("fail", ["list", "view", "comments"])
    def test_any_failed_read_refuses(self, monkeypatch, tmp_path, fail):
        assert _plan_cli(monkeypatch, tmp_path, _fake(fail=fail)) == {"dispatch": "false", "reason": "unreadable"}

    def test_another_pairs_pr_refuses(self, monkeypatch, tmp_path):
        view = {"number": 14000, "body": "", "headRefName": "implementation/bar-basic/plotly"}
        assert _plan_cli(monkeypatch, tmp_path, _fake(view=view))["reason"] == "unreadable"

    def test_a_marker_on_a_recent_pr_refuses(self, monkeypatch, tmp_path):
        comments = {14000: [_gate_comment(_record())], 13990: [_marker_comment(pr=13990)]}
        assert _plan_cli(monkeypatch, tmp_path, _fake(comments=comments))["reason"] == "recent_follow_up"

    def test_bad_input_is_a_usage_error(self, monkeypatch):
        monkeypatch.setattr(fu, "_gh", _fake())
        args = ["plan", "--kind", "repair", "--pr", "14000", "--library", "altair", "--repo", "owner/repo"]
        assert fu.main([*args, "--spec-id", "Bad Spec"]) == 2
        with pytest.raises(SystemExit):
            fu.main(["plan", "--kind", "repair", "--pr", "0", "--spec-id", "a", "--library", "b"])

    def test_gh_is_retried_then_raises(self, monkeypatch):
        calls = []

        def run(cmd, **_kwargs):
            calls.append(cmd)
            return type("P", (), {"returncode": 1, "stdout": "", "stderr": "HTTP 502\nmore"})()

        monkeypatch.setattr(fu.subprocess, "run", run)
        monkeypatch.setattr(fu.time, "sleep", lambda _s: None)
        with pytest.raises(fu.ReadError, match="HTTP 502 more"):
            fu._gh(["pr", "list"])
        assert len(calls) == 3


class TestOtherClis:
    def test_parse_body(self, monkeypatch, tmp_path, capsys):
        import io

        out = tmp_path / "gh_output"
        monkeypatch.setenv("GITHUB_OUTPUT", str(out))
        monkeypatch.setattr("sys.stdin", io.StringIO("**Follow-up of:** #14231 (retry)\n"))
        assert fu.main(["parse-body"]) == 0
        assert out.read_text().splitlines() == ["follow_up_of=14231", "follow_up_kind=retry"]
        monkeypatch.setattr("sys.stdin", io.StringIO("**Model:** sonnet\n"))
        assert fu.main(["parse-body"]) == 0
        assert out.read_text().splitlines()[-2:] == ["follow_up_of=", "follow_up_kind="]

    def test_marker(self, capsys):
        assert (
            fu.main(["marker", "--kind", "repair", "--pr", "14000", "--spec-id", "bar-basic", "--library", "altair"])
            == 0
        )
        assert fu.has_marker([{"login": BOT, "body": capsys.readouterr().out}])
        assert fu.main(["marker", "--kind", "repair", "--pr", "14000", "--spec-id", "Bar", "--library", "altair"]) == 2
