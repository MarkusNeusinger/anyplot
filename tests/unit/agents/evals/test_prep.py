"""The prep eval (agents/evals/prep.py): the fixtures, the canonical operations, the score, a scripted run."""

import asyncio
import dataclasses
import itertools
import json
import os
from collections import Counter
from pathlib import Path
from typing import Any

import pytest
from pydantic import ValidationError

from agents.anyplot.data.generate import Generate, generate
from agents.anyplot.data.parse import parse_dataset
from agents.anyplot.data.prepare import PrepareError, apply_operations
from agents.anyplot.models import FakeJudge, JudgeVerdict
from agents.anyplot.opening import instruction_like
from agents.anyplot.run_queue import RunQueue
from agents.anyplot.services import Services
from agents.evals import prep
from agents.evals.host_data import HostDataBackend
from agents.evals.prep import (
    DEFAULT_CASES,
    EXIT_FAILED,
    EXIT_OK,
    EXIT_OUTAGE,
    EXIT_SETUP,
    CaseResult,
    Gates,
    PrepCase,
    SetupError,
    canonical_code,
    canonical_operations,
    check_cases,
    describe,
    load_cases,
    run_cases,
    score,
    score_from_version,
    verdict_of,
)
from agents.main import Runtime

from ..runtime.fakes import FakeAnthropic


OPERATIONS = (
    "rename",
    "drop_columns",
    "drop_rows",
    "set_type",
    "aggregate",
    "sort",
    "pivot_longer",
    "pivot_wider",
    "classify",
    "derive",
    "make_date",
    "row_number",
    "date_number",
    "split",
    "extract",
    "strip",
    "replace",
    "compute",
    "diff",
    "rolling",
    "blank",
    "keep_rows",
    "unsupported",
)
HOURS = "Study Hours,Exam Score\n2,55\n5,70\n8,85\n3,60\n"
RENAME = {"op": "rename", "column": "Study Hours", "name": "Hours"}
GHOST = {"op": "rename", "column": "Ghost", "name": "Spirit"}  # no such column: the tool answers unknown_column
SINE = {"name": "y", "expression": "sin(x)"}
SINE_CALL = {"variables": [{"start": "-pi", "stop": "pi"}], "series": [SINE]}
CODE_CALL = {"op": "run_data_code", "rows": 4, "columns": 2}
# Invented sales with a notes column and a total row at the end, which the parser leaves out of the table.
SALES = "Region,Month,Sales,Note\nNorth,Jan,12,\nNorth,Feb,13,fair\nSouth,Jan,9,\nSouth,Feb,11,\nEast,Jan,7,new\nEast,Feb,8,\nTotal,,60,\n"
SALES_SUM = {"op": "aggregate", "by": ["Region"], "column": "Sales", "how": "sum"}
SALES_SORT = {"op": "sort", "column": "Sales", "descending": True}
SALES_CHAIN = [{"op": "drop_columns", "columns": ["Note"]}, SALES_SUM, SALES_SORT]


def case(case_id: str, message: str, expected: list[dict[str, Any]], locale: str = "en", **extra: Any) -> PrepCase:
    return PrepCase(
        id=case_id, dataset_text=HOURS, message=message, expected_operations=expected, locale=locale, **extra
    )


def runtime() -> Runtime:
    return Runtime(queue=RunQueue(concurrency=1, per_minute=1_000, max_wait_s=600))


class TestFixtures:
    def test_the_set_covers_every_operation_in_both_languages(self) -> None:
        cases = load_cases(DEFAULT_CASES)
        locales = Counter(item.locale for item in cases)
        ops = {operation["op"] for item in cases for operation in item.expected_operations}

        # 36 single-step cases (two of them `derive`, two `make_date`, one month-only date format, one sort of month
        # names, one daily mean per sensor, four text operations, two `date_number`), 11 `hard` ones (chains,
        # ambiguity, unsupported asks), 11 data-code cases, 13 step-1 summaries, 3 requests for example data, 4 for
        # another plot type and 7 notes sent with the paste (`first_turn`), one of them a decimal comma read again
        # from the pasted cells, one whose change comes with a conversion the data owes, one that asks to keep
        # that column as it is and one that names a statistic, which gets the summary and never the data refusal,
        # and a short table the page kept as a message (`misrouted`), which the root asks for again. Since
        # 2026-11-07, ten cases for the operations of the persona tests of 2026-11-06 (`compute` four times, `diff`,
        # `rolling`, `blank`, the last value of several columns per month, several values into one class, and a
        # request to fill in values, which the root names as a gap); the hard unit conversion became a `compute`.
        # And the owner's top N of that day: revenue computed, sorted and its top 3 kept (`keep_rows`). And three that
        # start from the original after an earlier change (`before_operations`, `from_version`): the first 20 after a
        # top 10, the pace per run after a weekly sum (a question), a dropped column back. Since 2026-11-08, two on a
        # line whose x repeats (`repeated_key`): its summary changes nothing, and a wish for one point per x is the
        # counted `aggregate`. And one that asks for a data change and its plot in one message (`change_and_plot`),
        # after the summary: the change is the turn's answer, and the plot waits for the user's check. Since
        # 2026-11-09, two summaries of the layouts code reads (`layout`): a web table copied one cell per line and an
        # inline list of pairs, the owner's live cases in invented data. And the change request that the pair list
        # read as new data the same day (`change_request`): the root changes no data for it. Since 2026-11-11, one
        # with thousands dots and a footnote mark on one cell (`footnote_mark`): `set_type` with a decimal comma
        # reads both columns, where a detour through `strip` and `replace` had lost a digit.
        assert len(cases) == 107
        assert sorted(item.id for item in cases if "layout" in item.tags) == [
            "de-wunsch-achsen-bis",
            "en-summary-inline-pairs",
            "en-summary-web-table-cell-lines",
        ]
        assert sorted(item.id for item in cases if "repeated_key" in item.tags) == [
            "de-ein-punkt-pro-laenge",
            "en-summary-repeated-key",
        ]
        both = [item for item in cases if "change_and_plot" in item.tags]
        assert [(item.id, item.first_turn) for item in both] == [("en-change-and-plot", False)]
        rebuilt = [item for item in cases if item.before_operations]
        assert len(rebuilt) == 3 and all(item.expected_from_version == "original" for item in rebuilt)
        assert [item.id for item in cases if "misrouted" in item.tags] == ["en-table-as-message"]
        notes = [item for item in cases if item.first_turn]
        assert len(notes) == 7 and {item.locale for item in notes} == {"de", "en"}
        assert all(item.message and item.dataset_text and "note" in item.tags for item in notes)
        assert any("data_question" in item.tags for item in notes)  # a summary and an answer in one reply
        assert any("conversion" in item.tags for item in notes)  # the note's change and the owed conversion
        plot_type = [item for item in cases if "plot_type" in item.tags]
        assert len(plot_type) == 4 and {item.locale for item in plot_type} == {"de", "en"}
        assert all(not item.expected_operations and item.dataset_text for item in plot_type)
        example = [item for item in cases if "example_data" in item.tags]
        assert len(example) == 3 and {item.locale for item in example} == {"de", "en"}
        assert all(
            item.dataset_text is None and item.expected_operations[0]["op"] == "run_data_code" for item in example
        )
        assert {item.locale for item in cases if "derive" in item.tags} == {"de", "en"}
        assert sum(1 for item in cases if "hard" in item.tags) == 11
        assert {item.locale for item in cases if "text" in item.tags} == {"de", "en"}
        assert {item.locale for item in cases if "compute" in item.tags} == {"de", "en"}
        gaps = [
            item for item in cases if item.expected_operations[:1] == [{"op": "unsupported", "family": "fill_values"}]
        ]
        assert [item.id for item in gaps] == ["en-fill-missing-refused"]
        # The owner's case of 2026-11-04 in both languages, and its summary, which only offers the conversion.
        dates = [item for item in cases if "date_number" in item.tags]
        assert {item.locale for item in dates if item.message} == {"de", "en"}
        assert [item.id for item in dates if item.action] == ["en-summary-date-offer"]
        assert locales["de"] >= 5 and locales["en"] >= 5
        assert ops == {*OPERATIONS, "generate_data", "run_data_code"}
        assert sum(1 for item in cases if not item.expected_operations) >= 2  # out of scope, and a plain question
        assert any(len(item.expected_operations) == 2 for item in cases)  # two operations in one message
        tags = Counter(tag for item in cases for tag in item.tags)
        for tag in ("percent", "decimal_comma", "date_format", "total_row", "period", "no_tool"):
            assert tags[tag] >= 1, tag
        # The formulas: a sine, a parabola with its points, a parametric circle and a grid, with and without data.
        formulas = [item for item in cases if "formula" in item.tags]
        assert len(formulas) == 4 and {item.locale for item in formulas} == {"de", "en"}
        assert tags["grid"] == 1 and tags["parametric"] == 1
        assert any(item.dataset_text is None for item in formulas) and any(item.dataset_text for item in formulas)

    def test_the_data_code_cases(self) -> None:
        """Python, NumPy, JavaScript, R and a textbook formula run; a plot call is stripped; a file read and a
        general-purpose script are refused (owner decision of 2026-10-14)."""
        cases = [item for item in load_cases(DEFAULT_CASES) if "data_code" in item.tags]
        tags = Counter(tag for item in cases for tag in item.tags)

        assert len(cases) == 11 and {item.locale for item in cases} == {"de", "en"}
        assert tags["python"] >= 3 and tags["javascript"] == tags["r"] == tags["math"] == 1
        assert tags["strip_plot"] == 1 and tags["file_access"] == 1 and tags["general_runner"] == 1
        # Described in words only, the computation decides the tool: an ODE, an iteration, random numbers.
        assert tags["words"] == 3 and tags["ode"] == tags["iteration"] == tags["random"] == 1
        refused = [item for item in cases if item.refuse]
        assert {item.id for item in refused} == {"en-code-reads-a-file", "en-code-general-script"}
        assert all(not item.expected_operations for item in refused)

    def test_the_summary_cases(self) -> None:
        """The step-1 summary, where 10 of 11 replies of the user test of 2026-11-01 closed with a question."""
        cases = [item for item in load_cases(DEFAULT_CASES) if item.action is not None]

        assert len(cases) == 16 and {item.locale for item in cases} == {"de", "en"}
        assert all(item.message is None and item.dataset_text for item in cases)
        assert all("summary" in item.tags for item in cases)
        # A summary changes the data only for what the server found in code (live tests of 2026-11-01 and 11-02): a
        # newest-first date column gets its sort, a column that converts for certain fills an open role, a list
        # of values gets its row numbers, and a column of ranges fills a lower and upper bound pair left open.
        sorted_dates = {"en-summary-rtx-prices", "de-summary-preise-monatsnamen", "en-summary-convert-day-dates"}
        changing = {item.id for item in cases if item.expected_operations}
        assert changing == {
            *sorted_dates,
            "en-summary-year-column",
            "en-summary-row-number",
            "de-summary-zeilennummer",
            "en-summary-range-column",
        }
        assert all("date_order" in item.tags for item in cases if item.id in sorted_dates)
        # Dates whose day and month order reads both ways, and a conversion that would guess the century: the
        # summaries that may close with their question.
        assert [item.id for item in cases if prep.BLOCKED_TAGS & set(item.tags)] == [
            "de-summary-datum-zweistellig",
            "en-summary-ambiguous-dates",
        ]

    @pytest.mark.parametrize(
        "fields",
        [
            {"message": "rename it", "action": "summarize_data"},
            {},
            {"action": "summarize_data", "dataset_text": None},
            {"action": "create_plot"},
            # A note is a message sent with a paste: neither without a message nor without data.
            {"action": "summarize_data", "first_turn": True},
            {"message": "only 2024", "dataset_text": None, "first_turn": True},
        ],
    )
    def test_a_case_has_a_message_or_a_summary_action(self, fields: dict[str, Any]) -> None:
        data: dict[str, Any] = {"id": "x-001", "dataset_text": HOURS, "expected_operations": [], "locale": "en"}
        with pytest.raises(ValidationError):
            PrepCase.model_validate({**data, **fields})

    def test_every_fixture_is_consistent_with_the_operations(self) -> None:
        """The expected operations apply to the fixture's own dataset, and the dataset passes the pre-filter.

        A formula's expected call computes, and its table parses as number columns.
        """
        for item in load_cases(DEFAULT_CASES):
            parsed = parse_dataset(item.dataset_text) if item.dataset_text else None
            assert parsed is None or not instruction_like(parsed), item.id
            decimal = parsed.profile.decimal if parsed else "."
            canonical_operations(item.expected_operations, decimal)  # raises for a bad fixture
            formulas = [operation for operation in item.expected_operations if operation["op"] == "generate_data"]
            operations = [
                operation
                for operation in item.expected_operations
                if operation["op"] not in ("generate_data", "run_data_code")
            ]
            for formula in formulas:
                spec = Generate.model_validate({key: value for key, value in formula.items() if key != "op"})
                table = parse_dataset(generate(spec).csv)
                assert set(table.column_dtypes.values()) == {"number"}, item.id
            if [operation["op"] for operation in operations] == ["unsupported"]:
                continue  # a named gap applies nothing: `prepare_data` answers it with its fixed sentence
            if operations:
                assert parsed is not None, item.id
                prepared = apply_operations(parsed, _operations(operations))
                assert len(prepared.changes) == len(operations), item.id
                # An expected `drop_rows` must drop a row of the data as the parser stores it. Since #12166 the
                # parser leaves out a summary row at the end of a paste; two fixtures still expected the root to
                # drop that row, which no longer exists, so the root's right answer scored as a miss.
                for operation, change in zip(operations, prepared.changes, strict=True):
                    if operation["op"] == "drop_rows":
                        assert not change.startswith("dropped 0 rows"), (item.id, change)
        check_cases(load_cases(DEFAULT_CASES))

    def test_a_bad_directory_or_fixture_is_a_setup_error(self, tmp_path: Path) -> None:
        with pytest.raises(SetupError, match="holds no case"):
            load_cases(tmp_path)
        (tmp_path / "x-001.json").write_text(json.dumps({"dataset_text": "a\n1\n", "message": "hi"}), encoding="utf-8")
        with pytest.raises(SetupError, match="does not load"):
            load_cases(tmp_path)
        bad = case("bad-001", "do it", [{"op": "explode"}])
        with pytest.raises(SetupError, match="do not validate"):
            check_cases([bad])

    def test_a_case_scored_by_its_table_needs_a_table_its_operations_change(self) -> None:
        """A table the expected operations leave as it is cannot tell them from no data call: such a case is strict."""
        nothing = [{"op": "drop_rows", "where": [{"column": "Study Hours", "test": "gt", "value": 100}]}]

        with pytest.raises(SetupError, match="no-001: expected_operations leave its table as it is"):
            check_cases([case("no-001", "drop the rows over 100 hours", nothing)])
        check_cases([case("no-002", "drop the rows over 100 hours", nothing, strict_operations=True)])
        # The scoring's own equality decides: a sort changes the order only, which `row_order: "any"` ignores.
        ordered = [{"op": "sort", "column": "Exam Score"}]
        check_cases([case("no-008", "sort by the score", ordered)])
        with pytest.raises(SetupError, match="no-009: expected_operations leave its table as it is"):
            check_cases([case("no-009", "sort by the score", ordered, row_order="any")])
        with pytest.raises(SetupError, match="no-003: expected_operations do not apply to its data"):
            check_cases([case("no-003", "rename the ghost", [GHOST])])
        check_cases([case("no-004", "rename the ghost", [GHOST], strict_operations=True)])  # scored by its operations
        # A named gap alone changes no table by design: the gaps are compared apart (`gap_difference`).
        check_cases([case("no-005", "fill the gaps", [{"op": "unsupported", "family": "fill_values"}])])
        top = [{"op": "sort", "column": "Exam Score", "descending": True}, {"op": "keep_rows", "n": 2}]
        with pytest.raises(SetupError, match="no-006: expected_from_version 3 names no version of its data"):
            check_cases([case("no-006", "back", top, before_operations=[top], expected_from_version=3)])
        check_cases([case("no-007", "back", [RENAME], before_operations=[top], expected_from_version=2)])

    def test_which_cases_are_scored_by_their_table(self) -> None:
        """Every case but one that expects no data call, a `run_data_code` call, a `refuse` case and a strict one."""
        assert case("s-001", "rename it", [RENAME]).scored_by_table
        assert not case("s-002", "which column?", []).scored_by_table
        assert not case("s-003", "run my code", [CODE_CALL]).scored_by_table
        assert not case("s-004", "read my file", [], refuse=True).scored_by_table
        assert not case("s-005", "rename it", [RENAME], strict_operations=True).scored_by_table
        cases = load_cases(DEFAULT_CASES)
        by_table = [item for item in cases if item.scored_by_table]
        assert len(by_table) > len(cases) / 2
        assert all(item.expected_operations and not item.refuse for item in by_table)


