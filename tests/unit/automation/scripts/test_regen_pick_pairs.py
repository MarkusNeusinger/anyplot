"""Tests for automation.scripts.regen_pick_pairs — daily-regen's pair mode.

The picker mirrors the spec mode's age rule per (spec, library) pair: the
newer of the metadata ``updated`` and the pair's last attempt, a minimum age,
the spec issue's activity as a postponement. Every exclusion is pinned here,
and ``main`` runs once against a fake ``gh`` the way the workflow calls it.
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
LIBS = ["altair", "matplotlib", "plotly"]
SCRIPT = Path(rp.__file__)


def ts(days: float) -> str:
    return (NOW - timedelta(days=days)).strftime("%Y-%m-%dT%H:%M:%SZ")


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


def picked(picks: list[rp.Pick]) -> list[str]:
    return [f"{p.spec}/{p.library}" for p in picks]


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
            rp.Candidate("a", "altair", at(5)),
            rp.Candidate("b", "plotly", at(50)),
            rp.Candidate("a", "plotly", at(20)),
        ]
        picks, eligible = rp.pick(cands, records(), {}, NOW, MIN_AGE, 2)
        assert picked(picks) == ["b/plotly", "a/plotly"]
        assert eligible == 3

    def test_a_kept_regeneration_ages_from_its_attempt(self):
        # The gate kept a/altair two days ago: `updated` is still 90 days old,
        # but the pair is now younger than b/plotly.
        cands = [rp.Candidate("a", "altair", at(90)), rp.Candidate("b", "plotly", at(30))]
        recs = records(attempts={("a", "altair"): (at(2), "kept PR")})
        picks, _ = rp.pick(cands, recs, {}, NOW, MIN_AGE, 2)
        assert picked(picks) == ["b/plotly", "a/altair"]
        assert picks[1].basis == "kept PR" and picks[1].touched == at(2)

    def test_an_attempt_older_than_the_metadata_changes_nothing(self):
        cands = [rp.Candidate("a", "altair", at(5))]
        picks, _ = rp.pick(cands, records(attempts={("a", "altair"): (at(9), "run")}), {}, NOW, MIN_AGE, 1)
        assert picks[0].basis == "metadata" and picks[0].touched == at(5)

    def test_too_fresh_pairs_are_skipped(self):
        cands = [rp.Candidate("a", "altair", at(0.5)), rp.Candidate("a", "plotly", at(30))]
        recs = records(attempts={("a", "plotly"): (at(0.2), "run")})  # a generation started 5 h ago
        assert rp.pick(cands, recs, {}, NOW, MIN_AGE, 5) == ([], 0)

    def test_open_pr_skips_only_its_pair(self):
        cands = [rp.Candidate("a", "altair", at(30)), rp.Candidate("a", "plotly", at(40))]
        picks, _ = rp.pick(cands, records(open_pairs={("a", "plotly")}), {}, NOW, MIN_AGE, 5)
        assert picked(picks) == ["a/altair"]

    def test_recent_issue_activity_postpones_every_pair_of_the_spec(self):
        cands = [rp.Candidate("a", "altair", at(30)), rp.Candidate("b", "altair", at(10))]
        recs = records(issues={1: at(0.3), 2: at(3)})
        picks, _ = rp.pick(cands, recs, {"a": 1, "b": 2}, NOW, MIN_AGE, 5)
        assert picked(picks) == ["b/altair"]  # b's issue is three days old: no postponement

    def test_issue_activity_is_a_gate_not_an_age(self):
        # Old activity on a's issue does not re-date a's pairs.
        cands = [rp.Candidate("a", "altair", at(30)), rp.Candidate("b", "altair", at(20))]
        picks, _ = rp.pick(cands, records(issues={1: at(2)}), {"a": 1}, NOW, MIN_AGE, 1)
        assert picked(picks) == ["a/altair"] and picks[0].touched == at(30)

    def test_no_timestamp_at_all_is_ancient(self):
        cands = [rp.Candidate("a", "altair", at(300)), rp.Candidate("b", "altair", None)]
        picks, _ = rp.pick(cands, records(), {}, NOW, MIN_AGE, 2)
        assert picked(picks) == ["b/altair", "a/altair"]
        assert picks[0].touched == rp.ANCIENT and picks[0].basis == "none"

    def test_no_metadata_timestamp_ages_from_the_attempt(self):
        cands = [rp.Candidate("b", "altair", None)]
        assert rp.pick(cands, records(attempts={("b", "altair"): (at(0.1), "run")}), {}, NOW, MIN_AGE, 1)[0] == []

    def test_ties_break_by_spec_then_library(self):
        cands = [
            rp.Candidate("b", "altair", at(9)),
            rp.Candidate("a", "plotly", at(9)),
            rp.Candidate("a", "altair", at(9)),
        ]
        assert picked(rp.pick(cands, records(), {}, NOW, MIN_AGE, 3)[0]) == ["a/altair", "a/plotly", "b/altair"]


class TestFold:
    def test_pulls_keep_the_newest_attempt_and_mark_open_ones(self):
        recs = records()
        rp.fold_pulls(
            [
                {"headRefName": "implementation/a/altair", "state": "MERGED", "updatedAt": ts(9)},
                {"headRefName": "implementation/a/altair", "state": "CLOSED", "updatedAt": ts(3)},
                {"headRefName": "implementation/b/plotly", "state": "OPEN", "updatedAt": ts(1)},
                {"headRefName": "review-writeback/a/altair/12", "state": "MERGED", "updatedAt": ts(0)},
                {"headRefName": "implementation/a/altair/extra", "state": "OPEN", "updatedAt": ts(0)},
            ],
            "implementation PR",
            recs,
        )
        assert recs.attempts == {
            ("a", "altair"): (at(3), "implementation PR"),
            ("b", "plotly"): (at(1), "implementation PR"),
        }
        assert recs.open_pairs == {("b", "plotly")}

    def test_runs_parse_the_impl_generate_run_name(self):
        recs = records()
        rp.fold_runs(
            [
                {"displayTitle": "Generate: plotly for line-basic", "createdAt": ts(4)},
                {"displayTitle": "Generate: generate:plotly for issue", "createdAt": ts(1)},
                {"displayTitle": "Review: PR #12", "createdAt": ts(1)},
            ],
            recs,
        )
        assert recs.attempts == {("line-basic", "plotly"): (at(4), "run")}

    def test_issues(self):
        recs = records()
        rp.fold_issues([{"number": 3, "updatedAt": ts(2)}, {"number": "x", "updatedAt": ts(1)}], recs)
        assert recs.issue_activity == {3: at(2)}


# Answers each listing the picker makes from a JSON file named after it; a
# listing whose file is missing fails like an API error. Logs every call.
FAKE_GH = """#!/bin/sh
echo "$*" >> "$GH_LOG"
case "$*" in
  *"head:implementation/"*) f=prs ;;
  *"regen:kept"*) f=kept ;;
  "run list"*) f=runs ;;
  "issue list"*) f=issues ;;
  *) exit 1 ;;
