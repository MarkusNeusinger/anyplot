""" pyplots.ai
arc-basic: Basic Arc Diagram
Library: plotnine 0.15.3 | Python 3.14.3
Quality: 81/100 | Updated: 2026-02-23
"""

import sys


sys.path = [p for p in sys.path if not p.endswith("implementations")]

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from plotnine import (  # noqa: E402
    aes,
    coord_cartesian,
    element_blank,
    element_rect,
    element_text,
    geom_path,
    geom_point,
    geom_text,
    ggplot,
    labs,
    scale_alpha_identity,
    scale_size_identity,
    theme,
)


# Data: Character interactions in a story chapter
nodes = ["Alice", "Bob", "Carol", "David", "Eve", "Frank", "Grace", "Henry", "Iris", "Jack"]
n_nodes = len(nodes)

# Edges: (source_idx, target_idx, weight)
edges = [
    (0, 1, 3),  # Alice-Bob (strong)
    (0, 3, 2),  # Alice-David
    (1, 2, 2),  # Bob-Carol
    (2, 4, 1),  # Carol-Eve
    (3, 5, 2),  # David-Frank
    (4, 6, 1),  # Eve-Grace
    (0, 7, 1),  # Alice-Henry (long-range)
    (1, 5, 2),  # Bob-Frank
    (2, 3, 3),  # Carol-David (strong)
    (5, 8, 1),  # Frank-Iris
    (6, 9, 2),  # Grace-Jack
    (0, 9, 1),  # Alice-Jack (longest range)
    (3, 7, 2),  # David-Henry
    (7, 8, 1),  # Henry-Iris
    (8, 9, 2),  # Iris-Jack
]

# Node positions along x-axis
x_positions = np.linspace(0, 1, n_nodes)
y_baseline = 0.0

# Build arc paths using vectorized construction
n_points = 50
theta = np.linspace(0, np.pi, n_points)
arc_rows = []

for arc_id, (start, end, weight) in enumerate(edges):
    x_start, x_end = x_positions[start], x_positions[end]
    x_center = (x_start + x_end) / 2
    arc_radius = abs(x_end - x_start) / 2
    height = 0.08 * abs(end - start)

    x_arc = x_center - arc_radius * np.cos(theta)
    y_arc = y_baseline + height * np.sin(theta)

    arc_df_chunk = pd.DataFrame(
        {"x": x_arc, "y": y_arc, "arc_id": arc_id, "size": 0.8 + weight * 0.7, "alpha": 0.30 + weight * 0.18}
    )
    arc_rows.append(arc_df_chunk)

arc_df = pd.concat(arc_rows, ignore_index=True)

# Node and label dataframes
node_df = pd.DataFrame({"x": x_positions, "y": [y_baseline] * n_nodes})
label_df = pd.DataFrame({"x": x_positions, "y": [y_baseline - 0.03] * n_nodes, "name": nodes})

# Plot
plot = (
    ggplot()
    + geom_path(arc_df, aes(x="x", y="y", group="arc_id", size="size", alpha="alpha"), color="#306998")
    + scale_size_identity()
    + scale_alpha_identity()
    + geom_point(node_df, aes(x="x", y="y"), color="#306998", size=8, stroke=1.2, fill="white")
    + geom_text(label_df, aes(x="x", y="y", label="name"), size=12, color="#2C3E50", fontweight="bold", va="top")
    + coord_cartesian(xlim=(-0.05, 1.05))
    + labs(title="Character Interactions \u00b7 arc-basic \u00b7 plotnine \u00b7 pyplots.ai")
    + theme(
        figure_size=(16, 9),
        plot_title=element_text(size=24, ha="center", weight="bold"),
        plot_margin=0.02,
        axis_title=element_blank(),
        axis_text=element_blank(),
        axis_ticks=element_blank(),
        panel_grid=element_blank(),
        panel_background=element_rect(fill="white", color="white"),
        plot_background=element_rect(fill="white", color="white"),
        legend_position="none",
    )
)

# Save
plot.save("plot.png", dpi=300, verbose=False)
