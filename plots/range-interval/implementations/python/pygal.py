""" anyplot.ai
range-interval: Range Interval Chart
Library: pygal 3.1.0 | Python 3.13.13
Quality: 90/100 | Updated: 2026-05-18
"""

import os
import sys


# Avoid importing local pygal.py file; ensure we get the installed pygal package
script_dir = os.path.dirname(os.path.abspath(__file__))
if script_dir in sys.path:
    sys.path.remove(script_dir)

import pygal  # noqa: E402
from pygal.style import Style  # noqa: E402


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

IMPRINT = ("#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477")

# Data: Monthly temperature ranges (daily high/low averages)
months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
temp_min = [-2, 0, 4, 8, 13, 17, 19, 18, 14, 9, 4, 0]
temp_max = [6, 8, 12, 16, 21, 25, 28, 27, 22, 16, 10, 7]

# Calculate the range for stacked bar visualization
temp_range = [high - low for low, high in zip(temp_min, temp_max, strict=True)]

# Custom style with theme-adaptive tokens
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

# Create stacked bar chart (first series base, second series visible range)
chart = pygal.StackedBar(
    width=4800,
    height=2700,
    style=custom_style,
    title="range-interval · python · pygal · anyplot.ai",
    x_title="Month",
    y_title="Temperature (°C)",
    show_legend=True,
    legend_at_bottom=True,
    show_y_guides=True,
    show_x_guides=False,
    print_values=False,
    spacing=40,
    margin=80,
    margin_bottom=150,
    margin_left=150,
)

# Set x-axis labels
chart.x_labels = months

# Add invisible base (from 0 to min_value)
chart.add("", temp_min, show_dots=False)

# Add visible range bars (from min to max) in brand color
chart.add("Temperature Range (°C)", temp_range, show_dots=False)

# Render to PNG and HTML
chart.render_to_png(f"plot-{THEME}.png")
with open(f"plot-{THEME}.html", "wb") as f:
    f.write(chart.render())
