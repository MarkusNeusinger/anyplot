""" pyplots.ai
scatter-regression-polynomial: Scatter Plot with Polynomial Regression
Library: pygal 3.1.0 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-25
"""

import numpy as np
import pygal
from pygal.style import Style


# Data - Studying growth curves: hours of sunlight vs plant growth
np.random.seed(42)
n_points = 80
x = np.linspace(2, 14, n_points)  # Hours of sunlight (2-14 hours)
# Quadratic relationship with noise: growth increases then plateaus
y_true = -2.5 * x**2 + 45 * x - 80  # Parabolic pattern (diminishing returns)
y = y_true + np.random.randn(n_points) * 12  # Add noise

# Fit polynomial regression (degree 2 - quadratic)
coeffs = np.polyfit(x, y, 2)
poly = np.poly1d(coeffs)

# Calculate R-squared
y_pred = poly(x)
ss_res = np.sum((y - y_pred) ** 2)
ss_tot = np.sum((y - np.mean(y)) ** 2)
r_squared = 1 - (ss_res / ss_tot)

# Generate smooth curve for regression line
x_curve = np.linspace(x.min(), x.max(), 200)
y_curve = poly(x_curve)

# Format polynomial equation
a, b, c = coeffs
equation = f"y = {a:.2f}x² + {b:.2f}x + {c:.2f}"

# Custom style for pyplots
custom_style = Style(
    background="white",
    plot_background="white",
    foreground="#333333",
    foreground_strong="#333333",
    foreground_subtle="#666666",
    colors=("#306998", "#E74C3C"),  # Python Blue for points, Red for curve
    title_font_size=48,
    label_font_size=32,
    major_label_font_size=28,
    legend_font_size=28,
    value_font_size=24,
    tooltip_font_size=20,
)

# Create XY scatter chart
chart = pygal.XY(
    width=4800,
    height=2700,
    style=custom_style,
    title="scatter-regression-polynomial · pygal · pyplots.ai",
    x_title="Sunlight Exposure (hours)",
    y_title="Plant Growth (cm)",
    show_legend=True,
    legend_at_bottom=False,
    stroke=False,
    dots_size=8,
    show_x_guides=True,
    show_y_guides=True,
    x_label_rotation=0,
)

# Prepare scatter data as list of (x, y) tuples
scatter_data = [(float(x[i]), float(y[i])) for i in range(len(x))]

# Prepare regression curve data
curve_data = [(float(x_curve[i]), float(y_curve[i])) for i in range(len(x_curve))]

# Add data series
chart.add("Data Points", scatter_data, dots_size=8, stroke=False)

# Create a separate line chart for the regression curve overlay
# Since pygal.XY with stroke=False won't show line, create Line chart approach
# Use XY with stroke enabled for the curve
curve_chart = pygal.XY(
    width=4800,
    height=2700,
    style=Style(
        background="transparent",
        plot_background="transparent",
        foreground="#333333",
        foreground_strong="#333333",
        foreground_subtle="#666666",
        colors=("#E74C3C",),
        title_font_size=48,
        label_font_size=32,
        major_label_font_size=28,
        legend_font_size=28,
        stroke_width=4,
    ),
    stroke=True,
    dots_size=0,
    show_dots=False,
)

# For pygal, we need to combine scatter and line in same chart
# Reset chart with proper configuration
chart = pygal.XY(
    width=4800,
    height=2700,
    style=custom_style,
    title="scatter-regression-polynomial · pygal · pyplots.ai",
    x_title="Sunlight Exposure (hours)",
    y_title="Plant Growth (cm)",
    show_legend=True,
    legend_at_bottom=True,
    legend_box_size=24,
    dots_size=10,
    show_x_guides=True,
    show_y_guides=True,
    x_label_rotation=0,
    stroke_style={"width": 4},
)

# Add scatter points (no stroke, just dots)
chart.add("Data Points (α=0.7)", scatter_data, stroke=False, dots_size=10)

# Add regression curve (stroke, no dots) - subsample for cleaner rendering
curve_subsample = [(float(x_curve[i]), float(y_curve[i])) for i in range(0, len(x_curve), 5)]
chart.add(f"Polynomial Fit (R²={r_squared:.3f})", curve_subsample, stroke=True, show_dots=False, dots_size=0)

# Render to PNG and HTML
chart.render_to_png("plot.png")
chart.render_to_file("plot.html")
