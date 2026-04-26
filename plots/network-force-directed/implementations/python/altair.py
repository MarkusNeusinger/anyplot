""" anyplot.ai
network-force-directed: Force-Directed Graph
Library: altair 6.1.0 | Python 3.14.4
Quality: 85/100 | Updated: 2026-04-26
"""

import os

import altair as alt
import numpy as np
import pandas as pd


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
EDGE_COLOR = "#6B6A63" if THEME == "light" else "#A8A79F"

# Okabe-Ito categorical palette (first series is always #009E73)
OKABE_ITO = ["#009E73", "#D55E00", "#0072B2"]

# Data: a 50-node organisational network with three communities
np.random.seed(42)

community_sizes = [18, 17, 15]
community_names = ["Engineering", "Marketing", "Sales"]

nodes = []
node_id = 0
for comm_idx, size in enumerate(community_sizes):
    for _ in range(size):
        nodes.append({"id": node_id, "community": community_names[comm_idx]})
        node_id += 1

edges = []
# Intra-community edges (dense)
for start, end in [(0, 18), (18, 35), (35, 50)]:
    for i in range(start, end):
        for j in range(i + 1, end):
            if np.random.random() < 0.3:
                edges.append((i, j))

# Inter-community bridges (sparse)
edges.extend([(0, 18), (5, 20), (10, 25), (18, 35), (22, 40), (30, 45), (8, 38), (15, 48)])

# Fruchterman-Reingold force-directed layout
n = len(nodes)
positions = np.random.rand(n, 2) * 2 - 1
k = 0.5
iterations = 200

for iteration in range(iterations):
    displacement = np.zeros((n, 2))
    for i in range(n):
        for j in range(i + 1, n):
            diff = positions[i] - positions[j]
            dist = max(np.linalg.norm(diff), 0.01)
            repulsive = (k * k / dist) * (diff / dist)
            displacement[i] += repulsive
            displacement[j] -= repulsive
    for src, tgt in edges:
        diff = positions[src] - positions[tgt]
        dist = max(np.linalg.norm(diff), 0.01)
        attractive = (dist * dist / k) * (diff / dist)
        displacement[src] -= attractive
        displacement[tgt] += attractive
    temperature = 1 - iteration / iterations
    for i in range(n):
        disp_norm = np.linalg.norm(displacement[i])
        if disp_norm > 0:
            positions[i] += (displacement[i] / disp_norm) * min(disp_norm, 0.15 * temperature)

pos_min = positions.min(axis=0)
pos_max = positions.max(axis=0)
positions = (positions - pos_min) / (pos_max - pos_min + 1e-6) * 0.9 + 0.05

# Node-level summary
degrees = {node["id"]: 0 for node in nodes}
for src, tgt in edges:
    degrees[src] += 1
    degrees[tgt] += 1

node_df = pd.DataFrame(
    {
        "id": [node["id"] for node in nodes],
        "x": positions[:, 0],
        "y": positions[:, 1],
        "community": [node["community"] for node in nodes],
        "degree": [degrees[node["id"]] for node in nodes],
    }
)
node_df["size"] = node_df["degree"] * 30 + 200

# Edge segments (long-form, two rows per edge)
edge_data = []
for src, tgt in edges:
    edge_data.append({"edge_id": f"{src}-{tgt}", "x": positions[src][0], "y": positions[src][1], "order": 0})
    edge_data.append({"edge_id": f"{src}-{tgt}", "x": positions[tgt][0], "y": positions[tgt][1], "order": 1})
edge_df = pd.DataFrame(edge_data)

# Label only the four most-connected nodes to avoid clutter
hub_df = node_df.nlargest(4, "degree").copy()
hub_df["label"] = "Hub " + hub_df["id"].astype(str)

# Edges layer
edges_chart = (
    alt.Chart(edge_df)
    .mark_line(strokeWidth=1.4, opacity=0.55)
    .encode(
        x=alt.X("x:Q", axis=None),
        y=alt.Y("y:Q", axis=None),
        detail="edge_id:N",
        order="order:O",
        color=alt.value(EDGE_COLOR),
    )
)

# Nodes layer
nodes_chart = (
    alt.Chart(node_df)
    .mark_circle(stroke=PAGE_BG, strokeWidth=1.5, opacity=0.95)
    .encode(
        x=alt.X("x:Q", axis=None),
        y=alt.Y("y:Q", axis=None),
        size=alt.Size("size:Q", legend=None, scale=alt.Scale(range=[200, 900])),
        color=alt.Color(
            "community:N",
            scale=alt.Scale(domain=community_names, range=OKABE_ITO),
            legend=alt.Legend(title="Team", titleFontSize=18, labelFontSize=16, symbolSize=400),
        ),
        tooltip=[alt.Tooltip("community:N", title="Team"), alt.Tooltip("degree:Q", title="Connections")],
    )
)

# Hub labels
hub_labels = (
    alt.Chart(hub_df)
    .mark_text(fontSize=15, fontWeight="bold", color=INK, dy=-22)
    .encode(x=alt.X("x:Q", axis=None), y=alt.Y("y:Q", axis=None), text="label:N")
)

chart = (
    (edges_chart + nodes_chart + hub_labels)
    .properties(
        width=1600,
        height=900,
        background=PAGE_BG,
        title=alt.Title(
            "network-force-directed · altair · anyplot.ai", fontSize=28, color=INK, anchor="start", offset=20
        ),
    )
    .configure_view(fill=PAGE_BG, strokeWidth=0)
    .configure_legend(
        fillColor=ELEVATED_BG, strokeColor=INK_SOFT, labelColor=INK_SOFT, titleColor=INK, padding=12, cornerRadius=4
    )
)

chart.save(f"plot-{THEME}.png", scale_factor=3.0)
chart.save(f"plot-{THEME}.html")
