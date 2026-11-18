"""anyplot.ai
dot-matrix-proportional: Dot Matrix Chart for Proportional Counts
Library: pygal 3.1.0 | Python 3.13.13
Quality: 82/100 | Updated: 2026-11-18
"""

import math
import os

import pandas as pd
import pygal
from pygal.style import Style


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Imprint palette: all eight positions, one per category in order
IMPRINT_PALETTE = ("#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314")

# Columns: set these to your table's column names
CATEGORY = "Work preference"  # role: category
COUNT = "Employees (count)"  # role: count
TOTAL = "Survey size (employees)"  # role: total

# Data: employee work-preference survey, replace with your own table, for example df = pd.read_csv("survey.csv")
df = pd.DataFrame(
    {CATEGORY: ["Prefer Remote", "Prefer Office", "Hybrid Model"], COUNT: [42, 31, 27], TOTAL: [100, 100, 100]}
)

# Plot: reads only df and the constants above
total = int(df[TOTAL].iloc[0])
cols = math.ceil(math.sqrt(total))
rows = math.ceil(total / cols)

# Grid positions: fill left-to-right, top-to-bottom (y is flipped so row 0 is on top)
all_positions = [(float(i % cols), float(rows - 1 - i // cols)) for i in range(total)]

# Style
title = "Employee Work Preferences · dot-matrix-proportional · python · pygal · anyplot.ai"
title_size = round(66 * min(1.0, 67 / len(title)))
custom_style = Style(
    background=PAGE_BG,
    plot_background=PAGE_BG,
    foreground=INK,
    foreground_strong=INK,
    foreground_subtle=INK_MUTED,
    colors=IMPRINT_PALETTE,
    title_font_size=title_size,
    label_font_size=48,
    major_label_font_size=40,
    legend_font_size=48,
    value_font_size=36,
    stroke_width=3,
)

# Chart: XY scatter with stroke=False gives a pure dot matrix
chart = pygal.XY(
    style=custom_style,
    width=2400,
    height=2400,
    title=title,
    stroke=False,
    dots_size=24,
    show_x_guides=False,
    show_y_guides=False,
    show_x_labels=False,
    show_y_labels=False,
    legend_at_bottom=True,
    x_title=f"{total} employees surveyed  —  each dot represents 1 person",
)

start = 0
for category, count in zip(df[CATEGORY], df[COUNT], strict=True):
    count = int(count)
    chart.add(f"{category}  ({count}, {count / total:.0%})", all_positions[start : start + count])
    start += count

# Save
chart.render_to_png(f"plot-{THEME}.png")
with open(f"plot-{THEME}.html", "wb") as f:
    f.write(chart.render())
