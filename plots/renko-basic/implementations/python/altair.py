""" pyplots.ai
renko-basic: Basic Renko Chart
Library: altair 6.0.0 | Python 3.13.11
Quality: 94/100 | Created: 2026-01-08
"""

import altair as alt
import numpy as np
import pandas as pd


# Data - Generate realistic stock price data
np.random.seed(42)
n_days = 250

# Simulate stock price with random walk and trend
returns = np.random.normal(0.001, 0.015, n_days)
price = 100 * np.cumprod(1 + returns)

# Calculate Renko bricks
brick_size = 2.0  # $2 brick size

bricks = []
last_brick_price = round(price[0] / brick_size) * brick_size

for p in price:
    while True:
        if p >= last_brick_price + brick_size:
            # Bullish brick
            brick_open = last_brick_price
            brick_close = last_brick_price + brick_size
            bricks.append({"brick_idx": len(bricks), "open": brick_open, "close": brick_close, "direction": "Bullish"})
            last_brick_price = brick_close
        elif p <= last_brick_price - brick_size:
            # Bearish brick
            brick_open = last_brick_price
            brick_close = last_brick_price - brick_size
            bricks.append({"brick_idx": len(bricks), "open": brick_open, "close": brick_close, "direction": "Bearish"})
            last_brick_price = brick_close
        else:
            break

df_bricks = pd.DataFrame(bricks)

# Calculate brick positions for visualization
df_bricks["y1"] = df_bricks[["open", "close"]].min(axis=1)
df_bricks["y2"] = df_bricks[["open", "close"]].max(axis=1)
df_bricks["x1"] = df_bricks["brick_idx"]
df_bricks["x2"] = df_bricks["brick_idx"] + 0.85  # Gap between bricks

# Create Renko chart
chart = (
    alt.Chart(df_bricks)
    .mark_rect(strokeWidth=1, stroke="white")
    .encode(
        x=alt.X("x1:Q", title="Brick Index", scale=alt.Scale(nice=False)),
        x2="x2:Q",
        y=alt.Y("y1:Q", title="Price ($)", scale=alt.Scale(zero=False)),
        y2="y2:Q",
        color=alt.Color(
            "direction:N",
            scale=alt.Scale(
                domain=["Bullish", "Bearish"],
                range=["#26A69A", "#EF5350"],  # Green for up, red for down
            ),
            legend=alt.Legend(title="Direction", titleFontSize=18, labelFontSize=16, orient="top-right"),
        ),
        tooltip=[
            alt.Tooltip("brick_idx:Q", title="Brick #"),
            alt.Tooltip("open:Q", title="Open", format="$.2f"),
            alt.Tooltip("close:Q", title="Close", format="$.2f"),
            alt.Tooltip("direction:N", title="Direction"),
        ],
    )
    .properties(
        width=1600, height=900, title=alt.Title("renko-basic · altair · pyplots.ai", fontSize=28, anchor="middle")
    )
    .configure_axis(labelFontSize=18, titleFontSize=22, gridColor="#E0E0E0", gridOpacity=0.5)
    .configure_view(strokeWidth=0)
)

# Save outputs
chart.save("plot.png", scale_factor=3.0)
chart.save("plot.html")
