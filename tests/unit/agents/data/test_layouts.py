"""The two pasted layouts the delimited reader does not see: a web table copied one cell per line, a pair list.

All data here is invented. The page routes the same shapes as data (`routeInput.ts`); the shared cases in
`routeInput.cases.json` hold the two sides together (`tests/unit/agents/test_route_cases.py`).
"""

import json
from pathlib import Path

import pytest

from agents.anyplot.data.layouts import (
    LOWERCASE_WISH_WORDS,
    MIN_PAIRS_WITH_DATA,
    MISSING_TOKENS,
    WISH_WORDS,
    cell_kind,
    cell_lines_table,
    is_pair,
    is_wish,
    pair_list_table,
    read_layout,
)
from agents.anyplot.data.parse import MISSING_VALUES, ParseError, parse_dataset
from agents.anyplot.data.transcribe import looks_like_free_text


WISH_WORDS_FILE = Path(__file__).resolve().parents[4] / "app" / "src" / "sections" / "agent-chat" / "wishWords.json"


WEB_TABLE = (
    "runs · mean · min–max\n\nNorthwind\n\n214\n\n87.3\n\n58–99\n\nSouthgate\n\n198\n\n84.9\n\n61–97\n\n"
    "Eastholm\n\n207\n\n90.1\n\n66–100\n\nruns\nmean\nmin–max"
)
"""The shape of a dashboard table copied in a browser: a header line split at ` · `, blocks of four cells (a name,
a count, a mean, a range) with blank lines between the cells, and the column labels repeated at the foot."""


class TestCellLines:
    def test_a_web_table_reads_its_blocks_header_and_foot(self) -> None:
        layout = cell_lines_table(WEB_TABLE)

        assert layout is not None and layout.kind == "cell_lines"
        assert layout.headers == ["label", "runs", "mean", "min–max"]
        assert layout.rows == [
            ["Northwind", "214", "87.3", "58–99"],
            ["Southgate", "198", "84.9", "61–97"],
            ["Eastholm", "207", "90.1", "66–100"],
        ]
        assert layout.note == (
            "read one cell per line: 3 rows of 4 columns; the first column is named label; "
            "left out 3 lines below the table, kept as a note"
        )
        assert layout.notes == ["runs, mean, min–max"]

    def test_a_range_cell_stays_one_text_cell(self) -> None:
        parsed = parse_dataset(WEB_TABLE)

        assert parsed.column_dtypes == {"label": "text", "runs": "integer", "mean": "number", "min–max": "text"}
        assert parsed.profile.source_format == "cell_lines"
        assert parsed.context_lines == ["runs, mean, min–max"]
        assert parsed.warnings[0].startswith("read one cell per line: 3 rows of 4 columns")
        assert not looks_like_free_text(parsed)

    def test_names_come_from_one_line_per_column_under_an_optional_title(self) -> None:
        block = cell_lines_table("Station\nTemp\nRain\n\nAlder\n\n9.8\n\n812\n\nBirch\n\n9.1\n\n790")
        titled = cell_lines_table("Weather 2024\nStation\nTemp\nRain\nAlder\n9.8\n812\nBirch\n9.1\n790")

        assert block is not None and block.headers == ["Station", "Temp", "Rain"] and block.notes == []
        assert titled is not None and titled.headers == ["Station", "Temp", "Rain"]
        assert titled.notes == ["Weather 2024"]
        assert "the line above the column names kept as a note" in titled.note

    def test_without_a_header_the_columns_get_generic_names(self) -> None:
        pairs = cell_lines_table("North\n12\nSouth\n9\nEast\n15")
        wide = cell_lines_table("North\n12\n3.5\nSouth\n9\n2.5\nEast\n15\n4.0")

        assert pairs is not None and pairs.headers == ["label", "value"]
        assert (
            pairs.note
            == "read one cell per line: 3 rows of 2 columns; no header line, so the columns are named label, value"
        )
        assert wide is not None and wide.headers == ["label", "value 1", "value 2"]

    def test_the_smallest_block_wins_over_its_repetition(self) -> None:
        layout = cell_lines_table("A\n1\nB\n2\nC\n3\nD\n4")

        assert layout is not None and len(layout.headers) == 2 and len(layout.rows) == 4

    @pytest.mark.parametrize(
        "text",
        [
            "Alpha\nBeta\nGamma\nDelta",  # names only: no value in a block
            "1\n2\n3\n4",  # values only: no label starts a block
            "Alpha\n1\nBeta\n2\nGamma\n3\n4",  # a value below the rows is a broken row, not a label block
            "Alpha\n1",  # one block is no table
            "Alpha\n1\nBeta\nx\nGamma\n3",  # the pattern breaks off after one block
            "Wert\n12\nkeine Angabe\n17",  # a one-column list: two blocks need a header line above them
            "value\n2026-01-01\nNaN\n2026-01-03",  # a missing token is never a label
        ],
    )
    def test_any_other_shape_is_no_table(self, text: str) -> None:
        assert cell_lines_table(text) is None

    def test_a_missing_token_stands_in_for_a_value(self) -> None:
        layout = cell_lines_table("Site\nScore\nAlder\n9\nBirch\n-\nCedar\n7")

        assert layout is not None and layout.rows == [["Alder", "9"], ["Birch", "-"], ["Cedar", "7"]]

    def test_the_missing_tokens_are_the_parsers(self) -> None:
        assert MISSING_TOKENS == MISSING_VALUES - {""}

    def test_cell_kinds(self) -> None:
        assert [cell_kind(cell) for cell in ("87.3", "2024-01-05", "58–99", "1,5-2,5", "Alpha", "10:30", "n/a")] == [
            "value",
            "value",
            "range",
            "range",
            "text",
            "value",
            "missing",
        ]


