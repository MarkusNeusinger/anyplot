""" pyplots.ai
residual-plot: Residual Plot
Library: bokeh 3.8.1 | Python 3.13.11
Quality: 92/100 | Created: 2025-12-26
"""

import numpy as np
from bokeh.io import export_png, save
from bokeh.models import Band, ColumnDataSource, Label, Span
from bokeh.plotting import figure
from bokeh.resources import CDN


# Data - Linear regression example with realistic housing price prediction
np.random.seed(42)
n_points = 150

# Generate fitted values (predicted house prices in $1000s)
y_pred = np.linspace(150, 450, n_points) + np.random.randn(n_points) * 20

# Generate residuals with some heteroscedasticity pattern for demonstration
# Most residuals near zero, some outliers
base_residuals = np.random.randn(n_points) * 25
# Add a few outliers beyond 2 standard deviations
outlier_indices = [10, 45, 89, 120, 140]
base_residuals[outlier_indices] = np.array([62, -68, 58, -65, 70])

residuals = base_residuals
y_true = y_pred + residuals

# Calculate statistics for reference bands
residual_std = np.std(residuals)
upper_band = 2 * residual_std
lower_band = -2 * residual_std

# Identify outliers (beyond ±2 standard deviations)
is_outlier = np.abs(residuals) > 2 * residual_std

# Prepare data sources
source_normal = ColumnDataSource(data={"x": y_pred[~is_outlier], "y": residuals[~is_outlier]})

source_outliers = ColumnDataSource(data={"x": y_pred[is_outlier], "y": residuals[is_outlier]})

# Band data for ±2 SD region
band_source = ColumnDataSource(
    data={
        "x": np.array([min(y_pred) - 10, max(y_pred) + 10]),
        "lower": np.array([lower_band, lower_band]),
        "upper": np.array([upper_band, upper_band]),
    }
)

# Create figure (4800x2700 for 16:9)
p = figure(
    width=4800,
    height=2700,
    title="residual-plot · bokeh · pyplots.ai",
    x_axis_label="Fitted Values (Predicted Price in $1000s)",
    y_axis_label="Residuals (Observed - Predicted)",
    tools="pan,wheel_zoom,box_zoom,reset,save",
    x_range=(min(y_pred) - 20, max(y_pred) + 20),
    y_range=(min(residuals) - 20, max(residuals) + 20),
)

# Add ±2 SD band (light gray background)
band = Band(
    base="x", lower="lower", upper="upper", source=band_source, fill_alpha=0.15, fill_color="#888888", line_width=0
)
p.add_layout(band)

# Add horizontal reference line at y=0
zero_line = Span(location=0, dimension="width", line_color="#306998", line_width=3, line_dash="solid")
p.add_layout(zero_line)

# Add dashed lines at ±2 SD boundaries
upper_line = Span(location=upper_band, dimension="width", line_color="#666666", line_width=2, line_dash="dashed")
lower_line = Span(location=lower_band, dimension="width", line_color="#666666", line_width=2, line_dash="dashed")
p.add_layout(upper_line)
p.add_layout(lower_line)

# Plot normal points (Python Blue)
p.scatter("x", "y", source=source_normal, size=18, color="#306998", alpha=0.7, legend_label="Residuals")

# Plot outliers (Python Yellow)
p.scatter(
    "x",
    "y",
    source=source_outliers,
    size=22,
    color="#FFD43B",
    alpha=0.9,
    line_color="#306998",
    line_width=2,
    legend_label="Outliers (>2 SD)",
)

# Add labels for ±2 SD bands (positioned inside the plot area)
label_upper = Label(
    x=min(y_pred) + 10,
    y=upper_band + 3,
    text="+2 SD",
    text_font_size="16pt",
    text_color="#555555",
    text_font_style="italic",
)
label_lower = Label(
    x=min(y_pred) + 10,
    y=lower_band + 3,
    text="-2 SD",
    text_font_size="16pt",
    text_color="#555555",
    text_font_style="italic",
)
p.add_layout(label_upper)
p.add_layout(label_lower)

# Styling - Text sizes for 4800x2700 canvas
p.title.text_font_size = "32pt"
p.title.text_color = "#333333"
p.xaxis.axis_label_text_font_size = "24pt"
p.yaxis.axis_label_text_font_size = "24pt"
p.xaxis.major_label_text_font_size = "18pt"
p.yaxis.major_label_text_font_size = "18pt"

# Grid styling
p.grid.grid_line_alpha = 0.3
p.grid.grid_line_dash = [6, 4]

# Legend styling
p.legend.location = "top_left"
p.legend.label_text_font_size = "18pt"
p.legend.background_fill_alpha = 0.8
p.legend.border_line_color = "#cccccc"
p.legend.padding = 15
p.legend.spacing = 10

# Axis styling
p.xaxis.axis_line_width = 2
p.yaxis.axis_line_width = 2
p.xaxis.axis_line_color = "#666666"
p.yaxis.axis_line_color = "#666666"

# Background
p.background_fill_color = "#fafafa"
p.border_fill_color = "#ffffff"

# Save outputs
export_png(p, filename="plot.png")

# Also save HTML for interactive version
save(p, filename="plot.html", resources=CDN, title="Residual Plot")
