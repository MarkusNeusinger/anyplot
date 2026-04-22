""" pyplots.ai
scatter-regression-lowess: Scatter Plot with LOWESS Regression
Library: bokeh 3.8.1 | Python 3.13.11
Quality: 92/100 | Created: 2025-12-30
"""

import numpy as np
from bokeh.io import export_png, save
from bokeh.models import ColumnDataSource
from bokeh.plotting import figure
from bokeh.resources import CDN
from statsmodels.nonparametric.smoothers_lowess import lowess


# Data: Simulate a complex non-linear relationship (e.g., temperature vs enzyme activity)
np.random.seed(42)
n = 200

# Create x values (temperature in Celsius)
x = np.linspace(10, 50, n) + np.random.normal(0, 1, n)
x = np.sort(x)

# Create y with complex non-linear relationship (enzyme activity %)
# Activity increases, peaks around 35°C, then decreases (typical enzyme behavior)
y_true = 20 + 60 * np.exp(-0.5 * ((x - 35) / 8) ** 2)  # Gaussian peak
y = y_true + np.random.normal(0, 5, n)  # Add noise

# Calculate LOWESS regression
lowess_result = lowess(y, x, frac=0.4)
x_lowess = lowess_result[:, 0]
y_lowess = lowess_result[:, 1]

# Create figure
p = figure(
    width=4800,
    height=2700,
    title="scatter-regression-lowess · bokeh · pyplots.ai",
    x_axis_label="Temperature (°C)",
    y_axis_label="Enzyme Activity (%)",
)

# Scatter points
source_scatter = ColumnDataSource(data={"x": x, "y": y})
p.scatter(x="x", y="y", source=source_scatter, size=18, color="#306998", alpha=0.6, legend_label="Data Points")

# LOWESS curve
source_lowess = ColumnDataSource(data={"x": x_lowess, "y": y_lowess})
p.line(x="x", y="y", source=source_lowess, line_width=5, color="#FFD43B", legend_label="LOWESS Fit")

# Styling - larger text for 4800x2700 canvas
p.title.text_font_size = "36pt"
p.xaxis.axis_label_text_font_size = "28pt"
p.yaxis.axis_label_text_font_size = "28pt"
p.xaxis.major_label_text_font_size = "22pt"
p.yaxis.major_label_text_font_size = "22pt"

# Grid styling
p.grid.grid_line_alpha = 0.3
p.grid.grid_line_dash = "dashed"

# Legend styling
p.legend.label_text_font_size = "22pt"
p.legend.location = "top_right"
p.legend.background_fill_alpha = 0.8

# Save outputs
export_png(p, filename="plot.png")
save(p, filename="plot.html", resources=CDN, title="scatter-regression-lowess")
