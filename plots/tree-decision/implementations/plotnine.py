"""pyplots.ai
tree-decision: Decision Tree Visualization with Probabilities
Library: plotnine | Python 3.13
Quality: pending | Created: 2026-03-06
"""

import pandas as pd
from plotnine import (
    aes,
    element_rect,
    element_text,
    geom_point,
    geom_segment,
    geom_text,
    ggplot,
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
        "y": [5, 7.8, 2.2, 9.2, 6, 3.5, 1, 7, 5, 8, 6],
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
emv_nodes["ly"] = emv_nodes["y"] - 0.65

terminal_nodes = nodes[nodes["node_type"] == "Terminal"].copy()
terminal_nodes["lx"] = terminal_nodes["x"] + 0.5
terminal_nodes["ly"] = terminal_nodes["y"]

edges = pd.DataFrame(
    {
        "x": [0, 0, 3, 3, 3, 3, 6.5, 6.5, 9.5, 9.5],
        "xend": [3, 3, 6.5, 6.5, 6.5, 6.5, 9.5, 9.5, 12.5, 12.5],
        "y": [5, 5, 7.8, 7.8, 2.2, 2.2, 6, 6, 7, 7],
        "yend": [7.8, 2.2, 9.2, 6, 3.5, 1, 7, 5, 8, 6],
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

edges["lx"] = (edges["x"] + edges["xend"]) / 2
edges["ly"] = (edges["y"] + edges["yend"]) / 2 + 0.4

active = edges[~edges["pruned"]].copy()
pruned = edges[edges["pruned"]].copy()

prune_marks = pruned.copy()
prune_marks["mx"] = (prune_marks["x"] + prune_marks["xend"]) / 2
prune_marks["my"] = (prune_marks["y"] + prune_marks["yend"]) / 2
prune_marks["mark"] = "||"

# Plot
plot = (
    ggplot()
    + geom_segment(aes(x="x", y="y", xend="xend", yend="yend"), data=active, size=1.2, color="#555555")
    + geom_segment(
        aes(x="x", y="y", xend="xend", yend="yend"),
        data=pruned,
        size=0.8,
        color="#BBBBBB",
        linetype="dashed",
        alpha=0.6,
    )
    + geom_text(aes(x="mx", y="my", label="mark"), data=prune_marks, size=14, color="#CC3333")
    + geom_text(aes(x="lx", y="ly", label="branch_label"), data=edges, size=8, color="#444444")
    + geom_point(aes(x="x", y="y", color="node_type", shape="node_type"), data=nodes, size=8)
    + geom_text(aes(x="lx", y="ly", label="value"), data=emv_nodes, size=7, color="#306998", ha="center")
    + geom_text(aes(x="lx", y="ly", label="value"), data=terminal_nodes, size=7, color="#333333", ha="left")
    + scale_color_manual(values={"Decision": "#306998", "Chance": "#E8833A", "Terminal": "#4CAF50"}, name="Node Type")
    + scale_shape_manual(values={"Decision": "s", "Chance": "o", "Terminal": ">"}, name="Node Type")
    + theme_void()
    + theme(
        figure_size=(16, 9),
        plot_title=element_text(size=24, weight="bold", ha="center"),
        legend_position="bottom",
        legend_title=element_text(size=16),
        legend_text=element_text(size=14),
        plot_background=element_rect(fill="white", color="white"),
    )
    + labs(title="tree-decision · plotnine · pyplots.ai")
    + xlim(-1.5, 14.5)
    + ylim(-0.2, 10.5)
)

# Save
plot.save("plot.png", dpi=300)
