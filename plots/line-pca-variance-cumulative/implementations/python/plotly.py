"""anyplot.ai
line-pca-variance-cumulative: Cumulative Explained Variance for PCA Component Selection
Library: plotly | Python 3.13
Quality: pending | Updated: 2026-05-29
"""

import sys


sys.path = sys.path[1:]  # prevent this file from shadowing the installed plotly package

import os

import numpy as np
import plotly.graph_objects as go
from sklearn.datasets import load_wine
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler


# Theme tokens — Imprint palette chrome
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
GRID = "rgba(26,26,23,0.15)" if THEME == "light" else "rgba(240,239,232,0.15)"

# Imprint categorical palette — data colors are theme-independent
BRAND = "#009E73"  # position 1 — cumulative variance line (always first series)
BAR_COLOR = "#4467A3"  # position 3 — individual variance bars
ELBOW_COLOR = "#C475FD"  # position 2 — elbow marker accent
AMBER = "#DDCC77"  # semantic anchor — 90% warning threshold
RED = "#AE3030"  # position 5 — 95% critical threshold

# Data — PCA on Wine dataset
wine = load_wine()
X_scaled = StandardScaler().fit_transform(wine.data)
pca = PCA().fit(X_scaled)

explained_variance = pca.explained_variance_ratio_
cumulative_variance = np.cumsum(explained_variance) * 100
n_components = np.arange(1, len(explained_variance) + 1)

# Threshold crossings
threshold_90_idx = int(np.argmax(cumulative_variance >= 90))
threshold_95_idx = int(np.argmax(cumulative_variance >= 95))
threshold_90_comp = threshold_90_idx + 1
threshold_95_comp = threshold_95_idx + 1

# Elbow: first component where marginal gain drops below mean gain
individual_pct = explained_variance * 100
elbow_idx = int(np.argmax(individual_pct < individual_pct.mean()))
elbow_comp = elbow_idx + 1
elbow_var = float(cumulative_variance[elbow_idx])

title = "line-pca-variance-cumulative · python · plotly · anyplot.ai"

# Plot
fig = go.Figure()

# Individual variance bars (secondary context)
bar_fill = "rgba(68,103,163,0.30)"
bar_edge = "rgba(68,103,163,0.55)"
fig.add_trace(
    go.Bar(
        x=n_components,
        y=explained_variance * 100,
        marker={"color": bar_fill, "line": {"width": 1, "color": bar_edge}},
        name="Individual variance",
        hovertemplate="PC%{x}<br>Individual: %{y:.1f}%<extra></extra>",
    )
)

# Cumulative variance line — primary series (Imprint position 1)
fig.add_trace(
    go.Scatter(
        x=n_components,
        y=cumulative_variance,
        mode="lines+markers",
        line={"color": BRAND, "width": 4, "shape": "spline"},
        marker={"size": 12, "color": BRAND, "line": {"width": 2, "color": PAGE_BG}},
        name="Cumulative variance",
        hovertemplate="PC%{x}<br>Cumulative: %{y:.1f}%<extra></extra>",
    )
)

# Dummy traces so threshold lines appear in the legend
fig.add_trace(
    go.Scatter(
        x=[None], y=[None], mode="lines", line={"color": AMBER, "width": 2.5, "dash": "dash"}, name="90% threshold"
    )
)
fig.add_trace(
    go.Scatter(
        x=[None], y=[None], mode="lines", line={"color": RED, "width": 2.5, "dash": "dash"}, name="95% threshold"
    )
)

# Horizontal threshold lines — placed on opposite sides to avoid label crowding
fig.add_hline(
    y=90,
    line_dash="dash",
    line_color=AMBER,
    line_width=2.5,
    annotation_text="90%",
    annotation_position="top right",
    annotation_font={"size": 14, "color": AMBER},
)
fig.add_hline(
    y=95,
    line_dash="dash",
    line_color=RED,
    line_width=2.5,
    annotation_text="95%",
    annotation_position="top left",
    annotation_font={"size": 14, "color": RED},
)

# Vertical drop lines from threshold crossings to x-axis
fig.add_shape(
    type="line",
    x0=threshold_90_comp,
    x1=threshold_90_comp,
    y0=0,
    y1=90,
    line={"color": AMBER, "width": 1.5, "dash": "dot"},
)
fig.add_shape(
    type="line",
    x0=threshold_95_comp,
    x1=threshold_95_comp,
    y0=0,
    y1=95,
    line={"color": RED, "width": 1.5, "dash": "dot"},
)

# Elbow marker — diamond outline for visual distinction
fig.add_trace(
    go.Scatter(
        x=[elbow_comp],
        y=[elbow_var],
        mode="markers",
        marker={"size": 22, "color": ELEVATED_BG, "line": {"width": 3, "color": ELBOW_COLOR}, "symbol": "diamond"},
        showlegend=False,
        hovertemplate=f"Elbow: PC{elbow_comp}<br>Cumulative: {elbow_var:.1f}%<extra></extra>",
    )
)

# Elbow annotation with arrow
fig.add_annotation(
    x=elbow_comp,
    y=elbow_var,
    text=f"<b>Elbow</b> — PC{elbow_comp}<br>{elbow_var:.0f}% variance",
    showarrow=True,
    arrowhead=2,
    arrowsize=1.4,
    arrowwidth=1.8,
    arrowcolor=ELBOW_COLOR,
    ax=-65,
    ay=-55,
    font={"size": 12, "color": ELBOW_COLOR},
    bgcolor=ELEVATED_BG,
    bordercolor=ELBOW_COLOR,
    borderwidth=1.5,
    borderpad=5,
)

# Layout
fig.update_layout(
    autosize=False,
    paper_bgcolor=PAGE_BG,
    plot_bgcolor=PAGE_BG,
    title={"text": title, "font": {"size": 16, "color": INK}, "x": 0.5, "xanchor": "center"},
    xaxis={
        "title": {"text": "Principal Component", "font": {"size": 12, "color": INK}},
        "tickfont": {"size": 10, "color": INK_SOFT},
        "tickmode": "linear",
        "tick0": 1,
        "dtick": 1,
        "showgrid": False,
        "zeroline": False,
        "showline": True,
        "linewidth": 1,
        "linecolor": INK_SOFT,
    },
    yaxis={
        "title": {"text": "Explained Variance (%)", "font": {"size": 12, "color": INK}},
        "tickfont": {"size": 10, "color": INK_SOFT},
        "range": [0, 105],
        "showgrid": True,
        "gridwidth": 1,
        "gridcolor": GRID,
        "zeroline": False,
        "showline": True,
        "linewidth": 1,
        "linecolor": INK_SOFT,
    },
    legend={
        "bgcolor": ELEVATED_BG,
        "bordercolor": INK_SOFT,
        "borderwidth": 1,
        "font": {"size": 10, "color": INK_SOFT},
        "x": 0.02,
        "y": 0.40,
    },
    font={"color": INK},
    margin={"t": 80, "b": 60, "l": 80, "r": 40},
    bargap=0.4,
)

# Save
fig.write_image(f"plot-{THEME}.png", width=800, height=450, scale=4)
fig.write_html(f"plot-{THEME}.html", include_plotlyjs="cdn")