class TestPairList:
    @pytest.mark.parametrize(
        ("text", "rows"),
        [
            ("a:7,b:12,c:5", [["a", "7"], ["b", "12"], ["c", "5"]]),
            ("a=7; b=12; c=5", [["a", "7"], ["b", "12"], ["c", "5"]]),
            ("Apples 7, Pears 12", [["Apples", "7"], ["Pears", "12"]]),
            ("Jan: 5\nFeb: 7\nMar: 9", [["Jan", "5"], ["Feb", "7"], ["Mar", "9"]]),
            ("a: 7,5; b: 12,0", [["a", "7,5"], ["b", "12,0"]]),
            ("Q1:5,Q2:7,Q3:9", [["Q1", "5"], ["Q2", "7"], ["Q3", "9"]]),
            ("2024: 7\n2025: 9", [["2024", "7"], ["2025", "9"]]),
            ("New York 5, Los Angeles 7", [["New York", "5"], ["Los Angeles", "7"]]),
            ("Hund 7, Katze 3\nVogel 4, Maus 2", [["Hund", "7"], ["Katze", "3"], ["Vogel", "4"], ["Maus", "2"]]),
        ],
    )
    def test_pairs_of_one_form_read_as_two_columns(self, text: str, rows: list[list[str]]) -> None:
        layout = pair_list_table(text)

        assert layout is not None and layout.kind == "pair_list"
        assert layout.headers == ["label", "value"]
        assert layout.rows == rows
        assert layout.note == f"read a list of {len(rows)} label/value pairs as two columns, named label and value"

    def test_a_first_line_of_two_words_names_the_columns(self) -> None:
        layout = pair_list_table("Monat Umsatz\nJan 5\nFeb 7\nMar 9")

        assert layout is not None and layout.headers == ["Monat", "Umsatz"] and len(layout.rows) == 3
        assert layout.note == "read a list of 3 label/value pairs as two columns"

    @pytest.mark.parametrize(
        "text",
        [
            "a:7",  # a single pair
            "make it 16:9",  # a ratio
            "at 10:30",  # a clock time
            "use 16:9, or 4:3",
            "a:7, b=12",  # two forms
            "a:7, b:x",  # a value that is no number
            "x from 1 to 10, step 2",  # a clause, no label
            "Set y from 0 to 10, please",
            "https://example.com/data?a=1,b=2",
            "name,city\nAnna,Wien",
        ],
    )
    def test_anything_else_is_no_pair_list(self, text: str) -> None:
        assert pair_list_table(text) is None

    def test_a_header_of_pairs_is_no_header(self) -> None:
        assert is_pair("Hund 7") and is_pair("a: 7") and not is_pair("Umsatz") and not is_pair("16:9")


