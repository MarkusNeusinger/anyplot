"""Write a triage round's status, tags and promotions to `agent_feedback`, after a snapshot; a dry run by default.

Run it from the repository root (in a worktree, name the main checkout's `.env` as `$ENV`, see SKILL.md):

    uv run python .claude/skills/triage-agent-cases/apply_triage.py --env "$ENV" --plan "$ROUND/plan.json"
    uv run python .claude/skills/triage-agent-cases/apply_triage.py --env "$ENV" --plan "$ROUND/plan.json" --apply

The plan is JSON (see SKILL.md, "The plan file"):

    {"round": "2026-11-04", "cases": [
      {"id": "20261012T143005Z-1a2b3c4d", "seen": {"status": "new", "tags": []},
       "status": "in_progress", "tags": ["legend-overlap"], "why": "one line; never written"}]}

`seen` is the row's status and tags as the round read them. A row that differs now (someone
triaged it on /debug since) is refused, so a write never overwrites a newer decision.
`status`, `tags`, `promoted` and `expected` mean what they mean in `PATCH /debug/agent/cases/{id}`
and go through the same rules (`core.agent_cases.triage_updates`); an absent or null field
stays as it is.

The dry run reads the rows in one read-only transaction and prints old -> new per row. With
`--apply`, ONE transaction locks the rows (`SELECT ... FOR UPDATE`), checks them again, writes
them all to a new `<backup root>/<UTC time>-agent-feedback-triage/rows.json` (never into an
existing directory; the file is read back and its rows counted), sets the changes and
commits. A refusal or an error before the commit changes nothing.

Exit codes: 0 done, or a dry run without refusals; 1 a refusal (a row missing, changed since
the plan, or refused by a rule); 2 bad arguments, an unreadable plan, or no `DATABASE_URL`.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import re
import sys
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any

import casedb


if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

    from core.database import AgentFeedback


DEFAULT_BACKUP_ROOT = Path.home() / "anyplot-backups"
SNAPSHOT_SUFFIX = "agent-feedback-triage"
PLAN_KEYS = frozenset({"round", "cases"})
CASE_KEYS = frozenset({"id", "seen", "status", "tags", "promoted", "expected", "why"})
FIELDS = ("status", "tags", "promoted", "expected")
"""The edit's fields, as the PATCH body names them."""
SHOWN = ("status", "tags", "expected", "promoted_at")
"""The columns an edit can change, in the order the diff prints them."""


class PlanError(ValueError):
    """A plan file that is not in the format above; the message names the entry."""


class SnapshotError(RuntimeError):
    """The snapshot file did not read back with the rows it was written with."""


@dataclass(frozen=True)
class Change:
    """One plan entry: the row's state the round saw, and the edit."""

    id: str
    seen_status: str
    seen_tags: tuple[str, ...]
    edit: dict[str, Any]


@dataclass(frozen=True)
class Planned:
    """A checked change: the locked row and the columns it gets."""

    row: AgentFeedback
    updates: dict[str, Any]


