"""The edit applier on Julia working forms (`code/edits.py` with the Makie dialect), and the Julia export header."""

import pytest

from agents.anyplot.code.edits import apply_plan, dialect_for, new_literals, protected_drift, restore_protected
from agents.anyplot.code.export import JULIA_RUN, export_code
from agents.anyplot.schemas import AdaptPlan, Edit

from .conftest import JULIA_WORKING


LIBRARY = "makie"
WORKING = JULIA_WORKING


def plan(*edits: tuple[str, str]) -> AdaptPlan:
    return AdaptPlan(edits=[Edit(find=find, replace=replace) for find, replace in edits])


def test_an_edit_applies() -> None:
    applied = apply_plan(WORKING, plan(('title = "Umsatz nach Ausgaben"', 'title = "Revenue"')), library=LIBRARY)

    assert applied.failures == [] and applied.code is not None
    assert 'title = "Revenue"' in applied.code


@pytest.mark.parametrize(
    ("find", "kind", "words"),
    [
        ('const PAGE_BG  = THEME == "light"', "protected:theme_token", "theme token PAGE_BG"),
        ('INK            = THEME == "light"', "protected:theme_token", "theme token INK"),
        ('const THEME    = get(ENV, "ANYPLOT_THEME", "light")', "protected:theme", "THEME assignment"),
        ("fig; px_per_unit = 2", "protected:savefig", "final save statement"),
        ("df = load_user_data()", "protected:placeholder", "df = load_user_data() line"),
    ],
)
def test_protected_regions_refuse_an_edit(find: str, kind: str, words: str) -> None:
    applied = apply_plan(WORKING, plan((find, "x = 1")), library=LIBRARY)

    assert applied.code is None and applied.kinds == (kind,)
    assert words in applied.failures[0]


def test_the_whitespace_tier_reads_julia_strings_across_lines() -> None:
    code = WORKING.replace('title = "Umsatz nach Ausgaben"', 'title = "Umsatz  nach\nAusgaben"')
    applied = apply_plan(
        code,
        plan(('ax = Axis(fig[1, 1];   title = "Umsatz  nach', 'ax = Axis(fig[1, 1]; title = "Umsatz nach')),
        library=LIBRARY,
    )

    assert applied.failures == [] and applied.code is not None
    assert 'title = "Umsatz nach\nAusgaben"' in applied.code


def test_drift_compares_meaning_not_spelling() -> None:
    restated = WORKING.replace(
        'const PAGE_BG  = THEME == "light" ? colorant"#FAF8F1" : colorant"#1A1A17"',
        'const PAGE_BG = THEME == "light" ?\n    colorant"#FAF8F1" : colorant"#1A1A17"  # same value',
    )
    changed = WORKING.replace('colorant"#FAF8F1" : colorant"#1A1A17"', 'colorant"#FF00FF" : colorant"#1A1A17"')
    unconst = WORKING.replace("const PAGE_BG  =", "PAGE_BG =")

    assert protected_drift(WORKING, restated, library=LIBRARY) == []
    assert protected_drift(WORKING, changed, library=LIBRARY)[0].startswith(
        "the plan changes or removes the protected theme token PAGE_BG"
    )
    assert protected_drift(WORKING, unconst, library=LIBRARY) != []


@pytest.mark.parametrize(
    "addition",
    ['PAGE_BG = colorant"#FF00FF"', "f(THEME) = 1", "for INK in 1:2\nend", "global ALPHA = 1.0", "g = (INK) -> 1"],
)
def test_a_theme_name_bound_again_is_drift(addition: str) -> None:
    code = WORKING.replace("fig = Figure", f"{addition}\nfig = Figure")
    applied = apply_plan(WORKING, AdaptPlan(full_code=code), library=LIBRARY)

    assert applied.code is None and "drift:rebind" in applied.kinds
    assert applied.failures[-1] == (
        "keep the THEME assignment, the theme tokens and the final save exactly as in the current code"
    )


def test_restore_puts_the_protected_save_back() -> None:
    drifted = WORKING.replace("px_per_unit = 2", "px_per_unit = 1").replace('"Umsatz nach Ausgaben"', '"Revenue"')
    applied = apply_plan(WORKING, AdaptPlan(full_code=drifted), library=LIBRARY)

    assert applied.kinds == ("drift:savefig",) and applied.drifted == drifted
    restored = restore_protected(WORKING, drifted, library=LIBRARY)
    assert restored == WORKING.replace('"Umsatz nach Ausgaben"', '"Revenue"')


def test_restore_puts_a_const_token_back() -> None:
    drifted = WORKING.replace("const ALPHA    = THEME", "ALPHA = THEME")

    assert restore_protected(WORKING, drifted, library=LIBRARY) == WORKING


def test_a_rebind_is_never_restored() -> None:
    drifted = WORKING.replace("fig = Figure", 'INK = colorant"#FF00FF"\nfig = Figure')

    assert restore_protected(WORKING, drifted, library=LIBRARY) is None


def test_an_unparseable_working_form() -> None:
    applied = apply_plan("x = (\n", plan(("x", "y")), library=LIBRARY)

    assert applied.kinds == ("working_unparseable",)
    assert applied.failures == ["the working form does not parse at line 1; no edit was applied"]


def test_new_literals_decode_julia_strings_and_count_macro_text() -> None:
    code = WORKING.replace('"Umsatz nach Ausgaben"', '"Revenue \\$"').replace(
        'colorant"#99B314",\n]', 'colorant"#99B314", colorant"#DDCC77",\n]'
    )

    assert new_literals(WORKING, code, library=LIBRARY) == ["#DDCC77", "Revenue $"]


def test_the_other_dialects_are_unchanged() -> None:
    assert dialect_for("matplotlib").placeholder == "df = load_user_data()"
    assert dialect_for("ggplot2").placeholder == "df <- load_user_data()"
    assert dialect_for(LIBRARY).placeholder == "df = load_user_data()"
    assert dialect_for(LIBRARY).save_word == "save"


def test_the_julia_export_names_the_catalogues_run_command() -> None:
    exported = export_code(
        "x = 1\n", spec_id="scatter-basic", library=LIBRARY, library_version="0.24.16", run=JULIA_RUN
    )

    assert exported == (
        "# Adapted by anyplot.ai from scatter-basic (makie 0.24.16) for your data.csv;\n"
        "# run: ANYPLOT_THEME=light julia --project=. plot.jl\n\nx = 1\n"
    )
    assert export_code(
        exported, spec_id="scatter-basic", library=LIBRARY, library_version="0.24.16", run=JULIA_RUN
    ) == (exported)
