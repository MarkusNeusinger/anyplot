""" pyplots.ai
network-directed: Directed Network Graph
Library: altair 6.0.0 | Python 3.13.11
Quality: 90/100 | Created: 2025-12-30
"""

import altair as alt
import numpy as np
import pandas as pd


np.random.seed(42)

# Data: Software package dependency graph
nodes = [
    {"id": "app", "label": "App", "group": "main"},
    {"id": "api", "label": "API", "group": "core"},
    {"id": "auth", "label": "Auth", "group": "core"},
    {"id": "database", "label": "Database", "group": "core"},
    {"id": "cache", "label": "Cache", "group": "service"},
    {"id": "logger", "label": "Logger", "group": "util"},
    {"id": "config", "label": "Config", "group": "util"},
    {"id": "utils", "label": "Utils", "group": "util"},
    {"id": "models", "label": "Models", "group": "data"},
    {"id": "schemas", "label": "Schemas", "group": "data"},
    {"id": "router", "label": "Router", "group": "core"},
    {"id": "middleware", "label": "Middleware", "group": "core"},
]

# Directed edges: (source, target) - arrows point from source to target
# Includes some bidirectional pairs to demonstrate curved edge handling
edges = [
    ("app", "api"),
    ("app", "auth"),
    ("app", "router"),
    ("api", "database"),
    ("api", "cache"),
    ("api", "models"),
    ("auth", "database"),
    ("auth", "cache"),
    ("auth", "logger"),
    ("database", "config"),
    ("database", "logger"),
    ("cache", "config"),
    ("cache", "logger"),
    ("router", "middleware"),
    ("router", "api"),
    ("middleware", "auth"),
    ("middleware", "logger"),
    ("models", "schemas"),
    ("models", "utils"),
    ("schemas", "utils"),
    ("logger", "config"),
    ("utils", "config"),
    # Bidirectional edges (mutual dependencies)
    ("api", "auth"),  # API also depends on Auth
    ("cache", "database"),  # Cache also depends on Database
]

# Node positions using hierarchical layout based on dependency depth
# Calculate depth for each node (topological sort-like approach)
depths = {"app": 0}
for _ in range(len(nodes)):
    for source, target in edges:
        if source in depths:
            current_depth = depths.get(target, -1)
            depths[target] = max(current_depth, depths[source] + 1)

# Assign default depth for any disconnected nodes
for node in nodes:
    if node["id"] not in depths:
        depths[node["id"]] = 0

# Group nodes by depth for horizontal positioning
depth_groups = {}
for node_id, depth in depths.items():
    if depth not in depth_groups:
        depth_groups[depth] = []
    depth_groups[depth].append(node_id)

# Calculate positions
positions = {}
max_depth = max(depths.values()) if depths else 0
for depth, node_ids in depth_groups.items():
    n_nodes = len(node_ids)
    for i, node_id in enumerate(node_ids):
        x = depth / max(max_depth, 1)  # Normalize x to [0, 1]
        y = (i + 0.5) / n_nodes  # Distribute vertically
        positions[node_id] = (x, y)

# Create node DataFrame
node_df = pd.DataFrame(
    [
        {
            "id": n["id"],
            "label": n["label"],
            "group": n["group"],
            "x": positions[n["id"]][0],
            "y": positions[n["id"]][1],
        }
        for n in nodes
    ]
)

# Identify bidirectional edge pairs for curved edge handling
edge_set = set(edges)
bidirectional_pairs = set()
for source, target in edges:
    if (target, source) in edge_set:
        bidirectional_pairs.add(tuple(sorted([source, target])))

# Create edge DataFrame with arrow coordinates
# Use curves for bidirectional edges to avoid overlap
edge_data = []
curved_edge_data = []
for source, target in edges:
    sx, sy = positions[source]
    tx, ty = positions[target]

    # Check if this edge is part of a bidirectional pair
    is_bidirectional = tuple(sorted([source, target])) in bidirectional_pairs

    # Shorten edge slightly so arrows don't overlap nodes
    dx, dy = tx - sx, ty - sy
    length = np.sqrt(dx**2 + dy**2)
    if length > 0:
        # Move endpoints slightly inward
        offset = 0.03
        sx_adj = sx + dx / length * offset
        sy_adj = sy + dy / length * offset
        tx_adj = tx - dx / length * offset
        ty_adj = ty - dy / length * offset
    else:
        sx_adj, sy_adj = sx, sy
        tx_adj, ty_adj = tx, ty

    if is_bidirectional:
        # Create curved path using control points
        # Offset perpendicular to the edge direction
        perp_x, perp_y = -dy / length * 0.05, dx / length * 0.05
        mid_x, mid_y = (sx + tx) / 2 + perp_x, (sy + ty) / 2 + perp_y

        # Generate points along a quadratic bezier curve
        for t in np.linspace(0, 1, 10):
            t_next = min(t + 0.1, 1)
            # Quadratic bezier formula
            bx1 = (1 - t) ** 2 * sx_adj + 2 * (1 - t) * t * mid_x + t**2 * tx_adj
            by1 = (1 - t) ** 2 * sy_adj + 2 * (1 - t) * t * mid_y + t**2 * ty_adj
            bx2 = (1 - t_next) ** 2 * sx_adj + 2 * (1 - t_next) * t_next * mid_x + t_next**2 * tx_adj
            by2 = (1 - t_next) ** 2 * sy_adj + 2 * (1 - t_next) * t_next * mid_y + t_next**2 * ty_adj
            curved_edge_data.append({"x": bx1, "y": by1, "x2": bx2, "y2": by2, "edge_id": f"{source}-{target}"})
    else:
        edge_data.append({"source": source, "target": target, "x": sx_adj, "y": sy_adj, "x2": tx_adj, "y2": ty_adj})

