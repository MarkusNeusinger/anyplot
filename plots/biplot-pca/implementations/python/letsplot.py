""" pyplots.ai
biplot-pca: PCA Biplot with Scores and Loading Vectors
Library: letsplot 4.8.2 | Python 3.13.11
Quality: 91/100 | Created: 2026-01-09
"""

import numpy as np
import pandas as pd
from lets_plot import *  # noqa: F403
from lets_plot.export import ggsave as export_ggsave
from sklearn.datasets import load_iris
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler


LetsPlot.setup_html()  # noqa: F405

# Load Iris dataset
iris = load_iris()
X = iris.data
y = iris.target
feature_names = iris.feature_names
target_names = iris.target_names

# Standardize features
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

# Perform PCA
pca = PCA(n_components=2)
scores = pca.fit_transform(X_scaled)
loadings = pca.components_.T  # Variables x Components

# Variance explained
var_explained = pca.explained_variance_ratio_ * 100

# Create dataframe for scores
scores_df = pd.DataFrame({"PC1": scores[:, 0], "PC2": scores[:, 1], "Species": [target_names[i] for i in y]})

# Scale loadings for visibility alongside scores
score_range = max(np.abs(scores).max(), 1)
loading_scale = score_range * 1.5

# Create dataframe for loading arrows
clean_names = ["Sepal Length", "Sepal Width", "Petal Length", "Petal Width"]
loadings_df = pd.DataFrame(
    {
        "x_start": [0] * len(feature_names),
        "y_start": [0] * len(feature_names),
        "x_end": loadings[:, 0] * loading_scale,
        "y_end": loadings[:, 1] * loading_scale,
        "variable": clean_names,
    }
)

# Label positions with smart offset to avoid overlap
# Petal Length and Petal Width have similar directions, so we offset them differently
label_offsets = []
for i, name in enumerate(clean_names):
    x_end = loadings_df["x_end"].iloc[i]
    y_end = loadings_df["y_end"].iloc[i]
    if name == "Petal Width":
        # Offset Petal Width label upward to avoid overlap with Petal Length
        label_offsets.append((x_end * 1.15, y_end * 1.15 + 0.4))
    elif name == "Petal Length":
        # Offset Petal Length label downward
        label_offsets.append((x_end * 1.15, y_end * 1.15 - 0.3))
    else:
        # Default offset for other labels
        label_offsets.append((x_end * 1.15, y_end * 1.15))

loadings_df["label_x"] = [offset[0] for offset in label_offsets]
loadings_df["label_y"] = [offset[1] for offset in label_offsets]

# Colorblind-safe palette (blue, orange, purple - distinguishable for all color vision types)
colors = ["#0077BB", "#EE7733", "#AA3377"]

# Build the plot
plot = (
    ggplot()  # noqa: F405
    + geom_point(  # noqa: F405
        data=scores_df,
        mapping=aes(x="PC1", y="PC2", color="Species"),  # noqa: F405
        size=5,
        alpha=0.8,
    )
    + geom_segment(  # noqa: F405
        data=loadings_df,
        mapping=aes(x="x_start", y="y_start", xend="x_end", yend="y_end"),  # noqa: F405
        color="#333333",
        size=1.8,
        arrow=arrow(length=15, type="open"),  # noqa: F405
    )
    + geom_text(  # noqa: F405
        data=loadings_df,
        mapping=aes(x="label_x", y="label_y", label="variable"),  # noqa: F405
        size=14,
        color="#333333",
    )
    + geom_hline(yintercept=0, color="gray", size=0.5, linetype="dashed", alpha=0.5)  # noqa: F405
    + geom_vline(xintercept=0, color="gray", size=0.5, linetype="dashed", alpha=0.5)  # noqa: F405
    + labs(  # noqa: F405
        x=f"PC1 ({var_explained[0]:.1f}%)",
        y=f"PC2 ({var_explained[1]:.1f}%)",
        title="biplot-pca · letsplot · pyplots.ai",
        color="Species",
    )
    + scale_color_manual(values=colors)  # noqa: F405
    + scale_x_continuous(expand=[0.15, 0.15])  # noqa: F405
    + scale_y_continuous(expand=[0.15, 0.15])  # noqa: F405
    + theme_minimal()  # noqa: F405
    + theme(  # noqa: F405
        plot_title=element_text(size=24),  # noqa: F405
        axis_title=element_text(size=20),  # noqa: F405
        axis_text=element_text(size=16),  # noqa: F405
        legend_title=element_text(size=18),  # noqa: F405
        legend_text=element_text(size=16),  # noqa: F405
    )
    + ggsize(1600, 900)  # noqa: F405
)

# Save PNG (scale 3x for 4800x2700)
export_ggsave(plot, filename="plot.png", path=".", scale=3)

# Save HTML for interactivity
export_ggsave(plot, filename="plot.html", path=".")