esac
[ -f "$GH_DATA/$f.json" ] || { echo "HTTP 502" >&2; exit 1; }
cat "$GH_DATA/$f.json"
"""


def run_main(tmp_path: Path, data: dict[str, list], count: int = 3) -> tuple[subprocess.CompletedProcess, dict, str]:
    bin_dir, data_dir = tmp_path / "bin", tmp_path / "data"
    bin_dir.mkdir()
    data_dir.mkdir()
    (bin_dir / "gh").write_text(FAKE_GH, encoding="utf-8")
    (bin_dir / "gh").chmod(0o755)
    for name, rows in data.items():
        (data_dir / f"{name}.json").write_text(json.dumps(rows), encoding="utf-8")
    out, summary = tmp_path / "out", tmp_path / "summary"
    env = {
        **os.environ,
        "PATH": f"{bin_dir}{os.pathsep}{os.environ['PATH']}",
        "GH_LOG": str(tmp_path / "gh.log"),
        "GH_DATA": str(data_dir),
        "GITHUB_OUTPUT": str(out),
        "GITHUB_STEP_SUMMARY": str(summary),
    }
    args = ["--count", str(count), "--min-age-hours", "20", "--repo", "o/r", "--libraries", " ".join(LIBS)]
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
        plots = tmp_path / "plots"
        now = datetime.now(timezone.utc)

        def old(days: float) -> str:
            return (now - timedelta(days=days)).strftime("%Y-%m-%dT%H:%M:%SZ")

        write_spec(plots, "a-spec", {"altair": {"updated": old(90)}, "plotly": {"updated": old(60)}}, issue=11)
        write_spec(plots, "b-spec", {"altair": {"updated": old(80)}, "matplotlib": {"updated": old(70)}}, issue=12)
        self.recent = old(0.1)
        self.week = old(7)

    def test_writes_pairs_specs_and_summary(self, tmp_path):
        self._plots(tmp_path)
        result, outputs, summary = run_main(
            tmp_path,
            {
                "prs": [{"headRefName": "implementation/b-spec/matplotlib", "state": "OPEN", "updatedAt": self.recent}],
                "kept": [{"headRefName": "implementation/a-spec/altair", "state": "CLOSED", "updatedAt": self.week}],
                "runs": [],
                "issues": [{"number": 11, "updatedAt": self.week}],
            },
        )
        assert result.returncode == 0, result.stdout + result.stderr
        # a-spec/altair is aged by its keep (7 d), b-spec/matplotlib has an open PR.
        assert json.loads(outputs["pairs_json"]) == [
            {"spec": "b-spec", "library": "altair"},
            {"spec": "a-spec", "library": "plotly"},
            {"spec": "a-spec", "library": "altair"},
        ]
        assert json.loads(outputs["specs_json"]) == ["b-spec", "a-spec"]
        assert outputs["specs"] == "b-spec a-spec" and outputs["count"] == "3"
        assert "| 3 | `a-spec` | `altair` |" in summary and "kept PR" in summary

    def test_a_failed_listing_degrades_with_a_warning(self, tmp_path):
        self._plots(tmp_path)
        result, outputs, _ = run_main(tmp_path, {"issues": []}, count=1)
        assert result.returncode == 0, result.stdout + result.stderr
        assert result.stdout.count("::warning::Could not list") == 3
        assert json.loads(outputs["pairs_json"]) == [{"spec": "a-spec", "library": "altair"}]

    def test_nothing_eligible_writes_an_empty_pick(self, tmp_path):
        (tmp_path / "plots").mkdir()
        result, outputs, _ = run_main(tmp_path, {"prs": [], "kept": [], "runs": [], "issues": []})
        assert result.returncode == 0, result.stdout + result.stderr
        assert outputs == {"pairs_json": "[]", "specs": "", "specs_json": "[]", "count": "0"}

    @pytest.mark.parametrize("count", [0, -1])
    def test_refuses_a_count_below_one(self, tmp_path, count):
        (tmp_path / "plots").mkdir()
        result, _, _ = run_main(tmp_path, {}, count=count)
        assert result.returncode == 1 and "::error::" in result.stdout
