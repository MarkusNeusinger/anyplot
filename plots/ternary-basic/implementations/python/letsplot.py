""" pyplots.ai
ternary-basic: Basic Ternary Plot
Library: letsplot 4.8.2 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-24
"""

import numpy as np
import pandas as pd
from lets_plot import (
    LetsPlot,
    aes,
    element_blank,
    element_text,
    geom_point,
    geom_polygon,
    geom_segment,
    geom_text,
    ggplot,
    ggsave,
    ggsize,
    labs,
    scale_color_manual,
    theme,
)


LetsPlot.setup_html()

# Data: Soil composition samples (Sand, Silt, Clay)
np.random.seed(42)

# Generate realistic soil composition data in different regions
samples = []
soil_types = []

# Sandy soils (high sand)
for _ in range(20):
    sand = np.random.uniform(60, 90)
    remaining = 100 - sand
    silt = np.random.uniform(0, remaining)
    clay = remaining - silt
    samples.append((sand, silt, clay))
    soil_types.append("Sandy")

# Silty soils (high silt)
for _ in range(20):
    silt = np.random.uniform(50, 80)
    remaining = 100 - silt
    sand = np.random.uniform(0, remaining)
    clay = remaining - sand
    samples.append((sand, silt, clay))
    soil_types.append("Silty")

# Clay soils (high clay)
for _ in range(20):
    clay = np.random.uniform(40, 70)
    remaining = 100 - clay
    sand = np.random.uniform(0, remaining)
    silt = remaining - sand
    samples.append((sand, silt, clay))
    soil_types.append("Clayey")

# Convert ternary to Cartesian coordinates
# Formula: x = 0.5 * (2*b + c) / (a+b+c), y = sqrt(3)/2 * c / (a+b+c)
# where a=Sand (bottom-left), b=Silt (bottom-right), c=Clay (top)
sqrt3_2 = np.sqrt(3) / 2
x_coords = []
y_coords = []
for sand, silt, clay in samples:
    total = sand + silt + clay
    silt_norm = silt / total
    clay_norm = clay / total
    x_coords.append(0.5 * (2 * silt_norm + clay_norm))
    y_coords.append(sqrt3_2 * clay_norm)

df = pd.DataFrame({"x": x_coords, "y": y_coords, "soil_type": soil_types})

# Triangle vertices (Sand at bottom-left, Silt at bottom-right, Clay at top)
vertices = pd.DataFrame({"x": [0, 1, 0.5, 0], "y": [0, 0, sqrt3_2, 0]})

# Grid lines at 20% intervals
grid_segments = []
for pct in [0.2, 0.4, 0.6, 0.8]:
    # Lines parallel to Sand-Silt edge (constant Clay)
    # From (1-pct, 0, pct) to (0, 1-pct, pct)
    x1 = 0.5 * (0 + pct)
    y1 = sqrt3_2 * pct
    x2 = 0.5 * (2 * (1 - pct) + pct)
    y2 = sqrt3_2 * pct
    grid_segments.append({"x": x1, "y": y1, "xend": x2, "yend": y2})

    # Lines parallel to Sand-Clay edge (constant Silt)
    # From (1-pct, pct, 0) to (0, pct, 1-pct)
    x1 = 0.5 * (2 * pct + 0)
    y1 = 0
    x2 = 0.5 * (2 * pct + (1 - pct))
    y2 = sqrt3_2 * (1 - pct)
    grid_segments.append({"x": x1, "y": y1, "xend": x2, "yend": y2})

    # Lines parallel to Silt-Clay edge (constant Sand)
    # From (pct, 1-pct, 0) to (pct, 0, 1-pct)
    x1 = 0.5 * (2 * (1 - pct) + 0)
    y1 = 0
    x2 = 0.5 * (0 + (1 - pct))
    y2 = sqrt3_2 * (1 - pct)
    grid_segments.append({"x": x1, "y": y1, "xend": x2, "yend": y2})

grid_df = pd.DataFrame(grid_segments)

# Vertex labels with offset for readability
label_offset = 0.06
labels_df = pd.DataFrame(
    {
        "x": [0 + label_offset, 1 - label_offset, 0.5],
        "y": [-label_offset - 0.02, -label_offset - 0.02, sqrt3_2 + label_offset],
        "label": ["Sand (%)", "Silt (%)", "Clay (%)"],
    }
)

# Tick labels along edges (at 20%, 40%, 60%, 80%)
tick_labels = []
for pct in [20, 40, 60, 80]:
    frac = pct / 100
    # Along left edge (Sand axis - reading Clay percentage going up)
    x = 0.5 * frac
    y = sqrt3_2 * frac
    tick_labels.append({"x": x - 0.04, "y": y + 0.02, "label": str(pct)})

    # Along right edge (Silt axis - reading Clay percentage going up)
    x = 0.5 * (2 * (1 - frac) + frac)
    y = sqrt3_2 * frac
    tick_labels.append({"x": x + 0.04, "y": y + 0.02, "label": str(pct)})

    # Along bottom edge (reading Silt percentage going right)
    x = 0.5 * (2 * frac)
    y = 0
    tick_labels.append({"x": x, "y": y - 0.04, "label": str(pct)})

tick_df = pd.DataFrame(tick_labels)

# Plot
plot = (
    ggplot()
    # Triangle outline
    + geom_polygon(data=vertices, mapping=aes(x="x", y="y"), fill="white", color="#333333", size=1.5, alpha=1)
    # Grid lines
    + geom_segment(
        data=grid_df, mapping=aes(x="x", y="y", xend="xend", yend="yend"), color="#CCCCCC", size=0.8, alpha=0.6
    )
    # Data points
    + geom_point(data=df, mapping=aes(x="x", y="y", color="soil_type"), size=6, alpha=0.8)
    # Vertex labels
    + geom_text(data=labels_df, mapping=aes(x="x", y="y", label="label"), size=18, fontface="bold", color="#333333")
    # Tick labels
    + geom_text(data=tick_df, mapping=aes(x="x", y="y", label="label"), size=11, color="#666666")
    # Color scale using Python colors
    + scale_color_manual(values=["#306998", "#FFD43B", "#DC2626"])
    # Labels and title
    + labs(title="Soil Composition · ternary-basic · letsplot · pyplots.ai", color="Soil Type")
    # Theme - remove axes since ternary uses its own coordinate system
    + theme(
        plot_title=element_text(size=24, face="bold"),
        legend_title=element_text(size=18),
        legend_text=element_text(size=16),
        axis_title=element_blank(),
        axis_text=element_blank(),
        axis_ticks=element_blank(),
        axis_line=element_blank(),
        panel_grid=element_blank(),
        legend_position="right",
    )
    + ggsize(1600, 900)
)

# Save as PNG (scale 3x to get 4800 x 2700 px)
ggsave(plot, "plot.png", path=".", scale=3)

# Save as HTML for interactive version
ggsave(plot, "plot.html", path=".")
