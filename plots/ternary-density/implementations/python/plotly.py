""" anyplot.ai
ternary-density: Ternary Density Plot
Library: plotly 6.7.0 | Python 3.13.13
Quality: 85/100 | Updated: 2026-05-19
"""

import os

import numpy as np
import plotly.graph_objects as go
from scipy.stats import gaussian_kde


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
GRID = "rgba(26,26,23,0.25)" if THEME == "light" else "rgba(240,239,232,0.25)"

# Data — synthetic sediment composition (sand/silt/clay)
np.random.seed(42)
n_samples = 500

# Cluster 1: Sand-dominant samples (beaches/river channels)
cluster1_a = np.random.beta(8, 2, n_samples // 3) * 70 + 25
cluster1_b = np.random.beta(2, 5, n_samples // 3) * 40
cluster1_c = 100 - cluster1_a - cluster1_b
mask1 = cluster1_c >= 0
cluster1_a, cluster1_b, cluster1_c = cluster1_a[mask1], cluster1_b[mask1], cluster1_c[mask1]

# Cluster 2: Silt-dominant samples (floodplains/estuaries)
cluster2_b = np.random.beta(7, 2, n_samples // 3) * 55 + 35
cluster2_a = np.random.beta(2, 5, n_samples // 3) * 30
cluster2_c = 100 - cluster2_a - cluster2_b
mask2 = cluster2_c >= 0
cluster2_a, cluster2_b, cluster2_c = cluster2_a[mask2], cluster2_b[mask2], cluster2_c[mask2]

# Cluster 3: Clay-dominant mixed samples (deep lake sediments)
cluster3_c = np.random.beta(6, 2, n_samples // 3) * 50 + 30
cluster3_a = np.random.beta(2, 4, n_samples // 3) * 35
cluster3_b = 100 - cluster3_a - cluster3_c
mask3 = cluster3_b >= 0
cluster3_a, cluster3_b, cluster3_c = cluster3_a[mask3], cluster3_b[mask3], cluster3_c[mask3]

# Combine clusters
sand = np.concatenate([cluster1_a, cluster2_a, cluster3_a])
silt = np.concatenate([cluster1_b, cluster2_b, cluster3_b])
clay = np.concatenate([cluster1_c, cluster2_c, cluster3_c])

# Normalize to sum = 100
total = sand + silt + clay
sand = sand / total * 100
silt = silt / total * 100
clay = clay / total * 100

# Convert ternary → Cartesian for KDE
x_cart = 0.5 * (2 * silt + clay) / 100
y_cart = (np.sqrt(3) / 2) * clay / 100

# 2D kernel density estimation
coords = np.vstack([x_cart, y_cart])
kde = gaussian_kde(coords, bw_method="scott")

# Evaluation grid (Cartesian space)
grid_size = 100
x_grid = np.linspace(0, 1, grid_size)
y_grid = np.linspace(0, np.sqrt(3) / 2, grid_size)
xx, yy = np.meshgrid(x_grid, y_grid)
grid_coords = np.vstack([xx.ravel(), yy.ravel()])

density = kde(grid_coords).reshape(xx.shape)

# Mask outside the ternary triangle
inside_triangle = (yy >= 0) & (yy <= np.sqrt(3) * xx) & (yy <= np.sqrt(3) * (1 - xx))
density[~inside_triangle] = np.nan

# Back to ternary coordinates for plotting
clay_grid = yy * (2 / np.sqrt(3)) * 100
silt_grid = (xx - clay_grid / 200) * 100
sand_grid = 100 - silt_grid - clay_grid

# Plot
fig = go.Figure()

# Density layer — Viridis-colored scatter markers
valid_mask = inside_triangle & ~np.isnan(density)
a_flat = sand_grid[valid_mask]
b_flat = silt_grid[valid_mask]
c_flat = clay_grid[valid_mask]
d_flat = density[valid_mask]

fig.add_trace(
    go.Scatterternary(
        a=a_flat,
        b=b_flat,
        c=c_flat,
        mode="markers",
        marker={
            "size": 6,
            "color": d_flat,
            "colorscale": "Viridis",
            "showscale": True,
            "colorbar": {
                "title": {"text": "Density", "font": {"size": 20, "color": INK}},
                "tickfont": {"size": 16, "color": INK_SOFT},
                "len": 0.7,
                "thickness": 25,
                "x": 1.02,
                "bgcolor": ELEVATED_BG,
                "bordercolor": INK_SOFT,
                "borderwidth": 1,
            },
            "opacity": 0.85,
        },
        hovertemplate="Sand: %{a:.1f}%<br>Silt: %{b:.1f}%<br>Clay: %{c:.1f}%<extra></extra>",
        showlegend=False,
    )
)

# Contour lines at key density percentiles
contour_color = "rgba(255,255,255,0.85)" if THEME == "light" else "rgba(240,239,232,0.85)"
contour_levels = np.percentile(d_flat, [25, 50, 75, 90])
for level in contour_levels:
    level_mask = np.abs(density - level) < (np.nanmax(density) - np.nanmin(density)) * 0.02
    level_mask = level_mask & valid_mask
    if np.sum(level_mask) > 10:
        a_level = sand_grid[level_mask]
        b_level = silt_grid[level_mask]
        c_level = clay_grid[level_mask]

        x_level = 0.5 * (2 * b_level + c_level) / 100
        y_level = (np.sqrt(3) / 2) * c_level / 100
        cx, cy = np.mean(x_level), np.mean(y_level)
        angles = np.arctan2(y_level - cy, x_level - cx)
        sort_idx = np.argsort(angles)

        fig.add_trace(
            go.Scatterternary(
                a=np.append(a_level[sort_idx], a_level[sort_idx][0]),
                b=np.append(b_level[sort_idx], b_level[sort_idx][0]),
                c=np.append(c_level[sort_idx], c_level[sort_idx][0]),
                mode="lines",
                line={"color": contour_color, "width": 2.5},
                hoverinfo="skip",
                showlegend=False,
            )
        )

# Style
fig.update_layout(
    title={
        "text": "Sediment Composition Distribution · ternary-density · python · plotly · anyplot.ai",
        "font": {"size": 26, "color": INK},
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
            "title": {"text": "Sand (%)", "font": {"size": 22, "color": INK}},
            "tickfont": {"size": 16, "color": INK_SOFT},
            "tickangle": 0,
            "dtick": 20,
            "gridcolor": GRID,
            "linecolor": INK_SOFT,
            "linewidth": 2,
        },
        "baxis": {
            "title": {"text": "Silt (%)", "font": {"size": 22, "color": INK}},
            "tickfont": {"size": 16, "color": INK_SOFT},
            "tickangle": 45,
            "dtick": 20,
            "gridcolor": GRID,
            "linecolor": INK_SOFT,
            "linewidth": 2,
        },
        "caxis": {
            "title": {"text": "Clay (%)", "font": {"size": 22, "color": INK}},
            "tickfont": {"size": 16, "color": INK_SOFT},
            "tickangle": -45,
            "dtick": 20,
            "gridcolor": GRID,
            "linecolor": INK_SOFT,
            "linewidth": 2,
        },
    },
    template="none",
    margin={"l": 80, "r": 120, "t": 100, "b": 80},
)

# Save
fig.write_image(f"plot-{THEME}.png", width=1600, height=900, scale=3)
fig.write_html(f"plot-{THEME}.html", include_plotlyjs="cdn")
