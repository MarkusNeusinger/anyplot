""" pyplots.ai
contour-density: Density Contour Plot
Library: bokeh 3.8.1 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-30
"""

import matplotlib


matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np
from bokeh.io import export_png, save
from bokeh.models import ColumnDataSource
from bokeh.plotting import figure
from bokeh.resources import CDN
from scipy import stats


# Data - bivariate distribution with clusters
np.random.seed(42)
n_points = 500

# Create two clusters to show density variation
cluster1_x = np.random.normal(25, 4, n_points // 2)
cluster1_y = np.random.normal(35, 5, n_points // 2)
cluster2_x = np.random.normal(40, 6, n_points // 2)
cluster2_y = np.random.normal(50, 4, n_points // 2)

x = np.concatenate([cluster1_x, cluster2_x])
y = np.concatenate([cluster1_y, cluster2_y])

# Compute 2D KDE
kde = stats.gaussian_kde([x, y])

# Create grid for contour evaluation
x_min, x_max = x.min() - 3, x.max() + 3
y_min, y_max = y.min() - 3, y.max() + 3
xx, yy = np.meshgrid(np.linspace(x_min, x_max, 100), np.linspace(y_min, y_max, 100))
positions = np.vstack([xx.ravel(), yy.ravel()])
density = kde(positions).reshape(xx.shape)

# Extract contour lines using matplotlib (for calculation only, not for plotting)
fig_temp, ax_temp = plt.subplots()
contour_set = ax_temp.contour(xx, yy, density, levels=8)
plt.close(fig_temp)

# Create Bokeh figure
p = figure(
    width=4800,
    height=2700,
    title="contour-density · bokeh · pyplots.ai",
    x_axis_label="Measurement A (units)",
    y_axis_label="Measurement B (units)",
    x_range=(x_min, x_max),
    y_range=(y_min, y_max),
)

# Colors for contour levels (blue gradient - darker = higher density)
colors = ["#e8f4f8", "#c6e4f2", "#94cfea", "#5bb4e0", "#306998", "#1f5070", "#143848", "#0a1c24"]

# Plot contour lines using allsegs (matplotlib 3.8+ compatible)
for i, level_segs in enumerate(contour_set.allsegs):
    color = colors[min(i, len(colors) - 1)]
    for seg in level_segs:
        if len(seg) > 1:
            p.line(x=seg[:, 0], y=seg[:, 1], line_width=3, line_color=color, line_alpha=0.9)

# Overlay scatter points with transparency to show actual data
source = ColumnDataSource(data={"x": x, "y": y})
p.scatter(x="x", y="y", source=source, size=8, color="#FFD43B", alpha=0.4, legend_label="Data points")

# Styling
p.title.text_font_size = "28pt"
p.xaxis.axis_label_text_font_size = "22pt"
p.yaxis.axis_label_text_font_size = "22pt"
p.xaxis.major_label_text_font_size = "18pt"
p.yaxis.major_label_text_font_size = "18pt"

p.grid.grid_line_alpha = 0.3
p.grid.grid_line_dash = "dashed"

p.legend.label_text_font_size = "18pt"
p.legend.location = "top_left"
p.legend.background_fill_alpha = 0.7

# Save
export_png(p, filename="plot.png")
save(p, filename="plot.html", resources=CDN, title="contour-density · bokeh · pyplots.ai")