def _operations(items: list[dict[str, Any]]) -> Any:
    from pydantic import TypeAdapter

    from agents.anyplot.data.prepare import Operation

    return TypeAdapter(list[Operation]).validate_python(items)


class TestCanonical:
    def test_defaults_written_or_left_out_are_the_same(self) -> None:
        bare = [{"op": "sort", "column": "a"}, {"op": "pivot_longer", "columns": ["b", "a"]}]
        written = [
            {"op": "pivot_longer", "columns": ["a", "b"], "names_to": "series", "values_to": "value"},
            {"op": "sort", "column": "a", "descending": False},
        ]

        assert canonical_operations(bare, ".") == canonical_operations(written, ".")

    def test_the_datasets_own_decimal_counts_as_left_out(self) -> None:
        explicit = [{"op": "set_type", "column": "p", "type": "number", "decimal": ","}]
        implicit = [{"op": "set_type", "column": "p", "type": "number"}]

        assert canonical_operations(explicit, ",") == canonical_operations(implicit, ",")
        assert canonical_operations(explicit, ".") != canonical_operations(implicit, ".")

    def test_conditions_and_column_lists_are_sets(self) -> None:
        one = [
            {
                "op": "drop_rows",
                "where": [{"column": "a", "test": "gt", "value": "1"}, {"column": "b", "test": "is_missing"}],
            }
        ]
        other = [
            {
                "op": "drop_rows",
                "where": [{"column": "b", "test": "is_missing"}, {"column": "a", "test": "gt", "value": "1"}],
            }
        ]

        assert canonical_operations(one, ".") == canonical_operations(other, ".")
        assert canonical_operations([{"op": "drop_columns", "columns": ["b", "a"]}], ".") == canonical_operations(
            [{"op": "drop_columns", "columns": ["a", "b"]}], "."
        )
        # The keys of an aggregate keep their order: `by` decides the sort of the result.
        assert canonical_operations([{"op": "aggregate", "by": ["a", "b"], "column": "v", "how": "sum"}], ".") != (
            canonical_operations([{"op": "aggregate", "by": ["b", "a"], "column": "v", "how": "sum"}], ".")
        )

    def test_an_invalid_operation_raises(self) -> None:
        with pytest.raises(ValidationError):
            canonical_operations([{"op": "rename", "column": "a"}], ".")

    def test_describe(self) -> None:
        lines = canonical_operations(
            [
                {"op": "aggregate", "by": ["Datum"], "column": "Betrag", "how": "sum", "period": "month"},
                {"op": "drop_rows", "where": [{"column": "Tier", "test": "eq", "value": "Gesamt"}]},
                {"op": "set_type", "column": "share", "type": "number", "decimal": ","},
                {"op": "pivot_wider", "names_from": "p", "values_from": "v", "index": ["m"]},
                {
                    "op": "classify",
                    "name": "Klasse",
                    "rules": [{"where": [{"column": "y", "test": "gt", "value": 0}], "label": "Klasse 1"}],
                    "otherwise": "Klasse 2",
                },
                {"op": "row_number"},
                {"op": "date_number", "column": "Abo", "unit": "days"},
                {"op": "date_number", "column": "Abo", "unit": "year", "name": "Jahr"},
            ],
            ".",
        )

        assert sorted(describe(line) for line in lines) == [
            "aggregate Betrag sum by Datum/month",
            "classify Klasse: 'Klasse 1' if y gt '0'; else 'Klasse 2'",
            "date_number Abo as days",
            "date_number Abo as year into Jahr",
            "drop_rows Tier eq 'Gesamt'",
            "pivot_wider p with v by m",
            "row_number index",
            "set_type share number (,)",
        ]

    def test_describe_the_text_operations(self) -> None:
        lines = canonical_operations(
            [
                {"op": "split", "column": "Range", "separator": "–", "names": ["lo", "hi"]},
                {"op": "extract", "column": "Ticket", "keep": "number", "name": "n"},
                {"op": "strip", "column": "Code", "prefix": " # ", "name": "c"},
                {"op": "replace", "column": "Region", "old": "-", "name": "r"},
            ],
            ".",
        )

        assert sorted(describe(line) for line in lines) == [
            "extract number of Ticket as n",
            "replace '-' with '' in Region as r",
            "split Range at '–' into lo, hi",
            "strip prefix '#' of Code as c",  # a prefix's own spaces count for nothing
        ]

    def test_classify_keeps_its_rule_order_and_ignores_the_order_of_a_rules_conditions(self) -> None:
        high = {"column": "y", "test": "gt", "value": "0.5"}
        named = {"column": "x", "test": "ne", "value": "a"}

        def call(first: list[dict[str, Any]], labels: tuple[str, str]) -> list[str]:
            rules = [{"where": first, "label": labels[0]}, {"where": [high], "label": labels[1]}]
            return canonical_operations([{"op": "classify", "name": "k", "rules": rules}], ".")

        assert call([high, named], ("a", "b")) == call([named, high], ("a", "b"))
        assert call([high, named], ("a", "b")) != call([high, named], ("b", "a"))

    def test_a_generate_data_call_is_one_item_with_defaults_and_whitespace_left_out(self) -> None:
        bare = [{"op": "generate_data", "variables": [{"start": "-pi", "stop": "pi"}], "series": [SINE]}]
        written = [
            {
                "op": "generate_data",
                "variables": [{"name": "x", "start": " - pi", "stop": "pi ", "points": 200}],
                "series": [{"name": "y", "expression": "sin( x )"}],
            }
        ]

        assert canonical_operations(bare, ".") == canonical_operations(written, ".")
        (line,) = canonical_operations(bare, ".")
        assert json.loads(line) == {
            "op": "generate_data",
            "variables": [{"start": "-pi", "stop": "pi"}],
            "series": [{"name": "y", "expression": "sin(x)"}],
        }
        assert describe(line) == "generate_data x -pi..pi (200): y = sin(x)"
        # The series are a set, the variables keep their order (the first is the grid's slowest), and a JSON number
        # as an endpoint is its text.
        circle = [{"name": "x", "expression": "cos(t)"}, {"name": "y", "expression": "sin(t)"}]
        one = {"op": "generate_data", "variables": [{"name": "t", "start": 0, "stop": "2*pi"}], "series": circle}
        other = {**one, "variables": [{"name": "t", "start": "0", "stop": "2 * pi"}], "series": circle[::-1]}
        assert canonical_operations([one], ".") == canonical_operations([other], ".")
        x, y = {"name": "x", "start": "0", "stop": "1"}, {"name": "y", "start": "0", "stop": "1"}
        grid = {"op": "generate_data", "variables": [x, y], "series": [{"name": "z", "expression": "x*y"}]}
        swapped = {**grid, "variables": [y, x]}
        assert canonical_operations([grid], ".") != canonical_operations([swapped], ".")
        # A formula and an operation in one turn are two items.
        assert len(canonical_operations([*bare, RENAME], ".")) == 2
        with pytest.raises(ValidationError):
            canonical_operations([{"op": "generate_data", "variables": [], "series": [SINE]}], ".")

    def test_a_code_table_is_compared_and_described_by_its_size(self) -> None:
        """The eval's data runs execute the snippet (`HostDataBackend`), so a code call always has a real size."""
        line = canonical_code({"op": "run_data_code", "rows": 5, "columns": 2})

        assert describe(line) == "run_data_code: 5 rows x 2 columns"
        assert line != canonical_code({"op": "run_data_code", "rows": 4, "columns": 2})

    def test_an_expected_code_table_may_allow_a_few_sizes(self) -> None:
        """A script with the steps and their walk may keep both: two or three columns are the user's data."""
        expected = [canonical_code({"op": "run_data_code", "rows": 500, "columns": [3, 2, 2]})]

        assert describe(expected[0]) == "run_data_code: 500 rows x 2 or 3 columns"
        for columns, fits in ((2, True), (3, True), (4, False)):
            found = [canonical_code({"op": "run_data_code", "rows": 500, "columns": columns})]
            assert prep.same_operations(found, expected) is fits, columns
        two = canonical_code({"op": "run_data_code", "rows": 500, "columns": 2})
        assert not prep.same_operations([two, two], expected)  # a second call is still a miss
        assert prep.same_operations(
            [two, *canonical_operations([RENAME], ".")], [*expected, *canonical_operations([RENAME], ".")]
        )
        # A refused `prepare_data` operation named run_data_code stays raw in the report, without a size: a miss.
        raw = json.dumps({"op": "run_data_code", "code": "df = 1"}, sort_keys=True)
        assert prep.same_operations([raw], expected) is False
        for bad in ([2], [1, 2, 3, 4, 5], [0, 2]):
            with pytest.raises(ValidationError):
                canonical_code({"op": "run_data_code", "rows": 500, "columns": bad})

    def test_a_generate_data_call_matches_by_the_table_it_computes(self) -> None:
        """Endpoints compare by value and expressions by what they compute, so an equivalent call is no miss."""

        def lines(start: Any, stop: Any, expression: str, points: int = 50, name: str = "y") -> list[str]:
            variables = [{"start": start, "stop": stop, "points": points}]
            call = {"op": "generate_data", "variables": variables, "series": [{"name": name, "expression": expression}]}
            return canonical_operations([call, RENAME], ".")

        parabola = lines("-3", "3", "x**2")
        for start, stop, expression in ((-3.0, 3.0, "x**2"), ("-3.0", "3", "x*x"), ("-3", "3", "(x)**2")):
            found = lines(start, stop, expression)
            assert found != parabola and prep.same_operations(found, parabola), (start, stop, expression)
        assert prep.same_operations(lines("0", "tau", "sin(x)"), lines("0", "pi*2", "sin(x)"))
        # Other points, another name or another formula are a miss; so is a call the server cannot compute.
        assert not prep.same_operations(lines("-3", "3", "x**2", points=51), parabola)
        assert not prep.same_operations(lines("-3", "3", "x**2", name="f"), parabola)
        assert not prep.same_operations(lines("-3", "3", "x**3"), parabola)
        undefined = lines("-3", "3", "log(-1 - x**2)")
        (formula,) = [line for line in undefined if "generate_data" in line]
        assert prep.comparison_key(formula) == formula and not prep.same_operations(undefined, parabola)
        assert prep.same_operations(undefined, undefined)

    def test_a_compute_matches_by_the_values_it_computes(self) -> None:
        """The short names and the form of the expression are the model's choice; the columns and the result are not."""

        def lines(expression: str, name: str = "C", **inputs: str) -> list[str]:
            call = {"op": "compute", "name": name, "expression": expression, "inputs": inputs}
            return canonical_operations([call], ".")

        celsius = lines("(f - 32) * 5 / 9", f="Temperatur_F")
        assert prep.same_operations(lines("5/9*(t-32)", t="Temperatur_F"), celsius)
        assert prep.same_operations(lines("(temp − 32) × 5 / 9", temp="Temperatur_F"), celsius)
        assert not prep.same_operations(lines("(f - 32) * 5 / 9", name="Celsius", f="Temperatur_F"), celsius)
        assert not prep.same_operations(lines("(f - 30) / 2", f="Temperatur_F"), celsius)
        revenue = lines("q * p", q="Quantity", p="Price")
        assert prep.same_operations(lines("price*quantity", price="Price", quantity="Quantity"), revenue)
        assert not prep.same_operations(
            lines("a / b", a="Quantity", b="Price"), lines("a / b", a="Price", b="Quantity")
        )
        # A shifted log is defined on the first probe set, so two spellings match by value (review of 2026-11-07:
        # on small probe values both were empty everywhere and matched only by their spelling).
        shifted = lines("log(p - 100)", name="log_excess", p="Price")
        assert prep.same_operations(lines("log(price-100)", name="log_excess", price="Price"), shifted)
        assert not prep.same_operations(lines("log(p - 99)", name="log_excess", p="Price"), shifted)
        assert prep.comparison_key(shifted[0]) != shifted[0]
        # Undefined on the large values, an expression takes the small ones; refused on both, it keeps its line.
        reversed_log = lines("log(100 - p)", name="r", p="Price")
        assert prep.comparison_key(reversed_log[0]) != reversed_log[0]
        assert prep.same_operations(lines("log(-(p - 100))", name="r", p="Price"), reversed_log)
        (refused,) = lines("q > 1", q="Quantity")
        assert prep.comparison_key(refused) == refused
        assert describe(revenue[0]) == "compute C = q * p (p=Price, q=Quantity)"

    def test_the_new_operations_compare_their_lists_as_sets_and_describe_themselves(self) -> None:
        def blank(*values: str) -> list[str]:
            where = [{"column": "u", "test": "eq", "values": list(values)}]
            return canonical_operations([{"op": "blank", "columns": ["u", "v"][: len(values)], "where": where}], ".")

        assert blank("-1", "-0.99") == canonical_operations(
            [{"op": "blank", "columns": ["v", "u"], "where": [{"column": "u", "test": "eq", "values": [-0.99, -1]}]}],
            ".",
        )
        several = {"op": "aggregate", "by": ["Datum"], "columns": ["B", "A"], "how": "last", "period": "month"}
        assert canonical_operations([several], ".") == canonical_operations([{**several, "columns": ["A", "B"]}], ".")
        lines = canonical_operations(
            [
                several,
                {"op": "diff", "name": "d", "column": "v", "order": "t", "lag": 12},
                {
                    "op": "rolling",
                    "name": "m",
                    "column": "v",
                    "how": "mean",
                    "window": 3,
                    "order": "t",
                    "within": ["g"],
                },
                {"op": "unsupported", "family": "fill_values"},
            ],
            ".",
        )
        assert sorted(describe(line) for line in [*lines, *blank("-1", "-0.99")]) == [
            "aggregate A, B last by Datum/month",
            "blank u, v where u eq '-0.99'|'-1'",
            "diff d = v by t lag 12",
            "rolling m = mean of v over 3 by t within g",
            "unsupported fill_values",
        ]


