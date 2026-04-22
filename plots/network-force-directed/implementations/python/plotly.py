""" pyplots.ai
network-force-directed: Force-Directed Graph
Library: plotly 6.5.0 | Python 3.13.11
Quality: 92/100 | Created: 2025-12-23
"""

import numpy as np
import plotly.graph_objects as go


# Set seed for reproducibility
np.random.seed(42)

# Data: A social network with 50 nodes in 3 communities
# Demonstrates force-directed layout with clear community structure
nodes = []
edges = []

# Create 3 communities
community_sizes = [18, 17, 15]  # Total: 50 nodes
community_names = ["Engineering", "Marketing", "Sales"]
node_id = 0

for comm_idx, size in enumerate(community_sizes):
    for _ in range(size):
        nodes.append({"id": node_id, "community": comm_idx})
        node_id += 1

# Intra-community edges (dense connections within communities)
# Engineering: nodes 0-17
for i in range(18):
    for j in range(i + 1, 18):
        if np.random.random() < 0.3:
            edges.append((i, j))

# Marketing: nodes 18-34
for i in range(18, 35):
    for j in range(i + 1, 35):
        if np.random.random() < 0.3:
            edges.append((i, j))

# Sales: nodes 35-49
for i in range(35, 50):
    for j in range(i + 1, 50):
        if np.random.random() < 0.3:
            edges.append((i, j))

# Inter-community edges (sparse bridges between communities)
bridge_edges = [(0, 18), (5, 20), (10, 25), (18, 35), (22, 40), (30, 45), (8, 38), (15, 48)]
edges.extend(bridge_edges)

# Force-directed layout algorithm (Fruchterman-Reingold)
n = len(nodes)
positions = np.random.rand(n, 2) * 2 - 1  # Initial random positions

# Optimal distance parameter
k = 0.5
iterations = 200

for iteration in range(iterations):
    displacement = np.zeros((n, 2))

    # Repulsive forces between all node pairs (nodes push apart)
    for i in range(n):
        for j in range(i + 1, n):
            diff = positions[i] - positions[j]
            dist = max(np.linalg.norm(diff), 0.01)
            repulsive_force = (k * k / dist) * (diff / dist)
            displacement[i] += repulsive_force
            displacement[j] -= repulsive_force

    # Attractive forces along edges (connected nodes pull together)
    for src, tgt in edges:
        diff = positions[src] - positions[tgt]
        dist = max(np.linalg.norm(diff), 0.01)
        attractive_force = (dist * dist / k) * (diff / dist)
        displacement[src] -= attractive_force
        displacement[tgt] += attractive_force

    # Apply displacement with cooling (decreasing temperature)
    temperature = 1 - iteration / iterations
    for i in range(n):
        disp_norm = np.linalg.norm(displacement[i])
        if disp_norm > 0:
            # Limit movement by temperature
            positions[i] += (displacement[i] / disp_norm) * min(disp_norm, 0.15 * temperature)

# Normalize positions to [0.05, 0.95] range
pos_min = positions.min(axis=0)
pos_max = positions.max(axis=0)
positions = (positions - pos_min) / (pos_max - pos_min + 1e-6) * 0.9 + 0.05
pos = {node["id"]: positions[i] for i, node in enumerate(nodes)}

# Calculate node degrees (number of connections)
degrees = {node["id"]: 0 for node in nodes}
for src, tgt in edges:
    degrees[src] += 1
    degrees[tgt] += 1

# Community colors (Python Blue first, then Python Yellow, then accessible third color)
community_colors = ["#306998", "#FFD43B", "#FF6B6B"]

# Create figure
fig = go.Figure()

# Draw edges first
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
        line={"width": 1.5, "color": "#AAAAAA"},
        opacity=0.4,
        hoverinfo="none",
        showlegend=False,
    )
)

# Draw nodes by community (for legend grouping)
for comm_idx, comm_name in enumerate(community_names):
    comm_nodes = [node for node in nodes if node["community"] == comm_idx]
    x_vals = [pos[node["id"]][0] for node in comm_nodes]
    y_vals = [pos[node["id"]][1] for node in comm_nodes]
    sizes = [20 + degrees[node["id"]] * 5 for node in comm_nodes]  # Scale size by connections

    # Hover text showing degree
    hover_text = [f"Node {node['id']}<br>Connections: {degrees[node['id']]}" for node in comm_nodes]

    fig.add_trace(
        go.Scatter(
            x=x_vals,
            y=y_vals,
            mode="markers",
            marker={
                "size": sizes,
                "color": community_colors[comm_idx],
                "line": {"width": 2, "color": "#333333"},
                "opacity": 0.85,
            },
            name=comm_name,
            text=hover_text,
            hoverinfo="text",
        )
    )

# Add "Hub" labels for high-degree nodes
hub_annotations = []
for node in nodes:
    if degrees[node["id"]] >= 7:
        x, y = pos[node["id"]]
        hub_annotations.append(
            {
                "x": x,
                "y": y + 0.04,
                "text": "Hub",
                "showarrow": False,
                "font": {"size": 14, "color": "#333333", "family": "Arial Black"},
                "xanchor": "center",
                "yanchor": "bottom",
            }
        )

# Layout
fig.update_layout(
    title={"text": "network-force-directed · plotly · pyplots.ai", "font": {"size": 28}, "x": 0.5, "xanchor": "center"},
    xaxis={"showgrid": False, "zeroline": False, "showticklabels": False, "range": [-0.05, 1.05]},
    yaxis={
        "showgrid": False,
        "zeroline": False,
        "showticklabels": False,
        "range": [-0.05, 1.05],
        "scaleanchor": "x",
        "scaleratio": 1,
    },
    template="plotly_white",
    legend={
        "title": {"text": "Teams", "font": {"size": 20}},
        "font": {"size": 18},
        "x": 0.02,
        "y": 0.98,
        "bgcolor": "rgba(255,255,255,0.9)",
        "bordercolor": "#333333",
        "borderwidth": 1,
    },
    annotations=hub_annotations,
    margin={"l": 20, "r": 20, "t": 80, "b": 20},
)

# Save as PNG and HTML
fig.write_image("plot.png", width=1600, height=900, scale=3)
fig.write_html("plot.html", include_plotlyjs="cdn")
