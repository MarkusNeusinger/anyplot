""" anyplot.ai
biplot-pca: PCA Biplot with Scores and Loading Vectors
Library: plotly 6.7.0 | Python 3.13.13
Quality: 86/100 | Updated: 2026-05-17
"""

import os

import numpy as np
import plotly.graph_objects as go
from sklearn.datasets import load_iris
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
GRID = "rgba(26,26,23,0.10)" if THEME == "light" else "rgba(240,239,232,0.10)"

# Okabe-Ito palette (first series is always #009E73)
IMPRINT = ["#009E73", "#C475FD", "#4467A3"]

# Load data
iris = load_iris()
X = iris.data
y = iris.target
feature_names = iris.feature_names
target_names = iris.target_names

# Standardize and perform PCA
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)
pca = PCA(n_components=2)
scores = pca.fit_transform(X_scaled)
loadings = pca.components_.T * np.sqrt(pca.explained_variance_)

# Variance explained
var_explained = pca.explained_variance_ratio_ * 100

# Create figure
fig = go.Figure()

# Plot scores for each group
for i, target in enumerate(target_names):
    mask = y == i
    fig.add_trace(
        go.Scatter(
            x=scores[mask, 0],
            y=scores[mask, 1],
            mode="markers",
            marker={"size": 14, "color": IMPRINT[i], "opacity": 0.8, "line": {"width": 1, "color": PAGE_BG}},
            name=target.capitalize(),
            legendgroup=target,
        )
    )

# Scale loadings for visibility (relative to score spread)
score_scale = max(np.abs(scores).max(axis=0))
loading_scale = max(np.abs(loadings).max(axis=0))
scale_factor = score_scale / loading_scale * 0.9

# Plot loading arrows
arrow_color = INK_SOFT
for loading, name in zip(loadings, feature_names, strict=False):
    x_end = loading[0] * scale_factor
    y_end = loading[1] * scale_factor

    # Arrow line
    fig.add_trace(
        go.Scatter(
            x=[0, x_end],
            y=[0, y_end],
            mode="lines",
            line={"color": arrow_color, "width": 3},
            showlegend=False,
            hoverinfo="skip",
        )
    )

    # Arrowhead using annotation
    fig.add_annotation(
        x=x_end,
        y=y_end,
        ax=0,
        ay=0,
        xref="x",
        yref="y",
        axref="x",
        ayref="y",
        showarrow=True,
        arrowhead=2,
        arrowsize=1.5,
        arrowwidth=3,
        arrowcolor=arrow_color,
    )

    # Variable label with offset to avoid overlap
    label_offsets = {
        "sepal length": (0.15, 0.3),
        "sepal width": (0.1, 0.25),
        "petal length": (0.15, -0.35),
        "petal width": (0.15, 0.15),
    }
    clean_name = name.replace(" (cm)", "")
    dx, dy = label_offsets.get(clean_name, (0.1, 0.1))
    offset_x = x_end + dx
    offset_y = y_end + dy
    xanchor = "left" if x_end > 0 else "right"
    fig.add_annotation(
        x=offset_x,
        y=offset_y,
        text=clean_name,
        showarrow=False,
        font={"size": 16, "color": arrow_color},
        xanchor=xanchor,
        yanchor="middle",
    )

# Layout
fig.update_layout(
    title={
        "text": "biplot-pca · plotly · anyplot.ai",
        "font": {"size": 28, "color": INK},
        "x": 0.5,
        "xanchor": "center",
    },
    paper_bgcolor=PAGE_BG,
    plot_bgcolor=PAGE_BG,
    font={"color": INK},
    xaxis={
        "title": {"text": f"PC1 ({var_explained[0]:.1f}%)", "font": {"size": 22, "color": INK}},
        "tickfont": {"size": 18, "color": INK_SOFT},
        "zeroline": True,
        "zerolinewidth": 1,
        "zerolinecolor": arrow_color,
        "gridcolor": GRID,
        "gridwidth": 1,
        "linecolor": INK_SOFT,
    },
    yaxis={
        "title": {"text": f"PC2 ({var_explained[1]:.1f}%)", "font": {"size": 22, "color": INK}},
        "tickfont": {"size": 18, "color": INK_SOFT},
        "zeroline": True,
        "zerolinewidth": 1,
        "zerolinecolor": arrow_color,
        "gridcolor": GRID,
        "gridwidth": 1,
        "linecolor": INK_SOFT,
        "scaleanchor": "x",
        "scaleratio": 1,
    },
    legend={
        "font": {"size": 18, "color": INK_SOFT},
        "x": 0.02,
        "y": 0.98,
        "xanchor": "left",
        "yanchor": "top",
        "bgcolor": ELEVATED_BG,
        "bordercolor": INK_SOFT,
        "borderwidth": 1,
    },
    margin={"l": 80, "r": 80, "t": 100, "b": 80},
)

# Save outputs
fig.write_image(f"plot-{THEME}.png", width=1600, height=900, scale=3)
fig.write_html(f"plot-{THEME}.html", include_plotlyjs="cdn")
