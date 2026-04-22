""" pyplots.ai
bar-permutation-importance: Permutation Feature Importance Plot
Library: plotly 6.5.0 | Python 3.13.11
Quality: 93/100 | Created: 2025-12-31
"""

import numpy as np
import pandas as pd
import plotly.graph_objects as go


# Data - Simulating permutation importance results from a regression model
np.random.seed(42)

# Feature names representing typical ML model features
features = [
    "Temperature",
    "Humidity",
    "Wind Speed",
    "Pressure",
    "Solar Radiation",
    "Precipitation",
    "Cloud Cover",
    "UV Index",
    "Visibility",
    "Dew Point",
    "Air Quality Index",
    "Altitude",
    "Latitude",
    "Season Encoded",
    "Time of Day",
]

n_features = len(features)

# Generate realistic importance values (some high, some low, a couple negative)
importance_mean = np.array(
    [0.245, 0.198, 0.156, 0.089, 0.072, 0.058, 0.045, 0.038, 0.025, 0.018, 0.012, 0.008, 0.003, -0.002, -0.008]
)

# Standard deviations vary - more important features often have higher variability
importance_std = np.array(
    [0.045, 0.038, 0.032, 0.022, 0.018, 0.015, 0.012, 0.010, 0.008, 0.006, 0.005, 0.004, 0.003, 0.003, 0.004]
)

# Create DataFrame and sort by importance (highest first)
df = pd.DataFrame({"feature": features, "importance_mean": importance_mean, "importance_std": importance_std})
df = df.sort_values("importance_mean", ascending=True)  # ascending for horizontal bar layout

# Color gradient based on importance (Python Blue to Yellow)
min_imp = df["importance_mean"].min()
max_imp = df["importance_mean"].max()
imp_range = max_imp - min_imp
colors = [
    f"rgb({int(48 + (255 - 48) * (v - min_imp) / imp_range)}, "
    f"{int(105 + (212 - 105) * (v - min_imp) / imp_range)}, "
    f"{int(152 - (152 - 59) * (v - min_imp) / imp_range)})"
    for v in df["importance_mean"]
]

# Create figure
fig = go.Figure()

# Add horizontal bars
fig.add_trace(
    go.Bar(
        x=df["importance_mean"],
        y=df["feature"],
        orientation="h",
        marker=dict(color=colors),
        error_x=dict(type="data", array=df["importance_std"], color="rgba(0, 0, 0, 0.5)", thickness=2, width=6),
        hovertemplate="<b>%{y}</b><br>Importance: %{x:.3f}<extra></extra>",
    )
)

# Add vertical reference line at x=0
fig.add_vline(x=0, line=dict(color="rgba(0, 0, 0, 0.4)", width=2, dash="dash"))

# Update layout for 4800x2700 canvas
fig.update_layout(
    title=dict(
        text="bar-permutation-importance · plotly · pyplots.ai",
        font=dict(size=32, color="#333333"),
        x=0.5,
        xanchor="center",
    ),
    xaxis=dict(
        title=dict(text="Mean Decrease in Model Score", font=dict(size=24)),
        tickfont=dict(size=18),
        gridcolor="rgba(0, 0, 0, 0.1)",
        gridwidth=1,
        zeroline=False,
    ),
    yaxis=dict(
        title=dict(text="Feature", font=dict(size=24)),
        tickfont=dict(size=18),
        gridcolor="rgba(0, 0, 0, 0.1)",
        gridwidth=1,
    ),
    template="plotly_white",
    plot_bgcolor="white",
    paper_bgcolor="white",
    margin=dict(l=180, r=60, t=100, b=80),
    showlegend=False,
)

# Save as PNG (4800x2700 via scale=3)
fig.write_image("plot.png", width=1600, height=900, scale=3)

# Save interactive HTML
fig.write_html("plot.html", include_plotlyjs="cdn")
