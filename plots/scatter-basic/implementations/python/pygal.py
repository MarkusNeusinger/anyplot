""" pyplots.ai
scatter-basic: Basic Scatter Plot
Library: pygal 3.1.0 | Python 3.14
Quality: 87/100 | Created: 2025-12-22
"""

import numpy as np
import pygal
from pygal.style import Style


# Data — study hours vs exam scores with realistic positive correlation
np.random.seed(42)
n = 115
study_hours = np.random.uniform(2, 14, n)
exam_scores = study_hours * 4.5 + np.random.normal(0, 5.5, n) + 25
exam_scores = np.clip(exam_scores, 15, 100)

# Add deliberate outliers showcasing scatter diversity (high/low performers)
outlier_hours = np.array([3.0, 12.5, 7.0, 11.0, 4.5])
outlier_scores = np.array([82.0, 42.0, 95.0, 48.0, 78.0])
study_hours = np.concatenate([study_hours, outlier_hours])
exam_scores = np.concatenate([exam_scores, outlier_scores])

# Compute trend line (linear regression) for data storytelling
coeffs = np.polyfit(study_hours, exam_scores, 1)
slope, intercept = coeffs
r = np.corrcoef(study_hours, exam_scores)[0, 1]
trend_x = np.linspace(study_hours.min(), study_hours.max(), 50)
trend_y = slope * trend_x + intercept

# Identify notable outliers for annotation
residuals = exam_scores - (slope * study_hours + intercept)
top_outlier_idx = int(np.argmax(residuals))
bottom_outlier_idx = int(np.argmin(residuals))

# Shared font family
font = "DejaVu Sans, Helvetica, Arial, sans-serif"

# Refined style for 4800x2700 px canvas — subtle, professional palette
custom_style = Style(
    background="white",
    plot_background="#f7f7f7",
    foreground="#2a2a2a",
    foreground_strong="#2a2a2a",
    foreground_subtle="#e0e0e0",
    guide_stroke_color="#e0e0e0",
    guide_stroke_dasharray="4, 4",
    colors=("#306998", "#d64541", "#e8a838"),
    font_family=font,
    title_font_family=font,
    title_font_size=56,
    label_font_size=42,
    major_label_font_size=38,
    legend_font_size=34,
    legend_font_family=font,
    value_font_size=28,
    tooltip_font_size=28,
    tooltip_font_family=font,
    opacity=0.65,
    opacity_hover=0.95,
    stroke_opacity=1,
    stroke_opacity_hover=1,
)

# Axis range tightened to data bounds for better canvas utilization
x_min, x_max = float(np.floor(study_hours.min())), float(np.ceil(study_hours.max()))
y_min = float(max(0, np.floor(exam_scores.min() / 5) * 5))
y_max = float(min(100, np.ceil(exam_scores.max() / 5) * 5 + 5))

# Create XY chart
chart = pygal.XY(
    width=4800,
    height=2700,
    style=custom_style,
    title="scatter-basic \u00b7 pygal \u00b7 pyplots.ai",
    x_title="Study Hours per Week (hrs)",
    y_title="Exam Score (%)",
    show_legend=True,
    legend_at_bottom=True,
    legend_at_bottom_columns=3,
    legend_box_size=24,
    stroke=False,
    dots_size=9,
    show_x_guides=True,
    show_y_guides=True,
    x_value_formatter=lambda x: f"{x:.0f}",
    value_formatter=lambda y: f"{y:.0f}%",
    margin_bottom=100,
    margin_left=60,
    margin_right=40,
    margin_top=50,
    x_label_rotation=0,
    truncate_legend=-1,
    range=(y_min, y_max),
    xrange=(x_min, x_max),
    x_labels_major_count=7,
    y_labels_major_count=9,
    print_values=False,
    print_zeroes=False,
    js=[],
)

# Add scatter data as list of (x, y) tuples
points = [(float(h), float(s)) for h, s in zip(study_hours, exam_scores, strict=True)]
chart.add(
    f"Students (n={len(points)})",
    points,
    stroke=False,
    formatter=lambda x: f"({x[0]:.1f} hrs, {x[1]:.0f}%)" if isinstance(x, (tuple, list)) else f"{x:.0f}",
)

# Add trend line — dashed stroke for visual contrast
trend_points = [(float(x), float(y)) for x, y in zip(trend_x, trend_y, strict=True)]
chart.add(
    f"Trend (r = {r:.2f})",
    trend_points,
    stroke=True,
    show_dots=False,
    stroke_style={"width": 14, "dasharray": "32, 14", "linecap": "round", "linejoin": "round"},
)

# Annotate notable outliers — pygal per-point metadata with label styling
oh = float(study_hours[top_outlier_idx])
os_ = float(exam_scores[top_outlier_idx])
bh = float(study_hours[bottom_outlier_idx])
bs = float(exam_scores[bottom_outlier_idx])
chart.add(
    "Outliers",
    [
        {"value": (oh, os_), "label": f"High performer ({oh:.0f}h \u2192 {os_:.0f}%)"},
        {"value": (bh, bs), "label": f"Low performer ({bh:.0f}h \u2192 {bs:.0f}%)"},
    ],
    stroke=False,
    dots_size=16,
    formatter=lambda x: f"{x[1]:.0f}%" if isinstance(x, (tuple, list)) else f"{x:.0f}",
)

# Save outputs — dual format leverages pygal's SVG-native + PNG capability
chart.render_to_png("plot.png")
chart.render_to_file("plot.html")
