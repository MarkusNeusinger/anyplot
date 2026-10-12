"""Sync the promoted feedback cases from the private case bucket into `agents/evals/.cases/`.

Run it from the repository root on the dev machine:

    uv run --extra agents python -m agents.evals.sync_cases
    uv run --extra agents python -m agents.evals.sync_cases --backfill            # also list unindexed cases
    uv run --extra agents python -m agents.evals.sync_cases --backfill --apply    # and insert their rows

The `agent_feedback` table (`core/database/models.py`, `AgentFeedback`) is the source of
truth for the triage; the bucket holds the files. A case is active when it is promoted
(`promoted_at` set), not superseded and not retired (status `done` or `wont_solve`). The
tool reads every row once and takes at most one action per case on
`.cases/case-<case id, lower case>/`, the directory name `import_case.py` gives a case
directory:

* active, no directory: download `manifest.json` (and `data.csv` when the case holds it)
  from `cases/<case_id>/` into a temporary directory and import it with the importer's
  own functions and the row's `expected` (`written`), or report why the importer
  refuses it and what to do instead (`skipped`);
* active, a directory: `kept` as it is, so a case you imported by hand with
  `--change-request` survives; `--force` imports it again;
* not active, a directory: `removed`. The directory is renamed out of `.cases/` first,
  so the harness never meets half a case;
* a `case-*` directory without a row: `unknown`, left alone. Other directories, such as
  the `session-*` ones of bundle imports, are never touched.

`--backfill` lists the case directories in the bucket that have no row (cases stored
before the table existed, or whose row insert failed with `502 row_missing`) and prints the
row each would get; with `--apply` it inserts them through
`AgentFeedbackRepository.create_case`, oldest first, so the supersede links come out as
the feedback route sets them. That insert is the only database write this tool makes.

Environment: `DATABASE_URL` from the shell, else from this checkout's `.env` (`--env` names
another file), and nothing else from that file; the bucket through Application Default
Credentials. The importer loads the agent settings, which refuse the development-only
`AGENT_*` exports (`AGENT_RENDERER=local`, `AGENT_DEV_FIXTURE`, `AGENT_RENDER_TOKEN`, ...)
unless `ENVIRONMENT=development`; the tool checks them before it touches the database.

Exit codes: 0 every action done, 1 a case skipped, failed or unknown (each one listed),
2 bad arguments, no `DATABASE_URL`, or agent settings that refuse the environment.

`core` and `agents.anyplot` are imported only inside functions: `core.database` reads
`DATABASE_URL` when it is imported, and `main` sets it first.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import re
import shutil
import sys
import tempfile
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any, Literal, NamedTuple, Protocol

from dotenv import dotenv_values
from google.api_core.exceptions import GoogleAPICallError
from google.auth.exceptions import GoogleAuthError
from sqlalchemy.exc import SQLAlchemyError


if TYPE_CHECKING:
    from core.database import AgentFeedback, AgentFeedbackRepository


DEFAULT_ENV_FILE = Path(__file__).resolve().parents[2] / ".env"
"""This checkout's `.env`, never a parent's: a worktree must not reach the main checkout's file by default."""
DEFAULT_BUCKET = "anyplot-agent-cases"
"""The default of `core.config.Settings.agent_cases_bucket`, the bucket the feedback route writes to."""
RETIRED_STATUSES = frozenset({"done", "wont_solve"})
"""The triage states that retire a case: its eval case leaves `.cases/`."""
CASE_DIR_PREFIX = "case-"
STAGING_PREFIX = ".import-old-"
"""Where a removed case waits for its deletion, beside `.cases/` (git-ignored as `agents/evals/.import-*/`)."""
CASE_ERRORS: tuple[type[BaseException], ...] = (GoogleAPICallError, GoogleAuthError, OSError)
"""The failures of one case's bucket read or file write; reported per case, the run continues."""

