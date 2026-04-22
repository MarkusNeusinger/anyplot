""" pyplots.ai
heatmap-correlation: Correlation Matrix Heatmap
Library: plotly 6.5.0 | Python 3.13.11
Quality: 92/100 | Created: 2025-12-26
"""

import numpy as np
import plotly.graph_objects as go


# Data - Financial metrics correlation matrix (realistic scenario)
np.random.seed(42)
variables = ["Revenue", "Profit", "Expenses", "Assets", "Debt", "ROI", "Growth", "Risk"]

# Create a realistic correlation matrix with meaningful relationships
n_vars = len(variables)
# Start with random base
base = np.random.randn(100, n_vars)

# Add realistic correlations
base[:, 1] = base[:, 0] * 0.85 + np.random.randn(100) * 0.3  # Profit ~ Revenue
base[:, 2] = base[:, 0] * 0.7 + np.random.randn(100) * 0.5  # Expenses ~ Revenue
base[:, 3] = base[:, 0] * 0.6 + np.random.randn(100) * 0.6  # Assets ~ Revenue
base[:, 4] = base[:, 3] * 0.5 + np.random.randn(100) * 0.7  # Debt ~ Assets
base[:, 5] = base[:, 1] * 0.7 - base[:, 2] * 0.3 + np.random.randn(100) * 0.4  # ROI
base[:, 6] = base[:, 0] * 0.4 + np.random.randn(100) * 0.8  # Growth ~ Revenue
base[:, 7] = -base[:, 5] * 0.6 + base[:, 4] * 0.4 + np.random.randn(100) * 0.5  # Risk

# Calculate correlation matrix
correlation_matrix = np.corrcoef(base.T)

# Create mask for lower triangle (show only lower triangle + diagonal)
mask = np.triu(np.ones_like(correlation_matrix, dtype=bool), k=1)
masked_corr = np.where(mask, np.nan, correlation_matrix)

# Create annotation text (2 decimal places) with dynamic text color
annotations = []
for i in range(n_vars):
    for j in range(n_vars):
        if not mask[i, j]:
            text_color = "white" if abs(correlation_matrix[i, j]) > 0.5 else "black"
            annotations.append(
                {
                    "x": variables[j],
                    "y": variables[i],
                    "text": f"{correlation_matrix[i, j]:.2f}",
                    "showarrow": False,
                    "font": {"size": 18, "color": text_color},
                }
            )

# Create custom hover text for rich interactive experience
hover_text = []
for i in range(n_vars):
    row = []
    for j in range(n_vars):
        if mask[i, j]:
            row.append("")
        else:
            r = correlation_matrix[i, j]
            # Interpret correlation strength
            if abs(r) >= 0.7:
                strength = "Strong"
            elif abs(r) >= 0.4:
                strength = "Moderate"
            else:
                strength = "Weak"
            direction = "positive" if r > 0 else "negative" if r < 0 else "none"
            row.append(
                f"<b>{variables[i]}</b> vs <b>{variables[j]}</b><br>"
                f"Correlation: <b>{r:.3f}</b><br>"
                f"Strength: {strength} {direction}"
            )
    hover_text.append(row)

# Create heatmap
fig = go.Figure(
    data=go.Heatmap(
        z=masked_corr,
        x=variables,
        y=variables,
        colorscale="RdBu_r",  # Diverging: red (negative) to blue (positive)
        zmin=-1,
        zmax=1,
        colorbar={
            "title": {"text": "Pearson<br>Correlation", "font": {"size": 20}},
            "tickfont": {"size": 16},
            "thickness": 25,
            "len": 0.8,
            "tickvals": [-1, -0.5, 0, 0.5, 1],
        },
        hoverongaps=False,
        hovertemplate="%{customdata}<extra></extra>",
        customdata=hover_text,
    )
)

# Update layout for 4800x2700 px
fig.update_layout(
    title={"text": "heatmap-correlation · plotly · pyplots.ai", "font": {"size": 32}, "x": 0.5, "xanchor": "center"},
    xaxis={
        "title": {"text": "Financial Metrics", "font": {"size": 24}},
        "tickfont": {"size": 18},
        "side": "bottom",
        "tickangle": 45,
    },
    yaxis={
        "title": {"text": "Financial Metrics", "font": {"size": 24}},
        "tickfont": {"size": 18},
        "autorange": "reversed",  # Match matrix orientation
    },
    annotations=annotations,
    template="plotly_white",
    margin={"l": 140, "r": 100, "t": 100, "b": 150},
    width=1600,
    height=900,
)

# Save as PNG (4800x2700 with scale=3) and HTML
fig.write_image("plot.png", width=1600, height=900, scale=3)
fig.write_html("plot.html", include_plotlyjs=True, full_html=True)
