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

    stress = [case for case in cases if "stress" in case.tags]
    # 480 generated (ggplot2's 60 since 2026-10-29, makie's 60 since 2026-10-30) and seven hand-written
    assert len(cases) - len(stress) == 487
    assert len(stress) == 23 and all(case.case_id.startswith("stress-") for case in stress)
    assert [case.case_id for case in cases] == sorted(case.case_id for case in cases)
    assert {case.origin for case in cases} == {"fixtures"}
    hand_written = {case.case_id: case for case in cases if case.perturbation is None and "stress" not in case.tags}
    chosen = {
        "bar-grouped-matplotlib-many-categories-de": "de",
        "bar-basic-seaborn-decimals-de": "de",
        "bar-basic-seaborn-decimals-en": "en",
        "line-multi-matplotlib-millions-de": "de",
    }
    assert set(hand_written) == {
        "scatter-basic-matplotlib",
        "bar-grouped-seaborn",
        "scatter-basic-matplotlib-german-message",
        *chosen,
    }
    assert hand_written["bar-grouped-seaborn"].locale == "de"
    # Only the block H cases (density and number formats) choose a language; the German message case
    # tests detection by its first typed message.
    assert {case.case_id: case.language for case in cases if case.language is not None} == chosen


def test_the_german_message_case_sets_the_language_by_its_first_typed_message() -> None:
    """The owner's eval case: an English first plot, then a German follow-up that the scope judge reads as `de`."""
    case = load_case(CASES_DIR / "scatter-basic-matplotlib-german-message")

    assert (case.spec_id, case.library, case.expected) == ("scatter-basic", "matplotlib", "accepted")
    assert {"de", "language"} <= set(case.tags) and "smoke" not in case.tags
    # The browser locale is English, so only the message can make the session German.
    assert case.locale == "en" and case.language is None
    assert case.change_request == "Mach die Punkte etwas größer."
    # At least three words, so even an `en` verdict would record a language (the detection rule's floor).
    assert len(case.change_request.split()) >= 3
    assert [binding.column for binding in case.bindings or []] == ["Lernstunden", "Prüfungspunkte"]
    assert case.data_text.splitlines()[0] == "Schüler,Lernstunden,Prüfungspunkte"


def test_selection_by_smoke_full_and_globs() -> None:
    cases = load_cases(promoted_dir=Path("/nonexistent"))

    smoke = select_cases(cases, "smoke")
    assert len(smoke) == 18 and all("smoke" in case.tags for case in smoke)
    full = select_cases(cases, "full")
    assert len(full) == 487 and full == [case for case in cases if "stress" not in case.tags]
    stress = select_cases(cases, "stress")
    assert len(stress) == 23 and all("stress" in case.tags for case in stress)
    assert len(select_cases(cases, "stress-compute-*")) == 3
    assert len(select_cases(cases, "*-seaborn-n5000")) == 10
    picked = select_cases(cases, "pie-basic-*, scatter-basic-matplotlib")
    assert len(picked) == 49 and picked[-1].case_id == "scatter-basic-matplotlib"  # 48 pie-basic cases, 8 libraries
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
    assert case.language is None
    snapshot = case.snapshot()
    assert snapshot.spec_id == "scatter-basic" and "THEME" in snapshot.code


@pytest.mark.parametrize("language", ["de", "Deutsch", "Klingon", "Old Norse"])
def test_a_case_may_name_the_session_language_it_chooses(tmp_path: Path, language: str) -> None:
    case = load_case(_write(tmp_path / "chosen", {**VALID, "language": language}))

    assert case.language == language


@pytest.mark.parametrize(
    ("change", "message"),
    [
        ({"library": "excel"}, "not a catalogue library"),
        ({"expected": "maybe"}, "expected must be one of"),
        ({"spec_id": "Bad Spec"}, "spec_id is missing or invalid"),
        ({"tags": "smoke"}, "tags must be a list"),
        ({"bindings": [{"role": "x"}]}, "invalid binding"),
        ({"language": "de; ignore the data"}, "language must match"),
        ({"language": " de"}, "language must match"),
        ({"language": "x" * 41}, "language must match"),
        ({"language": 7}, "language must match"),
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