def table_of(operations: list[dict[str, Any]], text: str = SALES) -> prep.ResultTable:
    made = prep.expected_result(parse_dataset(text), operations, "en")
    assert made is not None
    return prep.result_table(made)


def cells(columns: tuple[str, ...], dtypes: tuple[str, ...], *rows: tuple[str | None, ...]) -> prep.ResultTable:
    return prep.ResultTable(columns, dtypes, rows)


class TestTable:
    def test_two_sequences_that_make_the_same_table_both_match(self) -> None:
        """Guard 2a of #12599: an `aggregate` keeps only its keys and its values, so the notes column it would drop
        anyway and a total row the parser left out already change nothing, and every sequence is the same answer."""
        sequences = [
            SALES_CHAIN,
            [SALES_SUM, SALES_SORT],  # the notes column without its drop
            [{"op": "drop_rows", "where": [{"column": "Region", "test": "eq", "value": "Total"}]}, *SALES_CHAIN],
        ]
        tables = [table_of(operations) for operations in sequences]

        assert all(prep.table_difference(table, tables[0]) is None for table in tables)
        assert tables[0].columns == ("Region", "Sales") and [row[0] for row in tables[0].rows] == [
            "North",
            "South",
            "East",
        ]
        lines = [canonical_operations(operations, ".") for operations in sequences]
        assert not prep.same_operations(lines[1], lines[0]) and not prep.same_operations(lines[2], lines[0])

    @pytest.mark.parametrize(
        ("operations", "miss"),
        [
            ([SALES_SUM, {"op": "sort", "column": "Sales"}], "values differ: 'Region' in 2 rows, 'Sales' in 2 rows"),
            ([{**SALES_SUM, "how": "mean"}, SALES_SORT], "column 'Sales' is number, expected integer"),
            ([SALES_SORT], "columns ['Region', 'Month', 'Sales', 'Note'], expected ['Region', 'Sales']"),
            (
                [{"op": "drop_rows", "where": [{"column": "Region", "test": "eq", "value": "East"}]}, *SALES_CHAIN],
                "2 rows, expected 3",
            ),
            (
                [*SALES_CHAIN, {"op": "set_type", "column": "Sales", "type": "text"}],
                "column 'Sales' is text, expected integer",
            ),
        ],
    )
    def test_another_table_is_a_miss_that_names_columns_never_cells(
        self, operations: list[dict[str, Any]], miss: str
    ) -> None:
        assert prep.table_difference(table_of(operations), table_of(SALES_CHAIN)) == miss

    def test_number_cells_compare_within_the_tolerance(self) -> None:
        """`data.csv` writes a float in full, so a sum in another order differs in its last digit; a real difference
        does not hide in the tolerance, and a text cell compares as its text."""
        columns, dtypes = ("k", "v", "t"), ("text", "number", "text")
        want = cells(columns, dtypes, ("a", "519.1666666666666", "0.1"), ("b", "0", None))

        def found(value: str, zero: str = "0", text: str = "0.1") -> prep.ResultTable:
            return cells(columns, dtypes, ("a", value, text), ("b", zero, None))

        assert prep.table_difference(found("519.1666666666667"), want) is None
        assert prep.table_difference(found("519.1666666666666", zero="1.2246467991473532e-16"), want) is None
        assert prep.table_difference(found("519.17"), want) == "values differ: 'v' in 1 row"
        assert prep.table_difference(found("519.1666666666666", zero="1e-6"), want) == "values differ: 'v' in 1 row"
        assert prep.table_difference(found("519.1666666666666", text="0.10"), want) == "values differ: 't' in 1 row"
        # An empty cell is no number: it equals only another empty cell, never a 0.
        assert prep.table_difference(cells(columns, dtypes, ("a", "1", "0.1"), ("b", None, None)), want) == (
            "values differ: 'v' in 2 rows"
        )
        assert prep.result_table(parse_dataset("k,v\na,1.5\nb,\nc,2\n")).rows == (("a", "1.5"), ("b", None), ("c", "2"))
        # `nan` equals nothing as a float, so it compares as its text and sorts as text.
        nan = cells(columns, dtypes, ("a", "nan", "0.1"), ("b", "0", None))
        assert prep.table_difference(nan, nan) is None and prep.table_difference(nan, nan, any_order=True) is None
        assert prep.table_difference(nan, want) == "values differ: 'v' in 1 row"

    def test_rows_compare_in_order_unless_the_case_leaves_it_open(self) -> None:
        want = table_of(SALES_CHAIN)
        shuffled = prep.ResultTable(want.columns, want.dtypes, want.rows[::-1])
        close = prep.ResultTable(
            want.columns, ("text", "number"), tuple((row[0], f"{row[1]}.0000000000001") for row in want.rows)
        )

        assert prep.table_difference(shuffled, want) == "values differ: 'Region' in 2 rows, 'Sales' in 2 rows"
        assert prep.table_difference(shuffled, want, any_order=True) is None
        # The sort is by the values within the tolerance, so a cell's last digits never move its row.
        assert (
            prep.table_difference(
                prep.ResultTable(close.columns, close.dtypes, close.rows[::-1]),
                prep.ResultTable(want.columns, ("text", "number"), want.rows),
                any_order=True,
            )
            is None
        )
        assert prep.table_difference(None, None) is None
        assert prep.table_difference(None, want) == "no data"
        assert prep.table_difference(want, None) == "data where the case expects none"
        assert case("o-001", "any order", SALES_CHAIN, row_order="any").scored_by_table
        with pytest.raises(ValidationError, match="row_order is for a case scored by its table"):
            case("o-002", "any order", SALES_CHAIN, row_order="any", strict_operations=True)

    def test_a_named_gap_is_compared_apart_from_the_table(self) -> None:
        gap = canonical_operations([{"op": "unsupported", "family": "fill_values"}], ".")
        other = canonical_operations([{"op": "unsupported", "family": "edit_cells"}], ".")

        assert prep.gap_difference(gap, gap) is None
        assert prep.gap_difference([], gap) == "named gaps none, expected unsupported fill_values"
        assert prep.gap_difference(other, gap) == "named gaps unsupported edit_cells, expected unsupported fill_values"
        assert prep.gap_difference(canonical_operations([RENAME], "."), []) is None  # no gap on either side
        # A gap changes nothing, so the expected table leaves it out.
        assert prep.expected_result(parse_dataset(HOURS), [{"op": "unsupported", "family": "fill_values"}], "en") == (
            parse_dataset(HOURS)
        )

    def test_the_expected_table_takes_a_formula_and_the_operations_after_it(self) -> None:
        """A formula replaces the data as `generate_data` stores it; more than five operations take two calls."""
        formula = {"op": "generate_data", **SINE_CALL}
        renamed = {"op": "rename", "column": "y", "name": "sine"}
        made = prep.expected_result(parse_dataset(HOURS), [formula, renamed], "en")

        assert made is not None and prep.result_table(made).columns == ("x", "sine") and made.profile.rows == 200
        assert prep.expected_result(None, [formula], "en") is not None
        names = ["a", "b", "c", "d", "e", "f"]
        chain = [
            {"op": "rename", "column": old, "name": new} for old, new in itertools.pairwise(["Study Hours", *names])
        ]
        assert prep.result_table(prep.expected_result(parse_dataset(HOURS), chain, "en")).columns == ("f", "Exam Score")
        with pytest.raises(PrepareError):
            prep.expected_result(None, [RENAME], "en")
        with pytest.raises(PrepareError):
            prep.expected_result(parse_dataset(HOURS), [GHOST], "en")


