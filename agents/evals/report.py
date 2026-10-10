"""Reports of the matrix harness: the summary, the diff against a baseline, Markdown, and the review galleries.

No import of `agents.anyplot` (importing that package builds the agents from the
settings, which the harness configures first), so the report code also works on a
saved report alone.

A report is the JSON `matrix.py` writes: `{"schema", "stamp", "summary", "runs",
"stopped"}`; a baseline is a report kept under `agents/evals/baselines/`. Each run
record is one case and repeat (see `matrix.base_record` for its fields).

**Pass.** A run passes when it shipped a render (`ok` or `needs_attention`) that
passed every deterministic gate: the host gates R1 to R3 without a padded canvas, and
no ADAPTATION validator finding on the shipped code. The advisory probe gates (G3,
G5, G7, G8) and the reviewer's verdict do not decide a pass; the owner's blind
judgement in the gallery does that for the sample, which holds passed renders only.
Every rate counts all runs: a run that crashed in the harness did not pass.
**Accept-match** compares the harness outcome (`accepted` when the status is `ok`, the
reviewer's pass) with a case's `expected` value; cases that expect `unknown` are left
out.

**Diff.** `compare` measures both reports over the case ids they share (all repeats of
each), so a smoke run is judged against the same 12 cases of a full baseline, not
against the baseline's whole-matrix rate; each report's own full rate is an extra row.

Run as a module, it merges two reports into one blind gallery and scores the export:

    python -m agents.evals.report blind --report A.json --report B.json --out DIR
    python -m agents.evals.report score --key DIR/blind-key.json judgements.json
"""

import argparse
import base64
import hashlib
import html
import io
import json
import math
import random
import statistics
import sys
from collections import Counter
from collections.abc import Callable, Iterable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, NamedTuple


REPORT_SCHEMA = 1
SHIPPED = ("ok", "needs_attention")
GALLERY_SIZE = 30
GALLERY_MAX_WIDTH = 1600
"""The gallery embeds each render scaled to at most this width; the full-size PNG stays in `renders/`."""


# --- Summary -------------------------------------------------------------------------------


def percentile(values: Iterable[float], q: float) -> float | None:
    """The `q` quantile (0 to 1) with linear interpolation, or None without values."""
    ordered = sorted(values)
    if not ordered:
        return None
    position = (len(ordered) - 1) * q
    low, high = math.floor(position), math.ceil(position)
    return ordered[low] + (ordered[high] - ordered[low]) * (position - low)


def _rate(part: int, whole: int) -> float | None:
    return part / whole if whole else None


def _group(runs: list[dict[str, Any]], key: Callable[[dict[str, Any]], str]) -> dict[str, dict[str, Any]]:
    groups: dict[str, list[dict[str, Any]]] = {}
    for run in runs:
        groups.setdefault(key(run), []).append(run)
    return {
        name: {
            "runs": len(items),
            "passed": sum(1 for run in items if run.get("passed")),
            "ok": sum(1 for run in items if run.get("status") == "ok"),
            "pass_rate": _rate(sum(1 for run in items if run.get("passed")), len(items)),
        }
        for name, items in sorted(groups.items())
    }


def _counter(runs: list[dict[str, Any]], field_name: str) -> dict[str, int]:
    total: Counter[str] = Counter()
    for run in runs:
        total.update(run.get(field_name) or {})
    return dict(sorted(total.items()))


