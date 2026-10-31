"""Tests for agents/anyplot/code/figure.py: plotly's and bokeh's pinned figure save and the export's normal save."""

import ast
import re
from pathlib import Path

import pytest

from agents.anyplot.code.figure import (
    MAX_SIDE,
    MIN_SIDE,
    FigureSave,
    device_scale,
    export_form,
    figure_saves,
    json_save,
    match_figure_save,
    normal_save,
)

from .conftest import REPO_ROOT, source


def statement(code: str) -> ast.stmt:
    return ast.parse(code).body[0]


PLOTLY_SAVE = 'fig.update_layout(width=800, height=450).write_json(f"plot-{THEME}.json")'
BOKEH_SAVE = source("""
    with open(f"plot-{THEME}.json", "w", encoding="utf-8") as figure_file:
        json.dump(json_item(p), figure_file)
""")


class TestTheSaveIsPinned:
    def test_plotlys_save_with_and_without_a_size(self) -> None:
        assert match_figure_save(statement(PLOTLY_SAVE), "plotly") == FigureSave("plotly", "fig", (800, 450))
        assert match_figure_save(statement('chart.write_json(f"plot-{THEME}.json")'), "plotly") == FigureSave(
            "plotly", "chart"
        )
        reordered = 'fig.update_layout(height=450, width=800).write_json(f"plot-{THEME}.json")'
        assert match_figure_save(statement(reordered), "plotly") == FigureSave("plotly", "fig", (800, 450))

    def test_bokehs_save(self) -> None:
        assert match_figure_save(statement(BOKEH_SAVE), "bokeh") == FigureSave("bokeh", "p", handle="figure_file")

    @pytest.mark.parametrize(
        "code",
        [
            'fig.write_json("plot-light.json")',
            'fig.write_json(f"plot-{THEME}.png")',
            'fig.write_json(f"plot-{THEME!r}.json")',
            'fig.write_json(f"out/plot-{THEME}.json")',
            'fig.write_json(f"plot-{THEME}.json", pretty=True)',
            'fig.write_json(file=f"plot-{THEME}.json")',
            'fig.layout.write_json(f"plot-{THEME}.json")',
            'make().write_json(f"plot-{THEME}.json")',
            'fig.update_layout(width=800).write_json(f"plot-{THEME}.json")',
            'fig.update_layout(width=800, height=450, title="x").write_json(f"plot-{THEME}.json")',
            'fig.update_layout(width=800.0, height=450).write_json(f"plot-{THEME}.json")',
            'fig.update_layout(width=W, height=450).write_json(f"plot-{THEME}.json")',
            'fig.update_layout(width=True, height=450).write_json(f"plot-{THEME}.json")',
            f'fig.update_layout(width={MIN_SIDE - 1}, height=450).write_json(f"plot-{{THEME}}.json")',
            f'fig.update_layout(width={MAX_SIDE + 1}, height=450).write_json(f"plot-{{THEME}}.json")',
            'fig.update_layout({"width": 800}, height=450).write_json(f"plot-{THEME}.json")',
            'x = fig.write_json(f"plot-{THEME}.json")',
        ],
    )
    def test_any_other_plotly_shape_is_no_figure_save(self, code: str) -> None:
        assert match_figure_save(statement(code), "plotly") is None

    @pytest.mark.parametrize(
        ("old", "new"),
        [
            ('f"plot-{THEME}.json"', '"plot-light.json"'),
            ('"w"', '"a"'),
            ('"w", encoding="utf-8"', 'mode="w", encoding="utf-8"'),
            ('encoding="utf-8"', 'encoding="latin-1"'),
            ('encoding="utf-8"', 'encoding="utf-8", newline=""'),
            ("json.dump(", "json.dumps("),
            ("json.dump(", "other.dump("),
            ("json_item(p)", "json_item(p, 'target')"),
            ("json_item(p)", "json_item(p.children)"),
            ("json_item(p)", "json_item(figure_file)"),
            ("json_item(p)", "json_item(THEME)"),
            ("json_item(p)", "json_item(open)"),
            ("as figure_file", "as json"),
            (", figure_file)", ", other)"),
            ("open(", "io.open("),
            ('open(f"plot-{THEME}.json", "w", encoding="utf-8")', "open()"),
            ('open(f"plot-{THEME}.json", "w", encoding="utf-8")', 'open(f"plot-{THEME}.json")'),
        ],
    )
    def test_any_other_bokeh_shape_is_no_figure_save(self, old: str, new: str) -> None:
        assert old in BOKEH_SAVE
        assert match_figure_save(statement(BOKEH_SAVE.replace(old, new, 1)), "bokeh") is None

    def test_a_second_statement_in_the_with_body_is_no_figure_save(self) -> None:
        code = BOKEH_SAVE + "        figure_file.write('x')\n"
        assert match_figure_save(statement(code.replace("        figure", "    figure")), "bokeh") is None

    def test_only_module_level_saves_count(self) -> None:
        tree = ast.parse(f"if True:\n    {PLOTLY_SAVE}\n{PLOTLY_SAVE}\n")
        assert [found.name for _, found in figure_saves(tree, "plotly")] == ["fig"]

    def test_the_emitted_statements_match(self) -> None:
        for kind, name, size in (("plotly", "fig", (1600, 900)), ("plotly", "fig", None), ("bokeh", "layout", None)):
            found = match_figure_save(statement(json_save(kind, name, size)), kind)
            assert found is not None and found.name == name and found.size == size


