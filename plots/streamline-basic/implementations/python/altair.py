""" pyplots.ai
streamline-basic: Basic Streamline Plot
Library: altair 6.0.0 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-31
"""

import altair as alt
import numpy as np
import pandas as pd


# Disable data row limit
alt.data_transformers.disable_max_rows()

# Data - Create a vector field for a vortex flow (u = -y, v = x)
np.random.seed(42)

# Generate streamlines using Euler integration - flat KISS structure
streamlines_data = []
streamline_id = 0

# Starting points at different radii for vortex visualization
radii = [0.4, 0.7, 1.0, 1.4, 1.8, 2.2, 2.6, 3.0]
n_per_radius = 6
dt = 0.03
max_steps = 250

for r in radii:
    for i in range(n_per_radius):
        angle = 2 * np.pi * i / n_per_radius + (r * 0.1)
        x = r * np.cos(angle)
        y = r * np.sin(angle)
        points = [(x, y)]

        # Trace streamline using Euler integration
        for _ in range(max_steps):
            # Vector field: circular vortex (u = -y, v = x)
            u = -y
            v = x
            mag = np.sqrt(u**2 + v**2)
            if mag < 1e-6:
                break
            # Normalize and step
            x_new = x + dt * u / mag
            y_new = y + dt * v / mag
            # Stop if out of bounds
            if abs(x_new) > 3.2 or abs(y_new) > 3.2:
                break
            x, y = x_new, y_new
            points.append((x, y))

        # Only include streamlines with enough points
        if len(points) > 5:
            for j, (px, py) in enumerate(points):
                # Velocity magnitude equals distance from center in this vortex
                vel = np.sqrt(px**2 + py**2)
                streamlines_data.append(
                    {"x": float(px), "y": float(py), "streamline_id": streamline_id, "order": j, "velocity": float(vel)}
                )
            streamline_id += 1

df = pd.DataFrame(streamlines_data)

# Compute average velocity per streamline for color encoding
avg_velocity = df.groupby("streamline_id")["velocity"].mean().reset_index()
avg_velocity.columns = ["streamline_id", "avg_velocity"]
df = df.merge(avg_velocity, on="streamline_id")

# Create the streamline chart using line marks
# Color by average velocity (flow speed) for each streamline
chart = (
    alt.Chart(df)
    .mark_line(strokeWidth=2.5, opacity=0.85)
    .encode(
        x=alt.X("x:Q", title="X Position (units)", scale=alt.Scale(domain=[-3.5, 3.5])),
        y=alt.Y("y:Q", title="Y Position (units)", scale=alt.Scale(domain=[-3.5, 3.5])),
        color=alt.Color(
            "avg_velocity:Q",
            scale=alt.Scale(scheme="viridis"),
            title="Flow Speed",
            legend=alt.Legend(titleFontSize=18, labelFontSize=16, gradientLength=200),
        ),
        detail="streamline_id:N",
        order="order:O",
    )
    .properties(
        width=1600, height=900, title=alt.Title("streamline-basic · altair · pyplots.ai", fontSize=28, anchor="middle")
    )
    .configure_axis(labelFontSize=18, titleFontSize=22, grid=True, gridColor="#cccccc", gridOpacity=0.4)
    .configure_view(strokeWidth=0)
)

# Save as PNG and HTML
chart.save("plot.png", scale_factor=3.0)
chart.save("plot.html")
