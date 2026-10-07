#!/usr/bin/env python3
"""Collect one week of regenerations for the weekly regen review.

Reads GitHub only (``gh``), writes nothing there. For every pull request
labelled ``regen`` and created on or after ``--since`` it gathers the gate
record, the parsed review comment, the write-back pull request, the pair
artifact that holds both renders, and the production render URLs, then flags
what the weekly review must look at. It also counts the pipeline runs of the
window by conclusion, and with ``--costs`` sums the session cost that the
Claude steps print into their job logs.

    uv run python .claude/skills/review-regen-week/collect_week.py \\
        --since 2026-10-01 --out agentic/runs/weekly-review/2026-10-07.json \\
        [--previous agentic/runs/weekly-review/2026-09-30.json] [--costs]

The JSON holds every row and the summary; stdout gets a Markdown digest that
the report starts from. Exit code 0 even when flags fire: flags are prompts
to look, not failures.
"""

from __future__ import annotations

import argparse
import importlib
import json
import random
import re
import statistics
import subprocess
import sys
from collections import Counter, defaultdict
from collections.abc import Callable, Sequence
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


# The script lives in a skill folder, outside any package: put the repository
# root on the path and import the parsers the workflow itself uses, so the
# record and review formats have one definition.
REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
metrics = importlib.import_module("automation.scripts.review_retest_metrics")
parse_record_markers = importlib.import_module("automation.scripts.regen_gate").parse_record_markers
LIBRARY_LANGUAGES: dict[str, str] = importlib.import_module("core.constants").LIBRARY_LANGUAGES


GATE_AUTHOR = "github-actions[bot]"
REVIEW_AUTHOR = "claude[bot]"
BRANCH_RE = re.compile(r"^implementation/(?P<spec>[a-z0-9][a-z0-9-]*)/(?P<lib>[a-z0-9]+)$")
WRITEBACK_BRANCH_RE = re.compile(r"^review-writeback/(?P<spec>[^/]+)/(?P<lib>[^/]+)/(?P<kept>\d+)$")
RUN_URL_RE = re.compile(r"/actions/runs/(\d+)")
COST_RE = re.compile(r'"total_cost_usd":\s*([0-9.]+)')
GCS_PUBLIC = "https://storage.googleapis.com/anyplot-images/plots"
VERDICT_LABELS = ("regen:improved", "regen:kept", "ai-approved", "ai-rejected")
PIPELINE_WORKFLOWS = (
    "daily-regen.yml",
    "bulk-generate.yml",
    "impl-generate.yml",
    "impl-review.yml",
    "impl-repair.yml",
    "impl-merge.yml",
)
CLAUDE_WORKFLOWS = ("impl-generate.yml", "impl-review.yml", "impl-repair.yml")

# A keep whose re-score sits this far below the stored score is a render look.
# Under the same judge (both reviews from one model family) a few points is
# already a real change; across families the Opus offset alone is about 9 on
# production keeps and 13 on the retest, so only a drop past that means a
# defect the old review missed.
BIG_DROP_SAME_JUDGE = 3
BIG_DROP_OTHER_JUDGE = 13
# A verdict-less regen PR younger than this is still in its review, not stuck.
PENDING_HOURS = 3
# Scores at or above the approval line should stay rare (owner, 2026-09-28).
HIGH_SCORE = 90
# At most this many renders get opened per week (owner, 2026-10-07): the
# suspicious rows first, by tier, then a random fill.
SAMPLE_CAP = 15
SUSPICION_TIERS: tuple[frozenset[str], ...] = (
    frozenset({"merge_pn_only"}),
    frozenset({"big_drop"}),
    frozenset({"merge_without_carrier", "unverified", "regen_json_invalid", "no_record"}),
    frozenset({"high_score"}),
)


# ---------------------------------------------------------------------------
# Pure helpers (unit-tested)
# ---------------------------------------------------------------------------


