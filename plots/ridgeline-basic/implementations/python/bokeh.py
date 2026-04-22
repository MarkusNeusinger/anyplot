""" pyplots.ai
ridgeline-basic: Basic Ridgeline Plot
Library: bokeh 3.8.1 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-23
"""

import numpy as np
from bokeh.io import export_png, output_file, save
from bokeh.plotting import figure


# Data - Monthly temperature distributions
np.random.seed(42)

months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

# Generate realistic monthly temperature data (Celsius) with seasonal variation
base_temps = [5, 7, 12, 16, 20, 24, 27, 26, 22, 16, 10, 6]
temp_data = {}
for i, month in enumerate(months):
    temps = np.random.normal(base_temps[i], 3, 200)
    temp_data[month] = temps

# Create plot (4800 × 2700 px)
p = figure(
    width=4800,
    height=2700,
    title="ridgeline-basic · bokeh · pyplots.ai",
    x_axis_label="Temperature (°C)",
    y_axis_label="Month",
    y_range=months[::-1],  # Reverse to have January at top
    toolbar_location=None,
)

# Color gradient from blue (cold) to yellow/orange (warm) to blue again
colors = [
    "#306998",  # Jan - cold blue
    "#3A7CA5",  # Feb
    "#50A3C1",  # Mar
    "#6BBFCC",  # Apr
    "#8FD4B4",  # May
    "#C5E99B",  # Jun
    "#FFD43B",  # Jul - warm yellow
    "#FFAA33",  # Aug - warm orange
    "#E7A467",  # Sep
    "#DB8C7D",  # Oct
    "#5BB6CF",  # Nov
    "#306998",  # Dec - cold blue
]

# Spacing and overlap parameters
ridge_height = 0.65  # Height multiplier for each ridge
x_grid = np.linspace(-5, 40, 300)

# Plot ridgelines (from bottom to top for proper overlapping)
for i, month in enumerate(reversed(months)):
    temps = temp_data[month]

    # Compute KDE using Gaussian kernel (Silverman's rule for bandwidth)
    n = len(temps)
    std = np.std(temps)
    iqr = np.percentile(temps, 75) - np.percentile(temps, 25)
    bandwidth = 0.9 * min(std, iqr / 1.34) * n ** (-0.2)
    bandwidth = max(bandwidth, 0.1)

    density = np.zeros_like(x_grid, dtype=float)
    for xi in temps:
        density += np.exp(-0.5 * ((x_grid - xi) / bandwidth) ** 2)
    density /= n * bandwidth * np.sqrt(2 * np.pi)

    # Normalize density to fit within ridge height
    density_normalized = density / density.max() * ridge_height

    # Y position (reversed order so Jan is at top)
    color_idx = len(months) - 1 - i  # Original month index for color

    # Create patch coordinates
    x_patch = np.concatenate([[x_grid[0]], x_grid, [x_grid[-1]]])
    y_patch_numeric = np.concatenate([[0], density_normalized, [0]])

    # For categorical y-axis, use factor offsets
    y_patches = [(month, float(y)) for y in y_patch_numeric]

    # Fill with color and add outline
    p.patch(
        x=list(x_patch), y=y_patches, fill_color=colors[color_idx], fill_alpha=0.85, line_color="#333333", line_width=2
    )

# Style the plot
p.title.text_font_size = "32pt"
p.xaxis.axis_label_text_font_size = "24pt"
p.yaxis.axis_label_text_font_size = "24pt"
p.xaxis.major_label_text_font_size = "18pt"
p.yaxis.major_label_text_font_size = "18pt"

# Grid styling
p.xgrid.grid_line_alpha = 0.3
p.xgrid.grid_line_dash = "dashed"
p.ygrid.grid_line_alpha = 0

# Axis styling
p.xaxis.axis_line_width = 2
p.yaxis.axis_line_width = 2
p.xaxis.major_tick_line_width = 2
p.yaxis.major_tick_line_width = 2

# Set x-axis range to show all data
p.x_range.start = -5
p.x_range.end = 40

# Remove y-axis ticks (we have categorical labels)
p.yaxis.major_tick_line_color = None
p.yaxis.minor_tick_line_color = None

# Background
p.background_fill_color = "#FAFAFA"

# Save outputs
output_file("plot.html")
save(p)
export_png(p, filename="plot.png")
