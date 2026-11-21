"""anyplot.ai
candlestick-volume: Stock Candlestick Chart with Volume
Library: altair 6.1.0 | Python 3.13.13
Quality: 86/100 | Updated: 2026-11-21
"""

import os

import altair as alt
import numpy as np
import pandas as pd
from PIL import Image


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: all eight positions in canonical order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]
BULLISH = IMPRINT_PALETTE[0]  # close >= open
BEARISH = IMPRINT_PALETTE[4]  # close < open

# Columns: set these to your table's column names
DATE = "Date"  # role: date
OPEN = "Open ($)"  # role: open
HIGH = "High ($)"  # role: high
LOW = "Low ($)"  # role: low
CLOSE = "Close ($)"  # role: close
VOLUME = "Volume (shares)"  # role: volume
DIRECTION = "Direction"  # role: extra

# Data: replace this block with your own table, for example df = pd.read_csv("prices.csv")
np.random.seed(42)
n_days = 60
dates = pd.date_range("2024-01-02", periods=n_days, freq="B")
price = 150.0
opens, highs, lows, closes, volumes = [], [], [], [], []
for _ in range(n_days):
    daily_return = np.random.normal(0.001, 0.02)
    volatility = np.random.uniform(0.01, 0.03)
    open_price = price
    close_price = price * (1 + daily_return)
    intraday_high = max(open_price, close_price) * (1 + np.random.uniform(0, volatility))
    intraday_low = min(open_price, close_price) * (1 - np.random.uniform(0, volatility))
    opens.append(round(open_price, 2))
    highs.append(round(intraday_high, 2))
    lows.append(round(intraday_low, 2))
    closes.append(round(close_price, 2))
    vol_multiplier = 1 + abs(daily_return) * 20
    volumes.append(int(5000000 * vol_multiplier * np.random.uniform(0.7, 1.3)))
    price = close_price
df = pd.DataFrame({DATE: dates, OPEN: opens, HIGH: highs, LOW: lows, CLOSE: closes, VOLUME: volumes})

# Plot: reads only df and the constants above
ESCAPE = str.maketrans({".": "\\.", "[": "\\[", "]": "\\]", ":": "\\:"})
date_f, open_f, high_f, low_f, close_f, vol_f, dir_f = (
    c.translate(ESCAPE) for c in (DATE, OPEN, HIGH, LOW, CLOSE, VOLUME, DIRECTION)
)

df[DIRECTION] = np.where(df[CLOSE] >= df[OPEN], "Up", "Down")
color = alt.Color(
    dir_f,
    type="nominal",
    title=DIRECTION,
    scale=alt.Scale(domain=["Up", "Down"], range=[BULLISH, BEARISH]),
    legend=None,
)

x_axis = alt.Axis(format="%b %d", labelAngle=0, tickCount=8, labelFlush=False)
tooltip = [
    alt.Tooltip(date_f, type="temporal", title=DATE, format="%Y-%m-%d"),
    alt.Tooltip(open_f, type="quantitative", title=OPEN, format="$.2f"),
    alt.Tooltip(high_f, type="quantitative", title=HIGH, format="$.2f"),
    alt.Tooltip(low_f, type="quantitative", title=LOW, format="$.2f"),
    alt.Tooltip(close_f, type="quantitative", title=CLOSE, format="$.2f"),
    alt.Tooltip(vol_f, type="quantitative", title=VOLUME, format=","),
]

# Hover crosshair: one vertical guide at the date nearest the cursor, drawn through both panes
nearest = alt.selection_point(
    name="hover", fields=[DATE], nearest=True, on="pointerover", clear="pointerout", encodings=["x"]
)
x_enc = alt.X(date_f, type="temporal", title=None, axis=x_axis)

wicks = (
    alt.Chart(df)
    .mark_rule(strokeWidth=1.2)
    .encode(
        x=x_enc,
        y=alt.Y(low_f, type="quantitative", title="Price ($)", scale=alt.Scale(zero=False)),
        y2=alt.Y2(high_f),
        color=color,
    )
)
bodies = (
    alt.Chart(df)
    .mark_bar(size=6)
    .encode(
        x=x_enc,
        y=alt.Y(open_f, type="quantitative", scale=alt.Scale(zero=False)),
        y2=alt.Y2(close_f),
        color=color,
        tooltip=tooltip,
    )
)
price_pane = (wicks + bodies).properties(width=620, height=210)

volume_pane = (
    alt.Chart(df)
    .mark_bar(size=6)
    .encode(
        x=alt.X(date_f, type="temporal", title=DATE, axis=x_axis),
        y=alt.Y(vol_f, type="quantitative", title=VOLUME, axis=alt.Axis(format="~s", tickCount=3)),
        color=color,
        tooltip=tooltip,
    )
    .properties(width=620, height=70)
)

guide = (
    alt.Chart(df)
    .mark_rule(color=INK_SOFT, strokeDash=[4, 3], strokeWidth=1)
    .encode(x=alt.X(date_f, type="temporal"), opacity=alt.condition(nearest, alt.value(0.9), alt.value(0), empty=False))
    .add_params(nearest)
)

chart = (
    alt.vconcat(price_pane + guide, volume_pane + guide, spacing=8)
    .properties(
        title=alt.Title("candlestick-volume · python · altair · anyplot.ai", fontSize=16, anchor="middle", color=INK),
        background=PAGE_BG,
        padding={"left": 10, "right": 10, "top": 10, "bottom": 10},
    )
    .configure_view(fill=PAGE_BG, strokeWidth=0)
    .configure_axis(
        labelFontSize=10,
        titleFontSize=12,
        labelColor=INK_SOFT,
        titleColor=INK,
        domainColor=INK_SOFT,
        tickColor=INK_SOFT,
        gridColor=INK,
        gridOpacity=0.12,
    )
    .configure_title(color=INK, fontSize=16)
)

# Save: PNG padded (never cropped) to the 3200 x 1800 landscape target, plus interactive HTML
chart.save(f"plot-{THEME}.png", scale_factor=4.0)
TW, TH = 3200, 1800
img = Image.open(f"plot-{THEME}.png").convert("RGB")
w, h = img.size
if w > TW or h > TH:
    raise SystemExit(f"altair vl-convert produced {w}x{h}, exceeds target {TW}x{TH}")
if w < TW or h < TH:
    canvas = Image.new("RGB", (TW, TH), PAGE_BG)
    canvas.paste(img, ((TW - w) // 2, (TH - h) // 2))
    canvas.save(f"plot-{THEME}.png")
chart.save(f"plot-{THEME}.html")
