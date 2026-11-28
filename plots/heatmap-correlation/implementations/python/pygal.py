"""anyplot.ai
heatmap-correlation: Correlation Matrix Heatmap
Library: pygal 3.1.3 | Python 3.13.15
Quality: 87/100 | Updated: 2026-11-28
"""

import math
import os
from itertools import pairwise

import pandas as pd
from pygal.graph.graph import Graph
from pygal.style import Style


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Imprint palette: all eight positions in canonical order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Constants
# Imprint diverging ramp for fields: red (negative) -> page color (zero) -> blue (positive)
DIV_FIELDS = [(0.0, "#AE3030"), (0.5, PAGE_BG), (1.0, "#4467A3")]
CORRELATION_RANGE = (-1.0, 1.0)  # fixed color range, so the midpoint is always zero

# Columns: the matrix is a labeled square, so the descriptor names are its index and columns
DESCRIPTOR = "Molecular Descriptors"  # role: variables
CORRELATION = "Correlation"  # role: correlation_matrix

# Data: replace this block with your own labeled square matrix, e.g. df = pd.read_csv("corr.csv", index_col=0)
# Correlation matrix of molecular descriptors (cheminformatics QSAR feature set)
variables = [
    "Mol. Weight",
    "LogP",
    "TPSA",
    "H-Bond Donors",
    "H-Bond Acceptors",
    "Rotatable Bonds",
    "Aromatic Rings",
    "LogS",
]
df = pd.DataFrame(
    [
        [1.00, 0.45, 0.55, 0.25, 0.60, 0.70, 0.50, -0.55],
        [0.45, 1.00, -0.75, -0.50, -0.35, 0.20, 0.40, -0.80],
        [0.55, -0.75, 1.00, 0.80, 0.85, 0.15, -0.10, 0.50],
        [0.25, -0.50, 0.80, 1.00, 0.45, 0.10, -0.15, 0.40],
        [0.60, -0.35, 0.85, 0.45, 1.00, 0.25, 0.05, 0.35],
        [0.70, 0.20, 0.15, 0.10, 0.25, 1.00, -0.20, -0.15],
        [0.50, 0.40, -0.10, -0.15, 0.05, -0.20, 1.00, -0.35],
        [-0.55, -0.80, 0.50, 0.40, 0.35, -0.15, -0.35, 1.00],
    ],
    index=variables,
    columns=variables,
)


# Plot: reads only df and the constants above
def ramp_color(stops, t):
    """The hex at t (0 to 1) along (position, hex) stops, blended linearly in sRGB."""
    if not math.isfinite(t):
        return "none"  # a missing value draws nothing
    t = min(max(t, 0.0), 1.0)
    (p0, c0), (p1, c1) = next((a, b) for a, b in pairwise(stops) if t <= b[0])
    share = (t - p0) / (p1 - p0)
    return "#" + "".join(
        f"{round(int(c0[i : i + 2], 16) * (1 - share) + int(c1[i : i + 2], 16) * share):02X}" for i in (1, 3, 5)
    )


def cell_color(value):
    """Diverging fill for a correlation value on the fixed -1..1 range."""
    lo, hi = CORRELATION_RANGE
    return ramp_color(DIV_FIELDS, (value - lo) / (hi - lo))


def text_color_on(bg_color):
    """Dark or light text, whichever contrasts with the fill."""
    if bg_color == "none":
        return INK
    r, g, b = (int(bg_color[i : i + 2], 16) for i in (1, 3, 5))
    return "#FAF8F1" if (r * 299 + g * 587 + b * 114) / 1000 < 140 else "#1A1A17"


