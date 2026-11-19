"""No test reads the real promoted directory, `agents/evals/.cases/`, which holds visitors' data.

Two parts hold that: every eval test's `PROMOTED_DIR` is an empty temporary directory (`conftest.no_promoted_cases`),
and `import_case.promoted_cases_dir` refuses the real one in any process that has imported pytest, before anything
reads it, so a test anywhere in the session that reaches the default without the fixture fails. These tests never
name, list or stat the real directory: a marker case under `tmp_path` stands in for it, by pointing
`import_case.EVALS_DIR`, from which the guard derives the real location, at `tmp_path`.
"""

import json
import os
from pathlib import Path
from unittest.mock import patch

import pytest

from agents.evals import import_case, matrix
from agents.evals.cases import load_cases
from agents.evals.import_case import RealCasesUnderTest
from agents.evals.matrix import EXIT_SETUP


MARKER = "case-invented-marker"


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
    tmp_path: Path, stand_in_real: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Undo the fixture, as a test outside it would run: every default use of the directory refuses, and the marker
    case is never loaded. The two `matrix.main` calls are those of the tests that read the default before."""
    monkeypatch.setattr(import_case, "PROMOTED_DIR", stand_in_real)

    with pytest.raises(RealCasesUnderTest, match="a test reached the real agents/evals/.cases/"):
        import_case.promoted_cases_dir()
    with pytest.raises(RealCasesUnderTest):
        load_cases(fixtures_dir=tmp_path / "no-fixtures")
    out = str(tmp_path / "out")
    for argv in (
        ["--cases", "stress-over-*,stress-single-row", "--static", "--out", out],
        ["--cases", "no-such-case-*", "--renderer", "fake", "--out", out],
    ):
        with patch.dict(os.environ), pytest.raises(RealCasesUnderTest):
            matrix.main(argv)


def test_a_directory_a_test_names_is_used_as_named(tmp_path: Path, stand_in_real: Path) -> None:
    """The guard refuses only the real directory: a test's own promoted directory, here the stand-in's, still loads."""
    (case,) = load_cases(fixtures_dir=tmp_path / "no-fixtures", promoted_dir=stand_in_real)

    assert (case.case_id, case.origin) == (MARKER, "promoted")
