"""Tests for agents/anyplot/data/parse.py: limits, sanitising, headers, formats, typing, profile, round trip."""

import io
import json
import random
import sys
import time
from dataclasses import replace
from decimal import Decimal
from typing import Any

import pandas as pd
import pytest
from pydantic import TypeAdapter

from agents.anyplot.data import parse as parse_module
from agents.anyplot.data.bindings import default_bindings
from agents.anyplot.data.parse import (
    HEADERLESS_LIST_WARNING,
    LIST_COLUMN_NAME,
    MAX_COMPUTED_BYTES,
    MAX_CONTEXT_CHARS,
    MAX_INPUT_BYTES,
    MAX_INPUT_CELL_CHARS,
    MISSING_VALUES,
    PREVIEW_ROWS,
    RESPELLED,
    ParsedDataset,
    ParseError,
    canonical_headers,
    pandas_dtypes,
    parse_dataset,
    sniff_delimiter,
    without_context,
)
from agents.anyplot.data.prepare import Operation, apply_operations
from agents.anyplot.opening import NOTES_INSTRUCTION_WARNING, NOTES_REFUSED_WARNING, NOTES_UNCHECKED_WARNING
from agents.anyplot.schemas import (
    MAX_CELL_CHARS,
    MAX_COLUMN_NAME_CHARS,
    MAX_COLUMNS,
    MAX_LISTED_VALUES,
    MAX_MESSAGE_CHARS,
    MAX_ROWS,
    MAX_SAMPLE_ROWS,
    MAX_TOP_VALUES,
    MAX_WARNINGS,
)
from core.spec_roles import DataRole


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
    """What the loader does with the exported data.csv: only the empty cell is missing (`code/loader.py`)."""
    return pd.read_csv(
        io.StringIO(parsed.csv),
        dtype=pandas_dtypes(parsed.column_dtypes),
        parse_dates=parsed.parse_dates,
        keep_default_na=False,
        na_values=[""],
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
            '[{"a": [1, 2], "b": [1]}]',
            '[{"a": {"b": {"c": {"d": {"e": 1}}}}}]',
            '{"a": [1, 2], "b": [1]}',
            '{"a": 1, "b": [2]}',
            '{"a": [[1]]}',
            '[["a", 65], ["b"]]',
            '[["a", 65], {"b": 12}]',
            "[" * 5000 + "]" * 5000,
        ],
    )
    def test_unparseable(self, text: str) -> None:
        # `{"a": 1}` was in this list until the parser read an object of values as pairs (2026-10-11), and
        # `[{"a": {"nested": 1}}]` until it flattened nested objects into dotted columns (2026-10-15).
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
            '[{"a": {"SECRET": [{"b": 1}]}}]',
            '{"fields": ["SECRET"], "rows": [["SECRET", "SECRET"]]}',
            '[{"page": "SECRET"}, [{"x": 1}], [{"x": 2}]]',
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
        assert parsed.csv == "x,label,flag\n1,a,\n2.5,,True\n,c,\n"
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
        assert parsed.profile.warnings == [
            "left out 2 lines above the table (a title, notes or metadata)",
            # `0.00` as `0` is the same whole number and needs no note (owner decision of 2026-10-15); `1.20` as
            # `1.2` drops a written zero of a fraction and is counted.
            *respelled_warning(2, "precipitation_sum (mm)"),
        ]

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
            *respelled_warning(2, "precipitation_sum (mm)"),
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
        assert "had fewer fields than the header; the missing cells are empty (lines " in parsed.profile.warnings[0]

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

        dropped = without_context(parsed, NOTES_REFUSED_WARNING)

        assert dropped.context_lines == [] and dropped.csv == parsed.csv
        assert dropped.warnings[0] == dropped.profile.warnings[0] == NOTES_REFUSED_WARNING
        assert dropped.warnings[1:] == parsed.warnings

    def test_without_context_keeps_the_warning_cap_and_the_omitted_count(self) -> None:
        parsed = parse_dataset("x,y\n1,2\n3,4\n5,6\n")
        # Real sentences (the data tests check that every warning has a telemetry code, conftest.py).
        full = [f"column 'c{index}': spaces around the text removed in 1 cell" for index in range(MAX_WARNINGS - 1)]
        full += ["7 more warnings omitted"]
        capped = replace(parsed, warnings=full, profile=parsed.profile.model_copy(update={"warnings": full}))

        dropped = without_context(capped, NOTES_INSTRUCTION_WARNING)

        assert len(dropped.warnings) == MAX_WARNINGS
        assert dropped.warnings[0] == NOTES_INSTRUCTION_WARNING and dropped.warnings[-1] == "8 more warnings omitted"


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
        assert parsed.csv == "day,ok,n\na,True,1\nb,False,2.5\nc,,\n"

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
        assert parsed.csv.splitlines()[1:] == ["Mo,15.6", "Di,8"]
        assert parsed.profile.decimal == ","

    def test_a_leading_euro_with_the_sign_before_it(self) -> None:
        parsed = parse_dataset("Posten;Preis\nA;€ 5\nB;-€ 12,50\nC;€-1,5\n")

        assert parsed.column_dtypes == {"Posten": "text", "Preis (€)": "number"}
        assert parsed.csv.splitlines()[1:] == ["A,5", "B,-12.5", "C,-1.5"]

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
        assert parsed.csv.splitlines()[1:] == ["-3", "2", "-0.5"]

    @pytest.mark.parametrize(
        ("cells", "name", "dtype", "canonical"),
        [
            (["20 °C", "-5°C"], "v (°C)", "integer", ["20", "-5"]),
            (["12°", "15 °"], "v (°)", "integer", ["12", "15"]),
            (["5µs", "7 μs"], "v", "text", ["5µs", "7 μs"]),
            (["5µs", "7 µs"], "v (µs)", "integer", ["5", "7"]),
            (["3 Std", "4,5 Std"], "v (Std)", "number", ["3", "4.5"]),
            (["1.234,56 €", "7,5 €"], "v (€)", "number", ["1234.56", "7.5"]),
            (["$ 3", "-$ 2.5", "$-1"], "v ($)", "number", ["3", "-2.5", "-1"]),
            (["12‰"], "v (‰)", "integer", ["12"]),
            (["2E-2 h", "1e3h"], "v (h)", "number", ["0.02", "1000"]),
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
            (["5 Mio.", "3,5 Mio."], "v (Mio.)", ["5", "3.5"]),
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
            (["2025-01", "2025-12"], "datetime", ["2025-01-01", "2025-12-01"]),
            (["2025-Q1", "2025-q4"], "text", ["2025-Q1", "2025-q4"]),
            (["2009-10", "2010-11", "2011-12"], "text", ["2009-10", "2010-11", "2011-12"]),
            (["2000-05", "2005-10"], "text", ["2000-05", "2005-10"]),
            (["2025-13"], "text", ["2025-13"]),
            (["0999-01"], "text", ["0999-01"]),
            (["2025-01", "2025-Q2"], "text", ["2025-01", "2025-Q2"]),
            (["31.02.2024"], "text", ["31.02.2024"]),
            (["25/12/2024", "12/25/2024"], "text", ["25/12/2024", "12/25/2024"]),
            (["2024-01-05", "05.01.2024"], "text", ["2024-01-05", "05.01.2024"]),
            (["true", "FALSE", "True"], "boolean", ["True", "False", "True"]),
            (["1", "-2", "+3"], "integer", ["1", "-2", "3"]),
            (["9223372036854775807"], "integer", ["9223372036854775807"]),
            # Past int64 a float64 would round the last digits: text keeps every one (owner rule of 2026-10-15).
            (["9223372036854775808"], "text", ["9223372036854775808"]),
            (["007", "12"], "text", ["007", "12"]),
            (["0", "-0"], "integer", ["0", "0"]),
            (["1.5", ".5", "1e3", "2E-2", "3."], "number", ["1.5", "0.5", "1000", "0.02", "3"]),
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
        # A paste drops such a column (`TestEmptyColumns`); the service's own CSV keeps and types it.
        parsed = parse_dataset("a,b\n1,\n2,\n", find_table=False, max_bytes=MAX_COMPUTED_BYTES, canonical=True)

        assert column(parsed, "b").dtype == "text"
        assert column(parsed, "b").missing == 2


class TestMonthsAndQuarters:
    """Live test round 7 of 2026-10-16: `2025-01` read as text made `GWh` the x of a monthly line."""

    TEXT = "Monat,Quelle,GWh\n2025-01,Wasser,2228\n2025-01,Kern,1740\n2025-02,Wasser,2010\n2025-02,Kern,1702\n"

    def test_a_month_column_is_dates_with_the_reading_announced(self) -> None:
        parsed = parse_dataset(self.TEXT)

        assert parsed.column_dtypes["Monat"] == "datetime"
        assert parsed.csv.splitlines()[1] == "2025-01-01,Wasser,2228"
        assert "column 'Monat': 4 cells read as months (YYYY-MM, each as the first day of the month)" in parsed.warnings

    def test_it_reads_as_set_type_with_yyyy_mm_does(self) -> None:
        text_first = parse_dataset(self.TEXT, text_columns=["Monat"])
        operations = TypeAdapter(list[Operation]).validate_python(
            [{"op": "set_type", "column": "Monat", "type": "datetime", "date_format": "YYYY-MM"}]
        )

        converted = apply_operations(text_first, operations)

        assert converted.csv == parse_dataset(self.TEXT).csv

    def test_quarters_keep_their_spelling(self) -> None:
        # As a date `2025-Q1` would read `2025-01-01` and lose the word quarter; `set_type` reads it on request.
        parsed = parse_dataset("Quartal,Umsatz\n2025-Q1,10\n2025-Q2,12\n")

        assert parsed.column_dtypes["Quartal"] == "text"
        assert parsed.csv.splitlines()[1:] == ["2025-Q1,10", "2025-Q2,12"]

    @pytest.mark.parametrize("name", ["Saison", "season", "Code", "Kurs Nr"])
    def test_a_name_that_says_season_or_code_keeps_the_text(self, name: str) -> None:
        parsed = parse_dataset(f"{name},Punkte\n2024-01,10\n2024-03,12\n2025-02,9\n")

        assert parsed.column_dtypes[name] == "text"

    def test_season_spans_stay_text(self) -> None:
        # Each second part is the next year's last two digits: a season, not October, November, December.
        parsed = parse_dataset("Jahr,Tore\n2009-10,61\n2010-11,58\n2011-12,64\n")

        assert parsed.column_dtypes["Jahr"] == "text"
        assert not any("read as months" in line for line in parsed.warnings)

    def test_month_headers_stay_labels_through_to_long(self) -> None:
        """Review of #12204: the pivot's names must not turn into dates the heatmap's `y` would read as such."""
        text = "Region,2025-01,2025-02,2025-03\nNord,1,2,3\nSüd,4,5,6\nOst,7,8,9\n"
        operations = TypeAdapter(list[Operation]).validate_python(
            [{"op": "pivot_longer", "columns": ["2025-01", "2025-02", "2025-03"], "names_to": "y"}]
        )

        prepared = apply_operations(parse_dataset(text), operations)

        assert "y" in prepared.text_columns
        again = parse_dataset(prepared.csv, text_columns=prepared.text_columns, find_table=False, canonical=True)
        assert again.column_dtypes["y"] == "text" and again.csv.splitlines()[1] == "Nord,2025-01,1"


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
        assert column(parsed, "n").min == 1
        assert column(parsed, "n").max == 10
        assert isinstance(column(parsed, "n").max, int)  # exact: a float would round an id past 2**53
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

    @pytest.mark.parametrize(
        ("cells", "months"),
        [
            # Live test round 4 of 2026-10-15: the five top values stopped at `Mai`, the column runs to `Jun`.
            (["Jan", "Feb", "Mär", "Apr", "Mai", "Jun"], [1, 2, 3, 4, 5, 6]),
            (["Dezember", "Januar", "Februar", "Januar"], [1, 2, 12]),
            (["janv.", "févr.", "mars", "avr."], [1, 2, 3, 4]),
            (["Jan", "Feb", "Total"], None),  # one cell that is no month
            (["set", "out", "set"], None),  # two short words are a category, not September and October
            (["Q1", "Q2", "Q3"], None),
        ],
    )
    def test_a_text_column_of_month_names_carries_its_months(self, cells: list[str], months: list[int] | None) -> None:
        parsed = parse_dataset("Monat,v\n" + "".join(f"{cell},{index}\n" for index, cell in enumerate(cells)))

        assert column(parsed, "Monat").months == months
        assert column(parsed, "v").months is None

    def test_a_number_column_of_months_has_no_month_list(self) -> None:
        """Month numbers are an integer column: the range is its min and max."""
        assert column(parse_dataset("Monat,v\n1,5\n2,6\n3,7\n"), "Monat").months is None

    def test_top_values_are_capped_and_clipped(self) -> None:
        values = [f"value-{i}-" + "z" * 60 for i in range(MAX_LISTED_VALUES + 1)]
        parsed = parse_dataset("t\n" + "\n".join(values) + "\n")
        top = column(parsed, "t").top

        assert len(top) == MAX_TOP_VALUES
        assert all(len(value) <= MAX_CELL_CHARS for value in top)
        assert top[0].endswith("…")

    def test_a_column_of_few_values_lists_every_one(self) -> None:
        """Live test round 8 of 2026-10-16: the profile listed five of six sources, so the root never saw `Übrige`
        and told the user the plot had added it to fill the donut."""
        text = (
            "Quelle,Anteil_Prozent\nWasserkraft,56.3\nKernenergie,32.4\nSolar,6.8\nWind,0.4\nBiomasse,2.1\nÜbrige,2.0\n"
        )
        quelle = column(parse_dataset(text), "Quelle")

        assert quelle.top == ["Wasserkraft", "Kernenergie", "Solar", "Wind", "Biomasse", "Übrige"]
        assert quelle.unique == len(quelle.top)

    def test_twelve_values_are_listed_and_thirteen_are_the_five_most_frequent(self) -> None:
        def top(count: int) -> list[str]:
            rows = [f"v{i}" for i in range(count)] + ["v3"] * 2
            return column(parse_dataset("t\n" + "\n".join(rows) + "\n"), "t").top

        assert len(top(MAX_LISTED_VALUES)) == MAX_LISTED_VALUES
        assert top(MAX_LISTED_VALUES)[0] == "v3"  # most frequent first
        assert top(MAX_LISTED_VALUES + 1) == ["v3", "v0", "v1", "v2", "v4"]

    def test_preview_is_the_first_20_rows_with_clipped_cells(self) -> None:
        parsed = parse_dataset("t\n" + "\n".join(f"row {i} " + "y" * 50 for i in range(30)) + "\n")

        assert len(parsed.preview) == PREVIEW_ROWS
        assert parsed.preview[0][0].startswith("row 0 ")
        assert len(parsed.preview[0][0]) == MAX_CELL_CHARS
        assert len(parsed.profile.sample[0][0]) == MAX_CELL_CHARS

    def test_the_model_sees_single_lines_and_the_page_the_whitespace_as_it_is(self) -> None:
        """The page draws breaks and space runs visibly (owner decision of 2026-10-15); the profile stays one line."""
        parsed = parse_dataset('t\n"line one\nline  two"\n')

        assert parsed.preview == [["line one\nline  two"]]
        assert parsed.profile.sample == [["line one line two"]]
        assert parse_dataset("t\n" + "x" * 60 + "\n").preview == [["x" * (MAX_CELL_CHARS - 1) + "…"]]
        assert parsed.csv == 't\n"line one\nline  two"\n'

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

        assert parsed.csv == "Land,Jahr,value\nAT,2023,1.5\nAT,2024,\nCH,2023,\nCH,2024,4\n"
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


# A statistics-office export as pasted CSV (generalised from the live test of 2026-10-14, a BFS table): the
# filters `Region` and `Sex` repeat one value in every row, `Origin` and `Year` vary.
OFFICE_EXPORT = (
    "Year;Region;Origin;Sex;Population\n"
    "2021;Country;Native;Sex - Total;6500\n"
    "2021;Country;Foreign;Sex - Total;2200\n"
    "2022;Country;Native;Sex - Total;6550\n"
    "2022;Country;Foreign;Sex - Total;2400\n"
)


class TestConstantColumns:
    def test_constant_text_columns_move_to_the_notes(self) -> None:
        parsed = parse_dataset(OFFICE_EXPORT)

        assert [column.name for column in parsed.profile.columns] == ["Year", "Origin", "Population"]
        assert parsed.csv.splitlines()[0] == "Year,Origin,Population"
        assert parsed.context_lines == ["Region: Country", "Sex: Sex - Total"]
        assert "2 columns with the same text in every row moved to the notes: Region, Sex" in parsed.warnings
        assert "Country" not in " ".join(parsed.warnings)  # the warning names columns, never values
        assert list(read_back(parsed).columns) == ["Year", "Origin", "Population"]

    def test_the_notes_follow_the_lines_around_the_table(self) -> None:
        parsed = parse_dataset("Population by origin\n" + OFFICE_EXPORT)

        assert parsed.context_lines == ["Population by origin", "Region: Country", "Sex: Sex - Total"]

    def test_a_constant_whose_note_the_cap_would_cut_stays_a_column(self) -> None:
        """The notes hold at most `MAX_CONTEXT_CHARS`: a value never disappears into a cut note."""
        title = "x" * (MAX_CONTEXT_CHARS - 30)
        parsed = parse_dataset(f"{title}\n" + OFFICE_EXPORT)

        # `Region: Country` fits in the 29 characters left, `Sex: Sex - Total` no longer does.
        assert parsed.context_lines == [title, "Region: Country"]
        assert [column.name for column in parsed.profile.columns] == ["Year", "Origin", "Sex", "Population"]
        assert "1 column with the same text in every row moved to the notes: Region" in parsed.warnings

    def test_too_few_columns_left_keeps_every_column(self) -> None:
        parsed = parse_dataset("Region,Population\nCountry,6500\nCountry,2200\n")

        assert [column.name for column in parsed.profile.columns] == ["Region", "Population"]
        assert parsed.context_lines == []

    @pytest.mark.parametrize(
        "text",
        [
            "Region,Origin,Population\nCountry,Native,6500\n,Foreign,2200\n",  # a missing cell: not the same everywhere
            "Unit,Origin,Population\n1,Native,6500\n1,Foreign,2200\n",  # a number column, not text
            "Region,Origin,Population\nCountry,Native,6500\n",  # one row: every column is the same everywhere
        ],
    )
    def test_only_complete_text_columns_of_two_rows_count(self, text: str) -> None:
        parsed = parse_dataset(text)

        assert len(parsed.profile.columns) == 3 and parsed.context_lines == []

    def test_refused_notes_bring_the_columns_back(self) -> None:
        """The notes judge refuses the notes: the values they carried come back as columns, never lost."""
        parsed = without_context(parse_dataset(OFFICE_EXPORT), NOTES_UNCHECKED_WARNING)

        assert [column.name for column in parsed.profile.columns] == ["Year", "Region", "Origin", "Sex", "Population"]
        assert parsed.context_lines == [] and parsed.warnings[0] == NOTES_UNCHECKED_WARNING
        assert not any("moved to the notes" in warning for warning in parsed.warnings)
        assert read_back(parsed)["Region"].tolist() == ["Country"] * 4

    def test_a_store_without_screened_notes_keeps_the_columns(self) -> None:
        """A fixture seed or an eval's ingest stores no notes: the constant columns stay in the table."""
        from agents.anyplot.data.store import DatasetStore
        from agents.anyplot.dev_fixture import snapshot_from_repo
        from agents.anyplot.opening import dataset_judge_inputs, store_dataset

        parsed = parse_dataset(OFFICE_EXPORT)
        snapshot = snapshot_from_repo("scatter-basic", "matplotlib")
        unscreened = store_dataset(DatasetStore(), "s1", parsed, snapshot)
        screened = store_dataset(DatasetStore(), "s1", parsed, snapshot, notes_screened=True)

        assert "Region" in unscreened.parsed.column_dtypes and unscreened.parsed.context_lines == []
        assert "Region" not in screened.parsed.column_dtypes and screened.parsed.context_lines
        # The dataset judge reads the table with its constant columns, which may become columns again.
        assert '"Region"' in dataset_judge_inputs(parsed)[0] and "Country" in "".join(dataset_judge_inputs(parsed))

    def test_a_canonical_reparse_keeps_them(self) -> None:
        """An operation or the user's code made the column: the re-parse of the service's CSV keeps it."""
        parsed = parse_dataset(
            "Region,Origin,Population\nCountry,Native,6500\nCountry,Foreign,2200\n", find_table=False, canonical=True
        )

        assert [column.name for column in parsed.profile.columns] == ["Region", "Origin", "Population"]

    def test_a_column_kept_text_by_request_stays(self) -> None:
        parsed = parse_dataset(
            "Region,Origin,Population\nCountry,Native,6500\nCountry,Foreign,2200\n", text_columns=["Region"]
        )

        assert parsed.profile.columns[0].name == "Region"


class TestNaCategory:
    """`NA` is Namibia or North America as often as it is "not available"; `data.csv` and its loader keep it."""

    def test_na_among_letter_codes_is_a_code(self) -> None:
        parsed = parse_dataset("Country,Exports\nCH,12\nNA,3\nDE,40\n")

        assert parsed.csv == "Country,Exports\nCH,12\nNA,3\nDE,40\n"
        assert parsed.profile.columns[0].missing == 0 and "NA" in parsed.profile.columns[0].top
        assert any("NA read as a code" in warning for warning in parsed.warnings)
        assert read_back(parsed)["Country"].tolist() == ["CH", "NA", "DE"]

    @pytest.mark.parametrize(
        "text",
        [
            "Name,Score\nAnna,1\nNA,2\nBen,3\n",  # names, not codes
            "Country,Score\nCH,1\nNA,2\n",  # one other code is too few to tell
            "Score,Weight\n1,NA\n2,3\n",  # a number column
        ],
    )
    def test_na_elsewhere_stays_missing(self, text: str) -> None:
        parsed = parse_dataset(text)

        assert ",NA" not in parsed.csv and "\nNA," not in parsed.csv
        assert not any("NA read as a code" in warning for warning in parsed.warnings)

    def test_json_keys_and_json_stat_categories_survive_the_loader(self) -> None:
        pairs = parse_dataset('{"NA": 3, "EU": 4, "None": 5}')
        stat = parse_dataset(json_stat(["region"], [3], {"region": categories("NA", "EU", "AS")}, [1, 2, 3]))

        assert read_back(pairs)["category"].tolist() == ["NA", "EU", "None"]
        assert read_back(stat)["region"].tolist() == ["NA", "EU", "AS"]

    def test_a_canonical_reparse_keeps_every_text_cell(self) -> None:
        """The service writes a missing cell as an empty one: any other text, `NA` or `null`, is a value."""
        parsed = parse_dataset(
            "Continent,Label,Count\nNA,null,3\nEU,ok,\n", find_table=False, max_bytes=MAX_COMPUTED_BYTES, canonical=True
        )

        assert parsed.csv == "Continent,Label,Count\nNA,null,3\nEU,ok,\n"
        assert parsed.profile.columns[2].missing == 1
        frame = read_back(parsed)
        assert frame["Continent"].tolist() == ["NA", "EU"] and frame["Label"].tolist() == ["null", "ok"]


# Live test round 2 of 2026-10-15: a German-format semicolon CSV of Swiss CO2 emissions (decimal commas,
# population with thousands dots), the first rows as pasted.
CH_CO2_DE = (
    "Jahr;CO2 (Mio. t);CO2 pro Kopf (t);Bevölkerung\n"
    "2000;43,621;6,07;7.184.003\n"
    "2001;45,085;6,24;7.226.391\n"
    "2002;43,467;5,97;7.278.744\n"
    "2003;44,651;6,09;7.333.451\n"
)


class TestThousandsGroups:
    """Numbers whose thousands are grouped by a dot, a comma, an apostrophe or a space (`_as_grouped_numbers`)."""

    def test_the_swiss_co2_paste_reads_its_population_as_integers(self) -> None:
        parsed = parse_dataset(CH_CO2_DE)

        assert parsed.column_dtypes == {
            "Jahr": "integer",
            "CO2 (Mio. t)": "number",
            "CO2 pro Kopf (t)": "number",
            "Bevölkerung": "integer",
        }
        assert read_back(parsed)["Bevölkerung"].tolist() == [7184003, 7226391, 7278744, 7333451]
        assert warned(parsed, "column 'Bevölkerung': dots read as thousands separators")
        # `6,07` settles the file's decimal comma, so `43,621` asks no question.
        assert column(parsed, "CO2 (Mio. t)").max == 45.085
        assert not warned(parsed, "commas read as decimal commas")

    def test_two_dot_groups_settle_the_one_group_cells_of_the_column(self) -> None:
        parsed = parse_dataset("Ort,Einwohner\nA,999.123\nB,1.234.567\nC,12\n")

        assert parsed.csv.splitlines()[1:] == ["A,999123", "B,1234567", "C,12"]

    @pytest.mark.parametrize(
        ("cells", "expected", "label"),
        [
            (["1'234'567", "2'000", "15"], [1234567, 2000, 15], "apostrophes"),
            (["1’234.5", "20’000.25"], [1234.5, 20000.25], "apostrophes"),
            (["1 234 567", "12 000"], [1234567, 12000], "spaces"),
            (["1\N{NO-BREAK SPACE}234,5", "999"], [1234.5, 999], "spaces"),
            (
                ["1\N{NARROW NO-BREAK SPACE}234\N{NARROW NO-BREAK SPACE}567", "5\N{NARROW NO-BREAK SPACE}000"],
                [1234567, 5000],
                "spaces",
            ),
            (["1\N{THIN SPACE}234\N{THIN SPACE}000", "7"], [1234000, 7], "spaces"),
            (['"1,234,567"', '"2,000"'], [1234567, 2000], "commas"),
            (['"1,234.5"', "12.25"], [1234.5, 12.25], "commas"),
        ],
    )
    def test_grouped_numbers_read_as_numbers(self, cells: list[str], expected: list[float], label: str) -> None:
        parsed = parse_dataset("label\tvalue\n" + "".join(f"r{i}\t{cell}\n" for i, cell in enumerate(cells)))

        assert column(parsed, "value").dtype in ("integer", "number")
        assert read_back(parsed)["value"].tolist() == expected
        assert warned(parsed, f"column 'value': {label} read as thousands separators")

    def test_a_swiss_amount_behind_a_currency_keeps_its_groups(self) -> None:
        parsed = parse_dataset("Posten;Betrag\nMiete;CHF 1'850.50\nAuto;CHF 12'400\nHaus;CHF 1'250'000\n")

        assert parsed.column_dtypes["Betrag (CHF)"] == "number"
        assert read_back(parsed)["Betrag (CHF)"].tolist() == [1850.5, 12400, 1250000]

    @pytest.mark.parametrize(
        "evidence",
        [
            ["0.25", "0.5", "0.25"],  # a dot decimal elsewhere says nothing about the commas here
            ["12.30", "8.15", "17.45"],  # times
            ["4.5", "3.8", "4.1"],  # a rating beside a price (second opinion of 2026-10-15)
        ],
    )
    def test_a_dot_decimal_elsewhere_keeps_the_ambiguous_decimal_comma(self, evidence: list[str]) -> None:
        rows = "".join(
            f"{name}\t{price}\t{value}\n"
            for name, price, value in zip("ABC", ['"1,250"', '"2,500"', "980"], evidence, strict=True)
        )
        parsed = parse_dataset("name\tprice\tother\n" + rows)

        assert read_back(parsed)["price"].tolist() == [1.25, 2.5, 980]
        assert warned(parsed, "column 'price': commas read as decimal commas")

    def test_one_comma_group_beside_a_comma_grouped_column_is_thousands(self) -> None:
        parsed = parse_dataset('city\tpopulation\tarea\nA\t"1,234"\t"1,234,567"\nB\t"12,500"\t"2,000"\nC\t980\t17\n')

        assert read_back(parsed)["population"].tolist() == [1234, 12500, 980]
        assert read_back(parsed)["area"].tolist() == [1234567, 2000, 17]
        assert warned(parsed, "column 'population': commas read as thousands separators, as in the file's other")
        assert not warned(parsed, "commas read as decimal commas")

    def test_a_currency_column_of_three_digit_comma_groups_is_thousands(self) -> None:
        alone = parse_dataset('price\n"$1,200"\n"$950"\n"$12,500"\n')
        beside = parse_dataset('price,rating\n"$1,200",4.5\n"$950",3.8\n"$12,500",4.9\n')

        assert alone.column_dtypes == {"price ($)": "integer"}
        assert alone.csv == "price ($)\n1200\n950\n12500\n"
        assert alone.profile.decimal == "."
        assert read_back(alone)["price ($)"].tolist() == [1200, 950, 12500]
        assert warned(
            alone, "column 'price ($)': commas read as thousands separators, as a currency amount has at most two"
        )
        assert not warned(alone, "commas read as decimal commas")
        assert beside.csv == "price ($),rating\n1200,4.5\n950,3.8\n12500,4.9\n"
        assert warned(
            beside, "column 'price ($)': commas read as thousands separators, as a currency amount has at most two"
        )
        assert not warned(beside, "commas read as decimal commas")

    @pytest.mark.parametrize(
        ("cells", "unit"),
        [
            (['"1,200 USD"', '"950 USD"', '"12,500 USD"'], "USD"),
            (['"€ 1,200"', '"€ 950"', '"€ 12,500"'], "€"),
            (['"CHF 1,200"', '"CHF 950"', '"CHF 12,500"'], "CHF"),
        ],
    )
    def test_other_currencies_read_three_digit_comma_groups_as_thousands(self, cells: list[str], unit: str) -> None:
        rows = "".join(f"{cell},{rating}\n" for cell, rating in zip(cells, ["4.5", "3.8", "4.9"], strict=True))
        parsed = parse_dataset("price,rating\n" + rows)
        name = f"price ({unit})"

        assert parsed.column_dtypes[name] == "integer"
        assert read_back(parsed)[name].tolist() == [1200, 950, 12500]
        assert read_back(parsed)["rating"].tolist() == [4.5, 3.8, 4.9]
        assert warned(parsed, f"column '{name}': commas read as thousands separators, as a currency")
        assert not warned(parsed, "commas read as decimal commas")

    @pytest.mark.parametrize(
        ("cells", "expected"),
        [
            (['"$1,25"', '"$3,50"'], [1.25, 3.5]),  # two-digit fractions: decimal commas
            (['"$1,200"', '"$3,50"'], [1.2, 3.5]),  # a short fraction in the column keeps decimal commas
            (['"$1,2000"', '"$950"'], [1.2, 950.0]),  # a four-digit group: not a thousands group
            (['"$0,125"', '"$1,250"'], [0.125, 1.25]),  # a zero-leading group: not a thousands group
        ],
    )
    def test_currency_commas_that_are_not_three_digit_groups_stay_decimal_commas(
        self, cells: list[str], expected: list[float]
    ) -> None:
        parsed = parse_dataset("price\n" + "\n".join(cells) + "\n")

        assert parsed.column_dtypes == {"price ($)": "number"}
        assert parsed.profile.decimal == ","
        assert read_back(parsed)["price ($)"].tolist() == expected
        assert not warned(parsed, "commas read as thousands separators")

    def test_a_semicolon_file_with_decimal_commas_is_unchanged(self) -> None:
        parsed = parse_dataset("Preis;Menge\n3,50;1.200\n")

        assert parsed.csv == "Preis,Menge\n3.5,1200\n"
        assert parsed.profile.decimal == ","

    @pytest.mark.parametrize(
        ("text", "name", "expected", "asks"),
        [
            # a decimal-comma column settles the comma (a fuel receipt: `1,789 €` per litre)
            (
                "Datum;Preis;Liter\n01.10.2026;1,789 €;45,5\n02.10.2026;1,759 €;30,2\n",
                "Preis (€)",
                [1.789, 1.759],
                False,
            ),
            ('a,b\n"$1,200","$1,25"\n"$950","$2,50"\n', "a ($)", [1.2, 950.0], False),
            # a semicolon file is written where the comma is the decimal mark
            ("Datum;Preis\n01.10.2026;1,789 €\n02.10.2026;1,759 €\n", "Preis (€)", [1.789, 1.759], True),
            # a column of dot groups or `1.234` shapes speaks for dot thousands
            ('price,population\n"€ 1,200","7.184.003"\n"€ 950","7.226.391"\n', "price (€)", [1.2, 950.0], True),
            ('price,weight\n"$1,200",1.250\n"$950",2.500\n', "price ($)", [1.2, 950.0], True),
            # dot groups kept as text past int64 still speak for dot thousands
            (
                'price,total\n"€ 1,789",12.345.678.901.234.567.890.123\n"€ 1,759",7.226.391\n',
                "price (€)",
                [1.789, 1.759],
                True,
            ),
            # `0,125` is no thousands group, so its comma is a decimal comma
            ("Preis\tLiter\n1,789 €\t0,125\n1,759 €\t0,250\n", "Preis (€)", [1.789, 1.759], True),
        ],
    )
    def test_a_file_that_speaks_for_decimal_commas_keeps_them_in_a_currency_column(
        self, text: str, name: str, expected: list[float], asks: bool
    ) -> None:
        parsed = parse_dataset(text)

        assert parsed.column_dtypes[name] == "number"
        assert read_back(parsed)[name].tolist() == expected
        assert not warned(parsed, "as a currency amount")
        assert warned(parsed, f"column '{name}': commas read as decimal commas") is asks

    def test_an_id_or_oversized_currency_comma_column_is_not_retyped_as_integers(self) -> None:
        code = parse_dataset('Code\n"$1,200"\n"$2,500"\n')
        huge = parse_dataset('price\n"$1,200"\n"$12345678901234567890123"\n')

        assert code.column_dtypes == {"Code ($)": "number"}
        assert read_back(code)["Code ($)"].tolist() == [1.2, 2.5]
        assert huge.column_dtypes == {"price": "text"}
        assert huge.csv == 'price\n"$1,200"\n$12345678901234567890123\n'
        assert f"column 'price': {parse_module.BIG_INTEGERS}" in huge.warnings
        assert not warned(huge, "commas read as decimal commas")

    def test_an_oversized_comma_column_beside_comma_groups_stays_text(self) -> None:
        parsed = parse_dataset('a,b\n"1,234","1,234,567"\n9223372036854775808,"2,000"\n')

        assert parsed.column_dtypes["a"] == "text"
        assert read_back(parsed)["a"].tolist() == ["1,234", "9223372036854775808"]
        assert f"column 'a': {parse_module.BIG_INTEGERS}" in parsed.warnings
        assert not warned(parsed, "commas read as decimal commas")

    def test_one_dot_group_beside_a_dot_grouped_column_is_thousands(self) -> None:
        parsed = parse_dataset("a;b;c\nx;7.184.003;1.234\ny;7.226.391;2.500\nz;7.278.744;980\n")

        assert parsed.column_dtypes == {"a": "text", "b": "integer", "c": "integer"}
        assert read_back(parsed)["c"].tolist() == [1234, 2500, 980]
        assert warned(parsed, "column 'c': dots read as thousands separators, as in the file's other columns")
        assert parsed.profile.decimal == "."

    @pytest.mark.parametrize(
        ("header", "cells"),
        [
            ("value", ["123 456", "234 567", "345 678"]),  # one space group: a phone or article number
            ("value", ["1'234", "5'678", "9'012"]),  # one apostrophe group without a decimal
            ("value", ["192.168.100.200", "10.200.100.150", "172.160.100.250"]),  # IPv4 addresses
            ("Version", ["1.200.300", "1.200.301", "2.000.000"]),
            ("Artikel-Nr", ["1'234'567", "2'345'678", "3'456'789"]),
            ("customer_id", ["1.234.567", "2.345.678", "3.456.789"]),
            ("PLZ", ["8 000 001", "3 000 002", "1 200 003"]),
        ],
    )
    def test_ids_codes_and_addresses_stay_text(self, header: str, cells: list[str]) -> None:
        rows = "".join(f"r{i};{i};{cell}\n" for i, cell in enumerate(cells))
        parsed = parse_dataset(f"label;n;{header}\n" + rows)

        assert column(parsed, header).dtype == "text"
        assert not warned(parsed, "read as thousands separators")

    def test_an_id_column_is_not_retyped_by_the_files_decimal_comma(self) -> None:
        parsed = parse_dataset("Preis;Code\n3,50;1.200\n2,10;1.300\n")

        assert column(parsed, "Code").dtype == "number"
        assert read_back(parsed)["Code"].tolist() == [1.2, 1.3]

    def test_one_comma_group_without_other_evidence_stays_a_decimal_comma(self) -> None:
        parsed = parse_dataset("label;v\na;1,234\nb;5,678\n")

        assert column(parsed, "v").max == 5.678
        assert warned(parsed, "column 'v': commas read as decimal commas")

    @pytest.mark.parametrize(
        "cells",
        [
            ["1.2.3", "4.5.6"],  # groups of one digit: a version or an outline number
            ["1'23", "4'56"],  # an apostrophe before two digits
            ["1 23", "4 5"],  # spaces between short numbers
            ["1.234,5.6", "7"],  # a mark used as both separator and decimal
            ["1'234,5", "1'234.5"],  # two decimal marks in one column
            ["0.123.456", "7"],  # a group never starts with a zero
        ],
    )
    def test_irregular_groups_stay_text(self, cells: list[str]) -> None:
        rows = "".join(f"r{i};{i};{cell}\n" for i, cell in enumerate([*cells, *cells]))
        parsed = parse_dataset("label;n;value\n" + rows)

        assert column(parsed, "value").dtype == "text"

    def test_dotted_dates_are_still_dates(self) -> None:
        parsed = parse_dataset("Datum;Wert\n01.02.2024;1.234.567\n15.03.2024;7\n")

        assert parsed.column_dtypes == {"Datum": "datetime", "Wert": "integer"}
        assert column(parsed, "Datum").min == "2024-02-01"


class TestEmptyColumns:
    """Columns without a value in any row leave the table (`_without_empty_columns`)."""

    ECB = (
        "KEY,FREQ,TIME_PERIOD,OBS_VALUE,OBS_PRE_BREAK,OBS_COM,BREAKS,TITLE\n"
        "EXR.D.CHF.EUR.SP00.A,D,2024-01-02,0.9305,,,,Swiss franc/Euro\n"
        "EXR.D.CHF.EUR.SP00.A,D,2024-01-03,0.9322,,,,Swiss franc/Euro\n"
        "EXR.D.CHF.EUR.SP00.A,D,2024-01-04,0.9301,,,,Swiss franc/Euro\n"
    )

    def test_an_api_export_loses_its_empty_columns_with_one_warning(self) -> None:
        parsed = parse_dataset(self.ECB)

        assert [c.name for c in parsed.profile.columns] == ["TIME_PERIOD", "OBS_VALUE"]
        assert warned(parsed, "3 columns without any value dropped: OBS_PRE_BREAK, OBS_COM, BREAKS")
        assert all(len(row) == 2 for row in parsed.preview)
        # The constants went to the notes; the empty columns are simply gone.
        assert "KEY: EXR.D.CHF.EUR.SP00.A" in parsed.context_lines
        assert not any("OBS_COM" in line for line in parsed.context_lines)

    def test_missing_tokens_count_as_empty(self) -> None:
        parsed = parse_dataset("x,y,note\n1,2,NA\n3,4,-\n5,6,\n")

        assert parsed.column_dtypes == {"x": "integer", "y": "integer"}
        assert warned(parsed, "1 column without any value dropped: note")

    def test_one_column_with_values_is_kept_alone(self) -> None:
        parsed = parse_dataset("x,empty\n1,\n2,\n3,\n")

        assert [c.name for c in parsed.profile.columns] == ["x"]
        assert warned(parsed, "1 column without any value dropped: empty")

    def test_one_column_beside_many_empty_ones_is_no_column_cap_refusal(self) -> None:
        names = ["value", *(f"e{i}" for i in range(55))]
        rows = [f"{i}.5" + "," * 55 for i in range(3)]
        parsed = parse_dataset("\n".join([",".join(names), *rows]) + "\n")

        assert parsed.column_dtypes == {"value": "number"}

    def test_empty_columns_do_not_count_against_the_column_cap(self) -> None:
        names = ["a", "b", *(f"e{i}" for i in range(MAX_COLUMNS))]
        rows = ["1,2" + "," * MAX_COLUMNS, "3,4" + "," * MAX_COLUMNS]
        parsed = parse_dataset("\n".join([",".join(names), *rows]) + "\n")

        assert parsed.column_dtypes == {"a": "integer", "b": "integer"}

    def test_json_records_and_column_lists_drop_empty_fields_before_the_cap(self) -> None:
        empty = {f"unused_{i}": None for i in range(MAX_COLUMNS)}
        records = parse_dataset(json.dumps([{"a": 1, "b": 2, **empty}, {"a": 3, "b": 4, **empty}]))
        columns = parse_dataset(json.dumps({"a": [1, 3], "b": [2, 4], **{k: [None, None] for k in empty}}))

        for parsed in (records, columns):
            assert parsed.column_dtypes == {"a": "integer", "b": "integer"}
            assert warned(parsed, f"{MAX_COLUMNS} columns without any value dropped")

    def test_a_json_table_far_over_the_cap_is_refused_before_it_is_read(self) -> None:
        wide = parse_module.MAX_RAW_COLUMNS + 1
        assert error_code(json.dumps([{f"c{i}": None for i in range(wide)}])) == "too_many_columns"
        assert error_code(json.dumps({f"c{i}": [None] for i in range(wide)})) == "too_many_columns"

    def test_a_canonical_reparse_keeps_an_empty_column(self) -> None:
        parsed = parse_dataset(
            "x,y,ratio\n1,2,\n3,4,\n", find_table=False, max_bytes=MAX_COMPUTED_BYTES, canonical=True
        )

        assert [c.name for c in parsed.profile.columns] == ["x", "y", "ratio"]


# A weather station's export, generalised from the MeteoSwiss case of 2026-10-15 (live test round 3): a block of
# `Key: value` metadata, indented sub-keys and blank lines, then a table aligned with runs of spaces, a header name
# with one inner space, CRLF line ends and trailing spaces. The station and the values are invented.
STATION_EXPORT = (
    "Federal Office of Imaginary Weather\r\n"
    "\r\n"
    "Monthly values\r\n"
    "\r\n"
    "Station:                  Musterberg / Nord\r\n"
    "Altitude [m asl]:         812 m\r\n"
    "\r\n"
    "Units:\r\n"
    "         Max Temp:        °C\r\n"
    "         Precipitation:   mm\r\n"
    "\r\n"
    "Missing values:           {mark}\r\n"
    "Creation date:            3.10.2026\r\n"
    "\r\n"
    "Year  Month        Max Temp      Precipitation  \r\n"
    "1901      1            -4.2               31.5  \r\n"
    "1901      2            -1.0               {mark}  \r\n"
    "1901      3             5.7               48.0  \r\n"
    "1901      4            10.3               66.2  \r\n"
    "1901      5            15.1              102.4  \r\n"
)


class TestSpaceAlignedTables:
    """Tables aligned with spaces, as weather and statistics offices write them (live test of 2026-10-15)."""

    @pytest.mark.parametrize("mark", ["NA", "-999"])
    def test_a_station_export_splits_into_notes_and_a_table(self, mark: str) -> None:
        parsed = parse_dataset(STATION_EXPORT.format(mark=mark))

        assert parsed.profile.source_format == "whitespace"
        assert parsed.column_dtypes == {
            "Year": "integer",
            "Month": "integer",
            "Max Temp": "number",
            "Precipitation": "number",
        }
        assert parsed.profile.rows == 5
        assert column(parsed, "Precipitation").missing == 1
        assert "Station: Musterberg / Nord" in parsed.context_lines
        assert "Max Temp: °C" in parsed.context_lines
        assert f"Missing values: {mark}" in parsed.context_lines
        assert warned(parsed, "left out 9 lines above the table")
        assert parsed.csv.splitlines()[:3] == ["Year,Month,Max Temp,Precipitation", "1901,1,-4.2,31.5", "1901,2,-1,"]

    def test_a_declared_mark_that_reads_as_a_number_is_missing_with_a_warning(self) -> None:
        parsed = parse_dataset(STATION_EXPORT.format(mark="-999"))

        assert column(parsed, "Precipitation").min == 31.5
        assert warned(parsed, "1 cell of number or date columns matched the missing-value mark the notes declare")

    def test_without_a_declaration_the_mark_stays_a_value(self) -> None:
        parsed = parse_dataset(STATION_EXPORT.format(mark="-999").replace("Missing values:", "Remark:"))

        assert column(parsed, "Precipitation").min == -999

    def test_a_declared_na_leaves_a_column_of_letter_codes_alone(self) -> None:
        text = "Missing values: NA\n\nLand    Wert\nCH       1.5\nDE       2.5\nAT       NA\nNA       4.5\n"

        parsed = parse_dataset(text)

        assert column(parsed, "Land").missing == 0  # `NA` is Namibia here (owner decision of 2026-10-15)
        assert column(parsed, "Wert").missing == 1
        assert warned(parsed, "1 cell of number or date columns matched")

    def test_a_declared_letter_mark_never_blanks_a_text_category(self) -> None:
        text = "Missing values: M\n\nSex    Wert\nF       1.5\nM       M\nF       3.5\nM       4.5\n"

        parsed = parse_dataset(text)

        assert column(parsed, "Sex").missing == 0
        assert column(parsed, "Wert").missing == 1

    def test_a_numeric_mark_matches_by_value(self) -> None:
        text = "nodata = -999\n\nTag    Wert\n1      2.5\n2   -999.0\n3      4.5\n"

        parsed = parse_dataset(text)

        assert column(parsed, "Wert").missing == 1 and column(parsed, "Wert").min == 2.5

    def test_a_row_of_declared_marks_stays_a_row(self) -> None:
        text = "Fehlwerte: .\n\nJahr    Nord    Süd\n2020     4.1    6.3\n2021       .      .\n2022     4.7    6.9\n"

        parsed = parse_dataset(text)

        assert parsed.profile.rows == 3
        assert parsed.csv.splitlines()[2] == "2021,,"

    @pytest.mark.parametrize(
        ("lines", "marks"),
        [
            (["Missing values: NA"], {"NA"}),
            (["nodata = -9999"], {"-9999"}),
            (["Missing values: 9999"], {"9999"}),
            (["Fehlwerte: ."], {"."}),
            (["Missing values: none"], set()),
            (["Missing values: no"], set()),
            (["Missing values: 0"], set()),
            (["Missing values: 1"], set()),  # an ordinary value, no sentinel
            (["Missing values: 99"], set()),
            (["The missing values: NA are rare in this file"], set()),
        ],
    )
    def test_only_a_line_that_declares_a_mark_counts(self, lines: list[str], marks: set[str]) -> None:
        assert parse_module._declared_missing(lines) == marks

    def test_a_plain_aligned_table_keeps_its_thousands_and_decimal_rules(self) -> None:
        text = (
            "Region        Einwohner     Anteil   Stichtag\n"
            "Nord          1 234 567       12,5   01.02.2024\n"
            "Süd             987 654        8,25  01.02.2024\n"
            "Ost Mitte     2 001 002       30,0   01.03.2024\n"
        )

        parsed = parse_dataset(text)

        assert parsed.profile.source_format == "whitespace"
        assert parsed.column_dtypes == {
            "Region": "text",
            "Einwohner": "integer",
            "Anteil": "number",
            "Stichtag": "datetime",
        }
        assert parsed.csv.splitlines()[3] == "Ost Mitte,2001002,30,2024-03-01"

    def test_a_timestamp_with_one_inner_space_stays_one_cell(self) -> None:
        text = "Zeit                Wert\n2024-01-01 12:00     5\n2024-01-01 13:00     7\n2024-01-01 14:00     6\n"

        parsed = parse_dataset(text)

        assert parsed.column_dtypes == {"Zeit": "datetime", "Wert": "integer"}

    def test_a_blank_cell_of_a_fixed_width_row_stays_in_its_column(self) -> None:
        text = (
            "Jahr    Nord    Mitte    Süd\n"
            "2020     4.1      5.2    6.3\n"
            "2021              5.5    6.6\n"
            "2022     4.7             6.9\n"
            "2023     4.9      5.8    7.1\n"
        )

        parsed = parse_dataset(text)

        assert parsed.csv.splitlines()[2:4] == ["2021,,5.5,6.6", "2022,4.7,,6.9"]
        assert warned(parsed, "2 rows had fewer fields than the header; their cells were placed")

    def test_short_rows_at_the_end_stay_rows_and_a_source_line_stays_a_note(self) -> None:
        text = (
            "Jahr    Nord    Mitte    Süd\n"
            "2020     4.1      5.2    6.3\n"
            "2021     4.4      5.5    6.6\n"
            "2022     4.7             6.9\n"
            "2023              5.9\n"
            "Quelle: Testamt\n"
        )

        parsed = parse_dataset(text)

        assert parsed.csv.splitlines()[3:] == ["2022,4.7,,6.9", "2023,,5.9,"]
        assert parsed.context_lines == ["Quelle: Testamt"]

    def test_a_short_summary_row_below_the_table_is_left_out_as_a_summary(self) -> None:
        text = (
            "Jahr    Nord    Mitte    Süd\n"
            "2020     4.1      5.2    6.3\n"
            "2021     4.4      5.5    6.6\n"
            "2022     4.7             6.9\n"
            "Total" + " " * 20 + "19.8\n"
        )

        parsed = parse_dataset(text)

        assert parsed.column_dtypes["Jahr"] == "integer"
        assert parsed.profile.rows == 3
        assert parsed.context_lines == []
        assert warned(parsed, "left out 1 summary row")

    def test_a_field_beyond_every_column_is_refused(self) -> None:
        far = "2021" + " " * 50 + "99.0"
        text = f"Jahr    Nord    Mitte    Süd\n2020     4.1      5.2    6.3\n{far}\n2022     4.7      5.0    6.9\n"

        assert error_code(text) == "unparseable"

    def test_a_short_row_that_does_not_line_up_is_refused(self) -> None:
        two_under_mitte = "2021" + " " * 12 + "1  2"  # both fields sit within the `Mitte` column
        text = f"Jahr    Nord    Mitte    Süd\n2020     4.1      5.2    6.3\n{two_under_mitte}\n2022     4.7      5.0    6.9\n"

        assert error_code(text) == "unparseable"

    @pytest.mark.parametrize(
        "short_row",
        [
            "2022     3.14159265",  # starts under `Nord` and reaches into `Mitte`
            "2022       -12.55",  # starts at the end of `Nord` and ends under `Mitte`
        ],
    )
    def test_a_field_under_two_columns_is_refused(self, short_row: str) -> None:
        text = (
            f"Jahr    Nord    Mitte    Süd\n2020     4.1      5.2    6.3\n{short_row}\n2023     4.7      5.0    6.9\n"
        )

        assert error_code(text) == "unparseable"

    def test_a_misaligned_short_row_at_the_end_is_refused_not_a_note(self) -> None:
        text = (
            "Jahr    Nord    Mitte    Süd\n2020     4.1      5.2    6.3\n"
            "2021     4.4      5.5    6.6\n2022     3.14159265\n"
        )

        assert error_code(text) == "unparseable"

    def test_a_single_space_table_of_numbers_reads_with_a_warning(self) -> None:
        parsed = parse_dataset("month sales returns\n1 85 3\n2 90 4.5\n3 70 2\n")

        assert parsed.profile.source_format == "whitespace"
        assert parsed.column_dtypes == {"month": "integer", "sales": "integer", "returns": "number"}
        assert warned(parsed, "single spaces read as the column separator")

    @pytest.mark.parametrize(
        "text",
        [
            "Anteil (%)\n65 %\n12 %\n30 %\n",  # a unit after each value
            "x y\n1 234\n2 345\n3 456\n",  # a space-grouped thousand
            "x y label\n1 2.5 north\n2 3.5 south\n3 4.0 centre\n",  # a text column: the transcriber's
            "name age city\nAnna Lee 30 Bern\nBo Chen 41 Basel\nCara Diaz 28 Chur\n",  # two-word names
            "year country\n2020 CH\n2021 DE\n2022 AT\n",
            "Shopping list\n12 apples\n3 bananas\n5 pears\n",  # a list under a two-word title
        ],
    )
    def test_single_spaces_never_split_text(self, text: str) -> None:
        assert sniff_delimiter(text)[0] is None

    def test_a_key_value_block_is_no_table(self) -> None:
        text = "Station:      Zürich\nAltitude:     604 m\nOpened:       1864\nCount:        12\n"

        assert sniff_delimiter(text)[0] is None

    def test_quotes_around_a_whole_field_go(self) -> None:
        text = 'City          Wert\n"New York"     1.5\n"Bern"         2.5\nBasel          3.5\n'

        parsed = parse_dataset(text)

        assert parsed.csv.splitlines()[1:3] == ["New York,1.5", "Bern,2.5"]

    def test_a_tab_separated_file_with_double_spaces_in_its_text_stays_tsv(self) -> None:
        text = "Area  station\tvalue\nNorth  10\t1\nSouth  20\t2\nCentre  30\t3\n"

        parsed = parse_dataset(text)

        assert parsed.profile.source_format == "tsv"
        assert list(parsed.column_dtypes) == ["Area  station", "value"]

    def test_a_csv_with_spaces_in_its_text_stays_csv(self) -> None:
        parsed = parse_dataset("Station Name, Value\n10 North, 1\n20 South, 2\n30 West, 3\n")

        assert parsed.profile.source_format == "csv"
        assert list(parsed.column_dtypes) == ["Station Name", "Value"]

    def test_a_single_space_table_with_a_ragged_row_stays_one_column(self) -> None:
        parsed = parse_dataset("x y label\n1 2.5 a\n2 3.5 b c\n3 4.0 c\n")

        assert len(parsed.profile.columns) == 1

    def test_a_wide_table_with_years_as_header_reads(self) -> None:
        text = "Land       2020   2021   2022\nSchweiz     8.6    8.7    8.8\nÖsterreich  8.9    9.0    9.1\nItalien    59.4   59.2   58.9\n"

        parsed = parse_dataset(text)

        assert list(parsed.column_dtypes) == ["Land", "2020", "2021", "2022"]

    @pytest.mark.parametrize(
        "text",
        [
            # Prose with numbers and the odd double space after a full stop.
            "We measured 12 plants in 2024.  The tallest was 85 cm.\n"
            "In the second week 3 of them died.  The rest grew.\n"
            "Overall growth was about 4 cm per week, with 2 dry spells.\n",
            # A list without a header: the transcriber reads it, as before.
            "Hund 7\nKatze 3\nMaus 5\n",
            "Hund     7\nKatze    3\nMaus     5\n",
            # Prose whose double spaces would make one aligned line: one data row is no table.
            "Results  of  2024\nWe  sold  12  units.\n",
        ],
    )
    def test_prose_and_a_headerless_list_are_no_space_table(self, text: str) -> None:
        assert sniff_delimiter(text)[0] is None
        assert len(parse_dataset(text).profile.columns) == 1

    def test_a_real_delimiter_wins_over_spaces(self) -> None:
        assert sniff_delimiter("a, b, c\n1, 2, 3\n4, 5, 6\n7, 8, 9\n") == (",", "csv")
        assert sniff_delimiter("Name\tWert  \nAlpha\t1  \nBeta\t2  \nGamma\t3  \n") == ("\t", "tsv")
        assert sniff_delimiter("x;y\n1,5;2,5\n3,5;4,5\n5,5;6,5\n") == (";", "semicolon")
        # Double spaces inside a CSV's text fields add fields, never values: the comma keeps the table.
        spaced_text = "Area  station  name,value\nNorth  10  East,1\nSouth  20  West,2\nCentre  30  North,3\n"
        assert sniff_delimiter(spaced_text) == (",", "csv")


# An API answer shaped like the World Bank's (live test of 2026-10-15), with an invented indicator and values:
# a page-metadata object, then the records, each with nested objects and two always-empty fields.
API_PAGE = [
    {"page": 1, "pages": 1, "per_page": 50, "total": 4, "lastupdated": "2026-10-01"},
    [
        {
            "indicator": {"id": "XX.TEST.IND", "value": "Test indicator (units)"},
            "country": {"id": "AA", "value": "Alphaland"},
            "date": year,
            "value": value,
            "unit": "",
            "obs_status": "",
        }
        for year, value in (("2021", 10.5), ("2022", 11.25))
    ]
    + [
        {
            "indicator": {"id": "XX.TEST.IND", "value": "Test indicator (units)"},
            "country": {"id": "BB", "value": "Betaland"},
            "date": year,
            "value": value,
            "unit": "",
            "obs_status": "",
        }
        for year, value in (("2021", 7.0), ("2022", None))
    ],
]


class TestApiJson:
    """The shapes data APIs answer: records wrapped with metadata, nested objects (live test of 2026-10-15)."""

    def test_a_metadata_object_and_a_record_list_read_as_records_with_notes(self) -> None:
        parsed = parse_dataset(json.dumps(API_PAGE))

        assert parsed.profile.source_format == "json_records"
        assert parsed.column_dtypes == {
            "country.id": "text",
            "country.value": "text",
            "date": "integer",
            "value": "number",
        }
        assert parsed.profile.rows == 4
        assert column(parsed, "value").missing == 1
        assert parsed.context_lines == [
            "page: 1",
            "pages: 1",
            "per_page: 50",
            "total: 4",
            "lastupdated: 2026-10-01",
            "indicator.id: XX.TEST.IND",
            "indicator.value: Test indicator (units)",
        ]
        assert warned(parsed, "5 fields beside the records")
        assert warned(parsed, "named with a dot")
        assert warned(parsed, "2 columns without any value dropped: unit, obs_status")

    @pytest.mark.parametrize("key", ["data", "results", "records", "items"])
    def test_an_object_with_one_record_list_and_metadata_siblings(self, key: str) -> None:
        text = json.dumps(
            {"meta": {"source": "Test API", "count": 3}, key: [{"x": 1, "y": 2}, {"x": 2, "y": 4}, {"x": 3, "y": 6}]}
        )

        parsed = parse_dataset(text)

        assert parsed.column_dtypes == {"x": "integer", "y": "integer"}
        assert parsed.context_lines == ["meta.source: Test API", "meta.count: 3"]

    def test_curves_as_lists_expand_to_one_row_per_point(self) -> None:
        # One record per measured curve, generalised from the owner's case of 2026-10-15.
        curves = [
            {"sample": "A", "temperature_c": 20, "x": [0, 1, 2], "y": [0.1, 0.4, 0.9]},
            {"sample": "B", "temperature_c": 25, "x": [0, 1], "y": [0.2, 0.5]},
        ]

        parsed = parse_dataset(json.dumps(curves))

        assert list(parsed.column_dtypes) == ["sample", "temperature_c", "x", "y"]
        assert parsed.csv.splitlines()[1:] == ["A,20,0,0.1", "A,20,1,0.4", "A,20,2,0.9", "B,25,0,0.2", "B,25,1,0.5"]
        assert warned(parsed, "list fields expanded into one row per value (lists of one record are paired")

    def test_an_empty_list_beside_full_ones_leaves_its_cells_empty(self) -> None:
        parsed = parse_dataset(
            json.dumps([{"x": [1, 2], "y": [3, 4], "z": []}, {"x": [5, 6], "y": [7, 8], "z": [1, 2]}])
        )

        assert parsed.csv.splitlines()[1:3] == ["1,1,3,", "1,2,4,"]

    def test_a_field_that_is_a_list_in_one_record_and_a_value_in_another_is_refused(self) -> None:
        with pytest.raises(ParseError) as caught:
            parse_dataset(json.dumps([{"x": [1, 2], "y": 0}, {"x": [3, 4], "y": [5, 6]}]))

        assert caught.value.code == "unparseable" and "the field y" in caught.value.message

    def test_an_existing_record_id_field_is_never_overwritten(self) -> None:
        curves = [{"record_id": 7, "x": [1, 2]}, {"record_id": 7, "x": [3, 4]}]

        parsed = parse_dataset(json.dumps(curves))

        assert parsed.csv.splitlines()[0] == "record_id_2,record_id,x"
        assert parsed.csv.splitlines()[1:] == ["1,7,1", "1,7,2", "2,7,3", "2,7,4"]
        assert warned(parsed, "column 'record_id_2' added")

    @pytest.mark.parametrize(
        "ids",
        [
            ["A", "A "],  # the same cell once cleaned
            ["NA", "N/A"],  # both missing
            [20.5, 21.5],  # unique, but a measurement
            [True, False],
        ],
    )
    def test_only_distinct_text_or_whole_numbers_tell_curves_apart(self, ids: list[Any]) -> None:
        curves = [{"key": key, "x": [1, 2]} for key in ids]

        parsed = parse_dataset(json.dumps(curves))

        assert parsed.csv.splitlines()[0].startswith("record_id,")

    def test_curves_without_a_field_that_tells_them_apart_get_a_record_id(self) -> None:
        curves = [{"unit": "mV", "t": [0, 1], "v": [1.5, 2.5]}, {"unit": "mV", "t": [0, 1], "v": [3.5, 4.5]}]

        parsed = parse_dataset(json.dumps(curves))

        assert parsed.csv.splitlines()[0] == "record_id,t,v"  # `unit` is constant: it moves to the notes
        assert parsed.csv.splitlines()[1:] == ["1,0,1.5", "1,1,2.5", "2,0,3.5", "2,1,4.5"]
        assert warned(parsed, "column 'record_id' added")

    def test_lists_of_one_record_with_different_lengths_are_refused_by_name(self) -> None:
        with pytest.raises(ParseError) as caught:
            parse_dataset(json.dumps([{"id": 1, "x": [1, 2, 3], "y": [1, 2]}, {"id": 2, "x": [1], "y": [1]}]))

        assert caught.value.code == "unparseable"
        assert "record 1" in caught.value.message and "x (3), y (2)" in caught.value.message

    def test_lists_over_the_row_cap_are_thinned_per_record_with_a_warning(self) -> None:
        points = parse_module.MAX_ROWS  # two curves of this many points: twice the cap
        curves = [{"curve": name, "x": list(range(points)), "y": list(range(points))} for name in ("a", "b")]

        parsed = parse_dataset(json.dumps(curves), max_bytes=MAX_COMPUTED_BYTES)

        lines = parsed.csv.splitlines()
        assert parsed.profile.rows == points  # half of each curve
        assert lines[1] == "a,0,0" and lines[points // 2] == f"a,{points - 1},{points - 1}"  # both ends kept
        assert warned(parsed, f"{points:,} evenly spaced values are kept")
        assert warned(parsed, "paste fewer records or fewer points per record")

    def test_one_long_curve_keeps_both_ends_and_asks_for_fewer_points(self) -> None:
        points = parse_module.MAX_ROWS + 2  # (n - 1) is no multiple of the step
        curve = [{"x": list(range(points)), "y": list(range(points))}]

        parsed = parse_dataset(json.dumps(curve), max_bytes=MAX_COMPUTED_BYTES)

        lines = parsed.csv.splitlines()
        assert parsed.profile.rows <= parse_module.MAX_ROWS
        assert lines[1] == "0,0" and lines[-1] == f"{points - 1},{points - 1}"
        assert warned(parsed, "paste fewer points to keep every value")

    def test_a_list_of_records_with_name_and_type_is_data_not_a_schema(self) -> None:
        payload = {"data": [{"name": "Solar", "type": "renewable", "gwh": 420}], "links": [{"href": "next"}]}

        assert error_code(json.dumps(payload)) == "unparseable"  # two tables: none is taken by guess

    def test_descriptors_that_do_not_name_the_other_lists_fields_are_two_tables(self) -> None:
        payload = {
            "people": [{"name": "Ann", "type": "admin", "age": 3}, {"name": "Bo", "type": "user", "age": 4}],
            "roles": [{"name": "admin", "type": "role"}],
        }

        assert error_code(json.dumps(payload)) == "unparseable"

    def test_bigquerys_own_row_shape_is_refused_not_misread(self) -> None:
        payload = {"schema": {"fields": [{"name": "a", "type": "INTEGER"}]}, "rows": [{"f": [{"v": "1"}]}]}

        assert error_code(json.dumps(payload)) == "unparseable"

    def test_descriptors_beside_an_empty_record_list_are_refused(self) -> None:
        payload = {"fields": [{"name": "a", "type": "int"}, {"name": "b", "type": "str"}], "records": []}

        with pytest.raises(ParseError) as caught:
            parse_dataset(json.dumps(payload))

        assert caught.value.code == "unparseable" and "the list of records is empty" in caught.value.message

    def test_a_list_of_objects_inside_a_record_is_left_out_with_a_warning(self) -> None:
        text = json.dumps([{"name": "a", "n": 1, "tags": [{"k": 1}]}, {"name": "b", "n": 2, "tags": []}])

        parsed = parse_dataset(text)

        assert list(parsed.column_dtypes) == ["name", "n"]  # the other record's empty list leaves no value
        assert warned(parsed, "1 field holding a list of objects or lists")

    @pytest.mark.parametrize(
        "payload",
        [
            {
                "fields": [{"name": "x", "type": "integer"}, {"name": "y", "type": "number"}],
                "rows": [[1, 2.5], [2, 3.5]],
            },
            {
                "schema": {"fields": [{"name": "x", "type": "integer"}, {"name": "y", "type": "number"}]},
                "rows": [[1, 2.5], [2, 3.5]],
            },
            {"columns": ["x", "y"], "index": [0, 1], "data": [[1, 2.5], [2, 3.5]]},  # pandas orient="split"
            {"meta": {"view": {"columns": [{"fieldName": "x"}, {"fieldName": "y"}]}}, "data": [[1, 2.5], [2, 3.5]]},
        ],
    )
    def test_schema_and_rows_read_as_a_table_never_the_schema(self, payload: dict[str, Any]) -> None:
        parsed = parse_dataset(json.dumps(payload))

        assert parsed.column_dtypes == {"x": "integer", "y": "number"}
        assert parsed.csv.splitlines()[1:] == ["1,2.5", "2,3.5"]

    def test_a_schema_beside_records_is_metadata(self) -> None:
        payload = {"fields": [{"name": "x", "type": "integer"}], "data": [{"x": 1}, {"x": 2}]}

        assert parse_dataset(json.dumps(payload)).column_dtypes == {"x": "integer"}

    @pytest.mark.parametrize(
        "payload",
        [
            {"rows": [[1, 2], [3, 4]]},  # rows without names
            {"fields": [{"name": "x", "type": "integer"}], "rows": [[1, 2], [3, 4]]},  # names do not fit
            {"fields": [{"name": "x", "type": "a"}, {"name": "x", "type": "b"}], "rows": [[1, 2]]},
        ],
    )
    def test_rows_that_no_schema_names_are_refused(self, payload: dict[str, Any]) -> None:
        assert error_code(json.dumps(payload)) == "unparseable"

    def test_nesting_is_flattened_to_three_levels(self) -> None:
        record = {"id": 1, "a": {"b": {"c": {"d": 5, "e": {"f": 6}}}}}

        parsed = parse_dataset(json.dumps([record, {**record, "id": 2}]))

        assert list(parsed.column_dtypes) == ["id", "a.b.c.d"]
        assert warned(parsed, "left out: a.b.c.e")

    @pytest.mark.parametrize(
        "data",
        [
            {"left": [{"x": 1}], "right": [{"x": 2}]},  # two tables: none is taken by guess
            [{"page": 1}, [{"x": 1}], [{"x": 2}]],
            [{"page": 0, "total": 0}, []],  # metadata without records
            [{"a.b": 1, "a": {"b": 2}}],  # two fields, one flattened name
        ],
    )
    def test_ambiguous_or_empty_wrappings_are_refused(self, data: Any) -> None:
        assert error_code(json.dumps(data)) == "unparseable"

    def test_json_stat_is_still_read_first_and_plain_shapes_are_unchanged(self) -> None:
        assert parse_dataset(json.dumps({"a": [1, 2], "b": [3, 4]})).profile.source_format == "json_columns"
        assert parse_dataset(json.dumps([["x", 1], ["y", 2]])).profile.source_format == "json_pairs"
        assert parse_dataset(json.dumps([{"a": 1}, {"a": 2}])).context_lines == []


def decimals(seed: int, count: int, digits: int) -> list[str]:
    """Generalised fixture: `count` signed decimals of exactly `digits` significant digits, exponents -300 to 300,
    written plain or in scientific notation, some with trailing zeros (`1.50`)."""
    generator = random.Random(seed)
    texts: list[str] = []
    for position in range(count):
        mantissa = str(generator.randrange(10 ** (digits - 1), 10**digits))
        sign = "-" if generator.random() < 0.5 else ""
        exponent = generator.randint(-300, 300) if position % 2 else generator.randint(-6, 6)
        if position % 2:
            texts.append(f"{sign}{mantissa[0]}.{mantissa[1:]}{'0' * (position % 3)}e{exponent}")
        else:
            point = len(mantissa) + exponent
            plain = mantissa.rjust(-exponent + 1, "0") if point <= 0 else mantissa + "0" * max(exponent, 0)
            at = max(point, 1)
            texts.append(f"{sign}{plain[:at]}.{plain[at:] or '0'}")
    return texts


def same_value(written: str, cell: str) -> bool:
    return Decimal(written) == Decimal(cell)


def spelling_lost(written: str, cell: str) -> bool:
    """Oracle for the spelling count: the canonical cell drops trailing fraction zeros, a plus sign or the notation;
    a whole number's fraction of zeros (`2.0` as `2`) is no loss (owner decision of 2026-10-15)."""
    mantissa, _, exponent = written.lower().partition("e")
    cell_mantissa, _, cell_exponent = cell.partition("e")
    zeros = mantissa.partition(".")[2]
    whole_zeros = bool(zeros) and not zeros.strip("0") and "." not in cell_mantissa
    return (
        bool(exponent) != bool(cell_exponent)
        or mantissa.startswith("+")
        or (not whole_zeros and zeros.endswith("0") and len(zeros) > len(cell_mantissa.partition(".")[2]))
    )


def canonical_number(text: str) -> str:
    """Oracle for a number cell's canonical text: the shortest round-trip `repr`, without `.0` for a whole number
    the float holds exactly below 2**53 (owner decision of 2026-10-15: `30` and `30.0` are the same number)."""
    value = float(text)
    shortest = repr(value)
    exact = Decimal(text) == Decimal(shortest)
    return shortest[:-2] if shortest.endswith(".0") and abs(value) < 2**53 and exact else shortest


def respelled_warning(count: int, columns: str = "v") -> list[str]:
    if not count:
        return []
    noun = "number" if count == 1 else "numbers"
    return [
        f"{count} {noun} {RESPELLED} (trailing zeros, exponent or plus sign dropped, such as 1.50 as 1.5 or 1e3 "
        f"as 1000) in {columns}"
    ]


class TestFidelity:
    """Owner rule of 2026-10-15: what the user pastes is what the data holds, or a warning says what changed."""

    @pytest.mark.parametrize("digits", [1, 7, 15])
    def test_numbers_of_up_to_15_digits_keep_their_exact_value_in_every_input_format(self, digits: int) -> None:
        texts = decimals(seed=digits, count=300, digits=digits)
        literal = "[" + ", ".join(texts) + "]"
        inputs = {
            "csv": "v\n" + "\n".join(texts) + "\n",
            "json": json.dumps({"v": [float(text) for text in texts]}),
            "written json": '{"v": ' + literal + "}",
            "python": "v = {'v': " + literal + "}",
        }
        for name, text in inputs.items():
            parsed = parse_dataset(text, find_table=False)
            canonical = parsed.csv.splitlines()[1:]
            assert parsed.column_dtypes == {"v": "number"}, name
            # The value, not the spelling: `1.50` is written `1.5`, `1.5e3` `1500.0` (shortest round-trip form),
            # and one warning counts the cells whose spelling went (owner decision of 2026-10-15).
            pasted = [repr(float(text)) for text in texts] if name == "json" else texts
            lost = sum(spelling_lost(written, cell) for written, cell in zip(pasted, canonical, strict=True))
            assert (lost > 0) == (name != "json"), name
            assert parsed.warnings == respelled_warning(lost), name
            assert all(same_value(written, cell) for written, cell in zip(texts, canonical, strict=True)), name
            assert canonical == [canonical_number(text) for text in texts], name
            assert read_back(parsed)["v"].tolist() == [float(text) for text in texts], name

    @pytest.mark.parametrize(
        "make",
        [
            lambda texts: "v\n" + "\n".join(texts) + "\n",
            lambda texts: '{"v": [' + ", ".join(texts) + "]}",
            lambda texts: "{'v': [" + ", ".join(texts) + "]}",
        ],
        ids=["csv", "json", "python"],
    )
    def test_more_digits_than_a_float_holds_are_rounded_with_a_warning_that_counts_them(self, make: Any) -> None:
        long = decimals(seed=19, count=40, digits=19)
        short = decimals(seed=3, count=10, digits=3)
        texts = [*long, *short, "9007199254740993", "-0.1234567890123456789"]
        parsed = parse_dataset(make(texts), find_table=False)
        canonical = parsed.csv.splitlines()[1:]

        lost = sum(not same_value(written, cell) for written, cell in zip(texts, canonical, strict=True))
        assert lost == 42  # 2 of the 40 random 19-digit numbers happen to fit; the two named ones never do
        respelled = sum(
            same_value(written, cell) and spelling_lost(written, cell)
            for written, cell in zip(texts, canonical, strict=True)
        )
        assert parsed.warnings == [
            f"column 'v': {lost} values with more significant digits than a number holds (15 to 17) "
            "are stored rounded to the nearest number",
            *respelled_warning(respelled),
        ]
        assert canonical == [canonical_number(text) for text in texts]  # the nearest float, never fewer digits

    def test_a_spelling_that_was_not_kept_is_counted_in_one_line(self) -> None:
        """Owner decision of 2026-10-15: the value is enough, but the user hears that the spelling went."""
        parsed = parse_dataset("a,b,c\n1.50,+3,2\n1e3,-0,.5\n2.0,4,1e-7\n")

        # `1.50`, `1e3`; `+3`, `-0`. What the canonical form only adds (`.5` as `0.5`, `1e-07`) is no loss, and
        # neither is a whole number's `.0` (`2.0` as `2`: the same number, owner decision of 2026-10-15).
        assert parsed.csv == "a,b,c\n1.5,3,2\n1000,0,0.5\n2,4,1e-07\n"
        assert parsed.warnings == respelled_warning(4, "a, b")

    def test_nanoseconds_beside_a_date_outside_1677_to_2262_stay_text_with_a_note(self) -> None:
        """pandas holds a nanosecond only between 1677 and 2262; the loader left such a column text silently."""
        nanos = parse_dataset("t,v\n1500-01-01T10:00:00.123456789,1\n2024-07-01T10:00:00,2\n")
        micros = parse_dataset("t,v\n1500-01-01T10:00:00.123456,1\n2024-07-01T10:00:00,2\n")

        assert nanos.column_dtypes["t"] == "text" and nanos.csv.splitlines()[1].startswith(
            "1500-01-01T10:00:00.123456789"
        )
        assert nanos.warnings == [f"column 't': {parse_module.NS_OUT_OF_RANGE}"]
        assert micros.column_dtypes["t"] == "datetime"
        assert pd.api.types.is_datetime64_any_dtype(read_back(micros)["t"])  # the loader's typing agrees

    def test_json_nan_and_infinity_are_counted_as_missing(self) -> None:
        parsed = parse_dataset('[{"a": 1.5, "b": NaN}, {"a": Infinity, "b": 2}, {"a": -Infinity, "b": 3}]')

        assert parsed.csv == "a,b\n1.5,\n,2\n,3\n"
        assert "3 values NaN, Infinity or -Infinity read as missing" in parsed.warnings

    def test_thousands_dots_past_int64_stay_text(self) -> None:
        """`_retype_thousands_dots` fell back to a float for a whole number past int64 (review of #12196)."""
        parsed = parse_dataset("a;b\n1,5;12.345.678.901.234.567.890.123\n2,5;1.234\n")

        assert parsed.column_dtypes["b"] == "text"
        assert parsed.csv == "a,b\n1.5,12.345.678.901.234.567.890.123\n2.5,1.234\n"
        assert f"column 'b': {parse_module.BIG_INTEGERS}" in parsed.warnings

    def test_the_missing_token_note_says_how_many_other_tokens_there_are(self) -> None:
        parsed = parse_dataset("k,c\n1,a\n2,None\n3,-\n4,null\n5,n/a\n6,NULL\n")

        assert warned(parsed, "column 'c': 5 cells read as missing (")
        assert warned(parsed, " and 2 other tokens)")

    def test_a_subnormal_or_underflowing_number_is_warned_too(self) -> None:
        parsed = parse_dataset("v\n1.2345678901e-320\n1e-400\n5e-324\n0.000\n")

        assert parsed.csv == "v\n1.2347e-320\n0.0\n5e-324\n0\n"  # `1e-400` rounded to 0 keeps the `.0` that shows it
        assert warned(parsed, "column 'v': 2 values with more significant digits")

    def test_whole_numbers_are_exact_to_the_int64_limits_and_text_beyond(self) -> None:
        inside = ["9007199254740993", "-9223372036854775808", "9223372036854775807", "12"]
        parsed = parse_dataset("id\n" + "\n".join(inside) + "\n")
        beyond = parse_dataset("id,v\n12345678901234567890123,1\n7,2\n")

        assert parsed.column_dtypes == {"id": "integer"} and parsed.csv.splitlines()[1:] == inside
        assert read_back(parsed)["id"].tolist() == [int(text) for text in inside]
        assert column(parsed, "id").min == -(2**63) and column(parsed, "id").max == 2**63 - 1
        assert beyond.column_dtypes["id"] == "text"
        assert beyond.csv == "id,v\n12345678901234567890123,1\n7,2\n"
        assert beyond.warnings == [
            "column 'id': whole numbers beyond the 64-bit range kept as text, so no digit is lost"
        ]
        # From JSON as well: Python reads the integer exactly, the typing keeps it.
        assert parse_dataset('{"id": [12345678901234567890123, 7]}').column_dtypes["id"] == "text"

    def test_a_whole_number_past_2_53_beside_decimals_is_warned(self) -> None:
        parsed = parse_dataset("v\n9007199254740993\n1.5\n")

        assert parsed.csv == "v\n9007199254740992.0\n1.5\n"
        assert warned(parsed, "column 'v': 1 value with more significant digits than a number holds")

    def test_grouped_and_decimal_comma_numbers_keep_every_digit(self) -> None:
        parsed = parse_dataset("a;b\n1.234.567,890123;7.184.003\n2,5;12.000.000\n")

        assert parsed.csv == "a,b\n1234567.890123,7184003\n2.5,12000000\n"
        assert parsed.column_dtypes == {"a": "number", "b": "integer"}
        assert not warned(parsed, "rounded")

    def test_text_cells_keep_every_character_or_a_warning_counts_the_change(self) -> None:
        parsed = parse_dataset(f"k,c\n1,b \n2,a\n3,None\n4,-\n5,cafe{ACUTE}\n")

        assert parsed.csv == f"k,c\n1,b\n2,a\n3,\n4,\n5,caf{E_ACUTE}\n"
        assert parsed.warnings == [
            "1 line held decomposed characters (such as e and a separate accent), now written in Unicode's "
            "composed form (NFC); the text reads the same",
            "column 'c': spaces around the text removed in 1 cell",
            "column 'c': 2 cells read as missing ('None', '-')",
        ]

    def test_missing_marks_in_number_columns_are_counted_like_in_text_columns(self) -> None:
        """Live test round 5 of 2026-10-15: `NA` in `sex` was said, the same `NA` in `body_mass_g` was not."""
        numbers = parse_dataset("k,v,d\na,1,2024-01-01\nb,-,NA\nc,n/a,2024-01-03\n")

        assert numbers.column_dtypes == {"k": "text", "v": "integer", "d": "datetime"}
        assert numbers.warnings == [
            "column 'v': 2 cells read as missing ('-', 'n/a')",
            "column 'd': 1 cell read as missing ('NA')",
        ]

    def test_the_padding_of_aligned_tables_needs_no_warning(self) -> None:
        aligned = parse_dataset("Ort        Wert\nZürich     1\nBern       2\nBasel      3\n")

        assert aligned.csv == "Ort,Wert\nZürich,1\nBern,2\nBasel,3\n" and aligned.warnings == []

    def test_a_whole_number_beside_decimals_is_written_without_dot_zero(self) -> None:
        """Live test round 5 of 2026-10-15: Excel's `87000` beside `120500.5` showed as `87000.0`. Owner decision of
        that day: a whole number is written without `.0` whatever form it came in, and needs no note."""
        parsed = parse_dataset("Filiale,Umsatz\nZürich,120500.5\nBasel,87000\nBern,2.0\n")

        assert parsed.column_dtypes["Umsatz"] == "number"
        assert parsed.csv.splitlines()[1:] == ["Zürich,120500.5", "Basel,87000", "Bern,2"]
        assert parsed.warnings == []
        assert read_back(parsed)["Umsatz"].tolist() == [120500.5, 87000.0, 2.0]
        # The canonical CSV reads back the same: the form survives every later version's re-parse.
        assert parse_dataset(parsed.csv, find_table=False, canonical=True).csv == parsed.csv

    def test_json_floats_that_overflow_stay_text_instead_of_vanishing(self) -> None:
        parsed = parse_dataset('[{"a": 1e400, "b": 1}, {"a": 2, "b": 2}]')

        assert parsed.column_dtypes["a"] == "text" and parsed.csv == "a,b\n1e400,1\n2,2\n"

    def test_a_python_literal_keeps_complex_numbers_and_underscores_as_python_reads_them(self) -> None:
        assert parse_dataset("{'v': [1_000.5, 2.25]}").csv == "v\n1000.5\n2.25\n"
        assert error_code("{'v': [1.5+2j, 2.0]}") == "unparseable"

    def test_digit_separators_do_not_hide_digits_from_the_rounding_count(self) -> None:
        parsed = parse_dataset("{'v': [0.123_456_789_012_345_678_9, 2.25]}")

        assert parsed.csv == "v\n0.12345678901234568\n2.25\n"
        assert warned(parsed, "column 'v': 1 value with more significant digits")

    def test_float_texts_follow_every_line_break_and_non_ascii_text(self) -> None:
        text = "{'k': ['Zürich', 'Genève'],\r\n 'v': [0.1234567890123456789,\r -1.5]}"
        parsed = parse_dataset(text)

        assert parsed.csv == "k,v\nZürich,0.12345678901234568\nGenève,-1.5\n"
        assert warned(parsed, "column 'v': 1 value with more significant digits")

    def test_a_literal_of_many_floats_parses_in_linear_time(self) -> None:
        """`ast.get_source_segment` per float was quadratic (review of #12196): 20,000 floats on one line each."""
        values = decimals(seed=7, count=20_000, digits=9)
        started = time.perf_counter()
        parsed = parse_dataset("v = {'v': [\n" + ",\n".join(values) + "\n]}")

        assert parsed.profile.rows == 20_000 and not warned(parsed, "rounded")
        assert time.perf_counter() - started < 10


class TestPreciseTimestamps:
    """Owner rule of 2026-10-15: ISO timestamps keep every fraction digit and their UTC offset, typed as datetimes."""

    @staticmethod
    def column(text: str) -> tuple[str, list[str], Any]:
        parsed = parse_dataset(text)
        frame = pd.read_csv(
            io.StringIO(parsed.csv), dtype=pandas_dtypes(parsed.column_dtypes), parse_dates=parsed.parse_dates
        )
        cells = [row.split(",")[0] for row in parsed.csv.splitlines()[1:]]
        return parsed.column_dtypes["t"], cells, frame["t"]

    def test_nanoseconds_and_an_offset_round_trip_exactly(self) -> None:
        dtype, cells, loaded = self.column("t,v\n2024-01-01 10:00:00.123456789+01:00,1\n2024-01-01T10:00:01.5+0100,2\n")
        assert dtype == "datetime"
        assert cells == ["2024-01-01T10:00:00.123456789+01:00", "2024-01-01T10:00:01.500000000+01:00"]
        assert str(loaded.dtype) == "datetime64[ns, UTC+01:00]"
        assert loaded[0] == pd.Timestamp("2024-01-01T10:00:00.123456789+01:00")

    def test_z_is_utc_and_naive_fractions_stay_naive(self) -> None:
        assert self.column("t\n2024-01-01T10:00:00Z\n")[1] == ["2024-01-01T10:00:00+00:00"]
        dtype, cells, loaded = self.column("t\n2024-01-01T10:00:00.25\n2024-01-01T10:00:00\n")
        assert cells == ["2024-01-01T10:00:00.25", "2024-01-01T10:00:00.00"] and loaded.dt.tz is None
        assert loaded[0] == pd.Timestamp("2024-01-01T10:00:00.25")

    def test_several_offsets_are_written_in_utc_and_said(self) -> None:
        parsed = parse_dataset("t,v\n2024-01-01T10:00:00+01:00,1\n2024-07-01T10:00:00+02:00,2\n")
        assert parsed.csv.splitlines()[1:] == ["2024-01-01T09:00:00+00:00,1", "2024-07-01T08:00:00+00:00,2"]
        assert any("+01:00, +02:00 written in UTC" in warning for warning in parsed.warnings)

    def test_cells_with_and_without_an_offset_are_no_date_column(self) -> None:
        assert parse_dataset("t\n2024-01-01T10:00:00+01:00\n2024-01-02T10:00:00\n").column_dtypes["t"] == "text"

    def test_the_profile_names_the_exact_extremes(self) -> None:
        profile = parse_dataset("t\n2024-01-01T10:00:00.000000002\n2024-01-01T10:00:00.000000001\n").profile
        (column,) = profile.columns
        assert (column.min, column.max) == ("2024-01-01T10:00:00.000000001", "2024-01-01T10:00:00.000000002")

    def test_plain_dates_and_minutes_are_written_as_before(self) -> None:
        assert self.column("t\n2024-01-05\n2024-02-03\n")[1] == ["2024-01-05", "2024-02-03"]
        assert self.column("t\n2024-01-05 10:30\n2024-02-03\n")[1] == ["2024-01-05T10:30:00", "2024-02-03T00:00:00"]


# Live test round 5 of 2026-10-15, generalised: a report sheet (`Filialen_2025.xlsx`, sheet ‹Bericht›) as the
# converter writes it, a title, a revenue table, a blank row, a caption and a staff table. Synthetic values.
REPORT = (
    "Branch report 2025 - internal\n"
    "\n"
    "Branch,Revenue Q1 (CHF),Revenue Q2 (CHF)\n"
    "North,120500.5,130100\n"
    "South,98200.25,101500.5\n"
    "East,87000,90500\n"
    "\n"
    "Staff and floor space\n"
    "Branch,Staff,Floor (m²)\n"
    "North,24,450\n"
    "South,18,380\n"
    "East,15,300\n"
)


class TestTables:
    """A paste with several tables, each under its own header after a blank line (`_one_table`)."""

    def test_the_first_table_is_read_and_the_others_are_named(self) -> None:
        parsed = parse_dataset(REPORT)

        assert parsed.csv == (
            "Branch,Revenue Q1 (CHF),Revenue Q2 (CHF)\nNorth,120500.5,130100\nSouth,98200.25,101500.5\nEast,87000,90500\n"
        )
        assert parsed.column_dtypes == {"Branch": "text", "Revenue Q1 (CHF)": "number", "Revenue Q2 (CHF)": "number"}
        assert parsed.tables == [
            "Branch, Revenue Q1 (CHF), Revenue Q2 (CHF) · 3 rows",
            "Branch, Staff, Floor (m²) · 3 rows",
        ]
        assert parsed.table == 1
        assert parsed.warnings[0] == (
            "the data holds 2 tables, each under its own header; read table 1 (Branch, Revenue Q1 (CHF), Revenue Q2 "
            "(CHF) · 3 rows) and left out table 2 (Branch, Staff, Floor (m²) · 3 rows); the table picker in the data "
            "panel reads another one"
        )
        assert parsed.context_lines == ["Branch report 2025 - internal"]

    def test_the_second_table_keeps_the_title_and_its_caption_as_notes(self) -> None:
        parsed = parse_dataset(REPORT, table=2)

        assert parsed.csv == "Branch,Staff,Floor (m²)\nNorth,24,450\nSouth,18,380\nEast,15,300\n"
        assert parsed.column_dtypes["Staff"] == "integer"
        assert parsed.table == 2 and len(parsed.tables) == 2
        assert "read table 2 (Branch, Staff, Floor (m²) · 3 rows) and left out table 1" in parsed.warnings[0]
        assert parsed.context_lines == ["Branch report 2025 - internal", "Staff and floor space"]

    def test_a_table_number_past_the_tables_is_refused(self) -> None:
        with pytest.raises(ParseError) as many:
            parse_dataset(REPORT, table=3)
        with pytest.raises(ParseError) as one:
            parse_dataset("a,b\nx,1\ny,2\n", table=2)
        with pytest.raises(ParseError) as literal:
            parse_dataset('[{"a": 1}, {"a": 2}]', table=2)

        assert many.value.code == one.value.code == literal.value.code == "unparseable"
        assert "holds 2 tables" in many.value.message

    def test_pasted_semicolon_tables_with_another_width_split_too(self) -> None:
        text = (
            "Jahr;Wert\n2023;1,5\n2024;2,5\n\nRegion;Jahr;Anteil;Notiz\nNord;2024;12;a\nSüd;2024;13;b\nWest;2024;9;c\n"
        )
        first = parse_dataset(text)
        second = parse_dataset(text, table=2)

        assert first.csv == "Jahr,Wert\n2023,1.5\n2024,2.5\n"
        assert second.csv.splitlines()[0] == "Region,Jahr,Anteil,Notiz" and second.profile.rows == 3
        assert first.tables == second.tables

    @pytest.mark.parametrize(
        "text",
        [
            # One table with a blank line inside: the rows after it have no header of their own.
            "a,b\nx,1\ny,2\n\nz,3\nw,4\n",
            # An export's metadata of one row above the table (Open-Meteo): no table of its own.
            "latitude,longitude,elevation\n47.37,8.55,408.0\n\ntime,temperature\n2024-01-01T00:00,1.5\n"
            "2024-01-01T01:00,1.2\n2024-01-01T02:00,1.1\n",
            # A key-value block above the table.
            "Station:,Zürich\nHöhe:,556\nBreite:,47.37\n\nJahr,Wert\n2023,1\n2024,2\n",
            # Notes below the table.
            "a,b\nx,1\ny,2\n\nSource: somewhere, 2024\n",
            # A text-only block below a table.
            "a,b\nx,1\ny,2\n\nName,Role\nAnna,Lead\nBen,Dev\n",
        ],
    )
    def test_text_with_one_table_stays_one_table(self, text: str) -> None:
        parsed = parse_dataset(text)

        assert parsed.tables == [] and parsed.table == 1
        assert not any("tables" in warning for warning in parsed.warnings)

    def test_a_confirmed_or_computed_table_is_never_split(self) -> None:
        text = REPORT.split("\n", 2)[2]  # from the first header on: a confirmed table keeps every row
        parsed = parse_dataset(text, find_table=False)

        assert parsed.tables == [] and parsed.profile.rows == 8

    def test_a_year_header_starts_a_table(self) -> None:
        text = "Land,2020,2021\nCH,1,2\nDE,3,4\n\nLand,Hauptstadt\nCH,Bern\nDE,Berlin\n"
        assert parse_dataset(text).tables == []  # the second table holds no value: it is no table of its own
        text = "Land,Hauptstadt,Fläche\nCH,Bern,41285\nDE,Berlin,357588\n\nLand,2020,2021\nCH,1,2\nDE,3,4\n"
        assert parse_dataset(text, table=2).csv == "Land,2020,2021\nCH,1,2\nDE,3,4\n"

    @pytest.mark.parametrize(
        "text",
        [
            # Fable and Gemini review of #12200: a blank row inside one table, then a row that looks like a header.
            "City,1900,1950,2000\nZürich,150,390,363\nGeneva,97,145,177\n\nBern,1500,1850,2040\nBasel,110,183,166\n"
            "Luzern,29,60,57\n",
            "Land,Gründung,Beitritt\nFrance,1789,1958\nItaly,1861,1958\n\nSwitzerland,1848,2002\nAustria,1918,1995\n"
            "Norway,1905,1994\n",
            "Name,Start,End\nAlpha,2019,2020\nBeta,2020,2022\n\nGamma,2021,2023\nDelta,2022,2024\nEpsilon,2023,2025\n",
            # A row of text in a table of text.
            "Feature,Plan,Note\nStorage,Basic,yes\nBackup,Pro,no\n\nSupport,Service,Included\nTraining,Pro,1\n"
            "Hosting,Basic,2\n",
        ],
    )
    def test_a_blank_row_inside_one_table_never_splits_it(self, text: str) -> None:
        parsed = parse_dataset(text)

        assert parsed.tables == []
        assert not any("tables" in warning for warning in parsed.warnings)

    @pytest.mark.parametrize("title", ["", "Report 2025\n"])
    def test_a_header_of_text_over_numbers_is_never_joined_silently(self, title: str) -> None:
        """Fable review of #12200: joined, `Produkt,Menge` made `Umsatz` text without a word."""
        text = title + "Region,Umsatz\nNord,10\nSüd,20\nOst,30\n\nProdukt,Menge\nA,1\nB,2\nC,3\n"
        first = parse_dataset(text)
        second = parse_dataset(text, table=2)

        assert first.column_dtypes == {"Region": "text", "Umsatz": "integer"}
        assert first.csv == "Region,Umsatz\nNord,10\nSüd,20\nOst,30\n"
        assert second.column_dtypes == {"Produkt": "text", "Menge": "integer"}
        assert first.warnings[0].startswith("the data holds 2 tables")

    def test_an_ambiguous_text_row_over_numbers_splits_with_a_warning(self) -> None:
        """A split is said in a warning that names both tables; a join would change a column's type silently."""
        text = "Feature,Plan,Price\nStorage,Basic,10\nBackup,Pro,20\n\nSupport,Service,Included\nTraining,Pro,30\n"
        parsed = parse_dataset(text + "Hosting,Basic,15\n")

        assert parsed.column_dtypes["Price"] == "integer"
        assert "table 2 (Support, Service, Included · 2 rows)" in parsed.warnings[0]

    def test_years_of_a_header_run_one_way(self) -> None:
        assert not parse_module._header_line(["Bern", "2040", "1850", "2001"])
        assert parse_module._header_line(["Land", "2020", "2021"])
        assert parse_module._header_line(["Land", "2025", "2024", "2023"])  # finance writes the latest first

    def test_a_descending_year_header_starts_a_table(self) -> None:
        text = "Land,Hauptstadt,Fläche\nCH,Bern,41285\nDE,Berlin,357588\n\nLand,2021,2020\nCH,1,2\nDE,3,4\n"
        assert parse_dataset(text, table=2).csv == "Land,2021,2020\nCH,1,2\nDE,3,4\n"
        captioned = text.replace("\n\nLand,2021", "\n\nPer year\nLand,2021")
        assert parse_dataset(captioned, table=2).csv == "Land,2021,2020\nCH,1,2\nDE,3,4\n"

    def test_a_later_table_never_meets_the_lines_above_the_first_one(self) -> None:
        """Gemini review of #12200: an export's metadata above the first table must not become the second's rows,
        and the first table's own caption is no note of the second."""
        text = (
            "latitude,longitude,elevation\n47.37,8.55,408\n\nRevenue\nBranch,Q1,Q2\nNorth,1.5,2.5\nSouth,3.5,4.5\n\n"
            "Staff\nBranch,Staff,Floor\nNorth,24,450\nSouth,18,380\n"
        )
        first = parse_dataset(text)
        second = parse_dataset(text, table=2)

        assert first.csv == "Branch,Q1,Q2\nNorth,1.5,2.5\nSouth,3.5,4.5\n"
        assert first.tables == ["Branch, Q1, Q2 · 2 rows", "Branch, Staff, Floor · 2 rows"]
        assert first.context_lines == ["latitude, longitude, elevation", "47.37, 8.55, 408", "Revenue"]
        assert second.csv == "Branch,Staff,Floor\nNorth,24,450\nSouth,18,380\n"
        assert second.context_lines == ["latitude, longitude, elevation", "47.37, 8.55, 408", "Staff"]
        assert "left out 3 lines above the table (a title, notes or metadata)" in second.warnings

    def test_a_table_number_below_one_is_a_callers_error(self) -> None:
        with pytest.raises(ValueError):
            parse_dataset(REPORT, table=0)

    def test_tables_past_the_cap_keep_their_boundaries(self) -> None:
        """Copilot review of #12200: the eleventh table had joined the tenth, its header a data row."""
        text = "\n".join(f"a,b\nx{n},{n}\ny{n},{n + 0.5}\n" for n in range(11))
        tenth = parse_dataset(text, table=10)

        assert tenth.csv == "a,b\nx9,9\ny9,9.5\n"
        assert len(tenth.tables) == 10
        assert tenth.warnings[0].startswith("the data holds 11 tables, each under its own header; read table 10")
        assert "and 7 other tables;" in tenth.warnings[0]  # 3 named of the 10 left out
        with pytest.raises(ParseError):
            parse_dataset(text, table=11)


# Live test round 5 of 2026-10-15, generalised: R's `write.csv` writes the row names first under an empty header.
R_EXPORT = (
    '"","species","bill_length_mm","body_mass_g","sex"\n'
    '"1","Adelie",39.1,3750,"male"\n'
    '"2","Gentoo",NA,NA,NA\n'
    '"3","Chinstrap",40.0,3800,"female"\n'
)


class TestRowNames:
    def test_r_row_names_leave_the_table_with_a_warning(self) -> None:
        parsed = parse_dataset(R_EXPORT)

        assert list(parsed.column_dtypes) == ["species", "bill_length_mm", "body_mass_g", "sex"]
        assert parsed.warnings == [
            "left out the column without a header: its 3 cells only number the rows 1 to 3 in order, as R's "
            "write.csv or pandas' index write row names",
            "column 'bill_length_mm': 1 cell read as missing ('NA')",
            "column 'body_mass_g': 1 cell read as missing ('NA')",
            "column 'sex': 1 cell read as missing ('NA')",
        ]
        assert parsed.csv.splitlines()[1] == "Adelie,39.1,3750,male"
        assert parsed.csv.splitlines()[3] == "Chinstrap,40,3800,female"  # the same number as `40.0`

    def test_the_row_names_never_become_the_default_x(self) -> None:
        bindings = {
            binding.role: binding.column for binding in default_bindings(XY_ROLES, parse_dataset(R_EXPORT).profile)
        }

        assert bindings["x"] != "column_1" and "column_1" not in bindings.values()

    @pytest.mark.parametrize(
        ("header", "start"),
        [("", 1), ("...1", 1), ("Unnamed: 0", 0)],  # R and readr from 1, pandas' index from 0
    )
    def test_each_tools_exact_shape_leaves(self, header: str, start: int) -> None:
        rows = "".join(f"{start + n},{letter},{n + 1.5}\n" for n, letter in enumerate("xyz"))
        parsed = parse_dataset(f'"{header}",a,b\n{rows}')

        assert list(parsed.column_dtypes) == ["a", "b"]
        assert f"the rows {start} to {start + 2} in order" in parsed.warnings[0]
        named = f"'{header}'" if header else "without a header"
        assert parsed.warnings[0].startswith(f"left out the column {named}:")

    @pytest.mark.parametrize(
        "text",
        [
            '"",a\n3,x\n7,y\n12,z\n',  # row names after a filter: data
            '"",a\nMazda RX4,1\nDatsun 710,2\n',  # row names that are names
            '"",a\n0,x\n1,y\n2,z\n',  # an empty header from 0: maybe a step column (review of #12200)
            '"Unnamed: 0",a\n1,x\n2,y\n',  # pandas counts from 0
            "X,a\n1,x\n2,y\n",  # R's `read.csv` name: kept, but never a default binding
            "index,a\n0,x\n1,y\n",
            '"",a\n1,x\n',  # one row: no evidence of an order
            '"",a\n01,x\n02,y\n',  # zero-padded: a code, not a position
            "a,\nx,1\ny,2\n",  # an empty header that is not the first column
            ',"",a\n,1,x\n,2,y\n',  # not the text's own first column: an empty one went before it
        ],
    )
    def test_anything_else_stays_a_column(self, text: str) -> None:
        parsed = parse_dataset(text)

        assert not any("number the rows" in warning for warning in parsed.warnings)
        assert len(parsed.column_dtypes) == 2

    def test_a_canonical_re_parse_or_a_confirmed_transcription_keeps_every_column(self) -> None:
        canonical = parse_dataset('"",a\n1,x\n2,y\n', canonical=True, find_table=False)
        confirmed = parse_dataset('"",a\n1,x\n2,y\n', find_table=False)

        assert list(canonical.column_dtypes) == list(confirmed.column_dtypes) == ["column_1", "a"]

    @pytest.mark.parametrize(
        "text",
        [
            "X,height,weight\n1,170,65.5\n2,182,80.1\n3,165,58.0\n",  # R's `read.csv` of a `write.csv` file
            '"",height,weight\n0,170,65.5\n1,182,80.1\n2,165,58.0\n',  # pandas' `to_csv` with its index
        ],
    )
    def test_kept_row_numbers_take_no_default_binding_while_another_column_fits(self, text: str) -> None:
        """Owner decision of 2026-10-15: the column stays, but x is a measure, never the row number."""
        parsed = parse_dataset(text)
        bindings = {binding.role: binding.column for binding in default_bindings(XY_ROLES, parsed.profile)}

        assert len(parsed.column_dtypes) == 3
        assert bindings == {"x": "height", "y": "weight"}

    @pytest.mark.parametrize(
        ("text", "expected"),
        [
            ("X,weight\n1,65.5\n2,80.1\n3,58.0\n", {"x": "X", "y": "weight"}),
            ("index,value\n0,65.5\n1,80.1\n2,58.0\n", {"x": "index", "y": "value"}),
            ('"",v\n0,65.5\n1,80.1\n2,58.0\n', {"x": "column_1", "y": "v"}),
            ("X,Y\n1,65.5\n2,80.1\n3,58.0\n", {"x": "X", "y": "Y"}),
            # Another column fits x, so `X` takes none; `Y` is y by its name.
            ("X,Y,Z\n1,65.5,3.5\n2,80.1,4.5\n3,58.0,5.5\n", {"x": "Z", "y": "Y"}),
        ],
    )
    def test_row_numbers_keep_their_natural_slot_when_the_roles_need_them(
        self, text: str, expected: dict[str, str]
    ) -> None:
        """Fable review of #12200: decided per role set, so `X, weight` is never transposed into x = weight."""
        parsed = parse_dataset(text)
        bindings = {binding.role: binding.column for binding in default_bindings(XY_ROLES, parsed.profile)}

        assert bindings == expected


EVENTS_NDJSON = (
    '{"ts": "2026-10-01T09:14:00Z", "service": "worker", "latency_ms": 40.6, "status": 200}\n'
    '{"ts": "2026-10-01T10:43:00Z", "service": "worker", "latency_ms": 250.40, "status": 200}\n'
    "\n"
    '{"ts": "2026-10-01T10:59:00.125Z", "service": "web", "latency_ms": 85.5, "status": 503}\n'
)


class TestJsonLines:
    """Live round 6 (R6-2): `events.ndjson`, one JSON object per line, was refused as unreadable."""

    def test_json_lines_read_as_records_with_every_value(self) -> None:
        parsed = parse_dataset(EVENTS_NDJSON)

        assert parsed.profile.source_format == "json_lines"
        assert [column.name for column in parsed.profile.columns] == ["ts", "service", "latency_ms", "status"]
        assert parsed.profile.rows == 3
        rows = list(csv_rows(parsed.csv))[1:]
        assert [row[1:] for row in rows] == [
            ["worker", "40.6", "200"],
            ["worker", "250.4", "200"],
            ["web", "85.5", "503"],
        ]
        assert rows[2][0].startswith("2026-10-01T10:59:00.125")  # the milliseconds stay
        assert warned(parsed, "trailing zeros")  # 250.40 -> 250.4 is said, as in a JSON array

    def test_a_broken_line_is_named_with_the_json_error(self) -> None:
        text = '{"a": 1}\n{"a": 2}\n{"a": 3,}\n'
        with pytest.raises(ParseError) as caught:
            parse_dataset(text)

        assert caught.value.code == "unparseable"
        assert caught.value.message.startswith(
            "the data reads as JSON Lines (one JSON object per line), but line 3 is not valid JSON: "
        )
        assert caught.value.message.endswith("trailing comma before end of object at column 8")

    def test_the_column_of_a_json_error_counts_the_lines_leading_spaces(self) -> None:
        """Copilot review of #12201: the column is the one in the paste, indentation included."""
        with pytest.raises(ParseError) as caught:
            parse_dataset('{"a": 1, "b": 2}\n    {"a": 2 "b": 3}\n')

        assert caught.value.message.endswith("line 2 is not valid JSON: Expecting ',' delimiter at column 13")

    def test_a_lone_surrogate_in_a_named_column_list_is_refused_as_text(self) -> None:
        """Copilot review of #12201: a refusal's message is always valid text, never a 500 on encoding."""
        with pytest.raises(ParseError) as caught:
            parse_dataset('{"\\ud800": [1, 2], "b": [1]}')

        caught.value.message.encode("utf-8")  # raises when a surrogate slipped into the message

    def test_a_line_that_holds_no_object_is_named(self) -> None:
        with pytest.raises(ParseError, match="line 2 holds an array of 2 values instead of an object"):
            parse_dataset('{"a": 1}\n[1, 2]\n')

    def test_repeated_keys_and_nan_are_counted_as_in_json(self) -> None:
        parsed = parse_dataset('{"a": 1, "a": 2, "b": NaN}\n{"a": 3, "b": 4}\n')

        assert warned(parsed, "1 key repeated") and warned(parsed, "1 value NaN, Infinity or -Infinity")

    def test_json_lines_below_a_title_keep_the_title_as_notes(self) -> None:
        """Fable review of #12201: under a title line, JSON Lines had read as one text column of JSON."""
        parsed = parse_dataset('Export 2026\n# source: a log\n{"a": 1, "b": 2}\n{"a": 2, "b": 3}\n')

        assert (parsed.profile.source_format, parsed.profile.rows) == ("json_lines", 2)
        assert parsed.context_lines == ["Export 2026", "# source: a log"]
        assert warned(parsed, "left out 2 lines above the table")

    def test_a_broken_line_below_a_title_is_named(self) -> None:
        with pytest.raises(ParseError, match="line 3 is not valid JSON: Expecting ',' delimiter at column 9"):
            parse_dataset('Export 2026\n{"a": 1, "b": 2}\n{"a": 2 "b": 3}\n')

    def test_a_table_with_a_json_cell_stays_a_table(self) -> None:
        assert parse_dataset('a,b\n{"x":1},2\n3,4\n').profile.source_format == "csv"

    def test_a_dropped_jsonl_file_of_one_record_is_one_row(self) -> None:
        """Gemini review of #12201: a one-line `.jsonl` file is one record, not category/value pairs."""
        parsed = parse_dataset('{"city": "Berlin", "pop": 3.7}\n', json_lines=True)

        assert (parsed.profile.source_format, parsed.profile.rows) == ("json_lines", 1)
        assert [column.name for column in parsed.profile.columns] == ["city", "pop"]

    def test_a_pasted_object_of_mixed_values_stays_pairs_and_says_so(self) -> None:
        mixed = parse_dataset('{"city": "Berlin", "pop": 3.7}')
        counts = parse_dataset('{"Hund": 7, "Katze": 3}')

        assert (mixed.profile.source_format, mixed.profile.rows) == ("json_pairs", 2)
        assert warned(mixed, "read as 2 category/value pairs, one row per key; to read it as one row")
        assert counts.warnings == []  # one kind of value: the pair reading is the plain one

    def test_a_first_line_that_is_no_object_is_no_json_lines(self) -> None:
        """Two arrays on two lines stay a refusal of JSON, which names the JSON error."""
        with pytest.raises(ParseError, match=r"not valid JSON: Extra data at line 2, column 1"):
            parse_dataset("[1, 2]\n[3, 4]\n")


def csv_rows(text: str) -> list[list[str]]:
    import csv

    return list(csv.reader(io.StringIO(text)))


class TestRefusalsNameTheirCause:
    """Owner rule of 2026-10-16: a refused paste says what it fails on (live round 6, R6-3)."""

    def test_ragged_rows_name_every_line_and_its_field_count(self) -> None:
        text = "Monat,Besucher,Umsatz\nJan,1200,5400\nFeb,1350,6100,Notiz: Aktion\nMär,1100\nApr,1500,7200\n"
        with pytest.raises(ParseError) as caught:
            parse_dataset(text)

        assert caught.value.code == "unparseable"
        assert caught.value.message == (
            "the header has 3 fields, but line 3 has 4; line 4 has 2; a value that holds a comma needs quotes around it"
        )

    def test_many_ragged_lines_are_grouped_and_counted(self) -> None:
        text = "a,b\n" + "".join(f"{i},{i},{i}\n" for i in range(12))
        with pytest.raises(ParseError) as caught:
            parse_dataset(text)

        assert caught.value.message.startswith("the header has 2 fields, but lines 2, 3, 4, 5, 6 and 7 more have 3")

    def test_trailing_empty_fields_are_left_out_with_a_count(self) -> None:
        parsed = parse_dataset("Monat,Besucher\nJan,1200,,\nFeb,1350\nMär,1100,\n")

        assert parsed.csv == "Monat,Besucher\nJan,1200\nFeb,1350\nMär,1100\n"
        assert warned(parsed, "2 rows had empty fields past the header's 2 columns; those empty fields were left out")

    def test_short_rows_name_their_lines(self) -> None:
        parsed = parse_dataset("a,b,c\n1,2,3\n4,5\n6,7,8\n9,10,11\n")

        assert warned(parsed, "1 row had fewer fields than the header; the missing cells are empty (line 3)")

    @pytest.mark.parametrize(
        ("text", "fragment"),
        [
            # The end of the input is the paste's line 2 (its trailing line break counts).
            ('[{"a": 1}, {"a": 2}\n', "not valid JSON: Expecting ',' delimiter at line 2, column 1"),
            ('data = {"a": [1, 2}\n', "is not one: closing parenthesis '}' does not match opening parenthesis '['"),
            # Review of #12201: positions count from the paste's own first line, indentation included.
            ('\n\n{"a": 1,\n"b"}', "Expecting ':' delimiter at line 4, column 4"),
            ('\n\n    {"a": 1 "b": 2}\n', "Expecting ',' delimiter at line 3, column 13; a comma is missing"),
            ('\n\ndata = {"a": [1, 2}', "does not match opening parenthesis '[' on line 3"),
            # JSON that Python reads as names (`true`, `null`, unquoted keys) gets the JSON error, never "a call".
            ('[{"a": true}, {"a": false},]', "not valid JSON: Illegal trailing comma before end of array"),
            ("{a: 1, b: 2}", "at line 1, column 2; JSON writes every key in double quotes"),
            ('{"a": null},\n{"a": 1}', "Extra data at line 1, column 12; for one object per line (JSON Lines) leave"),
            ('{"a": open("x")}\n', "holds a name, a call or an operation, which is never run"),
            ('[{"a": 1}, 7]\n', "item 2 is a number"),
            ('{"a": [1, 2], "b": [1]}\n', "the column lists have different lengths (a (2), b (1))"),
            ('a,b\n"x,1\n', "the quoting is malformed near line 2"),
        ],
    )
    def test_each_refusal_names_where(self, text: str, fragment: str) -> None:
        with pytest.raises(ParseError) as caught:
            parse_dataset(text)

        assert fragment in caught.value.message

    def test_a_long_cell_names_its_row_and_length(self) -> None:
        cell = "x" * (MAX_INPUT_CELL_CHARS + 5)
        with pytest.raises(ParseError) as caught:
            parse_dataset(f"name,v\nok,1\n{cell},2\n")

        assert caught.value.message == (
            f"the cell in row 2 of column 'name' has {MAX_INPUT_CELL_CHARS + 5:,} characters; "
            f"at most {MAX_INPUT_CELL_CHARS} are read"
        )


class TestHeaderlessList:
    """A pasted list of values without a header line keeps its first value (owner rule: no silent value change)."""

    def test_the_first_number_is_a_row_and_the_column_is_named(self) -> None:
        parsed = parse_dataset("12\n15\n17\n9\n")

        assert [(column.name, column.dtype) for column in parsed.profile.columns] == [(LIST_COLUMN_NAME, "integer")]
        assert parsed.csv == "value\n12\n15\n17\n9\n"
        assert parsed.warnings == [HEADERLESS_LIST_WARNING]
        assert "every header looks like a value" not in " ".join(parsed.warnings)

    def test_dates_and_unit_values_keep_their_first_line_too(self) -> None:
        dates = parse_dataset("2024-01-01\n2024-02-01\n2024-03-05\n")
        weights = parse_dataset("5 kg\n7 kg\n3 kg\n")

        assert (dates.profile.columns[0].dtype, dates.profile.rows) == ("datetime", 3)
        assert (weights.profile.columns[0].name, weights.profile.rows) == ("value (kg)", 3)
        assert weights.csv == "value (kg)\n5\n7\n3\n" and weights.warnings[0] == HEADERLESS_LIST_WARNING

    @pytest.mark.parametrize(
        ("text", "first"),
        [
            pytest.param("007\n12\n15\n", "007", id="a-leading-zero"),  # the column stays text to keep the zeros
            pytest.param("123456789012345678901234567890\n12\n15\n", "123456789012345678901234567890", id="past-int64"),
            pytest.param("true\nfalse\ntrue\n", "true", id="booleans"),
            pytest.param("TRUE\nFalse\ntrue\n", "TRUE", id="booleans-in-mixed-case"),
            pytest.param("007 kg\n12 kg\n15 kg\n", "007 kg", id="a-leading-zero-with-a-unit"),
            pytest.param("5 kg\n7 g\n3 g\n", "5 kg", id="mixed-units"),
        ],
    )
    def test_a_first_value_the_column_cannot_type_is_kept_too(self, text: str, first: str) -> None:
        """Copilot on #12202: a first value that makes the column text, or a boolean, is still no header."""
        parsed = parse_dataset(text)

        assert parsed.profile.columns[0].name == LIST_COLUMN_NAME and parsed.profile.rows == 3
        assert parsed.preview[0][0].casefold() == first.casefold()
        assert HEADERLESS_LIST_WARNING in parsed.warnings

    @pytest.mark.parametrize(
        "text",
        [
            pytest.param("Pendelzeit_min\n12\n15\n", id="a-name"),
            pytest.param("Messung 2024\n12\n15\n", id="a-name-with-a-year"),
            pytest.param("Q1\n12\n15\n", id="a-code"),
        ],
    )
    def test_a_header_that_names_the_column_stays_the_header(self, text: str) -> None:
        parsed = parse_dataset(text)

        assert parsed.profile.columns[0].name == text.split("\n")[0] and parsed.profile.rows == 2
        assert HEADERLESS_LIST_WARNING not in parsed.warnings

    def test_a_list_of_text_keeps_its_first_line_as_the_header(self) -> None:
        """Only typed values are read as rows: a first category may as well be a name (the transcriber's call)."""
        parsed = parse_dataset("7 Zwerge\n3 Bären\n")

        assert parsed.profile.columns[0].name == "7 Zwerge" and parsed.profile.rows == 1

    def test_a_table_the_service_wrote_is_never_read_again_this_way(self) -> None:
        parsed = parse_dataset("2024\n12\n15\n", find_table=False)

        assert parsed.profile.columns[0].name == "2024" and parsed.profile.rows == 2

    def test_a_list_one_value_past_the_cap_is_refused_not_cut(self) -> None:
        """Review of #12202: read as a header, the first value would be lost; read as a row, one row too many."""
        with pytest.raises(ParseError) as caught:
            parse_dataset("1\n" * (MAX_ROWS + 1))

        assert caught.value.code == "too_many_rows"
        assert caught.value.message == (
            f"the list has {MAX_ROWS + 1:,} values and no header line; at most {MAX_ROWS:,} rows are read"
        )
        assert parse_dataset("1\n" * MAX_ROWS).profile.rows == MAX_ROWS  # at the cap every value is a row


XY_ROLES = [
    DataRole(name="x", kinds=("numeric",), required=True, variadic=False, description="x values"),
    DataRole(name="y", kinds=("numeric",), required=True, variadic=False, description="y values"),
]
