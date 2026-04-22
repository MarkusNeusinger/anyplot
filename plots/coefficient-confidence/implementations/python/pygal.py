""" pyplots.ai
coefficient-confidence: Coefficient Plot with Confidence Intervals
Library: pygal 3.1.0 | Python 3.13.11
Quality: 91/100 | Created: 2026-01-09
"""

import numpy as np
import pygal
from pygal.style import Style


# Data: Coefficients from a housing price regression model
np.random.seed(42)

# Variable names (predictors in housing price model)
variables = [
    "Square Footage",
    "Number of Bedrooms",
    "Number of Bathrooms",
    "Garage Size",
    "Lot Size (acres)",
    "Age of Home (years)",
    "Distance to City Center",
    "School Rating",
    "Crime Rate Index",
    "Property Tax Rate",
]

# Generate realistic coefficients (some significant, some not)
coefficients = np.array([0.45, 0.12, 0.28, 0.18, 0.35, -0.22, -0.15, 0.25, -0.08, -0.05])
std_errors = np.array([0.08, 0.09, 0.06, 0.05, 0.10, 0.07, 0.12, 0.08, 0.11, 0.09])

# Calculate 95% confidence intervals
ci_lower = coefficients - 1.96 * std_errors
ci_upper = coefficients + 1.96 * std_errors

# Determine significance (CI doesn't cross zero)
significant = (ci_lower > 0) | (ci_upper < 0)

# Sort by coefficient magnitude for easier comparison
sort_idx = np.argsort(coefficients)
variables = [variables[i] for i in sort_idx]
coefficients = coefficients[sort_idx]
ci_lower = ci_lower[sort_idx]
ci_upper = ci_upper[sort_idx]
significant = significant[sort_idx]

n_vars = len(variables)

# Custom style for pyplots.ai
# Colors: Blue for significant, Yellow for non-significant, Gray for zero line
custom_style = Style(
    background="white",
    plot_background="white",
    foreground="#333333",
    foreground_strong="#333333",
    foreground_subtle="#666666",
    colors=("#306998", "#FFD43B", "#999999"),  # Blue, Yellow, Gray
    title_font_size=72,
    label_font_size=48,
    major_label_font_size=42,
    legend_font_size=42,
    value_font_size=36,
    value_label_font_size=36,
    tooltip_font_size=36,
    stroke_width=5,
    font_family="sans-serif",
)

# Create XY chart for coefficient plot with confidence intervals
chart = pygal.XY(
    width=4800,
    height=2700,
    style=custom_style,
    title="coefficient-confidence · pygal · pyplots.ai",
    x_title="Coefficient Estimate (Standardized)",
    show_legend=True,
    legend_at_bottom=True,
    legend_at_bottom_columns=3,
    show_y_guides=True,
    show_x_guides=True,
    dots_size=20,
    stroke=False,
    xrange=(-0.6, 0.7),
    range=(0, n_vars + 1),
    margin=50,
    spacing=30,
    y_labels=[{"value": i + 1, "label": variables[i]} for i in range(n_vars)],
)

# Build data points for significant and non-significant coefficients
sig_points = []
nonsig_points = []

for i, (coef, sig) in enumerate(zip(coefficients, significant, strict=True)):
    y_pos = i + 1
    point = (coef, y_pos)
    if sig:
        sig_points.append(point)
    else:
        nonsig_points.append(point)

# Add series for coefficient points (Blue for significant first as primary color)
chart.add("Significant (p < 0.05)", sig_points)
chart.add("Not Significant", nonsig_points)

# Add vertical reference line at zero (null hypothesis threshold)
zero_line = [(0, 0), (0, n_vars + 1)]
chart.add("Zero Reference", zero_line, stroke=True, show_dots=False, stroke_style={"width": 3, "dasharray": "10,5"})

# Add confidence interval lines as separate series
# Match colors to the point colors (blue for sig, yellow for non-sig)
for i, (_coef, lower, upper, sig) in enumerate(zip(coefficients, ci_lower, ci_upper, significant, strict=True)):
    y_pos = i + 1
    ci_line = [(lower, y_pos), (upper, y_pos)]
    # Use matching color for CI line
    color = "#306998" if sig else "#FFD43B"
    chart.add(None, ci_line, stroke=True, show_dots=False, stroke_style={"width": 5}, color=color)

# Save as PNG and HTML
chart.render_to_png("plot.png")
chart.render_to_file("plot.html")