def summarize(runs: list[dict[str, Any]]) -> dict[str, Any]:
    """The headline numbers of a run list.

    The pass and ok rates count every run, so harness errors count as failures and a
    run list that mostly crashed cannot look healthy. Latencies and calls per run
    cover the `counted` runs, the ones that finished in the service.
    """
    counted = [run for run in runs if run.get("status") != "harness_error"]
    passed = [run for run in runs if run.get("passed")]
    judged = [run for run in runs if run.get("accept_match") is not None]
    cost_total = sum(float(run.get("cost_usd") or 0.0) for run in runs)
    e2e = [run["e2e_s"] for run in counted if isinstance(run.get("e2e_s"), int | float)]
    ttfe = [run["ttfe_s"] for run in counted if isinstance(run.get("ttfe_s"), int | float)]
    renders = [value for run in counted for value in run.get("render_s") or []]
    tokens: Counter[str] = Counter()
    for run in runs:
        tokens.update(run.get("tokens") or {})
    reviewer = Counter(str((run.get("reviewer") or {}).get("verdict")) for run in counted)
    return {
        "runs": len(runs),
        "counted": len(counted),
        "harness_errors": len(runs) - len(counted),
        "pipeline_errors": sum(1 for run in counted if run.get("reason") == "error"),
        "statuses": dict(sorted(Counter(str(run.get("status")) for run in runs).items())),
        "passed": len(passed),
        "pass_rate": _rate(len(passed), len(runs)),
        "repaired_passes": sum(1 for run in passed if run.get("attempts") == 2),
        "ok_rate": _rate(sum(1 for run in runs if run.get("status") == "ok"), len(runs)),
        "accept_judged": len(judged),
        "accept_match_rate": _rate(sum(1 for run in judged if run.get("accept_match")), len(judged)),
        "cost_total_usd": cost_total,
        "cost_per_run_usd": cost_total / len(runs) if runs else None,
        "cost_per_success_usd": cost_total / len(passed) if passed else None,
        "median_cost_per_success_usd": statistics.median(float(run.get("cost_usd") or 0.0) for run in passed)
        if passed
        else None,
        "latency_s": {
            "e2e_p50": percentile(e2e, 0.5),
            "e2e_p95": percentile(e2e, 0.95),
            "ttfe_p50": percentile(ttfe, 0.5),
            "ttfe_p95": percentile(ttfe, 0.95),
            "render_p50": percentile(renders, 0.5),
            "render_p95": percentile(renders, 0.95),
        },
        "llm_calls_per_run": statistics.fmean(int(run.get("llm_calls") or 0) for run in counted) if counted else None,
        "tokens": dict(sorted(tokens.items())),
        "gate_failures": _counter(runs, "gate_failures"),
        "validator_rejections": _counter(runs, "validator_rejections"),
        "adapter_outcomes": _counter(runs, "adapter_outcomes"),
        "edit_apply_failures": sum(int(run.get("edit_apply_failures") or 0) for run in runs),
        "reviewer": dict(sorted(reviewer.items())),
        "model_versions": sorted({version for run in runs for version in run.get("model_versions") or []}),
        "by_perturbation": _group(runs, lambda run: str(run.get("perturbation") or "custom")),
        "by_library": _group(runs, lambda run: str(run.get("library"))),
        "by_spec": _group(runs, lambda run: str(run.get("spec_id"))),
    }


# --- Diff ---------------------------------------------------------------------------------


class Flip(NamedTuple):
    """A shared case whose share of passed runs changed: `passed` of `runs` in the baseline and in this run."""

    case_id: str
    base_passed: int
    base_runs: int
    cand_passed: int
    cand_runs: int


@dataclass
class Diff:
    """A candidate report against a baseline over their shared cases: rows, flipped cases, the regression verdict."""

    rows: list[tuple[str, str, str, str]]
    flipped: list[Flip]
    regression: bool
    tolerance: float
    baseline_label: str
    shared_cases: int = 0
    only_in_baseline: int = 0
    only_in_candidate: int = 0
    notes: list[str] = field(default_factory=list)


def _pct(value: float | None) -> str:
    return "n/a" if value is None else f"{value * 100:.1f} %"


def _usd(value: float | None) -> str:
    return "n/a" if value is None else f"${value:.4f}"


def _secs(value: float | None) -> str:
    return "n/a" if value is None else f"{value:.1f} s"


def _num(value: float | None) -> str:
    return "n/a" if value is None else f"{value:.2f}"


def _change(base: float | None, cand: float | None, kind: str) -> str:
    if base is None or cand is None:
        return ""
    delta = cand - base
    if kind == "pct":
        return f"{delta * 100:+.1f} pp"
    if kind == "usd":
        relative = f" ({delta / base * 100:+.0f} %)" if base else ""
        return f"{'+' if delta >= 0 else '-'}${abs(delta):.4f}{relative}"
    if kind == "secs":
        return f"{delta:+.1f} s"
    return f"{delta:+.2f}"


METRICS: tuple[tuple[str, Callable[[dict[str, Any]], float | None], str], ...] = (
    ("Pass rate", lambda s: s.get("pass_rate"), "pct"),
    ("Accept-match rate", lambda s: s.get("accept_match_rate"), "pct"),
    ("ok rate", lambda s: s.get("ok_rate"), "pct"),
    ("Cost per successful plot", lambda s: s.get("cost_per_success_usd"), "usd"),
    ("Median cost per successful plot", lambda s: s.get("median_cost_per_success_usd"), "usd"),
    ("p50 end to end", lambda s: (s.get("latency_s") or {}).get("e2e_p50"), "secs"),
    ("p95 end to end", lambda s: (s.get("latency_s") or {}).get("e2e_p95"), "secs"),
    ("p50 time to first event", lambda s: (s.get("latency_s") or {}).get("ttfe_p50"), "secs"),
    ("LLM calls per run", lambda s: s.get("llm_calls_per_run"), "num"),
)
FORMATS: dict[str, Callable[[float | None], str]] = {"pct": _pct, "usd": _usd, "secs": _secs, "num": _num}


