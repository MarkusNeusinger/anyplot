""" pyplots.ai
maze-circular: Circular Maze Puzzle
Library: plotly 6.5.2 | Python 3.13.11
Quality: 91/100 | Created: 2026-01-16
"""

import numpy as np
import plotly.graph_objects as go


# Parameters
np.random.seed(42)
num_rings = 7
sectors_per_ring = [6, 12, 18, 24, 30, 36, 42]  # Increasing sectors for outer rings

# Build maze structure using depth-first search to guarantee one solution
# Each cell is identified by (ring, sector) where ring 0 is outermost
# Track which walls exist between cells
radial_walls = []  # radial_walls[ring][sector] = True if wall exists to next sector
ring_walls = []  # ring_walls[ring][sector] = True if wall exists to inner ring

for r in range(num_rings):
    radial_walls.append([True] * sectors_per_ring[r])
    if r < num_rings - 1:
        ring_walls.append([True] * sectors_per_ring[r])

# Generate maze using depth-first search (randomized)
visited = set()
stack = [(0, 0)]  # Start at ring 0, sector 0 (outer ring)
visited.add((0, 0))

while stack:
    current_ring, current_sector = stack[-1]
    n_sectors = sectors_per_ring[current_ring]

    # Build list of neighboring cells
    neighbors = []
    # Same ring neighbors
    neighbors.append((current_ring, (current_sector + 1) % n_sectors, "radial_next"))
    neighbors.append((current_ring, (current_sector - 1) % n_sectors, "radial_prev"))
    # Inner ring neighbor
    if current_ring < num_rings - 1:
        inner_sectors = sectors_per_ring[current_ring + 1]
        inner_sector = int(current_sector * inner_sectors / n_sectors)
        neighbors.append((current_ring + 1, inner_sector, "ring_in"))
    # Outer ring neighbor
    if current_ring > 0:
        outer_sectors = sectors_per_ring[current_ring - 1]
        outer_sector = int(current_sector * outer_sectors / n_sectors)
        neighbors.append((current_ring - 1, outer_sector, "ring_out"))

    # Filter to unvisited neighbors
    unvisited = [(r, s, d) for r, s, d in neighbors if (r, s) not in visited]

    if unvisited:
        next_ring, next_sector, direction = unvisited[np.random.randint(len(unvisited))]

        # Remove wall between current and next cell
        if direction == "radial_next":
            radial_walls[current_ring][current_sector] = False
        elif direction == "radial_prev":
            radial_walls[current_ring][next_sector] = False
        elif direction == "ring_in":
            ring_walls[current_ring][current_sector] = False
        elif direction == "ring_out":
            ring_walls[next_ring][next_sector] = False

        visited.add((next_ring, next_sector))
        stack.append((next_ring, next_sector))
    else:
        stack.pop()

# Create figure
fig = go.Figure()

# Drawing parameters
center_x, center_y = 0, 0
ring_width = 1.0
wall_color = "black"
wall_width = 3
outer_radius = num_rings * ring_width

# Draw concentric ring walls (arcs where passages are blocked)
for ring_idx in range(num_rings):
    n_sectors = sectors_per_ring[ring_idx]
    sector_angle = 2 * np.pi / n_sectors

    if ring_idx < num_rings - 1:
        inner_radius = (num_rings - ring_idx - 1) * ring_width
        for sector in range(n_sectors):
            if ring_walls[ring_idx][sector]:
                theta_start = sector * sector_angle
                theta_end = (sector + 1) * sector_angle
                theta = np.linspace(theta_start, theta_end, 30)
                x = center_x + inner_radius * np.cos(theta)
                y = center_y + inner_radius * np.sin(theta)
                fig.add_trace(
                    go.Scatter(
                        x=x, y=y, mode="lines", line={"color": wall_color, "width": wall_width}, showlegend=False
                    )
                )

