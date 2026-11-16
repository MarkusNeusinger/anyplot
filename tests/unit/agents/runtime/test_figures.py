"""Tests for the number-provenance matcher (`agents/anyplot/figures.py`): a corpus of invented replies and sources.

Every value, column and sentence here is invented for the test. Each corpus row names the figures the matcher must
find unsourced. A row whose `why` starts with `false alarm` is a reply a reader would call right that the check flags
all the same; one that starts with `general knowledge` states a figure no source of the turn holds, whose place is an
open product choice. The rows whose reply holds a token the check cannot read (`unread`) are counted too. All are
kept so a change of the rules shows in the numbers (the measured cost of each rule).
"""

from dataclasses import dataclass, field
from decimal import Decimal
from typing import Any

import pytest

from agents.anyplot import figures as figures_module
from agents.anyplot.figures import SOURCE_KINDS, Reading, SourceKind, Sources, figures, provenance


NNBSP = " "
NBSP = " "


@dataclass(frozen=True)
class Row:
    """One corpus case: a reply, its sources by kind, the figures it must find unsourced, and why."""

    id: str
    reply: str
    sources: list[tuple[SourceKind, Any]] = field(default_factory=list)
    unsourced: tuple[str, ...] = ()
    why: str = ""


def tool(value: Any) -> tuple[SourceKind, Any]:
    return ("tool_result", value)


def drawn(value: Any) -> tuple[SourceKind, Any]:
    return ("drawn_text", value)


def said(text: str) -> tuple[SourceKind, Any]:
    return ("user", text)


def block(text: str) -> tuple[SourceKind, Any]:
    return ("session", text)


TOTAL = tool({"columns": ["branch", "loans"], "rows": [["all", "58214.37"]], "total_rows": 1})
FIT = drawn({"legend": ["y=0.42x-1.35"]})

