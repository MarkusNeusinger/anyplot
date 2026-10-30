"""The edit applier on JavaScript working forms (`code/edits.py` with the JavaScript dialect), and the export header."""

import pytest

from agents.anyplot.code.edits import (
    FAILURE_KINDS,
    JAVASCRIPT_LIBRARIES,
    apply_plan,
    dialect_for,
    new_literals,
    protected_drift,
    restore_protected,
)
from agents.anyplot.code.export import SCRIPT_RUN, export_code
from agents.anyplot.schemas import AdaptPlan, Edit

from .conftest import JS_WORKING, MUIX_WORKING


LIBRARY = "chartjs"
WORKING = JS_WORKING
REMINDER = "keep the token lines and the //# anyplot-orientation directive exactly as in the current code"


def plan(*edits: tuple[str, str]) -> AdaptPlan:
    return AdaptPlan(edits=[Edit(find=find, replace=replace) for find, replace in edits])


def test_an_edit_applies() -> None:
    applied = apply_plan(WORKING, plan(('text: "Umsatz nach Ausgaben"', 'text: "Revenue"')), library=LIBRARY)

    assert applied.failures == [] and applied.code is not None
    assert 'text: "Revenue"' in applied.code


@pytest.mark.parametrize(
    ("find", "kind", "words"),
    [
        ("const t = window.ANYPLOT_TOKENS;", "protected:theme_token", "theme token t"),
        ("const { width, height } = window.ANYPLOT_SIZE;", "protected:theme_token", "theme token width, height"),
        ('isDark ? "#A8A79F"', "protected:theme_token", "theme token MUTED"),
        ("//# anyplot-orientation: square", "protected:savefig", "protected //# anyplot-orientation directive at"),
        ("const data = loadUserData();", "protected:placeholder", "const data = loadUserData(); line"),
    ],
)
def test_protected_regions_refuse_an_edit(find: str, kind: str, words: str) -> None:
    applied = apply_plan(WORKING, plan((find, "const x = 1;")), library=LIBRARY)

    assert applied.code is None and applied.kinds == (kind,)
    assert words in applied.failures[0]
    if kind != "protected:placeholder":
        assert (
            "the token lines (window.ANYPLOT_TOKENS, _THEME, _SIZE), the const data = loadUserData(); line and "
            in (applied.failures[0])
        )


def test_the_whitespace_tier_reads_javascript_comments_and_keeps_a_hash_in_a_string() -> None:
    code = WORKING.replace('grid: { color: "#00000022" } },', 'grid: {   color: "#00000022" } },  // a  comment')
    applied = apply_plan(
        code,
        plan(('x: { title: { display: true, text: SPEND }, grid: { color: "#00000022" } }, // a comment', "x: {},")),
        library=LIBRARY,
    )

    assert applied.failures == [] and applied.tolerant == ("whitespace",)
    assert applied.code is not None and "\n      x: {},\n" in applied.code


def test_a_hash_in_a_string_stays_text_in_the_whitespace_tier() -> None:
    code = WORKING.replace('grid: { color: "#00000022" }', 'grid: { color: "#0000  0022" }')
    applied = apply_plan(
        code,
        plan(('      x: { title: { display: true, text: SPEND }, grid: { color: "#0000 0022" } },', "x: {},")),
        library=LIBRARY,
    )

    assert applied.code is None and applied.kinds == ("zero_match",)


def test_a_block_comment_across_lines_opens_no_literal() -> None:
    """A backtick in a block comment would open a template that spans lines; inside the comment it is text."""
    code = WORKING.replace("// Plot: reads only", "/* a `b\n   stop  it */\n// Plot: reads only")
    applied = apply_plan(code, plan(("/* a `b\n   stop it */\n", "/* x */\n")), library=LIBRARY)

    assert applied.failures == [] and applied.tolerant == ("whitespace",)
    assert applied.code is not None and "/* x */\n// Plot" in applied.code


def test_a_template_spans_lines_in_the_whitespace_tier() -> None:
    code = WORKING.replace('text: "Umsatz nach Ausgaben"', "text: `Umsatz  nach\nAusgaben`")
    applied = apply_plan(
        code,
        plan(
            (
                "plugins: { title: { display: true,   text: `Umsatz  nach",
                "plugins: { title: { display: true, text: `Umsatz nach",
            )
        ),
        library=LIBRARY,
    )

    assert applied.failures == [] and applied.code is not None
    assert "text: `Umsatz nach\nAusgaben`" in applied.code


def test_drift_compares_meaning_not_spelling() -> None:
    restated = WORKING.replace(
        'const MUTED = isDark ? "#A8A79F" : "#6B6A63";', "const MUTED = isDark\n  ? '#A8A79F'\n  : '#6B6A63'; // same"
    )
    changed = WORKING.replace('"#A8A79F" : "#6B6A63"', '"#FF00FF" : "#6B6A63"')
    landscape = WORKING.replace("//# anyplot-orientation: square", "//# anyplot-orientation: landscape")
    spelled = WORKING.replace("//# anyplot-orientation: square", "//#   anyplot-orientation:  square")

    assert protected_drift(WORKING, restated, library=LIBRARY) == []
    assert protected_drift(WORKING, spelled, library=LIBRARY) == []
    assert protected_drift(WORKING, changed, library=LIBRARY)[0].startswith(
        "the plan changes or removes the protected theme token MUTED"
    )
    assert protected_drift(WORKING, landscape, library=LIBRARY) == [
        "the plan changes or removes the protected //# anyplot-orientation directive",
        REMINDER,
    ]


