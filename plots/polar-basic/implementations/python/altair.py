""" pyplots.ai
polar-basic: Basic Polar Chart
Library: altair 6.0.0 | Python 3.13.11
Quality: 92/100 | Created: 2025-12-23
"""

import altair as alt
import numpy as np
import pandas as pd


# Data - Hourly temperature pattern (24-hour cycle)
np.random.seed(42)
hours = np.arange(24)

# Temperature pattern: warmer during day, cooler at night
base_temp = 15 + 10 * np.sin((hours - 6) * np.pi / 12)  # Peak around 3 PM
temperatures = base_temp + np.random.randn(24) * 1.5

# Convert polar coordinates to cartesian
# theta: 0 hours = top (90 degrees), clockwise direction
theta = (90 - hours * 15) * np.pi / 180  # 15 degrees per hour

# Normalize radius to positive values with good spacing
radius = temperatures - temperatures.min() + 5

# Convert to x, y
x = radius * np.cos(theta)
y = radius * np.sin(theta)

df = pd.DataFrame({"hour": hours, "temperature": temperatures, "x": x, "y": y})

# Create radial gridlines (concentric circles)
max_radius = radius.max() + 2
grid_radii = np.linspace(5, max_radius, 5)
circle_angles = np.linspace(0, 2 * np.pi, 101)

grid_rows = []
for i, r in enumerate(grid_radii):
    for j, angle in enumerate(circle_angles):
        grid_rows.append({"x": r * np.cos(angle), "y": r * np.sin(angle), "circle_id": i, "order": j})

grid_df = pd.DataFrame(grid_rows)

# Create angular gridlines (spokes at major hours)
spoke_data = []
major_hours = [0, 3, 6, 9, 12, 15, 18, 21]
for hour in major_hours:
    angle = (90 - hour * 15) * np.pi / 180
    spoke_data.append({"x": 0, "y": 0, "xend": max_radius * np.cos(angle), "yend": max_radius * np.sin(angle)})

spoke_df = pd.DataFrame(spoke_data)

# Create hour labels
label_data = []
hour_labels_map = {0: "00:00", 3: "03:00", 6: "06:00", 9: "09:00", 12: "12:00", 15: "15:00", 18: "18:00", 21: "21:00"}
for hour, label in hour_labels_map.items():
    angle = (90 - hour * 15) * np.pi / 180
    label_radius = max_radius + 4
    label_data.append({"label": label, "x": label_radius * np.cos(angle), "y": label_radius * np.sin(angle)})

label_df = pd.DataFrame(label_data)

# Create path data (close the loop)
df_sorted = df.sort_values("hour").copy()
df_sorted["order"] = df_sorted["hour"]
first_row = df_sorted.iloc[[0]].copy()
first_row["order"] = 24
df_path = pd.concat([df_sorted, first_row], ignore_index=True)

# Radial gridlines (circles)
circles = (
    alt.Chart(grid_df)
    .mark_line(strokeWidth=1.5, opacity=0.3, color="#888888", strokeDash=[4, 4])
    .encode(x=alt.X("x:Q", axis=None), y=alt.Y("y:Q", axis=None), detail="circle_id:N", order="order:O")
)

# Angular gridlines (spokes) using rule marks
spokes = (
    alt.Chart(spoke_df)
    .mark_rule(strokeWidth=1.5, opacity=0.4, color="#888888")
    .encode(x="x:Q", y="y:Q", x2="xend:Q", y2="yend:Q")
)

# Hour labels
labels = (
    alt.Chart(label_df)
    .mark_text(fontSize=22, fontWeight="bold", color="#333333")
    .encode(x="x:Q", y="y:Q", text="label:N")
)

# Data line connecting all points
line = (
    alt.Chart(df_path).mark_line(strokeWidth=4, color="#FFD43B", opacity=0.9).encode(x="x:Q", y="y:Q", order="order:O")
)

# Data points
points = (
    alt.Chart(df)
    .mark_point(filled=True, size=500, color="#306998", opacity=0.9)
    .encode(
        x="x:Q",
        y="y:Q",
        tooltip=[
            alt.Tooltip("hour:O", title="Hour"),
            alt.Tooltip("temperature:Q", title="Temperature (°C)", format=".1f"),
        ],
    )
)

# Combine all layers with square format for polar chart
chart = (
    alt.layer(circles, spokes, line, points, labels)
    .properties(
        width=1200,
        height=1200,
        title=alt.Title(text="Hourly Temperature · polar-basic · altair · pyplots.ai", fontSize=30, anchor="middle"),
    )
    .configure_view(strokeWidth=0)
)

# Save (1200 * 3 = 3600 for square format)
chart.save("plot.png", scale_factor=3.0)
chart.save("plot.html")