CORPUS: list[Row] = [
    # --- English number format
    Row("en_total_sourced", "The loans add up to 58,214.37 EUR.", [TOTAL]),
    Row("en_total_invented", "The loans add up to 58,914.37 EUR.", [TOTAL], ("58,914.37",), "a total no tool gave"),
    Row("en_rounded", "That is about 58,214 EUR, or 58,214.4 to one decimal.", [TOTAL]),
    Row("en_bold_markdown", "Total: **58,214.37**", [TOTAL]),
    Row("en_no_figure", "The bars now run in descending order.", [TOTAL]),
    # --- German and French number formats, Swiss apostrophes
    Row("de_total", "Die Ausleihen ergeben 58.214,37 €.", [TOTAL]),
    Row("de_total_wrong", "Die Ausleihen ergeben 58.241,37 €.", [TOTAL], ("58.241,37",), "two digits swapped"),
    Row("de_rounded", "Das sind rund 58.214 €.", [TOTAL]),
    Row("fr_narrow_nbsp", f"Le total des prêts est de 58{NNBSP}214,37 €.", [TOTAL]),
    Row("fr_nbsp", f"Le total des prêts est de 58{NBSP}214 €.", [TOTAL]),
    Row("fr_plain_space", "Le total des prêts est de 58 214,37 €.", [TOTAL]),
    Row("fr_percent_narrow_nbsp", f"Une part de 37,5{NNBSP}% roule le matin.", [tool({"share": 0.375})]),
    Row("ch_apostrophe", "Die Summe ist CHF 58'214.37.", [TOTAL]),
    # --- Chinese and Japanese: no space between a number and the words around it
    Row("zh_glued_sourced", "借阅总额是58,214.37元。", [TOTAL]),
    Row("zh_glued_invented", "借阅总额是9,357.48元。", [TOTAL], ("9,357.48",), "a total no tool gave, glued to Han"),
    Row("ja_glued_sourced", "貸出の総額は58,214.37円でした。", [TOTAL]),
    Row(
        "ja_spaced_invented", "貸出の総額は 9,357.48 円でした。", [TOTAL], ("9,357.48",), "a total no tool gave, spaced"
    ),
    Row("zh_source_glued", "Your limit is 7,200.", [said("我们的上限是7200元")]),
    Row("ja_source_glued", "La limite est de 7 200.", [said("上限は7200円にします")]),
    Row("zh_glued_negative", "访问量下降了−4.6%。", [tool({"change": -4.6})]),
    Row("zh_glued_sign_flipped", "访问量下降了−4.6%。", [tool({"change": 4.6})], ("−4.6%",), "the sign flipped"),
    Row("full_width_digits", "借阅总额是５８，２１４．３７元。", [TOTAL]),
    Row("zh_full_width_comma_list", "三家分店的借阅量分别为312，475，508。", [tool({"loans": [312, 475, 508]})]),
    Row(
        "zh_full_width_comma_list_invented",
        "三家分店的借阅量分别为312，475，598。",
        [tool({"loans": [312, 475, 508]})],
        ("598",),
        "one number of the list no tool gave: each is read on its own",
    ),
    Row("ja_full_width_comma_list", "各支店の件数は214，389，463件です。", [tool({"counts": [214, 389, 463]})]),
    Row("zh_full_width_comma_list_of_the_user", "Your values 23, 47 and 61 repeat.", [said("我的数值是23，47，61")]),
    # --- Thai: no space between words either
    Row("th_glued_invented", "ยอดขายรวม7,425.60บาท", [TOTAL], ("7,425.60",), "a total no tool gave, glued to Thai"),
    Row(
        "zh_week_label",
        "第14周借阅最多。",
        [TOTAL],
        ("14",),
        "false alarm: a week number joined to Han, which no longer reads as a label",
    ),
    # --- rounding and precision
    Row("drawn_label_rounded", "The fitted line rises by 0.04 per hour.", [drawn({"title": ["slope 0.042"]})]),
    Row(
        "added_precision",
        "The fitted line rises by 0.0420 per hour.",
        [drawn({"title": ["slope 0.042"]})],
        ("0.0420",),
        "more digits than the drawn label holds",
    ),
    Row("trailing_zero_of_json", "Each ticket costs 12.50 EUR.", [tool({"price": 12.5})]),
    Row("trailing_zero_of_the_session", "The mean stays at 23.40.", [block("- Mean of loans: 23.4")]),
    Row("trailing_zero_of_the_user", "Your budget of 8,500.00 EUR stays.", [said("my budget is 8500 EUR")]),
    Row("trailing_zero_of_the_service", "At most 25.0 rows come back.", [("service", 25)]),
    Row(
        "round_thousand_is_no_trailing_zero",
        "About 3,000 rows in all.",
        [block("- Dataset: 3 columns")],
        ("3,000",),
        "a group-shaped token's zeros are no decimals: 3,000 is not 3",
    ),
    Row(
        "trailing_zero_of_memory",
        "The line stays at 61.50.",
        [("memory", "horizontal line at y = 61.5")],
        ("61.50",),
        "a model-written source keeps the strict rule",
    ),
    Row("round_half", "The mean is 7.25, about 7.3.", [tool({"mean": 7.25})]),
    Row(
        "round_whole_thousands",
        "About 58,000 EUR in all.",
        [TOTAL],
        ("58,000",),
        "false alarm: a figure rounded to the thousands reads as a whole number of its own",
    ),
    # --- signs
    Row("typographic_minus", "Visits changed by −3.8 % in May.", [tool({"change": -3.8})]),
    Row("hyphen_minus", "Visits changed by -3.8 % in May.", [tool({"change": -3.8})]),
    Row("sign_flipped", "Visits changed by −3.8 % in May.", [tool({"change": 3.8})], ("−3.8 %",), "the sign flipped"),
    Row("plus_flipped", "Visits changed by +3.8 % in May.", [tool({"change": -3.8})], ("+3.8 %",), "the sign flipped"),
    Row("sign_in_words", "Visits fell by 3.8 % in May.", [tool({"change": -3.8})]),
    # --- the signed terms of a drawn equation
    Row("eq_glued_intercept", "The intercept is −1.35.", [FIT]),
    Row("eq_glued_rounded", "The intercept is -1.3 and the slope 0.42.", [FIT]),
    Row("eq_glued_magnitude", "The line crosses zero 1.35 below the origin.", [FIT]),
    Row("eq_glued_flipped", "The intercept is +1.35.", [FIT], ("+1.35",), "the sign flipped"),
    Row("eq_spaced_intercept", "The intercept is −1.35.", [drawn({"legend": ["y = 0.42x - 1.35"]})]),
    Row("eq_plus_term", "The intercept is 4.15.", [drawn({"legend": ["y=2.6x+4.15"]})]),
    Row("eq_in_the_reply", "The fit is y = 0.42x − 1.35.", [FIT]),
    Row("eq_in_the_reply_glued", "The legend reads y=0.42x-1.35.", [FIT]),
    Row(
        "eq_restated_flipped_glued",
        "The legend reads y=0.42x+1.35.",
        [FIT],
        ("+1.35",),
        "a restated equation keeps the sign of its terms",
    ),
    Row(
        "eq_restated_flipped_spaced",
        "The legend reads y = 0.42x + 1.35.",
        [FIT],
        ("+ 1.35",),
        "a spaced operator is the term's sign",
    ),
    Row(
        "eq_restated_flipped_spaced_minus",
        "The fit is y = 2.6x − 4.15.",
        [drawn({"legend": ["y=2.6x+4.15"]})],
        ("− 4.15",),
        "a spaced operator is the term's sign",
    ),
    # --- percent, read per token
    Row("percent_of_fraction", "A share of 37.5 % rides in the morning.", [tool({"share": 0.375})]),
    Row("percent_as_written", "A share of 37.5 % rides in the morning.", [tool({"share": "37.5"})]),
    Row("percent_rounded_tie", "About 38 % ride in the morning.", [tool({"share": 0.375})]),
    Row(
        "percent_invented",
        "A share of 37.6 % rides in the morning.",
        [tool({"share": 0.375})],
        ("37.6 %",),
        "a share no tool gave",
    ),
    Row(
        "percent_per_token",
        "0.425 of the days, or 42.5 %, and 42.5 rentals.",
        [tool({"share": 0.425})],
        ("42.5",),
        "the percent reading belongs to one token, not to the reply",
    ),
    Row("percent_of_short_fraction", "Four in ten, 40 %, ride at night.", [tool({"share": 0.4})]),
    Row("leading_dot", "A share of .625 borrows online.", [tool({"share": 0.625})]),
    Row(
        "leading_dot_invented",
        "A share of .635 borrows online.",
        [tool({"share": 0.625})],
        (".635",),
        "no tool gave it",
    ),
    # --- ranges, dates and times
    Row("range_hyphen", "Between 120-180 bikes a day.", [tool({"min": 120, "max": 180})]),
    Row("range_en_dash", "Between 120–180 bikes a day.", [tool({"min": 120, "max": 180})]),
    Row("year_range", "From 2019-2023.", [tool({"first": "2019-01-01", "last": "2023-12-31"})]),
    Row("date_reordered", "The busiest day was 14.03.2024.", [tool({"rows": [["2024-03-14", "412"]]})]),
    Row("date_us", "The busiest day was 03/14/2024.", [tool({"rows": [["2024-03-14", "412"]]})]),
    Row("date_short_year", "The busiest day was 14.03.24.", [tool({"rows": [["2024-03-14", "412"]]})]),
    Row(
        "date_wrong",
        "The busiest day was 15.03.2024.",
        [tool({"rows": [["2024-03-14", "412"]]})],
        ("15.03.2024",),
        "a day no source holds",
    ),
    Row(
        "date_parts_permuted",
        "The peak was on 11.09.2024.",
        [tool({"rows": [["2009-11-24", "9"]]})],
        ("11.09.2024",),
        "the same numbers in other places of the date",
    ),
    Row(
        "date_dotted_month_first",
        "The busiest day was 03.14.2024.",
        [tool({"rows": [["2024-03-14", "412"]]})],
        (),
        "unread: a dotted date reads day first, and no month is 14, so its marks fit no date and no number",
    ),
    Row("year_from_date", "Every row is from 2024.", [tool({"rows": [["2024-03-14", "412"]]})]),
    Row("time_of_day", "The first loan was at 07:45.", [tool({"rows": [["2024-03-14 07:45:00", "3"]]})]),
    # --- structure that is no figure
    Row("version_labels", "Data v2 replaces v1 on the bar-basic-4 layout.", []),
    Row("ids_and_colours", "The series uses #2A9D8F and #1f77b4, and the column CO2 stays.", []),
    Row("list_markers", "Two steps:\n1. Sort the branches\n2) Keep the largest", []),
    Row("bold_list_markers", "**1.** Order the branches\n**2.** Keep the top 15", [tool({"limit": 15})]),
    Row("heading_list_marker", "### 12. Narrow it down\nKeep the rows.", []),
    Row("keycaps", "1️⃣ Order\n2️⃣ Narrow", []),
    Row("enclosed_numbers", "① order ② narrow", []),
    Row("aspect_ratio", "Pick 16:9 for slides or 21:9 for a banner.", []),
    Row("small_fraction", "About 3/4 of the rows are filled.", []),
    Row("code_spans", "Set `alpha=0.35` and `figsize=(16, 9)` in the code.", []),
    Row("code_span_number", "The sum is `9,357.48`.", []),
    Row("code_block", "```python\nax.set_ylim(0, 450)\n```", []),
    # --- ranges of glued units, and of plain numbers in a source
    Row("glued_unit_range", "Each batch takes 12h-15h.", [tool({"min": 12, "max": 15})]),
    Row("glued_unit_range_spaced", "Each batch takes 12h - 15h.", [tool({"min": 12, "max": 15})]),
    Row("glued_thousands_range", "Between 15k-20k visits a day.", [tool({"low": 15, "high": 20})]),
    Row("small_glued_range", "It takes 2h-3h, or 5k-8k steps.", []),
    Row(
        "unit_range_in_a_source",
        "The window closes at −11 hours.",
        [tool({"window": "8h-11h"})],
        ("−11",),
        "a range of units in a source has no sign",
    ),
    Row(
        "plain_range_in_a_source",
        "The band ends at −190.",
        [tool({"band": "140 - 190"})],
        ("−190",),
        "a range of two plain numbers in a source has no sign",
    ),
    # --- structure that is a figure
    Row(
        "currency_code",
        "That comes to EUR2,904.66.",
        [TOTAL],
        ("2,904.66",),
        "a total no tool gave, after a currency code",
    ),
    Row("label_colon", "Sum:9,357.48", [TOTAL], ("9,357.48",), "a total no tool gave, after a label and a colon"),
    Row(
        "ratio_read_as_time", "Print the map at 1:25.", [], ("1:25",), "false alarm: a ratio shaped like a time of day"
    ),
    # --- tokens the matcher cannot read: unread, never unsourced, and held only by the identical token
    Row(
        "version_number", "The renderer runs matplotlib 3.10.1.", [], (), "unread: a version whose marks fit no number"
    ),
    Row(
        "comma_list_of_the_user",
        "Your values 21,24,27 repeat.",
        [said("my values are 21,24,27")],
        (),
        "a list without spaces reads as no number, and the user's message holds the identical token",
    ),
    Row("numbers_across_a_nbsp", f"Since 2022{NBSP}140 loans moved.", [TOTAL], (), "unread: no number has its marks"),
    Row("exponent_past_any_decimal", "The rate is 4e2345678.", [TOTAL], (), "unread: no decimal holds it"),
    Row("exponent_held_as_written", "The rate is 4e2345678.", [said("a rate of 4e2345678")]),
    Row("a_huge_source_is_skipped", "The loans add up to 58,214.37 EUR.", [said("3e8888888 or 6.5e-8888888"), TOTAL]),
    Row(
        "a_huge_source_turns_nothing_off",
        "The loans add up to 9,357.48 EUR.",
        [said("3e8888888")],
        ("9,357.48",),
        "a total no source holds",
    ),
    # --- units and scientific notation
    Row("unit_spaced", "The heaviest crate weighs 18.6 kg.", [tool({"max": 18.6})]),
    Row("unit_glued", "The heaviest crate weighs 18.6kg.", [tool({"max": 18.6})]),
    Row("sci_e", "The decay rate is 3.2e-4 per hour.", [tool({"rate": 0.00032})]),
    Row("sci_times_ten", "The decay rate is 3.2 × 10⁻⁴ per hour.", [tool({"rate": 0.00032})]),
    Row("sci_caret", "The decay rate is 3.2x10^-4 per hour.", [tool({"rate": "0.00032"})]),
    Row("sci_invented", "The decay rate is 3.3e-4 per hour.", [tool({"rate": 0.00032})], ("3.3e-4",)),
    Row("sci_trailing_zero", "The decay rate is 3.20e-4 per hour.", [tool({"rate": 0.00032})]),
    Row(
        "sci_more_digits",
        "The decay rate is 3.21e-4 per hour.",
        [tool({"rate": 0.00032})],
        ("3.21e-4",),
        "a digit no source holds",
    ),
    # --- no digit runs out of longer tokens
    Row("no_inner_digits", "In 375 cases.", [tool({"ratio": "1.375", "code": "ID2024X"})], ("375",)),
    Row("no_inner_year", "In 2024.", [tool({"code": "ID2024X"})], ("2024",)),
    Row("no_decimal_part", "Five times 125.", [tool({"slope": "0.125"})], ("125",)),
    # --- source kinds
    Row("user_number", "As you said, the budget is 8,500 EUR.", [said("my budget is 8500 EUR")]),
    Row("session_count", "The table has 64 rows.", [block("- Dataset: 64 rows, 4 columns")]),
    Row("service_limit", "A computed table holds at most 20,000 rows.", [("service", 20000)]),
    Row("service_no_share", "About 50 % of the rows.", [("service", 50)], ("50 %",), "a limit is no share"),
    Row("plot_notes", "The reference line sits at 3.75.", [("plot_notes", {"changes": ["line at y = 3.75"]})]),
    Row("plot_code", "The line sits at 3.75.", [("plot_code", "ax.axhline(3.75)")]),
    # --- small whole numbers and general knowledge
    Row("small_count", "Here are 2 ways to show it.", [TOTAL]),
    Row("ordinal", "The 3rd week was the busiest.", [TOTAL]),
    Row("file_limits", "Pasted text is capped at 1 MB and a workbook at 5 MB.", []),
    Row(
        "world_constant",
        "At a speed of sound of 343.2 m/s the echo takes longer.",
        [TOTAL],
        ("343.2",),
        "general knowledge: a figure from no source, also when the user asked for a worked calculation with it",
    ),
    Row(
        "print_resolution",
        "A poster prints well at 350 ppi.",
        [],
        ("350",),
        "general knowledge: a figure from no source",
    ),
    Row(
        "scale_word",
        "About 1.2 million visits in all.",
        [tool({"visits": 1215408})],
        ("1.2",),
        "false alarm: a scale word, which the check does not read",
    ),
]