Kind = Literal["written", "kept", "removed", "skipped", "unknown", "failed", "backfill"]
Step = Literal["write", "keep", "remove"]
COUNTED: tuple[Kind, ...] = ("written", "kept", "removed", "skipped", "unknown", "failed")
"""The summary's counts, in this order; `backfill` follows when the run backfills."""
NEEDS_ATTENTION: frozenset[Kind] = frozenset({"skipped", "unknown", "failed"})
"""The actions that make the exit code 1."""


@dataclass(frozen=True)
class Action:
    """One line of the report: what happened to a case, and the detail to print."""

    case_id: str
    kind: Kind
    detail: str = ""


class Planned(NamedTuple):
    """What the sync is about to do with a case's directory, before any download."""

    step: Step
    detail: str


class CaseStore(Protocol):
    """The case bucket, read-only: the private bucket in use, a dict in the tests."""

    def list_case_ids(self) -> list[str]:
        """The `<case_id>` of every `cases/<case_id>/` prefix, sorted."""

    def download(self, case_id: str, name: str) -> bytes | None:
        """The bytes of `cases/<case_id>/<name>`; None when the object does not exist, raise otherwise."""


class TableUnavailable(RuntimeError):
    """The `agent_feedback` rows could not be read; the message says why, without the URL."""


class GcsCaseStore:
    """The case bucket through `google-cloud-storage` and Application Default Credentials.

    The same client style as the BFF's `api.agent_cases.GcsCaseBucket`, read-only; the
    client is created on first use, so a run that downloads nothing needs no credentials.
    """

    def __init__(self, bucket: str) -> None:
        self.bucket = bucket
        self._client: Any = None

    def _storage(self) -> Any:
        if self._client is None:
            from google.cloud.storage import Client

            self._client = Client()
        return self._client

    def list_case_ids(self) -> list[str]:
        from core.agent_cases import CASE_PREFIX

        prefix = f"{CASE_PREFIX}/"
        blobs = self._storage().list_blobs(self.bucket, prefix=prefix, delimiter="/")
        # The prefixes fill only as the iterator is consumed (as in the library's own samples).
        for _blob in blobs:
            pass
        return sorted(str(name).removeprefix(prefix).rstrip("/") for name in blobs.prefixes)

    def download(self, case_id: str, name: str) -> bytes | None:
        from google.api_core.exceptions import NotFound

        from core.agent_cases import case_object

        try:
            data: bytes = self._storage().bucket(self.bucket).blob(case_object(case_id, name)).download_as_bytes()
        except NotFound:
            return None
        return data


def dir_name(case_id: str) -> str:
    """The `.cases/` directory of a case: `case-<case id, lower case>`, what the importer names a case directory."""
    return f"{CASE_DIR_PREFIX}{case_id.lower()}"


def is_active(row: AgentFeedback) -> bool:
    """Promoted, not superseded and not retired: the case belongs in `.cases/`."""
    return row.promoted_at is not None and row.superseded_by is None and row.status not in RETIRED_STATUSES


def plan_case(row: AgentFeedback, has_dir: bool, force: bool) -> Planned | None:
    """The step for one row given whether its directory exists; None when there is nothing to do."""
    if is_active(row):
        if not has_dir or force:
            return Planned("write", "")
        return Planned("keep", "already synced")
    if not has_dir:
        return None
    if row.status in RETIRED_STATUSES:
        return Planned("remove", f"retired ({row.status})")
    if row.superseded_by is not None:
        return Planned("remove", f"superseded by {row.superseded_by}")
    return Planned("remove", "not promoted")


def _first_line(text: str) -> str:
    lines = text.strip().splitlines()
    return lines[0] if lines else ""


def _failed(case_id: str, exc: BaseException) -> Action:
    return Action(case_id, "failed", f"{type(exc).__name__}: {_first_line(str(exc))}")


