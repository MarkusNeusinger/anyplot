"""Eval case loading, validation and selection."""

import csv
import io
import json
import re
import shutil
import statistics
from datetime import UTC, datetime
from pathlib import Path

import pytest

from agents.anyplot.dev_fixture import CASES_DIR
from agents.anyplot.grounding import GROUP_LIMITS
from agents.evals.cases import CaseError, FollowUpChecks, ViewChecks, load_case, load_cases, select_cases
from agents.evals.matrix import holds_token, view_tokens
from agents.evals.replay import NO_MODEL_CALL


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
KEEP_B: dict = {"op": "keep_rows", "where": [{"column": "b", "test": "eq", "value": 2}]}
"""A selection on `VALID`'s data: a view of the plot."""
B_ABOVE_1: dict = {"op": "keep_rows", "where": [{"column": "b", "test": "gt", "value": 1}]}
"""A selection by an order condition alone: a view with no word of its own."""


def test_every_committed_case_loads() -> None:
    cases = load_cases(promoted_dir=Path("/nonexistent"))

    stress = [case for case in cases if "stress" in case.tags]
    # 900 generated (ggplot2's 60 since 2026-10-29, makie's 60 and the four JavaScript libraries' 240 since
    # 2026-10-30, MUI X's, plotly's and bokeh's 60 each since 2026-10-31) and fifteen hand-written (the four
    # combined-request cases since 2026-11-01, the four view cases since 2026-11-16)
    assert len(cases) - len(stress) == 915
    assert len(stress) == 23 and all(case.case_id.startswith("stress-") for case in stress)
    assert [case.case_id for case in cases] == sorted(case.case_id for case in cases)
    assert {case.origin for case in cases} == {"fixtures"}
    hand_written = {case.case_id: case for case in cases if case.perturbation is None and "stress" not in case.tags}
    chosen = {
        "bar-grouped-matplotlib-many-categories-de": "de",
        "bar-basic-seaborn-decimals-de": "de",
        "bar-basic-seaborn-decimals-en": "en",
        "line-multi-matplotlib-millions-de": "de",
        "bar-horizontal-matplotlib-view-selection-fr": "fr",
    }
    assert set(hand_written) == {
        "scatter-basic-matplotlib",
        "bar-grouped-seaborn",
        "scatter-basic-matplotlib-german-message",
        *chosen,
        *COMBINED,
        *VIEW_CASES,
    }
    assert hand_written["bar-grouped-seaborn"].locale == "de"
    # Only the block H cases (density and number formats) and the French view case choose a language; the German
    # message case tests detection by its first typed message.
    assert {case.case_id: case.language for case in cases if case.language is not None} == chosen
    assert {case.case_id for case in cases if case.before_view} == set(VIEW_CASES)


def test_the_german_message_case_sets_the_language_by_its_first_typed_message() -> None:
    """The owner's eval case: an English first plot, then a German follow-up that the scope judge reads as `de`."""
    case = load_case(CASES_DIR / "scatter-basic-matplotlib-german-message", "fixtures")

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

    def select(selector: str) -> list:
        return select_cases(cases, selector, routes=NO_MODEL_CALL)

    smoke = select("smoke")
    assert len(smoke) == 25 and all("smoke" in case.tags for case in smoke)
    full = select("full")
    assert len(full) == 915 and full == [case for case in cases if "stress" not in case.tags]
    assert [case.case_id for case in select("*-view-*")] == sorted(VIEW_CASES)
    stress = select("stress")
    assert len(stress) == 23 and all("stress" in case.tags for case in stress)
    assert len(select("stress-compute-*")) == 3
    assert len(select("*-seaborn-n5000")) == 10
    picked = select("pie-basic-*, scatter-basic-matplotlib")
    assert len(picked) == 91 and picked[-1].case_id == "scatter-basic-matplotlib"  # 90 pie-basic cases, 15 libraries
    assert select("nothing-*") == []


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
    assert (case.sent_at, case.lane, case.owner_chat) == (None, None, False)


def test_a_promoted_case_reads_when_it_was_sent_its_lane_and_the_owner_mark(tmp_path: Path) -> None:
    fields = {**VALID, "sent_at": "2026-11-18T23:59:59Z", "lane": "public", "owner_chat": True}

    case = load_case(_write(tmp_path / "sent", fields), "promoted")

    assert case.sent_at == datetime(2026, 11, 18, 23, 59, 59, tzinfo=UTC)
    assert (case.lane, case.owner_chat) == ("public", True)
    assert load_case(_write(tmp_path / "admin", {**VALID, "lane": "admin"}), "promoted").lane == "admin"


