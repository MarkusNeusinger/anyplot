""" pyplots.ai
curve-bias-variance-tradeoff: Bias-Variance Tradeoff Curve
Library: pygal 3.1.0 | Python 3.13.11
Quality: 88/100 | Created: 2026-01-26
"""

import numpy as np
import pygal
from pygal.style import Style


# Data: Generate theoretical bias-variance tradeoff curves
np.random.seed(42)
complexity = np.linspace(0.5, 10, 100)

# Bias squared: decreases with complexity (high bias at low complexity)
bias_squared = 4.0 / (1 + 0.8 * complexity)

# Variance: increases with complexity (high variance at high complexity)
variance = 0.1 * complexity**1.5

# Irreducible error: constant noise floor
irreducible_error = np.full_like(complexity, 0.5)

# Total error: sum of all components
total_error = bias_squared + variance + irreducible_error

# Find optimal complexity point (minimum total error)
optimal_idx = np.argmin(total_error)
optimal_complexity = complexity[optimal_idx]
optimal_error = total_error[optimal_idx]

# Custom style for pyplots with distinct colors for each series
# Colors: Underfitting zone, Overfitting zone, Bias², Variance, Total Error, Irreducible, Optimal Point
custom_style = Style(
    background="white",
    plot_background="white",
    foreground="#333",
    foreground_strong="#333",
    foreground_subtle="#666",
    colors=("#3498DB", "#E67E22", "#E74C3C", "#27AE60", "#9B59B6", "#1ABC9C", "#8B0000"),
    title_font_size=56,
    label_font_size=36,
    major_label_font_size=32,
    legend_font_size=30,
    value_font_size=28,
    stroke_width=5,
    value_label_font_size=32,
)

# Create XY chart for smooth curves
chart = pygal.XY(
    width=4800,
    height=2700,
    style=custom_style,
    title="curve-bias-variance-tradeoff · pygal · pyplots.ai",
    x_title="Model Complexity (Low → High)",
    y_title="Prediction Error  |  Total = Bias² + Variance + Irreducible",
    show_dots=False,
    stroke_style={"width": 6},
    show_x_guides=True,
    show_y_guides=True,
    legend_at_bottom=True,
    legend_box_size=24,
    truncate_legend=-1,
    range=(0, 4.5),
    xrange=(0, 11),
    tooltip_border_radius=10,
    print_values=False,
)

# Prepare data for XY chart (list of tuples)
bias_data = [(float(x), float(y)) for x, y in zip(complexity, bias_squared, strict=True)]
variance_data = [(float(x), float(y)) for x, y in zip(complexity, variance, strict=True)]
irreducible_data = [(float(x), float(y)) for x, y in zip(complexity, irreducible_error, strict=True)]
total_data = [(float(x), float(y)) for x, y in zip(complexity, total_error, strict=True)]

# Add shaded region indicators using thicker, semi-transparent lines at the bottom
# Underfitting zone indicator (left side - high bias region)
underfitting_indicator = [(float(x), 0.2) for x in complexity if x <= optimal_complexity]
chart.add(
    "Underfitting Zone ← (High Bias)",
    underfitting_indicator,
    stroke_style={"width": 50, "opacity": 0.35},
    show_dots=False,
)

# Overfitting zone indicator (right side - high variance region)
overfitting_indicator = [(float(x), 0.2) for x in complexity if x >= optimal_complexity]
chart.add(
    "Overfitting Zone → (High Variance)",
    overfitting_indicator,
    stroke_style={"width": 50, "opacity": 0.35},
    show_dots=False,
)

# Add curves with distinct styles - using descriptive legend labels with arrows
chart.add("Bias² (decreasing →)", bias_data, stroke_style={"width": 8, "dasharray": "20, 10"}, show_dots=False)
chart.add("Variance (← increasing)", variance_data, stroke_style={"width": 8, "dasharray": "10, 5"}, show_dots=False)
chart.add("Total Error (U-shaped)", total_data, stroke_style={"width": 9}, show_dots=False)
chart.add(
    "Irreducible Error (constant)", irreducible_data, stroke_style={"width": 7, "dasharray": "4, 4"}, show_dots=False
)

# Add optimal point marker with detailed tooltip
optimal_point = [
    {
        "value": (float(optimal_complexity), float(optimal_error)),
        "label": f"Optimal: x={optimal_complexity:.1f}, error={optimal_error:.2f}",
    }
]
chart.add(f"★ Optimal Point (x={optimal_complexity:.1f})", optimal_point, show_dots=True, dots_size=22, stroke=False)

# Save as PNG only
chart.render_to_png("plot.png")
