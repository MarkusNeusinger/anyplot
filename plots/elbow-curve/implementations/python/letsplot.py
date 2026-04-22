""" pyplots.ai
elbow-curve: Elbow Curve for K-Means Clustering
Library: letsplot 4.8.2 | Python 3.13.11
Quality: 92/100 | Created: 2025-12-26
"""

import numpy as np
import pandas as pd
from lets_plot import *


LetsPlot.setup_html()

# Simulated K-means inertia values showing typical elbow curve pattern
# Data represents clustering analysis on customer segmentation dataset
np.random.seed(42)

k_values = list(range(1, 11))

# Realistic inertia values that show clear elbow at k=4
# Inertia decreases sharply until k=4, then diminishing returns
inertias = [
    12500,  # k=1: all points in one cluster
    6800,  # k=2: significant drop
    3900,  # k=3: still improving
    2100,  # k=4: elbow point (optimal)
    1800,  # k=5: diminishing returns start
    1550,  # k=6
    1380,  # k=7
    1250,  # k=8
    1150,  # k=9
    1080,  # k=10
]

# Create DataFrame for plotting
df = pd.DataFrame({"k": k_values, "Inertia": inertias})

# Optimal k (elbow point)
optimal_k = 4

# Create elbow curve plot
plot = (
    ggplot(df, aes(x="k", y="Inertia"))
    + geom_line(size=2, color="#306998")
    + geom_point(size=6, color="#306998", alpha=0.9)
    + geom_point(data=df[df["k"] == optimal_k], mapping=aes(x="k", y="Inertia"), size=10, color="#FFD43B", shape=18)
    + geom_vline(xintercept=optimal_k, linetype="dashed", color="#FFD43B", size=1.5, alpha=0.7)
    + labs(
        title="elbow-curve · letsplot · pyplots.ai",
        x="Number of Clusters (k)",
        y="Inertia (Within-Cluster Sum of Squares)",
    )
    + scale_x_continuous(breaks=k_values)
    + theme_minimal()
    + theme(
        plot_title=element_text(size=28, face="bold"),
        axis_title=element_text(size=22),
        axis_text=element_text(size=18),
        panel_grid_major=element_line(color="#CCCCCC", size=0.5),
        panel_grid_minor=element_blank(),
    )
    + ggsize(1600, 900)
)

# Save as PNG (scale 3x for 4800x2700)
ggsave(plot, "plot.png", path=".", scale=3)

# Save interactive HTML
ggsave(plot, "plot.html", path=".")
