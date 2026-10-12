"""`agents/evals/sync_cases.py`: promoted cases from the bucket into `.cases/`, retired ones out, the backfill.

No test here opens a database or a GCS client: the bucket is an in-memory `MemoryStore`,
the table is a fake behind `core.database.get_db_context` or SQLite in memory
(`tests/conftest.py`), and the autouse `isolated` fixture makes any other attempt fail.
CI exports the production `DATABASE_URL` for the whole pytest run, so that fixture is
what keeps these tests away from it.
"""

import importlib
import json
import os
from contextlib import asynccontextmanager
from datetime import UTC, datetime
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest
from google.api_core.exceptions import NotFound, ServiceUnavailable
from sqlalchemy.exc import IntegrityError, OperationalError

import core.database
from agents.evals import import_case, sync_cases
from agents.evals.cases import load_cases
from agents.evals.sync_cases import (
    DEFAULT_BUCKET,
    DEFAULT_ENV_FILE,
    RETIRED_STATUSES,
    Action,
    GcsCaseStore,
    backfill,
    bucket_name,
    dir_name,
    is_active,
    main,
    plan_case,
    report,
    sync,
)
from core.agent_cases import row_from_manifest
from core.config import Settings
from core.database import FEEDBACK_STATUSES, AgentFeedback, AgentFeedbackRepository, connection

from .test_import_case import DATA, _bundle


CASE_A = "20261012T143005Z-1a2b3c4d"
CASE_B = "20261012T150000Z-2b3c4d5e"
CASE_C = "20261012T160000Z-3c4d5e6f"
PROMOTED = datetime(2026, 10, 12, 18, 0, 0)
SAFE_URL = "postgresql+asyncpg://nobody:none@localhost:1/none"
"""Never used (the table is faked), and port 1 has no listener, so a slip fails fast."""
ENV_NAMES = (
    "DATABASE_URL",
    "ENVIRONMENT",
    "INSTANCE_CONNECTION_NAME",
    "AGENT_CASES_BUCKET",
    "AGENT_RENDERER",
    "PYTHON_DOTENV_DISABLED",
    "ADK_DISABLE_LOAD_DOTENV",
)


@pytest.fixture(autouse=True)
def isolated(monkeypatch) -> None:
    """No database, no GCS client, and every variable `main` sets is restored afterwards."""

    async def refuse_init() -> None:
        raise AssertionError("a sync_cases test tried to open a database")

    def refuse(*args, **kwargs):
        raise AssertionError("a sync_cases test tried to reach a real service")

    monkeypatch.setattr(connection, "init_db", refuse_init)
    monkeypatch.setattr(core.database, "get_db_context", refuse)
    monkeypatch.setattr(core.database, "close_db", AsyncMock())
    monkeypatch.setattr("google.cloud.storage.Client", refuse)
    for name in ENV_NAMES:
        monkeypatch.setenv(name, "")  # records the current value, so teardown restores it
        monkeypatch.delenv(name)


@pytest.fixture
def cases(tmp_path, monkeypatch) -> Path:
    """The promoted directory and an empty fixtures directory, both in `tmp_path`."""
    directory = tmp_path / "evals" / ".cases"
    fixtures = tmp_path / "evals" / "fixtures"
    fixtures.mkdir(parents=True)
    monkeypatch.setattr(import_case, "PROMOTED_DIR", directory)
    monkeypatch.setattr(import_case, "FIXTURES_DIR", fixtures)
    return directory


def stored(
    case_id: str = CASE_A,
    *,
    reaction: str = "thumbs_down",
    version: int = 2,
    include_data: bool = True,
    replaces: str | None = None,
) -> dict[str, bytes]:
    """The files of a case exactly as the BFF's feedback route stores them (`api/agent_cases.py`)."""
    from api.agent_cases import Submission
    from api.agent_cases import build_case as build_stored_case

    bundle = _bundle()
    bundle["versions"] = [item for item in bundle["versions"] if item["number"] == version]
    if not include_data:
        for item in bundle["versions"]:
            item["data_csv"] = None
    case = build_stored_case(
        json.dumps(bundle).encode(),
        Submission(
            reaction=reaction,
            message="the legend hides points",
            include_data=include_data,
            result_version=version,
            replaces=replaces,
        ),
        case_id=case_id,
        created_at=datetime.strptime(case_id[:16], "%Y%m%dT%H%M%SZ").replace(tzinfo=UTC),
        bucket="anyplot-agent-cases",
        user_hash="adm_0123456789abcdef",
        session_id="S1abcdefgh",
    )
    return {item.name: item.data for item in case.files}


