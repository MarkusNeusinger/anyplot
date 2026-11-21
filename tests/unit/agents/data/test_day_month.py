"""`ColumnProfile.day_month`: the order a date column's day and month were read in, while its cells read both ways.

The root reads the profile without its warnings (`briefs.profile_json`), so the parser's note that it read
`03/04/2024` day first never reached it. Told "the dates are in month/day/year order", it saw only the ISO cells
(`2024-04-03`) and answered that they already were (eval case `prep/en-month-day-order`). The field states the
reading in the profile itself. It is read from the same warnings `prepare_data` swaps by (`parse.day_month_orders`),
so the field and the swap never disagree.
"""

from dataclasses import replace
from types import SimpleNamespace
from typing import Any, cast

import pytest
from pydantic import TypeAdapter, ValidationError

from agents.anyplot.agent import profile_block
from agents.anyplot.briefs import profile_json, trimmed_profiles
from agents.anyplot.data.parse import MAX_COMPUTED_BYTES, ParsedDataset, parse_dataset, with_day_month, with_warning
from agents.anyplot.data.prepare import Operation, _Carried, apply_and_parse, apply_operations, with_date_notes
from agents.anyplot.dev_fixture import snapshot_from_repo
from agents.anyplot.schemas import MAX_WARNINGS, ColumnProfile, DatasetProfile
from agents.anyplot.telemetry import profile_fields
from agents.anyplot.tools.session import profile_result


EVAL_TABLE = "date,visits\n03/04/2024,10\n05/06/2024,12\n07/08/2024,9\n09/10/2024,14\n11/12/2024,11\n"
"""The eval case's table: every day at most 12, so each date reads both ways."""
OPERATIONS = TypeAdapter(list[Operation])
MONTH_FIRST = {"op": "set_type", "column": "date", "type": "datetime", "date_format": "MM/DD/YYYY"}
DAY_FIRST = {"op": "set_type", "column": "date", "type": "datetime", "date_format": "DD/MM/YYYY"}


def step(parsed: ParsedDataset, *operations: dict[str, Any]) -> ParsedDataset:
    """The next version as `prepare_data` stores it (`apply_and_parse`)."""
    _, after = apply_and_parse(parsed, OPERATIONS.validate_python(list(operations)))
    return after


def day_month(parsed: ParsedDataset) -> dict[str, str | None]:
    return {column.name: column.day_month for column in parsed.profile.columns}


def agrees(parsed: ParsedDataset) -> bool:
    """Whether the field names exactly the orders a `set_type` on this version would swap (`_Carried.date_order`)."""
    swapped = {name: f"{order}_first" for name, order in _Carried.of(parsed).date_order.items()}
    return {name: value for name, value in day_month(parsed).items() if value is not None} == swapped


def column(parsed: ParsedDataset, name: str) -> ColumnProfile:
    return next(item for item in parsed.profile.columns if item.name == name)


class TestThePaste:
    def test_the_eval_table_reads_day_first(self) -> None:
        pasted = parse_dataset(EVAL_TABLE)

        assert day_month(pasted) == {"date": "day_first", "visits": None}
        assert agrees(pasted)

    @pytest.mark.parametrize(
        "cells",
        [
            ["13/04/2024", "05/06/2024"],  # a day over 12 settles the order
            ["2024-03-04", "2024-05-06"],  # ISO
            ["01/01/2024", "02/02/2024"],  # each date the same both ways
            ["03.04.2024", "05.06.2024"],  # a dot date is day first
            ["4 Mar 2024", "6 May 2024"],  # a month name
        ],
    )
    def test_a_settled_order_has_no_field(self, cells: list[str]) -> None:
        pasted = parse_dataset("date,visits\n" + "".join(f"{cell},{index}\n" for index, cell in enumerate(cells)))

        assert pasted.column_dtypes["date"] == "datetime"
        assert day_month(pasted)["date"] is None
        assert agrees(pasted)


