""" pyplots.ai
network-force-directed: Force-Directed Graph
Library: altair 6.0.0 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-23
"""

import altair as alt
import numpy as np
import pandas as pd


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
        nodes.append({"id": node_id, "community": community_names[comm_idx]})
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

# Calculate node degrees (number of connections)
degrees = {node["id"]: 0 for node in nodes}
for src, tgt in edges:
    degrees[src] += 1
    degrees[tgt] += 1

# Create node dataframe with positions and attributes
node_df = pd.DataFrame(
    {
        "id": [node["id"] for node in nodes],
        "x": positions[:, 0],
        "y": positions[:, 1],
        "community": [node["community"] for node in nodes],
        "degree": [degrees[node["id"]] for node in nodes],
    }
)

# Scale node size by degree for visualization
node_df["size"] = node_df["degree"] * 30 + 200

# Create edge dataframe for line segments
edge_data = []
for src, tgt in edges:
    edge_data.append({"edge_id": f"{src}-{tgt}", "x": positions[src][0], "y": positions[src][1], "order": 0})
    edge_data.append({"edge_id": f"{src}-{tgt}", "x": positions[tgt][0], "y": positions[tgt][1], "order": 1})
edge_df = pd.DataFrame(edge_data)

# Community color mapping (Python Blue, Python Yellow, and colorblind-safe coral)
community_colors = ["#306998", "#FFD43B", "#FF6B6B"]

# Create edges layer
edges_chart = (
    alt.Chart(edge_df)
    .mark_line(strokeWidth=1.5, opacity=0.4)
    .encode(
        x=alt.X("x:Q", axis=None),
        y=alt.Y("y:Q", axis=None),
        detail="edge_id:N",
        order="order:O",
        color=alt.value("#AAAAAA"),
    )
)

# Create nodes layer
nodes_chart = (
    alt.Chart(node_df)
    .mark_circle(stroke="#333333", strokeWidth=1.5, opacity=0.85)
    .encode(
        x=alt.X("x:Q", axis=None),
        y=alt.Y("y:Q", axis=None),
        size=alt.Size("size:Q", legend=None, scale=alt.Scale(range=[200, 800])),
        color=alt.Color(
            "community:N",
            scale=alt.Scale(domain=["Engineering", "Marketing", "Sales"], range=community_colors),
            legend=alt.Legend(title="Teams", titleFontSize=18, labelFontSize=16, symbolSize=400),
        ),
        tooltip=["community:N", "degree:Q"],
    )
)

# Label high-degree nodes (hubs)
hub_df = node_df[node_df["degree"] >= 7].copy()
hub_df["label"] = "Hub"

hub_labels = (
    alt.Chart(hub_df)
    .mark_text(fontSize=14, fontWeight="bold", color="#333333", dy=-15)
    .encode(x=alt.X("x:Q", axis=None), y=alt.Y("y:Q", axis=None), text="label:N")
)

# Combine all layers
chart = (
    (edges_chart + nodes_chart + hub_labels)
    .properties(width=1600, height=900, title=alt.Title("network-force-directed · altair · pyplots.ai", fontSize=28))
    .configure_view(strokeWidth=0)
)

# Save as PNG (4800x2700 at scale_factor=3) and HTML
chart.save("plot.png", scale_factor=3.0)
chart.save("plot.html")
