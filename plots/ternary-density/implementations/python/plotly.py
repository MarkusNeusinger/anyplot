""" pyplots.ai
ternary-density: Ternary Density Plot
Library: plotly 6.5.1 | Python 3.13.11
Quality: 91/100 | Created: 2026-01-11
"""

import numpy as np
import plotly.graph_objects as go
from scipy.stats import gaussian_kde


# Generate synthetic sediment composition data (sand/silt/clay)
np.random.seed(42)

# Create clustered compositional data with 3 distinct modes
n_samples = 500

# Cluster 1: Sand-dominant samples (common in beaches/rivers)
cluster1_a = np.random.beta(8, 2, n_samples // 3) * 70 + 25  # Sand: 25-95%
cluster1_b = np.random.beta(2, 5, n_samples // 3) * 40  # Silt: 0-40%
cluster1_c = 100 - cluster1_a - cluster1_b
mask1 = cluster1_c >= 0
cluster1_a, cluster1_b, cluster1_c = cluster1_a[mask1], cluster1_b[mask1], cluster1_c[mask1]

# Cluster 2: Silt-dominant samples (common in floodplains)
cluster2_b = np.random.beta(6, 2, n_samples // 3) * 60 + 30  # Silt: 30-90%
cluster2_a = np.random.beta(2, 4, n_samples // 3) * 35  # Sand: 0-35%
cluster2_c = 100 - cluster2_a - cluster2_b
mask2 = cluster2_c >= 0
cluster2_a, cluster2_b, cluster2_c = cluster2_a[mask2], cluster2_b[mask2], cluster2_c[mask2]

# Cluster 3: Mixed samples (balanced composition)
cluster3_a = np.random.beta(3, 3, n_samples // 3) * 50 + 20  # Sand: 20-70%
cluster3_b = np.random.beta(3, 3, n_samples // 3) * 50 + 10  # Silt: 10-60%
cluster3_c = 100 - cluster3_a - cluster3_b
mask3 = cluster3_c >= 0
cluster3_a, cluster3_b, cluster3_c = cluster3_a[mask3], cluster3_b[mask3], cluster3_c[mask3]

# Combine all clusters
sand = np.concatenate([cluster1_a, cluster2_a, cluster3_a])
silt = np.concatenate([cluster1_b, cluster2_b, cluster3_b])
clay = np.concatenate([cluster1_c, cluster2_c, cluster3_c])

# Normalize to ensure sum = 100
total = sand + silt + clay
sand = sand / total * 100
silt = silt / total * 100
clay = clay / total * 100

# Convert ternary coordinates to Cartesian for KDE
# Using standard ternary to Cartesian transformation
x_cart = 0.5 * (2 * silt + clay) / 100
y_cart = (np.sqrt(3) / 2) * clay / 100

# Perform 2D kernel density estimation
coords = np.vstack([x_cart, y_cart])
kde = gaussian_kde(coords, bw_method="scott")

# Create grid for density estimation (in Cartesian space)
grid_size = 100
x_grid = np.linspace(0, 1, grid_size)
y_grid = np.linspace(0, np.sqrt(3) / 2, grid_size)
xx, yy = np.meshgrid(x_grid, y_grid)
grid_coords = np.vstack([xx.ravel(), yy.ravel()])

# Evaluate KDE on grid
density = kde(grid_coords).reshape(xx.shape)

# Mask points outside the triangle
# Point is inside triangle if: y >= 0, y <= sqrt(3)*x, y <= sqrt(3)*(1-x)
inside_triangle = (yy >= 0) & (yy <= np.sqrt(3) * xx) & (yy <= np.sqrt(3) * (1 - xx))
density[~inside_triangle] = np.nan

# Convert grid back to ternary coordinates for plotting
# Inverse transformation: clay = y * 2/sqrt(3) * 100, silt = (x - clay/200) * 100
clay_grid = yy * (2 / np.sqrt(3)) * 100
silt_grid = (xx - clay_grid / 200) * 100
sand_grid = 100 - silt_grid - clay_grid

# Create figure with ternary axes
fig = go.Figure()

# Add density heatmap using scatterternary with colored markers
valid_mask = inside_triangle & ~np.isnan(density)
a_flat = sand_grid[valid_mask]
b_flat = silt_grid[valid_mask]
c_flat = clay_grid[valid_mask]
d_flat = density[valid_mask]

# Add filled contours as a scatter ternary with colorscale
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
                "title": {"text": "Density", "font": {"size": 20}},
                "tickfont": {"size": 16},
                "len": 0.7,
                "thickness": 25,
                "x": 1.02,
            },
            "opacity": 0.8,
        },
        hovertemplate="Sand: %{a:.1f}%<br>Silt: %{b:.1f}%<br>Clay: %{c:.1f}%<extra></extra>",
        showlegend=False,
    )
)

# Add contour lines for key density levels
contour_levels = np.percentile(d_flat, [25, 50, 75, 90])
for level in contour_levels:
    # Find points near this density level
    level_mask = np.abs(density - level) < (np.nanmax(density) - np.nanmin(density)) * 0.02
    level_mask = level_mask & valid_mask
    if np.sum(level_mask) > 10:
        # Sort points by angle from centroid for contour line
        a_level = sand_grid[level_mask]
        b_level = silt_grid[level_mask]
        c_level = clay_grid[level_mask]

        # Convert to Cartesian, compute angles, sort
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
                line={"color": "rgba(255, 255, 255, 0.6)", "width": 2},
                hoverinfo="skip",
                showlegend=False,
            )
        )

# Update layout for ternary plot
fig.update_layout(
    title={
        "text": "Sediment Composition Distribution · ternary-density · plotly · pyplots.ai",
        "font": {"size": 28},
        "x": 0.5,
        "xanchor": "center",
    },
    ternary={
        "sum": 100,
        "aaxis": {
            "title": {"text": "Sand (%)", "font": {"size": 22}},
            "tickfont": {"size": 16},
            "tickangle": 0,
            "dtick": 20,
            "gridcolor": "rgba(0, 0, 0, 0.15)",
            "linewidth": 2,
        },
        "baxis": {
            "title": {"text": "Silt (%)", "font": {"size": 22}},
            "tickfont": {"size": 16},
            "tickangle": 45,
            "dtick": 20,
            "gridcolor": "rgba(0, 0, 0, 0.15)",
            "linewidth": 2,
        },
        "caxis": {
            "title": {"text": "Clay (%)", "font": {"size": 22}},
            "tickfont": {"size": 16},
            "tickangle": -45,
            "dtick": 20,
            "gridcolor": "rgba(0, 0, 0, 0.15)",
            "linewidth": 2,
        },
        "bgcolor": "rgba(255, 255, 255, 1)",
    },
    template="plotly_white",
    margin={"l": 80, "r": 120, "t": 100, "b": 80},
)

# Save outputs
fig.write_image("plot.png", width=1600, height=900, scale=3)
fig.write_html("plot.html", include_plotlyjs="cdn")