class TestPrepareData:
    def test_month_first_flips_the_field_and_unrelated_steps_keep_it(self) -> None:
        month_first = step(parse_dataset(EVAL_TABLE), MONTH_FIRST)

        assert day_month(month_first) == {"date": "month_first", "visits": None}
        assert column(month_first, "date").min == "2024-03-04"
        renamed = step(month_first, {"op": "rename", "column": "visits", "name": "hits"})
        assert day_month(renamed) == {"date": "month_first", "hits": None}
        ordered = step(renamed, {"op": "sort", "column": "hits", "descending": True})
        assert day_month(ordered) == {"date": "month_first", "hits": None}
        assert agrees(month_first) and agrees(renamed) and agrees(ordered)

    def test_a_second_month_first_changes_nothing(self) -> None:
        month_first = step(parse_dataset(EVAL_TABLE), MONTH_FIRST)
        prepared = apply_operations(month_first, OPERATIONS.validate_python([MONTH_FIRST]))

        assert prepared.changes == ["date: already dates, nothing changed"]
        assert day_month(step(month_first, MONTH_FIRST))["date"] == "month_first"

    def test_day_first_flips_it_back(self) -> None:
        back = step(step(parse_dataset(EVAL_TABLE), MONTH_FIRST), DAY_FIRST)

        assert day_month(back)["date"] == "day_first"
        assert column(back, "date").min == "2024-04-03"
        assert agrees(back)

    def test_a_rename_of_the_date_column_carries_it(self) -> None:
        renamed = step(parse_dataset(EVAL_TABLE), MONTH_FIRST, {"op": "rename", "column": "date", "name": "day"})

        assert day_month(renamed) == {"day": "month_first", "visits": None}
        assert agrees(renamed)

    @pytest.mark.parametrize(
        "operation", [{"op": "set_type", "column": "date", "type": "text"}, {"op": "drop_columns", "columns": ["date"]}]
    )
    def test_a_column_no_longer_of_dates_has_none(self, operation: dict[str, Any]) -> None:
        after = step(parse_dataset(EVAL_TABLE), operation)

        assert all(value is None for value in day_month(after).values())
        assert agrees(after)

    # A column the paste left text (one stray cell), every day at most 12.
    TEXT_DATES = (
        "d,v\n05/03/2024,1\n06/04/2024,2\nunknown,3\n07/02/2024,4\n08/01/2024,5\n09/02/2024,6\n10/03/2024,7\n"
        "11/04/2024,8\n12/05/2024,9\n01/06/2024,10\n02/07/2024,11\n"
    )

    @pytest.mark.parametrize(
        ("operation", "expected"),
        [
            # Without a format the paste's own reader guesses, day first.
            ({"op": "set_type", "column": "d", "type": "datetime"}, {"d": "day_first", "v": None}),
            # A format reads in its order, which stays open while every day is at most 12.
            (
                {"op": "set_type", "column": "d", "type": "datetime", "date_format": "MM/DD/YYYY"},
                {"d": "month_first", "v": None},
            ),
            # Into a new column: the new one carries the order, the text column beside it has none.
            (
                {"op": "set_type", "column": "d", "type": "datetime", "date_format": "MM/DD/YYYY", "name": "when"},
                {"d": None, "v": None, "when": "month_first"},
            ),
        ],
    )
    def test_a_set_type_on_text_cells_opens_the_order(
        self, operation: dict[str, Any], expected: dict[str, str | None]
    ) -> None:
        pasted = parse_dataset(self.TEXT_DATES)
        assert pasted.column_dtypes["d"] == "text"

        read = step(pasted, operation)

        assert day_month(read) == expected
        assert agrees(read)

    def test_an_iso_column_stays_without_it_through_a_set_type(self) -> None:
        after = step(parse_dataset("date,v\n2024-01-05,1\n2024-02-06,2\n"), MONTH_FIRST)

        assert day_month(after) == {"date": None, "v": None}


