""" pyplots.ai
line-3d-trajectory: 3D Line Plot for Trajectory Visualization
Library: altair 6.0.0 | Python 3.13.11
Quality: 91/100 | Created: 2026-01-07
"""

import altair as alt
import numpy as np
import pandas as pd


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
        title=alt.Title(
            text="Lorenz Attractor · line-3d-trajectory · altair · pyplots.ai",
            subtitle="Isometric projection of chaotic trajectory (σ=10, ρ=28, β=8/3)",
            fontSize=28,
            subtitleFontSize=18,
            subtitleColor="#666666",
        ),
    )
    .configure_axis(grid=True, gridOpacity=0.3, gridDash=[6, 4])
    .configure_view(strokeWidth=0)
)

# Save outputs
chart.save("plot.png", scale_factor=3.0)
chart.save("plot.html")
