""" pyplots.ai
scatter-brush-zoom: Interactive Scatter Plot with Brush Selection and Zoom
Library: letsplot 4.8.2 | Python 3.13.11
Quality: 91/100 | Created: 2026-01-08
"""

import numpy as np
import pandas as pd
from lets_plot import (
    LetsPlot,
    aes,
    element_line,
    element_text,
    geom_point,
    geom_rect,
    geom_text,
    ggplot,
    ggsize,
    labs,
    layer_tooltips,
    scale_alpha_identity,
    scale_color_manual,
    theme,
    theme_minimal,
)
from lets_plot.export import ggsave


LetsPlot.setup_html()

# Data - Generate clustered data for brush selection demonstration
np.random.seed(42)

# Create 4 distinct clusters with different sizes
n_per_cluster = [80, 120, 100, 100]
centers = [(20, 60), (50, 30), (70, 70), (40, 80)]
spreads = [8, 12, 10, 6]
categories = ["Cluster A", "Cluster B", "Cluster C", "Cluster D"]

x_data, y_data, colors, labels, selected = [], [], [], [], []
point_id = 0
for n, (cx, cy), spread, cat in zip(n_per_cluster, centers, spreads, categories, strict=True):
    for _ in range(n):
        x_val = np.random.normal(cx, spread)
        y_val = np.random.normal(cy, spread)
        x_data.append(x_val)
        y_data.append(y_val)
        colors.append(cat)
        labels.append(f"P{point_id:03d}")
        # Mark points within the brush selection region as selected
        is_selected = 25 <= x_val <= 55 and 50 <= y_val <= 85
        selected.append(is_selected)
        point_id += 1

df = pd.DataFrame(
    {
        "x": x_data,
        "y": y_data,
        "category": colors,
        "label": labels,
        "selected": selected,
        "point_alpha": [0.9 if s else 0.25 for s in selected],
    }
)

# Create tooltips for hover interaction - shows point details
tooltips = (
    layer_tooltips()
    .title("@label")
    .line("Category: @category")
    .line("X: @x (units)")
    .line("Y: @y (units)")
    .line("Selected: @selected")
    .format("x", ".1f")
    .format("y", ".1f")
)

# Brush selection rectangle coordinates
brush_xmin, brush_xmax = 25, 55
brush_ymin, brush_ymax = 50, 85
n_selected = df["selected"].sum()

# Create brush rectangle data
brush_df = pd.DataFrame({"xmin": [brush_xmin], "xmax": [brush_xmax], "ymin": [brush_ymin], "ymax": [brush_ymax]})

# Create interactive scatter plot with brush selection visualization
# The static PNG demonstrates brush selection with:
# - Visible brush rectangle (blue dashed border with light fill)
# - Selected points shown with full opacity, unselected dimmed
# - Selection count annotation
# The HTML export includes built-in toolbar with:
# - Pan (drag to move around)
# - Wheel zoom (scroll to zoom in/out)
# - Box zoom (select area to zoom)
# - Reset (double-click to reset view)
plot = (
    ggplot(df, aes(x="x", y="y"))
    # Draw brush selection rectangle first (behind points)
    + geom_rect(
        aes(xmin="xmin", xmax="xmax", ymin="ymin", ymax="ymax"),
        data=brush_df,
        inherit_aes=False,
        fill="#3B82F6",
        alpha=0.15,
        color="#3B82F6",
        linetype="dashed",
        size=1.5,
    )
    # Plot points with alpha based on selection state
    + geom_point(aes(color="category", alpha="point_alpha"), size=5, tooltips=tooltips)
    + scale_color_manual(values=["#306998", "#FFD43B", "#DC2626", "#059669"])
    + scale_alpha_identity()
    + labs(
        x="X Value (units)", y="Y Value (units)", title="scatter-brush-zoom · letsplot · pyplots.ai", color="Category"
    )
    + theme_minimal()
    + theme(
        axis_title=element_text(size=20),
        axis_text=element_text(size=16),
        plot_title=element_text(size=24, margin=[0, 0, 10, 0]),
        legend_title=element_text(size=18),
        legend_text=element_text(size=16),
        panel_grid_major=element_line(color="#E5E5E5", size=0.5),
        panel_grid_minor=element_line(color="#F0F0F0", size=0.3),
    )
    + ggsize(1600, 900)
)

# Add annotation showing selection count
annotation_df = pd.DataFrame({"x": [40], "y": [88], "text": [f"Brush Selection: {n_selected} points selected"]})

plot = plot + geom_text(
    aes(x="x", y="y", label="text"), data=annotation_df, inherit_aes=False, size=14, color="#1E40AF", fontface="bold"
)

# Save static PNG (scaled 3x for 4800x2700 px)
ggsave(plot, "plot.png", path=".", scale=3)

# Save interactive HTML with zoom, pan, and hover capabilities
# The HTML viewer includes a toolbar with:
# - Pan mode: click and drag to navigate
# - Wheel zoom: scroll to zoom in/out
# - Box zoom: draw rectangle to zoom to area (brush-like selection)
# - Reset: double-click or use reset button to restore original view
ggsave(plot, "plot.html", path=".")
