"""anyplot.ai
network-weighted: Weighted Network Graph with Edge Thickness
Library: plotly | Python 3.13
Quality: pending | Created: 2026-05-17
"""

import os

import numpy as np
import plotly.graph_objects as go


# Theme tokens (see prompts/default-style-guide.md)
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
GRID = "rgba(26,26,23,0.10)" if THEME == "light" else "rgba(240,239,232,0.10)"
BRAND = "#009E73"  # Okabe-Ito position 1

# Data - Trade network between countries (billions USD)
np.random.seed(42)

# Define nodes (countries)
countries = [
    "USA",
    "China",
    "Germany",
    "Japan",
    "UK",
    "France",
    "Canada",
    "Mexico",
    "Brazil",
    "India",
    "Australia",
    "S. Korea",
    "Netherlands",
    "Italy",
    "Spain",
]
n_nodes = len(countries)
node_idx = {name: i for i, name in enumerate(countries)}

# Create weighted edges (trade relationships)
edges = [
    # Major trade routes (high weight)
    ("USA", "China", 580),
    ("USA", "Canada", 620),
    ("USA", "Mexico", 550),
    ("China", "Japan", 320),
    ("China", "S. Korea", 280),
    ("China", "Germany", 190),
    ("Germany", "France", 180),
    ("Germany", "Netherlands", 210),
    ("Germany", "Italy", 140),
    ("UK", "Germany", 130),
    ("UK", "USA", 140),
    ("UK", "Netherlands", 90),
    ("Japan", "USA", 200),
    ("Japan", "S. Korea", 85),
    # Medium trade routes
    ("France", "Italy", 95),
    ("France", "Spain", 110),
    ("Spain", "Italy", 50),
    ("Canada", "Mexico", 40),
    ("Brazil", "USA", 75),
    ("Brazil", "China", 100),
    ("India", "USA", 90),
    ("India", "China", 115),
    ("India", "UK", 35),
    ("Australia", "China", 145),
    ("Australia", "Japan", 55),
    ("Australia", "S. Korea", 45),
    # Lower trade routes
    ("Netherlands", "UK", 65),
    ("S. Korea", "USA", 120),
    ("Mexico", "China", 70),
]

# Compute force-directed layout (Fruchterman-Reingold algorithm)
pos = np.random.rand(n_nodes, 2) * 2 - 1
k = 0.5
for _ in range(200):
    displacement = np.zeros((n_nodes, 2))
    # Repulsive forces
    for i in range(n_nodes):
        diff = pos[i] - pos
        dist = np.sqrt((diff**2).sum(axis=1))
        dist = np.where(dist < 0.01, 0.01, dist)
        rep_force = k**2 / dist
        rep_force[i] = 0
        displacement[i] += (diff * rep_force[:, np.newaxis]).sum(axis=0)
    # Attractive forces along edges
    for source, target, weight in edges:
        i, j = node_idx[source], node_idx[target]
        diff = pos[j] - pos[i]
        dist = np.sqrt((diff**2).sum())
        if dist > 0.01:
            attr_force = dist**2 / k * (1 + weight / 200)
            displacement[i] += diff / dist * attr_force
            displacement[j] -= diff / dist * attr_force
    # Update positions
    length = np.sqrt((displacement**2).sum(axis=1))
    length = np.where(length < 0.01, 0.01, length)
    pos += displacement / length[:, np.newaxis] * min(0.1, k)

# Normalize positions
pos = (pos - pos.min(axis=0)) / (pos.max(axis=0) - pos.min(axis=0))
pos = pos * 1.6 - 0.8
pos = pos - pos.mean(axis=0)
node_positions = {countries[i]: pos[i] for i in range(n_nodes)}

# Calculate weighted degree for node sizing
weighted_degree = dict.fromkeys(countries, 0)
for source, target, weight in edges:
    weighted_degree[source] += weight
    weighted_degree[target] += weight

node_sizes = [20 + (weighted_degree[node] / 40) for node in countries]

# Create edge traces with varying thickness
edge_traces = []
min_weight = min(w for _, _, w in edges)
max_weight = max(w for _, _, w in edges)

