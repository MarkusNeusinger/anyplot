""" pyplots.ai
bar-permutation-importance: Permutation Feature Importance Plot
Library: altair 6.0.0 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-31
"""

import altair as alt
import numpy as np
import pandas as pd


# Data - Simulate permutation importance results from a ML model
np.random.seed(42)

# Feature names (typical ML features for a housing price model)
features = [
    "Location Score",
    "Square Footage",
    "Number of Bedrooms",
    "Year Built",
    "Lot Size",
    "Garage Capacity",
    "Bathroom Count",
    "Distance to Transit",
    "School Rating",
    "Crime Index",
    "Property Tax Rate",
    "HOA Fees",
    "Energy Rating",
    "Basement Area",
    "Pool Presence",
]

# Generate realistic importance values (some high, some medium, some low/negative)
importance_mean = np.array(
    [0.142, 0.128, 0.089, 0.072, 0.058, 0.045, 0.038, 0.032, 0.028, 0.022, 0.015, 0.008, 0.005, -0.002, -0.008]
)

# Standard deviations (higher for more important features, showing variability)
importance_std = np.array(
    [0.018, 0.015, 0.012, 0.010, 0.009, 0.008, 0.007, 0.006, 0.006, 0.005, 0.004, 0.003, 0.003, 0.002, 0.003]
)

# Create DataFrame
df = pd.DataFrame({"feature": features, "importance_mean": importance_mean, "importance_std": importance_std})

# Sort by importance (descending) for the chart
df = df.sort_values("importance_mean", ascending=True).reset_index(drop=True)

# Calculate error bar positions
df["error_min"] = df["importance_mean"] - df["importance_std"]
df["error_max"] = df["importance_mean"] + df["importance_std"]

# Base chart for bars with color gradient based on importance
bars = (
    alt.Chart(df)
    .mark_bar(size=30)
    .encode(
        x=alt.X(
            "importance_mean:Q",
            title="Mean Decrease in Model Score",
            axis=alt.Axis(labelFontSize=18, titleFontSize=22, titlePadding=15),
        ),
        y=alt.Y(
            "feature:N",
            sort=alt.EncodingSortField(field="importance_mean", order="descending"),
            title="Feature",
            axis=alt.Axis(labelFontSize=16, titleFontSize=22, titlePadding=15),
        ),
        color=alt.Color("importance_mean:Q", scale=alt.Scale(scheme="blues", domain=[-0.01, 0.15]), legend=None),
        tooltip=[
            alt.Tooltip("feature:N", title="Feature"),
            alt.Tooltip("importance_mean:Q", title="Mean Importance", format=".4f"),
            alt.Tooltip("importance_std:Q", title="Std Dev", format=".4f"),
        ],
    )
)

# Error bars
error_bars = (
    alt.Chart(df)
    .mark_errorbar(color="#306998", thickness=2.5)
    .encode(
        x=alt.X("error_min:Q", title=""),
        x2="error_max:Q",
        y=alt.Y("feature:N", sort=alt.EncodingSortField(field="importance_mean", order="descending")),
    )
)

# Vertical reference line at x=0
zero_line = (
    alt.Chart(pd.DataFrame({"x": [0]})).mark_rule(color="#333333", strokeWidth=2, strokeDash=[4, 4]).encode(x="x:Q")
)

# Combine layers
chart = (
    alt.layer(zero_line, bars, error_bars)
    .properties(
        width=1400,
        height=850,
        title=alt.Title("bar-permutation-importance · altair · pyplots.ai", fontSize=28, anchor="middle", offset=20),
    )
    .configure_axis(labelFontSize=16, titleFontSize=22)
    .configure_view(strokeWidth=0)
)

# Save as PNG (scale_factor=3 for 4200x2550, close to 4800x2700)
chart.save("plot.png", scale_factor=3.0)

# Save as HTML for interactivity
chart.save("plot.html")
