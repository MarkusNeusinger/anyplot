""" pyplots.ai
silhouette-basic: Silhouette Plot
Library: plotnine 0.15.2 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-26
"""

import numpy as np
import pandas as pd
from plotnine import (
    aes,
    element_blank,
    element_text,
    geom_segment,
    geom_text,
    geom_vline,
    ggplot,
    labs,
    scale_color_manual,
    theme,
    theme_minimal,
    xlim,
)
from sklearn.cluster import KMeans
from sklearn.datasets import load_iris
from sklearn.metrics import silhouette_samples, silhouette_score


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

colors = ["#306998", "#FFD43B", "#2ca02c"]  # Python Blue, Python Yellow, Green

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
        data_rows.append({"y": y_position, "silhouette": sil_val, "cluster": f"Cluster {cluster_idx}"})
        y_position += 1

    cluster_end = y_position - 1
    cluster_centers.append((cluster_start + cluster_end) / 2)

    # Add small gap between clusters
    y_position += 8

df = pd.DataFrame(data_rows)
df["x_start"] = 0  # Starting x position for horizontal bars

# Create annotation dataframe for cluster labels
annotation_df = pd.DataFrame(
    {
        "y": cluster_centers,
        "x": [-0.08] * n_clusters,
        "label": [f"Cluster {i}\n(avg: {cluster_avg_scores[i]:.2f})" for i in range(n_clusters)],
    }
)

# Create average line label dataframe
avg_label_df = pd.DataFrame(
    {"x": [avg_silhouette + 0.02], "y": [max(df["y"]) * 0.95], "label": [f"Avg: {avg_silhouette:.2f}"]}
)

# Create the silhouette plot using horizontal segments
plot = (
    ggplot()
    + geom_segment(aes(x="x_start", xend="silhouette", y="y", yend="y", color="cluster"), data=df, size=1.5)
    + geom_vline(xintercept=avg_silhouette, color="#d62728", linetype="dashed", size=1.2)
    + geom_text(aes(x="x", y="y", label="label"), data=annotation_df, size=12, ha="right")
    + geom_text(aes(x="x", y="y", label="label"), data=avg_label_df, size=11, ha="left")
    + scale_color_manual(values=colors)
    + labs(
        x="Silhouette Coefficient",
        y="Sample Index (sorted within cluster)",
        title="silhouette-basic · plotnine · pyplots.ai",
    )
    + xlim(-0.25, 1.0)
    + theme_minimal()
    + theme(
        figure_size=(16, 9),
        plot_title=element_text(size=24),
        axis_title=element_text(size=20),
        axis_text=element_text(size=16),
        axis_text_y=element_blank(),
        axis_ticks_major_y=element_blank(),
        legend_text=element_text(size=16),
        legend_title=element_text(size=18),
        legend_position="right",
        panel_grid_major_y=element_blank(),
        panel_grid_minor_y=element_blank(),
    )
)

# Save as PNG
plot.save("plot.png", dpi=300, verbose=False)
