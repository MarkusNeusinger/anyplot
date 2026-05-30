"""anyplot.ai
arc-basic: Basic Arc Diagram
Library: letsplot | Python 3.14
Quality: pending | Updated: 2026-05-30
"""

import os

import numpy as np
import pandas as pd
from lets_plot import (
    LetsPlot,
    aes,
    element_blank,
    element_rect,
    element_text,
    geom_path,
    geom_point,
    geom_segment,
    geom_text,
    ggplot,
    ggsize,
    labs,
    layer_tooltips,
    scale_alpha_identity,
    scale_color_identity,
    scale_size_identity,
    theme,
    xlim,
    ylim,
)
from lets_plot.export import ggsave


LetsPlot.setup_html()

# Theme tokens — Imprint palette, theme-adaptive chrome
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette — 3 weight levels in canonical order, first = brand green
ARC_COLORS = {
    1: "#009E73",  # Weak — Imprint position 1 (brand green)
    2: "#C475FD",  # Moderate — Imprint position 2 (lavender)
    3: "#4467A3",  # Strong — Imprint position 3 (blue)
}
ARC_ALPHAS = {1: 0.70, 2: 0.82, 3: 0.95}
NODE_FILL = "#BD8233"  # Imprint position 4 (ochre) — warm entity anchor

# Data: Character interactions in a story chapter
nodes = ["Alice", "Bob", "Carol", "David", "Eve", "Frank", "Grace", "Henry", "Iris", "Jack"]
n_nodes = len(nodes)

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

x_positions = np.linspace(0, 1.3, n_nodes)
y_baseline = 0.06

connections = [0] * n_nodes
for s, t, w in edges:
    connections[s] += w
    connections[t] += w

weight_labels = {1: "Weak", 2: "Moderate", 3: "Strong"}

# Arc path data — increased floor size for weak arc visibility
arc_data = []
for edge_id, (start, end, weight) in enumerate(edges):
    x_start = x_positions[start]
    x_end = x_positions[end]
    distance = abs(end - start)
    height = 0.08 * distance
    n_points = 50
    t_vals = np.linspace(0, np.pi, n_points)
    arc_x = x_start + (x_end - x_start) * (1 - np.cos(t_vals)) / 2
    arc_y = y_baseline + height * np.sin(t_vals)
    line_size = 1.8 + weight * 1.3  # raised floor: weak=3.1, moderate=4.4, strong=5.7
    for i in range(n_points):
        arc_data.append(
            {
                "x": arc_x[i],
                "y": arc_y[i],
                "edge_id": edge_id,
                "size": line_size,
                "color": ARC_COLORS[weight],
                "alpha": ARC_ALPHAS[weight],
                "connection": f"{nodes[start]} ↔ {nodes[end]}",
                "strength": weight_labels[weight],
            }
        )

arc_df = pd.DataFrame(arc_data)

max_conn = max(connections)
node_sizes = [10 + 8 * (c / max_conn) for c in connections]
node_df = pd.DataFrame(
    {"x": x_positions, "y": [y_baseline] * n_nodes, "name": nodes, "node_size": node_sizes, "connections": connections}
)

baseline_df = pd.DataFrame({"x": [x_positions[0]], "xend": [x_positions[-1]], "y": [y_baseline], "yend": [y_baseline]})

label_df = pd.DataFrame({"x": x_positions, "y": [y_baseline - 0.038] * n_nodes, "name": nodes})

# Legend — upper-left to balance canvas composition and utilize empty space
legend_x = 0.0
legend_y_start = 0.79
legend_spacing = 0.068
legend_line_len = 0.085
legend_lines = pd.DataFrame(
    {
        "x": [legend_x] * 3,
        "xend": [legend_x + legend_line_len] * 3,
        "y": [legend_y_start - i * legend_spacing for i in range(3)],
        "yend": [legend_y_start - i * legend_spacing for i in range(3)],
        "color": [ARC_COLORS[3], ARC_COLORS[2], ARC_COLORS[1]],
        "size": [1.8 + 3 * 1.3, 1.8 + 2 * 1.3, 1.8 + 1 * 1.3],
        "alpha": [ARC_ALPHAS[3], ARC_ALPHAS[2], ARC_ALPHAS[1]],
    }
)
legend_text_df = pd.DataFrame(
    {
        "x": [legend_x + legend_line_len + 0.013] * 3,
        "y": [legend_y_start - i * legend_spacing for i in range(3)],
        "label": ["Strong (3)", "Moderate (2)", "Weak (1)"],
    }
)
legend_title_df = pd.DataFrame({"x": [legend_x], "y": [legend_y_start + 0.075], "label": ["Connection Strength"]})

# Plot
plot = (
    ggplot()
    + geom_segment(
        data=baseline_df, mapping=aes(x="x", y="y", xend="xend", yend="yend"), color=INK_SOFT, size=0.6, alpha=0.4
    )
    + geom_path(
        data=arc_df,
        mapping=aes(x="x", y="y", group="edge_id", size="size", color="color", alpha="alpha"),
        tooltips=layer_tooltips().title("@connection").line("Strength|@strength"),
    )
    + scale_size_identity()
    + scale_color_identity()
    + scale_alpha_identity()
    + geom_point(
        data=node_df,
        mapping=aes(x="x", y="y", size="node_size"),
        color=INK,
        fill=NODE_FILL,
        stroke=1.5,
        shape=21,
        tooltips=layer_tooltips().title("@name").line("Total weight|@connections"),
    )
    + scale_size_identity()
    + geom_text(data=label_df, mapping=aes(x="x", y="y", label="name"), size=9, color=INK, fontface="bold", vjust=1)
    + geom_segment(
        data=legend_lines,
        mapping=aes(x="x", y="y", xend="xend", yend="yend", color="color", size="size", alpha="alpha"),
        tooltips="none",
    )
    + geom_text(data=legend_text_df, mapping=aes(x="x", y="y", label="label"), size=7, color=INK_SOFT, hjust=0)
    + geom_text(
        data=legend_title_df, mapping=aes(x="x", y="y", label="label"), size=8, color=INK, fontface="bold", hjust=0
    )
    + xlim(-0.05, 1.48)
    + ylim(-0.09, 0.92)
    + labs(
        title="arc-basic · python · letsplot · anyplot.ai",
        subtitle="Character interactions in a story chapter — node size reflects connection strength",
    )
    + theme(
        axis_title=element_blank(),
        axis_text=element_blank(),
        axis_ticks=element_blank(),
        axis_line=element_blank(),
        panel_grid=element_blank(),
        panel_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        plot_title=element_text(size=16, face="bold", color=INK),
        plot_subtitle=element_text(size=13, color=INK_SOFT),
        legend_position="none",
    )
    + ggsize(800, 450)
)

# Save — theme-suffixed filenames, scale=4 → 3200×1800 px
ggsave(plot, f"plot-{THEME}.png", path=".", scale=4)
ggsave(plot, f"plot-{THEME}.html", path=".")
