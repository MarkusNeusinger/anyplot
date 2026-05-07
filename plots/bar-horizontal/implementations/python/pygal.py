""" anyplot.ai
bar-horizontal: Horizontal Bar Chart
Library: pygal 3.1.0 | Python 3.13.13
Quality: 91/100 | Updated: 2026-05-07
"""

import os

import pygal
from pygal.style import Style


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"
BRAND = "#009E73"  # Okabe-Ito position 1

# Data - Programming language popularity (sorted descending for ranking display)
categories = ["Python", "JavaScript", "Java", "C++", "TypeScript", "C#", "Go", "Rust", "PHP", "Swift"]
values = [68.7, 62.3, 45.2, 38.5, 37.1, 29.8, 22.4, 18.6, 16.3, 12.9]

# Custom style for large canvas with theme-adaptive colors
custom_style = Style(
    background=PAGE_BG,
    plot_background=PAGE_BG,
    foreground=INK,
    foreground_strong=INK,
    foreground_subtle=INK_MUTED,
    colors=(BRAND,),
    title_font_size=28,
    label_font_size=22,
    major_label_font_size=18,
    legend_font_size=16,
    value_font_size=16,
)

# Create horizontal bar chart
chart = pygal.HorizontalBar(
    width=4800,
    height=2700,
    style=custom_style,
    title="bar-horizontal · pygal · anyplot.ai",
    x_title="Popularity (%)",
    show_legend=False,
    show_y_guides=False,
    show_x_guides=True,
    spacing=30,
    margin=50,
    margin_left=200,
    margin_right=60,
    margin_top=80,
    margin_bottom=80,
    print_values=True,
    print_values_position="end",
    value_formatter=lambda x: f"{x:.1f}%",
    truncate_label=-1,
)

# Add data as single series with category labels on y-axis
chart.add("Popularity", values)
chart.x_labels = [str(i * 10) for i in range(8)]
chart.y_labels = categories

# Save outputs
chart.render_to_png(f"plot-{THEME}.png")
chart.render_to_file(f"plot-{THEME}.html")
