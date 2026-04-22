""" pyplots.ai
elbow-curve: Elbow Curve for K-Means Clustering
Library: altair 6.0.0 | Python 3.13.11
Quality: 92/100 | Created: 2025-12-26
"""

import altair as alt
import numpy as np
import pandas as pd


# Data - Simulate K-means inertia values with realistic decay
np.random.seed(42)
k_values = list(range(1, 12))

# Realistic inertia: sharp drop initially, then diminishing returns
# Using exponential decay with noise
base_inertia = 5000
inertia = []
for k in k_values:
    decay = base_inertia * np.exp(-0.35 * (k - 1)) + 200
    noise = np.random.uniform(-50, 50)
    inertia.append(max(decay + noise, 150))

# Mark optimal k (elbow point at k=4)
optimal_k = 4

df = pd.DataFrame({"Number of Clusters (k)": k_values, "Inertia (Within-Cluster Sum of Squares)": inertia})

# Create base line chart
line = (
    alt.Chart(df)
    .mark_line(color="#306998", strokeWidth=4)
    .encode(
        x=alt.X(
            "Number of Clusters (k):Q",
            scale=alt.Scale(domain=[0.5, 11.5]),
            axis=alt.Axis(tickCount=11, values=k_values),
        ),
        y=alt.Y("Inertia (Within-Cluster Sum of Squares):Q", scale=alt.Scale(domain=[0, max(inertia) * 1.1])),
    )
)

# Add points at each k value
points = (
    alt.Chart(df)
    .mark_point(size=300, color="#306998", filled=True)
    .encode(
        x="Number of Clusters (k):Q",
        y="Inertia (Within-Cluster Sum of Squares):Q",
        tooltip=["Number of Clusters (k)", "Inertia (Within-Cluster Sum of Squares)"],
    )
)

# Highlight the elbow point (optimal k)
elbow_df = df[df["Number of Clusters (k)"] == optimal_k]
elbow_point = (
    alt.Chart(elbow_df)
    .mark_point(size=600, color="#FFD43B", filled=True, stroke="#306998", strokeWidth=3)
    .encode(x="Number of Clusters (k):Q", y="Inertia (Within-Cluster Sum of Squares):Q")
)

# Add annotation for elbow point
elbow_text = (
    alt.Chart(elbow_df)
    .mark_text(align="left", baseline="bottom", dx=15, dy=-15, fontSize=20, fontWeight="bold", color="#306998")
    .encode(
        x="Number of Clusters (k):Q",
        y="Inertia (Within-Cluster Sum of Squares):Q",
        text=alt.value(f"Optimal k = {optimal_k}"),
    )
)

# Combine layers
chart = (
    (line + points + elbow_point + elbow_text)
    .properties(
        width=1600, height=900, title=alt.Title("elbow-curve · altair · pyplots.ai", fontSize=28, anchor="middle")
    )
    .configure_axis(labelFontSize=18, titleFontSize=22, gridColor="#CCCCCC", gridOpacity=0.3)
    .configure_view(strokeWidth=0)
)

# Save outputs
chart.save("plot.png", scale_factor=3.0)
chart.save("plot.html")