class TestChangeRequests:
    """The live regression of 2026-11-09: a change request in words replaced a table with two `label`/`value` rows."""

    @pytest.mark.parametrize(
        "text",
        [
            "x bis 2030, y bis 60",
            "y-Achse 0 bis 3500, Linie 2500",
            "Titel 2026, Schrift 14",
            "y max 60, x max 2030",
            "x 2030, y 60",  # an axis letter alone is no label
            "x=1, y=2, z=3",
            "Schriftgröße 14, Breite 800",
            "Y MAX 60, X MAX 2030",  # capitals are no first name
            "dpi 300, margin 20, padding 10",
            "Rand 5, Abstand 2, Rahmen 1",
        ],
    )
    def test_a_change_request_is_no_pair_list(self, text: str) -> None:
        assert pair_list_table(text) is None
        assert pair_list_table(text, min_pairs=MIN_PAIRS_WITH_DATA) is None
        with pytest.raises(ParseError):
            parse_dataset(text)

    def test_a_name_with_a_capital_is_no_wish(self) -> None:
        assert not is_wish("Max 7, Lisa 5, Tim 2") and is_wish("y max 60")
        layout = pair_list_table("Max 7, Lisa 5, Tim 2", min_pairs=MIN_PAIRS_WITH_DATA)
        assert layout is not None and len(layout.rows) == 3

    def test_a_wish_word_counts_only_as_a_whole_word(self) -> None:
        assert is_wish("y-Achse 0") and is_wish("5 bis 7") and is_wish("Ändere")
        assert not is_wish("Tobias 7, Bismarck 3") and not is_wish("Linienbus 4")

    def test_while_the_session_holds_data_a_list_takes_three_pairs(self) -> None:
        assert pair_list_table("Apples 7, Pears 12") is not None
        assert pair_list_table("Apples 7, Pears 12", min_pairs=MIN_PAIRS_WITH_DATA) is None
        assert pair_list_table("Apples 7, Pears 12, Plums 5", min_pairs=MIN_PAIRS_WITH_DATA) is not None
        assert read_layout("Hund 7\nKatze 3", min_pairs=MIN_PAIRS_WITH_DATA) is None

    def test_the_web_table_is_read_whatever_its_header_says(self) -> None:
        """`min–max` in a header is no wish there: the one-cell-per-line reading takes no wish veto."""
        assert read_layout(WEB_TABLE, min_pairs=MIN_PAIRS_WITH_DATA) is not None

    def test_the_wish_words_are_the_pages(self) -> None:
        shared = json.loads(WISH_WORDS_FILE.read_text(encoding="utf-8"))

        assert tuple(shared["words"]) == WISH_WORDS
        assert tuple(shared["lowercase_only"]) == LOWERCASE_WISH_WORDS


class TestParseDataset:
    def test_a_pair_list_on_one_line_is_a_table_no_more_a_header_without_rows(self) -> None:
        parsed = parse_dataset("a:7,b:12,c:5")

        assert parsed.csv == "label,value\na,7\nb,12\nc,5\n"
        assert parsed.profile.source_format == "pair_list"

    def test_pairs_the_csv_reader_took_for_a_header_are_read_as_pairs(self) -> None:
        """`Hund 7, Katze 3` over one or two rows read as a header of pairs before: no names, a wrong table."""
        two = parse_dataset("Hund 7, Katze 3\nVogel 4, Maus 2")
        three = parse_dataset("Hund 7, Katze 3\nVogel 4, Maus 2\nPferd 1, Esel 5")

        assert two.profile.rows == 4 and three.profile.rows == 6
        assert two.column_dtypes == {"label": "text", "value": "integer"}

    @pytest.mark.parametrize(
        ("text", "source_format"),
        [
            ("month,sales\nJan,5\nFeb,7", "csv"),
            ("Q1 2024,Q2 2024\n5,7\n6,8", "csv"),
            ("Region\tSales\nNorth\t5\nSouth\t7", "tsv"),
            ("sales\n5\n7\n9", "csv"),
        ],
    )
    def test_a_table_the_reader_reads_keeps_its_reading(self, text: str, source_format: str) -> None:
        assert parse_dataset(text).profile.source_format == source_format

    def test_a_reread_of_the_services_own_csv_never_reads_a_layout(self) -> None:
        """`find_table=False` and `canonical=True` re-read a table the service wrote: its rows stay as they are."""
        text = "Tier Anzahl\nHund 7\nKatze 3\n"

        assert read_layout(text) is not None
        assert [column.name for column in parse_dataset(text, find_table=False).profile.columns] == ["Tier Anzahl"]
        assert [column.name for column in parse_dataset(text, canonical=True).profile.columns] == ["Tier Anzahl"]
