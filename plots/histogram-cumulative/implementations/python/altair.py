""" anyplot.ai
histogram-cumulative: Cumulative Histogram
Library: altair 6.1.0 | Python 3.13.13
Quality: 90/100 | Updated: 2026-05-11
"""

import os
import sys


# Handle module import name conflict (script is named altair.py)
sys.path = [p for p in sys.path if os.path.abspath(p) != os.path.dirname(os.path.abspath(__file__))]

import altair as alt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
RULE = "rgba(26,26,23,0.10)" if THEME == "light" else "rgba(240,239,232,0.10)"
BRAND = "#009E73"

# Data: Monthly electricity usage (kWh) for households
np.random.seed(42)
usage = np.concatenate([np.random.normal(250, 50, 300), np.random.normal(450, 80, 200)])

# Compute cumulative histogram
bin_edges = np.linspace(usage.min() - 10, usage.max() + 10, 31)
counts, edges = np.histogram(usage, bins=bin_edges)
cumulative_counts = np.cumsum(counts)
cumulative_proportion = cumulative_counts / cumulative_counts[-1]

# Create DataFrame for Altair
df = pd.DataFrame(
    {
        "Electricity Usage (kWh)": edges[:-1],
        "Cumulative Proportion": cumulative_proportion,
        "Cumulative Count": cumulative_counts,
    }
)

# Create cumulative histogram as step area chart
chart = (
    alt.Chart(df)
    .mark_area(interpolate="step-after", color=BRAND, opacity=0.8, line={"color": BRAND, "strokeWidth": 3})
    .encode(
        x=alt.X(
            "Electricity Usage (kWh):Q",
            title="Electricity Usage (kWh)",
            scale=alt.Scale(domain=[bin_edges[0], bin_edges[-1]]),
        ),
        y=alt.Y("Cumulative Proportion:Q", title="Cumulative Proportion", scale=alt.Scale(domain=[0, 1])),
        tooltip=[
            alt.Tooltip("Electricity Usage (kWh):Q", title="Usage (kWh)", format=".1f"),
            alt.Tooltip("Cumulative Proportion:Q", title="Cumulative %", format=".1%"),
            alt.Tooltip("Cumulative Count:Q", title="Count"),
        ],
    )
    .properties(
        width=1600,
        height=900,
        background=PAGE_BG,
        title=alt.Title("histogram-cumulative · altair · anyplot.ai", fontSize=28),
    )
    .configure_axis(
        domainColor=INK_SOFT,
        tickColor=INK_SOFT,
        gridColor=INK_SOFT,
        gridOpacity=0.10,
        labelColor=INK_SOFT,
        labelFontSize=18,
        titleColor=INK,
        titleFontSize=22,
    )
    .configure_view(fill=PAGE_BG, stroke=INK_SOFT)
    .configure_title(color=INK, fontSize=28)
    .configure_legend(fillColor=ELEVATED_BG, strokeColor=INK_SOFT, labelColor=INK_SOFT, titleColor=INK)
)

# Save PNG (1600 × 900 at scale 3 = 4800 × 2700)
chart.save(f"plot-{THEME}.png", scale_factor=3.0)

# Save interactive HTML
chart.save(f"plot-{THEME}.html")
