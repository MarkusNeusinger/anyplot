"""Closed codes for the parser's and the binding check's warning sentences, for the usage telemetry.

The parser (`parse.py`), the generator (`generate.py`), the dataset route (`opening.py`) and the
binding check (`bindings.py`) say what they did in sentences written for the user, and many of them
name a column or quote a count. The usage telemetry (`telemetry.py`) never logs a sentence: it logs
the code `warning_code` maps a sentence to, from the closed set `WarningCode`, and `other` for a
sentence no rule knows. The rules match the fixed parts of each sentence only, anchored where a
column name could sit in between, so a crafted column name can at worst pick a wrong code from the
set, never put its own text into a log line.

The table lives here, next to the modules that write the sentences, so a new warning and its code
change together: `tests/unit/agents/data/test_warning_codes.py` feeds every sentence the parser
writes for its fixtures through `warning_code` and fails on `other`.
"""

import re
from typing import Literal, cast, get_args


WarningCode = Literal[
    "notes_instruction_like",
    "notes_refused",
    "notes_unchecked",
    "notes_cut",
    "nfc_normalised",
    "single_space_separator",
    "lines_above_left_out",
    "lines_below_left_out",
    "summary_rows_left_out",
    "short_rows_positional",
    "short_rows_padded",
    "trailing_empty_fields",
    "multiple_tables",
    "headerless_list",
    "category_header",
    "repeated_keys",
    "nan_infinity_missing",
    "object_as_pairs",
    "fields_beside_records_to_notes",
    "list_fields_beside_left_out",
    "nested_fields_dotted",
    "deep_fields_left_out",
    "list_fields_expanded",
    "record_id_added",
    "list_values_thinned",
    "records_missing_keys",
    "jsonstat_dimension_renamed",
    "jsonstat_labels_with_codes",
    "jsonstat_status_ignored",
    "jsonstat_single_category_dims",
    "empty_header_named",
    "long_header_shortened",
    "header_shortened_for_unit",
    "duplicate_header_renamed",
    "empty_columns_dropped",
    "missing_marks_emptied",
    "header_whitespace_replaced",
    "headers_look_like_values",
    "invisible_chars_removed",
    "unit_removed_from_values",
    "unit_moved_to_name",
    "numbers_respelled",
    "valueless_columns_dropped",
    "row_number_column_dropped",
    "constant_columns_to_notes",
    "leading_zeros_text",
    "big_integers_text",
    "decimal_commas_ambiguous",
    "thousands_separators",
    "utc_offsets_normalised",
    "sub_microsecond_text",
    "date_order_ambiguous",
    "months_read",
    "na_as_code",
    "digits_rounded",
    "cells_trimmed",
    "cells_read_missing",
    "series_undefined",
    "more_omitted",
    "other",
]
"""Every warning code; `other` is a sentence no rule in `_RULES` knows (a new warning without its code)."""

WARNING_CODES: frozenset[str] = frozenset(get_args(WarningCode))

_COLUMN = r"column '.*': "
"""A column-scoped sentence's lead; greedy, so the rule's own text is matched at the end."""

