""" pyplots.ai
line-pca-variance-cumulative: Cumulative Explained Variance for PCA Component Selection
Library: letsplot 4.8.2 | Python 3.14.3
Quality: 91/100 | Created: 2026-02-17
"""

import numpy as np
import pandas as pd
from lets_plot import *
from sklearn.datasets import load_wine
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler


LetsPlot.setup_html()

# Data - PCA on Wine dataset (13 features)
wine = load_wine()
X = StandardScaler().fit_transform(wine.data)
pca = PCA()
pca.fit(X)

n_components = np.arange(1, len(pca.explained_variance_ratio_) + 1)
individual_variance = pca.explained_variance_ratio_ * 100
cumulative_variance = np.cumsum(individual_variance)

df_cumulative = pd.DataFrame({"Component": n_components, "Cumulative Variance (%)": cumulative_variance})

df_individual = pd.DataFrame({"Component": n_components, "Individual Variance (%)": individual_variance})

# Threshold lines
threshold_90 = 90.0
threshold_95 = 95.0

# Find components needed for each threshold
components_for_90 = int(n_components[cumulative_variance >= threshold_90][0])
components_for_95 = int(n_components[cumulative_variance >= threshold_95][0])

# Plot
plot = (
    ggplot()
    + geom_bar(
        data=df_individual,
        mapping=aes(x="Component", y="Individual Variance (%)"),
        stat="identity",
        fill="#B0C4DE",
        alpha=0.5,
        width=0.6,
    )
    + geom_line(data=df_cumulative, mapping=aes(x="Component", y="Cumulative Variance (%)"), size=2.5, color="#306998")
    + geom_point(
        data=df_cumulative, mapping=aes(x="Component", y="Cumulative Variance (%)"), size=6, color="#306998", alpha=0.9
    )
    + geom_hline(yintercept=threshold_90, linetype="dashed", color="#E07A3A", size=1.2, alpha=0.8)
    + geom_hline(yintercept=threshold_95, linetype="dashed", color="#C0392B", size=1.2, alpha=0.8)
    + geom_text(
        data=pd.DataFrame({"x": [13], "y": [threshold_90 + 1.2], "label": ["90%"]}),
        mapping=aes(x="x", y="y", label="label"),
        color="#E07A3A",
        size=14,
        hjust=1,
    )
    + geom_text(
        data=pd.DataFrame({"x": [13], "y": [threshold_95 + 1.2], "label": ["95%"]}),
        mapping=aes(x="x", y="y", label="label"),
        color="#C0392B",
        size=14,
        hjust=1,
    )
    + geom_vline(xintercept=components_for_90, linetype="dotted", color="#E07A3A", size=1, alpha=0.5)
    + geom_vline(xintercept=components_for_95, linetype="dotted", color="#C0392B", size=1, alpha=0.5)
    + scale_x_continuous(breaks=list(n_components))
    + scale_y_continuous(breaks=list(range(0, 101, 10)), limits=[0, 105])
    + labs(
        title="line-pca-variance-cumulative · letsplot · pyplots.ai",
        x="Number of Principal Components",
        y="Explained Variance (%)",
    )
    + theme_minimal()
    + theme(
        plot_title=element_text(size=24, face="medium"),
        axis_title=element_text(size=20),
        axis_text=element_text(size=16),
        panel_grid_major_x=element_blank(),
        panel_grid_minor=element_blank(),
        panel_grid_major_y=element_line(color="#E0E0E0", size=0.4),
    )
    + ggsize(1600, 900)
)

# Save
ggsave(plot, "plot.png", path=".", scale=3)
ggsave(plot, "plot.html", path=".")
