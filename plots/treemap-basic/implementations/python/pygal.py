""" anyplot.ai
treemap-basic: Basic Treemap
Library: pygal 3.1.0 | Python 3.13.13
Quality: 91/100 | Updated: 2026-05-05
"""

import os

import pygal
from pygal.style import Style


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Okabe-Ito palette (first series always brand green)
IMPRINT = ("#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477")

# Data - Budget allocation by department and project (in $K)
data = {
    "Engineering": [
        {"value": 450, "label": "R&D"},
        {"value": 280, "label": "Infrastructure"},
        {"value": 180, "label": "Tools"},
    ],
    "Marketing": [
        {"value": 320, "label": "Digital"},
        {"value": 210, "label": "Brand"},
        {"value": 120, "label": "Events"},
    ],
    "Sales": [
        {"value": 380, "label": "Enterprise"},
        {"value": 240, "label": "SMB"},
        {"value": 150, "label": "Partners"},
    ],
    "Operations": [
        {"value": 200, "label": "Facilities"},
        {"value": 160, "label": "IT Support"},
        {"value": 110, "label": "HR"},
    ],
}

# Custom style for 4800x2700 px canvas with theme-adaptive colors
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
)

# Create treemap
chart = pygal.Treemap(
    width=4800,
    height=2700,
    style=custom_style,
    title="Budget Allocation · treemap-basic · pygal · anyplot.ai",
    legend_at_bottom=True,
    legend_at_bottom_columns=4,
    print_values=True,
    value_formatter=lambda x: f"${x}K",
)

# Add data by category
for category, items in data.items():
    chart.add(category, items)

# Save as PNG and HTML with theme suffix
chart.render_to_png(f"plot-{THEME}.png")
with open(f"plot-{THEME}.html", "wb") as f:
    f.write(chart.render())
