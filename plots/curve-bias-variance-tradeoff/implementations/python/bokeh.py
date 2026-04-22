""" pyplots.ai
curve-bias-variance-tradeoff: Bias-Variance Tradeoff Curve
Library: bokeh 3.8.2 | Python 3.13.11
Quality: 93/100 | Created: 2026-01-26
"""

import numpy as np
from bokeh.io import export_png
from bokeh.models import BoxAnnotation, ColumnDataSource, Label, Span
from bokeh.plotting import figure


# Data - theoretical curves for bias-variance tradeoff
np.random.seed(42)
complexity = np.linspace(0.1, 10, 100)

# Bias squared: decreases with complexity (starts high, approaches asymptote)
bias_squared = 4.0 / (1 + complexity) ** 1.2

# Variance: increases with complexity
variance = 0.15 * complexity**1.3

# Irreducible error: constant noise floor
irreducible_error = np.full_like(complexity, 0.5)

# Total error: sum of all components (U-shaped)
total_error = bias_squared + variance + irreducible_error

# Find optimal complexity point (minimum total error)
optimal_idx = np.argmin(total_error)
optimal_complexity = complexity[optimal_idx]
optimal_error = total_error[optimal_idx]

# Create ColumnDataSource
source = ColumnDataSource(
    data={
        "complexity": complexity,
        "bias_squared": bias_squared,
        "variance": variance,
        "irreducible_error": irreducible_error,
        "total_error": total_error,
    }
)

# Create figure
p = figure(
    width=4800,
    height=2700,
    title="curve-bias-variance-tradeoff · bokeh · pyplots.ai",
    x_axis_label="Model Complexity",
    y_axis_label="Prediction Error",
    x_range=(0, 10.5),
    y_range=(0, 5.5),
)

# Add shaded regions for underfitting and overfitting zones
underfitting_zone = BoxAnnotation(left=0, right=optimal_complexity, fill_alpha=0.08, fill_color="#306998")
overfitting_zone = BoxAnnotation(left=optimal_complexity, right=11, fill_alpha=0.08, fill_color="#FFD43B")
p.add_layout(underfitting_zone)
p.add_layout(overfitting_zone)

# Plot curves with distinct colors and styles
p.line(
    "complexity",
    "bias_squared",
    source=source,
    line_width=5,
    line_color="#306998",
    line_dash="solid",
    legend_label="Bias²",
)
p.line(
    "complexity",
    "variance",
    source=source,
    line_width=5,
    line_color="#FFD43B",
    line_dash="solid",
    legend_label="Variance",
)
p.line(
    "complexity",
    "irreducible_error",
    source=source,
    line_width=4,
    line_color="#888888",
    line_dash="dashed",
    legend_label="Irreducible Error",
)
p.line(
    "complexity",
    "total_error",
    source=source,
    line_width=6,
    line_color="#E74C3C",
    line_dash="solid",
    legend_label="Total Error",
)

# Mark optimal complexity point with vertical line
optimal_line = Span(
    location=optimal_complexity, dimension="height", line_color="#2ECC71", line_width=4, line_dash="dashed"
)
p.add_layout(optimal_line)

# Add marker at optimal point
p.scatter(
    [optimal_complexity], [optimal_error], size=25, color="#2ECC71", marker="circle", line_color="white", line_width=3
)

# Add annotations for curves
label_bias = Label(x=1.0, y=2.8, text="Bias²", text_font_size="28pt", text_color="#306998", text_font_style="bold")
label_variance = Label(
    x=8.2, y=2.5, text="Variance", text_font_size="28pt", text_color="#B8860B", text_font_style="bold"
)
label_irreducible = Label(
    x=7.0, y=0.7, text="Irreducible Error", text_font_size="22pt", text_color="#666666", text_font_style="italic"
)
label_total = Label(
    x=6.8, y=3.8, text="Total Error", text_font_size="28pt", text_color="#E74C3C", text_font_style="bold"
)
p.add_layout(label_bias)
p.add_layout(label_variance)
p.add_layout(label_irreducible)
p.add_layout(label_total)

# Add optimal point annotation
label_optimal = Label(
    x=optimal_complexity + 0.3,
    y=optimal_error + 0.35,
    text="Optimal Complexity",
    text_font_size="22pt",
    text_color="#2ECC71",
    text_font_style="bold",
)
p.add_layout(label_optimal)

# Add formula annotation
label_formula = Label(
    x=5.2,
    y=5.0,
    text="Total Error = Bias² + Variance + Irreducible Error",
    text_font_size="26pt",
    text_color="#333333",
    text_font_style="italic",
)
p.add_layout(label_formula)

# Add zone labels
label_underfit = Label(
    x=0.6, y=4.7, text="Underfitting", text_font_size="22pt", text_color="#306998", text_align="left"
)
label_underfit2 = Label(
    x=0.6, y=4.35, text="(High Bias)", text_font_size="18pt", text_color="#306998", text_align="left"
)
label_overfit = Label(x=8.0, y=4.7, text="Overfitting", text_font_size="22pt", text_color="#B8860B", text_align="left")
label_overfit2 = Label(
    x=8.0, y=4.35, text="(High Variance)", text_font_size="18pt", text_color="#B8860B", text_align="left"
)
p.add_layout(label_underfit)
p.add_layout(label_underfit2)
p.add_layout(label_overfit)
p.add_layout(label_overfit2)

# Style the plot
p.title.text_font_size = "36pt"
p.title.text_font_style = "bold"
p.xaxis.axis_label_text_font_size = "28pt"
p.yaxis.axis_label_text_font_size = "28pt"
p.xaxis.major_label_text_font_size = "20pt"
p.yaxis.major_label_text_font_size = "20pt"

# Legend styling
p.legend.location = "top_right"
p.legend.label_text_font_size = "20pt"
p.legend.background_fill_alpha = 0.9
p.legend.border_line_width = 2
p.legend.spacing = 12
p.legend.padding = 20

# Grid styling
p.grid.grid_line_alpha = 0.3
p.grid.grid_line_dash = "dashed"

# Background
p.background_fill_color = "#FAFAFA"
p.border_fill_color = "#FFFFFF"

# Save
export_png(p, filename="plot.png")
