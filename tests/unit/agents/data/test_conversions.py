"""Tests for agents/anyplot/data/conversions.py: the conversions that would fill a required role left open."""

import json

import pytest
from pydantic import TypeAdapter

from agents.anyplot.data.bindings import carry_bindings, check_bindings, default_bindings
from agents.anyplot.data.conversions import (
    MAX_CANDIDATES,
    Candidate,
    DateNumbers,
    RangeSplit,
    RowNumbers,
    candidates,
    new_name,
    range_names,
)
from agents.anyplot.data.parse import DATE_FORMS, ParsedDataset, parse_dataset
from agents.anyplot.data.prepare import (
    SLASH_ORDER,
    DryRun,
    Operation,
    RangeRun,
    UnreadDates,
    apply_operations,
    range_run,
    read_frame,
)
from agents.anyplot.schemas import MAX_COLUMN_NAME_CHARS, Binding
from core.spec_roles import DataRole, parse_roles


ROLLING = [
    "`date` (datetime) - Timestamp values representing points in time",
    "`value` (numeric) - Raw measurements or observations at each timestamp",
    "`rolling_avg` (numeric) - Computed rolling average (e.g., 7-day, 30-day window)",
]
"""The roles of `line-timeseries-rolling`, the spec of the live test of 2026-11-01."""
OPERATIONS = TypeAdapter(list[Operation])
PAIRS = '{"2026-11-26": 1, "2026-11-25": 2, "2026-11-24": 3}'
"""Days newest first as the keys of JSON pairs, which the parser keeps text: a dry run reads every cell, no guess."""
DAYS = "Datum;Preis\n" + "".join(f"2026-11-{day};{day}\n" for day in range(26, 16, -1)) + "offen;0\n"
"""Ten days newest first and one cell of no date: the paste keeps the column text, a dry run reads ten of eleven."""


