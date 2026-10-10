"""Pricing, the report summary, the baseline diff, the Markdown and the review galleries, on synthetic runs."""

import json
import re
from pathlib import Path
from typing import Any

import pytest

from agents.anyplot.render.backends.fake import fixture_png
from agents.evals import pricing
from agents.evals.report import (
    Flip,
    blind_gallery,
    compare,
    diff_markdown,
    gallery_all_html,
    gallery_html,
    main,
    passed_runs,
    percentile,
    sample_runs,
    score,
    summarize,
    summary_markdown,
)

from .conftest import check_html


def run(case_id: str, **fields: Any) -> dict[str, Any]:
    record: dict[str, Any] = {
        "case_id": case_id,
        "repeat": 1,
        "spec_id": case_id.rsplit("-", 2)[0],
        "library": "matplotlib",
        "perturbation": "renamed",
        "expected": "accepted",
        "origin": "fixtures",
        "status": "ok",
        "reason": None,
        "attempts": 1,
        "passed": True,
        "accept_match": True,
        "cost_usd": 0.001,
        "e2e_s": 20.0,
        "ttfe_s": 1.0,
        "render_s": [3.0],
        "llm_calls": 4,
        "tokens": {"prompt": 1000, "candidates": 100},
        "gate_failures": {},
        "validator_rejections": {},
        "adapter_outcomes": {"plan": 1},
        "edit_apply_failures": 0,
        "reviewer": {"verdict": "ok", "defects": []},
        "residual_defects": [],
        "png": None,
    }
    record.update(fields)
    return record


def report_of(runs: list[dict[str, Any]], **stamp: Any) -> dict[str, Any]:
    return {
        "schema": 1,
        "stamp": {"model": "claude-haiku-5-5", "date": "2026-10-10", "run_id": "abc123def456", **stamp},
        "summary": summarize(runs),
        "runs": runs,
        "stopped": None,
    }


# --- Pricing -------------------------------------------------------------------------------


def test_claude_call_at_list_price_on_eu() -> None:
    cost = pricing.call_cost("claude-haiku-5-5", "eu", {"prompt": 10_000, "candidates": 2_000})

    assert cost == pytest.approx((10_000 * 0.10 + 2_000 * 0.50) / 1e6 * 1.10)


def test_cached_and_cache_write_tokens_have_their_own_rate() -> None:
    tokens = {"prompt": 10_000, "cached": 8_000, "cache_write": 1_000, "candidates": 500, "thoughts": 500}

    cost = pricing.call_cost("gemini-3.8-flash", "global", tokens)

    expected_input = 1_000 * 1.50 + 8_000 * 1.50 * 0.10 + 1_000 * 1.50 * 1.25
    assert cost == pytest.approx((expected_input + 1_000 * 7.50) / 1e6)


def test_the_eu_prices_of_the_design() -> None:
    assert pricing.call_cost("gemini-3.8-flash", "eu", {"prompt": 1_000_000}) == pytest.approx(1.65)
    assert pricing.call_cost("gemini-3.8-flash", "eu", {"candidates": 1_000_000}) == pytest.approx(8.25)
    assert pricing.judge_cost("gemini-3.5-flash-lite", "eu", 1_000_000, 1_000_000) == pytest.approx(0.33 + 2.75)


def test_an_unpriced_model_is_an_error() -> None:
    with pytest.raises(pricing.UnknownPrice, match="add it to agents/evals/pricing.py"):
        pricing.call_cost("gemini-9-flash", "eu", {"prompt": 1})


# --- Summary and diff ----------------------------------------------------------------------


def test_percentile_interpolates() -> None:
    assert percentile([], 0.5) is None
    assert percentile([4.0, 1.0, 3.0, 2.0], 0.5) == 2.5
    assert percentile(list(range(1, 101)), 0.95) == pytest.approx(95.05)


