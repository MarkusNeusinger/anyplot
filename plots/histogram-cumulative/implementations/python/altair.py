""" pyplots.ai
histogram-cumulative: Cumulative Histogram
Library: altair 6.0.0 | Python 3.13.11
Quality: 92/100 | Created: 2025-12-30
"""

import altair as alt
import numpy as np
import pandas as pd


# Data: Monthly electricity usage (kWh) for households
np.random.seed(42)
usage = np.concatenate(
    [
        np.random.normal(250, 50, 300),  # Low usage households
        np.random.normal(450, 80, 200),  # Medium usage households
    ]
)

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

# Create cumulative histogram as step chart
chart = (
    alt.Chart(df)
    .mark_area(interpolate="step-after", color="#306998", opacity=0.7, line={"color": "#306998", "strokeWidth": 3})
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
        title=alt.Title("histogram-cumulative · altair · pyplots.ai", fontSize=28, anchor="middle"),
    )
    .configure_axis(labelFontSize=18, titleFontSize=22, gridColor="#cccccc", gridOpacity=0.3)
    .configure_view(strokeWidth=0)
)

# Save PNG (1600 × 900 at scale 3 = 4800 × 2700)
chart.save("plot.png", scale_factor=3.0)

# Save interactive HTML
chart.interactive().save("plot.html")
