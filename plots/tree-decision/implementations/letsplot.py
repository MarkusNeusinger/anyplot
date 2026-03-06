""" pyplots.ai
tree-decision: Decision Tree Visualization with Probabilities
Library: letsplot 4.8.2 | Python 3.14.3
Quality: 85/100 | Created: 2026-03-06
"""

import pandas as pd
from lets_plot import (
    LetsPlot,
    aes,
    element_text,
    flavor_solarized_light,
    geom_label,
    geom_point,
    geom_polygon,
    geom_rect,
    geom_segment,
    geom_text,
    ggplot,
    ggsize,
    labs,
    scale_x_continuous,
    scale_y_continuous,
    theme,
    theme_void,
)
from lets_plot.export import ggsave


LetsPlot.setup_html()

# Data - Two-stage product launch decision
# EMV rollback:
#   C2: 0.6 * $600K + 0.4 * $200K = $440K
#   D2: max($440K, $350K) = $440K -> "Maintain" pruned
#   C1: 0.3 * $900K + 0.5 * $440K + 0.2 * (-$200K) = $450K
#   D1: max($450K, $250K) = $450K -> "License Tech" pruned

node_records = [
    {"id": "D1", "type": "decision", "x": 0, "y": 4.5, "value": "EMV $450K"},
    {"id": "C1", "type": "chance", "x": 5, "y": 7.0, "value": "EMV $450K"},
    {"id": "T6", "type": "terminal", "x": 5, "y": 1.5, "value": "$250K"},
    {"id": "T1", "type": "terminal", "x": 10, "y": 9.0, "value": "$900K"},
    {"id": "D2", "type": "decision", "x": 10, "y": 7.0, "value": "EMV $440K"},
    {"id": "T2", "type": "terminal", "x": 10, "y": 4.5, "value": "-$200K"},
    {"id": "C2", "type": "chance", "x": 15, "y": 8.0, "value": "EMV $440K"},
    {"id": "T3", "type": "terminal", "x": 15, "y": 6.0, "value": "$350K"},
    {"id": "T4", "type": "terminal", "x": 20, "y": 8.5, "value": "$600K"},
    {"id": "T5", "type": "terminal", "x": 20, "y": 7.5, "value": "$200K"},
]

branch_records = [
    {"from_id": "D1", "to_id": "C1", "label": "Launch Product", "pruned": False},
    {"from_id": "D1", "to_id": "T6", "label": "License Tech", "pruned": True},
    {"from_id": "C1", "to_id": "T1", "label": "Strong (0.3)", "pruned": False},
    {"from_id": "C1", "to_id": "D2", "label": "Moderate (0.5)", "pruned": False},
    {"from_id": "C1", "to_id": "T2", "label": "Weak (0.2)", "pruned": False},
    {"from_id": "D2", "to_id": "C2", "label": "Scale Up", "pruned": False},
    {"from_id": "D2", "to_id": "T3", "label": "Maintain", "pruned": True},
    {"from_id": "C2", "to_id": "T4", "label": "Success (0.6)", "pruned": False},
    {"from_id": "C2", "to_id": "T5", "label": "Setback (0.4)", "pruned": False},
]

node_lookup = {r["id"]: r for r in node_records}

# Build elbow connector segments (horizontal-vertical-horizontal)
active_segs = []
pruned_segs = []
for b in branch_records:
    f = node_lookup[b["from_id"]]
    t = node_lookup[b["to_id"]]
    mid_x = (f["x"] + t["x"]) / 2
    seg1 = {"x": f["x"], "y": f["y"], "xend": mid_x, "yend": f["y"]}
    seg2 = {"x": mid_x, "y": f["y"], "xend": mid_x, "yend": t["y"]}
    seg3 = {"x": mid_x, "y": t["y"], "xend": t["x"], "yend": t["y"]}
    target = pruned_segs if b["pruned"] else active_segs
    target.extend([seg1, seg2, seg3])

df_active = pd.DataFrame(active_segs)
df_pruned = pd.DataFrame(pruned_segs)

# Branch labels placed along the horizontal portion near the midpoint
branch_label_records = []
for b in branch_records:
    f = node_lookup[b["from_id"]]
    t = node_lookup[b["to_id"]]
    mid_x = (f["x"] + t["x"]) / 2
    label_y = t["y"] + 0.4
    branch_label_records.append({"x": mid_x, "y": label_y, "label": b["label"]})
df_branch_labels = pd.DataFrame(branch_label_records)

# Separate nodes by type
df_decision = pd.DataFrame([r for r in node_records if r["type"] == "decision"])
df_chance = pd.DataFrame([r for r in node_records if r["type"] == "chance"])
df_terminal = pd.DataFrame([r for r in node_records if r["type"] == "terminal"])

# Decision nodes as proper rectangles using geom_rect
rect_half = 0.55
df_decision_rects = pd.DataFrame(
    [
        {
            "xmin": r["x"] - rect_half,
            "xmax": r["x"] + rect_half,
            "ymin": r["y"] - rect_half * 0.8,
            "ymax": r["y"] + rect_half * 0.8,
        }
        for r in node_records
        if r["type"] == "decision"
    ]
)

# Right-pointing triangles for terminal nodes using geom_polygon
tri_w = 0.5
tri_h = 0.35
triangle_polys = []
for r in node_records:
    if r["type"] == "terminal":
        tri_id = f"tri_{r['id']}"
        triangle_polys.extend(
            [
                {"x": r["x"] - tri_w, "y": r["y"] + tri_h, "group": tri_id},
                {"x": r["x"] - tri_w, "y": r["y"] - tri_h, "group": tri_id},
                {"x": r["x"] + tri_w * 0.6, "y": r["y"], "group": tri_id},
            ]
        )
