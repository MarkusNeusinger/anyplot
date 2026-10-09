"""Pricing, the report summary, the baseline diff, the Markdown and the review galleries, on synthetic runs."""

import json
import re
from pathlib import Path
from typing import Any

import pytest

from agents.anyplot.render.backends.fake import fixture_png
from agents.evals import pricing
from agents.evals.report import (
    compare,
    diff_markdown,
    gallery_all_html,
    gallery_html,
    percentile,
    sample_runs,
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
    assert summary["pass_rate"] == pytest.approx(2 / 3)
    assert summary["repaired_passes"] == 1
    assert summary["ok_rate"] == pytest.approx(1 / 3)
    assert summary["accept_match_rate"] == pytest.approx(2 / 3)
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
    assert diff.flipped == [("b-matplotlib-x#1", True, False)]
    rows = {label: (base, cand, change) for label, base, cand, change in diff.rows}
    assert rows["Pass rate"] == ("100.0 %", "66.7 %", "-33.3 pp")
    markdown = diff_markdown(diff)
    assert "| Metric | Baseline | This run | Change |" in markdown
    assert "- `b-matplotlib-x#1`: pass → fail" in markdown and "**Regression**" in markdown

    assert not compare(baseline, candidate, tolerance=0.5).regression
    assert not compare(baseline, baseline, tolerance=0.0).regression


def test_diff_notes_runs_that_exist_on_one_side_only() -> None:
    diff = compare(report_of([run("a-matplotlib-x")]), report_of([run("b-matplotlib-x")]), tolerance=0.05)

    assert (diff.only_in_baseline, diff.only_in_candidate) == (1, 1)
    assert diff.flipped == [] and "differ" in diff.notes[0]


def test_summary_markdown_has_every_section() -> None:
    runs = [run("a-matplotlib-x"), run("b-matplotlib-x", status="failed", reason="render", passed=False)]
    report = report_of(runs, provider="anthropic-vertex", location="eu", renderer="fake")
    diff = compare(report, report, tolerance=0.05)

    text = summary_markdown(report, diff)

    for heading in ("## Results", "## By perturbation", "## By library", "## By spec", "## Against the baseline"):
        assert heading in text
    assert "## Runs that did not pass" in text and "`b-matplotlib-x`" in text


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


def test_gallery_sample_is_seeded(rendered: dict[str, Any]) -> None:
    first = [item["case_id"] for item in sample_runs(rendered, seed=3)]
    assert first == [item["case_id"] for item in sample_runs(rendered, seed=3)]
    assert first != [item["case_id"] for item in sample_runs(rendered, seed=4)]
    assert len(sample_runs(rendered, size=50)) == 40  # never more than the shipped renders


def test_gallery_all_lists_every_run(rendered: dict[str, Any]) -> None:
    text = gallery_all_html(rendered)

    checker = check_html(text)
    assert checker.doctype and checker.errors == [] and checker.stack == []
    assert text.count("<tr>") == 42  # the header row and 41 runs
    assert 'src="renders/case-00-matplotlib-x10-r1.png"' in text


def test_an_empty_report_still_renders(tmp_path: Path) -> None:
    empty = report_of([])

    assert check_html(gallery_html(empty, tmp_path)).errors == []
    assert "No shipped render" in gallery_html(empty, tmp_path)
