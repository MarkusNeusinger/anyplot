""" pyplots.ai
voronoi-basic: Voronoi Diagram for Spatial Partitioning
Library: altair 6.0.0 | Python 3.13.11
Quality: 90/100 | Created: 2026-01-09
"""

import altair as alt
import numpy as np
import pandas as pd
from scipy.spatial import Voronoi


# Data - Generate seed points for weather stations
np.random.seed(42)
n_points = 15
x_points = np.random.uniform(5, 95, n_points)
y_points = np.random.uniform(5, 95, n_points)
labels = [f"Station {i + 1}" for i in range(n_points)]

points = np.column_stack([x_points, y_points])

# Add boundary points to help with clipping (mirror points outside bounds)
x_min, x_max = 0, 100
y_min, y_max = 0, 100
margin = 200

boundary_points = []
for px, py in points:
    boundary_points.append([2 * x_min - margin - px, py])
    boundary_points.append([2 * x_max + margin - px, py])
    boundary_points.append([px, 2 * y_min - margin - py])
    boundary_points.append([px, 2 * y_max + margin - py])

all_points = np.vstack([points, boundary_points])

# Compute Voronoi diagram
vor = Voronoi(all_points)

# Color palette - colorblind safe with variety
color_palette = [
    "#306998",
    "#FFD43B",
    "#4B8BBE",
    "#FFE873",
    "#6A9BC3",
    "#3776AB",
    "#FFC61E",
    "#5A8AB5",
    "#E6C430",
    "#2E5984",
    "#FFCC00",
    "#4A7A9E",
    "#D4AA00",
    "#1E3F5A",
    "#FFB800",
]

# Create filled polygon data for Voronoi cells using line marks with path
polygon_data = []
for point_idx in range(n_points):
    region_idx = vor.point_region[point_idx]
    region = vor.regions[region_idx]

    if not region or -1 in region:
        continue

    vertices = vor.vertices[region]
    clipped_x = np.clip(vertices[:, 0], x_min, x_max)
    clipped_y = np.clip(vertices[:, 1], y_min, y_max)

    # Sort vertices by angle for proper polygon ordering
    center_x = np.mean(clipped_x)
    center_y = np.mean(clipped_y)
    angles = np.arctan2(clipped_y - center_y, clipped_x - center_x)
    sorted_indices = np.argsort(angles)

    sorted_x = clipped_x[sorted_indices]
    sorted_y = clipped_y[sorted_indices]

    color = color_palette[point_idx % len(color_palette)]
    station = labels[point_idx]

    # Add vertices for filled polygon with order index, close the polygon
    for i, (vx, vy) in enumerate(zip(sorted_x, sorted_y, strict=True)):
        polygon_data.append({"x": vx, "y": vy, "order": i, "cell_id": point_idx, "station": station, "color": color})
    # Close polygon by repeating first vertex
    polygon_data.append(
        {
            "x": sorted_x[0],
            "y": sorted_y[0],
            "order": len(sorted_x),
            "cell_id": point_idx,
            "station": station,
            "color": color,
        }
    )

df_polygons = pd.DataFrame(polygon_data)

# Create DataFrame for seed points
df_points = pd.DataFrame(
    {
        "x": x_points,
        "y": y_points,
        "label": labels,
        "station": labels,
        "color": [color_palette[i % len(color_palette)] for i in range(n_points)],
    }
)

# Create filled Voronoi regions using mark_line with filled attribute
voronoi_cells = (
    alt.Chart(df_polygons)
    .mark_line(filled=True, opacity=0.55, strokeWidth=2.5, stroke="#333333")
    .encode(
        x=alt.X("x:Q", scale=alt.Scale(domain=[x_min - 2, x_max + 2]), title="X Coordinate"),
        y=alt.Y("y:Q", scale=alt.Scale(domain=[y_min - 2, y_max + 2]), title="Y Coordinate"),
        color=alt.Color(
            "station:N",
            scale=alt.Scale(domain=labels, range=color_palette[:n_points]),
            legend=alt.Legend(
                title="Weather Stations",
                titleFontSize=16,
                labelFontSize=12,
                columns=2,
                orient="right",
                symbolType="square",
                symbolSize=150,
            ),
        ),
        order="order:O",
        detail="cell_id:N",
    )
)

# Create seed points layer
points_layer = (
    alt.Chart(df_points)
    .mark_circle(size=400, stroke="#FFFFFF", strokeWidth=3, color="#1a1a1a")
    .encode(
        x="x:Q",
        y="y:Q",
        tooltip=[
            alt.Tooltip("label:N", title="Station"),
            alt.Tooltip("x:Q", format=".1f", title="X"),
            alt.Tooltip("y:Q", format=".1f", title="Y"),
        ],
    )
)

# Add station labels
labels_layer = (
    alt.Chart(df_points)
    .mark_text(dy=-22, fontSize=14, fontWeight="bold", color="#1a1a1a")
    .encode(x="x:Q", y="y:Q", text="label:N")
)

# Combine layers
chart = (
    (voronoi_cells + points_layer + labels_layer)
    .properties(
        width=1400, height=900, title=alt.Title("voronoi-basic · altair · pyplots.ai", fontSize=28, anchor="middle")
    )
    .configure_axis(labelFontSize=18, titleFontSize=22, grid=True, gridOpacity=0.25, gridColor="#AAAAAA")
    .configure_view(strokeWidth=0)
)

# Save output
chart.save("plot.png", scale_factor=3.0)