_RULES: tuple[tuple[re.Pattern[str], WarningCode], ...] = tuple(
    (re.compile(pattern, re.DOTALL), cast(WarningCode, code))  # each code is in the set: test_warning_codes.py
    for pattern, code in (
        (
            r"^the notes above or below the table were left out: they read like instructions to an AI$",
            "notes_instruction_like",
        ),
        (
            r"^the notes above or below the table were left out: they are not about the data or the plot$",
            "notes_refused",
        ),
        (r"^the notes above or below the table were left out: they could not be checked right now$", "notes_unchecked"),
        (
            r"^the (?:notes around the table|notes from the fields beside the records|dataset's notes) were cut at [0-9,]+ characters$",
            "notes_cut",
        ),
        (r"^[0-9,]+ lines? held decomposed characters .* \(NFC\); the text reads the same$", "nfc_normalised"),
        (
            r"^single spaces read as the column separator; check that no value was split in two$",
            "single_space_separator",
        ),
        (r"^left out [0-9,]+ lines? above the table \(a title, notes or metadata\)$", "lines_above_left_out"),
        (r"^left out [0-9,]+ lines? below the table \(notes or a source line\)$", "lines_below_left_out"),
        (r"^left out [0-9,]+ summary rows? at the end of the table .*$", "summary_rows_left_out"),
        (
            r"^[0-9,]+ rows? had fewer fields than the header; their cells were placed under the header's columns by their position.*$",
            "short_rows_positional",
        ),
        (r"^[0-9,]+ rows? had fewer fields than the header; the missing cells are empty.*$", "short_rows_padded"),
        (
            r"^[0-9,]+ rows? had empty fields past the header's [0-9]+ columns; those empty fields were left out$",
            "trailing_empty_fields",
        ),
        (
            r"^the data holds [0-9]+ tables, each under its own header; .*the table picker in the data panel reads another one$",
            "multiple_tables",
        ),
        (
            r"^no header line: the first line is a value, kept as the first row, and the column is named '.*'$",
            "headerless_list",
        ),
        (r"^read '.*' as the column name$", "category_header"),
        (r"^[0-9,]+ keys? repeated; only the last value of a repeated key is kept$", "repeated_keys"),
        (r"^[0-9,]+ values? NaN, Infinity or -Infinity read as missing$", "nan_infinity_missing"),
        (r"^the object was read as [0-9,]+ category/value pairs?, one row per key; .*$", "object_as_pairs"),
        (
            r"^[0-9,]+ fields? beside the records \(such as paging or a timestamp\) moved to the notes$",
            "fields_beside_records_to_notes",
        ),
        (r"^[0-9,]+ fields? beside the records that hold lists left out$", "list_fields_beside_left_out"),
        (r"^fields of nested objects became columns named with a dot, such as parent\.field$", "nested_fields_dotted"),
        (
            r"^[0-9,]+ fields? holding a list of objects or lists, or objects nested more than [0-9]+ levels deep, left out: .*$",
            "deep_fields_left_out",
        ),
        (r"^list fields expanded into one row per value.*$", "list_fields_expanded"),
        (r"^column '.*' added: it numbers the records, so the rows of each stay together$", "record_id_added"),
        (r"^the lists hold [0-9,]+ values, more than the [0-9,]+ rows a table may have: .*$", "list_values_thinned"),
        (r"^[0-9,]+ records? [a-z ]+ some keys; those cells are empty$", "records_missing_keys"),
        (_COLUMN + r"a dimension named like the value column renamed$", "jsonstat_dimension_renamed"),
        (_COLUMN + r"labels shared by two categories carry their codes$", "jsonstat_labels_with_codes"),
        (r"^the dataset's status symbols \(such as provisional or estimated\) are ignored$", "jsonstat_status_ignored"),
        (r"^[0-9,]+ dimensions? with a single category left out of the columns; .*$", "jsonstat_single_category_dims"),
        (r"^column [0-9]+: empty header named '.*'$", "empty_header_named"),
        (r"^column [0-9]+: header longer than [0-9]+ characters shortened to '.*'$", "long_header_shortened"),
        (
            r"^column [0-9]+: header shortened to '.*' so the unit fits within [0-9]+ characters$",
            "header_shortened_for_unit",
        ),
        (r"^column [0-9]+: duplicate header '.*' renamed to '.*'$", "duplicate_header_renamed"),
        (r"^[0-9,]+ empty columns? without a header dropped$", "empty_columns_dropped"),
        (
            r"^[0-9,]+ cells? of number or date columns matched the missing-value mark the notes declare and are empty$",
            "missing_marks_emptied",
        ),
        (_COLUMN + r"tabs or line breaks in the header replaced with spaces$", "header_whitespace_replaced"),
        (
            r"^every header looks like a value; the first row may be data rather than column names$",
            "headers_look_like_values",
        ),
        (_COLUMN + r"invisible formatting characters \(zero-width or bidi\) removed$", "invisible_chars_removed"),
        (_COLUMN + r"unit '.*' removed from the values; the name already carries it$", "unit_removed_from_values"),
        (_COLUMN + r"unit '.*' moved from the values into the name '.*'$", "unit_moved_to_name"),
        (r"^[0-9,]+ numbers? written in another form with the same value .*$", "numbers_respelled"),
        (r"^[0-9,]+ columns? without any value dropped: .*$", "valueless_columns_dropped"),
        (r"^left out the column .*: its [0-9,]+ cells? only number the rows .*$", "row_number_column_dropped"),
        (r"^[0-9,]+ columns? with the same text in every row moved to the notes: .*$", "constant_columns_to_notes"),
        (_COLUMN + r"numbers with leading zeros kept as text$", "leading_zeros_text"),
        (_COLUMN + r"whole numbers beyond the 64-bit range kept as text, so no digit is lost$", "big_integers_text"),
        (
            _COLUMN + r"commas read as decimal commas; remove them first if they separate thousands$",
            "decimal_commas_ambiguous",
        ),
        (_COLUMN + r".* read as thousands separators(?:, as in the file's other columns)?$", "thousands_separators"),
        (
            _COLUMN + r"times with the UTC offsets .* written in UTC \(\+00:00\); the instants are the same$",
            "utc_offsets_normalised",
        ),
        (_COLUMN + r"kept as text: times with fractions below a microsecond .*$", "sub_microsecond_text"),
        (_COLUMN + r"day and month order is ambiguous; read as (?:DD/MM/YYYY|MM/DD/YYYY)$", "date_order_ambiguous"),
        (_COLUMN + r"[0-9,]+ cells? read as months \(YYYY-MM, each as the first day of the month\)$", "months_read"),
        (_COLUMN + r"NA read as a code \(such as Namibia or North America\), not as a missing cell$", "na_as_code"),
        (_COLUMN + r"[0-9,]+ values? with more significant digits than a number holds .*$", "digits_rounded"),
        (_COLUMN + r"spaces around the text removed in [0-9,]+ cells?$", "cells_trimmed"),
        (_COLUMN + r"[0-9,]+ cells? read as missing \(.*\)$", "cells_read_missing"),
        (r"^.*: [0-9]+ of [0-9]+ values (?:is|are) undefined and left empty$", "series_undefined"),
        (r"^[0-9,]+ more warnings omitted$", "more_omitted"),
    )
)
"""The rules in order, the first that matches wins: the column-scoped rules come after every rule that starts with
fixed text, so a column name cannot shadow a sentence that has none."""


