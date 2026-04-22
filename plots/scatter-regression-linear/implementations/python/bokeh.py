""" pyplots.ai
scatter-regression-linear: Scatter Plot with Linear Regression
Library: bokeh 3.8.1 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-24
"""

import numpy as np
from bokeh.io import export_png
from bokeh.models import Band, ColumnDataSource, Label
from bokeh.plotting import figure


# Data - Study hours vs exam scores
np.random.seed(42)
n_points = 80
x = np.random.uniform(1, 10, n_points)  # Study hours
noise = np.random.normal(0, 8, n_points)
y = 45 + 5 * x + noise  # Exam scores (base 45, +5 per hour studied)

# Linear regression calculation
slope, intercept = np.polyfit(x, y, 1)
y_pred = slope * x + intercept

# Calculate R-squared
ss_res = np.sum((y - y_pred) ** 2)
ss_tot = np.sum((y - np.mean(y)) ** 2)
r_squared = 1 - (ss_res / ss_tot)

# Calculate 95% confidence interval
n = len(x)
x_mean = np.mean(x)
se = np.sqrt(ss_res / (n - 2))
t_value = 1.99  # t-value for 95% CI with ~78 degrees of freedom

# Create sorted x values for smooth regression line and confidence band
x_line = np.linspace(x.min(), x.max(), 100)
y_line = slope * x_line + intercept

# Standard error of prediction for confidence interval
se_y = se * np.sqrt(1 / n + (x_line - x_mean) ** 2 / np.sum((x - x_mean) ** 2))
ci_upper = y_line + t_value * se_y
ci_lower = y_line - t_value * se_y

# Create figure
p = figure(
    width=4800,
    height=2700,
    title="scatter-regression-linear · bokeh · pyplots.ai",
    x_axis_label="Study Hours",
    y_axis_label="Exam Score (%)",
)

# Create data sources
scatter_source = ColumnDataSource(data={"x": x, "y": y})
line_source = ColumnDataSource(data={"x": x_line, "y": y_line})
band_source = ColumnDataSource(data={"x": x_line, "lower": ci_lower, "upper": ci_upper})

# Add confidence interval band
band = Band(
    base="x",
    lower="lower",
    upper="upper",
    source=band_source,
    fill_color="#306998",
    fill_alpha=0.2,
    line_color="#306998",
    line_alpha=0.3,
    line_width=1,
)
p.add_layout(band)

# Add regression line
p.line("x", "y", source=line_source, line_color="#FFD43B", line_width=5, legend_label="Linear Regression")

# Add scatter points
p.scatter("x", "y", source=scatter_source, size=18, color="#306998", alpha=0.65, legend_label="Data Points")

# Add R² annotation
r2_text = f"R² = {r_squared:.3f}"
equation_text = f"y = {slope:.2f}x + {intercept:.2f}"
annotation = Label(
    x=1.5,
    y=92,
    text=f"{equation_text}\n{r2_text}",
    text_font_size="24pt",
    text_color="#306998",
    background_fill_color="white",
    background_fill_alpha=0.8,
)
p.add_layout(annotation)

# Styling
p.title.text_font_size = "32pt"
p.xaxis.axis_label_text_font_size = "24pt"
p.yaxis.axis_label_text_font_size = "24pt"
p.xaxis.major_label_text_font_size = "18pt"
p.yaxis.major_label_text_font_size = "18pt"

p.legend.label_text_font_size = "18pt"
p.legend.location = "bottom_right"
p.legend.background_fill_alpha = 0.8

p.xgrid.grid_line_alpha = 0.3
p.ygrid.grid_line_alpha = 0.3

# Save
export_png(p, filename="plot.png")
