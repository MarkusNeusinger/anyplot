""" pyplots.ai
ternary-density: Ternary Density Plot
Library: plotnine 0.15.2 | Python 3.13.11
Quality: 91/100 | Created: 2026-01-11
"""

import numpy as np
import pandas as pd
from plotnine import (
    aes,
    coord_fixed,
    element_blank,
    element_text,
    geom_density_2d,
    geom_polygon,
    geom_segment,
    geom_text,
    geom_tile,
    ggplot,
    labs,
    scale_fill_cmap,
    theme,
    theme_void,
)
from scipy.stats import gaussian_kde


# Generate synthetic compositional data (sediment: sand/silt/clay)
np.random.seed(42)

# Create three clusters of compositions
# Cluster 1: Sandy sediments (high sand)
n1 = 300
sand1 = np.random.beta(5, 2, n1) * 60 + 35
silt1 = np.random.beta(2, 3, n1) * (100 - sand1) * 0.6
clay1 = 100 - sand1 - silt1

# Cluster 2: Silty sediments (high silt)
n2 = 250
silt2 = np.random.beta(5, 2, n2) * 50 + 40
sand2 = np.random.beta(2, 4, n2) * (100 - silt2) * 0.5
clay2 = 100 - sand2 - silt2

# Cluster 3: Clay-rich sediments (high clay)
n3 = 250
clay3 = np.random.beta(4, 2, n3) * 45 + 40
sand3 = np.random.beta(2, 5, n3) * (100 - clay3) * 0.4
silt3 = 100 - sand3 - clay3

# Combine all clusters
sand = np.concatenate([sand1, sand2, sand3])
silt = np.concatenate([silt1, silt2, silt3])
clay = np.concatenate([clay1, clay2, clay3])

# Ensure non-negative values and normalize to sum to 100
sand = np.clip(sand, 0, 100)
silt = np.clip(silt, 0, 100)
clay = np.clip(clay, 0, 100)
total = sand + silt + clay
sand = sand / total * 100
silt = silt / total * 100
clay = clay / total * 100

# Convert ternary to Cartesian coordinates
# Formula: x = 0.5 * (2*b + c) / total, y = (sqrt(3)/2) * c / total
# Where a=sand (bottom-left), b=silt (bottom-right), c=clay (top)
x_data = 0.5 * (2 * silt + clay) / 100
y_data = (np.sqrt(3) / 2) * clay / 100

# Compute KDE on the data points
points = np.vstack([x_data, y_data])
kde = gaussian_kde(points, bw_method="silverman")

# Create grid for density estimation
grid_resolution = 150
x_grid = np.linspace(0, 1, grid_resolution)
y_grid = np.linspace(0, np.sqrt(3) / 2, grid_resolution)
xx, yy = np.meshgrid(x_grid, y_grid)

# Evaluate KDE on grid
positions = np.vstack([xx.ravel(), yy.ravel()])
density = kde(positions).reshape(xx.shape)

# Create mask for valid ternary region (inside triangle)
# Convert grid points back to ternary to check bounds
# c = y * 2/sqrt(3), b = x - c/2, a = 1 - b - c
cc = yy * 2 / np.sqrt(3)
bb = xx - cc / 2
aa = 1 - bb - cc
mask = (aa >= -0.001) & (bb >= -0.001) & (cc >= -0.001) & (aa <= 1.001) & (bb <= 1.001) & (cc <= 1.001)

# Apply mask (set values outside triangle to NaN)
density_masked = np.where(mask, density, np.nan)

# Create DataFrame for density grid
density_df = pd.DataFrame({"x": xx.ravel(), "y": yy.ravel(), "density": density_masked.ravel()}).dropna()

# Triangle vertices for frame
vertices = pd.DataFrame({"x": [0, 1, 0.5, 0], "y": [0, 0, np.sqrt(3) / 2, 0]})

