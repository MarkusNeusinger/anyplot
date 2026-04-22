""" pyplots.ai
elbow-curve: Elbow Curve for K-Means Clustering
Library: plotnine 0.15.2 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-26
"""

import numpy as np
import pandas as pd
from plotnine import (
    aes,
    annotate,
    element_line,
    element_text,
    geom_line,
    geom_point,
    geom_vline,
    ggplot,
    labs,
    theme,
    theme_minimal,
)


# Data - Simulate realistic K-means inertia values
# Inertia decreases as k increases, with diminishing returns after optimal k
np.random.seed(42)

k_values = list(range(1, 11))

# Simulate inertia values that show clear elbow at k=4
# Formula: base decay curve + noise
base_inertias = [1000, 500, 280, 150, 120, 100, 85, 75, 68, 62]
noise = np.random.uniform(-5, 5, len(k_values))
inertias = [max(10, base + n) for base, n in zip(base_inertias, noise, strict=True)]

# Create DataFrame for plotting
df = pd.DataFrame({"k": k_values, "inertia": inertias})

# Optimal k (elbow point)
optimal_k = 4

# Plot
plot = (
    ggplot(df, aes(x="k", y="inertia"))
    + geom_line(color="#306998", size=2, alpha=0.9)
    + geom_point(color="#306998", size=5, alpha=1.0)
    + geom_vline(xintercept=optimal_k, linetype="dashed", color="#FFD43B", size=1.5, alpha=0.8)
    + annotate(
        "text",
        x=optimal_k + 0.5,
        y=inertias[optimal_k - 1] + 80,
        label=f"Optimal k = {optimal_k}",
        size=14,
        color="#FFD43B",
        ha="left",
        fontweight="bold",
    )
    + labs(
        title="elbow-curve · plotnine · pyplots.ai",
        x="Number of Clusters (k)",
        y="Inertia (Within-Cluster Sum of Squares)",
    )
    + theme_minimal()
    + theme(
        figure_size=(16, 9),
        plot_title=element_text(size=24, weight="bold"),
        axis_title=element_text(size=20),
        axis_text=element_text(size=16),
        panel_grid_major=element_line(color="#CCCCCC", size=0.5, alpha=0.3),
    )
)

# Save
plot.save("plot.png", dpi=300, verbose=False)
