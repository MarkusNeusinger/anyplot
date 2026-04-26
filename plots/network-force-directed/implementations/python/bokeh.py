""" anyplot.ai
network-force-directed: Force-Directed Graph
Library: bokeh 3.9.0 | Python 3.14.4
Quality: 85/100 | Updated: 2026-04-26
"""

import os

import numpy as np
from bokeh.io import export_png, output_file, save
from bokeh.models import ColumnDataSource, HoverTool
from bokeh.plotting import figure


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Data — A 50-node social network with 3 communities
np.random.seed(42)

community_sizes = [18, 17, 15]
community_names = ["Engineering", "Marketing", "Sales"]
# Okabe-Ito positions 1, 2, 3
community_colors = ["#009E73", "#D55E00", "#0072B2"]

nodes = []
node_id = 0
for comm_idx, size in enumerate(community_sizes):
    for _ in range(size):
        nodes.append({"id": node_id, "community": comm_idx})
        node_id += 1

# Intra-community edges (dense within each team)
edges = []
boundaries = [0, 18, 35, 50]
for c in range(3):
    start, end = boundaries[c], boundaries[c + 1]
    for i in range(start, end):
        for j in range(i + 1, end):
            if np.random.random() < 0.3:
                edges.append((i, j))

# Inter-community bridges (sparse)
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
        d = np.linalg.norm(displacement[i])
        if d > 0:
            positions[i] += (displacement[i] / d) * min(d, 0.15 * temperature)

# Normalize positions to [0.05, 0.95]
pos_min = positions.min(axis=0)
pos_max = positions.max(axis=0)
positions = (positions - pos_min) / (pos_max - pos_min + 1e-6) * 0.9 + 0.05
pos = {node["id"]: positions[i] for i, node in enumerate(nodes)}

# Node degrees
degrees = {node["id"]: 0 for node in nodes}
for src, tgt in edges:
    degrees[src] += 1
    degrees[tgt] += 1

# Plot
p = figure(
    width=4800,
    height=2700,
    title="network-force-directed · bokeh · anyplot.ai",
    x_range=(-0.05, 1.05),
    y_range=(-0.05, 1.05),
    tools="pan,wheel_zoom,box_zoom,reset,save",
    background_fill_color=PAGE_BG,
    border_fill_color=PAGE_BG,
)

p.title.text_font_size = "36pt"
p.title.text_color = INK
p.title.align = "center"
p.axis.visible = False
p.grid.visible = False
p.outline_line_color = None

# Edges
edge_x0 = [pos[src][0] for src, tgt in edges]
edge_y0 = [pos[src][1] for src, tgt in edges]
edge_x1 = [pos[tgt][0] for src, tgt in edges]
edge_y1 = [pos[tgt][1] for src, tgt in edges]

edge_source = ColumnDataSource(data={"x0": edge_x0, "y0": edge_y0, "x1": edge_x1, "y1": edge_y1})
p.segment(x0="x0", y0="y0", x1="x1", y1="y1", source=edge_source, line_color=INK_SOFT, line_alpha=0.30, line_width=2)

# Nodes — one renderer per community so the legend lives inside the plot frame
node_renderers = []
for comm_idx, color, name in zip(range(3), community_colors, community_names, strict=True):
    comm_nodes = [node for node in nodes if node["community"] == comm_idx]
    x_vals = [pos[node["id"]][0] for node in comm_nodes]
    y_vals = [pos[node["id"]][1] for node in comm_nodes]
    # Wider base size + degree boost so peripheral nodes remain visible
    size_vals = [22 + degrees[node["id"]] * 3 for node in comm_nodes]
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
        x="x",
        y="y",
        size="size",
        source=source,
        fill_color=color,
        fill_alpha=0.9,
        line_color=PAGE_BG,
        line_width=2,
        legend_label=name,
    )
    node_renderers.append(renderer)

# Hover tool — only on nodes
p.add_tools(
    HoverTool(
        renderers=node_renderers, tooltips=[("Team", "@team"), ("Node ID", "@node_id"), ("Connections", "@degree")]
    )
)

# Hub labels — bold "Hub" text above high-degree nodes
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
        text_font_size="16pt",
        text_font_style="bold",
        text_align="center",
        text_baseline="bottom",
        text_color=INK,
    )

# Legend — inside the plot frame, top-left
p.legend.title = "Teams"
p.legend.location = "top_left"
p.legend.label_text_font_size = "20pt"
p.legend.title_text_font_size = "22pt"
p.legend.label_text_color = INK_SOFT
p.legend.title_text_color = INK
p.legend.background_fill_color = ELEVATED_BG
p.legend.background_fill_alpha = 0.95
p.legend.border_line_color = INK_SOFT
p.legend.border_line_alpha = 0.4
p.legend.spacing = 10
p.legend.padding = 18
p.legend.margin = 24
p.legend.glyph_height = 28
p.legend.glyph_width = 28

# Save
export_png(p, filename=f"plot-{THEME}.png")
output_file(f"plot-{THEME}.html", title="network-force-directed · bokeh · anyplot.ai")
save(p)
