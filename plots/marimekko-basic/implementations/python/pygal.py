""" anyplot.ai
marimekko-basic: Basic Marimekko Chart
Library: pygal 3.1.0 | Python 3.14.4
Quality: 86/100 | Updated: 2026-04-27
"""

import os
import sys


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"
GRID_COLOR = "#C8C6BC" if THEME == "light" else "#2E2E2A"

OKABE_ITO = ("#009E73", "#D55E00", "#0072B2", "#CC79A7", "#E69F00", "#56B4E9", "#F0E442")

# Temporarily remove current directory from path to avoid name collision with pygal module
_cwd = sys.path[0] if sys.path[0] else "."
if _cwd in sys.path:
    sys.path.remove(_cwd)

from pygal.graph.graph import Graph  # noqa: E402
from pygal.style import Style  # noqa: E402


# Restore path
sys.path.insert(0, _cwd)


# Custom class required: pygal has no native Marimekko/mekko chart type.
# Variable-width stacked bars require extending the Graph base class.
class Marimekko(Graph):
    _serie_margin = 0

    def __init__(self, *args, **kwargs):
        self.gap = kwargs.pop("gap", 0.02)
        self.ink = kwargs.pop("ink", INK)
        self.ink_muted = kwargs.pop("ink_muted", INK_MUTED)
        self.grid_color = kwargs.pop("grid_color", GRID_COLOR)
        super().__init__(*args, **kwargs)

    def _compute_x_labels(self):
        pass

    def _compute_y_labels(self):
        pass

    def _plot(self):
        if not self.series:
            return

        num_cols = len(self.series[0].values) if self.series else 0
        col_totals = [0] * num_cols

        for serie in self.series:
            for i, val in enumerate(serie.values):
                if val is not None:
                    col_totals[i] += val

        grand_total = sum(col_totals)
        if grand_total == 0:
            return

        plot_width = self.view.width
        plot_height = self.view.height

        total_gap = self.gap * plot_width * (num_cols - 1)
        usable_width = plot_width - total_gap
        gap_px = self.gap * plot_width

        x_start = self.view.x(0)
        y_bottom = self.view.y(0)

        plot_node = self.nodes["plot"]
        mekko_group = self.svg.node(plot_node, class_="marimekko-chart")

        x_pos = x_start

        for col_idx in range(num_cols):
            col_total = col_totals[col_idx]
            if col_total == 0:
                continue

            bar_width = (col_total / grand_total) * usable_width
            y_offset = 0

            for serie_idx, serie in enumerate(self.series):
                val = serie.values[col_idx] if col_idx < len(serie.values) else None
                if val is None or val == 0:
                    continue

                segment_height = (val / col_total) * plot_height
                color = self.style.colors[serie_idx % len(self.style.colors)]

                y_pos = y_bottom - y_offset - segment_height

                serie_group = self.svg.node(mekko_group, class_="series serie-%d color-%d" % (serie_idx, serie_idx))

                self.svg.node(
                    serie_group,
                    "rect",
                    x=x_pos,
                    y=y_pos,
                    width=bar_width,
                    height=segment_height,
                    fill=color,
                    stroke=PAGE_BG,
                    **{"stroke-width": "3", "class": "rect reactive tooltip-trigger"},
                )

                if segment_height > 90 and bar_width > 120:
                    pct = (val / col_total) * 100
                    label_y = y_pos + segment_height / 2
                    label_x = x_pos + bar_width / 2

                    self.svg.node(
                        serie_group,
                        "text",
                        x=label_x,
                        y=label_y,
                        fill="white",
                        **{
                            "text-anchor": "middle",
                            "dominant-baseline": "middle",
                            "font-size": "36",
                            "font-weight": "bold",
                        },
                    ).text = f"{pct:.0f}%"

                y_offset += segment_height

            x_pos += bar_width + gap_px

        # X-axis category labels
        if hasattr(self, "x_labels") and self.x_labels:
            x_pos = x_start
            for col_idx in range(num_cols):
                col_total = col_totals[col_idx]
                if col_total == 0:
                    continue

                bar_width = (col_total / grand_total) * usable_width
                label_x = x_pos + bar_width / 2
                label_y = y_bottom + 65

                label_group = self.svg.node(mekko_group, class_="x-labels")

                self.svg.node(
                    label_group,
                    "text",
                    x=label_x,
                    y=label_y,
                    fill=self.ink,
                    **{"text-anchor": "middle", "font-size": "42", "font-weight": "normal"},
                ).text = str(self.x_labels[col_idx]) if col_idx < len(self.x_labels) else ""

                width_pct = (col_total / grand_total) * 100
                self.svg.node(
                    label_group,
                    "text",
                    x=label_x,
                    y=label_y + 55,
                    fill=self.ink_muted,
                    **{"text-anchor": "middle", "font-size": "34", "font-style": "italic"},
                ).text = f"({width_pct:.0f}%)"

                x_pos += bar_width + gap_px

        # Y-axis percentage scale
        y_axis_group = self.svg.node(mekko_group, class_="y-axis-labels")
        for pct in [0, 25, 50, 75, 100]:
            y_pos = y_bottom - (pct / 100) * plot_height
            label_x = x_start - 25

            self.svg.node(
                y_axis_group,
                "text",
                x=label_x,
                y=y_pos + 5,
                fill=self.ink_muted,
                **{"text-anchor": "end", "font-size": "34"},
            ).text = f"{pct}%"

            if pct > 0:
                self.svg.node(
                    y_axis_group,
                    "line",
                    x1=x_start,
                    y1=y_pos,
                    x2=x_start + plot_width,
                    y2=y_pos,
                    stroke=self.grid_color,
                    **{"stroke-width": "1", "stroke-dasharray": "5,5"},
                )

        # Y-axis title
        y_title_x = x_start - 120
        y_title_y = y_bottom - plot_height / 2
        self.svg.node(
            y_axis_group,
            "text",
            x=y_title_x,
            y=y_title_y,
            fill=self.ink,
            **{
                "text-anchor": "middle",
                "font-size": "42",
                "font-weight": "normal",
                "transform": f"rotate(-90, {y_title_x}, {y_title_y})",
            },
        ).text = "Share within Region (%)"

    def _compute(self):
        self._box.xmin = 0
        self._box.xmax = 1
        self._box.ymin = 0
        self._box.ymax = 1


