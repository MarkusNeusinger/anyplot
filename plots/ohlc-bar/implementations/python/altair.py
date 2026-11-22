"""anyplot.ai
ohlc-bar: OHLC Bar Chart
Library: altair 6.1.0 | Python 3.13.13
Quality: pending | Updated: 2026-05-17
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

# Imprint palette: all eight positions, one per group in order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Constants
UP, DOWN = "Up", "Down"  # direction of a period: close at or above the open, or below it
DIRECTION_COLORS = {UP: IMPRINT_PALETTE[0], DOWN: IMPRINT_PALETTE[4]}
TICK_SHARE = 0.42  # tick length as a share of the typical gap between bars

# Columns: set these to your table's column names
DATE = "Date"  # role: date
OPEN = "Open (USD)"  # role: open
HIGH = "High (USD)"  # role: high
LOW = "Low (USD)"  # role: low
CLOSE = "Close (USD)"  # role: close

# Data: replace this block with your own table, for example df = pd.read_csv("prices.csv", parse_dates=[DATE])
np.random.seed(42)
n_days = 50
dates = pd.date_range("2024-01-02", periods=n_days, freq="B")
returns = np.random.normal(0.001, 0.02, n_days)

prices = [150.0]
for r in returns[:-1]:
    prices.append(prices[-1] * (1 + r))

opens, highs, lows, closes = [], [], [], []
for base_price in prices:
    daily_volatility = abs(np.random.normal(0, 0.015))
    intraday_move = np.random.normal(0, 0.01)

    open_price = base_price * (1 + np.random.normal(0, 0.005))
    close_price = open_price * (1 + intraday_move)
    opens.append(open_price)
    closes.append(close_price)
    highs.append(max(open_price, close_price) * (1 + daily_volatility))
    lows.append(min(open_price, close_price) * (1 - daily_volatility))

df = pd.DataFrame({DATE: dates, OPEN: opens, HIGH: highs, LOW: lows, CLOSE: closes})

# Plot: reads only df and the constants above
ESCAPE = str.maketrans({".": "\\.", "[": "\\[", "]": "\\]", ":": "\\:"})
tick_length = TICK_SHARE * df[DATE].diff().median()
bars = pd.DataFrame(
    {
        "date": df[DATE],
        "open": df[OPEN],
        "high": df[HIGH],
        "low": df[LOW],
        "close": df[CLOSE],
        "open_start": df[DATE] - tick_length,
        "close_end": df[DATE] + tick_length,
        "direction": np.where(df[CLOSE] >= df[OPEN], UP, DOWN),
    }
)

color = alt.Color(
    "direction:N",
    title="Direction",
    scale=alt.Scale(domain=list(DIRECTION_COLORS), range=list(DIRECTION_COLORS.values())),
    legend=alt.Legend(titleFontSize=12, labelFontSize=10),
)
price_axis = alt.Axis(labelFontSize=10, titleFontSize=12)

# High-low range: one vertical line per period
hl_lines = (
    alt.Chart(bars)
    .mark_rule(strokeWidth=1.5)
    .encode(
        x=alt.X("date:T", title=DATE, axis=alt.Axis(labelFontSize=10, titleFontSize=12, format="%b %d")),
        y=alt.Y("low:Q", title="Price (USD)", scale=alt.Scale(zero=False), axis=price_axis),
        y2="high:Q",
        color=color,
    )
)

# Open tick to the left of the bar
open_ticks = (
    alt.Chart(bars)
    .mark_rule(strokeWidth=1.5)
    .encode(x="open_start:T", x2="date:T", y=alt.Y("open:Q", scale=alt.Scale(zero=False)), color=color.legend(None))
)

# Close tick to the right of the bar
close_ticks = (
    alt.Chart(bars)
    .mark_rule(strokeWidth=1.5)
    .encode(x="date:T", x2="close_end:T", y=alt.Y("close:Q", scale=alt.Scale(zero=False)), color=color.legend(None))
)

chart = (
    alt.layer(hl_lines, open_ticks, close_ticks)
    .properties(
        width=620,
        height=320,
        background=PAGE_BG,
        title=alt.Title("ohlc-bar · python · altair · anyplot.ai", fontSize=16, anchor="middle", color=INK),
    )
    .configure_axis(
        domainColor=INK_SOFT, tickColor=INK_SOFT, gridColor=INK, gridOpacity=0.15, labelColor=INK_SOFT, titleColor=INK
    )
    .configure_title(color=INK)
    .configure_view(strokeWidth=0, fill=PAGE_BG)
    .configure_legend(fillColor=ELEVATED_BG, strokeColor=INK_SOFT, labelColor=INK_SOFT, titleColor=INK)
    .interactive()
)

# Save as PNG and HTML with theme-suffixed filenames
chart.save(f"plot-{THEME}.png", scale_factor=4.0)
chart.save(f"plot-{THEME}.html")

# Pad (never crop) the PNG up to the canonical 3200 x 1800 canvas
TARGET_W, TARGET_H = 3200, 1800
img = Image.open(f"plot-{THEME}.png").convert("RGB")
w, h = img.size
if w > TARGET_W or h > TARGET_H:
    raise SystemExit(f"altair produced {w}x{h}, exceeds target {TARGET_W}x{TARGET_H}; shrink width/height")
if (w, h) != (TARGET_W, TARGET_H):
    canvas = Image.new("RGB", (TARGET_W, TARGET_H), PAGE_BG)
    canvas.paste(img, ((TARGET_W - w) // 2, (TARGET_H - h) // 2))
    canvas.save(f"plot-{THEME}.png")
