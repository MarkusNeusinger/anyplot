""" pyplots.ai
alluvial-basic: Basic Alluvial Diagram
Library: matplotlib 3.10.8 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-24
"""

import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.path import Path


# Data: Voter migration across 4 election cycles
# Categories: Party A, Party B, Party C, Independent
np.random.seed(42)

time_points = ["2012", "2016", "2020", "2024"]
categories = ["Party A", "Party B", "Party C", "Independent"]
colors = {
    "Party A": "#306998",  # Python Blue
    "Party B": "#FFD43B",  # Python Yellow
    "Party C": "#4ECDC4",  # Teal
    "Independent": "#95A5A6",  # Gray
}

# Node values at each time point (thousands of voters)
node_values = {
    "2012": {"Party A": 450, "Party B": 380, "Party C": 120, "Independent": 50},
    "2016": {"Party A": 420, "Party B": 350, "Party C": 150, "Independent": 80},
    "2020": {"Party A": 380, "Party B": 320, "Party C": 200, "Independent": 100},
    "2024": {"Party A": 350, "Party B": 280, "Party C": 250, "Independent": 120},
}

# Flow matrix between consecutive time points
flows = [
    # 2012 -> 2016
    {
        ("Party A", "Party A"): 380,
        ("Party A", "Party B"): 20,
        ("Party A", "Party C"): 30,
        ("Party A", "Independent"): 20,
        ("Party B", "Party A"): 25,
        ("Party B", "Party B"): 310,
        ("Party B", "Party C"): 25,
        ("Party B", "Independent"): 20,
        ("Party C", "Party A"): 10,
        ("Party C", "Party B"): 15,
        ("Party C", "Party C"): 80,
        ("Party C", "Independent"): 15,
        ("Independent", "Party A"): 5,
        ("Independent", "Party B"): 5,
        ("Independent", "Party C"): 15,
        ("Independent", "Independent"): 25,
    },
    # 2016 -> 2020
    {
        ("Party A", "Party A"): 340,
        ("Party A", "Party B"): 15,
        ("Party A", "Party C"): 45,
        ("Party A", "Independent"): 20,
        ("Party B", "Party A"): 20,
        ("Party B", "Party B"): 285,
        ("Party B", "Party C"): 30,
        ("Party B", "Independent"): 15,
        ("Party C", "Party A"): 15,
        ("Party C", "Party B"): 15,
        ("Party C", "Party C"): 105,
        ("Party C", "Independent"): 15,
        ("Independent", "Party A"): 5,
        ("Independent", "Party B"): 5,
        ("Independent", "Party C"): 20,
        ("Independent", "Independent"): 50,
    },
    # 2020 -> 2024
    {
        ("Party A", "Party A"): 310,
        ("Party A", "Party B"): 10,
        ("Party A", "Party C"): 40,
        ("Party A", "Independent"): 20,
        ("Party B", "Party A"): 20,
        ("Party B", "Party B"): 255,
        ("Party B", "Party C"): 30,
        ("Party B", "Independent"): 15,
        ("Party C", "Party A"): 15,
        ("Party C", "Party B"): 10,
        ("Party C", "Party C"): 160,
        ("Party C", "Independent"): 15,
        ("Independent", "Party A"): 5,
        ("Independent", "Party B"): 5,
        ("Independent", "Party C"): 20,
        ("Independent", "Independent"): 70,
    },
]

# Plot setup
fig, ax = plt.subplots(figsize=(16, 9))

# Layout parameters
x_positions = [2.0, 4.0, 6.0, 8.0]
node_width = 0.6
total_height = 7.5
node_gap = 0.25

# Calculate node positions and store boundaries
node_bounds = {}
for t_idx, tp in enumerate(time_points):
    values = [node_values[tp][cat] for cat in categories]
    total = sum(values)
    usable_height = total_height - (len(categories) - 1) * node_gap
    heights = [v / total * usable_height for v in values]

    y = 0.5
    for c_idx, cat in enumerate(categories):
        h = heights[c_idx]
        node_bounds[(tp, cat)] = {"x": x_positions[t_idx], "y_start": y, "height": h}
        y += h + node_gap

