"""Tests for agents/anyplot/code/edits.py: exact-once matching, protected regions, failure lines."""

import pytest

from agents.anyplot.code import edits
from agents.anyplot.code.edits import (
    FAILURE_KINDS,
    MAX_CHANGE_LITERAL_CHARS,
    MAX_NEW_LITERAL_CHARS,
    MAX_QUOTE_CHARS,
    AppliedPlan,
    apply_plan,
    new_literal_chars,
    new_literals,
    protected_drift,
    restore_protected,
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


def test_new_literals_lists_each_added_string_as_often_as_it_is_new() -> None:
    added = WORKING.replace("ax.set_ylim(0, 100)\n", 'ax.set_title("A")\nax.set_xlabel("A")\nax.text(0, 0, "B")\n')

    assert new_literals(WORKING, WORKING) == []
    assert new_literals(WORKING, added) == ["A", "A", "B"]
    assert new_literals(WORKING, "def broken(:\n") == []
    assert MAX_CHANGE_LITERAL_CHARS < MAX_NEW_LITERAL_CHARS


def test_bytes_literals_count_as_text() -> None:
    added = WORKING.replace("ax.set_ylim(0, 100)\n", "ax.set_title(b'Sales'.decode())\n")

    assert new_literals(WORKING, added) == ["Sales"] and new_literal_chars(WORKING, added) == 5


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
        ("dpi=400, facecolor=PAGE_BG)", "final savefig statement"),
        ("ax.set_ylim(0, 100)\nplt.savefig", "final savefig statement"),
    ],
)
def test_protected_regions_refuse_edits(find: str, what: str) -> None:
    result = apply((find, "x"))

    assert result.code is None
    assert f"overlaps the protected {what}" in result.failures[0]
    assert "anchor the edit on other lines" in result.failures[0]


@pytest.mark.parametrize("find", ["df = load_user_data()", "df = load_user_data()\nfig, ax"])
def test_placeholder_overlap_names_the_line_to_anchor_on(find: str) -> None:
    """The rerun's five `protected:placeholder` failures were edits that extended the line; say how to add after it."""
    result = apply((find, find.replace("load_user_data()", "load_user_data().dropna()")))

    failure = result.failures[0]
    assert result.kinds == ("protected:placeholder",)
    assert "overlaps the protected df = load_user_data() line at line 10" in failure
    assert "keep that line exactly as it is and out of find and replace" in failure
    assert 'set find to line 11 ("fig, ax = plt.subplots(figsize=(8, 4.5), dpi=400)")' in failure
    assert "write the new statements in front of that line in replace" in failure


def test_imprint_is_not_protected_and_neighbours_are_fine() -> None:
    result = apply(
        ('IMPRINT = ["#009E73", "#C475FD"]', 'IMPRINT = ["#009E73", "#C475FD", "#4467A3"]'),
        ("ax.set_ylim(0, 100)\n", ""),  # ends right where the savefig line starts
        ("import matplotlib.pyplot as plt\n", "import matplotlib.pyplot as plt\nimport numpy as np\n"),
    )

    assert result.failures == []
    assert result.code is not None and "#4467A3" in result.code and "ax.set_ylim" not in result.code


def test_an_added_ink_muted_line_is_neither_drift_nor_a_rebind() -> None:
    """adapter.md adds `INK_MUTED` right after the palette list for an "Other" group; both plan shapes keep it."""
    palette = 'IMPRINT = ["#009E73", "#C475FD"]\n'
    muted = 'INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"\n'
    with_muted = WORKING.replace(palette, palette + muted)

    assert protected_drift(WORKING, with_muted) == []
    assert apply_plan(WORKING, AdaptPlan(full_code=with_muted)) == AppliedPlan(with_muted, [])
    assert apply((palette, palette + muted)) == AppliedPlan(with_muted, [])


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
    assert result.code is None and "protected df = load_user_data() line" in result.failures[0]


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


DATA_THEME_LINE = '_tight_color = INK if THEME == "dark" else IMPRINT[int(df["y"].argmin()) % 2]\n'
WITH_DATA_THEME_LINE = WORKING.replace("ax.set_ylim(0, 100)\n", "ax.set_ylim(0, 100)\n" + DATA_THEME_LINE)