def manifest_of(files: dict[str, bytes]) -> dict:
    return json.loads(files["manifest.json"])


def row_for(files: dict[str, bytes], **triage) -> AgentFeedback:
    """The table row of a stored case, with the triage state given."""
    return AgentFeedback(**{**row_from_manifest(manifest_of(files)), **triage})


class MemoryStore:
    """The case bucket as a dict of `(case_id, name) -> bytes`; `failing` case ids raise like an outage."""

    def __init__(self, *cases: tuple[str, dict[str, bytes]]) -> None:
        self.objects: dict[tuple[str, str], bytes] = {}
        self.downloads: list[tuple[str, str]] = []
        self.failing: set[str] = set()
        self.list_error: Exception | None = None
        for case_id, files in cases:
            self.add(case_id, files)

    def add(self, case_id: str, files: dict[str, bytes]) -> None:
        for name, data in files.items():
            self.objects[(case_id, name)] = data

    def list_case_ids(self) -> list[str]:
        if self.list_error is not None:
            raise self.list_error
        return sorted({case_id for case_id, _ in self.objects})

    def download(self, case_id: str, name: str) -> bytes | None:
        self.downloads.append((case_id, name))
        if case_id in self.failing:
            raise ServiceUnavailable("the bucket is unavailable")
        return self.objects.get((case_id, name))


def written(directory: Path) -> dict[str, str]:
    return {path.name: path.read_text(encoding="utf-8") for path in sorted(directory.iterdir())}


def leftovers(cases: Path) -> list[str]:
    """Staging directories beside `.cases/`; every path must clean them up."""
    return [path.name for path in cases.parent.iterdir() if path.name.startswith(".import-")]


class TestPlan:
    @pytest.mark.parametrize(
        ("triage", "has_dir", "force", "planned"),
        [
            ({"promoted_at": PROMOTED}, False, False, ("write", "")),
            ({"promoted_at": PROMOTED, "status": "in_progress"}, False, False, ("write", "")),
            ({"promoted_at": PROMOTED}, True, False, ("keep", "already synced")),
            ({"promoted_at": PROMOTED}, True, True, ("write", "")),
            ({"promoted_at": PROMOTED, "status": "done"}, True, False, ("remove", "retired (done)")),
            ({"promoted_at": PROMOTED, "status": "wont_solve"}, True, True, ("remove", "retired (wont_solve)")),
            ({"promoted_at": PROMOTED, "superseded_by": CASE_B}, True, False, ("remove", f"superseded by {CASE_B}")),
            ({}, True, False, ("remove", "not promoted")),
            ({}, False, False, None),
            ({"promoted_at": PROMOTED, "status": "done"}, False, False, None),
        ],
    )
    def test_one_step_per_case(self, triage, has_dir, force, planned) -> None:
        assert plan_case(row_for(stored(), **triage), has_dir, force) == planned

    def test_active_means_promoted_not_superseded_not_retired(self) -> None:
        files = stored()
        assert is_active(row_for(files, promoted_at=PROMOTED))
        assert not is_active(row_for(files))
        assert not is_active(row_for(files, promoted_at=PROMOTED, superseded_by=CASE_B))
        assert not is_active(row_for(files, promoted_at=PROMOTED, status="done"))

    def test_the_directory_is_the_importers_name_for_a_case_directory(self, tmp_path) -> None:
        directory = tmp_path / CASE_A
        directory.mkdir()
        for name, data in stored().items():
            (directory / name).write_bytes(data)
        assert import_case.read_case_dir(directory, None).default_id == dir_name(CASE_A)
        assert dir_name(CASE_A) == "case-20261012t143005z-1a2b3c4d"

    def test_the_retired_states_are_triage_states(self) -> None:
        assert RETIRED_STATUSES == {"done", "wont_solve"}
        assert RETIRED_STATUSES < set(FEEDBACK_STATUSES)


