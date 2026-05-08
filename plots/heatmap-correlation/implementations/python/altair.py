""" anyplot.ai
heatmap-correlation: Correlation Matrix Heatmap
Library: altair 6.1.0 | Python 3.13.13
Quality: 71/100 | Updated: 2026-05-08
"""

import os

import altair as alt
import numpy as np
import pandas as pd


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

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

# Convert to long format for Altair, masking upper triangle
rows = []
for i, var1 in enumerate(variables):
    for j, var2 in enumerate(variables):
        # Only include lower triangle (including diagonal) to avoid redundancy
        if i >= j:
            rows.append({"Variable 1": var1, "Variable 2": var2, "Correlation": correlation[i, j]})

df = pd.DataFrame(rows)

# Create heatmap with diverging color scheme centered at zero
base = alt.Chart(df).encode(
    x=alt.X(
        "Variable 1:N",
        title="Variables",
        sort=variables,
        axis=alt.Axis(
            labelAngle=0, labelFontSize=18, labelFontWeight="bold", labelColor=INK, titleColor=INK, titleFontSize=22
        ),
    ),
    y=alt.Y(
        "Variable 2:N",
        title="Variables",
        sort=variables,
        axis=alt.Axis(labelFontSize=18, labelFontWeight="bold", labelColor=INK, titleColor=INK, titleFontSize=22),
    ),
)

# Heatmap rectangles
heatmap = base.mark_rect(stroke=PAGE_BG, strokeWidth=2).encode(
    color=alt.Color(
        "Correlation:Q",
        scale=alt.Scale(scheme="brownbluegreen", domain=[-1, 1]),
        legend=alt.Legend(
            title="Correlation",
            titleFontSize=20,
            labelFontSize=18,
            gradientLength=500,
            gradientThickness=35,
            fillColor=ELEVATED_BG,
            strokeColor=INK_SOFT,
        ),
    )
)

# Text annotations with correlation values
text = base.mark_text(fontSize=16, fontWeight="bold").encode(
    text=alt.Text("Correlation:Q", format=".2f"),
    color=alt.condition(
        (alt.datum.Correlation > 0.6) | (alt.datum.Correlation < -0.6), alt.value(PAGE_BG), alt.value(INK)
    ),
)

# Add tooltips for interactivity
heatmap_with_tooltip = base.mark_rect(stroke=PAGE_BG, strokeWidth=2).encode(
    color=alt.Color(
        "Correlation:Q",
        scale=alt.Scale(scheme="brownbluegreen", domain=[-1, 1]),
        legend=alt.Legend(
            title="Correlation",
            titleFontSize=20,
            labelFontSize=18,
            gradientLength=500,
            gradientThickness=35,
            fillColor=ELEVATED_BG,
            strokeColor=INK_SOFT,
        ),
    ),
    tooltip=[
        alt.Tooltip("Variable 1:N", title="X Variable"),
        alt.Tooltip("Variable 2:N", title="Y Variable"),
        alt.Tooltip("Correlation:Q", title="Correlation", format=".3f"),
    ],
)

# Combine heatmap and text with tooltips
chart = (
    (heatmap_with_tooltip + text)
    .properties(
        width=1400,
        height=1200,
        title=alt.Title(
            "heatmap-correlation · altair · anyplot.ai", fontSize=28, fontWeight="bold", anchor="middle", color=INK
        ),
    )
    .configure_view(fill=PAGE_BG, stroke=INK_SOFT, continuousWidth=1400, continuousHeight=1200)
    .configure_axis(
        domainColor=INK_SOFT,
        tickColor=INK_SOFT,
        labelColor=INK,
        labelFontSize=18,
        titleColor=INK,
        titleFontSize=22,
        titleFontWeight="bold",
        gridColor=INK_SOFT,
        gridOpacity=0.10,
    )
    .configure_title(color=INK, fontSize=28, fontWeight="bold")
    .configure_legend(
        fillColor=ELEVATED_BG, strokeColor=INK_SOFT, labelColor=INK, labelFontSize=18, titleColor=INK, titleFontSize=20
    )
)

# Save as PNG (square format ~3600x3600)
chart.save(f"plot-{THEME}.png", scale_factor=2.57)

# Save as HTML for interactivity
chart.save(f"plot-{THEME}.html")
