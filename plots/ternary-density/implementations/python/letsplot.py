""" pyplots.ai
ternary-density: Ternary Density Plot
Library: letsplot 4.8.2 | Python 3.13.11
Quality: 91/100 | Created: 2026-01-11
"""

import numpy as np
import pandas as pd
from lets_plot import (
    LetsPlot,
    aes,
    coord_fixed,
    element_blank,
    element_text,
    geom_path,
    geom_polygon,
    geom_segment,
    geom_text,
    ggplot,
    ggsave,
    ggsize,
    labs,
    scale_fill_viridis,
    theme,
)


LetsPlot.setup_html()

# Generate synthetic compositional data (sediment: sand/silt/clay)
np.random.seed(42)

# Create three clusters of compositions using Dirichlet distribution
# Cluster 1: Sandy sediments (high sand)
alpha1 = np.array([8, 2, 1])
comp1 = np.random.dirichlet(alpha1, 180) * 100

# Cluster 2: Silty sediments (high silt)
alpha2 = np.array([2, 7, 2])
comp2 = np.random.dirichlet(alpha2, 160) * 100

# Cluster 3: Clayey sediments (high clay)
alpha3 = np.array([1, 2, 8])
comp3 = np.random.dirichlet(alpha3, 160) * 100

# Combine all clusters
compositions = np.vstack([comp1, comp2, comp3])
sand = compositions[:, 0]
silt = compositions[:, 1]
clay = compositions[:, 2]

# Convert ternary to Cartesian coordinates
# Standard ternary: bottom-left = A (sand), bottom-right = B (silt), top = C (clay)
total = sand + silt + clay
b_norm = silt / total
c_norm = clay / total

# Cartesian transformation
x_data = 0.5 * (2 * b_norm + c_norm)
y_data = (np.sqrt(3) / 2) * c_norm

# Create density grid
grid_res = 100
x_grid = np.linspace(0, 1, grid_res)
y_grid = np.linspace(0, np.sqrt(3) / 2, grid_res)
X, Y = np.meshgrid(x_grid, y_grid)

# Compute 2D Gaussian KDE (Scott's rule for bandwidth)
n = len(x_data)
std_x = np.std(x_data)
std_y = np.std(y_data)
bw = n ** (-1.0 / 6)
bw_x = std_x * bw
bw_y = std_y * bw

Z = np.zeros_like(X)
for i in range(n):
    dx = (X - x_data[i]) / bw_x
    dy = (Y - y_data[i]) / bw_y
    Z += np.exp(-0.5 * (dx**2 + dy**2))
Z /= n * 2 * np.pi * bw_x * bw_y

# Mask points outside the triangle
# Triangle vertices: (0,0), (1,0), (0.5, sqrt(3)/2)
# Point inside if: y >= 0, y <= sqrt(3)*x, y <= sqrt(3)*(1-x)
sqrt3 = np.sqrt(3)
mask = (Y >= 0) & (Y <= sqrt3 * X + 1e-6) & (Y <= sqrt3 * (1 - X) + 1e-6)

# Create dataframe for density polygons
# Use slightly overlapping polygons to avoid gaps
polygon_data = []
poly_id = 0
dx = x_grid[1] - x_grid[0]
dy = y_grid[1] - y_grid[0]
overlap = 1.05  # Slight overlap to avoid gaps

for i in range(grid_res):
    for j in range(grid_res):
        if mask[i, j] and Z[i, j] > 0:
            cx, cy = X[i, j], Y[i, j]
            # Create small square polygon with slight overlap
            hdx = dx * overlap / 2
            hdy = dy * overlap / 2
            corners_x = [cx - hdx, cx + hdx, cx + hdx, cx - hdx, cx - hdx]
            corners_y = [cy - hdy, cy - hdy, cy + hdy, cy + hdy, cy - hdy]
            for k in range(5):
                polygon_data.append({"x": corners_x[k], "y": corners_y[k], "density": Z[i, j], "id": poly_id})
            poly_id += 1

df_polygons = pd.DataFrame(polygon_data)

# Create contour lines data at key density levels
# Find density range and pick meaningful levels
z_masked = Z.copy()
z_masked[~mask] = 0
z_min, z_max = z_masked[mask].min(), z_masked[mask].max()
contour_levels = [z_min + (z_max - z_min) * p for p in [0.25, 0.5, 0.75]]