def _by_case(report: dict[str, Any]) -> dict[str, list[dict[str, Any]]]:
    """A report's runs grouped by case id (every repeat, harness errors included)."""
    groups: dict[str, list[dict[str, Any]]] = {}
    for run in report.get("runs") or []:
        groups.setdefault(str(run.get("case_id")), []).append(run)
    return groups


def _row(label: str, base: float | None, cand: float | None, kind: str) -> tuple[str, str, str, str]:
    return (label, FORMATS[kind](base), FORMATS[kind](cand), _change(base, cand, kind))


def compare(baseline: dict[str, Any], candidate: dict[str, Any], *, tolerance: float) -> Diff:
    """The diff of `candidate` against `baseline` over the case ids both hold.

    Both sides are summarised afresh over those cases (all their repeats), so the rows
    and the regression verdict (the shared pass rate below the baseline's minus
    `tolerance`) compare like with like. A case flips when its share of passed runs
    changed. Each report's pass rate over all of its own runs is an extra row when the
    case sets differ.
    """
    base_cases, cand_cases = _by_case(baseline), _by_case(candidate)
    shared = sorted(base_cases.keys() & cand_cases.keys())
    base_runs = [run for case in shared for run in base_cases[case]]
    cand_runs = [run for case in shared for run in cand_cases[case]]
    base_summary, cand_summary = summarize(base_runs), summarize(cand_runs)
    rows = [("Runs compared", str(len(base_runs)), str(len(cand_runs)), "")]
    rows += [_row(label, read(base_summary), read(cand_summary), kind) for label, read, kind in METRICS]
    only_base, only_cand = len(base_cases.keys() - cand_cases.keys()), len(cand_cases.keys() - base_cases.keys())
    if only_base or only_cand:
        rows.append(
            _row(
                "Pass rate, all runs of each report",
                summarize([run for runs in base_cases.values() for run in runs])["pass_rate"],
                summarize([run for runs in cand_cases.values() for run in runs])["pass_rate"],
                "pct",
            )
        )
    flipped = []
    for case in shared:
        base_passed = sum(1 for run in base_cases[case] if run.get("passed"))
        cand_passed = sum(1 for run in cand_cases[case] if run.get("passed"))
        base_total, cand_total = len(base_cases[case]), len(cand_cases[case])
        if base_passed * cand_total != cand_passed * base_total:
            flipped.append(Flip(case, base_passed, base_total, cand_passed, cand_total))
    base_rate, cand_rate = base_summary["pass_rate"], cand_summary["pass_rate"]
    regression = base_rate is not None and cand_rate is not None and cand_rate < base_rate - tolerance
    stamp = baseline.get("stamp") or {}
    diff = Diff(
        rows=rows,
        flipped=flipped,
        regression=regression,
        tolerance=tolerance,
        baseline_label=f"{stamp.get('model', '?')} ({stamp.get('date', '?')})",
        shared_cases=len(shared),
        only_in_baseline=only_base,
        only_in_candidate=only_cand,
    )
    if not shared:
        diff.notes.append("No case is in both reports, so nothing was compared.")
    elif only_base or only_cand:
        diff.notes.append(
            f"The rows compare the {len(shared)} cases both reports hold; {only_base} cases are only in the "
            f"baseline and {only_cand} only in this run."
        )
    if cand_runs and 1 / len(cand_runs) > tolerance:
        diff.notes.append(
            f"One run is {100 / len(cand_runs):.1f} pp of the {len(cand_runs)} compared runs, more than the "
            f"{tolerance * 100:.1f} pp tolerance: a single run that flips from pass to fail is a regression."
        )
    return diff


def _flip_text(flip: Flip) -> str:
    if flip.base_runs == flip.cand_runs == 1:
        return f"{'pass' if flip.base_passed else 'fail'} → {'pass' if flip.cand_passed else 'fail'}"
    return f"{flip.base_passed} of {flip.base_runs} passed → {flip.cand_passed} of {flip.cand_runs}"


def diff_markdown(diff: Diff) -> str:
    """The diff as a Markdown table, readable in a terminal and in a job summary."""
    lines = [
        f"Baseline {diff.baseline_label}, over the {diff.shared_cases} cases both reports hold; a pass-rate drop "
        f"of more than {diff.tolerance * 100:.1f} pp is a regression.",
        "",
        "| Metric | Baseline | This run | Change |",
        "|---|---|---|---|",
        *(f"| {label} | {base} | {cand} | {change} |" for label, base, cand, change in diff.rows),
        "",
    ]
    if diff.flipped:
        lines.append(f"Flipped cases ({len(diff.flipped)}):")
        lines.append("")
        lines += [f"- `{flip.case_id}`: {_flip_text(flip)}" for flip in diff.flipped]
    else:
        lines.append("No case flipped between pass and fail.")
    lines += ["", *diff.notes] if diff.notes else []
    lines += [
        "",
        "**Regression**: the pass rate dropped below the baseline minus the tolerance." if diff.regression else "",
    ]
    return "\n".join(lines).rstrip() + "\n"


