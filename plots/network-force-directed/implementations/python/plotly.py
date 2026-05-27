""" anyplot.ai
network-force-directed: Force-Directed Graph
Library: plotly 6.7.0 | Python 3.14.4
Quality: 89/100 | Updated: 2026-04-26
"""

import os

import numpy as np
import plotly.graph_objects as go


# Theme-adaptive chrome tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Okabe-Ito categorical palette (positions 1-3)
IMPRINT = ["#009E73", "#C475FD", "#4467A3"]

np.random.seed(42)

# A social network with 50 nodes in 3 communities
nodes = []
edges = []

community_sizes = [18, 17, 15]
community_names = ["Engineering", "Marketing", "Sales"]
node_id = 0

for comm_idx, size in enumerate(community_sizes):
    for _ in range(size):
        nodes.append({"id": node_id, "community": comm_idx})
        node_id += 1

# Intra-community edges (dense connections within communities)
for i in range(18):
    for j in range(i + 1, 18):
        if np.random.random() < 0.3:
            edges.append((i, j))

for i in range(18, 35):
    for j in range(i + 1, 35):
        if np.random.random() < 0.3:
            edges.append((i, j))

for i in range(35, 50):
    for j in range(i + 1, 50):
        if np.random.random() < 0.3:
            edges.append((i, j))

# Inter-community bridge edges
bridge_edges = [(0, 18), (5, 20), (10, 25), (18, 35), (22, 40), (30, 45), (8, 38), (15, 48)]
edges.extend(bridge_edges)

# Force-directed layout (Fruchterman-Reingold)
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
            repulsive_force = (k * k / dist) * (diff / dist)
            displacement[i] += repulsive_force
            displacement[j] -= repulsive_force

    for src, tgt in edges:
        diff = positions[src] - positions[tgt]
        dist = max(np.linalg.norm(diff), 0.01)
        attractive_force = (dist * dist / k) * (diff / dist)
        displacement[src] -= attractive_force
        displacement[tgt] += attractive_force

    temperature = 1 - iteration / iterations
    for i in range(n):
        disp_norm = np.linalg.norm(displacement[i])
        if disp_norm > 0:
            positions[i] += (displacement[i] / disp_norm) * min(disp_norm, 0.15 * temperature)

pos_min = positions.min(axis=0)
pos_max = positions.max(axis=0)
positions = (positions - pos_min) / (pos_max - pos_min + 1e-6) * 0.9 + 0.05
pos = {node["id"]: positions[i] for i, node in enumerate(nodes)}

# Node degrees
degrees = {node["id"]: 0 for node in nodes}
for src, tgt in edges:
    degrees[src] += 1
    degrees[tgt] += 1

fig = go.Figure()

# Edge trace (single trace via None separators — classic plotly network pattern)
edge_x = []
edge_y = []
for src, tgt in edges:
    x0, y0 = pos[src]
    x1, y1 = pos[tgt]
    edge_x.extend([x0, x1, None])
    edge_y.extend([y0, y1, None])

fig.add_trace(
    go.Scatter(
        x=edge_x,
        y=edge_y,
        mode="lines",
        line={"width": 1.5, "color": INK_SOFT},
        opacity=0.35,
        hoverinfo="none",
        showlegend=False,
    )
)

# Nodes grouped by community for legend
for comm_idx, comm_name in enumerate(community_names):
    comm_nodes = [node for node in nodes if node["community"] == comm_idx]
    x_vals = [pos[node["id"]][0] for node in comm_nodes]
    y_vals = [pos[node["id"]][1] for node in comm_nodes]
    sizes = [20 + degrees[node["id"]] * 5 for node in comm_nodes]
    hover_text = [f"Node {node['id']}<br>Connections: {degrees[node['id']]}" for node in comm_nodes]

    fig.add_trace(
        go.Scatter(
            x=x_vals,
            y=y_vals,
            mode="markers",
            marker={
                "size": sizes,
                "color": IMPRINT[comm_idx],
                "line": {"width": 2, "color": PAGE_BG},
                "opacity": 0.9,
            },
            name=comm_name,
            text=hover_text,
            hoverinfo="text",
        )
    )

# Hub annotations: label only the single highest-degree node per community
hub_annotations = []
for comm_idx, comm_name in enumerate(community_names):
    comm_nodes = [node for node in nodes if node["community"] == comm_idx]
    top_node = max(comm_nodes, key=lambda node: degrees[node["id"]])
    x, y = pos[top_node["id"]]
    hub_annotations.append(
        {
            "x": x,
            "y": y + 0.04,
            "text": f"{comm_name} hub",
            "showarrow": False,
            "font": {"size": 16, "color": INK, "family": "Arial Black"},
            "bgcolor": ELEVATED_BG,
            "bordercolor": INK_SOFT,
            "borderwidth": 1,
            "borderpad": 4,
            "xanchor": "center",
            "yanchor": "bottom",
        }
    )

fig.update_layout(
    title={
        "text": "network-force-directed · plotly · anyplot.ai",
        "font": {"size": 28, "color": INK},
        "x": 0.5,
        "xanchor": "center",
    },
    paper_bgcolor=PAGE_BG,
    plot_bgcolor=PAGE_BG,
    font={"color": INK},
    xaxis={"showgrid": False, "zeroline": False, "showticklabels": False, "range": [-0.05, 1.05]},
    yaxis={
        "showgrid": False,
        "zeroline": False,
        "showticklabels": False,
        "range": [-0.05, 1.05],
        "scaleanchor": "x",
        "scaleratio": 1,
    },
    legend={
        "title": {"text": "Teams", "font": {"size": 20, "color": INK}},
        "font": {"size": 16, "color": INK_SOFT},
        "x": 0.02,
        "y": 0.98,
        "bgcolor": ELEVATED_BG,
        "bordercolor": INK_SOFT,
        "borderwidth": 1,
    },
    annotations=hub_annotations,
    margin={"l": 20, "r": 20, "t": 80, "b": 20},
)

fig.write_image(f"plot-{THEME}.png", width=1600, height=900, scale=3)
fig.write_html(f"plot-{THEME}.html", include_plotlyjs="cdn")
