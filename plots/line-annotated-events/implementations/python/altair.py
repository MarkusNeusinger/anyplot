""" pyplots.ai
line-annotated-events: Annotated Line Plot with Event Markers
Library: altair 6.0.0 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-31
"""

import altair as alt
import numpy as np
import pandas as pd


# Data
np.random.seed(42)

# Generate daily stock price data for one year
dates = pd.date_range(start="2024-01-01", periods=250, freq="B")  # Business days
base_price = 150
returns = np.random.normal(0.0005, 0.015, len(dates))
prices = base_price * np.exp(np.cumsum(returns))

df = pd.DataFrame({"date": dates, "price": prices})

# Define key events (quarterly earnings and other milestones)
events = pd.DataFrame(
    {
        "event_date": pd.to_datetime(
            ["2024-02-15", "2024-04-25", "2024-06-10", "2024-07-24", "2024-09-18", "2024-11-05"]
        ),
        "event_label": [
            "Q4 Earnings",
            "Q1 Earnings",
            "Product Launch",
            "Q2 Earnings",
            "Analyst Upgrade",
            "Q3 Earnings",
        ],
    }
)

# Get y positions for event labels (alternating heights to avoid overlap)
events["y_position"] = [
    prices.max() * 1.08,
    prices.max() * 1.02,
    prices.max() * 1.08,
    prices.max() * 1.02,
    prices.max() * 1.08,
    prices.max() * 1.02,
]

# Base line chart for stock price
line = (
    alt.Chart(df)
    .mark_line(strokeWidth=3, color="#306998")
    .encode(
        x=alt.X("date:T", title="Date", axis=alt.Axis(labelFontSize=18, titleFontSize=22)),
        y=alt.Y(
            "price:Q",
            title="Stock Price ($)",
            scale=alt.Scale(domain=[prices.min() * 0.95, prices.max() * 1.12]),
            axis=alt.Axis(labelFontSize=18, titleFontSize=22),
        ),
    )
)

# Vertical rule marks for events
rules = (
    alt.Chart(events)
    .mark_rule(strokeWidth=2, strokeDash=[6, 4], color="#FFD43B")
    .encode(x=alt.X("event_date:T"), y=alt.value(0), y2=alt.value(900))
)

# Event markers (points at the top)
markers = (
    alt.Chart(events)
    .mark_point(size=300, filled=True, color="#FFD43B", stroke="#306998", strokeWidth=2)
    .encode(x=alt.X("event_date:T"), y=alt.Y("y_position:Q"))
)

# Event labels
labels = (
    alt.Chart(events)
    .mark_text(align="center", baseline="bottom", fontSize=16, fontWeight="bold", color="#333333", dy=-15)
    .encode(x=alt.X("event_date:T"), y=alt.Y("y_position:Q"), text="event_label:N")
)

# Combine all layers
chart = (
    alt.layer(line, rules, markers, labels)
    .properties(
        width=1600,
        height=900,
        title=alt.Title("line-annotated-events · altair · pyplots.ai", fontSize=28, anchor="middle"),
    )
    .configure_view(strokeWidth=0)
    .configure_axis(labelFontSize=18, titleFontSize=22, gridColor="#cccccc", gridOpacity=0.3)
)

# Save as PNG
chart.save("plot.png", scale_factor=3.0)

# Save interactive HTML version
chart.interactive().save("plot.html")
