""" anyplot.ai
rose-basic: Basic Rose Chart
Library: pygal 3.1.0 | Python 3.13.13
Quality: 80/100 | Updated: 2026-04-30
"""

import os
import sys


# Pop script directory so local pygal.py doesn't shadow the installed package
_script_dir = sys.path.pop(0)
import pygal  # noqa: E402
from pygal.style import Style  # noqa: E402


sys.path.insert(0, _script_dir)

THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

OKABE_ITO = ("#009E73", "#D55E00", "#0072B2", "#CC79A7", "#E69F00", "#56B4E9", "#F0E442")

# Data: Monthly rainfall (mm) — Pacific Northwest seasonal pattern
months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
rainfall = [145, 115, 95, 65, 45, 35, 20, 25, 50, 90, 135, 155]

custom_style = Style(
    background=PAGE_BG,
    plot_background=PAGE_BG,
    foreground=INK,
    foreground_strong=INK,
    foreground_subtle=INK_MUTED,
    colors=OKABE_ITO,
    title_font_size=72,
    label_font_size=52,
    major_label_font_size=52,
    legend_font_size=44,
    value_font_size=36,
    stroke_width=4,
    opacity=0.75,
    opacity_hover=0.9,
)

# Radar is pygal's closest approximation of a rose/coxcomb chart:
# equal angular spacing, radius proportional to value, filled polygons
chart = pygal.Radar(
    width=3600,
    height=3600,
    style=custom_style,
    title="rose-basic · pygal · anyplot.ai",
    fill=True,
    show_legend=True,
    legend_at_bottom=True,
    legend_at_bottom_columns=1,
    margin=100,
    show_dots=False,
    range=(0, 170),
)

chart.x_labels = months
chart.add("Monthly Rainfall (mm)", rainfall)

# Save
chart.render_to_png(f"plot-{THEME}.png")
with open(f"plot-{THEME}.html", "wb") as f:
    f.write(chart.render())
