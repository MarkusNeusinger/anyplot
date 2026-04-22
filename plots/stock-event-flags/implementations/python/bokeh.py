""" pyplots.ai
stock-event-flags: Stock Chart with Event Flags
Library: bokeh 3.8.2 | Python 3.13.11
Quality: 91/100 | Created: 2026-01-21
"""

import numpy as np
import pandas as pd
from bokeh.io import export_png
from bokeh.models import ColumnDataSource, HoverTool, Label, Legend, LegendItem
from bokeh.plotting import figure, save


# Data - Generate synthetic stock price data for ~180 trading days
np.random.seed(42)
n_days = 180
start_date = pd.Timestamp("2024-01-02")
dates = pd.bdate_range(start=start_date, periods=n_days)

# Generate realistic stock price movement using geometric brownian motion
initial_price = 150.0
daily_returns = np.random.normal(0.0005, 0.018, n_days)
close_prices = initial_price * np.cumprod(1 + daily_returns)

# Generate OHLC data
high_prices = close_prices * (1 + np.abs(np.random.normal(0, 0.01, n_days)))
low_prices = close_prices * (1 - np.abs(np.random.normal(0, 0.01, n_days)))
open_prices = np.roll(close_prices, 1)
open_prices[0] = initial_price

df = pd.DataFrame({"date": dates, "open": open_prices, "high": high_prices, "low": low_prices, "close": close_prices})

# Define events with dates, types, and labels
events = [
    {"date": dates[25], "type": "earnings", "label": "Q4 Earnings"},
    {"date": dates[50], "type": "dividend", "label": "Dividend $0.50"},
    {"date": dates[75], "type": "news", "label": "Product Launch"},
    {"date": dates[95], "type": "earnings", "label": "Q1 Earnings"},
    {"date": dates[110], "type": "split", "label": "2:1 Split"},
    {"date": dates[140], "type": "dividend", "label": "Dividend $0.55"},
    {"date": dates[160], "type": "news", "label": "Partnership"},
]
events_df = pd.DataFrame(events)

# Event type colors and styling
event_colors = {
    "earnings": "#306998",  # Python Blue
    "dividend": "#2ECC71",  # Green
    "split": "#9B59B6",  # Purple
    "news": "#FFD43B",  # Python Yellow
}

event_markers = {"earnings": "triangle", "dividend": "circle", "split": "square", "news": "diamond"}

# Create figure
p = figure(
    width=4800,
    height=2700,
    x_axis_type="datetime",
    title="stock-event-flags · bokeh · pyplots.ai",
    x_axis_label="Date",
    y_axis_label="Price ($)",
    tools="pan,wheel_zoom,box_zoom,reset,save",
)

# Style the figure
p.title.text_font_size = "28pt"
p.xaxis.axis_label_text_font_size = "22pt"
p.yaxis.axis_label_text_font_size = "22pt"
p.xaxis.major_label_text_font_size = "18pt"
p.yaxis.major_label_text_font_size = "18pt"
p.background_fill_color = "#fafafa"
p.grid.grid_line_alpha = 0.4
p.grid.grid_line_dash = [6, 4]

# Plot price as a line chart
source = ColumnDataSource(df)
price_line = p.line(
    x="date", y="close", source=source, line_width=3, line_color="#306998", alpha=0.9, legend_label="Close Price"
)

# Add hover tool for price line
price_hover = HoverTool(
    renderers=[price_line],
    tooltips=[
        ("Date", "@date{%F}"),
        ("Open", "$@open{0.00}"),
        ("High", "$@high{0.00}"),
        ("Low", "$@low{0.00}"),
        ("Close", "$@close{0.00}"),
    ],
    formatters={"@date": "datetime"},
    mode="vline",
)
p.add_tools(price_hover)

# Add vertical dashed lines and flags for each event
legend_items = {}
price_range = close_prices.max() - close_prices.min()

for i, event in events_df.iterrows():
    event_date = event["date"]
    event_type = event["type"]
    event_label = event["label"]
    color = event_colors[event_type]
    marker = event_markers[event_type]

    # Get price at event date
    idx = df[df["date"] == event_date].index[0]
    event_price = df.loc[idx, "close"]

    # Alternate flag positions above/below price
    offset_direction = 1 if i % 2 == 0 else -1
    flag_y = event_price + offset_direction * price_range * 0.15

    # Add vertical dashed line from flag to price
    p.segment(
        x0=[event_date],
        y0=[event_price],
        x1=[event_date],
        y1=[flag_y],
        line_color=color,
        line_dash="dashed",
        line_width=2,
        alpha=0.7,
    )

    # Add flag marker
    flag_source = ColumnDataSource(
        data={"x": [event_date], "y": [flag_y], "label": [event_label], "type": [event_type.capitalize()]}
    )

    # Use scatter with marker parameter (triangle, diamond, square deprecated)
    marker_size = 30 if marker == "diamond" else 25
    renderer = p.scatter(
        x="x",
        y="y",
        source=flag_source,
        size=marker_size,
        color=color,
        alpha=0.9,
        line_color="white",
        line_width=2,
        marker=marker,
    )

    # Collect renderers for legend
    if event_type not in legend_items:
        legend_items[event_type] = renderer

    # Add hover for event flags
    event_hover = HoverTool(
        renderers=[renderer],
        tooltips=[("Event", "@type"), ("Label", "@label"), ("Date", "@x{%F}")],
        formatters={"@x": "datetime"},
    )
    p.add_tools(event_hover)

    # Add label next to flag
    label_offset_x = 15
    label = Label(
        x=event_date,
        y=flag_y,
        text=event_label,
        text_font_size="14pt",
        text_color=color,
        x_offset=label_offset_x,
        y_offset=5 if offset_direction > 0 else -20,
        text_font_style="bold",
    )
    p.add_layout(label)

# Create custom legend for event types
legend_items_list = [LegendItem(label="Close Price", renderers=[price_line])]
for event_type, renderer in legend_items.items():
    legend_items_list.append(LegendItem(label=event_type.capitalize(), renderers=[renderer]))

legend = Legend(items=legend_items_list, location="top_left", label_text_font_size="16pt", background_fill_alpha=0.8)
p.add_layout(legend)
p.legend.click_policy = "hide"

# Save outputs
export_png(p, filename="plot.png")
save(p, filename="plot.html", title="Stock Chart with Event Flags")
