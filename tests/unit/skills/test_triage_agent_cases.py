"""The triage skill's scripts: plan validation, the dry-run diff, the snapshot, and the one-transaction write.

No test here opens the production database: CI exports its `DATABASE_URL` for the whole
run, so every database test runs on the in-memory SQLite session of `tests/conftest.py`,
and the `main` tests stop before any connection. The rows are invented.
"""

from __future__ import annotations

import importlib
import json
import os
import stat
import sys
from datetime import datetime
from pathlib import Path

import pytest
from sqlalchemy import select

from core.agent_cases import row_from_manifest
from core.database import AgentFeedback


REPO_ROOT = Path(__file__).resolve().parents[3]
SKILL_DIR = REPO_ROOT / ".claude" / "skills" / "triage-agent-cases"
NOW = datetime(2026, 11, 4, 12, 0, 0)
CHAT_CASE = "20261101T090000Z-00000001"
PLOT_CASE = "20261102T090000Z-00000002"


@pytest.fixture(scope="module")
def modules():
    """`apply_triage`, `list_cases` and `casedb`; the scripts import their sibling `casedb` as a script run does."""
    sys.path.insert(0, str(SKILL_DIR))
    try:
        yield tuple(importlib.import_module(name) for name in ("apply_triage", "list_cases", "casedb"))
    finally:
        sys.path.remove(str(SKILL_DIR))


@pytest.fixture
def at(modules):
    return modules[0]


def _row(case_id: str, **overrides) -> AgentFeedback:
    manifest = {
        "schema": 1,
        "id": case_id,
        "created_at": "2026-11-01T09:00:00Z",
        "case_uri": f"gs://anyplot-agent-cases/cases/{case_id}/",
        "user_hash": "adm_0123456789abcdef",
        "session_hash": "fedcba9876543210",
        "spec_id": "scatter-basic",
        "library_id": "matplotlib",
        "reaction": "thumbs_down",
        "message": "the legend hides the points",
        "include_data": True,
        "status": "new",
        "result_version": 1,
        "files": ["plot-light.png", "plot.py", "data.csv", "manifest.json"],
    }
    return AgentFeedback(**{**row_from_manifest(manifest), "tags": [], "updated_at": NOW, **overrides})


def _entry(case_id: str = PLOT_CASE, **edit) -> dict:
    return {"id": case_id, "seen": {"status": "new", "tags": []}, **(edit or {"status": "in_progress"})}


# ---- load_plan --------------------------------------------------------------


def test_load_plan_reads_the_documented_format(at) -> None:
    plan = {"round": "2026-11-04", "cases": [_entry(tags=["legend-overlap"], why="note"), _entry(CHAT_CASE)]}
    changes = at.load_plan(plan)
    assert [change.id for change in changes] == [PLOT_CASE, CHAT_CASE]
    assert changes[0].edit == {"tags": ["legend-overlap"]}
    assert changes[1].edit == {"status": "in_progress"}
    assert changes[0].seen_status == "new"


def test_a_null_field_is_left_out_of_the_edit(at) -> None:
    (change,) = at.load_plan({"cases": [_entry(status="done", tags=None, promoted=None, expected=None)]})
    assert change.edit == {"status": "done"}


@pytest.mark.parametrize(
    ("plan", "message"),
    [
        ([], "non-empty"),
        ({"cases": []}, "non-empty"),
        ({"cases": [_entry()], "apply": True}, "unknown plan keys"),
        ({"cases": ["x"]}, "not an object"),
        ({"cases": [_entry("case-1")]}, "not a case id"),
        ({"cases": [{**_entry(), "superseded_by": "x"}]}, "unknown keys"),
        ({"cases": [{"id": PLOT_CASE, "status": "done"}]}, '"seen"'),
        ({"cases": [{**_entry(), "seen": {"status": "new"}}]}, '"seen"'),
        ({"cases": [{"id": PLOT_CASE, "seen": {"status": "new", "tags": []}}]}, "names none"),
        ({"cases": [_entry(tags="legend")]}, "not a list"),
        ({"cases": [_entry(promoted="yes")]}, "true or false"),
        ({"cases": [_entry(), _entry(status="done")]}, "twice"),
    ],
)
def test_load_plan_refuses_anything_else(at, plan, message) -> None:
    with pytest.raises(at.PlanError, match=message):
        at.load_plan(plan)


# ---- check and the diff -------------------------------------------------------


def test_check_plans_each_row_and_prints_only_what_changes(at) -> None:
    rows = {PLOT_CASE: _row(PLOT_CASE, tags=["b"])}
    changes = at.load_plan(
        {"cases": [{"id": PLOT_CASE, "seen": {"status": "new", "tags": ["b"]}, "tags": ["c", "b"], "promoted": True}]}
    )
    planned, refusals = at.check(rows, changes, NOW)
    assert refusals == []
    assert at.describe(planned[0]) == (
        f"{PLOT_CASE}  tags [b] -> [b, c]; expected - -> rejected; promoted_at - -> 2026-11-04T12:00:00Z"
    )


