"""anyplot.ai
heatmap-annotated: Annotated Heatmap
Library: pygal 3.1.3 | Python 3.13.14
Quality: pending | Updated: 2026-08-05
"""

import math
import os
from itertools import pairwise

import numpy as np
import pandas as pd
from pygal.graph.graph import Graph
from pygal.style import Style


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Imprint palette: all eight positions in canonical order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Constants
# Imprint diverging ramp for fields (colored cells): red, the page color at the midpoint, blue
DIV_FIELDS = [(0.0, "#AE3030"), (0.5, PAGE_BG), (1.0, "#4467A3")]
DARK_TEXT = "#1A1A17"  # annotation on pale cells
LIGHT_TEXT = "#FAF8F1"  # annotation on dark cells

# Columns: set these to your table's labels
X_LABEL = "Variable"  # role: x
Y_LABEL = "Variable"  # role: y
VALUE = "Correlation"  # role: value

# Data: replace this block with your own square table, for example df = pd.read_csv("matrix.csv", index_col=0)
# Correlation matrix of business metrics (symmetric, diagonal = 1.0); R&D spend competes with
# marketing budget and briefly disrupts satisfaction, hence the mild negative values.
variables = ["Revenue", "Marketing", "R&D Spend", "Customers", "Satisfaction", "Retention"]
df = pd.DataFrame(
    [
        [1.00, 0.85, 0.42, 0.78, 0.65, 0.72],
        [0.85, 1.00, -0.18, 0.68, 0.55, 0.62],
        [0.42, -0.18, 1.00, 0.28, -0.12, 0.38],
        [0.78, 0.68, 0.28, 1.00, 0.82, 0.88],
        [0.65, 0.55, -0.12, 0.82, 1.00, 0.75],
        [0.72, 0.62, 0.38, 0.88, 0.75, 1.00],
    ],
    index=variables,
    columns=variables,
)
df.columns.name = X_LABEL
df.index.name = Y_LABEL


# Plot: reads only df and the constants above
def ramp_color(stops, t):
    """The hex at t (0 to 1) along (position, hex) stops, blended linearly in sRGB."""
    if not math.isfinite(t):
        return "none"  # a missing value draws nothing, never the low end
    t = min(max(t, 0.0), 1.0)
    (p0, c0), (p1, c1) = next((a, b) for a, b in pairwise(stops) if t <= b[0])
    share = (t - p0) / (p1 - p0)
    return "#" + "".join(
        f"{round(int(c0[i : i + 2], 16) * (1 - share) + int(c1[i : i + 2], 16) * share):02X}" for i in (1, 3, 5)
    )


