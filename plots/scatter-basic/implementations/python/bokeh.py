""" anyplot.ai
scatter-basic: Basic Scatter Plot
Library: bokeh 3.9.0 | Python 3.14.4
Quality: 92/100 | Created: 2026-04-23
"""

import os

import numpy as np
from bokeh.io import export_png, output_file, save
from bokeh.models import Band, ColumnDataSource, HoverTool, Slope
from bokeh.plotting import figure


THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
BRAND = "#009E73"

# Data — study hours vs exam scores
np.random.seed(42)
n_points = 150
study_hours = np.random.uniform(1, 10, n_points)
exam_scores = study_hours * 7 + np.random.randn(n_points) * 6 + 25

# Natural outliers (test anxiety, gifted, under-performers)
exam_scores[5] = 38
exam_scores[22] = 92
exam_scores[47] = 30
exam_scores[71] = 95
exam_scores[88] = 42

exam_scores = np.clip(exam_scores, 15, 98)

# Linear regression for trend line and confidence band
slope_coef = np.polyfit(study_hours, exam_scores, 1)
predicted = np.polyval(slope_coef, study_hours)
residual_std = np.std(exam_scores - predicted)

sort_idx = np.argsort(study_hours)
x_sorted = study_hours[sort_idx]
y_pred_sorted = np.polyval(slope_coef, x_sorted)
band_source = ColumnDataSource(
    data={"x": x_sorted, "upper": y_pred_sorted + 1.5 * residual_std, "lower": y_pred_sorted - 1.5 * residual_std}
)

source = ColumnDataSource(data={"x": study_hours, "y": exam_scores})

p = figure(
    width=4800,
    height=2700,
    title="scatter-basic · bokeh · anyplot.ai",
    x_axis_label="Study Hours per Day (hrs)",
    y_axis_label="Exam Score (%)",
    toolbar_location=None,
    x_range=(0, 11),
    y_range=(12, 103),
)

# Confidence band — Bokeh-native Band glyph
band = Band(
    base="x",
    lower="lower",
    upper="upper",
    source=band_source,
    level="underlay",
    fill_alpha=0.15,
    fill_color=BRAND,
    line_width=0,
)
p.add_layout(band)

# Trend line via Slope model — Bokeh-specific annotation
trend = Slope(
    gradient=slope_coef[0],
    y_intercept=slope_coef[1],
    line_color=BRAND,
    line_width=5,
    line_alpha=0.55,
    line_dash="dashed",
)
p.add_layout(trend)

# Scatter points with white edge for definition in dense areas
scatter_renderer = p.scatter(
    x="x", y="y", source=source, size=32, color=BRAND, alpha=0.7, line_color="white", line_width=1
)

# HoverTool — Bokeh's distinctive interactive feature
hover = HoverTool(renderers=[scatter_renderer], tooltips=[("Study Hours", "@x{0.1} hrs"), ("Exam Score", "@y{0.0}%")])
p.add_tools(hover)

# Typography — explicitly sized for 4800×2700 canvas
p.title.text_font_size = "42pt"
p.title.text_color = INK
p.title.text_font_style = "bold"

p.xaxis.axis_label_text_font_size = "32pt"
p.yaxis.axis_label_text_font_size = "32pt"
p.xaxis.major_label_text_font_size = "24pt"
p.yaxis.major_label_text_font_size = "24pt"

# Theme-adaptive chrome
p.xaxis.axis_label_text_color = INK
p.yaxis.axis_label_text_color = INK
p.xaxis.major_label_text_color = INK_SOFT
p.yaxis.major_label_text_color = INK_SOFT
p.xaxis.axis_line_color = INK_SOFT
p.yaxis.axis_line_color = INK_SOFT
p.xaxis.major_tick_line_color = INK_SOFT
p.yaxis.major_tick_line_color = INK_SOFT
p.xaxis.minor_tick_line_color = None
p.yaxis.minor_tick_line_color = None

p.xgrid.grid_line_color = INK
p.ygrid.grid_line_color = INK
p.xgrid.grid_line_alpha = 0.10
p.ygrid.grid_line_alpha = 0.10
p.xgrid.grid_line_width = 2
p.ygrid.grid_line_width = 2

p.background_fill_color = PAGE_BG
p.border_fill_color = PAGE_BG
p.outline_line_color = None

p.xaxis.ticker.desired_num_ticks = 10
p.yaxis.ticker.desired_num_ticks = 8

export_png(p, filename=f"plot-{THEME}.png")
output_file(f"plot-{THEME}.html", title="scatter-basic · bokeh · anyplot.ai")
save(p)
