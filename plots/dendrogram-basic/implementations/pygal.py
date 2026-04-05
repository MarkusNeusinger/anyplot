""" pyplots.ai
dendrogram-basic: Basic Dendrogram
Library: pygal 3.1.0 | Python 3.14.3
Quality: 79/100 | Updated: 2026-04-05
"""

import numpy as np
import pygal
from pygal.style import Style
from scipy.cluster.hierarchy import fcluster, linkage


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

# Assign cluster colors - cut at 3 clusters matching species
cluster_ids = fcluster(linkage_matrix, t=3, criterion="maxclust")

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

# Compute node positions and determine cluster membership for coloring
node_x = {}
node_height = {}
node_cluster = {}

for pos, leaf_id in enumerate(leaf_order):
    node_x[leaf_id] = pos
    node_height[leaf_id] = 0
    node_cluster[leaf_id] = cluster_ids[leaf_id]

# Map cluster IDs to species names and colors
# Determine which cluster ID corresponds to which species
cluster_species = {}
for leaf_id in range(n):
    cid = cluster_ids[leaf_id]
    species = labels[leaf_id].rsplit("-", 1)[0]
    cluster_species[cid] = species

# Color palette: Python Blue for Setosa, complementary for others
species_colors = {"Setosa": "#306998", "Versicolor": "#E07A2F", "Virginica": "#5BA55B"}
mixed_color = "#888888"

# Build U-shape series with color information
# Each merge creates one U-shaped path as its own series
u_shapes = []  # list of (color, points)
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

    # Determine color: same cluster = cluster color, mixed = gray
    cl = node_cluster[left]
    cr = node_cluster[right]
    if cl == cr:
        node_cluster[new_node] = cl
        color = species_colors.get(cluster_species.get(cl, ""), mixed_color)
    else:
        node_cluster[new_node] = -1
        color = mixed_color

    # Full U-shape: left-up, across, right-down
    u_shapes.append((color, [(x_left, h_left), (x_left, dist), (x_right, dist), (x_right, h_right)]))

# Ordered labels for x-axis
ordered_labels = [labels[i] for i in leaf_order]

# Build colors tuple matching series order so each U-shape gets the right color
series_color_tuple = tuple(color for color, _ in u_shapes)

# Style - scaled for 4800x2700 canvas
custom_style = Style(
    background="white",
    plot_background="#fafafa",
    foreground="#2d2d2d",
    foreground_strong="#1a1a1a",
    foreground_subtle="#d4d4d4",
    colors=series_color_tuple,
    title_font_size=52,
    label_font_size=38,
    major_label_font_size=36,
    legend_font_size=34,
    value_font_size=28,
    stroke_width=5,
    opacity=1.0,
    guide_stroke_color="#e0e0e0",
    guide_stroke_dasharray="",
    major_guide_stroke_color="#cccccc",
    major_guide_stroke_dasharray="",
    title_font_family="sans-serif",
    label_font_family="sans-serif",
    major_label_font_family="sans-serif",
    legend_font_family="sans-serif",
    value_font_family="sans-serif",
)

# Chart
chart = pygal.XY(
    width=4800,
    height=2700,
    style=custom_style,
    title="Iris Species Clustering · dendrogram-basic · pygal · pyplots.ai",
    x_title="Sample",
    y_title="Distance (Ward's Method)",
    show_legend=True,
    show_dots=False,
    fill=False,
    show_x_guides=False,
    show_y_guides=True,
    x_label_rotation=45,
    truncate_label=20,
    xrange=(-0.8, n + 0.5),
    margin_right=40,
    legend_at_bottom=True,
    legend_box_size=24,
    tooltip_border_radius=6,
    print_values=False,
    js=[],
)

# X-axis labels at leaf positions
chart.x_labels = list(range(n))
chart.x_labels_major = list(range(n))
chart.x_value_formatter = lambda x: ordered_labels[int(round(x))] if 0 <= round(x) < n else ""

# Draw dendrogram - each U-shape as its own series
color_to_species = {v: k for k, v in species_colors.items()}
color_to_species[mixed_color] = "Inter-cluster"

# Only the first series of each color gets a name (for legend)
named_colors = set()
for color, points in u_shapes:
    if color not in named_colors:
        series_name = color_to_species.get(color, "Other")
        named_colors.add(color)
    else:
        series_name = None
    chart.add(series_name, points, show_dots=False, stroke_style={"width": 5})

# Save
chart.render_to_file("plot.html")
chart.render_to_png("plot.png")
