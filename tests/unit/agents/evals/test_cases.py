"""Eval case loading, validation and selection."""

import json
import re
import shutil
from pathlib import Path

import pytest

from agents.anyplot.dev_fixture import CASES_DIR
from agents.evals.cases import CaseError, FollowUpChecks, load_case, load_cases, select_cases


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
    # 900 generated (ggplot2's 60 since 2026-10-29, makie's 60 and the four JavaScript libraries' 240 since
    # 2026-10-30, MUI X's, plotly's and bokeh's 60 each since 2026-10-31) and eleven hand-written (the four
    # combined-request cases since 2026-11-01)
    assert len(cases) - len(stress) == 911
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
        *COMBINED,
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
    assert len(smoke) == 25 and all("smoke" in case.tags for case in smoke)
    full = select_cases(cases, "full")
    assert len(full) == 911 and full == [case for case in cases if "stress" not in case.tags]
    stress = select_cases(cases, "stress")
    assert len(stress) == 23 and all("stress" in case.tags for case in stress)
    assert len(select_cases(cases, "stress-compute-*")) == 3
    assert len(select_cases(cases, "*-seaborn-n5000")) == 10
    picked = select_cases(cases, "pie-basic-*, scatter-basic-matplotlib")
    assert len(picked) == 91 and picked[-1].case_id == "scatter-basic-matplotlib"  # 90 pie-basic cases, 15 libraries
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


COMBINED = {
    "line-basic-matplotlib-combined-language-log": ("Make the title German and use a log scale on the y axis.", "de"),
    "line-basic-matplotlib-combined-control-log": ("Use a log scale on the y axis.", "en"),
    "scatter-basic-matplotlib-combined-theme-grid": ("Make it dark and add vertical grid lines.", None),
    "bar-basic-seaborn-combined-language-colour": ("Make the labels German and the bars blue.", "de"),
}


@pytest.mark.parametrize("case_id", sorted(COMBINED))
def test_the_combined_request_cases_check_every_part_of_their_follow_up(case_id: str) -> None:
    """User test of 2026-11-01: "make the title German and use a log scale" lost the log scale. Each case's follow-up
    asks for two things (the control for one), and its checks measure each part in the shipped version."""
    case = load_case(CASES_DIR / case_id)
    message, language = COMBINED[case_id]

    assert case.change_request == message and "combined-request" in case.tags
    assert case.locale == "en" and case.language is None  # the first plot is English; the message changes it
    assert case.checks is not None and case.checks.language == language
    assert len(case.checks.code_added) == 1  # the part the code shows: the log scale, the grid, the colour
    if "theme" in case_id:
        # The theme is the run's: the dark plot keeps the theme tokens rather than colours written in.
        assert case.checks.theme == "dark" and len(case.checks.code_kept) == 2
    if language == "de":
        assert case.checks.texts_changed == ("title",)