# Extract contour paths using marching squares approach
contour_data = []
contour_id = 0
for level in contour_levels:
    for i in range(grid_res - 1):
        for j in range(grid_res - 1):
            # Check if contour crosses this cell
            corners = [Z[i, j], Z[i, j + 1], Z[i + 1, j + 1], Z[i + 1, j]]
            corners_mask = [mask[i, j], mask[i, j + 1], mask[i + 1, j + 1], mask[i + 1, j]]
            if not all(corners_mask):
                continue
            above = [c >= level for c in corners]
            if all(above) or not any(above):
                continue
            # Find intersection points on edges
            x0, x1 = x_grid[j], x_grid[j + 1]
            y0, y1 = y_grid[i], y_grid[i + 1]
            pts = []
            # Edge 0: bottom (i, j) -> (i, j+1)
            if above[0] != above[1]:
                t = (level - corners[0]) / (corners[1] - corners[0] + 1e-10)
                pts.append((x0 + t * (x1 - x0), y0))
            # Edge 1: right (i, j+1) -> (i+1, j+1)
            if above[1] != above[2]:
                t = (level - corners[1]) / (corners[2] - corners[1] + 1e-10)
                pts.append((x1, y0 + t * (y1 - y0)))
            # Edge 2: top (i+1, j+1) -> (i+1, j)
            if above[2] != above[3]:
                t = (level - corners[2]) / (corners[3] - corners[2] + 1e-10)
                pts.append((x1 - t * (x1 - x0), y1))
            # Edge 3: left (i+1, j) -> (i, j)
            if above[3] != above[0]:
                t = (level - corners[3]) / (corners[0] - corners[3] + 1e-10)
                pts.append((x0, y1 - t * (y1 - y0)))
            # Connect pairs of intersection points
            if len(pts) == 2:
                contour_data.append(
                    {"x": pts[0][0], "y": pts[0][1], "xend": pts[1][0], "yend": pts[1][1], "level": level}
                )
                contour_id += 1

df_contours = pd.DataFrame(contour_data) if contour_data else pd.DataFrame(columns=["x", "y", "xend", "yend", "level"])

# Create triangle outline data
tri_x = [0, 1, 0.5, 0]
tri_y = [0, 0, sqrt3 / 2, 0]
df_triangle = pd.DataFrame({"x": tri_x, "y": tri_y})

# Create grid lines data (only inside the triangle) - more prominent
# Triangle vertices: bottom-left (0,0), bottom-right (1,0), top (0.5, sqrt3/2)
grid_lines = []
for pct in [0.2, 0.4, 0.6, 0.8]:
    # Lines parallel to bottom edge (constant clay %, going from left edge to right edge)
    y_line = pct * sqrt3 / 2
    x_left = pct / 2
    x_right = 1 - pct / 2
    grid_lines.append({"x": x_left, "xend": x_right, "y": y_line, "yend": y_line})

    # Lines parallel to left edge (constant silt %)
    x_start = pct  # on bottom edge
    y_start = 0
    x_end = 1 - 0.5 * pct
    y_end = pct * sqrt3 / 2
    grid_lines.append({"x": x_start, "xend": x_end, "y": y_start, "yend": y_end})

    # Lines parallel to right edge (constant sand %)
    x_start = 1 - pct  # on bottom edge
    y_start = 0
    x_end = 0.5 * pct
    y_end = pct * sqrt3 / 2
    grid_lines.append({"x": x_start, "xend": x_end, "y": y_start, "yend": y_end})

df_grid = pd.DataFrame(grid_lines)

# Create vertex labels data
labels_data = pd.DataFrame(
    {"x": [-0.06, 1.06, 0.5], "y": [-0.05, -0.05, sqrt3 / 2 + 0.06], "label": ["Sand", "Silt", "Clay"]}
)

# Build the plot
plot = (
    ggplot()
    # Density heatmap using polygons
    + geom_polygon(aes(x="x", y="y", fill="density", group="id"), data=df_polygons, color=None, alpha=0.9)
    # Viridis color scale for density
    + scale_fill_viridis(name="Density", option="viridis")
    # Grid lines (more prominent - increased alpha and size)
    + geom_segment(aes(x="x", y="y", xend="xend", yend="yend"), data=df_grid, color="#555555", size=0.8, alpha=0.5)
    # Contour lines at key density levels (dashed white lines for visibility on viridis)
    + (
        geom_segment(
            aes(x="x", y="y", xend="xend", yend="yend"),
            data=df_contours,
            color="white",
            size=1.0,
            alpha=0.7,
            linetype="dashed",
        )
        if len(df_contours) > 0
        else geom_path(aes(x="x", y="y"), data=pd.DataFrame({"x": [], "y": []}))
    )
    # Triangle outline
    + geom_path(aes(x="x", y="y"), data=df_triangle, color="#306998", size=2)
    # Vertex labels
    + geom_text(aes(x="x", y="y", label="label"), data=labels_data, color="#306998", size=12, fontface="bold")
    # Title and styling
    + labs(title="Sediment Composition · ternary-density · letsplot · pyplots.ai", x="", y="")
    # Fixed aspect ratio to keep triangle equilateral
    + coord_fixed(ratio=1)
    # Theme for clean appearance
    + theme(
        plot_title=element_text(size=24, face="bold", color="#306998"),
        axis_title=element_blank(),
        axis_text=element_blank(),
        axis_ticks=element_blank(),
        axis_line=element_blank(),
        panel_grid=element_blank(),
        legend_title=element_text(size=16),
        legend_text=element_text(size=14),
    )
    # Size (will be scaled 3x on export to 4800x2700)
    + ggsize(1600, 900)
)

# Save PNG (scale 3x for 4800x2700 px)
ggsave(plot, "plot.png", path=".", scale=3)

# Save HTML for interactive viewing
ggsave(plot, "plot.html", path=".")
