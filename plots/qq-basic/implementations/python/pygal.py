""" pyplots.ai
qq-basic: Basic Q-Q Plot
Library: pygal 3.1.0 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-23
"""

import math

import numpy as np
import pygal
from pygal.style import Style


# Data - sample with slight right skew to show deviation from normality
np.random.seed(42)
sample = np.concatenate(
    [
        np.random.normal(0, 1, 80),
        np.random.exponential(0.5, 20),  # Adds some right skew
    ]
)
sample = np.sort(sample)
n = len(sample)

# Calculate theoretical quantiles using Beasley-Springer-Moro algorithm
# Coefficients for the approximation
a = [
    -3.969683028665376e01,
    2.209460984245205e02,
    -2.759285104469687e02,
    1.383577518672690e02,
    -3.066479806614716e01,
    2.506628277459239e00,
]
b = [-5.447609879822406e01, 1.615858368580409e02, -1.556989798598866e02, 6.680131188771972e01, -1.328068155288572e01]
c = [
    -7.784894002430293e-03,
    -3.223964580411365e-01,
    -2.400758277161838e00,
    -2.549732539343734e00,
    4.374664141464968e00,
    2.938163982698783e00,
]
d = [7.784695709041462e-03, 3.224671290700398e-01, 2.445134137142996e00, 3.754408661907416e00]
p_low, p_high = 0.02425, 1 - 0.02425

probabilities = (np.arange(1, n + 1) - 0.5) / n
theoretical_quantiles = []
for p in probabilities:
    if p < p_low:
        q = math.sqrt(-2 * math.log(p))
        val = (((((c[0] * q + c[1]) * q + c[2]) * q + c[3]) * q + c[4]) * q + c[5]) / (
            (((d[0] * q + d[1]) * q + d[2]) * q + d[3]) * q + 1
        )
    elif p <= p_high:
        q = p - 0.5
        r = q * q
        val = ((((((a[0] * r + a[1]) * r + a[2]) * r + a[3]) * r + a[4]) * r + a[5]) * q) / (
            ((((b[0] * r + b[1]) * r + b[2]) * r + b[3]) * r + b[4]) * r + 1
        )
    else:
        q = math.sqrt(-2 * math.log(1 - p))
        val = -(((((c[0] * q + c[1]) * q + c[2]) * q + c[3]) * q + c[4]) * q + c[5]) / (
            (((d[0] * q + d[1]) * q + d[2]) * q + d[3]) * q + 1
        )
    theoretical_quantiles.append(val)
theoretical_quantiles = np.array(theoretical_quantiles)

# Determine axis range for reference line
min_val = min(theoretical_quantiles.min(), sample.min())
max_val = max(theoretical_quantiles.max(), sample.max())
margin = (max_val - min_val) * 0.1
line_min = min_val - margin
line_max = max_val + margin

# Custom style for 4800x2700 px
custom_style = Style(
    background="white",
    plot_background="white",
    foreground="#333",
    foreground_strong="#333",
    foreground_subtle="#666",
    colors=("#306998", "#888888"),  # Blue for sample points, gray for reference line
    title_font_size=72,
    label_font_size=48,
    major_label_font_size=42,
    legend_font_size=42,
    value_font_size=36,
    stroke_width=3,
)

# Create XY chart
chart = pygal.XY(
    width=4800,
    height=2700,
    style=custom_style,
    title="qq-basic · pygal · pyplots.ai",
    x_title="Theoretical Quantiles",
    y_title="Sample Quantiles",
    show_legend=True,
    legend_at_bottom=True,
    dots_size=12,
    stroke=False,
    show_x_guides=True,
    show_y_guides=True,
)

# Prepare Q-Q data points
qq_points = list(zip(theoretical_quantiles, sample, strict=True))
chart.add("Sample Data", qq_points)

# Add reference line (y = x)
reference_line = [(line_min, line_min), (line_max, line_max)]
chart.add("Reference (y=x)", reference_line, stroke=True, show_dots=False, dots_size=0)

# Save as PNG and HTML
chart.render_to_png("plot.png")
chart.render_to_file("plot.html")
