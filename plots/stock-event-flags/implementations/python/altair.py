""" pyplots.ai
stock-event-flags: Stock Chart with Event Flags
Library: altair 6.0.0 | Python 3.13.11
Quality: 91/100 | Created: 2026-01-21
"""

import altair as alt
import numpy as np
import pandas as pd


# Data - Generate synthetic stock price data
np.random.seed(42)
dates = pd.date_range("2024-01-01", periods=180, freq="B")  # Business days

# Generate realistic stock price movement (random walk with drift)
returns = np.random.normal(0.0005, 0.018, len(dates))
prices = 100 * np.exp(np.cumsum(returns))

# Create main price DataFrame
df_price = pd.DataFrame({"date": dates, "close": prices})

# Define significant events
events = [
    {"event_date": "2024-01-25", "event_type": "Earnings", "event_label": "Q4 Earnings Beat"},
    {"event_date": "2024-02-15", "event_type": "Dividend", "event_label": "Dividend $0.25"},
    {"event_date": "2024-03-20", "event_type": "News", "event_label": "Product Launch"},
    {"event_date": "2024-04-24", "event_type": "Earnings", "event_label": "Q1 Results"},
    {"event_date": "2024-05-10", "event_type": "Dividend", "event_label": "Dividend $0.28"},
    {"event_date": "2024-06-05", "event_type": "News", "event_label": "Partnership Deal"},
    {"event_date": "2024-07-24", "event_type": "Earnings", "event_label": "Q2 Strong Growth"},
    {"event_date": "2024-08-20", "event_type": "Split", "event_label": "2:1 Stock Split"},
]

df_events = pd.DataFrame(events)
df_events["event_date"] = pd.to_datetime(df_events["event_date"])

# Merge events with price to get y-position
df_events = df_events.merge(
    df_price.rename(columns={"date": "event_date", "close": "price_at_event"}), on="event_date", how="left"
)

# For events not on exact trading days, find nearest
for idx, row in df_events.iterrows():
    if pd.isna(row["price_at_event"]):
        nearest_idx = (df_price["date"] - row["event_date"]).abs().idxmin()
        df_events.loc[idx, "price_at_event"] = df_price.loc[nearest_idx, "close"]
        df_events.loc[idx, "event_date"] = df_price.loc[nearest_idx, "date"]

# Calculate flag positions (alternate above/below with offset)
y_min, y_max = df_price["close"].min(), df_price["close"].max()
flag_offset = (y_max - y_min) * 0.15

df_events["flag_y"] = df_events.apply(
    lambda row: row["price_at_event"] + flag_offset if row.name % 2 == 0 else row["price_at_event"] - flag_offset,
    axis=1,
)

# Color mapping for event types
color_map = {"Earnings": "#306998", "Dividend": "#2E8B57", "News": "#FFD43B", "Split": "#E74C3C"}

df_events["color"] = df_events["event_type"].map(color_map)

# Symbol mapping for event types
symbol_map = {"Earnings": "triangle-up", "Dividend": "diamond", "News": "circle", "Split": "square"}
df_events["symbol"] = df_events["event_type"].map(symbol_map)

# Create vertical rule data for connectors
connector_data = []
for _, row in df_events.iterrows():
    connector_data.append({"event_date": row["event_date"], "y": row["price_at_event"]})
    connector_data.append({"event_date": row["event_date"], "y": row["flag_y"]})
    connector_data.append({"event_date": row["event_date"], "y": None})  # Break line

df_connectors = pd.DataFrame(connector_data)

# Price line chart
price_line = (
    alt.Chart(df_price)
    .mark_line(strokeWidth=2.5, color="#306998")
    .encode(
        x=alt.X("date:T", title="Date", axis=alt.Axis(format="%b %Y", labelAngle=-45)),
        y=alt.Y(
            "close:Q",
            title="Stock Price ($)",
            scale=alt.Scale(domain=[y_min - flag_offset * 1.5, y_max + flag_offset * 1.5]),
        ),
        tooltip=[alt.Tooltip("date:T", title="Date"), alt.Tooltip("close:Q", title="Price", format="$.2f")],
    )
)

# Connector lines (vertical dashed lines from flags to price)
connectors = (
    alt.Chart(df_connectors)
    .mark_line(strokeDash=[4, 4], strokeWidth=1.5, opacity=0.6, color="#666666")
    .encode(x="event_date:T", y="y:Q", detail="event_date:T")
)

# Event flags/markers
flags = (
    alt.Chart(df_events)
    .mark_point(size=400, filled=True, strokeWidth=2, stroke="white")
    .encode(
        x="event_date:T",
        y="flag_y:Q",
        color=alt.Color(
            "event_type:N",
            scale=alt.Scale(domain=list(color_map.keys()), range=list(color_map.values())),
            legend=alt.Legend(title="Event Type", titleFontSize=18, labelFontSize=16, symbolSize=300),
        ),
        shape=alt.Shape(
            "event_type:N",
            scale=alt.Scale(domain=list(symbol_map.keys()), range=list(symbol_map.values())),
            legend=None,
        ),
        tooltip=[
            alt.Tooltip("event_date:T", title="Date"),
            alt.Tooltip("event_type:N", title="Type"),
            alt.Tooltip("event_label:N", title="Event"),
            alt.Tooltip("price_at_event:Q", title="Price", format="$.2f"),
        ],
    )
)

# Event labels
labels = (
    alt.Chart(df_events)
    .mark_text(fontSize=14, fontWeight="bold", dy=-20)
    .encode(
        x="event_date:T",
        y="flag_y:Q",
        text="event_label:N",
        color=alt.Color(
            "event_type:N", scale=alt.Scale(domain=list(color_map.keys()), range=list(color_map.values())), legend=None
        ),
    )
)

# Combine all layers
chart = (
    (price_line + connectors + flags + labels)
    .properties(
        width=1600,
        height=900,
        title=alt.Title("stock-event-flags \u00b7 altair \u00b7 pyplots.ai", fontSize=28, anchor="middle"),
    )
    .configure_axis(labelFontSize=18, titleFontSize=22, gridOpacity=0.3)
    .configure_view(strokeWidth=0)
    .interactive()
)

# Save outputs
chart.save("plot.png", scale_factor=3.0)
chart.save("plot.html")