edge_df = pd.DataFrame(edge_data)
curved_edge_df = pd.DataFrame(curved_edge_data) if curved_edge_data else pd.DataFrame(columns=["x", "y", "x2", "y2"])

# Create arrow head data (triangular markers at edge endpoints)
arrow_data = []
for source, target in edges:
    sx, sy = positions[source]
    tx, ty = positions[target]

    dx, dy = tx - sx, ty - sy
    length = np.sqrt(dx**2 + dy**2)
    if length > 0:
        is_bidirectional = tuple(sorted([source, target])) in bidirectional_pairs

        if is_bidirectional:
            # For curved edges, adjust arrow position and angle
            perp_x, perp_y = -dy / length * 0.05, dx / length * 0.05
            mid_x, mid_y = (sx + tx) / 2 + perp_x, (sy + ty) / 2 + perp_y

            # Arrow tip position at end of curve (t=0.95)
            t = 0.95
            offset = 0.03
            sx_adj = sx + dx / length * offset
            sy_adj = sy + dy / length * offset
            tx_adj = tx - dx / length * offset
            ty_adj = ty - dy / length * offset

            ax = (1 - t) ** 2 * sx_adj + 2 * (1 - t) * t * mid_x + t**2 * tx_adj
            ay = (1 - t) ** 2 * sy_adj + 2 * (1 - t) * t * mid_y + t**2 * ty_adj

            # Tangent direction at arrow tip
            t_prev = 0.9
            ax_prev = (1 - t_prev) ** 2 * sx_adj + 2 * (1 - t_prev) * t_prev * mid_x + t_prev**2 * tx_adj
            ay_prev = (1 - t_prev) ** 2 * sy_adj + 2 * (1 - t_prev) * t_prev * mid_y + t_prev**2 * ty_adj
            angle = np.degrees(np.arctan2(ay - ay_prev, ax - ax_prev))
        else:
            # Arrow tip position (slightly before target node)
            offset = 0.04
            ax = tx - dx / length * offset
            ay = ty - dy / length * offset
            angle = np.degrees(np.arctan2(dy, dx))

        arrow_data.append({"x": ax, "y": ay, "angle": angle})

arrow_df = pd.DataFrame(arrow_data)

# Color palette for groups
group_colors = {
    "main": "#306998",  # Python Blue
    "core": "#FFD43B",  # Python Yellow
    "service": "#4ECDC4",
    "util": "#95A5A6",
    "data": "#E74C3C",
}

# Add colors to node dataframe
node_df["color"] = node_df["group"].map(group_colors)

# Create the visualization
# Straight edges as rules (lines)
edges_chart = (
    alt.Chart(edge_df)
    .mark_rule(strokeWidth=2, opacity=0.6, color="#666666")
    .encode(
        x=alt.X("x:Q", scale=alt.Scale(domain=[-0.1, 1.1]), axis=None),
        y=alt.Y("y:Q", scale=alt.Scale(domain=[-0.05, 1.05]), axis=None),
        x2="x2:Q",
        y2="y2:Q",
    )
)

# Curved edges (for bidirectional connections)
curved_edges_chart = (
    alt.Chart(curved_edge_df)
    .mark_rule(strokeWidth=2, opacity=0.6, color="#666666")
    .encode(
        x=alt.X("x:Q", scale=alt.Scale(domain=[-0.1, 1.1]), axis=None),
        y=alt.Y("y:Q", scale=alt.Scale(domain=[-0.05, 1.05]), axis=None),
        x2="x2:Q",
        y2="y2:Q",
    )
)

# Arrow heads as triangular points
arrows_chart = (
    alt.Chart(arrow_df)
    .mark_point(shape="triangle", size=150, filled=True, color="#666666", opacity=0.8)
    .encode(
        x=alt.X("x:Q", scale=alt.Scale(domain=[-0.1, 1.1])),
        y=alt.Y("y:Q", scale=alt.Scale(domain=[-0.05, 1.05])),
        angle=alt.Angle("angle:Q"),
    )
)

# Nodes as circles
nodes_chart = (
    alt.Chart(node_df)
    .mark_circle(size=800, stroke="#ffffff", strokeWidth=2)
    .encode(
        x=alt.X("x:Q", scale=alt.Scale(domain=[-0.1, 1.1])),
        y=alt.Y("y:Q", scale=alt.Scale(domain=[-0.05, 1.05])),
        color=alt.Color(
            "group:N",
            scale=alt.Scale(domain=list(group_colors.keys()), range=list(group_colors.values())),
            legend=alt.Legend(title="Module Type", titleFontSize=18, labelFontSize=16, orient="right"),
        ),
        tooltip=["label:N", "group:N"],
    )
)

# Node labels (fontSize 18 for better legibility at full resolution)
labels_chart = (
    alt.Chart(node_df)
    .mark_text(fontSize=18, fontWeight="bold", dy=-28)
    .encode(
        x=alt.X("x:Q", scale=alt.Scale(domain=[-0.1, 1.1])),
        y=alt.Y("y:Q", scale=alt.Scale(domain=[-0.05, 1.05])),
        text="label:N",
    )
)

# Combine all layers (include curved edges for bidirectional connections)
chart = (
    (edges_chart + curved_edges_chart + arrows_chart + nodes_chart + labels_chart)
    .properties(
        width=1600,
        height=900,
        title=alt.Title(
            text="network-directed · altair · pyplots.ai",
            subtitle="Software Package Dependencies (curved edges show bidirectional dependencies)",
            fontSize=28,
            subtitleFontSize=18,
            anchor="middle",
        ),
    )
    .configure_view(strokeWidth=0)
)

# Save as PNG and HTML
chart.save("plot.png", scale_factor=3.0)
chart.save("plot.html")
