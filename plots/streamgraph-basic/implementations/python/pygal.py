""" pyplots.ai
streamgraph-basic: Basic Stream Graph
Library: pygal 3.1.0 | Python 3.13.11
Quality: 75/100 | Created: 2025-12-23
"""

import numpy as np
import pygal
from pygal.style import Style


# Data: monthly streaming hours by music genre over two years
np.random.seed(42)

months = 24
month_labels = [
    "Jan 23",
    "Feb 23",
    "Mar 23",
    "Apr 23",
    "May 23",
    "Jun 23",
    "Jul 23",
    "Aug 23",
    "Sep 23",
    "Oct 23",
    "Nov 23",
    "Dec 23",
    "Jan 24",
    "Feb 24",
    "Mar 24",
    "Apr 24",
    "May 24",
    "Jun 24",
    "Jul 24",
    "Aug 24",
    "Sep 24",
    "Oct 24",
    "Nov 24",
    "Dec 24",
]
genres = ["Pop", "Rock", "Hip-Hop", "Electronic", "Jazz"]

# Generate smooth, realistic streaming data with trends
base_values = {"Pop": 45, "Rock": 35, "Hip-Hop": 40, "Electronic": 30, "Jazz": 15}

data = {}
for genre in genres:
    base = base_values[genre]
    # Add trend over time
    trend = np.linspace(0, np.random.uniform(-10, 15), months)
    # Seasonal variation
    seasonal = 8 * np.sin(np.linspace(0, 4 * np.pi, months) + np.random.uniform(0, 2 * np.pi))
    # Random noise
    noise = np.random.randn(months) * 3
    values = base + trend + seasonal + noise
    values = np.maximum(values, 5)  # Ensure positive values
    data[genre] = values.tolist()

# Convert data to array for streamgraph calculation
data_array = np.array([data[genre] for genre in genres])

# Calculate centered baseline for true streamgraph effect
# Symmetric baseline: streams expand outward from center (x-axis at y=0)
total_at_each_time = data_array.sum(axis=0)
baseline_offset = total_at_each_time / 2

# Custom style with colorblind-safe palette
# Colors ordered for maximum contrast between adjacent layers
custom_style = Style(
    background="white",
    plot_background="white",
    foreground="#2c3e50",
    foreground_strong="#2c3e50",
    foreground_subtle="#7f8c8d",
    # High contrast palette: dark blue, orange, teal, crimson, gold
    colors=("#1a5276", "#e67e22", "#138d75", "#c0392b", "#d4ac0d"),
    title_font_size=80,
    label_font_size=48,
    major_label_font_size=40,
    legend_font_size=48,
    value_font_size=36,
    opacity=0.90,
    opacity_hover=0.95,
    guide_stroke_color="#e0e0e0",
    major_guide_stroke_color="#cccccc",
)

# Calculate y-axis range based on actual data
# After centering, min is -baseline_offset, max is baseline_offset (total stack height)
y_min = -baseline_offset.max() * 1.1  # Add 10% padding
y_max = baseline_offset.max() * 1.1

# Create StackedLine chart - pygal's native stacked area chart
# We'll shift all data to center around zero by subtracting half the total from each layer
chart = pygal.StackedLine(
    width=4800,
    height=2700,
    title="streamgraph-basic · pygal · pyplots.ai",
    x_title="Month",
    y_title="Streaming Hours (centered)",
    style=custom_style,
    fill=True,
    show_dots=False,
    show_y_guides=True,
    show_x_guides=False,
    legend_at_bottom=True,
    legend_box_size=36,
    margin=100,
    spacing=40,
    truncate_legend=-1,
    truncate_label=-1,  # Prevent x-axis label truncation
    interpolate="cubic",  # Smooth flowing curves
    show_minor_x_labels=False,
    x_label_rotation=45,  # Rotate labels to prevent overlap
    range=(y_min, y_max),  # Dynamic y-axis range based on data
)

# Set x-axis labels showing months
chart.x_labels = month_labels
chart.x_labels_major = ["Jan 23", "Jul 23", "Jan 24", "Jul 24"]

# To create a centered streamgraph with StackedLine:
# We need to shift each layer's values so the visual center is at y=0
# First layer starts at -baseline_offset, subsequent layers stack on top

# Calculate shifted values for each layer
# The first (bottom) layer is shifted down by baseline_offset
# This makes the visual center of the total stack sit at y=0
shifted_data = []
for i, genre in enumerate(genres):
    if i == 0:
        # First layer: shift down by baseline to center the stream
        shifted_values = (np.array(data[genre]) - baseline_offset).tolist()
    else:
        # Subsequent layers: use original values (they stack on top)
        shifted_values = data[genre]
    shifted_data.append((genre, shifted_values))

# Add all layers
for genre, values in shifted_data:
    chart.add(genre, values)

# Save as PNG and HTML
chart.render_to_png("plot.png")
chart.render_to_file("plot.html")
