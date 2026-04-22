""" pyplots.ai
histogram-returns-distribution: Returns Distribution Histogram
Library: pygal 3.1.0 | Python 3.13.11
Quality: 58/100 | Created: 2026-01-16
"""

import numpy as np
import pygal
from pygal.style import Style


# Data - Generate 252 daily returns (1 year of trading data)
np.random.seed(42)
returns = np.random.normal(loc=0.0005, scale=0.015, size=252) * 100  # Convert to percentage

# Calculate statistics
n = len(returns)
mean_return = np.mean(returns)
std_return = np.std(returns, ddof=1)

# Skewness calculation
skewness = (n / ((n - 1) * (n - 2))) * np.sum(((returns - mean_return) / std_return) ** 3)

# Kurtosis calculation (excess kurtosis)
kurtosis = ((n * (n + 1)) / ((n - 1) * (n - 2) * (n - 3))) * np.sum(((returns - mean_return) / std_return) ** 4) - (
    3 * (n - 1) ** 2
) / ((n - 2) * (n - 3))

# Create histogram bins with density normalization
n_bins = 25
counts, bin_edges = np.histogram(returns, bins=n_bins, density=True)

# Identify tail regions (beyond 2 standard deviations)
lower_tail = mean_return - 2 * std_return
upper_tail = mean_return + 2 * std_return

# Generate normal distribution curve points
x_curve = np.linspace(returns.min() - 0.5, returns.max() + 0.5, 150)
normal_pdf = (1 / (std_return * np.sqrt(2 * np.pi))) * np.exp(-0.5 * ((x_curve - mean_return) / std_return) ** 2)

# Custom style for 4800x2700 px canvas with larger legend
custom_style = Style(
    background="white",
    plot_background="white",
    foreground="#333",
    foreground_strong="#333",
    foreground_subtle="#666",
    colors=("#306998", "#C0392B", "#1E8449"),  # Blue for normal, red for tails, green for curve
    title_font_size=64,
    label_font_size=44,
    major_label_font_size=40,
    legend_font_size=44,
    value_font_size=32,
    stroke_width=5,
    opacity=0.85,
    opacity_hover=1.0,
)

# Create stats subtitle
stats_text = f"Mean: {mean_return:.3f}% | Std: {std_return:.3f}% | Skew: {skewness:.2f} | Kurt: {kurtosis:.2f}"

# Use XY chart to render both histogram bars and normal curve on same y-axis
chart = pygal.XY(
    width=4800,
    height=2700,
    style=custom_style,
    title=f"histogram-returns-distribution · pygal · pyplots.ai\n{stats_text}",
    x_title="Returns (%)",
    y_title="Probability Density",
    show_legend=True,
    legend_at_bottom=True,
    legend_at_bottom_columns=3,
    legend_box_size=32,
    show_y_guides=True,
    show_x_guides=False,
    margin_bottom=200,
    margin_left=120,
    margin_right=80,
    print_values=False,
    explicit_size=True,
    show_dots=False,
    stroke=True,
    fill=True,
)

# Build histogram as step polygons for XY chart
# Each bar is rendered as a box shape for filled step histogram effect
normal_bars_xy = []
tail_bars_xy = []

for i, count in enumerate(counts):
    left = float(bin_edges[i])
    right = float(bin_edges[i + 1])
    center = (left + right) / 2
    height = float(count)

    box = [(left, 0), (left, height), (right, height), (right, 0)]

    if center < lower_tail or center > upper_tail:
        tail_bars_xy.extend(box)
    else:
        normal_bars_xy.extend(box)

# Add histogram series as filled areas
chart.add("Returns (within 2σ)", normal_bars_xy, fill=True, stroke_style={"width": 2})
chart.add("Tails (beyond ±2σ)", tail_bars_xy, fill=True, stroke_style={"width": 2})

# Add normal distribution curve - not filled, just line
curve_data = [(float(x), float(y)) for x, y in zip(x_curve, normal_pdf, strict=True)]
chart.add("Normal Distribution", curve_data, fill=False, stroke_style={"width": 6})

# Save outputs
chart.render_to_file("plot.html")
chart.render_to_png("plot.png")
