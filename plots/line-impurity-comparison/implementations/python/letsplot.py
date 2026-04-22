""" pyplots.ai
line-impurity-comparison: Gini Impurity vs Entropy Comparison
Library: letsplot 4.8.2 | Python 3.14.3
Quality: 88/100 | Created: 2026-02-17
"""

import numpy as np
import pandas as pd
from lets_plot import *  # noqa: F403
from lets_plot.export import ggsave as export_ggsave


LetsPlot.setup_html()  # noqa: F405

# Data
p = np.linspace(0, 1, 200)

# Gini impurity: 2 * p * (1 - p)
gini = 2 * p * (1 - p)

# Entropy: -p * log2(p) - (1-p) * log2(1-p), normalized to [0, 1]
with np.errstate(divide="ignore", invalid="ignore"):
    entropy = -p * np.log2(p) - (1 - p) * np.log2(1 - p)
entropy = np.nan_to_num(entropy, nan=0.0)

# Main curves data
df = pd.DataFrame(
    {
        "p": np.tile(p, 2),
        "impurity": np.concatenate([gini, entropy]),
        "metric": ["Gini: 2p(1\u2212p)"] * len(p) + ["Entropy (normalized)"] * len(p),
    }
)

# Shaded region between curves
ribbon_df = pd.DataFrame({"p": p, "gini": gini, "entropy": entropy})

# Marker data for maxima (consolidated into single DataFrame)
markers_df = pd.DataFrame({"p": [0.5, 0.5], "impurity": [1.0, 0.5], "color": ["#e07a2f", "#306998"]})

# Arrow from annotation to peak area (single arrow, no duplicates)
arrow_df = pd.DataFrame({"x": [0.5], "y": [0.93], "xend": [0.5], "yend": [0.86]})

# Annotation data (consolidated into categories)
main_label_df = pd.DataFrame({"p": [0.5], "impurity": [0.97], "label": ["Maximum uncertainty at p = 0.5"]})
region_label_df = pd.DataFrame(
    {"p": [0.72], "impurity": [0.6], "label": ["Shaded region:\ndifference between metrics"]}
)
boundary_df = pd.DataFrame(
    {
        "p": [0.03, 0.95],
        "impurity": [0.06, 0.06],
        "label": ["p \u2192 0: both \u2192 0", "p \u2192 1: both \u2192 0"],
        "hjust": [0.0, 1.0],
    }
)

# Plot
plot = (
    ggplot()  # noqa: F405
    # Shaded ribbon between curves
    + geom_ribbon(  # noqa: F405
        data=ribbon_df,
        mapping=aes(x="p", ymin="gini", ymax="entropy"),  # noqa: F405
        fill="#306998",
        alpha=0.12,
        tooltips="none",
    )
    # Main curves with interactive tooltips (lets-plot distinctive feature)
    + geom_line(  # noqa: F405
        data=df,
        mapping=aes(x="p", y="impurity", color="metric"),  # noqa: F405
        size=2.5,
        tooltips=layer_tooltips()  # noqa: F405
        .format("@p", ".2f")
        .format("@impurity", ".3f")
        .line("@metric")
        .line("p = @p")
        .line("impurity = @impurity"),
    )
    # Vertical guide at p=0.5
    + geom_vline(xintercept=0.5, color="#cccccc", size=0.6, linetype="dashed")  # noqa: F405
    # Arrow from annotation to entropy maximum
    + geom_segment(  # noqa: F405
        aes(x="x", y="y", xend="xend", yend="yend"),  # noqa: F405
        data=arrow_df,
        color="#999999",
        size=0.8,
        arrow=arrow(angle=25, length=8, type="closed"),  # noqa: F405
    )
    # Open circle markers at maxima (entropy peak and Gini peak)
    + geom_point(  # noqa: F405
        aes(x="p", y="impurity"),  # noqa: F405
        data=markers_df.iloc[[0]],
        size=9,
        color="#e07a2f",
        shape=21,
        fill="white",
        stroke=2.5,
        tooltips="none",
    )
    + geom_point(  # noqa: F405
        aes(x="p", y="impurity"),  # noqa: F405
        data=markers_df.iloc[[1]],
        size=9,
        color="#306998",
        shape=21,
        fill="white",
        stroke=2.5,
        tooltips="none",
    )
    # Annotation: maximum uncertainty label
    + geom_text(  # noqa: F405
        data=main_label_df,
        mapping=aes(x="p", y="impurity", label="label"),  # noqa: F405
        size=12,
        color="#333333",
        fontface="bold italic",
    )
    # Annotation: shaded region explanation
    + geom_text(  # noqa: F405
        data=region_label_df,
        mapping=aes(x="p", y="impurity", label="label"),  # noqa: F405
        size=10,
        color="#4a7a9b",
        fontface="italic",
    )
    # Annotations: boundary behavior at p→0 and p→1
    + geom_text(  # noqa: F405
        data=boundary_df,
        mapping=aes(x="p", y="impurity", label="label", hjust="hjust"),  # noqa: F405
        size=9,
        color="#888888",
        fontface="italic",
    )
    # Scales
    + scale_color_manual(values=["#306998", "#e07a2f"])  # noqa: F405
    + scale_x_continuous(  # noqa: F405
        breaks=list(np.arange(0, 1.1, 0.1)), limits=[0, 1]
    )
    + scale_y_continuous(  # noqa: F405
        breaks=list(np.arange(0, 1.2, 0.2)), limits=[-0.06, 1.05]
    )
    # Labels
    + labs(  # noqa: F405
        x="Probability of class 1 (p)",
        y="Impurity measure (normalized)",
        title="line-impurity-comparison \u00b7 letsplot \u00b7 pyplots.ai",
        subtitle="Both criteria peak at maximum uncertainty (p = 0.5), explaining why Gini and entropy yield similar tree structures",
        color="",
    )
    + ggsize(1600, 900)  # noqa: F405
    + theme_minimal()  # noqa: F405
    + theme(  # noqa: F405
        axis_text=element_text(size=16, color="#666666"),  # noqa: F405
        axis_title=element_text(size=20, color="#333333"),  # noqa: F405
        plot_title=element_text(size=24, face="bold", color="#1a1a1a"),  # noqa: F405
        plot_subtitle=element_text(size=15, color="#555555", face="italic"),  # noqa: F405
        legend_text=element_text(size=16),  # noqa: F405
        legend_position="bottom",
        panel_grid_major=element_line(color="#e8e8e8", size=0.4),  # noqa: F405
        panel_grid_minor=element_blank(),  # noqa: F405
        axis_line=element_blank(),  # noqa: F405
        axis_ticks=element_blank(),  # noqa: F405
        plot_margin=[40, 40, 20, 20],
    )
)

# Save
export_ggsave(plot, "plot.png", path=".", scale=3)
export_ggsave(plot, "plot.html", path=".")
