"""anyplot.ai
histogram-stepwise: Step Histogram
Library: altair | Python 3.13
Quality: pending | Created: 2025-05-12
"""

import os

import altair as alt
import numpy as np
import pandas as pd


THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
BRAND = "#009E73"

np.random.seed(42)
values = np.concatenate([np.random.normal(25, 5, 300), np.random.normal(45, 8, 200)])

counts, bin_edges = np.histogram(values, bins=25)

step_x = []
step_y = []
for i, count in enumerate(counts):
    step_x.extend([bin_edges[i], bin_edges[i + 1]])
    step_y.extend([count, count])

step_x = [bin_edges[0]] + step_x + [bin_edges[-1]]
step_y = [0] + step_y + [0]

df = pd.DataFrame({"Measurement Value": step_x, "Frequency": step_y, "order": range(len(step_x))})

chart = (
    alt.Chart(df)
    .mark_line(strokeWidth=3, color=BRAND, interpolate="step-after")
    .encode(
        x=alt.X("Measurement Value:Q", title="Measurement Value"),
        y=alt.Y("Frequency:Q", title="Frequency"),
        order="order:O",
    )
    .properties(
        width=1600,
        height=900,
        background=PAGE_BG,
        title=alt.Title("histogram-stepwise · altair · anyplot.ai", fontSize=28),
    )
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
    .configure_title(color=INK)
    .configure_view(strokeWidth=0, fill=PAGE_BG)
)

chart.save(f"plot-{THEME}.png", scale_factor=3.0)
chart.save(f"plot-{THEME}.html")
