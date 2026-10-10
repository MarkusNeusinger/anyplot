"""Tests for agents/anyplot/code/edits.py: exact-once matching, protected regions, failure lines."""

import pytest

from agents.anyplot.code.edits import (
    FAILURE_KINDS,
    MAX_NEW_LITERAL_CHARS,
    MAX_QUOTE_CHARS,
    AppliedPlan,
    apply_plan,
    new_literal_chars,
    protected_drift,
)
from agents.anyplot.schemas import MAX_EDITS, MAX_FEEDBACK, MAX_LINE_CHARS, AdaptPlan, Edit

from .conftest import source


WORKING = source("""
    import os

    import matplotlib.pyplot as plt

    THEME = os.getenv("ANYPLOT_THEME", "light")
    PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
    INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
    IMPRINT = ["#009E73", "#C475FD"]

    df = load_user_data()
    fig, ax = plt.subplots(figsize=(8, 4.5), dpi=400)
    ax.plot(df["x"], df["y"], color=IMPRINT[0])
    ax.set_ylim(0, 100)
    plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
""")


def plan(*edits: tuple[str, str]) -> AdaptPlan:
    return AdaptPlan(edits=[Edit(find=find, replace=replace) for find, replace in edits])


def apply(*edits: tuple[str, str], working: str = WORKING) -> AppliedPlan:
    result = apply_plan(working, plan(*edits))
    for failure in result.failures:
        assert "\n" not in failure and len(failure) <= MAX_LINE_CHARS
    return result


def test_edits_apply_in_order() -> None:
    result = apply(
        ("ax.set_ylim(0, 100)\n", 'ax.set_ylim(0, df["y"].max())\n'), ('df["y"].max()', 'df["y"].max() * 1.1')
    )

    assert result.failures == []
    assert result.code == WORKING.replace("ax.set_ylim(0, 100)", 'ax.set_ylim(0, df["y"].max() * 1.1)')


def test_no_edits_returns_the_working_form() -> None:
    assert apply() == AppliedPlan(WORKING, [])


def test_full_code_replaces_everything() -> None:
    full = WORKING.replace("ax.set_ylim(0, 100)\n", "")
    result = apply_plan(WORKING, AdaptPlan(full_code=full))
    assert result == AppliedPlan(full, [])


@pytest.mark.parametrize(
    ("full", "what"),
    [
        (WORKING.replace('"#FAF8F1" if', '"#FF00FF" if'), "theme token PAGE_BG"),
        (WORKING.replace('getenv("ANYPLOT_THEME", "light")', 'getenv("ANYPLOT_THEME", "dark")'), "THEME assignment"),
        (WORKING.replace("dpi=400, facecolor=PAGE_BG", "dpi=100, facecolor=PAGE_BG"), "final savefig"),
        ("print('x')\n", "THEME assignment"),
    ],
)
def test_full_code_keeps_the_protected_regions(full: str, what: str) -> None:
    result = apply_plan(WORKING, AdaptPlan(full_code=full))

    assert result.code is None and any(what in failure for failure in result.failures)


@pytest.mark.parametrize(
    "rebinding",
    [
        'PAGE_BG = "#FF00FF"\n',
        'PAGE_BG += "00"\n',
        'THEME = "dark"\n',
        "for INK in IMPRINT:\n    pass\n",
        "def recolour(PAGE_BG=None):\n    global INK\n",
        "from colours import magenta as PAGE_BG\n",
        "del INK\n",
    ],
)
def test_a_theme_name_bound_again_further_down_is_refused(rebinding: str) -> None:
    result = apply(("ax.set_ylim(0, 100)\n", rebinding))

    assert result.code is None
    assert any("a second time" in failure for failure in result.failures)


def test_new_literal_chars_counts_only_added_text() -> None:
    renamed = WORKING.replace("ax.set_ylim(0, 100)\n", 'ax.set_title("Sales by Month")\n')
    padded = WORKING.replace("ax.set_ylim(0, 100)\n", 'notes = ["' + "x" * 2100 + '"]\n')

    assert new_literal_chars(WORKING, WORKING) == 0
    assert new_literal_chars(WORKING, renamed) == len("Sales by Month")
    assert new_literal_chars(WORKING, padded) == 2100 > MAX_NEW_LITERAL_CHARS
    assert new_literal_chars(WORKING, "def broken(:\n") == 0


def test_full_code_rebinding_a_token_is_refused() -> None:
    full = WORKING.replace("df = load_user_data()\n", 'df = load_user_data()\nPAGE_BG = "#FF00FF"\n')

    result = apply_plan(WORKING, AdaptPlan(full_code=full))

    assert result.code is None and "binds PAGE_BG a second time" in result.failures[0]


@pytest.mark.parametrize(
    ("find", "count"), [("ax.set_xlim(0, 10)", "0 times"), ("ax.", "2 times"), ("THEME", "5 times")]
)
def test_find_must_match_exactly_once(find: str, count: str) -> None:
    result = apply(("ax.set_ylim(0, 100)", "ax.set_ylim(0, 50)"), (find, "x"))

    assert result.code is None
    assert len(result.failures) == 1
    assert result.failures[0].startswith(f"edit 2/2: find matches {count} in the current code")


def test_overlapping_occurrences_count() -> None:
    result = apply(("aa", "b"), working="x = 'aaa'\n")
    assert result.failures[0].startswith("edit 1/1: find matches 2 times")


