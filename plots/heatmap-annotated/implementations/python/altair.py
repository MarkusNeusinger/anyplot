""" pyplots.ai
heatmap-annotated: Annotated Heatmap
Library: altair 6.0.0 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-24
"""

import altair as alt
import numpy as np
import pandas as pd


# Data: Correlation matrix for realistic dataset
np.random.seed(42)

# Create variable names for a realistic correlation matrix
variables = ["Sales", "Marketing", "R&D", "Support", "Revenue", "Growth", "Profit"]
n_vars = len(variables)

# Generate a realistic correlation matrix
base = np.random.randn(100, n_vars)
# Add some correlations
base[:, 4] = base[:, 0] * 0.8 + base[:, 1] * 0.3 + np.random.randn(100) * 0.3  # Revenue
base[:, 5] = base[:, 2] * 0.6 + np.random.randn(100) * 0.4  # Growth
base[:, 6] = base[:, 4] * 0.7 - base[:, 3] * 0.2 + np.random.randn(100) * 0.3  # Profit

# Calculate correlation matrix
corr_matrix = np.corrcoef(base.T)

# Create long-format DataFrame for Altair
rows = []
for i, row_var in enumerate(variables):
    for j, col_var in enumerate(variables):
        rows.append({"x": col_var, "y": row_var, "correlation": round(corr_matrix[i, j], 2)})

df = pd.DataFrame(rows)

# Create base heatmap with rectangles
base_chart = (
    alt.Chart(df)
    .mark_rect(stroke="white", strokeWidth=2)
    .encode(
        x=alt.X(
            "x:N", title="Variable", sort=variables, axis=alt.Axis(labelFontSize=18, titleFontSize=22, labelAngle=-45)
        ),
        y=alt.Y("y:N", title="Variable", sort=variables, axis=alt.Axis(labelFontSize=18, titleFontSize=22)),
        color=alt.Color(
            "correlation:Q",
            scale=alt.Scale(scheme="blueorange", domain=[-1, 1]),
            legend=alt.Legend(title="Correlation", titleFontSize=18, labelFontSize=16),
        ),
    )
)

# Create text layer for annotations
# Use conditional color for text visibility (white on dark, black on light)
text = (
    alt.Chart(df)
    .mark_text(fontSize=20, fontWeight="bold")
    .encode(
        x=alt.X("x:N", sort=variables),
        y=alt.Y("y:N", sort=variables),
        text=alt.Text("correlation:Q", format=".2f"),
        color=alt.condition(
            (alt.datum.correlation > 0.5) | (alt.datum.correlation < -0.5), alt.value("white"), alt.value("black")
        ),
    )
)

# Combine heatmap and text
chart = (
    (base_chart + text)
    .properties(
        width=1000,
        height=1000,
        title=alt.Title("heatmap-annotated \u00b7 altair \u00b7 pyplots.ai", fontSize=28, anchor="middle"),
    )
    .configure_view(strokeWidth=0)
)

# Save as PNG (scale_factor=3 for high resolution: 1000x1000 * 3.6 = 3600x3600)
chart.save("plot.png", scale_factor=3.0)

# Save as HTML for interactive version
chart.save("plot.html")