# Style
custom_style = Style(
    background=PAGE_BG,
    plot_background=PAGE_BG,
    foreground=INK,
    foreground_strong=INK,
    foreground_subtle=INK_MUTED,
    colors=OKABE_ITO,
    title_font_size=60,
    legend_font_size=48,
    label_font_size=42,
    value_font_size=36,
    font_family="sans-serif",
)

# Data - Market share by region and product line (revenue in millions USD)
regions = ["North America", "Europe", "Asia Pacific", "Latin America", "MEA"]

products = {
    "Enterprise": [180, 140, 200, 60, 40],
    "Consumer": [120, 130, 180, 70, 45],
    "SMB": [90, 70, 90, 35, 25],
    "Government": [60, 40, 50, 15, 10],
}

# Chart
chart = Marimekko(
    width=4800,
    height=2700,
    gap=0.015,
    ink=INK,
    ink_muted=INK_MUTED,
    grid_color=GRID_COLOR,
    style=custom_style,
    title="marimekko-basic · pygal · anyplot.ai",
    show_legend=True,
    legend_at_bottom=True,
    legend_at_bottom_columns=4,
    margin=80,
    margin_left=200,
    margin_bottom=340,
    show_x_labels=False,
    show_y_labels=False,
)

chart.x_labels = regions

for product_name, values in products.items():
    chart.add(product_name, values)

# Save
chart.render_to_png(f"plot-{THEME}.png")

html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>marimekko-basic · pygal · anyplot.ai</title>
    <style>
        body {{ margin: 0; padding: 20px; background: {PAGE_BG}; }}
        .container {{ max-width: 100%; margin: 0 auto; }}
        svg {{ max-width: 100%; height: auto; }}
    </style>
</head>
<body>
    <div class="container">
        {chart.render(is_unicode=True)}
    </div>
</body>
</html>"""

with open(f"plot-{THEME}.html", "w", encoding="utf-8") as f:
    f.write(html_content)