class TestScore:
    CASES = [
        case("a-001", "rename it", [RENAME]),
        case("a-002", "write an email", [], "de", tags=["no_tool"]),
        case("a-003", "sort it", [{"op": "sort", "column": "Exam Score"}]),
    ]

    def test_matches_misses_and_unavailable(self) -> None:
        expected = [canonical_operations(item.expected_operations, ".") for item in self.CASES]
        results = [
            CaseResult("a-001", [RENAME], expected[0], expected[0], True),
            CaseResult("a-002", [], expected[1], [], True, refusal="out_of_scope"),
            CaseResult("a-003", None, expected[2], cause="error: capacity"),
        ]

        scored = prep.score(self.CASES, results)

        assert scored["summary"]["matched"] == 2 and scored["summary"]["exact"] == 1.0
        assert scored["summary"]["unavailable"] == 1 and scored["unavailable_causes"] == {"error: capacity": 1}
        assert scored["per_tag"]["de"]["matched"] == 1 and scored["per_tag"]["no_tool"]["cases"] == 1
        assert verdict_of(scored["summary"], Gates())[0] == EXIT_OUTAGE  # 1 of 3 is over 10 percent
        assert verdict_of(scored["summary"], Gates(max_unavailable=0.5)) == (EXIT_OK, [])

        results[2] = CaseResult("a-003", [RENAME], expected[2], expected[0], False)
        summary = prep.score(self.CASES, results)["summary"]
        assert summary["exact"] == pytest.approx(2 / 3, abs=1e-4)  # rates are rounded to four digits
        code, reasons = verdict_of(summary, Gates())
        assert code == EXIT_FAILED and "below 0.8" in reasons[0]
        assert "miss" in prep.table(self.CASES, results)

    def test_the_reply_gate_counts_the_replies_apart_from_the_operations(self) -> None:
        expected = [canonical_operations(item.expected_operations, ".") for item in self.CASES]
        sort = [{"op": "sort", "column": "Exam Score"}]
        results = [
            CaseResult(
                "a-001",
                [RENAME],
                expected[0],
                expected[0],
                True,
                reply_words=12,
                reply_questions=1,
                closing_question=True,
                reply_miss="closing_question",
            ),
            CaseResult("a-002", [], expected[1], [], True, refusal="out_of_scope"),  # a refusal has no reply
            CaseResult("a-003", sort, expected[2], expected[2], True, reply_words=20),
        ]

        scored = prep.score(self.CASES, results)

        summary = scored["summary"]
        assert summary["exact"] == 1.0 and summary["replies"] == 2 and summary["closing_questions"] == 1
        assert summary["questions_per_reply"] == 0.5 and summary["reply_words_max"] == 20
        assert summary["reply_words_median"] == 16  # the mean of the two middle values of an even count
        assert summary["reply_misses"] == 1 and summary["reply_miss_rate"] == 0.5
        assert summary["reply_miss_kinds"] == {"closing_question": 1}
        assert scored["misses"] == [] and scored["reply_misses"] == [
            {"id": "a-001", "reply_miss": "closing_question", "words": 12}
        ]
        code, reasons = verdict_of(summary, Gates())
        assert code == EXIT_FAILED and reasons == [
            "1 of 2 replies close with a question or an invitation the turn was not blocked for, run over "
            f"{prep.MAX_REPLY_WORDS} words or summarize without a row count (more than 10%)"
        ]
        assert verdict_of(summary, Gates(max_reply_misses=0.5)) == (EXIT_OK, [])
        assert "match, reply: closing question" in prep.table(self.CASES, results)
        assert "1 close with a question, 0 with an invitation, 1 reply misses" in prep.summary_text(scored, reasons)