df_triangles = pd.DataFrame(triangle_polys)

# Value labels: offset terminal payoffs further right to avoid triangle overlap
value_label_records = []
for r in node_records:
    if r["type"] == "terminal":
        value_label_records.append({"x": r["x"] + 1.0, "y": r["y"], "label": r["value"]})
    else:
        value_label_records.append({"x": r["x"], "y": r["y"] - 0.7, "label": r["value"]})
df_values = pd.DataFrame(value_label_records)

# Pruning cross marks
prune_mark_records = []
for b in branch_records:
    if b["pruned"]:
        f = node_lookup[b["from_id"]]
        t = node_lookup[b["to_id"]]
        cx = f["x"] + (t["x"] - f["x"]) * 0.4
        cy = f["y"] + (t["y"] - f["y"]) * 0.4
        d = 0.25
        prune_mark_records.append({"x": cx - d, "y": cy - d, "xend": cx + d, "yend": cy + d})
        prune_mark_records.append({"x": cx - d, "y": cy + d, "xend": cx + d, "yend": cy - d})
df_prune_marks = pd.DataFrame(prune_mark_records)

# Compact legend data using geom_rect and geom_polygon for consistency
legend_y_base = 1.0
legend_x = 15.0
df_legend_labels = pd.DataFrame(
    [
        {"x": legend_x + 0.8, "y": legend_y_base + 1.2, "label": "Decision Node"},
        {"x": legend_x + 0.8, "y": legend_y_base + 0.6, "label": "Chance Node"},
        {"x": legend_x + 0.8, "y": legend_y_base, "label": "Terminal Node"},
    ]
)
df_legend_decision_rect = pd.DataFrame(
    [
        {
            "xmin": legend_x - 0.35,
            "xmax": legend_x + 0.35,
            "ymin": legend_y_base + 1.2 - 0.22,
            "ymax": legend_y_base + 1.2 + 0.22,
        }
    ]
)
legend_tri = [
    {"x": legend_x - 0.3, "y": legend_y_base + 0.2, "group": "legend_tri"},
    {"x": legend_x - 0.3, "y": legend_y_base - 0.2, "group": "legend_tri"},
    {"x": legend_x + 0.25, "y": legend_y_base, "group": "legend_tri"},
]
df_legend_tri = pd.DataFrame(legend_tri)

# Plot
plot = (
    ggplot()
    # Active branches
    + geom_segment(aes(x="x", y="y", xend="xend", yend="yend"), data=df_active, size=1.8, color="#4A4A4A")
    # Pruned branches
    + geom_segment(
        aes(x="x", y="y", xend="xend", yend="yend"), data=df_pruned, size=1.2, color="#B0B0B0", linetype="dashed"
    )
    # Pruning X marks
    + geom_segment(aes(x="x", y="y", xend="xend", yend="yend"), data=df_prune_marks, size=2.0, color="#CC3333")
    # Decision nodes as rectangles (geom_rect - distinctive lets-plot feature)
    + geom_rect(
        aes(xmin="xmin", xmax="xmax", ymin="ymin", ymax="ymax"),
        data=df_decision_rects,
        fill="#306998",
        color="#1A3D5C",
        size=1.5,
        alpha=0.9,
    )
    # Chance nodes as circles
    + geom_point(aes(x="x", y="y"), data=df_chance, shape=21, size=16, fill="#E8A838", color="#B8841A", stroke=1.8)
    # Terminal nodes as right-pointing triangles (geom_polygon - distinctive lets-plot feature)
    + geom_polygon(aes(x="x", y="y", group="group"), data=df_triangles, fill="#6AAB6A", color="#4A8B4A", size=1.2)
    # Branch labels with background (geom_label - distinctive lets-plot feature)
    + geom_label(
        aes(x="x", y="y", label="label"),
        data=df_branch_labels,
        size=11,
        color="#2A2A2A",
        fill="white",
        alpha=0.85,
        label_padding=0.3,
        label_r=0.15,
        label_size=0,
    )
    # EMV and payoff value labels
    + geom_text(aes(x="x", y="y", label="label"), data=df_values, size=11, color="#1A1A1A", fontface="bold")
    # Legend: decision rect
    + geom_rect(
        aes(xmin="xmin", xmax="xmax", ymin="ymin", ymax="ymax"),
        data=df_legend_decision_rect,
        fill="#306998",
        color="#1A3D5C",
        size=1.0,
    )
    # Legend: chance circle
    + geom_point(
        aes(x="x", y="y"),
        data=pd.DataFrame([{"x": legend_x, "y": legend_y_base + 0.6}]),
        shape=21,
        size=10,
        fill="#E8A838",
        color="#B8841A",
        stroke=1.2,
    )
    # Legend: terminal triangle
    + geom_polygon(aes(x="x", y="y", group="group"), data=df_legend_tri, fill="#6AAB6A", color="#4A8B4A", size=0.8)
    # Legend labels
    + geom_text(aes(x="x", y="y", label="label"), data=df_legend_labels, size=10, color="#4A4A4A", hjust=0)
    + scale_x_continuous(limits=[-1.5, 23])
    + scale_y_continuous(limits=[-0.2, 10])
    + labs(title="Product Launch Strategy · tree-decision · letsplot · pyplots.ai")
    + theme_void()
    + flavor_solarized_light()
    + theme(plot_title=element_text(size=26, hjust=0.5, face="bold"), plot_margin=[50, 30, 20, 20])
    + ggsize(1600, 900)
)

# Save
ggsave(plot, "plot.png", path=".", scale=3)
ggsave(plot, "plot.html", path=".")