# --- Markdown summary ----------------------------------------------------------------------


def _table(header: list[str], rows: list[list[str]]) -> list[str]:
    return [
        "| " + " | ".join(header) + " |",
        "|" + "---|" * len(header),
        *("| " + " | ".join(row) + " |" for row in rows),
        "",
    ]


def _groups_table(groups: dict[str, dict[str, Any]], label: str) -> list[str]:
    rows = [
        [name, str(item["runs"]), str(item["passed"]), _pct(item["pass_rate"]), str(item["ok"])]
        for name, item in groups.items()
    ]
    return _table([label, "Runs", "Passed", "Pass rate", "ok"], rows)


def _failure_reason(run: dict[str, Any]) -> str:
    """The reason column of a run that did not pass, with the error class when there was one."""
    reason = str(run.get("reason") or ("canvas padded" if run.get("padded") else ""))
    error = run.get("pipeline_error") or (run.get("error") if run.get("status") == "harness_error" else None)
    return f"{reason} ({error})" if reason and error else reason or str(error or "")


def summary_markdown(report: dict[str, Any], diff: Diff | None = None) -> str:
    """The Markdown summary written next to the JSON report."""
    stamp, summary = report.get("stamp") or {}, report.get("summary") or {}
    latency = summary.get("latency_s") or {}
    lines = [
        f"# Eval run {stamp.get('date', '')}: {stamp.get('model', '')}",
        "",
        f"Provider `{stamp.get('provider')}`, model `{stamp.get('model')}`, judge `{stamp.get('judge_model')}`, "
        f"location `{stamp.get('location')}`, renderer `{stamp.get('renderer')}`; cases `{stamp.get('cases')}` "
        f"({stamp.get('case_count')} cases, {stamp.get('repeats')} runs each); ADK {stamp.get('adk_version')}, "
        f"commit `{str(stamp.get('git_sha') or '')[:12]}`.",
        "",
    ]
    if report.get("stopped"):
        lines += [f"**Stopped early** ({report['stopped']}): the rates cover the runs that finished.", ""]
    lines += ["## Results", ""]
    lines += _table(
        ["Metric", "Value"],
        [
            [
                "Runs",
                f"{summary.get('runs')} ({summary.get('harness_errors')} harness errors, "
                f"{summary.get('pipeline_errors', 0)} pipeline errors)",
            ],
            [
                "Pass rate",
                f"{_pct(summary.get('pass_rate'))} ({summary.get('passed')} passed, "
                f"{summary.get('repaired_passes')} of them after a repair)",
            ],
            ["ok rate", _pct(summary.get("ok_rate"))],
            ["Accept-match rate", f"{_pct(summary.get('accept_match_rate'))} of {summary.get('accept_judged')}"],
            ["Statuses", ", ".join(f"{name} {count}" for name, count in (summary.get("statuses") or {}).items())],
            ["Cost at list price", _usd(summary.get("cost_total_usd"))],
            ["Cost per successful plot", _usd(summary.get("cost_per_success_usd"))],
            ["Median cost per successful plot", _usd(summary.get("median_cost_per_success_usd"))],
            ["End to end p50 / p95", f"{_secs(latency.get('e2e_p50'))} / {_secs(latency.get('e2e_p95'))}"],
            ["Time to first event p50 / p95", f"{_secs(latency.get('ttfe_p50'))} / {_secs(latency.get('ttfe_p95'))}"],
            ["Render p50 / p95", f"{_secs(latency.get('render_p50'))} / {_secs(latency.get('render_p95'))}"],
            ["LLM calls per run", _num(summary.get("llm_calls_per_run"))],
            ["Tokens", ", ".join(f"{name} {count:,}" for name, count in (summary.get("tokens") or {}).items())],
            ["Model versions", ", ".join(summary.get("model_versions") or []) or "n/a"],
        ],
    )
    lines += ["## By perturbation", "", *_groups_table(summary.get("by_perturbation") or {}, "Perturbation")]
    lines += ["## By library", "", *_groups_table(summary.get("by_library") or {}, "Library")]
    lines += ["## By spec", "", *_groups_table(summary.get("by_spec") or {}, "Spec")]
    lines += ["## Gates, validator and reviewer", ""]
    counts = [
        *(["Gate " + name, str(count)] for name, count in (summary.get("gate_failures") or {}).items()),
        *(["Validator " + name, str(count)] for name, count in (summary.get("validator_rejections") or {}).items()),
        *(["Adapter " + name, str(count)] for name, count in (summary.get("adapter_outcomes") or {}).items()),
        ["Edit-apply failure lines", str(summary.get("edit_apply_failures"))],
        *(["Reviewer " + name, str(count)] for name, count in (summary.get("reviewer") or {}).items()),
    ]
    lines += _table(["Finding", "Count"], counts)
    if diff is not None:
        lines += ["## Against the baseline", "", diff_markdown(diff)]
    failures = [run for run in report.get("runs") or [] if not run.get("passed")]
    if failures:
        lines += ["## Runs that did not pass", ""]
        lines += _table(
            ["Case", "Repeat", "Status", "Reason", "Attempts", "Gates", "Validator"],
            [
                [
                    f"`{run.get('case_id')}`",
                    str(run.get("repeat")),
                    str(run.get("status")),
                    _failure_reason(run),
                    str(run.get("attempts")),
                    ", ".join(f"{name} {count}" for name, count in (run.get("gate_failures") or {}).items()),
                    ", ".join(f"{name} {count}" for name, count in (run.get("validator_rejections") or {}).items()),
                ]
                for run in failures
            ],
        )
    return "\n".join(lines).rstrip() + "\n"