def warning_code(sentence: str) -> WarningCode:
    """The closed code of one warning sentence; `other` when no rule matches."""
    for pattern, code in _RULES:
        if pattern.match(sentence):
            return code
    return "other"


def warning_codes(sentences: list[str]) -> list[WarningCode]:
    """The distinct codes of `sentences`, sorted, so a line carries each code once."""
    return sorted({warning_code(sentence) for sentence in sentences})


BindingWarningCode = Literal["negative_values", "negative_unbound", "label_sibling", "window_mismatch", "other"]
"""The binding check's warnings (`bindings.check_bindings`) as closed codes."""

_BINDING_RULES: tuple[tuple[re.Pattern[str], BindingWarningCode], ...] = tuple(
    (re.compile(pattern, re.DOTALL), cast(BindingWarningCode, code))
    for pattern, code in (
        (
            r"^.*: not bound, because every column that fits it \(.*\) has negative values; this role needs values of 0 or more$",
            "negative_unbound",
        ),
        (
            r"^.*: column '.*' has negative values \(down to .*\); this role needs values of 0 or more$",
            "negative_values",
        ),
        (
            r"^.*: bound to '.*', one of [0-9]+ number columns .* turn the columns into rows first \(\.to_long\(\)\)$",
            "label_sibling",
        ),
        (r"^.*: column '.*' holds a .*-period value; the spec's convention is .*$", "window_mismatch"),
    )
)


def binding_warning_codes(sentences: list[str]) -> list[BindingWarningCode]:
    """The distinct closed codes of the binding check's warnings, sorted; `other` for a sentence no rule knows."""
    codes: set[BindingWarningCode] = set()
    for sentence in sentences:
        codes.add(next((code for pattern, code in _BINDING_RULES if pattern.match(sentence)), "other"))
    return sorted(codes)
