"""anyplot.ai
violin-box: Violin Plot with Embedded Box Plot
Library: plotnine 0.15.4 | Python 3.13.13
Quality: 87/100 | Updated: 2026-05-12
"""

import os

import numpy as np
import pandas as pd
from plotnine import (
    aes,
    element_blank,
    element_line,
    element_rect,
    element_text,
    geom_boxplot,
    geom_violin,
    ggplot,
    guide_legend,
    labs,
    scale_fill_manual,
    scale_x_discrete,
    theme,
)


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Constants
SEED = 42
N_PER_GROUP = 80

# Columns
GROUP = "Product Category"  # role: group
SCORE = "Satisfaction Score (points)"  # role: value

# Data
rng = np.random.default_rng(SEED)
df = pd.DataFrame(
    {
        SCORE: np.concatenate(
            [
                rng.normal(55, 10, N_PER_GROUP),
                rng.exponential(8, N_PER_GROUP) + 35,
                np.concatenate([rng.normal(40, 5, N_PER_GROUP // 2), rng.normal(65, 5, N_PER_GROUP // 2)]),
                rng.uniform(30, 70, N_PER_GROUP),
            ]
        ),
        GROUP: np.repeat(["Product A", "Product B", "Product C", "Product D"], N_PER_GROUP),
    }
)

# Plot
groups = df[GROUP].unique().tolist()

anyplot_theme = theme(
    figure_size=(8, 4.5),
    plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
    panel_background=element_rect(fill=PAGE_BG, color=None),
    panel_grid_major=element_line(color=INK, size=0.3, alpha=0.10),
    panel_grid_minor=element_line(color=INK, size=0.2, alpha=0.05),
    panel_border=element_blank(),
    axis_title=element_text(color=INK, size=10, weight="bold"),
    axis_text=element_text(color=INK_SOFT, size=8),
    axis_line_x=element_line(color=INK_SOFT, size=0.5),
    axis_line_y=element_line(color=INK_SOFT, size=0.5),
    axis_ticks=element_line(color=INK_SOFT, size=0.3),
    plot_title=element_text(color=INK, size=12, weight="bold"),
    legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT),
    legend_text=element_text(color=INK_SOFT, size=8),
    legend_title=element_text(color=INK, size=8, weight="bold"),
    legend_position="top",
    legend_direction="horizontal",
)

plot = (
    ggplot(df, aes(x=GROUP, y=SCORE, fill=GROUP))
    + geom_violin(alpha=0.65, color=INK_SOFT, size=0.4, width=0.85)
    + geom_boxplot(width=0.22, alpha=0.9, color=INK_SOFT, fill=ELEVATED_BG, size=0.4, outlier_size=2, outlier_alpha=0.7)
    + scale_x_discrete(limits=groups)
    + scale_fill_manual(values=IMPRINT_PALETTE, limits=groups, name="Product", guide=guide_legend(nrow=1))
    + labs(title="violin-box · python · plotnine · anyplot.ai")
    + anyplot_theme
)

# Save
plot.save(f"plot-{THEME}.png", dpi=400, width=8, height=4.5, units="in", verbose=False)