class CorrelationHeatmap(Graph):
    """Correlation matrix heatmap: pygal has no heatmap type, so the grid is drawn in the plot layer."""

    def __init__(self, *args, **kwargs):
        self.matrix = kwargs.pop("matrix")
        self.labels = kwargs.pop("labels")
        self.axis_title = kwargs.pop("axis_title")
        self.bar_title = kwargs.pop("bar_title")
        super().__init__(*args, **kwargs)

    def _text(self, parent, x, y, text, size, fill, bold=False, anchor=None, rotate=None):
        node = self.svg.node(parent, "text", x=x, y=y)
        if anchor:
            node.set("text-anchor", anchor)
        node.set("fill", fill)
        weight = "font-weight:bold;" if bold else ""
        node.set("style", f"font-size:{size}px;{weight}font-family:sans-serif")
        if rotate is not None:
            node.set("transform", f"rotate({rotate}, {x}, {y})")
        node.text = text

    def _plot(self):
        n = len(self.matrix)
        longest = max(len(label) for label in self.labels)

        # Label blocks scale with the longest name so nothing collides with the axis titles
        row_label_width = longest * 54 * 0.64
        col_label_drop = longest * 54 * 0.56 * 0.7071
        title_block = 90
        margin_left = row_label_width + title_block + 60
        margin_bottom = 25 + col_label_drop + title_block + 40
        margin_top = 20
        margin_right = 340

        available_width = self.view.width - margin_left - margin_right
        available_height = self.view.height - margin_bottom - margin_top
        cell = min(available_width, available_height) / n
        gap = cell * 0.02
        grid = n * (cell + gap) - gap

        left = self.view.x(0)
        x0 = left + margin_left + (available_width - grid) / 2
        y0 = self.view.y(n) + margin_top + (available_height - grid) / 2
        group = self.svg.node(self.nodes["plot"], class_="correlation-heatmap")

        # Axis titles
        y_title_x, y_title_y = left + title_block / 2, y0 + grid / 2
        self._text(group, y_title_x, y_title_y, self.axis_title, 52, INK, True, "middle", -90)
        label_size = min(54, int(cell * 0.55))
        col_label_y = y0 + grid + 25
        self._text(group, x0 + grid / 2, col_label_y + col_label_drop + 40, self.axis_title, 52, INK, True, "middle")

        # Row labels and 45-degree column labels, same names in the same order
        for i, label in enumerate(self.labels):
            y = y0 + i * (cell + gap) + cell / 2
            self._text(group, x0 - 25, y + label_size * 0.35, label, label_size, INK_SOFT, True, "end")
            x = x0 + i * (cell + gap) + cell / 2
            self._text(group, x, col_label_y, label, label_size, INK_SOFT, True, "start", 45)

        # Cells with their values
        value_size = min(46, int(cell * 0.33))
        for i in range(n):
            for j in range(n):
                value = self.matrix[i][j]
                fill = cell_color(value)
                x, y = x0 + j * (cell + gap), y0 + i * (cell + gap)
                rect = self.svg.node(group, "rect", x=x, y=y, width=cell, height=cell, rx=4, ry=4)
                rect.set("fill", fill)
                rect.set("stroke", PAGE_BG)
                rect.set("stroke-width", "2")
                if math.isfinite(value):
                    label = f"{value:.2f}"
                    self._text(
                        group,
                        x + cell / 2,
                        y + cell / 2 + value_size * 0.35,
                        label,
                        value_size,
                        text_color_on(fill),
                        True,
                        "middle",
                    )

        # Color bar fixed to the full -1..1 range, top = +1
        bar_w, bar_h = 55, grid * 0.85
        bar_x, bar_y = x0 + grid + 125, y0 + (grid - bar_h) / 2
        segments = 60
        for k in range(segments):
            value = CORRELATION_RANGE[1] - (CORRELATION_RANGE[1] - CORRELATION_RANGE[0]) * k / (segments - 1)
            self.svg.node(
                group,
                "rect",
                x=bar_x,
                y=bar_y + k * bar_h / segments,
                width=bar_w,
                height=bar_h / segments + 1,
                fill=cell_color(value),
            )
        self.svg.node(group, "rect", x=bar_x, y=bar_y, width=bar_w, height=bar_h, fill="none", stroke=INK_SOFT)
        tick_size = 42
        for frac, tick in ((0.0, "+1.00"), (0.5, " 0.00"), (1.0, "-1.00")):
            self._text(group, bar_x + bar_w + 18, bar_y + bar_h * frac + tick_size * 0.35, tick, tick_size, INK_SOFT)
        self._text(group, bar_x + bar_w / 2, bar_y - 40, self.bar_title, 46, INK, True, "middle")

    def _compute(self):
        n = len(self.matrix)
        self._box.xmin, self._box.xmax = 0, n
        self._box.ymin, self._box.ymax = 0, n


custom_style = Style(
    background=PAGE_BG,
    plot_background=PAGE_BG,
    foreground=INK,
    foreground_strong=INK,
    foreground_subtle=INK_MUTED,
    colors=IMPRINT_PALETTE,
    title_font_size=72,
    legend_font_size=48,
    guide_stroke_color=INK_MUTED,
    major_guide_stroke_color=INK_MUTED,
    label_font_size=50,
    major_label_font_size=50,
    value_font_size=44,
    font_family="sans-serif",
)

chart = CorrelationHeatmap(
    width=2400,
    height=2400,
    style=custom_style,
    title="heatmap-correlation · python · pygal · anyplot.ai",
    matrix=df.to_numpy().tolist(),
    labels=[str(name) for name in df.index],
    axis_title=DESCRIPTOR,
    bar_title=CORRELATION,
    show_legend=False,
    margin=120,
    margin_top=60,
    margin_bottom=100,
    show_x_labels=False,
    show_y_labels=False,
)
chart.add("", [0])

# Save
chart.render_to_file(f"plot-{THEME}.svg")
chart.render_to_png(f"plot-{THEME}.png")

html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>heatmap-correlation - pygal</title>
    <style>
        body {{ margin: 0; display: flex; justify-content: center; align-items: center; min-height: 100vh; background: {PAGE_BG}; }}
        .chart {{ max-width: 100%; height: auto; }}
    </style>
</head>
<body>
    <figure class="chart">
        {chart.render(is_unicode=True)}
    </figure>
</body>
</html>
"""
with open(f"plot-{THEME}.html", "w", encoding="utf-8") as f:
    f.write(html_content)
