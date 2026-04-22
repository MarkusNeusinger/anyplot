""" pyplots.ai
silhouette-basic: Silhouette Plot
Library: seaborn 0.13.2 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-26
"""

import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
from sklearn.cluster import KMeans
from sklearn.datasets import load_iris
from sklearn.metrics import silhouette_samples, silhouette_score


# Set random seed for reproducibility
np.random.seed(42)

# Load iris dataset for realistic example
iris = load_iris()
X = iris.data

# Perform K-means clustering with 3 clusters
n_clusters = 3
kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
cluster_labels = kmeans.fit_predict(X)

# Calculate silhouette scores
silhouette_vals = silhouette_samples(X, cluster_labels)
avg_score = silhouette_score(X, cluster_labels)

# Create figure
fig, ax = plt.subplots(figsize=(16, 9))

# Define colors using Python palette first, then colorblind-safe
colors = ["#306998", "#FFD43B", "#4DAF4A"]

y_lower = 10
cluster_info = []

for i in range(n_clusters):
    # Get silhouette values for cluster i
    cluster_silhouette_vals = silhouette_vals[cluster_labels == i]
    cluster_silhouette_vals.sort()

    cluster_size = len(cluster_silhouette_vals)
    y_upper = y_lower + cluster_size

    # Create horizontal bar chart for this cluster
    y_positions = np.arange(y_lower, y_upper)

    ax.barh(
        y_positions,
        cluster_silhouette_vals,
        height=1.0,
        color=colors[i],
        edgecolor=colors[i],
        alpha=0.8,
        label=f"Cluster {i}",
    )

    # Calculate cluster average
    cluster_avg = np.mean(cluster_silhouette_vals)
    cluster_info.append((i, cluster_avg, (y_lower + y_upper) / 2))

    y_lower = y_upper + 10  # Gap between clusters

# Add vertical line for average silhouette score
ax.axvline(x=avg_score, color="#E31A1C", linestyle="--", linewidth=3, label=f"Average: {avg_score:.3f}")

# Annotate each cluster with its average score (positioned to avoid overlap)
for cluster_id, cluster_avg, y_center in cluster_info:
    # Position annotation at right edge for visibility
    ax.annotate(
        f"Avg: {cluster_avg:.3f}",
        xy=(0.92, y_center),
        fontsize=16,
        fontweight="bold",
        color=colors[cluster_id],
        va="center",
        ha="left",
    )

# Style the plot using seaborn
sns.despine(left=True, bottom=False)
ax.set_xlim([-0.1, 1.0])
ax.set_xlabel("Silhouette Coefficient", fontsize=20)
ax.set_ylabel("Samples (grouped by cluster)", fontsize=20)
ax.set_title("silhouette-basic · seaborn · pyplots.ai", fontsize=24, fontweight="bold")
ax.tick_params(axis="both", labelsize=16)
ax.set_yticks([])  # Hide y-axis ticks as samples are grouped

# Add legend
ax.legend(loc="lower right", fontsize=16, framealpha=0.9)

# Add subtle grid for x-axis
ax.grid(axis="x", alpha=0.3, linestyle="--")

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
