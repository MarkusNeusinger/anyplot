""" pyplots.ai
streamline-basic: Basic Streamline Plot
Library: pygal 3.1.0 | Python 3.13.11
Quality: 77/100 | Created: 2025-12-31
"""

import numpy as np
import pygal
from pygal.style import Style


# Data - Vortex flow field (circular streamlines)
# u = -y, v = x creates counterclockwise circular flow
np.random.seed(42)

# Trace streamlines inline - KISS structure (no helper functions)
# Starting points distributed at different radii to show flow structure
streamlines = []

# Use 4 radii to show different orbital distances
radii = [0.8, 1.3, 1.8, 2.3]
points_per_radius = 5

for radius in radii:
    for angle_idx in range(points_per_radius):
        angle = 2 * np.pi * angle_idx / points_per_radius
        x0 = radius * np.cos(angle)
        y0 = radius * np.sin(angle)

        # Trace streamline from this starting point
        points = [(x0, y0)]
        x, y = x0, y0
        dt = 0.02  # Smaller step for smoother curves
        max_steps = 400  # More steps for longer, smoother curves
        bounds = 3.0

        for _ in range(max_steps):
            # Velocity field: vortex with radial decay
            r = np.sqrt(x**2 + y**2)
            factor = 1.0 / (1.0 + 0.1 * r)
            u = -y * factor
            v = x * factor
            speed = np.sqrt(u**2 + v**2)

            if speed < 0.001:  # Stagnation point
                break

            # Normalize and step
            x_new = x + dt * u / speed
            y_new = y + dt * v / speed

            # Check bounds
            if abs(x_new) > bounds or abs(y_new) > bounds:
                break

            x, y = x_new, y_new
            points.append((x, y))

        if len(points) > 10:  # Only keep meaningful streamlines
            streamlines.append((points, radius))

# Group streamlines by radial distance for coloring
# 4 distinct high-contrast colors for different radii
# Labels describe orbit radius, not "speed" - for vortex flow, all orbits have same
# angular velocity so inner orbits have lower linear speed
bin_colors = ["#d62728", "#2ca02c", "#1f77b4", "#9467bd"]
bin_labels = ["Inner Orbit (r=0.8)", "Mid-Inner Orbit (r=1.3)", "Mid-Outer Orbit (r=1.8)", "Outer Orbit (r=2.3)"]

binned_streamlines = {i: [] for i in range(4)}
for points, radius in streamlines:
    bin_idx = radii.index(radius)
    binned_streamlines[bin_idx].append(points)

# Custom style with larger fonts for readability
custom_style = Style(
    background="white",
    plot_background="white",
    foreground="#333333",
    foreground_strong="#333333",
    foreground_subtle="#555555",
    colors=tuple(bin_colors),
    title_font_size=72,
    label_font_size=48,
    major_label_font_size=40,
    legend_font_size=48,
    value_font_size=32,
    guide_stroke_color="#cccccc",
)

# Create chart
chart = pygal.XY(
    style=custom_style,
    width=4800,
    height=2700,
    stroke=True,
    stroke_style={"width": 10},
    show_dots=False,
    show_legend=True,
    legend_at_bottom=True,
    legend_at_bottom_columns=4,
    title="streamline-basic · pygal · pyplots.ai",
    x_title="X Position",
    y_title="Y Position",
    show_x_guides=True,
    show_y_guides=True,
    range=(-3.5, 3.5),
    xrange=(-3.5, 3.5),
    dots_size=8,  # Larger dots for legend visibility
)

# Add each bin as a series
for bin_idx in range(4):
    series_data = []
    for sl in binned_streamlines[bin_idx]:
        # Add streamline points
        for point in sl:
            series_data.append(point)
        # Add None to separate streamlines
        series_data.append(None)

    if series_data:
        chart.add(bin_labels[bin_idx], series_data)

# Save outputs
chart.render_to_png("plot.png")
chart.render_to_file("plot.html")