def sync(rows: list[AgentFeedback], store: CaseStore, cases_dir: Path, *, force: bool) -> list[Action]:
    """Bring `cases_dir` in line with the rows: write the active cases, remove the others.

    Only `case-*` directories whose case has a row are written or removed; a bucket or file
    error of one case is reported as `failed` and the next case goes on.
    """
    present = {path.name for path in cases_dir.iterdir() if path.is_dir()} if cases_dir.is_dir() else set()
    owned: set[str] = set()
    actions: list[Action] = []
    for row in rows:
        name = dir_name(row.id)
        owned.add(name)
        planned = plan_case(row, name in present, force)
        if planned is None:
            continue
        try:
            if planned.step == "write":
                actions.append(_import(row, store, cases_dir, replace=name in present))
            elif planned.step == "keep":
                actions.append(Action(row.id, "kept", planned.detail))
            else:
                _remove(cases_dir / name)
                actions.append(Action(row.id, "removed", planned.detail))
        except CASE_ERRORS as exc:
            actions.append(_failed(row.id, exc))
    for name in sorted(present - owned):
        if name.startswith(CASE_DIR_PREFIX):
            actions.append(Action(name, "unknown", "no row for this directory; left alone"))
    return actions


def _import(row: AgentFeedback, store: CaseStore, cases_dir: Path, *, replace: bool) -> Action:
    """Download one promoted case and write it through the importer; `skipped` with the reason it refuses."""
    from agents.evals import import_case
    from core.agent_cases import EXPECTED_BY_REACTION, MANIFEST_NAME

    # The row's outcome, else the reaction rule; promoting on /debug always sets one, so this
    # refusal is a defence for a row promoted some other way. Checked before any download.
    expected = row.expected or EXPECTED_BY_REACTION.get(row.reaction)
    if expected is None:
        return Action(
            row.id,
            "skipped",
            f"the reaction {row.reaction} implies no outcome: set expected on /debug, or import by hand with --expected",
        )
    manifest = store.download(row.id, MANIFEST_NAME)
    if manifest is None:
        return Action(row.id, "skipped", "files expired in the bucket")
    data = store.download(row.id, "data.csv") if row.include_data else None
    name = dir_name(row.id)
    with tempfile.TemporaryDirectory(prefix="anyplot-sync-") as tmp:
        directory = Path(tmp) / row.id
        directory.mkdir()
        (directory / MANIFEST_NAME).write_bytes(manifest)
        if data is not None:
            (directory / "data.csv").write_bytes(data)
        try:
            source = import_case.read_case_dir(directory, None)
            manifest_id = source.manifest.get("id") if source.manifest else None
            if manifest_id != row.id:
                return Action(row.id, "skipped", f"manifest id {manifest_id} differs from its object prefix {row.id}")
            imported = import_case.build_case(source, expected)
            import_case.write_case(name, imported, force=replace, promoted_dir=cases_dir)
        except import_case.AmbiguousRequest:
            return Action(
                row.id,
                "skipped",
                f"cannot tell which message made version {row.result_version}: "
                "import it by hand with --change-request TEXT or --no-change-request",
            )
        except import_case.ImportRefused as exc:
            return Action(row.id, "skipped", _first_line(str(exc)))
    case = imported.case
    detail = f"{cases_dir.name}/{name}: {case['spec_id']} {case['library']}, expected {case['expected']}"
    if imported.change_request:
        detail += ", with its change request"
    for note in imported.notes:
        detail += f"; note: {note}"
    return Action(row.id, "written", detail)


def _remove(directory: Path) -> None:
    """Move `directory` out of `.cases/` by one rename, then delete it."""
    holder = Path(tempfile.mkdtemp(prefix=f"{STAGING_PREFIX}{directory.name}-", dir=directory.parent.parent))
    try:
        os.rename(directory, holder / directory.name)
    finally:
        shutil.rmtree(holder, ignore_errors=True)


