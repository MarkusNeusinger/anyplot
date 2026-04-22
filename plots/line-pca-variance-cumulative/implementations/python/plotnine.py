""" pyplots.ai
line-pca-variance-cumulative: Cumulative Explained Variance for PCA Component Selection
Library: plotnine 0.15.3 | Python 3.14.3
Quality: 87/100 | Created: 2026-02-17
"""

import numpy as np
import pandas as pd
from plotnine import (
    aes,
    annotate,
    element_blank,
    element_line,
    element_rect,
    element_text,
    geom_col,
    geom_hline,
    geom_line,
    geom_point,
    geom_segment,
    geom_text,
    ggplot,
    labs,
    scale_color_identity,
    scale_fill_identity,
    scale_x_continuous,
    scale_y_continuous,
    theme,
    theme_minimal,
)
from sklearn.datasets import load_wine
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler


# Data - PCA on the Wine dataset (13 features)
X_scaled = StandardScaler().fit_transform(load_wine().data)
pca = PCA().fit(X_scaled)

n_components = np.arange(1, len(pca.explained_variance_ratio_) + 1)
cumulative_var = np.cumsum(pca.explained_variance_ratio_) * 100
individual_var = pca.explained_variance_ratio_ * 100

df = pd.DataFrame({"component": n_components, "cumulative": cumulative_var, "individual": individual_var})

# Elbow detection via maximum second-derivative change
diffs = np.diff(cumulative_var)
elbow_idx = int(np.argmax(np.abs(np.diff(diffs)))) + 1
elbow_c = int(n_components[elbow_idx])
elbow_v = cumulative_var[elbow_idx]
elbow_df = pd.DataFrame({"component": [elbow_c], "cumulative": [elbow_v]})

# Threshold reference data — staggered x-positions to prevent label crowding
thresholds = pd.DataFrame(
    {
        "y": [90.0, 95.0, 99.0],
        "label": ["90%", "95%", "99%"],
        "color": ["#E65100", "#2E7D32", "#1565C0"],
        "x": [12.3, 12.3, 12.3],
    }
)

# Plot
plot = (
    ggplot(df, aes(x="component", y="cumulative"))
    # Shaded threshold bands with distinct tints
    + annotate("rect", xmin=0.3, xmax=13.7, ymin=90, ymax=95, fill="#FFF3E0", alpha=0.35)
    + annotate("rect", xmin=0.3, xmax=13.7, ymin=95, ymax=99, fill="#E8F5E9", alpha=0.35)
    + annotate("rect", xmin=0.3, xmax=13.7, ymin=99, ymax=102, fill="#E3F2FD", alpha=0.3)
    # Threshold dashed lines
    + geom_hline(yintercept=90.0, linetype="dashed", color="#E65100", size=0.7, alpha=0.5)
    + geom_hline(yintercept=95.0, linetype="dashed", color="#2E7D32", size=0.7, alpha=0.5)
    + geom_hline(yintercept=99.0, linetype="dashed", color="#1565C0", size=0.7, alpha=0.5)
    # Individual variance as translucent bars — fills the lower portion meaningfully
    + geom_col(aes(y="individual", fill=["#306998"] * len(df)), width=0.5, alpha=0.2, show_legend=False)
    + scale_fill_identity()
    # Vertical drop-line from elbow point to x-axis
    + geom_segment(
        data=elbow_df,
        mapping=aes(x="component", xend="component", y=0, yend="cumulative"),
        linetype="dotted",
        color="#D84315",
        size=0.7,
        alpha=0.5,
    )
    # Main cumulative line
    + geom_line(color="#306998", size=1.5)
    # Data point markers — white-filled circles
    + geom_point(color="#306998", size=4, fill="white", stroke=1.5, shape="o")
    # Highlighted elbow point
    + geom_point(
        data=elbow_df,
        mapping=aes(x="component", y="cumulative"),
        color="#D84315",
        size=7,
        fill="#FF8A65",
        stroke=2.2,
        shape="o",
    )
    # Elbow annotation
    + geom_text(
        data=elbow_df,
        mapping=aes(x="component", y="cumulative", label=[f"Elbow: {elbow_c} components\n({elbow_v:.1f}% variance)"]),
        ha="left",
        va="bottom",
        size=10,
        color="#D84315",
        fontweight="bold",
        nudge_x=0.5,
        nudge_y=3.0,
    )
    # Threshold labels — right-aligned at the plot edge to avoid crowding
    + geom_text(
        data=thresholds,
        mapping=aes(x="x", y="y", label="label", color="color"),
        ha="right",
        va="bottom",
        size=9,
        fontweight="bold",
        nudge_y=0.5,
        show_legend=False,
    )
    + scale_color_identity()
    # Scales
    + scale_x_continuous(breaks=n_components, labels=[str(i) for i in n_components], expand=(0.02, 0.4))
    + scale_y_continuous(
        limits=(0, 102), breaks=[0, 20, 40, 60, 80, 100], labels=["0%", "20%", "40%", "60%", "80%", "100%"]
    )
    + labs(
        x="Number of Principal Components",
        y="Cumulative Explained Variance (%)",
        title="line-pca-variance-cumulative · plotnine · pyplots.ai",
    )
    + theme_minimal()
    + theme(
        figure_size=(16, 9),
        text=element_text(size=14, color="#333333"),
        axis_title=element_text(size=20, color="#444444", face="bold"),
        axis_text=element_text(size=16, color="#555555"),
        plot_title=element_text(size=24, color="#222222", face="bold", ha="left"),
        panel_grid_major_x=element_blank(),
        panel_grid_minor=element_blank(),
        panel_grid_major_y=element_line(color="#E0E0E0", size=0.3, alpha=0.4),
        plot_background=element_rect(fill="white", color="white"),
        panel_background=element_rect(fill="#FAFAFA", color="#EEEEEE", size=0.3),
        axis_line_x=element_line(color="#BBBBBB", size=0.5),
        axis_ticks_major_x=element_line(color="#BBBBBB", size=0.4),
        plot_margin=0.02,
    )
)

# Save
plot.save("plot.png", dpi=300, verbose=False)
