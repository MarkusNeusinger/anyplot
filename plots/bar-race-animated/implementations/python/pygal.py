""" anyplot.ai
bar-race-animated: Animated Bar Chart Race
Library: pygal 3.1.0 | Python 3.13.13
Quality: 80/100 | Updated: 2026-05-19
"""

import os
import sys
from io import BytesIO


# Remove the script's own directory from sys.path so "pygal.py" doesn't shadow the installed package.
sys.path.pop(0)

import cairosvg
import pygal
from PIL import Image, ImageDraw, ImageFont
from pygal.style import Style


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Okabe-Ito palette — consistent entity colors across all frames
OKABE_ITO = ("#009E73", "#D55E00", "#0072B2", "#CC79A7", "#E69F00", "#56B4E9", "#F0E442")

# Data — Country GDP rankings (approximate, trillion USD)
countries = ["USA", "China", "Japan", "Germany", "UK", "India", "France"]
years = [2000, 2005, 2010, 2015, 2020, 2023]

gdp_data = {
    "USA": [10.2, 13.0, 14.9, 18.2, 20.9, 26.9],
    "China": [1.2, 2.3, 6.1, 11.1, 14.7, 17.5],
    "Japan": [4.9, 4.8, 5.7, 4.4, 5.0, 4.2],
    "Germany": [1.9, 2.9, 3.4, 3.4, 3.9, 4.5],
    "UK": [1.6, 2.5, 2.4, 2.9, 2.7, 3.1],
    "India": [0.5, 0.8, 1.7, 2.1, 2.7, 3.7],
    "France": [1.4, 2.2, 2.7, 2.4, 2.6, 2.9],
}

country_colors = {country: OKABE_ITO[i] for i, country in enumerate(countries)}

# Create individual pygal charts for each snapshot year
charts = []
for year_idx, year in enumerate(years):
    year_data = sorted([(c, gdp_data[c][year_idx]) for c in countries], key=lambda x: x[1], reverse=True)

    snap_style = Style(
        background=PAGE_BG,
        plot_background=PAGE_BG,
        foreground=INK,
        foreground_strong=INK,
        foreground_subtle=INK_MUTED,
        title_font_size=52,
        label_font_size=36,
        major_label_font_size=32,
        legend_font_size=32,
        value_font_size=28,
    )

    chart = pygal.HorizontalBar(
        width=1500,
        height=950,
        style=snap_style,
        show_legend=False,
        title=str(year),
        x_title="GDP (Trillion USD)",
        print_values=True,
        print_values_position="middle",
        value_formatter=lambda x: f"${x:.1f}T" if x is not None else "",
        margin=40,
        spacing=12,
        truncate_label=-1,
        show_x_labels=True,
        x_label_rotation=0,
        show_minor_x_labels=False,
    )

    chart.x_labels = [c for c, _ in year_data]
    num_countries = len(year_data)
    for idx, (country, value) in enumerate(year_data):
        slot = [None] * num_countries
        slot[idx] = {"value": value, "color": country_colors[country]}
        chart.add(country, slot)

    charts.append(chart)

# Render each chart to PNG
chart_images = []
for chart in charts:
    svg_data = chart.render()
    png_data = cairosvg.svg2png(bytestring=svg_data, output_width=1500, output_height=950)
    img = Image.open(BytesIO(png_data))
    chart_images.append(img)

# Composite 3×2 grid at 4800 × 2700
grid_width = 4800
grid_height = 2700
title_height = 160
legend_height = 120
content_height = grid_height - title_height - legend_height
cell_width = grid_width // 3
cell_height = content_height // 2

combined = Image.new("RGB", (grid_width, grid_height), PAGE_BG)
draw = ImageDraw.Draw(combined)

try:
    title_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 72)
    legend_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 36)
except OSError:
    title_font = ImageFont.load_default()
    legend_font = ImageFont.load_default()

title_text = "GDP Country Rankings · bar-race-animated · python · pygal · anyplot.ai"
bbox = draw.textbbox((0, 0), title_text, font=title_font)
title_width = bbox[2] - bbox[0]
draw.text(((grid_width - title_width) // 2, 40), title_text, fill=INK, font=title_font)

positions = [(0, 0), (1, 0), (2, 0), (0, 1), (1, 1), (2, 1)]
for idx, (col, row) in enumerate(positions):
    if idx < len(chart_images):
        img = chart_images[idx].resize((cell_width, cell_height), Image.Resampling.LANCZOS)
        x = col * cell_width
        y = title_height + row * cell_height
        combined.paste(img, (x, y))

# Legend bar at bottom
legend_y = grid_height - legend_height + 25
box_size = 40
spacing_between = grid_width // len(countries)
legend_x_start = spacing_between // 2 - 80

for i, country in enumerate(countries):
    x_pos = legend_x_start + i * spacing_between
    draw.rectangle([x_pos, legend_y, x_pos + box_size, legend_y + box_size], fill=country_colors[country])
    draw.text((x_pos + box_size + 12, legend_y - 2), country, fill=INK, font=legend_font)

combined.save(f"plot-{THEME}.png", dpi=(300, 300))

# HTML: interactive 2023 snapshot with pygal tooltips
html_style = Style(
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
)

html_chart = pygal.HorizontalBar(
    width=1200,
    height=800,
    style=html_style,
    show_legend=True,
    title="GDP Country Rankings 2023 · bar-race-animated · python · pygal · anyplot.ai",
    x_title="GDP (Trillion USD)",
    print_values=True,
    value_formatter=lambda x: f"${x:.1f}T" if x is not None else "",
)

final_data = sorted([(c, gdp_data[c][-1]) for c in countries], key=lambda x: x[1], reverse=True)

html_chart.x_labels = [c for c, _ in final_data]
num_final = len(final_data)
for idx, (country, value) in enumerate(final_data):
    slot = [None] * num_final
    slot[idx] = {"value": value, "color": country_colors[country]}
    html_chart.add(country, slot)

with open(f"plot-{THEME}.html", "wb") as f:
    f.write(html_chart.render())
