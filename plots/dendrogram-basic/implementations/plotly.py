""" pyplots.ai
dendrogram-basic: Basic Dendrogram
Library: plotly 6.5.2 | Python 3.14.3
Quality: 83/100 | Updated: 2026-04-05
"""

import numpy as np
import plotly.figure_factory as ff
from scipy.cluster.hierarchy import linkage


# Data - Iris flower measurements for 15 samples across 3 species
np.random.seed(42)
labels = [
    "Setosa-1",
    "Setosa-2",
    "Setosa-3",
    "Setosa-4",
    "Setosa-5",
    "Versicolor-1",
    "Versicolor-2",
    "Versicolor-3",
    "Versicolor-4",
    "Versicolor-5",
    "Virginica-1",
    "Virginica-2",
    "Virginica-3",
    "Virginica-4",
    "Virginica-5",
]

# Sepal length, sepal width, petal length, petal width
setosa = np.random.randn(5, 4) * 0.3 + np.array([5.0, 3.4, 1.5, 0.2])
versicolor = np.random.randn(5, 4) * 0.4 + np.array([5.9, 2.8, 4.3, 1.3])
virginica = np.random.randn(5, 4) * 0.4 + np.array([6.6, 3.0, 5.5, 2.0])
data = np.vstack([setosa, versicolor, virginica])

# Colorscale: maps to scipy color keys (b, c, g, k, m, r, w, y) alphabetically
# C0->b(idx 0), C1->g(idx 2), C2->r(idx 5), C3->c(idx 1), above-threshold->C0
colorscale = [
    "#306998",  # b -> Python Blue (above-threshold merges)
    "#E1974C",  # c -> Warm amber
    "#52A675",  # g -> Muted green
    "#333333",  # k
    "#8B6BAE",  # m
    "#D45B5B",  # r -> Soft coral
    "#ffffff",  # w
    "#C4A437",  # y
]

fig = ff.create_dendrogram(
    data, labels=labels, colorscale=colorscale, linkagefun=lambda x: linkage(x, method="ward"), color_threshold=3.5
)

# Add merge distance hover to each branch
for trace in fig.data:
    trace.line.width = 3
    merge_height = max(y for y in trace.y if y > 0) if any(y > 0 for y in trace.y) else 0
    trace.hovertemplate = f"Merge distance: {merge_height:.2f}<extra></extra>"

# Layout
fig.update_layout(
    title={
        "text": "dendrogram-basic · plotly · pyplots.ai",
        "font": {"size": 28, "color": "#2a2a2a", "family": "Arial, sans-serif"},
        "x": 0.5,
        "xanchor": "center",
    },
    xaxis={
        "title": {"text": "Iris Flower Samples", "font": {"size": 22}},
        "tickfont": {"size": 16},
        "tickangle": -35,
        "showline": True,
        "linecolor": "#cccccc",
        "zeroline": False,
    },
    yaxis={
        "title": {"text": "Distance (Ward linkage)", "font": {"size": 22}},
        "tickfont": {"size": 18},
        "showline": True,
        "linecolor": "#cccccc",
        "gridcolor": "rgba(0,0,0,0.06)",
        "gridwidth": 1,
        "zeroline": False,
    },
    template="plotly_white",
    width=1600,
    height=900,
    margin={"l": 90, "r": 50, "t": 100, "b": 150},
    plot_bgcolor="#ffffff",
    hoverlabel={"bgcolor": "white", "font_size": 14, "bordercolor": "#cccccc"},
)

# Save
fig.write_image("plot.png", width=1600, height=900, scale=3)
fig.write_html("plot.html", include_plotlyjs="cdn")