@pytest.mark.parametrize(
    ("find", "what"),
    [
        ('THEME = os.getenv("ANYPLOT_THEME", "light")', "THEME assignment"),
        ('PAGE_BG = "#FAF8F1"', "theme token PAGE_BG"),
        ('else "#F0EFE8"\nIMPRINT', "theme token INK"),
        ("df = load_user_data()", "placeholder line"),
        ("dpi=400, facecolor=PAGE_BG)", "final savefig statement"),
        ("ax.set_ylim(0, 100)\nplt.savefig", "final savefig statement"),
    ],
)
def test_protected_regions_refuse_edits(find: str, what: str) -> None:
    result = apply((find, "x"))

    assert result.code is None
    assert f"overlaps the protected {what}" in result.failures[0]
    assert "anchor the edit on other lines" in result.failures[0]


def test_imprint_is_not_protected_and_neighbours_are_fine() -> None:
    result = apply(
        ('IMPRINT = ["#009E73", "#C475FD"]', 'IMPRINT = ["#009E73", "#C475FD", "#4467A3"]'),
        ("ax.set_ylim(0, 100)\n", ""),  # ends right where the savefig line starts
        ("import matplotlib.pyplot as plt\n", "import matplotlib.pyplot as plt\nimport numpy as np\n"),
    )

    assert result.failures == []
    assert result.code is not None and "#4467A3" in result.code and "ax.set_ylim" not in result.code


def test_protected_regions_move_with_earlier_edits() -> None:
    result = apply(("import os\n", "import os\nimport math\n\n\n"), ('INK = "#1A1A17"', "INK = INK_X"))
    assert result.code is None and "theme token INK at line 10" in result.failures[0]


def test_placeholder_introduced_by_an_earlier_edit_is_protected() -> None:
    working = WORKING.replace("df = load_user_data()\n", "df = make_demo_data()\n")
    result = apply(
        ("df = make_demo_data()", "df = load_user_data()"),
        ("df = load_user_data()\nfig", "df = load_user_data().dropna()\nfig"),
        working=working,
    )
    assert result.code is None and "placeholder line" in result.failures[0]


def test_failures_skip_and_report_every_bad_edit() -> None:
    result = apply(("nope", "x"), ("ax.set_ylim(0, 100)", "ax.set_ylim(0, 50)"), ("THEME =", "T ="))

    assert result.code is None
    assert [failure.split(":")[0] for failure in result.failures] == ["edit 1/3", "edit 3/3"]


def test_quotes_are_short_and_escaped() -> None:
    find = "line one\n" + "x" * 200
    failure = apply((find, "y")).failures[0]

    quoted = failure.split("find = ", 1)[1]
    assert quoted.startswith('"line one\\nxxx') and quoted.endswith('…"')
    assert len(quoted) <= MAX_QUOTE_CHARS + 8


def test_failures_are_capped_at_the_feedback_limit() -> None:
    result = apply(*((f"missing {i}", "x") for i in range(MAX_EDITS)))

    assert len(result.failures) == MAX_FEEDBACK
    assert result.failures[-1].startswith(f"{MAX_EDITS - MAX_FEEDBACK + 1} more edits failed")


def test_unparseable_working_form() -> None:
    result = apply(("a", "b"), working="def broken(:\n")
    assert result.code is None and result.failures[0].startswith("the working form does not parse")
    assert result.kinds == ("working_unparseable",)


class TestFailureKinds:
    """Each failure has a content-free kind for the attribution log; the lines quote code, the kinds never do."""

    def test_match_and_overlap_kinds_follow_the_edits(self) -> None:
        result = apply(
            ("nope", "x"),
            ("ax.", "x"),
            ('PAGE_BG = "#FAF8F1"', "x"),
            ("df = load_user_data()", "x"),
            ("dpi=400, facecolor=PAGE_BG)", "x"),
            ('THEME = os.getenv("ANYPLOT_THEME", "light")', "x"),
        )

        assert result.kinds == (
            "zero_match",
            "multi_match",
            "protected:theme_token",
            "protected:placeholder",
            "protected:savefig",
            "protected:theme",
        )
        assert set(result.kinds) <= FAILURE_KINDS

    def test_drift_kinds_leave_the_reminder_without_a_kind(self) -> None:
        full = WORKING.replace('INK = "#1A1A17" if', 'INK = "#FF00FF" if').replace(
            "df = load_user_data()\n", 'df = load_user_data()\nPAGE_BG = "#FF00FF"\n'
        )

        result = apply_plan(WORKING, AdaptPlan(full_code=full))

        assert result.kinds == ("drift:theme_token", "drift:rebind")
        assert len(result.failures) == 3 and result.failures[-1].startswith("keep the THEME assignment")
        assert result.failures == protected_drift(WORKING, full)

    @pytest.mark.parametrize(
        ("full", "kind"),
        [
            (WORKING.replace('getenv("ANYPLOT_THEME", "light")', 'getenv("ANYPLOT_THEME", "dark")'), "drift:theme"),
            (WORKING.replace("dpi=400, facecolor=PAGE_BG", "dpi=100, facecolor=PAGE_BG"), "drift:savefig"),
        ],
    )
    def test_each_protected_statement_has_its_drift_kind(self, full: str, kind: str) -> None:
        assert apply_plan(WORKING, AdaptPlan(full_code=full)).kinds == (kind,)

    def test_kinds_count_the_edits_past_the_feedback_cap(self) -> None:
        result = apply(*((f"missing {i}", "x") for i in range(MAX_EDITS)))

        assert len(result.failures) == MAX_FEEDBACK
        assert result.kinds == ("zero_match",) * MAX_EDITS

    def test_a_clean_plan_has_no_kinds(self) -> None:
        assert apply(("ax.set_ylim(0, 100)", "ax.set_ylim(0, 50)")).kinds == ()
