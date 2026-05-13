""" anyplot.ai
line-stepwise: Step Line Plot
Library: altair 6.1.0 | Python 3.13.13
Quality: 91/100 | Updated: 2026-05-13
"""

import os
import sys


# Workaround for import conflict: remove script directory from path
script_dir = os.path.dirname(os.path.abspath(__file__))
if script_dir in sys.path:
    sys.path.remove(script_dir)

import altair as alt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
BRAND = "#009E73"

# Data - Discrete price changes showing step behavior (both increases and decreases)
np.random.seed(42)
days = np.arange(0, 25)
# Price values that step discretely, with varied pattern
base_price = 100
price_changes = [0, 0, 5, 5, 0, -3, -3, -3, 8, 8, 8, 2, 2, -2, -2, -2, 6, 6, 3, 3, 3, 1, 1, 1, 0]
prices = base_price + np.cumsum(price_changes)

df = pd.DataFrame({"Day": days, "Price ($)": prices})

# Create step line chart using interpolate='step-after'
chart = (
    alt.Chart(df)
    .mark_line(interpolate="step-after", strokeWidth=4, color=BRAND)
    .encode(
        x=alt.X("Day:Q", title="Day", axis=alt.Axis(labelFontSize=18, titleFontSize=22)),
        y=alt.Y(
            "Price ($):Q",
            title="Price ($)",
            scale=alt.Scale(zero=False),
            axis=alt.Axis(labelFontSize=18, titleFontSize=22),
        ),
        tooltip=["Day", "Price ($)"],
    )
    .properties(
        width=1600,
        height=900,
        background=PAGE_BG,
        title=alt.Title("line-stepwise · altair · anyplot.ai", fontSize=28, anchor="middle"),
    )
    .configure_axis(
        domainColor=INK_SOFT,
        tickColor=INK_SOFT,
        gridColor=INK,
        gridOpacity=0.15,
        labelColor=INK_SOFT,
        titleColor=INK,
        grid=True,
        gridDash=[4, 4],
    )
    .configure_view(strokeWidth=0, fill=PAGE_BG)
    .configure_title(color=INK)
)

# Save as PNG (1600 × 900 * 3 = 4800 × 2700 px)
chart.save(f"plot-{THEME}.png", scale_factor=3.0)

# Save as HTML for interactivity
chart.save(f"plot-{THEME}.html")
