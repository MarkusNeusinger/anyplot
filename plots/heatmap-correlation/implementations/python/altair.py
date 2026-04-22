""" pyplots.ai
heatmap-correlation: Correlation Matrix Heatmap
Library: altair 6.0.0 | Python 3.13.11
Quality: 92/100 | Created: 2025-12-26
"""

import altair as alt
import numpy as np
import pandas as pd


# Data - realistic financial metrics correlation matrix
np.random.seed(42)

variables = ["Revenue", "Profit", "Expenses", "Employees", "Market Cap", "Debt", "Assets", "R&D Spend"]

# Create realistic correlation matrix
n = len(variables)
# Generate a random matrix and make it symmetric positive semi-definite
A = np.random.randn(n, n) * 0.5
correlation = np.dot(A, A.T)
# Normalize to correlation matrix (values between -1 and 1)
D = np.sqrt(np.diag(correlation))
correlation = correlation / np.outer(D, D)
# Set diagonal to 1
np.fill_diagonal(correlation, 1.0)
# Round to 2 decimal places
correlation = np.round(correlation, 2)

# Convert to long format for Altair
rows = []
for i, var1 in enumerate(variables):
    for j, var2 in enumerate(variables):
        rows.append({"Variable 1": var1, "Variable 2": var2, "Correlation": correlation[i, j]})

df = pd.DataFrame(rows)

# Create heatmap with diverging color scheme centered at zero
base = alt.Chart(df).encode(
    x=alt.X(
        "Variable 1:N",
        title=None,
        sort=variables,
        axis=alt.Axis(labelAngle=0, labelFontSize=15, labelFontWeight="bold"),
    ),
    y=alt.Y("Variable 2:N", title=None, sort=variables, axis=alt.Axis(labelFontSize=15, labelFontWeight="bold")),
)

# Heatmap rectangles
heatmap = base.mark_rect(stroke="white", strokeWidth=2).encode(
    color=alt.Color(
        "Correlation:Q",
        scale=alt.Scale(scheme="redblue", domain=[-1, 1], reverse=True),
        legend=alt.Legend(
            title="Correlation", titleFontSize=20, labelFontSize=16, gradientLength=500, gradientThickness=30
        ),
    )
)

# Text annotations with correlation values
text = base.mark_text(fontSize=14, fontWeight="bold").encode(
    text=alt.Text("Correlation:Q", format=".2f"),
    color=alt.condition(
        (alt.datum.Correlation > 0.6) | (alt.datum.Correlation < -0.6), alt.value("white"), alt.value("black")
    ),
)

# Combine heatmap and text
chart = (
    (heatmap + text)
    .properties(
        width=700,
        height=700,
        title=alt.Title("heatmap-correlation · altair · pyplots.ai", fontSize=28, fontWeight="bold", anchor="middle"),
    )
    .configure_view(strokeWidth=0)
    .configure_axis(domain=False, ticks=False)
)

# Save as PNG (square format ~3600x3600)
chart.save("plot.png", scale_factor=5.0)

# Save as HTML for interactivity
chart.save("plot.html")
