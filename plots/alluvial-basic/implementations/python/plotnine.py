""" pyplots.ai
alluvial-basic: Basic Alluvial Diagram
Library: plotnine 0.15.2 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-26
"""

import sys


# Prevent current directory from shadowing the plotnine package
sys.path = [p for p in sys.path if not p.endswith("implementations")]

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from plotnine import (  # noqa: E402
    aes,
    annotate,
    coord_cartesian,
    element_blank,
    element_text,
    geom_polygon,
    geom_rect,
    geom_text,
    ggplot,
    labs,
    scale_fill_manual,
    theme,
    theme_minimal,
)


# Data - Voter migration between parties across 4 election cycles
# Each row represents a transition from one party at time t to another at time t+1
transitions = pd.DataFrame(
    {
        "from_time": [0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 2, 2, 2, 2, 2, 2, 2, 2, 2],
        "to_time": [1, 1, 1, 1, 1, 1, 1, 1, 1, 2, 2, 2, 2, 2, 2, 2, 2, 2, 3, 3, 3, 3, 3, 3, 3, 3, 3],
        "from_party": [
            "Democrats",
            "Democrats",
            "Democrats",
            "Republicans",
            "Republicans",
            "Republicans",
            "Independent",
            "Independent",
            "Independent",
            "Democrats",
            "Democrats",
            "Democrats",
            "Republicans",
            "Republicans",
            "Republicans",
            "Independent",
            "Independent",
            "Independent",
            "Democrats",
            "Democrats",
            "Democrats",
            "Republicans",
            "Republicans",
            "Republicans",
            "Independent",
            "Independent",
            "Independent",
        ],
        "to_party": [
            "Democrats",
            "Republicans",
            "Independent",
            "Democrats",
            "Republicans",
            "Independent",
            "Democrats",
            "Republicans",
            "Independent",
            "Democrats",
            "Republicans",
            "Independent",
            "Democrats",
            "Republicans",
            "Independent",
            "Democrats",
            "Republicans",
            "Independent",
            "Democrats",
            "Republicans",
            "Independent",
            "Democrats",
            "Republicans",
            "Independent",
            "Democrats",
            "Republicans",
            "Independent",
        ],
        "voters": [38, 4, 3, 3, 36, 2, 2, 3, 9, 35, 5, 5, 4, 33, 4, 4, 4, 6, 32, 6, 7, 5, 30, 6, 6, 5, 3],
    }
)

# Party colors - colorblind-safe palette
party_colors = {
    "Democrats": "#306998",  # Python Blue
    "Republicans": "#E74C3C",  # Red
    "Independent": "#FFD43B",  # Python Yellow
}

parties = ["Democrats", "Republicans", "Independent"]
time_points = [0, 1, 2, 3]
time_labels = ["2016", "2018", "2020", "2022"]

# Layout parameters
x_positions = {0: 0.15, 1: 0.38, 2: 0.62, 3: 0.85}
node_width = 0.06
node_gap = 0.04
total_height = 0.85
y_start = 0.95

# Calculate node sizes at each time point
node_positions = {}
for t in time_points:
    if t == 0:
        totals = transitions[transitions["from_time"] == t].groupby("from_party")["voters"].sum()
    else:
        totals = transitions[transitions["to_time"] == t].groupby("to_party")["voters"].sum()

    total_voters = totals.sum()
    current_y = y_start

    for party in parties:
        count = totals.get(party, 0)
        height = (count / total_voters) * total_height

        node_positions[(t, party)] = {
            "x": x_positions[t],
            "y_top": current_y,
            "y_bottom": current_y - height,
            "height": height,
            "count": count,
            "flow_offset": 0,
        }
        current_y = current_y - height - node_gap

# Build node rectangles
node_data = []
for (t, party), pos in node_positions.items():
    node_data.append(
        {
            "time": t,
            "party": party,
            "xmin": pos["x"] - node_width / 2,
            "xmax": pos["x"] + node_width / 2,
            "ymin": pos["y_bottom"],
            "ymax": pos["y_top"],
            "label_y": (pos["y_top"] + pos["y_bottom"]) / 2,
            "count": pos["count"],
        }
    )
nodes_df = pd.DataFrame(node_data)

# Build flow polygons between adjacent time points
# Filter out very small transitions (< 3 voters) to improve clarity
flow_polygons = []
min_voters_for_flow = 3

