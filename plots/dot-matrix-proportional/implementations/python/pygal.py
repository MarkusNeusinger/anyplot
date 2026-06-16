""" anyplot.ai
dot-matrix-proportional: Dot Matrix Chart for Proportional Counts
Library: pygal 3.1.0 | Python 3.13.13
Quality: 82/100 | Created: 2026-05-08
"""

import os

import pygal
from pygal.style import Style


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

IMPRINT = ("#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477")

# Data: employee work-preference survey (100 respondents)
categories = [("Prefer Remote", 42), ("Prefer Office", 31), ("Hybrid Model", 27)]
total = 100
cols = 10
rows = total // cols  # 10

# Build grid positions: fill left-to-right, top-to-bottom
all_positions = []
for idx in range(total):
    col = idx % cols
    row = idx // cols
    all_positions.append((float(col), float((rows - 1) - row)))

# Assign positions to each category in order
cat_series = []
start = 0
for name, count in categories:
    cat_series.append((name, count, all_positions[start : start + count]))
    start += count

# Style
custom_style = Style(
    background=PAGE_BG,
    plot_background=PAGE_BG,
    foreground=INK,
    foreground_strong=INK,
    foreground_subtle=INK_MUTED,
    colors=IMPRINT,
    title_font_size=28,
    label_font_size=18,
    major_label_font_size=16,
    legend_font_size=16,
    value_font_size=14,
    stroke_width=3,
)

# Chart — XY scatter with stroke=False gives a pure dot matrix
chart = pygal.XY(
    style=custom_style,
    width=3600,
    height=3600,
    title="Employee Work Preferences · dot-matrix-proportional · pygal · anyplot.ai",
    stroke=False,
    dots_size=35,
    show_x_guides=False,
    show_y_guides=False,
    show_x_labels=False,
    show_y_labels=False,
    legend_at_bottom=True,
    x_title="100 employees surveyed  —  each dot represents 1 person",
)

for name, count, positions in cat_series:
    chart.add(f"{name}  ({count})", positions)

# Save
chart.render_to_png(f"plot-{THEME}.png")
with open(f"plot-{THEME}.html", "wb") as f:
    f.write(chart.render())
