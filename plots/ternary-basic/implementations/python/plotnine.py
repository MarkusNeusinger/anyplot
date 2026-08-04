"""anyplot.ai
ternary-basic: Basic Ternary Plot
Library: plotnine 0.15.7 | Python 3.13.13
Quality: 84/100 | Updated: 2026-08-04
"""

import os
import sys


sys.path.pop(0)

import numpy as np
import pandas as pd
from plotnine import (
    aes,
    coord_fixed,
    element_rect,
    element_text,
    geom_point,
    geom_polygon,
    geom_segment,
    geom_text,
    ggplot,
    labs,
    scale_color_gradient,
    theme,
    theme_void,
)


# Theme tokens (Imprint)
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
BRAND = "#009E73"  # Imprint position 1
BLUE = "#4467A3"  # Imprint position 3 — far end of imprint_seq

# Data - Soil composition samples (sand, silt, clay), USDA-style texture triangle
np.random.seed(42)
n_points = 50

# Dirichlet mixtures give a realistic spread across sand-, silt-, and clay-heavy soils
raw1 = np.random.dirichlet(alpha=[5, 1, 1], size=n_points // 3) * 100  # Sand-heavy
raw2 = np.random.dirichlet(alpha=[1, 5, 1], size=n_points // 3) * 100  # Silt-heavy
raw3 = np.random.dirichlet(alpha=[1, 1, 5], size=n_points - 2 * (n_points // 3)) * 100  # Clay-heavy
raw = np.vstack([raw1, raw2, raw3])
np.random.shuffle(raw)
sand = raw[:, 0]
silt = raw[:, 1]
clay = raw[:, 2]

# Convert ternary coordinates to Cartesian (equilateral triangle, unit height)
total = sand + silt + clay
x_data = 0.5 * (2 * silt + clay) / total
y_data = (np.sqrt(3) / 2) * clay / total

# Ideal loam target (USDA loam zone center: ~42% sand, 42% silt, 16% clay) — the
# focal point every sample is compared against, encoded as a continuous gradient
target_sand, target_silt, target_clay = 42.0, 42.0, 16.0
x_target = 0.5 * (2 * target_silt + target_clay) / 100.0
y_target = (np.sqrt(3) / 2) * target_clay / 100.0
distance = np.sqrt((x_data - x_target) ** 2 + (y_data - y_target) ** 2)

df = pd.DataFrame({"x": x_data, "y": y_data, "sand": sand, "silt": silt, "clay": clay, "distance": distance})
target_df = pd.DataFrame({"x": [x_target], "y": [y_target]})
target_label_df = pd.DataFrame({"x": [x_target + 0.1], "y": [y_target - 0.02], "label": ["Ideal loam"]})

# Triangle vertices (for the frame)
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
label_offset = 0.045
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
        "y": [0 - 0.07, 0 - 0.07, np.sqrt(3) / 2 + 0.05],
        "label": ["Sand (%)", "Silt (%)", "Clay (%)"],
    }
)

# Build the plot
plot = (
    ggplot()
    # Triangle frame
    + geom_polygon(data=vertices, mapping=aes(x="x", y="y"), fill=PAGE_BG, color=BRAND, size=1.4)
    # Grid lines
    + geom_segment(data=grid_df, mapping=aes(x="x", y="y", xend="xend", yend="yend"), color=INK, size=0.4, alpha=0.15)
    # Data points, colored by distance to the ideal-loam target — brand green (close)
    # to blue (far), the imprint_seq sequential colormap
    + geom_point(data=df, mapping=aes(x="x", y="y", color="distance"), size=3, alpha=0.85)
    + scale_color_gradient(low=BRAND, high=BLUE, name="Distance to\nideal loam")
    # Target marker — theme-neutral reference point, not a data series
    + geom_point(data=target_df, mapping=aes(x="x", y="y"), color=INK, size=4.5, shape="D", stroke=1.2)
    + geom_text(
        data=target_label_df,
        mapping=aes(x="x", y="y", label="label"),
        size=3.6,
        color=INK,
        fontweight="bold",
        ha="left",
    )
    # Tick labels
    + geom_text(data=tick_df, mapping=aes(x="x", y="y", label="label"), size=3, color=INK_SOFT)
    # Vertex labels
    + geom_text(data=vertex_labels, mapping=aes(x="x", y="y", label="label"), size=4.2, fontweight="bold", color=INK)
    # Title and theme
    + labs(title="ternary-basic · plotnine · anyplot.ai")
    + coord_fixed(ratio=1)
    + theme_void()
    + theme(
        figure_size=(8, 4.5),
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        plot_title=element_text(size=13, ha="center", color=INK, weight="medium"),
        legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT),
        legend_text=element_text(size=7, color=INK_SOFT),
        legend_title=element_text(size=8, color=INK),
        legend_position="right",
        plot_margin=0.02,
    )
)

# Save
plot.save(f"plot-{THEME}.png", dpi=400, width=8, height=4.5, units="in", verbose=False)
