""" pyplots.ai
scatter-color-mapped: Color-Mapped Scatter Plot
Library: pygal 3.1.0 | Python 3.13.11
Quality: 90/100 | Created: 2025-12-26
"""

import numpy as np
import pygal
from pygal.style import Style


# Data - Temperature readings across sensor grid
np.random.seed(42)
n_points = 100
x = np.random.uniform(0, 100, n_points)  # Grid X position (meters)
y = np.random.uniform(0, 100, n_points)  # Grid Y position (meters)
# Temperature increases toward center with some noise
center_dist = np.sqrt((x - 50) ** 2 + (y - 50) ** 2)
temperature = 35 - 0.3 * center_dist + np.random.normal(0, 3, n_points)

# Create color bins for the continuous variable (pygal uses discrete series)
n_bins = 8
temp_min, temp_max = temperature.min(), temperature.max()
bin_edges = np.linspace(temp_min, temp_max, n_bins + 1)
bin_indices = np.digitize(temperature, bin_edges[:-1]) - 1
bin_indices = np.clip(bin_indices, 0, n_bins - 1)

# Viridis-inspired colorblind-safe palette (dark to light)
viridis_colors = [
    "#440154",  # Dark purple
    "#482878",  # Purple
    "#3E4A89",  # Blue-purple
    "#31688E",  # Blue
    "#26828E",  # Teal
    "#35B779",  # Green
    "#6DCD59",  # Light green
    "#FDE725",  # Yellow
]

# Custom style for large canvas
custom_style = Style(
    background="white",
    plot_background="white",
    foreground="#333333",
    foreground_strong="#333333",
    foreground_subtle="#666666",
    colors=viridis_colors,
    title_font_size=60,
    label_font_size=40,
    major_label_font_size=36,
    legend_font_size=32,
    value_font_size=28,
    stroke_width=1,
    opacity=0.85,
)

# Create XY scatter chart
chart = pygal.XY(
    width=4800,
    height=2700,
    style=custom_style,
    title="scatter-color-mapped · pygal · pyplots.ai",
    x_title="Grid X Position (meters)",
    y_title="Grid Y Position (meters)",
    show_dots=True,
    dots_size=16,
    stroke=False,  # No lines connecting points
    show_x_guides=True,
    show_y_guides=True,
    legend_at_bottom=True,
    legend_box_size=24,
    truncate_legend=-1,  # Don't truncate legend text
)

# Add data as separate series for each color bin (creates color-mapped effect)
# Legend acts as colorbar reference scale with Temperature label
for i in range(n_bins):
    mask = bin_indices == i
    if mask.sum() > 0:
        points = [(float(x[j]), float(y[j])) for j in range(n_points) if mask[j]]
        # First bin includes variable name as colorbar title
        if i == 0:
            label = f"Temperature: {bin_edges[i]:.0f}-{bin_edges[i + 1]:.0f}°C"
        else:
            label = f"{bin_edges[i]:.0f}-{bin_edges[i + 1]:.0f}°C"
        chart.add(label, points)

# Save outputs
chart.render_to_png("plot.png")
chart.render_to_file("plot.html")
