"""The canonical CSV as typed JSON for the JavaScript harness (`agents/anyplot/data/typed_json.py`)."""

import json

import pytest

from agents.anyplot.data.kinds import ColumnKinds, read_kinds
from agents.anyplot.data.parse import parse_dataset
from agents.anyplot.data.typed_json import typed_json
from agents.anyplot.schemas import MAX_COLUMNS, MAX_ROWS
from agents.renderer.wire import MAX_DATA_CSV_CHARS, MAX_DATA_JSON_CHARS


def _typed(csv_text: str, dtypes: dict, parse_dates: tuple[str, ...] = ()) -> dict:
    return json.loads(typed_json(csv_text, read_kinds(csv_text, dtypes, parse_dates)))


def test_a_parse_types_every_kind_and_keeps_text_verbatim() -> None:
    """One parse through the service's own parser: the JSON carries each kind as JavaScript reads it."""
    parsed = parse_dataset(
        "Month,Sales,Units,Open,Code,Country,Stamp\n"
        "2024-01-31,12.5,3,true,001,NA,2024-01-31T08:00:00+01:00\n"
        "2024-02-29,,4,false,002,DE,2024-02-01T09:30:00+01:00\n"
        "2024-03-31,7,5,true,003,FR,2024-03-01T10:00:00+01:00\n"
    )
    table = json.loads(typed_json(parsed.csv, read_kinds(parsed.csv, parsed.column_dtypes, parsed.parse_dates)))
    assert table["columns"] == ["Month", "Sales", "Units", "Open", "Code", "Country", "Stamp"]
    assert table["data"] == [
        ["2024-01-31", 12.5, 3, True, "001", "NA", "2024-01-31T07:00:00.000Z"],
        ["2024-02-29", None, 4, False, "002", "DE", "2024-02-01T08:30:00.000Z"],
        ["2024-03-31", 7.0, 5, True, "003", "FR", "2024-03-01T09:00:00.000Z"],
    ]


def test_a_missing_cell_is_null_in_every_kind() -> None:
    csv_text = "i,n,b,t,d,s\n,,,,,\n1,1.5,True,x,2024-01-31,2024-01-31T08:00:00\n"
    dtypes = {"i": "integer", "n": "number", "b": "boolean", "t": "text", "d": "datetime", "s": "datetime"}
    assert _typed(csv_text, dtypes)["data"][0] == [None] * 6


@pytest.mark.parametrize(
    ("cell", "utc"),
    [
        ("2024-01-31T08:00:00", "2024-01-31T08:00:00.000Z"),  # no offset: read as written, as UTC
        ("2024-01-31T08:00:00Z", "2024-01-31T08:00:00.000Z"),
        ("2024-01-31T08:00:00+01:00", "2024-01-31T07:00:00.000Z"),
        ("2024-01-31T08:00:00-05:30", "2024-01-31T13:30:00.000Z"),
        ("2024-01-31T08:00:00+0100", "2024-01-31T07:00:00.000Z"),
        ("2024-01-31T08:00:00+01", "2024-01-31T07:00:00.000Z"),
        ("2024-01-31 08:00", "2024-01-31T08:00:00.000Z"),
        ("2024-01-31T00:30:00+01:00", "2024-01-30T23:30:00.000Z"),  # the day moves with the offset
        ("2024-01-31T08:00:00.1", "2024-01-31T08:00:00.100Z"),
        ("2024-01-31T08:00:00.123456789", "2024-01-31T08:00:00.123Z"),  # truncated, never rounded
        ("2024-01-31T08:00:00.999999+01:00", "2024-01-31T07:00:00.999Z"),
        ("0001-01-01T00:00:00", "0001-01-01T00:00:00.000Z"),
    ],
)
def test_a_timestamp_becomes_utc_with_milliseconds(cell: str, utc: str) -> None:
    csv_text = f"s\n{cell}\n"
    assert _typed(csv_text, {"s": "datetime"})["data"] == [[utc]]


def test_a_plain_date_in_a_timestamp_column_is_its_midnight_and_a_date_column_stays_a_date() -> None:
    csv_text = "s,d\n2024-01-31,2024-01-31\n2024-02-01T08:00:00,2024-02-01\n"
    kinds = read_kinds(csv_text, {"s": "datetime", "d": "datetime"})
    assert kinds.kinds == {"s": "datetime", "d": "date"}
    assert json.loads(typed_json(csv_text, kinds))["data"] == [
        ["2024-01-31T00:00:00.000Z", "2024-01-31"],
        ["2024-02-01T08:00:00.000Z", "2024-02-01"],
    ]


