"""List the agent chat's feedback cases for a triage round; read-only on the `agent_feedback` table.

Run it from the repository root (in a worktree, name the main checkout's `.env` as `$ENV`, see SKILL.md):

    uv run python .claude/skills/triage-agent-cases/list_cases.py --env "$ENV" --json "$ROUND/cases.json"
    uv run python .claude/skills/triage-agent-cases/list_cases.py --all

By default it lists the open queue as `/debug` shows it: status `new` or `in_progress`, not
superseded. `--all` lists every row. It prints one line per case, oldest first, and with
`--json` writes every column of those rows to that file (mode 0600). The file holds the
users' messages, so it must lie outside any git checkout. The query runs in a transaction
that PostgreSQL itself holds read-only.

Exit codes: 0 listed, 2 bad arguments or no `DATABASE_URL`.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING

import casedb


if TYPE_CHECKING:
    from core.database import AgentFeedback


MESSAGE_PREVIEW = 48
"""Characters of the user's message in the table; the JSON holds all of it."""


def is_listed(row: AgentFeedback, *, everything: bool) -> bool:
    """In the open queue (`new` or `in_progress`, not superseded), or any row with `everything`."""
    return everything or (row.status in casedb.OPEN_STATUSES and row.superseded_by is None)


def _cell(text: str | None, width: int) -> str:
    flat = " ".join((text or "").split())
    return flat if len(flat) <= width else flat[: width - 1] + "…"


def table(rows: list[AgentFeedback]) -> str:
    """One line per row: id, reaction, status, spec and library, version, data, flags, tags, message."""
    lines = [
        f"{'case id':<25}  {'reaction':<11}  {'status':<11}  {'spec / library':<34}  {'v':>3}  data  flags  tags | message"
    ]
    for row in rows:
        where = f"{row.spec_id or '-'} / {row.library_id or '-'}"
        flags = ("S" if row.superseded_by else "-") + ("P" if row.promoted_at else "-") + ("E" if row.expected else "-")
        tags = ",".join(row.tags) or "-"
        lines.append(
            f"{row.id:<25}  {row.reaction:<11}  {row.status:<11}  {_cell(where, 34):<34}  {row.result_version:>3}  "
            f"{'yes' if row.include_data else 'no':<4}  {flags:<5}  {tags} | {_cell(row.message, MESSAGE_PREVIEW)}"
        )
    lines.append(f"{len(rows)} case(s); flags: S superseded, P promoted, E expected outcome set")
    return "\n".join(lines)


async def read_rows(*, everything: bool) -> list[AgentFeedback]:
    """The listed rows, oldest first, from one read-only transaction; the engine is disposed afterwards."""
    from core.database import AgentFeedbackRepository, close_db, get_db_context

    try:
        async with get_db_context() as session:
            await casedb.read_only(session)
            rows = await AgentFeedbackRepository(session).list_all()
    finally:
        await close_db()
    return [row for row in rows if is_listed(row, everything=everything)]


def write_json(path: Path, rows: list[AgentFeedback], *, everything: bool) -> None:
    payload = {
        "listed_at": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "filter": "all" if everything else "open",
        "cases": [casedb.row_json(row) for row in rows],
    }
    path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, ensure_ascii=False)
        handle.write("\n")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="List the agent chat's feedback cases, read-only.")
    parser.add_argument("--all", action="store_true", help="every row, not only the open queue")
    parser.add_argument("--json", type=Path, help="also write the rows' columns to this file (outside any checkout)")
    parser.add_argument("--env", type=Path, default=casedb.DEFAULT_ENV_FILE, help="the .env to read DATABASE_URL from")
    args = parser.parse_args(argv)
    if args.json is not None and not casedb.outside_repository(args.json):
        print(f"list_cases: {args.json} is inside a git checkout; the rows hold users' messages", file=sys.stderr)
        return 2
    if not casedb.use_database_url(args.env):
        print(f"list_cases: DATABASE_URL is not set and {args.env} does not define it", file=sys.stderr)
        return 2
    rows = asyncio.run(read_rows(everything=args.all))
    print(table(rows))
    if args.json is not None:
        write_json(args.json, rows, everything=args.all)
        print(f"wrote {args.json}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
