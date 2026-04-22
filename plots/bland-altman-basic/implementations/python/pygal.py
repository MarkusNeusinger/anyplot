""" pyplots.ai
bland-altman-basic: Bland-Altman Agreement Plot
Library: pygal 3.1.0 | Python 3.13.11
Quality: 94/100 | Created: 2025-12-25
"""

import numpy as np
import pygal
from pygal.style import Style


# Data - Blood pressure readings from two different sphygmomanometers
np.random.seed(42)
n_subjects = 50

# Simulate paired blood pressure measurements (systolic, mmHg)
true_bp = np.random.normal(125, 15, n_subjects)
method1 = true_bp + np.random.normal(0, 5, n_subjects)  # First sphygmomanometer
method2 = true_bp + np.random.normal(2, 6, n_subjects)  # Second sphygmomanometer (slight bias)

# Bland-Altman calculations
mean_values = (method1 + method2) / 2
differences = method1 - method2

mean_diff = np.mean(differences)
std_diff = np.std(differences, ddof=1)
upper_loa = mean_diff + 1.96 * std_diff
lower_loa = mean_diff - 1.96 * std_diff

# Custom style for pyplots
custom_style = Style(
    background="white",
    plot_background="white",
    foreground="#333333",
    foreground_strong="#333333",
    foreground_subtle="#999999",  # More visible grid lines (alpha ~0.4 equivalent)
    guide_stroke_color="#666666",  # Grid line color with good visibility
    colors=("#306998", "#E74C3C", "#27AE60", "#8E44AD"),
    title_font_size=48,
    label_font_size=40,  # Increased for better readability
    major_label_font_size=38,  # Larger tick labels for 4800x2700 canvas
    legend_font_size=32,
    value_font_size=28,
    tooltip_font_size=24,
    stroke_width=4,
    opacity=0.7,
    opacity_hover=0.9,
)

# Create XY chart for scatter plot
chart = pygal.XY(
    width=4800,
    height=2700,
    style=custom_style,
    title="bland-altman-basic · pygal · pyplots.ai",
    x_title="Mean of Two Methods (mmHg)",
    y_title="Difference (Method 1 - Method 2) (mmHg)",
    show_legend=True,
    legend_at_bottom=True,
    legend_at_bottom_columns=4,
    dots_size=12,
    stroke=False,
    show_x_guides=True,
    show_y_guides=True,
    x_label_rotation=0,
    truncate_legend=-1,
    range=(lower_loa - 10, upper_loa + 10),
    y_labels=[round(lower_loa, 1), -10, round(mean_diff, 1), 0, 10, round(upper_loa, 1)],
)

# Prepare scatter data points
scatter_data = [
    {"value": (float(mean_values[i]), float(differences[i])), "label": f"Subject {i + 1}"} for i in range(n_subjects)
]

# Add scatter points
chart.add("Measurements", scatter_data)

# Add horizontal lines for mean and limits of agreement
# Create line data across the x-range
x_min, x_max = min(mean_values), max(mean_values)
margin = (x_max - x_min) * 0.05
x_range = [x_min - margin, x_max + margin]

# Mean line (bias)
chart.add(
    f"Mean Bias ({mean_diff:.1f})",
    [(x_range[0], mean_diff), (x_range[1], mean_diff)],
    stroke=True,
    dots_size=0,
    stroke_style={"width": 4},
)

# Upper limit of agreement
chart.add(
    f"Upper LoA (+1.96 SD: {upper_loa:.1f})",
    [(x_range[0], upper_loa), (x_range[1], upper_loa)],
    stroke=True,
    dots_size=0,
    stroke_style={"width": 3, "dasharray": "10, 5"},
)

# Lower limit of agreement
chart.add(
    f"Lower LoA (-1.96 SD: {lower_loa:.1f})",
    [(x_range[0], lower_loa), (x_range[1], lower_loa)],
    stroke=True,
    dots_size=0,
    stroke_style={"width": 3, "dasharray": "10, 5"},
)

# Save outputs
chart.render_to_file("plot.html")
chart.render_to_png("plot.png")
