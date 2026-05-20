#!/usr/bin/env python3
# /// script
# requires-python = ">=3.13"
# dependencies = []
# ///
"""Aggregate canvas_gate ::notice:: log lines from recent impl-review runs.

Scans the GitHub Actions logs of recent `Impl: Review` workflow runs, parses the
structured `::notice::canvas_gate library=<lib> status=<pass|fail> actual=WxH
target=WxH delta=+dx+dy attempt=<n>` lines emitted by the gate step in
`.github/workflows/impl-review.yml`, and prints a per-library first-attempt
pass/fail-rate table.

The goal is to spot libraries whose **prompt** is leaking (high first-attempt
fail rate → wasted compute on repair) so we know when to tighten the library
prompt rather than accept gate firing as steady-state.

Usage:
    uv run automation/scripts/canvas_gate_report.py
    uv run automation/scripts/canvas_gate_report.py --limit 200
    uv run automation/scripts/canvas_gate_report.py --since 14d

Requires `gh` CLI on PATH and authentication for the current repo.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone


LINE_RE = re.compile(
    r"canvas_gate\s+library=(?P<lib>\S+)\s+status=(?P<status>pass|fail)\s+"
    r"actual=(?P<aw>\d+)x(?P<ah>\d+)\s+target=(?P<tw>\d+)x(?P<th>\d+)\s+"
    r"delta=(?P<dw>[+-]?\d+)x(?P<dh>[+-]?\d+)\s+attempt=(?P<attempt>\d+)"
)


@dataclass
class LibStats:
    runs: int = 0
    first_pass: int = 0
    first_fail: int = 0
    deltas: list[tuple[int, int]] = field(default_factory=list)

    @property
    def fail_rate(self) -> float:
        if not self.runs:
            return 0.0
        return self.first_fail / self.runs

    @property
    def avg_delta(self) -> tuple[float, float]:
        if not self.deltas:
            return (0.0, 0.0)
        n = len(self.deltas)
        return (sum(d[0] for d in self.deltas) / n, sum(d[1] for d in self.deltas) / n)


def parse_since(value: str) -> datetime:
    """Parse "14d" / "48h" / ISO date into a UTC cutoff."""
    now = datetime.now(timezone.utc)
    m = re.match(r"^(\d+)([dh])$", value)
    if m:
        n, unit = int(m.group(1)), m.group(2)
        delta = timedelta(days=n) if unit == "d" else timedelta(hours=n)
        return now - delta
    return datetime.fromisoformat(value).astimezone(timezone.utc)


def list_runs(limit: int, since: datetime) -> list[dict]:
    """Return recent `Impl: Review` runs as dicts (id, createdAt)."""
    cmd = [
        "gh",
        "run",
        "list",
        "--workflow",
        "impl-review.yml",
        "--limit",
        str(limit),
        "--json",
        "databaseId,createdAt,conclusion",
    ]
    raw = subprocess.check_output(cmd, text=True)
    runs = json.loads(raw)
    out = []
    for r in runs:
        created = datetime.fromisoformat(r["createdAt"].replace("Z", "+00:00"))
        if created < since:
            continue
        out.append({"id": r["databaseId"], "createdAt": created, "conclusion": r["conclusion"]})
    return out


def fetch_log_lines(run_id: int) -> list[str]:
    """Return canvas_gate notice lines from one run's log (may be empty)."""
    try:
        log = subprocess.check_output(["gh", "run", "view", str(run_id), "--log"], text=True, stderr=subprocess.DEVNULL)
    except subprocess.CalledProcessError:
        return []
    return [line for line in log.splitlines() if "canvas_gate" in line]


def parse_lines(lines: list[str]) -> list[dict]:
    """Extract structured records from raw log lines."""
    records = []
    for line in lines:
        m = LINE_RE.search(line)
        if not m:
            continue
        records.append(
            {
                "library": m.group("lib"),
                "status": m.group("status"),
                "actual": (int(m.group("aw")), int(m.group("ah"))),
                "target": (int(m.group("tw")), int(m.group("th"))),
                "delta": (int(m.group("dw")), int(m.group("dh"))),
                "attempt": int(m.group("attempt")),
            }
        )
    return records


def aggregate(records: list[dict]) -> dict[str, LibStats]:
    """Build per-library first-attempt stats. `attempt=1` is the first try."""
    stats: dict[str, LibStats] = defaultdict(LibStats)
    for r in records:
        if r["attempt"] != 1:
            continue  # we only care about first-attempt rate
        s = stats[r["library"]]
        s.runs += 1
        if r["status"] == "pass":
            s.first_pass += 1
        else:
            s.first_fail += 1
            s.deltas.append(r["delta"])
    return stats


def render_table(stats: dict[str, LibStats]) -> str:
    """Format the per-library report as an aligned text table."""
    if not stats:
        return "(no canvas_gate notice lines found in the scanned runs)"

    rows = []
    for lib in sorted(stats):
        s = stats[lib]
        adw, adh = s.avg_delta
        delta_col = "—" if s.first_fail == 0 else f"{adw:+.0f}×{adh:+.0f}"
        flag = "  ← prompt still leaking" if s.fail_rate > 0.20 else ""
        rows.append((lib, s.runs, s.first_pass, s.first_fail, f"{s.fail_rate * 100:5.1f}%", delta_col, flag))

    header = ("library", "runs", "first_pass", "first_fail", "fail_rate", "avg_delta", "")
    widths = [max(len(str(r[i])) for r in [header, *rows]) for i in range(len(header))]
    fmt = "  ".join(f"{{:<{w}}}" for w in widths)
    lines = [fmt.format(*header), fmt.format(*("-" * w for w in widths))]
    for r in rows:
        lines.append(fmt.format(*r))
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--limit", type=int, default=100, help="Max workflow runs to scan (default 100).")
    parser.add_argument("--since", default="14d", help="Cutoff window: '14d', '48h', or ISO date.")
    args = parser.parse_args()

    cutoff = parse_since(args.since)
    runs = list_runs(args.limit, cutoff)
    if not runs:
        print(f"(no impl-review runs found since {cutoff.isoformat()})")
        return 0

    all_records: list[dict] = []
    for run in runs:
        lines = fetch_log_lines(run["id"])
        all_records.extend(parse_lines(lines))

    stats = aggregate(all_records)
    print(
        f"# canvas_gate report — {len(runs)} run(s) scanned, {len(all_records)} canvas_gate line(s) since {cutoff.date()}\n"
    )
    print(render_table(stats))
    print()
    if any(s.fail_rate > 0.20 for s in stats.values()):
        print("Any library > 20 % first-attempt fail rate over 14 days warrants tightening that library's prompt.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
