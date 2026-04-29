""" anyplot.ai
pyramid-basic: Basic Pyramid Chart
Library: pygal 3.1.0 | Python 3.13.13
Quality: 85/100 | Updated: 2026-04-29
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
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

OKABE_ITO = ("#009E73", "#D55E00", "#0072B2", "#CC79A7", "#E69F00", "#56B4E9", "#F0E442")

# US 2023 population by age group (millions); prime working-age cohorts 30-49 lead both sexes
age_groups = ["0-9", "10-19", "20-29", "30-39", "40-49", "50-59", "60-69", "70-79", "80+"]
female = [18.0, 20.0, 21.5, 21.8, 21.0, 21.5, 20.0, 14.0, 9.5]
male = [18.8, 20.8, 21.8, 22.1, 21.3, 21.0, 19.0, 12.2, 5.8]

# Style — stroke_width=0 removes heavy bar outlines that bleed in dark theme
custom_style = Style(
    background=PAGE_BG,
    plot_background=PAGE_BG,
    foreground=INK,
    foreground_strong=INK,
    foreground_subtle=INK_SOFT,
    colors=OKABE_ITO,
    title_font_size=28,
    label_font_size=22,
    major_label_font_size=18,
    legend_font_size=16,
    value_font_size=14,
    stroke_width=0,
)

# Plot — guides off for a clean look; legend at bottom for better layout
chart = pygal.Pyramid(
    width=4800,
    height=2700,
    style=custom_style,
    title="pyramid-basic · pygal · anyplot.ai",
    x_title="Population (millions) — 30–49 cohorts at peak for both sexes",
    y_title="Age Group",
    show_y_guides=False,
    show_x_guides=False,
    print_values=False,
    show_legend=True,
    human_readable=True,
    legend_at_bottom=True,
    legend_at_bottom_columns=2,
)

chart.x_labels = age_groups

# First series goes RIGHT (female), second goes LEFT (male)
chart.add("Female", female)
chart.add("Male", male)

# Save
chart.render_to_png(f"plot-{THEME}.png")
chart.render_to_file(f"plot-{THEME}.html")
