""" pyplots.ai
arc-basic: Basic Arc Diagram
Library: plotnine 0.15.3 | Python 3.14.3
Quality: 90/100 | Updated: 2026-02-23
"""

import sys


sys.path = [p for p in sys.path if not p.endswith("implementations")]

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from plotnine import (  # noqa: E402
    aes,
    annotate,
    coord_cartesian,
    element_rect,
    element_text,
    geom_path,
    geom_point,
    geom_segment,
    geom_text,
    ggplot,
    guide_colorbar,
    labs,
    scale_alpha_identity,
    scale_color_gradient,
    scale_size_identity,
    theme,
    theme_void,
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

# Build arc paths
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

    arc_rows.append(
        pd.DataFrame(
            {
                "x": x_arc,
                "y": y_arc,
                "arc_id": arc_id,
                "weight": float(weight),
                "size": 1.2 + weight * 0.7,
                "alpha": 0.50 + weight * 0.15,
            }
        )
    )

arc_df = pd.concat(arc_rows, ignore_index=True)

# Baseline, node, and label dataframes
baseline_df = pd.DataFrame({"x": [x_positions[0]], "xend": [x_positions[-1]], "y": [y_baseline], "yend": [y_baseline]})
node_df = pd.DataFrame({"x": x_positions, "y": [y_baseline] * n_nodes})
label_df = pd.DataFrame({"x": x_positions, "y": [y_baseline - 0.035] * n_nodes, "name": nodes})

# Plot with grammar of graphics layering and guide customization
plot = (
    ggplot()
    + geom_segment(
        baseline_df, aes(x="x", y="y", xend="xend", yend="yend"), color="#C0C8D0", size=0.8, linetype="solid"
    )
    + geom_path(arc_df, aes(x="x", y="y", group="arc_id", color="weight", size="size", alpha="alpha"))
    + scale_color_gradient(
        low="#A8C4D8",
        high="#1A3A5C",
        name="Interaction\nStrength",
        breaks=[1, 2, 3],
        labels=["Weak", "Medium", "Strong"],
        guide=guide_colorbar(direction="vertical"),
    )
    + scale_size_identity()
    + scale_alpha_identity()
    + geom_point(node_df, aes(x="x", y="y"), color="#1A3A5C", size=11, stroke=1.8, fill="white")
    + geom_text(label_df, aes(x="x", y="y", label="name"), size=16, color="#1A3A5C", fontweight="bold", va="top")
    + annotate(
        "text",
        x=0.5,
        y=0.76,
        label="Stronger connections shown with darker, thicker arcs",
        size=16,
        color="#666666",
        ha="center",
        fontstyle="italic",
    )
    + coord_cartesian(xlim=(-0.06, 1.06), ylim=(-0.10, 0.82))
    + labs(
        title="Character Interactions \u00b7 arc-basic \u00b7 plotnine \u00b7 pyplots.ai",
        subtitle="Narrative connections in Chapter 1 \u2014 arc thickness and color encode interaction strength",
    )
    + theme_void()
    + theme(
        figure_size=(16, 9),
        plot_title=element_text(size=24, ha="center", weight="bold", color="#1A3A5C"),
        plot_subtitle=element_text(size=16, ha="center", color="#555555"),
        plot_margin=0.02,
        plot_background=element_rect(fill="white", color="white"),
        legend_position="right",
        legend_title=element_text(size=14, weight="bold", color="#1A3A5C"),
        legend_text=element_text(size=12, color="#444444"),
        legend_key_height=40,
        legend_key_width=12,
    )
)

# Save
plot.save("plot.png", dpi=300, verbose=False)
