""" pyplots.ai
indicator-ema: Exponential Moving Average (EMA) Indicator Chart
Library: altair 6.0.0 | Python 3.13.11
Quality: 92/100 | Created: 2026-01-11
"""

import altair as alt
import numpy as np
import pandas as pd


# Data - Generate synthetic stock price data with EMAs
np.random.seed(42)
n_days = 120

# Generate realistic stock price movement
dates = pd.date_range(start="2024-01-01", periods=n_days, freq="B")  # Business days
returns = np.random.normal(0.0005, 0.02, n_days)  # Daily returns
price = 100 * np.cumprod(1 + returns)  # Starting price $100

# Calculate EMAs
df = pd.DataFrame({"date": dates, "close": price})
df["ema_12"] = df["close"].ewm(span=12, adjust=False).mean()
df["ema_26"] = df["close"].ewm(span=26, adjust=False).mean()

# Melt for layered chart
df_price = df[["date", "close"]].copy()
df_price["series"] = "Close Price"
df_price = df_price.rename(columns={"close": "value"})

df_ema12 = df[["date", "ema_12"]].copy()
df_ema12["series"] = "EMA 12"
df_ema12 = df_ema12.rename(columns={"ema_12": "value"})

df_ema26 = df[["date", "ema_26"]].copy()
df_ema26["series"] = "EMA 26"
df_ema26 = df_ema26.rename(columns={"ema_26": "value"})

df_long = pd.concat([df_price, df_ema12, df_ema26], ignore_index=True)

# Define colors
color_scale = alt.Scale(domain=["Close Price", "EMA 12", "EMA 26"], range=["#306998", "#FFD43B", "#E74C3C"])

# Define stroke width for each series (price thicker, EMAs thinner)
stroke_scale = alt.Scale(domain=["Close Price", "EMA 12", "EMA 26"], range=[3.5, 2.5, 2.5])

# Create chart
chart = (
    alt.Chart(df_long)
    .mark_line()
    .encode(
        x=alt.X("date:T", title="Date", axis=alt.Axis(format="%b %Y", labelAngle=-45)),
        y=alt.Y("value:Q", title="Price (USD)", scale=alt.Scale(zero=False)),
        color=alt.Color(
            "series:N", scale=color_scale, legend=alt.Legend(title="Series", orient="top-left", direction="vertical")
        ),
        strokeWidth=alt.StrokeWidth("series:N", scale=stroke_scale, legend=None),
        tooltip=[
            alt.Tooltip("date:T", title="Date", format="%Y-%m-%d"),
            alt.Tooltip("series:N", title="Series"),
            alt.Tooltip("value:Q", title="Price", format="$.2f"),
        ],
    )
    .properties(width=1600, height=900, title="indicator-ema · altair · pyplots.ai")
    .configure_title(fontSize=28, anchor="middle")
    .configure_axis(labelFontSize=18, titleFontSize=22, tickSize=10)
    .configure_legend(titleFontSize=20, labelFontSize=18, symbolStrokeWidth=4, symbolSize=200)
    .configure_view(strokeWidth=0)
)

# Save
chart.save("plot.png", scale_factor=3.0)
chart.save("plot.html")
