"""Tests for agents/anyplot/data/parse.py: limits, sanitising, headers, formats, typing, profile, round trip."""

import io
import json
import sys
import time
from dataclasses import replace
from typing import Any

import pandas as pd
import pytest

from agents.anyplot.data import parse as parse_module
from agents.anyplot.data.bindings import default_bindings
from agents.anyplot.data.parse import (
    MAX_COMPUTED_BYTES,
    MAX_CONTEXT_CHARS,
    MAX_INPUT_BYTES,
    MAX_INPUT_CELL_CHARS,
    MISSING_VALUES,
    PREVIEW_ROWS,
    ParsedDataset,
    ParseError,
    canonical_headers,
    pandas_dtypes,
    parse_dataset,
    sniff_delimiter,
    without_context,
)
from agents.anyplot.data.roles import DataRole
from agents.anyplot.schemas import (
    MAX_CELL_CHARS,
    MAX_COLUMN_NAME_CHARS,
    MAX_COLUMNS,
    MAX_MESSAGE_CHARS,
    MAX_ROWS,
    MAX_SAMPLE_ROWS,
    MAX_TOP_VALUES,
    MAX_WARNINGS,
)


# Named escapes keep invisible and combining characters visible in the source.
ZWSP = "\N{ZERO WIDTH SPACE}"
BOM = "\N{ZERO WIDTH NO-BREAK SPACE}"
RLO = "\N{RIGHT-TO-LEFT OVERRIDE}"
PDF = "\N{POP DIRECTIONAL FORMATTING}"
LRI = "\N{LEFT-TO-RIGHT ISOLATE}"
RLI = "\N{RIGHT-TO-LEFT ISOLATE}"
PDI = "\N{POP DIRECTIONAL ISOLATE}"
ACUTE = "\N{COMBINING ACUTE ACCENT}"
E_ACUTE = "\N{LATIN SMALL LETTER E WITH ACUTE}"
ARABIC_12 = "\N{ARABIC-INDIC DIGIT ONE}\N{ARABIC-INDIC DIGIT TWO}"


def read_back(parsed: ParsedDataset) -> pd.DataFrame:
    """What the loader does with the exported data.csv."""
    return pd.read_csv(
        io.StringIO(parsed.csv), dtype=pandas_dtypes(parsed.column_dtypes), parse_dates=parsed.parse_dates
    )


def error_code(text: str) -> str:
    with pytest.raises(ParseError) as caught:
        parse_dataset(text)
    return caught.value.code


def column(parsed: ParsedDataset, name: str) -> Any:
    return next(c for c in parsed.profile.columns if c.name == name)


def warned(parsed: ParsedDataset, fragment: str) -> bool:
    return any(fragment in warning for warning in parsed.warnings)


class TestDecimalCommaAndDateGuard:
    def test_semicolon_file_with_decimal_comma_and_german_dates(self) -> None:
        parsed = parse_dataset("Datum;Umsatz\n01.02.2024;1.234,56\n15.03.2024;7,5\n")

        assert parsed.profile.source_format == "semicolon"
        assert parsed.profile.decimal == ","
        assert parsed.column_dtypes == {"Datum": "datetime", "Umsatz": "number"}
        assert parsed.parse_dates == ["Datum"]
        assert parsed.csv == "Datum,Umsatz\n2024-02-01,1234.56\n2024-03-15,7.5\n"

    def test_a_dd_mm_yyyy_column_is_never_a_thousands_dot_number(self) -> None:
        parsed = parse_dataset("Datum;Wert\n01.02.2024;1,5\n03.04.2024;2,5\n")

        assert column(parsed, "Datum").dtype == "datetime"
        assert column(parsed, "Datum").min == "2024-02-01"
        assert column(parsed, "Wert").max == 2.5

    def test_thousands_dots_in_a_decimal_comma_file(self) -> None:
        parsed = parse_dataset("Preis;Menge\n3,50;1.200\n2,10;800\n")

        assert parsed.column_dtypes == {"Preis": "number", "Menge": "integer"}
        assert parsed.csv.splitlines()[1:] == ["3.5,1200", "2.1,800"]
        assert warned(parsed, "column 'Menge': dots read as thousands separators")

    def test_a_zero_leading_group_keeps_dot_decimals_in_a_decimal_comma_file(self) -> None:
        parsed = parse_dataset("rate;amount\n0.125;1,5\n1.250;2,5\n")

        assert column(parsed, "rate").dtype == "number"
        assert parsed.csv.splitlines()[1:] == ["0.125,1.5", "1.25,2.5"]
        assert not warned(parsed, "column 'rate': dots read as thousands separators")

    def test_dot_decimals_stay_dot_decimals_without_a_comma_column(self) -> None:
        parsed = parse_dataset("a,b\n1.200,x\n0.800,y\n")

        assert column(parsed, "a").dtype == "number"
        assert column(parsed, "a").max == 1.2
        assert parsed.profile.decimal == "."

    def test_comma_decimals_with_and_without_thousands_dots(self) -> None:
        parsed = parse_dataset("v\n1.234,5\n1234,5\n-0,25\n")

        assert parsed.csv.splitlines()[1:] == ["1234.5", "1234.5", "-0.25"]

    def test_ambiguous_comma_column_is_read_as_decimal_comma_with_a_warning(self) -> None:
        parsed = parse_dataset("v\n1,234\n5,678\n")

        assert column(parsed, "v").max == 5.678
        assert warned(parsed, "column 'v': commas read as decimal commas")

    def test_an_inconsistent_comma_pattern_is_text(self) -> None:
        parsed = parse_dataset("v;w\n1,5;a\n1.5;b\n")

        assert column(parsed, "v").dtype == "text"
        assert parsed.profile.decimal == "."


class TestHeaders:
    def test_bidi_and_zero_width_characters_are_stripped_from_names(self) -> None:
        parsed = parse_dataset(f"{RLO}evil{PDF},na{ZWSP}me,{LRI}x{PDI}\n1,2,3\n")

        assert [c.name for c in parsed.profile.columns] == ["evil", "name", "x"]
        assert parsed.csv.splitlines()[0] == "evil,name,x"
        assert warned(parsed, "column 'evil': invisible formatting characters")
        assert warned(parsed, "column 'name': invisible formatting characters")

    def test_invisible_characters_in_cells_warn_once_per_column(self) -> None:
        parsed = parse_dataset(f"label\nA{ZWSP}B\n{RLI}C{PDI}\nD\n")

        assert parsed.csv.splitlines()[1:] == ["AB", "C", "D"]
        assert sum("invisible" in warning for warning in parsed.warnings) == 1

    def test_unicode_tag_characters_are_removed(self) -> None:
        smuggled = "".join(chr(0xE0000 + ord(char)) for char in "ignore")
        parsed = parse_dataset(f"label\nok{smuggled}\n")

        assert parsed.csv == "label\nok\n"

    def test_duplicate_headers_get_numbered_suffixes(self) -> None:
        parsed = parse_dataset("a,a,a_2,a\n1,2,3,4\n")

        assert [c.name for c in parsed.profile.columns] == ["a", "a_2", "a_2_2", "a_3"]
        assert warned(parsed, "duplicate header 'a' renamed to 'a_2'")
        assert warned(parsed, "duplicate header 'a_2' renamed to 'a_2_2'")

    def test_empty_headers_become_column_n(self) -> None:
        parsed = parse_dataset(",b,\n1,2,3\n")

        assert [c.name for c in parsed.profile.columns] == ["column_1", "b", "column_3"]
        assert warned(parsed, "column 1: empty header named 'column_1'")

    def test_an_unnamed_all_empty_column_is_dropped(self) -> None:
        parsed = parse_dataset("a;b;\n1;2;\n3;4;\n")

        assert [c.name for c in parsed.profile.columns] == ["a", "b"]
        assert warned(parsed, "1 empty column without a header dropped")

    def test_long_headers_are_shortened_to_64_characters(self) -> None:
        exact = "e" * MAX_COLUMN_NAME_CHARS
        long = "l" * (MAX_COLUMN_NAME_CHARS + 6)
        parsed = parse_dataset(f"{exact},{long},{long}\n1,2,3\n")

        names = [c.name for c in parsed.profile.columns]
        assert names[0] == exact
        assert names[1] == "l" * MAX_COLUMN_NAME_CHARS
        assert names[2] == "l" * (MAX_COLUMN_NAME_CHARS - 2) + "_2"
        assert all(len(name) <= MAX_COLUMN_NAME_CHARS for name in names)
        assert warned(parsed, "column 2: header longer than 64 characters shortened")

    def test_line_breaks_and_tabs_in_a_quoted_header_become_spaces(self) -> None:
        parsed = parse_dataset('"first\nsecond",b\n1,2\n')

        assert column(parsed, "first second").dtype == "integer"
        assert warned(parsed, "column 'first second': tabs or line breaks in the header replaced with spaces")

    def test_numeric_headers_hint_that_the_first_row_is_data(self) -> None:
        parsed = parse_dataset("1,2\n3,4\n")

        assert warned(parsed, "the first row may be data")

    def test_canonical_headers_reports_every_rename(self) -> None:
        names, warnings = canonical_headers(["x", "", "x"])

        assert names == ["x", "column_2", "x_2"]
        assert len(warnings) == 2