def test_a_case_says_where_it_comes_from(tmp_path: Path) -> None:
    """Where a case lies must never decide what it is: `load_case` has no default origin."""
    directory = _write(tmp_path / "plain", VALID)

    with pytest.raises(TypeError):
        load_case(directory)


@pytest.mark.parametrize(
    "fields",
    [
        {"sent_at": "2026-11-12T07:40:27Z"},
        {"lane": "public"},
        {"owner_chat": False},
        {"replaces_sent_at": None},
        {"saved_session": True},
        {"tags": ["imported", "thumbs_down"]},
    ],
    ids=["sent_at", "lane", "owner_chat", "replaces_sent_at", "saved_session", "imported-tag"],
)
def test_a_fixture_that_carries_what_only_an_imported_case_carries_is_refused(tmp_path: Path, fields: dict) -> None:
    """Such a case would replay anywhere as a synthetic one, and could be committed as a fixture."""
    directory = _write(tmp_path / "case-invented-copied", {**VALID, **fields})

    with pytest.raises(CaseError, match="a fixture carries what only an imported case carries"):
        load_case(directory, "fixtures")
    assert load_case(directory, "promoted").origin == "promoted"


@pytest.mark.parametrize("value", ["2026-11-19t00:00:00z", "2026-1-9T0:0:0Z", "２０２６-11-19T00:00:00Z"])
def test_a_send_time_needs_ascii_digits_padded_and_capitals(tmp_path: Path, value: str) -> None:
    with pytest.raises(CaseError, match="sent_at must be a UTC time"):
        load_case(_write(tmp_path / "odd", {**VALID, "sent_at": value}), "promoted")


@pytest.mark.parametrize(
    ("value", "replaces"),
    [(None, None), ("unknown", "unknown"), ("2026-11-18T08:00:00Z", datetime(2026, 11, 18, 8, tzinfo=UTC))],
)
def test_a_promoted_case_reads_the_case_it_corrects(tmp_path: Path, value: object, replaces: object) -> None:
    case = load_case(_write(tmp_path / "corrected", {**VALID, "replaces_sent_at": value}), "promoted")

    assert case.replaces == replaces
    assert load_case(_write(tmp_path / "plain", VALID), "promoted").replaces == "unknown"  # absent fails closed
    with pytest.raises(CaseError, match="replaces_sent_at must be"):
        load_case(_write(tmp_path / "odd", {**VALID, "replaces_sent_at": "20261118T080000Z-0a1b2c3d"}), "promoted")


@pytest.mark.parametrize("value", ["owner", "Admin", "adm_0123456789abcdef", 1])
def test_a_lane_is_admin_or_public(tmp_path: Path, value: object) -> None:
    """A closed value: never a `user_hash`, never a near miss."""
    with pytest.raises(CaseError, match="lane must be one of admin, public"):
        load_case(_write(tmp_path / "odd", {**VALID, "lane": value}), "promoted")


@pytest.mark.parametrize(
    "value",
    ["2026-11-18T23:59:59", "2026-11-18T23:59:59+00:00", "2026-11-19T00:59:59+01:00", "2026-11-18 23:59:59Z", ""],
)
def test_a_send_time_in_another_form_is_refused_never_guessed(tmp_path: Path, value: str) -> None:
    """Only the manifest's own form is a send time; a naive time or another offset is a broken case."""
    with pytest.raises(CaseError, match="sent_at must be a UTC time"):
        load_case(_write(tmp_path / "odd", {**VALID, "sent_at": value}), "promoted")


@pytest.mark.parametrize("value", ["true", 1, None])
def test_the_owner_mark_is_true_or_false(tmp_path: Path, value: object) -> None:
    with pytest.raises(CaseError, match="owner_chat must be true or false"):
        load_case(_write(tmp_path / "odd", {**VALID, "owner_chat": value}), "promoted")


def test_a_case_may_take_data_steps_before_its_plot(tmp_path: Path) -> None:
    steps = [[{"op": "sort", "column": "b", "descending": True}], [{"op": "keep_rows", "n": 1}]]

    case = load_case(_write(tmp_path / "stepped", {**VALID, "before_operations": steps}), "fixtures")

    assert case.before_operations == tuple(tuple(operations) for operations in steps)
    assert load_case(_write(tmp_path / "plain", VALID), "fixtures").before_operations == ()


