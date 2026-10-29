"""The edit applier on R working forms (`code/edits.py` with the ggplot2 dialect), and the R export header."""

import pytest

from agents.anyplot.code.edits import apply_plan, dialect_for, new_literals, protected_drift, restore_protected
from agents.anyplot.code.export import R_RUN, export_code
from agents.anyplot.schemas import AdaptPlan, Edit

from .conftest import source


LIBRARY = "ggplot2"
WORKING = source("""
    library(ggplot2)

    THEME    <- Sys.getenv("ANYPLOT_THEME", "light")
    PAGE_BG  <- if (THEME == "light") "#FAF8F1" else "#1A1A17"
    INK      <- if (THEME == "light") "#1A1A17" else "#F0EFE8"
    IMPRINT_PALETTE <- c("#009E73", "#C475FD")

    SALES <- "Sales"  # role: y
    df <- load_user_data()
    p <- ggplot(df, aes(x = .data[["Month"]], y = .data[[SALES]])) +
      geom_col(fill = IMPRINT_PALETTE[1]) +
      labs(title = "Sales by month", x = "Month") +
      theme(plot.background = element_rect(fill = PAGE_BG))
    ggsave(
      filename = sprintf("plot-%s.png", THEME),
      plot     = p,
      device   = ragg::agg_png,
      width    = 8,
      height   = 4.5,
      units    = "in",
      dpi      = 400
    )
""")


def plan(*edits: tuple[str, str]) -> AdaptPlan:
    return AdaptPlan(edits=[Edit(find=find, replace=replace) for find, replace in edits])


def test_an_edit_applies() -> None:
    applied = apply_plan(WORKING, plan(('title = "Sales by month"', 'title = "Revenue"')), library=LIBRARY)

    assert applied.failures == [] and applied.code is not None
    assert 'title = "Revenue"' in applied.code


@pytest.mark.parametrize(
    ("find", "kind", "words"),
    [
        ('PAGE_BG  <- if (THEME == "light") "#FAF8F1"', "protected:theme_token", "theme token PAGE_BG"),
        ('THEME    <- Sys.getenv("ANYPLOT_THEME", "light")', "protected:theme", "THEME assignment"),
        ("  dpi      = 400", "protected:savefig", "final ggsave statement"),
        ("df <- load_user_data()", "protected:placeholder", "df <- load_user_data() line"),
    ],
)
def test_protected_regions_refuse_an_edit(find: str, kind: str, words: str) -> None:
    applied = apply_plan(WORKING, plan((find, "x <- 1")), library=LIBRARY)

    assert applied.code is None and applied.kinds == (kind,)
    assert words in applied.failures[0]


def test_the_whitespace_tier_reads_r_strings_across_lines_and_raw_strings() -> None:
    code = WORKING.replace(
        'labs(title = "Sales by month", x = "Month")', 'labs(title = r"(Sales  "by" month)", x = "a\nb")'
    )
    applied = apply_plan(
        code, plan(('labs(title = r"(Sales  "by" month)",   x = "a', 'labs(title = "T", x = "a')), library=LIBRARY
    )

    assert applied.failures == [] and applied.code is not None
    assert 'labs(title = "T", x = "a\nb")' in applied.code


def test_drift_compares_meaning_not_spelling() -> None:
    restated = WORKING.replace(
        'PAGE_BG  <- if (THEME == "light") "#FAF8F1" else "#1A1A17"',
        "PAGE_BG <- if (THEME == 'light') '#FAF8F1' else '#1A1A17'  # same value",
    )
    changed = WORKING.replace('"#FAF8F1" else "#1A1A17"', '"#FF00FF" else "#1A1A17"')

    assert protected_drift(WORKING, restated, library=LIBRARY) == []
    assert protected_drift(WORKING, changed, library=LIBRARY)[0].startswith(
        "the plan changes or removes the protected theme token PAGE_BG"
    )


@pytest.mark.parametrize(
    "addition", ['PAGE_BG <- "#FF00FF"', "f <- function(THEME) 1", "for (INK in 1:2) 1", 'names(INK) <- "x"']
)
def test_a_theme_name_bound_again_is_drift(addition: str) -> None:
    code = WORKING.replace("p <- ggplot", f"{addition}\np <- ggplot")
    applied = apply_plan(WORKING, AdaptPlan(full_code=code), library=LIBRARY)

    assert applied.code is None and "drift:rebind" in applied.kinds
    assert applied.failures[-1] == (
        "keep the THEME assignment, the theme tokens and the final ggsave exactly as in the current code"
    )


def test_restore_puts_the_protected_save_back() -> None:
    drifted = WORKING.replace("dpi      = 400", "dpi      = 72").replace('"Sales by month"', '"Revenue"')
    applied = apply_plan(WORKING, AdaptPlan(full_code=drifted), library=LIBRARY)

    assert applied.kinds == ("drift:savefig",) and applied.drifted == drifted
    restored = restore_protected(WORKING, drifted, library=LIBRARY)
    assert restored == WORKING.replace('"Sales by month"', '"Revenue"')


def test_a_rebind_is_never_restored() -> None:
    drifted = WORKING.replace("p <- ggplot", 'INK <- "#FF00FF"\np <- ggplot')

    assert restore_protected(WORKING, drifted, library=LIBRARY) is None


def test_an_unparseable_working_form() -> None:
    applied = apply_plan("x <- (\n", plan(("x", "y")), library=LIBRARY)

    assert applied.kinds == ("working_unparseable",)
    assert applied.failures == ["the working form does not parse at line 1; no edit was applied"]


def test_new_literals_decode_r_strings() -> None:
    code = WORKING.replace('"Sales by month"', "'Revenue'").replace('x = "Month"', 'x = r"(Month)"')

    assert new_literals(WORKING, code, library=LIBRARY) == ["Revenue"]


def test_the_python_dialect_is_unchanged_and_an_unknown_library_is_refused() -> None:
    assert dialect_for("matplotlib").placeholder == "df = load_user_data()"
    assert dialect_for(LIBRARY).placeholder == "df <- load_user_data()"
    with pytest.raises(ValueError):
        dialect_for("ggplot3")


def test_the_r_export_names_rscript() -> None:
    exported = export_code("x <- 1\n", spec_id="scatter-basic", library=LIBRARY, library_version="4.0.3", run=R_RUN)

    assert exported == (
        "# Adapted by anyplot.ai from scatter-basic (ggplot2 4.0.3) for your data.csv;\n"
        "# run: ANYPLOT_THEME=light Rscript plot.R\n\nx <- 1\n"
    )
    with pytest.raises(ValueError, match="run command"):
        export_code("x <- 1\n", spec_id="scatter-basic", library=LIBRARY, library_version=None, run="rm -rf /")
