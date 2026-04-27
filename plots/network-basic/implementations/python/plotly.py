""" anyplot.ai
network-basic: Basic Network Graph
Library: plotly 6.7.0 | Python 3.14.4
Quality: 86/100 | Updated: 2026-04-27
"""

import os
import sys


# Prevent this file from shadowing the installed plotly package
_here = os.path.dirname(os.path.abspath(__file__))
sys.path = [p for p in sys.path if os.path.abspath(p) != _here]
del _here

import numpy as np
import plotly.graph_objects as go


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Okabe-Ito palette — first series always #009E73
GROUP_COLORS = ["#009E73", "#D55E00", "#0072B2", "#CC79A7"]
GROUP_NAMES = ["Research", "Engineering", "Management", "Marketing"]

# Data: social network with 20 people across 4 teams of varying size
np.random.seed(42)

nodes = [
    # Research (5 members)
    {"id": 0, "label": "Alice", "group": 0},
    {"id": 1, "label": "Bob", "group": 0},
    {"id": 2, "label": "Carol", "group": 0},
    {"id": 3, "label": "David", "group": 0},
    {"id": 4, "label": "Eve", "group": 0},
    # Engineering (6 members — densely connected)
    {"id": 5, "label": "Frank", "group": 1},
    {"id": 6, "label": "Grace", "group": 1},
    {"id": 7, "label": "Henry", "group": 1},
    {"id": 8, "label": "Ivy", "group": 1},
    {"id": 9, "label": "Jack", "group": 1},
    {"id": 10, "label": "Kim", "group": 1},
    # Management (4 members — sparse, but high cross-team reach)
    {"id": 11, "label": "Leo", "group": 2},
    {"id": 12, "label": "Mia", "group": 2},
    {"id": 13, "label": "Noah", "group": 2},
    {"id": 14, "label": "Olivia", "group": 2},
    # Marketing (5 members)
    {"id": 15, "label": "Paul", "group": 3},
    {"id": 16, "label": "Quinn", "group": 3},
    {"id": 17, "label": "Ryan", "group": 3},
    {"id": 18, "label": "Sara", "group": 3},
    {"id": 19, "label": "Tom", "group": 3},
]

edges = [
    # Research — moderate connectivity
    (0, 1),
    (0, 2),
    (1, 2),
    (1, 3),
    (2, 4),
    # Engineering — tight-knit, many connections
    (5, 6),
    (5, 7),
    (5, 8),
    (6, 7),
    (6, 9),
    (7, 8),
    (7, 9),
    (8, 10),
    (9, 10),
    # Management — sparse (hub nodes bridging teams)
    (11, 12),
    (12, 13),
    (13, 14),
    # Marketing — moderate connectivity
    (15, 16),
    (15, 17),
    (16, 18),
    (17, 18),
    (17, 19),
    # Cross-team bridges
    (0, 5),  # Alice ↔ Frank
    (4, 11),  # Eve ↔ Leo
    (9, 15),  # Jack ↔ Paul
    (14, 19),  # Olivia ↔ Tom
    (2, 6),  # Carol ↔ Grace
    (10, 13),  # Kim ↔ Noah
    (3, 12),  # David ↔ Mia
    (16, 11),  # Quinn ↔ Leo
]

# Spring layout — circular initialisation avoids diagonal bias
n = len(nodes)
angles = np.linspace(0, 2 * np.pi, n, endpoint=False)
positions = np.column_stack([np.cos(angles), np.sin(angles)]) * 0.8
k = 0.35

for iteration in range(250):
    displacement = np.zeros((n, 2))
    for i in range(n):
        for j in range(i + 1, n):
            diff = positions[i] - positions[j]
            dist = max(np.linalg.norm(diff), 0.01)
            force = (k * k / dist) * (diff / dist)
            displacement[i] += force
            displacement[j] -= force
    for src, tgt in edges:
        diff = positions[src] - positions[tgt]
        dist = max(np.linalg.norm(diff), 0.01)
        force = (dist * dist / k) * (diff / dist)
        displacement[src] -= force
        displacement[tgt] += force
    cooling = 1 - iteration / 250
    for i in range(n):
        disp_norm = np.linalg.norm(displacement[i])
        if disp_norm > 0:
            positions[i] += (displacement[i] / disp_norm) * min(disp_norm, 0.1 * cooling)

