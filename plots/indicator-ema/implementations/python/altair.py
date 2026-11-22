"""anyplot.ai
indicator-ema: Exponential Moving Average (EMA) Indicator Chart
Library: altair 6.1.0 | Python 3.13.13
Quality: 91/100 | Updated: 2026-05-19
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
SHORT_SPAN = 12  # periods of the fast EMA
LONG_SPAN = 26  # periods of the slow EMA

# Columns: set these to your table's column names
DATE = "Date"  # role: date
CLOSE = "Close Price"  # role: close
EMA_SHORT = "EMA 12"  # role: ema_short
EMA_LONG = "EMA 26"  # role: ema_long

# Data: replace this block with your own table, for example df = pd.read_csv("prices.csv", parse_dates=[DATE])
np.random.seed(42)
n_days = 120
price = 100 * np.cumprod(1 + np.random.normal(0.0005, 0.02, n_days))
df = pd.DataFrame({DATE: pd.date_range(start="2024-01-01", periods=n_days, freq="B"), CLOSE: price})
df[EMA_SHORT] = df[CLOSE].ewm(span=SHORT_SPAN, adjust=False).mean()
df[EMA_LONG] = df[CLOSE].ewm(span=LONG_SPAN, adjust=False).mean()

# Plot: reads only df and the constants above
ESCAPE = str.maketrans({".": "\\.", "[": "\\[", "]": "\\]", ":": "\\:"})
SERIES = "Series"
VALUE = "Price (USD)"
series_order = [CLOSE, EMA_SHORT, EMA_LONG]

# Crossover points: sign change of the short minus the long EMA
diff = df[EMA_SHORT] - df[EMA_LONG]
crossovers = df[(diff.shift(1) * diff < 0)][[DATE, EMA_SHORT]].rename(columns={EMA_SHORT: VALUE})

# Long format for the multi-series line layer
df_long = df.melt(id_vars=DATE, value_vars=series_order, var_name=SERIES, value_name=VALUE)

color_scale = alt.Scale(domain=series_order, range=IMPRINT_PALETTE)
stroke_scale = alt.Scale(domain=series_order, range=[1.6, 1.0, 1.0])

lines = (
    alt.Chart(df_long)
    .mark_line()
    .encode(
        x=alt.X(DATE.translate(ESCAPE), type="temporal", title=DATE, axis=alt.Axis(format="%b %Y", tickCount="month")),
        y=alt.Y(VALUE.translate(ESCAPE), type="quantitative", title=VALUE, scale=alt.Scale(zero=False)),
        color=alt.Color(SERIES, type="nominal", title=SERIES, scale=color_scale, legend=alt.Legend(orient="right")),
        strokeWidth=alt.StrokeWidth(SERIES, type="nominal", scale=stroke_scale, legend=None),
        tooltip=[
            alt.Tooltip(DATE.translate(ESCAPE), type="temporal", title=DATE, format="%Y-%m-%d"),
            alt.Tooltip(SERIES, type="nominal", title=SERIES),
            alt.Tooltip(VALUE.translate(ESCAPE), type="quantitative", title=VALUE, format="$.2f"),
        ],
    )
)

# Diamonds where the short EMA crosses the long one
crossover_markers = (
    alt.Chart(crossovers)
    .mark_point(size=60, shape="diamond", filled=True, color=IMPRINT_PALETTE[3], opacity=0.9)
    .encode(
        x=alt.X(DATE.translate(ESCAPE), type="temporal"),
        y=alt.Y(VALUE.translate(ESCAPE), type="quantitative"),
        tooltip=[alt.Tooltip(DATE.translate(ESCAPE), type="temporal", title="EMA crossover", format="%Y-%m-%d")],
    )
)

chart = (
    alt.layer(lines, crossover_markers)
    .properties(
        width=520,
        height=320,
        title=alt.Title("indicator-ema · python · altair · anyplot.ai", fontSize=16),
        background=PAGE_BG,
    )
    .configure_view(fill=PAGE_BG, stroke=None)
    .configure_axis(
        domainColor=INK_SOFT,
        tickColor=INK_SOFT,
        gridColor=INK,
        gridOpacity=0.10,
        labelColor=INK_SOFT,
        titleColor=INK,
        labelFontSize=10,
        titleFontSize=12,
    )
    .configure_title(color=INK, anchor="middle")
    .configure_legend(
        fillColor=ELEVATED_BG,
        strokeColor=INK_SOFT,
        labelColor=INK_SOFT,
        titleColor=INK,
        titleFontSize=11,
        labelFontSize=10,
        symbolStrokeWidth=2,
        symbolSize=120,
        padding=6,
    )
)

# Save
chart.save(f"plot-{THEME}.png", scale_factor=4.0)
chart.save(f"plot-{THEME}.html")

# Pad (never crop) to the 3200 x 1800 target
TW, TH = 3200, 1800
img = Image.open(f"plot-{THEME}.png").convert("RGB")
w, h = img.size
if w > TW or h > TH:
    raise SystemExit(f"altair vl-convert produced {w}x{h}, exceeds target {TW}x{TH}; shrink width/height")
if w < TW or h < TH:
    canvas = Image.new("RGB", (TW, TH), PAGE_BG)
    canvas.paste(img, ((TW - w) // 2, (TH - h) // 2))
    canvas.save(f"plot-{THEME}.png")
