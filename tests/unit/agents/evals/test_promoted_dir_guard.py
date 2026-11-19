"""No test reads the real promoted directory, `agents/evals/.cases/`, which holds visitors' data.

Two parts hold that: every eval test's `PROMOTED_DIR` is an empty temporary directory (`conftest.no_promoted_cases`),
and `import_case.guard_promoted_dir` refuses the real one, in any spelling and whether it comes from the default or a
caller, in any process that runs tests, before anything reads it. These tests never name, list or stat the real
directory: a marker case under `tmp_path` stands in for it, by pointing `import_case.EVALS_DIR`, from which the guard
derives the real location, at `tmp_path`.
"""

import json
import os
import subprocess
import sys
from collections.abc import Callable
from pathlib import Path
from typing import Any
from unittest.mock import patch

import pytest

import core.database
from agents.evals import import_case, matrix, sync_cases
from agents.evals.cases import load_cases
from agents.evals.import_case import ImportedCase, RealCasesUnderTest
from agents.evals.matrix import EXIT_SETUP


MARKER = "case-invented-marker"
REPO_ROOT = Path(__file__).resolve().parents[4]


@pytest.fixture
def stand_in_real(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """`tmp_path/evals/.cases` as the real promoted directory, with one marker case in it; `PROMOTED_DIR` stays the
    autouse fixture's empty directory."""
    root = tmp_path / "evals"
    marker = root / ".cases" / MARKER
    marker.mkdir(parents=True)
    fields = {"spec_id": "scatter-basic", "library": "matplotlib", "expected": "rejected", "tags": ["imported"]}
    (marker / "case.json").write_text(json.dumps(fields), encoding="utf-8")
    (marker / "data.csv").write_text("a,b\n1,2\n", encoding="utf-8")
    monkeypatch.setattr(import_case, "EVALS_DIR", root)
    return root / ".cases"


@pytest.fixture
def no_database(monkeypatch: pytest.MonkeyPatch) -> None:
    """The sync never reaches a database, even under a mutation of the guard."""

    def refuse(*args: object, **kwargs: object) -> None:
        raise AssertionError("a guard test tried to open a database")

    monkeypatch.setattr(core.database, "get_db_context", refuse)


class EmptyStore:
    def list_case_ids(self) -> list[str]:
        return []

    def download(self, case_id: str, name: str) -> bytes | None:
        return None


IMPORTED = ImportedCase(
    case={"spec_id": "scatter-basic", "library": "matplotlib", "bindings": [], "expected": "rejected", "tags": []},
    data_csv="a,b\n1,2\n",
    change_request=None,
    notes=[],
)


def test_the_suites_loaders_read_the_empty_directory_not_the_real_one(
    tmp_path: Path, stand_in_real: Path, no_promoted_cases: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    assert import_case.promoted_cases_dir() == no_promoted_cases != stand_in_real
    assert list(no_promoted_cases.iterdir()) == []
    assert load_cases(fixtures_dir=tmp_path / "no-fixtures") == []
    # The run the matrix tests made through the default: the marker is not among the cases it can select.
    with patch.dict(os.environ):
        assert matrix.main(["--cases", f"{MARKER}*", "--static", "--out", str(tmp_path / "out")]) == EXIT_SETUP
    assert f"no case matches --cases '{MARKER}*'" in capsys.readouterr().err


def test_a_test_that_reaches_the_real_default_fails_before_any_read(
    tmp_path: Path, stand_in_real: Path, monkeypatch: pytest.MonkeyPatch, no_database: None
) -> None:
    """Undo the fixture, as a test outside it would run: every default use of the directory refuses, and the marker
    case is never loaded. The two `matrix.main` calls are those of the tests that read the default before; the
    `write_case` and `sync_cases.main` defaults are the two the first version of this test missed."""
    monkeypatch.setattr(import_case, "PROMOTED_DIR", stand_in_real)
    monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://nobody:none@localhost:1/none")

    with pytest.raises(RealCasesUnderTest, match="it is the real agents/evals/.cases/"):
        import_case.promoted_cases_dir()
    with pytest.raises(RealCasesUnderTest):
        load_cases(fixtures_dir=tmp_path / "no-fixtures")
    with pytest.raises(RealCasesUnderTest):
        import_case.write_case("case-invented-written", IMPORTED, fixtures_dir=tmp_path / "no-fixtures")
    with patch.dict(os.environ), pytest.raises(RealCasesUnderTest):
        sync_cases.main(["--env", str(tmp_path / "no.env")], store=EmptyStore())
    out = str(tmp_path / "out")
    for argv in (
        ["--cases", "stress-over-*,stress-single-row", "--static", "--out", out],
        ["--cases", "no-such-case-*", "--renderer", "fake", "--out", out],
    ):
        with patch.dict(os.environ), pytest.raises(RealCasesUnderTest):
            matrix.main(argv)
    assert [path.name for path in stand_in_real.iterdir()] == [MARKER]  # nothing was written into it either


ALIASES: dict[str, Callable[[Path, Path], Any]] = {
    "dot": lambda real, tmp: real.parent / "." / ".cases",
    "dotdot": lambda real, tmp: real.parent / "sub" / ".." / ".cases",
    "relative": lambda real, tmp: Path(os.path.relpath(real)),
    "string": lambda real, tmp: str(real),
    "inside": lambda real, tmp: real / MARKER,
    "symlink": lambda real, tmp: _link(tmp / "link-to-cases", real),
    "symlinked-parent": lambda real, tmp: _link(tmp / "link-to-evals", real.parent) / ".cases",
}


def _link(link: Path, target: Path) -> Path:
    link.symlink_to(target, target_is_directory=True)
    return link


@pytest.mark.parametrize("alias", sorted(ALIASES))
def test_any_spelling_of_the_real_directory_is_refused(
    tmp_path: Path, stand_in_real: Path, monkeypatch: pytest.MonkeyPatch, no_database: None, alias: str
) -> None:
    value = ALIASES[alias](stand_in_real, tmp_path)

    monkeypatch.setattr(import_case, "PROMOTED_DIR", value)
    with pytest.raises(RealCasesUnderTest):
        import_case.promoted_cases_dir()
    monkeypatch.setattr(import_case, "PROMOTED_DIR", tmp_path / "elsewhere")
    with pytest.raises(RealCasesUnderTest):
        load_cases(fixtures_dir=tmp_path / "no-fixtures", promoted_dir=value)
    with pytest.raises(RealCasesUnderTest):
        import_case.write_case("case-invented-x", IMPORTED, promoted_dir=Path(value), fixtures_dir=tmp_path / "none")
    with pytest.raises(RealCasesUnderTest):
        sync_cases.sync([], EmptyStore(), Path(value), force=False)


def test_a_directory_a_test_names_is_used_as_named(tmp_path: Path, stand_in_real: Path) -> None:
    """The guard refuses only the real directory: a test's own promoted directory still loads."""
    own = tmp_path / "own"
    (own / MARKER).mkdir(parents=True)
    for name in ("case.json", "data.csv"):
        (own / MARKER / name).write_bytes((stand_in_real / MARKER / name).read_bytes())

    (case,) = load_cases(fixtures_dir=tmp_path / "no-fixtures", promoted_dir=own)

    assert (case.case_id, case.origin) == (MARKER, "promoted")


CHILD = """
import json, sys
from pathlib import Path
sys.path.insert(0, sys.argv[1])
from agents.evals import import_case
import_case.EVALS_DIR = Path(sys.argv[2])
import_case.PROMOTED_DIR = Path(sys.argv[2]) / ".cases"
out = {"pytest_imported": "pytest" in sys.modules}
try:
    import_case.promoted_cases_dir()
    out["refused"] = False
except import_case.RealCasesUnderTest:
    out["refused"] = True
print(json.dumps(out))
"""


@pytest.mark.parametrize(("marker", "refused"), [(True, True), (False, False)])
def test_a_process_a_test_starts_is_refused_too(stand_in_real: Path, marker: bool, refused: bool) -> None:
    """A child process has not imported pytest, but inherits `PYTEST_CURRENT_TEST` from the test that started it. Without
    the marker, as outside any test, the path is handed out; the child compares paths and reads nothing."""
    environ = {key: value for key, value in os.environ.items() if key != "PYTEST_CURRENT_TEST"}
    if marker:
        environ["PYTEST_CURRENT_TEST"] = os.environ["PYTEST_CURRENT_TEST"]
    done = subprocess.run(
        [sys.executable, "-c", CHILD, str(REPO_ROOT), str(stand_in_real.parent)],
        capture_output=True,
        text=True,
        check=True,
        env=environ,
    )

    assert json.loads(done.stdout) == {"pytest_imported": False, "refused": refused}