class TestTheDeviceScale:
    @pytest.mark.parametrize(
        ("size", "scale"),
        [
            ((800, 450), 4),
            ((1600, 900), 2),
            ((4800, 2700), 2 / 3),
            ((3200, 1800), 1),
            ((600, 600), 4),
            ((1200, 1200), 2),
            ((3600, 3600), 2 / 3),
            ((800, 600), 3200 / 1072),  # 4:3 is landscape, padded to 16:9 and rounded up to 16 px
            ((600, 800), 3),  # narrower than 4:3: the square canvas of the larger side
        ],
    )
    def test_the_figure_modes_rule(self, size: tuple[int, int], scale: float) -> None:
        assert device_scale(*size) == pytest.approx(scale)

    def test_it_is_render_mjs_rule(self) -> None:
        """The rule the export reproduces is the figure mode's (`render.mjs`, `figureCanvas`), side for side."""
        harness = (REPO_ROOT / "automation" / "js-render" / "render.mjs").read_text(encoding="utf-8")
        assert "if (3 * size.width < 4 * size.height) {" in harness
        assert "const width = 16 * Math.ceil(Math.max(size.width, (size.height * 16) / 9) / 16);" in harness
        assert f"const FIGURE_MIN_SIDE = {MIN_SIDE};" in harness and f"const FIGURE_MAX_SIDE = {MAX_SIDE};" in harness


class TestTheExport:
    def test_plotlys_normal_save_reproduces_the_chats_canvas(self) -> None:
        assert normal_save(FigureSave("plotly", "fig", (800, 450))) == (
            'fig.write_image(f"plot-{THEME}.png", width=800, height=450, scale=4)\n'
            'fig.write_html(f"plot-{THEME}.html", include_plotlyjs="cdn")'
        )
        assert "width=1600, height=900, scale=2)" in normal_save(FigureSave("plotly", "fig", (1600, 900)))
        assert "width=4800, height=2700, scale=0.6667)" in normal_save(FigureSave("plotly", "fig", (4800, 2700)))
        assert normal_save(FigureSave("plotly", "fig")).startswith('fig.write_image(f"plot-{THEME}.png", scale=2)\n')

    def test_bokehs_normal_save_is_the_catalogues(self) -> None:
        assert normal_save(FigureSave("bokeh", "p", handle="figure_file")) == (
            'export_png(p, filename=f"plot-{THEME}.png")\noutput_file(f"plot-{THEME}.html")\nsave(p)'
        )

    def test_plotlys_export_swaps_the_last_save(self) -> None:
        run_form = f'import os\n\nTHEME = os.getenv("ANYPLOT_THEME", "light")\n# Save\n{PLOTLY_SAVE}\n'
        exported = export_form(run_form, "plotly")

        assert exported == (
            'import os\n\nTHEME = os.getenv("ANYPLOT_THEME", "light")\n# Save\n'
            'fig.write_image(f"plot-{THEME}.png", width=800, height=450, scale=4)\n'
            'fig.write_html(f"plot-{THEME}.html", include_plotlyjs="cdn")\n'
        )
        assert export_form(exported, "plotly") == exported

    def test_bokehs_export_swaps_the_save_and_its_imports(self) -> None:
        run_form = (
            source("""
            import json
            import os

            from bokeh.embed import json_item
            from bokeh.plotting import figure

            THEME = os.getenv("ANYPLOT_THEME", "light")
            p = figure(width=4800, height=2700)
        """)
            + BOKEH_SAVE
        )
        exported = export_form(run_form, "bokeh")

        assert exported == source("""
            import os

            from bokeh.io import export_png, output_file, save
            from bokeh.plotting import figure

            THEME = os.getenv("ANYPLOT_THEME", "light")
            p = figure(width=4800, height=2700)
            export_png(p, filename=f"plot-{THEME}.png")
            output_file(f"plot-{THEME}.html")
            save(p)
        """)
        assert export_form(exported, "bokeh") == exported

    def test_bokehs_export_keeps_imports_something_else_reads(self) -> None:
        run_form = "import json\nimport os\n\nlabels = json.loads('[]')\n" + BOKEH_SAVE
        exported = export_form(run_form, "bokeh")

        assert exported.startswith("import json\nimport os\nfrom bokeh.io import export_png, output_file, save\n")
        assert "json.loads" in exported and "json.dump(" not in exported

    def test_a_run_form_without_a_save_or_that_does_not_parse_stays(self) -> None:
        assert export_form("fig.show()\n", "plotly") == "fig.show()\n"
        assert export_form("def (\n", "bokeh") == "def (\n"

    @pytest.mark.parametrize("library", ["plotly", "bokeh"])
    def test_every_normalised_catalogue_file_exports_a_normal_save_that_parses(self, library: str) -> None:
        """The swap on all 650 catalogue files through the normaliser: every pinned save becomes the normal save, and
        no JSON save is left."""
        from agents.anyplot.code.normalise import normalise

        normal = "write_image(" if library == "plotly" else "export_png("
        swapped = 0
        for path in sorted(Path(REPO_ROOT).glob(f"plots/*/implementations/python/{library}.py")):
            normalised = normalise(path.read_text(encoding="utf-8"), library=library)
            exported = export_form(normalised, library)  # type: ignore[arg-type]
            ast.parse(exported)
            if figure_saves(ast.parse(normalised), library):  # type: ignore[arg-type]
                swapped += 1
                assert normal in exported and not re.search(r"plot-\{THEME\}\.json", exported), path
        assert swapped >= 318