def test_summary_counts_rates_and_cost() -> None:
    runs = [
        run("scatter-basic-matplotlib-renamed", cost_usd=0.002),
        run("pie-basic-seaborn-n12", library="seaborn", perturbation="n12", attempts=2, status="needs_attention"),
        run("box-basic-matplotlib-x10", perturbation="x10", status="failed", passed=False, accept_match=False),
        run("line-basic-seaborn-date", status="harness_error", passed=False, accept_match=None, cost_usd=0.0),
    ]

    summary = summarize(runs)

    assert (summary["runs"], summary["counted"], summary["harness_errors"]) == (4, 3, 1)
    assert summary["pass_rate"] == pytest.approx(2 / 4)  # the harness error counts as a run that did not pass
    assert summary["repaired_passes"] == 1
    assert summary["ok_rate"] == pytest.approx(1 / 4)
    assert summary["accept_match_rate"] == pytest.approx(2 / 3)  # a harness error has no outcome to match
    assert summary["cost_total_usd"] == pytest.approx(0.004)
    assert summary["cost_per_success_usd"] == pytest.approx(0.002)
    assert summary["median_cost_per_success_usd"] == pytest.approx(0.0015)
    assert summary["by_perturbation"]["x10"] == {"runs": 1, "passed": 0, "ok": 0, "pass_rate": 0.0}
    assert summary["statuses"] == {"failed": 1, "harness_error": 1, "needs_attention": 1, "ok": 1}


def test_diff_flags_a_regression_beyond_the_tolerance_and_lists_flips() -> None:
    baseline = report_of([run("a-matplotlib-x"), run("b-matplotlib-x"), run("c-matplotlib-x")])
    candidate = report_of([run("a-matplotlib-x"), run("b-matplotlib-x", passed=False), run("c-matplotlib-x")])

    diff = compare(baseline, candidate, tolerance=0.05)

    assert diff.regression
    assert diff.flipped == [Flip("b-matplotlib-x", 1, 1, 0, 1)]
    rows = {label: (base, cand, change) for label, base, cand, change in diff.rows}
    assert rows["Pass rate"] == ("100.0 %", "66.7 %", "-33.3 pp")
    assert rows["Runs compared"] == ("3", "3", "")
    markdown = diff_markdown(diff)
    assert "| Metric | Baseline | This run | Change |" in markdown
    assert "- `b-matplotlib-x`: pass → fail" in markdown and "**Regression**" in markdown
    assert "One run is 33.3 pp of the 3 compared runs" in markdown

    assert not compare(baseline, candidate, tolerance=0.5).regression
    assert not compare(baseline, baseline, tolerance=0.0).regression


def test_diff_without_a_shared_case_compares_nothing() -> None:
    diff = compare(report_of([run("a-matplotlib-x")]), report_of([run("b-matplotlib-x")]), tolerance=0.05)

    assert (diff.shared_cases, diff.only_in_baseline, diff.only_in_candidate) == (0, 1, 1)
    assert diff.flipped == [] and not diff.regression and "No case is in both" in diff.notes[0]


def test_a_smoke_run_is_compared_on_the_baselines_same_cases() -> None:
    full = [run(f"case-{index:02d}-matplotlib-x") for index in range(20)]
    for index in (0, 5, 9):
        full[index] = run(f"case-{index:02d}-matplotlib-x", passed=False, status="failed")
    baseline = report_of(full)  # 17 of 20 passed: 85 %
    smoke = report_of([dict(full[index]) for index in (0, 1, 2, 3)])  # the same outcomes: 3 of 4 passed

    diff = compare(baseline, smoke, tolerance=0.05)

    assert diff.shared_cases == 4 and diff.flipped == [] and not diff.regression
    rows = {label: (base, cand) for label, base, cand, _ in diff.rows}
    assert rows["Pass rate"] == ("75.0 %", "75.0 %")
    assert rows["Pass rate, all runs of each report"] == ("85.0 %", "75.0 %")
    assert "16 cases are only in the baseline" in " ".join(diff.notes)

    worse = report_of([dict(full[index]) for index in (0, 1, 2)] + [run("case-03-matplotlib-x", passed=False)])
    assert compare(baseline, worse, tolerance=0.05).flipped == [Flip("case-03-matplotlib-x", 1, 1, 0, 1)]
    assert compare(baseline, worse, tolerance=0.05).regression


