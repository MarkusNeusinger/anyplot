""" anyplot.ai
kagi-basic: Basic Kagi Chart
Library: altair 6.1.0 | Python 3.13.13
Quality: 92/100 | Updated: 2026-05-17
"""

import os
from pathlib import Path

import altair as alt
import numpy as np
import pandas as pd


# Get script directory for saving outputs
SCRIPT_DIR = Path(__file__).parent

# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Okabe-Ito palette
YANG_COLOR = "#009E73"  # Bluish green (brand)
YIN_COLOR = "#AE3030"  # imprint red — bearish

# Generate realistic stock price data (simulated random walk)
np.random.seed(42)
n_days = 250
dates = pd.date_range("2024-01-01", periods=n_days, freq="D")
returns = np.random.normal(0.0005, 0.02, n_days)
prices = 100 * np.cumprod(1 + returns)

# Kagi chart algorithm
# Reversal threshold: 4% as specified
reversal_pct = 0.04

# Build Kagi line segments
segments = []
current_direction = None  # 1 = up, -1 = down
current_high = prices[0]
current_low = prices[0]
current_x = 0
last_y = prices[0]

# Track yang/yin state (yang = thick/bullish, yin = thin/bearish)
yang = True  # Start as yang
last_shoulder = prices[0]  # Last yang high
last_waist = prices[0]  # Last yin low

for i in range(1, len(prices)):
    price = prices[i]

    if current_direction is None:
        # Initialize direction
        if price >= current_high * (1 + reversal_pct):
            current_direction = 1
            segments.append({"x": current_x, "y": last_y, "x2": current_x, "y2": price, "yang": yang})
            current_high = price
            last_y = price
        elif price <= current_low * (1 - reversal_pct):
            current_direction = -1
            segments.append({"x": current_x, "y": last_y, "x2": current_x, "y2": price, "yang": yang})
            current_low = price
            last_y = price
    elif current_direction == 1:  # Currently going up
        if price > current_high:
            # Extend upward - update last segment
            if segments:
                segments[-1]["y2"] = price
            current_high = price
            last_y = price
        elif price <= current_high * (1 - reversal_pct):
            # Reversal down
            # Check if we break below last waist (transition to yin)
            if price < last_waist:
                yang = False
                last_waist = price
            # Draw horizontal connector and vertical down
            current_x += 1
            segments.append({"x": current_x - 1, "y": last_y, "x2": current_x, "y2": last_y, "yang": yang})
            last_shoulder = last_y  # Record shoulder
            segments.append({"x": current_x, "y": last_y, "x2": current_x, "y2": price, "yang": yang})
            current_low = price
            current_direction = -1
            last_y = price
    else:  # current_direction == -1, going down
        if price < current_low:
            # Extend downward
            if segments:
                segments[-1]["y2"] = price
            current_low = price
            last_y = price
        elif price >= current_low * (1 + reversal_pct):
            # Reversal up
            # Check if we break above last shoulder (transition to yang)
            if price > last_shoulder:
                yang = True
                last_shoulder = price
            # Draw horizontal connector and vertical up
            current_x += 1
            segments.append({"x": current_x - 1, "y": last_y, "x2": current_x, "y2": last_y, "yang": yang})
            last_waist = last_y  # Record waist
            segments.append({"x": current_x, "y": last_y, "x2": current_x, "y2": price, "yang": yang})
            current_high = price
            current_direction = 1
            last_y = price

# Create DataFrame for segments
df_segments = pd.DataFrame(segments)
df_segments["color"] = df_segments["yang"].map({True: YANG_COLOR, False: YIN_COLOR})
df_segments["thickness"] = df_segments["yang"].map({True: 6, False: 2})
df_segments["type"] = df_segments["yang"].map({True: "Yang (Bullish)", False: "Yin (Bearish)"})

# Create Altair chart using mark_rule for line segments
chart = (
    alt.Chart(df_segments)
    .mark_rule()
    .encode(
        x=alt.X("x:Q", title="Line Index"),
        x2="x2:Q",
        y=alt.Y("y:Q", title="Price ($)", scale=alt.Scale(zero=False)),
        y2="y2:Q",
        color=alt.Color(
            "type:N",
            scale=alt.Scale(domain=["Yang (Bullish)", "Yin (Bearish)"], range=[YANG_COLOR, YIN_COLOR]),
            legend=alt.Legend(title="Trend"),
        ),
        strokeWidth=alt.StrokeWidth("yang:N", scale=alt.Scale(domain=[True, False], range=[6, 2]), legend=None),
    )
    .properties(width=1600, height=900, title="kagi-basic · altair · anyplot.ai", background=PAGE_BG)
    .configure_view(fill=PAGE_BG, stroke=INK_SOFT)
    .configure_title(fontSize=28, anchor="middle", color=INK)
    .configure_axis(
        domainColor=INK_SOFT,
        tickColor=INK_SOFT,
        gridColor=INK,
        gridOpacity=0.10,
        labelColor=INK_SOFT,
        labelFontSize=18,
        titleColor=INK,
        titleFontSize=22,
    )
    .configure_legend(
        fillColor=ELEVATED_BG,
        strokeColor=INK_SOFT,
        labelColor=INK_SOFT,
        labelFontSize=16,
        titleColor=INK,
        titleFontSize=18,
    )
)

# Save as PNG and HTML with theme-suffixed filenames
chart.save(str(SCRIPT_DIR / f"plot-{THEME}.png"), scale_factor=3.0)
chart.save(str(SCRIPT_DIR / f"plot-{THEME}.html"))
