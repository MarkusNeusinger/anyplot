""" anyplot.ai
ternary-density: Ternary Density Plot
Library: plotly 7.1.0 | Python 3.14.10
Quality: 81/100 | Updated: 2026-11-22
"""

import os
import sys


# Remove the script directory from sys.path so that sibling implementations
# (e.g. matplotlib.py) do not shadow installed packages.
_script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path = [p for p in sys.path if os.path.abspath(p or os.getcwd()) != _script_dir]

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from scipy.stats import gaussian_kde


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
GRID = "rgba(250,248,241,0.55)"  # drawn over the density fill, so light in both themes

# Imprint palette: all eight positions in canonical order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]
# Imprint sequential colormap (single-polarity density)
IMPRINT_SEQ = [[0.0, IMPRINT_PALETTE[0]], [1.0, IMPRINT_PALETTE[2]]]

# Columns: set these to your table's column names
SAND = "Sand (%)"  # role: component_a
SILT = "Silt (%)"  # role: component_b
CLAY = "Clay (%)"  # role: component_c

# Data: replace this block with your own table, for example df = pd.read_csv("sediment.csv")
# Synthetic sediment composition: beach/channel, floodplain and deep-lake samples
rng = np.random.default_rng(42)
n_cluster = 500 // 3
sand_1 = rng.beta(8, 2, n_cluster) * 70 + 25
silt_1 = rng.beta(2, 5, n_cluster) * 40
silt_2 = rng.beta(7, 2, n_cluster) * 55 + 35
sand_2 = rng.beta(2, 5, n_cluster) * 30
clay_3 = rng.beta(6, 2, n_cluster) * 50 + 30
sand_3 = rng.beta(2, 4, n_cluster) * 35
raw = pd.DataFrame(
    {
        SAND: np.concatenate([sand_1, sand_2, sand_3]),
        SILT: np.concatenate([silt_1, silt_2, 100 - sand_3 - clay_3]),
        CLAY: np.concatenate([100 - sand_1 - silt_1, 100 - sand_2 - silt_2, clay_3]),
    }
)
# Keep physically valid samples and normalise each row to sum to 100
raw = raw[(raw >= 0).all(axis=1)]
df = raw.div(raw.sum(axis=1), axis=0).mul(100).reset_index(drop=True)

# Plot
components = [SAND, SILT, CLAY]
sqrt3 = np.sqrt(3)

# Ternary -> Cartesian so the KDE respects the triangle geometry
complete = df[components].dropna()
share = complete.div(complete.sum(axis=1), axis=0).to_numpy()
points = np.vstack([share[:, 1] + share[:, 2] / 2, share[:, 2] * sqrt3 / 2])
kde = gaussian_kde(points, bw_method="scott")

# Regular grid in Cartesian space, evaluated by the KDE (100 x 100 cells)
grid_size = 101
xs = np.linspace(0, 1, grid_size)
ys = np.linspace(0, sqrt3 / 2, grid_size)
xx, yy = np.meshgrid(xs, ys)
inside = (yy <= sqrt3 * xx) & (yy <= sqrt3 * (1 - xx))
density = kde(np.vstack([xx.ravel(), yy.ravel()])).reshape(xx.shape)
density = np.where(inside, density, np.nan)


def to_ternary(x, y):
    """Cartesian triangle coordinates -> (sand, silt, clay) in the data's own total."""
    total = df[components].sum(axis=1).mean()
    frac_c = y * 2 / sqrt3
    frac_b = x - frac_c / 2
    return (1 - frac_b - frac_c) * total, frac_b * total, frac_c * total


fig = go.Figure()

# Density surface: a lattice of overlapping markers fills the triangle without gaps
a_fill, b_fill, c_fill = to_ternary(xx[inside], yy[inside])
fig.add_trace(
    go.Scatterternary(
        a=a_fill,
        b=b_fill,
        c=c_fill,
        mode="markers",
        marker={
            "size": 5,
            "symbol": "square",
            "color": density[inside],
            "colorscale": IMPRINT_SEQ,
            "showscale": True,
            "colorbar": {
                "title": {"text": "Relative density", "font": {"size": 12, "color": INK}},
                "tickfont": {"size": 11, "color": INK_SOFT},
                "tickvals": [np.nanmin(density), np.nanmax(density)],
                "ticktext": ["low", "high"],
                "len": 0.7,
                "thickness": 14,
                "bgcolor": ELEVATED_BG,
                "bordercolor": INK_SOFT,
                "borderwidth": 1,
            },
        },
        hovertemplate="%{a:.1f} / %{b:.1f} / %{c:.1f}<extra></extra>",
        showlegend=False,
    )
)

# Ternary grid drawn over the fill (plotly paints its own grid beneath the markers)
total = df[components].sum(axis=1).mean()
for level in np.arange(0.2, 1.0, 0.2):
    for i in range(3):
        j, k = (i + 1) % 3, (i + 2) % 3
        ends = np.zeros((2, 3))
        ends[:, i] = level
        ends[0, j], ends[1, k] = 1 - level, 1 - level
        fig.add_trace(
            go.Scatterternary(
                a=ends[:, 0] * total,
                b=ends[:, 1] * total,
                c=ends[:, 2] * total,
                mode="lines",
                line={"color": GRID, "width": 1},
                hoverinfo="skip",
                showlegend=False,
            )
        )

# Style
fig.update_layout(
    title={
        "text": "Sediment Composition Distribution · ternary-density · python · plotly · anyplot.ai",
        "font": {"size": 15, "color": INK},
        "x": 0.5,
        "xanchor": "center",
    },
    paper_bgcolor=PAGE_BG,
    plot_bgcolor=PAGE_BG,
    font={"color": INK},
    ternary={
        "sum": 100,
        "bgcolor": PAGE_BG,
        "aaxis": {
            "title": {"text": SAND, "font": {"size": 13, "color": INK}},
            "tickfont": {"size": 11, "color": INK_SOFT},
            "dtick": 20,
            "gridcolor": GRID,
            "layer": "above traces",
            "linecolor": INK_SOFT,
            "linewidth": 1.5,
        },
        "baxis": {
            "title": {"text": SILT, "font": {"size": 13, "color": INK}},
            "tickfont": {"size": 11, "color": INK_SOFT},
            "tickangle": 45,
            "dtick": 20,
            "gridcolor": GRID,
            "layer": "above traces",
            "linecolor": INK_SOFT,
            "linewidth": 1.5,
        },
        "caxis": {
            "title": {"text": CLAY, "font": {"size": 13, "color": INK}},
            "tickfont": {"size": 11, "color": INK_SOFT},
            "tickangle": -45,
            "dtick": 20,
            "gridcolor": GRID,
            "layer": "above traces",
            "linecolor": INK_SOFT,
            "linewidth": 1.5,
        },
    },
    template="none",
    autosize=False,
    margin={"l": 60, "r": 60, "t": 60, "b": 50},
)

# Save
fig.write_image(f"plot-{THEME}.png", width=800, height=450, scale=4)
fig.write_html(f"plot-{THEME}.html", include_plotlyjs="cdn")
