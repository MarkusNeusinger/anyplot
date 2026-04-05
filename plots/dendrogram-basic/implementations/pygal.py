""" pyplots.ai
dendrogram-basic: Basic Dendrogram
Library: pygal 3.1.0 | Python 3.14.3
Quality: 80/100 | Updated: 2026-04-05
"""

import numpy as np
import pygal
from pygal.style import Style
from scipy.cluster.hierarchy import linkage


# Data - Iris flower measurements (4 features for 15 samples)
np.random.seed(42)
samples_per_species = 5

labels = []
measurements = []

# Setosa: shorter petals, wider sepals
for i in range(samples_per_species):
    labels.append(f"Setosa-{i + 1}")
    measurements.append(
        [
            5.0 + np.random.randn() * 0.35,
            3.4 + np.random.randn() * 0.35,
            1.5 + np.random.randn() * 0.25,
            0.3 + np.random.randn() * 0.12,
        ]
    )

# Versicolor: medium measurements
for i in range(samples_per_species):
    labels.append(f"Versicolor-{i + 1}")
    measurements.append(
        [
            5.9 + np.random.randn() * 0.5,
            2.8 + np.random.randn() * 0.35,
            4.3 + np.random.randn() * 0.5,
            1.3 + np.random.randn() * 0.25,
        ]
    )

# Virginica: longer petals and sepals
for i in range(samples_per_species):
    labels.append(f"Virginica-{i + 1}")
    measurements.append(
        [
            6.6 + np.random.randn() * 0.55,
            3.0 + np.random.randn() * 0.35,
            5.5 + np.random.randn() * 0.55,
            2.0 + np.random.randn() * 0.3,
        ]
    )

measurements = np.array(measurements)

# Compute hierarchical clustering
linkage_matrix = linkage(measurements, method="ward")
n = len(labels)

# Build leaf ordering from linkage (iterative traversal)
leaf_order = []
stack = [2 * n - 2]
while stack:
    node_id = stack.pop()
    if node_id < n:
        leaf_order.append(node_id)
    else:
        idx = node_id - n
        left = int(linkage_matrix[idx, 0])
        right = int(linkage_matrix[idx, 1])
        stack.append(right)
        stack.append(left)

# Compute node positions and collect dendrogram segments
node_x = {}
node_height = {}

for pos, leaf_id in enumerate(leaf_order):
    node_x[leaf_id] = pos
    node_height[leaf_id] = 0

segments = []
for idx in range(len(linkage_matrix)):
    left = int(linkage_matrix[idx, 0])
    right = int(linkage_matrix[idx, 1])
    dist = linkage_matrix[idx, 2]
    new_node = n + idx

    x_left = node_x[left]
    x_right = node_x[right]
    node_x[new_node] = (x_left + x_right) / 2
    node_height[new_node] = dist

    h_left = node_height[left]
    h_right = node_height[right]

    # U-shape: left vertical, horizontal bar, right vertical
    segments.append([(x_left, h_left), (x_left, dist)])
    segments.append([(x_left, dist), (x_right, dist)])
    segments.append([(x_right, h_right), (x_right, dist)])

# Ordered labels for x-axis
ordered_labels = [labels[i] for i in leaf_order]

# Style - scaled for 4800x2700 canvas
custom_style = Style(
    background="white",
    plot_background="white",
    foreground="#333333",
    foreground_strong="#333333",
    foreground_subtle="#cccccc",
    colors=("#306998",),
    title_font_size=52,
    label_font_size=40,
    major_label_font_size=38,
    legend_font_size=32,
    value_font_size=28,
    stroke_width=5,
    opacity=1.0,
    guide_stroke_color="#e5e5e5",
    guide_stroke_dasharray="",
)

# Chart
chart = pygal.XY(
    width=4800,
    height=2700,
    style=custom_style,
    title="Iris Species Clustering · dendrogram-basic · pygal · pyplots.ai",
    x_title="Sample",
    y_title="Distance (Ward's Method)",
    show_legend=False,
    show_dots=False,
    fill=False,
    show_x_guides=False,
    show_y_guides=True,
    x_label_rotation=45,
    truncate_label=20,
    xrange=(-0.5, n - 0.5),
)

# X-axis labels at leaf positions
chart.x_labels = list(range(n))
chart.x_labels_major = list(range(n))
chart.x_value_formatter = lambda x: ordered_labels[int(round(x))] if 0 <= round(x) < n else ""

# Draw dendrogram segments
for seg in segments:
    chart.add(None, seg, show_dots=False, stroke_style={"width": 5})

# Save
chart.render_to_file("plot.html")
chart.render_to_png("plot.png")
