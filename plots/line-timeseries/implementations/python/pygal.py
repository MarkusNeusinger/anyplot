""" pyplots.ai
line-timeseries: Time Series Line Plot
Library: pygal 3.1.0 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-26
"""

import random
from datetime import datetime, timedelta

import pygal
from pygal.style import Style


# Seed for reproducibility
random.seed(42)

# Generate realistic daily stock price data for one year
start_date = datetime(2024, 1, 1)
dates = [start_date + timedelta(days=i) for i in range(365)]

# Simulate stock price with trend and volatility
price = 150.0
prices = []
for _ in range(365):
    # Add slight upward trend with random daily changes
    change = random.gauss(0.1, 2.5)
    price = max(100, price + change)  # Prevent going too low
    prices.append(round(price, 2))

# Custom style for 4800x2700 canvas with larger fonts
custom_style = Style(
    background="white",
    plot_background="white",
    foreground="#333333",
    foreground_strong="#333333",
    foreground_subtle="#666666",
    colors=("#306998",),  # Python Blue
    title_font_size=72,
    label_font_size=48,
    major_label_font_size=42,
    legend_font_size=42,
    value_font_size=36,
    guide_stroke_color="#cccccc",
    guide_stroke_dasharray="2,4",
)

# Create line chart
chart = pygal.Line(
    width=4800,
    height=2700,
    style=custom_style,
    title="line-timeseries · pygal · pyplots.ai",
    x_title="Date",
    y_title="Stock Price (USD)",
    show_x_guides=False,
    show_y_guides=True,
    x_label_rotation=45,
    show_legend=True,
    legend_at_bottom=True,
    truncate_legend=-1,
    show_dots=False,
    stroke_style={"width": 5},
    margin=60,
)

# Add data series
chart.add("ACME Corp Stock", prices)

# Set x-axis labels - show first of each month only
x_labels = []
x_labels_major = []
for d in dates:
    if d.day == 1:  # First of each month
        x_labels.append(d.strftime("%b %Y"))
        x_labels_major.append(d.strftime("%b %Y"))
    else:
        x_labels.append("")

chart.x_labels = x_labels
chart.x_labels_major = x_labels_major

# Save as PNG and HTML
chart.render_to_file("plot.html")
chart.render_to_png("plot.png")
