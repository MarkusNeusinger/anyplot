""" anyplot.ai
voronoi-basic: Voronoi Diagram for Spatial Partitioning
Library: altair 6.1.0 | Python 3.13.13
Quality: 89/100 | Updated: 2026-05-17
"""

import os
import sys


# Remove current directory from path to avoid shadowing altair library
_current_dir = os.path.dirname(os.path.abspath(__file__))
_sys_path_backup = sys.path.copy()
sys.path = [p for p in sys.path if os.path.abspath(p) != _current_dir]

try:
    import altair as alt
finally:
    sys.path = _sys_path_backup

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from scipy.spatial import Voronoi  # noqa: E402


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Okabe-Ito palette
IMPRINT = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477"]

# Data - Generate seed points for weather stations
np.random.seed(42)
n_points = 15
x_points = np.random.uniform(5, 95, n_points)
y_points = np.random.uniform(5, 95, n_points)
labels = [f"Station {i + 1}" for i in range(n_points)]

points = np.column_stack([x_points, y_points])

# Add boundary points to help with clipping
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

# Create filled polygon data for Voronoi cells
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

    color = IMPRINT[point_idx % len(IMPRINT)]
    station = labels[point_idx]

    # Add vertices for filled polygon
    for i in range(len(sorted_x)):
        polygon_data.append(
            {"x": sorted_x[i], "y": sorted_y[i], "order": i, "cell_id": point_idx, "station": station, "color": color}
        )
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
        "color": [IMPRINT[i % len(IMPRINT)] for i in range(n_points)],
    }
)

# Create filled Voronoi regions
voronoi_cells = (
    alt.Chart(df_polygons)
    .mark_line(filled=True, opacity=0.50, strokeWidth=2.5)
    .encode(
        x=alt.X("x:Q", scale=alt.Scale(domain=[x_min - 2, x_max + 2]), title="X Coordinate"),
        y=alt.Y("y:Q", scale=alt.Scale(domain=[y_min - 2, y_max + 2]), title="Y Coordinate"),
        color=alt.Color(
            "station:N",
            scale=alt.Scale(domain=labels, range=IMPRINT[:n_points]),
            legend=alt.Legend(
                title="Weather Stations",
                titleFontSize=16,
                labelFontSize=14,
                columns=2,
                orient="right",
                symbolType="square",
                symbolSize=150,
            ),
        ),
        order="order:O",
        detail="cell_id:N",
        stroke=alt.value(INK_SOFT),
    )
)

# Create seed points layer
points_layer = (
    alt.Chart(df_points)
    .mark_circle(size=300, stroke=PAGE_BG, strokeWidth=3)
    .encode(
        x="x:Q",
        y="y:Q",
        color=alt.Color("station:N", scale=alt.Scale(domain=labels, range=IMPRINT[:n_points]), legend=None),
        tooltip=[
            alt.Tooltip("label:N", title="Station"),
            alt.Tooltip("x:Q", format=".1f", title="X"),
            alt.Tooltip("y:Q", format=".1f", title="Y"),
        ],
    )
)

# Add station labels with adjusted positioning to reduce overlap
labels_layer = (
    alt.Chart(df_points)
    .mark_text(dy=-18, fontSize=13, fontWeight="bold")
    .encode(x="x:Q", y="y:Q", text="label:N", color=alt.value(INK))
)

# Combine layers
chart = (
    (voronoi_cells + points_layer + labels_layer)
    .properties(
        width=1600,
        height=900,
        background=PAGE_BG,
        title=alt.Title("voronoi-basic · altair · anyplot.ai", fontSize=28, anchor="middle"),
    )
    .configure_view(fill=PAGE_BG, stroke=INK_SOFT)
    .configure_axis(
        domainColor=INK_SOFT,
        tickColor=INK_SOFT,
        gridColor=INK,
        gridOpacity=0.10,
        labelColor=INK_SOFT,
        titleColor=INK,
        labelFontSize=18,
        titleFontSize=22,
    )
    .configure_title(color=INK)
    .configure_legend(
        fillColor=ELEVATED_BG, strokeColor=INK_SOFT, labelColor=INK_SOFT, titleColor=INK, labelFontSize=14
    )
)

# Save output
chart.save(f"plot-{THEME}.png", scale_factor=3.0)
chart.save(f"plot-{THEME}.html")
