"""Eval case loading, validation and selection."""

import json
import shutil
from pathlib import Path

import pytest

from agents.anyplot.dev_fixture import CASES_DIR
from agents.evals.cases import CaseError, load_case, load_cases, select_cases


def _write(directory: Path, case: dict, data: str = "a,b\n1,2\n") -> Path:
    directory.mkdir(parents=True)
    (directory / "case.json").write_text(json.dumps(case))
    (directory / "data.csv").write_text(data)
    return directory


VALID = {
    "spec_id": "scatter-basic",
    "library": "matplotlib",
    "bindings": [{"role": "x", "column": "a"}, {"role": "y", "column": "b"}],
    "expected": "rejected",
    "tags": ["custom"],
}


def test_every_committed_case_loads() -> None:
    cases = load_cases(promoted_dir=Path("/nonexistent"))

    assert len(cases) == 122  # 120 generated plus the two hand-written cases
    assert [case.case_id for case in cases] == sorted(case.case_id for case in cases)
    assert {case.origin for case in cases} == {"fixtures"}
    hand_written = {case.case_id: case for case in cases if case.perturbation is None}
    assert set(hand_written) == {"scatter-basic-matplotlib", "bar-grouped-seaborn"}
    assert hand_written["bar-grouped-seaborn"].locale == "de"


def test_selection_by_smoke_full_and_globs() -> None:
    cases = load_cases(promoted_dir=Path("/nonexistent"))

    smoke = select_cases(cases, "smoke")
    assert len(smoke) == 12 and all("smoke" in case.tags for case in smoke)
    assert select_cases(cases, "full") == cases
    assert len(select_cases(cases, "*-seaborn-n5000")) == 10
    picked = select_cases(cases, "pie-basic-*, scatter-basic-matplotlib")
    assert len(picked) == 13 and picked[-1].case_id == "scatter-basic-matplotlib"
    assert select_cases(cases, "nothing-*") == []


def test_a_case_reads_its_fields_and_builds_its_snapshot(tmp_path: Path) -> None:
    directory = _write(tmp_path / "my-case", VALID)
    (directory / "change_request.txt").write_text("make the markers bigger\n")

    case = load_case(directory, "promoted")

    assert (case.case_id, case.spec_id, case.library, case.locale) == ("my-case", "scatter-basic", "matplotlib", "en")
    assert case.expected == "rejected" and case.tags == ("custom",) and case.origin == "promoted"
    assert [binding.column for binding in case.bindings or []] == ["a", "b"]
    assert case.change_request == "make the markers bigger"
    assert case.data_text == "a,b\n1,2\n"
    snapshot = case.snapshot()
    assert snapshot.spec_id == "scatter-basic" and "THEME" in snapshot.code


@pytest.mark.parametrize(
    ("change", "message"),
    [
        ({"library": "excel"}, "not a catalogue library"),
        ({"expected": "maybe"}, "expected must be one of"),
        ({"spec_id": "Bad Spec"}, "spec_id is missing or invalid"),
        ({"tags": "smoke"}, "tags must be a list"),
        ({"bindings": [{"role": "x"}]}, "invalid binding"),
    ],
)
def test_invalid_fields_are_refused(tmp_path: Path, change: dict, message: str) -> None:
    directory = _write(tmp_path / "bad-case", {**VALID, **change})

    with pytest.raises(CaseError, match=message):
        load_case(directory)


def test_missing_files_and_bad_ids_are_refused(tmp_path: Path) -> None:
    directory = tmp_path / "no-data"
    directory.mkdir()
    (directory / "case.json").write_text(json.dumps(VALID))
    with pytest.raises(CaseError, match="case.json and data.csv"):
        load_case(directory)
    with pytest.raises(CaseError, match="not a case id"):
        load_case(_write(tmp_path / "Upper_Case", VALID))


def test_promoted_cases_join_and_may_not_shadow_a_fixture(tmp_path: Path) -> None:
    fixtures, promoted = tmp_path / "fixtures", tmp_path / ".cases"
    shutil.copytree(CASES_DIR / "scatter-basic-matplotlib", fixtures / "scatter-basic-matplotlib")
    _write(promoted / "user-case-1", VALID)

    cases = load_cases(fixtures, promoted)
    assert [(case.case_id, case.origin) for case in cases] == [
        ("scatter-basic-matplotlib", "fixtures"),
        ("user-case-1", "promoted"),
    ]
    shutil.copytree(fixtures / "scatter-basic-matplotlib", promoted / "scatter-basic-matplotlib")
    with pytest.raises(CaseError, match="exists in both"):
        load_cases(fixtures, promoted)
