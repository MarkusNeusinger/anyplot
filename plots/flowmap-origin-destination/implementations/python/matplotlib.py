""" pyplots.ai
flowmap-origin-destination: Origin-Destination Flow Map
Library: matplotlib 3.10.8 | Python 3.13.11
Quality: 90/100 | Created: 2026-01-16
"""

import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import numpy as np


# Data - Trade flows between major world ports
np.random.seed(42)

# Major port cities with coordinates (lon, lat)
ports = {
    "Shanghai": (121.47, 31.23),
    "Singapore": (103.82, 1.35),
    "Rotterdam": (4.48, 51.92),
    "Los Angeles": (-118.25, 33.75),
    "Dubai": (55.27, 25.20),
    "Hong Kong": (114.17, 22.32),
    "Busan": (129.03, 35.10),
    "Hamburg": (9.99, 53.55),
    "New York": (-74.00, 40.71),
    "Santos": (-46.33, -23.95),
}

# Define trade flows (origin, destination, flow volume in million TEUs)
flows = [
    ("Shanghai", "Los Angeles", 8.5),
    ("Shanghai", "Rotterdam", 6.2),
    ("Shanghai", "Singapore", 5.8),
    ("Singapore", "Rotterdam", 4.5),
    ("Hong Kong", "Los Angeles", 3.9),
    ("Busan", "Los Angeles", 3.2),
    ("Dubai", "Rotterdam", 2.8),
    ("Hamburg", "New York", 2.5),
    ("Rotterdam", "New York", 2.3),
    ("Santos", "Rotterdam", 1.9),
    ("Shanghai", "Dubai", 3.5),
    ("Singapore", "Dubai", 2.7),
    ("Hong Kong", "Singapore", 2.4),
    ("Shanghai", "Hamburg", 4.1),
    ("Busan", "Shanghai", 1.8),
]

# Create figure
fig, ax = plt.subplots(figsize=(16, 9))

# Draw simplified world map background (coastline approximation)
ax.set_facecolor("#e8f4f8")
ax.set_xlim(-180, 180)
ax.set_ylim(-60, 80)

# Simplified continent outlines (rough polygons)
continent_coords = [
    [
        (-170, 60),
        (-170, 25),
        (-130, 25),
        (-100, 20),
        (-80, 25),
        (-60, 45),
        (-55, 50),
        (-70, 70),
        (-170, 70),
        (-170, 60),
    ],
    [(-80, 10), (-60, 5), (-35, -5), (-35, -25), (-55, -55), (-75, -55), (-80, -20), (-80, 10)],
    [(-10, 35), (0, 35), (30, 35), (40, 45), (30, 60), (30, 70), (10, 70), (-10, 60), (-10, 35)],
    [(-20, 35), (35, 35), (50, 15), (50, -5), (35, -35), (20, -35), (10, -5), (-20, 5), (-20, 35)],
    [
        (30, 35),
        (60, 25),
        (70, 25),
        (100, 20),
        (120, 25),
        (145, 45),
        (145, 55),
        (180, 65),
        (180, 75),
        (60, 75),
        (30, 50),
        (30, 35),
    ],
    [(110, -10), (155, -10), (155, -40), (130, -40), (110, -25), (110, -10)],
]

for coords in continent_coords:
    xs = [c[0] for c in coords]
    ys = [c[1] for c in coords]
    ax.fill(xs, ys, color="#d4e5d4", edgecolor="#888888", linewidth=0.5, zorder=1)

# Normalize flow values for line width
max_flow = max(f[2] for f in flows)
min_flow = min(f[2] for f in flows)

# Draw flows with curved arcs (Bezier curves)
t = np.linspace(0, 1, 50)  # Parameter for curve
height_factor = 0.25

for origin_name, dest_name, flow in flows:
    ox, oy = ports[origin_name]
    dx, dy = ports[dest_name]

    # Calculate midpoint
    mx, my = (ox + dx) / 2, (oy + dy) / 2

    # Distance between points
    distance = np.sqrt((dx - ox) ** 2 + (dy - oy) ** 2)

    # Perpendicular direction for curve control point
    if distance > 0:
        px, py = -(dy - oy) / distance, (dx - ox) / distance
    else:
        px, py = 0, 1

    # Control point for quadratic Bezier curve
    cx = mx + px * distance * height_factor
    cy = my + py * distance * height_factor

    # Quadratic Bezier curve formula
    x = (1 - t) ** 2 * ox + 2 * (1 - t) * t * cx + t**2 * dx
    y = (1 - t) ** 2 * oy + 2 * (1 - t) * t * cy + t**2 * dy

    # Calculate line width based on flow (2-10 range)
    normalized = (flow - min_flow) / (max_flow - min_flow) if max_flow > min_flow else 0.5
    line_width = 2 + normalized * 8

    # Calculate alpha based on flow (0.4-0.8 range)
    alpha = 0.4 + normalized * 0.4

    # Draw arc with color based on flow magnitude
    color = plt.cm.Blues(0.4 + normalized * 0.5)
    ax.plot(x, y, color=color, linewidth=line_width, alpha=alpha, zorder=3, solid_capstyle="round")

# Draw port markers
for port_name, (lon, lat) in ports.items():
    ax.scatter(lon, lat, s=250, c="#306998", edgecolors="white", linewidths=2, zorder=4)
    # Add labels with offset
    ax.annotate(
        port_name,
        (lon, lat),
        xytext=(5, 5),
        textcoords="offset points",
        fontsize=12,
        fontweight="bold",
        color="#333333",
        zorder=5,
    )

# Create legend for flow magnitude
legend_flows = [2, 5, 8]
legend_handles = []
for lf in legend_flows:
    normalized = (lf - min_flow) / (max_flow - min_flow)
    color = plt.cm.Blues(0.4 + normalized * 0.5)
    line = mpatches.Patch(facecolor=color, edgecolor="none", label=f"{lf} M TEUs", alpha=0.7)
    legend_handles.append(line)

ax.legend(
    handles=legend_handles, loc="lower left", fontsize=14, title="Trade Volume", title_fontsize=16, framealpha=0.9
)

# Labels and title
ax.set_xlabel("Longitude", fontsize=20)
ax.set_ylabel("Latitude", fontsize=20)
ax.set_title("Global Port Trade Routes · flowmap-origin-destination · matplotlib · pyplots.ai", fontsize=24)
ax.tick_params(axis="both", labelsize=16)

# Add grid
ax.grid(True, alpha=0.3, linestyle="--", zorder=0)

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