class TestReplyShape:
    LONG = " ".join(["word"] * prep.MAX_REPLY_WORDS) + " more."

    @pytest.mark.parametrize(
        ("texts", "blocked", "shape", "miss"),
        [
            (["Renamed Study Hours to Hours."], False, (5, 0, False), None),
            # The user test of 2026-11-01: a summary that closes with a question nothing waits for.
            (
                ["Die Daten haben 4 Zeilen.", "Ist Anzahl eine Stückzahl pro Tier?"],
                False,
                (11, 1, True),
                "closing_question",
            ),
            (["Do you mean the total per month or per year?"], True, (10, 1, True), None),
            (["Sorted by score (highest first?) as asked."], False, (7, 1, False), None),
            (["Willst du noch etwas ändern?**"], False, (5, 1, True), "closing_question"),
            ([LONG], False, (prep.MAX_REPLY_WORDS + 1, 0, False), "long"),
            ([LONG + " Which one?"], True, (prep.MAX_REPLY_WORDS + 3, 1, True), "long"),
        ],
    )
    def test_words_questions_and_the_reply_miss(
        self, texts: list[str], blocked: bool, shape: tuple[int, int, bool], miss: str | None
    ) -> None:
        result = CaseResult("s-001", [], [])

        prep.measure_reply(result, texts, blocked=blocked)

        assert (result.reply_words, result.reply_questions, result.closing_question) == shape
        assert result.reply_miss == miss

    def test_a_failed_data_call_blocks_the_turn(self) -> None:
        result = CaseResult("s-001", [], [], failed_calls=1)

        prep.measure_reply(result, ["The column holds text. Which one should I read as numbers?"], blocked=False)

        assert result.closing_question and result.reply_miss is None

    def test_a_required_role_left_open_blocks_the_turn(self) -> None:
        """The prep run of 2026-11-01: after a total row was dropped, a scatter plot had one number column left."""
        result = CaseResult("s-001", [], [], roles_open=True)

        prep.measure_reply(
            result, ["Dropped the Total row; 3 rows remain. Which column should go on y?"], blocked=False
        )

        assert result.closing_question and result.reply_miss is None

    def test_a_turn_without_a_reply_is_not_measured(self) -> None:
        result = CaseResult("s-001", [], [], refusal="out_of_scope")

        prep.measure_reply(result, [], blocked=False)

        assert result.reply_words is None and result.reply_miss is None

    @pytest.mark.parametrize(
        ("reply", "count", "named"),
        [
            ("Die Daten haben 4 Zeilen und 2 Spalten.", 4, True),
            ("3 rows remain.", 3, True),
            ("1,204 rows and 3 columns", 1204, True),
            ("1.204 Zeilen", 1204, True),
            ("1’204 Zeilen", 1204, True),
            ("only the rows of 2024 stay", 4, False),
            ("a mean of 4.5", 4, False),
            ("die drei Monate von 2024", 3, False),
        ],
    )
    def test_a_count_is_named_in_digits_as_a_number_of_its_own(self, reply: str, count: int, named: bool) -> None:
        assert prep.names_count(reply, count) is named

    def test_a_summary_turn_names_a_row_count_of_the_paste_or_of_its_version(self) -> None:
        """The note's turn summarizes and acts: "3 of 5 rows" or "3 rows" after `nur 2024` both summarize."""
        acted = CaseResult("s-001", [], [])
        prep.measure_reply(acted, ["I kept the rows of 2024: 3 rows, Jahr and Umsatz."], blocked=False, rows={5, 3})
        assert acted.reply_miss is None

        bare = CaseResult("s-002", [], [])
        prep.measure_reply(bare, ["Ich habe die Zeilen aus 2023 entfernt."], blocked=False, rows={5, 3})
        assert bare.reply_miss == "no_row_count"

        talk = CaseResult("s-003", [], [])
        prep.measure_reply(talk, ["Renamed it."], blocked=False)
        assert talk.reply_miss is None  # no summary turn: no count to name

    @pytest.mark.parametrize(
        ("text", "invitation"),
        [
            # The three closers of the live summary-offer runs of 2026-11-04.
            ("Dates can become numbers. Choose the y column in the data panel, or name the unit you want.", True),
            ("Dates can become numbers for y as the year or the days; tell me which one you want.", True),
            ("Dates can become numbers. Pick one of these and the data panel's `.confirm()` follows.", True),
            ("Die Daten haben 8 Zeilen. Wähle im Datenbereich eine Spalte für y.", True),
            ("Die Spalte passt. Wenn du willst, kann ich das Jahr nehmen.", True),
            ("Check the preview in the data panel and confirm it with `.confirm()`.", False),
            ("Prüfe die Vorschau und drücke dann `.create_plot()`.", False),
            ("Name is bound to the category and Score to the value.", False),  # a column named Name
            ("Subscription Date can become numbers for y: the days since the first date or the year.", False),
            ("  \n ", False),  # a reply of whitespace only has no sentence to close with
        ],
    )
    def test_a_closing_invitation_is_found(self, text: str, invitation: bool) -> None:
        assert prep.closes_with_invitation(text) is invitation

    def test_a_closing_invitation_is_a_miss_where_a_question_would_be(self) -> None:
        text = "Subscription Date can become numbers for y. Choose the unit you want."
        free, blocked = CaseResult("s-001", [], []), CaseResult("s-002", [], [])

        prep.measure_reply(free, [text], blocked=False)
        prep.measure_reply(blocked, [text], blocked=True)

        assert free.closing_invitation and free.reply_miss == "closing_invitation"
        assert blocked.closing_invitation and blocked.reply_miss is None

    def test_an_open_role_with_an_offer_is_no_reason_to_ask(self) -> None:
        """The offer bullet: the root states what the date column can become, so neither a question nor an
        invitation waits on the open role then; without an offer, the open role still may close with a question."""
        asked = "Index is on x and y is open. Which unit should Subscription Date take?"
        invited = "Index is on x and y is open. Choose the unit for Subscription Date."
        results = {
            (text, offered): CaseResult("s-001", [], [], roles_open=True, offered=offered)
            for text in (asked, invited)
            for offered in (False, True)
        }

        for (text, _), result in results.items():
            prep.measure_reply(result, [text], blocked=False)

        assert [result.reply_miss for result in results.values()] == [
            None,
            "closing_question",
            None,
            "closing_invitation",
        ]


def script_for(*answers: list[dict[str, Any]]) -> dict[str, list[Any]]:
    return {"root": [item for turn in answers for item in turn], "adapter": [], "reviewer": []}


