"""anyplot.ai
kagi-basic: Basic Kagi Chart
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

# Imprint palette: yang takes position 1 (brand green), yin position 5 (red)
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Constants
REVERSAL_PCT = 0.04  # a Kagi line turns only after a 4 % move against its direction
YANG_LABEL = "Yang (bullish)"
YIN_LABEL = "Yin (bearish)"

# Columns: set these to your table's column names
DATE = "Date"  # role: date
CLOSE = "Close price (USD)"  # role: close

# Data: replace this block with your own table, for example df = pd.read_csv("prices.csv")
np.random.seed(42)
n_days = 250
df = pd.DataFrame(
    {
        DATE: pd.date_range("2024-01-01", periods=n_days, freq="D"),
        CLOSE: 100 * np.cumprod(1 + np.random.normal(0.0005, 0.02, n_days)),
    }
)

# Plot: reads only df and the constants above
prices = df[CLOSE].dropna().to_numpy()

# Kagi construction: vertical segments joined by horizontal shoulders and waists
segments = []
direction = 0  # 1 = up, -1 = down, 0 = not yet decided
high = low = last_y = shoulder = waist = prices[0]
column = 0
yang = True

for price in prices[1:]:
    if direction == 0:
        if price >= high * (1 + REVERSAL_PCT) or price <= low * (1 - REVERSAL_PCT):
            direction = 1 if price > last_y else -1
            segments.append({"x": column, "y": last_y, "x2": column, "y2": price, "yang": yang})
            high = low = last_y = price
    elif direction == 1:
        if price > high:
            segments[-1]["y2"] = high = last_y = price
        elif price <= high * (1 - REVERSAL_PCT):
            if price < waist:
                yang = False
                waist = price
            column += 1
            shoulder = last_y
            segments.append({"x": column - 1, "y": last_y, "x2": column, "y2": last_y, "yang": yang})
            segments.append({"x": column, "y": last_y, "x2": column, "y2": price, "yang": yang})
            low = last_y = price
            direction = -1
    else:
        if price < low:
            segments[-1]["y2"] = low = last_y = price
        elif price >= low * (1 + REVERSAL_PCT):
            if price > shoulder:
                yang = True
                shoulder = price
            column += 1
            waist = last_y
            segments.append({"x": column - 1, "y": last_y, "x2": column, "y2": last_y, "yang": yang})
            segments.append({"x": column, "y": last_y, "x2": column, "y2": price, "yang": yang})
            high = last_y = price
            direction = 1

lines = pd.DataFrame(segments)
lines["trend"] = np.where(lines["yang"], YANG_LABEL, YIN_LABEL)
trend_domain = [YANG_LABEL, YIN_LABEL]

TITLE = "kagi-basic · python · altair · anyplot.ai"
chart = (
    alt.Chart(lines)
    .mark_rule()
    .encode(
        x=alt.X("x:Q", title="Line index", axis=alt.Axis(tickMinStep=1, format="d")),
        x2="x2:Q",
        y=alt.Y("y:Q", title=CLOSE, scale=alt.Scale(zero=False)),
        y2="y2:Q",
        color=alt.Color(
            "trend:N",
            title="Trend",
            scale=alt.Scale(domain=trend_domain, range=[IMPRINT_PALETTE[0], IMPRINT_PALETTE[4]]),
        ),
        strokeWidth=alt.StrokeWidth("trend:N", scale=alt.Scale(domain=trend_domain, range=[4, 1.5]), legend=None),
    )
    .properties(width=620, height=320, title=alt.Title(TITLE, fontSize=16), background=PAGE_BG)
    .configure_view(fill=PAGE_BG, stroke=INK_SOFT)
    .configure_axis(
        domainColor=INK_SOFT,
        tickColor=INK_SOFT,
        gridColor=INK,
        gridOpacity=0.10,
        labelColor=INK_SOFT,
        labelFontSize=11,
        titleColor=INK,
        titleFontSize=13,
    )
    .configure_title(anchor="middle", color=INK)
    .configure_legend(
        fillColor=ELEVATED_BG,
        strokeColor=INK_SOFT,
        labelColor=INK_SOFT,
        labelFontSize=11,
        titleColor=INK,
        titleFontSize=12,
        symbolStrokeWidth=4,
    )
)

# Save PNG (padded to the canonical canvas) and HTML
chart.save(f"plot-{THEME}.png", scale_factor=4.0)
chart.save(f"plot-{THEME}.html")

TARGET_W, TARGET_H = 3200, 1800
img = Image.open(f"plot-{THEME}.png").convert("RGB")
if img.width > TARGET_W or img.height > TARGET_H:
    raise SystemExit(f"altair rendered {img.width}x{img.height}, larger than {TARGET_W}x{TARGET_H}; shrink the view")
canvas = Image.new("RGB", (TARGET_W, TARGET_H), PAGE_BG)
canvas.paste(img, ((TARGET_W - img.width) // 2, (TARGET_H - img.height) // 2))
canvas.save(f"plot-{THEME}.png")