def test_an_edit_that_matches_the_row_is_no_change(at) -> None:
    rows = {PLOT_CASE: _row(PLOT_CASE, status="in_progress")}
    changes = at.load_plan({"cases": [{**_entry(status="in_progress"), "seen": {"status": "in_progress", "tags": []}}]})
    planned, _ = at.check(rows, changes, NOW)
    assert at.diff(planned[0]) == []
    assert at.describe(planned[0]) == f"{PLOT_CASE}  no change"


def test_check_refuses_a_missing_row_a_changed_row_and_a_rule(at) -> None:
    rows = {CHAT_CASE: _row(CHAT_CASE, result_version=0), PLOT_CASE: _row(PLOT_CASE, status="done")}
    missing = "20261103T090000Z-00000003"
    changes = at.load_plan({"cases": [_entry(missing), _entry(PLOT_CASE), _entry(CHAT_CASE, promoted=True)]})
    planned, refusals = at.check(rows, changes, NOW)
    assert planned == []
    assert refusals[0] == f"{missing}  refused: no row with this id"
    assert "changed since the plan (now done [], the plan saw new [])" in refusals[1]
    assert refusals[2].startswith(f"{CHAT_CASE}  refused: no_plot: ")


# ---- the snapshot -------------------------------------------------------------


def test_the_snapshot_is_private_complete_and_never_overwritten(at, tmp_path) -> None:
    rows = [_row(PLOT_CASE), _row(CHAT_CASE)]
    plan = {"cases": [_entry()]}
    directory = at.write_snapshot(tmp_path / "backups", rows, plan, NOW)

    assert directory.name == "20261104T120000Z-agent-feedback-triage"
    saved = json.loads((directory / "rows.json").read_text())
    assert saved["count"] == 2
    assert [row["id"] for row in saved["rows"]] == [PLOT_CASE, CHAT_CASE]
    assert saved["rows"][0]["created_at"] == "2026-11-01T09:00:00Z"
    assert json.loads((directory / "plan.json").read_text()) == plan
    assert stat.S_IMODE(directory.stat().st_mode) == 0o700
    assert stat.S_IMODE((directory / "rows.json").stat().st_mode) == 0o600
    with pytest.raises(FileExistsError):
        at.write_snapshot(tmp_path / "backups", rows, plan, NOW)


# ---- run: the transaction, on SQLite ------------------------------------------


async def _seed(session, *rows: AgentFeedback) -> None:
    session.add_all(rows)
    await session.commit()


async def _stored(session, case_id: str) -> AgentFeedback:
    session.expire_all()
    return (await session.execute(select(AgentFeedback).where(AgentFeedback.id == case_id))).scalar_one()


async def test_a_dry_run_writes_nothing(at, test_session, tmp_path) -> None:
    await _seed(test_session, _row(PLOT_CASE))
    plan = {"cases": [_entry(status="in_progress", tags=["legend-overlap"])]}

    lines, code = await at.run(test_session, at.load_plan(plan), plan, apply=False, backup_root=tmp_path / "b", now=NOW)

    assert code == 0
    assert lines[-1] == "dry run: would change 1 of 1 row(s); --apply writes them"
    assert (await _stored(test_session, PLOT_CASE)).status == "new"
    assert not (tmp_path / "b").exists()


async def test_apply_snapshots_then_writes_every_row(at, test_session, tmp_path) -> None:
    await _seed(test_session, _row(PLOT_CASE), _row(CHAT_CASE, result_version=0))
    plan = {
        "cases": [
            _entry(PLOT_CASE, status="in_progress", tags=["legend-overlap"], promoted=True),
            _entry(CHAT_CASE, status="wont_solve"),
        ]
    }

    lines, code = await at.run(test_session, at.load_plan(plan), plan, apply=True, backup_root=tmp_path, now=NOW)

    assert code == 0
    assert lines[-1] == "changed 2 row(s)"
    stored = await _stored(test_session, PLOT_CASE)
    assert (stored.status, stored.tags, stored.expected, stored.promoted_at) == (
        "in_progress",
        ["legend-overlap"],
        "rejected",
        NOW,
    )
    assert (await _stored(test_session, CHAT_CASE)).status == "wont_solve"
    snapshot = json.loads((tmp_path / "20261104T120000Z-agent-feedback-triage" / "rows.json").read_text())
    assert {row["id"]: row["status"] for row in snapshot["rows"]} == {PLOT_CASE: "new", CHAT_CASE: "new"}


