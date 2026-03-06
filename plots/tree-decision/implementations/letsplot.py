""" pyplots.ai
tree-decision: Decision Tree Visualization with Probabilities
Library: letsplot 4.8.2 | Python 3.14.3
Quality: 87/100 | Created: 2026-03-06
"""

import pandas as pd
from lets_plot import (
    LetsPlot,
    aes,
    element_rect,
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
    {"id": "D1", "type": "decision", "x": 0, "y": 5.0, "value": "EMV $450K"},
    {"id": "C1", "type": "chance", "x": 5, "y": 8.0, "value": "EMV $450K"},
    {"id": "T6", "type": "terminal", "x": 5, "y": 1.5, "value": "$250K"},
    {"id": "T1", "type": "terminal", "x": 10, "y": 10.5, "value": "$900K"},
    {"id": "D2", "type": "decision", "x": 10, "y": 7.5, "value": "EMV $440K"},
    {"id": "T2", "type": "terminal", "x": 10, "y": 4.5, "value": "-$200K"},
    {"id": "C2", "type": "chance", "x": 15, "y": 9.8, "value": "EMV $440K"},
    {"id": "T3", "type": "terminal", "x": 15, "y": 5.5, "value": "$350K"},
    {"id": "T4", "type": "terminal", "x": 20, "y": 11.5, "value": "$600K"},
    {"id": "T5", "type": "terminal", "x": 20, "y": 7.8, "value": "$200K"},
]