for source, target, weight in edges:
    x0, y0 = node_positions[source]
    x1, y1 = node_positions[target]
    # Scale width: 2 to 18 based on weight
    normalized = (weight - min_weight) / (max_weight - min_weight)
    line_width = 2 + normalized * 16
    # Edge color from Okabe-Ito palette (use BRAND with alpha for weight-based opacity)
    alpha = 0.4 + normalized * 0.5
    # Parse BRAND hex and create rgba
    edge_color = f"rgba(0, 158, 115, {alpha})"
    edge_traces.append(
        go.Scatter(
            x=[x0, x1, None],
            y=[y0, y1, None],
            mode="lines",
            line={"width": line_width, "color": edge_color},
            hoverinfo="text",
            text=f"{source} ↔ {target}: ${weight}B",
            showlegend=False,
        )
    )

# Create node trace
node_x = [node_positions[node][0] for node in countries]
node_y = [node_positions[node][1] for node in countries]

# Calculate smart label positions to avoid overlap
label_positions = []

for i, node in enumerate(countries):
    x, y = node_positions[node]
    # Find nearby nodes and adjust position
    nearby_above = 0
    nearby_below = 0
    nearby_left = 0
    nearby_right = 0
    for j, other in enumerate(countries):
        if i != j:
            ox, oy = node_positions[other]
            dx, dy = x - ox, y - oy
            dist = np.sqrt(dx**2 + dy**2)
            if dist < 0.35:
                if dy > 0:
                    nearby_below += 1
                else:
                    nearby_above += 1
                if dx > 0:
                    nearby_left += 1
                else:
                    nearby_right += 1

    # Handle specific known close pairs to avoid overlap
    if node == "Japan":
        pos_choice = "top right"
    elif node == "S. Korea":
        pos_choice = "bottom left"
    elif node == "Italy":
        pos_choice = "top left"
    elif node == "France":
        pos_choice = "bottom right"
    elif nearby_above > nearby_below:
        pos_choice = "bottom center"
    elif nearby_left > nearby_right:
        pos_choice = "middle right"
    elif nearby_right > nearby_left:
        pos_choice = "middle left"
    else:
        pos_choice = "top center"
    label_positions.append(pos_choice)

node_trace = go.Scatter(
    x=node_x,
    y=node_y,
    mode="markers+text",
    marker={"size": node_sizes, "color": BRAND, "line": {"width": 2, "color": INK_SOFT}},
    text=countries,
    textposition=label_positions,
    textfont={"size": 16, "color": INK},
    hoverinfo="text",
    hovertext=[f"{c}<br>Trade Volume: ${weighted_degree[c]}B" for c in countries],
    showlegend=False,
)

# Create figure
fig = go.Figure()

# Add edges first (behind nodes)
for trace in edge_traces:
    fig.add_trace(trace)

# Add nodes
fig.add_trace(node_trace)

# Add weight scale annotation
fig.add_annotation(
    x=0.01,
    y=0.99,
    xref="paper",
    yref="paper",
    text="Edge Thickness = Trade Volume<br>35B USD (thin) to 620B USD (thick)",
    showarrow=False,
    font={"size": 18, "color": INK, "family": "Arial"},
    align="left",
    xanchor="left",
    yanchor="top",
    bgcolor=ELEVATED_BG,
    bordercolor=INK_SOFT,
    borderwidth=1,
    borderpad=10,
)

# Update layout with theme-adaptive colors
fig.update_layout(
    title={
        "text": "network-weighted · plotly · anyplot.ai",
        "font": {"size": 28, "color": INK},
        "x": 0.5,
        "xanchor": "center",
    },
    xaxis={"showgrid": False, "zeroline": False, "showticklabels": False, "title": "", "linecolor": INK_SOFT},
    yaxis={"showgrid": False, "zeroline": False, "showticklabels": False, "title": "", "linecolor": INK_SOFT},
    paper_bgcolor=PAGE_BG,
    plot_bgcolor=PAGE_BG,
    font={"color": INK},
    showlegend=False,
    margin={"l": 80, "r": 80, "t": 100, "b": 80},
)

# Save outputs
fig.write_image(f"plot-{THEME}.png", width=1600, height=900, scale=3)
fig.write_html(f"plot-{THEME}.html", include_plotlyjs="cdn")
