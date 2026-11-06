"""anyplot.ai
pyramid-basic: Basic Pyramid Chart
Library: pygal 3.1.0 | Python 3.13.13
Quality: pending | Updated: 2026-04-29
"""

import os

import pandas as pd
import pygal
from pygal.style import Style


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: all eight positions, one per group in order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Columns: set these to your table's column names
AGE_GROUP = "Age Group"  # role: category
FEMALE = "Female"  # role: value_right
MALE = "Male"  # role: value_left
UNIT = "Population (millions)"  # role: extra

# Data: replace this block with your own table, for example df = pd.read_csv("population.csv")
# US 2023 population by age group (millions); prime working-age cohorts 30-49 lead both sexes
df = pd.DataFrame(
    {
        AGE_GROUP: ["0-9", "10-19", "20-29", "30-39", "40-49", "50-59", "60-69", "70-79", "80+"],
        FEMALE: [18.0, 20.0, 21.5, 21.8, 21.0, 21.5, 20.0, 14.0, 9.5],
        MALE: [18.8, 20.8, 21.8, 22.1, 21.3, 21.0, 19.0, 12.2, 5.8],
    }
)

# Plot
custom_style = Style(
    background=PAGE_BG,
    plot_background=PAGE_BG,
    foreground=INK,
    foreground_strong=INK,
    foreground_subtle=INK_SOFT,
    colors=tuple(IMPRINT_PALETTE),
    title_font_size=66,
    label_font_size=56,
    major_label_font_size=44,
    legend_font_size=44,
    value_font_size=36,
    stroke_width=0,
)

chart = pygal.Pyramid(
    width=3200,
    height=1800,
    style=custom_style,
    title="pyramid-basic · python · pygal · anyplot.ai",
    x_title=UNIT,
    y_title=AGE_GROUP,
    show_y_guides=False,
    show_x_guides=False,
    print_values=False,
    show_legend=True,
    value_formatter=lambda v: f"{abs(v):g}",
    legend_at_bottom=True,
    legend_at_bottom_columns=2,
    legend_box_size=36,
    margin_bottom=40,
    margin_left=40,
)

chart.x_labels = df[AGE_GROUP].tolist()

# First series goes RIGHT (female), second goes LEFT (male)
chart.add(FEMALE, df[FEMALE].tolist())
chart.add(MALE, df[MALE].tolist())

# Save
chart.render_to_png(f"plot-{THEME}.png")
chart.render_to_file(f"plot-{THEME}.html")