# --- Galleries ----------------------------------------------------------------------------

_STYLE = """
:root { color-scheme: light dark; --bg: #faf8f1; --card: #ffffff; --ink: #1a1a17; --muted: #5d5b52;
  --line: #d9d6cb; --accept: #1d7a46; --reject: #b71d27; }
@media (prefers-color-scheme: dark) { :root { --bg: #1a1a17; --card: #24241f; --ink: #f0efe8;
  --muted: #b3b1a6; --line: #3b3a33; --accept: #5cc98a; --reject: #f07178; } }
* { box-sizing: border-box; }
body { margin: 0; background: var(--bg); color: var(--ink); font: 15px/1.5 system-ui, sans-serif; }
header, main { max-width: 1240px; margin: 0 auto; padding: 16px; }
header { position: sticky; top: 0; background: var(--bg); border-bottom: 1px solid var(--line); z-index: 1; }
@media (max-width: 700px) { header { position: static; } }
a { color: inherit; }
h1 { font-size: 20px; margin: 0 0 4px; }
p { margin: 4px 0; color: var(--muted); }
.bar { display: flex; flex-wrap: wrap; gap: 12px; align-items: center; margin-top: 8px; }
button { font: inherit; padding: 6px 14px; border-radius: 6px; border: 1px solid var(--line);
  background: var(--card); color: var(--ink); cursor: pointer; }
.card { background: var(--card); border: 1px solid var(--line); border-radius: 10px; margin: 16px 0; padding: 12px; }
.card img { width: 100%; height: auto; display: block; border-radius: 6px; border: 1px solid var(--line); }
.meta { display: flex; flex-wrap: wrap; gap: 6px 16px; margin: 8px 0; font-size: 14px; }
.meta b { font-weight: 600; }
ul.residual { margin: 4px 0 8px 20px; padding: 0; font-size: 13px; color: var(--muted); }
.choice { display: flex; gap: 20px; font-weight: 600; }
.choice label { display: flex; gap: 6px; align-items: center; cursor: pointer; }
.choice .accept { color: var(--accept); } .choice .reject { color: var(--reject); }
table { width: 100%; border-collapse: collapse; font-size: 13px; }
th, td { text-align: left; padding: 6px; border-bottom: 1px solid var(--line); vertical-align: top; }
td img { width: 160px; height: auto; border: 1px solid var(--line); border-radius: 4px; }
.scroll { overflow-x: auto; }
"""

