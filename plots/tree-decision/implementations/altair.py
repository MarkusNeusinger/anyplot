"""pyplots.ai
tree-decision: Decision Tree Visualization with Probabilities
Library: altair 6.0.0 | Python 3.14.3
Quality: 87/100 | Created: 2026-03-06
"""

import altair as alt
import pandas as pd


# Data - Two-stage investment decision tree
nodes_df = pd.DataFrame(
    [
        {
            "id": "D1",
            "type": "decision",
            "x": 50,
            "y": 300,
            "emv": "$152K",
            "label": "",
            "payoff": "",
            "detail": "Root decision | EMV=$152K | Optimal: Invest Large",
            "pruned": False,
        },
        {
            "id": "C1",
            "type": "chance",
            "x": 300,
            "y": 150,
            "emv": "$152K",
            "label": "Invest\nLarge",
            "payoff": "",
            "detail": "Chance | EMV=$152K | 0.40x300+0.35x120+0.25x(-40)",
            "pruned": False,
        },
        {
            "id": "C2",
            "type": "chance",
            "x": 300,
            "y": 470,
            "emv": "$95K",
            "label": "Invest\nSmall",
            "payoff": "",
            "detail": "Chance (pruned) | EMV=$95K | 0.40x180+0.35x90+0.25x20",
            "pruned": True,
        },
        {
            "id": "T1",
            "type": "terminal",
            "x": 530,
            "y": 55,
            "emv": "",
            "label": "High Demand",
            "payoff": "$300K",
            "detail": "High Demand | Payoff=$300K | Prob=0.40",
            "pruned": False,
        },
        {
            "id": "T2",
            "type": "terminal",
            "x": 530,
            "y": 160,
            "emv": "",
            "label": "Moderate",
            "payoff": "$120K",
            "detail": "Moderate Demand | Payoff=$120K | Prob=0.35",
            "pruned": False,
        },
        {
            "id": "T3",
            "type": "terminal",
            "x": 530,
            "y": 255,
            "emv": "",
            "label": "Low Demand",
            "payoff": "$-40K",
            "detail": "Low Demand | Payoff=-$40K | Prob=0.25",
            "pruned": False,
        },
        {
            "id": "T4",
            "type": "terminal",
            "x": 530,
            "y": 380,
            "emv": "",
            "label": "High Demand",
            "payoff": "$180K",
            "detail": "High Demand | Payoff=$180K | Prob=0.40",
            "pruned": True,
        },
        {
            "id": "T5",
            "type": "terminal",
            "x": 530,
            "y": 470,
            "emv": "",
            "label": "Moderate",
            "payoff": "$90K",
            "detail": "Moderate Demand | Payoff=$90K | Prob=0.35",
            "pruned": True,
        },
        {
            "id": "T6",
            "type": "terminal",
            "x": 530,
            "y": 555,
            "emv": "",
            "label": "Low Demand",
            "payoff": "$20K",
            "detail": "Low Demand | Payoff=$20K | Prob=0.25",
            "pruned": True,
        },
    ]
)

edges_df = pd.DataFrame(
    [
        {"x": 50, "y": 300, "x2": 300, "y2": 150, "label": "Invest Large", "prob": "", "pruned": False},
        {"x": 50, "y": 300, "x2": 300, "y2": 470, "label": "Invest Small", "prob": "", "pruned": True},
        {"x": 300, "y": 150, "x2": 530, "y2": 55, "label": "", "prob": "0.40", "pruned": False},
        {"x": 300, "y": 150, "x2": 530, "y2": 160, "label": "", "prob": "0.35", "pruned": False},
        {"x": 300, "y": 150, "x2": 530, "y2": 255, "label": "", "prob": "0.25", "pruned": False},
        {"x": 300, "y": 470, "x2": 530, "y2": 380, "label": "", "prob": "0.40", "pruned": True},
        {"x": 300, "y": 470, "x2": 530, "y2": 470, "label": "", "prob": "0.35", "pruned": True},
        {"x": 300, "y": 470, "x2": 530, "y2": 555, "label": "", "prob": "0.25", "pruned": True},
    ]
)

# Colorblind-safe palette: blue (decision), orange (chance), teal (terminal)
DECISION_COLOR = "#306998"
CHANCE_COLOR = "#E67E22"
TERMINAL_COLOR = "#1ABC9C"
DECISION_STROKE = "#1A3A5C"
CHANCE_STROKE = "#A85A13"
TERMINAL_STROKE = "#148F77"

# Shared scales
x_scale = alt.Scale(domain=[-30, 680])
y_scale = alt.Scale(domain=[620, -30])
x_enc = alt.X("x:Q", scale=x_scale, axis=None)
y_enc = alt.Y("y:Q", scale=y_scale, axis=None)

