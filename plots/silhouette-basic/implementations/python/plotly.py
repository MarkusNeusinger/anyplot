""" pyplots.ai
silhouette-basic: Silhouette Plot
Library: plotly 6.5.0 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-26
"""

import numpy as np
import plotly.graph_objects as go
from sklearn.cluster import KMeans
from sklearn.datasets import load_iris
from sklearn.metrics import silhouette_samples, silhouette_score


# Data - load iris dataset and perform clustering
np.random.seed(42)
iris = load_iris()
X = iris.data
n_clusters = 3

# Perform K-means clustering
kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
cluster_labels = kmeans.fit_predict(X)

# Compute silhouette scores
silhouette_vals = silhouette_samples(X, cluster_labels)
silhouette_avg = silhouette_score(X, cluster_labels)

# Colors for clusters (Python blue, Python yellow, and a colorblind-safe third color)
colors = ["#306998", "#FFD43B", "#E84A5F"]

# Create figure
fig = go.Figure()

y_lower = 10
cluster_info = []

for i in range(n_clusters):
    # Get silhouette values for this cluster
    cluster_silhouette_vals = silhouette_vals[cluster_labels == i]
    cluster_silhouette_vals.sort()

    cluster_size = cluster_silhouette_vals.shape[0]
    y_upper = y_lower + cluster_size
    cluster_avg = np.mean(cluster_silhouette_vals)

    # Create y positions for bars
    y_positions = np.arange(y_lower, y_upper)

    # Add horizontal bars for each sample
    fig.add_trace(
        go.Bar(
            x=cluster_silhouette_vals,
            y=y_positions,
            orientation="h",
            marker=dict(color=colors[i], line=dict(width=0)),
            name=f"Cluster {i} (avg: {cluster_avg:.2f})",
            hovertemplate=f"Cluster {i}<br>Silhouette: %{{x:.3f}}<extra></extra>",
        )
    )

    # Store cluster info for annotation
    cluster_info.append({"y_center": y_lower + 0.5 * cluster_size, "avg": cluster_avg, "cluster": i})

    y_lower = y_upper + 10  # Gap between clusters

# Add vertical line for average silhouette score
fig.add_vline(
    x=silhouette_avg,
    line=dict(color="red", width=3, dash="dash"),
    annotation_text=f"Average: {silhouette_avg:.3f}",
    annotation_position="top",
    annotation_font=dict(size=20, color="red"),
)

# Add vertical line at 0
fig.add_vline(x=0, line=dict(color="gray", width=2))

# Update layout
fig.update_layout(
    title=dict(text="silhouette-basic \u00b7 plotly \u00b7 pyplots.ai", font=dict(size=32), x=0.5, xanchor="center"),
    xaxis=dict(
        title=dict(text="Silhouette Coefficient", font=dict(size=24)),
        tickfont=dict(size=18),
        range=[-0.2, 1.0],
        showgrid=True,
        gridcolor="rgba(0,0,0,0.1)",
        zeroline=True,
        zerolinecolor="gray",
        zerolinewidth=2,
    ),
    yaxis=dict(
        title=dict(text="Samples (grouped by cluster)", font=dict(size=24)),
        tickfont=dict(size=18),
        showticklabels=False,
    ),
    legend=dict(font=dict(size=20), x=0.98, xanchor="right", y=0.98, yanchor="top"),
    template="plotly_white",
    margin=dict(l=100, r=100, t=120, b=100),
    bargap=0,
    showlegend=True,
)

# Add cluster annotations on y-axis
for info in cluster_info:
    fig.add_annotation(
        x=-0.18,
        y=info["y_center"],
        text=f"Cluster {info['cluster']}",
        showarrow=False,
        font=dict(size=18),
        xanchor="center",
    )

# Save as PNG and HTML
fig.write_image("plot.png", width=1600, height=900, scale=3)
fig.write_html("plot.html", include_plotlyjs="cdn")
