""" pyplots.ai
network-weighted: Weighted Network Graph with Edge Thickness
Library: plotnine 0.15.2 | Python 3.13.11
Quality: 90/100 | Created: 2026-01-08
"""

import numpy as np
import pandas as pd
from plotnine import (
    aes,
    element_text,
    geom_point,
    geom_segment,
    geom_text,
    ggplot,
    guide_legend,
    guides,
    labs,
    scale_size_continuous,
    theme,
    theme_void,
)


# Data - Trade network between countries (billions USD annual trade volume)
np.random.seed(42)

# Define nodes (countries)
nodes = pd.DataFrame(
    {
        "id": [
            "USA",
            "China",
            "Germany",
            "Japan",
            "UK",
            "France",
            "Canada",
            "Mexico",
            "S.Korea",
            "India",
            "Brazil",
            "Australia",
        ],
        "group": [
            "Americas",
            "Asia",
            "Europe",
            "Asia",
            "Europe",
            "Europe",
            "Americas",
            "Americas",
            "Asia",
            "Asia",
            "Americas",
            "Oceania",
        ],
    }
)

# Define edges (trade relationships with weights in billions USD)
edges_data = [
    ("USA", "China", 580),
    ("USA", "Canada", 620),
    ("USA", "Mexico", 550),
    ("USA", "Japan", 180),
    ("USA", "Germany", 160),
    ("USA", "UK", 130),
    ("USA", "S.Korea", 140),
    ("China", "Japan", 280),
    ("China", "S.Korea", 240),
    ("China", "Germany", 170),
    ("China", "Australia", 150),
    ("China", "India", 90),
    ("Germany", "France", 180),
    ("Germany", "UK", 140),
    ("Germany", "Japan", 45),
    ("France", "UK", 80),
    ("Japan", "S.Korea", 70),
    ("Canada", "Mexico", 35),
    ("India", "UK", 30),
    ("Brazil", "USA", 75),
    ("Brazil", "China", 95),
    ("Australia", "Japan", 55),
]

edges = pd.DataFrame(edges_data, columns=["source", "target", "weight"])

# Create node positions using circular layout
n_nodes = len(nodes)
angles = np.linspace(0, 2 * np.pi, n_nodes, endpoint=False)

# Arrange nodes in circular pattern with slight variation
node_positions = {}
for i, node_id in enumerate(nodes["id"]):
    radius = 4.0 + 0.3 * np.sin(i * 1.5)
    node_positions[node_id] = (radius * np.cos(angles[i]), radius * np.sin(angles[i]))

# Calculate weighted degree for node sizing (sum of connected edge weights)
weighted_degree = {}
for node_id in nodes["id"]:
    total_weight = edges[(edges["source"] == node_id) | (edges["target"] == node_id)]["weight"].sum()
    weighted_degree[node_id] = total_weight

# Add positions and weighted degree to nodes DataFrame
nodes["x"] = nodes["id"].map(lambda n: node_positions[n][0])
nodes["y"] = nodes["id"].map(lambda n: node_positions[n][1])
nodes["weighted_degree"] = nodes["id"].map(weighted_degree)

# Create edges DataFrame with coordinates
edges["x"] = edges["source"].map(lambda n: node_positions[n][0])
edges["y"] = edges["source"].map(lambda n: node_positions[n][1])
edges["xend"] = edges["target"].map(lambda n: node_positions[n][0])
edges["yend"] = edges["target"].map(lambda n: node_positions[n][1])

# Scale edge thickness for better visibility (1-6 range)
weight_min, weight_max = edges["weight"].min(), edges["weight"].max()
edges["thickness"] = 1.0 + (edges["weight"] - weight_min) / (weight_max - weight_min) * 5

# Scale node size based on weighted degree (5-16 range for better visibility)
degree_min = nodes["weighted_degree"].min()
degree_max = nodes["weighted_degree"].max()
nodes["node_size"] = 5 + (nodes["weighted_degree"] - degree_min) / (degree_max - degree_min) * 11

# Create plot
plot = (
    ggplot()
    # Draw edges with thickness mapped to trade weight
    + geom_segment(
        data=edges, mapping=aes(x="x", y="y", xend="xend", yend="yend", size="weight"), color="#306998", alpha=0.55
    )
    # Draw nodes with size mapped to weighted degree - larger for better visibility
    + geom_point(
        data=nodes,
        mapping=aes(x="x", y="y", size="weighted_degree"),
        color="#1a1a1a",
        stroke=1.5,
        fill="#FFD43B",
        show_legend=False,
    )
    # Add node labels with offset - larger size for better legibility
    + geom_text(
        data=nodes, mapping=aes(x="x", y="y", label="id"), size=14, color="#1a1a1a", fontweight="bold", nudge_y=0.65
    )
    # Scale edge thickness
    + scale_size_continuous(range=(0.8, 6), name="Trade Volume\n(Billions USD)", breaks=[100, 300, 500])
    # Labels and title - format: {spec-id} · {library} · pyplots.ai
    + labs(
        title="network-weighted · plotnine · pyplots.ai",
        subtitle="Edge thickness represents bilateral trade volume between countries",
    )
    # Clean theme with no axes
    + theme_void()
    + theme(
        figure_size=(16, 9),
        plot_title=element_text(size=26, ha="center", weight="bold"),
        plot_subtitle=element_text(size=18, ha="center", color="#555555"),
        legend_title=element_text(size=16),
        legend_text=element_text(size=14),
        legend_position="right",
        plot_margin=0.05,
    )
    + guides(size=guide_legend(override_aes={"alpha": 0.8}))
)

# Save plot
plot.save("plot.png", dpi=300, width=16, height=9, verbose=False)
