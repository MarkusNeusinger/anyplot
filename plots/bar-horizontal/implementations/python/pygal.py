""" anyplot.ai
bar-horizontal: Horizontal Bar Chart
Library: pygal 3.1.3 | Python 3.13.14
Quality: 87/100 | Updated: 2026-08-05
"""

import os

import pygal
from pygal.style import Style


# Theme tokens (Imprint palette)
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"
BRAND = "#009E73"  # Imprint palette position 1

# Data - Retail revenue by product category (sorted descending for ranking display)
categories = [
    "Electronics",
    "Apparel",
    "Home & Furniture",
    "Groceries",
    "Health & Beauty",
    "Sporting Goods",
    "Toys & Games",
    "Books & Media",
    "Automotive",
    "Garden & Outdoor",
]
values = [842.6, 615.3, 498.7, 437.2, 356.8, 289.4, 214.5, 156.9, 128.3, 97.6]

# Title fontsize scales with title length (formula: prompts/plot-generator.md)
TITLE = "Retail Revenue by Category · bar-horizontal · python · pygal · anyplot.ai"
_ratio = 67 / len(TITLE) if len(TITLE) > 67 else 1.0
title_font_size = max(44, round(66 * _ratio))

# Custom style with theme-adaptive colors, sized for the 3200x1800 canvas
custom_style = Style(
    background=PAGE_BG,
    plot_background=PAGE_BG,
    foreground=INK,
    foreground_strong=INK,
    foreground_subtle=INK_MUTED,
    colors=(BRAND,),
    title_font_size=title_font_size,
    label_font_size=56,
    major_label_font_size=44,
    legend_font_size=44,
    value_font_size=36,
    stroke_width=2.5,
)

# Create horizontal bar chart - ultra-minimal, no x-axis guides
chart = pygal.HorizontalBar(
    width=3200,
    height=1800,
    style=custom_style,
    title=TITLE,
    x_title="Revenue ($M)",
    show_legend=False,
    show_y_guides=False,
    show_x_guides=False,
    spacing=20,
    margin=40,
    margin_left=280,
    margin_right=140,
    margin_top=100,
    margin_bottom=100,
    print_values=True,
    print_values_position="end",
    value_formatter=lambda x: f"${x:,.1f}M",
    truncate_label=-1,
)

# Add data as single series. pygal.HorizontalBar transposes axes internally,
# so x_labels carries the category axis and y_labels the value-tick axis.
chart.add("Revenue", values)
chart.x_labels = categories
chart.y_labels = [str(v) for v in range(0, 901, 150)]

# Save outputs
chart.render_to_png(f"plot-{THEME}.png")
chart.render_to_file(f"plot-{THEME}.html")