class AnnotatedHeatmap(Graph):
    """pygal has no heatmap type: a Graph subclass that draws cells, labels and a colorbar as SVG nodes."""

    def __init__(self, *args, **kwargs):
        self.matrix_data = kwargs.pop("matrix_data")
        self.row_labels = kwargs.pop("row_labels")
        self.col_labels = kwargs.pop("col_labels")
        self.bar_title = kwargs.pop("bar_title")
        super().__init__(*args, **kwargs)

    def _compute(self):
        self._box.xmin = 0
        self._box.xmax = len(self.col_labels)
        self._box.ymin = 0
        self._box.ymax = len(self.row_labels)

    def _text(self, group, x, y, text, size, fill, weight="normal", anchor="start"):
        node = self.svg.node(group, "text", x=x, y=y)
        node.set("text-anchor", anchor)
        node.set("fill", fill)
        node.set("style", f"font-size:{size}px;font-weight:{weight};font-family:sans-serif")
        node.text = text
        return node

    def _plot(self):
        n_rows, n_cols = self.matrix_data.shape
        min_val = float(np.nanmin(self.matrix_data))
        max_val = float(np.nanmax(self.matrix_data))
        # Diverging scale centered on zero, at least the full -1..1 correlation domain
        span = max(1.0, float(np.nanmax(np.abs(self.matrix_data))))

        # Room for the labels around the grid
        margin_left, margin_bottom, margin_top, margin_right = 400, 230, 0, 280
        available_width = self.view.width - margin_left - margin_right
        available_height = self.view.height - margin_bottom - margin_top
        cell_width = available_width / n_cols * 0.95
        cell_height = available_height / n_rows * 0.95
        gap = min(cell_width, cell_height) * 0.03
        grid_width = n_cols * (cell_width + gap) - gap
        grid_height = n_rows * (cell_height + gap) - gap
        x_offset = self.view.x(0) + margin_left + (available_width - grid_width) / 2
        y_offset = self.view.y(n_rows) + margin_top + (available_height - grid_height) / 2

        group = self.svg.node(self.nodes["plot"], class_="annotated-heatmap")

        # Row labels on the left
        label_size = min(52, int(cell_height * 0.4))
        for i, label in enumerate(self.row_labels):
            y = y_offset + i * (cell_height + gap) + cell_height / 2
            self._text(group, x_offset - 25, y + label_size * 0.35, label, label_size, INK, "600", "end")

        # Column labels below the grid, rotated to fit
        for j, label in enumerate(self.col_labels):
            x = x_offset + j * (cell_width + gap) + cell_width / 2
            y = y_offset + n_rows * (cell_height + gap) + 25
            node = self._text(group, x, y, label, label_size, INK, "600")
            node.set("transform", f"rotate(45, {x}, {y})")

        # Cells with the value printed inside, the text switching with the cell's darkness
        value_size = min(52, int(min(cell_width, cell_height) * 0.4))
        for i in range(n_rows):
            for j in range(n_cols):
                value = float(self.matrix_data[i, j])
                color = ramp_color(DIV_FIELDS, (value / span + 1) / 2)
                x = x_offset + j * (cell_width + gap)
                y = y_offset + i * (cell_height + gap)
                rect = self.svg.node(group, "rect", x=x, y=y, width=cell_width, height=cell_height, rx=4, ry=4)
                rect.set("fill", color)
                rect.set("stroke", PAGE_BG)
                rect.set("stroke-width", "2")
                if color == "none":
                    continue
                red, green, blue = (int(color[k : k + 2], 16) for k in (1, 3, 5))
                dark_cell = (red * 299 + green * 587 + blue * 114) / 1000 < 140
                self._text(
                    group,
                    x + cell_width / 2,
                    y + cell_height / 2 + value_size * 0.35,
                    f"{value:.2f}",
                    value_size,
                    LIGHT_TEXT if dark_cell else DARK_TEXT,
                    "bold",
                    "middle",
                )

        # Colorbar on the right, spanning the data range on the same scale
        bar_width = 55
        bar_height = grid_height * 0.8
        bar_x = x_offset + grid_width + 120
        bar_y = y_offset + (grid_height - bar_height) / 2
        n_segments = 50
        seg_height = bar_height / n_segments
        for k in range(n_segments):
            seg_value = max_val - (max_val - min_val) * k / (n_segments - 1)
            self.svg.node(
                group,
                "rect",
                x=bar_x,
                y=bar_y + k * seg_height,
                width=bar_width,
                height=seg_height + 1,
                fill=ramp_color(DIV_FIELDS, (seg_value / span + 1) / 2),
            )
        self.svg.node(
            group,
            "rect",
            x=bar_x,
            y=bar_y,
            width=bar_width,
            height=bar_height,
            fill="none",
            stroke=INK,
            stroke_width="2",
        )
        tick_size = 40
        for frac, tick_value in ((0.0, max_val), (0.5, (min_val + max_val) / 2), (1.0, min_val)):
            self._text(
                group,
                bar_x + bar_width + 15,
                bar_y + bar_height * frac + tick_size * 0.35,
                f"{tick_value:.2f}",
                tick_size,
                INK,
            )
        self._text(group, bar_x + bar_width / 2, bar_y - 35, self.bar_title, 40, INK, "bold", "middle")


# Style
title = "heatmap-annotated · python · pygal · anyplot.ai"
custom_style = Style(
    background=PAGE_BG,
    plot_background=PAGE_BG,
    foreground=INK,
    foreground_strong=INK,
    foreground_subtle=INK_MUTED,
    colors=IMPRINT_PALETTE,
    title_font_size=72,
    legend_font_size=48,
    label_font_size=44,
    major_label_font_size=44,
    guide_stroke_color=INK_MUTED,
    major_guide_stroke_color=INK_MUTED,
    value_font_size=38,
    font_family="sans-serif",
)

chart = AnnotatedHeatmap(
    width=2400,
    height=2400,
    style=custom_style,
    title=title,
    matrix_data=df.to_numpy(dtype=float),
    row_labels=[str(label) for label in df.index],
    col_labels=[str(label) for label in df.columns],
    bar_title=VALUE,
    show_legend=False,
    margin=120,
    margin_top=130,
    margin_bottom=100,
    show_x_labels=False,
    show_y_labels=False,
)
# pygal needs one series to reach _plot
chart.add("", [0])

# Save
chart.render_to_png(f"plot-{THEME}.png")
chart_svg = chart.render(is_unicode=True)
html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>{title}</title>
    <style>
        body {{ margin: 0; display: flex; justify-content: center; align-items: center; min-height: 100vh; background: {PAGE_BG}; }}
        .chart {{ max-width: 100%; height: auto; }}
    </style>
</head>
<body>
    <figure class="chart">
        {chart_svg}
    </figure>
</body>
</html>
"""
with open(f"plot-{THEME}.html", "w", encoding="utf-8") as f:
    f.write(html_content)
