"""The transcriber's schema and helpers: what counts as free text, and the table's CSV form."""

import pytest
from pydantic import ValidationError

from agents.anyplot.data.parse import parse_dataset
from agents.anyplot.data.transcribe import (
    MAX_TRANSCRIBE_CHARS,
    MAX_TRANSCRIBE_COLUMNS,
    MAX_TRANSCRIBE_ROWS,
    TranscribedTable,
    looks_like_free_text,
    table_to_csv,
    transcribable,
)


def test_transcribable_is_short_non_blank_text() -> None:
    assert transcribable("Hund 7 Katze 3 und Vogel 4")
    assert not transcribable("   \n")
    assert transcribable("x" * MAX_TRANSCRIBE_CHARS)
    assert not transcribable("x" * (MAX_TRANSCRIBE_CHARS + 1))


def test_free_text_is_one_column_without_a_delimiter_but_never_json() -> None:
    # A list typed one value per line parses as one text column headed by its first line.
    assert looks_like_free_text(parse_dataset("Hund 7\nKatze 3\nVogel 4\n"))
    assert not looks_like_free_text(parse_dataset("Tier,Anzahl\nHund,7\nKatze,3\n"))
    assert not looks_like_free_text(parse_dataset('[{"Anzahl": 7}, {"Anzahl": 3}]'))


def test_one_line_prose_is_unparseable_not_free_text() -> None:
    # A single line is a header without rows: the parser refuses it, and the route's fallback
    # applies to that refusal, not to this helper.
    with pytest.raises(Exception, match="header but no rows"):
        parse_dataset("Hund 7 Katze 3 und Vogel 4")


def test_table_to_csv_quotes_pads_and_cuts_rows() -> None:
    table = TranscribedTable(
        columns=["Tier", "Anzahl, Stück"], rows=[["Hund", "7"], ["Katze"], ["Vogel", "4", "extra"]], note=""
    )

    csv_text = table_to_csv(table)

    assert csv_text == 'Tier,"Anzahl, Stück"\nHund,7\nKatze,\nVogel,4\n'
    parsed = parse_dataset(csv_text)
    assert [column.name for column in parsed.profile.columns] == ["Tier", "Anzahl, Stück"]
    assert parsed.profile.rows == 3


def test_the_schema_bounds_the_table() -> None:
    with pytest.raises(ValidationError):
        TranscribedTable(columns=[], rows=[["1"]])
    with pytest.raises(ValidationError):
        TranscribedTable(columns=["a"], rows=[])
    with pytest.raises(ValidationError):
        TranscribedTable(columns=[f"c{i}" for i in range(MAX_TRANSCRIBE_COLUMNS + 1)], rows=[["1"]])
    with pytest.raises(ValidationError):
        TranscribedTable(columns=["a"], rows=[["1"]] * (MAX_TRANSCRIBE_ROWS + 1))
    with pytest.raises(ValidationError):
        TranscribedTable(columns=["a"], rows=[["1"]], note="n" * 201)
    with pytest.raises(ValidationError):
        TranscribedTable(columns=["a"], rows=[["1"]], extra="no")  # type: ignore[call-arg]
