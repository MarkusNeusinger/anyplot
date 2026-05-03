"""anyplot.ai
sparkline-basic: Basic Sparkline
Library: altair 6.0.0 | Python 3.13.11
Quality: 78/100 | Updated: 2026-05-03
"""

import os

import altair as alt
import numpy as np
import pandas as pd


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Okabe-Ito palette
OKABE_ITO = ["#009E73", "#D55E00", "#0072B2", "#CC79A7",
             "#E69F00", "#56B4E9", "#F0E442"]

# Data - 75 consecutive business days: a product's launch-to-maturity user trend
# with viral spike, long-tail stabilization, and recovery — a classic adoption curve
np.random.seed(42)
n_points = 75
day = np.arange(n_points)

# S-shaped adoption curve: slow start → acceleration → saturation
adoption = 40 + 60 * (1 - np.exp(-day / 20)) ** 2
# Viral launch-week spike
spike = 18 * np.exp(-((day - 25) ** 2) / 8)
# Weekly engagement pattern
weekly = 3 * np.sin(2 * np.pi * day / 5)
noise = np.random.randn(n_points) * 1.5
users = adoption + spike + weekly + noise

df = pd.DataFrame({"day": day, "users": users})

# Min/max highlights
min_idx = df["users"].idxmin()
max_idx = df["users"].idxmax()
highlights = df.iloc[[min_idx, max_idx]].copy()
highlights["type"] = ["min", "max"]

# Semi-transparent area fill — Altair's layered chart pattern
fill = (
    alt.Chart(df)
    .mark_area(color=OKABE_ITO[0], opacity=0.15)
    .encode(
        x=alt.X("day:Q", axis=None),
        y=alt.Y("users:Q", axis=None, scale=alt.Scale(zero=False)),
    )
)

# Main line
line = (
    alt.Chart(df)
    .mark_line(color=OKABE_ITO[0], strokeWidth=3)
    .encode(
        x=alt.X("day:Q", axis=None),
        y=alt.Y("users:Q", axis=None, scale=alt.Scale(zero=False)),
    )
)

# Highlight min (orange) and max (violet)
points = (
    alt.Chart(highlights)
    .mark_circle(size=150)
    .encode(
        x=alt.X("day:Q", axis=None),
        y=alt.Y("users:Q", axis=None, scale=alt.Scale(zero=False)),
        color=alt.Color(
            "type:N",
            scale=alt.Scale(domain=["min", "max"],
                            range=[OKABE_ITO[1], OKABE_ITO[3]]),
            legend=None,
        ),
    )
)

# Combine layers
chart = (
    (fill + line + points)
    .properties(
        width=1600,
        height=320,  # ~5:1 aspect ratio
        background=PAGE_BG,
        title=alt.Title("sparkline-basic · altair · anyplot.ai",
                        fontSize=28, color=INK),
    )
    .configure_axis(domainColor=INK_SOFT, tickColor=INK_SOFT,
                    labelColor=INK_SOFT, titleColor=INK)
    .configure_view(strokeWidth=0)
)

# Save as PNG and HTML
chart.save(f"plot-{THEME}.png", scale_factor=3.0)
chart.save(f"plot-{THEME}.html")
