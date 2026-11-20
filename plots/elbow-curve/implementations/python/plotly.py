"""anyplot.ai
elbow-curve: Elbow Curve for K-Means Clustering
Library: plotly 6.7.0 | Python 3.13.13
Quality: pending | Updated: 2026-05-10
"""

import os

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from sklearn.cluster import KMeans
from sklearn.datasets import make_blobs


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
GRID = "rgba(26,26,23,0.10)" if THEME == "light" else "rgba(240,239,232,0.10)"

# Imprint palette: position 1 for the curve, position 2 for the highlighted elbow
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Columns: set these to your table's column names
K = "Number of clusters (k)"  # role: k_values
INERTIA = "Within-cluster sum of squares (inertia)"  # role: inertia

# Data: replace this block with your own table, for example df = pd.read_csv("inertia.csv")
# Simulation: customer segments (spend vs. visits) in 6 groups, K-means fitted for k = 1..12
points, _ = make_blobs(n_samples=900, centers=6, cluster_std=1.3, center_box=(-12, 12), random_state=7)
ks = list(range(1, 13))
df = pd.DataFrame({K: ks, INERTIA: [KMeans(n_clusters=k, n_init=10, random_state=7).fit(points).inertia_ for k in ks]})

# Plot: reads only df and the constants above
# Elbow = point farthest from the straight line joining the first and last point (both axes scaled to 0-1)
x_norm = (df[K] - df[K].min()) / (df[K].max() - df[K].min())
y_norm = (df[INERTIA] - df[INERTIA].min()) / (df[INERTIA].max() - df[INERTIA].min())
elbow_row = df.iloc[int(np.argmax(np.abs(x_norm + y_norm - 1)))]
elbow_k = int(elbow_row[K])
elbow_inertia = float(elbow_row[INERTIA])

fig = go.Figure()

fig.add_trace(
    go.Scatter(
        x=df[K],
        y=df[INERTIA],
        mode="lines+markers",
        name="Inertia",
        line={"color": IMPRINT_PALETTE[0], "width": 3},
        marker={"size": 11, "color": IMPRINT_PALETTE[0], "line": {"color": PAGE_BG, "width": 1.5}},
        hovertemplate="k=%{x}<br>Inertia=%{y:,.0f}<extra></extra>",
    )
)

fig.add_trace(
    go.Scatter(
        x=[elbow_k],
        y=[elbow_inertia],
        mode="markers",
        name=f"Elbow (k={elbow_k})",
        marker={"size": 18, "color": IMPRINT_PALETTE[1], "line": {"color": INK, "width": 2}},
        hovertemplate=f"Elbow k={elbow_k}<br>Inertia={elbow_inertia:,.0f}<extra></extra>",
    )
)

fig.add_annotation(
    x=elbow_k,
    y=elbow_inertia,
    text=f"Elbow at k = {elbow_k}",
    showarrow=True,
    arrowhead=2,
    arrowwidth=1.5,
    arrowcolor=INK,
    ax=60,
    ay=-50,
    font={"size": 13, "color": INK},
    bgcolor=ELEVATED_BG,
    bordercolor=INK_SOFT,
    borderwidth=1,
    borderpad=5,
)

# Style
fig.update_layout(
    autosize=False,
    title={
        "text": "elbow-curve · python · plotly · anyplot.ai",
        "font": {"size": 18, "color": INK},
        "x": 0.5,
        "xanchor": "center",
    },
    xaxis={
        "title": {"text": K, "font": {"size": 14, "color": INK}},
        "tickfont": {"size": 12, "color": INK_SOFT},
        "tickmode": "linear",
        "tick0": 1,
        "dtick": 1,
        "showgrid": True,
        "gridcolor": GRID,
        "zeroline": False,
        "linecolor": INK_SOFT,
    },
    yaxis={
        "title": {"text": INERTIA, "font": {"size": 14, "color": INK}},
        "tickfont": {"size": 12, "color": INK_SOFT},
        "showgrid": True,
        "gridcolor": GRID,
        "zeroline": False,
        "linecolor": INK_SOFT,
        "range": [0, df[INERTIA].max() * 1.05],
    },
    paper_bgcolor=PAGE_BG,
    plot_bgcolor=PAGE_BG,
    font={"color": INK},
    legend={
        "x": 0.97,
        "y": 0.97,
        "xanchor": "right",
        "yanchor": "top",
        "font": {"size": 12, "color": INK_SOFT},
        "bgcolor": ELEVATED_BG,
        "bordercolor": INK_SOFT,
        "borderwidth": 1,
    },
    margin={"l": 90, "r": 40, "t": 70, "b": 65},
)

fig.write_image(f"plot-{THEME}.png", width=800, height=450, scale=4)
fig.write_html(f"plot-{THEME}.html", include_plotlyjs="cdn")
