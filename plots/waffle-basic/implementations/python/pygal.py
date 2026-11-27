"""anyplot.ai
waffle-basic: Basic Waffle Chart
Library: pygal 3.1.3 | Python 3.14.10
Quality: pending | Updated: 2026-11-27
"""

import os
import re
import sys

import cairosvg
import pandas as pd


THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Imprint palette
IMPRINT = ("#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314")

_cwd = sys.path[0] if sys.path[0] else "."
if _cwd in sys.path:
    sys.path.remove(_cwd)

import pygal  # noqa: E402
from pygal.style import Style  # noqa: E402


sys.path.insert(0, _cwd)

# Constants
ROWS = 10
COLS = 10
LEGEND_ROOM = 70  # pixels kept free between the grid and the legend
GAP_SHARE = 0.12  # gap between squares as a share of the pitch

CATEGORY = "category"  # role: category
VALUE = "value"  # role: value

# Data
df = pd.DataFrame({CATEGORY: ["Operations", "Marketing", "R&D", "Admin"], VALUE: [42, 28, 18, 12]})

# Plot
custom_style = Style(
    background=PAGE_BG,
    plot_background=PAGE_BG,
    foreground=INK,
    foreground_strong=INK,
    foreground_subtle=INK_MUTED,
    guide_stroke_color=INK_MUTED,
    major_guide_stroke_color=INK_MUTED,
    colors=IMPRINT,
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
    width=3200,
    height=1800,
    style=custom_style,
    title="Budget Allocation · waffle-basic · python · pygal · anyplot.ai",
    show_legend=True,
    show_dots=False,
    legend_at_bottom=True,
    legend_at_bottom_columns=2,
    legend_box_size=40,
    show_x_labels=False,
    show_y_labels=False,
    show_x_guides=False,
    show_y_guides=False,
    margin=40,
    margin_left=800,
    margin_right=800,
)

# pygal draws the title, legend and page; one-point series give the legend its entries
total = df[VALUE].sum()
for category, value in zip(df[CATEGORY], df[VALUE], strict=True):
    chart.add(f"{category} ({value / total * 100:.0f}%)", [(0, 0)])

svg = chart.render().decode("utf-8")
plot_open = re.search(r'<g transform="translate\([^)]*\)" class="plot">', svg)
plot_bg = re.search(
    r'<rect x="0" y="0" width="([\d.]+)" height="([\d.]+)" class="background" />', svg[plot_open.end() :]
)
plot_w, plot_h = float(plot_bg.group(1)), float(plot_bg.group(2))
insert_at = plot_open.end() + plot_bg.end()  # after the plot's own background, so the squares stay visible

# Grid of squares in the plot area, centered; cumulative rounding keeps blocks whole and fills the grid exactly
pitch = min(plot_w / COLS, (plot_h - LEGEND_ROOM) / ROWS)
side = pitch * (1 - GAP_SHARE)
x0 = (plot_w - pitch * COLS) / 2 + (pitch - side) / 2
y0 = (plot_h - LEGEND_ROOM - pitch * ROWS) / 2 + (pitch - side) / 2
placed = 0
cumulative = 0
squares = []
for color, value in zip(IMPRINT, df[VALUE], strict=False):
    cumulative += value
    count = round(cumulative / total * ROWS * COLS) - placed
    for index in range(placed, placed + count):
        row, col = divmod(index, COLS)
        squares.append(
            f'<rect x="{x0 + col * pitch:.2f}" y="{y0 + row * pitch:.2f}" width="{side:.2f}" height="{side:.2f}" '
            f'rx="{side * 0.1:.2f}" fill="{color}"/>'
        )
    placed += count

svg = svg[:insert_at] + "".join(squares) + svg[insert_at:]
cairosvg.svg2png(bytestring=svg.encode("utf-8"), write_to=f"plot-{THEME}.png")

with open(f"plot-{THEME}.html", "w", encoding="utf-8") as f:
    f.write(svg)
