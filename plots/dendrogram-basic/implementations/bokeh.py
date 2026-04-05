"""pyplots.ai
dendrogram-basic: Basic Dendrogram
Library: bokeh 3.8.2 | Python 3.14.3
Quality: /100 | Updated: 2026-04-05
"""

import numpy as np
from bokeh.io import export_png
from bokeh.models import ColumnDataSource, Label
from bokeh.plotting import figure, output_file, save
from scipy.cluster.hierarchy import leaves_list, linkage


# Data - Iris flower measurements (4 features for 15 samples)
np.random.seed(42)

samples_per_species = 5

labels = []
data = []

# Setosa: shorter petals, wider sepals
for i in range(samples_per_species):
    labels.append(f"Setosa-{i + 1}")
    data.append(
        [
            5.0 + np.random.randn() * 0.3,
            3.4 + np.random.randn() * 0.3,
            1.5 + np.random.randn() * 0.2,
            0.3 + np.random.randn() * 0.1,
        ]
    )

# Versicolor: medium measurements
for i in range(samples_per_species):
    labels.append(f"Versicolor-{i + 1}")
    data.append(
        [
            5.9 + np.random.randn() * 0.4,
            2.8 + np.random.randn() * 0.3,
            4.3 + np.random.randn() * 0.4,
            1.3 + np.random.randn() * 0.2,
        ]
    )

# Virginica: longer petals and sepals
for i in range(samples_per_species):
    labels.append(f"Virginica-{i + 1}")
    data.append(
        [
            6.6 + np.random.randn() * 0.5,
            3.0 + np.random.randn() * 0.3,
            5.5 + np.random.randn() * 0.5,
            2.0 + np.random.randn() * 0.3,
        ]
    )

data = np.array(data)
n_samples = len(labels)

# Compute hierarchical clustering using Ward's method
linkage_matrix = linkage(data, method="ward")

# Get leaf order for x-axis positioning
leaf_order = leaves_list(linkage_matrix)
ordered_labels = [labels[i] for i in leaf_order]

# Build dendrogram structure manually
node_positions = {}
for idx, leaf_idx in enumerate(leaf_order):
    node_positions[leaf_idx] = idx

# Color threshold for distinguishing clusters
max_dist = linkage_matrix[:, 2].max()
color_threshold = 0.7 * max_dist

# Collect line segments grouped by color for multi_line rendering
above_xs, above_ys = [], []
below_xs, below_ys = [], []

for i, (left, right, dist, _) in enumerate(linkage_matrix):
    left, right = int(left), int(right)
    new_node = n_samples + i

    left_x = node_positions[left]
    right_x = node_positions[right]
    left_y = 0 if left < n_samples else linkage_matrix[left - n_samples, 2]
    right_y = 0 if right < n_samples else linkage_matrix[right - n_samples, 2]

    new_x = (left_x + right_x) / 2
    node_positions[new_node] = new_x

    # U-shaped connector: left vertical, horizontal, right vertical
    xs = [left_x, left_x, right_x, right_x]
    ys = [left_y, dist, dist, right_y]

    if dist > color_threshold:
        above_xs.append(xs)
        above_ys.append(ys)
    else:
        below_xs.append(xs)
        below_ys.append(ys)

# Plot
p = figure(
    width=4800,
    height=2700,
    title="Iris Species Clustering · dendrogram-basic · bokeh · pyplots.ai",
    x_axis_label="Iris Sample",
    y_axis_label="Distance (Ward's Method)",
    x_range=(-0.8, n_samples - 0.2),
    y_range=(-max_dist * 0.16, max_dist * 1.08),
    toolbar_location=None,
)

# Draw dendrogram branches using multi_line with ColumnDataSource
if below_xs:
    source_below = ColumnDataSource(data={"xs": below_xs, "ys": below_ys})
    p.multi_line(
        xs="xs", ys="ys", source=source_below, line_width=4, line_color="#D4A017", legend_label="Within-cluster"
    )

source_above = ColumnDataSource(data={"xs": above_xs, "ys": above_ys})
p.multi_line(xs="xs", ys="ys", source=source_above, line_width=4, line_color="#306998", legend_label="Between-cluster")

# Leaf labels
for idx, label in enumerate(ordered_labels):
    label_obj = Label(
        x=idx,
        y=-max_dist * 0.02,
        text=label,
        text_font_size="20pt",
        text_color="#444444",
        text_align="right",
        angle=0.785,
        angle_units="rad",
        y_offset=-15,
    )
    p.add_layout(label_obj)

# Style
p.title.text_font_size = "30pt"
p.title.text_font_style = "normal"
p.title.text_color = "#333333"
p.xaxis.axis_label_text_font_size = "24pt"
p.yaxis.axis_label_text_font_size = "24pt"
p.xaxis.axis_label_text_color = "#555555"
p.yaxis.axis_label_text_color = "#555555"
p.xaxis.major_label_text_font_size = "0pt"
p.yaxis.major_label_text_font_size = "20pt"
p.yaxis.major_label_text_color = "#666666"

p.xgrid.visible = False
p.ygrid.grid_line_alpha = 0.15
p.ygrid.grid_line_dash = [1, 0]

p.xaxis.axis_line_color = "#CCCCCC"
p.yaxis.axis_line_color = "#CCCCCC"
p.xaxis.major_tick_line_color = None
p.xaxis.minor_tick_line_color = None
p.yaxis.major_tick_line_color = "#CCCCCC"
p.yaxis.minor_tick_line_color = None
p.outline_line_color = None

# Legend
p.legend.location = "top_right"
p.legend.label_text_font_size = "18pt"
p.legend.label_text_color = "#444444"
p.legend.glyph_width = 40
p.legend.glyph_height = 6
p.legend.spacing = 8
p.legend.padding = 15
p.legend.background_fill_alpha = 0.9
p.legend.border_line_color = "#DDDDDD"
p.legend.border_line_alpha = 0.5

# Save
export_png(p, filename="plot.png")
output_file("plot.html")
save(p)
