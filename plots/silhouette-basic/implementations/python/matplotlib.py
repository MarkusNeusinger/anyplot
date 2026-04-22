""" pyplots.ai
silhouette-basic: Silhouette Plot
Library: matplotlib 3.10.8 | Python 3.13.11
Quality: 92/100 | Created: 2025-12-26
"""

import matplotlib.pyplot as plt
import numpy as np
from sklearn.cluster import KMeans
from sklearn.datasets import load_iris
from sklearn.metrics import silhouette_samples, silhouette_score


# Data - use iris dataset for realistic clustering example
np.random.seed(42)
iris = load_iris()
X = iris.data
n_clusters = 3

# Perform clustering
kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
cluster_labels = kmeans.fit_predict(X)

# Calculate silhouette scores
silhouette_avg = silhouette_score(X, cluster_labels)
sample_silhouette_values = silhouette_samples(X, cluster_labels)

# Create plot
fig, ax = plt.subplots(figsize=(16, 9))

# Colors for clusters - Python Blue first, then yellow and accessible colors
colors = ["#306998", "#FFD43B", "#2ca02c"]

y_lower = 10
for i in range(n_clusters):
    # Get silhouette values for cluster i and sort them
    ith_cluster_silhouette_values = sample_silhouette_values[cluster_labels == i]
    ith_cluster_silhouette_values.sort()

    size_cluster_i = ith_cluster_silhouette_values.shape[0]
    y_upper = y_lower + size_cluster_i

    # Fill horizontal bars for each sample
    ax.fill_betweenx(
        np.arange(y_lower, y_upper),
        0,
        ith_cluster_silhouette_values,
        facecolor=colors[i],
        edgecolor=colors[i],
        alpha=0.8,
    )

    # Annotate cluster with its average silhouette score
    cluster_avg = np.mean(ith_cluster_silhouette_values)
    ax.text(
        -0.05,
        y_lower + 0.5 * size_cluster_i,
        f"Cluster {i}\n(avg: {cluster_avg:.2f})",
        fontsize=16,
        verticalalignment="center",
        horizontalalignment="right",
    )

    y_lower = y_upper + 10  # Gap between clusters

# Add vertical line for average silhouette score
ax.axvline(x=silhouette_avg, color="#d62728", linestyle="--", linewidth=3, label=f"Average Score: {silhouette_avg:.2f}")

# Styling
ax.set_xlabel("Silhouette Coefficient", fontsize=20)
ax.set_ylabel("Sample Index (by Cluster)", fontsize=20)
ax.set_title("silhouette-basic · matplotlib · pyplots.ai", fontsize=24)

ax.tick_params(axis="both", labelsize=16)
ax.set_xlim([-0.2, 1.0])
ax.set_ylim([0, y_lower])
ax.set_yticks([])  # Hide y-axis ticks as they're not meaningful

ax.legend(fontsize=16, loc="lower right")
ax.grid(True, alpha=0.3, linestyle="--", axis="x")

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