def found(
    text: str, language: str = "en", roles: list[DataRole] | None = None, **kwargs: object
) -> list[Candidate | RangeSplit | RowNumbers | DateNumbers]:
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
        [candidate] = found(PAIRS, language="de")

        # No sort: the table keeps its rows as pasted, and a plot run draws the dates oldest first by itself.
        assert candidate.role == "date" and candidate.dry.certain
        assert candidate.operations() == [
            {"op": "set_type", "column": "category", "type": "datetime", "name": "category (Datum)"}
        ]
        assert candidate.line() == (
            "date: column 'category' (text): 3 of 3 cells would be read as dates (format inferred, year first); "
            'certain: every cell reads and nothing is guessed; operations: [{"op": "set_type", "column": "category", '
            '"type": "datetime", "name": "category (Datum)"}]'
        )
        assert "newest first" not in candidate.made()

    def test_its_operations_fill_the_role(self) -> None:
        """The operations the line gives make the column that the service binds (`carry_bindings`): the role is filled."""
        parsed = parse_dataset(PAIRS)
        roles = parse_roles(ROLLING)
        [candidate] = found(PAIRS)

        after = applied(parsed, candidate)

        column = next(column for column in after.profile.columns if column.name == "category (date)")
        assert column.dtype == "datetime" and column.order == "descending"  # the rows stay as pasted
        assert after.csv.splitlines()[1] == "2026-11-26,1,2026-11-26"
        assert check_bindings(default_bindings(roles, after.profile), roles, after.profile).complete

    def test_an_uncertain_conversion_says_why(self) -> None:
        """Slash dates whose order no cell settles: the paste reads them day first by guess, and so does a dry run."""
        [candidate] = found('{"01/11/2026": 1, "02/11/2026": 2}')

        assert not candidate.dry.certain
        assert "uncertain: the reading guesses the day and month order" in candidate.line()
        assert "newest first" not in candidate.line()

    def test_cells_that_would_be_missing_are_counted(self) -> None:
        [candidate] = found(DAYS)

        assert "10 of 11 cells would be read as dates" in candidate.line()
        assert "uncertain: 1 cell would not read and be missing" in candidate.line()

    def test_dates_outside_the_date_list_are_no_candidate(self) -> None:
        """`26 Nov 2026` is no form the chat reads: no dry run proposes what no conversion reads."""
        assert found("Datum;Preis\n26 Nov 2026;1\n25 Nov 2026;2\n24 Nov 2026;3\n") == []

    def test_a_number_role_takes_a_currency_column(self) -> None:
        [candidate] = found("when,price\n2024-01-01,$5\n2024-01-02,7\n2024-01-03,$12\n")

        assert (candidate.role, candidate.dry.type, candidate.name) == ("value", "number", "price (number)")
        assert candidate.dry.certain
        assert candidate.operations() == [
            {"op": "set_type", "column": "price", "type": "number", "name": "price (number)"}
        ]

    def test_a_column_of_dates_is_never_a_number_candidate(self) -> None:
        """`Nov 26, 2026` would be 26.2026 behind a unit `Nov`: a date column serves a date role or none. The paste
        types it as dates, so the open measure gets the offer of a free date column, never a number conversion."""
        roles = [*parse_roles(ROLLING)[:2]]
        text = "when;price;note\n2024-01-01;x;Nov 26, 2026\n2024-01-02;y;Nov 25, 2026\n"

        assert found(text, roles=roles) == [DateNumbers(role="value", column="note", dates=2)]

    @pytest.mark.parametrize(
        "text",
        [
            "Person,Preis\nMay,1\nJune,2\nApril,3\n",  # names that look like months
            "Monat,Preis\nNov 26,1\nOct 26,2\nSep 26,3\n",  # two-digit years: no date pandas may fill in
            "Monat,Preis\nQ1 2026,1\nQ2 2026,2\n",
            "Band;Preis\n10–20;1\n20–30;2\n30–40;3\n",  # a range
            "Band;Preis\n10-20;1\n20-30;2\n30-40;3\n",
        ],
    )
    def test_text_that_reads_as_no_date_is_no_candidate(self, text: str) -> None:
        assert found(text) == []

    def test_a_column_kept_text_on_request_is_no_candidate(self) -> None:
        assert found(DAYS) != []
        assert found(DAYS, keep_text=["Datum"]) == []

    def test_a_column_a_role_holds_is_no_candidate(self) -> None:
        """A conversion is a suggestion, like the defaults: it takes a free column only, although a column bound by
        hand may serve several roles (owner decision of 2026-11-04)."""
        parsed = parse_dataset(DAYS)
        label = DataRole(name="label", kinds=("text",), required=False, variadic=False, description="")
        roles = [*parse_roles(ROLLING)[:2], label]
        free = [Binding(role="value", column="Preis")]
        held = [*free, Binding(role="label", column="Datum")]

        assert [candidate.role for candidate in candidates(free, roles, parsed.profile, parsed)] == ["date"]
        assert candidates(held, roles, parsed.profile, parsed) == []

    def test_no_open_role_no_check(self) -> None:
        """The paste of the live test reads `Nov 2026` as dates now: every role is bound, nothing to convert."""
        text = "Month\tUsed\tΔ\nNov 2026\t$3000\t+75\nOct 2026\t$2925\t−100\n"

        assert found(text) == []

    def test_a_dry_run_is_made_once_per_version(self) -> None:
        cache: dict[tuple[str, str], DryRun | None] = {}
        text = "Datum;Preis;Notiz\n" + "".join(f"2026-11-{day};{day};a\n" for day in range(26, 16, -1)) + "offen;0;b\n"

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
        width = MAX_CANDIDATES + 2
        header = ";".join(f"c{index}" for index in range(width))
        days = "".join(";".join(f"2026-11-{day}" for _ in range(width)) + "\n" for day in range(10, 20))
        # One cell of no date in each column, each in a row of its own, keeps every column text at the paste.
        stray = "".join(
            ";".join("offen" if row == index else "2026-12-01" for index in range(width)) + "\n" for row in range(width)
        )

        assert len(found(f"{header}\n{days}{stray}", roles=roles)) == MAX_CANDIDATES

    def test_the_line_is_valid_json_after_operations(self) -> None:
        [candidate] = found(PAIRS)

        assert json.loads(candidate.line().split("; operations: ", 1)[1]) == candidate.operations()

    @pytest.mark.parametrize(
        "text",
        [
            DAYS.replace("Datum", "Order ID"),  # the name says an id, though ten of eleven cells read as dates
            DAYS.replace("Datum", "Code"),
            "Season,Preis\n2009-10,1\n2010-11,2\n2011-12,3\n",  # spans of years
            DAYS.replace("Datum", "Saison"),
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
            "Year,Month,Temp\n2020,1,1.5\n2020,2,1.4\n2021,1,1.6\n",  # every month on 1 January: `make_date` builds those
        ],
    )
    def test_whole_numbers_that_are_no_series_of_years(self, text: str) -> None:
        assert found(text) == []


