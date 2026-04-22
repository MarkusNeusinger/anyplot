""" pyplots.ai
density-rug: Density Plot with Rug Marks
Library: bokeh 3.8.2 | Python 3.13.11
Quality: 91/100 | Created: 2026-01-09
"""

import numpy as np
from bokeh.io import export_png
from bokeh.models import ColumnDataSource
from bokeh.plotting import figure, output_file, save


# Data - Response times in milliseconds (realistic API latency data)
np.random.seed(42)
# Mix of normal operations and some slower responses (bimodal-ish)
normal_times = np.random.normal(loc=120, scale=25, size=180)
slow_times = np.random.normal(loc=220, scale=30, size=40)
response_times = np.concatenate([normal_times, slow_times])
response_times = response_times[response_times > 0]  # Ensure positive values

# Compute KDE (Gaussian kernel density estimation)
n = len(response_times)
std = np.std(response_times)
iqr = np.percentile(response_times, 75) - np.percentile(response_times, 25)
bandwidth = 0.9 * min(std, iqr / 1.34) * n ** (-0.2)  # Silverman's rule

x_range = np.linspace(response_times.min() - 20, response_times.max() + 20, 500)
density = np.zeros_like(x_range)
for xi in response_times:
    density += np.exp(-0.5 * ((x_range - xi) / bandwidth) ** 2)
density = density / (n * bandwidth * np.sqrt(2 * np.pi))

# Create figure
p = figure(
    width=4800,
    height=2700,
    title="density-rug · bokeh · pyplots.ai",
    x_axis_label="Response Time (ms)",
    y_axis_label="Density",
)

# Plot KDE as filled area using patch
kde_x = np.concatenate([[x_range[0]], x_range, [x_range[-1]]])
kde_y = np.concatenate([[0], density, [0]])
p.patch(x=kde_x, y=kde_y, fill_color="#306998", fill_alpha=0.4, line_color="#306998", line_width=4)

# Plot KDE line on top
kde_source = ColumnDataSource(data={"x": x_range, "y": density})
p.line(x="x", y="y", source=kde_source, line_color="#306998", line_width=5)

# Rug marks along x-axis
rug_height = density.max() * 0.03  # Small tick height relative to density
rug_source = ColumnDataSource(
    data={"x": response_times, "y0": np.zeros(len(response_times)), "y1": np.full(len(response_times), -rug_height)}
)
p.segment(x0="x", y0="y0", x1="x", y1="y1", source=rug_source, line_color="#306998", line_width=2, line_alpha=0.6)

# Styling - larger text for 4800x2700 canvas
p.title.text_font_size = "32pt"
p.xaxis.axis_label_text_font_size = "24pt"
p.yaxis.axis_label_text_font_size = "24pt"
p.xaxis.major_label_text_font_size = "20pt"
p.yaxis.major_label_text_font_size = "20pt"

p.xgrid.grid_line_alpha = 0.3
p.ygrid.grid_line_alpha = 0.3
p.xgrid.grid_line_dash = "dashed"
p.ygrid.grid_line_dash = "dashed"

p.background_fill_color = "#fafafa"
p.border_fill_color = "#ffffff"

# Extend y-axis slightly below 0 to show rug marks
p.y_range.start = -rug_height * 1.5
p.y_range.end = density.max() * 1.1

# Save PNG
export_png(p, filename="plot.png")

# Save HTML for interactivity
output_file("plot.html", title="density-rug · bokeh · pyplots.ai")
save(p)
