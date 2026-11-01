"""Tests for agents/anyplot/data/conversions.py: the conversions that would fill a required role left open."""

import json

import pytest
from pydantic import TypeAdapter

from agents.anyplot.data.bindings import check_bindings, default_bindings
from agents.anyplot.data.conversions import MAX_CANDIDATES, Candidate, candidates, new_name
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


def found(text: str, language: str = "en", roles: list[DataRole] | None = None, **kwargs: object) -> list[Candidate]:
    parsed = parse_dataset(text)
    spec_roles = roles or parse_roles(ROLLING)
    bindings = default_bindings(spec_roles, parsed.profile)
    return candidates(bindings, spec_roles, parsed.profile, parsed, language=language, **kwargs)  # type: ignore[arg-type]


def applied(parsed: ParsedDataset, candidate: Candidate) -> ParsedDataset:
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
        assert candidate.operations() == [{"op": "set_type", "column": "price", "type": "number", "name": "price (number)"}]

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
        [candidate] = found('Datum;Preis\n26 Nov 2026;1\n25 Nov 2026;2\n')

        assert json.loads(candidate.line().split("; operations: ", 1)[1]) == candidate.operations()


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
