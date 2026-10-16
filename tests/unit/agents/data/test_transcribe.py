"""The transcriber's schema and helpers: what counts as free text, and the table's CSV form."""

import pytest
from pydantic import ValidationError

from agents.anyplot.data.parse import parse_dataset
from agents.anyplot.data.transcribe import (
    MAX_TRANSCRIBE_CHARS,
    MAX_TRANSCRIBE_COLUMNS,
    MAX_TRANSCRIBE_LINES,
    MAX_TRANSCRIBE_ROWS,
    TranscribedTable,
    category_header_warning,
    looks_like_free_text,
    near_transcribe_cap,
    table_to_csv,
    transcribable,
    transcribe_refusal,
)


def test_transcribable_is_short_non_blank_text() -> None:
    assert transcribable("Hund 7 Katze 3 und Vogel 4")
    assert not transcribable("   \n")
    assert transcribable("x" * MAX_TRANSCRIBE_CHARS)
    assert not transcribable("x" * (MAX_TRANSCRIBE_CHARS + 1))


def test_transcribable_caps_the_lines_and_says_why() -> None:
    """Live round 7: 800 short lines are 2.4 KB, under the character cap, but no model copies them in time."""
    assert transcribe_refusal("a\n" * MAX_TRANSCRIBE_LINES + "\n\n") is None  # blank lines do not count
    many = "Hund 7\n" * (MAX_TRANSCRIBE_LINES + 1)
    assert len(many) < MAX_TRANSCRIBE_CHARS and not transcribable(many)
    assert transcribe_refusal(many) == (
        f"the text has {MAX_TRANSCRIBE_LINES + 1} lines, more than the {MAX_TRANSCRIBE_LINES} the model that reads "
        "free text as a table takes"
    )
    assert transcribe_refusal("x" * (MAX_TRANSCRIBE_CHARS + 1)) == (
        "the text is longer than the 4,000 characters the model that reads free text as a table takes"
    )
    assert transcribe_refusal(" \n") == "the text is empty"


def test_the_line_cap_fits_the_schema_also_without_a_header() -> None:
    """Review of #12202: a 201-line list without a header is 201 rows, one more than the schema holds."""
    assert MAX_TRANSCRIBE_LINES <= MAX_TRANSCRIBE_ROWS


