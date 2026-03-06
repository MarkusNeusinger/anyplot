"""pyplots.ai
heatmap-stripes-climate: Climate Warming Stripes
Library: altair | Python 3.13
Quality: pending | Created: 2026-03-06
"""

import altair as alt
import numpy as np
import pandas as pd


# Data - synthetic global temperature anomalies (1850-2024) mimicking HadCRUT pattern
np.random.seed(42)
years = np.arange(1850, 2025)
n = len(years)

# Build a realistic warming trend: slight cooling until ~1910, gradual rise, acceleration after 1980
baseline_trend = np.piecewise(
    years.astype(float),
    [years < 1910, (years >= 1910) & (years < 1980), years >= 1980],
    [lambda y: -0.2 + (y - 1850) * (-0.001), lambda y: -0.3 + (y - 1910) * 0.005, lambda y: 0.05 + (y - 1980) * 0.022],
)
noise = np.random.normal(0, 0.08, n)
anomaly = baseline_trend + noise

df = pd.DataFrame({"year": years, "anomaly": anomaly})

# Plot - warming stripes: vertical colored bars with no axes or labels
max_abs = max(abs(anomaly.min()), abs(anomaly.max()))

chart = (
    alt.Chart(df)
    .mark_rect()
    .encode(
        x=alt.X("year:O", axis=None),
        color=alt.Color(
            "anomaly:Q",
            scale=alt.Scale(domain=[-max_abs, 0, max_abs], range=["#08306b", "#f7f7f7", "#67000d"], type="linear"),
            legend=None,
        ),
    )
    .properties(
        width=1600,
        height=530,
        title=alt.Title("heatmap-stripes-climate \u00b7 altair \u00b7 pyplots.ai", fontSize=28, anchor="middle"),
    )
    .configure_view(strokeWidth=0)
)

# Save
chart.save("plot.png", scale_factor=3.0)
chart.save("plot.html")
