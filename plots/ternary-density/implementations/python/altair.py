""" pyplots.ai
ternary-density: Ternary Density Plot
Library: altair 6.0.0 | Python 3.13.11
Quality: 91/100 | Created: 2026-01-11
"""

import altair as alt
import numpy as np
import pandas as pd
from scipy.stats import gaussian_kde


# Data - Generate clustered compositional data (sand/silt/clay for sediment analysis)
np.random.seed(42)
n_per_cluster = 400

# Cluster 1: Sandy sediment (high sand, low clay)
c1_sand = np.random.beta(12, 2, n_per_cluster) * 80 + 15  # 15-95% sand
c1_clay = np.random.beta(2, 8, n_per_cluster) * (100 - c1_sand) * 0.3
c1_silt = 100 - c1_sand - c1_clay

# Cluster 2: Silty sediment (high silt)
c2_silt = np.random.beta(10, 2, n_per_cluster) * 70 + 25  # 25-95% silt
c2_sand = np.random.beta(3, 6, n_per_cluster) * (100 - c2_silt) * 0.7
c2_clay = 100 - c2_silt - c2_sand

# Cluster 3: Clay-rich sediment (high clay)
c3_clay = np.random.beta(8, 3, n_per_cluster) * 60 + 30  # 30-90% clay
c3_sand = np.random.beta(2, 5, n_per_cluster) * (100 - c3_clay) * 0.5
c3_silt = 100 - c3_clay - c3_sand

# Combine all clusters
sand = np.concatenate([c1_sand, c2_sand, c3_sand])
silt = np.concatenate([c1_silt, c2_silt, c3_silt])
clay = np.concatenate([c1_clay, c2_clay, c3_clay])

# Clip and normalize to ensure valid compositions
sand = np.clip(sand, 0.1, 99.8)
silt = np.clip(silt, 0.1, 99.8)
clay = np.clip(clay, 0.1, 99.8)
total = sand + silt + clay
sand, silt, clay = sand / total * 100, silt / total * 100, clay / total * 100

# Convert ternary to Cartesian coordinates
# Triangle vertices: Sand=(0,0), Silt=(1,0), Clay=(0.5, sqrt(3)/2)
sqrt3_2 = np.sqrt(3) / 2
x_points = 0.5 * (2 * silt + clay) / 100
y_points = sqrt3_2 * clay / 100

# Create grid for density estimation
grid_res = 80
x_grid = np.linspace(0, 1, grid_res)
y_grid = np.linspace(0, sqrt3_2, grid_res)
xx, yy = np.meshgrid(x_grid, y_grid)

# Perform KDE on the transformed coordinates
coords = np.vstack([x_points, y_points])
kde = gaussian_kde(coords, bw_method="scott")
density = kde(np.vstack([xx.ravel(), yy.ravel()])).reshape(xx.shape)

# Create mask for points inside the triangle (half-plane method)
# Triangle: A=(0,0), B=(1,0), C=(0.5, sqrt3_2)
margin = 0.005
inside_bottom = yy >= -margin
inside_right = np.sqrt(3) * xx + yy <= np.sqrt(3) + margin
inside_left = yy - np.sqrt(3) * xx <= margin
mask = inside_bottom & inside_right & inside_left

# Create DataFrame for heatmap (only points inside triangle)
density_data = []
for i in range(grid_res):
    for j in range(grid_res):
        if mask[i, j]:
            density_data.append({"x": xx[i, j], "y": yy[i, j], "density": density[i, j]})
density_df = pd.DataFrame(density_data)

# Triangle outline vertices
triangle_df = pd.DataFrame({"x": [0, 1, 0.5, 0], "y": [0, 0, sqrt3_2, 0], "order": [0, 1, 2, 3]})

# Grid lines for ternary diagram (all lines stay inside triangle)
grid_lines = []
n_lines = 10
for i in range(1, n_lines):
    frac = i / n_lines
    # Horizontal lines (constant clay %)
    y_val = frac * sqrt3_2
    x_left = y_val / np.sqrt(3)
    x_right = 1 - y_val / np.sqrt(3)
    grid_lines.extend(
        [{"x": x_left, "y": y_val, "line": f"h{i}", "o": 0}, {"x": x_right, "y": y_val, "line": f"h{i}", "o": 1}]
    )
    # Lines from bottom to left edge (constant sand %)
    x_bottom = frac
    x_top = frac / 2
    y_top = frac * sqrt3_2
    grid_lines.extend(
        [{"x": x_bottom, "y": 0, "line": f"l{i}", "o": 0}, {"x": x_top, "y": y_top, "line": f"l{i}", "o": 1}]
    )
    # Lines from bottom to right edge (constant silt %)
    x_bottom = 1 - frac
    x_top = 1 - frac / 2
    y_top = frac * sqrt3_2
    grid_lines.extend(
        [{"x": x_bottom, "y": 0, "line": f"r{i}", "o": 0}, {"x": x_top, "y": y_top, "line": f"r{i}", "o": 1}]
    )
grid_df = pd.DataFrame(grid_lines)

# Vertex labels
labels_df = pd.DataFrame(
    {"x": [-0.02, 1.02, 0.5], "y": [-0.05, -0.05, sqrt3_2 + 0.05], "label": ["Sand (%)", "Silt (%)", "Clay (%)"]}
)

# Shared axis config (no visible axes for ternary diagram)
x_enc = alt.X("x:Q", scale=alt.Scale(domain=[-0.12, 1.12]), axis=None)
y_enc = alt.Y("y:Q", scale=alt.Scale(domain=[-0.12, sqrt3_2 + 0.12]), axis=None)

# Density heatmap layer
heatmap = (
    alt.Chart(density_df)
    .mark_square(size=250, opacity=0.9)
    .encode(
        x=x_enc,
        y=y_enc,
        color=alt.Color(
            "density:Q",
            scale=alt.Scale(scheme="viridis"),
            legend=alt.Legend(title="Density", titleFontSize=20, labelFontSize=16, orient="right"),
        ),
    )
)

# Triangle outline
triangle = alt.Chart(triangle_df).mark_line(color="#222", strokeWidth=3).encode(x=x_enc, y=y_enc, order="order:O")

# Grid lines
grid = (
    alt.Chart(grid_df)
    .mark_line(color="#888", strokeWidth=1, opacity=0.4)
    .encode(x=x_enc, y=y_enc, detail="line:N", order="o:O")
)

# Vertex labels
labels = (
    alt.Chart(labels_df)
    .mark_text(fontSize=24, fontWeight="bold", color="#222")
    .encode(x=x_enc, y=y_enc, text="label:N")
)

# Combine layers
chart = (
    alt.layer(grid, heatmap, triangle, labels)
    .properties(
        width=1600,
        height=900,
        title=alt.Title("Sediment Composition · ternary-density · altair · pyplots.ai", fontSize=28),
    )
    .configure_view(strokeWidth=0)
)

# Save
chart.save("plot.png", scale_factor=3.0)
chart.save("plot.html")