def parse_branch(head: str) -> tuple[str, str] | None:
    match = BRANCH_RE.match(head or "")
    return (match.group("spec"), match.group("lib")) if match else None


def render_urls(spec: str, lib: str) -> dict[str, str]:
    """The production renders: the new version after a merge, the live one after a keep."""
    base = f"{GCS_PUBLIC}/{spec}/{LIBRARY_LANGUAGES.get(lib, 'python')}/{lib}"
    return {"light": f"{base}/plot-light.png", "dark": f"{base}/plot-dark.png"}


def gate_record(comments: Sequence[dict[str, Any]]) -> tuple[dict[str, Any] | None, int | None]:
    """The first gate record the workflow posted, and the review run its comment links.

    Only the workflow's own comments count: anyone can paste a marker. The
    verdict step runs once per PR, so there is one record; the first wins, as
    in ``review_retest.gh_gate_records``.
    """
    for comment in sorted(comments, key=lambda c: str(c.get("at") or "")):
        if comment.get("login") != GATE_AUTHOR:
            continue
        body = str(comment.get("body") or "")
        records = parse_record_markers(body)
        if records:
            run = RUN_URL_RE.search(body)
            return records[0], int(run.group(1)) if run else None
    return None, None


def last_review(comments: Sequence[dict[str, Any]]) -> dict[str, Any] | None:
    """The last parsed AI review comment by the reviewer (a retried review posts twice)."""
    reviews = [
        review
        for comment in sorted(comments, key=lambda c: str(c.get("at") or ""))
        if comment.get("login") == REVIEW_AUTHOR
        for review in [metrics.parse_review_comment(str(comment.get("body") or ""))]
        if review is not None
    ]
    return reviews[-1] if reviews else None


def category_vector(checklist: dict[str, dict[str, int]]) -> str:
    """``VQ 28 · DE 12 · …``: the category sums, in rubric order."""
    sums: dict[str, int] = {}
    for cid in metrics.CRITERIA_IDS:
        item = checklist.get(cid)
        if item is not None:
            sums[cid[:2]] = sums.get(cid[:2], 0) + int(item["score"])
    return " · ".join(f"{cat} {total}" for cat, total in sums.items())


def build_row(
    pull: dict[str, Any],
    comments: Sequence[dict[str, Any]],
    writeback: dict[str, Any] | None,
    artifacts: Sequence[dict[str, Any]],
    now: datetime | None = None,
) -> dict[str, Any]:
    """One regeneration with its flags. ``pull`` is a ``gh pr list`` entry."""
    spec, lib = parse_branch(str(pull.get("headRefName") or "")) or ("?", "?")
    labels = sorted(str((label or {}).get("name") or "") for label in pull.get("labels") or [])
    record, review_run = gate_record(comments)
    review = last_review(comments)
    improvements = (record or {}).get("improvements") or {}
    row: dict[str, Any] = {
        "pr": int(pull["number"]),
        "spec": spec,
        "lib": lib,
        "created": str(pull.get("createdAt") or ""),
        "state": str(pull.get("state") or ""),
        "labels": labels,
        "forced": "regen:forced" in labels,
        "verdict": (record or {}).get("verdict"),
        "code": (record or {}).get("code"),
        "prev_stored": (record or {}).get("prev_stored"),
        "prev_rescored": (record or {}).get("prev_rescored"),
        "new": (record or {}).get("new") if record else (review or {}).get("score"),
        "carriers": improvements.get("carriers"),
        "carriers_pn": improvements.get("carriers_pn"),
        "code_fixes": improvements.get("code"),
        "suggestions": improvements.get("suggestion"),
        "unverified": improvements.get("unverified"),
        "by_kind": improvements.get("by_kind"),
        "regressions": (record or {}).get("regressions"),
        "writeback": (record or {}).get("writeback"),
        "writeback_pr": writeback,
        "model": (record or {}).get("model"),
        "prev_model": (record or {}).get("prev_model"),
        "review_run": review_run,
        "pair_artifacts": [a["name"] for a in artifacts if str(a.get("name", "")).startswith("regen-pair-")],
        "pair_expired": any(a.get("expired") for a in artifacts if str(a.get("name", "")).startswith("regen-pair-")),
        "renders": render_urls(spec, lib),
        "checklist": (review or {}).get("checklist"),
        "categories": category_vector(review["checklist"]) if review else None,
        "silent": metrics.silent_deductions(review["checklist"], review["weaknesses"])[0] if review else [],
    }
    row["flags"] = row_flags(row, now or datetime.now(timezone.utc))
    return row