def test_a_case_may_draw_under_a_view_of_the_plot(tmp_path: Path) -> None:
    top = [{"op": "sort", "column": "b", "descending": True}, {"op": "keep_rows", "n": 1}]
    fields = {"before_view": [KEEP_B, *top], "view_checks": {"named": True, "clear": True}}

    case = load_case(_write(tmp_path / "viewed", {**VALID, **fields}), "fixtures")

    assert case.before_view == (KEEP_B, *top)
    assert case.view_checks == ViewChecks(named=True, clear=True, no_dq03=False)
    # Without checks the harness checks the drawn rows alone; without a view the case is as before.
    assert load_case(_write(tmp_path / "unchecked", {**VALID, "before_view": top}), "fixtures").view_checks is None
    plain = load_case(_write(tmp_path / "plain", VALID), "fixtures")
    assert (plain.before_view, plain.view_checks) == ((), None)


def test_the_clearing_of_a_view_is_the_cases_only_follow_up(tmp_path: Path) -> None:
    directory = _write(tmp_path / "both", {**VALID, "before_view": [KEEP_B], "view_checks": {"clear": True}})
    (directory / "change_request.txt").write_text("make the bars blue\n")

    with pytest.raises(CaseError, match="view_checks.clear and a change_request.txt exclude each other"):
        load_case(directory, "fixtures")


@pytest.mark.parametrize("language", ["de", "Deutsch", "Klingon", "Old Norse"])
def test_a_case_may_name_the_session_language_it_chooses(tmp_path: Path, language: str) -> None:
    case = load_case(_write(tmp_path / "chosen", {**VALID, "language": language}), "fixtures")

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
        ({"before_operations": []}, "a list of 1 to 5 operation lists"),
        ({"before_operations": [[{"op": "sort", "column": "a"}]] * 6}, "a list of 1 to 5 operation lists"),
        ({"before_operations": [[{"op": "fill", "column": "a"}]]}, "an operation list that prepare_data refuses"),
        ({"before_operations": [{"op": "sort", "column": "a"}]}, "an operation list that prepare_data refuses"),
        ({"before_view": []}, "a non-empty list of operations"),
        ({"before_view": {"op": "keep_rows", "n": 1}}, "a non-empty list of operations"),
        ({"before_view": [{"op": "fill", "column": "a"}]}, "an operation list that prepare_data refuses"),
        # A top N without its sort ranks by nothing a view could keep, so the call lands in the table.
        ({"before_view": [{"op": "keep_rows", "n": 1}]}, "must land in the view of the plot alone"),
        ({"before_view": [{"op": "keep_rows", "n": 1, "target": "table"}]}, "must land in the view of the plot"),
        ({"before_view": [{"op": "sort", "column": "a"}]}, "must land in the view of the plot alone"),
        ({"before_view": [{"op": "reset_view"}, KEEP_B]}, "must land in the view of the plot alone"),
        ({"before_view": [KEEP_B, {"op": "reset_view"}]}, "a view that prepare_data refuses"),
        ({"before_view": [KEEP_B, {"op": "rename", "column": "a", "name": "c"}]}, "must land in the view"),
        ({"view_checks": {"named": True}}, "view_checks need a before_view"),
        ({"before_view": [KEEP_B], "view_checks": {}}, "view_checks must be an object"),
        ({"before_view": [KEEP_B], "view_checks": {"named": "yes"}}, "each true or false"),
        ({"before_view": [KEEP_B], "view_checks": {"total": True}}, "view_checks must be an object"),
        # A view of an order condition alone has no word a label repeats, so `named` or `clear` would read nothing.
        ({"before_view": [B_ABOVE_1], "view_checks": {"named": True}}, "need a part of the view a label repeats"),
        ({"before_view": [B_ABOVE_1], "view_checks": {"clear": True}}, "need a part of the view a label repeats"),
    ],
)
def test_invalid_fields_are_refused(tmp_path: Path, change: dict, message: str) -> None:
    directory = _write(tmp_path / "bad-case", {**VALID, **change})

    with pytest.raises(CaseError, match=message):
        load_case(directory, "fixtures")


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
    case = load_case(CASES_DIR / case_id, "fixtures")
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
    checks = load_case(CASES_DIR / case_id, "fixtures").checks
    assert checks is not None

    assert (re.search(getattr(checks, field_name)[index], code) is not None) is found


