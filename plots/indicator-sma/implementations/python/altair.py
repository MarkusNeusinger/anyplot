"""anyplot.ai
indicator-sma: Simple Moving Average (SMA) Indicator Chart
Library: altair 6.1.0 | Python 3.13.13
Quality: 87/100 | Updated: 2026-05-19
"""

import os

import altair as alt
import numpy as np
import pandas as pd
from PIL import Image


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: all eight positions, one per series in order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Constants
WINDOW_SHORT, WINDOW_MEDIUM, WINDOW_LONG = (
    20,
    50,
    200,
)  # standard SMA periods for daily data; match the column names below

# Columns: set these to your table's column names
DATE = "Date"  # role: date
CLOSE = "Close price"  # role: close
SMA_SHORT = "SMA 20"  # role: sma_short
SMA_MEDIUM = "SMA 50"  # role: sma_medium
SMA_LONG = "SMA 200"  # role: sma_long

# Data: replace this block with your own table, for example df = pd.read_csv("prices.csv")
np.random.seed(42)
n_days = 400
returns = np.random.normal(0.0003, 0.015, n_days)
close = 100 * np.cumprod(1 + returns) + np.linspace(0, 20, n_days)
df = pd.DataFrame({DATE: pd.date_range("2025-01-01", periods=n_days, freq="D"), CLOSE: close})
df[SMA_SHORT] = df[CLOSE].rolling(WINDOW_SHORT).mean()
df[SMA_MEDIUM] = df[CLOSE].rolling(WINDOW_MEDIUM).mean()
df[SMA_LONG] = df[CLOSE].rolling(WINDOW_LONG).mean()

# Plot: reads only df and the constants above
ESCAPE = str.maketrans({".": "\\.", "[": "\\[", "]": "\\]", ":": "\\:"})
series = [column for column in df.columns if column != DATE]
long_df = df.melt(id_vars=DATE, value_vars=series, var_name="Series", value_name="Price ($)")
dash_range = [[1, 0]] + [[8, 4], [5, 3], [3, 2]][: len(series) - 1]
width_range = [2.6] + [1.5] * (len(series) - 2) + [1.9]

chart = (
    alt.Chart(long_df)
    .mark_line()
    .encode(
        x=alt.X(
            DATE.translate(ESCAPE),
            type="temporal",
            title=DATE,
            axis=alt.Axis(format="%b %Y", tickCount=7, labelAngle=0),
        ),
        y=alt.Y("Price ($)".translate(ESCAPE), type="quantitative", title="Price ($)", scale=alt.Scale(zero=False)),
        color=alt.Color(
            "Series",
            type="nominal",
            title=None,
            sort=None,
            scale=alt.Scale(domain=series, range=IMPRINT_PALETTE),
            legend=alt.Legend(orient="top-left", symbolStrokeWidth=3, symbolSize=300, padding=6),
        ),
        strokeDash=alt.StrokeDash(
            "Series", type="nominal", sort=None, scale=alt.Scale(domain=series, range=dash_range), legend=None
        ),
        strokeWidth=alt.StrokeWidth(
            "Series", type="nominal", sort=None, scale=alt.Scale(domain=series, range=width_range), legend=None
        ),
        tooltip=[
            alt.Tooltip(DATE.translate(ESCAPE), type="temporal", title=DATE, format="%Y-%m-%d"),
            alt.Tooltip("Series", type="nominal"),
            alt.Tooltip("Price ($)".translate(ESCAPE), type="quantitative", title="Price ($)", format="$.2f"),
        ],
    )
    .properties(
        width=620,
        height=320,
        title=alt.Title("indicator-sma · python · altair · anyplot.ai", fontSize=16, anchor="middle", color=INK),
        background=PAGE_BG,
    )
    .configure_view(fill=PAGE_BG, stroke=INK_SOFT)
    .configure_axis(
        labelFontSize=10,
        titleFontSize=12,
        gridOpacity=0.10,
        domainColor=INK_SOFT,
        tickColor=INK_SOFT,
        gridColor=INK,
        labelColor=INK_SOFT,
        titleColor=INK,
    )
    .configure_legend(
        labelFontSize=10, fillColor=ELEVATED_BG, strokeColor=INK_SOFT, labelColor=INK_SOFT, titleColor=INK
    )
)

# Output: pad (never crop) to the 3200 x 1800 canvas
chart.save(f"plot-{THEME}.png", scale_factor=4.0)
TARGET_W, TARGET_H = 3200, 1800
img = Image.open(f"plot-{THEME}.png").convert("RGB")
if img.width > TARGET_W or img.height > TARGET_H:
    raise SystemExit(f"altair produced {img.width}x{img.height}, exceeds {TARGET_W}x{TARGET_H}; shrink width/height")
canvas = Image.new("RGB", (TARGET_W, TARGET_H), PAGE_BG)
canvas.paste(img, ((TARGET_W - img.width) // 2, (TARGET_H - img.height) // 2))
canvas.save(f"plot-{THEME}.png")
chart.save(f"plot-{THEME}.html")
