""" pyplots.ai
dendrogram-basic: Basic Dendrogram
Library: pygal 3.1.0 | Python 3.14.3
Quality: 82/100 | Updated: 2026-04-05
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

# Map cluster IDs to species names
cluster_species = {}
for leaf_id in range(n):
    cid = cluster_ids[leaf_id]
    species = labels[leaf_id].rsplit("-", 1)[0]
    cluster_species[cid] = species

# Colorblind-safe palette: blue, teal, amber (high contrast, avoids red-green)
species_colors = {"Setosa": "#306998", "Versicolor": "#D4872C", "Virginica": "#7B4EA3"}
mixed_color = "#5C6370"

# Build U-shape series with color and distance metadata
u_shapes = []
max_dist = linkage_matrix[:, 2].max()

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

    cl = node_cluster[left]
    cr = node_cluster[right]
    if cl == cr:
        node_cluster[new_node] = cl
        color = species_colors.get(cluster_species.get(cl, ""), mixed_color)
    else:
        node_cluster[new_node] = -1
        color = mixed_color

    # Stroke width scales with merge distance for visual hierarchy
    stroke_w = 3.5 + 6 * (dist / max_dist)

    u_shapes.append((color, stroke_w, dist, [(x_left, h_left), (x_left, dist), (x_right, dist), (x_right, h_right)]))

# Ordered labels for x-axis
ordered_labels = [labels[i] for i in leaf_order]

# Style - refined for publication quality at 4800x2700
custom_style = Style(
    background="#FFFFFF",
    plot_background="#FAFAFA",
    foreground="#2d2d2d",
    foreground_strong="#1a1a1a",
    foreground_subtle="#e0e0e0",
    colors=tuple(color for color, _, _, _ in u_shapes),
    title_font_size=56,
    label_font_size=38,
    major_label_font_size=36,
    legend_font_size=34,
    value_font_size=28,
    stroke_width=4,
    opacity=1.0,
    guide_stroke_color="#e8e8e8",
    major_guide_stroke_color="#d8d8d8",
    title_font_family="Helvetica, Arial, sans-serif",
    label_font_family="Helvetica, Arial, sans-serif",
    major_label_font_family="Helvetica, Arial, sans-serif",
    legend_font_family="Helvetica, Arial, sans-serif",
    value_font_family="Helvetica, Arial, sans-serif",
)

# Chart - leveraging pygal XY with extensive configuration
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
    show_minor_x_labels=False,
    x_label_rotation=35,
    truncate_label=30,
    xrange=(-1.0, n + 0.2),
    range=(0, max_dist * 1.05),
    margin_top=50,
    margin_bottom=140,
    margin_left=100,
    margin_right=80,
    legend_at_bottom=True,
    legend_box_size=30,
    tooltip_border_radius=10,
    print_values=False,
    spacing=35,
    js=[],
)

# Custom x-axis labels at leaf positions with formatted names
chart.x_labels = list(range(n))
chart.x_labels_major = list(range(n))
chart.x_value_formatter = lambda x: ordered_labels[int(round(x))] if 0 <= round(x) < n else ""

# Y-axis: custom labels with formatted distances
y_max_nice = int(np.ceil(max_dist))
step = 1 if y_max_nice <= 6 else 2
chart.y_labels = [{"value": v, "label": f"{v:.0f}"} for v in range(0, y_max_nice + 1, step)]

# Draw dendrogram - each U-shape as its own series with scaled stroke
color_to_species = {v: k for k, v in species_colors.items()}
color_to_species[mixed_color] = "Inter-cluster"

named_colors = set()
for color, stroke_w, dist, points in u_shapes:
    if color not in named_colors:
        series_name = color_to_species.get(color, "Other")
        named_colors.add(color)
    else:
        series_name = None

    # Use pygal's per-series formatter for distance tooltips
    chart.add(
        series_name,
        [{"value": p, "label": f"d={dist:.2f}"} for p in points],
        show_dots=False,
        stroke_style={"width": stroke_w, "linecap": "round", "linejoin": "round"},
        allow_interruptions=False,
    )

# Add invisible reference series for key distance annotations via pygal secondary axis
# Mark the two most important merge distances with horizontal reference lines
key_merges = sorted(linkage_matrix[:, 2])
within_cluster_max = key_merges[n - 4]  # Highest within-cluster merge
between_cluster = key_merges[-2]  # Second-to-last merge (between two groups)

for ref_dist, ref_label in [
    (within_cluster_max, f"Within-species max (d={within_cluster_max:.1f})"),
    (between_cluster, f"Between-group merge (d={between_cluster:.1f})"),
]:
    chart.add(
        ref_label,
        [(-0.8, ref_dist), (n - 0.2, ref_dist)],
        show_dots=False,
        stroke_style={"width": 2, "dasharray": "12, 8", "linecap": "butt"},
    )

# Save
chart.render_to_file("plot.html")
chart.render_to_png("plot.png")
