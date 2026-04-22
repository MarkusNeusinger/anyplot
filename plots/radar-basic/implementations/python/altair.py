""" pyplots.ai
radar-basic: Basic Radar Chart
Library: altair 6.0.0 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-23
"""

import altair as alt
import numpy as np
import pandas as pd


# Data - Employee performance review scores across competencies
categories = ["Communication", "Technical Skills", "Teamwork", "Problem Solving", "Leadership", "Creativity"]
values = [85, 90, 75, 88, 70, 82]

# Number of variables
n = len(categories)

# Create angles for each axis (evenly spaced around circle)
angles = np.linspace(0, 2 * np.pi, n, endpoint=False).tolist()

# Convert polar to cartesian coordinates
max_val = 100
values_scaled = [v / max_val for v in values]

# Data points coordinates
x_coords = [v * np.cos(a - np.pi / 2) for v, a in zip(values_scaled, angles, strict=True)]
y_coords = [v * np.sin(a - np.pi / 2) for v, a in zip(values_scaled, angles, strict=True)]

# Close the polygon for the line
angles_closed = angles + [angles[0]]
values_scaled_closed = values_scaled + [values_scaled[0]]
x_coords_closed = [v * np.cos(a - np.pi / 2) for v, a in zip(values_scaled_closed, angles_closed, strict=True)]
y_coords_closed = [v * np.sin(a - np.pi / 2) for v, a in zip(values_scaled_closed, angles_closed, strict=True)]

# DataFrame for data points (without closing point)
df_points = pd.DataFrame(
    {"x": x_coords, "y": y_coords, "category": categories, "value": values, "order": range(len(x_coords))}
)

# Create gridlines at 20, 40, 60, 80, 100 as hexagons (matching the 6 axes)
grid_levels = [20, 40, 60, 80, 100]
grid_data = []
for level in grid_levels:
    level_scaled = level / max_val
    for i, angle in enumerate(angles):
        grid_data.append(
            {
                "x": level_scaled * np.cos(angle - np.pi / 2),
                "y": level_scaled * np.sin(angle - np.pi / 2),
                "level": level,
                "order": i,
            }
        )
    # Close the grid polygon
    grid_data.append(
        {
            "x": level_scaled * np.cos(angles[0] - np.pi / 2),
            "y": level_scaled * np.sin(angles[0] - np.pi / 2),
            "level": level,
            "order": n,
        }
    )

df_grid = pd.DataFrame(grid_data)

# Create axis lines (spokes from center to edge)
spokes_data = []
for cat, angle in zip(categories, angles, strict=True):
    spokes_data.append({"x": 0, "y": 0, "category": cat, "order": 0})
    spokes_data.append({"x": np.cos(angle - np.pi / 2), "y": np.sin(angle - np.pi / 2), "category": cat, "order": 1})

df_spokes = pd.DataFrame(spokes_data)

# Create axis labels positioned outside the chart
label_data = []
label_offset = 1.18
for cat, angle in zip(categories, angles, strict=True):
    label_data.append(
        {"x": label_offset * np.cos(angle - np.pi / 2), "y": label_offset * np.sin(angle - np.pi / 2), "label": cat}
    )

df_labels = pd.DataFrame(label_data)

# Create value labels at each point
value_label_data = []
for val, angle in zip(values, angles, strict=True):
    val_scaled = val / max_val
    # Position value labels slightly outside the data points
    offset = 0.10
    value_label_data.append(
        {
            "x": (val_scaled + offset) * np.cos(angle - np.pi / 2),
            "y": (val_scaled + offset) * np.sin(angle - np.pi / 2),
            "value": str(val),
        }
    )

df_value_labels = pd.DataFrame(value_label_data)

# Grid polygons (hexagons)
grid_lines = (
    alt.Chart(df_grid)
    .mark_line(strokeWidth=1, opacity=0.3, color="#888888")
    .encode(x=alt.X("x:Q", axis=None), y=alt.Y("y:Q", axis=None), detail="level:N", order="order:O")
)

# Spokes (axis lines from center)
spokes = (
    alt.Chart(df_spokes)
    .mark_line(strokeWidth=1, opacity=0.4, color="#888888")
    .encode(x=alt.X("x:Q", axis=None), y=alt.Y("y:Q", axis=None), detail="category:N", order="order:O")
)

# Create GeoJSON polygon for fill
polygon_coords = [[x, y] for x, y in zip(x_coords_closed, y_coords_closed, strict=True)]
geojson_data = {"type": "Feature", "geometry": {"type": "Polygon", "coordinates": [polygon_coords]}, "properties": {}}

# Filled polygon using geoshape
polygon_fill = (
    alt.Chart(alt.Data(values=[geojson_data]))
    .mark_geoshape(fill="#306998", fillOpacity=0.25, stroke="#306998", strokeWidth=4)
    .project(type="identity", reflectY=True)
)

# Data points
points = (
    alt.Chart(df_points)
    .mark_point(filled=True, size=500, color="#306998", opacity=1.0)
    .encode(
        x=alt.X("x:Q"),
        y=alt.Y("y:Q"),
        tooltip=[alt.Tooltip("category:N", title="Competency"), alt.Tooltip("value:Q", title="Score")],
    )
)

# Axis labels
labels = (
    alt.Chart(df_labels)
    .mark_text(fontSize=22, fontWeight="bold", color="#333333")
    .encode(x=alt.X("x:Q"), y=alt.Y("y:Q"), text="label:N")
)

# Value labels
value_labels = (
    alt.Chart(df_value_labels)
    .mark_text(fontSize=18, fontWeight="bold", color="#306998")
    .encode(x=alt.X("x:Q"), y=alt.Y("y:Q"), text="value:N")
)

# Combine all layers
chart = (
    alt.layer(grid_lines, spokes, polygon_fill, points, labels, value_labels)
    .properties(width=1400, height=1200, title=alt.Title(text="radar-basic · altair · pyplots.ai", fontSize=28))
    .configure_view(strokeWidth=0)
)

# Save
chart.save("plot.png", scale_factor=3.0)
chart.save("plot.html")