def load_plan(data: Any) -> list[Change]:
    """The plan's changes, in file order; raises PlanError on anything but the documented format."""
    from core.agent_cases import CASE_ID_PATTERN

    if not isinstance(data, dict) or not isinstance(data.get("cases"), list) or not data["cases"]:
        raise PlanError('the plan is not an object with a non-empty "cases" list')
    if extra := sorted(set(data) - PLAN_KEYS):
        raise PlanError(f"unknown plan keys {extra}")
    changes: list[Change] = []
    for number, entry in enumerate(data["cases"], start=1):
        where = f"case {number}"
        if not isinstance(entry, dict):
            raise PlanError(f"{where} is not an object")
        case_id = entry.get("id")
        if not isinstance(case_id, str) or not re.fullmatch(CASE_ID_PATTERN, case_id):
            raise PlanError(f"{where}: id is not a case id")
        where = f"case {case_id}"
        if extra := sorted(set(entry) - CASE_KEYS):
            raise PlanError(f"{where}: unknown keys {extra}")
        seen = entry.get("seen")
        if (
            not isinstance(seen, dict)
            or set(seen) != {"status", "tags"}
            or not isinstance(seen["status"], str)
            or not isinstance(seen["tags"], list)
            or not all(isinstance(tag, str) for tag in seen["tags"])
        ):
            raise PlanError(f'{where}: "seen" is not {{"status": str, "tags": [str, ...]}}')
        edit = {field: entry[field] for field in FIELDS if entry.get(field) is not None}
        if not edit:
            raise PlanError(f"{where}: names none of {', '.join(FIELDS)}")
        if "tags" in edit and not isinstance(edit["tags"], list):
            raise PlanError(f"{where}: tags is not a list")
        if "promoted" in edit and not isinstance(edit["promoted"], bool):
            raise PlanError(f"{where}: promoted is not true or false")
        if any(change.id == case_id for change in changes):
            raise PlanError(f"{where} appears twice")
        changes.append(Change(case_id, seen["status"], tuple(seen["tags"]), edit))
    return changes


def check(rows: dict[str, AgentFeedback], changes: list[Change], now: datetime) -> tuple[list[Planned], list[str]]:
    """The planned updates, and one refusal line per change the table or the rules refuse."""
    from core.agent_cases import TriageRefused, triage_updates

    planned: list[Planned] = []
    refusals: list[str] = []
    for change in changes:
        row = rows.get(change.id)
        if row is None:
            refusals.append(f"{change.id}  refused: no row with this id")
            continue
        if row.status != change.seen_status or sorted(row.tags) != sorted(change.seen_tags):
            refusals.append(
                f"{change.id}  refused: changed since the plan (now {row.status} {sorted(row.tags)}, "
                f"the plan saw {change.seen_status} {sorted(change.seen_tags)}); list the cases again"
            )
            continue
        try:
            planned.append(Planned(row, triage_updates(row, now=now, **change.edit)))
        except TriageRefused as exc:
            refusals.append(f"{change.id}  refused: {exc.code}: {exc}")
    return planned, refusals


def _shown(value: Any) -> str:
    if value is None:
        return "-"
    if isinstance(value, datetime):
        return value.strftime("%Y-%m-%dT%H:%M:%SZ")
    if isinstance(value, list):
        return "[" + ", ".join(value) + "]"
    return str(value)


def diff(item: Planned) -> list[str]:
    """`status new -> in_progress`, one entry per column whose value the update changes."""
    parts = []
    for column in SHOWN:
        if column not in item.updates:
            continue
        old, new = getattr(item.row, column), item.updates[column]
        if (sorted(old) if column == "tags" else old) != new:
            parts.append(f"{column} {_shown(old)} -> {_shown(new)}")
    return parts


def describe(item: Planned) -> str:
    """`<id>  status new -> in_progress; tags [] -> [a, b]`, or `<id>  no change`."""
    return f"{item.row.id}  " + ("; ".join(diff(item)) or "no change")


