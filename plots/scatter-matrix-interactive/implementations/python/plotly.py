""" pyplots.ai
scatter-matrix-interactive: Interactive Scatter Plot Matrix (SPLOM)
Library: plotly 6.5.0 | Python 3.13.11
Quality: 91/100 | Created: 2026-01-10
"""

import plotly.graph_objects as go
import seaborn as sns
from plotly.subplots import make_subplots


# Data - Using Iris dataset for multivariate exploration
iris = sns.load_dataset("iris")

# Column names for cleaner code
cols = ["sepal_length", "sepal_width", "petal_length", "petal_width"]
labels = ["Sepal Length (cm)", "Sepal Width (cm)", "Petal Length (cm)", "Petal Width (cm)"]

# Capitalize species names for display
iris["species"] = iris["species"].str.capitalize()

# Color mapping for species (Python branding colors + complementary)
color_map = {"Setosa": "#306998", "Versicolor": "#FFD43B", "Virginica": "#4ECDC4"}
species_list = ["Setosa", "Versicolor", "Virginica"]

# Create 4x4 subplot grid - not sharing axes to allow histograms to have different y scale
n = len(cols)
fig = make_subplots(
    rows=n,
    cols=n,
    shared_xaxes="columns",  # Share x-axes within columns
    shared_yaxes=False,  # Don't share y-axes (histograms have different scale)
    horizontal_spacing=0.02,
    vertical_spacing=0.02,
)

# Add scatter plots for off-diagonal and histograms for diagonal
for i in range(n):
    for j in range(n):
        row, col = i + 1, j + 1

        if i == j:
            # Diagonal: histograms for each species (stacked)
            for species in species_list:
                subset = iris[iris["species"] == species]
                fig.add_trace(
                    go.Histogram(
                        x=subset[cols[i]],
                        name=species,
                        marker_color=color_map[species],
                        opacity=0.7,
                        showlegend=(i == 0),  # Only show legend for first diagonal
                        legendgroup=species,
                    ),
                    row=row,
                    col=col,
                )
            fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor="rgba(0,0,0,0.1)", row=row, col=col)
            fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor="rgba(0,0,0,0.1)", row=row, col=col)
        else:
            # Off-diagonal: scatter plots
            for species in species_list:
                subset = iris[iris["species"] == species]
                fig.add_trace(
                    go.Scatter(
                        x=subset[cols[j]],
                        y=subset[cols[i]],
                        mode="markers",
                        name=species,
                        marker=dict(color=color_map[species], size=8, opacity=0.7, line=dict(width=0.5, color="white")),
                        showlegend=False,
                        legendgroup=species,
                        selected=dict(marker=dict(opacity=1.0, size=10)),
                        unselected=dict(marker=dict(opacity=0.15, size=6)),
                    ),
                    row=row,
                    col=col,
                )
            fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor="rgba(0,0,0,0.1)", row=row, col=col)
            fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor="rgba(0,0,0,0.1)", row=row, col=col)

# Update axis labels - only on edges
for i in range(n):
    fig.update_yaxes(title_text=labels[i], row=i + 1, col=1)
    fig.update_xaxes(title_text=labels[i], row=n, col=i + 1)

# Layout for large canvas with interactivity
fig.update_layout(
    title=dict(text="scatter-matrix-interactive · plotly · pyplots.ai", font=dict(size=28), x=0.5, xanchor="center"),
    font=dict(size=14),
    dragmode="select",
    width=1600,
    height=1500,
    template="plotly_white",
    barmode="overlay",  # Overlay histograms
    legend=dict(
        title=dict(text="Species", font=dict(size=18)),
        font=dict(size=16),
        yanchor="top",
        y=0.99,
        xanchor="left",
        x=1.02,
        bgcolor="rgba(255,255,255,0.9)",
        bordercolor="#CCCCCC",
        borderwidth=1,
    ),
    margin=dict(l=100, r=150, t=100, b=100),
)

# Save as PNG (3600x3600 for square format)
fig.write_image("plot.png", width=1200, height=1200, scale=3)

# Save interactive HTML version with full interactivity
fig.write_html(
    "plot.html",
    include_plotlyjs=True,
    full_html=True,
    config={"displayModeBar": True, "modeBarButtonsToAdd": ["select2d", "lasso2d"], "scrollZoom": True},
)
