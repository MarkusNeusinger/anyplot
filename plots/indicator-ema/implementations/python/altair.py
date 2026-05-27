""" anyplot.ai
indicator-ema: Exponential Moving Average (EMA) Indicator Chart
Library: altair 6.1.0 | Python 3.13.13
Quality: 91/100 | Updated: 2026-05-19
"""

import os

import altair as alt
import numpy as np
import pandas as pd


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

IMPRINT = ["#009E73", "#C475FD", "#4467A3"]

# Data
np.random.seed(42)
n_days = 120
dates = pd.date_range(start="2024-01-01", periods=n_days, freq="B")
returns = np.random.normal(0.0005, 0.02, n_days)
price = 100 * np.cumprod(1 + returns)

df = pd.DataFrame({"date": dates, "close": price})
df["ema_12"] = df["close"].ewm(span=12, adjust=False).mean()
df["ema_26"] = df["close"].ewm(span=26, adjust=False).mean()

# Detect EMA crossover points (sign change in ema_12 - ema_26)
diff = df["ema_12"] - df["ema_26"]
crossover_mask = (diff.shift(1) * diff < 0) & diff.shift(1).notna()
crossover_df = df[crossover_mask][["date", "ema_12"]].rename(columns={"ema_12": "value"})

# Melt into long format for multi-series chart
df_price = df[["date", "close"]].rename(columns={"close": "value"})
df_price["series"] = "Close Price"
df_ema12 = df[["date", "ema_12"]].rename(columns={"ema_12": "value"})
df_ema12["series"] = "EMA 12"
df_ema26 = df[["date", "ema_26"]].rename(columns={"ema_26": "value"})
df_ema26["series"] = "EMA 26"
df_long = pd.concat([df_price, df_ema12, df_ema26], ignore_index=True)

# Scales
color_scale = alt.Scale(domain=["Close Price", "EMA 12", "EMA 26"], range=IMPRINT)
stroke_scale = alt.Scale(domain=["Close Price", "EMA 12", "EMA 26"], range=[3.5, 2.5, 2.5])

# Line chart layer
lines = (
    alt.Chart(df_long)
    .mark_line()
    .encode(
        x=alt.X("date:T", title="Date", axis=alt.Axis(format="%b %Y", labelAngle=-45)),
        y=alt.Y("value:Q", title="Price (USD)", scale=alt.Scale(zero=False)),
        color=alt.Color("series:N", scale=color_scale, legend=alt.Legend(title="Series", orient="top-right")),
        strokeWidth=alt.StrokeWidth("series:N", scale=stroke_scale, legend=None),
        tooltip=[
            alt.Tooltip("date:T", title="Date", format="%Y-%m-%d"),
            alt.Tooltip("series:N", title="Series"),
            alt.Tooltip("value:Q", title="Price", format="$.2f"),
        ],
    )
)

# Crossover markers (diamond points where EMA 12 crosses EMA 26)
crossover_markers = (
    alt.Chart(crossover_df)
    .mark_point(size=300, shape="diamond", filled=True, color="#BD8233", opacity=0.85)
    .encode(
        x=alt.X("date:T"), y=alt.Y("value:Q"), tooltip=[alt.Tooltip("date:T", title="EMA Crossover", format="%Y-%m-%d")]
    )
)

# Compose and style
chart = (
    alt.layer(lines, crossover_markers)
    .properties(width=1600, height=900, title="indicator-ema · python · altair · anyplot.ai", background=PAGE_BG)
    .configure_view(fill=PAGE_BG, stroke=INK_SOFT)
    .configure_axis(
        domainColor=INK_SOFT,
        tickColor=INK_SOFT,
        gridColor=INK,
        gridOpacity=0.10,
        labelColor=INK_SOFT,
        titleColor=INK,
        labelFontSize=18,
        titleFontSize=22,
        tickSize=10,
    )
    .configure_title(fontSize=28, color=INK, anchor="middle")
    .configure_legend(
        fillColor=ELEVATED_BG,
        strokeColor=INK_SOFT,
        labelColor=INK_SOFT,
        titleColor=INK,
        titleFontSize=20,
        labelFontSize=18,
        symbolStrokeWidth=4,
        symbolSize=200,
    )
)

# Save
chart.save(f"plot-{THEME}.png", scale_factor=3.0)
chart.save(f"plot-{THEME}.html")