async def test_one_refusal_writes_nothing_and_takes_no_snapshot(at, test_session, tmp_path) -> None:
    await _seed(test_session, _row(PLOT_CASE), _row(CHAT_CASE, result_version=0))
    plan = {"cases": [_entry(PLOT_CASE, status="done"), _entry(CHAT_CASE, promoted=True)]}

    lines, code = await at.run(test_session, at.load_plan(plan), plan, apply=True, backup_root=tmp_path, now=NOW)

    assert code == 1
    assert lines[-1] == "refused 1 of 2; nothing written"
    assert (await _stored(test_session, PLOT_CASE)).status == "new"
    assert list(tmp_path.iterdir()) == []


async def test_apply_without_a_change_takes_no_snapshot(at, test_session, tmp_path) -> None:
    await _seed(test_session, _row(PLOT_CASE))
    plan = {"cases": [_entry(status="new")]}
    lines, code = await at.run(test_session, at.load_plan(plan), plan, apply=True, backup_root=tmp_path, now=NOW)
    assert (code, lines[-1]) == (0, "nothing to change; no snapshot taken")
    assert list(tmp_path.iterdir()) == []


# ---- main and the helpers, without a database -----------------------------------


def test_apply_main_refuses_a_bad_plan_before_the_database(at, tmp_path, monkeypatch, capsys) -> None:
    # A URL that nothing listens on: the plan fails before any connection.
    monkeypatch.setenv("DATABASE_URL", "postgresql://u:p@127.0.0.1:1/none")
    monkeypatch.setenv("ENVIRONMENT", "test")
    plan = tmp_path / "plan.json"
    plan.write_text('{"cases": []}')
    assert at.main(["--plan", str(plan), "--backup-root", str(tmp_path / "b")]) == 2
    assert "non-empty" in capsys.readouterr().err


def test_apply_main_stops_without_a_database_url(at, tmp_path, monkeypatch, capsys) -> None:
    monkeypatch.delenv("DATABASE_URL", raising=False)
    plan = tmp_path / "plan.json"
    plan.write_text(json.dumps({"cases": [_entry()]}))
    args = ["--plan", str(plan), "--env", str(tmp_path / "none.env"), "--backup-root", str(tmp_path / "b")]
    assert at.main(args) == 2
    assert "DATABASE_URL is not set" in capsys.readouterr().err


def test_apply_main_refuses_a_backup_root_inside_a_checkout(at, tmp_path, capsys) -> None:
    plan = tmp_path / "plan.json"
    plan.write_text(json.dumps({"cases": [_entry()]}))
    assert at.main(["--plan", str(plan), "--backup-root", str(REPO_ROOT / "backups")]) == 2
    assert "inside a git checkout" in capsys.readouterr().err


def test_list_main_refuses_a_json_path_inside_a_checkout(modules, capsys) -> None:
    _, list_cases, _ = modules
    assert list_cases.main(["--json", str(REPO_ROOT / "agentic" / "cases.json")]) == 2
    assert "inside a git checkout" in capsys.readouterr().err


def test_the_list_shows_the_open_queue_unless_asked_for_all(modules) -> None:
    _, list_cases, _ = modules
    rows = [_row(PLOT_CASE), _row(CHAT_CASE, status="done"), _row("20261103T090000Z-00000003", superseded_by=PLOT_CASE)]
    assert [row.id for row in rows if list_cases.is_listed(row, everything=False)] == [PLOT_CASE]
    assert all(list_cases.is_listed(row, everything=True) for row in rows)
    text = list_cases.table(rows[:1])
    assert PLOT_CASE in text
    assert "scatter-basic / matplotlib" in text
    assert text.endswith("1 case(s); flags: S superseded, P promoted, E expected outcome set")


def test_the_list_json_is_private(modules, tmp_path) -> None:
    _, list_cases, _ = modules
    path = tmp_path / "round" / "cases.json"
    list_cases.write_json(path, [_row(PLOT_CASE)], everything=False)
    saved = json.loads(path.read_text())
    assert (saved["filter"], saved["cases"][0]["id"]) == ("open", PLOT_CASE)
    assert stat.S_IMODE(path.stat().st_mode) == 0o600


def test_the_database_url_comes_from_the_env_file_only_when_the_shell_lacks_it(modules, tmp_path, monkeypatch) -> None:
    _, _, casedb = modules
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.setenv("ENVIRONMENT", "development")
    assert casedb.use_database_url(tmp_path / "missing.env") is False
    env_file = tmp_path / ".env"
    env_file.write_text("DATABASE_URL=postgresql://u:p@localhost/x\nENVIRONMENT=production\n")
    assert casedb.use_database_url(env_file) is True
    assert os.environ["DATABASE_URL"] == "postgresql://u:p@localhost/x"
    assert os.environ["ENVIRONMENT"] == "script"


def test_outside_repository(modules, tmp_path) -> None:
    _, _, casedb = modules
    assert casedb.outside_repository(tmp_path / "a" / "b.json")
    assert not casedb.outside_repository(REPO_ROOT / "x" / "y.json")