pos_min = positions.min(axis=0)
pos_max = positions.max(axis=0)
positions = (positions - pos_min) / (pos_max - pos_min + 1e-6) * 0.82 + 0.09
pos = {node["id"]: positions[i] for i, node in enumerate(nodes)}

# Node degrees
degrees = {node["id"]: 0 for node in nodes}
for src, tgt in edges:
    degrees[src] += 1
    degrees[tgt] += 1

# Edge trace
edge_x, edge_y = [], []
for src, tgt in edges:
    x0, y0 = pos[src]
    x1, y1 = pos[tgt]
    edge_x.extend([x0, x1, None])
    edge_y.extend([y0, y1, None])

edge_color = "rgba(80,80,80,0.30)" if THEME == "light" else "rgba(200,200,200,0.25)"
edge_trace = go.Scatter(
    x=edge_x, y=edge_y, mode="lines", line={"width": 2, "color": edge_color}, hoverinfo="none", showlegend=False
)

# Node traces — one per group so the legend shows communities
node_traces = []
for group_id, (color, name) in enumerate(zip(GROUP_COLORS, GROUP_NAMES, strict=False)):
    group_nodes = [node for node in nodes if node["group"] == group_id]
    node_x = [pos[node["id"]][0] for node in group_nodes]
    node_y = [pos[node["id"]][1] for node in group_nodes]
    node_sizes = [26 + degrees[node["id"]] * 7 for node in group_nodes]
    node_labels = [node["label"] for node in group_nodes]

    # Build neighbour list for rich hover tooltips (Plotly hovertemplate + customdata)
    customdata = []
    for node in group_nodes:
        nid = node["id"]
        nbrs = []
        for src, tgt in edges:
            if src == nid:
                nbrs.append(nodes[tgt]["label"])
            elif tgt == nid:
                nbrs.append(nodes[src]["label"])
        customdata.append([degrees[nid], ", ".join(nbrs) if nbrs else "—"])

    node_traces.append(
        go.Scatter(
            x=node_x,
            y=node_y,
            mode="markers+text",
            marker={"size": node_sizes, "color": color, "line": {"width": 2, "color": PAGE_BG}},
            text=node_labels,
            textposition="middle center",
            textfont={"size": 16, "color": "#FFFFFF", "family": "Arial Black"},
            customdata=customdata,
            hovertemplate=(
                "<b>%{text}</b><br>"
                f"Team: {name}<br>"
                "Connections: %{customdata[0]}<br>"
                "Connected to: %{customdata[1]}"
                "<extra></extra>"
            ),
            name=name,
            legendgroup=name,
        )
    )

# Figure
fig = go.Figure(data=[edge_trace] + node_traces)

fig.update_layout(
    title={
        "text": "network-basic · plotly · anyplot.ai",
        "font": {"size": 28, "color": INK},
        "x": 0.5,
        "xanchor": "center",
    },
    showlegend=True,
    legend={
        "title": {"text": "Teams", "font": {"size": 20, "color": INK}},
        "font": {"size": 18, "color": INK_SOFT},
        "bgcolor": ELEVATED_BG,
        "bordercolor": INK_SOFT,
        "borderwidth": 1,
        "x": 0.02,
        "y": 0.98,
        "xanchor": "left",
        "yanchor": "top",
    },
    paper_bgcolor=PAGE_BG,
    plot_bgcolor=PAGE_BG,
    font={"color": INK},
    xaxis={"showgrid": False, "zeroline": False, "showticklabels": False, "range": [-0.05, 1.05]},
    yaxis={"showgrid": False, "zeroline": False, "showticklabels": False, "range": [-0.05, 1.05]},
    margin={"l": 20, "r": 20, "t": 80, "b": 20},
)

# Save
fig.write_image(f"plot-{THEME}.png", width=1600, height=900, scale=3)
fig.write_html(f"plot-{THEME}.html", include_plotlyjs="cdn")