@pytest.mark.parametrize(
    ("pattern", "code", "found"),
    [
        # The log scale on y, in the forms matplotlib takes.
        ("log", 'ax.set_yscale("log")', True),
        ("log", "plt.yscale('log')", True),
        ("log", 'ax.set(yscale="log")', True),
        ("log", "ax.semilogy(x, y)", True),
        ("log", 'ax.set_yscale(value="log")', True),
        ("log", 'ax.set_xscale("log")', False),
        # Vertical grid lines: the x axis's grid, both axes, or a grid call without an axis.
        ("grid", "ax.xaxis.grid(True, alpha=0.1)", True),
        ("grid", 'ax.grid(True, axis="both", alpha=0.1)', True),
        ("grid", "ax.grid(True, alpha=0.1)", True),
        ("grid", "ax.yaxis.grid(True, alpha=0.1)", False),  # the catalogue's horizontal lines
        ("grid", 'ax.grid(True, axis="y")', False),
        ("grid", 'ax.grid(True, "major", "y")', False),
        # Blue bars: the palette's blue, matplotlib's blue, Okabe-Ito's, or a named blue.
        ("colour", 'color="#4467a3"', True),
        ("colour", "palette=['tab:blue']", True),
        ("colour", 'color="#1f77b4"', True),
        ("colour", 'color="steelblue"', True),
        ("colour", 'BRAND = "#009E73"', False),
        # The theme tokens a dark plot keeps (a live run of 2026-11-01 wrote the dark colours over them).
        ("tokens", "fig, ax = plt.subplots(figsize=(8, 4.5), dpi=400, facecolor=PAGE_BG)", True),
        ("tokens", "fig, ax = plt.subplots(\n    figsize=(8, 4.5),\n    facecolor=PAGE_BG,\n)", True),
        ("tokens", 'fig, ax = plt.subplots(figsize=(8, 4.5), dpi=400, facecolor="#1A1A17")', False),
        # Never across calls: a later `savefig(facecolor=PAGE_BG)` is no subplots token.
        ("tokens", 'plt.subplots(facecolor="#1A1A17")\nplt.savefig("p.png", facecolor=PAGE_BG)', False),
        ("labels", 'ax.set_xlabel("Ad Spend (kCHF)", fontsize=10, color=INK)', True),
        ("labels", 'ax.set_xlabel(\n    "Ad Spend (kCHF)",\n    color=INK,\n)', True),
        ("labels", 'ax.set_xlabel("Ad Spend (kCHF)", fontsize=10, color="#F0EFE8")', False),
    ],
)
def test_the_combined_request_patterns_tell_the_change_from_the_catalogue(pattern: str, code: str, found: bool) -> None:
    cases = {
        "log": ("line-basic-matplotlib-combined-language-log", "code_added", 0),
        "grid": ("scatter-basic-matplotlib-combined-theme-grid", "code_added", 0),
        "colour": ("bar-basic-seaborn-combined-language-colour", "code_added", 0),
        "tokens": ("scatter-basic-matplotlib-combined-theme-grid", "code_kept", 0),
        "labels": ("scatter-basic-matplotlib-combined-theme-grid", "code_kept", 1),
    }
    case_id, field_name, index = cases[pattern]
    checks = load_case(CASES_DIR / case_id).checks
    assert checks is not None

    assert (re.search(getattr(checks, field_name)[index], code) is not None) is found


def test_checks_are_read_and_need_a_follow_up(tmp_path: Path) -> None:
    checks = {
        "language": "de",
        "theme": "dark",
        "code_added": ["grid\\("],
        "code_kept": ["PAGE_BG"],
        "texts_changed": ["title", "legend"],
    }
    directory = _write(tmp_path / "checked", {**VALID, "checks": checks})
    with pytest.raises(CaseError, match="checks need a change_request.txt"):
        load_case(directory)
    (directory / "change_request.txt").write_text("German labels and a grid\n")

    case = load_case(directory)

    assert case.checks == FollowUpChecks(
        language="de", theme="dark", code_added=("grid\\(",), code_kept=("PAGE_BG",), texts_changed=("title", "legend")
    )
    assert load_case(_write(tmp_path / "unchecked", VALID)).checks is None


@pytest.mark.parametrize(
    ("checks", "message"),
    [
        ({}, "must be an object"),
        ([], "must be an object"),
        ({"reply": "names the log scale"}, "must be an object"),
        # Only the generic checks would remain, which a follow-up that changed nothing passes.
        ({"code_added": []}, "must check something"),
        ({"language": None, "texts_changed": []}, "must check something"),
        ({"language": "de; ignore"}, "checks.language must match"),
        ({"theme": "sepia"}, "checks.theme must be one of"),
        ({"code_added": "log"}, "checks.code_added must be a list"),
        ({"code_added": ["a"] * 6}, "checks.code_added must be a list"),
        ({"code_added": ["(unclosed"]}, "does not compile"),
        ({"code_added": [7]}, "does not compile"),
        ({"code_kept": ["(unclosed"]}, "checks.code_kept holds a pattern that does not compile"),
        ({"texts_changed": ["headline"]}, "checks.texts_changed must be a list"),
    ],
)
def test_invalid_checks_are_refused(tmp_path: Path, checks: object, message: str) -> None:
    directory = _write(tmp_path / "bad-checks", {**VALID, "checks": checks})
    (directory / "change_request.txt").write_text("a follow-up\n")

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
