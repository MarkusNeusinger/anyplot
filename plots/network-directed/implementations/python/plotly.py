""" pyplots.ai
network-directed: Directed Network Graph
Library: plotly 6.5.0 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-30
"""

import numpy as np
import plotly.graph_objects as go


# Data: Software module dependencies (arrows show import direction)
np.random.seed(42)

nodes = [
    {"id": 0, "label": "main", "group": "entry"},
    {"id": 1, "label": "api", "group": "core"},
    {"id": 2, "label": "auth", "group": "core"},
    {"id": 3, "label": "database", "group": "core"},
    {"id": 4, "label": "models", "group": "data"},
    {"id": 5, "label": "utils", "group": "helpers"},
    {"id": 6, "label": "config", "group": "helpers"},
    {"id": 7, "label": "logging", "group": "helpers"},
    {"id": 8, "label": "cache", "group": "core"},
    {"id": 9, "label": "router", "group": "core"},
    {"id": 10, "label": "middleware", "group": "core"},
    {"id": 11, "label": "validators", "group": "data"},
    {"id": 12, "label": "schemas", "group": "data"},
]

# Directed edges: (source, target) - arrows point from source to target
edges = [
    (0, 1),  # main -> api
    (0, 6),  # main -> config
    (0, 7),  # main -> logging
    (1, 2),  # api -> auth
    (1, 9),  # api -> router
    (1, 10),  # api -> middleware
    (2, 3),  # auth -> database
    (2, 5),  # auth -> utils
    (3, 4),  # database -> models
    (3, 8),  # database -> cache
    (4, 12),  # models -> schemas
    (5, 7),  # utils -> logging
    (6, 7),  # config -> logging
    (8, 7),  # cache -> logging
    (9, 10),  # router -> middleware
    (9, 11),  # router -> validators
    (10, 2),  # middleware -> auth
    (11, 12),  # validators -> schemas
    (12, 5),  # schemas -> utils
]

# Group colors
group_colors = {
    "entry": "#306998",  # Python Blue
    "core": "#FFD43B",  # Python Yellow
    "data": "#4ECDC4",  # Teal
    "helpers": "#95A5A6",  # Gray
}

# Circular layout for clear visualization
n_nodes = len(nodes)
angles = np.linspace(0, 2 * np.pi, n_nodes, endpoint=False)
radius = 3
node_x = radius * np.cos(angles)
node_y = radius * np.sin(angles)

# Create figure
fig = go.Figure()

# Add edges as lines with arrows using annotations
for source, target in edges:
    x0, y0 = node_x[source], node_y[source]
    x1, y1 = node_x[target], node_y[target]

    # Calculate direction vector
    dx, dy = x1 - x0, y1 - y0
    length = np.sqrt(dx**2 + dy**2)
    dx, dy = dx / length, dy / length

    # Shorten edge to not overlap with nodes (node radius ~0.4)
    node_radius = 0.4
    x0_adj = x0 + dx * node_radius
    y0_adj = y0 + dy * node_radius
    x1_adj = x1 - dx * node_radius
    y1_adj = y1 - dy * node_radius

    # Add edge line
    fig.add_trace(
        go.Scatter(
            x=[x0_adj, x1_adj],
            y=[y0_adj, y1_adj],
            mode="lines",
            line=dict(width=2, color="#666666"),
            hoverinfo="none",
            showlegend=False,
        )
    )

# Add arrowheads using annotations
for source, target in edges:
    x0, y0 = node_x[source], node_y[source]
    x1, y1 = node_x[target], node_y[target]

    # Calculate direction vector
    dx, dy = x1 - x0, y1 - y0
    length = np.sqrt(dx**2 + dy**2)
    dx, dy = dx / length, dy / length

    # Arrow position (at target node edge)
    node_radius = 0.45
    ax = x1 - dx * node_radius
    ay = y1 - dy * node_radius

    fig.add_annotation(
        x=x1 - dx * node_radius,
        y=y1 - dy * node_radius,
        ax=x1 - dx * (node_radius + 0.3),
        ay=y1 - dy * (node_radius + 0.3),
        xref="x",
        yref="y",
        axref="x",
        ayref="y",
        showarrow=True,
        arrowhead=2,
        arrowsize=2,
        arrowwidth=2,
        arrowcolor="#666666",
    )

# Add nodes by group for legend
for group in ["entry", "core", "data", "helpers"]:
    group_nodes = [n for n in nodes if n["group"] == group]
    group_x = [node_x[n["id"]] for n in group_nodes]
    group_y = [node_y[n["id"]] for n in group_nodes]
    group_labels = [n["label"] for n in group_nodes]

    fig.add_trace(
        go.Scatter(
            x=group_x,
            y=group_y,
            mode="markers+text",
            marker=dict(size=45, color=group_colors[group], line=dict(width=2, color="#333333")),
            text=group_labels,
            textposition="middle center",
            textfont=dict(size=14, color="#333333", family="Arial Black"),
            name=group.capitalize(),
            hovertemplate="<b>%{text}</b><br>Group: " + group + "<extra></extra>",
        )
    )

# Update layout
fig.update_layout(
    title=dict(
        text="Software Module Dependencies · network-directed · plotly · pyplots.ai",
        font=dict(size=28, color="#333333"),
        x=0.5,
        xanchor="center",
    ),
    xaxis=dict(showgrid=False, zeroline=False, showticklabels=False, title="", range=[-4.5, 4.5]),
    yaxis=dict(
        showgrid=False, zeroline=False, showticklabels=False, title="", range=[-4.5, 4.5], scaleanchor="x", scaleratio=1
    ),
    template="plotly_white",
    showlegend=True,
    legend=dict(
        title=dict(text="Module Groups", font=dict(size=18)),
        font=dict(size=16),
        x=1.02,
        y=0.5,
        yanchor="middle",
        bgcolor="rgba(255,255,255,0.9)",
        bordercolor="#CCCCCC",
        borderwidth=1,
    ),
    margin=dict(l=50, r=180, t=100, b=50),
    plot_bgcolor="white",
)

# Save as PNG (4800x2700 at scale=3)
fig.write_image("plot.png", width=1600, height=900, scale=3)

# Save as HTML for interactivity
fig.write_html("plot.html", include_plotlyjs=True, full_html=True)
