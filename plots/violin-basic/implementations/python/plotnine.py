""" pyplots.ai
violin-basic: Basic Violin Plot
Library: plotnine 0.15.3 | Python 3.14.3
Quality: 92/100 | Updated: 2026-02-21
"""

import numpy as np
import pandas as pd
from plotnine import (
    aes,
    element_blank,
    element_line,
    element_rect,
    element_text,
    geom_violin,
    ggplot,
    labs,
    scale_fill_manual,
    theme,
    theme_minimal,
)


# Data
np.random.seed(42)

records = []

# Biology: right-skewed (many average, few high scorers)
scores_bio = np.concatenate([np.random.normal(68, 6, 150), np.random.normal(85, 3, 30)])
records.extend([("Biology", s) for s in scores_bio])

# Statistics: bimodal (two distinct clusters)
scores_stat = np.concatenate([np.random.normal(55, 5, 100), np.random.normal(82, 5, 100)])
records.extend([("Statistics", s) for s in scores_stat])

# Chemistry: tight normal (consistent performance)
scores_chem = np.random.normal(74, 4, 200)
records.extend([("Chemistry", s) for s in scores_chem])

# Psychology: wide spread (high variance)
scores_psych = np.random.normal(70, 14, 200)
records.extend([("Psychology", s) for s in scores_psych])

df = pd.DataFrame(records, columns=["course", "score"])
df["score"] = df["score"].clip(0, 100)
df["course"] = pd.Categorical(
    df["course"], categories=["Biology", "Statistics", "Chemistry", "Psychology"], ordered=True
)

# Custom palette: Python Blue for focal bimodal distribution, muted tones for context
palette = {"Biology": "#7BAE7F", "Statistics": "#306998", "Chemistry": "#E8A87C", "Psychology": "#B8B3D6"}

# Plot
plot = (
    ggplot(df, aes(x="course", y="score", fill="course"))
    + geom_violin(draw_quantiles=[0.25, 0.5, 0.75], alpha=0.82, color="#666666", size=0.35, trim=False)
    + scale_fill_manual(values=palette)
    + labs(x="Course", y="Final Exam Score (pts)", title="violin-basic \u00b7 plotnine \u00b7 pyplots.ai")
    + theme_minimal()
    + theme(
        figure_size=(16, 9),
        text=element_text(size=14, color="#333333"),
        axis_title=element_text(size=20, color="#333333"),
        axis_text=element_text(size=16, color="#444444"),
        plot_title=element_text(size=24, color="#222222", weight="bold"),
        legend_position="none",
        panel_grid_major_x=element_blank(),
        panel_grid_minor=element_blank(),
        panel_grid_major_y=element_line(color="#dedede", size=0.3),
        plot_background=element_rect(fill="#fafafa", color="none"),
        panel_background=element_rect(fill="#fafafa", color="none"),
    )
)

# Save
plot.save("plot.png", dpi=300, verbose=False)
