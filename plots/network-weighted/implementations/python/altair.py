""" pyplots.ai
network-weighted: Weighted Network Graph with Edge Thickness
Library: altair 6.0.0 | Python 3.13.11
Quality: 92/100 | Created: 2026-01-08
"""

import altair as alt
import numpy as np
import pandas as pd


# Data: Trade network between 15 countries (billions USD)
np.random.seed(42)

nodes = [
    {"id": 0, "name": "USA", "group": "Americas"},
    {"id": 1, "name": "China", "group": "Asia"},
    {"id": 2, "name": "Germany", "group": "Europe"},
    {"id": 3, "name": "Japan", "group": "Asia"},
    {"id": 4, "name": "UK", "group": "Europe"},
    {"id": 5, "name": "France", "group": "Europe"},
    {"id": 6, "name": "India", "group": "Asia"},
    {"id": 7, "name": "Italy", "group": "Europe"},
    {"id": 8, "name": "Brazil", "group": "Americas"},
    {"id": 9, "name": "Canada", "group": "Americas"},
    {"id": 10, "name": "S. Korea", "group": "Asia"},
    {"id": 11, "name": "Australia", "group": "Oceania"},
    {"id": 12, "name": "Mexico", "group": "Americas"},
    {"id": 13, "name": "Spain", "group": "Europe"},
    {"id": 14, "name": "Netherlands", "group": "Europe"},
]

# Trade relationships with weights (billions USD)
edges = [
    (0, 1, 560),
    (0, 2, 185),
    (0, 3, 210),
    (0, 4, 140),
    (0, 9, 580),
    (0, 12, 490),
    (1, 3, 320),
    (1, 10, 280),
    (1, 2, 175),
    (1, 11, 145),
    (2, 5, 165),
    (2, 7, 130),
    (2, 14, 195),
    (2, 4, 125),
    (3, 10, 85),
    (3, 11, 75),
    (4, 5, 95),
    (4, 14, 85),
    (5, 7, 80),
    (5, 13, 75),
    (6, 0, 95),
    (6, 1, 110),
    (8, 0, 60),
    (8, 1, 115),
    (9, 4, 25),
    (10, 0, 120),
    (11, 1, 190),
    (12, 1, 45),
    (13, 5, 55),
    (14, 4, 70),
]

n_nodes = len(nodes)

# Force-directed layout calculation
pos = np.random.rand(n_nodes, 2) * 2 - 1
k = 0.3  # Optimal distance

for iteration in range(200):
    disp = np.zeros((n_nodes, 2))
    # Repulsive forces between all node pairs
    for i in range(n_nodes):
        for j in range(i + 1, n_nodes):
            delta = pos[i] - pos[j]
            dist = max(np.linalg.norm(delta), 0.01)
            force = k * k / dist
            disp[i] += (delta / dist) * force
            disp[j] -= (delta / dist) * force

    # Attractive forces along edges
    for src, tgt, _weight in edges:
        delta = pos[src] - pos[tgt]
        dist = max(np.linalg.norm(delta), 0.01)
        force = dist * dist / k
        disp[src] -= (delta / dist) * force * 0.5
        disp[tgt] += (delta / dist) * force * 0.5

    # Apply displacement with cooling
    temp = 0.1 * (1 - iteration / 200)
    for i in range(n_nodes):
        disp_len = max(np.linalg.norm(disp[i]), 0.01)
        pos[i] += (disp[i] / disp_len) * min(disp_len, temp)

    pos = np.clip(pos, -1, 1)

# Calculate weighted degree for node sizing
weighted_degree = dict.fromkeys(range(n_nodes), 0)
for src, tgt, weight in edges:
    weighted_degree[src] += weight
    weighted_degree[tgt] += weight

max_degree = max(weighted_degree.values())
min_degree = min(weighted_degree.values())

# Build node dataframe
node_df = pd.DataFrame(nodes)
node_df["x"] = pos[:, 0]
node_df["y"] = pos[:, 1]
node_df["weighted_degree"] = [weighted_degree[i] for i in range(n_nodes)]

# Get weight range for scaling edge thickness
min_weight = min(e[2] for e in edges)
max_weight = max(e[2] for e in edges)

# Build edge dataframe
edge_data = []
for src, tgt, weight in edges:
    edge_data.append({"x": pos[src, 0], "y": pos[src, 1], "x2": pos[tgt, 0], "y2": pos[tgt, 1], "weight": weight})
edge_df = pd.DataFrame(edge_data)

# Create edge layer with varying thickness
edge_chart = (
    alt.Chart(edge_df)
    .mark_rule(opacity=0.5)
    .encode(
        x=alt.X("x:Q", axis=None, scale=alt.Scale(domain=[-1.2, 1.2])),
        y=alt.Y("y:Q", axis=None, scale=alt.Scale(domain=[-1.2, 1.2])),
        x2="x2:Q",
        y2="y2:Q",
        strokeWidth=alt.StrokeWidth(
            "weight:Q",
            scale=alt.Scale(domain=[min_weight, max_weight], range=[2, 14]),
            legend=alt.Legend(title="Trade (B USD)", titleFontSize=18, labelFontSize=16, orient="right", offset=10),
        ),
        color=alt.value("#555555"),
    )
)

# Create node layer with size by weighted degree
node_chart = (
    alt.Chart(node_df)
    .mark_circle(stroke="#222222", strokeWidth=2)
    .encode(
        x=alt.X("x:Q", axis=None, scale=alt.Scale(domain=[-1.2, 1.2])),
        y=alt.Y("y:Q", axis=None, scale=alt.Scale(domain=[-1.2, 1.2])),
        size=alt.Size(
            "weighted_degree:Q",
            scale=alt.Scale(domain=[min_degree, max_degree], range=[600, 3000]),
            legend=alt.Legend(title="Total Trade", titleFontSize=18, labelFontSize=16, orient="right", offset=10),
        ),
        color=alt.Color(
            "group:N",
            scale=alt.Scale(
                domain=["Americas", "Europe", "Asia", "Oceania"], range=["#306998", "#FFD43B", "#FF6B6B", "#4ECDC4"]
            ),
            legend=alt.Legend(
                title="Region", titleFontSize=18, labelFontSize=16, orient="right", symbolSize=600, offset=10
            ),
        ),
        tooltip=["name:N", "group:N", "weighted_degree:Q"],
    )
)

# Create label layer for node names
label_chart = (
    alt.Chart(node_df)
    .mark_text(fontSize=16, fontWeight="bold", dy=-22)
    .encode(
        x=alt.X("x:Q", scale=alt.Scale(domain=[-1.2, 1.2])),
        y=alt.Y("y:Q", scale=alt.Scale(domain=[-1.2, 1.2])),
        text="name:N",
        color=alt.value("#222222"),
    )
)

# Combine all layers
chart = (
    (edge_chart + node_chart + label_chart)
    .properties(
        width=1600,
        height=900,
        title=alt.Title(
            "network-weighted · altair · pyplots.ai",
            fontSize=28,
            anchor="middle",
            subtitle="International Trade Network: Edge thickness shows bilateral trade volume (billions USD)",
            subtitleFontSize=18,
        ),
    )
    .configure_view(strokeWidth=0)
    .configure_legend(titleFontSize=18, labelFontSize=16, padding=10)
)

# Save outputs
chart.save("plot.png", scale_factor=3.0)
chart.save("plot.html")
