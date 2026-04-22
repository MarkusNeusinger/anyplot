""" pyplots.ai
silhouette-basic: Silhouette Plot
Library: pygal 3.1.0 | Python 3.13.11
Quality: 88/100 | Created: 2025-12-26
"""

import numpy as np
import pygal
from pygal.style import Style
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_samples, silhouette_score


# Data - Synthetic clustering data designed to show both positive and negative silhouettes
np.random.seed(42)

# Create 3 clusters with deliberate overlap to generate negative silhouette values
# Cluster 0: tight cluster at origin
# Cluster 1: well-separated cluster
# Cluster 2: overlaps significantly with cluster 0 to create misclassified samples
n_samples_per_cluster = 50
cluster0 = np.random.randn(n_samples_per_cluster, 2) * 0.6 + np.array([0, 0])
cluster1 = np.random.randn(n_samples_per_cluster, 2) * 0.7 + np.array([4, 4])
cluster2 = np.random.randn(n_samples_per_cluster, 2) * 1.0 + np.array([0.8, 0.3])  # Heavy overlap with cluster0
X = np.vstack([cluster0, cluster1, cluster2])

# Cluster the data
kmeans = KMeans(n_clusters=3, random_state=42, n_init=10)
cluster_labels = kmeans.fit_predict(X)

# Compute silhouette scores
silhouette_vals = silhouette_samples(X, cluster_labels)
avg_silhouette = silhouette_score(X, cluster_labels)
n_clusters = 3

# Colors for each cluster (Python Blue, Python Yellow, Complementary Red)
cluster_colors = ["#306998", "#FFD43B", "#E74C3C"]

# Custom style for pyplots with prominent grid and reference lines
custom_style = Style(
    background="white",
    plot_background="white",
    foreground="#333333",
    foreground_strong="#000000",  # Bold black for major labels (avg reference)
    foreground_subtle="#666666",  # More visible grid lines
    guide_stroke_color="#999999",  # Darker grid color for visibility
    major_guide_stroke_dasharray="8,4",  # More prominent dashed pattern for avg line
    colors=tuple(cluster_colors),
    title_font_size=48,
    label_font_size=32,
    major_label_font_size=36,  # Larger major labels for avg reference line
    legend_font_size=28,
    value_font_size=24,
    stroke_width=0,
)

# Process and sort silhouette values within each cluster
# Store original averages before any sample reduction
original_cluster_avgs = {}
for i in range(n_clusters):
    cluster_silhouette_vals = silhouette_vals[cluster_labels == i]
    original_cluster_avgs[i] = np.mean(cluster_silhouette_vals)

# Build cluster data with sorted values (descending for visual appeal)
cluster_data = {}
sample_idx = 0
for i in range(n_clusters):
    cluster_silhouette_vals = silhouette_vals[cluster_labels == i]
    cluster_silhouette_vals = np.sort(cluster_silhouette_vals)[::-1]  # Descending
    # Subsample for thicker bars while maintaining pattern
    reduced_vals = cluster_silhouette_vals[::2] if len(cluster_silhouette_vals) > 30 else cluster_silhouette_vals
    cluster_data[i] = {
        "values": reduced_vals,
        "avg": original_cluster_avgs[i],  # Use original average
        "start_idx": sample_idx,
        "size": len(reduced_vals),
    }
    sample_idx += len(reduced_vals)

total_samples = sample_idx

# Build all bars list for chart data with separator gaps between clusters
all_bars = []
separator_count = 3  # Number of empty bars between clusters for visual separation
for i in range(n_clusters):
    for val in cluster_data[i]["values"]:
        all_bars.append((i, val))
    # Add separator gaps after each cluster except the last
    if i < n_clusters - 1:
        for _ in range(separator_count):
            all_bars.append((-1, None))  # -1 indicates separator

chart = pygal.HorizontalBar(
    width=4800,
    height=2700,
    style=custom_style,
    title="silhouette-basic · pygal · pyplots.ai",
    x_title=f"Silhouette Coefficient (avg: {avg_silhouette:.3f})",
    y_title="Samples (grouped by cluster)",
    show_legend=True,
    legend_at_bottom=True,
    legend_at_bottom_columns=3,
    show_y_guides=False,
    show_x_guides=True,
    print_values=False,
    range=(-0.2, 1.0),
    spacing=4,  # Increased spacing between bars
    margin=50,
    margin_bottom=150,
    show_y_labels=False,
    x_labels=[-0.2, 0.0, 0.2, round(avg_silhouette, 2), 0.4, 0.6, 0.8, 1.0],
    x_labels_major=[round(avg_silhouette, 2)],  # Highlight average silhouette value as major
)

# Build data series for each cluster
# Track positions for cluster midpoints (excluding separators)
cluster_positions = {}
pos = 0
for i in range(n_clusters):
    cluster_positions[i] = {"start": pos, "size": cluster_data[i]["size"]}
    pos += cluster_data[i]["size"]
    if i < n_clusters - 1:
        pos += separator_count

for cluster_idx in range(n_clusters):
    cluster_avg = cluster_data[cluster_idx]["avg"]
    cluster_size = cluster_positions[cluster_idx]["size"]
    start_pos = cluster_positions[cluster_idx]["start"]
    mid_point = start_pos + cluster_size // 2

    series_data = []
    for bar_idx, (c, val) in enumerate(all_bars):
        if c == cluster_idx:
            # Annotate at cluster midpoint with cluster average
            if bar_idx == mid_point:
                series_data.append({"value": val, "label": f"Cluster {cluster_idx} avg: {cluster_avg:.3f}"})
            else:
                series_data.append(val)
        else:
            series_data.append(None)

    chart.add(f"Cluster {cluster_idx} (avg: {cluster_avg:.3f})", series_data)

# Save outputs
chart.render_to_file("plot.html")
chart.render_to_png("plot.png")
