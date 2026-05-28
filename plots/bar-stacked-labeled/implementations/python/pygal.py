""" anyplot.ai
bar-stacked-labeled: Stacked Bar Chart with Total Labels
Library: pygal 3.1.0 | Python 3.13.13
Quality: 88/100 | Updated: 2026-05-18
"""

import os
import sys
from pathlib import Path


# Remove the script's directory from sys.path to avoid conflict with pygal.py filename
script_dir = str(Path(__file__).parent)
sys.path = [p for p in sys.path if p != script_dir]

import pygal  # noqa: E402
from pygal.style import Style  # noqa: E402


# Theme tokens (Okabe-Ito palette, theme-adaptive chrome)
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Okabe-Ito palette (first series always #009E73)
IMPRINT = ("#009E73", "#C475FD", "#4467A3", "#BD8233")

# Data - Quarterly revenue by product category (in thousands)
categories = ["Q1", "Q2", "Q3", "Q4"]
products = {
    "Electronics": [180, 95, 140, 220],
    "Furniture": [45, 130, 85, 75],
    "Clothing": [55, 60, 145, 90],
    "Accessories": [32, 45, 38, 115],
}

# Calculate totals for labels
totals = [sum(products[product][i] for product in products) for i in range(len(categories))]

# Custom style for large canvas with theme-adaptive tokens
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
    value_font_size=16,
    stroke_width=3,
)

# Create stacked bar chart with proper legend positioning
chart = pygal.StackedBar(
    width=4800,
    height=2700,
    style=custom_style,
    title="bar-stacked-labeled · Python · pygal · anyplot.ai",
    x_title="Quarter",
    y_title="Revenue ($K)",
    show_y_guides=True,
    show_x_guides=False,
    legend_at_bottom=False,  # Move legend to side to avoid truncation
    legend_at_bottom_columns=None,
    print_values=True,
    print_values_position="top",
    value_formatter=lambda x: "",  # Hide default values
    margin=80,
    margin_right=150,  # Extra space for legend on right
    margin_bottom=200,
    spacing=80,
)

# Set x-axis labels
chart.x_labels = categories

# Add data series with total labels on top
product_list = list(products.items())
for idx, (product, values) in enumerate(product_list):
    is_top = idx == len(product_list) - 1
    if is_top:
        # Top series: show total labels above each bar
        data = [{"value": v, "formatter": lambda x, i=i: f"${totals[i]}K"} for i, v in enumerate(values)]
    else:
        # Other series: no labels
        data = values
    chart.add(product, data)

# Save as PNG and HTML
chart.render_to_png(f"plot-{THEME}.png")
chart.render_to_file(f"plot-{THEME}.html")
