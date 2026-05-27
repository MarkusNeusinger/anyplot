""" anyplot.ai
line-3d-trajectory: 3D Line Plot for Trajectory Visualization
Library: pygal 3.1.0 | Python 3.13.13
Quality: 89/100 | Created: 2026-05-16
"""

import os

import matplotlib.pyplot as plt
import numpy as np
import pygal
from matplotlib.colors import Normalize
from pygal.style import Style


THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

IMPRINT = ("#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477")

np.random.seed(42)


# Generate Lorenz attractor trajectory
def lorenz_attractor(dt=0.01, num_steps=3000):
    """Generate Lorenz attractor trajectory."""
    sigma, rho, beta = 10.0, 28.0, 8.0 / 3.0
    x, y, z = 1.0, 1.0, 1.0

    trajectory = np.zeros((num_steps, 3))
    for i in range(num_steps):
        dx = sigma * (y - x)
        dy = x * (rho - z) - y
        dz = x * y - beta * z

        x += dt * dx
        y += dt * dy
        z += dt * dz

        trajectory[i] = [x, y, z]

    return trajectory


# Generate trajectory
trajectory = lorenz_attractor()

# Normalize coordinates for better visualization
x_data = trajectory[:, 0]
y_data = trajectory[:, 1]
z_data = trajectory[:, 2]

# Normalize to [-1, 1] for better scaling
x_norm = (x_data - x_data.mean()) / (x_data.std() + 1e-8)
y_norm = (y_data - y_data.mean()) / (y_data.std() + 1e-8)
z_norm = (z_data - z_data.mean()) / (z_data.std() + 1e-8)

# Create segments with color gradient based on Z progression
num_segments = 30
segment_length = len(x_norm) // num_segments

# Generate color gradient from viridis
cmap = plt.get_cmap("viridis")
norm = Normalize(vmin=0, vmax=num_segments - 1)

custom_style = Style(
    background=PAGE_BG,
    plot_background=PAGE_BG,
    foreground=INK,
    foreground_strong=INK,
    foreground_subtle=INK_MUTED,
    colors=IMPRINT,
    title_font_size=28,
    label_font_size=22,
    major_label_font_size=18,
    legend_font_size=16,
    value_font_size=14,
    stroke_width=2.5,
)

chart = pygal.XY(
    title="line-3d-trajectory · pygal · anyplot.ai",
    x_title="X (Projected)",
    y_title="Y (Projected)",
    width=4800,
    height=2700,
    style=custom_style,
    show_legend=True,
    show_dots=False,
    stroke_dasharray=None,
)

# Add trajectory segments with color progression
for i in range(num_segments):
    start_idx = i * segment_length
    end_idx = start_idx + segment_length if i < num_segments - 1 else len(x_norm)

    segment_x = x_norm[start_idx:end_idx]
    segment_y = y_norm[start_idx:end_idx]

    # Create (x, y) coordinate pairs for this segment
    xy_pairs = [(float(segment_x[j]), float(segment_y[j])) for j in range(len(segment_x))]

    # Get color for this segment (Z progression)
    z_value = z_norm[start_idx : end_idx + 1].mean()
    normalized_z = (z_value + 1) / 2  # Map [-1, 1] to [0, 1]
    rgba = cmap(norm(i))
    color = f"#{int(rgba[0] * 255):02x}{int(rgba[1] * 255):02x}{int(rgba[2] * 255):02x}"

    # Add series
    chart.add(f"Segment {i + 1}", xy_pairs, stroke_style={"width": 2}, color=color)

# Save outputs
chart.render_to_png(f"plot-{THEME}.png")

with open(f"plot-{THEME}.html", "wb") as f:
    f.write(chart.render())
