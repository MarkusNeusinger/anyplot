""" anyplot.ai
polar-bar: Polar Bar Chart (Wind Rose)
Library: pygal 3.1.0 | Python 3.13.13
Quality: 96/100 | Updated: 2026-05-13
"""

import os

import pygal
from pygal.style import Style


# Theme-adaptive colors (see prompts/default-style-guide.md)
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Okabe-Ito palette (first series always #009E73)
IMPRINT = ("#009E73", "#C475FD", "#4467A3", "#BD8233")

# Wind direction and frequency data
directions = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"]

# Wind speed categories (realistic meteorological data showing westerly dominance)
calm_winds = [8, 5, 4, 3, 5, 7, 12, 11]  # 0-5 km/h
light_winds = [6, 4, 3, 2, 4, 7, 10, 9]  # 5-15 km/h
moderate_winds = [3, 2, 2, 1, 2, 4, 7, 6]  # 15-25 km/h
strong_winds = [2, 1, 1, 1, 1, 2, 4, 3]  # 25+ km/h

# Create custom style with theme-adaptive colors
custom_style = Style(
    background=PAGE_BG,
    plot_background=PAGE_BG,
    foreground=INK,
    foreground_strong=INK,
    foreground_subtle=INK_SOFT,
    colors=IMPRINT,
    title_font_size=28,
    label_font_size=22,
    major_label_font_size=18,
    legend_font_size=16,
    value_font_size=14,
    stroke_width=3,
    opacity=0.85,
)

# Create radar chart (pygal's polar visualization for wind rose)
chart = pygal.Radar(
    width=4800,
    height=2700,
    style=custom_style,
    title="Wind Rose · Wind Frequency (%) by Direction · polar-bar · pygal · pyplots.ai",
    show_legend=True,
    legend_at_bottom=True,
    legend_at_bottom_columns=4,
    fill=True,
    stroke=True,
    show_dots=False,
    range=(0, 15),
    inner_radius=0.12,
    margin=100,
    spacing=50,
)

# X-axis labels (compass directions)
chart.x_labels = directions

# Add wind speed categories (layered from calm to strong)
chart.add("Calm (0-5 km/h)", calm_winds)
chart.add("Light (5-15 km/h)", light_winds)
chart.add("Moderate (15-25 km/h)", moderate_winds)
chart.add("Strong (25+ km/h)", strong_winds)

# Save outputs
chart.render_to_png(f"plot-{THEME}.png")
with open(f"plot-{THEME}.html", "wb") as f:
    f.write(chart.render())
