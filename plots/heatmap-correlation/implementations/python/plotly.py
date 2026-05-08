"""anyplot.ai
heatmap-correlation: Correlation Matrix Heatmap
Library: plotly | Python 3.13
Quality: 92/100 | Updated: 2025-05-08
"""

import os

import numpy as np
import plotly.graph_objects as go


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"
GRID = "rgba(26,26,23,0.10)" if THEME == "light" else "rgba(240,239,232,0.10)"

# Data - Healthcare metrics correlation matrix
np.random.seed(42)
variables = [
    "Heart Rate",
    "Blood Pressure",
    "Cholesterol",
    "BMI",
    "Sleep Hours",
    "Exercise (hrs)",
    "Stress Level",
    "Resting O2",
]

# Create realistic correlation matrix with meaningful health relationships
n_vars = len(variables)
base = np.random.randn(200, n_vars)

# Add realistic correlations based on health domain knowledge
base[:, 1] = base[:, 0] * 0.65 + np.random.randn(200) * 0.4  # BP ~ Heart Rate
base[:, 2] = base[:, 0] * 0.5 + base[:, 3] * 0.6 + np.random.randn(200) * 0.4  # Cholesterol
base[:, 3] = np.random.randn(200)  # BMI (independent)
base[:, 4] = -base[:, 6] * 0.7 + np.random.randn(200) * 0.4  # Sleep ~ -Stress
base[:, 5] = (
    -base[:, 0] * 0.5 - base[:, 6] * 0.4 + np.random.randn(200) * 0.5
)  # Exercise inversely related to HR and Stress
base[:, 6] = np.random.randn(200)  # Stress (independent)
base[:, 7] = base[:, 4] * 0.6 + np.random.randn(200) * 0.5  # O2 ~ Sleep

# Calculate correlation matrix
correlation_matrix = np.corrcoef(base.T)

# Create mask for lower triangle (show only lower triangle + diagonal)
mask = np.triu(np.ones_like(correlation_matrix, dtype=bool), k=1)
masked_corr = np.where(mask, np.nan, correlation_matrix)

# Create annotation text with theme-adaptive colors
annotations = []
for i in range(n_vars):
    for j in range(n_vars):
        if not mask[i, j]:
            # Use theme-adaptive text color based on correlation strength
            text_color = INK if abs(correlation_matrix[i, j]) <= 0.5 else ELEVATED_BG
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
        colorscale="BrBG",  # Diverging: brown (negative) to green (positive)
        zmin=-1,
        zmax=1,
        colorbar={
            "title": {"text": "Pearson<br>Correlation", "font": {"size": 20, "color": INK}},
            "tickfont": {"size": 16, "color": INK_SOFT},
            "thickness": 25,
            "len": 0.8,
            "tickvals": [-1, -0.5, 0, 0.5, 1],
            "bgcolor": PAGE_BG,
        },
        hoverongaps=False,
        hovertemplate="%{customdata}<extra></extra>",
        customdata=hover_text,
    )
)

# Update layout for 4800x2700 px
fig.update_layout(
    title={
        "text": "heatmap-correlation · plotly · anyplot.ai",
        "font": {"size": 32, "color": INK},
        "x": 0.5,
        "xanchor": "center",
    },
    xaxis={
        "title": {"text": "Health Metrics", "font": {"size": 24, "color": INK}},
        "tickfont": {"size": 18, "color": INK_SOFT},
        "side": "bottom",
        "tickangle": 45,
        "gridcolor": GRID,
        "linecolor": INK_SOFT,
    },
    yaxis={
        "title": {"text": "Health Metrics", "font": {"size": 24, "color": INK}},
        "tickfont": {"size": 18, "color": INK_SOFT},
        "autorange": "reversed",
        "gridcolor": GRID,
        "linecolor": INK_SOFT,
    },
    annotations=annotations,
    paper_bgcolor=PAGE_BG,
    plot_bgcolor=PAGE_BG,
    font={"color": INK},
    margin={"l": 140, "r": 100, "t": 100, "b": 150},
    width=1600,
    height=900,
)

# Save as PNG and HTML with theme-suffixed filenames
fig.write_image(f"plot-{THEME}.png", width=1600, height=900, scale=3)
fig.write_html(f"plot-{THEME}.html", include_plotlyjs="cdn")
