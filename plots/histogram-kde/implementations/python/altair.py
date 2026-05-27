""" anyplot.ai
histogram-kde: Histogram with KDE Overlay
Library: altair 6.1.0 | Python 3.13.13
Quality: 93/100 | Updated: 2026-05-06
"""

import os

import altair as alt
import numpy as np
import pandas as pd
from scipy.stats import gaussian_kde


# Theme-adaptive tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Okabe-Ito palette
BRAND = "#009E73"  # Position 1 - first series
ACCENT = "#954477"  # Position 7 - for KDE line

# Data - bimodal distribution for interesting KDE demonstration
np.random.seed(42)
values = np.concatenate([np.random.normal(loc=45, scale=8, size=300), np.random.normal(loc=72, scale=10, size=200)])

# Calculate histogram bins for density
hist, bin_edges = np.histogram(values, bins=30, density=True)
hist_df = pd.DataFrame({"bin_start": bin_edges[:-1], "bin_end": bin_edges[1:], "density": hist, "base": 0.0})

# Calculate KDE
kde = gaussian_kde(values, bw_method="scott")
x_kde = np.linspace(values.min() - 5, values.max() + 5, 200)
y_kde = kde(x_kde)
kde_df = pd.DataFrame({"x": x_kde, "density": y_kde})

# Histogram bars using Okabe-Ito brand color
histogram = (
    alt.Chart(hist_df)
    .mark_bar(opacity=0.6, color=BRAND)
    .encode(
        x=alt.X("bin_start:Q", title="Test Score", scale=alt.Scale(zero=False)),
        x2="bin_end:Q",
        y=alt.Y("density:Q", title="Density"),
        y2="base:Q",
    )
)

# KDE line using Okabe-Ito position 7
kde_line = alt.Chart(kde_df).mark_line(color=ACCENT, strokeWidth=4).encode(x=alt.X("x:Q"), y=alt.Y("density:Q"))

# Combine and configure with theme-adaptive styling
chart = (
    (histogram + kde_line)
    .properties(
        width=1600, height=900, background=PAGE_BG, title=alt.Title("histogram-kde · altair · anyplot.ai", fontSize=28)
    )
    .configure_axis(
        domainColor=INK_SOFT,
        tickColor=INK_SOFT,
        gridColor=INK,
        gridOpacity=0.10,
        labelFontSize=18,
        labelColor=INK_SOFT,
        titleFontSize=22,
        titleColor=INK,
    )
    .configure_view(strokeWidth=0, fill=PAGE_BG)
    .configure_title(color=INK)
)

# Save PNG and HTML with theme suffix
chart.save(f"plot-{THEME}.png", scale_factor=3.0)
chart.save(f"plot-{THEME}.html")
