""" pyplots.ai
stock-event-flags: Stock Chart with Event Flags
Library: pygal 3.1.0 | Python 3.13.11
Quality: 91/100 | Created: 2026-01-21
"""

import numpy as np
import pandas as pd
import pygal
from pygal.style import Style


# Set seed for reproducibility
np.random.seed(42)

# Generate stock price data (simulating ~180 trading days)
start_date = pd.Timestamp("2024-01-02")
trading_days = pd.bdate_range(start=start_date, periods=180)

# Generate realistic stock price movement
initial_price = 150.0
returns = np.random.normal(0.0005, 0.018, len(trading_days))
prices = initial_price * np.cumprod(1 + returns)

# Create price dataframe
df = pd.DataFrame({"date": trading_days, "close": prices})

# Define events with their dates, types, and labels
events = [
    {"date": pd.Timestamp("2024-01-25"), "type": "earnings", "label": "Q4 Beat"},
    {"date": pd.Timestamp("2024-02-15"), "type": "dividend", "label": "$0.25"},
    {"date": pd.Timestamp("2024-03-12"), "type": "news", "label": "Launch"},
    {"date": pd.Timestamp("2024-04-18"), "type": "earnings", "label": "Q1"},
    {"date": pd.Timestamp("2024-05-10"), "type": "dividend", "label": "$0.28"},
    {"date": pd.Timestamp("2024-06-05"), "type": "split", "label": "3:1"},
    {"date": pd.Timestamp("2024-07-22"), "type": "earnings", "label": "Q2"},
    {"date": pd.Timestamp("2024-08-08"), "type": "dividend", "label": "$0.30"},
]

# Event colors by type - distinct and accessible
event_type_colors = {
    "earnings": "#2E86AB",  # teal
    "dividend": "#28A745",  # green
    "news": "#E74C3C",  # red
    "split": "#9B59B6",  # purple
}

# Build color list: price line + 8 connector lines (matching event order) + 4 flag series
connector_colors = [event_type_colors[e["type"]] for e in events]
flag_colors = [event_type_colors[t] for t in ["earnings", "dividend", "split", "news"]]
all_colors = ["#306998"] + connector_colors + flag_colors

custom_style = Style(
    background="white",
    plot_background="white",
    foreground="#333333",
    foreground_strong="#333333",
    foreground_subtle="#888888",
    colors=tuple(all_colors),
    title_font_size=72,
    label_font_size=48,
    major_label_font_size=40,
    legend_font_size=44,
    value_font_size=36,
    stroke_width=4,
    value_label_font_size=32,
    tooltip_font_size=36,
    guide_stroke_color="#CCCCCC",
    guide_stroke_dasharray="5,5",
)

# Use XY chart for precise coordinate control
chart = pygal.XY(
    width=4800,
    height=2700,
    style=custom_style,
    title="stock-event-flags · pygal · pyplots.ai",
    x_title="Trading Day Index (2024)",
    y_title="Stock Price ($)",
    show_x_guides=False,
    show_y_guides=True,
    stroke=True,
    fill=False,
    show_legend=True,
    legend_at_bottom=True,
    legend_at_bottom_columns=5,
    dots_size=3,
    truncate_label=-1,
    truncate_legend=-1,
    margin=50,
    spacing=30,
    x_labels_major_every=20,
    show_minor_x_labels=False,
)

# Add main stock price line
price_points = [(i, df.iloc[i]["close"]) for i in range(len(df))]
chart.add("Stock Price", price_points, dots_size=0, stroke_style={"width": 5})

# Calculate y-axis range for flag positioning
min_price = df["close"].min()
max_price = df["close"].max()
price_range = max_price - min_price

# Flag heights for different event types (above max price)
event_heights = {"earnings": 0.12, "dividend": 0.20, "split": 0.28, "news": 0.36}

# Add all connector lines first (one series per event for clean vertical lines)
for event in events:
    idx = df["date"].searchsorted(event["date"])
    if idx < len(df):
        event_type = event["type"]
        height_offset = event_heights[event_type]
        flag_y = max_price + (price_range * height_offset)
        price_at_event = df.iloc[idx]["close"]

        # Single vertical connector line
        connector_points = [
            (idx, price_at_event),  # Bottom at price level
            (idx, flag_y),  # Top at flag position
        ]
        chart.add(None, connector_points, stroke=True, stroke_style={"width": 2, "dasharray": "6,4"}, show_dots=False)

# Add flag markers grouped by type (for legend)
for event_type in ["earnings", "dividend", "split", "news"]:
    type_events = [e for e in events if e["type"] == event_type]
    height_offset = event_heights[event_type]
    flag_y = max_price + (price_range * height_offset)

    flag_points = []
    for event in type_events:
        idx = df["date"].searchsorted(event["date"])
        if idx < len(df):
            flag_points.append({"value": (idx, flag_y), "label": f"{event_type.upper()}: {event['label']}"})

    type_label = event_type.capitalize()
    chart.add(type_label, flag_points, stroke=False, show_dots=True, dots_size=25)

# Render to PNG and HTML
chart.render_to_png("plot.png")
chart.render_to_file("plot.html")
