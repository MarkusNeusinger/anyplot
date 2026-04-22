""" pyplots.ai
histogram-basic: Basic Histogram
Library: plotnine 0.15.3 | Python 3.14.0
Quality: 95/100 | Created: 2025-12-23
"""

import numpy as np
import pandas as pd
from plotnine import (
    aes,
    after_stat,
    annotate,
    element_blank,
    element_line,
    element_rect,
    element_text,
    geom_histogram,
    geom_vline,
    ggplot,
    labs,
    scale_x_continuous,
    scale_y_continuous,
    theme,
    theme_minimal,
)


# Data — mixture of two normal distributions for visible bimodality
np.random.seed(42)
n_points = 500
group_a = np.random.normal(loc=45, scale=10, size=int(n_points * 0.55))
group_b = np.random.normal(loc=80, scale=7, size=int(n_points * 0.45))
raw_scores = np.concatenate([group_a, group_b])
scores = np.clip(raw_scores, 0, 100)

df = pd.DataFrame({"score": scores})

# Key statistics for storytelling
mean_score = float(np.mean(scores))
median_score = float(np.median(scores))

# Plot with after_stat and annotate for storytelling
plot = (
    ggplot(df, aes(x="score"))
    + geom_histogram(aes(y=after_stat("count")), bins=30, fill="#306998", color="#1a3a5c", alpha=0.82, size=0.3)
    # Mean line
    + geom_vline(xintercept=mean_score, color="#c0392b", size=1.2, linetype="dashed")
    # Median line
    + geom_vline(xintercept=median_score, color="#d68910", size=1.2, linetype="solid")
    # Annotate mean — placed above the valley
    + annotate(
        "text",
        x=mean_score + 2,
        y=48,
        label=f"Mean: {mean_score:.1f}",
        color="#c0392b",
        size=12,
        ha="left",
        fontweight="bold",
    )
    # Annotate median — placed below mean label
    + annotate(
        "text",
        x=median_score - 2,
        y=48,
        label=f"Median: {median_score:.1f}",
        color="#d68910",
        size=12,
        ha="right",
        fontweight="bold",
    )
    # Annotate distribution shape — positioned in the upper-right area
    + annotate(
        "label",
        x=96,
        y=46,
        label="Bimodal distribution:\ntwo student clusters",
        size=10,
        color="#444444",
        fill="#f5f5f5",
        alpha=0.9,
        label_size=0,
        ha="right",
    )
    + scale_x_continuous(breaks=range(10, 101, 10), limits=(8, 102))
    + scale_y_continuous(expand=(0, 0, 0.1, 0))
    + labs(x="Test Score (points)", y="Frequency (count)", title="histogram-basic · plotnine · pyplots.ai")
    + theme_minimal()
    + theme(
        figure_size=(16, 9),
        text=element_text(size=14, color="#333333"),
        axis_title_x=element_text(size=20, color="#222222", margin={"t": 14}),
        axis_title_y=element_text(size=20, color="#222222", margin={"r": 14}),
        axis_text=element_text(size=16, color="#555555"),
        plot_title=element_text(size=24, color="#1a1a1a", weight="bold", margin={"b": 14}),
        panel_grid_major_x=element_blank(),
        panel_grid_minor=element_blank(),
        panel_grid_major_y=element_line(color="#e0e0e0", size=0.5),
        plot_background=element_rect(fill="white", color="white"),
        panel_background=element_rect(fill="white", color="white"),
    )
)

# Save
plot.save("plot.png", dpi=300, verbose=False)