branch_records = [
    {"from_id": "D1", "to_id": "C1", "label": "Launch Product", "pruned": False, "is_prob": False},
    {"from_id": "D1", "to_id": "T6", "label": "License Tech", "pruned": True, "is_prob": False},
    {"from_id": "C1", "to_id": "T1", "label": "Strong (0.3)", "pruned": False, "is_prob": True},
    {"from_id": "C1", "to_id": "D2", "label": "Moderate (0.5)", "pruned": False, "is_prob": True},
    {"from_id": "C1", "to_id": "T2", "label": "Weak (0.2)", "pruned": False, "is_prob": True},
    {"from_id": "D2", "to_id": "C2", "label": "Scale Up", "pruned": False, "is_prob": False},
    {"from_id": "D2", "to_id": "T3", "label": "Maintain", "pruned": True, "is_prob": False},
    {"from_id": "C2", "to_id": "T4", "label": "Success (0.6)", "pruned": False, "is_prob": True},
    {"from_id": "C2", "to_id": "T5", "label": "Setback (0.4)", "pruned": False, "is_prob": True},
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

# Branch labels - probability labels use italic, decision labels use bold
prob_label_records = []
decision_label_records = []
for b in branch_records:
    f = node_lookup[b["from_id"]]
    t = node_lookup[b["to_id"]]
    mid_x = (f["x"] + t["x"]) / 2
    label_y = t["y"] + 0.5
    rec = {"x": mid_x, "y": label_y, "label": b["label"]}
    if b["is_prob"]:
        prob_label_records.append(rec)
    else:
        decision_label_records.append(rec)
df_prob_labels = pd.DataFrame(prob_label_records)
df_decision_labels = pd.DataFrame(decision_label_records)

# Separate nodes by type
df_decision = pd.DataFrame([r for r in node_records if r["type"] == "decision"])
df_chance = pd.DataFrame([r for r in node_records if r["type"] == "chance"])
df_terminal = pd.DataFrame([r for r in node_records if r["type"] == "terminal"])

# Decision nodes as proper rectangles using geom_rect
rect_half = 0.6
df_decision_rects = pd.DataFrame(
    [
        {
            "xmin": r["x"] - rect_half,
            "xmax": r["x"] + rect_half,
            "ymin": r["y"] - rect_half * 0.75,
            "ymax": r["y"] + rect_half * 0.75,
        }
        for r in node_records
        if r["type"] == "decision"
    ]
)

# Right-pointing triangles for terminal nodes using geom_polygon
tri_w = 0.55
tri_h = 0.38
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

# Value labels: EMV below non-terminal nodes, payoffs right of terminals
emv_label_records = []
payoff_label_records = []
for r in node_records:
    if r["type"] == "terminal":
        payoff_label_records.append({"x": r["x"] + 1.1, "y": r["y"], "label": r["value"]})
    else:
        emv_label_records.append({"x": r["x"], "y": r["y"] - 0.8, "label": r["value"]})
df_emv_labels = pd.DataFrame(emv_label_records)
df_payoff_labels = pd.DataFrame(payoff_label_records)

# Pruning cross marks
prune_mark_records = []
for b in branch_records:
    if b["pruned"]:
        f = node_lookup[b["from_id"]]
        t = node_lookup[b["to_id"]]
        cx = f["x"] + (t["x"] - f["x"]) * 0.4
        cy = f["y"] + (t["y"] - f["y"]) * 0.4
        d = 0.28
        prune_mark_records.append({"x": cx - d, "y": cy - d, "xend": cx + d, "yend": cy + d})
        prune_mark_records.append({"x": cx - d, "y": cy + d, "xend": cx + d, "yend": cy - d})
df_prune_marks = pd.DataFrame(prune_mark_records)

# Legend data
legend_y_base = 1.0
legend_x = 16.0
df_legend_labels = pd.DataFrame(
    [
        {"x": legend_x + 0.9, "y": legend_y_base + 1.4, "label": "Decision Node"},
        {"x": legend_x + 0.9, "y": legend_y_base + 0.7, "label": "Chance Node"},
        {"x": legend_x + 0.9, "y": legend_y_base, "label": "Terminal Node"},
    ]
)
df_legend_decision_rect = pd.DataFrame(
    [
        {
            "xmin": legend_x - 0.35,
            "xmax": legend_x + 0.35,
            "ymin": legend_y_base + 1.4 - 0.22,
            "ymax": legend_y_base + 1.4 + 0.22,
        }
    ]
)
legend_tri = [
    {"x": legend_x - 0.3, "y": legend_y_base + 0.2, "group": "legend_tri"},
    {"x": legend_x - 0.3, "y": legend_y_base - 0.2, "group": "legend_tri"},
    {"x": legend_x + 0.25, "y": legend_y_base, "group": "legend_tri"},
]
df_legend_tri = pd.DataFrame(legend_tri)

# Subtle level shading bands to distinguish tree depth
level_bands = pd.DataFrame(
    [
        {"xmin": -1.5, "xmax": 2.5, "ymin": -0.5, "ymax": 13.0, "level": "Stage 1"},
        {"xmin": 7.5, "xmax": 12.5, "ymin": -0.5, "ymax": 13.0, "level": "Stage 2"},
    ]
)

# Plot
plot = (
    ggplot()
    # Subtle depth shading bands
    + geom_rect(
        aes(xmin="xmin", xmax="xmax", ymin="ymin", ymax="ymax"),
        data=level_bands,
        fill="#CCCCCC",
        color="transparent",
        size=0,
        alpha=0.08,
    )
    # Active branches
    + geom_segment(aes(x="x", y="y", xend="xend", yend="yend"), data=df_active, size=2.0, color="#3A3A3A")
    # Pruned branches
    + geom_segment(
        aes(x="x", y="y", xend="xend", yend="yend"), data=df_pruned, size=1.2, color="#B8B8B8", linetype="dashed"
    )
    # Pruning X marks
    + geom_segment(aes(x="x", y="y", xend="xend", yend="yend"), data=df_prune_marks, size=2.5, color="#CC3333")
    # Decision nodes as rectangles
    + geom_rect(
        aes(xmin="xmin", xmax="xmax", ymin="ymin", ymax="ymax"),
        data=df_decision_rects,
        fill="#306998",
        color="#1A3D5C",
        size=1.8,
        alpha=0.92,
    )
    # Chance nodes as circles
    + geom_point(aes(x="x", y="y"), data=df_chance, shape=21, size=18, fill="#E8A838", color="#B07820", stroke=2.0)
    # Terminal nodes as right-pointing triangles
    + geom_polygon(aes(x="x", y="y", group="group"), data=df_triangles, fill="#6AAB6A", color="#3D7A3D", size=1.4)
    # Probability branch labels (italic style)
    + geom_label(
        aes(x="x", y="y", label="label"),
        data=df_prob_labels,
        size=11,
        color="#555555",
        fill="white",
        alpha=0.88,
        label_padding=0.35,
        label_r=0.18,
        label_size=0,
        fontface="italic",
    )
    # Decision branch labels (bold style)
    + geom_label(
        aes(x="x", y="y", label="label"),
        data=df_decision_labels,
        size=12,
        color="#1A1A1A",
        fill="white",
        alpha=0.88,
        label_padding=0.35,
        label_r=0.18,
        label_size=0.3,
        fontface="bold",
    )
    # EMV labels (bold, dark blue)
    + geom_text(aes(x="x", y="y", label="label"), data=df_emv_labels, size=12, color="#1A3D5C", fontface="bold")
    # Payoff labels (bold, dark green for positive distinction)
    + geom_text(aes(x="x", y="y", label="label"), data=df_payoff_labels, size=12, color="#2D5A2D", fontface="bold")
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
        data=pd.DataFrame([{"x": legend_x, "y": legend_y_base + 0.7}]),
        shape=21,
        size=10,
        fill="#E8A838",
        color="#B07820",
        stroke=1.2,
    )
    # Legend: terminal triangle
    + geom_polygon(aes(x="x", y="y", group="group"), data=df_legend_tri, fill="#6AAB6A", color="#3D7A3D", size=0.8)
    # Legend labels
    + geom_text(aes(x="x", y="y", label="label"), data=df_legend_labels, size=10, color="#4A4A4A", hjust=0)
    + scale_x_continuous(limits=[-2, 23])
    + scale_y_continuous(limits=[-0.5, 13.0])
    + labs(title="Product Launch Strategy · tree-decision · letsplot · pyplots.ai")
    + theme_void()
    + flavor_solarized_light()
    + theme(
        plot_title=element_text(size=28, hjust=0.5, face="bold"),
        plot_margin=[60, 40, 30, 30],
        plot_background=element_rect(color="transparent"),
        plot_subtitle=element_text(size=14, hjust=0.5, color="#666666"),
    )
    + ggsize(1600, 900)
)

# Save
ggsave(plot, "plot.png", path=".", scale=3)
ggsave(plot, "plot.html", path=".")