class TestSync:
    def test_writes_a_promoted_case_through_the_importer(self, cases) -> None:
        files = stored()
        store = MemoryStore((CASE_A, files))

        actions = sync([row_for(files, promoted_at=PROMOTED, expected="rejected")], store, cases, force=False)

        target = cases / dir_name(CASE_A)
        assert actions == [
            Action(
                CASE_A,
                "written",
                f".cases/{target.name}: scatter-basic matplotlib, expected rejected, with its change request",
            )
        ]
        content = written(target)
        assert json.loads(content["case.json"])["expected"] == "rejected"
        assert json.loads(content["case.json"])["tags"] == ["imported", "thumbs_down"]
        assert content["data.csv"] == DATA
        assert content["change_request.txt"] == "log scale on y\n"
        assert store.downloads == [(CASE_A, "manifest.json"), (CASE_A, "data.csv")]
        loaded = load_cases(fixtures_dir=import_case.FIXTURES_DIR, promoted_dir=cases)
        assert [(case.case_id, case.origin) for case in loaded] == [(target.name, "promoted")]
        assert leftovers(cases) == []

    def test_the_rows_outcome_wins_over_the_reaction(self, cases) -> None:
        files = stored(reaction="thumbs_down")
        sync(
            [row_for(files, promoted_at=PROMOTED, expected="accepted")],
            MemoryStore((CASE_A, files)),
            cases,
            force=False,
        )
        assert json.loads((cases / dir_name(CASE_A) / "case.json").read_text())["expected"] == "accepted"

    def test_without_an_outcome_the_reaction_rule_applies(self, cases) -> None:
        files = stored(reaction="thumbs_up")
        actions = sync([row_for(files, promoted_at=PROMOTED)], MemoryStore((CASE_A, files)), cases, force=False)
        assert actions[0].kind == "written"
        assert json.loads((cases / dir_name(CASE_A) / "case.json").read_text())["expected"] == "accepted"

    @pytest.mark.parametrize("reaction", ["bug", "idea"])
    def test_a_bug_or_idea_without_an_outcome_is_skipped_before_any_download(self, cases, reaction) -> None:
        files = stored(reaction=reaction)
        store = MemoryStore((CASE_A, files))

        actions = sync([row_for(files, promoted_at=PROMOTED)], store, cases, force=False)

        assert actions == [
            Action(
                CASE_A,
                "skipped",
                f"the reaction {reaction} implies no outcome: set expected on /debug, or import by hand with --expected",
            )
        ]
        assert store.downloads == []
        assert not cases.exists()

    def test_a_bug_with_an_outcome_is_written(self, cases) -> None:
        files = stored(reaction="bug")
        row = row_for(files, promoted_at=PROMOTED, expected="accepted")
        assert sync([row], MemoryStore((CASE_A, files)), cases, force=False)[0].kind == "written"

    def test_an_existing_directory_is_kept_and_force_imports_it_again(self, cases) -> None:
        files = stored()
        store = MemoryStore((CASE_A, files))
        row = row_for(files, promoted_at=PROMOTED, expected="rejected")
        sync([row], store, cases, force=False)
        target = cases / dir_name(CASE_A)
        (target / "change_request.txt").write_text("my own request\n")
        store.downloads.clear()

        assert sync([row], store, cases, force=False) == [Action(CASE_A, "kept", "already synced")]
        assert store.downloads == []
        assert (target / "change_request.txt").read_text() == "my own request\n"

        assert sync([row], store, cases, force=True)[0].kind == "written"
        assert (target / "change_request.txt").read_text() == "log scale on y\n"
        assert leftovers(cases) == []

    def test_a_case_without_data_is_skipped(self, cases) -> None:
        files = stored(include_data=False)
        store = MemoryStore((CASE_A, files))

        actions = sync([row_for(files, promoted_at=PROMOTED, expected="rejected")], store, cases, force=False)

        assert actions[0].kind == "skipped"
        assert actions[0].detail.startswith("the source holds no data.csv")
        assert store.downloads == [(CASE_A, "manifest.json")]
        assert not cases.exists()

    def test_expired_files_are_skipped(self, cases) -> None:
        row = row_for(stored(), promoted_at=PROMOTED, expected="rejected")
        assert sync([row], MemoryStore(), cases, force=False) == [
            Action(CASE_A, "skipped", "files expired in the bucket")
        ]

    def test_an_ambiguous_change_request_names_the_hand_import(self, cases) -> None:
        """A case sent on an older version: the importer cannot tell which message made it."""
        files = stored(version=1)
        actions = sync(
            [row_for(files, promoted_at=PROMOTED, expected="rejected")],
            MemoryStore((CASE_A, files)),
            cases,
            force=False,
        )
        assert actions == [
            Action(
                CASE_A,
                "skipped",
                "cannot tell which message made version 1: "
                "import it by hand with --change-request TEXT or --no-change-request",
            )
        ]
        assert not (cases / dir_name(CASE_A)).exists()

    def test_a_manifest_under_another_prefix_is_skipped(self, cases) -> None:
        store = MemoryStore((CASE_B, stored(CASE_A)))
        row = row_for(stored(CASE_B), promoted_at=PROMOTED, expected="rejected")
        assert sync([row], store, cases, force=False) == [
            Action(CASE_B, "skipped", f"manifest id {CASE_A} differs from its object prefix {CASE_B}")
        ]

    @pytest.mark.parametrize(
        ("triage", "detail"),
        [
            ({"status": "done"}, "retired (done)"),
            ({"status": "wont_solve"}, "retired (wont_solve)"),
            ({"superseded_by": CASE_C}, f"superseded by {CASE_C}"),
            ({"promoted_at": None}, "not promoted"),
        ],
    )
    def test_an_inactive_case_is_removed_cleanly(self, cases, triage, detail) -> None:
        first, second = stored(CASE_A), stored(CASE_B)
        store = MemoryStore((CASE_A, first), (CASE_B, second))
        rows = [
            row_for(first, promoted_at=PROMOTED, expected="rejected"),
            row_for(second, promoted_at=PROMOTED, expected="rejected"),
        ]
        sync(rows, store, cases, force=False)
        assert sorted(path.name for path in cases.iterdir()) == [dir_name(CASE_A), dir_name(CASE_B)]

        rows[0] = row_for(first, **{"promoted_at": PROMOTED, "expected": "rejected", **triage})
        actions = sync(rows, store, cases, force=False)

        assert actions == [Action(CASE_A, "removed", detail), Action(CASE_B, "kept", "already synced")]
        assert [path.name for path in cases.iterdir()] == [dir_name(CASE_B)]
        assert leftovers(cases) == []
        loaded = load_cases(fixtures_dir=import_case.FIXTURES_DIR, promoted_dir=cases)
        assert [case.case_id for case in loaded] == [dir_name(CASE_B)]

    def test_a_case_directory_without_a_row_is_left_alone(self, cases) -> None:
        (cases / "case-made-by-hand").mkdir(parents=True)
        (cases / "session-0a1b2c3d-v2").mkdir()
        (cases / "case-a-file").write_text("not a directory")

        actions = sync([], MemoryStore(), cases, force=False)

        assert actions == [Action("case-made-by-hand", "unknown", "no row for this directory; left alone")]
        assert sorted(path.name for path in cases.iterdir()) == [
            "case-a-file",
            "case-made-by-hand",
            "session-0a1b2c3d-v2",
        ]

    def test_a_bucket_error_fails_one_case_and_the_next_goes_on(self, cases) -> None:
        first, second = stored(CASE_A), stored(CASE_B)
        store = MemoryStore((CASE_A, first), (CASE_B, second))
        store.failing.add(CASE_A)
        rows = [
            row_for(first, promoted_at=PROMOTED, expected="rejected"),
            row_for(second, promoted_at=PROMOTED, expected="rejected"),
        ]

        actions = sync(rows, store, cases, force=False)

        assert actions[0] == Action(CASE_A, "failed", "ServiceUnavailable: 503 the bucket is unavailable")
        assert actions[1].kind == "written"
        assert [path.name for path in cases.iterdir()] == [dir_name(CASE_B)]


