""" pyplots.ai
phase-diagram: Phase Diagram (State Space Plot)
Library: bokeh 3.8.1 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-31
"""

# Fix module shadowing when script is named bokeh.py
import sys


sys.path = [p for p in sys.path if p and not p.endswith("implementations")]

import numpy as np  # noqa: E402
from bokeh.io import export_png, output_file, save  # noqa: E402
from bokeh.models import ColorBar, ColumnDataSource, LinearColorMapper  # noqa: E402
from bokeh.palettes import Viridis256  # noqa: E402
from bokeh.plotting import figure  # noqa: E402


# Data: Damped harmonic oscillator (simple pendulum with friction)
# dx/dt = v, dv/dt = -omega^2 * x - gamma * v
np.random.seed(42)

omega = 2.0  # Natural frequency
gamma = 0.3  # Damping coefficient
dt = 0.02
n_steps = 800

# Multiple trajectories from different initial conditions
trajectories = []
initial_conditions = [
    (2.0, 0.0),  # Start from displacement, no velocity
    (-1.5, 2.0),  # Start with both displacement and velocity
    (0.5, -2.5),  # Different quadrant
    (2.5, 1.5),  # Another starting point
]

for x0, v0 in initial_conditions:
    x_traj = [x0]
    v_traj = [v0]
    t_traj = [0]
    x, v = x0, v0

    for i in range(n_steps):
        # Euler integration of damped harmonic oscillator
        ax = -(omega**2) * x - gamma * v
        x_new = x + v * dt
        v_new = v + ax * dt
        x, v = x_new, v_new
        x_traj.append(x)
        v_traj.append(v)
        t_traj.append((i + 1) * dt)

    trajectories.append((x_traj, v_traj, t_traj))

# Create figure
p = figure(
    width=4800,
    height=2700,
    title="Damped Pendulum · phase-diagram · bokeh · pyplots.ai",
    x_axis_label="Position x (displacement)",
    y_axis_label="Velocity dx/dt (m/s)",
    tools="pan,wheel_zoom,box_zoom,reset",
)

# Color palette for distinct trajectories
traj_colors = ["#306998", "#FFD43B", "#E34A33", "#31A354"]

# Single color mapper for time evolution (shared across all trajectories)
color_mapper = LinearColorMapper(palette=Viridis256, low=0, high=1)

# Plot each trajectory as connected line with time-based color markers
for idx, (x_traj, v_traj, t_traj) in enumerate(trajectories):
    # Normalize time for color mapping
    t_norm = np.array(t_traj)
    t_norm = (t_norm - t_norm.min()) / (t_norm.max() - t_norm.min())

    source = ColumnDataSource(data={"x": x_traj, "v": v_traj, "t_norm": t_norm.tolist()})

    # Draw trajectory as scatter points with time-based coloring
    p.scatter(x="x", y="v", source=source, size=12, color={"field": "t_norm", "transform": color_mapper}, alpha=0.85)

    # Add starting point marker (larger, colored by trajectory)
    p.scatter(
        x=[x_traj[0]],
        y=[v_traj[0]],
        size=30,
        color=traj_colors[idx],
        marker="circle",
        line_color="white",
        line_width=3,
        legend_label=f"Start: ({initial_conditions[idx][0]}, {initial_conditions[idx][1]})",
    )

# Mark the fixed point (equilibrium at origin)
p.scatter(x=[0], y=[0], size=40, color="#D62728", marker="x", line_width=5, legend_label="Equilibrium (stable)")

# Add zero velocity line (where dx/dt = 0)
p.line(
    x=[-3.5, 3.5],
    y=[0, 0],
    line_width=3,
    line_dash="dashed",
    line_color="#7F7F7F",
    alpha=0.7,
    legend_label="Zero velocity (dx/dt = 0)",
)

# Add color bar to show time evolution
color_bar = ColorBar(
    color_mapper=LinearColorMapper(palette=Viridis256, low=0, high=16),
    title="Time (s)",
    title_text_font_size="24pt",
    major_label_text_font_size="20pt",
    label_standoff=15,
    width=40,
    location=(0, 0),
)
p.add_layout(color_bar, "right")

# Styling for large canvas (4800x2700)
p.title.text_font_size = "36pt"
p.title.text_font_style = "bold"
p.xaxis.axis_label_text_font_size = "28pt"
p.yaxis.axis_label_text_font_size = "28pt"
p.xaxis.major_label_text_font_size = "22pt"
p.yaxis.major_label_text_font_size = "22pt"

# Grid styling
p.grid.grid_line_alpha = 0.3
p.grid.grid_line_dash = [6, 4]

# Legend styling
p.legend.label_text_font_size = "20pt"
p.legend.location = "top_right"
p.legend.background_fill_alpha = 0.9
p.legend.border_line_width = 2
p.legend.padding = 15
p.legend.spacing = 10

# Background
p.background_fill_color = "#fafafa"

# Save as PNG and HTML
export_png(p, filename="plot.png")
output_file("plot.html")
save(p)
