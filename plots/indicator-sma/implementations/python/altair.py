""" anyplot.ai
indicator-sma: Simple Moving Average (SMA) Indicator Chart
Library: altair 6.1.0 | Python 3.13.13
Quality: 87/100 | Updated: 2026-05-19
"""

import os

import altair as alt
import numpy as np
import pandas as pd


THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

OKABE_ITO = ["#009E73", "#D55E00", "#0072B2", "#CC79A7"]

np.random.seed(42)
n_days = 300
dates = pd.date_range("2025-01-01", periods=n_days, freq="D")

returns = np.random.normal(0.0003, 0.015, n_days)
price = 100 * np.cumprod(1 + returns)
trend = np.linspace(0, 20, n_days)
price = price + trend

df = pd.DataFrame({"date": dates, "close": price})
df["sma_20"] = df["close"].rolling(window=20).mean()
df["sma_50"] = df["close"].rolling(window=50).mean()
df["sma_200"] = df["close"].rolling(window=200).mean()

price_df = df[["date", "close"]].copy()
price_df["series"] = "Close Price"
price_df = price_df.rename(columns={"close": "value"})

sma20_df = df[["date", "sma_20"]].copy()
sma20_df["series"] = "SMA 20"
sma20_df = sma20_df.rename(columns={"sma_20": "value"})

sma50_df = df[["date", "sma_50"]].copy()
sma50_df["series"] = "SMA 50"
sma50_df = sma50_df.rename(columns={"sma_50": "value"})

sma200_df = df[["date", "sma_200"]].copy()
sma200_df["series"] = "SMA 200"
sma200_df = sma200_df.rename(columns={"sma_200": "value"})

combined_df = pd.concat([price_df, sma20_df, sma50_df, sma200_df], ignore_index=True)

SERIES = ["Close Price", "SMA 20", "SMA 50", "SMA 200"]

color_scale = alt.Scale(domain=SERIES, range=OKABE_ITO)
stroke_dash_scale = alt.Scale(domain=SERIES, range=[[0], [8, 4], [4, 4], [2, 2]])
stroke_width_scale = alt.Scale(domain=SERIES, range=[3.5, 1.5, 1.5, 1.5])

chart = (
    alt.Chart(combined_df)
    .mark_line()
    .encode(
        x=alt.X("date:T", title="Date", axis=alt.Axis(format="%b %Y", labelAngle=-45)),
        y=alt.Y("value:Q", title="Price ($)", scale=alt.Scale(zero=False)),
        color=alt.Color(
            "series:N",
            scale=color_scale,
            legend=alt.Legend(
                title="Series",
                orient="top-right",
                titleFontSize=18,
                labelFontSize=16,
                symbolSize=200,
                symbolStrokeWidth=3,
            ),
        ),
        strokeDash=alt.StrokeDash("series:N", scale=stroke_dash_scale, legend=None),
        strokeWidth=alt.StrokeWidth("series:N", scale=stroke_width_scale, legend=None),
        tooltip=[
            alt.Tooltip("date:T", title="Date", format="%Y-%m-%d"),
            alt.Tooltip("series:N", title="Series"),
            alt.Tooltip("value:Q", title="Price", format="$.2f"),
        ],
    )
    .properties(width=1600, height=900, title="indicator-sma · python · altair · anyplot.ai", background=PAGE_BG)
    .configure_title(fontSize=28, anchor="middle", color=INK)
    .configure_axis(
        labelFontSize=18,
        titleFontSize=22,
        gridOpacity=0.10,
        domainColor=INK_SOFT,
        tickColor=INK_SOFT,
        gridColor=INK,
        labelColor=INK_SOFT,
        titleColor=INK,
    )
    .configure_view(fill=PAGE_BG, stroke=INK_SOFT)
    .configure_legend(fillColor=ELEVATED_BG, strokeColor=INK_SOFT, labelColor=INK_SOFT, titleColor=INK)
)

chart.save(f"plot-{THEME}.png", scale_factor=3.0)
chart.save(f"plot-{THEME}.html")
