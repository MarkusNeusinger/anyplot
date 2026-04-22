""" pyplots.ai
scatter-matrix: Scatter Plot Matrix
Library: plotly 6.5.0 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-26
"""

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots


# Data - Iris-like dataset with 4 variables
np.random.seed(42)
n = 150

# Create realistic flower measurement data (inspired by Iris)
species = np.repeat(["Setosa", "Versicolor", "Virginica"], n // 3)

# Generate measurements with species-specific distributions
sepal_length = np.concatenate(
    [
        np.random.normal(5.0, 0.35, n // 3),  # Setosa
        np.random.normal(5.9, 0.5, n // 3),  # Versicolor
        np.random.normal(6.6, 0.6, n // 3),  # Virginica
    ]
)
sepal_width = np.concatenate(
    [
        np.random.normal(3.4, 0.4, n // 3),  # Setosa
        np.random.normal(2.8, 0.3, n // 3),  # Versicolor
        np.random.normal(3.0, 0.3, n // 3),  # Virginica
    ]
)
petal_length = np.concatenate(
    [
        np.random.normal(1.5, 0.2, n // 3),  # Setosa
        np.random.normal(4.3, 0.5, n // 3),  # Versicolor
        np.random.normal(5.5, 0.5, n // 3),  # Virginica
    ]
)
petal_width = np.concatenate(
    [
        np.random.normal(0.25, 0.1, n // 3),  # Setosa
        np.random.normal(1.3, 0.2, n // 3),  # Versicolor
        np.random.normal(2.0, 0.3, n // 3),  # Virginica
    ]
)

df = pd.DataFrame(
    {
        "Sepal Length (cm)": sepal_length,
        "Sepal Width (cm)": sepal_width,
        "Petal Length (cm)": petal_length,
        "Petal Width (cm)": petal_width,
        "Species": species,
    }
)

# Variables and colors
dimensions = ["Sepal Length (cm)", "Sepal Width (cm)", "Petal Length (cm)", "Petal Width (cm)"]
species_list = ["Setosa", "Versicolor", "Virginica"]
colors = {"Setosa": "#306998", "Versicolor": "#FFD43B", "Virginica": "#E74C3C"}
n_dims = len(dimensions)

# Create subplots grid
fig = make_subplots(rows=n_dims, cols=n_dims, horizontal_spacing=0.03, vertical_spacing=0.03)

# Track if legend has been added for each species
legend_added = dict.fromkeys(species_list, False)

# Build scatter matrix with histograms on diagonal
for i, dim_y in enumerate(dimensions):
    for j, dim_x in enumerate(dimensions):
        row, col = i + 1, j + 1

        if i == j:
            # Diagonal: histograms
            for sp in species_list:
                mask = df["Species"] == sp
                fig.add_trace(
                    go.Histogram(
                        x=df.loc[mask, dim_x],
                        name=sp,
                        marker_color=colors[sp],
                        opacity=0.7,
                        showlegend=not legend_added[sp],
                        legendgroup=sp,
                    ),
                    row=row,
                    col=col,
                )
                legend_added[sp] = True
            fig.update_xaxes(showticklabels=True, row=row, col=col)
            fig.update_yaxes(showticklabels=False, row=row, col=col)
        else:
            # Off-diagonal: scatter plots
            for sp in species_list:
                mask = df["Species"] == sp
                fig.add_trace(
                    go.Scatter(
                        x=df.loc[mask, dim_x],
                        y=df.loc[mask, dim_y],
                        mode="markers",
                        name=sp,
                        marker=dict(color=colors[sp], size=7, opacity=0.7, line=dict(width=0.5, color="white")),
                        showlegend=False,
                        legendgroup=sp,
                    ),
                    row=row,
                    col=col,
                )

        # Add axis labels on edges
        if i == n_dims - 1:
            fig.update_xaxes(title_text=dim_x, row=row, col=col, title_font=dict(size=14))
        if j == 0:
            fig.update_yaxes(title_text=dim_y, row=row, col=col, title_font=dict(size=14))

# Update overall layout
fig.update_layout(
    title=dict(text="scatter-matrix · plotly · pyplots.ai", font=dict(size=32), x=0.5, xanchor="center"),
    font=dict(size=14),
    legend=dict(
        font=dict(size=18),
        title=dict(text="Species", font=dict(size=20)),
        yanchor="top",
        y=0.98,
        xanchor="right",
        x=0.98,
        bgcolor="rgba(255,255,255,0.9)",
    ),
    template="plotly_white",
    showlegend=True,
    barmode="overlay",
    margin=dict(l=80, r=80, t=100, b=80),
)

# Update all axes
fig.update_xaxes(tickfont=dict(size=12), showgrid=True, gridwidth=1, gridcolor="rgba(0,0,0,0.1)")
fig.update_yaxes(tickfont=dict(size=12), showgrid=True, gridwidth=1, gridcolor="rgba(0,0,0,0.1)")

# Save as PNG (square format for matrix)
fig.write_image("plot.png", width=1200, height=1200, scale=3)

# Save interactive HTML
fig.write_html("plot.html", include_plotlyjs="cdn")