async def backfill(
    bucket_ids: list[str], rows: list[AgentFeedback], store: CaseStore, repo: AgentFeedbackRepository, *, apply: bool
) -> list[Action]:
    """Index the bucket's cases that have no row: list them, or with `apply` insert them, oldest first.

    Ids sort by time, so a case is inserted before the case that replaces it, and
    `create_case` links both directions in one commit. A failed insert rolls the session
    back, so the next case does not inherit its error.
    """
    from core.agent_cases import CASE_ID_PATTERN, MANIFEST_NAME, ManifestError, row_from_manifest

    known = {row.id for row in rows}
    actions: list[Action] = []
    for case_id in sorted(set(bucket_ids) - known):
        if not re.fullmatch(CASE_ID_PATTERN, case_id):
            actions.append(Action(case_id, "skipped", "not a case id; left alone"))
            continue
        try:
            raw = store.download(case_id, MANIFEST_NAME)
            if raw is None:
                actions.append(Action(case_id, "skipped", "aborted upload, no manifest"))
                continue
            try:
                row = row_from_manifest(json.loads(raw))
            except ValueError as exc:  # ManifestError, or bytes that are not JSON
                reason = str(exc) if isinstance(exc, ManifestError) else "manifest.json is not JSON"
                actions.append(Action(case_id, "skipped", reason))
                continue
            if row["id"] != case_id:
                actions.append(
                    Action(case_id, "skipped", f"manifest id {row['id']} differs from its object prefix {case_id}")
                )
                continue
            if not apply:
                where = f"{row['spec_id'] or '-'} {row['library_id'] or '-'}"
                detail = f"would insert ({row['reaction']}, {where}, v{row['result_version']}); run with --apply"
                actions.append(Action(case_id, "backfill", detail))
                continue
            entity = await repo.create_case(row)
            detail = "inserted" + (f", superseded by {entity.superseded_by}" if entity.superseded_by else "")
            actions.append(Action(case_id, "backfill", detail))
        except SQLAlchemyError as exc:
            # One `AsyncSession` serves the whole run, and after a failed flush or commit every
            # further statement raises `PendingRollbackError` until it is rolled back.
            await repo.session.rollback()
            actions.append(_failed(case_id, exc))
        except CASE_ERRORS as exc:
            actions.append(_failed(case_id, exc))
    return actions


async def run(args: argparse.Namespace, store: CaseStore, cases_dir: Path) -> list[Action]:
    """Read the rows, sync `cases_dir`, and backfill when asked; the engine is disposed on every path."""
    from core.database import AgentFeedbackRepository, close_db, get_db_context

    try:
        try:
            async with get_db_context() as session:
                rows = await AgentFeedbackRepository(session).list_all()
        except (SQLAlchemyError, OSError) as exc:
            raise TableUnavailable(f"{type(exc).__name__}: {_first_line(str(exc))}") from exc
        actions = sync(rows, store, cases_dir, force=args.force)
        if args.backfill:
            try:
                bucket_ids = store.list_case_ids()
            except CASE_ERRORS as exc:
                return [*actions, _failed("cases/", exc)]
            async with get_db_context() as session:
                actions += await backfill(bucket_ids, rows, store, AgentFeedbackRepository(session), apply=args.apply)
        return actions
    finally:
        await close_db()


def report(actions: list[Action], *, backfill_run: bool, apply: bool) -> str:
    """The fixed-width table, one line per action, and the summary line."""
    from core.database import CASE_ID_LENGTH

    lines: list[str] = []
    if actions:
        # As wide as a case id, wider only for a longer name (an `unknown` directory).
        width = max(CASE_ID_LENGTH, *(len(action.case_id) for action in actions))
        lines.append(f"{'case id':<{width}}  {'action':<8}  detail")
        lines.extend(f"{action.case_id:<{width}}  {action.kind:<8}  {action.detail}".rstrip() for action in actions)
    counts = Counter(action.kind for action in actions)
    parts = [f"{kind} {counts[kind]}" for kind in COUNTED]
    if backfill_run:
        parts.append(f"backfill {counts['backfill']} ({'applied' if apply else 'dry run'})")
    lines.append(", ".join(parts))
    return "\n".join(lines)


