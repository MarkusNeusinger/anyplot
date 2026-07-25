""" anyplot.ai
rose-basic: Basic Rose Chart
Library: pygal 3.1.3 | Python 3.13.14
Quality: 81/100 | Updated: 2026-07-25
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

BRAND = "#009E73"  # Imprint palette position 1 — single series, always brand green

# Data: Monthly rainfall (mm) — Pacific Northwest seasonal pattern
months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
rainfall = [145, 115, 95, 65, 45, 35, 20, 25, 50, 90, 135, 155]

custom_style = Style(
    background=PAGE_BG,
    plot_background=PAGE_BG,
    foreground=INK,
    foreground_strong=INK,
    foreground_subtle=INK_MUTED,
    colors=(BRAND,),
    title_font_size=66,
    label_font_size=56,
    major_label_font_size=44,
    stroke_width=3,
    opacity=0.78,
    opacity_hover=0.92,
)

# Radar is pygal's closest built-in approximation of a rose/coxcomb chart:
# equal angular spacing per category, radius proportional to value, filled
# polygon. Dots mark each month's exact vertex so low-radius months (summer)
# stay readable even where the filled area collapses near the center.
chart = pygal.Radar(
    width=2400,
    height=2400,
    style=custom_style,
    title="rose-basic · python · pygal · anyplot.ai",
    fill=True,
    stroke=True,
    show_dots=True,
    dots_size=10,
    show_legend=False,
    show_x_guides=True,
    show_y_guides=True,
    range=(0, 160),
    margin=70,
    value_formatter=lambda v: f"{v:.0f} mm",
)

chart.x_labels = months
chart.add("Monthly Rainfall", rainfall)

# Save
chart.render_to_png(f"plot-{THEME}.png")
with open(f"plot-{THEME}.html", "wb") as f:
    f.write(chart.render())
