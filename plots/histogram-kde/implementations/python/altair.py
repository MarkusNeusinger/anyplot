""" pyplots.ai
histogram-kde: Histogram with KDE Overlay
Library: altair 6.0.0 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-24
"""

import altair as alt
import numpy as np
import pandas as pd
from scipy.stats import gaussian_kde


# Data - bimodal distribution for interesting KDE demonstration
np.random.seed(42)
values = np.concatenate([np.random.normal(loc=45, scale=8, size=300), np.random.normal(loc=72, scale=10, size=200)])

# Calculate histogram bins for density
hist, bin_edges = np.histogram(values, bins=30, density=True)
hist_df = pd.DataFrame(
    {
        "bin_start": bin_edges[:-1],
        "bin_end": bin_edges[1:],
        "density": hist,
        "base": 0.0,  # Explicit baseline
    }
)

# Calculate KDE
kde = gaussian_kde(values, bw_method="scott")
x_kde = np.linspace(values.min() - 5, values.max() + 5, 200)
y_kde = kde(x_kde)
kde_df = pd.DataFrame({"x": x_kde, "density": y_kde})

# Histogram bars
histogram = (
    alt.Chart(hist_df)
    .mark_bar(opacity=0.5, color="#306998")
    .encode(
        x=alt.X("bin_start:Q", title="Test Score"), x2="bin_end:Q", y=alt.Y("density:Q", title="Density"), y2="base:Q"
    )
)

# KDE line
kde_line = alt.Chart(kde_df).mark_line(color="#FFD43B", strokeWidth=4).encode(x=alt.X("x:Q"), y=alt.Y("density:Q"))

# Combine and configure
chart = (
    (histogram + kde_line)
    .properties(width=1600, height=900, title=alt.Title("histogram-kde · altair · pyplots.ai", fontSize=28))
    .configure_axis(labelFontSize=18, titleFontSize=22)
    .configure_view(strokeWidth=0)
)

# Save PNG and HTML
chart.save("plot.png", scale_factor=3.0)
chart.save("plot.html")
