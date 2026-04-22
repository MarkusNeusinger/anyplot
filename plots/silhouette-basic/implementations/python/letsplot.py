""" pyplots.ai
silhouette-basic: Silhouette Plot
Library: letsplot 4.8.2 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-26
"""

import numpy as np
import pandas as pd
from lets_plot import *
from sklearn.cluster import KMeans
from sklearn.datasets import load_iris
from sklearn.metrics import silhouette_samples, silhouette_score


LetsPlot.setup_html()

# Data - Clustering iris dataset into 3 groups
np.random.seed(42)
iris = load_iris()
X = iris.data
n_clusters = 3

# Perform K-means clustering
kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
cluster_labels = kmeans.fit_predict(X)

# Calculate silhouette scores
silhouette_vals = silhouette_samples(X, cluster_labels)
avg_silhouette = silhouette_score(X, cluster_labels)

# Build dataframe for plotting - sort samples within each cluster by silhouette score
data_rows = []
y_position = 0
cluster_centers = []
cluster_avg_scores = []

colors = ["#306998", "#FFD43B", "#DC2626"]  # Python Blue, Python Yellow, Red

for cluster_idx in range(n_clusters):
    # Get samples in this cluster
    mask = cluster_labels == cluster_idx
    cluster_silhouettes = silhouette_vals[mask]
    cluster_silhouettes_sorted = np.sort(cluster_silhouettes)

    # Calculate cluster average
    cluster_avg = cluster_silhouettes.mean()
    cluster_avg_scores.append(cluster_avg)

    # Track the center position for annotation
    cluster_start = y_position

    # Add each sample as a row
    for sil_val in cluster_silhouettes_sorted:
        data_rows.append(
            {"y": y_position, "silhouette": sil_val, "cluster": f"Cluster {cluster_idx}", "cluster_idx": cluster_idx}
        )
        y_position += 1

    cluster_end = y_position - 1
    cluster_centers.append((cluster_start + cluster_end) / 2)

    # Add small gap between clusters
    y_position += 5

df = pd.DataFrame(data_rows)
df["x_start"] = 0  # Starting x position for horizontal bars

# Create annotation dataframe for cluster labels
annotation_df = pd.DataFrame(
    {
        "y": cluster_centers,
        "x": [-0.12] * n_clusters,
        "label": [f"Cluster {i}\n(avg: {cluster_avg_scores[i]:.2f})" for i in range(n_clusters)],
    }
)

# Create the silhouette plot using horizontal bars
plot = (
    ggplot()
    + geom_segment(aes(x="x_start", xend="silhouette", y="y", yend="y", color="cluster"), data=df, size=1.5)
    + geom_vline(xintercept=avg_silhouette, color="#333333", linetype="dashed", size=1)
    + geom_text(aes(x="x", y="y", label="label"), data=annotation_df, size=14, hjust=1)
    + scale_color_manual(values=colors)
    + labs(
        x="Silhouette Coefficient",
        y="Sample Index (sorted within cluster)",
        title="silhouette-basic · letsplot · pyplots.ai",
    )
    + xlim(-0.3, 1.0)
    + theme_minimal()
    + theme(
        axis_title=element_text(size=20),
        axis_text=element_text(size=16),
        plot_title=element_text(size=24),
        legend_text=element_text(size=16),
        legend_title=element_text(size=18),
        legend_position="right",
        axis_text_y=element_blank(),
        axis_ticks_y=element_blank(),
        panel_grid_major_y=element_blank(),
        panel_grid_minor_y=element_blank(),
    )
    + ggsize(1600, 900)
)

# Add annotation for average silhouette line
avg_label_df = pd.DataFrame(
    {"x": [avg_silhouette + 0.03], "y": [max(df["y"]) * 0.95], "label": [f"Avg: {avg_silhouette:.2f}"]}
)
plot = plot + geom_text(aes(x="x", y="y", label="label"), data=avg_label_df, size=14, hjust=0)

# Save as PNG (scale 3x to get 4800 x 2700 px)
ggsave(plot, "plot.png", path=".", scale=3)

# Save as HTML for interactive version
ggsave(plot, "plot.html", path=".")
