""" pyplots.ai
network-transport-static: Static Transport Network Diagram
Library: matplotlib 3.10.8 | Python 3.13.11
Quality: 91/100 | Created: 2026-01-09
"""

import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import numpy as np


# Seed for reproducibility
np.random.seed(42)

# Station data - regional rail network with geographic-style positioning
stations = [
    {"id": 0, "label": "Central", "x": 0.5, "y": 0.5},
    {"id": 1, "label": "North", "x": 0.5, "y": 0.92},
    {"id": 2, "label": "East", "x": 0.92, "y": 0.5},
    {"id": 3, "label": "South", "x": 0.5, "y": 0.08},
    {"id": 4, "label": "West", "x": 0.08, "y": 0.5},
    {"id": 5, "label": "Airport", "x": 0.88, "y": 0.88},
    {"id": 6, "label": "University", "x": 0.12, "y": 0.88},
    {"id": 7, "label": "Harbor", "x": 0.88, "y": 0.12},
    {"id": 8, "label": "Old Town", "x": 0.12, "y": 0.12},
]

# Route data with manual label positioning for clarity
# t_pos: position along edge (0=source, 1=target)
# offset: perpendicular offset multiplier (positive = left of direction)
routes = [
    # Main lines from Central (RE = Regional Express) - outbound
    {"source": 0, "target": 1, "route": "RE1", "dep": "06:00", "arr": "06:18", "t_pos": 0.58, "offset": 0.10},
    {"source": 0, "target": 2, "route": "RE2", "dep": "06:10", "arr": "06:28", "t_pos": 0.58, "offset": 0.10},
    {"source": 0, "target": 3, "route": "RE3", "dep": "06:20", "arr": "06:38", "t_pos": 0.58, "offset": -0.10},
    {"source": 0, "target": 4, "route": "RE4", "dep": "06:15", "arr": "06:33", "t_pos": 0.58, "offset": 0.10},
    # Main lines - return to Central
    {"source": 1, "target": 0, "route": "RE1", "dep": "06:30", "arr": "06:48", "t_pos": 0.42, "offset": 0.10},
    {"source": 2, "target": 0, "route": "RE2", "dep": "06:40", "arr": "06:58", "t_pos": 0.42, "offset": 0.10},
    {"source": 3, "target": 0, "route": "RE3", "dep": "06:50", "arr": "07:08", "t_pos": 0.42, "offset": -0.10},
    {"source": 4, "target": 0, "route": "RE4", "dep": "06:45", "arr": "07:03", "t_pos": 0.42, "offset": 0.10},
    # Airport express (AIR)
    {"source": 0, "target": 5, "route": "AIR", "dep": "05:30", "arr": "06:00", "t_pos": 0.40, "offset": 0.10},
    {"source": 5, "target": 0, "route": "AIR", "dep": "22:00", "arr": "22:30", "t_pos": 0.60, "offset": 0.10},
    # Suburban lines (S-Bahn) - single direction only
    {"source": 1, "target": 6, "route": "S1", "dep": "07:00", "arr": "07:15", "t_pos": 0.5, "offset": 0.08},
    {"source": 1, "target": 5, "route": "S2", "dep": "07:05", "arr": "07:22", "t_pos": 0.5, "offset": -0.08},
    {"source": 2, "target": 7, "route": "S3", "dep": "07:10", "arr": "07:25", "t_pos": 0.5, "offset": 0.08},
    {"source": 3, "target": 7, "route": "S4", "dep": "07:20", "arr": "07:38", "t_pos": 0.5, "offset": -0.10},
    {"source": 3, "target": 8, "route": "S5", "dep": "07:25", "arr": "07:43", "t_pos": 0.5, "offset": 0.08},
    {"source": 4, "target": 8, "route": "S6", "dep": "07:15", "arr": "07:32", "t_pos": 0.5, "offset": 0.08},
    {"source": 4, "target": 6, "route": "S7", "dep": "07:30", "arr": "07:48", "t_pos": 0.5, "offset": -0.08},
]

# Route type colors
route_colors = {
    "RE": "#306998",  # Python Blue - Regional Express
    "AIR": "#FFD43B",  # Python Yellow - Airport service
    "S": "#2E8B57",  # Sea Green - S-Bahn
}


