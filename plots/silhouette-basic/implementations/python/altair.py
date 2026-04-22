""" pyplots.ai
silhouette-basic: Silhouette Plot
Library: altair 6.0.0 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-26
"""

import altair as alt
import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.datasets import load_iris
from sklearn.metrics import silhouette_samples, silhouette_score


# Data - Use iris dataset for realistic clustering example
np.random.seed(42)
iris = load_iris()
X = iris.data

# Perform K-means clustering with 3 clusters
n_clusters = 3
kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
cluster_labels = kmeans.fit_predict(X)

# Calculate silhouette scores
silhouette_avg = silhouette_score(X, cluster_labels)
sample_silhouette_values = silhouette_samples(X, cluster_labels)

# Build dataframe with samples sorted by cluster and silhouette score
# Horizontal bars: y-axis is sample position, x-axis is silhouette score
records = []
y_lower = 0

for cluster_id in range(n_clusters):
    cluster_mask = cluster_labels == cluster_id
    cluster_silhouette_values = sample_silhouette_values[cluster_mask]
    cluster_silhouette_values.sort()

    cluster_size = len(cluster_silhouette_values)
    cluster_avg = np.mean(cluster_silhouette_values)

    for i, sil_value in enumerate(cluster_silhouette_values):
        records.append(
            {
                "y": y_lower + i,
                "y2": y_lower + i + 0.8,  # Bar thickness
                "silhouette": sil_value,
                "cluster": f"Cluster {cluster_id} (avg: {cluster_avg:.2f})",
                "cluster_id": cluster_id,
            }
        )

    y_lower += cluster_size + 5  # Gap between clusters

df = pd.DataFrame(records)

# Color palette - Python Blue as primary, then distinct colors
colors = ["#306998", "#FFD43B", "#E34C26"]

# Create horizontal silhouette bars using mark_rect for proper horizontal bars
bars = (
    alt.Chart(df)
    .mark_rect()
    .encode(
        x=alt.X("silhouette:Q", title="Silhouette Coefficient", scale=alt.Scale(domain=[-0.15, 1.0])),
        x2=alt.value(0),  # Bars start from 0 and extend to silhouette value
        y=alt.Y("y:Q", axis=None),
        y2="y2:Q",
        color=alt.Color(
            "cluster:N",
            title="Cluster",
            scale=alt.Scale(domain=df["cluster"].unique().tolist(), range=colors),
            legend=alt.Legend(titleFontSize=18, labelFontSize=16, symbolSize=200),
        ),
        tooltip=[
            alt.Tooltip("cluster:N", title="Cluster"),
            alt.Tooltip("silhouette:Q", title="Silhouette Score", format=".3f"),
        ],
    )
)

# Vertical line for average silhouette score
avg_line_data = pd.DataFrame({"avg_silhouette": [silhouette_avg]})
avg_line = (
    alt.Chart(avg_line_data)
    .mark_rule(color="#E63946", strokeWidth=3, strokeDash=[8, 4])
    .encode(
        x=alt.X("avg_silhouette:Q"), tooltip=[alt.Tooltip("avg_silhouette:Q", title="Average Silhouette", format=".3f")]
    )
)

# Annotation for average line
avg_text = (
    alt.Chart(pd.DataFrame({"x": [silhouette_avg + 0.02], "y": [5], "text": [f"Avg: {silhouette_avg:.3f}"]}))
    .mark_text(fontSize=18, fontWeight="bold", color="#E63946", align="left")
    .encode(x="x:Q", y="y:Q", text="text:N")
)

# Combine layers
chart = (
    alt.layer(bars, avg_line, avg_text)
    .properties(width=1600, height=900, title=alt.Title("silhouette-basic · altair · pyplots.ai", fontSize=28))
    .configure_axis(labelFontSize=18, titleFontSize=22)
    .configure_legend(titleFontSize=18, labelFontSize=16)
)

# Save as PNG (4800x2700 at scale_factor=3)
chart.save("plot.png", scale_factor=3.0)

# Save as HTML for interactivity
chart.save("plot.html")
