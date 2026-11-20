""" anyplot.ai
line-timeseries: Time Series Line Plot
Library: altair 6.3.0 | Python 3.14.10
Quality: 82/100 | Updated: 2026-11-20
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

# Imprint palette: first series is always brand green
BRAND = "#009E73"

# Columns: set these to your table's column names
DATE = "Date"  # role: date
PRICE = "Stock price ($)"  # role: value

# Data: replace this block with your own table, for example df = pd.read_csv("prices.csv")
np.random.seed(42)
dates = pd.date_range(start="2024-01-02", periods=252, freq="B")
price = 100.0
prices = [price]
for _ in range(251):
    change = np.random.randn() * 2 + 0.05
    price = max(price + change, 50)
    prices.append(price)
df = pd.DataFrame({DATE: dates, PRICE: prices})

# Plot: reads only df and the constants above
ESCAPE = str.maketrans({".": "\\.", "[": "\\[", "]": "\\]", ":": "\\:"})
axis_style = {
    "labelFontSize": 10,
    "titleFontSize": 12,
    "labelColor": INK_SOFT,
    "titleColor": INK,
    "domainColor": INK_SOFT,
    "tickColor": INK_SOFT,
    "gridColor": INK,
    "gridOpacity": 0.10,
}

chart = (
    alt.Chart(df)
    .mark_line(strokeWidth=1.8, color=BRAND, point=alt.OverlayMarkDef(size=14, color=BRAND, filled=True))
    .encode(
        x=alt.X(
            DATE.translate(ESCAPE),
            type="temporal",
            title=DATE,
            axis=alt.Axis(format="%b %Y", labelAngle=-45, tickCount="month", **axis_style),
        ),
        y=alt.Y(
            PRICE.translate(ESCAPE),
            type="quantitative",
            title=PRICE,
            scale=alt.Scale(zero=False),
            axis=alt.Axis(**axis_style),
        ),
        tooltip=[
            alt.Tooltip(DATE.translate(ESCAPE), type="temporal", title=DATE, format="%B %d, %Y"),
            alt.Tooltip(PRICE.translate(ESCAPE), type="quantitative", title=PRICE, format="$.2f"),
        ],
    )
    .properties(
        width=620,
        height=320,
        background=PAGE_BG,
        title=alt.Title("line-timeseries · python · altair · anyplot.ai", fontSize=16, anchor="middle", color=INK),
    )
    .configure_view(fill=PAGE_BG, stroke=INK_SOFT, strokeWidth=1)
    .interactive()
)

# Save outputs
chart.save(f"plot-{THEME}.png", scale_factor=4.0)
chart.save(f"plot-{THEME}.html")

# Pad (never crop) to the exact 3200 x 1800 canvas
TW, TH = 3200, 1800
img = Image.open(f"plot-{THEME}.png").convert("RGB")
w, h = img.size
if w > TW or h > TH:
    raise SystemExit(f"altair produced {w}x{h}, exceeds target {TW}x{TH}; shrink width/height")
if (w, h) != (TW, TH):
    canvas = Image.new("RGB", (TW, TH), PAGE_BG)
    canvas.paste(img, ((TW - w) // 2, (TH - h) // 2))
    canvas.save(f"plot-{THEME}.png")