_SCRIPT = """
(function () {
  var items = JSON.parse(document.getElementById("items").textContent);
  var key = "anyplot-eval-gallery:" + document.body.dataset.run;
  var choices = {};
  try { choices = JSON.parse(window.localStorage.getItem(key) || "{}") || {}; } catch (e) { choices = {}; }
  function save() { try { window.localStorage.setItem(key, JSON.stringify(choices)); } catch (e) {} }
  function count() {
    var accepted = 0, rejected = 0;
    items.forEach(function (item) {
      if (choices[item.key] === "accept") accepted++;
      if (choices[item.key] === "reject") rejected++;
    });
    document.getElementById("progress").textContent =
      accepted + " accepted, " + rejected + " rejected, " + (items.length - accepted - rejected) + " open";
    return { accepted: accepted, rejected: rejected };
  }
  document.querySelectorAll("input[data-choice]").forEach(function (box) {
    var itemKey = box.dataset.key;
    box.checked = choices[itemKey] === box.dataset.choice;
    box.addEventListener("change", function () {
      document.querySelectorAll('input[data-key="' + itemKey + '"]').forEach(function (other) {
        if (other !== box) other.checked = false;
      });
      choices[itemKey] = box.checked ? box.dataset.choice : null;
      save();
      count();
    });
  });
  document.getElementById("export").addEventListener("click", function () {
    var totals = count();
    var judged = totals.accepted + totals.rejected;
    var payload = {
      run_id: document.body.dataset.run,
      sample_seed: Number(document.body.dataset.seed),
      accepted: totals.accepted,
      rejected: totals.rejected,
      open: items.length - judged,
      acceptance_rate: judged ? totals.accepted / judged : null,
      judgements: items.map(function (item) {
        return { key: item.key, case_id: item.case_id, repeat: item.repeat, choice: choices[item.key] || null };
      })
    };
    var blob = new Blob([JSON.stringify(payload, null, 2) + "\\n"], { type: "application/json" });
    var link = document.createElement("a");
    link.href = URL.createObjectURL(blob);
    link.download = "judgements-" + document.body.dataset.run + ".json";
    document.body.appendChild(link);
    link.click();
    link.remove();
  });
  count();
})();
"""


def _esc(value: Any) -> str:
    return html.escape(str(value), quote=True)


def passed_runs(report: dict[str, Any]) -> list[dict[str, Any]]:
    """The runs whose render passed the deterministic gates and was saved, in report order.

    The gallery samples only these: a padded canvas or an ADAPTATION finding already
    failed the run, so the owner's acceptance rate measures the renders that passed.
    """
    return [run for run in report.get("runs") or [] if run.get("passed") and run.get("png")]


def sample_runs(report: dict[str, Any], *, size: int = GALLERY_SIZE, seed: int = 0) -> list[dict[str, Any]]:
    """A seeded random sample of `size` passed runs, in random order."""
    candidates = passed_runs(report)
    return random.Random(seed).sample(candidates, min(size, len(candidates)))


