""" pyplots.ai
violin-split: Split Violin Plot
Library: pygal 3.1.0 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-26
"""

import numpy as np
import pygal
from pygal.style import Style


# Data - Patient recovery scores before/after treatment across clinics
np.random.seed(42)
categories = ["Clinic A", "Clinic B", "Clinic C", "Clinic D"]
split_groups = ["Before", "After"]

# Generate realistic before/after data with different improvements per clinic
data = {}
for cat in categories:
    data[cat] = {}
    if cat == "Clinic A":
        data[cat]["Before"] = np.random.normal(45, 12, 80)
        data[cat]["After"] = np.random.normal(72, 10, 80)
    elif cat == "Clinic B":
        data[cat]["Before"] = np.random.normal(50, 15, 80)
        data[cat]["After"] = np.random.normal(68, 12, 80)
    elif cat == "Clinic C":
        data[cat]["Before"] = np.random.normal(42, 10, 80)
        data[cat]["After"] = np.random.normal(78, 8, 80)
    else:  # Clinic D
        data[cat]["Before"] = np.random.normal(55, 18, 80)
        data[cat]["After"] = np.random.normal(65, 14, 80)

# Clip to realistic 0-100 range
for cat in categories:
    for group in split_groups:
        data[cat][group] = np.clip(data[cat][group], 10, 95)

# Colors for split groups
before_color = "#306998"  # Python Blue
after_color = "#FFD43B"  # Python Yellow
marker_color = "#333333"  # Dark gray for markers

# Custom style for 4800x2700 px canvas
custom_style = Style(
    background="white",
    plot_background="white",
    foreground="#333333",
    foreground_strong="#333333",
    foreground_subtle="#666666",
    guide_stroke_color="#e0e0e0",
    colors=(before_color,) * 4 + (after_color,) * 4 + (marker_color,) * 50,
    title_font_size=84,
    label_font_size=54,
    major_label_font_size=48,
    legend_font_size=48,
    value_font_size=36,
    opacity=0.7,
    opacity_hover=0.9,
)

# Create XY chart for split violin plot
chart = pygal.XY(
    width=4800,
    height=2700,
    style=custom_style,
    title="violin-split · pygal · pyplots.ai",
    x_title="Clinic",
    y_title="Recovery Score",
    show_legend=True,
    legend_at_bottom=True,
    legend_at_bottom_columns=2,
    stroke=True,
    fill=True,
    dots_size=0,
    show_x_guides=False,
    show_y_guides=True,
    range=(0, 100),
    xrange=(0, 5.5),
    margin=60,
)

# Parameters for violin shapes
violin_width = 0.38
n_points = 80


# KDE helper function
def compute_kde(values, y_range):
    """Compute Gaussian KDE using Silverman's rule."""
    n = len(values)
    std = np.std(values)
    iqr = np.percentile(values, 75) - np.percentile(values, 25)
    bandwidth = 0.9 * min(std, iqr / 1.34) * n ** (-0.2)

    density = np.zeros_like(y_range)
    for v in values:
        density += np.exp(-0.5 * ((y_range - v) / bandwidth) ** 2)
    density /= n * bandwidth * np.sqrt(2 * np.pi)
    return density


# Pre-compute all violin shapes and markers
before_violins = []
after_violins = []
before_markers = []
after_markers = []

for i, category in enumerate(categories):
    center_x = i + 1.25

    for group in split_groups:
        values = data[category][group]

        # Create range of y values for density
        y_min, y_max = values.min(), values.max()
        padding = (y_max - y_min) * 0.15
        y_range = np.linspace(y_min - padding, y_max + padding, n_points)

        # Compute KDE
        density = compute_kde(values, y_range)

        # Normalize density to desired width
        density = density / density.max() * violin_width

        # Compute quartile statistics
        median = float(np.median(values))
        q1 = float(np.percentile(values, 25))
        q3 = float(np.percentile(values, 75))

        # Create half-violin shape (split violin - each group on one side)
        if group == "Before":
            # Left half - density extends to the left
            half_points = [(center_x - d, y) for y, d in zip(y_range, density, strict=True)]
            half_points = [(center_x, y_range[0])] + half_points + [(center_x, y_range[-1]), (center_x, y_range[0])]
            before_violins.append(half_points)
            before_markers.append((center_x, median, q1, q3, -0.08))
        else:
            # Right half - density extends to the right
            half_points = [(center_x + d, y) for y, d in zip(y_range, density, strict=True)]
            half_points = [(center_x, y_range[0])] + half_points + [(center_x, y_range[-1]), (center_x, y_range[0])]
            after_violins.append(half_points)
            after_markers.append((center_x, median, q1, q3, 0.08))

# Add all "Before" violins first (blue, with legend entry for first one only)
for i, violin in enumerate(before_violins):
    label = "Before" if i == 0 else None
    chart.add(label, violin, show_dots=False)

# Add all "After" violins (yellow, with legend entry for first one only)
for i, violin in enumerate(after_violins):
    label = "After" if i == 0 else None
    chart.add(label, violin, show_dots=False)

# Add quartile markers for "Before" group (no legend entries)
marker_width = 0.04
for center_x, median, q1, q3, offset in before_markers:
    # IQR line (thin vertical line)
    iqr_line = [(center_x + offset, q1), (center_x + offset, q3)]
    chart.add(None, iqr_line, stroke=True, fill=False, show_dots=False, stroke_style={"width": 8})
    # Median marker (small horizontal line)
    median_line = [(center_x + offset - marker_width, median), (center_x + offset + marker_width, median)]
    chart.add(None, median_line, stroke=True, fill=False, show_dots=False, stroke_style={"width": 12})

# Add quartile markers for "After" group (no legend entries)
for center_x, median, q1, q3, offset in after_markers:
    # IQR line
    iqr_line = [(center_x + offset, q1), (center_x + offset, q3)]
    chart.add(None, iqr_line, stroke=True, fill=False, show_dots=False, stroke_style={"width": 8})
    # Median marker
    median_line = [(center_x + offset - marker_width, median), (center_x + offset + marker_width, median)]
    chart.add(None, median_line, stroke=True, fill=False, show_dots=False, stroke_style={"width": 12})

# X-axis labels for categories
chart.x_labels = [
    {"value": 0, "label": ""},
    {"value": 1.25, "label": "Clinic A"},
    {"value": 2.25, "label": "Clinic B"},
    {"value": 3.25, "label": "Clinic C"},
    {"value": 4.25, "label": "Clinic D"},
    {"value": 5.5, "label": ""},
]

# Save outputs
chart.render_to_file("plot.html")
chart.render_to_png("plot.png")