def test_harness_errors_cannot_hide_a_regression() -> None:
    baseline = report_of([run(f"case-{index:02d}-matplotlib-x") for index in range(20)])
    crashed = [run(f"case-{index:02d}-matplotlib-x") for index in range(4)]
    crashed += [
        run(f"case-{index:02d}-matplotlib-x", status="harness_error", passed=False, accept_match=None)
        for index in range(4, 20)
    ]

    diff = compare(baseline, report_of(crashed), tolerance=0.05)

    assert diff.regression and len(diff.flipped) == 16


def test_flips_with_repeats_compare_the_share_of_passed_runs() -> None:
    baseline = report_of([run("a-matplotlib-x", repeat=1), run("a-matplotlib-x", repeat=2, passed=False)])
    same_share = report_of([run("a-matplotlib-x", repeat=1, passed=False), run("a-matplotlib-x", repeat=2)])
    worse = report_of([run("a-matplotlib-x", repeat=1, passed=False), run("a-matplotlib-x", repeat=2, passed=False)])

    assert compare(baseline, same_share, tolerance=0.05).flipped == []
    (flip,) = compare(baseline, worse, tolerance=0.05).flipped
    assert flip == Flip("a-matplotlib-x", 1, 2, 0, 2)
    assert "1 of 2 passed → 0 of 2" in diff_markdown(compare(baseline, worse, tolerance=0.05))


def test_summary_markdown_has_every_section() -> None:
    runs = [run("a-matplotlib-x"), run("b-matplotlib-x", status="failed", reason="render", passed=False)]
    report = report_of(runs, provider="anthropic-vertex", location="eu", renderer="fake")
    diff = compare(report, report, tolerance=0.05)

    text = summary_markdown(report, diff)

    for heading in ("## Results", "## By perturbation", "## By library", "## By spec", "## Against the baseline"):
        assert heading in text
    assert "## Runs that did not pass" in text and "`b-matplotlib-x`" in text


def schema_2_run(case_id: str, **fields: Any) -> dict[str, Any]:
    """A run with the diagnostic fields of report schema 2."""
    entries = [
        {"turn": 1, "attempt": 1, "adapter": "truncated", "finish_reason": "MAX_TOKENS", "stage": "adapter_truncated"},
        {"turn": 1, "attempt": 2, "adapter": "plan", "finish_reason": "STOP", "stage": "edit_apply"},
    ]
    values: dict[str, Any] = {
        "stage": "edit_apply",
        "stages": ["adapter_truncated", "edit_apply"],
        "shipped_attempt": None,
        "reviewed_attempt": None,
        "attempt_log": entries,
        "calls": [],
        "finish_reasons": {"adapter": {"MAX_TOKENS": 1, "STOP": 1}, "root": {"STOP": 2}},
        "edit_failure_kinds": {"multi_match": 1},
        "status": "failed",
        "reason": "validation",
        "passed": False,
        "attempts": 2,
    }
    values.update(fields)
    return run(case_id, **values)


def test_summary_counts_the_schema_2_diagnostics() -> None:
    runs = [
        schema_2_run("a-matplotlib-x"),
        schema_2_run(
            "b-matplotlib-x",
            stage="reviewer_ok",
            stages=["reviewer_ok"],
            shipped_attempt=1,
            reviewed_attempt=1,
            attempt_log=[{"turn": 1, "attempt": 1, "adapter": "plan", "stage": "reviewer_ok"}],
            finish_reasons={"adapter": {"STOP": 1}},
            edit_failure_kinds={},
            status="ok",
            reason=None,
            passed=True,
            attempts=1,
        ),
    ]

    summary = summarize(runs)

    assert summary["stages"] == {"edit_apply": 1, "reviewer_ok": 1}
    assert summary["stages_not_passed"] == {"edit_apply": 1}
    assert summary["finish_reasons"] == {"adapter": {"MAX_TOKENS": 1, "STOP": 2}, "root": {"STOP": 2}}
    assert summary["adapter_outcomes_by_attempt"] == {"1": {"plan": 1, "truncated": 1}, "2": {"plan": 1}}
    assert summary["edit_failure_kinds"] == {"multi_match": 1}
    assert summary["shipped_from_attempt"] == {"1": 1}
    text = summary_markdown(report_of(runs))
    assert "| Finish adapter MAX_TOKENS | 1 |" in text and "| Stage, not passed, edit_apply | 1 |" in text
    assert "| validation [edit_apply] |" in text  # the reason column names the stage


