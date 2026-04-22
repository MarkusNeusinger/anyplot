""" pyplots.ai
line-annotated-events: Annotated Line Plot with Event Markers
Library: pygal 3.1.0 | Python 3.13.11
Quality: 72/100 | Created: 2025-12-31
"""

import numpy as np
import pygal
from pygal.style import Style


# Data - Stock price over a year with quarterly events
np.random.seed(42)
n_days = 250  # Trading days in a year

# Generate realistic stock-like price data with trend
base_price = 150
returns = np.random.randn(n_days) * 0.012
prices = base_price * np.cumprod(1 + returns)

# Event data - indices and labels (quarterly earnings + product launch)
events = [(31, "Q4 Earnings"), (94, "Q1 Earnings"), (136, "Product Launch"), (157, "Q2 Earnings"), (220, "Q3 Earnings")]

# Custom style for 4800x2700 canvas with large fonts
custom_style = Style(
    background="white",
    plot_background="#fafafa",
    foreground="#333333",
    foreground_strong="#1a1a1a",
    foreground_subtle="#666666",
    colors=("#306998", "#E74C3C", "#F39C12", "#9B59B6", "#27AE60", "#3498DB"),
    title_font_size=72,
    label_font_size=42,
    major_label_font_size=38,
    legend_font_size=42,
    value_font_size=36,
    value_label_font_size=34,
    tooltip_font_size=32,
    stroke_width=6,
    font_family="sans-serif",
)

# Create XY chart for better control over coordinates
chart = pygal.XY(
    width=4800,
    height=2700,
    style=custom_style,
    title="line-annotated-events · pygal · pyplots.ai",
    x_title="Trading Day (2024)",
    y_title="Stock Price (USD)",
    show_dots=False,
    stroke_style={"width": 6, "linecap": "round"},
    show_legend=True,
    legend_at_bottom=True,
    legend_at_bottom_columns=3,
    show_x_guides=False,
    show_y_guides=True,
    margin=100,
    margin_bottom=200,
    margin_left=200,
    margin_right=100,
    print_values=False,
    interpolate="cubic",
    range=(min(prices) * 0.95, max(prices) * 1.08),
    xrange=(0, n_days),
    x_labels_major_count=6,
    show_minor_x_labels=False,
)

# Set numeric x-axis labels for trading days
chart.x_labels = [0, 50, 100, 150, 200, 250]

# Add main stock price line as XY coordinates
price_data = [(i, prices[i]) for i in range(n_days)]
chart.add("Stock Price", price_data, stroke_style={"width": 6})

# Add event markers as separate dot series with vertical line effect
# Each event gets its own series for clear legend labeling
y_min = min(prices) * 0.95
y_max = max(prices) * 1.08

for event_idx, label in events:
    # Create vertical line effect using multiple points
    event_price = prices[event_idx]
    # Vertical line from bottom to the event point
    vertical_line = [(event_idx, y_min), (event_idx, event_price)]
    # Add the vertical line with dashed effect
    chart.add(label, vertical_line, stroke_style={"width": 4, "dasharray": "15, 10"}, show_dots=True, dots_size=18)

# Render outputs
chart.render_to_png("plot.png")
chart.render_to_file("plot.html")
