"""anyplot.ai
waffle-basic: Basic Waffle Chart
Library: pygal 3.1.3 | Python 3.14.10
Quality: pending | Updated: 2026-11-27
"""

import os
import sys

import pandas as pd


_cwd = sys.path[0] if sys.path[0] else "."
if _cwd in sys.path:
    sys.path.remove(_cwd)

import pygal  # noqa: E402
from pygal.style import Style  # noqa: E402


sys.path.insert(0, _cwd)

THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Imprint palette
IMPRINT = ("#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314")

CATEGORY = "category"  # role: category
VALUE = "value"  # role: value

# Data
df = pd.DataFrame({CATEGORY: ["Operations", "Marketing", "R&D", "Admin"], VALUE: [42, 28, 18, 12]})

# Plot
ROWS, COLS = 10, 10
WIDTH, HEIGHT = 3200, 1800
PLOT_W, PLOT_H = 2570, 1747  # drawing area measured from a render; equal pixels per unit on both axes
units_h = ROWS + 0.4
units_w = units_h * PLOT_W / PLOT_H
SQUARE_PX = round(0.82 * PLOT_H / units_h)  # square side in canvas pixels

# Whole squares per category by cumulative rounding, so the blocks together fill the grid
total = df[VALUE].sum()
cumulative = df[VALUE].cumsum() / total * ROWS * COLS
squares = cumulative.round().astype(int).diff().fillna(cumulative.round()).astype(int)
square_colors = tuple(IMPRINT[i % len(IMPRINT)] for i, count in enumerate(squares) for _ in range(count))

style = Style(
    background=PAGE_BG,
    plot_background=PAGE_BG,
    foreground=INK,
    foreground_strong=INK,
    foreground_subtle=INK_MUTED,
    guide_stroke_color=INK_MUTED,
    major_guide_stroke_color=INK_MUTED,
    colors=square_colors,
    opacity="1",
    opacity_hover="1",
    title_font_size=66,
    label_font_size=44,
    major_label_font_size=44,
    legend_font_size=44,
    value_font_size=36,
    stroke_width=2.5,
)

chart = pygal.XY(
    width=WIDTH,
    height=HEIGHT,
    style=style,
    title="Budget Allocation · waffle-basic · python · pygal · anyplot.ai",
    show_legend=True,
    legend_box_size=40,
    truncate_legend=40,
    show_x_labels=False,
    show_y_labels=False,
    show_x_guides=False,
    show_y_guides=False,
    show_minor_x_labels=False,
    show_minor_y_labels=False,
    show_dots=False,
    xrange=((COLS - 1) / 2 - units_w / 2, (COLS - 1) / 2 + units_w / 2),
    range=(-0.2, ROWS - 0.8),
    margin=40,
    spacing=10,
    css=[
        "file://style.css",
        "file://graph.css",
        f"inline:.series .line{{stroke-width:{SQUARE_PX}px !important;stroke-linecap:square !important;stroke-opacity:1 !important;opacity:1 !important}}",
    ],
)

# One series per square (pygal cannot break a line), colored by category; only the first
# square of a category carries a legend title
labels = [f"{c} ({v / total * 100:.0f}%)" for c, v in zip(df[CATEGORY], df[VALUE], strict=True)]
square_labels = [label if k == 0 else None for label, count in zip(labels, squares, strict=True) for k in range(count)]
for index, label in enumerate(square_labels):
    row, col = divmod(index, COLS)
    # A square is a very short segment drawn with a thick, square-capped stroke
    chart.add(label, [(col - 0.001, ROWS - 1 - row), (col + 0.001, ROWS - 1 - row)])

chart.render_to_png(f"plot-{THEME}.png")

with open(f"plot-{THEME}.html", "wb") as f:
    f.write(chart.render())
