""" anyplot.ai
silhouette-basic: Silhouette Plot
Library: plotnine 0.15.4 | Python 3.13.13
Quality: 89/100 | Updated: 2026-05-10
"""

import os

import numpy as np
import pandas as pd
from plotnine import (
    aes,
    element_blank,
    element_line,
    element_rect,
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


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Okabe-Ito palette
IMPRINT = ["#009E73", "#C475FD", "#4467A3"]

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
    + geom_vline(xintercept=avg_silhouette, color=INK_SOFT, linetype="dashed", size=1.2, alpha=0.6)
    + geom_text(aes(x="x", y="y", label="label"), data=annotation_df, size=12, ha="right", color=INK_SOFT)
    + geom_text(aes(x="x", y="y", label="label"), data=avg_label_df, size=11, ha="left", color=INK_SOFT)
    + scale_color_manual(values=IMPRINT)
    + labs(
        x="Silhouette Coefficient",
        y="Sample Index (sorted within cluster)",
        title="silhouette-basic · plotnine · anyplot.ai",
    )
    + xlim(-0.25, 1.0)
    + theme_minimal()
    + theme(
        figure_size=(16, 9),
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG),
        panel_grid_major_y=element_blank(),
        panel_grid_minor_y=element_blank(),
        panel_grid_major_x=element_line(color=INK, size=0.3, alpha=0.10),
        panel_grid_minor_x=element_line(color=INK, size=0.2, alpha=0.05),
        panel_border=element_rect(color=INK_SOFT, fill=None, size=0.5),
        plot_title=element_text(size=24, color=INK),
        axis_title=element_text(size=20, color=INK),
        axis_text_x=element_text(size=16, color=INK_SOFT),
        axis_text_y=element_blank(),
        axis_ticks_major_y=element_blank(),
        legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT),
        legend_text=element_text(size=16, color=INK_SOFT),
        legend_title=element_text(size=18, color=INK),
        legend_position="right",
    )
)

# Save as PNG
plot.save(f"plot-{THEME}.png", dpi=300, verbose=False)
