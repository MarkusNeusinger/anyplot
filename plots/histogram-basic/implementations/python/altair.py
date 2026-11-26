""" anyplot.ai
histogram-basic: Basic Histogram
Library: altair 6.3.0 | Python 3.14.10
Quality: 84/100 | Updated: 2026-11-26
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

# Imprint palette: a single series uses position 1
BRAND = "#009E73"

# Constants
MAX_BINS = 30  # upper bound on the number of equal-width bins

# Columns: set these to your table's column names
HEIGHT = "Height (cm)"  # role: values

# Data: replace this block with your own table, for example df = pd.read_csv("heights.csv")
np.random.seed(42)
primary = np.random.normal(loc=170, scale=7, size=350)
taller = np.random.normal(loc=186, scale=4.5, size=150)
df = pd.DataFrame({HEIGHT: np.concatenate([primary, taller])})

# Plot: reads only df and the constants above
ESCAPE = str.maketrans({".": "\\.", "[": "\\[", "]": "\\]", ":": "\\:"})
field = HEIGHT.translate(ESCAPE)

chart = (
    alt.Chart(df)
    .mark_bar(color=BRAND, stroke=PAGE_BG, strokeWidth=1)
    .encode(
        x=alt.X(field, type="quantitative", bin=alt.Bin(maxbins=MAX_BINS), title=HEIGHT),
        y=alt.Y("count()", type="quantitative", title="Frequency"),
        tooltip=[
            alt.Tooltip(field, type="quantitative", bin=alt.Bin(maxbins=MAX_BINS), title=HEIGHT),
            alt.Tooltip("count()", type="quantitative", title="Frequency"),
        ],
    )
    .properties(
        width=800,
        height=450,
        autosize=alt.AutoSizeParams(type="fit", contains="padding"),
        padding=10,
        background=PAGE_BG,
        title=alt.Title("histogram-basic · python · altair · anyplot.ai", fontSize=16, anchor="start", color=INK),
    )
    .configure_view(fill=PAGE_BG, strokeWidth=0)
    .configure_axis(
        labelFontSize=11,
        titleFontSize=13,
        titleColor=INK,
        labelColor=INK_SOFT,
        domainColor=INK_SOFT,
        tickColor=INK_SOFT,
        grid=False,
    )
    .configure_axisY(grid=True, gridColor=INK, gridOpacity=0.12, gridDash=[4, 4])
)

# Output
chart.save(f"plot-{THEME}.png", scale_factor=4.0)
chart.save(f"plot-{THEME}.html")
