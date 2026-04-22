""" pyplots.ai
residual-plot: Residual Plot
Library: pygal 3.1.0 | Python 3.13.11
Quality: 88/100 | Created: 2025-12-26
"""

import numpy as np
import pygal
from pygal.style import Style


# Data - Linear regression example with some non-linearity
np.random.seed(42)
n_points = 100

# Generate fitted values (x-axis) - house price predictions in $1000s
fitted_values = np.linspace(150, 500, n_points)

# Generate residuals with slight heteroscedasticity and a few outliers
base_residuals = np.random.normal(0, 20, n_points)
# Add slight heteroscedasticity (variance increases with fitted values)
heteroscedasticity = (fitted_values / 500) * np.random.normal(0, 15, n_points)
residuals = base_residuals + heteroscedasticity

# Add a few outliers
outlier_indices = [15, 45, 78]
residuals[outlier_indices] = [85, -75, 90]

# Calculate standard deviation for reference bands
std_residuals = np.std(residuals)
upper_band = 2 * std_residuals
lower_band = -2 * std_residuals

# Identify outliers (beyond 2 standard deviations)
outlier_mask = np.abs(residuals) > 2 * std_residuals

# Custom style for 4800x2700 canvas following library guide recommendations
custom_style = Style(
    background="white",
    plot_background="white",
    foreground="#333333",
    foreground_strong="#333333",
    foreground_subtle="#999999",
    colors=("#306998", "#E74C3C", "#2C3E50", "#AAAAAA", "#AAAAAA"),
    title_font_size=32,
    label_font_size=22,
    major_label_font_size=20,
    legend_font_size=24,
    value_font_size=16,
    tooltip_font_size=16,
    stroke_width=3,
    guide_stroke_color="#DDDDDD",
    guide_stroke_dasharray="3, 3",
)

# Create XY scatter chart for residual plot
# Use explicit x_labels to control axis display and range settings
chart = pygal.XY(
    width=4800,
    height=2700,
    style=custom_style,
    title="residual-plot · pygal · pyplots.ai",
    x_title="Fitted Values - Predicted Price ($1000s)",
    y_title="Residuals - Actual minus Predicted ($1000s)",
    show_legend=True,
    legend_at_bottom=True,
    legend_at_bottom_columns=5,
    show_x_guides=True,
    show_y_guides=True,
    stroke=False,
    dots_size=12,
    truncate_legend=-1,
    x_label_rotation=0,
    xrange=(140, 510),
    range=(-100, 110),
)

# Set explicit x-axis labels to display actual fitted values (not indices)
chart.x_labels = [150, 200, 250, 300, 350, 400, 450, 500]

# Prepare data points - separate normal and outlier points
normal_points = [(float(fitted_values[i]), float(residuals[i])) for i in range(n_points) if not outlier_mask[i]]
outlier_points = [(float(fitted_values[i]), float(residuals[i])) for i in range(n_points) if outlier_mask[i]]

# Add data series
chart.add("Residuals", normal_points)
chart.add("Outliers (>2σ)", outlier_points)

# Add zero reference line - create more points for solid appearance
zero_line_points = [(float(x), 0.0) for x in np.linspace(150, 500, 50)]
chart.add("Zero Reference (Perfect Fit)", zero_line_points, stroke=True, show_dots=False, stroke_style={"width": 5})

# Add +2σ reference band line with multiple points for visibility
upper_band_points = [(float(x), float(upper_band)) for x in np.linspace(150, 500, 50)]
chart.add(
    "+2σ Threshold", upper_band_points, stroke=True, show_dots=False, stroke_style={"width": 3, "dasharray": "10, 8"}
)

# Add -2σ reference band line with multiple points for visibility
lower_band_points = [(float(x), float(lower_band)) for x in np.linspace(150, 500, 50)]
chart.add(
    "-2σ Threshold", lower_band_points, stroke=True, show_dots=False, stroke_style={"width": 3, "dasharray": "10, 8"}
)

# Save as PNG and HTML
chart.render_to_png("plot.png")
chart.render_to_file("plot.html")