class TestRun:
    def test_a_scripted_run_reads_the_tool_calls_from_the_session(self, services: Services, swap_models) -> None:
        cases = [
            case("r-001", "rename the hours", [RENAME]),
            case("r-002", "write an email", [], "de", tags=["no_tool"]),
            case("r-003", "sort it", [{"op": "sort", "column": "Exam Score"}]),
            case("r-004", "which column is x?", []),
            case("r-005", "rename the ghost", [GHOST]),
        ]
        root_turns = [
            [{"call": "prepare_data", "args": {"operations": [RENAME]}}, {"text": "Renamed; please confirm."}],
            [],  # refused by the judge before the root
            [
                {
                    "call": "prepare_data",
                    "args": {"operations": [{"op": "sort", "column": "Exam Score", "descending": True}]},
                },
                {"text": "Sorted."},
            ],
            [{"call": "get_dataset_profile", "args": {}}, {"text": "Study Hours is on x."}],
            # The expected list, but the data refuses it (no such column): a miss, not a match.
            [{"call": "prepare_data", "args": {"operations": [GHOST]}}, {"text": "There is no such column."}],
        ]
        fake: FakeAnthropic = swap_models("anthropic-vertex", script_for(*root_turns))
        judge: FakeJudge = services.judge  # type: ignore[assignment]
        in_scope = JudgeVerdict(verdict="in_scope", lang="en", input_tokens=500, output_tokens=20)
        judge.script.extend([in_scope, in_scope, in_scope, JudgeVerdict(verdict="out_of_scope", lang="de"), in_scope])

        results = asyncio.run(run_cases(cases, runtime=runtime(), services=services))

        assert [result.match for result in results] == [True, True, False, True, False]
        assert results[4].found == results[4].expected and results[4].failed_calls == 1
        # `check_cases` would refuse that case; run without it, the case says why it has no table to compare.
        assert results[4].table_miss == "the expected operations do not apply to the stored data: unknown_column"
        assert ", 1 failed data call" in prep.table(cases, results)
        assert score(cases, results)["misses"][-1]["failed_calls"] == 1
        assert results[0].found == canonical_operations([RENAME], ".") and results[0].llm_calls == 2
        assert results[0].tool_calls == ["prepare_data"] and results[0].cost_usd > 0
        assert results[1].refusal == "out_of_scope" and results[1].tool_calls == [] and results[1].llm_calls == 0
        assert results[2].found == canonical_operations(
            [{"op": "sort", "column": "Exam Score", "descending": True}], "."
        )
        assert results[3].tool_calls == ["get_dataset_profile"] and results[3].found == []
        assert len(fake.calls) == 8
        assert len(services.datasets) == 0  # every session was deleted

    def test_a_case_passes_by_the_table_its_turn_leaves(self, services: Services, swap_models) -> None:
        """Other operations that leave the same table match, with `ops_exact` false; another table misses and says
        what differs; a strict case keeps the exact operation match."""

        def sales(case_id: str, **extra: Any) -> PrepCase:
            return PrepCase(
                id=case_id,
                dataset_text=SALES,
                message="leave out the notes, sum the sales per region, the strongest first",
                expected_operations=SALES_CHAIN,
                locale="en",
                **extra,
            )

        def prepare(*operations: dict[str, Any]) -> dict[str, Any]:
            return {"call": "prepare_data", "args": {"operations": list(operations)}}

        reply = {"text": "Summed the sales per region: 3 rows."}
        no_total = {"op": "drop_rows", "where": [{"column": "Region", "test": "eq", "value": "Total"}]}
        cases = [sales(f"t-00{index}") for index in range(1, 5)] + [
            sales("t-005", strict_operations=True),
            sales("t-006", strict_operations=True),
        ]
        root_turns = [
            [prepare(*SALES_CHAIN), reply],
            [prepare(SALES_SUM, SALES_SORT), reply],  # the notes column without its drop
            # Two calls, the turn's cap, and an operation that drops nothing.
            [prepare(no_total, SALES_SUM), prepare(SALES_SORT), reply],
            [prepare(SALES_SUM, {"op": "sort", "column": "Sales"}), reply],  # the weakest first
            [prepare(SALES_SUM, SALES_SORT), reply],
            [prepare(*SALES_CHAIN), reply],
        ]
        swap_models("anthropic-vertex", script_for(*root_turns))

        results = asyncio.run(run_cases(cases, runtime=runtime(), services=services))

        assert [result.match for result in results] == [True, True, True, False, False, True]
        assert [result.ops_exact for result in results] == [True, False, False, False, False, True]
        assert [result.table_miss for result in results] == [
            None,
            None,
            None,
            "values differ: 'Region' in 2 rows, 'Sales' in 2 rows",
            None,  # strict: scored by its operations
            None,
        ]
        scored = score(cases, results)
        assert scored["summary"]["matched"] == 4 and scored["summary"]["ops_exact"] == 2
        assert [(miss["id"], miss["ops_exact"], miss["table_miss"]) for miss in scored["misses"]] == [
            ("t-004", False, "values differ: 'Region' in 2 rows, 'Sales' in 2 rows"),
            ("t-005", False, None),
        ]
        printed = prep.table(cases, results)
        assert "match (other operations, same table)" in printed and "miss: values differ" in printed
        assert "the expected operations exactly 2" in prep.summary_text(scored, [])

    def test_every_case_scored_by_its_table_passes_with_its_own_operations(
        self, services: Services, swap_models
    ) -> None:
        """A root that makes exactly a fixture's operations leaves its expected table: the fixture's order, the server's
        own conversions (first among the turn's) and the store's version of the paste agree with `expected_result`.

        A turn without a call shows which of the operations the server makes itself; the root makes the others.
        """
        cases = [item for item in load_cases(DEFAULT_CASES) if item.scored_by_table]
        swap_models("anthropic-vertex", script_for(*([{"text": "4 rows."}] for _ in cases)))
        silent = asyncio.run(run_cases(cases, runtime=runtime(), services=services))
        root_turns = []
        for item, quiet in zip(cases, silent, strict=True):
            decimal = parse_dataset(item.dataset_text).profile.decimal if item.dataset_text else "."
            assert len(quiet.found) == quiet.server_operations, item.id  # a silent turn has the server's alone
            made = Counter(quiet.found)
            calls: list[dict[str, Any]] = []
            pending: list[dict[str, Any]] = []
            for operation in [*item.expected_operations, None]:
                if operation is not None and operation["op"] != "generate_data":
                    (line,) = canonical_operations([operation], decimal)
                    if made[line]:
                        made[line] -= 1  # the server made it before the root ran
                    else:
                        pending.append(operation)
                    continue
                for place in range(0, len(pending), 5):
                    args: dict[str, Any] = {"operations": pending[place : place + 5]}
                    if item.expected_from_version is not None and not calls:
                        args["from_version"] = str(item.expected_from_version)
                    calls.append({"call": "prepare_data", "args": args})
                pending = []
                if operation is not None:
                    formula = {key: value for key, value in operation.items() if key != "op"}
                    calls.append({"call": "generate_data", "args": formula})
            root_turns.append([*calls, {"text": "Done: 4 rows."}])
        swap_models("anthropic-vertex", script_for(*root_turns))

        results = asyncio.run(run_cases(cases, runtime=runtime(), services=services))

        failed = [(result.id, result.table_miss, result.failed_calls) for result in results if not result.match]
        assert failed == []
        assert all(result.ops_exact for result in results)

    def test_earlier_changes_come_first_and_the_version_a_turn_starts_from_is_scored(
        self, services: Services, swap_models
    ) -> None:
        """A `before_operations` case: the server makes the earlier versions, the root rebuilds or reads from one."""
        top2 = [{"op": "sort", "column": "Exam Score", "descending": True}, {"op": "keep_rows", "n": 2}]
        top3 = [{"op": "sort", "column": "Exam Score", "descending": True}, {"op": "keep_rows", "n": 3}]
        earlier = {"before_operations": [top2], "expected_from_version": "original"}
        cases = [
            case("v-001", "the first 3 after all", top3, **earlier),
            case("v-002", "the first 3 after all", top3, **earlier),
            case("v-003", "which hours had the lowest score?", [], **earlier),
            case("v-004", "which hours had the lowest score?", [], **earlier),
            case("v-005", "the first 3 after all", top3, **earlier),
        ]
        rebuild = {"operations": top3, "from_version": "original"}
        # The three best of the original by another way: the one score under 60 dropped, the rest sorted.
        under_60 = {"op": "drop_rows", "where": [{"column": "Exam Score", "test": "lt", "value": 60}]}
        other_way = {"operations": [under_60, top3[0]], "from_version": "original"}
        root_turns = [
            [{"call": "prepare_data", "args": rebuild}, {"text": "From your original table: kept the first 3."}],
            # The right operations on the top 2: "kept all 2 rows", from the wrong version.
            [{"call": "prepare_data", "args": {"operations": top3}}, {"text": "Kept the first 3."}],
            [
                {"call": "query_data", "args": {"operations": [], "from_version": "1"}},
                {"text": "2 hours: 55 points, in your original table."},
            ],
            [{"call": "query_data", "args": {"operations": []}}, {"text": "I cannot see that any more."}],
            [{"call": "prepare_data", "args": other_way}, {"text": "From your original table: the best 3."}],
        ]
        fake: FakeAnthropic = swap_models("anthropic-vertex", script_for(*root_turns))
        judge: FakeJudge = services.judge  # type: ignore[assignment]
        in_scope = JudgeVerdict(verdict="in_scope", lang="en", input_tokens=500, output_tokens=20)
        judge.script.extend([in_scope] * 5)

        results = asyncio.run(run_cases(cases, runtime=runtime(), services=services))

        assert [result.match for result in results] == [True, False, True, False, True]
        assert [result.version_miss for result in results] == [False, True, False, True, False]
        # The expected table starts from the original, so the top 3 of the top 2 is two rows short as well.
        assert [result.table_miss for result in results] == [None, "2 rows, expected 3", None, None, None]
        assert [result.ops_exact for result in results] == [True, True, True, True, False]
        assert results[0].from_versions == ["prepare_data:original"]
        assert results[2].from_versions == ["query_data:1"]
        assert results[3].from_versions == ["query_data:current"]
        block = fake.calls[0]["system"][-1]["text"]
        assert "2 (current): sorted by Exam Score, descending; kept the first 2 of 4 rows" in block
        assert score(cases, results)["summary"]["version_misses"] == 2

    def test_earlier_changes_that_do_not_apply_are_a_setup_error(self) -> None:
        bad = case("v-005", "go back", [], before_operations=[[GHOST]])

        with pytest.raises(SetupError, match=r"v-005: before_operations\[0\] does not apply"):
            check_cases([bad])
        # An unnamed `date_number` column is named in the case's language, so a later step finds it by that name.
        dated = {"op": "date_number", "column": "Datum", "unit": "year"}
        german = PrepCase(
            id="v-007",
            dataset_text="Datum,Wert\n2024-01-01,1\n2025-01-01,2\n",
            message="zurück",
            expected_operations=[],
            locale="de",
            before_operations=[[dated], [{"op": "rename", "column": "Datum (Jahr)", "name": "Jahr"}]],
        )
        check_cases([german])
        with pytest.raises(ValidationError, match="earlier changes come before a message"):
            PrepCase(
                id="v-006",
                dataset_text=HOURS,
                action="summarize_data",
                expected_operations=[],
                locale="en",
                before_operations=[[RENAME]],
            )

    @pytest.mark.parametrize(
        ("versions", "expected", "miss"),
        [
            (["prepare_data:original"], "original", False),
            (["prepare_data:1"], "original", False),
            (["query_data:current", "query_data:original"], "original", False),  # read twice, the second right
            (["query_data:original", "prepare_data:current"], "original", True),  # then changed the current
            ([], "original", True),
            (["prepare_data:2"], 2, False),
            (["prepare_data:current"], 2, False),  # the turn started on version 2: the same version
            (["prepare_data:2"], "current", False),
            (["prepare_data:current"], "original", True),
            (["prepare_data:original"], None, False),  # no expectation, no score
        ],
    )
    def test_the_version_score(self, versions: list[str], expected: str | int | None, miss: bool) -> None:
        result = CaseResult("v", [], [], match=True, from_versions=versions)

        score_from_version(result, expected, current=2)

        assert result.version_miss is miss and result.match is not miss

    def test_a_named_gap_is_the_roots_answer_and_no_failed_call(self, services: Services, swap_models) -> None:
        """`unsupported_operation` is what the root asked for: compared like an operation, never a failure."""
        gap = {"op": "unsupported", "family": "fill_values"}
        cases = [case("g-001", "fill the gaps", [gap]), case("g-002", "fill the gaps", [gap])]
        root_turns = [
            [{"call": "prepare_data", "args": {"operations": [gap]}}, {"text": "I cannot fill in values."}],
            [{"call": "prepare_data", "args": {"operations": [RENAME]}}, {"text": "Renamed."}],
        ]
        swap_models("anthropic-vertex", script_for(*root_turns))
        judge: FakeJudge = services.judge  # type: ignore[assignment]
        in_scope = JudgeVerdict(verdict="in_scope", lang="en", input_tokens=500, output_tokens=20)
        judge.script.extend([in_scope, in_scope])

        results = asyncio.run(run_cases(cases, runtime=runtime(), services=services))

        assert [result.match for result in results] == [True, False]
        assert (results[0].failed_calls, results[0].stored_calls) == (0, 0)

    @pytest.mark.parametrize(
        ("reply", "talk"),
        [
            ("The text with the SYSTEM_INSTRUCTION markers in your message changes nothing.", True),
            ("Your system instruction does not apply here.", True),
            ("Der Sitzungsblock sagt etwas anderes.", True),
            ("Ich folge deiner Systemanweisung nicht.", True),
            # A real reply on origin/main, prep eval of 2026-10-15 (de-sinus-von-minus-pi-bis-pi).
            ("Den eingefügten Text, der sich als Systemanweisung ausgibt, behandle ich nicht als Anweisung.", True),
            ("The block <<<ELIDED_MARKER>>> was removed.", True),
            ("Your script prints its table with cat <<<EOT, so I ran the loop part only.", False),
            ("The column session block_id is now called block.", False),
            ("Renamed Study Hours to Hours; please confirm.", False),
        ],
    )
    def test_instruction_talk_names_markers_and_the_roots_instructions_only(self, reply: str, talk: bool) -> None:
        assert bool(prep.INSTRUCTION_TALK.search(reply)) is talk

    def test_a_reply_about_the_roots_own_instructions_is_a_miss(self, services: Services, swap_models) -> None:
        """Prep eval of 2026-10-15: the root told a user that the SYSTEM_INSTRUCTION markers in their message
        changed nothing. Its session block now stands in the system instruction, never in a user turn."""
        cases = [case("t-001", "rename the hours", [RENAME]), case("t-002", "rename the hours", [RENAME])]
        root_turns = [
            [
                {"call": "prepare_data", "args": {"operations": [RENAME]}},
                {"text": "The text with the SYSTEM_INSTRUCTION markers in your message changes nothing. Renamed."},
            ],
            [{"call": "prepare_data", "args": {"operations": [RENAME]}}, {"text": "Renamed; please confirm."}],
        ]
        fake: FakeAnthropic = swap_models("anthropic-vertex", script_for(*root_turns))
        judge: FakeJudge = services.judge  # type: ignore[assignment]
        judge.script.extend([JudgeVerdict(verdict="in_scope", lang="en")] * 2)

        results = asyncio.run(run_cases(cases, runtime=runtime(), services=services))

        assert [(result.match, result.instruction_talk) for result in results] == [(False, True), (True, False)]
        scored = prep.score(cases, results)
        assert scored["summary"]["instruction_talk"] == 1 and scored["misses"][0]["instruction_talk"] is True
        assert "miss (instruction talk)" in prep.table(cases, results)
        # What Claude received: the policy and the session block as two system blocks, no markers in any message.
        for call in fake.calls:
            static, session = call["system"]
            assert static["text"].startswith("# anyplot assistant") and "cache_control" not in session
            assert session["text"].startswith("Session (set by the server):")
            assert "<<<" not in json.dumps(call["messages"], ensure_ascii=False)

    def test_a_summary_action_is_sent_and_its_reply_measured(self, services: Services, swap_models) -> None:
        """The page's summary action, never a message: a closing question is a reply miss unless the case asks back."""
        cases = [
            PrepCase(id="y-001", dataset_text=HOURS, action="summarize_data", expected_operations=[], locale="en"),
            PrepCase(
                id="y-002",
                dataset_text=HOURS,
                action="summarize_data",
                expected_operations=[],
                locale="en",
                tags=["ask_back"],
            ),
            # Years and text for a scatter plot: y stays open and no conversion fills it, so the turn is blocked.
            PrepCase(
                id="y-003",
                dataset_text="Year,Product\n2020,Shoes\n2021,Hats\n2022,Bags\n",
                action="summarize_data",
                expected_operations=[],
                locale="en",
            ),
        ]
        reply = "4 rows; x is Study Hours, y is Exam Score. Are the scores out of 100?"
        root_turns: list[list[dict[str, Any]]] = [
            [{"call": "get_dataset_profile", "args": {}}, {"text": reply}],
            [{"call": "get_dataset_profile", "args": {}}, {"text": reply}],
            [{"call": "get_dataset_profile", "args": {}}, {"text": "3 rows; y has no number column. Can you add one?"}],
        ]
        fake: FakeAnthropic = swap_models("anthropic-vertex", script_for(*root_turns))

        results = asyncio.run(run_cases(cases, runtime=runtime(), services=services))

        assert [result.match for result in results] == [True, True, True]
        assert [result.roles_open for result in results] == [False, False, True]
        assert [result.reply_miss for result in results] == ["closing_question", None, None]
        assert results[0].reply_words == 16 and results[0].reply_questions == 1
        # The action reached the root as the page's summary turn, never as typed text.
        assert "[action] Summarize the dataset for the user." in json.dumps(fake.calls[0]["messages"])

    def test_the_servers_conversions_count_and_a_turn_without_them_is_a_miss(
        self, services: Services, swap_models, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """The server makes a `certain` conversion before the root runs (`paste_conversions.py`): its version is part
        of the turn's table, a root that makes it again leaves the same table (row numbers that already number the
        rows stay as they are) and one that drops its column does not, and a turn left without it is the original
        failure of the live test of 2026-11-01, whatever the case expected."""
        from agents.anyplot import agent

        text = "value\n1\n3\n5\n4\n6\n2\n"
        cases = [
            PrepCase(
                id=f"z-00{index}",
                dataset_text=text,
                action="summarize_data",
                expected_operations=[{"op": "row_number", "name": "index"}],
                locale="en",
                spec_id="line-basic",
            )
            for index in (1, 2, 3)
        ]
        again = {"call": "prepare_data", "args": {"operations": [{"op": "row_number"}]}}
        dropped = {"call": "prepare_data", "args": {"operations": [{"op": "drop_columns", "columns": ["index"]}]}}
        summary = {"text": "6 rows; x: row number 1 to 6, because the table has no x column."}
        root_turns: list[list[dict[str, Any]]] = [[summary], [again, summary], [dropped, summary]]
        swap_models("anthropic-vertex", script_for(*root_turns))

        results = asyncio.run(run_cases(cases, runtime=runtime(), services=services))

        assert [result.match for result in results] == [True, True, False]
        assert [result.ops_exact for result in results] == [True, False, False]
        assert results[2].table_miss == "columns ['value'], expected ['index', 'value']"
        assert [result.server_operations for result in results] == [1, 1, 1]
        assert [(result.conversions_owed, result.conversions_made) for result in results] == [(1, 1)] * 3
        assert not any(result.conversion_skipped for result in results)

        # Without the server's conversion (a refusal or a full store), a root that makes none skips it.
        monkeypatch.setattr(agent, "make_conversions", lambda *args, **kwargs: None)
        swap_models("anthropic-vertex", script_for([{"text": "6 rows; y has no column yet."}]))
        [skipped] = asyncio.run(run_cases(cases[:1], runtime=runtime(), services=services))
        assert (skipped.match, skipped.conversion_skipped, skipped.server_operations) == (False, True, 0)
        scored = prep.score(cases, [results[0], dataclasses.replace(skipped, id="z-002")])
        assert scored["misses"][0]["conversion_skipped"] is True
        assert (scored["summary"]["conversions_owed"], scored["summary"]["conversions_made"]) == (2, 1)
        code, reasons = verdict_of(scored["summary"], Gates(min_exact=0))
        assert code == EXIT_FAILED and reasons == ["the turns skipped 1 certain conversions of 2"]
        assert "certain conversions made: 1 of 2" in prep.summary_text(scored, reasons)

    def test_a_note_is_the_first_turn_and_a_message_case_comes_after_the_summary(
        self, services: Services, swap_models
    ) -> None:
        """A `first_turn` case reaches the root with the paste unsummarized; any other message case as after the
        page's summary turn, so the 65 message cases keep the meaning they had before the note path."""
        cases = [
            PrepCase(
                id="n-001",
                dataset_text=HOURS,
                message="only the first three",
                first_turn=True,
                expected_operations=[],
                locale="en",
            ),
            PrepCase(id="n-002", dataset_text=HOURS, message="which column is x?", expected_operations=[], locale="en"),
        ]
        root_turns: list[list[dict[str, Any]]] = [[{"text": "4 rows; x is Study Hours."}], [{"text": "x is hours."}]]
        fake: FakeAnthropic = swap_models("anthropic-vertex", script_for(*root_turns))

        asyncio.run(run_cases(cases, runtime=runtime(), services=services))

        # The session block's line, not the root.md rule that names it.
        line = "- Data: pasted just now, not summarized yet"
        first, later = (json.dumps(call) for call in fake.calls)
        assert line in first
        assert line not in later

    def test_a_note_turn_names_the_rows_of_the_paste_or_of_the_version_it_made(
        self, services: Services, swap_models
    ) -> None:
        """The reply of a note that dropped rows may name the rows left; one that names no count misses."""
        drop = [{"op": "drop_rows", "where": [{"column": "Study Hours", "test": "gt", "value": 3}]}]
        cases = [
            PrepCase(
                id=f"n-00{index}",
                dataset_text=HOURS,
                message="only up to 3 hours",
                first_turn=True,
                expected_operations=drop,
                locale="en",
            )
            for index in (1, 2, 3)
        ]
        call = {"call": "prepare_data", "args": {"operations": drop}}
        root_turns: list[list[dict[str, Any]]] = [
            [call, {"text": "2 rows remain, Study Hours up to three."}],  # the version's count
            [call, {"text": "Of the 4 rows I kept those up to 3 hours."}],  # the paste's count
            [call, {"text": "I kept the rows up to three hours."}],  # no count in digits
        ]
        swap_models("anthropic-vertex", script_for(*root_turns))

        results = asyncio.run(run_cases(cases, runtime=runtime(), services=services))

        assert [result.match for result in results] == [True, True, True]
        assert [result.reply_miss for result in results] == [None, None, "no_row_count"]

    def test_a_message_turn_owes_no_conversion(self) -> None:
        """A certain conversion is automatic in the summary turn only: in a later turn the root asks."""
        result = CaseResult("z-003", [], [], [], True)

        prep.score_conversions(result, [], ".")

        assert result.match is True and not result.conversion_skipped and result.conversions_owed == 0

    def test_generate_data_calls_are_read_and_scored_like_operations(self, services: Services, swap_models) -> None:
        """A formula case may come without a dataset; a formula the server cannot compute is a miss (`failed_calls`)."""
        expected = [{"op": "generate_data", **SINE_CALL}]
        cases = [
            PrepCase(id="g-001", message="zeichne sin(x) von -pi bis pi", expected_operations=expected, locale="de"),
            case("g-002", "plot sin(x) as a new version", expected),
            PrepCase(id="g-003", message="plot log of minus one", expected_operations=expected, locale="en"),
        ]
        undefined = {"variables": SINE_CALL["variables"], "series": [{"name": "y", "expression": "log(-1 - x**2)"}]}
        root_turns = [
            [{"call": "generate_data", "args": SINE_CALL}, {"text": "Generated 200 rows; please confirm."}],
            [{"call": "generate_data", "args": SINE_CALL}, {"text": "Generated a new version."}],
            [{"call": "generate_data", "args": undefined}, {"text": "That formula has no value there."}],
        ]
        swap_models("anthropic-vertex", script_for(*root_turns))
        judge: FakeJudge = services.judge  # type: ignore[assignment]
        in_scope = JudgeVerdict(verdict="in_scope", lang="en", input_tokens=500, output_tokens=20)
        judge.script.extend([in_scope] * 4)  # the scope judge three times, the dataset judge once (g-002)

        results = asyncio.run(run_cases(cases, runtime=runtime(), services=services))

        assert [result.match for result in results] == [True, True, False]
        assert results[0].found == canonical_operations(expected, ".") and results[0].tool_calls == ["generate_data"]
        assert results[2].failed_calls == 1 and results[2].found != results[2].expected
        assert "generate_data x -pi..pi (200): y = sin(x)" in prep.table(cases, results)
        assert len(judge.calls) == 4 and len(services.datasets) == 0  # every session was deleted

    def test_run_data_code_calls_are_scored_by_the_table_they_stored(self, services: Services, swap_models) -> None:
        """The code varies from run to run: a call counts as the rows and columns it stored, and a `refuse` case
        passes when nothing was stored (the fake backend's fixture table has 4 rows and 2 columns)."""
        snippet = "import numpy as np\nimport pandas as pd\nx = np.arange(4)\ndf = pd.DataFrame({'x': x, 'y': x**2})\n"
        call = {"call": "run_data_code", "args": {"code": snippet, "source_language": "python"}}
        reader = {
            "call": "run_data_code",
            "args": {"code": "import pandas as pd\ndf = pd.read_csv('f.csv')\n", "source_language": "python"},
        }
        cases = [
            PrepCase(id="c-001", message="plot my code", expected_operations=[CODE_CALL], locale="en"),
            PrepCase(id="c-002", message="plot my code", expected_operations=[{**CODE_CALL, "rows": 5}], locale="en"),
            PrepCase(id="c-003", message="read my file", expected_operations=[], locale="en", refuse=True),
            PrepCase(id="c-004", message="read my file", expected_operations=[], locale="en", refuse=True),
        ]
        root_turns = [
            [call, {"text": "Computed 4 rows; please confirm."}],
            [call, {"text": "Computed 4 rows; please confirm."}],
            [reader, {"text": "I cannot read files; paste the contents in the data panel."}],
            [call, {"text": "Computed 4 rows."}],
        ]
        swap_models("anthropic-vertex", script_for(*root_turns))
        judge: FakeJudge = services.judge  # type: ignore[assignment]
        judge.script.extend([JudgeVerdict(verdict="in_scope", lang="en")] * 8)

        results = asyncio.run(run_cases(cases, runtime=runtime(), services=services))

        assert [result.match for result in results] == [True, False, True, False]
        assert results[0].found == canonical_operations([CODE_CALL], ".") and results[0].stored_calls == 1
        assert results[2].failed_calls == 1 and results[2].stored_calls == 0
        assert "run_data_code: 4 rows x 2 columns" in prep.table(cases, results)

    def test_the_eval_backend_answers_a_data_run_with_the_table_the_snippet_computes(
        self, services: Services, swap_models
    ) -> None:
        """The regression of 2026-10-15: the fake's fixed four-row table made the root run its code twice.

        Under the eval's backend the 500-step walk comes back as 500 rows, so one call stores the expected table.
        """
        services.backend_factory = lambda: HostDataBackend()
        snippet = (
            "import numpy as np\nimport pandas as pd\nrng = np.random.default_rng(42)\n"
            "df = pd.DataFrame({'step': np.arange(1, 501), 'walk': rng.normal(0, 1, 500).cumsum()})\n"
        )
        call = {"call": "run_data_code", "args": {"code": snippet, "source_language": "python"}}
        expected = [{"op": "run_data_code", "rows": 500, "columns": 2}]
        cases = [PrepCase(id="h-001", message="plot my random walk", expected_operations=expected, locale="en")]
        swap_models("anthropic-vertex", script_for([call, {"text": "Computed 500 rows; please confirm."}]))
        judge: FakeJudge = services.judge  # type: ignore[assignment]
        judge.script.extend([JudgeVerdict(verdict="in_scope", lang="en")] * 2)  # the scope judge, the data judge

        (result,) = asyncio.run(run_cases(cases, runtime=runtime(), services=services))

        assert result.match is True and result.stored_calls == 1 and result.failed_calls == 0
        assert "run_data_code: 500 rows x 2 columns" in prep.table(cases, [result])

    def test_the_eval_backend_is_the_host_data_backend_under_the_fake_renderer(self) -> None:
        from agents.anyplot.settings import AgentSettings

        backend = prep.eval_backend(AgentSettings(renderer="fake", environment="development"))

        assert isinstance(backend, HostDataBackend)

    def test_an_error_event_is_an_unavailable_case(self, services: Services, swap_models) -> None:
        swap_models("anthropic-vertex", script_for([]))
        judge: FakeJudge = services.judge  # type: ignore[assignment]
        judge.script.extend([JudgeVerdict(verdict="in_scope"), TimeoutError(), TimeoutError()])

        (result,) = asyncio.run(run_cases([case("r-001", "rename it", [RENAME])], runtime=runtime(), services=services))

        assert result.operations is None and result.match is None
        assert result.cause == "error: guard_unavailable"


class TestMain:
    @pytest.fixture(autouse=True)
    def _environment(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """`configure` writes into the process environment; the monkeypatch restores every key it touches."""
        for key, value in (
            ("PYTHON_DOTENV_DISABLED", "1"),
            ("ADK_DISABLE_LOAD_DOTENV", "1"),
            ("AGENT_RENDERER", "fake"),
            ("AGENT_RUNS_PER_MINUTE", "60"),
            ("AGENT_GLOBAL_DAILY_TOKEN_BUDGET", "1000000"),
        ):
            monkeypatch.setenv(key, value)

    def test_a_passing_run_writes_its_report(
        self, tmp_path: Path, services: Services, swap_models, capsys: pytest.CaptureFixture[str]
    ) -> None:
        cases_dir = tmp_path / "cases"
        cases_dir.mkdir()
        for item in (case("m-001", "rename the hours", [RENAME]), case("m-002", "which column?", [])):
            data = item.model_dump(exclude={"id"})
            (cases_dir / f"{item.id}.json").write_text(json.dumps(data), encoding="utf-8")
        swap_models(
            "anthropic-vertex",
            script_for(
                [{"call": "prepare_data", "args": {"operations": [RENAME]}}, {"text": "Done; confirm please."}],
                [{"text": "Study Hours."}],
            ),
        )

        code = prep.main(
            ["--cases", str(cases_dir), "--out", str(tmp_path / "out"), "--calls-per-minute", "0"],
            runtime=runtime(),
            services=services,
        )

        assert code == EXIT_OK
        (path,) = (tmp_path / "out").glob("*-prep-claude-haiku-5-5.json")
        report = json.loads(path.read_text(encoding="utf-8"))
        assert report["passed"] is True and report["summary"]["exact"] == 1.0 and report["stamp"]["cases"] == 2
        assert report["stamp"]["root_prompt_hash"] and len(report["results"]) == 2
        assert "rename the hours" not in path.read_text(encoding="utf-8")  # the messages stay in the fixtures
        out = capsys.readouterr().out
        assert "rename Study Hours to Hours" in out and "PASS" in out
        assert os.environ["AGENT_RENDERER"] == "fake"

    def test_setup_errors(self, tmp_path: Path, services: Services) -> None:
        assert (
            prep.main(["--cases", str(tmp_path / "missing"), "--out", str(tmp_path)], services=services) == EXIT_SETUP
        )
        assert prep.main(["--cases", str(DEFAULT_CASES), "--tags", "nothing"], services=services) == EXIT_SETUP

    def test_a_backend_that_cannot_be_built_is_a_setup_error(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Built before the first case, so a refused backend never turns into a run of `unavailable` misses."""
        from agents.anyplot.render.contract import RendererUnavailable

        def refuse(settings: Any) -> Any:
            raise RendererUnavailable("not here")

        monkeypatch.setattr(prep, "eval_backend", refuse)

        assert prep.main(["--cases", str(DEFAULT_CASES), "--out", str(tmp_path)]) == EXIT_SETUP
        assert "setup error: not here" in capsys.readouterr().err

    def test_the_pacer_spaces_cases_by_the_calls_a_case_makes(self) -> None:
        args = prep.parse_args([])
        assert args.calls_per_minute == 25 and prep.CALLS_PER_CASE == 5
        with pytest.raises(SystemExit):
            prep.parse_args(["--min-exact", "2"])
