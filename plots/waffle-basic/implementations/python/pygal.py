"""anyplot.ai
waffle-basic: Basic Waffle Chart
Library: pygal | Python 3.13
Quality: pending | Created: 2025-05-05
"""

import os
import sys


THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

OKABE_ITO = ("#009E73", "#D55E00", "#0072B2", "#CC79A7", "#E69F00", "#56B4E9", "#F0E442")

_cwd = sys.path[0] if sys.path[0] else "."
if _cwd in sys.path:
    sys.path.remove(_cwd)

from pygal.graph.graph import Graph  # noqa: E402
from pygal.style import Style  # noqa: E402


sys.path.insert(0, _cwd)


class Waffle(Graph):
    _serie_margin = 0

    def __init__(self, *args, **kwargs):
        self.rows = kwargs.pop("rows", 10)
        self.cols = kwargs.pop("cols", 10)
        super().__init__(*args, **kwargs)

    def _plot(self):
        total = sum(sum(v for v in serie.values if v is not None) for serie in self.series)
        if total == 0:
            return

        total_squares = self.rows * self.cols

        plot_width = self.view.width
        plot_height = self.view.height

        square_size = min(plot_width / self.cols, plot_height / self.rows) * 0.85
        gap = square_size * 0.12

        grid_width = self.cols * (square_size + gap) - gap
        grid_height = self.rows * (square_size + gap) - gap

        x_start = self.view.x(0)
        y_start = self.view.y(self.rows)

        x_offset = x_start + (plot_width - grid_width) / 2
        y_offset = y_start + (plot_height - grid_height) / 2

        plot_node = self.nodes["plot"]
        waffle_group = self.svg.node(plot_node, class_="waffle-chart")

        square_index = 0
        for serie_index, serie in enumerate(self.series):
            serie_value = sum(v for v in serie.values if v is not None)
            num_squares = round(serie_value / total * total_squares)

            color = self.style.colors[serie_index % len(self.style.colors)]

            serie_group = self.svg.node(waffle_group, class_="series serie-%d color-%d" % (serie_index, serie_index))

            for _ in range(num_squares):
                if square_index >= total_squares:
                    break

                row = square_index // self.cols
                col = square_index % self.cols

                x = x_offset + col * (square_size + gap)
                y = y_offset + row * (square_size + gap)

                self.svg.node(
                    serie_group,
                    "rect",
                    x=x,
                    y=y,
                    width=square_size,
                    height=square_size,
                    fill=color,
                    rx=square_size * 0.1,
                    ry=square_size * 0.1,
                    class_="waffle-square reactive",
                )

                square_index += 1

    def _compute(self):
        self._box.xmin = 0
        self._box.xmax = self.cols
        self._box.ymin = 0
        self._box.ymax = self.rows


custom_style = Style(
    background=PAGE_BG,
    plot_background=PAGE_BG,
    foreground=INK,
    foreground_strong=INK,
    foreground_subtle=INK_MUTED,
    colors=OKABE_ITO,
    title_font_size=28,
    label_font_size=22,
    major_label_font_size=18,
    legend_font_size=16,
    value_font_size=14,
    stroke_width=3,
)

categories = {"Operations": 42, "Marketing": 28, "R&D": 18, "Admin": 12}

chart = Waffle(
    width=4800,
    height=2700,
    rows=10,
    cols=10,
    style=custom_style,
    title="Budget Allocation · waffle-basic · pygal · anyplot.ai",
    show_legend=True,
    legend_at_bottom=True,
    legend_at_bottom_columns=4,
    margin=80,
    margin_bottom=250,
    show_x_labels=False,
    show_y_labels=False,
)

for category, value in categories.items():
    chart.add(f"{category} ({value}%)", [value])

chart.render_to_png(f"plot-{THEME}.png")

with open(f"plot-{THEME}.html", "wb") as f:
    f.write(chart.render())