def test_a_schema_1_baseline_diffs_against_a_schema_2_run() -> None:
    """A baseline written before the diagnostic fields existed reads them as empty, never as a crash."""
    old = [run("a-matplotlib-x"), run("b-matplotlib-x", status="failed", reason="validation", passed=False)]
    baseline = report_of(old)
    new = [schema_2_run("a-matplotlib-x", status="ok", reason=None, passed=True), schema_2_run("b-matplotlib-x")]
    candidate = {**report_of(new), "schema": 2}

    diff = compare(baseline, candidate, tolerance=0.05)
    text = summary_markdown(candidate, diff)

    assert baseline["schema"] == 1 and not diff.regression and diff.flipped == []
    assert summarize(old)["stages"] == {} and summarize(old)["finish_reasons"] == {}
    assert "## Against the baseline" in text
    assert summary_markdown(baseline, compare(candidate, baseline, tolerance=0.05)).startswith("# Eval run")


# --- Galleries ------------------------------------------------------------------------------


@pytest.fixture
def rendered(tmp_path: Path) -> dict[str, Any]:
    (tmp_path / "renders").mkdir()
    png = fixture_png("light", (320, 180))
    runs = []
    for index in range(40):
        name = f"case-{index:02d}-matplotlib-x10"
        (tmp_path / "renders" / f"{name}-r1.png").write_bytes(png)
        runs.append(run(name, png=f"renders/{name}-r1.png", residual_defects=["VQ-03 (light): <small> markers"]))
    runs.append(run("failed-matplotlib-x10", status="failed", passed=False))
    (tmp_path / "renders" / "padded-matplotlib-x10-r1.png").write_bytes(png)
    runs.append(
        run(
            "padded-matplotlib-x10",
            status="needs_attention",
            passed=False,
            padded=True,
            png="renders/padded-matplotlib-x10-r1.png",
        )
    )
    return report_of(runs, provider="anthropic-vertex")


def test_gallery_is_valid_blind_html_with_thirty_judgeable_renders(rendered: dict[str, Any], tmp_path: Path) -> None:
    text = gallery_html(rendered, tmp_path, seed=7)

    checker = check_html(text)
    assert checker.doctype and checker.titles == 1 and checker.errors == [] and checker.stack == []
    images = [attrs for tag, attrs in checker.tags if tag == "img"]
    assert len(images) == 30 and all(str(attrs["src"]).startswith("data:image/png;base64,") for attrs in images)
    boxes = [attrs for tag, attrs in checker.tags if tag == "input"]
    assert len(boxes) == 60 and {attrs["data-choice"] for attrs in boxes} == {"accept", "reject"}
    items = json.loads(re.search(r'<script type="application/json" id="items">(.*?)</script>', text, re.S).group(1))
    assert len(items) == 30 and len({item["key"] for item in items}) == 30
    assert "&lt;small&gt;" in text  # residual lines are escaped
    assert "claude" not in text.lower() and "anthropic" not in text.lower()  # blind to the arm
    assert 'id="export"' in text and "acceptance_rate" in text


def test_gallery_sample_is_seeded_and_holds_passed_renders_only(rendered: dict[str, Any]) -> None:
    first = [item["case_id"] for item in sample_runs(rendered, seed=3)]
    assert first == [item["case_id"] for item in sample_runs(rendered, seed=3)]
    assert first != [item["case_id"] for item in sample_runs(rendered, seed=4)]
    assert len(sample_runs(rendered, size=50)) == 40  # never more than the passed renders
    assert "padded-matplotlib-x10" not in {run["case_id"] for run in passed_runs(rendered)}  # shipped, not passed


def test_gallery_all_lists_every_run(rendered: dict[str, Any]) -> None:
    text = gallery_all_html(rendered)

    checker = check_html(text)
    assert checker.doctype and checker.errors == [] and checker.stack == []
    assert text.count("<tr>") == 43  # the header row and 42 runs
    assert 'src="renders/case-00-matplotlib-x10-r1.png"' in text


def test_an_empty_report_still_renders(tmp_path: Path) -> None:
    empty = report_of([])

    assert check_html(gallery_html(empty, tmp_path)).errors == []
    assert "No passed render" in gallery_html(empty, tmp_path)


