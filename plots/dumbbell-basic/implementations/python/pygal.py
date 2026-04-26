""" anyplot.ai
dumbbell-basic: Basic Dumbbell Chart
Library: pygal 3.1.0 | Python 3.14.4
Quality: 87/100 | Updated: 2026-04-26
"""

import os
import sys
from pathlib import Path


# Remove script directory from path to avoid name collision with the pygal package
_script_dir = str(Path(__file__).parent)
sys.path = [p for p in sys.path if p != _script_dir]

import pygal  # noqa: E402
from pygal.style import Style  # noqa: E402


# Theme-adaptive chrome tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Okabe-Ito data colors (theme-independent)
BEFORE = "#009E73"  # position 1 — brand
AFTER = "#D55E00"  # position 2
CONNECTOR = INK_SOFT  # neutral chrome that adapts to theme

# Data — Employee satisfaction scores before and after policy changes.
# Hand-picked values include one regression (Legal) to exercise full data range.
categories = [
    "Engineering",
    "Sales",
    "Marketing",
    "Customer Support",
    "Finance",
    "Human Resources",
    "Operations",
    "Product",
    "Legal",
]
before = [62, 71, 58, 45, 68, 52, 64, 73, 70]
after = [78, 82, 75, 69, 74, 71, 79, 85, 67]

# Sort by improvement (largest at top)
data = sorted(zip(categories, before, after, strict=True), key=lambda x: x[2] - x[1], reverse=True)
categories = [d[0] for d in data]
before = [d[1] for d in data]
after = [d[2] for d in data]
n = len(categories)

# Y positions: top row = biggest improvement (first sorted item)
y_positions = list(range(n, 0, -1))

# Series colors map 1:1 to the order series are added below:
#   n connector series (drawn first, underneath) then 2 dot series.
colors_tuple = (CONNECTOR,) * n + (BEFORE, AFTER)

custom_style = Style(
    background=PAGE_BG,
    plot_background=PAGE_BG,
    foreground=INK,
    foreground_strong=INK,
    foreground_subtle=INK_MUTED,
    colors=colors_tuple,
    title_font_size=32,
    label_font_size=22,
    major_label_font_size=20,
    legend_font_size=20,
    value_font_size=16,
    stroke_width=4,
    opacity=1.0,
    opacity_hover=0.85,
)

chart = pygal.XY(
    width=4800,
    height=2700,
    style=custom_style,
    title="Employee Satisfaction · dumbbell-basic · pygal · anyplot.ai",
    x_title="Satisfaction Score (out of 100)",
    y_title="Department",
    show_legend=True,
    legend_at_bottom=True,
    legend_at_bottom_columns=2,
    legend_box_size=36,
    margin=80,
    show_x_guides=True,
    show_y_guides=False,
    xrange=(35, 95),
    range=(0, n + 1),
    y_labels=[{"label": cat, "value": pos} for cat, pos in zip(categories, y_positions, strict=True)],
    truncate_legend=-1,
    truncate_label=-1,
    dots_size=22,
    stroke=False,
)

# Connector lines first so they sit underneath the dots.
# title=None suppresses the legend entry while still rendering the series.
for b, a, pos in zip(before, after, y_positions, strict=True):
    chart.add(None, [(b, pos), (a, pos)], stroke=True, show_dots=False, stroke_style={"width": 5, "linecap": "round"})

# Before dots — Okabe-Ito green
before_points = [
    {"value": (b, pos), "label": f"{cat}: {b}"} for cat, b, pos in zip(categories, before, y_positions, strict=True)
]
chart.add("Before policy change", before_points, stroke=False, dots_size=24)

# After dots — Okabe-Ito vermillion
after_points = [
    {"value": (a, pos), "label": f"{cat}: {a}"} for cat, a, pos in zip(categories, after, y_positions, strict=True)
]
chart.add("After policy change", after_points, stroke=False, dots_size=24)

# Save outputs
chart.render_to_png(f"plot-{THEME}.png")
with open(f"plot-{THEME}.html", "wb") as f:
    f.write(chart.render())
