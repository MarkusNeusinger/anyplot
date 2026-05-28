""" anyplot.ai
radar-multi: Multi-Series Radar Chart
Library: altair 6.1.0 | Python 3.13.13
Quality: 86/100 | Updated: 2026-05-07
"""

import importlib.util
import os
import sys

import numpy as np
import pandas as pd


# Explicitly import altair from site-packages to avoid shadowing
spec = importlib.util.find_spec("altair")
if spec and spec.origin and "site-packages" in spec.origin:
    alt = importlib.util.module_from_spec(spec)
    sys.modules["altair"] = alt
    spec.loader.exec_module(alt)
else:
    # Fallback: remove the directory containing this script from path
    script_dir = os.path.dirname(os.path.abspath(__file__))
    sys.path[:] = [p for p in sys.path if os.path.abspath(p) != script_dir]
    import altair as alt


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Okabe-Ito palette (first series ALWAYS #009E73)
IMPRINT = ["#009E73", "#C475FD", "#4467A3"]

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
    for i, (cat, val, angle) in enumerate(zip(categories, values, angles, strict=True)):
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
for i, (cat, angle) in enumerate(zip(categories, angles, strict=True)):
    spoke_records.append({"category": cat, "x": 0, "y": 0, "order": 0, "spoke_id": i})
    spoke_records.append(
        {"category": cat, "x": 105 * np.cos(angle), "y": 105 * np.sin(angle), "order": 1, "spoke_id": i}
    )
spoke_df = pd.DataFrame(spoke_records)

# Create axis labels (positioned beyond the outer gridline)
label_records = []
for cat, angle in zip(categories, angles, strict=True):
    label_x = 125 * np.cos(angle)
    label_y = 125 * np.sin(angle)
    label_records.append({"category": cat, "x": label_x, "y": label_y})
label_df = pd.DataFrame(label_records)

# Create grid value labels on all spokes
value_label_records = []
for r in [20, 40, 60, 80, 100]:
    for angle in angles:
        x = r * np.cos(angle) + 8
        y = r * np.sin(angle) + 2
        value_label_records.append({"value": str(r), "x": x, "y": y})
value_label_df = pd.DataFrame(value_label_records)

# Series list and colors
series_list = ["Product A", "Product B", "Product C"]
color_scale = alt.Scale(domain=series_list, range=IMPRINT)

# Chart dimensions for square output (base size with 3x scale factor)
chart_width = 1600
chart_height = 1600

# Domain for axes
axis_domain = [-160, 160]

# Base encoding for x and y
x_enc = alt.X("x:Q", scale=alt.Scale(domain=axis_domain), axis=None)
y_enc = alt.Y("y:Q", scale=alt.Scale(domain=axis_domain), axis=None)

# Grid hexagons
grid_lines = (
    alt.Chart(grid_df)
    .mark_line(strokeWidth=1.5, opacity=0.15)
    .encode(x=x_enc, y=y_enc, detail="radius:N", order="order:Q", stroke=alt.value(INK_SOFT))
)

# Spokes (axis lines)
spokes = (
    alt.Chart(spoke_df)
    .mark_line(strokeWidth=1.5, opacity=0.25)
    .encode(x=x_enc, y=y_enc, detail="spoke_id:N", order="order:Q", stroke=alt.value(INK_SOFT))
)

# Axis labels
labels = (
    alt.Chart(label_df)
    .mark_text(fontSize=22, fontWeight="bold")
    .encode(x="x:Q", y="y:Q", text="category:N", color=alt.value(INK))
)

# Grid value labels
value_labels = (
    alt.Chart(value_label_df)
    .mark_text(fontSize=14, align="left", baseline="middle")
    .encode(x="x:Q", y="y:Q", text="value:N", color=alt.value(INK_SOFT))
)

# Create filled polygons for each series
fill_layers = []
for series_name, fill_color in zip(series_list, IMPRINT, strict=True):
    series_df = df[df["series"] == series_name].copy()

    # Use mark_area for proper polygon fill
    fill_layer = (
        alt.Chart(series_df)
        .mark_area(fillOpacity=0.25, opacity=0.25)
        .encode(x=x_enc, y=y_enc, color=alt.value(fill_color), order="order:Q")
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
                fillColor=ELEVATED_BG,
                strokeColor=INK_SOFT,
                labelColor=INK_SOFT,
                titleColor=INK,
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
        width=chart_width,
        height=chart_height,
        background=PAGE_BG,
        title=alt.Title("radar-multi · altair · pyplots.ai", fontSize=28, anchor="middle", offset=20),
    )
    .configure_view(strokeWidth=0, fill=PAGE_BG)
    .configure_legend(strokeColor=INK_SOFT, padding=15, labelColor=INK_SOFT, titleColor=INK)
)

# Save as PNG and HTML with theme suffix
chart.save(f"plot-{THEME}.png", scale_factor=3.0)
chart.save(f"plot-{THEME}.html")
