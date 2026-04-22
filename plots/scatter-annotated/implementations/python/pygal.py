""" pyplots.ai
scatter-annotated: Annotated Scatter Plot with Text Labels
Library: pygal 3.1.0 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-30
"""

import numpy as np
import pygal
from pygal.style import Style


# Data - Company market performance (market cap vs revenue)
np.random.seed(42)
companies = [
    "TechFlow",
    "DataPrime",
    "CloudNine",
    "NetWave",
    "CodeSphere",
    "ByteLogic",
    "SoftEdge",
    "DevStack",
    "AppForge",
    "WebCore",
    "CyberLink",
    "DigiTech",
]

# Generate realistic market cap (x) and revenue (y) data in billions
# Spread out to avoid overlap
market_cap = np.array([15, 45, 75, 105, 135, 25, 55, 85, 115, 145, 35, 95])
revenue = np.array([8, 22, 35, 28, 48, 12, 18, 42, 32, 55, 15, 38])

# Create color palette - cycle through distinct colors for each company
colors = (
    "#306998",  # Python Blue
    "#FFD43B",  # Python Yellow
    "#E74C3C",  # Red
    "#2ECC71",  # Green
    "#9B59B6",  # Purple
    "#3498DB",  # Light Blue
    "#E67E22",  # Orange
    "#1ABC9C",  # Teal
    "#34495E",  # Dark Gray
    "#F39C12",  # Gold
    "#16A085",  # Dark Teal
    "#8E44AD",  # Dark Purple
)

# Custom style for large canvas with larger value font for annotations
custom_style = Style(
    background="white",
    plot_background="white",
    foreground="#333333",
    foreground_strong="#333333",
    foreground_subtle="#666666",
    colors=colors,
    title_font_size=48,
    label_font_size=32,
    major_label_font_size=28,
    legend_font_size=24,
    value_font_size=28,  # Font size for annotations
    tooltip_font_size=24,
    stroke_width=2,
)

# Store company names for value formatter
company_data = {}

# Create XY chart (scatter plot)
chart = pygal.XY(
    width=4800,
    height=2700,
    style=custom_style,
    title="scatter-annotated · pygal · pyplots.ai",
    x_title="Market Cap (Billion $)",
    y_title="Annual Revenue (Billion $)",
    show_legend=True,
    legend_at_bottom=True,
    legend_at_bottom_columns=6,
    show_x_guides=True,
    show_y_guides=True,
    dots_size=18,
    stroke=False,
    show_dots=True,
    truncate_label=-1,
    x_label_rotation=0,
    range=(0, 65),
    xrange=(0, 165),
    print_values=True,
    print_values_position="top",
)

# Add each company as individual series with its own color for legend identification
# Use formatter dict to show company name instead of coordinates
for i, company in enumerate(companies):
    company_data[(market_cap[i], revenue[i])] = company
    chart.add(
        company,
        [{"value": (market_cap[i], revenue[i]), "label": company, "formatter": lambda x, c=company: c}],
        dots_size=20,
        formatter=lambda x, c=company: c,
    )

# Render to PNG and HTML
chart.render_to_png("plot.png")
chart.render_to_file("plot.html")