# Interactive hover selection (Altair-distinctive feature)
hover = alt.selection_point(on="pointerover", fields=["id"], empty=False)

node_tooltip = [
    alt.Tooltip("id:N", title="Node"),
    alt.Tooltip("type:N", title="Type"),
    alt.Tooltip("detail:N", title="Info"),
]

# --- Subtle background panel behind optimal path (storytelling) ---
optimal_path_bg = pd.DataFrame([{"x": 20, "y": -10, "x2": 670, "y2": 285}])
optimal_bg = (
    alt.Chart(optimal_path_bg)
    .mark_rect(cornerRadius=16, color="#E8F4F8", opacity=0.45, stroke="#B0D4E3", strokeWidth=1.5, strokeDash=[6, 4])
    .encode(x=alt.X("x:Q", scale=x_scale, axis=None), y=alt.Y("y:Q", scale=y_scale, axis=None), x2="x2:Q", y2="y2:Q")
)

optimal_label = (
    alt.Chart(pd.DataFrame([{"x": 640, "y": 275}]))
    .mark_text(fontSize=12, fontStyle="italic", color="#5A9BB5", align="right", fontWeight="bold")
    .encode(
        x=alt.X("x:Q", scale=x_scale, axis=None),
        y=alt.Y("y:Q", scale=y_scale, axis=None),
        text=alt.value("optimal path"),
    )
)

# --- Edges ---
active_edges = edges_df[~edges_df["pruned"]]
pruned_edges = edges_df[edges_df["pruned"]]

active_lines = (
    alt.Chart(active_edges).mark_rule(strokeWidth=3.5, color="#3A3A3A").encode(x=x_enc, y=y_enc, x2="x2:Q", y2="y2:Q")
)

pruned_lines = (
    alt.Chart(pruned_edges)
    .mark_rule(strokeWidth=2, strokeDash=[8, 6], opacity=0.28, color="#999999")
    .encode(x=x_enc, y=y_enc, x2="x2:Q", y2="y2:Q")
)

# Pruned cross mark
pruned_cross = (
    alt.Chart(pd.DataFrame([{"cx": 140, "cy": 405}]))
    .mark_text(fontSize=32, fontWeight="bold", color="#C0392B", text="\u2715")
    .encode(x=alt.X("cx:Q", scale=x_scale, axis=None), y=alt.Y("cy:Q", scale=y_scale, axis=None))
)

# --- Nodes: unified with conditional opacity (reduces repetition) ---
chance_df = nodes_df[nodes_df["type"] == "chance"]
terminal_df = nodes_df[nodes_df["type"] == "terminal"]
decision_df = nodes_df[nodes_df["type"] == "decision"]

decision_nodes = (
    alt.Chart(decision_df)
    .mark_square(size=2200, color=DECISION_COLOR, stroke=DECISION_STROKE, strokeWidth=2.5)
    .encode(x=x_enc, y=y_enc, size=alt.condition(hover, alt.value(2600), alt.value(2200)), tooltip=node_tooltip)
    .add_params(hover)
)

chance_nodes = (
    alt.Chart(chance_df)
    .mark_circle(size=2200, color=CHANCE_COLOR, stroke=CHANCE_STROKE, strokeWidth=2.5)
    .encode(
        x=x_enc,
        y=y_enc,
        opacity=alt.condition(alt.datum.pruned == True, alt.value(0.30), alt.value(1.0)),  # noqa: E712
        size=alt.condition(hover, alt.value(2600), alt.value(2200)),
        tooltip=node_tooltip,
    )
    .add_params(hover)
)

terminal_nodes = (
    alt.Chart(terminal_df)
    .mark_point(
        shape="triangle-right", size=1600, filled=True, color=TERMINAL_COLOR, stroke=TERMINAL_STROKE, strokeWidth=2.5
    )
    .encode(
        x=x_enc,
        y=y_enc,
        opacity=alt.condition(alt.datum.pruned == True, alt.value(0.30), alt.value(1.0)),  # noqa: E712
        size=alt.condition(hover, alt.value(2000), alt.value(1600)),
        tooltip=node_tooltip,
    )
    .add_params(hover)
)

# --- Text labels ---
emv_labels = (
    alt.Chart(nodes_df)
    .transform_filter(alt.datum.emv != "")
    .mark_text(fontSize=18, fontWeight="bold", dy=-34, color="#1A1A1A")
    .encode(x=x_enc, y=y_enc, text="emv:N")
)

