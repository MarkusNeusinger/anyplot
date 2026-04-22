""" pyplots.ai
violin-basic: Basic Violin Plot
Library: pygal 3.1.0 | Python 3.14.3
Quality: 85/100 | Updated: 2026-02-21
"""

import numpy as np
import pygal
from pygal.style import Style


# Data - Test scores across 4 class groups with distinct distribution shapes
np.random.seed(42)
data = {
    "Honors": np.clip(np.random.normal(88, 6, 200), 50, 100),
    "Standard": np.clip(60 + np.random.gamma(3.5, 4, 200), 40, 100),
    "Remedial": np.clip(np.random.normal(62, 8, 200), 30, 100),
    "Advanced": np.clip(np.concatenate([np.random.normal(75, 6, 120), np.random.normal(93, 4, 80)]), 45, 100),
}

# Colors: 3 series per violin (fill, IQR fill, median line)
# Purple replaces green for deuteranopia accessibility; gold emphasizes bimodal Advanced
violin_colors = ["#306998", "#E8875B", "#8B6FBF", "#D4A017"]
iqr_colors = ["#1d3f5c", "#a35a38", "#5A3F82", "#8a6a10"]
median_color = "#FFFFFF"
palette = []
for vc, ic in zip(violin_colors, iqr_colors, strict=True):
    palette.extend([vc, ic, median_color])

custom_style = Style(
    background="white",
    plot_background="white",
    foreground="#555555",
    foreground_strong="#333333",
    foreground_subtle="#e0e0e0",
    colors=tuple(palette),
    title_font_size=72,
    label_font_size=48,
    major_label_font_size=42,
    legend_font_size=36,
    value_font_size=36,
    opacity=0.78,
    opacity_hover=0.92,
    transition="200ms ease-in",
)

# Create XY chart for violin plot (pygal has no native violin)
chart = pygal.XY(
    width=4800,
    height=2700,
    style=custom_style,
    title="violin-basic · pygal · pyplots.ai",
    x_title="Class Group",
    y_title="Test Score (%)",
    show_legend=False,
    stroke=True,
    fill=True,
    dots_size=0,
    show_x_guides=False,
    show_y_guides=True,
    range=(33, 103),
    xrange=(0, 5.0),
    margin=50,
    value_formatter=lambda x: f"{x:.0f}%",
    x_value_formatter=lambda x: "",
    tooltip_border_radius=10,
    tooltip_fancy_mode=True,
    human_readable=True,
    pretty_print=True,
)

# Violin widths — Advanced is wider to visually highlight its bimodal shape
base_width = 0.38
widths = {"Honors": base_width, "Standard": base_width, "Remedial": base_width, "Advanced": 0.46}
n_points = 100

# Build violins with quartile markers and median lines
for i, (category, values) in enumerate(data.items()):
    center_x = i + 1.0
    violin_width = widths[category]

    # KDE using Silverman's rule
    n = len(values)
    std = np.std(values)
    iqr_val = np.percentile(values, 75) - np.percentile(values, 25)
    bandwidth = 0.9 * min(std, iqr_val / 1.34) * n ** (-0.2)

    # Y values for density estimation
    y_min, y_max = values.min(), values.max()
    y_range = np.linspace(y_min - 2, y_max + 2, n_points)

    # Gaussian kernel density estimation
    density = np.zeros_like(y_range)
    for v in values:
        density += np.exp(-0.5 * ((y_range - v) / bandwidth) ** 2)
    density /= n * bandwidth * np.sqrt(2 * np.pi)

    # Normalize density to desired width
    density = density / density.max() * violin_width

    # Mirrored violin shape with tooltip showing statistics
    median_val = float(np.median(values))
    q1 = float(np.percentile(values, 25))
    q3 = float(np.percentile(values, 75))
    tooltip = f"{category} — Median: {median_val:.1f}%, Q1: {q1:.1f}%, Q3: {q3:.1f}%"

    left_points = [(center_x - d, y) for y, d in zip(y_range, density, strict=True)]
    right_points = [(center_x + d, y) for y, d in zip(y_range[::-1], density[::-1], strict=True)]
    violin_points = left_points + right_points + [left_points[0]]
    chart.add(category, violin_points, formatter=lambda x, t=tooltip: t, stroke_style={"width": 2})

    # Quartile markers — filled box in darker shade for clear visibility
    box_w = 0.16
    quartile_box = [
        (center_x - box_w, q1),
        (center_x - box_w, q3),
        (center_x + box_w, q3),
        (center_x + box_w, q1),
        (center_x - box_w, q1),
    ]
    chart.add(None, quartile_box, stroke=True, fill=True, show_dots=False, stroke_style={"width": 5})

    # Median line — thick white for high contrast against dark IQR box
    median_line = [(center_x - box_w * 1.1, median_val), (center_x + box_w * 1.1, median_val)]
    chart.add(None, median_line, stroke=True, fill=False, show_dots=False, stroke_style={"width": 18})

# X-axis labels at violin positions
chart.x_labels = ["", "Honors", "Standard", "Remedial", "Advanced", ""]
chart.x_labels_major_count = 4

# Save
chart.render_to_file("plot.html")
chart.render_to_png("plot.png")
