""" pyplots.ai
violin-swarm: Violin Plot with Overlaid Swarm Points
Library: bokeh 3.8.2 | Python 3.13.11
Quality: 91/100 | Created: 2026-01-09
"""

import numpy as np
from bokeh.io import export_png, save
from bokeh.models import ColumnDataSource, FactorRange
from bokeh.plotting import figure
from bokeh.resources import CDN
from scipy import stats


# Data - Reaction times (ms) across 4 experimental conditions
np.random.seed(42)

categories = ["Control", "Low Dose", "Medium Dose", "High Dose"]
n_per_group = 50

# Generate different distributions for each condition
data = {
    "Control": np.random.normal(350, 50, n_per_group),
    "Low Dose": np.random.normal(320, 45, n_per_group),
    "Medium Dose": np.random.normal(280, 60, n_per_group),
    "High Dose": np.random.normal(250, 40, n_per_group),
}

# Colors: Python Blue for violin, Python Yellow for points
violin_color = "#306998"
point_color = "#FFD43B"

# Create figure with padding for violins
p = figure(
    width=4800,
    height=2700,
    title="violin-swarm · bokeh · pyplots.ai",
    x_range=FactorRange(*categories, range_padding=0.15),
    y_axis_label="Reaction Time (ms)",
    x_axis_label="Experimental Condition",
)

# Styling - larger text for 4800x2700 canvas
p.title.text_font_size = "36pt"
p.xaxis.axis_label_text_font_size = "28pt"
p.yaxis.axis_label_text_font_size = "28pt"
p.xaxis.major_label_text_font_size = "24pt"
p.yaxis.major_label_text_font_size = "22pt"
p.grid.grid_line_alpha = 0.3
p.grid.grid_line_dash = [6, 4]
p.outline_line_color = None

# Build violin shapes and swarm points
violin_patches_x = []
violin_patches_y = []
swarm_x = []
swarm_y = []

for i, cat in enumerate(categories):
    values = data[cat]

    # Kernel density estimation for violin
    kde = stats.gaussian_kde(values)
    y_range = np.linspace(values.min() - 20, values.max() + 20, 200)
    density = kde(y_range)

    # Normalize density to max width of 0.4 (so violin fits within category space)
    max_width = 0.35
    density_normalized = density / density.max() * max_width

    # Create violin shape (mirrored density)
    x_violin = np.concatenate([i - density_normalized, (i + density_normalized)[::-1]])
    y_violin = np.concatenate([y_range, y_range[::-1]])

    violin_patches_x.append(x_violin.tolist())
    violin_patches_y.append(y_violin.tolist())

    # Create swarm points (jitter within violin boundary)
    for val in values:
        # Get the density at this y value to determine jitter range
        val_density = kde(val)[0]
        jitter_range = (val_density / density.max()) * max_width * 0.8
        jitter = np.random.uniform(-jitter_range, jitter_range)
        swarm_x.append(i + jitter)
        swarm_y.append(val)

# Draw violins as patches (semi-transparent)
for vx, vy in zip(violin_patches_x, violin_patches_y, strict=True):
    p.patch(vx, vy, fill_color=violin_color, fill_alpha=0.4, line_color=violin_color, line_width=2)

# Draw swarm points - larger size for visibility
swarm_source = ColumnDataSource(data={"x": swarm_x, "y": swarm_y})
p.scatter("x", "y", source=swarm_source, size=18, color=point_color, alpha=0.9, line_color="#333333", line_width=1.5)

# Save PNG and HTML
export_png(p, filename="plot.png")
save(p, filename="plot.html", resources=CDN, title="violin-swarm · bokeh · pyplots.ai")
