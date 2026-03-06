""" pyplots.ai
tree-decision: Decision Tree Visualization with Probabilities
Library: plotnine 0.15.3 | Python 3.14.3
Quality: 84/100 | Created: 2026-03-06
"""

import pandas as pd
from plotnine import (
    aes,
    annotate,
    coord_fixed,
    element_rect,
    element_text,
    geom_point,
    geom_segment,
    geom_text,
    ggplot,
    guide_legend,
    guides,
    labs,
    scale_color_manual,
    scale_shape_manual,
    theme,
    theme_void,
    xlim,
    ylim,
)


# Data - Two-stage product launch decision tree
# EMV rollback calculations:
#   C2 = 0.5 * 200 + 0.5 * (-100) = $50K
#   D2 = max(Pivot=$50K, Cut=-$50K) = $50K  (prune Cut Losses)
#   C1 = 0.6 * 500 + 0.4 * 50 = $320K
#   C3 = 0.7 * 250 + 0.3 * 30 = $184K
#   D1 = max(Launch=$320K, License=$184K) = $320K  (prune License IP)

nodes = pd.DataFrame(
    {
        "x": [0, 3, 3, 6.5, 6.5, 6.5, 6.5, 9.5, 9.5, 12.5, 12.5],
        "y": [5, 8, 2, 9.5, 6, 3.5, 0.5, 7.2, 4.8, 8.2, 6.2],
        "node_type": [
            "Decision",
            "Chance",
            "Chance",
            "Terminal",
            "Decision",
            "Terminal",
            "Terminal",
            "Chance",
            "Terminal",
            "Terminal",
            "Terminal",
        ],
        "value": [
            "EMV: $320K",
            "EMV: $320K",
            "EMV: $184K",
            "$500K",
            "EMV: $50K",
            "$250K",
            "$30K",
            "EMV: $50K",
            "-$50K",
            "$200K",
            "-$100K",
        ],
    }
)

emv_nodes = nodes[nodes["node_type"] != "Terminal"].copy()
emv_nodes["lx"] = emv_nodes["x"]
emv_nodes["ly"] = emv_nodes["y"] - 0.8

terminal_nodes = nodes[nodes["node_type"] == "Terminal"].copy()
terminal_nodes["lx"] = terminal_nodes["x"] + 0.6
terminal_nodes["ly"] = terminal_nodes["y"]

edges = pd.DataFrame(
    {
        "x": [0, 0, 3, 3, 3, 3, 6.5, 6.5, 9.5, 9.5],
        "xend": [3, 3, 6.5, 6.5, 6.5, 6.5, 9.5, 9.5, 12.5, 12.5],
        "y": [5, 5, 8, 8, 2, 2, 6, 6, 7.2, 7.2],
        "yend": [8, 2, 9.5, 6, 3.5, 0.5, 7.2, 4.8, 8.2, 6.2],
        "branch_label": [
            "Launch Product",
            "License IP",
            "High Demand\n(p=0.60)",
            "Low Demand\n(p=0.40)",
            "Accepted\n(p=0.70)",
            "Rejected\n(p=0.30)",
            "Pivot Strategy",
            "Cut Losses",
            "Recovery\n(p=0.50)",
            "No Recovery\n(p=0.50)",
        ],
        "pruned": [False, True, False, False, True, True, False, True, False, False],
    }
)

# Position labels with offset depending on pruned status
# Active branches: label above midpoint; Pruned: label shifted to avoid prune mark overlap
edges["lx"] = (edges["x"] + edges["xend"]) / 2
edges["ly"] = (edges["y"] + edges["yend"]) / 2

# Offset labels upward for branches going up, downward for branches going down
for i in edges.index:
    dy = edges.loc[i, "yend"] - edges.loc[i, "y"]
    if dy > 0:
        edges.loc[i, "ly"] += 0.6
    else:
        edges.loc[i, "ly"] -= 0.6
    # For pruned branches, shift label further from midpoint to avoid prune mark collision
    if edges.loc[i, "pruned"]:
        edges.loc[i, "lx"] += 0.8

active = edges[~edges["pruned"]].copy()
pruned = edges[edges["pruned"]].copy()

prune_marks = pruned.copy()
prune_marks["mx"] = (prune_marks["x"] + prune_marks["xend"]) / 2 - 0.3
prune_marks["my"] = (prune_marks["y"] + prune_marks["yend"]) / 2
prune_marks["mark"] = "✕"

# Plot using plotnine's grammar of graphics with annotate() and coord_fixed()
plot = (
    ggplot()
    # Active branches: solid, dark
    + geom_segment(aes(x="x", y="y", xend="xend", yend="yend"), data=active, size=1.5, color="#3D3D3D", lineend="round")
    # Pruned branches: dashed, light
    + geom_segment(
        aes(x="x", y="y", xend="xend", yend="yend"),
        data=pruned,
        size=0.9,
        color="#BBBBBB",
        linetype="dashed",
        alpha=0.55,
    )
    # Prune marks
    + geom_text(aes(x="mx", y="my", label="mark"), data=prune_marks, size=14, color="#CC3333", fontweight="bold")
    # Branch labels (increased size for legibility)
    + geom_text(aes(x="lx", y="ly", label="branch_label"), data=edges, size=10, color="#333333")
    # Nodes with border effect using larger background points
    + geom_point(aes(x="x", y="y", shape="node_type"), data=nodes, size=13, color="#333333", fill="#333333", stroke=0.5)
    # Nodes with color fill
    + geom_point(aes(x="x", y="y", color="node_type", shape="node_type"), data=nodes, size=11)
    # EMV labels at non-terminal nodes (increased size)
    + geom_text(
        aes(x="lx", y="ly", label="value"), data=emv_nodes, size=9, color="#306998", ha="center", fontweight="bold"
    )
    # Payoff labels at terminal nodes (increased size)
    + geom_text(
        aes(x="lx", y="ly", label="value"), data=terminal_nodes, size=9, color="#222222", ha="left", fontweight="bold"
    )
    # Use annotate() for optimal path highlight annotation (plotnine-specific feature)
    + annotate("text", x=1.5, y=8.8, label="★ Optimal", size=9, color="#306998", fontstyle="italic")
    + scale_color_manual(values={"Decision": "#306998", "Chance": "#E8833A", "Terminal": "#4CAF50"}, name="Node Type")
    + scale_shape_manual(values={"Decision": "s", "Chance": "o", "Terminal": ">"}, name="Node Type")
    + guides(color=guide_legend(override_aes={"size": 8}))
    + theme_void()
    + theme(
        figure_size=(16, 9),
        plot_title=element_text(size=24, weight="bold", ha="center"),
        plot_subtitle=element_text(size=14, ha="center", color="#666666"),
        legend_position=(0.5, 0.03),
        legend_direction="horizontal",
        legend_title=element_text(size=16),
        legend_text=element_text(size=14),
        legend_key_size=20,
        plot_background=element_rect(fill="white", color="white"),
        plot_margin=0.02,
    )
    + labs(title="tree-decision · plotnine · pyplots.ai")
    + coord_fixed(ratio=0.65)
    + xlim(-1.5, 14.5)
    + ylim(-0.8, 11)
)

# Save
plot.save("plot.png", dpi=300)
