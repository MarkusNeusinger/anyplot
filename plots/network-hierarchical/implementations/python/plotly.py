""" pyplots.ai
network-hierarchical: Hierarchical Network Graph with Tree Layout
Library: plotly 6.5.1 | Python 3.13.11
Quality: 92/100 | Created: 2026-01-08
"""

import plotly.graph_objects as go


# Data: Organizational chart with 16 employees across 4 levels
nodes = {
    # Level 0 - CEO
    "CEO": {"label": "CEO", "level": 0, "parent": None},
    # Level 1 - VPs
    "VP_Eng": {"label": "VP Engineering", "level": 1, "parent": "CEO"},
    "VP_Sales": {"label": "VP Sales", "level": 1, "parent": "CEO"},
    "VP_Ops": {"label": "VP Operations", "level": 1, "parent": "CEO"},
    # Level 2 - Directors (2 per VP)
    "Dir_FE": {"label": "Frontend", "level": 2, "parent": "VP_Eng"},
    "Dir_BE": {"label": "Backend", "level": 2, "parent": "VP_Eng"},
    "Dir_NA": {"label": "Americas", "level": 2, "parent": "VP_Sales"},
    "Dir_EU": {"label": "Europe", "level": 2, "parent": "VP_Sales"},
    "Dir_HR": {"label": "HR", "level": 2, "parent": "VP_Ops"},
    "Dir_Fin": {"label": "Finance", "level": 2, "parent": "VP_Ops"},
    # Level 3 - Leads (1 per director)
    "Mgr_React": {"label": "React", "level": 3, "parent": "Dir_FE"},
    "Mgr_API": {"label": "API", "level": 3, "parent": "Dir_BE"},
    "Mgr_East": {"label": "East", "level": 3, "parent": "Dir_NA"},
    "Mgr_UK": {"label": "UK", "level": 3, "parent": "Dir_EU"},
    "Mgr_Recruit": {"label": "Recruit", "level": 3, "parent": "Dir_HR"},
    "Mgr_Acct": {"label": "Acct", "level": 3, "parent": "Dir_Fin"},
}

# Build edges and children lookup
edges = []
children = {node_id: [] for node_id in nodes}
for node_id, data in nodes.items():
    if data["parent"]:
        edges.append((data["parent"], node_id))
        children[data["parent"]].append(node_id)

# Calculate positions using bottom-up tree layout
# Assign x positions to leaf nodes first, then center parents over children
positions = {}
leaf_spacing = 1.8
level_height = 2.5

# Get all leaf nodes (level 3) and assign sequential x positions
leaf_nodes = [n for n in nodes if nodes[n]["level"] == 3]
for i, node_id in enumerate(leaf_nodes):
    x = (i - (len(leaf_nodes) - 1) / 2) * leaf_spacing
    positions[node_id] = (x, -3 * level_height)

# Level 2: center each director over its children
for node_id in [n for n in nodes if nodes[n]["level"] == 2]:
    child_xs = [positions[c][0] for c in children[node_id]]
    center_x = sum(child_xs) / len(child_xs) if child_xs else 0
    positions[node_id] = (center_x, -2 * level_height)

# Level 1: center each VP over its children
for node_id in [n for n in nodes if nodes[n]["level"] == 1]:
    child_xs = [positions[c][0] for c in children[node_id]]
    center_x = sum(child_xs) / len(child_xs) if child_xs else 0
    positions[node_id] = (center_x, -1 * level_height)

# Level 0: center CEO over VPs
ceo_children = children["CEO"]
center_x = sum(positions[c][0] for c in ceo_children) / len(ceo_children)
positions["CEO"] = (center_x, 0)

# Create edge traces with orthogonal routing
edge_x = []
edge_y = []
for parent_id, child_id in edges:
    x0, y0 = positions[parent_id]
    x1, y1 = positions[child_id]
    mid_y = (y0 + y1) / 2
    edge_x.extend([x0, x0, x1, x1, None])
    edge_y.extend([y0, mid_y, mid_y, y1, None])

edge_trace = go.Scatter(x=edge_x, y=edge_y, mode="lines", line=dict(width=2.5, color="#888888"), hoverinfo="none")

# Create node trace
node_x = [positions[n][0] for n in nodes]
node_y = [positions[n][1] for n in nodes]
node_labels = [nodes[n]["label"] for n in nodes]

# Color by level using Python colors
level_colors = {
    0: "#306998",  # Python Blue - CEO
    1: "#FFD43B",  # Python Yellow - VPs
    2: "#4B8BBE",  # Light blue - Directors
    3: "#646464",  # Gray - Leads
}
node_colors = [level_colors[nodes[n]["level"]] for n in nodes]

node_trace = go.Scatter(
    x=node_x,
    y=node_y,
    mode="markers+text",
    marker=dict(size=45, color=node_colors, line=dict(width=2, color="white")),
    text=node_labels,
    textposition="bottom center",
    textfont=dict(size=16, color="#333333"),
    hoverinfo="text",
    hovertext=node_labels,
)

# Create figure
fig = go.Figure(data=[edge_trace, node_trace])

fig.update_layout(
    title=dict(
        text="Organizational Chart · network-hierarchical · plotly · pyplots.ai",
        font=dict(size=28, color="#333333"),
        x=0.5,
        xanchor="center",
    ),
    showlegend=False,
    xaxis=dict(showgrid=False, zeroline=False, showticklabels=False, title=""),
    yaxis=dict(showgrid=False, zeroline=False, showticklabels=False, title="", scaleanchor="x", scaleratio=1),
    template="plotly_white",
    margin=dict(l=100, r=50, t=100, b=80),
    paper_bgcolor="white",
    plot_bgcolor="white",
    annotations=[
        dict(
            x=-6.2, y=0, text="Level 0: Executive", showarrow=False, font=dict(size=16, color="#666666"), xanchor="left"
        ),
        dict(x=-6.2, y=-2.5, text="Level 1: VPs", showarrow=False, font=dict(size=16, color="#666666"), xanchor="left"),
        dict(
            x=-6.2,
            y=-5.0,
            text="Level 2: Directors",
            showarrow=False,
            font=dict(size=16, color="#666666"),
            xanchor="left",
        ),
        dict(
            x=-6.2, y=-7.5, text="Level 3: Leads", showarrow=False, font=dict(size=16, color="#666666"), xanchor="left"
        ),
    ],
)

# Save as PNG (4800x2700 via scale=3)
fig.write_image("plot.png", width=1600, height=900, scale=3)

# Save as HTML for interactivity
fig.write_html("plot.html", include_plotlyjs=True, full_html=True)