class TestTheWarningCap:
    """The field is read from the profile's own warnings, so a cut that drops the order note drops the field too."""

    # Real warning sentences, each with its telemetry code (the data tests' conftest checks every warning has one).
    FILLER = tuple(
        f"column 'c{index}': invisible formatting characters (zero-width or bidi) removed"
        for index in range(MAX_WARNINGS)
    )

    def test_a_warning_put_first_that_pushes_the_note_out(self) -> None:
        pasted = parse_dataset(EVAL_TABLE)
        crowded = [*self.FILLER[1:], *pasted.warnings]
        assert len(crowded) == MAX_WARNINGS
        full = replace(
            pasted, warnings=crowded, profile=with_day_month(pasted.profile.model_copy(update={"warnings": crowded}))
        )
        assert day_month(full)["date"] == "day_first"

        cut = with_warning(full, self.FILLER[0])

        assert day_month(cut)["date"] is None
        assert agrees(cut)

    def test_a_date_note_past_the_cap_of_the_next_version(self) -> None:
        prepared = apply_operations(parse_dataset(EVAL_TABLE), OPERATIONS.validate_python([MONTH_FIRST]))
        again = parse_dataset(
            prepared.csv,
            text_columns=prepared.text_columns,
            find_table=False,
            max_bytes=MAX_COMPUTED_BYTES,
            canonical=True,
        )
        full = list(self.FILLER)
        crowded = replace(again, warnings=full, profile=again.profile.model_copy(update={"warnings": full}))

        stored = with_date_notes(crowded, prepared)

        assert day_month(stored)["date"] is None
        assert agrees(stored)


class TestWhatTheRootReads:
    def test_the_profile_json_names_it_on_the_date_column_alone(self) -> None:
        text = profile_json(parse_dataset(EVAL_TABLE).profile)

        assert text.count('"day_month"') == 1
        assert '"day_month":"day_first"' in text

    def test_every_trimmed_version_keeps_it(self) -> None:
        versions = [text for text, _ in trimmed_profiles(step(parse_dataset(EVAL_TABLE), MONTH_FIRST).profile)]

        assert all('"day_month":"month_first"' in text for text in versions)

    def test_the_tools_result_and_the_session_block_carry_it(self) -> None:
        view = SimpleNamespace(bindings=[], snapshot=snapshot_from_repo("scatter-basic", "matplotlib"), language="en")
        stored = SimpleNamespace(profile=parse_dataset(EVAL_TABLE).profile)

        result = profile_result(cast(Any, view), cast(Any, stored))

        assert '"day_month":"day_first"' in result["profile"]
        assert '"day_month":"day_first"' in profile_block(result)

    def test_telemetry_reads_no_more_of_the_profile(self) -> None:
        profile = parse_dataset(EVAL_TABLE).profile
        without = profile.model_copy(
            update={"columns": [item.model_copy(update={"day_month": None}) for item in profile.columns]}
        )

        assert profile_fields(profile) == profile_fields(without)


class TestStoredProfiles:
    def test_a_profile_from_before_the_field_still_validates(self) -> None:
        profile = parse_dataset(EVAL_TABLE).profile
        older = profile.model_dump_json(exclude={"columns": {"__all__": {"day_month"}}})
        assert "day_month" not in older

        loaded = DatasetProfile.model_validate_json(older)

        assert [item.day_month for item in loaded.columns] == [None, None]

    def test_the_route_payload_round_trips(self) -> None:
        profile = parse_dataset(EVAL_TABLE).profile
        payload = profile.model_dump(mode="json")

        assert payload["columns"][0]["day_month"] == "day_first"
        assert DatasetProfile.model_validate(payload) == profile

    def test_another_value_is_refused(self) -> None:
        with pytest.raises(ValidationError):
            ColumnProfile.model_validate(
                {"name": "d", "dtype": "datetime", "missing": 0, "unique": 2, "day_month": "year_first"}
            )
