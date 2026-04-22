""" pyplots.ai
frequency-polygon-basic: Frequency Polygon for Distribution Comparison
Library: bokeh 3.8.2 | Python 3.13.11
Quality: 92/100 | Created: 2026-01-09
"""

import numpy as np
from bokeh.io import export_png, save
from bokeh.models import ColumnDataSource
from bokeh.plotting import figure
from bokeh.resources import CDN


# Data - Three groups with different distributions
np.random.seed(42)

# Group A: Normal distribution centered at 65 (Morning Session)
group_a = np.random.normal(loc=65, scale=8, size=300)

# Group B: Normal distribution centered at 75, more spread (Afternoon Session)
group_b = np.random.normal(loc=75, scale=12, size=300)

# Group C: Slightly bimodal distribution (Evening Session)
group_c = np.concatenate([np.random.normal(loc=50, scale=6, size=150), np.random.normal(loc=60, scale=6, size=150)])

# Common bin edges for all groups
all_data = np.concatenate([group_a, group_b, group_c])
bins = np.linspace(all_data.min() - 5, all_data.max() + 5, 21)
bin_centers = (bins[:-1] + bins[1:]) / 2

# Compute histogram counts
counts_a, _ = np.histogram(group_a, bins=bins)
counts_b, _ = np.histogram(group_b, bins=bins)
counts_c, _ = np.histogram(group_c, bins=bins)

# Extend to zero at both ends for closed polygon shape
bin_width = bins[1] - bins[0]
x_extended = np.concatenate([[bin_centers[0] - bin_width], bin_centers, [bin_centers[-1] + bin_width]])
y_a_extended = np.concatenate([[0], counts_a, [0]])
y_b_extended = np.concatenate([[0], counts_b, [0]])
y_c_extended = np.concatenate([[0], counts_c, [0]])

# Create figure (4800 x 2700)
p = figure(
    width=4800,
    height=2700,
    title="frequency-polygon-basic · bokeh · pyplots.ai",
    x_axis_label="Test Score (points)",
    y_axis_label="Frequency (count)",
)

# Create sources
source_a = ColumnDataSource(data={"x": x_extended, "y": y_a_extended})
source_b = ColumnDataSource(data={"x": x_extended, "y": y_b_extended})
source_c = ColumnDataSource(data={"x": x_extended, "y": y_c_extended})

# Plot frequency polygons with fills
# Group A - Python Blue (Morning Session)
p.patch(x="x", y="y", source=source_a, fill_alpha=0.25, fill_color="#306998", line_width=0)
p.line(x="x", y="y", source=source_a, line_color="#306998", line_width=5, legend_label="Morning Session")
p.scatter(x=bin_centers, y=counts_a, size=18, color="#306998", alpha=0.9, legend_label="Morning Session")

# Group B - Python Yellow (Afternoon Session)
p.patch(x="x", y="y", source=source_b, fill_alpha=0.25, fill_color="#FFD43B", line_width=0)
p.line(x="x", y="y", source=source_b, line_color="#FFD43B", line_width=5, legend_label="Afternoon Session")
p.scatter(x=bin_centers, y=counts_b, size=18, color="#FFD43B", alpha=0.9, legend_label="Afternoon Session")

# Group C - Teal (Evening Session)
p.patch(x="x", y="y", source=source_c, fill_alpha=0.25, fill_color="#17A589", line_width=0)
p.line(x="x", y="y", source=source_c, line_color="#17A589", line_width=5, legend_label="Evening Session")
p.scatter(x=bin_centers, y=counts_c, size=18, color="#17A589", alpha=0.9, legend_label="Evening Session")

# Styling for large canvas
p.title.text_font_size = "36pt"
p.xaxis.axis_label_text_font_size = "28pt"
p.yaxis.axis_label_text_font_size = "28pt"
p.xaxis.major_label_text_font_size = "22pt"
p.yaxis.major_label_text_font_size = "22pt"

# Legend styling - place inside plot area
p.legend.location = "top_left"
p.legend.label_text_font_size = "24pt"
p.legend.background_fill_alpha = 0.85
p.legend.background_fill_color = "white"
p.legend.border_line_width = 2
p.legend.border_line_color = "#333333"
p.legend.padding = 15
p.legend.spacing = 8
p.legend.glyph_height = 35
p.legend.glyph_width = 35
p.legend.margin = 20

# Grid styling
p.grid.grid_line_alpha = 0.3
p.grid.grid_line_dash = [6, 4]

# Outline styling
p.outline_line_width = 2
p.outline_line_color = "#333333"

# Save PNG and HTML
export_png(p, filename="plot.png")
save(p, filename="plot.html", resources=CDN, title="frequency-polygon-basic · bokeh · pyplots.ai")
