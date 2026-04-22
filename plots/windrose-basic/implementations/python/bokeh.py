""" pyplots.ai
windrose-basic: Wind Rose Chart
Library: bokeh 3.8.1 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-24
"""

import numpy as np
from bokeh.io import export_png, output_file, save
from bokeh.models import ColumnDataSource, Legend, LegendItem
from bokeh.plotting import figure


# Data - Generate realistic wind data for a coastal weather station
np.random.seed(42)
n_observations = 5000

# Direction distribution favoring SW and W winds (common for coastal areas)
direction_weights = [0.08, 0.06, 0.05, 0.08, 0.10, 0.18, 0.25, 0.20]  # N, NE, E, SE, S, SW, W, NW
directions_idx = np.random.choice(8, size=n_observations, p=direction_weights)
direction_noise = np.random.uniform(-22.5, 22.5, n_observations)
directions = directions_idx * 45 + direction_noise
directions = directions % 360

# Wind speed with Weibull distribution (realistic for wind data)
speeds = np.random.weibull(2.2, n_observations) * 6  # Scale for m/s

# Define bins
direction_bins = np.linspace(0, 360, 9)  # 8 direction sectors
direction_labels = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"]
speed_bins = [0, 3, 6, 9, 12, np.inf]  # m/s ranges
speed_labels = ["0-3 m/s", "3-6 m/s", "6-9 m/s", "9-12 m/s", ">12 m/s"]

# Colors from cool (calm) to warm (strong)
speed_colors = ["#306998", "#4A90A4", "#FFD43B", "#FFA500", "#E74C3C"]

# Aggregate data into direction/speed bins
dir_indices = np.digitize(directions, direction_bins) - 1
dir_indices = np.clip(dir_indices, 0, 7)
speed_indices = np.digitize(speeds, speed_bins) - 1
speed_indices = np.clip(speed_indices, 0, len(speed_bins) - 2)

# Calculate frequencies for each direction/speed combination
frequencies = np.zeros((8, len(speed_bins) - 1))
for d_idx in range(8):
    for s_idx in range(len(speed_bins) - 1):
        frequencies[d_idx, s_idx] = np.sum((dir_indices == d_idx) & (speed_indices == s_idx))

# Convert to percentages
frequencies = frequencies / n_observations * 100

# Create figure - square format for polar-like display
p = figure(
    width=3600,
    height=3600,
    title="windrose-basic · bokeh · pyplots.ai",
    x_range=(-35, 35),
    y_range=(-35, 35),
    tools="",
    toolbar_location=None,
)

# Style title
p.title.text_font_size = "32pt"
p.title.align = "center"

# Hide axes for polar plot
p.xaxis.visible = False
p.yaxis.visible = False
p.xgrid.visible = False
p.ygrid.visible = False
p.outline_line_color = None

# Draw concentric circles for reference
for radius in [5, 10, 15, 20, 25]:
    theta_circle = np.linspace(0, 2 * np.pi, 100)
    x_circle = radius * np.cos(theta_circle)
    y_circle = radius * np.sin(theta_circle)
    p.line(x_circle, y_circle, line_color="#CCCCCC", line_width=1.5, line_alpha=0.5)
    # Add frequency labels on the right side
    p.text(
        x=[radius + 0.5],
        y=[0.5],
        text=[f"{radius}%"],
        text_font_size="16pt",
        text_color="#666666",
        text_baseline="bottom",
    )

# Draw direction lines and labels
sector_width = 2 * np.pi / 8  # 45 degrees in radians
for i, label in enumerate(direction_labels):
    angle = np.pi / 2 - i * sector_width  # Start from North (top), go clockwise

    # Draw spoke lines
    x_spoke = [0, 28 * np.cos(angle)]
    y_spoke = [0, 28 * np.sin(angle)]
    p.line(x_spoke, y_spoke, line_color="#AAAAAA", line_width=1.5, line_alpha=0.4)

    # Add direction labels outside
    label_radius = 30
    x_label = label_radius * np.cos(angle)
    y_label = label_radius * np.sin(angle)
    p.text(
        x=[x_label],
        y=[y_label],
        text=[label],
        text_font_size="22pt",
        text_font_style="bold",
        text_color="#333333",
        text_align="center",
        text_baseline="middle",
    )

# Draw stacked wedges for each direction
legend_items = []
renderers_by_speed = {i: [] for i in range(len(speed_labels))}

for dir_idx in range(8):
    # Angle for this direction (North = up, clockwise)
    center_angle = np.pi / 2 - dir_idx * sector_width

    # Draw wedges for each speed bin (stacked from center outward)
    cumulative_radius = 0
    for speed_idx in range(len(speed_labels)):
        freq = frequencies[dir_idx, speed_idx]
        if freq > 0.1:  # Only draw if significant
            inner_radius = cumulative_radius
            outer_radius = cumulative_radius + freq

            # Create wedge shape
            n_points = 30
            angles = np.linspace(
                center_angle - sector_width / 2 + 0.02, center_angle + sector_width / 2 - 0.02, n_points
            )

            # Build polygon: inner arc, outer arc (reversed)
            x_inner = inner_radius * np.cos(angles)
            y_inner = inner_radius * np.sin(angles)
            x_outer = outer_radius * np.cos(angles[::-1])
            y_outer = outer_radius * np.sin(angles[::-1])

            x_wedge = np.concatenate([x_inner, x_outer])
            y_wedge = np.concatenate([y_inner, y_outer])

            source = ColumnDataSource(data={"x": [x_wedge.tolist()], "y": [y_wedge.tolist()]})
            renderer = p.patches(
                xs="x",
                ys="y",
                source=source,
                fill_color=speed_colors[speed_idx],
                fill_alpha=0.85,
                line_color="white",
                line_width=1.5,
            )
            renderers_by_speed[speed_idx].append(renderer)

            cumulative_radius = outer_radius

# Create legend items
for speed_idx in range(len(speed_labels)):
    if renderers_by_speed[speed_idx]:
        legend_items.append(LegendItem(label=speed_labels[speed_idx], renderers=[renderers_by_speed[speed_idx][0]]))

# Add legend
legend = Legend(
    items=legend_items,
    location="center",
    label_text_font_size="18pt",
    spacing=10,
    padding=15,
    background_fill_alpha=0.9,
    background_fill_color="white",
    border_line_color="#CCCCCC",
    border_line_width=2,
)
p.add_layout(legend, "right")

# Add subtitle with data info
p.text(
    x=[0],
    y=[-33],
    text=["Wind Speed (m/s)"],
    text_font_size="20pt",
    text_color="#444444",
    text_align="center",
    text_baseline="top",
)

# Save as PNG and HTML
export_png(p, filename="plot.png")
output_file("plot.html")
save(p)
