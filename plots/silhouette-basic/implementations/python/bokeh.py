""" pyplots.ai
silhouette-basic: Silhouette Plot
Library: bokeh 3.8.1 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-26
"""

import numpy as np
from bokeh.io import export_png, output_file, save
from bokeh.models import ColumnDataSource, Label, Span
from bokeh.plotting import figure


# Data - simulating silhouette analysis of customer segmentation (3 clusters)
# Realistic scenario: clustering customers by purchase behavior
np.random.seed(42)

n_clusters = 3
cluster_sizes = [50, 55, 45]  # Different sized clusters

# Generate realistic silhouette values for each cluster
# Cluster 0: Well-separated cluster (high silhouette scores)
cluster0_vals = np.clip(np.random.beta(8, 2, cluster_sizes[0]) * 0.6 + 0.35, 0.1, 0.95)
# Cluster 1: Good cluster with some overlap (medium-high scores)
cluster1_vals = np.clip(np.random.beta(5, 2, cluster_sizes[1]) * 0.5 + 0.25, 0.0, 0.85)
# Cluster 2: Some ambiguous samples (includes negative values)
cluster2_vals = np.clip(np.random.beta(4, 3, cluster_sizes[2]) * 0.8 - 0.1, -0.15, 0.75)

# Combine all values
silhouette_vals = np.concatenate([cluster0_vals, cluster1_vals, cluster2_vals])
cluster_labels = np.concatenate(
    [
        np.zeros(cluster_sizes[0], dtype=int),
        np.ones(cluster_sizes[1], dtype=int),
        np.full(cluster_sizes[2], 2, dtype=int),
    ]
)

# Calculate average silhouette score
avg_silhouette = float(np.mean(silhouette_vals))

# Prepare data for plotting - sorted silhouette values within each cluster
y_lower = 15
bar_data = {"x": [], "y": [], "width": [], "height": [], "color": []}
cluster_info = []  # For labels

# Colors for clusters - Python blue, yellow, and a colorblind-safe third color
colors = ["#306998", "#FFD43B", "#2ECC71"]

for i in range(n_clusters):
    # Get silhouette values for this cluster
    cluster_mask = cluster_labels == i
    cluster_silhouette_vals = silhouette_vals[cluster_mask]
    cluster_silhouette_vals.sort()

    cluster_size = len(cluster_silhouette_vals)
    y_upper = y_lower + cluster_size

    # Store center position for cluster label
    cluster_center = (y_lower + y_upper) / 2
    cluster_avg = float(np.mean(cluster_silhouette_vals))
    cluster_info.append((cluster_center, cluster_avg, cluster_size, i))

    # Add bars for each sample in cluster
    for j, val in enumerate(cluster_silhouette_vals):
        bar_data["x"].append(val / 2)  # Center of bar
        bar_data["y"].append(y_lower + j + 0.5)  # Y position
        bar_data["width"].append(abs(val))  # Width = silhouette value
        bar_data["height"].append(0.85)  # Slightly less than 1 for gap
        bar_data["color"].append(colors[i])

    y_lower = y_upper + 15  # Gap between clusters

# Create figure
p = figure(
    width=4800,
    height=2700,
    title="silhouette-basic · bokeh · pyplots.ai",
    x_axis_label="Silhouette Coefficient",
    y_axis_label="Cluster (samples sorted by silhouette score)",
    x_range=(-0.3, 1.25),
    y_range=(0, y_lower + 5),
    tools="",
)

# Style the figure - larger text for 4800x2700 canvas
p.title.text_font_size = "42pt"
p.title.text_font_style = "bold"
p.xaxis.axis_label_text_font_size = "32pt"
p.yaxis.axis_label_text_font_size = "32pt"
p.xaxis.major_label_text_font_size = "24pt"
p.yaxis.major_label_text_font_size = "24pt"
p.xaxis.axis_label_standoff = 25
p.yaxis.axis_label_standoff = 25

# Create data source for bars
source = ColumnDataSource(data=bar_data)

# Draw horizontal bars using hbar for proper horizontal bar rendering
p.rect(x="x", y="y", width="width", height="height", color="color", source=source, line_color=None, alpha=0.85)

# Add vertical line for average silhouette score
avg_line = Span(location=avg_silhouette, dimension="height", line_color="#E74C3C", line_width=5, line_dash="dashed")
p.add_layout(avg_line)

# Add average silhouette score label at top
avg_label = Label(
    x=avg_silhouette + 0.03,
    y=y_lower - 5,
    text=f"Average: {avg_silhouette:.3f}",
    text_font_size="28pt",
    text_color="#E74C3C",
    text_font_style="bold",
)
p.add_layout(avg_label)

# Add cluster labels with their average silhouette scores - positioned to avoid overlap
for center_y, cluster_avg, size, cluster_idx in cluster_info:
    # Position label to the left side, outside the bars
    cluster_label = Label(
        x=-0.22,
        y=center_y,
        text=f"Cluster {cluster_idx}",
        text_font_size="26pt",
        text_color=colors[cluster_idx],
        text_font_style="bold",
        text_align="left",
        text_baseline="middle",
    )
    p.add_layout(cluster_label)

    # Add cluster stats on the right side
    stats_label = Label(
        x=1.01,
        y=center_y,
        text=f"n={size}, avg={cluster_avg:.2f}",
        text_font_size="22pt",
        text_color=colors[cluster_idx],
        text_font_style="normal",
        text_align="left",
        text_baseline="middle",
    )
    p.add_layout(stats_label)

# Style grid
p.xgrid.grid_line_alpha = 0.3
p.ygrid.grid_line_alpha = 0.0  # No horizontal grid
p.xgrid.grid_line_dash = [6, 4]

# Remove y-axis ticks (sample indices are not meaningful)
p.yaxis.major_tick_line_color = None
p.yaxis.minor_tick_line_color = None
p.yaxis.major_label_text_font_size = "0pt"

# Add vertical line at x=0 for reference
zero_line = Span(location=0, dimension="height", line_color="#666666", line_width=2, line_alpha=0.5)
p.add_layout(zero_line)

# Background
p.background_fill_color = "#fafafa"
p.border_fill_color = "#ffffff"
p.outline_line_color = None

# Save as PNG and HTML
export_png(p, filename="plot.png")

output_file("plot.html")
save(p)
