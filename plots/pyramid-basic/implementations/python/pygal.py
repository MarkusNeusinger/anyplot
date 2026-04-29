""" anyplot.ai
pyramid-basic: Basic Pyramid Chart
Library: pygal 3.1.0 | Python 3.13.13
Quality: 81/100 | Updated: 2026-04-29
"""

import os
import sys


# Pop script directory so local pygal.py doesn't shadow the installed package
_script_dir = sys.path.pop(0)

import pygal  # noqa: E402
from pygal.style import Style  # noqa: E402


sys.path.insert(0, _script_dir)

# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

OKABE_ITO = ("#009E73", "#D55E00", "#0072B2", "#CC79A7", "#E69F00", "#56B4E9", "#F0E442")

# Data - US 2023 population estimates by age group (millions)
age_groups = ["0-9", "10-19", "20-29", "30-39", "40-49", "50-59", "60-69", "70-79", "80+"]
female = [4.5, 5.0, 6.3, 7.5, 8.7, 8.2, 6.4, 4.1, 2.1]
male = [4.8, 5.2, 6.1, 7.3, 8.5, 7.8, 5.9, 3.2, 1.2]

# Style
custom_style = Style(
    background=PAGE_BG,
    plot_background=PAGE_BG,
    foreground=INK,
    foreground_strong=INK,
    foreground_subtle=INK_MUTED,
    colors=OKABE_ITO,
    title_font_size=28,
    label_font_size=18,
    major_label_font_size=16,
    legend_font_size=16,
    value_font_size=14,
    stroke_width=3,
)

# Plot
chart = pygal.Pyramid(
    width=4800,
    height=2700,
    style=custom_style,
    title="pyramid-basic · pygal · anyplot.ai",
    x_title="Population (millions)",
    y_title="Age Group",
    show_y_guides=True,
    show_x_guides=False,
    print_values=False,
    show_legend=True,
    human_readable=True,
)

chart.x_labels = age_groups

# First series goes RIGHT (female), second goes LEFT (male)
chart.add("Female", female)
chart.add("Male", male)

# Save
chart.render_to_png(f"plot-{THEME}.png")
chart.render_to_file(f"plot-{THEME}.html")
