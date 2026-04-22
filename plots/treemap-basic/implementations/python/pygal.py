""" pyplots.ai
treemap-basic: Basic Treemap
Library: pygal 3.1.0 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-24
"""

import pygal
from pygal.style import Style


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

# Custom style for 4800x2700 px canvas
custom_style = Style(
    background="white",
    plot_background="white",
    foreground="#333",
    foreground_strong="#333",
    foreground_subtle="#666",
    colors=("#306998", "#FFD43B", "#4ECDC4", "#FF6B6B"),
    title_font_size=72,
    label_font_size=42,
    major_label_font_size=42,
    legend_font_size=42,
    value_font_size=36,
    tooltip_font_size=36,
)

# Create treemap
chart = pygal.Treemap(
    width=4800,
    height=2700,
    style=custom_style,
    title="Budget Allocation · treemap-basic · pygal · pyplots.ai",
    legend_at_bottom=True,
    legend_at_bottom_columns=4,
    print_values=True,
    value_formatter=lambda x: f"${x}K",
)

# Add data by category
for category, items in data.items():
    chart.add(category, items)

# Save as PNG and HTML
chart.render_to_png("plot.png")
chart.render_to_file("plot.html")
