""" pyplots.ai
line-pca-variance-cumulative: Cumulative Explained Variance for PCA Component Selection
Library: pygal 3.1.0 | Python 3.14.3
Quality: 89/100 | Created: 2026-02-17
"""

import numpy as np
import pygal
from pygal.style import Style


# Data - Realistic PCA variance ratios for a 13-feature dataset (Wine-like)
eigenvalues = np.array([4.73, 2.51, 1.45, 0.92, 0.85, 0.64, 0.55, 0.35, 0.29, 0.21, 0.17, 0.13, 0.08])
explained_variance_ratio = eigenvalues / eigenvalues.sum()
individual_variance = explained_variance_ratio * 100
cumulative_variance = np.cumsum(explained_variance_ratio) * 100
n_components = len(cumulative_variance)
component_labels = [str(i) for i in range(1, n_components + 1)]

# Detect elbow point: where slope drops below 35% of max slope
slopes = np.diff(cumulative_variance)
elbow_idx = int(np.argmax(slopes < slopes[0] * 0.35))

# Find threshold crossings
cross_90 = int(np.searchsorted(cumulative_variance, 90))
cross_95 = int(np.searchsorted(cumulative_variance, 95))

# Custom style - refined palette, colorblind-safe (blue + purple + teal + steel)
custom_style = Style(
    background="white",
    plot_background="#F7F9FC",
    foreground="#2C3E50",
    foreground_strong="#1A252F",
    foreground_subtle="#E0E4E8",
    colors=("#306998", "#8E44AD", "#0E8C6B", "#4682B4"),
    opacity=0.85,
    opacity_hover=1.0,
    stroke_opacity=1.0,
    stroke_opacity_hover=1.0,
    stroke_width=6,
    stroke_width_hover=8,
    dot_opacity=1.0,
    guide_stroke_color="#E0E4E8",
    guide_stroke_dasharray="2,6",
    major_guide_stroke_color="#C0C8D0",
    major_guide_stroke_dasharray="4,4",
    title_font_size=66,
    label_font_size=44,
    major_label_font_size=48,
    legend_font_size=40,
    value_font_size=44,
    tooltip_font_size=34,
    font_family="Helvetica, Arial, sans-serif",
    title_font_family="Helvetica, Arial, sans-serif",
    label_font_family="Helvetica, Arial, sans-serif",
    legend_font_family="Helvetica, Arial, sans-serif",
    value_font_family="Helvetica, Arial, sans-serif",
    major_label_font_family="Helvetica, Arial, sans-serif",
    value_label_font_size=40,
    transition="200ms",
)

# Chart with refined configuration
chart = pygal.Line(
    width=4800,
    height=2700,
    title="line-pca-variance-cumulative · pygal · pyplots.ai",
    x_title="Number of Components",
    y_title="Cumulative Explained Variance (%)",
    style=custom_style,
    show_dots=True,
    dots_size=12,
    show_only_major_dots=False,
    show_y_guides=True,
    show_x_guides=False,
    legend_at_bottom=True,
    legend_at_bottom_columns=4,
    legend_box_size=30,
    truncate_legend=-1,
    range=(0, 105),
    secondary_range=(0, 50),
    margin=30,
    margin_bottom=110,
    margin_left=150,
    margin_right=160,
    margin_top=50,
    print_values=True,
    print_values_position="top",
    value_formatter=lambda x: "",
    spacing=22,
    x_labels_major_count=13,
    show_minor_x_labels=False,
    tooltip_fancy_mode=True,
    tooltip_border_radius=10,
    interpolate="cubic",
    interpolation_precision=200,
)

# X-axis and Y-axis labels
chart.x_labels = component_labels

# Y-axis: key percentages with major labels at thresholds for emphasis
chart.y_labels = [0, 20, 40, 60, 80, 90, 95, 100]
chart.y_labels_major = [90, 95]
chart.show_minor_y_labels = True

# Annotation formatters for key data points - improved with clearer labels
elbow_pct = cumulative_variance[elbow_idx]
annotations = {
    elbow_idx: lambda x: f">> Elbow ({x:.0f}%)",
    cross_90: lambda x: f"← 90% threshold (n={cross_90 + 1})",
    cross_95: lambda x: f"← 95% threshold (n={cross_95 + 1})",
}

# Cumulative variance line with per-point annotations at key locations
cumulative_values = [
    {"value": round(v, 1), "formatter": annotations.get(i, lambda x: "")} for i, v in enumerate(cumulative_variance)
]

chart.add(
    "Cumulative Variance",
    cumulative_values,
    stroke_style={"width": 9, "linecap": "round", "linejoin": "round"},
    fill=True,
)

# 90% threshold line (dashed, purple - colorblind-safe vs blue)
chart.add(
    "90% Threshold",
    [{"value": 90, "formatter": lambda x: ""} for _ in range(n_components)],
    show_dots=False,
    fill=False,
    stroke_style={"width": 5, "dasharray": "24, 12", "linecap": "round"},
)

# 95% threshold line (dashed, teal - colorblind-safe vs both blue and purple)
chart.add(
    "95% Threshold",
    [{"value": 95, "formatter": lambda x: ""} for _ in range(n_components)],
    show_dots=False,
    fill=False,
    stroke_style={"width": 5, "dasharray": "10, 8", "linecap": "round"},
)

# Individual variance on secondary Y-axis (steel blue, visible stroke)
individual_values = [
    {"value": round(v, 1), "formatter": lambda x: f"{x:.1f}%" if x > 3 else ""} for v in individual_variance
]
chart.add(
    "Individual Variance (%)",
    individual_values,
    secondary=True,
    stroke_style={"width": 7, "linecap": "round", "linejoin": "round"},
    show_dots=True,
    dots_size=6,
    fill=False,
)

# Save
chart.render_to_png("plot.png")