def test_near_the_cap_is_half_the_characters_or_half_the_lines() -> None:
    assert not near_transcribe_cap("Hund 7\nKatze 3\n")
    assert near_transcribe_cap("a\n" * (MAX_TRANSCRIBE_LINES // 2))
    assert not near_transcribe_cap("a\n" * (MAX_TRANSCRIBE_LINES // 2 - 1))
    assert near_transcribe_cap("x" * (MAX_TRANSCRIBE_CHARS // 2))


R7_COMMUTE_TIMES = "Pendelzeit_min\n" + "".join(f"{12 + (i * 7) % 61}\n" for i in range(800))
"""The shape of live round 7's `pendelzeiten.csv`: a header and 800 integers, 2.4 KB."""


@pytest.mark.parametrize(
    "text",
    [
        pytest.param(R7_COMMUTE_TIMES, id="numbers-with-header"),
        pytest.param("12\n15\n17\n9\n", id="numbers-without-header"),
        pytest.param("Messwert\n1.5\n2.25\n-0.5\n", id="decimals"),
        pytest.param("Datum\n2024-01-01\n2024-02-01\n2024-03-05\n", id="dates"),
        pytest.param("2024-01-01\n2024-02-01\n", id="dates-without-header"),
        pytest.param("Gewicht\n5 kg\n7 kg\n", id="numbers-with-a-unit"),
        pytest.param("Verkehrsmittel\nAuto\nBahn\nAuto\nFahrrad\nBahn\nAuto\n", id="categories"),
        pytest.param("Lieblingsfarbe\nhell blau\nrot\nhell blau\n", id="categories-of-two-words"),
        pytest.param("PLZ\n01067\n01069\n01067\n", id="codes-with-leading-zeros"),
        pytest.param("Antwort\nstimme gar nicht zu\nstimme eher nicht zu\nstimme gar nicht zu\n", id="likert"),
        pytest.param("Menge\nca.\ngenau\nca.\n", id="an-abbreviation"),
    ],
)
def test_one_column_of_values_or_categories_is_a_table(text: str) -> None:
    parsed = parse_dataset(text)

    assert len(parsed.profile.columns) == 1
    assert not looks_like_free_text(parsed)


def test_a_category_list_names_the_line_that_became_its_header() -> None:
    """Review of #12202: `Apfel` above `Birne, Birne, Kirsche` cannot be told from a header by form."""
    assert category_header_warning(parse_dataset("Apfel\nBirne\nBirne\nKirsche\n")) == "read 'Apfel' as the column name"
    # `Tier` has the categories' form too: no cheap rule tells it from `Apfel`, so the same quiet note.
    assert category_header_warning(parse_dataset("Tier\nHund\nKatze\nHund\n")) == "read 'Tier' as the column name"


@pytest.mark.parametrize(
    "text",
    [
        pytest.param("Tier_Art\nHund\nKatze\nHund\n", id="underscore"),
        pytest.param("Tier (Art)\nHund\nKatze\nHund\n", id="brackets"),
        pytest.param("Verkehrsmittel zur Arbeit\nAuto\nBahn\nAuto\n", id="more-words-than-any-category"),
        pytest.param("Typ:\nA\nB\nA\n", id="colon"),
        pytest.param("PLZ\n01067\n01069\n01067\n", id="digit-codes"),
        pytest.param(R7_COMMUTE_TIMES, id="typed-values"),
        pytest.param("Tier,Anzahl\nHund,7\n", id="two-columns"),
    ],
)
def test_a_header_with_a_column_names_form_gets_no_note(text: str) -> None:
    assert category_header_warning(parse_dataset(text)) is None


def test_a_category_header_note_is_never_a_free_text_reading() -> None:
    assert not looks_like_free_text(parse_dataset("Tier_Art\nHund\nKatze\nHund\n"))
    assert category_header_warning(parse_dataset("Hund 7\nKatze 3\nHund 2\n")) is None  # free text, no table


@pytest.mark.parametrize(
    "text",
    [
        pytest.param("Hund 7\nKatze 3\nVogel 4\n", id="label-value-lines"),
        pytest.param("Tier Anzahl\nHund 7\nKatze 3\nHund 2\n", id="label-value-lines-under-a-header"),
        pytest.param("Tier Anzahl\nHund .5\nKatze -.3\nHund .5\n", id="label-value-lines-with-leading-dots"),
        pytest.param(
            "Wir hatten letztes Jahr sieben Hunde.\nDann kamen drei Katzen dazu.\nDann kamen drei Katzen dazu.\n",
            id="prose",
        ),
        pytest.param("Alice\nBob\nCarol\n", id="names-one-per-line"),  # the first could be a header or a name
        pytest.param("Auto\nBahn\nAuto\n", id="categories-without-header"),  # the header is one of them
        pytest.param("Wert\n12\nkeine Angabe\n17\n", id="numbers-with-a-word"),  # a mixed column stays text
        pytest.param("Das sind meine Daten aus der Umfrage\nja\nja\n", id="a-sentence-above-a-list"),
    ],
)
def test_one_column_of_prose_or_label_value_lines_is_free_text(text: str) -> None:
    assert looks_like_free_text(parse_dataset(text))


def test_free_text_is_one_column_without_a_delimiter_but_never_json() -> None:
    # A list typed one label and value per line parses as one text column headed by its first line.
    assert looks_like_free_text(parse_dataset("Hund 7\nKatze 3\nVogel 4\n"))
    assert not looks_like_free_text(parse_dataset("Tier,Anzahl\nHund,7\nKatze,3\n"))
    assert not looks_like_free_text(parse_dataset('[{"Anzahl": 7}, {"Anzahl": 3}]'))
    # An object of values or a dict literal is `json_pairs`: data, never free text.
    assert not looks_like_free_text(parse_dataset('{"Hund": 7, "Katze": 3}'))
    assert not looks_like_free_text(parse_dataset("tiere = {'Hund': 7, 'Katze': 3}"))


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
