""" pyplots.ai
dendrogram-basic: Basic Dendrogram
Library: bokeh 3.8.2 | Python 3.14.3
Quality: 90/100 | Updated: 2026-04-05
"""

import numpy as np
from bokeh.io import export_png
from bokeh.models import ColumnDataSource, FixedTicker, HoverTool, Label, Span
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

# Track cluster members for hover info
cluster_members = {}
for i in range(n_samples):
    cluster_members[i] = [labels[i]]

# Color threshold for distinguishing clusters
max_dist = linkage_matrix[:, 2].max()
color_threshold = 0.7 * max_dist

# Colorblind-safe palette
colors_within = "#0F7B6C"  # teal for within-cluster
colors_between = "#C0392B"  # warm red for between-cluster (cross-species merges)

# Collect line segments with hover metadata
all_xs, all_ys = [], []
all_colors = []
all_distances = []
all_left_items = []
all_right_items = []
all_cluster_sizes = []

for i, (left, right, dist, count) in enumerate(linkage_matrix):
    left, right = int(left), int(right)
    new_node = n_samples + i

    left_x = node_positions[left]
    right_x = node_positions[right]
    left_y = 0 if left < n_samples else linkage_matrix[left - n_samples, 2]
    right_y = 0 if right < n_samples else linkage_matrix[right - n_samples, 2]

    new_x = (left_x + right_x) / 2
    node_positions[new_node] = new_x

    # Track members
    left_members = cluster_members[left]
    right_members = cluster_members[right]
    cluster_members[new_node] = left_members + right_members

    # U-shaped connector: left vertical, horizontal, right vertical
    xs = [left_x, left_x, right_x, right_x]
    ys = [left_y, dist, dist, right_y]

    color = colors_between if dist > color_threshold else colors_within

    all_xs.append(xs)
    all_ys.append(ys)
    all_colors.append(color)
    all_distances.append(f"{dist:.2f}")
    all_left_items.append(", ".join(left_members[:3]) + ("..." if len(left_members) > 3 else ""))
    all_right_items.append(", ".join(right_members[:3]) + ("..." if len(right_members) > 3 else ""))
    all_cluster_sizes.append(str(int(count)))

# Apply sqrt scaling to y-axis for better visibility of lower merges
sqrt_max = np.sqrt(max_dist)

all_ys_scaled = []
for ys in all_ys:
    all_ys_scaled.append([np.sqrt(y) for y in ys])

# Plot
p = figure(
    width=4800,
    height=2700,
    title="dendrogram-basic \u00b7 bokeh \u00b7 pyplots.ai",
    x_axis_label="Iris Sample",
    y_axis_label="Distance (Ward\u2019s Method, \u221a scale)",
    x_range=(-0.8, n_samples - 0.2),
    y_range=(-sqrt_max * 0.02, sqrt_max * 1.12),
    toolbar_location=None,
    min_border_bottom=220,
)

# Draw dendrogram branches using multi_line with ColumnDataSource and hover data
source = ColumnDataSource(
    data={
        "xs": all_xs,
        "ys": all_ys_scaled,
        "color": all_colors,
        "distance": all_distances,
        "left_cluster": all_left_items,
        "right_cluster": all_right_items,
        "cluster_size": all_cluster_sizes,
    }
)

branch_renderer = p.multi_line(
    xs="xs",
    ys="ys",
    source=source,
    line_width=4,
    line_color="color",
    line_alpha=0.85,
    hover_line_width=7,
    hover_line_alpha=1.0,
    hover_line_color="#E74C3C",
)

# Add HoverTool for interactive branch inspection
hover = HoverTool(
    renderers=[branch_renderer],
    tooltips=[
        ("Merge Distance", "@distance"),
        ("Cluster Size", "@cluster_size items"),
        ("Left", "@left_cluster"),
        ("Right", "@right_cluster"),
    ],
    line_policy="interp",
)
p.add_tools(hover)

# Cluster threshold line for visual storytelling
threshold_y_scaled = np.sqrt(color_threshold)
threshold_line = Span(
    location=threshold_y_scaled,
    dimension="width",
    line_color="#999999",
    line_dash="dashed",
    line_width=2,
    line_alpha=0.5,
)
p.add_layout(threshold_line)

threshold_label = Label(
    x=n_samples - 1.2,
    y=threshold_y_scaled,
    text="cluster threshold",
    text_font_size="16pt",
    text_color="#888888",
    text_font_style="italic",
    y_offset=8,
    text_align="right",
)
p.add_layout(threshold_label)

# Legend entries via off-screen line glyphs for colored swatches
p.line([-99, -98], [-99, -99], line_color=colors_within, line_width=6, legend_label="Within-cluster")
p.line([-99, -98], [-99, -99], line_color=colors_between, line_width=6, legend_label="Between-cluster")

# Leaf labels as x-axis tick labels (renders outside plot frame, no clipping)
p.xaxis.ticker = FixedTicker(ticks=list(range(n_samples)))
p.xaxis.major_label_overrides = {i: ordered_labels[i] for i in range(n_samples)}
p.xaxis.major_label_orientation = 0.785  # 45 degrees in radians

# Style
p.title.text_font_size = "30pt"
p.title.text_font_style = "normal"
p.title.text_color = "#333333"
p.xaxis.axis_label_text_font_size = "24pt"
p.yaxis.axis_label_text_font_size = "24pt"
p.xaxis.axis_label_text_color = "#555555"
p.yaxis.axis_label_text_color = "#555555"
p.xaxis.major_label_text_font_size = "18pt"
p.xaxis.major_label_text_color = "#444444"
p.yaxis.major_label_text_font_size = "20pt"
p.yaxis.major_label_text_color = "#666666"

p.background_fill_color = "#FAFAFA"
p.border_fill_color = "white"
p.xgrid.visible = False
p.ygrid.grid_line_alpha = 0.12
p.ygrid.grid_line_dash = [4, 4]
p.ygrid.grid_line_color = "#AAAAAA"

p.xaxis.axis_line_color = "#CCCCCC"
p.yaxis.axis_line_color = "#CCCCCC"
p.xaxis.major_tick_line_color = None
p.xaxis.minor_tick_line_color = None
p.yaxis.major_tick_line_color = "#CCCCCC"
p.yaxis.minor_tick_line_color = None
p.outline_line_color = None

# Legend
p.legend.location = "top_left"
p.legend.label_text_font_size = "22pt"
p.legend.label_text_color = "#333333"
p.legend.glyph_width = 50
p.legend.glyph_height = 8
p.legend.spacing = 12
p.legend.padding = 20
p.legend.margin = 15
p.legend.background_fill_alpha = 0.92
p.legend.background_fill_color = "#FAFAFA"
p.legend.border_line_color = "#CCCCCC"
p.legend.border_line_alpha = 0.6

# Save
export_png(p, filename="plot.png")
output_file("plot.html")
save(p)