def write_snapshot(root: Path, rows: list[AgentFeedback], plan: Any, now: datetime) -> Path:
    """Write `rows` and the plan to a new `<root>/<now>-agent-feedback-triage/`, read the rows back, return the directory.

    The directory must not exist (FileExistsError otherwise: a snapshot is never overwritten);
    it, its files and the root are private (0700 and 0600), because the rows hold users' messages;
    a root that exists already is tightened too.
    """
    root.mkdir(mode=0o700, parents=True, exist_ok=True)
    root.chmod(0o700)
    directory = root / f"{now:%Y%m%dT%H%M%SZ}-{SNAPSHOT_SUFFIX}"
    directory.mkdir(mode=0o700)
    payload = {"table": "agent_feedback", "taken_at": _shown(now), "count": len(rows)}
    payload["rows"] = [casedb.row_json(row) for row in rows]
    for name, content in (("rows.json", payload), ("plan.json", plan)):
        descriptor = os.open(directory / name, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            json.dump(content, handle, indent=2, ensure_ascii=False)
            handle.write("\n")
    back = json.loads((directory / "rows.json").read_text(encoding="utf-8"))
    if back.get("count") != len(rows) or sorted(r["id"] for r in back.get("rows", [])) != sorted(r.id for r in rows):
        raise SnapshotError(f"{directory / 'rows.json'} does not hold the {len(rows)} rows it was written with")
    return directory


async def run(
    session: AsyncSession, changes: list[Change], plan: Any, *, apply: bool, backup_root: Path, now: datetime
) -> tuple[list[str], int]:
    """Check the plan against the table and, with `apply`, snapshot and write it in this one transaction."""
    from sqlalchemy import select

    from core.database import AgentFeedback
    from core.database.repositories import AGENT_FEEDBACK_UPDATABLE_FIELDS

    if not apply:
        await casedb.read_only(session)
    statement = select(AgentFeedback).where(AgentFeedback.id.in_([change.id for change in changes]))
    if apply:
        statement = statement.with_for_update()
    rows = {row.id: row for row in (await session.execute(statement)).scalars()}
    planned, refusals = check(rows, changes, now)
    lines = [describe(item) for item in planned] + refusals
    changing = [item for item in planned if diff(item)]
    if refusals:
        await session.rollback()
        return [*lines, f"refused {len(refusals)} of {len(changes)}; nothing written"], 1
    if not apply:
        await session.rollback()
        return [*lines, f"dry run: would change {len(changing)} of {len(changes)} row(s); --apply writes them"], 0
    if not changing:
        await session.rollback()
        return [*lines, "nothing to change; no snapshot taken"], 0
    snapshot = write_snapshot(backup_root, [item.row for item in planned], plan, now)
    for item in changing:
        for column, value in item.updates.items():
            if column not in AGENT_FEEDBACK_UPDATABLE_FIELDS:
                raise RuntimeError(f"{column} is not a triage column")
            setattr(item.row, column, value)
    await session.commit()
    return [*lines, f"snapshot {snapshot / 'rows.json'} ({len(planned)} rows)", f"changed {len(changing)} row(s)"], 0


async def _main(changes: list[Change], plan: Any, args: argparse.Namespace) -> int:
    from core.database import close_db, get_db_context

    now = datetime.now(UTC).replace(tzinfo=None)
    try:
        async with get_db_context() as session:
            lines, code = await run(session, changes, plan, apply=args.apply, backup_root=args.backup_root, now=now)
    finally:
        await close_db()
    print("\n".join(lines))
    return code


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Write a triage round's plan to agent_feedback (a dry run by default)."
    )
    parser.add_argument("--plan", type=Path, required=True, help="the round's plan.json")
    parser.add_argument("--apply", action="store_true", help="snapshot the rows, then write the plan")
    parser.add_argument("--backup-root", type=Path, default=DEFAULT_BACKUP_ROOT, help="where the snapshot goes")
    parser.add_argument("--env", type=Path, default=casedb.DEFAULT_ENV_FILE, help="the .env to read DATABASE_URL from")
    args = parser.parse_args(argv)
    if not casedb.outside_repository(args.backup_root):
        print(
            f"apply_triage: {args.backup_root} is inside a git checkout; a snapshot holds users' messages",
            file=sys.stderr,
        )
        return 2
    # Before `load_plan`: its `core` import makes `core.database` read DATABASE_URL.
    if not casedb.use_database_url(args.env):
        print(f"apply_triage: DATABASE_URL is not set and {args.env} does not define it", file=sys.stderr)
        return 2
    try:
        plan = json.loads(args.plan.read_text(encoding="utf-8"))
        changes = load_plan(plan)
    except (OSError, ValueError) as exc:  # PlanError, or a file that is missing or not JSON
        print(f"apply_triage: {args.plan}: {exc}", file=sys.stderr)
        return 2
    return asyncio.run(_main(changes, plan, args))


if __name__ == "__main__":
    raise SystemExit(main())
