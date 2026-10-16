"""The warning sentences map to closed codes (`data/warning_codes.py`), never to their own text."""

from pathlib import Path
from typing import get_args

import pytest

from agents.anyplot.data.parse import (
    AMBIGUOUS_DATE_ORDER,
    HEADERLESS_LIST_WARNING,
    NS_OUT_OF_RANGE,
    ParseError,
    parse_dataset,
    rounded_note,
)
from agents.anyplot.data.prepare import AMBIGUOUS_MONTH_FIRST
from agents.anyplot.data.signs import sign_line
from agents.anyplot.data.warning_codes import WARNING_CODES, binding_warning_codes, warning_code, warning_codes
from agents.anyplot.opening import NOTES_INSTRUCTION_WARNING, NOTES_REFUSED_WARNING, NOTES_UNCHECKED_WARNING
from agents.anyplot.schemas import ColumnProfile


REPO_ROOT = Path(__file__).resolve().parents[4]

SAMPLES: dict[str, str] = {
    NOTES_INSTRUCTION_WARNING: "notes_instruction_like",
    NOTES_REFUSED_WARNING: "notes_refused",
    NOTES_UNCHECKED_WARNING: "notes_unchecked",
    "the notes around the table were cut at 2,000 characters": "notes_cut",
    "the dataset's notes were cut at 2,000 characters": "notes_cut",
    "3 lines held decomposed characters (such as e and a separate accent), now written in Unicode's composed form "
    "(NFC); the text reads the same": "nfc_normalised",
    "single spaces read as the column separator; check that no value was split in two": "single_space_separator",
    "left out 2 lines above the table (a title, notes or metadata)": "lines_above_left_out",
    "left out 1 line below the table (notes or a source line)": "lines_below_left_out",
    "left out 1 summary row at the end of the table (a total, sum, mean or similar)": "summary_rows_left_out",
    "2 rows had fewer fields than the header; their cells were placed under the header's columns by their "
    "position, and the cells left over are empty (lines 3, 4)": "short_rows_positional",
    "1 row had fewer fields than the header; the missing cells are empty (line 7)": "short_rows_padded",
    "4 rows had empty fields past the header's 3 columns; those empty fields were left out": "trailing_empty_fields",
    "the data holds 2 tables, each under its own header; read table 1 (a, b: 3 rows) and left out table 2; the "
    "table picker in the data panel reads another one": "multiple_tables",
    HEADERLESS_LIST_WARNING: "headerless_list",
    "read 'Apples' as the column name": "category_header",
    "2 keys repeated; only the last value of a repeated key is kept": "repeated_keys",
    "1 value NaN, Infinity or -Infinity read as missing": "nan_infinity_missing",
    "the object was read as 3 category/value pairs, one row per key; to read it as one row with the keys as "
    "columns, put it in brackets [ … ]": "object_as_pairs",
    "2 fields beside the records (such as paging or a timestamp) moved to the notes": "fields_beside_records_to_notes",
    "1 field beside the records that hold lists left out": "list_fields_beside_left_out",
    "fields of nested objects became columns named with a dot, such as parent.field": "nested_fields_dotted",
    "2 fields holding a list of objects or lists, or objects nested more than 3 levels deep, left out: a, b": (
        "deep_fields_left_out"
    ),
    "list fields expanded into one row per value: x, y": "list_fields_expanded",
    "column 'record' added: it numbers the records, so the rows of each stay together": "record_id_added",
    "the lists hold 30,000 values, more than the 20,000 rows a table may have: 20,000 evenly spaced values are "
    "kept, the first and last of each record among them; paste fewer points to keep every value": "list_values_thinned",
    "3 records lack some keys; those cells are empty": "records_missing_keys",
    "column 'value': a dimension named like the value column renamed": "jsonstat_dimension_renamed",
    "column 'Region': labels shared by two categories carry their codes": "jsonstat_labels_with_codes",
    "the dataset's status symbols (such as provisional or estimated) are ignored": "jsonstat_status_ignored",
    "2 dimensions with a single category left out of the columns; the notes name each one with its category": (
        "jsonstat_single_category_dims"
    ),
    "column 3: empty header named 'column_3'": "empty_header_named",
    "column 2: header longer than 64 characters shortened to 'A very long name'": "long_header_shortened",
    "column 2: header shortened to 'Name (kg)' so the unit fits within 64 characters": "header_shortened_for_unit",
    "column 4: duplicate header 'x' renamed to 'x_2'": "duplicate_header_renamed",
    "2 empty columns without a header dropped": "empty_columns_dropped",
    "5 cells of number or date columns matched the missing-value mark the notes declare and are empty": (
        "missing_marks_emptied"
    ),
    "column 'a b': tabs or line breaks in the header replaced with spaces": "header_whitespace_replaced",
    "every header looks like a value; the first row may be data rather than column names": "headers_look_like_values",
    "column 'x': invisible formatting characters (zero-width or bidi) removed": "invisible_chars_removed",
    "column 'Weight (kg)': unit 'kg' removed from the values; the name already carries it": "unit_removed_from_values",
    "column 'Weight': unit 'kg' moved from the values into the name 'Weight (kg)'": "unit_moved_to_name",
    "12 numbers written in another form with the same value (trailing zeros, exponent or plus sign dropped, such as "
    "1.50 as 1.5 or 1e3 as 1000) in 'a'": "numbers_respelled",
    "2 columns without any value dropped: 'a', 'b'": "valueless_columns_dropped",
    "left out the column '': its 24 cells only number the rows 1 to 24 in order, as R's write.csv or pandas' index "
    "write row names": "row_number_column_dropped",
    "1 column with the same text in every row moved to the notes: 'unit'": "constant_columns_to_notes",
    "column 'zip': numbers with leading zeros kept as text": "leading_zeros_text",
    "column 'id': whole numbers beyond the 64-bit range kept as text, so no digit is lost": "big_integers_text",
    "column 'x': commas read as decimal commas; remove them first if they separate thousands": (
        "decimal_commas_ambiguous"
    ),
    "column 'x': dots read as thousands separators, as in the file's other columns": "thousands_separators",
    "column 'x': commas read as thousands separators": "thousands_separators",
    "column 't': times with the UTC offsets +01:00, +02:00 written in UTC (+00:00); the instants are the same": (
        "utc_offsets_normalised"
    ),
    f"column 't': {NS_OUT_OF_RANGE}": "sub_microsecond_text",
    f"column 'd': {AMBIGUOUS_DATE_ORDER}": "date_order_ambiguous",
    f"column 'd': {AMBIGUOUS_MONTH_FIRST}": "date_order_ambiguous",
    "column 'm': 12 cells read as months (YYYY-MM, each as the first day of the month)": "months_read",
    "column 'country': NA read as a code (such as Namibia or North America), not as a missing cell": "na_as_code",
    f"column 'v': {rounded_note(3)}": "digits_rounded",
    "column 'name': spaces around the text removed in 4 cells": "cells_trimmed",
    "column 'v': 3 cells read as missing ('n/a', '-')": "cells_read_missing",
    "y: 2 of 200 values are undefined and left empty": "series_undefined",
    "4 more warnings omitted": "more_omitted",
}


