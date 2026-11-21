"""anyplot.ai
contour-decision-boundary: Decision Boundary Classifier Visualization
Library: plotly 6.7.0 | Python 3.13.13
Quality: pending | Updated: 2026-05-16
"""

import os

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from sklearn.datasets import make_moons
from sklearn.neighbors import KNeighborsClassifier
from sklearn.preprocessing import StandardScaler


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
GRID = "rgba(26,26,23,0.10)" if THEME == "light" else "rgba(240,239,232,0.10)"

# Imprint palette: all eight positions, one per class in order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Constants
MESH_SIZE = 200  # grid points per axis for the prediction mesh
N_NEIGHBORS = 15  # classifier smoothness
SYMBOLS = ["circle", "diamond", "square", "triangle-up"]  # one marker shape per class

# Columns: set these to your table's column names
X1 = "Feature 1 (standardized)"  # role: X1
X2 = "Feature 2 (standardized)"  # role: X2
CLASS = "Class"  # role: y

# Data: replace this block with your own table, for example df = pd.read_csv("points.csv")
features, labels = make_moons(n_samples=200, noise=0.25, random_state=42)
features = StandardScaler().fit_transform(features)
df = pd.DataFrame({X1: features[:, 0], X2: features[:, 1], CLASS: labels})

# Plot: reads only df and the constants above
df = df.dropna(subset=[X1, X2, CLASS])
classes = sorted(df[CLASS].unique())
clf = KNeighborsClassifier(n_neighbors=N_NEIGHBORS).fit(df[[X1, X2]].to_numpy(), df[CLASS])

# Prediction mesh covering the data with a margin
gx = np.linspace(df[X1].min() - 0.5, df[X1].max() + 0.5, MESH_SIZE)
gy = np.linspace(df[X2].min() - 0.5, df[X2].max() + 0.5, MESH_SIZE)
xx, yy = np.meshgrid(gx, gy)
proba = clf.predict_proba(np.c_[xx.ravel(), yy.ravel()])[:, -1].reshape(xx.shape)

fig = go.Figure()

# Filled probability regions, translucent so the points stay the strongest marks
fig.add_trace(
    go.Contour(
        x=gx,
        y=gy,
        z=proba,
        colorscale=[[0, IMPRINT_PALETTE[0]], [1, IMPRINT_PALETTE[1]]],
        opacity=0.4,
        showscale=True,
        colorbar=dict(
            title=dict(text=f"P({CLASS} = {classes[-1]})", font=dict(size=12, color=INK)),
            tickfont=dict(size=10, color=INK_SOFT),
            len=0.7,
            thickness=14,
            outlinewidth=0,
        ),
        contours=dict(showlines=False),
        hovertemplate=f"{X1}: %{{x:.2f}}<br>{X2}: %{{y:.2f}}<br>Probability: %{{z:.2f}}<extra></extra>",
        showlegend=False,
    )
)

# Decision boundary where the predicted probability is 0.5
fig.add_trace(
    go.Contour(
        x=gx,
        y=gy,
        z=proba,
        showscale=False,
        contours=dict(start=0.5, end=0.5, size=0.1, coloring="lines", showlabels=False),
        line=dict(color=INK_SOFT, width=2, dash="dash"),
        hoverinfo="skip",
        showlegend=False,
    )
)

# Training points at their true class, outlined so they stay visible on every region
for i, cls in enumerate(classes):
    rows = df[df[CLASS] == cls]
    fig.add_trace(
        go.Scatter(
            x=rows[X1],
            y=rows[X2],
            mode="markers",
            marker=dict(
                size=9,
                color=IMPRINT_PALETTE[i % len(IMPRINT_PALETTE)],
                symbol=SYMBOLS[i % len(SYMBOLS)],
                line=dict(color=PAGE_BG, width=1),
            ),
            name=f"{CLASS} {cls}",
            hovertemplate=f"{X1}: %{{x:.2f}}<br>{X2}: %{{y:.2f}}<br>{CLASS}: {cls}<extra></extra>",
        )
    )

fig.update_layout(
    autosize=False,
    title=dict(
        text="contour-decision-boundary · python · plotly · anyplot.ai",
        font=dict(size=16, color=INK),
        x=0.5,
        xanchor="center",
    ),
    xaxis=dict(
        title=dict(text=X1, font=dict(size=12, color=INK)),
        tickfont=dict(size=10, color=INK_SOFT),
        showgrid=True,
        gridwidth=1,
        gridcolor=GRID,
        zeroline=False,
        linecolor=INK_SOFT,
        linewidth=1,
    ),
    yaxis=dict(
        title=dict(text=X2, font=dict(size=12, color=INK)),
        tickfont=dict(size=10, color=INK_SOFT),
        showgrid=True,
        gridwidth=1,
        gridcolor=GRID,
        zeroline=False,
        linecolor=INK_SOFT,
        linewidth=1,
    ),
    paper_bgcolor=PAGE_BG,
    plot_bgcolor=PAGE_BG,
    font=dict(color=INK),
    legend=dict(
        font=dict(size=10, color=INK_SOFT),
        x=0.02,
        y=0.98,
        xanchor="left",
        yanchor="top",
        bgcolor=ELEVATED_BG,
        bordercolor=INK_SOFT,
        borderwidth=1,
    ),
    margin=dict(l=70, r=40, t=60, b=55),
    hovermode="closest",
)

fig.write_image(f"plot-{THEME}.png", width=800, height=450, scale=4)
fig.write_html(f"plot-{THEME}.html", include_plotlyjs="cdn")
