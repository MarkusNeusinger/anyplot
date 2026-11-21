"""anyplot.ai
scatter-annotated: Annotated Scatter Plot with Text Labels
Library: pygal 3.1.0 | Python 3.13.13
Quality: 81/100 | Updated: 2026-05-13
"""

import os

import cairosvg
import pandas as pd
import pygal
from pygal.style import Style


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Imprint palette: one position per group in order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Columns: set these to your table's column names
CITY = "City"  # role: label
POPULATION = "Metro population (millions)"  # role: x
AREA = "Urban area (km²)"  # role: y
REGION = "Region"  # role: extra

# Data: replace this block with your own table, for example df = pd.read_csv("cities.csv")
df = pd.DataFrame(
    {
        CITY: [
            "Tokyo",
            "Delhi",
            "Shanghai",
            "Mumbai",
            "Seoul",
            "Lagos",
            "Cairo",
            "Istanbul",
            "Paris",
            "London",
            "Moscow",
            "New York",
            "Los Angeles",
            "Mexico City",
            "São Paulo",
            "Buenos Aires",
        ],
        POPULATION: [37.3, 32.9, 28.5, 21.7, 10.0, 15.9, 21.8, 15.8, 11.2, 9.6, 12.7, 19.2, 12.5, 22.2, 22.6, 15.4],
        AREA: [8547, 2344, 3820, 881, 2266, 1171, 1760, 5343, 2845, 1738, 5698, 11642, 6299, 4180, 3173, 2681],
        REGION: ["Asia"] * 5 + ["Africa"] * 2 + ["Europe"] * 4 + ["Americas"] * 5,
    }
)

# Plot: reads only df and the constants above
title = "scatter-annotated · python · pygal · anyplot.ai"
groups = list(dict.fromkeys(df[REGION]))

custom_style = Style(
    background=PAGE_BG,
    plot_background=PAGE_BG,
    foreground=INK,
    foreground_strong=INK,
    foreground_subtle=INK_MUTED,
    colors=tuple(IMPRINT_PALETTE),
    title_font_size=60,
    label_font_size=48,
    major_label_font_size=40,
    legend_font_size=40,
    value_font_size=38,
    value_colors=(INK,) * len(IMPRINT_PALETTE),
    stroke_width=2.5,
    opacity=0.7,
    opacity_hover=1.0,
    guide_stroke_color=INK_MUTED,
    major_guide_stroke_color=INK_MUTED,
)

chart = pygal.XY(
    width=3200,
    height=1800,
    style=custom_style,
    title=title,
    x_title=POPULATION,
    y_title=AREA,
    show_legend=True,
    legend_at_bottom=True,
    show_x_guides=True,
    show_y_guides=True,
    stroke=False,
    dots_size=14,
    range=(0, df[AREA].max() * 1.12),
    xrange=(0, df[POPULATION].max() * 1.1),
    print_values=True,
    print_values_position="top",
    truncate_legend=-1,
    margin=40,
)

for group in groups:
    sub = df[df[REGION] == group].dropna(subset=[POPULATION, AREA])
    chart.add(
        group,
        [
            {"value": (x, y), "formatter": lambda _v, name=str(city): name}
            for city, x, y in zip(sub[CITY], sub[POPULATION], sub[AREA], strict=True)
        ],
    )

# Output: SVG for the interactive page, PNG via cairosvg
svg = chart.render()
with open(f"plot-{THEME}.html", "wb") as f:
    f.write(svg)
cairosvg.svg2png(bytestring=svg, write_to=f"plot-{THEME}.png", output_width=3200, output_height=1800)
