""" anyplot.ai
candlestick-basic: Basic Candlestick Chart
Library: altair 6.3.0 | Python 3.14.10
Quality: 85/100 | Updated: 2026-11-27
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
# Finance semantic exception: green = close above open, red = close below open
DIRECTION_COLORS = {"Bullish": IMPRINT_PALETTE[0], "Bearish": IMPRINT_PALETTE[4]}

# Columns: set these to your table's column names
DATE = "Date"  # role: date
OPEN = "Open ($)"  # role: open
HIGH = "High ($)"  # role: high
LOW = "Low ($)"  # role: low
CLOSE = "Close ($)"  # role: close
DIRECTION = "Direction"  # role: extra

# Data: replace this block with your own table, for example df = pd.read_csv("prices.csv")
np.random.seed(42)
n_days = 30
dates = pd.date_range(start="2024-01-01", periods=n_days, freq="B")

prices = [100.0]
for _ in range(n_days - 1):
    prices.append(prices[-1] + np.random.randn() * 2)

rows = []
for i, date in enumerate(dates):
    base = prices[i]
    volatility = np.random.uniform(1, 3)
    open_price = base + np.random.uniform(-volatility, volatility)
    close_price = base + np.random.uniform(-volatility, volatility)
    high_price = max(open_price, close_price) + np.random.uniform(0.5, volatility)
    low_price = min(open_price, close_price) - np.random.uniform(0.5, volatility)
    rows.append(
        {
            DATE: date,
            OPEN: round(open_price, 2),
            HIGH: round(high_price, 2),
            LOW: round(low_price, 2),
            CLOSE: round(close_price, 2),
        }
    )
df = pd.DataFrame(rows)

# Plot: reads only df and the constants above
ESCAPE = str.maketrans({".": "\\.", "[": "\\[", "]": "\\]", ":": "\\:"})
df[DIRECTION] = np.where(df[CLOSE] >= df[OPEN], "Bullish", "Bearish")

date_enc = alt.X(
    DATE.translate(ESCAPE),
    type="temporal",
    title=DATE,
    axis=alt.Axis(format="%b %d", grid=False),
    scale=alt.Scale(padding=14),
)
price_scale = alt.Scale(zero=False)
color_scale = alt.Scale(domain=list(DIRECTION_COLORS), range=list(DIRECTION_COLORS.values()))

# Wicks: low-high rule through the middle of each body, thinner than the body
wicks = (
    alt.Chart(df)
    .mark_rule(strokeWidth=2)
    .encode(
        x=date_enc,
        y=alt.Y(LOW.translate(ESCAPE), type="quantitative", title="Price ($)", scale=price_scale),
        y2=alt.Y2(HIGH.translate(ESCAPE)),
        color=alt.Color(
            DIRECTION.translate(ESCAPE),
            type="nominal",
            title=DIRECTION,
            scale=color_scale,
            legend=alt.Legend(symbolType="square", symbolSize=120),
        ),
    )
)

# Bodies: open-close bar, outlined in ink so direction does not rest on color alone
bodies = (
    alt.Chart(df)
    .mark_bar(size=14, stroke=INK, strokeWidth=0.7)
    .encode(
        x=date_enc,
        y=alt.Y(OPEN.translate(ESCAPE), type="quantitative", title="Price ($)", scale=price_scale),
        y2=alt.Y2(CLOSE.translate(ESCAPE)),
        color=alt.Color(
            DIRECTION.translate(ESCAPE),
            type="nominal",
            title=DIRECTION,
            scale=color_scale,
            legend=alt.Legend(symbolType="square", symbolSize=120),
        ),
        tooltip=[
            alt.Tooltip(DATE.translate(ESCAPE), type="temporal", title=DATE, format="%b %d, %Y"),
            alt.Tooltip(OPEN.translate(ESCAPE), type="quantitative", title=OPEN, format="$.2f"),
            alt.Tooltip(HIGH.translate(ESCAPE), type="quantitative", title=HIGH, format="$.2f"),
            alt.Tooltip(LOW.translate(ESCAPE), type="quantitative", title=LOW, format="$.2f"),
            alt.Tooltip(CLOSE.translate(ESCAPE), type="quantitative", title=CLOSE, format="$.2f"),
        ],
    )
)

chart = (
    alt.layer(wicks, bodies)
    .properties(
        width=800,
        height=450,
        padding=10,
        autosize=alt.AutoSizeParams(type="fit", contains="padding"),
        background=PAGE_BG,
        title=alt.Title("candlestick-basic · python · altair · anyplot.ai", fontSize=16, anchor="middle", color=INK),
    )
    .configure_view(fill=PAGE_BG, strokeWidth=0)
    .configure_axis(
        domainColor=INK_SOFT,
        tickColor=INK_SOFT,
        gridColor=INK,
        gridOpacity=0.15,
        labelColor=INK_SOFT,
        titleColor=INK,
        labelFontSize=10,
        titleFontSize=12,
    )
    .configure_legend(
        fillColor=ELEVATED_BG,
        padding=8,
        strokeColor=INK_SOFT,
        labelColor=INK_SOFT,
        titleColor=INK,
        labelFontSize=10,
        titleFontSize=10,
    )
    .interactive()
)

# Save: PNG at 3200 x 1800, then pad (never crop) a size that is off
chart.save(f"plot-{THEME}.png", scale_factor=4.0)
TW, TH = 3200, 1800
_img = Image.open(f"plot-{THEME}.png").convert("RGB")
if _img.size != (TW, TH):
    _scale = min(1.0, TW / _img.width, TH / _img.height)
    _img = _img.resize((round(_img.width * _scale), round(_img.height * _scale)), Image.LANCZOS)
    _canvas = Image.new("RGB", (TW, TH), PAGE_BG)
    _canvas.paste(_img, ((TW - _img.width) // 2, (TH - _img.height) // 2))
    _canvas.save(f"plot-{THEME}.png")
chart.save(f"plot-{THEME}.html")