class TestThemeTokenDrift:
    """The rerun's 13 `drift:theme_token` failures: 12 from box-basic's data-dependent conditional, 1 from a token."""

    def test_a_data_dependent_theme_conditional_is_plot_code(self) -> None:
        """A full file may rewrite it, as box-basic's repair needs; it reads the data, not just the theme."""
        rewritten = WITH_DATA_THEME_LINE.replace(
            DATA_THEME_LINE, '_tight_color = INK if THEME == "dark" else IMPRINT[0]\n'
        )

        assert protected_drift(WITH_DATA_THEME_LINE, rewritten) == []
        assert apply_plan(WITH_DATA_THEME_LINE, AdaptPlan(full_code=rewritten)).code == rewritten

    def test_an_edit_may_change_a_data_dependent_theme_conditional(self) -> None:
        result = apply(("% 2]", "% len(IMPRINT)]"), working=WITH_DATA_THEME_LINE)

        assert result.failures == [] and result.code is not None and "% len(IMPRINT)]" in result.code

    @pytest.mark.parametrize(
        "restated",
        [
            "PAGE_BG = '#FAF8F1' if THEME == 'light' else '#1A1A17'",  # other quotes
            'PAGE_BG = "#FAF8F1" if THEME=="light" else "#1A1A17"  # page',  # spacing and a comment
            'PAGE_BG = (\n    "#FAF8F1" if THEME == "light" else "#1A1A17"\n)',  # line breaks
        ],
    )
    def test_a_token_restated_with_the_same_value_is_no_drift(self, restated: str) -> None:
        full = WORKING.replace('PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"', restated)

        assert protected_drift(WORKING, full) == []
        assert apply_plan(WORKING, AdaptPlan(full_code=full)).code == full

    def test_a_token_with_another_value_drifts_and_says_to_copy_the_line(self) -> None:
        full = WORKING.replace('else "#1A1A17"\nINK', 'else "#000000"\nINK')

        result = apply_plan(WORKING, AdaptPlan(full_code=full))

        assert result.kinds == ("drift:theme_token",)
        assert "theme token PAGE_BG; copy its line unchanged from the current code" in result.failures[0]


PLOT_CHANGE = ("ax.set_ylim(0, 100)\n", "ax.set_ylim(0, 50)\n")
"""A plot change the restore must keep: it is outside every protected statement."""


class TestRestoreProtected:
    """Owner decision 2026-10-16: drift of the protected theme statements alone is restored, a rebind never."""

    @staticmethod
    def drifted(*replacements: tuple[str, str]) -> str:
        code = WORKING.replace(*PLOT_CHANGE)
        for old, new in replacements:
            assert old in code
            code = code.replace(old, new)
        return code

    @pytest.mark.parametrize(
        ("replacements", "kinds"),
        [
            ((('getenv("ANYPLOT_THEME", "light")', 'getenv("ANYPLOT_THEME", "dark")'),), {"drift:theme"}),
            ((('THEME = os.getenv("ANYPLOT_THEME", "light")', 'THEME = "light"'),), {"drift:theme"}),
            ((('else "#1A1A17"\nINK', 'else "#000000"\nINK'),), {"drift:theme_token"}),
            # A token that no longer tests the theme is no token in the plan's code; it is found by name.
            (
                (('PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"', 'PAGE_BG = "#FFFFFF"'),),
                {"drift:theme_token"},
            ),
            ((("dpi=400, facecolor=PAGE_BG)", "dpi=100, facecolor=PAGE_BG)"),), {"drift:savefig"}),
            (
                (
                    ('getenv("ANYPLOT_THEME", "light")', 'getenv("ANYPLOT_THEME", "dark")'),
                    ('INK = "#1A1A17" if', 'INK = "#FF00FF" if'),
                    ("dpi=400, facecolor=PAGE_BG)", "dpi=100)"),
                ),
                {"drift:theme", "drift:theme_token", "drift:savefig"},
            ),
        ],
    )
    def test_each_restorable_kind_is_restored_and_the_plot_change_kept(
        self, replacements: tuple[tuple[str, str], ...], kinds: set[str]
    ) -> None:
        drifted = self.drifted(*replacements)
        applied = apply_plan(WORKING, AdaptPlan(full_code=drifted))
        assert applied.code is None and set(applied.kinds) == kinds and applied.drifted == drifted

        restored = restore_protected(WORKING, drifted)

        assert restored == WORKING.replace(*PLOT_CHANGE)
        assert protected_drift(WORKING, restored) == []

    def test_a_protected_statement_at_the_end_of_the_file_keeps_the_code_after_it(self) -> None:
        base = WORKING.rstrip("\n")  # the savefig ends the file without a line break
        drifted = base.replace("dpi=400, facecolor=PAGE_BG)", "dpi=100)") + "\nplt.close()\n"

        assert restore_protected(base, drifted) == base + "\nplt.close()\n"

    def test_a_rebind_is_never_restored(self) -> None:
        drifted = self.drifted(
            ('INK = "#1A1A17" if', 'INK = "#FF00FF" if'),
            ("df = load_user_data()\n", 'df = load_user_data()\nPAGE_BG = "#FF00FF"\n'),
        )
        applied = apply_plan(WORKING, AdaptPlan(full_code=drifted))
        assert "drift:rebind" in applied.kinds and applied.drifted == drifted

        assert restore_protected(WORKING, drifted) is None

    def test_a_removed_protected_statement_is_not_restored(self) -> None:
        drifted = self.drifted(('INK = "#1A1A17" if THEME == "light" else "#F0EFE8"\n', ""))

        assert restore_protected(WORKING, drifted) is None

    def test_a_statement_sharing_its_line_is_not_restored(self) -> None:
        drifted = self.drifted(('INK = "#1A1A17" if', 'x = 1; INK = "#FF00FF" if'))

        assert restore_protected(WORKING, drifted) is None

    def test_a_splice_that_does_not_parse_is_not_restored(self, monkeypatch: pytest.MonkeyPatch) -> None:
        drifted = self.drifted(('else "#1A1A17"\nINK', 'else "#000000"\nINK'))
        monkeypatch.setattr(edits, "_splice", lambda code, splices: code + "\nif (:\n")

        assert restore_protected(WORKING, drifted) is None

    def test_code_without_drift_or_without_a_parse_has_nothing_to_restore(self) -> None:
        assert restore_protected(WORKING, WORKING.replace(*PLOT_CHANGE)) is None
        assert restore_protected(WORKING, "if (:\n") is None

    def test_failed_edits_carry_no_drifted_code(self) -> None:
        assert apply(("missing", "x")).drifted is None


