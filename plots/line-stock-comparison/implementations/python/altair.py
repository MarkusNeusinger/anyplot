"""anyplot.ai
line-stock-comparison: Stock Price Comparison Chart
Library: altair 6.3.0 | Python 3.14.10
Quality: pending | Updated: 2026-11-26
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

# Imprint palette
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Constants
BASE = 100  # every series starts at this index value
BENCHMARK = "SPY"  # drawn thicker than the single stocks

# Columns
DATE = "Date"  # role: date
SYMBOL = "Symbol"  # role: symbol
REBASED = "Performance index (start = 100)"  # role: price

# Data
np.random.seed(42)
dates = pd.date_range("2024-01-01", periods=252, freq="B")
returns_params = {"AAPL": (0.0003, 0.012), "GOOGL": (0.0002, 0.011), "MSFT": (0.0003, 0.008), "SPY": (0.0001, 0.006)}

frames = []
for symbol, (mean_return, volatility) in returns_params.items():
    returns = np.random.normal(mean_return, volatility, len(dates))
    prices = 50 * np.cumprod(1 + returns)
    frames.append(pd.DataFrame({DATE: dates, SYMBOL: symbol, REBASED: prices / prices[0] * BASE}))
df = pd.concat(frames, ignore_index=True)

# Plot
ESCAPE = str.maketrans({".": "\\.", "[": "\\[", "]": "\\]", ":": "\\:"})

lines = (
    alt.Chart(df)
    .mark_line()
    .encode(
        x=alt.X(DATE.translate(ESCAPE), type="temporal", title=DATE),
        y=alt.Y(REBASED.translate(ESCAPE), type="quantitative", title=REBASED, scale=alt.Scale(zero=False)),
        color=alt.Color(
            SYMBOL.translate(ESCAPE),
            type="nominal",
            title=SYMBOL,
            sort=None,
            scale=alt.Scale(range=IMPRINT_PALETTE),
            legend=alt.Legend(titleFontSize=12, labelFontSize=11, symbolSize=160, symbolStrokeWidth=3),
        ),
        strokeWidth=alt.condition(alt.datum[SYMBOL] == BENCHMARK, alt.value(3.5), alt.value(2.2)),
        tooltip=[
            alt.Tooltip(DATE.translate(ESCAPE), type="temporal", title=DATE),
            alt.Tooltip(SYMBOL.translate(ESCAPE), type="nominal", title=SYMBOL),
            alt.Tooltip(REBASED.translate(ESCAPE), type="quantitative", title=REBASED, format=".1f"),
        ],
    )
)

reference_line = (
    alt.Chart(pd.DataFrame({"y": [BASE]}))
    .mark_rule(color=INK_SOFT, strokeDash=[6, 4], strokeWidth=1.5, opacity=0.6)
    .encode(y="y:Q")
)

chart = (
    alt.layer(reference_line, lines)
    .properties(
        width=800,
        height=450,
        autosize=alt.AutoSizeParams(type="fit", contains="padding"),
        padding=10,
        background=PAGE_BG,
        title=alt.Title(
            "line-stock-comparison · python · altair · anyplot.ai", fontSize=16, color=INK, anchor="middle"
        ),
    )
    .configure_view(fill=PAGE_BG, stroke=None)
    .configure_axis(
        grid=True,
        labelFontSize=11,
        titleFontSize=13,
        domainColor=INK_SOFT,
        tickColor=INK_SOFT,
        gridColor=INK,
        gridOpacity=0.10,
        labelColor=INK_SOFT,
        titleColor=INK,
    )
    .configure_title(color=INK, fontSize=16)
    .configure_legend(fillColor=ELEVATED_BG, strokeColor=INK_SOFT, labelColor=INK_SOFT, titleColor=INK, padding=8)
)

# Save
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
