""" anyplot.ai
andrews-curves: Andrews Curves for Multivariate Data
Library: plotly 6.7.0 | Python 3.13.13
Quality: 85/100 | Updated: 2026-05-15
"""

import os

import numpy as np
import plotly.graph_objects as go
from sklearn.datasets import load_iris


THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
GRID = "rgba(26,26,23,0.10)" if THEME == "light" else "rgba(240,239,232,0.10)"

IMPRINT = ["#009E73", "#C475FD", "#4467A3"]
BRAND = IMPRINT[0]

# Data
iris = load_iris()
X = iris.data
y = iris.target
species_names = iris.target_names

# Normalize
X_normalized = (X - X.mean(axis=0)) / X.std(axis=0)

# Andrews curve transformation parameter
t = np.linspace(-np.pi, np.pi, 200)

# Plot
fig = go.Figure()

# Plot curves for each sample, colored by species
for species_idx in range(3):
    species_mask = y == species_idx
    X_species = X_normalized[species_mask]

    for i, x in enumerate(X_species):
        # Inline Andrews curve transformation
        n_features = len(x)
        curve = np.ones_like(t) * x[0] / np.sqrt(2)
        for j in range(1, n_features):
            freq = (j + 1) // 2
            if j % 2 == 1:
                curve += x[j] * np.sin(freq * t)
            else:
                curve += x[j] * np.cos(freq * t)

        fig.add_trace(
            go.Scatter(
                x=t,
                y=curve,
                mode="lines",
                line=dict(color=IMPRINT[species_idx], width=2),
                opacity=0.4,
                name=species_names[species_idx],
                legendgroup=species_names[species_idx],
                showlegend=(i == 0),
                hovertemplate=f"{species_names[species_idx]}<br>t: %{{x:.2f}}<br>f(t): %{{y:.2f}}<extra></extra>",
            )
        )

# Layout
fig.update_layout(
    title=dict(text="andrews-curves · plotly · anyplot.ai", font=dict(size=28, color=INK), x=0.5, xanchor="center"),
    xaxis=dict(
        title=dict(text="Parameter t (radians)", font=dict(size=22, color=INK)),
        tickfont=dict(size=18, color=INK_SOFT),
        gridcolor=GRID,
        gridwidth=0.5,
        zeroline=True,
        zerolinecolor=GRID,
        zerolinewidth=1,
        linecolor=INK_SOFT,
        range=[-np.pi, np.pi],
        tickvals=[-np.pi, -np.pi / 2, 0, np.pi / 2, np.pi],
        ticktext=["-π", "-π/2", "0", "π/2", "π"],
    ),
    yaxis=dict(
        title=dict(text="f(t) (normalized units)", font=dict(size=22, color=INK)),
        tickfont=dict(size=18, color=INK_SOFT),
        gridcolor=GRID,
        gridwidth=0.5,
        zeroline=True,
        zerolinecolor=GRID,
        zerolinewidth=1,
        linecolor=INK_SOFT,
    ),
    legend=dict(
        font=dict(size=16, color=INK_SOFT),
        x=0.98,
        y=0.98,
        xanchor="right",
        yanchor="top",
        bgcolor=ELEVATED_BG,
        bordercolor=INK_SOFT,
        borderwidth=1,
    ),
    margin=dict(l=120, r=80, t=100, b=100),
    plot_bgcolor=PAGE_BG,
    paper_bgcolor=PAGE_BG,
    font=dict(color=INK),
)

# Save
fig.write_image(f"plot-{THEME}.png", width=1600, height=900, scale=3)
fig.write_html(f"plot-{THEME}.html", include_plotlyjs="cdn")