class TestBackfill:
    async def test_a_dry_run_lists_and_inserts_nothing(self) -> None:
        store = MemoryStore((CASE_A, stored(CASE_A)))
        repo = MagicMock(create_case=AsyncMock())

        actions = await backfill(store.list_case_ids(), [], store, repo, apply=False)

        assert actions == [
            Action(CASE_A, "backfill", "would insert (thumbs_down, scatter-basic matplotlib, v2); run with --apply")
        ]
        repo.create_case.assert_not_awaited()

    async def test_only_cases_without_a_row(self) -> None:
        first, second = stored(CASE_A), stored(CASE_B)
        store = MemoryStore((CASE_A, first), (CASE_B, second))

        actions = await backfill(store.list_case_ids(), [row_for(first)], store, MagicMock(), apply=False)

        assert [action.case_id for action in actions] == [CASE_B]
        assert (CASE_A, "manifest.json") not in store.downloads

    async def test_apply_inserts_oldest_first_and_links_the_chain(self, test_session) -> None:
        store = MemoryStore((CASE_B, stored(CASE_B, replaces=CASE_A)), (CASE_A, stored(CASE_A)))
        repo = AgentFeedbackRepository(test_session)

        actions = await backfill([CASE_B, CASE_A], [], store, repo, apply=True)

        assert actions == [Action(CASE_A, "backfill", "inserted"), Action(CASE_B, "backfill", "inserted")]
        earlier, later = await repo.get_by_id(CASE_A), await repo.get_by_id(CASE_B)
        assert (earlier.superseded_by, later.superseded_by) == (CASE_B, None)
        assert earlier.created_at == datetime(2026, 10, 12, 14, 30, 5)
        assert (earlier.status, earlier.tags, earlier.promoted_at) == ("new", [], None)

    async def test_an_orphan_whose_successor_the_route_inserted_arrives_superseded(self, test_session) -> None:
        successor = stored(CASE_B, replaces=CASE_A)
        repo = AgentFeedbackRepository(test_session)
        indexed = await repo.create_case(row_from_manifest(manifest_of(successor)))
        store = MemoryStore((CASE_A, stored(CASE_A)), (CASE_B, successor))

        actions = await backfill(store.list_case_ids(), [indexed], store, repo, apply=True)

        assert actions == [Action(CASE_A, "backfill", f"inserted, superseded by {CASE_B}")]
        assert (await repo.get_by_id(CASE_A)).superseded_by == CASE_B

    async def test_apply_inserts_the_manifests_row(self) -> None:
        files = stored(CASE_A)
        repo = MagicMock(create_case=AsyncMock(return_value=SimpleNamespace(superseded_by=None)))

        await backfill([CASE_A], [], MemoryStore((CASE_A, files)), repo, apply=True)

        repo.create_case.assert_awaited_once_with(row_from_manifest(manifest_of(files)))

    @pytest.mark.parametrize(
        ("files", "detail"),
        [
            ({"plot.py": b"print(1)\n"}, "aborted upload, no manifest"),
            ({"manifest.json": b"{"}, "manifest.json is not JSON"),
            ({"manifest.json": json.dumps({**manifest_of(stored()), "schema": 2}).encode()}, "schema is not 1"),
            (
                {"manifest.json": json.dumps({**manifest_of(stored()), "reaction": "heart"}).encode()},
                "reaction is not one of the feedback reactions",
            ),
        ],
    )
    async def test_an_unusable_case_is_skipped(self, files, detail) -> None:
        repo = MagicMock(create_case=AsyncMock())
        actions = await backfill([CASE_A], [], MemoryStore((CASE_A, files)), repo, apply=True)
        assert actions == [Action(CASE_A, "skipped", detail)]
        repo.create_case.assert_not_awaited()

    async def test_a_manifest_under_another_prefix_inserts_nothing(self) -> None:
        repo = MagicMock(create_case=AsyncMock())
        actions = await backfill([CASE_B], [], MemoryStore((CASE_B, stored(CASE_A))), repo, apply=True)
        assert actions == [Action(CASE_B, "skipped", f"manifest id {CASE_A} differs from its object prefix {CASE_B}")]
        repo.create_case.assert_not_awaited()

    async def test_a_prefix_that_is_no_case_id_is_left_alone(self) -> None:
        store = MemoryStore(("misc", {"note.txt": b"x"}))
        assert await backfill(store.list_case_ids(), [], store, MagicMock(), apply=True) == [
            Action("misc", "skipped", "not a case id; left alone")
        ]
        assert store.downloads == []

    async def test_a_failed_insert_rolls_back_and_the_next_case_goes_on(self) -> None:
        store = MemoryStore((CASE_A, stored(CASE_A)), (CASE_B, stored(CASE_B)))
        duplicate = IntegrityError("INSERT INTO agent_feedback", {}, Exception("duplicate key value (id)"))
        repo = MagicMock(
            session=MagicMock(rollback=AsyncMock()),
            create_case=AsyncMock(side_effect=[duplicate, SimpleNamespace(superseded_by=None)]),
        )

        actions = await backfill(store.list_case_ids(), [], store, repo, apply=True)

        assert actions == [
            Action(CASE_A, "failed", "IntegrityError: (builtins.Exception) duplicate key value (id)"),
            Action(CASE_B, "backfill", "inserted"),
        ]
        repo.session.rollback.assert_awaited_once()
        assert report(actions, backfill_run=True, apply=True).endswith("failed 1, backfill 1 (applied)")

    async def test_a_bucket_error_fails_one_case(self) -> None:
        store = MemoryStore((CASE_A, stored(CASE_A)), (CASE_B, stored(CASE_B)))
        store.failing.add(CASE_A)
        actions = await backfill(store.list_case_ids(), [], store, MagicMock(), apply=False)
        assert [(action.case_id, action.kind) for action in actions] == [(CASE_A, "failed"), (CASE_B, "backfill")]


