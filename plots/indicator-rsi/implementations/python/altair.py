""" anyplot.ai
indicator-rsi: RSI Technical Indicator Chart
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

# Imprint palette
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]
OVERSOLD_COLOR = IMPRINT_PALETTE[2]
OVERBOUGHT_COLOR = IMPRINT_PALETTE[4]

# Constants
LOOKBACK = 14  # standard RSI period
OVERSOLD = 30
OVERBOUGHT = 70
CENTERLINE = 50

# Columns: set these to your table's column names
DATE = "Date"  # role: date
RSI = "RSI value"  # role: rsi

# Data: replace this block with your own table, for example df = pd.read_csv("rsi.csv")
rng = np.random.default_rng(42)
n_periods = 140
dates = pd.date_range(start="2024-01-01", periods=n_periods, freq="D")
change = rng.standard_normal(n_periods) * 4
change[0] = 0
gains = np.where(change > 0, change, 0.0)
losses = np.where(change < 0, -change, 0.0)

avg_gain = np.full(n_periods, np.nan)
avg_loss = np.full(n_periods, np.nan)
avg_gain[LOOKBACK] = gains[1 : LOOKBACK + 1].mean()
avg_loss[LOOKBACK] = losses[1 : LOOKBACK + 1].mean()
for i in range(LOOKBACK + 1, n_periods):
    avg_gain[i] = (avg_gain[i - 1] * (LOOKBACK - 1) + gains[i]) / LOOKBACK
    avg_loss[i] = (avg_loss[i - 1] * (LOOKBACK - 1) + losses[i]) / LOOKBACK

rsi = 100 - 100 / (1 + avg_gain / avg_loss)
df = pd.DataFrame({DATE: dates, RSI: rsi})

# Plot: reads only df and the constants above
ESCAPE = str.maketrans({".": "\\.", "[": "\\[", "]": "\\]", ":": "\\:"})
y_scale = alt.Scale(domain=[0, 100])

zones = alt.layer(
    *[
        alt.Chart(pd.DataFrame({"low": [low], "high": [high]}))
        .mark_rect(opacity=0.14, color=color)
        .encode(y=alt.Y("low:Q", scale=y_scale), y2="high:Q")
        for low, high, color in [(0, OVERSOLD, OVERSOLD_COLOR), (OVERBOUGHT, 100, OVERBOUGHT_COLOR)]
    ]
)

level_names = [f"Oversold ({OVERSOLD})", f"Centerline ({CENTERLINE})", f"Overbought ({OVERBOUGHT})"]
levels_df = pd.DataFrame({"level": [OVERSOLD, CENTERLINE, OVERBOUGHT], "label": level_names})
levels = (
    alt.Chart(levels_df)
    .mark_rule(strokeDash=[6, 3], strokeWidth=1.2)
    .encode(
        y=alt.Y("level:Q", scale=y_scale),
        color=alt.Color(
            "label:N",
            sort=None,
            title=f"{LOOKBACK}-period levels",
            scale=alt.Scale(domain=level_names, range=[OVERSOLD_COLOR, INK_SOFT, OVERBOUGHT_COLOR]),
            legend=alt.Legend(
                orient="right", titleFontSize=10, labelFontSize=10, symbolType="stroke", symbolStrokeWidth=2
            ),
        ),
    )
)

rsi_line = (
    alt.Chart(df)
    .mark_line(strokeWidth=1.8, clip=True, color=IMPRINT_PALETTE[0])
    .encode(
        x=alt.X(DATE.translate(ESCAPE), type="temporal", title=DATE, axis=alt.Axis(format="%b %Y", tickCount="month")),
        y=alt.Y(RSI.translate(ESCAPE), type="quantitative", title=RSI, scale=y_scale),
        tooltip=[
            alt.Tooltip(DATE.translate(ESCAPE), type="temporal", title=DATE, format="%Y-%m-%d"),
            alt.Tooltip(RSI.translate(ESCAPE), type="quantitative", title=RSI, format=".1f"),
        ],
    )
)

chart = (
    alt.layer(zones, levels, rsi_line)
    .properties(
        width=560,
        height=290,
        background=PAGE_BG,
        title=alt.Title(
            "indicator-rsi · python · altair · anyplot.ai",
            fontSize=16,
            anchor="middle",
            subtitle=f"{LOOKBACK}-period RSI with overbought and oversold zones",
            subtitleFontSize=11,
            subtitleColor=INK_SOFT,
        ),
    )
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
    .configure_title(color=INK)
    .configure_legend(fillColor=ELEVATED_BG, strokeColor=INK_SOFT, labelColor=INK_SOFT, titleColor=INK, padding=6)
    .configure_view(strokeWidth=0, fill=PAGE_BG)
)

chart.save(f"plot-{THEME}.png", scale_factor=4.0)
chart.save(f"plot-{THEME}.html")

# Pad (never crop) to the exact 3200 x 1800 target
TW, TH = 3200, 1800
img = Image.open(f"plot-{THEME}.png").convert("RGB")
w, h = img.size
if w > TW or h > TH:
    raise SystemExit(f"altair produced {w}x{h}, exceeds target {TW}x{TH}; shrink width/height")
if (w, h) != (TW, TH):
    canvas = Image.new("RGB", (TW, TH), PAGE_BG)
    canvas.paste(img, ((TW - w) // 2, (TH - h) // 2))
    canvas.save(f"plot-{THEME}.png")
