"""anyplot.ai
indicator-bollinger: Bollinger Bands Indicator Chart
Library: altair 6.1.0 | Python 3.13.13
Quality: 99/100 | Updated: 2026-05-17
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

# Imprint palette positions 1-3 (theme-independent)
PRICE_COLOR = "#009E73"
SMA_COLOR = "#C475FD"
BAND_COLOR = "#4467A3"

# Constants
WINDOW = 20  # averaging period of the standard Bollinger setup
NUM_STD = 2  # band width in standard deviations

DATE = "Date"  # role: date
CLOSE = "Close price ($)"  # role: close
SMA = "20-day SMA ($)"  # role: sma
UPPER_BAND = "Upper band ($)"  # role: upper_band
LOWER_BAND = "Lower band ($)"  # role: lower_band

# Data: replace this block with your own table, for example df = pd.read_csv("prices.csv")
np.random.seed(42)
n_days = 120
dates = pd.date_range("2024-01-01", periods=n_days, freq="B")
returns = np.random.randn(n_days) * 0.015
returns[:30] += 0.002
returns[50:70] -= 0.003
returns[90:] += 0.002
price = pd.Series(100 * np.cumprod(1 + returns))

sma = price.rolling(WINDOW).mean()
std = price.rolling(WINDOW).std()
df = pd.DataFrame(
    {DATE: dates, CLOSE: price, SMA: sma, UPPER_BAND: sma + NUM_STD * std, LOWER_BAND: sma - NUM_STD * std}
).dropna()

# Plot
ESCAPE = str.maketrans({".": "\\.", "[": "\\[", "]": "\\]", ":": "\\:"})
y_min = min(df[CLOSE].min(), df[LOWER_BAND].min()) * 0.98
y_max = max(df[CLOSE].max(), df[UPPER_BAND].max()) * 1.02
y_scale = alt.Scale(domain=[y_min, y_max])

x_enc = alt.X(
    DATE.translate(ESCAPE), type="temporal", title=DATE, axis=alt.Axis(format="%b %d", labelAngle=-45, tickCount=10)
)


def y_enc(column, **kwargs):
    return alt.Y(column.translate(ESCAPE), type="quantitative", title="Price ($)", scale=y_scale, **kwargs)


band_area = (
    alt.Chart(df)
    .mark_area(opacity=0.2, color=BAND_COLOR)
    .encode(x=x_enc, y=y_enc(LOWER_BAND), y2=alt.Y2(UPPER_BAND.translate(ESCAPE)))
)
upper_line = alt.Chart(df).mark_line(strokeWidth=1, color=BAND_COLOR, opacity=0.6).encode(x=x_enc, y=y_enc(UPPER_BAND))
lower_line = alt.Chart(df).mark_line(strokeWidth=1, color=BAND_COLOR, opacity=0.6).encode(x=x_enc, y=y_enc(LOWER_BAND))
sma_line = alt.Chart(df).mark_line(strokeWidth=1.25, strokeDash=[6, 3], color=SMA_COLOR).encode(x=x_enc, y=y_enc(SMA))
price_line = alt.Chart(df).mark_line(strokeWidth=1.75, color=PRICE_COLOR).encode(x=x_enc, y=y_enc(CLOSE))

chart = (
    alt.layer(band_area, upper_line, lower_line, sma_line, price_line)
    .properties(
        width=620,
        height=320,
        background=PAGE_BG,
        title=alt.Title("indicator-bollinger · python · altair · anyplot.ai", fontSize=16, anchor="middle"),
    )
    .configure_view(fill=PAGE_BG, stroke=None)
    .configure_axis(
        domainColor=INK_SOFT,
        tickColor=INK_SOFT,
        gridColor=INK,
        gridOpacity=0.1,
        labelColor=INK_SOFT,
        titleColor=INK,
        labelFontSize=10,
        titleFontSize=12,
    )
    .configure_title(color=INK)
)

# Save
chart.save(f"plot-{THEME}.png", scale_factor=4.0)
chart.save(f"plot-{THEME}.html")

# Pad (never crop) to the canonical 3200 x 1800 canvas
TARGET_W, TARGET_H = 3200, 1800
img = Image.open(f"plot-{THEME}.png").convert("RGB")
if img.width > TARGET_W or img.height > TARGET_H:
    raise SystemExit(f"vl-convert produced {img.width}x{img.height}, exceeds {TARGET_W}x{TARGET_H}")
if img.size != (TARGET_W, TARGET_H):
    canvas = Image.new("RGB", (TARGET_W, TARGET_H), PAGE_BG)
    canvas.paste(img, ((TARGET_W - img.width) // 2, (TARGET_H - img.height) // 2))
    canvas.save(f"plot-{THEME}.png")