def sources_of(row: Row) -> Sources:
    sources = Sources()
    for kind, value in row.sources:
        if isinstance(value, str):
            sources.add_text(value, kind)
        else:
            sources.add_json(value, kind)
    return sources


@pytest.mark.parametrize("row", CORPUS, ids=[row.id for row in CORPUS])
def test_the_corpus(row: Row) -> None:
    assert provenance(row.reply, sources_of(row)).unsourced == row.unsourced, row.why


def test_the_corpus_counts() -> None:
    """The measured behaviour, counted from the matcher's output: how many replies the check flags, how many of those
    a reader would call right (false alarms), how many state general knowledge, and which hold a token the check
    cannot read, which it counts and never flags."""
    found = {row.id: provenance(row.reply, sources_of(row)) for row in CORPUS}
    flagged = [row for row in CORPUS if found[row.id].unsourced]
    false_alarms = [row.id for row in flagged if row.why.startswith("false alarm")]
    general = [row.id for row in flagged if row.why.startswith("general knowledge")]
    assert (len(CORPUS), len(flagged)) == (124, 38)
    assert false_alarms == ["zh_week_label", "round_whole_thousands", "ratio_read_as_time", "scale_word"]
    assert general == ["world_constant", "print_resolution"]
    assert [row.id for row in CORPUS if found[row.id].unread] == [
        "date_dotted_month_first",
        "version_number",
        "numbers_across_a_nbsp",
        "exponent_past_any_decimal",
    ]