@pytest.mark.parametrize(("sentence", "code"), SAMPLES.items())
def test_every_sentence_maps_to_its_code(sentence: str, code: str) -> None:
    assert warning_code(sentence) == code


def test_every_code_has_a_sample() -> None:
    """A code without a sample sentence is a rule nobody checked."""
    assert set(SAMPLES.values()) | {"other"} == WARNING_CODES


def test_every_rule_names_a_code_of_the_set() -> None:
    from agents.anyplot.data.warning_codes import _BINDING_RULES, _RULES, BindingWarningCode

    assert {code for _, code in _RULES} <= WARNING_CODES
    assert {code for _, code in _BINDING_RULES} <= set(get_args(BindingWarningCode))


def test_an_unknown_sentence_is_other() -> None:
    assert warning_code("something the parser never wrote, with a value 42") == "other"


def test_a_column_name_cannot_shadow_a_fixed_sentence() -> None:
    """A crafted column name picks a code from the set at worst; the code is never its text."""
    crafted = "column 'left out 9 lines above the table (a title, notes or metadata)': spaces around the text removed in 1 cell"
    assert warning_code(crafted) == "cells_trimmed"
    assert set(warning_codes([crafted, "CANARY free text"])) <= WARNING_CODES


def test_codes_are_distinct_and_sorted() -> None:
    sentences = [
        "4 more warnings omitted",
        "4 more warnings omitted",
        "left out 1 line below the table (notes or a source line)",
    ]
    assert warning_codes(sentences) == ["lines_below_left_out", "more_omitted"]


def test_the_fixture_corpus_has_no_unknown_warning() -> None:
    """Every warning the parser writes for the eval fixtures has a code: a new warning needs its rule."""
    files = sorted((REPO_ROOT / "agents" / "evals" / "fixtures").rglob("data.*"))
    assert files
    unknown = []
    for path in files:
        try:
            parsed = parse_dataset(path.read_text(encoding="utf-8"))
        except (ParseError, UnicodeDecodeError):
            continue
        unknown += [line for line in parsed.warnings if warning_code(line) == "other"]
    assert unknown == []


def test_parser_warnings_of_real_pastes_have_codes() -> None:
    pastes = [
        "Title of the table\n\nx,y\n1,2\n3,4\nTotal,6\n",
        "x;y\n1,5;2\n3,5;4\n",
        "a,b,c\n1,2\n3,4,5\n",
        "x y\n1 2\n3 4\n",
        '[{"a": 1, "b": [1, 2]}, {"a": 2, "b": [3]}]',
        "name,value\n Alice ,1\nBob,n/a\n",
    ]
    for text in pastes:
        try:
            parsed = parse_dataset(text)
        except ParseError:
            continue
        assert "other" not in warning_codes(parsed.warnings), parsed.warnings


def test_binding_warnings_map_to_codes() -> None:
    column = ColumnProfile(name="Change", dtype="number", missing=0, unique=3, min=-2.5, max=4.0)
    negative = sign_line("y", column)
    unbound = "y: not bound, because every column that fits it ('a', 'b') has negative values; this role needs values of 0 or more"
    sibling = (
        "y: bound to 'Mo', one of 7 number columns ('Mo', 'Tu', 'We', 'Th', ...) that hold one measure side by side; "
        "y wants labels, so each number would become a category of its own: turn the columns into rows first (.to_long())"
    )
    assert binding_warning_codes([negative, unbound, sibling, "CANARY"]) == [
        "label_sibling",
        "negative_unbound",
        "negative_values",
        "other",
    ]
