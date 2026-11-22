""" anyplot.ai
indicator-macd: MACD Technical Indicator Chart
Library: altair 6.3.0 | Python 3.14.10
Quality: 85/100 | Updated: 2026-11-22
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

# Imprint palette: all eight positions in canonical order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Constants
POSITIVE = "Positive"  # histogram above zero
NEGATIVE = "Negative"  # histogram below zero
ESCAPE = str.maketrans({".": "\\.", "[": "\\[", "]": "\\]", ":": "\\:"})

# Columns: set these to your table's column names
DATE = "Date"  # role: date
MACD = "MACD (12, 26)"  # role: macd
SIGNAL = "Signal (9)"  # role: signal
HISTOGRAM = "Histogram (MACD - Signal)"  # role: histogram

# Data: replace this block with your own table, for example df = pd.read_csv("macd.csv", parse_dates=[DATE])
np.random.seed(42)
n_days = 150
warmup = 26  # skip the days before the slow average is filled
returns = np.random.normal(0.001, 0.015, n_days)
price = pd.Series(100 * np.cumprod(1 + returns))
macd_line = price.ewm(span=12, adjust=False).mean() - price.ewm(span=26, adjust=False).mean()
signal_line = macd_line.ewm(span=9, adjust=False).mean()
df = pd.DataFrame(
    {
        DATE: pd.date_range("2025-06-01", periods=n_days - warmup, freq="D"),
        MACD: macd_line.values[warmup:],
        SIGNAL: signal_line.values[warmup:],
        HISTOGRAM: (macd_line - signal_line).values[warmup:],
    }
)

# Plot
sign = np.where(df[HISTOGRAM] >= 0, POSITIVE, NEGATIVE)
bars_df = df.assign(Momentum=sign)
lines_df = df.melt(id_vars=[DATE], value_vars=[MACD, SIGNAL], var_name="Line", value_name="Value")
zero_df = pd.DataFrame({"zero": [0.0]})

x_axis = alt.Axis(format="%b %Y", tickCount=6)
bars = (
    alt.Chart(bars_df)
    .mark_bar(size=3.5)
    .encode(
        x=alt.X(DATE.translate(ESCAPE), type="temporal", title=DATE, axis=x_axis),
        y=alt.Y(HISTOGRAM.translate(ESCAPE), type="quantitative", title="MACD value (price units)"),
        color=alt.Color(
            "Momentum",
            type="nominal",
            title="Histogram",
            sort=None,
            scale=alt.Scale(domain=[POSITIVE, NEGATIVE], range=[IMPRINT_PALETTE[0], IMPRINT_PALETTE[4]]),
        ),
        tooltip=[
            alt.Tooltip(DATE.translate(ESCAPE), type="temporal", title=DATE),
            alt.Tooltip(HISTOGRAM.translate(ESCAPE), type="quantitative", title=HISTOGRAM, format=".3f"),
        ],
    )
)

lines = (
    alt.Chart(lines_df)
    .mark_line(strokeWidth=2.2)
    .encode(
        x=alt.X(DATE.translate(ESCAPE), type="temporal", title=DATE, axis=x_axis),
        y=alt.Y("Value", type="quantitative", title="MACD value (price units)"),
        color=alt.Color(
            "Line",
            type="nominal",
            title="Lines",
            sort=None,
            scale=alt.Scale(domain=[MACD, SIGNAL], range=[IMPRINT_PALETTE[2], IMPRINT_PALETTE[3]]),
        ),
        strokeDash=alt.StrokeDash(
            "Line",
            type="nominal",
            sort=None,
            scale=alt.Scale(domain=[MACD, SIGNAL], range=[[1, 0], [6, 3]]),
            legend=None,
        ),
        tooltip=[
            alt.Tooltip(DATE.translate(ESCAPE), type="temporal", title=DATE),
            alt.Tooltip("Line", type="nominal", title="Line"),
            alt.Tooltip("Value", type="quantitative", title="Value", format=".3f"),
        ],
    )
)

zero_line = (
    alt.Chart(zero_df)
    .mark_rule(color=INK_SOFT, strokeWidth=1.2, strokeDash=[4, 3])
    .encode(y=alt.Y("zero", type="quantitative"))
)

TITLE = "indicator-macd · python · altair · anyplot.ai"
chart = (
    alt.layer(bars, lines, zero_line)
    .resolve_scale(color="independent")
    .properties(
        width=570,
        height=360,
        background=PAGE_BG,
        padding={"left": 8, "right": 8, "top": 8, "bottom": 8},
        title=alt.Title(
            TITLE,
            fontSize=15,
            anchor="middle",
            color=INK,
            subtitle="MACD parameters: fast EMA 12, slow EMA 26, signal EMA 9",
            subtitleFontSize=11,
            subtitleColor=INK_SOFT,
        ),
    )
    .configure_axis(
        labelFontSize=11,
        titleFontSize=13,
        gridColor=INK,
        gridOpacity=0.10,
        domainColor=INK_SOFT,
        tickColor=INK_SOFT,
        labelColor=INK_SOFT,
        titleColor=INK,
    )
    .configure_view(fill=PAGE_BG, strokeWidth=0)
    .configure_legend(
        labelFontSize=11,
        titleFontSize=12,
        orient="right",
        fillColor=ELEVATED_BG,
        strokeColor=INK_SOFT,
        labelColor=INK_SOFT,
        titleColor=INK,
        padding=6,
    )
)

# Save
chart.save(f"plot-{THEME}.png", scale_factor=4.0)
chart.save(f"plot-{THEME}.html")

# Pad (never crop) to the 3200 x 1800 target
TARGET_W, TARGET_H = 3200, 1800
img = Image.open(f"plot-{THEME}.png").convert("RGB")
w, h = img.size
if w > TARGET_W or h > TARGET_H:
    raise SystemExit(f"altair produced {w}x{h}, exceeds target {TARGET_W}x{TARGET_H}; shrink width/height")
if (w, h) != (TARGET_W, TARGET_H):
    canvas = Image.new("RGB", (TARGET_W, TARGET_H), PAGE_BG)
    canvas.paste(img, ((TARGET_W - w) // 2, (TARGET_H - h) // 2))
    canvas.save(f"plot-{THEME}.png")