class TestErrors:
    def test_the_canonical_csv_has_its_own_boundary(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """A paste within its cap whose canonical CSV grows past `MAX_CANONICAL_BYTES` is `too_long`."""
        text = "v\n" + "7e15\n" * 10  # each cell becomes 7000000000000000.0 in the canonical CSV
        canonical = len(parse_dataset(text).csv.encode("utf-8"))
        assert canonical > 2 * len(text)

        monkeypatch.setattr(parse_module, "MAX_CANONICAL_BYTES", canonical)
        assert parse_dataset(text).profile.rows == 10
        monkeypatch.setattr(parse_module, "MAX_CANONICAL_BYTES", canonical - 1)
        assert error_code(text) == "too_long"

    def test_computed_data_takes_its_own_byte_cap(self) -> None:
        text = "label,v\n" + "".join(f"{'k' * 58},{i}\n" for i in range(18_000))
        assert MAX_INPUT_BYTES < len(text.encode("utf-8")) <= MAX_COMPUTED_BYTES

        assert error_code(text) == "too_long"
        assert parse_dataset(text, find_table=False, max_bytes=MAX_COMPUTED_BYTES).profile.rows == 18_000

    def test_size_boundary_is_1_mib_of_utf8_bytes(self) -> None:
        rows = (MAX_INPUT_BYTES - 2) // 100
        text = "v\n" + ("a" * 99 + "\n") * rows
        text += "b" * (MAX_INPUT_BYTES - len(text) - 1) + "\n"
        assert len(text.encode("utf-8")) == MAX_INPUT_BYTES

        assert parse_dataset(text).profile.rows == rows + 1
        assert error_code(text + "c") == "too_long"

    def test_size_counts_bytes_not_characters(self) -> None:
        text = "v\n" + E_ACUTE * (MAX_INPUT_BYTES // 2)

        assert len(text) < MAX_INPUT_BYTES
        assert error_code(text) == "too_long"

    @pytest.mark.parametrize("char", ["\x00", "\x07", "\x1b", "\x7f", "\x85", "\x9f"])
    def test_control_characters_are_refused(self, char: str) -> None:
        with pytest.raises(ParseError) as caught:
            parse_dataset(f"a,b\n1,2\n3,x{char}y\n")

        assert caught.value.code == "control_chars"
        assert "line 3" in caught.value.message

    def test_tab_newline_and_carriage_return_are_allowed(self) -> None:
        parsed = parse_dataset('a,b\r\n"x\ty",2\r\n')

        assert parsed.csv == "a,b\nx\ty,2\n"

    def test_control_characters_from_json_escapes_are_refused(self) -> None:
        assert error_code('[{"a": "x\\u0007"}]') == "control_chars"
        assert error_code('{"a\\u0000": [1]}') == "control_chars"

    def test_lone_surrogates_are_unparseable(self) -> None:
        assert error_code("a\n" + chr(0xD800) + "\n") == "unparseable"
        assert error_code('[{"a": "\\ud800"}]') == "unparseable"
        assert error_code('{"\\udfff": [1]}') == "unparseable"

    def test_column_boundary(self) -> None:
        header = ",".join(f"c{i}" for i in range(MAX_COLUMNS))
        row = ",".join("1" for _ in range(MAX_COLUMNS))

        assert len(parse_dataset(f"{header}\n{row}\n").profile.columns) == MAX_COLUMNS
        assert error_code(f"{header},extra\n{row},1\n") == "too_many_columns"

    def test_row_boundary(self) -> None:
        text = "v\n" + "1\n" * MAX_ROWS

        assert parse_dataset(text).profile.rows == MAX_ROWS
        assert error_code(text + "1\n") == "too_many_rows"

    def test_json_row_and_column_boundaries(self) -> None:
        assert error_code(json.dumps([{"a": 1}] * (MAX_ROWS + 1))) == "too_many_rows"
        assert error_code(json.dumps({"a": [1] * (MAX_ROWS + 1)})) == "too_many_rows"
        assert error_code(json.dumps([{f"c{i}": 1 for i in range(MAX_COLUMNS + 1)}])) == "too_many_columns"
        assert error_code(json.dumps({f"c{i}": [1] for i in range(MAX_COLUMNS + 1)})) == "too_many_columns"

    def test_cell_boundary(self) -> None:
        assert parse_dataset("v\n" + "x" * MAX_INPUT_CELL_CHARS + "\n").profile.rows == 1

        with pytest.raises(ParseError) as caught:
            parse_dataset("v\nSECRET" + "x" * MAX_INPUT_CELL_CHARS + "\n")
        assert caught.value.code == "cell_too_long"
        assert "column 'v'" in caught.value.message
        assert "SECRET" not in caught.value.message

    def test_a_header_longer_than_the_cell_limit_is_refused(self) -> None:
        assert error_code("h" * (MAX_INPUT_CELL_CHARS + 1) + "\n1\n") == "cell_too_long"

    @pytest.mark.parametrize(
        "shape",
        ["v\n{big}\n", "a\tb\nx\t{big}\n", '[{{"id": "{big}"}}]', '{{"a": "{big}"}}', "v\n{big} kg\n", "v\n€ {big}\n"],
    )
    def test_a_numeric_cell_over_the_int_digit_limit_is_cell_too_long(self, shape: str) -> None:
        """The length check runs before typing: `int()` refuses more than 4,300 digits with a ValueError of its own."""
        big = "1" * (sys.get_int_max_str_digits() + 1)

        with pytest.raises(ParseError) as caught:
            parse_dataset(shape.format(big=big))
        assert caught.value.code == "cell_too_long"
        assert "111" not in caught.value.message

    @pytest.mark.parametrize(
        ("text", "named"),
        [
            (",b\n" + "x" * 201 + ",1\n", "column_1"),
            ('"a\nb"\n' + "x" * 201 + "\n", "a b"),
            ("v\n" + "x" * 201 + " %\n", "v"),
        ],
    )
    def test_a_cell_too_long_names_the_column_by_its_cleaned_header(self, text: str, named: str) -> None:
        with pytest.raises(ParseError) as caught:
            parse_dataset(text)

        assert caught.value.code == "cell_too_long"
        assert f"column '{named}'" in caught.value.message

    @pytest.mark.parametrize(
        "text",
        [
            "",
            "  \n\n ",
            "a,b\n1,2,3\n",
            'a,b\n"x"y,1\n',
            'a,b\n"x,1\n',
            "[1, 2",
            "[]",
            "{}",
            "()",
            "[1, 2]",
            "(1, 2)",
            "x = [1, 2]",
            '[{"a": {"nested": 1}}]',
            '[{"a": [1, 2]}]',
            '{"a": [1, 2], "b": [1]}',
            '{"a": 1, "b": [2]}',
            '{"a": [[1]]}',
            '[["a", 65], ["b"]]',
            '[["a", 65], {"b": 12}]',
            "[" * 5000 + "]" * 5000,
        ],
    )
    def test_unparseable(self, text: str) -> None:
        # `{"a": 1}` was in this list until the parser read an object of values as pairs (2026-10-11).
        assert error_code(text) == "unparseable"

    @pytest.mark.parametrize(
        "text", ["a,b\n", '"just a string"', "Hund 7 Katze 3 und Vogel 4", "Hund 7, Katze 3, Vogel 4\n"]
    )
    def test_text_with_no_table_in_it_has_its_own_code(self, text: str) -> None:
        """A header line alone, prose, a list on one line: `no_table`, which the route hands to the transcriber."""
        assert error_code(text) == "no_table"

    def test_messages_never_quote_the_data(self) -> None:
        for text in (
            'a,b\n"SECRET"y,1\n',
            "a,b\nSECRET,2,SECRET\n",
            '[{"a": {"SECRET": 1}}]',
            "x = [SECRET]",
            "{'SECRET': {'a': 1}}",
            "{'SECRET': 1, 'b': [2]}",
        ):
            with pytest.raises(ParseError) as caught:
                parse_dataset(text)
            assert "SECRET" not in caught.value.message


class TestFormats:
    @pytest.mark.parametrize(
        ("text", "source_format"),
        [("a,b\n1,2\n", "csv"), ("a;b\n1;2\n", "semicolon"), ("a\tb\n1\t2\n", "tsv"), ("a|b\n1|2\n", "pipe")],
    )
    def test_each_delimiter(self, text: str, source_format: str) -> None:
        parsed = parse_dataset(text)

        assert parsed.profile.source_format == source_format
        assert parsed.csv == "a,b\n1,2\n"

    def test_quoted_delimiters_do_not_split(self) -> None:
        parsed = parse_dataset('name,city\n"Smith, John","Paris; France"\n')

        assert column(parsed, "name").top == ["Smith, John"]
        assert column(parsed, "city").top == ["Paris; France"]

    def test_single_column(self) -> None:
        parsed = parse_dataset("name\nSmith, John\n1,5\n")

        assert parsed.profile.source_format == "csv"
        assert [c.name for c in parsed.profile.columns] == ["name"]
        assert parsed.profile.rows == 2

    def test_single_numeric_column_with_decimal_commas(self) -> None:
        parsed = parse_dataset("wert\n1,5\n2,5\n")

        assert parsed.column_dtypes == {"wert": "number"}
        assert parsed.profile.decimal == ","

    def test_sniffing_prefers_the_delimiter_that_splits_the_header(self) -> None:
        assert sniff_delimiter("a;b\n1,5;2,5\n3,5;4,5\n") == (";", "semicolon")
        assert sniff_delimiter("a,b\n1,2\n") == (",", "csv")
        assert sniff_delimiter("only\n1,2\n") == (None, "csv")

    def test_crlf_and_cr_line_ends(self) -> None:
        assert parse_dataset("a,b\r\n1,2\r\n3,4\r\n").csv == "a,b\n1,2\n3,4\n"
        assert parse_dataset("a,b\r1,2\r3,4\r").csv == "a,b\n1,2\n3,4\n"

    def test_line_breaks_inside_a_quoted_cell_become_lf(self) -> None:
        parsed = parse_dataset('a,b\n"one\r\ntwo",1\n')

        assert parsed.csv == 'a,b\n"one\ntwo",1\n'

    def test_bom_is_stripped(self) -> None:
        parsed = parse_dataset(f"{BOM}a,b\n1,2\n")

        assert [c.name for c in parsed.profile.columns] == ["a", "b"]

    def test_nfc_normalisation(self) -> None:
        parsed = parse_dataset(f"Cafe{ACUTE}\nre{ACUTE}sume{ACUTE}\n")

        assert parsed.profile.columns[0].name == f"Caf{E_ACUTE}"
        assert parsed.csv == f"Caf{E_ACUTE}\nr{E_ACUTE}sum{E_ACUTE}\n"

    def test_blank_lines_are_skipped_and_short_rows_padded(self) -> None:
        parsed = parse_dataset("a,b,c\n\n1,2,3\n;\n4,5\n,,\n")

        assert parsed.profile.rows == 3
        assert parsed.csv.splitlines()[1:] == ["1,2,3", ";,,", "4,5,"]
        assert warned(parsed, "2 rows had fewer fields than the header")

    def test_trailing_empty_fields_beyond_the_header_are_ignored(self) -> None:
        assert parse_dataset("a,b\n1,2,,\n").csv == "a,b\n1,2\n"

    def test_json_records(self) -> None:
        parsed = parse_dataset('[{"x": 1, "label": "a"}, {"x": 2.5, "flag": true}, {"x": null, "label": "c"}]')

        assert parsed.profile.source_format == "json_records"
        assert parsed.column_dtypes == {"x": "number", "label": "text", "flag": "boolean"}
        assert parsed.csv == "x,label,flag\n1.0,a,\n2.5,,True\n,c,\n"
        assert warned(parsed, "3 records lack some keys")

    def test_one_incomplete_json_record_takes_a_singular_verb(self) -> None:
        parsed = parse_dataset('[{"x": 1, "y": 2}, {"x": 3}]')

        assert warned(parsed, "1 record lacks some keys")

    def test_json_columns(self) -> None:
        parsed = parse_dataset('{"day": ["2024-01-01", "2024-01-02"], "n": [3, NaN]}')

        assert parsed.profile.source_format == "json_columns"
        assert parsed.column_dtypes == {"day": "datetime", "n": "integer"}
        assert column(parsed, "n").missing == 1

    def test_json_with_surrounding_whitespace(self) -> None:
        assert parse_dataset('\n  [{"a": 1}]  \n').profile.rows == 1

    def test_a_json_object_of_values_is_a_category_value_table_in_its_order(self) -> None:
        parsed = parse_dataset('{"Schlafen & Dösen": 65, "Fellpflege": 12, "Fressen & Betteln": 8, "Rest": null}')

        assert parsed.profile.source_format == "json_pairs"
        assert parsed.column_dtypes == {"category": "text", "value": "integer"}
        assert parsed.csv == "category,value\nSchlafen & Dösen,65\nFellpflege,12\nFressen & Betteln,8\nRest,\n"
        assert column(parsed, "value").missing == 1
        assert not parsed.warnings

    def test_a_json_array_of_pairs_is_the_same_table(self) -> None:
        parsed = parse_dataset('[["a", 65], ["b", 12.5], [3, true]]')

        assert parsed.profile.source_format == "json_pairs"
        assert parsed.column_dtypes == {"category": "text", "value": "text"}
        assert parsed.csv == "category,value\na,65\nb,12.5\n3,true\n"

    def test_json_pairs_row_boundary(self) -> None:
        # Single CJK characters keep 20,001 distinct keys under the 200 KB input cap.
        keys = {chr(0x4E00 + i): 1 for i in range(MAX_ROWS + 1)}
        compact = {"ensure_ascii": False, "separators": (",", ":")}

        assert error_code(json.dumps(keys, **compact)) == "too_many_rows"
        assert error_code(json.dumps([["k", 1]] * (MAX_ROWS + 1), **compact)) == "too_many_rows"
        assert parse_dataset(json.dumps([["k", 1]] * MAX_ROWS, **compact)).profile.rows == MAX_ROWS

    @pytest.mark.parametrize(
        "text", ['{"2023": 65, "2024": 12}', '{"2024-01-01": 65, "2024-02-01": 12}', "{1: 5, 2: 7}", '{"true": 1}']
    )
    def test_the_keys_of_a_pairs_table_stay_text(self, text: str) -> None:
        """The keys are names, so `category` is text whatever they look like; `value` is typed as usual."""
        parsed = parse_dataset(text)

        assert parsed.column_dtypes == {"category": "text", "value": "integer"}
        assert column(parsed, "category").top
        assert column(parsed, "category").min is None

    def test_a_repeated_key_keeps_its_last_value_with_a_warning(self) -> None:
        as_json = parse_dataset('{"Jan": 5, "Feb": 3, "Jan": 7}')
        as_literal = parse_dataset("x = {'Jan': 5, 'Feb': 3, 'Jan': 7, 'Feb': 1}")
        as_pairs = parse_dataset('[["Jan", 5], ["Feb", 3], ["Jan", 7]]')
        in_records = parse_dataset('[{"a": 1, "a": 2}, {"a": 3}]')

        assert as_json.csv == "category,value\nJan,7\nFeb,3\n"
        assert as_json.warnings == ["1 key repeated; only the last value of a repeated key is kept"]
        assert as_literal.csv == "category,value\nJan,7\nFeb,1\n"
        assert as_literal.warnings == ["2 keys repeated; only the last value of a repeated key is kept"]
        assert as_pairs.csv == "category,value\nJan,5\nFeb,3\nJan,7\n"
        assert not as_pairs.warnings
        assert in_records.csv == "a\n2\n3\n"
        assert warned(in_records, "1 key repeated")

    def test_brackets_inside_strings_and_comments_are_not_nesting(self) -> None:
        """Main parsed these; the first depth guard counted every bracket character."""
        records = parse_dataset(json.dumps([{"name": f"n{i}", "mood": ":("} for i in range(51)]))
        note = parse_dataset(json.dumps([{"note": "(" * 51}]))
        commented = parse_dataset("{ # " + "(" * 60 + "\n 'a': 1}")
        escaped = parse_dataset('[{"a": "\\"[", "b": "it\'s ["}]')

        assert records.profile.rows == 51
        assert column(records, "mood").top == [":("]
        assert note.csv == "note\n" + "(" * 51 + "\n"
        assert commented.csv == "category,value\na,1\n"
        assert escaped.csv == 'a,b\n"""[",it\'s [\n'


OWNER_DICT_LITERAL = """cat_day = {
    "Schlafen & Dösen": 65,
    "Fellpflege": 12,
    "Fressen & Betteln": 8,
    "Wand anstarren": 5,
    "Zoomies um 3 Uhr": 5,
    "Türen anjammern": 5,
}
"""


OPEN_METEO = """latitude,longitude,elevation,utc_offset_seconds,timezone,timezone_abbreviation
48.189804,16.377296,194.0,7200,Europe/Vienna,GMT+2

time,temperature_2m_max (°C),precipitation_sum (mm)
2025-01-01,-0.2,0.00
2025-01-02,6.0,0.60
2025-01-03,3.5,0.00
2025-01-04,2.9,1.20
"""
"""The shape of an Open-Meteo CSV download (owner's weather test of 2026-10-14): metadata above the header."""


class TestTableAmongOtherLines:
    """Pasted data with a title, metadata, notes or a total around the table (owner rule of 2026-10-14)."""

    def test_an_export_with_metadata_above_the_header(self) -> None:
        parsed = parse_dataset(OPEN_METEO)

        assert list(parsed.column_dtypes) == ["time", "temperature_2m_max (°C)", "precipitation_sum (mm)"]
        assert parsed.column_dtypes["time"] == "datetime"
        assert parsed.profile.rows == 4
        assert parsed.profile.warnings == ["left out 2 lines above the table (a title, notes or metadata)"]

    def test_a_comment_above_and_below_also_with_commas(self) -> None:
        text = (
            "Hier meine Wetterdaten, time ist das Datum, dann Temperatur und Regen:\n"
            + OPEN_METEO
            + "\nQuelle: Open-Meteo, ERA5, abgerufen am 14.10.2026\n"
        )

        parsed = parse_dataset(text)

        assert parsed.profile.rows == 4
        assert parsed.profile.warnings == [
            "left out 3 lines above the table (a title, notes or metadata)",
            "left out 1 line below the table (notes or a source line)",
        ]

    def test_a_sentence_below_the_table_that_its_commas_split_into_the_tables_width(self) -> None:
        text = "Tag,Temp,Regen\nMo,3.5,0\nDi,4.1,1.2\nMi,2.0,0\nWerte gemessen in Wien, Temperatur in °C, Regen in mm\n"

        parsed = parse_dataset(text)

        assert parsed.profile.rows == 3
        assert parsed.profile.warnings == ["left out 1 line below the table (notes or a source line)"]

    def test_a_title_without_delimiter_above_a_semicolon_table_with_decimal_commas(self) -> None:
        text = "Monatsmittel Wien 2025\nMonat;Temperatur;Niederschlag\nJan;1,2;30,5\nFeb;3,4;25,0\nMär;8,1;41,2\n"

        parsed = parse_dataset(text)

        assert parsed.profile.source_format == "semicolon"
        assert parsed.column_dtypes == {"Monat": "text", "Temperatur": "number", "Niederschlag": "number"}
        assert parsed.csv.splitlines()[1] == "Jan,1.2,30.5"

    @pytest.mark.parametrize("label", ["Summe", "TOTAL", "Gesamt:", "Mittelwert", "Average"])
    def test_a_summary_row_at_the_end_is_left_out(self, label: str) -> None:
        text = f"Monat;Regen\nJan;30,5\nFeb;25,0\nMär;41,2\n{label};96,7\n"

        parsed = parse_dataset(text)

        assert parsed.profile.rows == 3
        assert parsed.profile.warnings == [
            "left out 1 summary row at the end of the table (a total, sum, mean or similar)"
        ]

    def test_a_summary_row_in_a_date_column_and_a_source_line_below(self) -> None:
        text = "Datum,Menge\n2024-03-02,4\n2024-03-05,10\n2024-03-09,2\nTOTAL,16\nExport: Shop-System v2\n"

        parsed = parse_dataset(text)

        assert parsed.column_dtypes == {"Datum": "datetime", "Menge": "integer"}
        assert parsed.profile.rows == 3

    def test_a_last_row_with_missing_values_stays(self) -> None:
        parsed = parse_dataset("Datum,Temp,Regen\n2025-01-01,1.0,0\n2025-01-02,2.0,0\n2025-01-03,,\n")

        assert parsed.profile.rows == 3
        assert parsed.profile.warnings == []

    def test_a_plain_table_and_a_text_table_are_unchanged(self) -> None:
        plain = parse_dataset("x,y\n1,2\n3,4\n5,6\n")
        text_only = parse_dataset("Name,Stadt\nAnna,Wien\nBen,Graz\nCem,Linz\n")

        assert (plain.csv, plain.profile.warnings) == ("x,y\n1,2\n3,4\n5,6\n", [])
        assert text_only.profile.rows == 3 and text_only.profile.warnings == []

    @pytest.mark.parametrize(
        "text", ["a,b,c\n1,2,3\n4,5\n6,7\n8,9\n", "a,b,c\n4,5\n6,7\n1,2,3\n"], ids=["full-row-first", "full-row-last"]
    )
    def test_a_ragged_table_keeps_its_wider_header_and_full_rows(self, text: str) -> None:
        """Short rows are padded, as before: the most common width is no new header (#12166 review)."""
        parsed = parse_dataset(text)

        assert list(parsed.column_dtypes) == ["a", "b", "c"]
        assert parsed.profile.rows == text.count("\n") - 1
        assert parsed.profile.warnings[0].endswith("had fewer fields than the header; the missing cells are empty")

    def test_the_services_own_csv_keeps_every_row(self) -> None:
        """A `Total` category a sort moved to the end stays in a re-parse of a prepared table (#12166 review)."""
        sorted_csv = "Kategorie,Wert\nA,1\nB,2\nC,4\nTotal,3\n"

        assert parse_dataset(sorted_csv).profile.rows == 3  # a paste: the summary row is left out
        assert parse_dataset(sorted_csv, find_table=False).profile.rows == 4
        assert parse_dataset(OPEN_METEO, find_table=False).profile.warnings[0].startswith("5 rows had fewer fields")

    def test_sniffing_reads_past_the_metadata(self) -> None:
        assert sniff_delimiter("Wetterstation Hohe Warte\nDatum;Temp\n2025-01-01;1,5\n2025-01-02;2,5\n") == (
            ";",
            "semicolon",
        )


class TestContextLines:
    """The lines left out around the table are kept as the user's notes (owner rule of 2026-10-14)."""

    def test_lines_above_and_below_become_one_text_line_each(self) -> None:
        text = (
            "Hier meine Wetterdaten, time ist das Datum, dann Temperatur und Regen:\n"
            + OPEN_METEO
            + "\nQuelle: Open-Meteo, ERA5, abgerufen am 14.10.2026\n"
        )

        parsed = parse_dataset(text)

        assert parsed.context_lines == [
            "Hier meine Wetterdaten, time ist das Datum, dann Temperatur und Regen:",
            "latitude, longitude, elevation, utc_offset_seconds, timezone, timezone_abbreviation",
            "48.189804, 16.377296, 194.0, 7200, Europe/Vienna, GMT+2",
            "Quelle: Open-Meteo, ERA5, abgerufen am 14.10.2026",
        ]
        assert parsed.profile.rows == 4  # the table and data.csv are unchanged
        assert "Quelle" not in parsed.csv and "latitude" not in parsed.csv

    def test_the_delimiter_joins_the_fields_and_empty_fields_and_invisible_characters_go(self) -> None:
        text = "Werte in °F;;\nTag;Temp;Regen\nMo;3,5;0\nDi;4,1;1,2\nMi;2,0;0\n​Quelle: eigene;Messung\n"

        parsed = parse_dataset(text)

        assert parsed.context_lines == ["Werte in °F", "Quelle: eigene; Messung"]

    def test_a_quoted_field_with_a_line_break_stays_one_line(self) -> None:
        parsed = parse_dataset('x,y\n1,2\n3,4\n5,6\n"Note: first line\nsecond line",\n')

        assert parsed.context_lines == ["Note: first line second line"]

    def test_summary_rows_are_data_not_notes(self) -> None:
        parsed = parse_dataset(
            "Datum,Menge\n2024-03-02,4\n2024-03-05,10\n2024-03-09,2\nTOTAL,16\nExport: Shop-System v2\n"
        )

        assert parsed.context_lines == ["Export: Shop-System v2"]

    def test_no_notes_without_left_out_lines_for_a_literal_or_for_the_services_own_csv(self) -> None:
        assert parse_dataset("x,y\n1,2\n3,4\n5,6\n").context_lines == []
        assert parse_dataset('[{"a": 1, "b": 2}, {"a": 3, "b": 4}]').context_lines == []
        assert parse_dataset(OPEN_METEO).context_lines != []
        assert parse_dataset(OPEN_METEO, find_table=False).context_lines == []  # every record kept, none a note

    def test_the_notes_are_cut_at_the_chat_message_cap_with_a_warning(self) -> None:
        notes = "\n".join(f"Note {index:03d}: " + "n" * 90 for index in range(30))  # 30 lines of 100 characters

        parsed = parse_dataset(f"{notes}\nx,y\n1,2\n3,4\n5,6\n")

        lines = parsed.context_lines
        assert MAX_CONTEXT_CHARS == MAX_MESSAGE_CHARS == 2_000
        assert len("\n".join(lines)) <= MAX_CONTEXT_CHARS
        assert lines[0].startswith("Note 000") and lines[-1].endswith("…") and len(lines) == 20
        assert "the notes around the table were cut at 2,000 characters" in parsed.warnings
        assert parsed.profile.rows == 3

    def test_without_context_drops_the_notes_and_puts_its_warning_first(self) -> None:
        parsed = parse_dataset(f"Title\n{OPEN_METEO}")

        dropped = without_context(parsed, "the notes were left out")

        assert dropped.context_lines == [] and dropped.csv == parsed.csv
        assert dropped.warnings[0] == dropped.profile.warnings[0] == "the notes were left out"
        assert dropped.warnings[1:] == parsed.warnings

    def test_without_context_keeps_the_warning_cap_and_the_omitted_count(self) -> None:
        parsed = parse_dataset("x,y\n1,2\n3,4\n5,6\n")
        full = [f"w{index}" for index in range(MAX_WARNINGS - 1)] + ["7 more warnings omitted"]
        capped = replace(parsed, warnings=full, profile=parsed.profile.model_copy(update={"warnings": full}))

        dropped = without_context(capped, "first")

        assert len(dropped.warnings) == MAX_WARNINGS
        assert dropped.warnings[0] == "first" and dropped.warnings[-1] == "8 more warnings omitted"


class TestPythonLiterals:
    def test_the_owners_dict_literal_with_its_assignment_and_trailing_comma(self) -> None:
        parsed = parse_dataset(OWNER_DICT_LITERAL)

        assert parsed.profile.source_format == "json_pairs"
        assert parsed.column_dtypes == {"category": "text", "value": "integer"}
        assert parsed.csv.splitlines()[1:] == [
            "Schlafen & Dösen,65",
            "Fellpflege,12",
            "Fressen & Betteln,8",
            "Wand anstarren,5",
            "Zoomies um 3 Uhr,5",
            "Türen anjammern,5",
        ]

    def test_single_quotes_tuples_and_python_constants(self) -> None:
        parsed = parse_dataset("x = {'day': ('a', 'b', 'c',), 'ok': (True, False, None), 'n': [1, 2.5, None]}")

        assert parsed.profile.source_format == "json_columns"
        assert parsed.column_dtypes == {"day": "text", "ok": "boolean", "n": "number"}
        assert parsed.csv == "day,ok,n\na,True,1.0\nb,False,2.5\nc,,\n"

    def test_records_and_pairs_as_literals(self) -> None:
        records = parse_dataset("rows = [{'x': 1, 'label': 'a'}, {'x': 2, 'label': 'b'},]")
        pairs = parse_dataset("data = (('a', 1), ('b', 2))")

        assert records.profile.source_format == "json_records"
        assert records.csv == "x,label\n1,a\n2,b\n"
        assert pairs.profile.source_format == "json_pairs"
        assert pairs.csv == "category,value\na,1\nb,2\n"

    def test_numeric_keys_become_names(self) -> None:
        parsed = parse_dataset("{2023: [1, 2], 2024: [3, 4]}")

        assert [c.name for c in parsed.profile.columns] == ["2023", "2024"]

    def test_a_nested_dict_is_unparseable(self) -> None:
        assert error_code("{'a': {'b': 1}}") == "unparseable"
        assert error_code("x = {'a': {'b': 1}, 'c': {'d': 2}}") == "unparseable"

    @pytest.mark.parametrize(
        "text",
        [
            "[1, len('x')]",
            "x = [__import__('os').system('id')]",
            "{'a': open('/etc/passwd')}",
            "{'a': nan}",
            "[1, 2] + [3]",
            "x = {'a': 1}\ny = {'b': 2}",
            "cat_day = {'a': 1",
            "[" + "1" * 5000 + "]",
        ],
    )
    def test_names_calls_and_broken_literals_are_unparseable(self, text: str) -> None:
        assert error_code(text) == "unparseable"

    @pytest.mark.parametrize("depth", [60, 100_000])
    def test_a_deeply_nested_literal_is_refused_before_evaluation(self, depth: int) -> None:
        started = time.perf_counter()

        assert error_code("[" * depth + "]" * depth) == "unparseable"
        assert time.perf_counter() - started < 1.0

    @pytest.mark.parametrize("depth", [2_000, 20_000])
    def test_closing_brackets_inside_a_string_cannot_hide_the_nesting(self, depth: int) -> None:
        """A string of `]` drove the first guard's count negative; the readers then recursed to a RecursionError."""
        started = time.perf_counter()
        evasion = '["' + "]" * depth + '", ' + "[" * depth + "]" * depth + "]"

        with pytest.raises(ParseError) as caught:
            parse_dataset(evasion)
        assert caught.value.code == "unparseable"
        assert "50 levels" in caught.value.message
        assert time.perf_counter() - started < 1.0

    def test_an_assignment_without_a_literal_is_delimited_text(self) -> None:
        # `x = 5` is a header line without rows, so the route hands it to the transcriber.
        assert error_code("x = 5") == "no_table"
        assert parse_dataset("x = 5,y\n1,2\n").csv == "x = 5,y\n1,2\n"

    def test_a_bare_parenthesis_that_is_no_literal_is_delimited_text(self) -> None:
        """A header such as `(in %) Land` and prose in parentheses keep the path they had before literals."""
        header = parse_dataset("(in %) Land;Wert\nA;1\nB;2\n")
        table = parse_dataset("(a),b\n1,2\n")
        stand = parse_dataset("(Stand: 2024)\nLand;Wert\nA;1\nB;2\n")

        assert header.column_dtypes == {"(in %) Land": "text", "Wert": "integer"}
        assert table.csv == "(a),b\n1,2\n"
        # A title line above the table is left out since 2026-10-14 (`table_block`).
        assert stand.csv == "Land,Wert\nA,1\nB,2\n"
        assert stand.profile.warnings == ["left out 1 line above the table (a title, notes or metadata)"]
        assert error_code("(siehe Anhang) Die Werte sind 3, 4 und 5") == "no_table"
        assert parse_dataset("(x) Katze 3\n(y) Hund 7\n").csv == "(x) Katze 3\n(y) Hund 7\n"

    def test_a_parenthesis_behind_an_assignment_or_a_bracket_stays_a_literal(self) -> None:
        # The assignment and `[` / `{` say "literal"; only a bare `(` is ambiguous enough to fall back.
        assert error_code("x = (foo)") == "unparseable"
        assert error_code("(1, 2)") == "unparseable"
        assert error_code("[a],b\n1,2\n") == "unparseable"


class TestUnits:
    def test_a_percent_column_moves_the_unit_into_the_name(self) -> None:
        parsed = parse_dataset("Kategorie,Anteil\nSchlafen,65 %\nFellpflege,12%\n")

        assert parsed.column_dtypes == {"Kategorie": "text", "Anteil (%)": "integer"}
        assert parsed.csv == "Kategorie,Anteil (%)\nSchlafen,65\nFellpflege,12\n"
        assert column(parsed, "Anteil (%)").max == 65.0
        assert parsed.warnings == ["column 'Anteil': unit '%' moved from the values into the name 'Anteil (%)'"]

    def test_decimal_comma_hours(self) -> None:
        parsed = parse_dataset("Tag;Dauer\nMo;15,6 h\nDi;8 h\n")

        assert parsed.column_dtypes == {"Tag": "text", "Dauer (h)": "number"}
        assert parsed.csv.splitlines()[1:] == ["Mo,15.6", "Di,8.0"]
        assert parsed.profile.decimal == ","

    def test_a_leading_euro_with_the_sign_before_it(self) -> None:
        parsed = parse_dataset("Posten;Preis\nA;€ 5\nB;-€ 12,50\nC;€-1,5\n")

        assert parsed.column_dtypes == {"Posten": "text", "Preis (€)": "number"}
        assert parsed.csv.splitlines()[1:] == ["A,5.0", "B,-12.5", "C,-1.5"]

    def test_a_currency_code_before_or_after_the_number(self) -> None:
        parsed = parse_dataset("a,b\nx,CHF 1200\ny,800 CHF\n")

        assert parsed.column_dtypes == {"a": "text", "b (CHF)": "integer"}
        assert parsed.csv.splitlines()[1:] == ["x,1200", "y,800"]

    def test_a_column_with_units_in_only_some_cells_stays_text(self) -> None:
        parsed = parse_dataset("v\n65 %\n12\n")

        assert parsed.column_dtypes == {"v": "text"}
        assert parsed.csv == "v\n65 %\n12\n"
        assert not parsed.warnings

    def test_a_column_with_two_units_stays_text(self) -> None:
        assert parse_dataset("v\n5 kg\n3 g\n").column_dtypes == {"v": "text"}
        assert parse_dataset("v\n5 kg\n3 Kg\n").column_dtypes == {"v": "text"}

    def test_a_negative_percent(self) -> None:
        parsed = parse_dataset("v\n-3 %\n+2 %\n-0,5 %\n")

        assert parsed.column_dtypes == {"v (%)": "number"}
        assert parsed.csv.splitlines()[1:] == ["-3.0", "2.0", "-0.5"]

    @pytest.mark.parametrize(
        ("cells", "name", "dtype", "canonical"),
        [
            (["20 °C", "-5°C"], "v (°C)", "integer", ["20", "-5"]),
            (["12°", "15 °"], "v (°)", "integer", ["12", "15"]),
            (["5µs", "7 μs"], "v", "text", ["5µs", "7 μs"]),
            (["5µs", "7 µs"], "v (µs)", "integer", ["5", "7"]),
            (["3 Std", "4,5 Std"], "v (Std)", "number", ["3.0", "4.5"]),
            (["1.234,56 €", "7,5 €"], "v (€)", "number", ["1234.56", "7.5"]),
            (["$ 3", "-$ 2.5", "$-1"], "v ($)", "number", ["3.0", "-2.5", "-1.0"]),
            (["12‰"], "v (‰)", "integer", ["12"]),
            (["2E-2 h", "1e3h"], "v (h)", "number", ["0.02", "1000.0"]),
            (["5 km/h"], "v", "text", ["5 km/h"]),
            (["5 metre"], "v", "text", ["5 metre"]),
            (["-$-1"], "v", "text", ["-$-1"]),
            (["1e999 kg"], "v", "text", ["1e999 kg"]),
            (["h 5"], "v", "text", ["h 5"]),
            (["€"], "v", "text", ["€"]),
        ],
    )
    def test_unit_shapes(self, cells: list[str], name: str, dtype: str, canonical: list[str]) -> None:
        parsed = parse_dataset("v\n" + "\n".join(cells) + "\n")

        assert parsed.column_dtypes == {name: dtype}
        assert parsed.csv.splitlines()[1:] == canonical

    def test_leading_zeros_behind_a_unit_keep_the_text(self) -> None:
        parsed = parse_dataset("v\n007 kg\n12 kg\n")

        assert parsed.column_dtypes == {"v": "text"}
        assert parsed.warnings == ["column 'v': numbers with leading zeros kept as text"]

    def test_dates_are_tried_before_units(self) -> None:
        # `1.2.2024` could be a thousands-dot number behind no unit; a unit never changes that order.
        parsed = parse_dataset("d;v\n01.02.2024;1 h\n")

        assert parsed.column_dtypes == {"d": "datetime", "v (h)": "integer"}

    def test_unit_names_take_the_canonical_path(self) -> None:
        long = "l" * MAX_COLUMN_NAME_CHARS
        parsed = parse_dataset(f"a,a,,{long}\n1 %,2 %,3 %,4 kg\n")

        names = [c.name for c in parsed.profile.columns]
        # The duplicate suffix sits before the unit, so the unit stays at the end of every name.
        assert names == ["a (%)", "a_2 (%)", "column_3 (%)", "l" * (MAX_COLUMN_NAME_CHARS - 5) + " (kg)"]
        assert all(len(name) <= MAX_COLUMN_NAME_CHARS for name in names)
        assert warned(parsed, "column 2: duplicate header 'a (%)' renamed to 'a_2 (%)'")
        assert warned(parsed, "column 3: empty header named 'column_3'")
        assert warned(parsed, "column 'column_3': unit '%' moved from the values into the name 'column_3 (%)'")
        assert warned(parsed, f"shortened to '{names[3]}'")

    def test_thousands_dots_behind_a_unit_in_a_decimal_comma_file(self) -> None:
        parsed = parse_dataset("Preis;Menge\n3,50 €;1.200 kg\n2,10 €;800 kg\n")

        assert parsed.column_dtypes == {"Preis (€)": "number", "Menge (kg)": "integer"}
        assert parsed.csv.splitlines()[1:] == ["3.5,1200", "2.1,800"]
        assert warned(parsed, "column 'Menge (kg)': dots read as thousands separators")

    def test_the_canonical_csv_of_a_unit_column_parses_to_itself(self) -> None:
        parsed = parse_dataset("Anteil;Dauer\n65 %;15,6 h\n12 %;2,9 h\n")
        again = parse_dataset(parsed.csv)

        assert again.csv == parsed.csv
        assert again.column_dtypes == parsed.column_dtypes
        assert not again.warnings

    @pytest.mark.parametrize("space", ["\N{NO-BREAK SPACE}", "\N{NARROW NO-BREAK SPACE}", "\N{THIN SPACE}"])
    def test_a_no_break_or_thin_space_between_number_and_unit(self, space: str) -> None:
        """What the CLDR formats for de and fr write, and what a copy from a spreadsheet or a web table carries."""
        percent = parse_dataset(f"v\n65{space}%\n12{space}%\n")
        euro = parse_dataset(f"v\n1.234,56{space}€\n7,50{space}€\n")
        leading = parse_dataset(f"v\n€{space}5\n€{space}7\n")

        assert percent.column_dtypes == {"v (%)": "integer"}
        assert percent.csv == "v (%)\n65\n12\n"
        assert euro.column_dtypes == {"v (€)": "number"}
        assert euro.csv.splitlines()[1:] == ["1234.56", "7.5"]
        assert leading.csv == "v (€)\n5\n7\n"

    def test_a_line_break_between_number_and_unit_is_no_unit(self) -> None:
        assert parse_dataset('v\n"65\n%"\n"12\n%"\n').column_dtypes == {"v": "text"}

    def test_a_header_that_already_names_the_unit_keeps_its_name(self) -> None:
        parenthesised = parse_dataset("Anteil (%)\n65 %\n12 %\n")
        worded = parse_dataset("Preis in €\n5 €\n7 €\n")
        other_unit = parse_dataset("Umsatz (Tsd. €)\n5 %\n7 %\n")

        assert parenthesised.column_dtypes == {"Anteil (%)": "integer"}
        assert parenthesised.csv == "Anteil (%)\n65\n12\n"
        assert parenthesised.warnings == [
            "column 'Anteil (%)': unit '%' removed from the values; the name already carries it"
        ]
        assert worded.column_dtypes == {"Preis in €": "integer"}
        assert other_unit.column_dtypes == {"Umsatz (Tsd. €) (%)": "integer"}

    @pytest.mark.parametrize(
        "cells",
        [
            ["5 Jan", "12 Jan"],
            ["5 true", "6 true"],
            ["1st", "21st"],
            ["5 NA", "6 NA"],
            ["5 pm", "11 pm"],
            ["3 Dez.", "4 dez"],
        ],
    )
    def test_letters_that_are_a_month_a_boolean_or_an_ordinal_are_no_unit(self, cells: list[str]) -> None:
        parsed = parse_dataset("v\n" + "\n".join(cells) + "\n")

        assert parsed.column_dtypes == {"v": "text"}
        assert not parsed.warnings

    @pytest.mark.parametrize(
        ("cells", "name", "canonical"),
        [
            (["5 Std.", "3 Std."], "v (Std.)", ["5", "3"]),
            (["5 Mio.", "3,5 Mio."], "v (Mio.)", ["5.0", "3.5"]),
            (["100 m²", "80 m²"], "v (m²)", ["100", "80"]),
            (["2 m³"], "v (m³)", ["2"]),
        ],
    )
    def test_dotted_abbreviations_and_superscripts_are_units(
        self, cells: list[str], name: str, canonical: list[str]
    ) -> None:
        parsed = parse_dataset("v\n" + "\n".join(cells) + "\n")

        assert list(parsed.column_dtypes) == [name]
        assert parsed.csv.splitlines()[1:] == canonical

    def test_a_unit_suffix_that_pushes_a_header_over_the_cap_names_the_cause(self) -> None:
        parsed = parse_dataset("x" * (MAX_COLUMN_NAME_CHARS - 2) + "\n5 %\n6 %\n")

        assert [c.name for c in parsed.profile.columns] == ["x" * (MAX_COLUMN_NAME_CHARS - 4) + " (%)"]
        assert warned(parsed, "column 1: header shortened to")
        assert warned(parsed, f"so the unit fits within {MAX_COLUMN_NAME_CHARS} characters")
        assert not warned(parsed, f"longer than {MAX_COLUMN_NAME_CHARS} characters")


class TestTyping:
    @pytest.mark.parametrize(
        ("cells", "dtype", "canonical"),
        [
            (["2024-01-05", "2024-12-31"], "datetime", ["2024-01-05", "2024-12-31"]),
            (["2024-01-05T10:00", "2024-01-05 11:30:15"], "datetime", ["2024-01-05T10:00:00", "2024-01-05T11:30:15"]),
            (["2024-01-05", "2024-01-06T12:00"], "datetime", ["2024-01-05T00:00:00", "2024-01-06T12:00:00"]),
            (["5.1.2024", "31.12.2024"], "datetime", ["2024-01-05", "2024-12-31"]),
            (["31.12.2024 23:59"], "datetime", ["2024-12-31T23:59:00"]),
            (["25/12/2024", "01/02/2024"], "datetime", ["2024-12-25", "2024-02-01"]),
            (["12/25/2024", "01/02/2024"], "datetime", ["2024-12-25", "2024-01-02"]),
            (["31.02.2024"], "text", ["31.02.2024"]),
            (["25/12/2024", "12/25/2024"], "text", ["25/12/2024", "12/25/2024"]),
            (["2024-01-05", "05.01.2024"], "text", ["2024-01-05", "05.01.2024"]),
            (["true", "FALSE", "True"], "boolean", ["True", "False", "True"]),
            (["1", "-2", "+3"], "integer", ["1", "-2", "3"]),
            (["9223372036854775807"], "integer", ["9223372036854775807"]),
            (["9223372036854775808"], "number", ["9.223372036854776e+18"]),
            (["007", "12"], "text", ["007", "12"]),
            (["0", "-0"], "integer", ["0", "0"]),
            (["1.5", ".5", "1e3", "2E-2", "3."], "number", ["1.5", "0.5", "1000.0", "0.02", "3.0"]),
            (["1e999"], "text", ["1e999"]),
            ([ARABIC_12], "text", [ARABIC_12]),
            (["1_000"], "text", ["1_000"]),
            (["yes", "no"], "text", ["yes", "no"]),
        ],
    )
    def test_column_types(self, cells: list[str], dtype: str, canonical: list[str]) -> None:
        parsed = parse_dataset("v\n" + "\n".join(cells) + "\n")

        assert parsed.column_dtypes == {"v": dtype}
        assert parsed.csv.splitlines()[1:] == canonical

    def test_ambiguous_day_month_order_is_read_day_first_with_a_warning(self) -> None:
        parsed = parse_dataset("d\n03/04/2024\n05/06/2024\n")

        assert parsed.csv.splitlines()[1:] == ["2024-04-03", "2024-06-05"]
        assert warned(parsed, "column 'd': day and month order is ambiguous; read as DD/MM/YYYY")

    def test_same_day_and_month_is_not_ambiguous(self) -> None:
        parsed = parse_dataset("d\n01/01/2024\n05/05/2024\n")

        assert not warned(parsed, "ambiguous")

    def test_leading_zeros_warn(self) -> None:
        assert warned(parse_dataset("zip\n01234\n"), "column 'zip': numbers with leading zeros kept as text")

    @pytest.mark.parametrize("token", ["", "NA", "N/A", "NaN", "nan", "null", "NULL", "None", "-", "#N/A", "<NA>"])
    def test_missing_values(self, token: str) -> None:
        parsed = parse_dataset(f"a,b\n1,x\n{token},y\n")

        assert column(parsed, "a").missing == 1
        assert column(parsed, "a").dtype == "integer"

    def test_missing_values_cover_every_pandas_default(self) -> None:
        parsers = pytest.importorskip("pandas._libs.parsers")

        assert set(parsers.STR_NA_VALUES) <= MISSING_VALUES

    def test_whitespace_around_cells_is_stripped(self) -> None:
        parsed = parse_dataset("a, b\n 1 ,  x \n")

        assert parsed.csv == "a,b\n1,x\n"

    def test_an_all_missing_column_is_text(self) -> None:
        parsed = parse_dataset("a,b\n1,\n2,NA\n")

        assert column(parsed, "b").dtype == "text"
        assert column(parsed, "b").missing == 2


class TestProfile:
    def test_profile_fields(self) -> None:
        text = "when,n,x,label,flag\n" + "".join(
            f"2024-01-{day:02d},{day},{day / 2},{'abc'[day % 3]},{'true' if day % 2 else 'false'}\n"
            for day in range(1, 11)
        )
        parsed = parse_dataset(text + "2024-01-11,,,,\n")
        profile = parsed.profile

        assert profile.rows == 11
        assert column(parsed, "when").min == "2024-01-01"
        assert column(parsed, "when").max == "2024-01-11"
        assert column(parsed, "n").min == 1.0
        assert column(parsed, "n").max == 10.0
        assert isinstance(column(parsed, "n").max, float)
        assert column(parsed, "n").missing == 1
        assert column(parsed, "x").max == 5.0
        assert column(parsed, "label").unique == 3
        assert column(parsed, "label").top == ["b", "c", "a"]
        assert column(parsed, "label").min is None
        assert column(parsed, "flag").top == ["True", "False"]
        assert len(profile.sample) == MAX_SAMPLE_ROWS
        assert profile.sample[0] == ["2024-01-01", "1", "0.5", "b", "True"]

    def test_numeric_columns_carry_mean_and_median(self) -> None:
        """The root's step-1 summary names what a column holds; a text or date column has no statistics."""
        parsed = parse_dataset("when,n,share,label\n2024-01-01,1,0.1,a\n2024-01-02,2,0.2,b\n2024-01-03,6,0.3,c\n")

        assert (column(parsed, "n").mean, column(parsed, "n").median) == (3.0, 2.0)
        assert (column(parsed, "share").mean, column(parsed, "share").median) == (0.2, 0.2)  # six digits, no noise
        assert column(parsed, "when").mean is None and column(parsed, "label").median is None

    def test_statistics_that_no_float_holds_are_left_out_not_an_error(self) -> None:
        """`fsum` of two `1e308` overflows; the parse must not fail on finite values."""
        parsed = parse_dataset("v\n1e308\n1e308\n")

        assert column(parsed, "v").dtype == "number"
        assert column(parsed, "v").mean is None and column(parsed, "v").median == 1e308
        assert column(parse_dataset("v\n1e308\n-1e308\n"), "v").median == 0.0
        assert parse_dataset("v\n1\n").profile.columns[0].mean == 1.0
        assert "mean" not in parsed.profile.sample[0]  # statistics are column facts, never sample cells

    def test_top_values_are_capped_and_clipped(self) -> None:
        values = [f"value-{i}-" + "z" * 60 for i in range(8)]
        parsed = parse_dataset("t\n" + "\n".join(values) + "\n")
        top = column(parsed, "t").top

        assert len(top) == MAX_TOP_VALUES
        assert all(len(value) <= MAX_CELL_CHARS for value in top)
        assert top[0].endswith("…")

    def test_preview_is_the_first_20_rows_with_clipped_cells(self) -> None:
        parsed = parse_dataset("t\n" + "\n".join(f"row {i} " + "y" * 50 for i in range(30)) + "\n")

        assert len(parsed.preview) == PREVIEW_ROWS
        assert parsed.preview[0][0].startswith("row 0 ")
        assert len(parsed.preview[0][0]) == MAX_CELL_CHARS
        assert len(parsed.profile.sample[0][0]) == MAX_CELL_CHARS

    def test_display_copies_are_single_line(self) -> None:
        parsed = parse_dataset('t\n"line one\nline two"\n')

        assert parsed.preview == [["line one line two"]]
        assert parsed.profile.sample == [["line one line two"]]
        assert parsed.csv == 't\n"line one\nline two"\n'

    def test_warnings_are_capped_with_a_note(self) -> None:
        header = "first" + "," * (MAX_COLUMNS - 1)  # 49 empty names, each a rename warning
        row = ",".join(f"{ZWSP}007" for _ in range(MAX_COLUMNS))  # invisible and leading-zero warnings
        parsed = parse_dataset(f"{header}\n{row}\n")
        total = (MAX_COLUMNS - 1) + 2 * MAX_COLUMNS

        assert len(parsed.warnings) == MAX_WARNINGS
        assert parsed.warnings[-1] == f"{total - (MAX_WARNINGS - 1)} more warnings omitted"
        assert parsed.profile.warnings == parsed.warnings


class TestRoundTrip:
    @pytest.mark.parametrize(
        "text",
        [
            "Datum;Umsatz;Menge;Kunde;Aktiv\n01.02.2024;1.234,56;1.200;Müller, A.;true\n"
            "15.03.2024;-7,5;800;;FALSE\n16.03.2024;;12;None;\n",
            '[{"t": "2024-01-01T10:00", "v": 1.5, "n": 3, "s": "a,b"}, {"t": null, "v": null, "n": null, "s": null}]',
            'x\ty\tlabel\n1\t0.5\t#N/A\n2\t1e-3\t"quoted ""text"""\n',
            "d|id\n12/31/2024|0007\n01/15/2025|42\n",
            "Anteil;Dauer;Preis\n65 %;15,6 h;€ 5\n12 %;;-€ 12,50\n",
            "cat_day = {'Schlafen & Dösen': 65, 'Fellpflege': 12, 'Rest': None}",
        ],
    )
    def test_the_exported_csv_reproduces_the_typed_frame(self, text: str) -> None:
        parsed = parse_dataset(text)
        frame = read_back(parsed)

        assert list(frame.columns) == [c.name for c in parsed.profile.columns]
        assert len(frame) == parsed.profile.rows
        for profile in parsed.profile.columns:
            series = frame[profile.name]
            assert int(series.isna().sum()) == profile.missing
            if profile.dtype == "datetime":
                assert pd.api.types.is_datetime64_any_dtype(series)
                assert series.min().isoformat().startswith(str(profile.min))
            elif profile.dtype == "integer":
                assert str(series.dtype) == "Int64"
                assert float(series.min()) == profile.min
            elif profile.dtype == "number":
                assert series.dtype == "float64"
                assert float(series.max()) == pytest.approx(profile.max)
            elif profile.dtype == "boolean":
                assert str(series.dtype) == "boolean"
            else:
                assert pd.api.types.is_string_dtype(series)

    def test_typed_values_survive_exactly(self) -> None:
        parsed = parse_dataset(
            "Datum;Umsatz;Menge;Kunde;Aktiv\n01.02.2024;1.234,56;1.200;None;true\n15.03.2024;;800;B;\n"
        )
        frame = read_back(parsed)
        expected = pd.DataFrame(
            {
                "Datum": pd.to_datetime(["2024-02-01", "2024-03-15"]).as_unit("us"),
                "Umsatz": pd.Series([1234.56, float("nan")], dtype="float64"),
                "Menge": pd.Series([1200, 800], dtype="Int64"),
                "Kunde": pd.Series([None, "B"], dtype="str"),
                "Aktiv": pd.Series([True, None], dtype="boolean"),
            }
        )

        pd.testing.assert_frame_equal(frame, expected)

    def test_parsing_the_canonical_csv_again_changes_nothing(self) -> None:
        parsed = parse_dataset("Datum;Wert;Text\n01.02.2024;1.234,56;a\n03.02.2024;2,5;b\n")
        again = parse_dataset(parsed.csv)

        assert again.csv == parsed.csv
        assert again.column_dtypes == parsed.column_dtypes
        assert again.profile.decimal == "."

    def test_a_column_named_in_text_columns_stays_text(self) -> None:
        """`set_type text` of the data operations survives the re-parse through this hint; unknown names are ignored."""
        parsed = parse_dataset(
            "year,when,v\n2023,2024-01-05,1\n2024,2024-01-06,2\n", text_columns=["year", "when", "x"]
        )

        assert parsed.column_dtypes == {"year": "text", "when": "text", "v": "integer"}
        assert parsed.text_columns == ["year", "when"] and parsed.parse_dates == []
        assert parsed.csv == "year,when,v\n2023,2024-01-05,1\n2024,2024-01-06,2\n"
        assert column(parsed, "year").min is None and column(parsed, "year").top == ["2023", "2024"]
        assert pd.api.types.is_string_dtype(read_back(parsed)["year"])
        assert parse_dataset(parsed.csv).column_dtypes["year"] == "integer"  # without the hint: by content again


class TestReviewRegressions:
    """Copilot's findings on #12132: the depth guard, pair keys that look missing, a long header with its unit."""

    def test_a_triple_quoted_string_with_a_quote_cannot_hide_the_nesting(self) -> None:
        # The first guard read a triple quote as three strings and lost its alignment at the inner quote.
        evasion = '["""a"b""", ' + "[" * 60 + "]" * 60 + "]"
        with pytest.raises(ParseError) as caught:
            parse_dataset(evasion)
        assert caught.value.code == "unparseable" and "50 levels" in caught.value.message

        # The same shape within the limit still reads: the string is one token, the lists nest 10 deep.
        fine = '[["""a"b""", 1], ' + "[" * 10 + "2" + "]" * 10 + "]"
        with pytest.raises(ParseError) as refused:  # a nested value is no table, but it is not "too deep"
            parse_dataset(fine)
        assert "50 levels" not in refused.value.message

    def test_pair_keys_that_look_like_missing_values_stay_text(self) -> None:
        parsed = parse_dataset('{"NA": 1, "null": 2, "-": 3}')
        assert [column.name for column in parsed.profile.columns] == ["category", "value"]
        assert parsed.preview == [["NA", "1"], ["null", "2"], ["-", "3"]]
        assert parsed.profile.columns[0].missing == 0

        pairs = parse_dataset('[["null", 1], ["x", 2]]')
        assert pairs.preview[0] == ["null", "1"]

    def test_a_long_header_that_names_the_unit_keeps_it_after_the_cut(self) -> None:
        header = "x" * 64 + " (%)"
        parsed = parse_dataset(f"{header}\n65 %\n12 %\n")
        (column,) = parsed.profile.columns
        assert column.name.endswith(" (%)") and len(column.name) <= 64
        assert column.dtype == "integer" and parsed.preview == [["65"], ["12"]]
        assert any("already carries it" in warning for warning in parsed.warnings)

    def test_a_duplicate_suffix_never_cuts_into_the_unit(self) -> None:
        header = "x" * 64
        parsed = parse_dataset(f"{header},{header}\n65 %,12 %\n")
        names = [column.name for column in parsed.profile.columns]
        assert all(name.endswith(" (%)") and len(name) <= 64 for name in names)
        assert names[1].endswith("_2 (%)") and names[0] != names[1]
        assert [column.dtype for column in parsed.profile.columns] == ["integer", "integer"]

        same = canonical_headers(["Anteil", "Anteil"], ["%", "%"])[0]
        assert same == ["Anteil (%)", "Anteil_2 (%)"]


def bfs_births() -> dict[str, Any]:
    """The BFS PxWeb answer of 2026-10-14 (births and deaths by canton, json-stat2), trimmed to three cantons."""
    total = {"extension": {"show": "value"}}
    return {
        "class": "dataset",
        "label": "Demografische Bilanz nach Kanton nach Jahr, Kanton, Staatsangehörigkeit (Kategorie), Geschlecht "
        "und Demografische Komponente",
        "source": "BFS - ESPOP, STATPOP - © BFS",
        "updated": "2010-12-20T09:58:00Z",
        "id": ["Jahr", "Kanton", "Staatsangehörigkeit (Kategorie)", "Geschlecht", "Demografische Komponente"],
        "size": [1, 3, 1, 1, 2],
        "dimension": {
            "Jahr": {**total, "label": "Jahr", "category": {"index": {"2024": 0}, "label": {"2024": "2024"}}},
            "Kanton": {
                **total,
                "label": "Kanton",
                "category": {
                    "index": {"1": 0, "2": 1, "18": 2},
                    "label": {"1": "Zürich", "2": "Bern / Berne", "18": "Graubünden / Grigioni / Grischun"},
                },
            },
            "Staatsangehörigkeit (Kategorie)": {
                **total,
                "label": "Staatsangehörigkeit (Kategorie)",
                "category": {"index": {"0": 0}, "label": {"0": "Staatsangehörigkeit (Kategorie) - Total"}},
            },
            "Geschlecht": {
                **total,
                "label": "Geschlecht",
                "category": {"index": {"0": 0}, "label": {"0": "Geschlecht - Total"}},
            },
            "Demografische Komponente": {
                **total,
                "label": "Demografische Komponente",
                "category": {"index": {"1": 0, "2": 1}, "label": {"1": "Lebendgeburt", "2": "Todesfall"}},
            },
        },
        "value": [14949, 11813, 8727, 9872, 1772, 2082],
        "role": {"time": ["Jahr"]},
        "version": "2.0",
        "extension": {"px": {"decimals": 0}},
    }


def json_stat(ids: list[str], sizes: list[int], dimensions: dict[str, Any], value: Any, **extra: Any) -> str:
    return json.dumps({"class": "dataset", "id": ids, "size": sizes, "dimension": dimensions, "value": value, **extra})


def categories(*codes: str, labels: dict[str, str] | None = None) -> dict[str, Any]:
    category: dict[str, Any] = {"index": {code: at for at, code in enumerate(codes)}}
    if labels is not None:
        category["label"] = labels
    return {"category": category}


class TestJsonStat:
    def test_the_bfs_answer_is_a_long_table_with_its_constants_as_notes(self) -> None:
        parsed = parse_dataset(json.dumps(bfs_births(), ensure_ascii=False))

        assert parsed.profile.source_format == "json_stat"
        assert parsed.column_dtypes == {"Kanton": "text", "Demografische Komponente": "text", "value": "integer"}
        assert parsed.csv.splitlines() == [
            "Kanton,Demografische Komponente,value",
            "Zürich,Lebendgeburt,14949",
            "Zürich,Todesfall,11813",
            "Bern / Berne,Lebendgeburt,8727",
            "Bern / Berne,Todesfall,9872",
            "Graubünden / Grigioni / Grischun,Lebendgeburt,1772",
            "Graubünden / Grigioni / Grischun,Todesfall,2082",
        ]
        assert parsed.context_lines == [
            "Demografische Bilanz nach Kanton nach Jahr, Kanton, Staatsangehörigkeit (Kategorie), Geschlecht und "
            "Demografische Komponente",
            "Source: BFS - ESPOP, STATPOP - © BFS",
            "Jahr: 2024",
            "Staatsangehörigkeit (Kategorie): Staatsangehörigkeit (Kategorie) - Total",
            "Geschlecht: Geschlecht - Total",
        ]
        assert warned(parsed, "3 dimensions with a single category left out of the columns")
        assert not any("2024" in warning or "Total" in warning for warning in parsed.warnings)  # values only as notes

    def test_a_header_with_special_characters_takes_the_canonical_path(self) -> None:
        data = bfs_births()
        data["size"] = [1, 3, 2, 1, 1]
        data["dimension"]["Staatsangehörigkeit (Kategorie)"]["category"] = {
            "index": ["1", "2"],
            "label": {"1": "Schweiz", "2": "Ausland"},
        }
        data["dimension"]["Demografische Komponente"]["category"] = {"index": {"1": 0}, "label": {"1": "Lebendgeburt"}}
        parsed = parse_dataset(json.dumps(data))

        assert parsed.csv.splitlines()[:3] == [
            "Kanton,Staatsangehörigkeit (Kategorie),value",
            "Zürich,Schweiz,14949",
            "Zürich,Ausland,11813",
        ]
        assert "Demografische Komponente: Lebendgeburt" in parsed.context_lines

    def test_a_sparse_value_object_leaves_the_missing_positions_empty(self) -> None:
        text = json_stat(
            ["Land", "Jahr"],
            [2, 2],
            {"Land": categories("AT", "CH"), "Jahr": categories("2023", "2024")},
            {"0": 1.5, "3": 4},
        )
        parsed = parse_dataset(text)

        assert parsed.csv == "Land,Jahr,value\nAT,2023,1.5\nAT,2024,\nCH,2023,\nCH,2024,4.0\n"
        assert column(parsed, "value").missing == 2

    def test_an_index_array_without_labels_keeps_the_codes(self) -> None:
        dimensions = {"geo": {"label": "Region", "category": {"index": ["AT", "DE"]}}, "unit": categories("PC")}
        parsed = parse_dataset(json_stat(["geo", "unit"], [2, 1], dimensions, [None, 2.5]))

        assert parsed.csv == "Region,value\nAT,\nDE,2.5\n"
        assert parsed.context_lines == ["unit: PC"]

    def test_a_dimension_without_a_label_is_named_by_its_id(self) -> None:
        parsed = parse_dataset(json_stat(["sex"], [2], {"sex": categories("F", "M", labels={"F": "Frauen"})}, [1, 2]))

        assert parsed.csv == "sex,value\nFrauen,1\nM,2\n"

    def test_a_one_category_dimension_may_omit_its_index(self) -> None:
        dimensions = {"t": {"category": {"label": {"2024": "2024"}}}, "g": categories("a", "b")}
        parsed = parse_dataset(json_stat(["t", "g"], [1, 2], dimensions, [1, 2]))

        assert parsed.csv == "g,value\na,1\nb,2\n" and parsed.context_lines == ["t: 2024"]

    def test_every_dimension_of_one_category_leaves_one_value_row(self) -> None:
        parsed = parse_dataset(json_stat(["t"], [1], {"t": categories("2024")}, [7]))

        assert parsed.csv == "value\n7\n" and parsed.context_lines == ["t: 2024"]

    def test_a_shared_label_gets_its_code_and_status_symbols_a_warning(self) -> None:
        dimensions = {"c": categories("1", "2", labels={"1": "Other", "2": "Other"})}
        parsed = parse_dataset(json_stat(["c"], [2], dimensions, [1, 2], status={"1": "p"}))

        assert parsed.csv == "c,value\nOther (1),1\nOther (2),2\n"
        assert warned(parsed, "labels shared by two categories carry their codes")
        assert warned(parsed, "status symbols")

    def test_a_label_shared_after_cleaning_gets_its_code(self) -> None:
        dimensions = {"c": categories("1", "2", labels={"1": "Other", "2": f"Other{ZWSP} "})}
        parsed = parse_dataset(json_stat(["c"], [2], dimensions, [1, 2]))

        assert parsed.csv == "c,value\nOther (1),1\nOther (2),2\n"

    def test_categories_stay_text_and_only_the_value_is_typed(self) -> None:
        dimensions = {"geo": categories("NA", "-", "CH"), "year": categories("2023", "2024")}
        parsed = parse_dataset(json_stat(["geo", "year"], [3, 2], dimensions, [1, 2, 3, 4, 5, None]))

        assert parsed.column_dtypes == {"geo": "text", "year": "text", "value": "integer"}
        assert parsed.csv.splitlines()[1:3] == ["NA,2023,1", "NA,2024,2"]
        assert column(parsed, "geo").missing == 0 and column(parsed, "value").missing == 1
        assert column(parsed, "geo").top == ["NA", "-", "CH"]

    @pytest.mark.parametrize("label", ["value", "Value", " VALUE "])
    def test_a_dimension_named_value_leaves_the_name_to_the_measure(self, label: str) -> None:
        dimensions = {"v": {"label": label, **categories("1", "2")}}
        parsed = parse_dataset(json_stat(["v"], [2], dimensions, [10, 20]))

        assert list(parsed.column_dtypes) == [f"{label.strip()} (dimension)", "value"]
        assert parsed.column_dtypes["value"] == "integer"
        assert warned(parsed, "a dimension named like the value column renamed")
        roles = [DataRole(name="value", kinds=("numeric",), required=True, variadic=False, description="")]
        assert [binding.column for binding in default_bindings(roles, parsed.profile)] == ["value"]

    def test_a_json_stat_1_bundle_of_one_dataset_is_read(self) -> None:
        bundle = {"births": {"dimension": {"id": ["g"], "size": [2], "g": categories("a", "b")}, "value": [3, 4]}}
        parsed = parse_dataset(json.dumps(bundle))

        assert parsed.profile.source_format == "json_stat" and parsed.csv == "g,value\na,3\nb,4\n"

    @pytest.mark.parametrize(
        ("document", "fragment"),
        [
            (json_stat(["g"], [3], {"g": categories("a", "b")}, [1, 2, 3]), "has 2 categories where `size` gives 3"),
            (json_stat(["g"], [2], {"g": categories("a", "b")}, [1, 2, 3]), "`value` holds 3 values"),
            (json_stat(["g", "h"], [2], {"g": categories("a", "b")}, [1, 2]), "one size per dimension"),
            (json_stat(["g"], [2], {}, [1, 2]), "has no `category` object"),
            (json_stat(["g"], [2], {"g": categories("a", "b")}, {"2": 1}), "no position within `size`"),
            (json_stat(["g"], [2], {"g": {"category": {"index": {"a": 0, "b": 2}}}}, [1, 2]), "number its categories"),
            (json_stat(["g"], [0], {"g": categories()}, []), "at least 1"),
            (json_stat(["g"], [2], {"g": categories("a", "b")}, [1, [2]]), "a value is nested"),
            (json.dumps({"a": {"dimension": {}, "value": []}, "b": {"dimension": {}, "value": []}}), "2 datasets"),
            (json.dumps({"class": "collection", "link": {"item": []}}), "collection"),
        ],
    )
    def test_an_inconsistent_document_is_unparseable_without_quoting_it(self, document: str, fragment: str) -> None:
        with pytest.raises(ParseError) as refused:
            parse_dataset(document)

        assert refused.value.code == "unparseable" and fragment in refused.value.message
        assert '"a"' not in refused.value.message

    def test_too_many_rows_are_refused_before_the_values_are_read(self) -> None:
        width = MAX_ROWS // 100
        dimensions = {"x": categories(*(str(n) for n in range(width))), "y": categories(*(str(n) for n in range(100)))}

        assert parse_dataset(json_stat(["x", "y"], [width, 100], dimensions, [1] * MAX_ROWS)).profile.rows == MAX_ROWS
        wider = {**dimensions, "x": categories(*(str(n) for n in range(width + 1)))}
        assert error_code(json_stat(["x", "y"], [width + 1, 100], wider, [1] * (MAX_ROWS + 100))) == "too_many_rows"
        assert error_code(json_stat(["x", "y"], [MAX_ROWS, 2], {}, [])) == "too_many_rows"  # before any dimension

    def test_other_objects_with_a_class_key_keep_their_shape(self) -> None:
        assert parse_dataset('{"class": "dataset", "rest": 3}').profile.source_format == "json_pairs"
        assert parse_dataset('{"id": [1, 2], "value": [3, 4]}').profile.source_format == "json_columns"

    def test_the_nesting_limit_is_unchanged_for_other_input(self) -> None:
        assert error_code('{"a": ' + "[" * 60 + "]" * 60 + "}") == "unparseable"
        nested = json.loads(json.dumps(bfs_births()))  # a normal JSON-stat document nests five levels
        assert parse_dataset(json.dumps(nested)).profile.rows == 6

    def test_the_loader_reads_the_table_back(self) -> None:
        frame = read_back(parse_dataset(json.dumps(bfs_births())))

        assert list(frame.columns) == ["Kanton", "Demografische Komponente", "value"]
        assert (
            str(frame["value"].dtype) == "Int64" and frame["value"].sum() == 14949 + 11813 + 8727 + 9872 + 1772 + 2082
        )