class TestReport:
    def test_a_fixed_width_table_and_the_summary(self) -> None:
        actions = [
            Action(CASE_A, "written", ".cases/x: scatter-basic matplotlib, expected rejected"),
            Action(CASE_B, "backfill", "would insert (thumbs_up, bar-grouped seaborn, v1); run with --apply"),
        ]
        assert report(actions, backfill_run=True, apply=False).splitlines() == [
            "case id                    action    detail",
            f"{CASE_A}  written   .cases/x: scatter-basic matplotlib, expected rejected",
            f"{CASE_B}  backfill  would insert (thumbs_up, bar-grouped seaborn, v1); run with --apply",
            "written 1, kept 0, removed 0, skipped 0, unknown 0, failed 0, backfill 1 (dry run)",
        ]

    def test_nothing_to_do_is_one_summary_line_without_the_backfill(self) -> None:
        assert report([], backfill_run=False, apply=False) == (
            "written 0, kept 0, removed 0, skipped 0, unknown 0, failed 0"
        )


@pytest.fixture
def table(monkeypatch) -> SimpleNamespace:
    """A fake `agent_feedback` table behind `core.database.get_db_context`, for `main` and `run`."""
    state = SimpleNamespace(rows=[], inserted=[], opened=0, read_error=None)
    session = MagicMock(rollback=AsyncMock())

    @asynccontextmanager
    async def context():
        state.opened += 1
        yield session

    class Repository:
        def __init__(self, given) -> None:
            self.session = given

        async def list_all(self) -> list:
            if state.read_error is not None:
                raise state.read_error
            return list(state.rows)

        async def create_case(self, row: dict) -> SimpleNamespace:
            state.inserted.append(row)
            return SimpleNamespace(superseded_by=None)

    monkeypatch.setattr(core.database, "get_db_context", context)
    monkeypatch.setattr(core.database, "AgentFeedbackRepository", Repository)
    return state