def test_the_truncated_cells_are_the_ones_the_kinds_count() -> None:
    """`ColumnKinds.submillisecond` is what the runtime announces; the JSON changes exactly those cells."""
    cells = ["08:00:00.123456", "08:00:00.120000", "08:00:00.5", "08:00:00.000001", "08:00:00", "08:00:00.999000"]
    csv_text = "s\n" + "".join(f"2024-01-31T{cell}\n" for cell in cells)
    kinds = read_kinds(csv_text, {"s": "datetime"})
    data = json.loads(typed_json(csv_text, kinds))["data"]

    def nanoseconds(time: str) -> int:
        return int((time.partition(".")[2] + "0" * 9)[:9])

    changed = sum(
        1 for cell, (value,) in zip(cells, data, strict=True) if nanoseconds(cell) != nanoseconds(value[11:23])
    )
    assert changed == kinds.submillisecond["s"] == 2


def test_integers_keep_every_digit_in_the_json_and_the_kinds_count_the_inexact_ones() -> None:
    """The JSON literal is exact; JavaScript's JSON.parse reads it as a double, so the cells past 2^53 are what
    `ColumnKinds.inexact` counts for the runtime's note."""
    csv_text = "big\n9007199254740993\n-9223372036854775807\n42\n"
    kinds = read_kinds(csv_text, {"big": "integer"})
    text = typed_json(csv_text, kinds)
    assert "[9007199254740993],[-9223372036854775807],[42]" in text
    assert kinds.kinds["big"] == "big-integer" and kinds.inexact == {"big": 2}


def test_text_is_verbatim_including_what_would_close_a_script() -> None:
    """Escaping for HTML is the harness's (`render.mjs`, `readDataJson`): the JSON holds the cell as it is."""
    cell = 'a</script><script>alert(1)</script> \N{LINE SEPARATOR} \N{PARAGRAPH SEPARATOR} "q" \\ é'
    csv_text = 't\n"' + cell.replace('"', '""') + '"\n'
    text = typed_json(csv_text, read_kinds(csv_text, {"t": "text"}))
    assert json.loads(text)["data"] == [[cell]]
    assert "</script>" in text and "é" in text  # ensure_ascii off: the text keeps its characters


def test_numbers_and_booleans() -> None:
    csv_text = "n,b\n1e+20,True\n-0,False\n1.2e-05,True\n"
    data = _typed(csv_text, {"n": "number", "b": "boolean"})["data"]
    assert data == [[1e20, True], [-0.0, False], [1.2e-05, True]]


@pytest.mark.parametrize(
    ("csv_text", "kinds", "message"),
    [
        ("a,b\n1,2\n", ColumnKinds({"b": "integer", "a": "integer"}), "do not name"),
        ("a\n1,2\n", ColumnKinds({"a": "integer"}), "2 cells for 1 columns"),
        ("a\nyes\n", ColumnKinds({"a": "boolean"}), "canonical boolean"),
        ("a\ninf\n", ColumnKinds({"a": "number"}), "finite"),
        ("a\n2024-01\n", ColumnKinds({"a": "date"}), "plain ISO date"),
        ("a\n0001-01-01T00:30:00+01:00\n", ColumnKinds({"a": "datetime"}), "years 1 to 9999"),
        ("a\n9999-12-31T23:30:00-01:00\n", ColumnKinds({"a": "datetime"}), "years 1 to 9999"),
        ("a\nnoon\n", ColumnKinds({"a": "datetime"}), "ISO timestamp"),
    ],
)
def test_what_a_canonical_csv_never_holds_is_refused(csv_text: str, kinds: ColumnKinds, message: str) -> None:
    with pytest.raises(ValueError, match=message):
        typed_json(csv_text, kinds)


def test_the_worst_tables_of_the_parsers_caps_fit_the_wire() -> None:
    """At the parser's 20,000 rows and 50 columns: a table of missing cells (one character in the CSV, `null` in the
    JSON) and one of three backslashes per cell (a CSV of about 4 MiB, each escaped and quoted in the JSON) stay
    under `MAX_DATA_JSON_CHARS`, whose docstring quotes the larger size."""
    header = ",".join(f"c{index:02d}" for index in range(MAX_COLUMNS))
    kinds = ColumnKinds({f"c{index:02d}": "text" for index in range(MAX_COLUMNS)})
    sizes = []
    for cell in ("", "\\\\\\"):
        csv_text = header + "\n" + (",".join([cell] * MAX_COLUMNS) + "\n") * MAX_ROWS
        assert len(csv_text) <= MAX_DATA_CSV_CHARS
        sizes.append(len(typed_json(csv_text, kinds)))
    assert max(sizes) < MAX_DATA_JSON_CHARS
    assert sizes == [5_040_322, 9_040_322]  # the docstring's 5.04 and 9.04 million