def test_a_removed_directive_is_drift() -> None:
    removed = WORKING.replace("//# anyplot-orientation: square\n", "")
    applied = apply_plan(WORKING, AdaptPlan(full_code=removed), library=LIBRARY)

    assert applied.code is None and applied.kinds == ("drift:savefig",)


@pytest.mark.parametrize(
    "addition", ["const t = {};", "let MUTED = 1;", "function isDark() {}", "var width = 2;", "class t {}"]
)
def test_a_token_bound_again_at_the_top_level_is_drift(addition: str) -> None:
    code = WORKING.replace("// Plot: reads only", f"{addition}\n// Plot: reads only")
    applied = apply_plan(WORKING, AdaptPlan(full_code=code), library=LIBRARY)

    assert applied.code is None and "drift:rebind" in applied.kinds
    assert applied.failures[-1] == REMINDER


@pytest.mark.parametrize(
    "addition", ["const f = (t) => t * 2;", "function g(width) { return width; }", "const THEME = 1;"]
)
def test_a_parameter_that_shadows_a_token_is_no_drift(addition: str) -> None:
    code = WORKING.replace("// Plot: reads only", f"{addition}\n// Plot: reads only")
    applied = apply_plan(WORKING, AdaptPlan(full_code=code), library=LIBRARY)

    assert applied.failures == [] and applied.code == code


def test_restore_puts_the_directive_back() -> None:
    drifted = WORKING.replace("anyplot-orientation: square", "anyplot-orientation: landscape").replace(
        '"Umsatz nach Ausgaben"', '"Revenue"'
    )
    applied = apply_plan(WORKING, AdaptPlan(full_code=drifted), library=LIBRARY)

    assert applied.kinds == ("drift:savefig",) and applied.drifted == drifted
    assert restore_protected(WORKING, drifted, library=LIBRARY) == WORKING.replace(
        '"Umsatz nach Ausgaben"', '"Revenue"'
    )


def test_restore_puts_a_token_back() -> None:
    drifted = WORKING.replace("const t = window.ANYPLOT_TOKENS;", "const t = window.ANYPLOT_TOKENS || {};")

    assert restore_protected(WORKING, drifted, library=LIBRARY) == WORKING


def test_a_rebind_is_never_restored() -> None:
    drifted = WORKING.replace("// Plot: reads only", 'var MUTED = "#FF00FF";\n// Plot: reads only')

    assert restore_protected(WORKING, drifted, library=LIBRARY) is None


def test_an_unparseable_working_form() -> None:
    applied = apply_plan("const a = (;\n", plan(("a", "b")), library=LIBRARY)

    assert applied.kinds == ("working_unparseable",)
    assert applied.failures == ["the working form does not parse at line 1; no edit was applied"]


def test_new_literals_decode_strings_templates_and_jsx_text() -> None:
    code = MUIX_WORKING.replace("Umsatz nach Ausgaben</Typography>", "Revenue by spend</Typography>").replace(
        'const Y = "Umsatz";', "const Y = `Revenue \\u0024`;"
    )

    assert new_literals(MUIX_WORKING, code, library="muix") == ["Revenue $", "Revenue by spend"]


def test_the_muix_dialect_reads_tsx() -> None:
    applied = apply_plan(MUIX_WORKING, plan(("height={height - 40}", "height={height - 60}")), library="muix")

    assert applied.failures == [] and applied.code is not None and "height - 60" in applied.code


def test_every_failure_kind_stays_in_the_closed_set() -> None:
    applied = apply_plan(WORKING, plan(("//# anyplot-orientation: square", "x"), ("nope", "x")), library=LIBRARY)

    assert set(applied.kinds) <= FAILURE_KINDS


def test_the_dialects() -> None:
    assert JAVASCRIPT_LIBRARIES == {"chartjs", "d3", "echarts", "highcharts", "muix"}
    assert dialect_for(LIBRARY).placeholder == "const data = loadUserData();"
    assert dialect_for("matplotlib").placeholder == "df = load_user_data()"
    assert dialect_for("ggplot2").placeholder == "df <- load_user_data()"
    assert dialect_for("makie").save_word == "save" and dialect_for("makie").saved() == "final save statement"


@pytest.mark.parametrize(("library", "version"), [("chartjs", "4.4.7"), ("muix", "9.16.0")])
def test_the_javascript_export_names_the_page_not_node(library: str, version: str) -> None:
    exported = export_code(
        "const a = 1;\n", spec_id="scatter-basic", library=library, library_version=version, run=SCRIPT_RUN
    )

    assert exported == (
        f"// Adapted by anyplot.ai from scatter-basic ({library} {version}) for your data.csv;\n"
        "// run: open plot.html in a browser, which runs this code with the chart library, the light theme and your "
        "data\n\nconst a = 1;\n"
    )
    assert export_code(exported, spec_id="scatter-basic", library=library, library_version=version, run=SCRIPT_RUN) == (
        exported
    )
    dark = export_code(
        exported, spec_id="scatter-basic", library=library, library_version=version, theme="dark", run=SCRIPT_RUN
    )
    assert "the dark theme" in dark and dark.count("// Adapted by anyplot.ai") == 1
