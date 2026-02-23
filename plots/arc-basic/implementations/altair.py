"""pyplots.ai
arc-basic: Basic Arc Diagram
Library: altair 6.0.0 | Python 3.14.3
Quality: 86/100 | Updated: 2026-02-23
"""

import altair as alt
import numpy as np
import pandas as pd


# Data: Character interactions in a story chapter
np.random.seed(42)

nodes = ["Alice", "Bob", "Carol", "David", "Eve", "Frank", "Grace", "Henry", "Iris", "Jack"]
n_nodes = len(nodes)

edges = [
    (0, 1, 3),  # Alice-Bob (strong)
    (0, 3, 2),  # Alice-David
    (1, 2, 2),  # Bob-Carol
    (2, 4, 1),  # Carol-Eve
    (3, 5, 2),  # David-Frank
    (4, 6, 1),  # Eve-Grace
    (0, 7, 1),  # Alice-Henry (long-range)
    (1, 5, 2),  # Bob-Frank
    (2, 3, 3),  # Carol-David (strong)
    (5, 8, 1),  # Frank-Iris
    (6, 9, 2),  # Grace-Jack
    (0, 9, 1),  # Alice-Jack (longest range)
    (3, 7, 2),  # David-Henry
    (7, 8, 1),  # Henry-Iris
    (8, 9, 2),  # Iris-Jack
]

# Node positions along x-axis
x_positions = np.linspace(0, 100, n_nodes)
y_baseline = 0

# Node dataframe with connection count for sizing
connection_count = [0] * n_nodes
for s, e, w in edges:
    connection_count[s] += w
    connection_count[e] += w

nodes_df = pd.DataFrame({"x": x_positions, "y": [y_baseline] * n_nodes, "name": nodes, "connections": connection_count})

# Build arc paths as semicircular curves
arc_data = []
points_per_arc = 50
max_span = max(abs(e - s) for s, e, _ in edges)

for edge_id, (start, end, weight) in enumerate(edges):
    x_start = x_positions[start]
    x_end = x_positions[end]
    span = abs(end - start)
    height = 7 * span

    angles = np.linspace(0, np.pi, points_per_arc)
    x_center = (x_start + x_end) / 2
    radius_x = abs(x_end - x_start) / 2
    radius_y = height / 2

    pair = f"{nodes[start]}–{nodes[end]}"
    for i, angle in enumerate(angles):
        arc_data.append(
            {
                "edge_id": edge_id,
                "x": x_center - radius_x * np.cos(angle),
                "y": y_baseline + radius_y * np.sin(angle),
                "weight": weight,
                "pair": pair,
                "order": i,
            }
        )

arcs_df = pd.DataFrame(arc_data)

# Y-domain: tight around data for better canvas use
max_arc_height = 7 * max_span / 2
y_domain = [-5, max_arc_height + 4]
x_domain = [-4, 104]

# Hover selection for interactive arc highlighting (HTML export)
hover = alt.selection_point(on="pointerover", empty=False, fields=["edge_id"])

# Arcs: weight drives color, thickness, and opacity for visual hierarchy
arcs = (
    alt.Chart(arcs_df)
    .mark_line()
    .encode(
        x=alt.X("x:Q", axis=None, scale=alt.Scale(domain=x_domain)),
        y=alt.Y("y:Q", axis=None, scale=alt.Scale(domain=y_domain)),
        detail="edge_id:N",
        strokeWidth=alt.StrokeWidth(
            "weight:Q",
            scale=alt.Scale(domain=[1, 3], range=[1.5, 6]),
            legend=alt.Legend(
                title="Interaction Strength",
                titleFontSize=16,
                labelFontSize=16,
                orient="top-right",
                offset=10,
                values=[1, 2, 3],
                symbolStrokeWidth=3,
                labelExpr="datum.value == 1 ? 'Weak' : datum.value == 2 ? 'Moderate' : 'Strong'",
            ),
        ),
        strokeOpacity=alt.condition(
            hover,
            alt.value(0.95),
            alt.StrokeOpacity("weight:Q", scale=alt.Scale(domain=[1, 3], range=[0.3, 0.8]), legend=None),
        ),
        color=alt.Color(
            "weight:Q", scale=alt.Scale(domain=[1, 2, 3], range=["#7daed4", "#306998", "#152d4a"]), legend=None
        ),
        tooltip=[alt.Tooltip("pair:N", title="Connection"), alt.Tooltip("weight:Q", title="Strength")],
    )
    .add_params(hover)
)

# Nodes: size proportional to total connection weight
node_points = (
    alt.Chart(nodes_df)
    .mark_circle(color="#FFD43B", stroke="#152d4a", strokeWidth=2.5)
    .encode(
        x=alt.X("x:Q", axis=None, scale=alt.Scale(domain=x_domain)),
        y=alt.Y("y:Q", axis=None, scale=alt.Scale(domain=y_domain)),
        size=alt.Size("connections:Q", scale=alt.Scale(domain=[2, 11], range=[500, 1200]), legend=None),
        tooltip=[alt.Tooltip("name:N", title="Character"), alt.Tooltip("connections:Q", title="Total Weight")],
    )
)

# Node labels below baseline
node_labels = (
    alt.Chart(nodes_df)
    .mark_text(dy=30, fontSize=18, fontWeight="bold", color="#152d4a")
    .encode(x=alt.X("x:Q"), y=alt.Y("y:Q"), text="name:N")
)

# Combine layers
chart = (
    alt.layer(arcs, node_points, node_labels)
    .properties(
        width=1600,
        height=900,
        title=alt.Title("arc-basic · altair · pyplots.ai", fontSize=28, anchor="middle", offset=15),
    )
    .configure_view(strokeWidth=0)
    .configure_legend(strokeColor="transparent", padding=12, titleColor="#152d4a", labelColor="#333333")
)

# Save
chart.save("plot.png", scale_factor=3.0)
chart.save("plot.html")