def test_the_ids_are_unique() -> None:
    assert len({row.id for row in CORPUS}) == len(CORPUS)


class TestSourceKinds:
    def test_a_figure_counts_under_the_most_trusted_source_that_holds_it(self) -> None:
        sources = Sources()
        sources.add_text("slope 0.042", "drawn_text")
        sources.add_json({"slope": 0.042}, "tool_result")
        sources.add_text("8500", "user")

        found = provenance("A slope of 0.042, a budget of 8500.", sources)

        assert found.by_kind == {"tool_result": 1, "user": 1}
        assert found.counts() == {
            "figures": 2,
            "unsourced": 0,
            "exempt": 0,
            "unread": 0,
            "magnitude_only": 0,
            "from_tool_result": 1,
            "from_session": 0,
            "from_user": 1,
            "from_service": 0,
            "from_memory": 0,
            "from_plot_notes": 0,
            "from_plot_code": 0,
            "from_drawn_text": 0,
        }

    def test_the_kinds_are_credited_in_their_order(self) -> None:
        assert SOURCE_KINDS == (
            "tool_result",
            "session",
            "user",
            "service",
            "memory",
            "plot_notes",
            "plot_code",
            "drawn_text",
        )

    def test_the_counts_name_every_kind_and_no_figure(self) -> None:
        found = provenance("Visits fell to 3,141.", Sources())

        assert found.unsourced == ("3,141",)
        keys = {"figures", "unsourced", "exempt", "unread", "magnitude_only"}
        assert set(found.counts()) == keys | {f"from_{kind}" for kind in SOURCE_KINDS}
        assert all(isinstance(value, int) for value in found.counts().values())

    def test_each_unsourced_figure_is_named_once_in_order(self) -> None:
        assert provenance("5.5, 6.5 and 5.5 again", Sources()).unsourced == ("5.5", "6.5")

    def test_a_match_that_held_only_by_magnitude_is_counted(self) -> None:
        sources = Sources()
        sources.add_json({"change": -3.8, "mean": 7.25}, "tool_result")

        found = provenance("Visits fell by 3.8 %, the mean is 7.25 and the change −3.8 %.", sources)

        assert (found.unsourced, found.magnitude_only, found.by_kind) == ((), 1, {"tool_result": 3})

    def test_an_unread_token_is_counted_apart_and_never_unsourced(self) -> None:
        """A token whose marks fit no number, or that no decimal holds, is no figure the check can verify."""
        found = provenance("Rows 11,22,33 and 4e2345678, total 58.", Sources())

        assert (found.unsourced, found.missing[0].text) == (("58",), "58")
        assert (found.checked, found.unread, found.counts()["unsourced"]) == (3, 2, 1)

    def test_an_unread_token_stands_where_a_source_holds_the_identical_token(self) -> None:
        sources = Sources()
        sources.add_json({"version": "4.12.7", "note": "rows 11,22,33"}, "tool_result")

        found = provenance("Version 4.12.7 reads rows 11,22,33, not 11,22,34.", sources)

        assert (found.unsourced, found.unread, found.by_kind) == ((), 1, {"tool_result": 2})