payoff_labels = (
    alt.Chart(nodes_df)
    .transform_filter(alt.datum.payoff != "")
    .mark_text(fontSize=17, fontWeight="bold", dx=55, align="left", color="#1A1A1A")
    .encode(
        x=x_enc,
        y=y_enc,
        text="payoff:N",
        opacity=alt.condition(alt.datum.pruned == True, alt.value(0.35), alt.value(1.0)),  # noqa: E712
    )
)

terminal_desc = (
    alt.Chart(nodes_df)
    .transform_filter(alt.datum.type == "terminal")
    .mark_text(fontSize=14, dx=55, dy=18, align="left", color="#666666")
    .encode(
        x=x_enc,
        y=y_enc,
        text="label:N",
        opacity=alt.condition(alt.datum.pruned == True, alt.value(0.30), alt.value(1.0)),  # noqa: E712
    )
)

# Edge midpoint labels
edges_df["mx"] = (edges_df["x"] + edges_df["x2"]) / 2
edges_df["my"] = (edges_df["y"] + edges_df["y2"]) / 2

branch_label_df = edges_df[edges_df["label"] != ""]
prob_label_df = edges_df[edges_df["prob"] != ""]

branch_labels = (
    alt.Chart(branch_label_df)
    .mark_text(fontSize=16, fontWeight="bold", dy=-16, color=DECISION_COLOR)
    .encode(
        x=alt.X("mx:Q", scale=x_scale, axis=None),
        y=alt.Y("my:Q", scale=y_scale, axis=None),
        text="label:N",
        opacity=alt.condition(alt.datum.pruned == True, alt.value(0.35), alt.value(1.0)),  # noqa: E712
    )
)

prob_labels = (
    alt.Chart(prob_label_df)
    .mark_text(fontSize=15, dy=-14, color=CHANCE_STROKE, fontWeight="bold")
    .encode(
        x=alt.X("mx:Q", scale=x_scale, axis=None),
        y=alt.Y("my:Q", scale=y_scale, axis=None),
        text="prob:N",
        opacity=alt.condition(alt.datum.pruned == True, alt.value(0.30), alt.value(1.0)),  # noqa: E712
    )
)

# --- Legend ---
legend_data = pd.DataFrame(
    [
        {"lx": 100, "ly": 590, "label": "Decision Node", "shape": "square"},
        {"lx": 280, "ly": 590, "label": "Chance Node", "shape": "circle"},
        {"lx": 460, "ly": 590, "label": "Terminal Node", "shape": "triangle"},
    ]
)

legend_sq = (
    alt.Chart(legend_data.query("shape == 'square'"))
    .mark_square(size=550, color=DECISION_COLOR, stroke=DECISION_STROKE, strokeWidth=1.5)
    .encode(x=alt.X("lx:Q", scale=x_scale, axis=None), y=alt.Y("ly:Q", scale=y_scale, axis=None))
)
legend_ci = (
    alt.Chart(legend_data.query("shape == 'circle'"))
    .mark_circle(size=550, color=CHANCE_COLOR, stroke=CHANCE_STROKE, strokeWidth=1.5)
    .encode(x=alt.X("lx:Q", scale=x_scale, axis=None), y=alt.Y("ly:Q", scale=y_scale, axis=None))
)
legend_tr = (
    alt.Chart(legend_data.query("shape == 'triangle'"))
    .mark_point(
        shape="triangle-right", size=450, filled=True, color=TERMINAL_COLOR, stroke=TERMINAL_STROKE, strokeWidth=1.5
    )
    .encode(x=alt.X("lx:Q", scale=x_scale, axis=None), y=alt.Y("ly:Q", scale=y_scale, axis=None))
)
legend_txt = (
    alt.Chart(legend_data)
    .mark_text(fontSize=14, dx=20, align="left", color="#555555")
    .encode(x=alt.X("lx:Q", scale=x_scale, axis=None), y=alt.Y("ly:Q", scale=y_scale, axis=None), text="label:N")
)

# Combine all layers
chart = (
    alt.layer(
        optimal_bg,
        active_lines,
        pruned_lines,
        pruned_cross,
        decision_nodes,
        chance_nodes,
        terminal_nodes,
        emv_labels,
        payoff_labels,
        terminal_desc,
        branch_labels,
        prob_labels,
        optimal_label,
        legend_sq,
        legend_ci,
        legend_tr,
        legend_txt,
    )
    .properties(
        width=1600,
        height=900,
        title=alt.Title("tree-decision \u00b7 altair \u00b7 pyplots.ai", fontSize=28, anchor="start", offset=12),
    )
    .configure_view(strokeWidth=0)
)

chart.save("plot.png", scale_factor=3.0)
chart.save("plot.html")
