""" anyplot.ai
step-basic: Basic Step Plot
Library: pygal 3.1.0 | Python 3.13.13
Quality: 76/100 | Updated: 2026-04-30
"""

import os
import sys


# Pop script dir so this file (pygal.py) doesn't shadow the installed pygal package
_script_dir = sys.path.pop(0)
import pygal  # noqa: E402
from pygal.style import Style  # noqa: E402


sys.path.insert(0, _script_dir)

# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

OKABE_ITO = ("#009E73", "#D55E00", "#0072B2", "#CC79A7", "#E69F00", "#56B4E9", "#F0E442")

# Data - Monthly cumulative sales (in thousands)
months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
cumulative_sales = [45, 92, 128, 165, 198, 256, 312, 378, 425, 489, 562, 635]

# Build step data by duplicating points for stair-step effect (post-style)
step_x_labels = []
step_values = []

for i, (month, value) in enumerate(zip(months, cumulative_sales, strict=True)):
    step_x_labels.append(month)
    step_values.append({"value": value, "node": {"r": 14}})
    if i < len(months) - 1:
        step_x_labels.append("​")
        step_values.append({"value": value, "node": {"r": 0}})

# Custom style
custom_style = Style(
    background=PAGE_BG,
    plot_background=PAGE_BG,
    foreground=INK,
    foreground_strong=INK,
    foreground_subtle=INK_MUTED,
    colors=OKABE_ITO,
    title_font_size=72,
    label_font_size=48,
    major_label_font_size=44,
    legend_font_size=56,
    value_font_size=40,
    stroke_width=3,
)

# Chart
chart = pygal.Line(
    width=4800,
    height=2700,
    title="step-basic · pygal · anyplot.ai",
    x_title="Month",
    y_title="Cumulative Sales ($K)",
    style=custom_style,
    show_dots=True,
    dots_size=14,
    stroke_style={"width": 8},
    show_y_guides=True,
    show_x_guides=False,
    x_label_rotation=0,
    show_legend=False,
    margin=120,
)

chart.x_labels = step_x_labels
chart.add("Cumulative Sales", step_values)

# Save
chart.render_to_png(f"plot-{THEME}.png")
with open(f"plot-{THEME}.html", "wb") as f:
    f.write(chart.render())
