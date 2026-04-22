""" pyplots.ai
radar-multi: Multi-Series Radar Chart
Library: altair 6.0.0 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-25
"""

import altair as alt
import numpy as np
import pandas as pd


# Data: Product comparison across key attributes
categories = ["Price", "Quality", "Durability", "Support", "Features", "Design"]
n_categories = len(categories)

data = {
    "Product A": [85, 70, 90, 65, 80, 75],
    "Product B": [60, 85, 75, 90, 70, 80],
    "Product C": [75, 65, 80, 70, 95, 85],
}

# Calculate angles for each axis (in radians) - start from top
angles = [np.pi / 2 - i * 2 * np.pi / n_categories for i in range(n_categories)]

# Build records for each series
records = []
for series_name, values in data.items():
    for i, (cat, val, angle) in enumerate(zip(categories, values, angles)):
        # Convert polar to cartesian for plotting
        x = val * np.cos(angle)
        y = val * np.sin(angle)
        records.append(
            {"series": series_name, "category": cat, "value": val, "angle": angle, "x": x, "y": y, "order": i}
        )
    # Close the polygon by adding the first point again
    first_val = values[0]
    first_angle = angles[0]
    records.append(
        {
            "series": series_name,
            "category": categories[0],
            "value": first_val,
            "angle": first_angle,
            "x": first_val * np.cos(first_angle),
            "y": first_val * np.sin(first_angle),
            "order": n_categories,
        }
    )

df = pd.DataFrame(records)

# Create gridlines (hexagonal matching the axes)
grid_records = []
for r in [20, 40, 60, 80, 100]:
    for i, angle in enumerate(angles):
        grid_records.append({"radius": r, "x": r * np.cos(angle), "y": r * np.sin(angle), "order": i})
    # Close the hexagon
    grid_records.append({"radius": r, "x": r * np.cos(angles[0]), "y": r * np.sin(angles[0]), "order": n_categories})
grid_df = pd.DataFrame(grid_records)

# Create axis lines (spokes from center to edge)
spoke_records = []
for i, (cat, angle) in enumerate(zip(categories, angles)):
    spoke_records.append({"category": cat, "x": 0, "y": 0, "order": 0, "spoke_id": i})
    spoke_records.append(
        {"category": cat, "x": 105 * np.cos(angle), "y": 105 * np.sin(angle), "order": 1, "spoke_id": i}
    )
spoke_df = pd.DataFrame(spoke_records)

# Create axis labels (positioned beyond the outer gridline)
label_records = []
for cat, angle in zip(categories, angles):
    label_x = 125 * np.cos(angle)
    label_y = 125 * np.sin(angle)
    label_records.append({"category": cat, "x": label_x, "y": label_y})
label_df = pd.DataFrame(label_records)

# Colors for each series (Python Blue, Python Yellow, third color)
series_list = ["Product A", "Product B", "Product C"]
fill_colors = ["#306998", "#FFD43B", "#4CAF50"]

color_scale = alt.Scale(domain=series_list, range=fill_colors)

# Chart dimensions for square output
chart_size = 1200

# Domain for axes
axis_domain = [-160, 160]

# Base encoding for x and y
x_enc = alt.X("x:Q", scale=alt.Scale(domain=axis_domain), axis=None)
y_enc = alt.Y("y:Q", scale=alt.Scale(domain=axis_domain), axis=None)

# Grid hexagons
grid_lines = (
    alt.Chart(grid_df)
    .mark_line(strokeWidth=1.5, stroke="#bbbbbb", opacity=0.6)
    .encode(x=x_enc, y=y_enc, detail="radius:N", order="order:Q")
)

# Spokes (axis lines)
spokes = (
    alt.Chart(spoke_df)
    .mark_line(strokeWidth=1.5, stroke="#999999", opacity=0.7)
    .encode(x=x_enc, y=y_enc, detail="spoke_id:N", order="order:Q")
)

# Axis labels
labels = (
    alt.Chart(label_df)
    .mark_text(fontSize=22, fontWeight="bold", color="#333333")
    .encode(x="x:Q", y="y:Q", text="category:N")
)

# Grid value labels (at each gridline level on top spoke)
value_label_records = []
for r in [20, 40, 60, 80, 100]:
    value_label_records.append({"value": str(r), "x": 6, "y": r + 2})
value_label_df = pd.DataFrame(value_label_records)

value_labels = (
    alt.Chart(value_label_df)
    .mark_text(fontSize=14, color="#666666", align="left", baseline="middle")
    .encode(x="x:Q", y="y:Q", text="value:N")
)

# Create filled polygons for each series using mark_trail for better polygon fill
fill_layers = []
for series_name, fill_color in zip(series_list, fill_colors):
    series_df = df[df["series"] == series_name].copy()

    # Use mark_area with proper encoding for polygon fill
    fill_layer = (
        alt.Chart(series_df)
        .mark_line(strokeWidth=0, filled=True, fill=fill_color, fillOpacity=0.2)
        .encode(x=x_enc, y=y_enc, order="order:Q")
    )
    fill_layers.append(fill_layer)

# Polygon outlines
polygon_outline = (
    alt.Chart(df)
    .mark_line(strokeWidth=3, opacity=0.9)
    .encode(
        x=x_enc,
        y=y_enc,
        color=alt.Color(
            "series:N",
            scale=color_scale,
            legend=alt.Legend(
                title="Series",
                titleFontSize=20,
                labelFontSize=18,
                orient="right",
                offset=10,
                symbolSize=300,
                symbolStrokeWidth=3,
            ),
        ),
        detail="series:N",
        order="order:Q",
    )
)

# Data points (exclude the closing point)
points_df = df[df["order"] < n_categories].copy()
points = (
    alt.Chart(points_df)
    .mark_circle(size=200, opacity=0.9)
    .encode(
        x=x_enc,
        y=y_enc,
        color=alt.Color("series:N", scale=color_scale, legend=None),
        tooltip=["series:N", "category:N", "value:Q"],
    )
)

# Combine all layers
all_layers = [grid_lines, spokes] + fill_layers + [polygon_outline, points, labels, value_labels]

chart = (
    alt.layer(*all_layers)
    .properties(
        width=chart_size,
        height=chart_size,
        title=alt.Title("radar-multi · altair · pyplots.ai", fontSize=28, anchor="middle", offset=20),
    )
    .configure_view(strokeWidth=0)
    .configure_legend(strokeColor="#cccccc", padding=15)
)

# Save as PNG and HTML
chart.save("plot.png", scale_factor=3.0)
chart.save("plot.html")
