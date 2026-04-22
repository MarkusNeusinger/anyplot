""" pyplots.ai
ohlc-bar: OHLC Bar Chart
Library: altair 6.0.0 | Python 3.13.11
Quality: 92/100 | Created: 2026-01-08
"""

import altair as alt
import numpy as np
import pandas as pd


# Data - Generate 50 trading days of OHLC data
np.random.seed(42)
n_days = 50
dates = pd.date_range("2024-01-02", periods=n_days, freq="B")  # Business days

# Start price and random walk
start_price = 150.0
returns = np.random.normal(0.001, 0.02, n_days)  # Daily returns

# Generate OHLC data
prices = [start_price]
for r in returns[:-1]:
    prices.append(prices[-1] * (1 + r))

opens = []
highs = []
lows = []
closes = []

for base_price in prices:
    daily_volatility = abs(np.random.normal(0, 0.015))
    intraday_move = np.random.normal(0, 0.01)

    open_price = base_price * (1 + np.random.normal(0, 0.005))
    close_price = open_price * (1 + intraday_move)
    high_price = max(open_price, close_price) * (1 + daily_volatility)
    low_price = min(open_price, close_price) * (1 - daily_volatility)

    opens.append(open_price)
    highs.append(high_price)
    lows.append(low_price)
    closes.append(close_price)

df = pd.DataFrame({"date": dates, "open": opens, "high": highs, "low": lows, "close": closes})

# Add color indicator for up/down bars
df["direction"] = ["Up" if c >= o else "Down" for o, c in zip(df["open"], df["close"], strict=True)]

# Color scheme
up_color = "#306998"  # Python Blue for up bars
down_color = "#FFD43B"  # Python Yellow for down bars

# Create OHLC bar chart using layered approach
# High-Low vertical lines
hl_lines = (
    alt.Chart(df)
    .mark_rule(strokeWidth=2)
    .encode(
        x=alt.X("date:T", title="Date", axis=alt.Axis(labelFontSize=18, titleFontSize=22, format="%b %d")),
        y=alt.Y(
            "low:Q", title="Price (USD)", scale=alt.Scale(zero=False), axis=alt.Axis(labelFontSize=18, titleFontSize=22)
        ),
        y2="high:Q",
        color=alt.Color(
            "direction:N",
            scale=alt.Scale(domain=["Up", "Down"], range=[up_color, down_color]),
            legend=alt.Legend(title="Direction", titleFontSize=18, labelFontSize=16),
        ),
    )
)

# Open ticks as short horizontal rules (left side)
open_rules = (
    alt.Chart(df)
    .transform_calculate(
        open_start="datum.date - 10*60*60*1000"  # 10 hours offset in milliseconds
    )
    .mark_rule(strokeWidth=2)
    .encode(
        x="open_start:T",
        x2="date:T",
        y="open:Q",
        color=alt.Color(
            "direction:N", scale=alt.Scale(domain=["Up", "Down"], range=[up_color, down_color]), legend=None
        ),
    )
)

# Create close ticks as short horizontal rules
close_rules = (
    alt.Chart(df)
    .transform_calculate(
        close_end="datum.date + 10*60*60*1000"  # 10 hours offset in milliseconds
    )
    .mark_rule(strokeWidth=2)
    .encode(
        x="date:T",
        x2="close_end:T",
        y="close:Q",
        color=alt.Color(
            "direction:N", scale=alt.Scale(domain=["Up", "Down"], range=[up_color, down_color]), legend=None
        ),
    )
)

# Layer all components
chart = (
    alt.layer(hl_lines, open_rules, close_rules)
    .properties(
        width=1600,
        height=900,
        title=alt.Title("ohlc-bar \u00b7 altair \u00b7 pyplots.ai", fontSize=28, anchor="middle"),
    )
    .configure_axis(labelFontSize=18, titleFontSize=22, gridColor="#cccccc", gridOpacity=0.3)
    .configure_view(strokeWidth=0)
    .configure_legend(titleFontSize=18, labelFontSize=16)
)

# Save as PNG (4800 x 2700 px with scale_factor=3)
chart.save("plot.png", scale_factor=3.0)

# Save interactive HTML version
chart.save("plot.html")
