""" pyplots.ai
voronoi-basic: Voronoi Diagram for Spatial Partitioning
Library: plotly 6.5.1 | Python 3.13.11
Quality: 92/100 | Created: 2026-01-09
"""

import numpy as np
import plotly.graph_objects as go
from scipy.spatial import Voronoi


# Data - Generate seed points for Voronoi diagram
np.random.seed(42)
n_points = 20
x = np.random.uniform(10, 90, n_points)
y = np.random.uniform(10, 90, n_points)
points = np.column_stack([x, y])

# Bounding box for clipping
x_min, x_max = 0, 100
y_min, y_max = 0, 100

# Add far-away boundary points to ensure finite regions within bounding box
boundary_offset = 200
boundary_points = np.array(
    [
        [x_min - boundary_offset, y_min - boundary_offset],
        [x_max + boundary_offset, y_min - boundary_offset],
        [x_min - boundary_offset, y_max + boundary_offset],
        [x_max + boundary_offset, y_max + boundary_offset],
        [(x_min + x_max) / 2, y_min - boundary_offset],
        [(x_min + x_max) / 2, y_max + boundary_offset],
        [x_min - boundary_offset, (y_min + y_max) / 2],
        [x_max + boundary_offset, (y_min + y_max) / 2],
    ]
)
all_points = np.vstack([points, boundary_points])

# Compute Voronoi diagram
vor = Voronoi(all_points)

# Colors for regions (colorblind-safe palette starting with Python Blue and Yellow)
colors = [
    "#306998",
    "#FFD43B",
    "#4ECDC4",
    "#FF6B6B",
    "#95E1D3",
    "#F38181",
    "#AA96DA",
    "#FCBAD3",
    "#A8D8EA",
    "#B5EAD7",
    "#C7CEEA",
    "#FFDAC1",
    "#E2F0CB",
    "#FF9AA2",
    "#FFB7B2",
    "#E0BBE4",
    "#957DAD",
    "#D291BC",
    "#C9B1FF",
    "#A1C4FD",
]

# Create figure
fig = go.Figure()

# Draw Voronoi cells (only for original points, not boundary points)
for idx in range(n_points):
    region_idx = vor.point_region[idx]
    region = vor.regions[region_idx]

    if not region or -1 in region:
        continue

    vertices = [list(vor.vertices[v]) for v in region]

    # Clip polygon to bounding box using Sutherland-Hodgman algorithm
    polygon = vertices
    for edge, bounds in [("left", x_min), ("right", x_max), ("bottom", y_min), ("top", y_max)]:
        if len(polygon) == 0:
            break
        clipped = []
        for i in range(len(polygon)):
            curr = polygon[i]
            next_v = polygon[(i + 1) % len(polygon)]

            # Check if points are inside edge
            if edge == "left":
                curr_in, next_in = curr[0] >= bounds, next_v[0] >= bounds
            elif edge == "right":
                curr_in, next_in = curr[0] <= bounds, next_v[0] <= bounds
            elif edge == "bottom":
                curr_in, next_in = curr[1] >= bounds, next_v[1] >= bounds
            else:  # top
                curr_in, next_in = curr[1] <= bounds, next_v[1] <= bounds

            # Compute intersection if needed
            if curr_in != next_in:
                dx, dy = next_v[0] - curr[0], next_v[1] - curr[1]
                if edge in ("left", "right"):
                    t = (bounds - curr[0]) / dx if dx != 0 else 0
                    intersect = [bounds, curr[1] + t * dy]
                else:
                    t = (bounds - curr[1]) / dy if dy != 0 else 0
                    intersect = [curr[0] + t * dx, bounds]

            if curr_in:
                clipped.append(curr)
                if not next_in:
                    clipped.append(intersect)
            elif next_in:
                clipped.append(intersect)

        polygon = clipped

    if len(polygon) >= 3:
        polygon_x = [p[0] for p in polygon] + [polygon[0][0]]
        polygon_y = [p[1] for p in polygon] + [polygon[0][1]]

        fig.add_trace(
            go.Scatter(
                x=polygon_x,
                y=polygon_y,
                fill="toself",
                fillcolor=colors[idx % len(colors)],
                opacity=0.6,
                line={"color": "#333333", "width": 2},
                mode="lines",
                hoverinfo="skip",
                showlegend=False,
            )
        )

# Draw seed points on top
fig.add_trace(
    go.Scatter(
        x=x,
        y=y,
        mode="markers",
        marker={"size": 18, "color": "#306998", "line": {"color": "white", "width": 3}, "symbol": "circle"},
        name="Seed Points",
        hovertemplate="Point %{pointNumber}<br>X: %{x:.1f}<br>Y: %{y:.1f}<extra></extra>",
    )
)

# Update layout
fig.update_layout(
    title={
        "text": "voronoi-basic · plotly · pyplots.ai",
        "font": {"size": 32, "color": "#333333"},
        "x": 0.5,
        "xanchor": "center",
    },
    xaxis={
        "title": {"text": "X Coordinate", "font": {"size": 24}},
        "tickfont": {"size": 18},
        "range": [-5, 105],
        "showgrid": True,
        "gridwidth": 1,
        "gridcolor": "rgba(0,0,0,0.1)",
        "zeroline": False,
    },
    yaxis={
        "title": {"text": "Y Coordinate", "font": {"size": 24}},
        "tickfont": {"size": 18},
        "range": [-5, 105],
        "showgrid": True,
        "gridwidth": 1,
        "gridcolor": "rgba(0,0,0,0.1)",
        "zeroline": False,
        "scaleanchor": "x",
        "scaleratio": 1,
    },
    template="plotly_white",
    showlegend=True,
    legend={"font": {"size": 18}, "x": 0.02, "y": 0.98, "bgcolor": "rgba(255,255,255,0.8)"},
    margin={"l": 80, "r": 40, "t": 100, "b": 80},
    plot_bgcolor="white",
)

# Save as PNG and HTML (square format for Voronoi diagram)
fig.write_image("plot.png", width=1200, height=1200, scale=3)
fig.write_html("plot.html", include_plotlyjs=True, full_html=True)