class TestTolerantMatching:
    """Exact, then trailing whitespace, then whitespace-normalised whole lines; never fuzzy."""

    def test_exact_matches_need_no_tolerance(self) -> None:
        assert apply(("ax.set_ylim(0, 100)", "ax.set_ylim(0, 50)")).tolerant == ()

    def test_trailing_blanks_in_find_or_code_are_ignored(self) -> None:
        working = WORKING.replace("ax.set_ylim(0, 100)\n", "ax.set_ylim(0, 100)   \n")

        result = apply(
            ('ax.plot(df["x"], df["y"], color=IMPRINT[0])  \nax.set_ylim(0, 100)\n', "ax.grid()\n"), working=working
        )

        assert result.failures == [] and result.tolerant == ("trailing_whitespace",)
        assert result.code == WORKING.replace(
            'ax.plot(df["x"], df["y"], color=IMPRINT[0])\nax.set_ylim(0, 100)\n', "ax.grid()\n"
        )

    def test_windows_line_breaks_in_find_are_read_as_newlines(self) -> None:
        result = apply(("color=IMPRINT[0])\r\nax.set_ylim(0, 100)", "color=IMPRINT[0])\nax.set_ylim(0, 50)"))

        assert result.failures == [] and result.tolerant == ("trailing_whitespace",)
        assert result.code == WORKING.replace("ax.set_ylim(0, 100)", "ax.set_ylim(0, 50)")

    def test_a_block_written_with_less_indentation_is_found_and_the_replacement_indented(self) -> None:
        working = WORKING.replace(
            "ax.set_ylim(0, 100)\n", "for low in (0, 10):\n    ax.set_ylim(low, 100)\n    ax.grid(True)\n"
        )

        result = apply(
            ("ax.set_ylim(low, 100)\nax.grid(True)\n", "ax.set_ylim(low, 90)\nax.grid(False)\n"), working=working
        )

        assert result.failures == [] and result.tolerant == ("whitespace",)
        assert result.code == working.replace(
            "    ax.set_ylim(low, 100)\n    ax.grid(True)\n", "    ax.set_ylim(low, 90)\n    ax.grid(False)\n"
        )

    def test_a_block_written_with_more_indentation_is_moved_back(self) -> None:
        result = apply(
            ('    ax.plot(df["x"],  df["y"], color=IMPRINT[0])\n    ax.set_ylim(0, 100)\n', "    ax.set_ylim(0, 50)\n")
        )

        assert result.failures == [] and result.tolerant == ("whitespace",)
        assert result.code == WORKING.replace(
            'ax.plot(df["x"], df["y"], color=IMPRINT[0])\nax.set_ylim(0, 100)\n', "ax.set_ylim(0, 50)\n"
        )

    def test_lines_without_one_shared_indentation_shift_do_not_match(self) -> None:
        working = WORKING.replace("ax.set_ylim(0, 100)\n", "for low in (0, 10):\n    ax.set_ylim(low, 100)\n")

        result = apply(("    for low in (0, 10):\n    ax.set_ylim(low, 100)\n", "pass\n"), working=working)

        assert result.kinds == ("zero_match",) and result.tolerant == ()

    def test_words_must_agree_exactly(self) -> None:
        """Never fuzzy: one changed character is no match, however close."""
        assert apply(("ax.set_ylim(0, 10)\n", "x\n")).kinds == ("zero_match",)
        assert apply(("ax.set_ylim(0,100)\n", "x\n")).kinds == ("zero_match",)

    def test_several_tolerant_matches_are_a_multi_match(self) -> None:
        """The first tier that finds anything decides; two candidates there are never resolved by guessing."""
        grid = "ax.grid(True, alpha=0.3)"
        working = WORKING.replace("ax.set_ylim(0, 100)\n", f"if df.empty:\n    {grid}\nelse:\n    {grid}\n")

        trailing = apply((f"{grid}  \n", "x\n"), working=working)
        spaced = apply(("ax.grid(True,  alpha=0.3)\n", "ax.grid(False)\n"), working=working)

        assert trailing.kinds == ("multi_match",) and spaced.kinds == ("multi_match",)
        assert trailing.failures[0].startswith("edit 1/1: find matches 2 times")

    def test_a_tolerant_match_still_respects_the_protected_regions(self) -> None:
        result = apply(
            ('    ax.set_ylim(0, 100)\n    plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)', "    x")
        )

        assert result.kinds == ("protected:savefig",)

    def test_a_replacement_that_lacks_the_indentation_to_remove_is_no_match(self) -> None:
        """Moving `replace` back by four spaces is impossible when a line of it has none: no safe placement."""
        assert apply(("    ax.set_ylim(0, 100)\n", "ax.set_ylim(0, 50)\n")).kinds == ("zero_match",)

    @pytest.mark.parametrize(
        ("code", "find"),
        [
            ('ax.set_title("North America")\n', 'ax.set_title("North  America")\n'),
            ('ax.set_title("North  America")\n', 'ax.set_title("North America")\n'),
            ("ax.text(0, 0, '# of  runs')\n", "ax.text(0, 0, '# of runs')\n"),
            ('ax.text(0, 0, "say \\"a  b\\"")\n', 'ax.text(0, 0, "say \\"a b\\"")\n'),
        ],
    )
    def test_blanks_inside_a_string_literal_must_agree(self, code: str, find: str) -> None:
        """A literal's text is the plot's text: other blanks inside it are other code, not a tolerable typo."""
        working = WORKING.replace("ax.set_ylim(0, 100)\n", code)

        assert apply((find, "x\n"), working=working).kinds == ("zero_match",)

    def test_blanks_between_tokens_still_vary_next_to_a_string_literal(self) -> None:
        working = WORKING.replace("ax.set_ylim(0, 100)\n", 'ax.set_title("North  America", fontsize=12)  # top\n')

        result = apply(
            ('ax.set_title("North  America",   fontsize=12) #  top\n', 'ax.set_title("Europe")\n'), working=working
        )

        assert result.failures == [] and result.tolerant == ("whitespace",)
        assert result.code == working.replace(
            'ax.set_title("North  America", fontsize=12)  # top\n', 'ax.set_title("Europe")\n'
        )

    def test_a_failed_plan_still_names_the_tiers_its_other_edits_matched_in(self) -> None:
        """The log counts every tolerant match, also in a plan that a sibling edit or a drift fails."""
        sibling_failed = apply(("ax.set_ylim(0,  100)\n", "ax.set_ylim(0, 50)\n"), ("not in the code", "x"))
        drifted = apply(("ax.set_ylim(0,  100)\n", 'ax.set_ylim(0, 50)\nINK = "#000000"\n'))

        assert (sibling_failed.code, sibling_failed.kinds, sibling_failed.tolerant) == (
            None,
            ("zero_match",),
            ("whitespace",),
        )
        assert (drifted.code, drifted.kinds, drifted.tolerant) == (None, ("drift:rebind",), ("whitespace",))

    def test_a_line_inside_a_multi_line_string_literal_is_never_matched_by_its_words(self) -> None:
        working = WORKING.replace("ax.set_ylim(0, 100)\n", 'note = """first\n    second  line\n"""\n')

        assert apply(("second line\n", "x\n"), working=working).kinds == ("zero_match",)


def test_a_find_that_an_earlier_edit_already_changed_is_a_stale_match() -> None:
    result = apply(
        ("ax.set_ylim(0, 100)", "ax.set_ylim(0, 50)"), ("ax.set_ylim(0, 100)\nplt", "ax.set_ylim(0, 90)\nplt")
    )

    assert result.kinds == ("stale_match",) and set(result.kinds) <= FAILURE_KINDS
    assert result.failures[0].startswith("edit 2/2: find matches the code only as it was before an earlier edit")
    assert "merge the two edits into one" in result.failures[0]


def test_a_stale_find_is_recognised_in_a_tolerant_tier_too() -> None:
    """A stale find written with other blanks than the code gets the stale-match line, not the zero-match one."""
    result = apply(("ax.set_ylim(0, 100)", "ax.set_ylim(0, 50)"), ("ax.set_ylim(0,  100)\n", "ax.set_ylim(0, 90)\n"))

    assert result.kinds == ("stale_match",)
