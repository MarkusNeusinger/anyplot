""" pyplots.ai
pie-portfolio-interactive: Interactive Portfolio Allocation Chart
Library: pygal 3.1.0 | Python 3.13.11
Quality: 90/100 | Created: 2026-01-20
"""

import pygal
from pygal.style import Style


# Data - Investment portfolio allocation by asset class
categories = {
    "Equities": {"US Large Cap": 25.0, "US Mid Cap": 10.0, "International Developed": 12.0, "Emerging Markets": 8.0},
    "Fixed Income": {"US Treasury": 15.0, "Corporate Bonds": 8.0, "Municipal Bonds": 5.0},
    "Alternatives": {"Real Estate": 7.0, "Commodities": 5.0, "Private Equity": 5.0},
}

# Custom style for large canvas with improved legibility
custom_style = Style(
    background="white",
    plot_background="white",
    foreground="#333333",
    foreground_strong="#333333",
    foreground_subtle="#666666",
    colors=(
        "#306998",  # Blue - Equities
        "#FFD43B",  # Yellow - Fixed Income
        "#E07C3E",  # Orange - Alternatives
    ),
    title_font_size=72,
    label_font_size=48,
    major_label_font_size=48,
    legend_font_size=52,
    value_font_size=60,
    tooltip_font_size=40,
    value_label_font_size=60,
)

# Create interactive pie chart with value labels on slices
chart = pygal.Pie(
    width=4800,
    height=2700,
    style=custom_style,
    inner_radius=0.4,  # Donut style
    show_legend=True,
    legend_at_bottom=True,
    legend_at_bottom_columns=3,  # All legend items in one row for balance
    legend_box_size=52,
    title="pie-portfolio-interactive · pygal · pyplots.ai",
    print_values=True,  # Show percentage values on slices
    print_labels=True,  # Show labels on slices for better PNG readability
    value_formatter=lambda x: f"{x:.0f}%",  # Format as percentage
    truncate_legend=None,  # Don't truncate legend text
    margin=100,  # Margin around chart
    margin_bottom=200,  # Extra margin for legend
    spacing=30,  # Spacing between chart and legend
)

# Add category-level slices with simple values (not dict) for print_values to work
for category, holdings in categories.items():
    total = sum(holdings.values())
    # Use simple numeric value for proper value display on slices
    # Legend shows category name, slice shows percentage value
    chart.add(f"{category} ({total:.0f}%)", total)

# Render to PNG (primary output as per spec)
chart.render_to_png("plot.png")
