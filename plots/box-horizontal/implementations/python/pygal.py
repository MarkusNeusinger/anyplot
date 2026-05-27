""" anyplot.ai
box-horizontal: Horizontal Box Plot
Library: pygal 3.1.0 | Python 3.13.13
Quality: 83/100 | Updated: 2026-05-12
"""

import os

import numpy as np
import pygal
from pygal.style import Style


THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

IMPRINT = ("#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030")

# Data - Salary ranges by job title
np.random.seed(42)
categories = ["Software Engineer", "Data Scientist", "Product Manager", "Designer", "DevOps Engineer"]
data = {
    "Software Engineer": np.random.normal(125000, 20000, 100),
    "Data Scientist": np.random.normal(130000, 22000, 100),
    "Product Manager": np.random.normal(140000, 25000, 100),
    "Designer": np.random.normal(105000, 18000, 100),
    "DevOps Engineer": np.random.normal(135000, 21000, 100),
}

# Custom style using theme-adaptive tokens
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

# Create horizontal box dynamically (pygal doesn't include HorizontalBox natively)
HorizontalBox = type("HorizontalBox", (pygal.graph.horizontal.HorizontalGraph, pygal.graph.box.Box), {})

# Create chart
chart = HorizontalBox(
    width=4800,
    height=2700,
    style=custom_style,
    title="box-horizontal · pygal · anyplot.ai",
    x_title="Salary (USD)",
    show_legend=True,
    show_y_guides=True,
    show_x_guides=False,
    margin=80,
    margin_left=300,
    margin_bottom=120,
    box_mode="tukey",
)

# Set category labels on y-axis
chart.x_labels = categories

# Add data for each category
for category in categories:
    chart.add(category, data[category].tolist())

# Save outputs
chart.render_to_file(f"plot-{THEME}.html")
chart.render_to_png(f"plot-{THEME}.png")