# --- The blind gallery over two runs ---------------------------------------------------------


def two_arms(tmp_path: Path) -> list[tuple[dict[str, Any], Path]]:
    """Two runs in their own folders: 12 cases pass in both, 3 only in the first, 2 only in the second."""
    png = fixture_png("light", (320, 180))
    arms = []
    for arm, model, provider, cases in (
        ("claude", "claude-haiku-5-5", "anthropic-vertex", [*range(12), 12, 13, 14]),
        ("gemini", "gemini-3.8-flash", "gemini", [*range(12), 15, 16]),
    ):
        folder = tmp_path / arm
        (folder / "renders").mkdir(parents=True)
        runs = []
        for index in cases:
            name = f"case-{index:02d}-seaborn-n12"
            (folder / "renders" / f"{name}-r1.png").write_bytes(png)
            runs.append(run(name, library="seaborn", png=f"renders/{name}-r1.png"))
        arms.append((report_of(runs, model=model, provider=provider, run_id=f"run-{arm}"), folder))
    return arms


def test_blind_gallery_shows_both_runs_of_the_same_cases_without_naming_them(tmp_path: Path) -> None:
    page, key = blind_gallery(two_arms(tmp_path), size=5, seed=1)

    checker = check_html(page)
    assert checker.doctype and checker.errors == [] and checker.stack == []
    assert len([attrs for tag, attrs in checker.tags if tag == "img"]) == 10
    for word in ("claude", "anthropic", "gemini", "run-claude", "run-gemini"):
        assert word not in page.lower()
    assert (key["cases"], key["common_cases"], len(key["items"])) == (5, 12, 10)
    by_case: dict[str, set[str]] = {}
    for item in key["items"].values():
        by_case.setdefault(item["case_id"], set()).add(item["arm"])
    assert len(by_case) == 5 and all(arms == {"a", "b"} for arms in by_case.values())
    assert all(int(case[5:7]) < 12 for case in by_case)  # only cases both runs passed
    assert key["arms"]["a"]["model"] == "claude-haiku-5-5" and key["arms"]["b"]["model"] == "gemini-3.8-flash"
    assert f'data-run="{key["blind_id"]}"' in page


def test_score_joins_the_export_to_the_key(tmp_path: Path) -> None:
    _, key = blind_gallery(two_arms(tmp_path), size=4, seed=2)
    judgements = {
        "run_id": key["blind_id"],
        "judgements": [
            {"key": card, "choice": "accept" if item["arm"] == "a" else ("reject" if index % 2 else None)}
            for index, (card, item) in enumerate(sorted(key["items"].items()))
        ],
    }

    result = score(key, judgements)

    assert (result["a"]["renders"], result["a"]["accepted"], result["a"]["acceptance_rate"]) == (4, 4, 1.0)
    assert result["b"]["accepted"] == 0 and result["b"]["rejected"] + result["b"]["open"] == 4
    with pytest.raises(ValueError, match="another gallery"):
        score(key, {**judgements, "run_id": "other"})


def test_blind_and_score_commands(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    arms = two_arms(tmp_path)
    paths = []
    for report, folder in arms:
        paths.append(folder / "report.json")
        paths[-1].write_text(json.dumps(report))

    code = main(["blind", "--report", str(paths[0]), "--report", str(paths[1]), "--out", str(tmp_path / "blind")])

    assert code == 0
    key = json.loads((tmp_path / "blind" / "blind-key.json").read_text())
    assert check_html((tmp_path / "blind" / "blind.html").read_text()).errors == []
    export = {"run_id": key["blind_id"], "judgements": [{"key": card, "choice": "accept"} for card in key["items"]]}
    (tmp_path / "judgements.json").write_text(json.dumps(export))
    capsys.readouterr()

    assert main(["score", "--key", str(tmp_path / "blind" / "blind-key.json"), str(tmp_path / "judgements.json")]) == 0
    table = capsys.readouterr().out
    assert "| a | anthropic-vertex | claude-haiku-5-5 | 12 | 12 | 0 | 0 | 100.0 % |" in table  # 12 common cases
    assert main(["score", "--key", str(tmp_path / "missing.json"), str(tmp_path / "judgements.json")]) == 2
