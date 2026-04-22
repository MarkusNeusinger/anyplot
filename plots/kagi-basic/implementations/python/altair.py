""" pyplots.ai
kagi-basic: Basic Kagi Chart
Library: altair 6.0.0 | Python 3.13.11
Quality: 91/100 | Created: 2026-01-08
"""

import altair as alt
import numpy as np
import pandas as pd


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
df_segments["color"] = df_segments["yang"].map({True: "#2E7D32", False: "#C62828"})
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
            scale=alt.Scale(domain=["Yang (Bullish)", "Yin (Bearish)"], range=["#2E7D32", "#C62828"]),
            legend=alt.Legend(title="Trend"),
        ),
        strokeWidth=alt.StrokeWidth("yang:N", scale=alt.Scale(domain=[True, False], range=[6, 2]), legend=None),
    )
    .properties(width=1600, height=900, title="kagi-basic \u00b7 altair \u00b7 pyplots.ai")
    .configure_title(fontSize=28, anchor="middle")
    .configure_axis(labelFontSize=18, titleFontSize=22)
    .configure_legend(titleFontSize=18, labelFontSize=16)
)

# Save as PNG (4800x2700 with scale_factor=3)
chart.save("plot.png", scale_factor=3.0)

# Save as HTML for interactivity
chart.save("plot.html")