# Draw flows between consecutive time points
for t_idx in range(len(time_points) - 1):
    tp_from = time_points[t_idx]
    tp_to = time_points[t_idx + 1]

    from_offsets = dict.fromkeys(categories, 0)
    to_offsets = dict.fromkeys(categories, 0)

    flow_data = flows[t_idx]
    for from_cat in categories:
        for to_cat in categories:
            flow_val = flow_data.get((from_cat, to_cat), 0)
            if flow_val <= 0:
                continue

            from_node = node_bounds[(tp_from, from_cat)]
            to_node = node_bounds[(tp_to, to_cat)]

            from_total = sum(node_values[tp_from].values())
            to_total = sum(node_values[tp_to].values())

            usable_height = total_height - (len(categories) - 1) * node_gap
            from_height = flow_val / from_total * usable_height
            to_height = flow_val / to_total * usable_height

            x0 = from_node["x"] + node_width / 2
            x1 = to_node["x"] - node_width / 2
            mid_x = (x0 + x1) / 2

            y0_start = from_node["y_start"] + from_offsets[from_cat]
            y0_end = y0_start + from_height
            y1_start = to_node["y_start"] + to_offsets[to_cat]
            y1_end = y1_start + to_height

            # Draw curved flow band using bezier path
            verts = [
                (x0, y0_start),
                (mid_x, y0_start),
                (mid_x, y1_start),
                (x1, y1_start),
                (x1, y1_end),
                (mid_x, y1_end),
                (mid_x, y0_end),
                (x0, y0_end),
                (x0, y0_start),
            ]
            codes = [
                Path.MOVETO,
                Path.CURVE4,
                Path.CURVE4,
                Path.CURVE4,
                Path.LINETO,
                Path.CURVE4,
                Path.CURVE4,
                Path.CURVE4,
                Path.CLOSEPOLY,
            ]
            path = Path(verts, codes)
            patch = mpatches.PathPatch(path, facecolor=colors[from_cat], edgecolor="none", alpha=0.4)
            ax.add_patch(patch)

            from_offsets[from_cat] += from_height
            to_offsets[to_cat] += to_height

# Draw nodes (rectangles)
for tp in time_points:
    for cat in categories:
        node = node_bounds[(tp, cat)]
        y_start = node["y_start"]
        height = node["height"]
        x = node["x"]

        rect = mpatches.Rectangle(
            (x - node_width / 2, y_start), node_width, height, facecolor=colors[cat], edgecolor="white", linewidth=2
        )
        ax.add_patch(rect)

        # Add category label (abbreviated for small nodes)
        value = node_values[tp][cat]
        short_name = "Indep." if cat == "Independent" else cat
        label = f"{short_name}\n({value}K)"
        ax.text(
            x,
            y_start + height / 2,
            label,
            ha="center",
            va="center",
            fontsize=13,
            fontweight="bold",
            color="white" if cat != "Party B" else "black",
        )

# Add time point labels
for t_idx, tp in enumerate(time_points):
    ax.text(
        x_positions[t_idx],
        total_height + 0.8,
        tp,
        ha="center",
        va="bottom",
        fontsize=22,
        fontweight="bold",
        color="#333333",
    )

# Create legend
legend_handles = [mpatches.Patch(color=colors[cat], label=cat) for cat in categories]
ax.legend(
    handles=legend_handles, loc="lower left", bbox_to_anchor=(0.01, 0.02), fontsize=16, framealpha=0.9, edgecolor="none"
)

# Styling
ax.set_xlim(0.8, 9.2)
ax.set_ylim(-0.5, total_height + 1.5)
ax.set_title(
    "Voter Migration 2012-2024 · alluvial-basic · matplotlib · pyplots.ai", fontsize=24, fontweight="bold", pad=20
)
ax.axis("off")

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight", facecolor="white")