VIEW_CASES: dict[str, ViewChecks] = {
    "bar-horizontal-matplotlib-view-top-mean": ViewChecks(named=True),
    "bar-horizontal-matplotlib-view-selection-fr": ViewChecks(named=True),
    "bar-horizontal-matplotlib-view-top-cleared": ViewChecks(named=True, clear=True),
    "bar-basic-seaborn-view-top-control": ViewChecks(no_dq03=True),
}
"""The view cases of PR #13142: a mean drawn under a top N and under a selection in French, the top N cleared, and a
control whose plot labels each bar and draws no figure over several rows."""
MEAN_LINE = re.compile(r"\bax[hv]line\(")
SUMMARY_CALL = re.compile(r"\b(?:mean|median|sum)\(")


def _rows(case_id: str) -> list[dict[str, str]]:
    return list(csv.DictReader(io.StringIO(load_case(CASES_DIR / case_id, "fixtures").data_text)))


@pytest.mark.parametrize("case_id", sorted(VIEW_CASES))
def test_the_view_cases_hold_the_premises_their_checks_read(case_id: str) -> None:
    """What a view case's checks read only holds on its data: the catalogue file draws a mean (or, for the control,
    none), the view's words stand in no cell and no mean the plot would write, the keys are unique (or the cleared
    run would combine rows first), the selected column is no bound one (or the legend would name it anyway), and
    every bar's label and the mean's fit the annotations `PlotShows.texts` keeps."""
    from pydantic import TypeAdapter

    from agents.anyplot.data.prepare import Operation
    from agents.anyplot.plot_view import PlotView, merged, route

    case = load_case(CASES_DIR / case_id, "fixtures")
    checks = VIEW_CASES[case_id]
    assert case.view_checks == checks and "view" in case.tags and case.change_request is None
    code = case.snapshot().code
    if checks.named:  # a catalogue regeneration that drops the mean leaves the case nothing to name
        assert MEAN_LINE.search(code) and SUMMARY_CALL.search(code)
    else:
        assert "bar_label(" in code and not MEAN_LINE.search(code) and not SUMMARY_CALL.search(code)
    view = merged(PlotView(), route(TypeAdapter(list[Operation]).validate_python(list(case.before_view))))
    tokens = [token for part in view_tokens(view) for token in part]
    bound = {binding.role: binding.column for binding in case.bindings or []}
    selected = {condition.column for where in view.selections for condition in where}
    assert tokens and not selected & set(bound.values())
    rows = _rows(case_id)
    keys = [row[bound["category"]] for row in rows]
    assert len(set(keys)) == len(keys)
    values = [float(row[bound["value"]]) for row in rows]
    if view.top is not None:
        drawn = sorted(values, reverse=view.top.descending)[: view.top.n]
    else:
        drawn = [value for row, value in zip(rows, values, strict=True) if all(row[c] in tokens for c in selected)]
    written = [cell for row in rows for column, cell in row.items() if column not in selected]
    written += [f"{statistics.fmean(sample):.{places}f}" for sample in (drawn, values) for places in (0, 1, 2)]
    written += [text.replace(".", ",") for text in written]  # the plot language's decimal comma
    assert not [text for text in written for token in tokens if holds_token(text, token)]
    marks = len(rows) if checks.clear else len(drawn)
    assert marks + 1 <= GROUP_LIMITS["annotations"]


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
        load_case(directory, "fixtures")
    (directory / "change_request.txt").write_text("German labels and a grid\n")

    case = load_case(directory, "fixtures")

    assert case.checks == FollowUpChecks(
        language="de", theme="dark", code_added=("grid\\(",), code_kept=("PAGE_BG",), texts_changed=("title", "legend")
    )
    assert load_case(_write(tmp_path / "unchecked", VALID), "fixtures").checks is None


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
        load_case(directory, "fixtures")


def test_missing_files_and_bad_ids_are_refused(tmp_path: Path) -> None:
    directory = tmp_path / "no-data"
    directory.mkdir()
    (directory / "case.json").write_text(json.dumps(VALID))
    with pytest.raises(CaseError, match="case.json and data.csv"):
        load_case(directory, "fixtures")
    with pytest.raises(CaseError, match="not a case id"):
        load_case(_write(tmp_path / "Upper_Case", VALID), "fixtures")


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
