"""Tests for automation.scripts.regen_pick_pairs — daily-regen's pair mode.

The picker ages each (spec, library) pair by its newest touch, the metadata
``updated`` or the last real attempt (a merged or closed implementation PR, a
failed generation), keeps every pair touched within the attempt window out
of the queue, and postpones a spec whose issue just saw activity. The
no-loop rule is pinned here: a pair the gate kept, or whose generation
failed, does not come back the next night, and an infrastructure failure or
a stop at a spend or usage limit is no attempt. ``main`` runs once against a fake
``gh`` the way the workflow calls it.
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
        attempts=kw.get("attempts", {}), open_pairs=kw.get("open_pairs", set()), issue_activity=kw.get("issues", {})
    )


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
            {"created_at": ts(1), "body": "<!-- impl-paused-claude-limit:a:plotly -->"},  # a spend or usage limit
        ]
        assert rp.failed_generations(comments, "a") == {"altair": at(5)}

    def test_the_read_cap_stops_reading(self, capsys):
        cands = [rp.Candidate(spec, "altair", at(100 + i)) for i, spec in enumerate("abc")]
        asked: list[str] = []
        picks, _ = run_pick(cands, count=3, failures=lambda spec: asked.append(spec) or {}, max_reads=1)
        assert len(picks) == 3 and asked == ["c"]
        assert "::warning::Read the failed generations of 1 specs" in capsys.readouterr().out


class TestFoldPulls:
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

    def test_the_window_comes_from_the_argument(self, tmp_path):
        self._plots(tmp_path)
        kept = [{"headRefName": "implementation/a-spec/altair", "state": "CLOSED", "closedAt": ts(40, self.now)}]
        data = {"prs.json": "[]", "kept.json": json.dumps(kept), "issues.json": "[]"}
        data |= {"comments-11.jsonl": "", "comments-12.jsonl": ""}
        _, outputs, _ = run_main(tmp_path, data, 5, "--attempt-window-days", "60")
        # Kept 40 days ago is inside a 60-day window.
        pairs = {(p["spec"], p["library"]) for p in json.loads(outputs["pairs_json"])}
        assert pairs == {("a-spec", "plotly"), ("b-spec", "altair"), ("b-spec", "matplotlib")}

    def test_a_failed_listing_degrades_with_a_warning(self, tmp_path):
        self._plots(tmp_path)
        result, outputs, _ = run_main(tmp_path, {"issues.json": "[]"}, 1)
        assert result.returncode == 0, result.stdout + result.stderr
        assert result.stdout.count("::warning::Could not list") == 2
        assert "::warning::Could not read the comments of issue #11" in result.stdout
        assert json.loads(outputs["pairs_json"]) == [{"spec": "a-spec", "library": "altair"}]

    def test_nothing_eligible_writes_an_empty_pick(self, tmp_path):
        (tmp_path / "plots").mkdir()
        result, outputs, _ = run_main(tmp_path, {"prs.json": "[]", "kept.json": "[]", "issues.json": "[]"})
        assert result.returncode == 0, result.stdout + result.stderr
        assert outputs == {"pairs_json": "[]", "specs": "", "specs_json": "[]", "count": "0"}

    @pytest.mark.parametrize(("count", "window"), [(0, "30"), (-1, "30"), (1, "-1")])
    def test_refuses_bad_numbers(self, tmp_path, count, window):
        (tmp_path / "plots").mkdir()
        result, _, _ = run_main(tmp_path, {}, count, "--attempt-window-days", window)
        assert result.returncode == 1 and "::error::" in result.stdout
