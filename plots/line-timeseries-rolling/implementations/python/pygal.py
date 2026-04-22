""" pyplots.ai
line-timeseries-rolling: Time Series with Rolling Average Overlay
Library: pygal 3.1.0 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-30
"""

import random
from datetime import datetime, timedelta

import pygal
from pygal.style import Style


# Seed for reproducibility
random.seed(42)

# Generate daily temperature readings for 4 months
start_date = datetime(2024, 1, 1)
dates = [start_date + timedelta(days=i) for i in range(120)]

# Generate temperature data with seasonal trend and noise
temperatures = []
for i in range(120):
    # Seasonal variation: winter to early spring
    seasonal = 5 + 8 * (i / 120)  # Gradual warming from 5°C to 13°C
    noise = random.gauss(0, 3)
    temp = seasonal + noise
    temperatures.append(round(temp, 1))

# Calculate 7-day rolling average (None for first 6 days)
window_size = 7
rolling_avg = []
for i in range(len(temperatures)):
    if i < window_size - 1:
        rolling_avg.append(None)  # pygal handles None as gaps
    else:
        window = temperatures[i - window_size + 1 : i + 1]
        avg = sum(window) / window_size
        rolling_avg.append(round(avg, 1))

# Custom style for 4800x2700 canvas with larger fonts
custom_style = Style(
    background="white",
    plot_background="white",
    foreground="#333333",
    foreground_strong="#333333",
    foreground_subtle="#666666",
    colors=("#306998", "#E67E22"),  # Python Blue for raw, Orange for rolling avg (better visibility)
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
    title="line-timeseries-rolling · pygal · pyplots.ai",
    x_title="Date",
    y_title="Temperature (°C)",
    show_x_guides=False,
    show_y_guides=True,
    x_label_rotation=45,
    show_legend=True,
    legend_at_bottom=True,
    legend_at_bottom_columns=2,  # Keep legend items together in 2 columns
    legend_box_size=24,  # Larger legend box for visibility
    truncate_legend=-1,
    show_dots=False,
    stroke_style={"width": 4},
    margin=60,
)

# Add raw temperature data (lighter line)
chart.add("Raw Temperature", temperatures, stroke_style={"width": 2})

# Add rolling average (prominent line)
chart.add("7-Day Rolling Average", rolling_avg, stroke_style={"width": 6})

# Set x-axis labels - show every 2 weeks
x_labels = []
x_labels_major = []
for d in dates:
    if d.day in [1, 15]:  # 1st and 15th of each month
        label = d.strftime("%b %d")
        x_labels.append(label)
        x_labels_major.append(label)
    else:
        x_labels.append("")

chart.x_labels = x_labels
chart.x_labels_major = x_labels_major

# Save as HTML and PNG
chart.render_to_file("plot.html")
chart.render_to_png("plot.png")
