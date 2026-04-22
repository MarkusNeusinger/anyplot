""" pyplots.ai
polar-scatter: Polar Scatter Plot
Library: altair 6.0.0 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-26
"""

import altair as alt
import numpy as np
import pandas as pd


# Data - Synthetic wind measurements with prevailing directions
np.random.seed(42)
n_points = 120

# Create realistic wind data with prevailing directions (NW and SE)
angles_nw = np.random.normal(315, 25, n_points // 3)  # NW winds
angles_se = np.random.normal(135, 30, n_points // 3)  # SE winds
angles_other = np.random.uniform(0, 360, n_points - 2 * (n_points // 3))  # Other directions
angles_deg = np.concatenate([angles_nw, angles_se, angles_other]) % 360

# Wind speeds (m/s) - higher speeds for prevailing directions
speeds = np.zeros(n_points)
speeds[: n_points // 3] = np.random.gamma(4, 2.5, n_points // 3)  # NW - stronger
speeds[n_points // 3 : 2 * n_points // 3] = np.random.gamma(3, 2, n_points // 3)  # SE - moderate
speeds[2 * n_points // 3 :] = np.random.gamma(2, 1.5, n_points - 2 * (n_points // 3))  # Other - weaker
speeds = np.clip(speeds, 1, 20)

# Time of day categories
time_of_day = np.array(
    ["Morning"] * (n_points // 3) + ["Afternoon"] * (n_points // 3) + ["Evening"] * (n_points - 2 * (n_points // 3))
)

# Convert polar to Cartesian for Altair (doesn't have native polar support)
angles_rad = np.deg2rad(angles_deg)
x = speeds * np.cos(angles_rad)
y = speeds * np.sin(angles_rad)

df = pd.DataFrame({"x": x, "y": y, "speed": speeds, "direction": angles_deg, "time_of_day": time_of_day})

# Create polar gridlines (circles)
max_radius = 20
radii = [5, 10, 15, 20]
circle_points = []
for r in radii:
    theta = np.linspace(0, 2 * np.pi, 100)
    for i, t in enumerate(theta):
        circle_points.append({"x": r * np.cos(t), "y": r * np.sin(t), "radius": r, "order": i})
circles_df = pd.DataFrame(circle_points)

# Create angular gridlines (spokes)
spoke_angles = [0, 45, 90, 135, 180, 225, 270, 315]
spoke_points = []
for angle in spoke_angles:
    rad = np.deg2rad(angle)
    spoke_points.append({"x": 0, "y": 0, "angle": angle, "group": angle, "order": 0})
    spoke_points.append(
        {"x": max_radius * np.cos(rad), "y": max_radius * np.sin(rad), "angle": angle, "group": angle, "order": 1}
    )
spokes_df = pd.DataFrame(spoke_points)

# Create angle labels
label_offset = max_radius * 1.12
angle_labels = []
direction_names = {
    0: "E (0°)",
    45: "NE (45°)",
    90: "N (90°)",
    135: "NW (135°)",
    180: "W (180°)",
    225: "SW (225°)",
    270: "S (270°)",
    315: "SE (315°)",
}
for angle, name in direction_names.items():
    rad = np.deg2rad(angle)
    angle_labels.append({"x": label_offset * np.cos(rad), "y": label_offset * np.sin(rad), "label": name})
labels_df = pd.DataFrame(angle_labels)

# Create radius labels
radius_labels = [{"x": r + 0.5, "y": 0.5, "label": f"{r} m/s"} for r in radii]
radius_labels_df = pd.DataFrame(radius_labels)

# Define colors (Python blue and yellow, plus a third colorblind-safe color)
color_scale = alt.Scale(domain=["Morning", "Afternoon", "Evening"], range=["#306998", "#FFD43B", "#E87D72"])

# Circular gridlines
grid_circles = (
    alt.Chart(circles_df)
    .mark_line(strokeWidth=1, opacity=0.3, color="#888888")
    .encode(x=alt.X("x:Q", axis=None), y=alt.Y("y:Q", axis=None), detail="radius:N", order="order:Q")
)

# Radial spokes
grid_spokes = (
    alt.Chart(spokes_df)
    .mark_line(strokeWidth=1, opacity=0.3, color="#888888")
    .encode(x=alt.X("x:Q", axis=None), y=alt.Y("y:Q", axis=None), detail="group:N", order="order:Q")
)

# Angle labels
angle_text = (
    alt.Chart(labels_df)
    .mark_text(fontSize=18, fontWeight="bold", color="#444444")
    .encode(x=alt.X("x:Q", axis=None), y=alt.Y("y:Q", axis=None), text="label:N")
)

# Radius labels
radius_text = (
    alt.Chart(radius_labels_df)
    .mark_text(fontSize=14, color="#666666", align="left")
    .encode(x=alt.X("x:Q", axis=None), y=alt.Y("y:Q", axis=None), text="label:N")
)

# Data points
points = (
    alt.Chart(df)
    .mark_point(size=200, filled=True, opacity=0.8)
    .encode(
        x=alt.X("x:Q", axis=None, scale=alt.Scale(domain=[-25, 25])),
        y=alt.Y("y:Q", axis=None, scale=alt.Scale(domain=[-25, 25])),
        color=alt.Color("time_of_day:N", scale=color_scale, title="Time of Day"),
        tooltip=[
            alt.Tooltip("direction:Q", title="Direction (°)", format=".1f"),
            alt.Tooltip("speed:Q", title="Speed (m/s)", format=".1f"),
            alt.Tooltip("time_of_day:N", title="Time"),
        ],
    )
)

# Combine all layers
chart = (
    alt.layer(grid_circles, grid_spokes, angle_text, radius_text, points)
    .properties(
        width=1200,
        height=1200,
        title=alt.Title("Wind Observations · polar-scatter · altair · pyplots.ai", fontSize=28, anchor="middle"),
    )
    .configure_view(strokeWidth=0)
    .configure_legend(titleFontSize=18, labelFontSize=16, symbolSize=200, orient="right")
)

# Save as PNG and HTML
chart.save("plot.png", scale_factor=3.0)
chart.save("plot.html")
