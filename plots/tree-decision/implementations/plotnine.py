"""pyplots.ai
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
        "y": [5, 8.2, 1.8, 9.8, 5.8, 3.3, 0.3, 7.5, 4.1, 8.6, 6.0],
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
emv_nodes["ly"] = emv_nodes["y"] - 1.0

terminal_nodes = nodes[nodes["node_type"] == "Terminal"].copy()
terminal_nodes["lx"] = terminal_nodes["x"] + 0.7
terminal_nodes["ly"] = terminal_nodes["y"]

edges = pd.DataFrame(
    {
        "x": [0, 0, 3, 3, 3, 3, 6.5, 6.5, 9.5, 9.5],
        "xend": [3, 3, 6.5, 6.5, 6.5, 6.5, 9.5, 9.5, 12.5, 12.5],
        "y": [5, 5, 8.2, 8.2, 1.8, 1.8, 5.8, 5.8, 7.5, 7.5],
        "yend": [8.2, 1.8, 9.8, 5.8, 3.3, 0.3, 7.5, 4.1, 8.6, 6.0],
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
        edges.loc[i, "ly"] += 0.8
    else:
        edges.loc[i, "ly"] -= 0.8
    # For pruned branches, shift label slightly toward start to avoid overlap with prune mark
    if edges.loc[i, "pruned"]:
        edges.loc[i, "lx"] -= 0.3

active = edges[~edges["pruned"]].copy()
pruned = edges[edges["pruned"]].copy()

prune_marks = pruned.copy()
prune_marks["mx"] = (prune_marks["x"] + prune_marks["xend"]) / 2 - 0.3
prune_marks["my"] = (prune_marks["y"] + prune_marks["yend"]) / 2
prune_marks["mark"] = "✕"

# Optimal path segments for highlight glow effect
optimal_path = pd.DataFrame(
    {
        "x": [0, 3, 3, 6.5, 9.5, 9.5],
        "xend": [3, 6.5, 6.5, 9.5, 12.5, 12.5],
        "y": [5, 8.2, 8.2, 5.8, 7.5, 7.5],
        "yend": [8.2, 9.8, 5.8, 7.5, 8.6, 6.0],
    }
)

# Plot using plotnine's grammar of graphics
plot = (
    ggplot()
    # Optimal path glow: wide translucent highlight behind active branches
    + geom_segment(
        aes(x="x", y="y", xend="xend", yend="yend"),
        data=optimal_path,
        size=5,
        color="#306998",
        alpha=0.12,
        lineend="round",
    )
    # Active branches: solid, dark
    + geom_segment(aes(x="x", y="y", xend="xend", yend="yend"), data=active, size=1.8, color="#2B2B2B", lineend="round")
    # Pruned branches: dashed, light
    + geom_segment(
        aes(x="x", y="y", xend="xend", yend="yend"),
        data=pruned,
        size=0.8,
        color="#C0C0C0",
        linetype="dashed",
        alpha=0.5,
    )
    # Prune marks
    + geom_text(aes(x="mx", y="my", label="mark"), data=prune_marks, size=18, color="#CC3333", fontweight="bold")
    # Branch labels
    + geom_text(aes(x="lx", y="ly", label="branch_label"), data=edges, size=14, color="#2B2B2B")
    # Nodes with border effect
    + geom_point(aes(x="x", y="y", shape="node_type"), data=nodes, size=14, color="#2B2B2B", fill="#2B2B2B", stroke=0.5)
    # Nodes with color fill
    + geom_point(aes(x="x", y="y", color="node_type", shape="node_type"), data=nodes, size=12)
    # EMV labels at non-terminal nodes
    + geom_text(
        aes(x="lx", y="ly", label="value"), data=emv_nodes, size=13, color="#306998", ha="center", fontweight="bold"
    )
    # Payoff labels at terminal nodes
    + geom_text(
        aes(x="lx", y="ly", label="value"), data=terminal_nodes, size=13, color="#1A1A1A", ha="left", fontweight="bold"
    )
    # Optimal path annotation — prominent with arrow-like indicator
    + annotate("text", x=0.8, y=10.2, label="★ Optimal Path", size=14, color="#306998", fontweight="bold")
    + annotate("segment", x=0.8, y=9.9, xend=1.2, yend=9.0, size=1.0, color="#306998", alpha=0.7)
    + scale_color_manual(values={"Decision": "#306998", "Chance": "#E8833A", "Terminal": "#00796B"}, name="Node Type")
    + scale_shape_manual(values={"Decision": "s", "Chance": "o", "Terminal": ">"}, name="Node Type")
    + guides(color=guide_legend(override_aes={"size": 9}))
    + theme_void()
    + theme(
        figure_size=(16, 9),
        plot_title=element_text(size=26, weight="bold", ha="center", color="#1A1A1A"),
        plot_subtitle=element_text(size=16, ha="center", color="#555555"),
        legend_position=(0.5, 0.03),
        legend_direction="horizontal",
        legend_title=element_text(size=16, weight="bold"),
        legend_text=element_text(size=15),
        legend_key_size=22,
        plot_background=element_rect(fill="#FAFAFA", color="#FAFAFA"),
        plot_margin=0.02,
    )
    + labs(
        title="tree-decision · plotnine · pyplots.ai",
        subtitle="Product Launch vs. License IP — EMV Rollback Analysis (Optimal: Launch → $320K)",
    )
    + coord_fixed(ratio=0.65)
    + xlim(-1.5, 14.5)
    + ylim(-1.0, 11.5)
)

# Save
plot.save("plot.png", dpi=300)
