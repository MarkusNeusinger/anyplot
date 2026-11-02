"""Tests for agents/anyplot/data/conversions.py: the conversions that would fill a required role left open."""

import json

import pytest
from pydantic import TypeAdapter

from agents.anyplot.data.bindings import carry_bindings, check_bindings, default_bindings
from agents.anyplot.data.conversions import MAX_CANDIDATES, Candidate, RowNumbers, candidates, new_name
from agents.anyplot.data.parse import ParsedDataset, parse_dataset
from agents.anyplot.data.prepare import DryRun, Operation, apply_operations
from agents.anyplot.schemas import MAX_COLUMN_NAME_CHARS, Binding
from core.spec_roles import DataRole, parse_roles


ROLLING = [
    "`date` (datetime) - Timestamp values representing points in time",
    "`value` (numeric) - Raw measurements or observations at each timestamp",
    "`rolling_avg` (numeric) - Computed rolling average (e.g., 7-day, 30-day window)",
]
"""The roles of `line-timeseries-rolling`, the spec of the live test of 2026-11-01."""
OPERATIONS = TypeAdapter(list[Operation])


def found(
    text: str, language: str = "en", roles: list[DataRole] | None = None, **kwargs: object
) -> list[Candidate | RowNumbers]:
    parsed = parse_dataset(text)
    spec_roles = roles or parse_roles(ROLLING)
    bindings = default_bindings(spec_roles, parsed.profile)
    return candidates(bindings, spec_roles, parsed.profile, parsed, language=language, **kwargs)  # type: ignore[arg-type]


def applied(parsed: ParsedDataset, candidate: Candidate | RowNumbers) -> ParsedDataset:
    """The version the candidate's operations make, as `prepare_data` stores it."""
    prepared = apply_operations(parsed, OPERATIONS.validate_python(candidate.operations()))
    return parse_dataset(prepared.csv, text_columns=prepared.text_columns, find_table=False, canonical=True)