class TestMain:
    def test_without_a_database_url_it_stops_before_any_import(self, tmp_path, monkeypatch, capsys) -> None:
        env_file = tmp_path / ".env"
        env_file.write_text("OTHER=1\n")
        monkeypatch.setattr(sync_cases, "_settings_refusal", MagicMock(side_effect=AssertionError("too far")))
        store = MemoryStore()

        assert main(["--env", str(env_file)], store=store) == 2

        assert capsys.readouterr().err.strip() == (
            f"sync_cases: DATABASE_URL is not set and {env_file} does not define it"
        )
        assert store.downloads == []

    def test_reads_only_the_database_url_from_the_env_file(self, tmp_path, table, cases, capsys) -> None:
        env_file = tmp_path / ".env"
        env_file.write_text(f"DATABASE_URL={SAFE_URL}\nENVIRONMENT=production\nINSTANCE_CONNECTION_NAME=p:r:i\n")

        assert main(["--env", str(env_file)], store=MemoryStore(), cases_dir=cases) == 0

        assert os.environ["DATABASE_URL"] == SAFE_URL
        assert os.environ["ENVIRONMENT"] == "script"
        assert "INSTANCE_CONNECTION_NAME" not in os.environ
        assert (os.environ["PYTHON_DOTENV_DISABLED"], os.environ["ADK_DISABLE_LOAD_DOTENV"]) == ("1", "1")
        assert capsys.readouterr().out.strip() == "written 0, kept 0, removed 0, skipped 0, unknown 0, failed 0"
        assert table.opened == 1
        core.database.close_db.assert_awaited_once()

    def test_an_exported_database_url_wins(self, tmp_path, table, cases, monkeypatch) -> None:
        monkeypatch.setenv("DATABASE_URL", SAFE_URL)
        env_file = tmp_path / ".env"
        env_file.write_text("DATABASE_URL=postgresql://other@localhost:1/other\n")
        assert main(["--env", str(env_file)], store=MemoryStore(), cases_dir=cases) == 0
        assert os.environ["DATABASE_URL"] == SAFE_URL

    def test_agent_settings_that_refuse_the_shell_stop_before_the_database(self, cases, monkeypatch, capsys) -> None:
        importlib.import_module("agents.anyplot.settings")  # imported under a valid environment first
        monkeypatch.setenv("DATABASE_URL", SAFE_URL)
        monkeypatch.setenv("AGENT_RENDERER", "local")
        store = MemoryStore()

        assert main([], store=store, cases_dir=cases) == 2

        err = capsys.readouterr().err
        assert "the agent settings refuse this shell environment: " in err
        assert "AGENT_RENDERER=local is allowed only when ENVIRONMENT=development, not 'script'" in err
        assert "unset the AGENT_* exports or run with ENVIRONMENT=development" in err
        assert store.downloads == []
        core.database.close_db.assert_not_awaited()

    def test_apply_needs_backfill(self, capsys) -> None:
        with pytest.raises(SystemExit) as exit_info:
            main(["--apply"])
        assert exit_info.value.code == 2
        assert "--apply inserts the rows that --backfill lists" in capsys.readouterr().err

    def test_a_full_run_with_a_dry_backfill(self, table, cases, monkeypatch, capsys) -> None:
        monkeypatch.setenv("DATABASE_URL", SAFE_URL)
        first, second, orphan = stored(CASE_A), stored(CASE_B), stored(CASE_C)
        store = MemoryStore((CASE_A, first), (CASE_B, second), (CASE_C, orphan))
        (cases / dir_name(CASE_B)).mkdir(parents=True)
        table.rows = [
            row_for(first, promoted_at=PROMOTED, expected="rejected"),
            row_for(second, promoted_at=PROMOTED, status="done"),
        ]

        assert main(["--backfill"], store=store, cases_dir=cases) == 0

        out = capsys.readouterr().out.splitlines()
        assert out[0] == "case id                    action    detail"
        assert out[1].startswith(f"{CASE_A}  written   .cases/{dir_name(CASE_A)}: scatter-basic matplotlib")
        assert out[2] == f"{CASE_B}  removed   retired (done)"
        assert out[3] == (
            f"{CASE_C}  backfill  would insert (thumbs_down, scatter-basic matplotlib, v2); run with --apply"
        )
        assert out[4] == "written 1, kept 0, removed 1, skipped 0, unknown 0, failed 0, backfill 1 (dry run)"
        assert table.inserted == []
        core.database.close_db.assert_awaited_once()

    def test_apply_inserts_and_says_so(self, table, cases, monkeypatch, capsys) -> None:
        monkeypatch.setenv("DATABASE_URL", SAFE_URL)
        files = stored(CASE_A)

        assert main(["--backfill", "--apply"], store=MemoryStore((CASE_A, files)), cases_dir=cases) == 0

        assert table.inserted == [row_from_manifest(manifest_of(files))]
        assert capsys.readouterr().out.splitlines()[-1].endswith("backfill 1 (applied)")

    def test_a_skipped_case_exits_1(self, table, cases, monkeypatch, capsys) -> None:
        monkeypatch.setenv("DATABASE_URL", SAFE_URL)
        files = stored(reaction="bug")
        table.rows = [row_for(files, promoted_at=PROMOTED)]

        assert main([], store=MemoryStore((CASE_A, files)), cases_dir=cases) == 1
        assert "skipped 1" in capsys.readouterr().out

    def test_an_unreadable_table_exits_1_and_disposes_the_engine(self, table, cases, monkeypatch, capsys) -> None:
        monkeypatch.setenv("DATABASE_URL", SAFE_URL)
        table.read_error = OperationalError("SELECT agent_feedback.id", {}, Exception("connection refused"))

        assert main([], store=MemoryStore(), cases_dir=cases) == 1

        err = capsys.readouterr().err
        assert err.startswith("sync_cases: cannot read the agent_feedback table: OperationalError: ")
        assert "nobody:none" not in err
        core.database.close_db.assert_awaited_once()

    def test_a_bucket_that_cannot_be_listed_fails_the_backfill(self, table, cases, monkeypatch, capsys) -> None:
        monkeypatch.setenv("DATABASE_URL", SAFE_URL)
        store = MemoryStore()
        store.list_error = ServiceUnavailable("no listing")

        assert main(["--backfill"], store=store, cases_dir=cases) == 1

        out = capsys.readouterr().out.splitlines()
        assert out[1] == f"{'cases/':<25}  failed    ServiceUnavailable: 503 no listing"
        assert table.opened == 1  # the rows only: no backfill session without a listing
        core.database.close_db.assert_awaited_once()