def bucket_name(requested: str | None) -> str:
    """`--bucket`, else `AGENT_CASES_BUCKET`, else the feedback route's default bucket."""
    return requested or os.environ.get("AGENT_CASES_BUCKET") or DEFAULT_BUCKET


def _settings_refusal() -> str | None:
    """Why the agent settings refuse this shell environment, or None.

    Constructed explicitly rather than relying on the import: `agents.anyplot` validates
    the settings once at import, and a process that imported it before would not again.
    """
    from pydantic import ValidationError

    try:
        from agents.anyplot.settings import AgentSettings

        AgentSettings()
    except ValidationError as exc:
        return "; ".join(str(error["msg"]).removeprefix("Value error, ") for error in exc.errors())
    return None


def main(argv: list[str] | None = None, *, store: CaseStore | None = None, cases_dir: Path | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m agents.evals.sync_cases",
        description="Sync the promoted feedback cases from the case bucket into agents/evals/.cases/.",
    )
    parser.add_argument(
        "--backfill", action="store_true", help="also list the bucket's cases that have no table row (a dry run)"
    )
    parser.add_argument("--apply", action="store_true", help="with --backfill: insert those rows")
    parser.add_argument(
        "--force", action="store_true", help="import an active case again although its directory exists"
    )
    parser.add_argument("--bucket", help=f"the case bucket (default: AGENT_CASES_BUCKET, else {DEFAULT_BUCKET})")
    parser.add_argument(
        "--env",
        type=Path,
        default=DEFAULT_ENV_FILE,
        help="the .env to read DATABASE_URL from (default: this checkout's)",
    )
    args = parser.parse_args(argv)
    if args.apply and not args.backfill:
        parser.error("--apply inserts the rows that --backfill lists; pass both")

    # 1. The database URL, and nothing else from the .env: its ENVIRONMENT would reach the
    # agent settings, and INSTANCE_CONNECTION_NAME is not needed with a direct URL.
    # `dotenv_values` reads the file whatever PYTHON_DOTENV_DISABLED says.
    if not os.environ.get("DATABASE_URL"):
        url = dotenv_values(args.env).get("DATABASE_URL")
        if not url:
            print(f"sync_cases: DATABASE_URL is not set and {args.env} does not define it", file=sys.stderr)
            return 2
        os.environ["DATABASE_URL"] = url
    # 2. `core.database` echoes every statement under `development`, its default.
    os.environ.setdefault("ENVIRONMENT", "script")
    # 3. The agents package reads settings only from the environment, never from a .env file.
    os.environ["PYTHON_DOTENV_DISABLED"] = "1"
    os.environ["ADK_DISABLE_LOAD_DOTENV"] = "1"
    # 4. The importer's `write_case` loads the agent settings; a refusal is one clean exit here,
    # before the database or the bucket is touched, not one failed case after another.
    try:
        refusal = _settings_refusal()
    except ImportError as exc:
        print(f"sync_cases: {exc}; run it with `uv run --extra agents`", file=sys.stderr)
        return 2
    if refusal is not None:
        print(
            f"sync_cases: the agent settings refuse this shell environment: {refusal}; "
            "unset the AGENT_* exports or run with ENVIRONMENT=development",
            file=sys.stderr,
        )
        return 2

    from agents.evals import import_case

    if store is None:
        store = GcsCaseStore(bucket_name(args.bucket))
    if cases_dir is None:
        cases_dir = import_case.PROMOTED_DIR
    try:
        actions = asyncio.run(run(args, store, cases_dir))
    except TableUnavailable as exc:
        print(f"sync_cases: cannot read the agent_feedback table: {exc}", file=sys.stderr)
        return 1
    print(report(actions, backfill_run=args.backfill, apply=args.apply))
    return 1 if any(action.kind in NEEDS_ATTENTION for action in actions) else 0


if __name__ == "__main__":
    raise SystemExit(main())
