""" anyplot.ai
line-3d-trajectory: 3D Line Plot for Trajectory Visualization
Library: altair 6.1.0 | Python 3.13.13
Quality: 89/100 | Updated: 2026-05-16
"""

import os

import altair as alt
import numpy as np
import pandas as pd


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Data - Lorenz attractor trajectory (chaotic system)
np.random.seed(42)

# Lorenz system parameters
sigma = 10.0
rho = 28.0
beta = 8.0 / 3.0

# Generate trajectory using Euler integration
n_points = 1500
dt = 0.01

x_traj = np.zeros(n_points)
y_traj = np.zeros(n_points)
z_traj = np.zeros(n_points)

# Initial conditions
x_traj[0], y_traj[0], z_traj[0] = 1.0, 1.0, 1.0

for i in range(1, n_points):
    x, y, z = x_traj[i - 1], y_traj[i - 1], z_traj[i - 1]
    x_traj[i] = x + sigma * (y - x) * dt
    y_traj[i] = y + (x * (rho - z) - y) * dt
    z_traj[i] = z + (x * y - beta * z) * dt

# 3D to 2D isometric projection (elevation=20°, azimuth=135° for good view of Lorenz wings)
elev_rad = np.radians(20)
azim_rad = np.radians(135)

# Rotation around z-axis (azimuth)
x_rot = x_traj * np.cos(azim_rad) - y_traj * np.sin(azim_rad)
y_rot = x_traj * np.sin(azim_rad) + y_traj * np.cos(azim_rad)

# Rotation around x-axis (elevation) and project to 2D
x_proj = x_rot
z_proj = y_rot * np.sin(elev_rad) + z_traj * np.cos(elev_rad)

# Create line segments dataframe for mark_rule (each row is a segment)
segments = []
for i in range(n_points - 1):
    segments.append(
        {
            "x": x_proj[i],
            "y": z_proj[i],
            "x2": x_proj[i + 1],
            "y2": z_proj[i + 1],
            "time": i,
            "x_orig": x_traj[i],
            "y_orig": y_traj[i],
            "z_orig": z_traj[i],
        }
    )

df_segments = pd.DataFrame(segments)

# Create trajectory using mark_rule for line segments with color gradient
trajectory = (
    alt.Chart(df_segments)
    .mark_rule(strokeWidth=2.5, strokeCap="round")
    .encode(
        x=alt.X("x:Q", axis=alt.Axis(title="X-Y Projection (Horizontal)", labelFontSize=18, titleFontSize=22)),
        y=alt.Y("y:Q", axis=alt.Axis(title="Z Projection (Vertical)", labelFontSize=18, titleFontSize=22)),
        x2="x2:Q",
        y2="y2:Q",
        color=alt.Color(
            "time:Q",
            scale=alt.Scale(scheme="viridis"),
            legend=alt.Legend(title="Time Step", titleFontSize=20, labelFontSize=16, orient="right"),
        ),
        tooltip=[
            alt.Tooltip("x_orig:Q", title="X", format=".2f"),
            alt.Tooltip("y_orig:Q", title="Y", format=".2f"),
            alt.Tooltip("z_orig:Q", title="Z", format=".2f"),
            alt.Tooltip("time:Q", title="Time Step"),
        ],
    )
)

# Add pan and zoom interactivity
pan_zoom = alt.selection_interval(bind="scales", encodings=["x", "y"])

# Final chart
chart = (
    trajectory.add_params(pan_zoom)
    .properties(
        width=1600,
        height=900,
        background=PAGE_BG,
        title=alt.Title(text="line-3d-trajectory · altair · anyplot.ai", fontSize=28, color=INK),
    )
    .configure_view(fill=PAGE_BG, stroke=INK_SOFT)
    .configure_axis(
        domainColor=INK_SOFT, tickColor=INK_SOFT, gridColor=INK, gridOpacity=0.10, labelColor=INK_SOFT, titleColor=INK
    )
    .configure_title(color=INK)
    .configure_legend(fillColor=ELEVATED_BG, strokeColor=INK_SOFT, labelColor=INK_SOFT, titleColor=INK)
)

# Save outputs
chart.save(f"plot-{THEME}.png", scale_factor=3.0)
chart.save(f"plot-{THEME}.html")