class TestCandidates:
    def test_a_certain_date_conversion_of_a_newest_first_column(self) -> None:
        text = "Datum;Preis\n26 Nov 2026;1\n25 Nov 2026;2\n24 Nov 2026;3\n"

        [candidate] = found(text, language="de")

        assert candidate.role == "date" and candidate.dry.certain
        assert candidate.operations() == [
            {"op": "set_type", "column": "Datum", "type": "datetime", "name": "Datum (Datum)"},
            {"op": "sort", "column": "Datum (Datum)"},
        ]
        assert candidate.line() == (
            "date: column 'Datum' (text): 3 of 3 cells would be read as dates (format inferred, day before month); "
            "certain: every cell reads and nothing is guessed; the dates run newest first, so the sort puts them "
            'oldest first; operations: [{"op": "set_type", "column": "Datum", "type": "datetime", "name": '
            '"Datum (Datum)"}, {"op": "sort", "column": "Datum (Datum)"}]'
        )

    def test_its_operations_fill_the_role(self) -> None:
        """The operations the line gives make the column that the service binds (`carry_bindings`): the role is filled."""
        text = "Datum;Preis\n26 Nov 2026;1\n25 Nov 2026;2\n24 Nov 2026;3\n"
        parsed = parse_dataset(text)
        roles = parse_roles(ROLLING)
        [candidate] = found(text)

        after = applied(parsed, candidate)

        column = next(column for column in after.profile.columns if column.name == "Datum (date)")
        assert column.dtype == "datetime" and column.order == "ascending"
        assert after.csv.splitlines()[1] == "24 Nov 2026,3,2026-11-24"
        assert check_bindings(default_bindings(roles, after.profile), roles, after.profile).complete

    def test_an_uncertain_conversion_says_why(self) -> None:
        [candidate] = found("Datum,Preis\n26.11.26,1\n27.11.26,2\n")

        assert not candidate.dry.certain
        assert "uncertain: the reading guesses the century of two-digit years" in candidate.line()
        assert "newest first" not in candidate.line()

    def test_cells_that_would_be_missing_are_counted(self) -> None:
        rows = "".join(f"{day} Nov 2026;{day}\n" for day in range(1, 11)) + "offen;11\n"

        [candidate] = found("Datum;Preis\n" + rows)

        assert "10 of 11 cells would be read as dates" in candidate.line()
        assert "uncertain: 1 cell would not read and be missing" in candidate.line()

    def test_a_number_role_takes_a_currency_column(self) -> None:
        [candidate] = found("when,price\n2024-01-01,$5\n2024-01-02,7\n2024-01-03,$12\n")

        assert (candidate.role, candidate.dry.type, candidate.name) == ("value", "number", "price (number)")
        assert candidate.dry.certain
        assert candidate.operations() == [
            {"op": "set_type", "column": "price", "type": "number", "name": "price (number)"}
        ]

    def test_a_column_of_dates_is_never_a_number_candidate(self) -> None:
        """`Nov 26, 2026` would be 26.2026 behind a unit `Nov`: a date column serves a date role or none."""
        roles = [*parse_roles(ROLLING)[:2]]
        text = "when;price;note\n2024-01-01;x;Nov 26, 2026\n2024-01-02;y;Nov 25, 2026\n"

        assert found(text, roles=roles) == []

    @pytest.mark.parametrize(
        "text",
        [
            "Person,Preis\nMay,1\nJune,2\nApril,3\n",  # names that look like months
            "Monat,Preis\nNov 26,1\nOct 26,2\nSep 26,3\n",  # two-digit years: no date pandas may fill in
            "Monat,Preis\nQ1 2026,1\nQ2 2026,2\n",
        ],
    )
    def test_text_that_reads_as_no_date_is_no_candidate(self, text: str) -> None:
        assert found(text) == []

    def test_a_column_kept_text_on_request_is_no_candidate(self) -> None:
        assert found("Datum,Preis\n26 Nov 2026,1\n25 Nov 2026,2\n", keep_text=["Datum"]) == []

    def test_no_open_role_no_check(self) -> None:
        """The paste of the live test reads `Nov 2026` as dates now: every role is bound, nothing to convert."""
        text = "Month\tUsed\tΔ\nNov 2026\t$3000\t+75\nOct 2026\t$2925\t−100\n"

        assert found(text) == []

    def test_a_dry_run_is_made_once_per_version(self) -> None:
        cache: dict[tuple[str, str], DryRun | None] = {}
        text = "Datum;Preis;Notiz\n26 Nov 2026;1;a\n25 Nov 2026;2;b\n"

        first = found(text, cache=cache)
        cache[("Datum", "datetime")] = None  # a stored verdict is taken as it is
        second = found(text, cache=cache)

        assert len(first) == 1 and second == []
        assert ("Datum", "number") not in cache  # a date column is never tried as numbers

    def test_at_most_max_candidates(self) -> None:
        roles = [
            DataRole(name=f"t{index}", kinds=("datetime",), required=True, variadic=False, description="a date")
            for index in range(MAX_CANDIDATES + 2)
        ]
        header = ";".join(f"c{index}" for index in range(MAX_CANDIDATES + 2))
        rows = ";".join("26 Nov 2026" for _ in range(MAX_CANDIDATES + 2))

        assert len(found(f"{header}\n{rows}\n{rows}\n", roles=roles)) == MAX_CANDIDATES

    def test_the_line_is_valid_json_after_operations(self) -> None:
        [candidate] = found("Datum;Preis\n26 Nov 2026;1\n25 Nov 2026;2\n")

        assert json.loads(candidate.line().split("; operations: ", 1)[1]) == candidate.operations()

    @pytest.mark.parametrize(
        "text",
        [
            "Order ID,Preis\n26 Nov 2026,1\n25 Nov 2026,2\n",  # the name says an id
            "Code,Preis\n26 Nov 2026,1\n25 Nov 2026,2\n",
            "Season,Preis\n2009-10,1\n2010-11,2\n2011-12,3\n",  # spans of years
            "Saison,Preis\n26 Nov 2026,1\n25 Nov 2026,2\n",
            "Land,Preis\nAT,1\nCH,2\nDE,3\n",  # short capitals
        ],
    )
    def test_ids_codes_and_spans_are_no_candidates(self, text: str) -> None:
        assert found(text) == []

    def test_a_range_is_no_number_candidate(self) -> None:
        roles = parse_roles(["`y` (numeric) - values", "`z` (text) - labels"])

        assert found("Band;Name\n10–20;a\n20–30;b\n30–40;c\n", roles=roles) == []

    def test_an_en_dash_is_no_minus_for_a_candidate(self) -> None:
        roles = parse_roles(["`y` (numeric) - values"])

        assert found("d;v\na;–5\nb;–7\nc;–9\n", roles=roles) == []

    def test_leading_zeros_never_convert_automatically(self) -> None:
        roles = parse_roles(["`y` (numeric) - values"])

        [candidate] = found("Kennung;v\n007;a\n012;b\n105;c\n", roles=roles)

        assert isinstance(candidate, Candidate) and not candidate.certain


class TestYears:
    def test_a_column_named_year_converts_for_a_date_role(self) -> None:
        [candidate] = found("Jahr,CO2\n2019,1.5\n2020,1.4\n2021,1.6\n", language="de")

        assert isinstance(candidate, Candidate) and candidate.role == "date" and candidate.certain
        assert candidate.operations() == [
            {"op": "set_type", "column": "Jahr", "type": "datetime", "date_format": "YYYY", "name": "Jahr (Datum)"}
        ]
        assert "column 'Jahr' (whole numbers): 3 of 3 cells would be read as years" in candidate.line()

    def test_its_operations_fill_the_role(self) -> None:
        text = "Jahr,CO2\n2019,1.5\n2020,1.4\n2021,1.6\n"
        parsed = parse_dataset(text)
        roles = parse_roles(ROLLING)
        [candidate] = found(text)

        after = applied(parsed, candidate)

        assert check_bindings(default_bindings(roles, after.profile), roles, after.profile).complete

    @pytest.mark.parametrize(
        "text",
        [
            "Price,Stock\n1149,1.5\n1450,1.4\n3000,1.6\n",  # no year header: prices of 1149 to 3000 look like years
            "Id,Stock\n2019,1.5\n2020,1.4\n2021,1.6\n",  # a run of years without a year header
        ],
    )
    def test_whole_numbers_without_a_year_header_are_no_years(self, text: str) -> None:
        assert found(text) == []