class TestReadings:
    @pytest.mark.parametrize(
        ("text", "values"),
        [
            ("1,234", [Decimal("1.234"), Decimal("1234")]),
            ("1.234", [Decimal("1.234"), Decimal("1234")]),
            ("0.234", [Decimal("0.234")]),
            ("1,25", [Decimal("1.25")]),
            ("1.234.567,8", [Decimal("1234567.8")]),
            ("1,234,567.8", [Decimal("1234567.8")]),
            (f"1{NNBSP}234{NNBSP}567", [Decimal("1234567")]),
            ("1 234.5", [Decimal("1234.5")]),
            ("1'234.5", [Decimal("1234.5")]),
            ("−12.5", [Decimal("-12.5")]),
            ("+14", [Decimal("14")]),
            (".625", [Decimal("0.625")]),
            ("１２．５", [Decimal("12.5")]),
        ],
    )
    def test_the_marks_of_every_number_format(self, text: str, values: list[Decimal]) -> None:
        (figure,) = figures(text)
        assert [reading.value for reading in figure.numbers] == values

    def test_a_full_width_token_keeps_its_text_as_written(self) -> None:
        (figure,) = figures("总额是５８．５元")
        assert figure.text == "５８．５"

    def test_a_full_width_comma_or_full_stop_is_a_mark_only_between_full_width_digits(self) -> None:
        """Elsewhere it is the comma or full stop of Chinese or Japanese text, which separates numbers."""
        assert [figure.text for figure in figures("分别为312，475。共１，２３４件．")] == ["312", "475", "１，２３４"]

    @pytest.mark.parametrize(
        "text",
        ["ยอดขายรวม7,425.60บาท", "ຍອດລວມ7,425.60ກີບ", "សរុប7,425.60រៀល", "စုစုပေါင်း7,425.60ကျပ်"],
        ids=["thai", "lao", "khmer", "myanmar"],
    )
    def test_a_number_beside_a_script_written_without_spaces_is_read(self, text: str) -> None:
        assert [figure.text for figure in figures(text)] == ["7,425.60"]

    def test_a_plain_space_may_group_one_number_or_separate_two(self) -> None:
        (figure,) = figures("in 2023 120 rows")

        assert figure.numbers == ()  # 2023 is no group of a number
        assert [part.numbers for part in figure.split] == [
            (Reading(Decimal("2023"), 0),),
            (Reading(Decimal("120"), 0),),
        ]

    def test_an_exponent_moves_the_decimals(self) -> None:
        (small,) = figures("1.2e-5")
        (large,) = figures("1.2e5")

        assert small.numbers == (Reading(Decimal("0.000012"), 6),)
        assert large.numbers[0].value == Decimal("120000") and large.numbers[0].decimals == -4

    def test_a_percent_sign_marks_its_own_token(self) -> None:
        tokens = figures("12 % and 12")

        assert [(figure.text, figure.percent) for figure in tokens] == [("12 %", True), ("12", False)]

    def test_dates_and_times_are_tokens_of_their_own(self) -> None:
        tokens = figures("On 2024-03-14 at 07:45, and 06/2024.")

        assert [(figure.date, figure.slots, figure.time) for figure in tokens] == [
            ((2024, 3, 14), ((2024, 3, 14),), None),
            (None, (), (7, 45)),
            ((6, 2024), ((2024, 6, None),), None),
        ]

    def test_a_date_reads_in_the_orders_its_shape_allows(self) -> None:
        dotted, slashed = figures("04.05.2024 and 04/05/2024")

        assert dotted.slots == ((2024, 5, 4),)
        assert slashed.slots == ((2024, 5, 4), (2024, 4, 5))

    @pytest.mark.parametrize("text", ["2024-13-40", "31.31.2024", "25:61"])
    def test_a_shape_with_impossible_parts_is_no_date(self, text: str) -> None:
        assert all(not figure.slots and figure.time is None for figure in figures(text))

    def test_a_source_keeps_its_list_markers_and_code(self) -> None:
        """A number in a tool's code or numbered list is still that tool's number."""
        assert [figure.text for figure in figures("1. `alpha=0.35`", reply=False)] == ["1", "0.35"]
        assert figures("1. `alpha=0.35`") == []

    @pytest.mark.parametrize(
        ("text", "values"),
        [
            ("y=0.42x-1.35", ["0.42", "-1.35"]),
            ("y = 0.42x - 1.35", ["0.42", "-1.35"]),
            ("y = 0.42x² - 1.35", ["0.42", "-1.35"]),
            ("y = 0.42x − 1.35", ["0.42", "-1.35"]),
            ("y=2.6x+4.15", ["2.6", "4.15"]),
            ("12h-15h", ["12", "15"]),
            ("12h - 15h", ["12", "15"]),
            ("140-190", ["140", "190"]),
            ("140 - 190", ["140", "190"]),
            ("140 − 190", ["140", "190"]),
            ("140–190", ["140", "190"]),
            ("x-2 and y_2", []),
        ],
    )
    def test_a_reply_and_a_source_read_signs_the_same_way(self, text: str, values: list[str]) -> None:
        """The term of an equation keeps its sign, glued or spaced; a range of units (the same letter after both
        numbers) and a range of two plain numbers have none."""
        assert [str(figure.numbers[0].value) for figure in figures(text, reply=False)] == values
        assert [str(figure.numbers[0].value) for figure in figures(text)] == values

    def test_a_source_keeps_what_no_decimal_holds_as_written(self) -> None:
        sources = Sources()
        sources.add_text("3e8888888, 6.5e-8888888 and 4e2345678 next to 4.5", "user")

        assert sources.kind_of(figures("4.5")[0]) == "user"
        assert sources.kind_of(figures("4e2345678")[0]) == "user"
        assert sources.kind_of(figures("4e2345679")[0]) is None

    def test_a_reply_never_reads_a_digit_run_of_a_label_or_identifier(self) -> None:
        assert figures("CO2, Q4, PM2.5, bar-basic-12, v.2, x_12, 1f77b4 and ID2024X") == []


class TestSmallWholeNumbers:
    def test_ten_is_the_provisional_default(self) -> None:
        assert figures_module.SMALL_WHOLE_MAX == 10

    def test_a_bare_small_whole_number_is_exempt_and_a_marked_one_is_read(self) -> None:
        found = provenance("Here are 2 ways, 3rd week, −2 degrees, 2.5 hours, 2 %, 12 rows.", Sources())

        assert found.unsourced == ("−2", "2.5", "2 %", "12")
        assert found.exempt == 2

    def test_none_reads_every_whole_number(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(figures_module, "SMALL_WHOLE_MAX", None)

        found = provenance("Here are 2 ways, about 3/4 of them, 3rd week.", Sources())

        assert (found.unsourced, found.exempt) == (("2", "3", "4"), 0)
