""" pyplots.ai
biplot-pca: PCA Biplot with Scores and Loading Vectors
Library: plotly 6.5.1 | Python 3.13.11
Quality: 91/100 | Created: 2026-01-09
"""

import numpy as np
import plotly.graph_objects as go
from sklearn.datasets import load_iris
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler


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

# Colors for groups (Python Blue and related colors)
colors = ["#306998", "#FFD43B", "#4B8BBE"]

# Create figure
fig = go.Figure()

# Plot scores for each group
for i, (target, color) in enumerate(zip(target_names, colors, strict=False)):
    mask = y == i
    fig.add_trace(
        go.Scatter(
            x=scores[mask, 0],
            y=scores[mask, 1],
            mode="markers",
            marker={"size": 14, "color": color, "opacity": 0.8, "line": {"width": 1, "color": "white"}},
            name=target.capitalize(),
            legendgroup=target,
        )
    )

# Scale loadings for visibility (relative to score spread)
score_scale = max(np.abs(scores).max(axis=0))
loading_scale = max(np.abs(loadings).max(axis=0))
scale_factor = score_scale / loading_scale * 0.9

# Plot loading arrows
arrow_color = "#333333"
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
    # Add vertical offset for near-horizontal arrows to separate labels
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
    title={"text": "biplot-pca · plotly · pyplots.ai", "font": {"size": 28}, "x": 0.5, "xanchor": "center"},
    xaxis={
        "title": {"text": f"PC1 ({var_explained[0]:.1f}%)", "font": {"size": 22}},
        "tickfont": {"size": 18},
        "zeroline": True,
        "zerolinewidth": 1,
        "zerolinecolor": "lightgray",
        "gridcolor": "lightgray",
        "gridwidth": 1,
    },
    yaxis={
        "title": {"text": f"PC2 ({var_explained[1]:.1f}%)", "font": {"size": 22}},
        "tickfont": {"size": 18},
        "zeroline": True,
        "zerolinewidth": 1,
        "zerolinecolor": "lightgray",
        "gridcolor": "lightgray",
        "gridwidth": 1,
        "scaleanchor": "x",
        "scaleratio": 1,
    },
    template="plotly_white",
    legend={
        "font": {"size": 18},
        "x": 0.02,
        "y": 0.98,
        "xanchor": "left",
        "yanchor": "top",
        "bgcolor": "rgba(255,255,255,0.8)",
        "bordercolor": "lightgray",
        "borderwidth": 1,
    },
    margin={"l": 80, "r": 80, "t": 100, "b": 80},
)

# Save outputs
fig.write_image("plot.png", width=1600, height=900, scale=3)
fig.write_html("plot.html", include_plotlyjs="cdn")
