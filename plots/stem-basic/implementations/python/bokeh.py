""" pyplots.ai
stem-basic: Basic Stem Plot
Library: bokeh 3.8.1 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-23
"""

import numpy as np
from bokeh.io import export_png, output_file, save
from bokeh.models import ColumnDataSource
from bokeh.plotting import figure


# Data - Discrete signal samples (damped oscillation)
np.random.seed(42)
n_points = 30
x = np.arange(n_points)
y = np.exp(-0.1 * x) * np.sin(0.5 * x) * 2 + np.random.randn(n_points) * 0.1

# Baseline for stems
baseline = 0

# Create data sources
source = ColumnDataSource(data={"x": x, "y": y})
stem_source = ColumnDataSource(data={"x0": x, "y0": np.full_like(x, baseline, dtype=float), "x1": x, "y1": y})

# Create figure
p = figure(
    width=4800,
    height=2700,
    title="stem-basic · bokeh · pyplots.ai",
    x_axis_label="Sample Index",
    y_axis_label="Amplitude",
)

# Draw stems (vertical lines from baseline to data points)
p.segment(x0="x0", y0="y0", x1="x1", y1="y1", source=stem_source, line_width=4, color="#306998", alpha=0.8)

# Draw markers at data points
p.scatter(x="x", y="y", source=source, size=25, color="#306998", alpha=0.9)

# Draw baseline
p.line(
    x=[x.min() - 0.5, x.max() + 0.5],
    y=[baseline, baseline],
    line_width=3,
    line_dash="dashed",
    color="#999999",
    alpha=0.6,
)

# Styling for 4800x2700
p.title.text_font_size = "36pt"
p.xaxis.axis_label_text_font_size = "28pt"
p.yaxis.axis_label_text_font_size = "28pt"
p.xaxis.major_label_text_font_size = "22pt"
p.yaxis.major_label_text_font_size = "22pt"

# Grid styling
p.grid.grid_line_alpha = 0.3
p.grid.grid_line_dash = "dashed"

# Save outputs
export_png(p, filename="plot.png")
output_file("plot.html")
save(p)
