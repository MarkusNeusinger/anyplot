""" pyplots.ai
phase-diagram: Phase Diagram (State Space Plot)
Library: altair 6.0.0 | Python 3.13.11
Quality: 92/100 | Created: 2025-12-31
"""

import altair as alt
import numpy as np
import pandas as pd


# Data: Damped pendulum simulation
# The pendulum equation: d2x/dt2 = -sin(x) - gamma * dx/dt
np.random.seed(42)

# Simulate damped pendulum from multiple initial conditions
dt = 0.02
gamma = 0.15  # Damping coefficient

trajectories = []
colors = ["#306998", "#FFD43B", "#E55934", "#9BC53D"]  # Python blue, yellow, + colorblind-safe

initial_conditions = [
    (2.5, 0.0),  # High initial displacement, zero velocity
    (-2.0, 1.5),  # Negative displacement, positive velocity
    (0.5, 2.0),  # Low displacement, high velocity
    (1.5, -1.5),  # Moderate displacement, negative velocity
]

for idx, (x0, v0) in enumerate(initial_conditions):
    x, v = x0, v0
    trajectory_x = [x]
    trajectory_v = [v]

    # Simulate for 500 steps
    for _ in range(500):
        # Euler method for damped pendulum: d2x/dt2 = -sin(x) - gamma * dx/dt
        a = -np.sin(x) - gamma * v
        v = v + a * dt
        x = x + v * dt
        trajectory_x.append(x)
        trajectory_v.append(v)

    # Store trajectory with time-based ordering
    for i, (px, pv) in enumerate(zip(trajectory_x, trajectory_v, strict=True)):
        trajectories.append(
            {
                "x": px,
                "dx_dt": pv,
                "trajectory": f"IC {idx + 1}: ({x0:.1f}, {v0:.1f})",
                "order": i,
                "color": colors[idx],
                "time_normalized": i / len(trajectory_x),
            }
        )

df = pd.DataFrame(trajectories)

# Create phase diagram
base = (
    alt.Chart(df)
    .mark_line(strokeWidth=2.5, opacity=0.85)
    .encode(
        x=alt.X("x:Q", title="Position (x)", axis=alt.Axis(titleFontSize=22, labelFontSize=18)),
        y=alt.Y("dx_dt:Q", title="Velocity (dx/dt)", axis=alt.Axis(titleFontSize=22, labelFontSize=18)),
        color=alt.Color(
            "trajectory:N",
            title="Initial Condition",
            scale=alt.Scale(range=colors),
            legend=alt.Legend(titleFontSize=18, labelFontSize=16, symbolStrokeWidth=3),
        ),
        order=alt.Order("order:Q"),
        detail="trajectory:N",
    )
    .properties(
        width=1600,
        height=900,
        title=alt.Title(
            text="Damped Pendulum Phase Space",
            subtitle="phase-diagram \u00b7 altair \u00b7 pyplots.ai",
            fontSize=28,
            subtitleFontSize=20,
            anchor="middle",
        ),
    )
)

# Add starting points as markers
start_points = df[df["order"] == 0]
points = (
    alt.Chart(start_points)
    .mark_point(size=400, filled=True, opacity=1.0)
    .encode(x="x:Q", y="dx_dt:Q", color=alt.Color("trajectory:N", scale=alt.Scale(range=colors), legend=None))
)

# Add equilibrium point marker at origin
equilibrium = pd.DataFrame([{"x": 0, "y": 0}])
eq_point = (
    alt.Chart(equilibrium).mark_point(shape="cross", size=600, strokeWidth=4, color="black").encode(x="x:Q", y="y:Q")
)

# Combine layers
chart = (
    (base + points + eq_point)
    .configure_axis(grid=True, gridOpacity=0.3, gridDash=[3, 3])
    .configure_view(strokeWidth=0)
    .configure_legend(orient="right", padding=20)
)

# Save as PNG (4800x2700 at scale_factor=3)
chart.save("plot.png", scale_factor=3.0)

# Save interactive HTML version
chart.interactive().save("plot.html")