def png_data_uri(path: Path, max_width: int = GALLERY_MAX_WIDTH) -> str:
    """The PNG at `path` as a data URI, scaled down to `max_width` (Pillow) when it is wider."""
    data = path.read_bytes()
    try:
        from PIL import Image

        with Image.open(io.BytesIO(data)) as image:
            if image.width > max_width:
                image.thumbnail((max_width, max_width * image.height // image.width))
                buffer = io.BytesIO()
                image.save(buffer, format="PNG", optimize=True)
                data = buffer.getvalue()
    except (OSError, ValueError):
        pass  # not a decodable PNG: embed it as it is
    return "data:image/png;base64," + base64.b64encode(data).decode("ascii")


def _meta(run: dict[str, Any]) -> str:
    fields = [
        ("Spec", run.get("spec_id")),
        ("Library", run.get("library")),
        ("Perturbation", run.get("perturbation") or "custom"),
        ("Status", run.get("status")),
    ]
    return "".join(f"<span><b>{_esc(label)}</b> {_esc(value)}</span>" for label, value in fields)


JUDGE_HINT = (
    "Judge each plot as a user would: accept it when you would use it as it is. Your choices stay in this "
    "browser until you export them."
)


def _review_page(
    entries: list[tuple[str, dict[str, Any], Path]], *, page_id: str, seed: int, title: str, intro: str
) -> str:
    """A self-contained review page: one card per `(key, run, png path)` with an accept and reject pair.

    The CSS, the script and the PNGs (as data URIs) are inline. The page names no
    provider and no model; the export lists every key with its choice.
    """
    items = []
    cards = []
    for index, (key, run, png) in enumerate(entries, start=1):
        items.append(
            {
                "key": key,
                "case_id": run.get("case_id"),
                "repeat": run.get("repeat"),
                "spec_id": run.get("spec_id"),
                "library": run.get("library"),
                "perturbation": run.get("perturbation"),
                "status": run.get("status"),
            }
        )
        residual = "".join(f"<li>{_esc(line)}</li>" for line in run.get("residual_defects") or [])
        cards.append(
            f'<section class="card" id="{key}">'
            f'<img alt="{_esc(run.get("spec_id"))} rendered with {_esc(run.get("library"))}" '
            f'src="{png_data_uri(png)}">'
            f'<div class="meta"><span><b>#{index}</b></span>{_meta(run)}</div>'
            + (f'<ul class="residual">{residual}</ul>' if residual else "")
            + f'<div class="choice"><label class="accept"><input type="checkbox" data-key="{key}" '
            f'data-choice="accept"> Accept</label><label class="reject"><input type="checkbox" data-key="{key}" '
            f'data-choice="reject"> Reject</label></div></section>'
        )
    items_json = json.dumps(items, ensure_ascii=False).replace("</", "<\\/")
    return (
        "<!doctype html>\n"
        '<html lang="en">\n<head>\n<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
        f"<title>{_esc(title)}</title>\n"
        f"<style>{_STYLE}</style>\n</head>\n"
        f'<body data-run="{_esc(page_id)}" data-seed="{seed}">\n'
        f"<header><h1>{_esc(title)}</h1><p>{intro}</p>"
        '<div class="bar"><button id="export" type="button">Export judgements as JSON</button>'
        '<span id="progress"></span></div></header>\n'
        f"<main>{''.join(cards) or '<p>No passed render to review.</p>'}</main>\n"
        f'<script type="application/json" id="items">{items_json}</script>\n'
        f"<script>{_SCRIPT}</script>\n"
        "</body>\n</html>\n"
    )


def gallery_html(report: dict[str, Any], out_dir: Path, *, size: int = GALLERY_SIZE, seed: int = 0) -> str:
    """The review page of one run: a sample of passed renders with an accept and reject pair each.

    It never names the provider or the model; the folder it sits in may, so use
    `blind_gallery` to compare two arms without knowing which is which.
    """
    stamp = report.get("stamp") or {}
    sample = sample_runs(report, size=size, seed=seed)
    entries = [(f"k{index:02d}", run, out_dir / str(run["png"])) for index, run in enumerate(sample, start=1)]
    intro = (
        f"{len(sample)} renders sampled at random from the {len(passed_runs(report))} renders that passed the "
        f'gates (seed {seed}). {JUDGE_HINT} <a href="gallery-all.html">All renders</a>'
    )
    return _review_page(
        entries, page_id=str(stamp.get("run_id") or "run"), seed=seed, title="Render review", intro=intro
    )


ARMS: tuple[str, str] = ("a", "b")


def _passed_by_key(report: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {f"{run.get('case_id')}#{run.get('repeat')}": run for run in passed_runs(report)}


def blind_gallery(
    reports: list[tuple[dict[str, Any], Path]], *, size: int = GALLERY_SIZE, seed: int = 0
) -> tuple[str, dict[str, Any]]:
    """One review page over two runs, and the key that says which render came from which run.

    `reports` is two `(report, the directory its renders/ folder is in)` pairs. The page
    samples `size` case runs (`case_id#repeat`) that passed in both reports and shows
    both renders of each, all shuffled; it names neither run. The key (written next to
    the page, never into it) maps every card to its run, for `score`.
    """
    if len(reports) != len(ARMS):
        raise ValueError("a blind gallery compares exactly two reports")
    passed = [_passed_by_key(report) for report, _ in reports]
    common = sorted(passed[0].keys() & passed[1].keys())
    chosen = random.Random(seed).sample(common, min(size, len(common)))
    cards = [(arm, case_key) for case_key in chosen for arm in range(len(ARMS))]
    random.Random(seed + 1).shuffle(cards)
    run_ids = [str((report.get("stamp") or {}).get("run_id")) for report, _ in reports]
    page_id = hashlib.sha256(f"{run_ids[0]}|{run_ids[1]}|{seed}".encode()).hexdigest()[:12]
    entries = []
    key_items: dict[str, dict[str, Any]] = {}
    for index, (arm, case_key) in enumerate(cards, start=1):
        run = passed[arm][case_key]
        card = f"k{index:03d}"
        entries.append((card, run, reports[arm][1] / str(run["png"])))
        key_items[card] = {"arm": ARMS[arm], "case_id": run.get("case_id"), "repeat": run.get("repeat")}
    intro = (
        f"{len(chosen)} cases that passed in both runs, each shown twice (once from each run, in random order: "
        f"{len(entries)} renders, seed {seed}). The page does not say which run made a render; judge every plot "
        f"on its own. {JUDGE_HINT}"
    )
    page = _review_page(entries, page_id=page_id, seed=seed, title="Blind render review", intro=intro)
    key: dict[str, Any] = {
        "blind_id": page_id,
        "seed": seed,
        "cases": len(chosen),
        "common_cases": len(common),
        "arms": {
            ARMS[index]: {
                "provider": (report.get("stamp") or {}).get("provider"),
                "model": (report.get("stamp") or {}).get("model"),
                "run_id": run_ids[index],
                "passed": len(passed[index]),
            }
            for index, (report, _) in enumerate(reports)
        },
        "items": key_items,
    }
    return page, key


def score(key: dict[str, Any], judgements: dict[str, Any]) -> dict[str, dict[str, Any]]:
    """The acceptance per run of a blind gallery's export, joined to its key by card key."""
    if judgements.get("run_id") != key.get("blind_id"):
        raise ValueError("the judgements belong to another gallery (run_id differs from the key's blind_id)")
    choices = {str(item.get("key")): item.get("choice") for item in judgements.get("judgements") or []}
    result: dict[str, dict[str, Any]] = {}
    for arm, about in (key.get("arms") or {}).items():
        cards = [card for card, item in (key.get("items") or {}).items() if item.get("arm") == arm]
        accepted = sum(1 for card in cards if choices.get(card) == "accept")
        rejected = sum(1 for card in cards if choices.get(card) == "reject")
        result[arm] = {
            "provider": about.get("provider"),
            "model": about.get("model"),
            "renders": len(cards),
            "accepted": accepted,
            "rejected": rejected,
            "open": len(cards) - accepted - rejected,
            "acceptance_rate": _rate(accepted, accepted + rejected),
        }
    return result


def _load_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{path} is not a JSON object")
    return data


def main(argv: list[str] | None = None) -> int:
    """`blind`: write a two-run blind gallery and its key; `score`: acceptance per run from an export."""
    parser = argparse.ArgumentParser(prog="python -m agents.evals.report", description=main.__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    blind = commands.add_parser("blind", help="merge two reports into one blind review page")
    blind.add_argument("--report", type=Path, action="append", required=True, help="a report JSON (twice)")
    blind.add_argument("--out", type=Path, required=True, help="directory for blind.html and blind-key.json")
    blind.add_argument("--size", type=int, default=GALLERY_SIZE, help="cases to sample, two renders each (30)")
    blind.add_argument("--seed", type=int, default=0, help="seed of the sample and the order (0)")
    scored = commands.add_parser("score", help="acceptance per run from a blind gallery's export")
    scored.add_argument("--key", type=Path, required=True, help="the blind-key.json next to the page")
    scored.add_argument("judgements", type=Path, help="the exported judgements JSON")
    args = parser.parse_args(argv)
    try:
        if args.command == "blind":
            if len(args.report) != len(ARMS):
                parser.error("pass --report exactly twice")
            reports = [(_load_json(path), path.resolve().parent) for path in args.report]
            page, key = blind_gallery(reports, size=args.size, seed=args.seed)
            args.out.mkdir(parents=True, exist_ok=True)
            (args.out / "blind.html").write_text(page, encoding="utf-8")
            (args.out / "blind-key.json").write_text(json.dumps(key, indent=2) + "\n", encoding="utf-8")
            print(f"Page: {args.out / 'blind.html'} ({len(key['items'])} renders of {key['cases']} cases)")
            print(f"Key: {args.out / 'blind-key.json'} (do not open it before you have judged the page)")
            return 0
        result = score(_load_json(args.key), _load_json(args.judgements))
    except (OSError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    print("| Run | Provider | Model | Renders | Accepted | Rejected | Open | Acceptance |")
    print("|---|---|---|---|---|---|---|---|")
    for arm, row in result.items():
        print(
            f"| {arm} | {row['provider']} | {row['model']} | {row['renders']} | {row['accepted']} | "
            f"{row['rejected']} | {row['open']} | {_pct(row['acceptance_rate'])} |"
        )
    return 0


def gallery_all_html(report: dict[str, Any]) -> str:
    """The second page: every run with its status and a thumbnail from `renders/` (not embedded, so it stays small)."""
    rows = []
    for run in report.get("runs") or []:
        image = (
            f'<a href="{_esc(run["png"])}"><img loading="lazy" alt="" src="{_esc(run["png"])}"></a>'
            if run.get("png")
            else ""
        )
        residual = "<br>".join(_esc(line) for line in run.get("residual_defects") or [])
        rows.append(
            "<tr>"
            f"<td>{image}</td><td>{_esc(run.get('case_id'))}<br>repeat {_esc(run.get('repeat'))}</td>"
            f"<td>{_esc(run.get('status'))}{('<br>' + _esc(run.get('reason'))) if run.get('reason') else ''}</td>"
            f"<td>{'pass' if run.get('passed') else 'fail'}</td><td>{_esc(run.get('attempts'))}</td>"
            f"<td>{residual}</td></tr>"
        )
    return (
        "<!doctype html>\n"
        '<html lang="en">\n<head>\n<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
        "<title>All renders</title>\n"
        f"<style>{_STYLE}</style>\n</head>\n<body>\n"
        "<header><h1>All renders</h1>"
        f'<p>{len(rows)} runs. Thumbnails load from the renders folder next to this page. <a href="gallery.html">'
        "Back to the review</a></p></header>\n"
        '<main><div class="scroll"><table><thead><tr><th>Render</th><th>Case</th><th>Status</th><th>Pass</th>'
        "<th>Attempts</th><th>Residual notes</th></tr></thead><tbody>"
        + "".join(rows)
        + "</tbody></table></div></main>\n</body>\n</html>\n"
    )


if __name__ == "__main__":
    raise SystemExit(main())