LINE = ["`x` (numeric/datetime) - position", "`y` (numeric) - values"]
BAR = ["`category` (categorical) - bar labels", "`value` (numeric) - values"]


class TestRowNumbers:
    def test_a_list_of_values_gets_them_on_the_axis(self) -> None:
        [candidate] = found("value\n1\n3\n5\n4\n6\n2\n", roles=parse_roles(LINE))

        assert isinstance(candidate, RowNumbers) and candidate.role == "x" and candidate.certain
        assert candidate.operations() == [{"op": "row_number", "name": "index"}]
        assert candidate.line() == (
            "y: no column or conversion fills it; a new column 'index' with the row numbers 1 to 6 takes x, and y "
            "takes 'value', which x holds now; certain: a list of values is drawn by position, and this is wanted, "
            'never a mistake; operations: [{"op": "row_number", "name": "index"}]'
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
        [candidate] = found('{"2026-11-08": 1, "2026-11-09": 3, "2026-11-10": 2}', roles=parse_roles(LINE))

        assert isinstance(candidate, Candidate) and candidate.role == "x" and candidate.certain
        assert candidate.moved == Binding(role="y", column="value")
        assert "y then takes 'value', which x holds now" in candidate.line()

    def test_days_with_a_month_name_take_the_axis_without_a_conversion(self) -> None:
        """A day with a month name is a date at the paste: it takes x, the numbers take y, nothing is left open."""
        text = "Datum;Preis\n8 Nov 2026;1\n9 Nov 2026;3\n10 Nov 2026;2\n"
        parsed = parse_dataset(text)

        assert parsed.column_dtypes["Datum"] == "datetime"
        bindings = default_bindings(parse_roles(LINE), parsed.profile)
        assert {binding.role: binding.column for binding in bindings} == {"x": "Datum", "y": "Preis"}
        assert found(text, roles=parse_roles(LINE)) == []

    def test_a_taken_name_gets_a_number(self) -> None:
        [candidate] = found("index,value\na,1\nb,2\nc,3\n", roles=parse_roles(LINE))

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

        assert after.csv.splitlines()[:2] == ["index,value", "1,1"]
        carried = carry_bindings(default_bindings(roles, parsed.profile), roles, after.profile, None, None, ["index"])
        assert [(binding.role, binding.column) for binding in carried] == [("x", "index"), ("y", "value")]
        assert check_bindings(carried, roles, after.profile).complete


SCATTER = ["`x` (numeric) - horizontal values", "`y` (numeric) - vertical values"]
"""The roles of `scatter-basic`, the spec of the owner's live test of 2026-11-04."""


def day_column(cells: list[str], name: str = "day") -> str:
    """A pasted table of one text column `name` with `cells` beside a column of whole numbers."""
    return f"{name},orders\n" + "".join(f'"{cell}",{14 + index * 3}\n' for index, cell in enumerate(cells))


SLASHES = ["2026/03/01", "2026/03/02", "2026/03/03", "2026/03/04"]
NO_SUCH_DAY = "1 cell names a day that does not exist, such as 31 November"
UNREAD = {
    # The row numbers took the date axis unasked beside these: a form outside the date list, or dates the list
    # leaves unread for a reason of its own.
    "a slashes year first": (SLASHES, DATE_FORMS),
    "b ordinal day": (["1st March 2026", "2nd March 2026", "3rd March 2026", "4th March 2026"], DATE_FORMS),
    "c one 31.02. in four": (["28.02.2026", "31.02.2026", "01.03.2026", "02.03.2026"], NO_SUCH_DAY),
    "f slashes in both orders": (["15/03/2026", "03/15/2026", "04/05/2026", "06/07/2026"], SLASH_ORDER),
    "g a slash date beside ISO": (["2026-03-01", "03/04/2026", "2026-03-05", "2026-03-07"], SLASH_ORDER),
    "h UTC as a word": ([f"2026-03-0{day} 10:00:00 UTC" for day in range(1, 5)], DATE_FORMS),
    "i a space before the offset": ([f"2026-03-0{day} 10:00:00 +0100" for day in range(1, 5)], DATE_FORMS),
    "j AM and PM": ([f"3/{day}/2026 10:00:00 AM" for day in range(1, 5)], DATE_FORMS),
    "k a range of times after the date": ([f"2026-03-0{day} 08:00-16:30" for day in range(1, 5)], DATE_FORMS),
    "l two-digit year with dots": ([f"0{day}.03.26" for day in range(1, 5)], DATE_FORMS),
    "m two-digit year with slashes": ([f"3/{day}/26" for day in range(13, 17)], DATE_FORMS),
}
CERTAIN_ROW_NUMBERS = {
    # Never read, and no date look the rule takes either: these keep their row numbers unasked.
    "n quarters": (day_column(["2026 Q1", "2026 Q2", "2026 Q3", "2026 Q4"]), LINE, ()),
    "o ISO weeks": (day_column(["2026-W01", "2026-W02", "2026-W03", "2026-W04"]), LINE, ()),
    "p a day in Chinese": (day_column([f"2026年3月{day}日" for day in range(1, 5)]), LINE, ()),
    "q a list of values": ("value\n1\n3\n5\n4\n6\n2\n", LINE, ()),
    "r city names": (day_column(["Bern", "Basel", "Genf", "Chur"], "city"), LINE, ()),
    "s hour labels": (day_column(["T00", "T01", "T02", "T03"], "hour"), LINE, ()),
    "t weekdays": (day_column(["Mon", "Tue", "Wed", "Thu"], "weekday"), LINE, ()),
    "v ids": (day_column(["A-12", "A-13", "A-14", "A-15"], "id"), LINE, ()),
    "w month names without a year": (day_column(["Jan", "Feb", "Mar", "Apr"], "month"), LINE, ()),
    "x kept text on request": (day_column(SLASHES), LINE, ("day",)),
    "y an axis that takes numbers only": (day_column(SLASHES), SCATTER, ()),
    "z street addresses with a year": (
        day_column(["12 Main St 2026", "14 Main St 2026", "16 Main St 2026", "18 Main St 2026"], "address"),
        LINE,
        (),
    ),
    "a name that says ids": (day_column(SLASHES, "Order ID"), LINE, ()),
    "spans of years": (day_column(["2009-10", "2010-11", "2011-12", "2012-13"], "period"), LINE, ()),
    "times with and without an offset, every cell read": (
        day_column(["2026-03-01T10:00Z", "2026-03-02T10:00", "2026-03-03T10:00Z", "2026-03-04T10:00"]),
        LINE,
        (),
    ),
}


class TestRowNumbersBesideUnreadDates:
    """A text column that looks like dates the date list leaves unread: the row numbers wait for a yes on an axis
    that takes dates, since the user may mean those dates, and the line says why they would not read."""

    @pytest.mark.parametrize(("cells", "why"), list(UNREAD.values()), ids=list(UNREAD))
    def test_the_row_numbers_are_a_question(self, cells: list[str], why: str) -> None:
        [candidate] = found(day_column(cells), roles=parse_roles(LINE))

        assert isinstance(candidate, RowNumbers) and candidate.role == "x" and not candidate.certain
        assert candidate.unread == UnreadDates("day", why)
        assert f"; uncertain: x takes dates, and column 'day' looks like dates that would not read: {why};" in (
            candidate.line()
        )
        assert candidate.operations() == [{"op": "row_number", "name": "index"}]

    def test_the_line_keeps_its_parts_and_names_the_forms(self) -> None:
        [candidate] = found(day_column(SLASHES), roles=parse_roles(LINE))

        assert candidate.line() == (
            "y: no column or conversion fills it; a new column 'index' with the row numbers 1 to 4 takes x, and y "
            "takes 'orders', which x holds now; uncertain: x takes dates, and column 'day' looks like dates that "
            "would not read: the chat reads 2026-03-01, 01.03.2026, 03/15/2026, 8 Nov 2026, each also with a time, "
            'and months such as 2026-03 or Mar 2026; operations: [{"op": "row_number", "name": "index"}]'
        )

    @pytest.mark.parametrize(
        ("text", "line_roles", "keep_text"), list(CERTAIN_ROW_NUMBERS.values()), ids=list(CERTAIN_ROW_NUMBERS)
    )
    def test_other_text_keeps_them_certain(self, text: str, line_roles: list[str], keep_text: tuple[str, ...]) -> None:
        [candidate] = found(text, roles=parse_roles(line_roles), keep_text=keep_text)

        assert isinstance(candidate, RowNumbers) and candidate.certain and candidate.unread is None
        assert "; certain: a list of values is drawn by position" in candidate.line()

    @pytest.mark.parametrize(
        ("cells", "outcome"),
        [
            # One impossible day in twelve: the conversion reads the rest, as before.
            ([f"{day:02d}.02.2026" for day in range(1, 12)] + ["31.02.2026"], "date"),
            (["Week 1", "Week 2", "Week 3", "Week 4"], "number"),  # the week numbers, as before
        ],
    )
    def test_a_conversion_still_comes_first(self, cells: list[str], outcome: str) -> None:
        [candidate] = found(day_column(cells), roles=parse_roles(LINE))

        assert isinstance(candidate, Candidate) and candidate.outcome == outcome

    def test_slash_dates_the_paste_types_take_the_axis(self) -> None:
        """No cell settles the order: the paste reads them day first by guess, so nothing is left open."""
        text = day_column(["03/04/2026", "05/06/2026", "07/08/2026", "09/10/2026"])

        assert found(text, roles=parse_roles(LINE)) == []

    def test_the_first_free_column_that_looks_like_dates_is_named(self) -> None:
        cities = ["Bern", "Basel", "Genf", "Chur"]
        text = "city,day,orders\n" + "".join(f"{city},2026/03/0{day},{day}\n" for day, city in enumerate(cities, 1))

        [candidate] = found(text, roles=parse_roles(LINE))

        assert isinstance(candidate, RowNumbers) and candidate.unread == UnreadDates("day", DATE_FORMS)

    def test_the_verdict_is_made_once_per_version(self) -> None:
        cache: dict[tuple[str, str], DryRun | RangeRun | UnreadDates | None] = {}

        first = found(day_column(SLASHES), roles=parse_roles(LINE), cache=cache)
        cache[("day", "unread")] = None  # a stored verdict is taken as it is
        second = found(day_column(SLASHES), roles=parse_roles(LINE), cache=cache)

        assert not first[0].certain and second[0].certain


CUSTOMERS = (
    "Index,Customer Id,First Name,Subscription Date\n"
    "1,DD37Cf93aecA6Dc,Mara,2020-08-24\n"
    "2,1Ef7b82A4CAAD10,Tobin,2021-04-23\n"
    "3,6F94879bDAfE5a6,Ilse,\n"
    "4,5Cef8BFA16c5e3c,Ravi,2020-06-02\n"
)


class TestDateNumbers:
    def test_an_open_measure_beside_a_free_date_column_gets_an_offer(self) -> None:
        """The owner's case: `Index` on x, nothing for y but the subscription dates, whose unit is the user's choice."""
        [offer] = found(CUSTOMERS, roles=parse_roles(SCATTER))

        assert isinstance(offer, DateNumbers) and (offer.role, offer.column, offer.dates) == (
            "y",
            "Subscription Date",
            3,
        )
        assert not offer.certain and offer.outcome == "number"
        assert offer.operations() == [{"op": "date_number", "column": "Subscription Date", "unit": "days"}]
        assert offer.line() == (
            "y: column 'Subscription Date' (dates): date_number would turn its 3 dates into numbers in a new column; "
            "offer: the unit is the user's choice (the days since the earliest date, the year, the Unix time in seconds "
            "or a decimal year), so state it in one sentence, never as a question or a request to choose, and make it "
            'only when the user asks; operations with days: [{"op": "date_number", "column": "Subscription Date", '
            '"unit": "days"}]'
        )

    def test_its_operations_fill_the_role(self) -> None:
        parsed = parse_dataset(CUSTOMERS)
        roles = parse_roles(SCATTER)
        bindings = default_bindings(roles, parsed.profile)
        [offer] = found(CUSTOMERS, roles=roles)

        prepared = apply_operations(parsed, OPERATIONS.validate_python(offer.operations()))
        after = parse_dataset(prepared.csv, text_columns=prepared.text_columns, find_table=False, canonical=True)
        carried = carry_bindings(bindings, roles, after.profile, parsed.profile, prepared.converted)

        assert [(binding.role, binding.column) for binding in carried] == [
            ("x", "Index"),
            ("y", "Subscription Date (days)"),
        ]
        assert check_bindings(carried, roles, after.profile).complete

    def test_a_conversion_of_a_text_column_fills_the_role_first(self) -> None:
        text = "Index,price,Signup\n1,$5,2024-01-01\n2,7,2024-01-02\n3,$12,2024-01-03\n"

        [candidate] = found(text, roles=parse_roles(SCATTER))

        assert isinstance(candidate, Candidate) and (candidate.role, candidate.dry.column) == ("y", "price")

    def test_the_row_numbers_fill_the_axis_first(self) -> None:
        """A list of values with dates beside it on a scatter: the axis takes the row numbers, as before, no offer."""
        [candidate] = found("Signup,value\n2024-01-01,3\n2024-01-02,5\n2024-01-03,4\n", roles=parse_roles(SCATTER))

        assert isinstance(candidate, RowNumbers) and candidate.role == "x"
        assert candidate.slot.moved == Binding(role="y", column="value")

    def test_a_date_column_a_role_holds_is_no_offer(self) -> None:
        """The time series' date role holds the only date column: the open value gets no offer of it."""
        roles = parse_roles(ROLLING)
        parsed = parse_dataset("when,price\n2024-01-01,x\n2024-01-02,y\n")
        bindings = default_bindings(roles, parsed.profile)

        assert bindings == [Binding(role="date", column="when")]
        assert candidates(bindings, roles, parsed.profile, parsed) == []

    def test_a_role_that_takes_dates_is_no_offer(self) -> None:
        """A free date column binds to such a role as it is; the user unbound it on purpose, so nothing is offered."""
        roles = parse_roles(LINE)
        parsed = parse_dataset("Signup,value\n2024-01-01,3\n2024-01-02,5\n")

        offers = candidates([Binding(role="y", column="value")], roles, parsed.profile, parsed)

        assert not any(isinstance(offer, DateNumbers) for offer in offers)

    def test_a_date_column_without_a_date_is_no_offer(self) -> None:
        """A column that is all missing would make an empty column: nothing to offer. The parser drops such a column
        at the paste, so the profile here is the guard's own case."""
        parsed = parse_dataset(CUSTOMERS)
        roles = parse_roles(SCATTER)
        profile = parsed.profile.model_copy(
            update={
                "columns": [
                    column.model_copy(update={"missing": parsed.profile.rows})
                    if column.name == "Subscription Date"
                    else column
                    for column in parsed.profile.columns
                ]
            }
        )

        offers = candidates(default_bindings(roles, profile), roles, profile, parsed)

        assert found(CUSTOMERS, roles=roles) != []  # with its dates the column is offered
        assert not any(isinstance(offer, DateNumbers) for offer in offers)


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


RANGE = [
    "`category` (categorical) - Labels for each range group",
    "`min_value` (numeric) - Lower bound of the range/interval",
    "`max_value` (numeric) - Upper bound of the range/interval",
]
"""The roles of `range-interval`, the spec of the agent case triage."""
# Invented, the shape of the case: the defaults would put the count and the average on the range's ends.
RANGES = "team;games;mean;min–max\nalpha;140;61.5;48–80\nbeta;146;67.2;52–77\ngamma;143;64.0;45–79\n"


def ranges(text: str, language: str = "en", **kwargs: object) -> list[Candidate | RangeSplit | RowNumbers]:
    return found(text, language, roles=parse_roles(RANGE), **kwargs)


class TestRanges:
    def test_the_open_pair_takes_a_certain_split(self) -> None:
        [candidate] = ranges(RANGES)

        assert isinstance(candidate, RangeSplit) and candidate.certain and candidate.outcome == "number"
        assert candidate.operations() == [
            {"op": "split", "column": "min–max", "separator": "–", "names": ["min–max (min)", "min–max (max)"]}
        ]
        assert candidate.line() == (
            "min_value and max_value: column 'min–max' (text): 3 of 3 cells would split at '–' into two numbers, "
            "the first never above the second, and be read as numbers, as the new columns 'min–max (min)' "
            "(min_value) and 'min–max (max)' (max_value); certain: every cell reads and nothing is guessed; "
            'operations: [{"op": "split", "column": "min–max", "separator": "–", "names": ["min–max (min)", '
            '"min–max (max)"]}]'
        )

    def test_its_operation_fills_both_roles(self) -> None:
        """The case end to end: the pair the defaults left open is bound to the two parts, nothing guessed."""
        parsed = parse_dataset(RANGES)
        roles = parse_roles(RANGE)
        before = default_bindings(roles, parsed.profile)
        [candidate] = ranges(RANGES, language="de")
        prepared = apply_operations(parsed, OPERATIONS.validate_python(candidate.operations()))
        after = parse_dataset(prepared.csv, text_columns=prepared.text_columns, find_table=False, canonical=True)

        carried = carry_bindings(
            before, roles, after.profile, parsed.profile, prepared.converted, splits=prepared.splits
        )

        assert [(binding.role, binding.column) for binding in carried] == [
            ("category", "team"),
            ("min_value", "min–max (Min)"),
            ("max_value", "min–max (Max)"),
        ]
        check = check_bindings(carried, roles, after.profile)
        assert check.complete and check.warnings == []
        assert candidates(carried, roles, after.profile, after) == []  # nothing left to convert

    @pytest.mark.parametrize(
        ("text", "reading"),
        [
            ("k;r\na;-5–10\nb;-3–4\n", "read as numbers"),  # a negative lower end
            ("k;r\na;-10--5\nb;-8--1\n", "read as numbers"),  # a hyphen between two negative numbers
            ("k;r\na;10 - 20\nb;30 - 40\n", "read as numbers"),
            ("k;r\na;1,5–2,5\nb;0,5–1\n", "read as numbers (decimal comma)"),
        ],
    )
    def test_ranges_of_one_shape(self, text: str, reading: str) -> None:
        [candidate] = ranges(text)

        assert isinstance(candidate, RangeSplit) and reading in candidate.line()

    def test_thousands_that_read_both_ways_split_only_on_request(self) -> None:
        """`1.200` is 1.2 with a decimal point: no automatic split, as for any number reading that guesses its mark.

        Asked for, the split reads the file's own way: 1200 in a file with decimal commas.
        """
        text = "Ort;Wert;Spanne\nA;3,5;1.200–2.500\nB;4,0;900–1.100\n"
        parsed = parse_dataset(text)
        operation = {"op": "split", "column": "Spanne", "separator": "–", "names": ["lo", "hi"]}

        assert parsed.profile.decimal == "," and range_run(read_frame(parsed), "Spanne", ",") is None
        prepared = apply_operations(parsed, OPERATIONS.validate_python([operation]))
        assert prepared.csv.splitlines()[1:] == ["A,3.5,1.200–2.500,1200,2500", "B,4,900–1.100,900,1100"]

    @pytest.mark.parametrize(
        ("text", "dtype"),
        [
            ("k;v\na;2024-11-03\nb;2024-12-01\n", "datetime"),  # ISO dates stay dates
            ("k;v\na;-5\nb;-7\n", "integer"),  # negative numbers stay numbers
            ("k;v;w\na;1,5;2\nb;2,5;3\n", "number"),  # a decimal comma keeps its reading
            ("k;v;w\na;1.200;2,5\nb;3.400;3,5\n", "integer"),  # and so do thousands dots in such a file
        ],
    )
    def test_a_column_the_parser_types_is_never_a_range(self, text: str, dtype: str) -> None:
        parsed = parse_dataset(text)

        assert parsed.column_dtypes["v"] == dtype
        assert range_run(read_frame(parsed), "v", parsed.profile.decimal) is None

    @pytest.mark.parametrize(
        "text",
        [
            "k;r\na;A-12\nb;B-7\n",  # an id or a code stays text
            "k;r\na;2019-20\nb;2020-21\n",  # a season: the second part is the smaller
            "k;r\na;75–30\nb;68–35\n",  # the first end above the second
            "k;r\na;30–75\nb;40\nc;35–68\n",  # one cell without the dash: only on request
            "k;r\na;30–75\nb;35–50–68\n",  # one cell with two
            "k;r\na;30 %–75 %\nb;35 %–68 %\n",  # a unit: only on request
            "k;r\na;007–012\nb;003–009\n",  # leading zeros: codes
            "k;r\na;2024–11–03\nb;2024–12–01\n",  # a date with en dashes
        ],
    )
    def test_text_of_another_shape_is_no_range(self, text: str) -> None:
        parsed = parse_dataset(text)

        assert parsed.column_dtypes["r"] == "text"
        assert range_run(read_frame(parsed), "r") is None
        assert not any(isinstance(candidate, RangeSplit) for candidate in ranges(text))

    @pytest.mark.parametrize(
        "text",
        [
            "k;id\na;1-2\nb;3-4\n",  # a column named as ids, whatever its cells
            "k;Saison\na;2019-2020\nb;2020-2021\n",  # a span of years, by its name
        ],
    )
    def test_ids_and_spans_stay_text_by_their_name(self, text: str) -> None:
        parsed = parse_dataset(text)
        column = parsed.profile.columns[1].name

        assert range_run(read_frame(parsed), column) is not None  # the shape alone would do
        assert ranges(text) == []

    def test_an_iso_date_column_kept_text_is_no_range(self) -> None:
        text = "k;d\na;2024-11-03\nb;2024-12-01\n"
        parsed = parse_dataset(text, text_columns=["d"])
        roles = parse_roles(RANGE)

        assert candidates(default_bindings(roles, parsed.profile), roles, parsed.profile, parsed) == []

    def test_a_pair_with_one_role_bound_takes_no_split(self) -> None:
        parsed = parse_dataset(RANGES)
        roles = parse_roles(RANGE)
        bindings = [Binding(role="category", column="team"), Binding(role="min_value", column="mean")]

        assert not any(
            isinstance(candidate, RangeSplit) for candidate in candidates(bindings, roles, parsed.profile, parsed)
        )

    def test_a_spec_without_a_pair_takes_none(self) -> None:
        assert not any(isinstance(candidate, RangeSplit) for candidate in found("Band;Preis\n10–20;1\n20–30;2\n"))

    def test_the_names_are_in_the_session_language_and_never_taken(self) -> None:
        assert range_names("Spanne", "de", ()) == ("Spanne (Min)", "Spanne (Max)")
        assert range_names("r", "es", ()) == ("r (mín)", "r (máx)")
        assert range_names("r", "en", ["r (min)"]) == ("r_2 (min)", "r (max)")

    def test_the_range_run_is_made_once_per_version(self) -> None:
        cache: dict[tuple[str, str], DryRun | RangeRun | None] = {}
        parsed = parse_dataset(RANGES)
        roles = parse_roles(RANGE)
        bindings = default_bindings(roles, parsed.profile)

        candidates(bindings, roles, parsed.profile, parsed, cache=cache)
        cache[("min–max", "range")] = None  # a stored answer is used as it is: no second run

        assert candidates(bindings, roles, parsed.profile, parsed, cache=cache) == []


def test_bindings_are_untouched() -> None:
    """The check reads the bindings; it never changes them."""
    bindings = [Binding(role="value", column="Preis")]
    parsed = parse_dataset(DAYS)

    assert candidates(bindings, parse_roles(ROLLING), parsed.profile, parsed) != []
    assert bindings == [Binding(role="value", column="Preis")]
