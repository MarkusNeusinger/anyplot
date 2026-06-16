""" anyplot.ai
renko-basic: Basic Renko Chart
Library: altair 6.1.0 | Python 3.13.13
Quality: 91/100 | Updated: 2026-05-17
"""

import os
import sys


# Workaround for import conflict: altair.py shadows the altair library
# Remove the script directory from sys.path before importing
_script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path = [p for p in sys.path if os.path.abspath(p) != _script_dir]

import altair as alt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402


# Theme tokens (see prompts/default-style-guide.md "Background" + "Theme-adaptive Chrome")
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Okabe-Ito colors (positions 1 and 2 for bullish/bearish)
BULLISH = "#009E73"  # Okabe-Ito position 1
BEARISH = "#AE3030"  # imprint red — bearish

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
    .mark_rect(strokeWidth=1, stroke=INK_SOFT)
    .encode(
        x=alt.X("x1:Q", title="Brick Index", scale=alt.Scale(nice=False)),
        x2="x2:Q",
        y=alt.Y("y1:Q", title="Price ($)", scale=alt.Scale(zero=False)),
        y2="y2:Q",
        color=alt.Color(
            "direction:N",
            scale=alt.Scale(domain=["Bullish", "Bearish"], range=[BULLISH, BEARISH]),
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
        width=1600,
        height=900,
        title=alt.Title("renko-basic · altair · anyplot.ai", fontSize=28, anchor="middle"),
        background=PAGE_BG,
    )
    .interactive()
    .configure_view(fill=PAGE_BG, stroke=INK_SOFT, strokeWidth=0)
    .configure_axis(
        labelFontSize=18,
        titleFontSize=22,
        labelColor=INK_SOFT,
        titleColor=INK,
        gridColor=INK,
        gridOpacity=0.10,
        domainColor=INK_SOFT,
        tickColor=INK_SOFT,
    )
    .configure_title(color=INK)
    .configure_legend(fillColor=ELEVATED_BG, strokeColor=INK_SOFT, labelColor=INK_SOFT, titleColor=INK)
)

# Save outputs
chart.save(f"plot-{THEME}.png", scale_factor=3.0)
chart.save(f"plot-{THEME}.html")