class TestEnvironmentDefaults:
    def test_the_env_file_is_this_checkouts_own(self) -> None:
        assert DEFAULT_ENV_FILE == Path(sync_cases.__file__).resolve().parents[2] / ".env"
        assert (DEFAULT_ENV_FILE.parent / "pyproject.toml").is_file()

    def test_the_default_bucket_is_the_feedback_routes(self) -> None:
        assert DEFAULT_BUCKET == Settings.model_fields["agent_cases_bucket"].default

    def test_the_bucket_comes_from_the_flag_then_the_environment(self, monkeypatch) -> None:
        assert bucket_name(None) == DEFAULT_BUCKET
        monkeypatch.setenv("AGENT_CASES_BUCKET", "my-cases")
        assert bucket_name(None) == "my-cases"
        assert bucket_name("flag-cases") == "flag-cases"


class TestGcsCaseStore:
    def test_lists_the_case_prefixes(self) -> None:
        class Blobs:
            """The library's iterator: `prefixes` fills only while it is consumed."""

            def __init__(self) -> None:
                self.prefixes: set[str] = set()

            def __iter__(self):
                self.prefixes = {f"cases/{CASE_B}/", f"cases/{CASE_A}/"}
                return iter([])

        client = MagicMock()
        client.list_blobs.return_value = Blobs()
        store = GcsCaseStore("anyplot-agent-cases")
        store._client = client

        assert store.list_case_ids() == [CASE_A, CASE_B]
        client.list_blobs.assert_called_once_with("anyplot-agent-cases", prefix="cases/", delimiter="/")

    def test_downloads_one_case_file(self) -> None:
        client = MagicMock()
        client.bucket.return_value.blob.return_value.download_as_bytes.return_value = b"{}"
        store = GcsCaseStore("anyplot-agent-cases")
        store._client = client

        assert store.download(CASE_A, "manifest.json") == b"{}"
        client.bucket.assert_called_with("anyplot-agent-cases")
        client.bucket.return_value.blob.assert_called_with(f"cases/{CASE_A}/manifest.json")

    def test_a_missing_object_is_none_and_other_errors_raise(self) -> None:
        client = MagicMock()
        download = client.bucket.return_value.blob.return_value.download_as_bytes
        store = GcsCaseStore("anyplot-agent-cases")
        store._client = client

        download.side_effect = NotFound("gone")
        assert store.download(CASE_A, "plot-dark.png") is None
        download.side_effect = ServiceUnavailable("down")
        with pytest.raises(ServiceUnavailable):
            store.download(CASE_A, "manifest.json")

    def test_the_client_is_created_on_first_use(self) -> None:
        """The autouse fixture makes creating a client fail; constructing the store must not."""
        GcsCaseStore("anyplot-agent-cases")
