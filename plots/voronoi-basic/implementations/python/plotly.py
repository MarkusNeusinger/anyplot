""" anyplot.ai
voronoi-basic: Voronoi Diagram for Spatial Partitioning
Library: plotly 6.7.0 | Python 3.13.13
Quality: 87/100 | Updated: 2026-05-17
"""

import os
import sys


# Remove current directory from path BEFORE importing plotly
cur_dir = os.path.dirname(os.path.abspath(__file__))
sys.path = [p for p in sys.path if os.path.abspath(p) != cur_dir]

import numpy as np  # noqa: E402
import plotly.graph_objects as go  # noqa: E402
from scipy.spatial import Voronoi  # noqa: E402


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
GRID = "rgba(26,26,23,0.10)" if THEME == "light" else "rgba(240,239,232,0.10)"

# Okabe-Ito palette (position 1 is brand color #009E73)
IMPRINT = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477"]

# Data - Generate seed points (retail stores) within city bounds
np.random.seed(42)
n_stores = 20
x = np.random.uniform(10, 90, n_stores)
y = np.random.uniform(10, 90, n_stores)
points = np.column_stack([x, y])

# Bounding box for city area
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

# Extended color palette (cycle through Okabe-Ito + supplementary colors)
extended_colors = IMPRINT + [
    "#FF9AA2",
    "#FFB7B2",
    "#E0BBE4",
    "#957DAD",
    "#D291BC",
    "#C9B1FF",
    "#A1C4FD",
    "#B5EAD7",
    "#C7CEEA",
    "#FFDAC1",
    "#E2F0CB",
]

# Create figure
fig = go.Figure()

# Draw Voronoi cells (service areas for retail stores)
for idx in range(n_stores):
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
                fillcolor=extended_colors[idx % len(extended_colors)],
                opacity=0.6,
                line={"color": INK_SOFT, "width": 2},
                mode="lines",
                hoverinfo="skip",
                showlegend=False,
            )
        )

# Draw seed points (store locations) on top
fig.add_trace(
    go.Scatter(
        x=x,
        y=y,
        mode="markers",
        marker={"size": 18, "color": IMPRINT[0], "line": {"color": ELEVATED_BG, "width": 3}, "symbol": "circle"},
        name="Store Location",
        hovertemplate="Store %{pointNumber}<br>Latitude: %{y:.1f}<br>Longitude: %{x:.1f}<extra></extra>",
    )
)

# Update layout with theme-adaptive colors
fig.update_layout(
    title={
        "text": "voronoi-basic · plotly · pyplots.ai",
        "font": {"size": 28, "color": INK},
        "x": 0.5,
        "xanchor": "center",
    },
    xaxis={
        "title": {"text": "Longitude (°)", "font": {"size": 22, "color": INK}},
        "tickfont": {"size": 18, "color": INK_SOFT},
        "range": [-5, 105],
        "showgrid": True,
        "gridwidth": 1,
        "gridcolor": GRID,
        "zeroline": False,
        "linecolor": INK_SOFT,
    },
    yaxis={
        "title": {"text": "Latitude (°)", "font": {"size": 22, "color": INK}},
        "tickfont": {"size": 18, "color": INK_SOFT},
        "range": [-5, 105],
        "showgrid": True,
        "gridwidth": 1,
        "gridcolor": GRID,
        "zeroline": False,
        "scaleanchor": "x",
        "scaleratio": 1,
        "linecolor": INK_SOFT,
    },
    paper_bgcolor=PAGE_BG,
    plot_bgcolor=PAGE_BG,
    font={"color": INK},
    showlegend=True,
    legend={
        "font": {"size": 16, "color": INK_SOFT},
        "x": 0.02,
        "y": 0.98,
        "bgcolor": ELEVATED_BG,
        "bordercolor": INK_SOFT,
        "borderwidth": 1,
    },
    margin={"l": 80, "r": 40, "t": 100, "b": 80},
)

# Save as PNG and HTML (square format for Voronoi diagram)
fig.write_image(f"plot-{THEME}.png", width=1200, height=1200, scale=3)
fig.write_html(f"plot-{THEME}.html", include_plotlyjs="cdn")
