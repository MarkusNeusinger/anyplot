""" pyplots.ai
scatter-regression-polynomial: Scatter Plot with Polynomial Regression
Library: bokeh 3.8.1 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-25
"""

import numpy as np
from bokeh.io import export_png, output_file, save
from bokeh.models import ColumnDataSource, Label
from bokeh.plotting import figure


# Data - Manufacturing efficiency curve (diminishing returns pattern)
np.random.seed(42)
n_points = 100

# Investment amount (thousands of dollars)
x = np.linspace(10, 100, n_points)
# Efficiency gains follow a quadratic pattern with diminishing returns
# True relationship: y = -0.005x^2 + 1.2x + 20 + noise
y = -0.005 * x**2 + 1.2 * x + 20 + np.random.normal(0, 3, n_points)

# Polynomial regression (degree 2 - quadratic)
coeffs = np.polyfit(x, y, 2)
poly = np.poly1d(coeffs)

# Calculate R-squared
y_pred = poly(x)
ss_res = np.sum((y - y_pred) ** 2)
ss_tot = np.sum((y - np.mean(y)) ** 2)
r_squared = 1 - (ss_res / ss_tot)

# Create smooth curve for regression line
x_smooth = np.linspace(x.min(), x.max(), 200)
y_smooth = poly(x_smooth)

# Format polynomial equation
a, b, c = coeffs
equation = f"y = {a:.4f}x² + {b:.2f}x + {c:.2f}"

# Create data sources
scatter_source = ColumnDataSource(data={"x": x, "y": y})
line_source = ColumnDataSource(data={"x": x_smooth, "y": y_smooth})

# Create figure (4800 x 2700 px)
p = figure(
    width=4800,
    height=2700,
    title="scatter-regression-polynomial · bokeh · pyplots.ai",
    x_axis_label="Investment (thousands $)",
    y_axis_label="Efficiency Gain (%)",
)

# Plot scatter points
p.scatter(x="x", y="y", source=scatter_source, size=18, color="#306998", alpha=0.65, legend_label="Data Points")

# Plot polynomial regression curve
p.line(x="x", y="y", source=line_source, line_width=5, color="#FFD43B", legend_label="Polynomial Fit (degree 2)")

# Add R² and equation annotation
annotation_text = f"R² = {r_squared:.4f}\n{equation}"
annotation = Label(
    x=70,
    y=75,
    text=annotation_text,
    text_font_size="22pt",
    text_color="#333333",
    background_fill_color="white",
    background_fill_alpha=0.8,
)
p.add_layout(annotation)

# Styling - Text sizes for 4800x2700 canvas
p.title.text_font_size = "32pt"
p.title.text_color = "#333333"
p.xaxis.axis_label_text_font_size = "24pt"
p.yaxis.axis_label_text_font_size = "24pt"
p.xaxis.major_label_text_font_size = "18pt"
p.yaxis.major_label_text_font_size = "18pt"

# Grid styling
p.xgrid.grid_line_alpha = 0.3
p.ygrid.grid_line_alpha = 0.3
p.xgrid.grid_line_dash = "dashed"
p.ygrid.grid_line_dash = "dashed"

# Legend styling
p.legend.location = "bottom_right"
p.legend.label_text_font_size = "20pt"
p.legend.background_fill_alpha = 0.8

# Background
p.background_fill_color = "#fafafa"

# Save as PNG
export_png(p, filename="plot.png")

# Save as HTML for interactive version
output_file("plot.html")
save(p)