# Grid lines at 20% intervals
grid_lines = []
for pct in [0.2, 0.4, 0.6, 0.8]:
    # Lines parallel to bottom (constant clay)
    x1 = 0.5 * (2 * 0 + pct)
    y1 = (np.sqrt(3) / 2) * pct
    x2 = 0.5 * (2 * (1 - pct) + pct)
    y2 = (np.sqrt(3) / 2) * pct
    grid_lines.append({"x": x1, "y": y1, "xend": x2, "yend": y2})

    # Lines parallel to left side (constant silt)
    x1 = 0.5 * (2 * pct + (1 - pct))
    y1 = (np.sqrt(3) / 2) * (1 - pct)
    x2 = 0.5 * (2 * pct + 0)
    y2 = 0
    grid_lines.append({"x": x1, "y": y1, "xend": x2, "yend": y2})

    # Lines parallel to right side (constant sand)
    x1 = 0.5 * (2 * 0 + (1 - pct))
    y1 = (np.sqrt(3) / 2) * (1 - pct)
    x2 = 0.5 * (2 * (1 - pct) + 0)
    y2 = 0
    grid_lines.append({"x": x1, "y": y1, "xend": x2, "yend": y2})

grid_df = pd.DataFrame(grid_lines)

# Tick labels along edges
tick_labels = []
label_offset = 0.06
for pct in [0, 20, 40, 60, 80, 100]:
    frac = pct / 100
    # Sand axis (left edge going up)
    x = 0.5 * (2 * 0 + frac)
    y = (np.sqrt(3) / 2) * frac
    tick_labels.append({"x": x - label_offset, "y": y, "label": str(pct)})

    # Silt axis (bottom edge)
    x = 0.5 * (2 * frac + 0)
    y = 0
    tick_labels.append({"x": x, "y": y - label_offset * 0.8, "label": str(pct)})

    # Clay axis (right edge going up)
    x = 0.5 * (2 * (1 - frac) + frac)
    y = (np.sqrt(3) / 2) * frac
    tick_labels.append({"x": x + label_offset, "y": y, "label": str(pct)})

tick_df = pd.DataFrame(tick_labels)

# Vertex labels
vertex_labels = pd.DataFrame(
    {
        "x": [0 - 0.02, 1 + 0.02, 0.5],
        "y": [0 - 0.1, 0 - 0.1, np.sqrt(3) / 2 + 0.08],
        "label": ["Sand (%)", "Silt (%)", "Clay (%)"],
    }
)

# Build the plot
# Calculate tile size for proper coverage
tile_size = 1.0 / grid_resolution

plot = (
    ggplot()
    # Density heatmap using tiles
    + geom_tile(
        data=density_df,
        mapping=aes(x="x", y="y", fill="density"),
        width=tile_size * 1.1,
        height=tile_size * 1.1,
        alpha=0.85,
    )
    + scale_fill_cmap(cmap_name="viridis", name="Density")
    # Contour lines for key density levels using geom_density_2d
    + geom_density_2d(
        data=pd.DataFrame({"x": x_data, "y": y_data}),
        mapping=aes(x="x", y="y"),
        color="white",
        size=0.8,
        alpha=0.7,
        levels=6,
    )
    # Grid lines beneath density (already visible due to alpha)
    + geom_segment(
        data=grid_df, mapping=aes(x="x", y="y", xend="xend", yend="yend"), color="#ffffff", size=0.8, alpha=0.3
    )
    # Triangle frame on top
    + geom_polygon(data=vertices, mapping=aes(x="x", y="y"), fill=None, color="#306998", size=2.5)
    # Tick labels
    + geom_text(data=tick_df, mapping=aes(x="x", y="y", label="label"), size=14, color="#666666")
    # Vertex labels
    + geom_text(
        data=vertex_labels, mapping=aes(x="x", y="y", label="label"), size=18, fontweight="bold", color="#306998"
    )
    # Title and theme
    + labs(title="ternary-density · plotnine · pyplots.ai")
    + coord_fixed(ratio=1)
    + theme_void()
    + theme(
        figure_size=(12, 12),
        plot_title=element_text(size=28, ha="center", weight="bold"),
        plot_margin=0.02,
        legend_position="right",
        legend_title=element_text(size=18),
        legend_text=element_text(size=14),
        legend_key_size=40,
        legend_background=element_blank(),
    )
)

# Save
plot.save("plot.png", dpi=300, verbose=False)
