""" pyplots.ai
scatter-basic: Basic Scatter Plot
Library: bokeh 3.8.2 | Python 3.14
Quality: 94/100 | Created: 2025-12-22
"""

import numpy as np
from bokeh.io import export_png
from bokeh.models import Band, ColumnDataSource, Label, Slope
from bokeh.plotting import figure


# Data - Study hours vs exam scores (realistic scenario)
np.random.seed(42)
n_points = 100
study_hours = np.random.uniform(1, 10, n_points)
# Base relationship: ~7 points per hour + baseline of 25
exam_scores = study_hours * 7 + np.random.randn(n_points) * 6 + 25

# Add a few natural outliers (students who over/under-performed)
exam_scores[5] = 38  # High study hours, low score (test anxiety)
exam_scores[22] = 92  # Moderate hours, exceptional score (gifted)
exam_scores[47] = 30  # Moderate hours, very low score
exam_scores[71] = 95  # High hours, top performer
exam_scores[88] = 42  # Above-average hours, poor result

# Soft clipping to realistic range (no hard ceiling at 100)
exam_scores = np.clip(exam_scores, 15, 98)

# Linear regression for trend line and R²
slope = np.polyfit(study_hours, exam_scores, 1)
predicted = np.polyval(slope, study_hours)
ss_res = np.sum((exam_scores - predicted) ** 2)
ss_tot = np.sum((exam_scores - np.mean(exam_scores)) ** 2)
r_squared = 1 - ss_res / ss_tot

# Confidence band data (sorted for Band glyph)
sort_idx = np.argsort(study_hours)
x_sorted = study_hours[sort_idx]
y_pred_sorted = np.polyval(slope, x_sorted)
residual_std = np.std(exam_scores - predicted)
band_source = ColumnDataSource(
    data={
        "x": x_sorted,
        "y_pred": y_pred_sorted,
        "upper": y_pred_sorted + 1.5 * residual_std,
        "lower": y_pred_sorted - 1.5 * residual_std,
    }
)

# Create ColumnDataSource
source = ColumnDataSource(data={"study_hours": study_hours, "exam_scores": exam_scores})

# Create figure with axis labels in kwargs (idiomatic Bokeh)
p = figure(
    width=4800,
    height=2700,
    title="scatter-basic · bokeh · pyplots.ai",
    x_axis_label="Study Hours (hrs)",
    y_axis_label="Exam Score (%)",
    toolbar_location=None,
    x_range=(0, 11.5),
    y_range=(10, 105),
)

# Confidence band (distinctive Bokeh Band glyph - not easily replicated elsewhere)
band = Band(
    base="x",
    lower="lower",
    upper="upper",
    source=band_source,
    level="underlay",
    fill_alpha=0.12,
    fill_color="#306998",
    line_width=0,
)
p.add_layout(band)

# Trend line using Slope model (Bokeh-specific annotation)
trend = Slope(
    gradient=slope[0], y_intercept=slope[1], line_color="#306998", line_width=4, line_alpha=0.6, line_dash="dashed"
)
p.add_layout(trend)

# Scatter points with white edge for definition
p.scatter(
    x="study_hours",
    y="exam_scores",
    source=source,
    size=45,
    color="#306998",
    alpha=0.7,
    line_color="white",
    line_width=2,
)

# R² annotation using Label model (Bokeh-native annotation)
r2_label = Label(
    x=0.5,
    y=97,
    text=f"R² = {r_squared:.3f}",
    text_font_size="42pt",
    text_color="#306998",
    text_alpha=0.8,
    text_font_style="italic",
)
p.add_layout(r2_label)

# Subtitle annotation for storytelling context
subtitle = Label(
    x=0.5,
    y=90,
    text="Positive correlation with natural outliers — shaded region shows ±1.5σ",
    text_font_size="36pt",
    text_color="#666666",
    text_alpha=0.7,
)
p.add_layout(subtitle)

# Title styling
p.title.text_font_size = "72pt"
p.title.text_color = "#333333"

# Axis label styling (scaled for 4800x2700 canvas)
p.xaxis.axis_label_text_font_size = "48pt"
p.yaxis.axis_label_text_font_size = "48pt"
p.xaxis.major_label_text_font_size = "36pt"
p.yaxis.major_label_text_font_size = "36pt"
p.xaxis.axis_label_text_color = "#444444"
p.yaxis.axis_label_text_color = "#444444"
p.xaxis.major_label_text_color = "#555555"
p.yaxis.major_label_text_color = "#555555"

# Remove axis lines and ticks for cleaner look
p.xaxis.axis_line_color = None
p.yaxis.axis_line_color = None
p.xaxis.major_tick_line_color = None
p.yaxis.major_tick_line_color = None
p.xaxis.minor_tick_line_color = None
p.yaxis.minor_tick_line_color = None

# Subtle grid styling
p.grid.grid_line_alpha = 0.15
p.grid.grid_line_width = 2
p.grid.grid_line_color = "#888888"

# Background and border refinement
p.background_fill_color = "#FAFAFA"
p.border_fill_color = "white"
p.outline_line_color = None

# Tick formatting for clean numbers
p.xaxis.ticker.desired_num_ticks = 10
p.yaxis.ticker.desired_num_ticks = 8

# Save as PNG
export_png(p, filename="plot.png")
