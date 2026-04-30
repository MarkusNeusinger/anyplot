"""anyplot.ai
rug-basic: Basic Rug Plot
Library: altair | Python 3.13
Quality: pending | Created: 2026-04-30
"""

import os

import altair as alt
import numpy as np
import pandas as pd


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
BRAND = "#009E73"  # Okabe-Ito position 1

# Data - bimodal distribution showing clustering patterns and gaps
np.random.seed(42)
values = np.concatenate(
    [
        np.random.normal(25, 5, 60),  # Dense cluster around 25 ms
        np.random.normal(55, 8, 40),  # Sparser cluster around 55 ms
    ]
)

df = pd.DataFrame({"values": values, "y": [0] * len(values), "y2": [3] * len(values)})

# Plot
rug = (
    alt.Chart(df)
    .mark_rule(strokeWidth=3, opacity=0.6, color=BRAND)
    .encode(
        x=alt.X("values:Q", title="Response Time (ms)", scale=alt.Scale(domain=[5, 80])),
        y=alt.Y("y:Q", scale=alt.Scale(domain=[0, 10]), axis=None),
        y2="y2:Q",
    )
)

chart = (
    rug.properties(
        width=1600, height=900, title=alt.Title("rug-basic · altair · anyplot.ai", fontSize=28), background=PAGE_BG
    )
    .configure_view(fill=PAGE_BG, stroke=INK_SOFT)
    .configure_axis(
        domainColor=INK_SOFT,
        tickColor=INK_SOFT,
        gridColor=INK,
        gridOpacity=0.10,
        labelColor=INK_SOFT,
        titleColor=INK,
        labelFontSize=18,
        titleFontSize=22,
    )
    .configure_title(color=INK)
)

# Save
chart.save(f"plot-{THEME}.png", scale_factor=3.0)
chart.save(f"plot-{THEME}.html")
