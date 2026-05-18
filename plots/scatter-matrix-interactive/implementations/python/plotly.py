""" anyplot.ai
scatter-matrix-interactive: Interactive Scatter Plot Matrix (SPLOM)
Library: plotly 6.7.0 | Python 3.13.13
Quality: 90/100 | Updated: 2026-05-18
"""

import os

import plotly.graph_objects as go
import seaborn as sns
from plotly.subplots import make_subplots


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"
GRID = "rgba(26,26,23,0.10)" if THEME == "light" else "rgba(240,239,232,0.10)"
GRID_LIGHT = "rgba(26,26,23,0.05)" if THEME == "light" else "rgba(240,239,232,0.05)"

# Okabe-Ito palette
OKABE_ITO = ["#009E73", "#D55E00", "#0072B2", "#CC79A7"]

# Data - Using Iris dataset for multivariate exploration
iris = sns.load_dataset("iris")

# Column names for cleaner code
cols = ["sepal_length", "sepal_width", "petal_length", "petal_width"]
labels = ["Sepal Length (cm)", "Sepal Width (cm)", "Petal Length (cm)", "Petal Width (cm)"]

# Capitalize species names for display
iris["species"] = iris["species"].str.capitalize()

# Species info
species_list = ["Setosa", "Versicolor", "Virginica"]
color_map = {s: OKABE_ITO[i] for i, s in enumerate(species_list)}

# Create 4x4 subplot grid
n = len(cols)
fig = make_subplots(
    rows=n, cols=n, shared_xaxes="columns", shared_yaxes=False, horizontal_spacing=0.02, vertical_spacing=0.02
)

# Add scatter plots for off-diagonal and histograms for diagonal
for i in range(n):
    for j in range(n):
        row, col = i + 1, j + 1

        if i == j:
            # Diagonal: histograms for each species (overlaid)
            for species in species_list:
                subset = iris[iris["species"] == species]
                fig.add_trace(
                    go.Histogram(
                        x=subset[cols[i]],
                        name=species,
                        marker_color=color_map[species],
                        opacity=0.7,
                        showlegend=(i == 0),
                        legendgroup=species,
                    ),
                    row=row,
                    col=col,
                )
            fig.update_xaxes(showgrid=True, gridwidth=0.8, gridcolor=GRID_LIGHT, row=row, col=col)
            fig.update_yaxes(showgrid=True, gridwidth=0.8, gridcolor=GRID_LIGHT, row=row, col=col)
        else:
            # Off-diagonal: scatter plots with linked selection
            for species in species_list:
                subset = iris[iris["species"] == species]
                fig.add_trace(
                    go.Scatter(
                        x=subset[cols[j]],
                        y=subset[cols[i]],
                        mode="markers",
                        name=species,
                        marker={
                            "color": color_map[species], "size": 10, "opacity": 0.7, "line": {"width": 0.5, "color": PAGE_BG}
                        },
                        showlegend=False,
                        legendgroup=species,
                        selected={"marker": {"opacity": 1.0, "size": 12}},
                        unselected={"marker": {"opacity": 0.15, "size": 6}},
                    ),
                    row=row,
                    col=col,
                )
            fig.update_xaxes(showgrid=True, gridwidth=0.8, gridcolor=GRID_LIGHT, row=row, col=col)
            fig.update_yaxes(showgrid=True, gridwidth=0.8, gridcolor=GRID_LIGHT, row=row, col=col)

# Update axis labels - only on edges
for i in range(n):
    fig.update_yaxes(title_text=labels[i], row=i + 1, col=1)
    fig.update_xaxes(title_text=labels[i], row=n, col=i + 1)

# Layout for large canvas with interactivity
fig.update_layout(
    title={
        "text": "scatter-matrix-interactive · python · plotly · anyplot.ai",
        "font": {"size": 28, "color": INK},
        "x": 0.5,
        "xanchor": "center",
    },
    font={"color": INK_SOFT, "size": 14},
    dragmode="select",
    width=1600,
    height=900,
    paper_bgcolor=PAGE_BG,
    plot_bgcolor=PAGE_BG,
    barmode="overlay",
    legend={
        "title": {"text": "Species", "font": {"size": 18, "color": INK}},
        "font": {"size": 16, "color": INK_SOFT},
        "yanchor": "top",
        "y": 0.99,
        "xanchor": "left",
        "x": 1.02,
        "bgcolor": ELEVATED_BG,
        "bordercolor": INK_SOFT,
        "borderwidth": 1,
    },
    margin={"l": 100, "r": 150, "t": 100, "b": 100},
)

# Update all axis properties for theme-adaptive chrome
fig.update_xaxes(
    title_font={"color": INK, "size": 22},
    tickfont={"color": INK_SOFT, "size": 18},
    linecolor=INK_SOFT,
    zerolinecolor=INK_SOFT,
)
fig.update_yaxes(
    title_font={"color": INK, "size": 22},
    tickfont={"color": INK_SOFT, "size": 18},
    linecolor=INK_SOFT,
    zerolinecolor=INK_SOFT,
)

# Save as PNG and HTML
fig.write_image(f"plot-{THEME}.png", width=1600, height=900, scale=3)
fig.write_html(
    f"plot-{THEME}.html",
    include_plotlyjs="cdn",
    config={"displayModeBar": True, "modeBarButtonsToAdd": ["select2d", "lasso2d"]},
)