def model_family(model: Any) -> str | None:
    """``opus`` for ``claude-opus-5``; ``None`` when the record names no model."""
    match = re.match(r"^claude-([a-z]+)", str(model or ""))
    return match.group(1) if match else None


def big_drop_limit(row: dict[str, Any]) -> int:
    family = model_family(row["model"])
    same_judge = family is not None and family == model_family(row["prev_model"])
    return BIG_DROP_SAME_JUDGE if same_judge else BIG_DROP_OTHER_JUDGE


def _age_hours(created: str, now: datetime) -> float:
    try:
        then = datetime.strptime(created, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
    except ValueError:
        return float("inf")
    return (now - then).total_seconds() / 3600


def row_flags(row: dict[str, Any], now: datetime) -> list[str]:
    """What the weekly review looks at for this row; the SKILL explains each flag."""
    flags = []
    labels = set(row["labels"])
    if row["verdict"] is None:
        if row["forced"]:
            pass  # a forced regeneration takes the first-generation path and writes no record
        elif row["state"] == "OPEN" and _age_hours(row["created"], now) < PENDING_HOURS:
            flags.append("pending")
        elif row["state"] == "OPEN" or not labels & set(VERDICT_LABELS):
            flags.append("stuck")
        else:
            flags.append("no_record")
    if "ai-review-failed" in labels:
        flags.append("review_failed")
    # A record from before P3 has no carrier count at all; that is not a zero.
    if row["verdict"] == "merge" and row["carriers"] == 0 and not (row["code_fixes"] or 0):
        flags.append("merge_without_carrier")
    if row["verdict"] == "merge" and row["carriers"] and row["carriers_pn"] == row["carriers"]:
        flags.append("merge_pn_only")
    if row["code"] == "regen_json_invalid":
        flags.append("regen_json_invalid")
    if row["unverified"]:
        flags.append("unverified")
    if row["silent"]:
        flags.append("silent")
    if row["verdict"] == "keep":
        wb = row["writeback_pr"]
        # no_rescore follows from a gate failure the reason code already shows.
        if row["writeback"] not in (None, "opened", "unchanged", "no_rescore"):
            flags.append(f"writeback_{row['writeback']}")
        elif row["writeback"] == "opened" and not (wb and wb.get("merged")):
            flags.append("writeback_stranded")
        stored, rescored = row["prev_stored"], row["prev_rescored"]
        if isinstance(stored, int) and isinstance(rescored, int) and stored - rescored > big_drop_limit(row):
            flags.append("big_drop")
    if isinstance(row["new"], int) and row["new"] >= HIGH_SCORE:
        flags.append("high_score")
    if row["verdict"] and not row["pair_artifacts"]:
        flags.append("no_pair_artifact")
    return flags


def identical_vectors(rows: Sequence[dict[str, Any]]) -> list[dict[str, Any]]:
    """Libraries of one spec whose 24-item review vectors are identical (anchoring red flag)."""
    groups: dict[tuple[str, str], list[str]] = defaultdict(list)
    for row in rows:
        if row["checklist"]:
            key = json.dumps({k: row["checklist"][k]["score"] for k in sorted(row["checklist"])})
            groups[(row["spec"], key)].append(row["lib"])
    return [{"spec": spec, "libs": sorted(libs)} for (spec, _), libs in sorted(groups.items()) if len(libs) > 1]


def suspicion_rank(row: dict[str, Any]) -> int | None:
    """Where a row stands in the render queue (0 first); ``None`` when nothing is suspicious.

    The owner's order (2026-10-07): merges carried only by P or new defects,
    keeps whose re-score dropped past the family threshold, then gate oddities
    (no carrier, an unverified claim, an invalid regen JSON, a decided PR
    without a record). A score of 90 or more comes last: rare by design, so
    worth a look, but not a sign that something went wrong.
    """
    flags = set(row["flags"])
    for rank, tier in enumerate(SUSPICION_TIERS):
        if flags & tier:
            return rank
    return None


def render_sample(rows: Sequence[dict[str, Any]], seed: str) -> tuple[list[int], list[int]]:
    """The pull requests whose renders get opened, and the suspicious ones left over.

    At most ``SAMPLE_CAP``: every suspicious row in ``suspicion_rank`` order
    (ties by PR number), then a seeded random fill from the other decided rows.
    When more than ``SAMPLE_CAP`` rows are suspicious, the rest come back as the
    second list, for the report's "not opened" line.
    """
    ranked = sorted(((rank, r["pr"]) for r in rows if (rank := suspicion_rank(r)) is not None))
    suspicious = [pr for _, pr in ranked]
    sample, not_opened = suspicious[:SAMPLE_CAP], suspicious[SAMPLE_CAP:]
    rest = sorted(r["pr"] for r in rows if r["verdict"] and r["pr"] not in set(suspicious))
    fill = random.Random(seed).sample(rest, min(SAMPLE_CAP - len(sample), len(rest)))
    return sorted(sample + fill), sorted(not_opened)


def previously_reported(rows: Sequence[dict[str, Any]]) -> set[int]:
    """PRs last week's report already settled: everything but the ones still open.

    A forced regeneration never has a gate verdict, so the PR state, not the
    verdict, says whether it is done.
    """
    return {int(r["pr"]) for r in rows if r.get("state") != "OPEN"}


def summarize(rows: Sequence[dict[str, Any]], runs: dict[str, Counter], cost: float | None) -> dict[str, Any]:
    decided = [r for r in rows if r["verdict"]]
    merges = [r for r in decided if r["verdict"] == "merge"]
    keeps = [r for r in decided if r["verdict"] == "keep"]
    scores = [r["new"] for r in decided if isinstance(r["new"], int)]
    drift = [
        r["prev_rescored"] - r["prev_stored"]
        for r in decided
        if isinstance(r["prev_rescored"], int) and isinstance(r["prev_stored"], int)
    ]
    flag_counts = Counter(f for r in rows for f in r["flags"])
    return {
        "regen_prs": len(rows),
        "specs": len({r["spec"] for r in rows}),
        "decisions": len(decided),
        "merges": len(merges),
        "keeps": len(keeps),
        "merge_rate": round(len(merges) / len(decided), 3) if decided else None,
        "codes": dict(Counter(str(r["code"]) for r in decided).most_common()),
        "score_mean": round(statistics.fmean(scores), 1) if scores else None,
        "score_sd": round(statistics.stdev(scores), 1) if len(scores) > 1 else None,
        "score_histogram": dict(sorted(Counter(scores).items())),
        "at_or_above_90": sum(1 for s in scores if s >= HIGH_SCORE),
        "rescore_drift_mean": round(statistics.fmean(drift), 1) if drift else None,
        "flags": dict(sorted(flag_counts.items())),
        "identical_vectors": identical_vectors(rows),
        "runs": {wf: dict(counter) for wf, counter in runs.items()},
        "cost_usd": round(cost, 2) if cost is not None else None,
    }


METRIC_ROWS: tuple[tuple[str, str, Callable[[dict[str, Any]], Any]], ...] = (
    ("Regen PRs (specs)", "", lambda s: f"{s['regen_prs']} ({s['specs']})"),
    ("Decisions", "", lambda s: s["decisions"]),
    ("Merge rate", "5–50 %", lambda s: "–" if s["merge_rate"] is None else f"{s['merge_rate'] * 100:.0f} %"),
    ("Merges without a carrier", "0", lambda s: s["flags"].get("merge_without_carrier", 0)),
    ("Merges carried only by P/new", "read each", lambda s: s["flags"].get("merge_pn_only", 0)),
    ("regen_json_invalid", "0", lambda s: s["flags"].get("regen_json_invalid", 0)),
    ("Unverified claims", "0", lambda s: s["flags"].get("unverified", 0)),
    ("Reviews with silent deductions", "0", lambda s: s["flags"].get("silent", 0)),
    ("Write-back not merged", "0", lambda s: sum(v for k, v in s["flags"].items() if k.startswith("writeback_"))),
    (
        "Keeps re-scored far below stored (> 3 same judge, > 13 across models)",
        "read each",
        lambda s: s["flags"].get("big_drop", 0),
    ),
    ("New score mean (SD)", "≈ 80–88", lambda s: f"{_cell(s['score_mean'])} ({_cell(s['score_sd'])})"),
    ("Scores ≥ 90", "rare", lambda s: s["at_or_above_90"]),
    ("Re-score − stored, mean", "≈ −9 (Opus offset)", lambda s: _cell(s["rescore_drift_mean"])),
    ("Identical review vectors in a spec", "0", lambda s: len(s["identical_vectors"])),
    ("Stuck or failed review PRs", "0", lambda s: s["flags"].get("stuck", 0) + s["flags"].get("review_failed", 0)),
    ("Reviews still running", "–", lambda s: s["flags"].get("pending", 0)),
    ("Missing pair artifact", "0", lambda s: s["flags"].get("no_pair_artifact", 0)),
    ("daily-regen runs (success/all)", "7/7", lambda s: _success(s["runs"].get("daily-regen.yml", {}))),
    ("Failed pipeline runs", "few", lambda s: sum(c.get("failure", 0) for c in s["runs"].values())),
    ("Session cost (USD)", "", lambda s: "not collected" if s["cost_usd"] is None else f"${s['cost_usd']:.0f}"),
)


def _cell(value: Any) -> str:
    """A record key that older records lack (pre-P3.1 kinds, pre-P8 code) reads as a dash."""
    return "–" if value is None else str(value)


def _success(counter: dict[str, int]) -> str:
    return f"{counter.get('success', 0)}/{sum(counter.values())}"


def render_markdown(
    summary: dict[str, Any],
    rows: Sequence[dict[str, Any]],
    sample: Sequence[int],
    previous: dict[str, Any] | None,
    failed_runs: dict[str, list[dict[str, Any]]] | None = None,
    not_opened: Sequence[int] = (),
) -> str:
    head = "| Metric | Target | This week |" + (" Last week |" if previous else "")
    rule = "|---|---|---|" + ("---|" if previous else "")
    lines = ["## Metrics", "", head, rule]
    for name, target, value in METRIC_ROWS:
        cells = [name, target or "–", str(value(summary))]
        if previous:
            try:
                cells.append(str(value(previous)))
            except (KeyError, TypeError):
                cells.append("–")
        lines.append("| " + " | ".join(cells) + " |")
    lines += ["", f"Reason codes: {', '.join(f'{k} {v}' for k, v in summary['codes'].items()) or 'none'}", ""]
    if summary["identical_vectors"]:
        lines += ["Identical review vectors:", ""]
        lines += [f"- {g['spec']}: {', '.join(g['libs'])}" for g in summary["identical_vectors"]]
        lines.append("")
    failed = [(wf, run) for wf, listed in (failed_runs or {}).items() for run in listed]
    if failed:
        lines += ["Failed pipeline runs:", ""]
        lines += [f"- {wf} {run['id']} {run['at']}: {run['title']}" for wf, run in failed]
        lines.append("")
    lines += [
        "## Regenerations",
        "",
        "| PR | Spec / library | Verdict (code) | Stored → re-scored → new | Carriers (P/new, code) | Flags |",
        "|---|---|---|---|---|---|",
    ]
    for r in sorted(rows, key=lambda r: (r["spec"], r["lib"])):
        verdict = f"{r['verdict']} ({r['code']})" if r["verdict"] else ("forced" if r["forced"] else "–")
        scores = " → ".join(_cell(r[k]) for k in ("prev_stored", "prev_rescored", "new"))
        carriers = (
            f"{_cell(r['carriers'])} ({_cell(r['carriers_pn'])}, {_cell(r['code_fixes'])})" if r["verdict"] else "–"
        )
        mark = " ◆" if r["pr"] in sample else ""
        flags = ", ".join(r["flags"]) or "–"
        lines.append(f"| #{r['pr']}{mark} | {r['spec']} / {r['lib']} | {verdict} | {scores} | {carriers} | {flags} |")
    lines += ["", f"◆ = in the render sample (at most {SAMPLE_CAP}; open both renders from the pair artifact).", ""]
    if not_opened:
        lines += [f"Suspicious but not opened (over the cap): {', '.join(f'#{pr}' for pr in not_opened)}", ""]
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# GitHub I/O (read-only)
# ---------------------------------------------------------------------------


def _gh(args: Sequence[str]) -> str:
    return subprocess.run(["gh", *args], check=True, capture_output=True, text=True).stdout


def _gh_json(args: Sequence[str]) -> Any:
    return json.loads(_gh(args) or "null")


def regen_pulls(since: str, limit: int) -> list[dict[str, Any]]:
    """Gated regenerations (``regen``) and forced ones (``regen:forced`` only), by number."""
    pulls: dict[int, dict[str, Any]] = {}
    for label in ("regen", "regen:forced"):
        listed = _gh_json(
            [
                "pr",
                "list",
                "--state",
                "all",
                "--label",
                label,
                "--search",
                f"created:>={since}",
                "--limit",
                str(limit),
                "--json",
                "number,headRefName,labels,state,createdAt",
            ]
        )
        if len(listed or []) >= limit:
            print(f"::warning::the {label} listing stopped at --limit {limit}; raise it", file=sys.stderr)
        pulls.update({int(p["number"]): p for p in listed or []})
    return [pulls[n] for n in sorted(pulls)]


def writeback_pulls(since: str) -> dict[int, dict[str, Any]]:
    """Write-back pull requests by the kept pull request they belong to."""
    listed = _gh_json(
        [
            "pr",
            "list",
            "--state",
            "all",
            "--label",
            "review-writeback",
            "--search",
            f"created:>={since}",
            "--limit",
            "500",
            "--json",
            "number,headRefName,state,mergedAt",
        ]
    )
    return map_writebacks(listed or [])


def map_writebacks(listed: Sequence[dict[str, Any]]) -> dict[int, dict[str, Any]]:
    """The write-back of each kept PR; a merged one wins over a closed earlier attempt."""
    out: dict[int, dict[str, Any]] = {}
    for pull in sorted(listed, key=lambda p: int(p["number"])):
        match = WRITEBACK_BRANCH_RE.match(str(pull.get("headRefName") or ""))
        if not match:
            continue
        kept = int(match.group("kept"))
        if out.get(kept, {}).get("merged"):
            continue
        out[kept] = {"number": int(pull["number"]), "state": pull.get("state"), "merged": bool(pull.get("mergedAt"))}
    return out


def pull_comments(number: int) -> list[dict[str, Any]]:
    out = _gh(
        [
            "api",
            "--paginate",
            f"repos/{{owner}}/{{repo}}/issues/{number}/comments",
            "--jq",
            ".[] | {body, at: .created_at, login: .user.login} | @json",
        ]
    )
    return [json.loads(line) for line in out.splitlines() if line.strip()]


def run_artifacts(run_id: int | None) -> list[dict[str, Any]]:
    if not run_id:
        return []
    out = _gh(["api", f"repos/{{owner}}/{{repo}}/actions/runs/{run_id}/artifacts", "--jq", ".artifacts[] | @json"])
    return [json.loads(line) for line in out.splitlines() if line.strip()]


def pipeline_runs(since: str) -> dict[str, list[dict[str, Any]]]:
    runs = {}
    for workflow in PIPELINE_WORKFLOWS:
        runs[workflow] = (
            _gh_json(
                [
                    "run",
                    "list",
                    "--workflow",
                    workflow,
                    "--created",
                    f">={since}",
                    "--limit",
                    "1000",
                    "--json",
                    "databaseId,conclusion,status,displayTitle,createdAt",
                ]
            )
            or []
        )
    return runs


def session_cost(runs: dict[str, list[dict[str, Any]]]) -> float:
    """Sum of ``total_cost_usd`` over every job log of the Claude-running workflows."""
    total = 0.0
    for workflow in CLAUDE_WORKFLOWS:
        for run in runs.get(workflow, []):
            jobs = _gh_json(["api", f"repos/{{owner}}/{{repo}}/actions/runs/{run['databaseId']}/jobs"]) or {}
            for job in jobs.get("jobs", []):
                try:
                    log = _gh(["api", f"repos/{{owner}}/{{repo}}/actions/jobs/{job['id']}/logs"])
                except subprocess.CalledProcessError:
                    continue  # an expired or missing log costs nothing to skip
                total += sum(float(m) for m in COST_RE.findall(log))
    return total


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--since", required=True, help="ISO date, pull requests created on or after it")
    parser.add_argument("--out", required=True, help="JSON output path (rows and summary)")
    parser.add_argument("--previous", default="", help="last week's JSON, for the comparison column")
    parser.add_argument("--costs", action="store_true", help="sum session cost from job logs (slow)")
    parser.add_argument("--limit", type=int, default=500)
    args = parser.parse_args(argv)

    # The window starts on the previous report's date, so the day it was written
    # is covered twice: PRs that report already decided, and runs created before
    # it was collected, are left out here. A PR that was still open comes back.
    previous_payload: dict[str, Any] = {}
    if args.previous:
        if not Path(args.previous).is_file():
            parser.error(f"--previous {args.previous} does not exist")
        previous_payload = json.loads(Path(args.previous).read_text(encoding="utf-8"))
    reported = previously_reported(previous_payload.get("rows", []))
    cutoff = str(previous_payload.get("collected_at") or "")

    writebacks = writeback_pulls(args.since)
    rows = []
    for pull in regen_pulls(args.since, args.limit):
        if int(pull["number"]) in reported:
            continue
        comments = pull_comments(int(pull["number"]))
        _, review_run = gate_record(comments)
        rows.append(build_row(pull, comments, writebacks.get(int(pull["number"])), run_artifacts(review_run)))
    runs = {
        wf: [r for r in listed if str(r.get("createdAt") or "") > cutoff]
        for wf, listed in pipeline_runs(args.since).items()
    }
    run_counts = {
        wf: Counter(str(r.get("conclusion") or r.get("status")) for r in listed) for wf, listed in runs.items()
    }
    failures = {
        wf: [
            {"id": r["databaseId"], "title": r["displayTitle"], "at": r["createdAt"]}
            for r in listed
            if r.get("conclusion") == "failure"
        ]
        for wf, listed in runs.items()
    }
    summary = summarize(rows, run_counts, session_cost(runs) if args.costs else None)
    sample, not_opened = render_sample(rows, seed=args.since)
    previous = previous_payload.get("summary")
    payload = {
        "since": args.since,
        "collected_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "summary": summary,
        "sample": sample,
        "not_opened": not_opened,
        "failed_runs": failures,
        "rows": rows,
    }
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(render_markdown(summary, rows, sample, previous, failures, not_opened))
    return 0


if __name__ == "__main__":
    sys.exit(main())
