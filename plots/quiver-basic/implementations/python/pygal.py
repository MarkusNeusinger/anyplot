""" pyplots.ai
quiver-basic: Basic Quiver Plot
Library: pygal 3.1.0 | Python 3.13.11
Quality: 82/100 | Created: 2025-12-23
"""

import numpy as np
import pygal
from pygal.style import Style


# Data - Wind flow pattern over a geographic area
# Simulating wind vectors that flow around a central low-pressure system
np.random.seed(42)
grid_size = 12
x_range = np.linspace(-3, 3, grid_size)  # Longitude-like coordinates
y_range = np.linspace(-3, 3, grid_size)  # Latitude-like coordinates
X, Y = np.meshgrid(x_range, y_range)
x_flat = X.flatten()
y_flat = Y.flatten()

# Circular rotation field simulating counterclockwise wind around low pressure
# u = -y, v = x creates the rotation pattern
U = -y_flat
V = x_flat

# Calculate magnitude - represents wind speed (stronger further from center)
magnitude = np.sqrt(U**2 + V**2)
max_mag = magnitude.max()

# Normalize magnitude to 0-1 range for color mapping
norm_mag = magnitude / max_mag

# Scale vectors for visual clarity
arrow_scale = 0.12
U_scaled = U * arrow_scale
V_scaled = V * arrow_scale

# Arrowhead parameters
head_ratio = 0.4
head_angle = 0.55

# Color palette for magnitude bins (blue to orange to red, colorblind-friendly)
# Low magnitude = blue/cyan, High magnitude = orange/red
num_bins = 5
bin_colors = ["#2269a4", "#32b9b0", "#e6a020", "#e65020", "#ff3232"]
wind_labels = ["Calm", "Light", "Moderate", "Fresh", "Strong"]

# Group arrows by magnitude ranges for color encoding
arrow_groups = {i: [] for i in range(num_bins)}

for i in range(len(x_flat)):
    # Skip very weak vectors (near center)
    if magnitude[i] < 0.05:
        continue

    x1, y1 = x_flat[i], y_flat[i]
    x2, y2 = x1 + U_scaled[i], y1 + V_scaled[i]

    # Calculate arrowhead size based on arrow length
    arrow_len = np.sqrt(U_scaled[i] ** 2 + V_scaled[i] ** 2)
    head_size = arrow_len * head_ratio

    # Calculate arrowhead points
    angle = np.arctan2(V_scaled[i], U_scaled[i])
    x_left = x2 - head_size * np.cos(angle - head_angle)
    y_left = y2 - head_size * np.sin(angle - head_angle)
    x_right = x2 - head_size * np.cos(angle + head_angle)
    y_right = y2 - head_size * np.sin(angle + head_angle)

    # Determine which bin this arrow belongs to
    bin_idx = min(int(norm_mag[i] * num_bins), num_bins - 1)

    # Build arrow segments (shaft + arrowhead)
    arrow_groups[bin_idx].extend([(x1, y1), (x2, y2), None])
    arrow_groups[bin_idx].extend([(x2, y2), (x_left, y_left), None])
    arrow_groups[bin_idx].extend([(x2, y2), (x_right, y_right), None])

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
    legend_font_size=56,
    value_font_size=32,
    guide_stroke_color="#dddddd",
)

# Create chart
chart = pygal.XY(
    style=custom_style,
    width=4800,
    height=2700,
    stroke=True,
    stroke_style={"width": 20},
    show_dots=False,
    show_legend=True,
    legend_at_bottom=True,
    legend_at_bottom_columns=5,
    title="quiver-basic · pygal · pyplots.ai",
    x_title="Longitude (degrees)",
    y_title="Latitude (degrees)",
    show_x_guides=True,
    show_y_guides=True,
    range=(-3.8, 3.8),
    xrange=(-3.8, 3.8),
)

# Add each magnitude group as a separate series with its color
for i in range(num_bins):
    if arrow_groups[i]:
        chart.add(wind_labels[i], arrow_groups[i])

# Save outputs
chart.render_to_png("plot.png")
chart.render_to_file("plot.html")