def get_route_color(route_id):
    """Get color based on route type prefix."""
    for prefix, color in route_colors.items():
        if route_id.startswith(prefix):
            return color
    return "#666666"


# Create figure
fig, ax = plt.subplots(figsize=(16, 9))

# Set axis limits with padding
ax.set_xlim(-0.05, 1.05)
ax.set_ylim(-0.05, 1.05)

# Track route pairs for curve calculation
route_pairs = {}
for route in routes:
    pair = (min(route["source"], route["target"]), max(route["source"], route["target"]))
    if pair not in route_pairs:
        route_pairs[pair] = []
    route_pairs[pair].append(route)

# Draw routes as curved arrows with labels
for route in routes:
    src = stations[route["source"]]
    tgt = stations[route["target"]]

    # Get curve parameters based on multiple routes between same stations
    pair = (min(route["source"], route["target"]), max(route["source"], route["target"]))
    same_pair = route_pairs[pair]
    n_routes = len(same_pair)

    # Calculate curve direction and strength for bidirectional routes
    if n_routes == 1:
        curve = 0.0
    else:
        # Outbound from lower-id station gets positive curve
        if route["source"] < route["target"]:
            curve = 0.2
        else:
            curve = -0.2

    color = get_route_color(route["route"])

    # Draw arrow
    arrow = mpatches.FancyArrowPatch(
        (src["x"], src["y"]),
        (tgt["x"], tgt["y"]),
        connectionstyle=f"arc3,rad={curve}",
        arrowstyle="->,head_length=10,head_width=6",
        color=color,
        linewidth=2.5,
        alpha=0.85,
        zorder=1,
    )
    ax.add_patch(arrow)

    # Get label position from route data
    t = route["t_pos"]
    base_offset = route["offset"]

    # Linear position along edge
    base_x = src["x"] + t * (tgt["x"] - src["x"])
    base_y = src["y"] + t * (tgt["y"] - src["y"])

    # Calculate perpendicular direction
    dx = tgt["x"] - src["x"]
    dy = tgt["y"] - src["y"]
    length = np.sqrt(dx**2 + dy**2)

    if length > 0:
        perp_x = -dy / length
        perp_y = dx / length
    else:
        perp_x, perp_y = 0, 0

    label_x = base_x + perp_x * base_offset
    label_y = base_y + perp_y * base_offset

    # Route label with times
    label_text = f"{route['route']} {route['dep']}→{route['arr']}"
    ax.annotate(
        label_text,
        (label_x, label_y),
        fontsize=9,
        ha="center",
        va="center",
        color="#333333",
        fontweight="bold",
        bbox={"boxstyle": "round,pad=0.15", "facecolor": "white", "edgecolor": color, "linewidth": 1.5, "alpha": 0.95},
        zorder=3,
    )

# Draw station nodes
node_radius = 0.035
for station in stations:
    # Node circle with fill
    circle = plt.Circle(
        (station["x"], station["y"]), node_radius, facecolor="white", edgecolor="#306998", linewidth=3.5, zorder=4
    )
    ax.add_patch(circle)

    # Station label below node
    ax.annotate(
        station["label"],
        (station["x"], station["y"] - node_radius - 0.025),
        fontsize=13,
        ha="center",
        va="top",
        fontweight="bold",
        color="#222222",
        zorder=5,
    )

# Create legend - place in upper left to avoid overlapping with routes
legend_elements = [
    mpatches.Patch(facecolor="#306998", edgecolor="#306998", label="Regional Express (RE)"),
    mpatches.Patch(facecolor="#FFD43B", edgecolor="#FFD43B", label="Airport Service (AIR)"),
    mpatches.Patch(facecolor="#2E8B57", edgecolor="#2E8B57", label="S-Bahn (S)"),
]
ax.legend(handles=legend_elements, loc="upper left", fontsize=14, framealpha=0.95)

# Styling
ax.set_title("network-transport-static · matplotlib · pyplots.ai", fontsize=24, fontweight="bold", pad=20)
ax.set_xlabel("Relative Position (West → East)", fontsize=18)
ax.set_ylabel("Relative Position (South → North)", fontsize=18)
ax.tick_params(axis="both", labelsize=14)
ax.set_aspect("equal")
ax.grid(True, alpha=0.25, linestyle="--")

# Clean appearance - remove spines
for spine in ax.spines.values():
    spine.set_visible(False)

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
