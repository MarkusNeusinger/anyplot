""" anyplot.ai
line-multi: Multi-Line Comparison Plot
Library: pygal 3.1.0 | Python 3.13.13
Quality: 83/100 | Updated: 2026-05-06
"""

import os
import sys
from pathlib import Path


# Remove the script's directory from sys.path to avoid import collision
script_dir = str(Path(__file__).parent)
sys.path = [p for p in sys.path if p != script_dir and p != ""]

import pygal  # noqa: E402
from pygal.style import Style  # noqa: E402


# Theme tokens (see prompts/default-style-guide.md)
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Okabe-Ito palette (canonical order)
IMPRINT = (
    "#009E73",  # bluish green (brand — first series)
    "#C475FD",  # vermillion
    "#4467A3",  # blue
    "#BD8233",  # reddish purple
)

# Data - Monthly sales for 4 product lines over 12 months
months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

electronics = [45, 52, 48, 61, 55, 67, 72, 78, 69, 85, 92, 110]
clothing = [38, 42, 51, 48, 55, 62, 58, 65, 71, 68, 75, 88]
home_goods = [28, 31, 35, 38, 42, 45, 48, 52, 49, 55, 62, 72]
sports = [22, 25, 32, 45, 58, 65, 72, 68, 55, 42, 35, 28]

# Custom style with theme-adaptive colors
custom_style = Style(
    background=PAGE_BG,
    plot_background=PAGE_BG,
    foreground=INK,
    foreground_strong=INK,
    foreground_subtle=INK_MUTED,
    colors=IMPRINT,
    title_font_size=28,
    label_font_size=22,
    major_label_font_size=18,
    legend_font_size=16,
    value_font_size=14,
    stroke_width=3,
)

# Create chart
chart = pygal.Line(
    width=4800,
    height=2700,
    title="line-multi · pygal · anyplot.ai",
    x_title="Month",
    y_title="Sales (thousands USD)",
    style=custom_style,
    show_dots=True,
    dots_size=6,
    show_legend=True,
    legend_at_bottom=False,
    x_label_rotation=0,
    show_y_guides=True,
    show_x_guides=False,
    margin=100,
    margin_top=120,
    margin_bottom=100,
    spacing=20,
)

# Add data series
chart.x_labels = months
chart.add("Electronics", electronics)
chart.add("Clothing", clothing)
chart.add("Home Goods", home_goods)
chart.add("Sports", sports)

# Save as PNG and HTML
chart.render_to_png(f"plot-{THEME}.png")
with open(f"plot-{THEME}.html", "wb") as f:
    f.write(chart.render())
