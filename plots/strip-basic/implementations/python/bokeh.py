""" pyplots.ai
strip-basic: Basic Strip Plot
Library: bokeh 3.8.1 | Python 3.13.11
Quality: 92/100 | Created: 2025-12-23
"""

import numpy as np
from bokeh.io import export_png, save
from bokeh.models import ColumnDataSource
from bokeh.plotting import figure


# Data - Survey response scores by department
np.random.seed(42)

categories = ["Engineering", "Marketing", "Sales", "HR"]
n_per_category = [45, 38, 52, 30]

# Generate realistic survey scores (1-10 scale) with different distributions
data = {
    "Engineering": np.clip(np.random.normal(7.2, 1.5, n_per_category[0]), 1, 10),
    "Marketing": np.clip(np.random.normal(6.8, 1.8, n_per_category[1]), 1, 10),
    "Sales": np.clip(np.random.normal(7.5, 1.2, n_per_category[2]), 1, 10),
    "HR": np.clip(np.random.normal(8.0, 1.0, n_per_category[3]), 1, 10),
}

# Build arrays for plotting with jitter
x_values = []
y_values = []
colors = []

color_map = {"Engineering": "#306998", "Marketing": "#FFD43B", "Sales": "#4CAF50", "HR": "#E91E63"}

jitter_width = 0.25

for i, cat in enumerate(categories):
    values = data[cat]
    n = len(values)
    # Random jitter for x position
    jittered_x = i + np.random.uniform(-jitter_width, jitter_width, n)
    x_values.extend(jittered_x)
    y_values.extend(values)
    colors.extend([color_map[cat]] * n)

source = ColumnDataSource(data={"x": x_values, "y": y_values, "color": colors})

# Create figure
p = figure(
    width=4800,
    height=2700,
    title="strip-basic · bokeh · pyplots.ai",
    x_axis_label="Department",
    y_axis_label="Survey Score",
    x_range=(-0.5, len(categories) - 0.5),
    y_range=(0, 11),
)

# Plot strip points
p.scatter(x="x", y="y", source=source, size=28, color="color", alpha=0.6, line_color="white", line_width=2)

# Add horizontal lines for group means as reference
for i, cat in enumerate(categories):
    mean_val = float(np.mean(data[cat]))
    p.line(x=[i - 0.35, i + 0.35], y=[mean_val, mean_val], line_color="#333333", line_width=5, line_dash="solid")

# Styling for 4800x2700 px
p.title.text_font_size = "42pt"
p.xaxis.axis_label_text_font_size = "32pt"
p.yaxis.axis_label_text_font_size = "32pt"
p.xaxis.major_label_text_font_size = "26pt"
p.yaxis.major_label_text_font_size = "26pt"

# Set categorical tick labels on x-axis
p.xaxis.ticker = list(range(len(categories)))
p.xaxis.major_label_overrides = dict(enumerate(categories))

# Grid styling
p.xgrid.grid_line_color = None
p.ygrid.grid_line_alpha = 0.3
p.ygrid.grid_line_dash = "dashed"

# Background
p.background_fill_color = "#fafafa"
p.border_fill_color = "white"

# Axis styling
p.xaxis.axis_line_width = 2
p.yaxis.axis_line_width = 2

# Save outputs
export_png(p, filename="plot.png")
save(p, filename="plot.html")