for _, row in transitions.iterrows():
    from_t = row["from_time"]
    to_t = row["to_time"]
    from_party = row["from_party"]
    to_party = row["to_party"]
    voters = row["voters"]

    if voters < min_voters_for_flow:
        # Still accumulate offset for small flows but don't draw them
        src_pos = node_positions[(from_t, from_party)]
        tgt_pos = node_positions[(to_t, to_party)]

        total_src = sum(
            transitions[(transitions["from_time"] == from_t) & (transitions["from_party"] == from_party)]["voters"]
        )
        flow_height_src = (voters / total_src) * src_pos["height"] if total_src > 0 else 0

        total_tgt = sum(transitions[(transitions["to_time"] == to_t) & (transitions["to_party"] == to_party)]["voters"])
        flow_height_tgt = (voters / total_tgt) * tgt_pos["height"] if total_tgt > 0 else 0

        src_pos["flow_offset"] += flow_height_src
        tgt_pos["flow_offset"] += flow_height_tgt
        continue

    # Get source and target positions
    src_pos = node_positions[(from_t, from_party)]
    tgt_pos = node_positions[(to_t, to_party)]

    total_src = sum(
        transitions[(transitions["from_time"] == from_t) & (transitions["from_party"] == from_party)]["voters"]
    )
    flow_height_src = (voters / total_src) * src_pos["height"] if total_src > 0 else 0

    total_tgt = sum(transitions[(transitions["to_time"] == to_t) & (transitions["to_party"] == to_party)]["voters"])
    flow_height_tgt = (voters / total_tgt) * tgt_pos["height"] if total_tgt > 0 else 0

    # Source connection point
    src_y_top = src_pos["y_top"] - src_pos["flow_offset"]
    src_y_bottom = src_y_top - flow_height_src
    src_pos["flow_offset"] += flow_height_src

    # Target connection point
    tgt_y_top = tgt_pos["y_top"] - tgt_pos["flow_offset"]
    tgt_y_bottom = tgt_y_top - flow_height_tgt
    tgt_pos["flow_offset"] += flow_height_tgt

    # Create curved flow polygon
    flow_x_left = x_positions[from_t] + node_width / 2
    flow_x_right = x_positions[to_t] - node_width / 2
    n_points = 40

    # Smooth cubic interpolation for top and bottom edges
    t_param = np.linspace(0, 1, n_points)
    x_top = flow_x_left + (flow_x_right - flow_x_left) * t_param
    y_top = src_y_top + (tgt_y_top - src_y_top) * (3 * t_param**2 - 2 * t_param**3)

    x_bottom = flow_x_right + (flow_x_left - flow_x_right) * t_param
    y_bottom = tgt_y_bottom + (src_y_bottom - tgt_y_bottom) * (3 * t_param**2 - 2 * t_param**3)

    # Combine into polygon
    x_polygon = np.concatenate([x_top, x_bottom])
    y_polygon = np.concatenate([y_top, y_bottom])

    flow_id = f"{from_t}_{to_t}_{from_party}_{to_party}"
    for i in range(len(x_polygon)):
        flow_polygons.append({"x": x_polygon[i], "y": y_polygon[i], "flow_id": flow_id, "from_party": from_party})

flows_df = pd.DataFrame(flow_polygons)

# Create the plot
plot = (
    ggplot()
    # Flow polygons with transparency - colored by source party
    + geom_polygon(flows_df, aes(x="x", y="y", group="flow_id", fill="from_party"), alpha=0.5)
    # Node rectangles
    + geom_rect(
        nodes_df, aes(xmin="xmin", xmax="xmax", ymin="ymin", ymax="ymax", fill="party"), color="white", size=0.5
    )
    # Voter count labels on nodes (only for larger nodes)
    + geom_text(
        nodes_df[nodes_df["count"] >= 10],
        aes(x=(nodes_df["xmin"] + nodes_df["xmax"]) / 2, y="label_y", label="count"),
        ha="center",
        va="center",
        size=12,
        color="white",
        fontweight="bold",
    )
    + scale_fill_manual(
        values=party_colors, name="Party", breaks=parties, labels=["Democrats", "Republicans", "Independent"]
    )
    + labs(title="Voter Migration · alluvial-basic · plotnine · pyplots.ai", x="", y="")
    + coord_cartesian(xlim=(0, 1), ylim=(-0.05, 1.05))
    + theme_minimal()
    + theme(
        figure_size=(16, 9),
        plot_title=element_text(size=24, ha="center", weight="bold"),
        axis_text=element_blank(),
        axis_ticks=element_blank(),
        panel_grid=element_blank(),
        legend_title=element_text(size=16, weight="bold"),
        legend_text=element_text(size=14),
        legend_position="right",
    )
)

# Add time point labels at bottom
for t, label in zip(time_points, time_labels, strict=True):
    plot = plot + annotate(
        "text", x=x_positions[t], y=0.02, label=label, size=18, color="#333333", fontweight="bold", ha="center"
    )

# Add party name labels on the left side of first column nodes
for party in parties:
    pos = node_positions[(0, party)]
    label_y = (pos["y_top"] + pos["y_bottom"]) / 2
    plot = plot + annotate(
        "text",
        x=x_positions[0] - node_width / 2 - 0.015,
        y=label_y,
        label=party,
        size=11,
        color="#333333",
        fontweight="bold",
        ha="right",
        va="center",
    )

# Add party name labels on the right side of last column nodes
for party in parties:
    pos = node_positions[(3, party)]
    label_y = (pos["y_top"] + pos["y_bottom"]) / 2
    plot = plot + annotate(
        "text",
        x=x_positions[3] + node_width / 2 + 0.015,
        y=label_y,
        label=party,
        size=11,
        color="#333333",
        fontweight="bold",
        ha="left",
        va="center",
    )

plot.save("plot.png", dpi=300, verbose=False)
