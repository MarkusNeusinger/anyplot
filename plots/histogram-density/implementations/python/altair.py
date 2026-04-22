""" pyplots.ai
histogram-density: Density Histogram
Library: altair 6.0.0 | Python 3.13.11
Quality: 93/100 | Created: 2025-12-29
"""

import altair as alt
import numpy as np
import pandas as pd
from scipy import stats


# Data - Generate bimodal distribution to show density histogram features
np.random.seed(42)
# Reaction times from two conditions: baseline and fatigued
baseline_times = np.random.normal(loc=250, scale=30, size=350)
fatigued_times = np.random.normal(loc=380, scale=45, size=150)
reaction_times = np.concatenate([baseline_times, fatigued_times])

# Compute histogram data manually for density normalization
num_bins = 25
bins = np.linspace(reaction_times.min() - 10, reaction_times.max() + 10, num_bins + 1)
counts, bin_edges = np.histogram(reaction_times, bins=bins, density=True)
bin_width = bin_edges[1] - bin_edges[0]

# Create DataFrame with bin ranges for proper bar rendering
hist_df = pd.DataFrame(
    {
        "bin_start": bin_edges[:-1],
        "bin_end": bin_edges[1:],
        "Density": counts,
        "bin_center": (bin_edges[:-1] + bin_edges[1:]) / 2,
    }
)

# Create density histogram using rect mark for proper filled bars
histogram = (
    alt.Chart(hist_df)
    .mark_rect(color="#306998", opacity=0.75, stroke="#1a3a5c", strokeWidth=1.5)
    .encode(
        x=alt.X("bin_start:Q", scale=alt.Scale(domain=[bins.min(), bins.max()]), title="Reaction Time (ms)"),
        x2="bin_end:Q",
        y=alt.Y("Density:Q", scale=alt.Scale(domain=[0, counts.max() * 1.1]), title="Density (probability per ms)"),
        tooltip=[
            alt.Tooltip("bin_center:Q", title="Bin Center", format=".0f"),
            alt.Tooltip("Density:Q", title="Density", format=".5f"),
        ],
    )
)

# Create KDE overlay for theoretical density reference
kde = stats.gaussian_kde(reaction_times, bw_method=0.15)
x_kde = np.linspace(reaction_times.min() - 20, reaction_times.max() + 20, 300)
y_kde = kde(x_kde)

kde_df = pd.DataFrame({"Reaction Time (ms)": x_kde, "Density": y_kde})

kde_line = alt.Chart(kde_df).mark_line(color="#FFD43B", strokeWidth=4).encode(x="Reaction Time (ms):Q", y="Density:Q")

# Combine histogram and KDE
chart = (
    alt.layer(histogram, kde_line)
    .properties(
        width=1600,
        height=900,
        title=alt.Title("histogram-density · altair · pyplots.ai", fontSize=28, anchor="middle", color="#333333"),
    )
    .configure_axis(labelFontSize=18, titleFontSize=22, gridColor="#cccccc", gridOpacity=0.3)
    .configure_view(strokeWidth=0)
)

# Save as PNG (1600 × 900 × 3 = 4800 × 2700 px)
chart.save("plot.png", scale_factor=3.0)

# Save interactive HTML version
chart.save("plot.html")