LINE = ["`x` (numeric/datetime) - position", "`y` (numeric) - values"]
BAR = ["`category` (categorical) - bar labels", "`value` (numeric) - values"]


class TestRowNumbers:
    def test_a_list_of_values_gets_them_on_the_axis(self) -> None:
        [candidate] = found("value\n1\n3\n5\n4\n6\n2\n", roles=parse_roles(LINE))

        assert isinstance(candidate, RowNumbers) and candidate.role == "x" and candidate.certain
        assert candidate.operations() == [{"op": "row_number", "name": "index"}]
        assert candidate.line() == (
            "x: no column or conversion fills it; column 'index' holds the row numbers 1 to 6; certain: a list of "
            "values is drawn by position; y then takes 'value', which x holds now; operations: "
            '[{"op": "row_number", "name": "index"}]'
        )

    def test_a_table_with_labels_only_besides_gets_them_too(self) -> None:
        [candidate] = found("Name,Wert\na,1\nb,2\nc,3\n", roles=parse_roles(LINE))

        assert isinstance(candidate, RowNumbers) and candidate.certain

    def test_a_bar_chart_without_labels_gets_them_as_a_question(self) -> None:
        [candidate] = found("value\n1\n3\n5\n", roles=parse_roles(BAR))

        assert isinstance(candidate, RowNumbers) and candidate.role == "category" and not candidate.certain
        assert "uncertain: the table has no labels for category" in candidate.line()

    def test_a_conversion_comes_first(self) -> None:
        """Real dates take the axis: the row numbers are the last fallback, never in place of the user's dates."""
        text = "Datum;Preis\n8 Nov 2026;1\n9 Nov 2026;3\n10 Nov 2026;2\n"

        [candidate] = found(text, roles=parse_roles(LINE))

        assert isinstance(candidate, Candidate) and candidate.role == "x" and candidate.certain
        assert candidate.moved == Binding(role="y", column="Preis")
        assert "y then takes 'Preis', which x holds now" in candidate.line()

    def test_a_taken_name_gets_a_number(self) -> None:
        parsed = parse_dataset("index,value\n5,1\n7,2\n9,3\n")
        bindings = [Binding(role="y", column="value")]

        [candidate] = candidates(bindings, parse_roles(LINE), parsed.profile, parsed)

        assert isinstance(candidate, RowNumbers) and candidate.name == "index_2"

    def test_a_pasted_row_number_is_reused(self) -> None:
        parsed = parse_dataset("value,index\n5,1\n7,2\n9,3\n")
        roles = parse_roles(LINE)
        bindings = [Binding(role="y", column="value")]

        [candidate] = candidates(bindings, roles, parsed.profile, parsed)

        assert isinstance(candidate, RowNumbers) and candidate.name == "index"

    def test_its_operations_fill_the_roles(self) -> None:
        text = "value\n1\n3\n5\n4\n6\n2\n"
        parsed = parse_dataset(text)
        roles = parse_roles(LINE)
        [candidate] = found(text, roles=roles)

        after = applied(parsed, candidate)

        assert after.csv.splitlines()[:2] == ["value,index", "1,1"]
        carried = carry_bindings(default_bindings(roles, parsed.profile), roles, after.profile, None, None, ["index"])
        assert [(binding.role, binding.column) for binding in carried] == [("x", "index"), ("y", "value")]
        assert check_bindings(carried, roles, after.profile).complete


class TestNewName:
    @pytest.mark.parametrize(
        ("language", "target", "name"),
        [
            ("en", "datetime", "Month (date)"),
            ("de", "datetime", "Month (Datum)"),
            ("Deutsch", "number", "Month (Zahl)"),
            ("fr", "datetime", "Month (date)"),
            ("sv", "datetime", "Month (date)"),  # outside the table: English
        ],
    )
    def test_the_type_in_the_session_language(self, language: str, target: str, name: str) -> None:
        assert new_name("Month", target, language, ()) == name  # type: ignore[arg-type]

    def test_a_taken_name_gets_a_number_and_a_long_one_is_cut(self) -> None:
        assert new_name("Month", "datetime", "en", ["Month (date)"]) == "Month_2 (date)"
        long = new_name("x" * 80, "datetime", "en", ())
        assert len(long) == MAX_COLUMN_NAME_CHARS and long.endswith(" (date)")


def test_bindings_are_untouched() -> None:
    """The check reads the bindings; it never changes them."""
    bindings = [Binding(role="value", column="Preis")]
    parsed = parse_dataset("Datum,Preis\n26 Nov 2026,1\n25 Nov 2026,2\n")

    candidates(bindings, parse_roles(ROLLING), parsed.profile, parsed)

    assert bindings == [Binding(role="value", column="Preis")]
