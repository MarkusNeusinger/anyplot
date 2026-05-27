""" anyplot.ai
line-annotated-events: Annotated Line Plot with Event Markers
Library: altair 6.1.0 | Python 3.13.13
Quality: 93/100 | Updated: 2026-05-16
"""

import os
import sys


sys.path.pop(0)

import altair as alt
import numpy as np
import pandas as pd


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

BRAND = "#009E73"  # Okabe-Ito position 1 (bluish green)
EVENT_COLOR = "#C475FD"  # Okabe-Ito position 2 (vermillion)

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
        "event_type": ["Earnings", "Earnings", "Product", "Earnings", "Analyst", "Earnings"],
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
    .mark_line(strokeWidth=3, color=BRAND)
    .encode(
        x=alt.X("date:T", title="Date"),
        y=alt.Y("price:Q", title="Stock Price ($)", scale=alt.Scale(domain=[prices.min() * 0.95, prices.max() * 1.12])),
    )
)

# Get the price range for dynamic rule scaling
price_min = prices.min() * 0.95
price_max = prices.max() * 1.12

# Vertical rule marks for events (dynamic y2 based on price range)
rules = (
    alt.Chart(events)
    .mark_rule(strokeWidth=2, strokeDash=[6, 4], color=EVENT_COLOR, opacity=0.7)
    .encode(x=alt.X("event_date:T"), y=alt.value(price_min), y2=alt.value(price_max))
)

# Event markers (points at the top)
markers = (
    alt.Chart(events)
    .mark_point(size=300, filled=True, color=EVENT_COLOR, stroke=INK, strokeWidth=2)
    .encode(x=alt.X("event_date:T"), y=alt.Y("y_position:Q"), tooltip=["event_label:N", "event_type:N", "event_date:T"])
)

# Event labels
labels = (
    alt.Chart(events)
    .mark_text(align="center", baseline="bottom", fontSize=14, fontWeight="bold", color=INK, dy=-15)
    .encode(x=alt.X("event_date:T"), y=alt.Y("y_position:Q"), text="event_label:N")
)

# Combine all layers
chart = (
    alt.layer(line, rules, markers, labels)
    .properties(
        width=1600,
        height=900,
        background=PAGE_BG,
        title=alt.Title("line-annotated-events · altair · anyplot.ai", fontSize=28, anchor="middle"),
    )
    .configure_view(fill=PAGE_BG, stroke=INK_SOFT, strokeWidth=0)
    .configure_axis(
        domainColor=INK_SOFT,
        tickColor=INK_SOFT,
        gridColor=INK,
        gridOpacity=0.10,
        labelColor=INK_SOFT,
        labelFontSize=18,
        titleColor=INK,
        titleFontSize=22,
    )
    .configure_title(color=INK, fontSize=28)
    .configure_legend(
        fillColor=ELEVATED_BG,
        strokeColor=INK_SOFT,
        labelColor=INK_SOFT,
        labelFontSize=16,
        titleColor=INK,
        titleFontSize=18,
    )
)

# Save as PNG and HTML
chart.save(f"plot-{THEME}.png", scale_factor=3.0)
chart.interactive().save(f"plot-{THEME}.html")
