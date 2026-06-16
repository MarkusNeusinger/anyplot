""" anyplot.ai
scatter-text: Scatter Plot with Text Labels Instead of Points
Library: pygal 3.1.0 | Python 3.13.13
Quality: 83/100 | Created: 2026-05-17
"""

import os

import pygal
from pygal.style import Style


THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"
BRAND = "#009E73"

IMPRINT = ("#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477")

custom_style = Style(
    background=PAGE_BG,
    plot_background=PAGE_BG,
    foreground=INK,
    foreground_strong=INK,
    foreground_subtle=INK_MUTED,
    colors=IMPRINT,
    title_font_size=28,
    label_font_size=18,
    major_label_font_size=16,
    legend_font_size=16,
    value_font_size=14,
    stroke_width=2,
)

# Data: Product positioning (Price Competitiveness vs. Feature Completeness)
products = [
    {"x": 2.1, "y": 3.2, "label": "Budget Start-up Kit"},
    {"x": 3.5, "y": 2.8, "label": "Standard Pro"},
    {"x": 4.2, "y": 4.1, "label": "Premium Suite"},
    {"x": 1.8, "y": 4.5, "label": "Full Enterprise"},
    {"x": 3.9, "y": 1.9, "label": "Lite Essentials"},
    {"x": 2.7, "y": 3.7, "label": "Growth Package"},
    {"x": 4.6, "y": 3.3, "label": "Elite Plus"},
    {"x": 1.2, "y": 2.1, "label": "Basic Tier"},
    {"x": 3.3, "y": 4.8, "label": "Advanced Max"},
    {"x": 4.8, "y": 2.5, "label": "Performance Edge"},
]

# Plot
chart = pygal.XY(
    style=custom_style,
    width=4800,
    height=2700,
    title="scatter-text · Python · pygal · anyplot.ai",
    x_title="Price Competitiveness",
    y_title="Feature Completeness",
    show_legend=False,
    show_dots=False,
    show_y_guides=True,
    dots_size=0,
)

# Add data series with text labels
chart.add(
    "Products",
    [
        {
            "value": (p["x"], p["y"]),
            "label": p["label"],
            "color": BRAND,
        }
        for p in products
    ],
)

# Set axis ranges
chart.range = (0, 5.5)

# Save
chart.render_to_png(f"plot-{THEME}.png")
with open(f"plot-{THEME}.html", "wb") as f:
    f.write(chart.render())