# Draw outer boundary with entry gap
entry_sector = 0
entry_angle_start = entry_sector * (2 * np.pi / sectors_per_ring[0])
entry_angle_end = (entry_sector + 1) * (2 * np.pi / sectors_per_ring[0])
theta = np.linspace(entry_angle_end, entry_angle_start + 2 * np.pi, 180)
x = center_x + outer_radius * np.cos(theta)
y = center_y + outer_radius * np.sin(theta)
fig.add_trace(go.Scatter(x=x, y=y, mode="lines", line={"color": wall_color, "width": wall_width + 1}, showlegend=False))

# Draw radial walls
for ring_idx in range(num_rings):
    radius_outer = (num_rings - ring_idx) * ring_width
    radius_inner = (num_rings - ring_idx - 1) * ring_width
    n_sectors = sectors_per_ring[ring_idx]
    sector_angle = 2 * np.pi / n_sectors

    for sector in range(n_sectors):
        if radial_walls[ring_idx][sector]:
            theta = (sector + 1) * sector_angle
            x = [center_x + radius_inner * np.cos(theta), center_x + radius_outer * np.cos(theta)]
            y = [center_y + radius_inner * np.sin(theta), center_y + radius_outer * np.sin(theta)]
            fig.add_trace(
                go.Scatter(x=x, y=y, mode="lines", line={"color": wall_color, "width": wall_width}, showlegend=False)
            )

# Draw center goal circle
goal_radius = 0.4
theta = np.linspace(0, 2 * np.pi, 50)
x_goal = center_x + goal_radius * np.cos(theta)
y_goal = center_y + goal_radius * np.sin(theta)
fig.add_trace(
    go.Scatter(
        x=x_goal, y=y_goal, fill="toself", fillcolor="#306998", line={"color": "#306998", "width": 2}, showlegend=False
    )
)

# Add center star marker
fig.add_trace(
    go.Scatter(
        x=[center_x],
        y=[center_y],
        mode="markers",
        marker={"symbol": "star", "size": 20, "color": "#FFD43B", "line": {"color": "#306998", "width": 2}},
        showlegend=False,
    )
)

# Add entry arrow and labels
entry_angle = (entry_sector + 0.5) * (2 * np.pi / sectors_per_ring[0])
arrow_x = center_x + (outer_radius + 0.8) * np.cos(entry_angle)
arrow_y = center_y + (outer_radius + 0.8) * np.sin(entry_angle)
fig.add_annotation(
    x=center_x + outer_radius * np.cos(entry_angle),
    y=center_y + outer_radius * np.sin(entry_angle),
    ax=arrow_x,
    ay=arrow_y,
    xref="x",
    yref="y",
    axref="x",
    ayref="y",
    showarrow=True,
    arrowhead=2,
    arrowsize=2,
    arrowwidth=3,
    arrowcolor="#306998",
)

fig.add_annotation(
    x=center_x + (outer_radius + 1.2) * np.cos(entry_angle),
    y=center_y + (outer_radius + 1.2) * np.sin(entry_angle),
    text="START",
    showarrow=False,
    font={"size": 22, "color": "#306998", "family": "Arial Black"},
)

fig.add_annotation(
    x=center_x,
    y=center_y - goal_radius - 0.8,
    text="GOAL",
    showarrow=False,
    font={"size": 22, "color": "#306998", "family": "Arial Black"},
)

# Update layout
fig.update_layout(
    title={
        "text": "maze-circular · plotly · pyplots.ai",
        "font": {"size": 28, "color": "black"},
        "x": 0.5,
        "xanchor": "center",
    },
    xaxis={
        "showgrid": False,
        "zeroline": False,
        "showticklabels": False,
        "scaleanchor": "y",
        "scaleratio": 1,
        "range": [-num_rings - 2, num_rings + 2],
    },
    yaxis={"showgrid": False, "zeroline": False, "showticklabels": False, "range": [-num_rings - 2, num_rings + 2]},
    plot_bgcolor="white",
    paper_bgcolor="white",
    showlegend=False,
    margin={"l": 50, "r": 50, "t": 100, "b": 50},
)

# Save as PNG and HTML
fig.write_image("plot.png", width=1200, height=1200, scale=3)
fig.write_html("plot.html", include_plotlyjs="cdn")
