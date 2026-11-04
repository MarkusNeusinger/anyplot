"""What the triage skill's two database scripts share: the database URL, a read-only transaction, a row as JSON.

`core` is imported only inside functions: `core.database` reads `DATABASE_URL` when it is
imported, and `use_database_url` sets it first (the pattern of `agents/evals/sync_cases.py`).
"""

from __future__ import annotations

import os
import sys
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any

from dotenv import dotenv_values


if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

    from core.database import AgentFeedback


REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

DEFAULT_ENV_FILE = REPO_ROOT / ".env"
"""This checkout's `.env`. A worktree has none: name the main checkout's with `--env` on purpose."""
OPEN_STATUSES = ("new", "in_progress")
"""The triage queue of `/debug`: the statuses that do not retire a case."""


def use_database_url(env_file: Path) -> bool:
    """Export `DATABASE_URL` from the shell, else from `env_file` (that key only); False when neither has it.

    The value is never printed. `ENVIRONMENT` is set to `script`, because `core.database`
    echoes every statement with its parameters under `development`, its default.
    """
    if not os.environ.get("DATABASE_URL"):
        url = dotenv_values(env_file).get("DATABASE_URL") if env_file.is_file() else None
        if not url:
            return False
        os.environ["DATABASE_URL"] = url
    os.environ["ENVIRONMENT"] = "script"
    return True


async def read_only(session: AsyncSession) -> None:
    """Make the session's transaction read-only before its first query, and check that PostgreSQL agrees.

    SQLite (the tests) has no such mode and is left as it is.
    """
    from sqlalchemy import text

    if session.get_bind().dialect.name != "postgresql":
        return
    await session.execute(text("SET TRANSACTION READ ONLY"))
    state = (await session.execute(text("SHOW transaction_read_only"))).scalar_one()
    if state != "on":
        raise RuntimeError(f"the transaction is not read-only (transaction_read_only = {state})")


def row_json(row: AgentFeedback) -> dict[str, Any]:
    """Every column of the row, timestamps as UTC ISO 8601 with `Z` (the table stores naive UTC)."""
    from core.database import AgentFeedback

    out: dict[str, Any] = {}
    for column in AgentFeedback.__table__.columns:
        value = getattr(row, column.key)
        if isinstance(value, datetime):
            value = value.isoformat() + "Z"
        elif isinstance(value, list):
            value = list(value)
        out[column.name] = value
    return out


def outside_repository(path: Path) -> bool:
    """True when no directory from `path` up holds a `.git` (a checkout or a worktree): case data stays out of git."""
    resolved = path.resolve()
    return not any((directory / ".git").exists() for directory in (resolved, *resolved.parents))
