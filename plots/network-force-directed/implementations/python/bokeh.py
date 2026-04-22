""" pyplots.ai
network-force-directed: Force-Directed Graph
Library: bokeh 3.8.1 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-23
"""

import numpy as np
from bokeh.io import export_png, output_file, save
from bokeh.models import ColumnDataSource, HoverTool, Legend, LegendItem
from bokeh.plotting import figure


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

# Community colors (Python Blue and Yellow first, then accessible red)
community_colors = ["#306998", "#FFD43B", "#FF6B6B"]

# Create figure (4800x2700 px)
p = figure(
    width=4800,
    height=2700,
    title="network-force-directed · bokeh · pyplots.ai",
    x_range=(-0.05, 1.05),
    y_range=(-0.05, 1.05),
    tools="pan,wheel_zoom,box_zoom,reset,save",
)

# Style the figure
p.title.text_font_size = "28pt"
p.axis.visible = False
p.grid.visible = False
p.outline_line_color = None
p.background_fill_color = "white"

# Draw edges as lines
edge_x0 = [pos[src][0] for src, tgt in edges]
edge_y0 = [pos[src][1] for src, tgt in edges]
edge_x1 = [pos[tgt][0] for src, tgt in edges]
edge_y1 = [pos[tgt][1] for src, tgt in edges]

edge_source = ColumnDataSource(data={"x0": edge_x0, "y0": edge_y0, "x1": edge_x1, "y1": edge_y1})
p.segment(x0="x0", y0="y0", x1="x1", y1="y1", source=edge_source, line_color="#AAAAAA", line_alpha=0.4, line_width=2)

# Draw nodes by community for legend
renderers = []
for comm_idx, (color, name) in enumerate(zip(community_colors, community_names, strict=True)):
    comm_nodes = [node for node in nodes if node["community"] == comm_idx]
    x_vals = [pos[node["id"]][0] for node in comm_nodes]
    y_vals = [pos[node["id"]][1] for node in comm_nodes]
    size_vals = [15 + degrees[node["id"]] * 3 for node in comm_nodes]  # Scale size by degree
    degree_vals = [degrees[node["id"]] for node in comm_nodes]
    node_ids = [node["id"] for node in comm_nodes]

    source = ColumnDataSource(
        data={
            "x": x_vals,
            "y": y_vals,
            "size": size_vals,
            "degree": degree_vals,
            "node_id": node_ids,
            "team": [name] * len(comm_nodes),
        }
    )

    renderer = p.scatter(
        x="x", y="y", size="size", source=source, fill_color=color, fill_alpha=0.85, line_color="#333333", line_width=2
    )
    renderers.append((name, [renderer]))

# Add legend
legend = Legend(
    items=[LegendItem(label=name, renderers=r) for name, r in renderers], location="top_left", title="Teams"
)
legend.label_text_font_size = "18pt"
legend.title_text_font_size = "20pt"
legend.background_fill_alpha = 0.9
p.add_layout(legend, "left")

# Add hover tool
hover = HoverTool(
    tooltips=[("Team", "@team"), ("Node ID", "@node_id"), ("Connections", "@degree")],
    renderers=[r for _, rlist in renderers for r in rlist],
)
p.add_tools(hover)

# Label hub nodes (high degree)
hub_x = []
hub_y = []
for node in nodes:
    if degrees[node["id"]] >= 7:
        hub_x.append(pos[node["id"]][0])
        hub_y.append(pos[node["id"]][1] + 0.035)

if hub_x:
    hub_source = ColumnDataSource(data={"x": hub_x, "y": hub_y, "text": ["Hub"] * len(hub_x)})
    p.text(
        x="x",
        y="y",
        text="text",
        source=hub_source,
        text_font_size="14pt",
        text_font_style="bold",
        text_align="center",
        text_baseline="bottom",
        text_color="#333333",
    )

# Save outputs
export_png(p, filename="plot.png")
output_file("plot.html")
save(p)
