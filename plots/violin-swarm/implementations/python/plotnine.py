"""anyplot.ai
violin-swarm: Violin Plot with Overlaid Swarm Points
Library: plotnine 0.15.4 | Python 3.13.13
Quality: 90/100 | Updated: 2026-05-18
"""

import os

import numpy as np
import pandas as pd
from plotnine import (
    aes,
    element_line,
    element_rect,
    element_text,
    geom_jitter,
    geom_violin,
    ggplot,
    labs,
    position_jitter,
    scale_x_discrete,
    theme,
    theme_minimal,
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
N_PER_GROUP = 50

# Columns
CONDITION = "Experimental Condition"  # role: category
REACTION = "Reaction Time (ms)"  # role: value

# Data - Reaction times (ms) across 4 experimental conditions
np.random.seed(SEED)

conditions = ["Control", "Treatment A", "Treatment B", "Treatment C"]
half = N_PER_GROUP // 2
samples = [
    np.random.normal(450, 80, N_PER_GROUP),
    np.random.normal(380, 60, N_PER_GROUP),
    np.concatenate([np.random.normal(420, 40, half), np.random.normal(520, 50, N_PER_GROUP - half)]),
    np.random.normal(350, 90, N_PER_GROUP),
]
df = pd.DataFrame({CONDITION: np.repeat(conditions, [len(s) for s in samples]), REACTION: np.concatenate(samples)})

# Plot
anyplot_theme = theme(
    plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
    panel_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
    panel_grid_major=element_line(color=INK_SOFT, size=0.3, alpha=0.12),
    panel_grid_minor=element_line(color=INK_SOFT, size=0.15, alpha=0.06),
    panel_border=element_rect(color=INK_SOFT, fill=None, size=0.6),
    axis_title=element_text(color=INK, size=10),
    axis_text=element_text(color=INK_SOFT, size=8),
    axis_line=element_line(color=INK_SOFT, size=0.5),
    plot_title=element_text(color=INK, size=12, weight="medium"),
    legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT),
    legend_text=element_text(color=INK_SOFT, size=8),
    legend_title=element_text(color=INK, size=8),
    figure_size=(8, 4.5),
)

plot = (
    ggplot(df, aes(x=CONDITION, y=REACTION))
    + geom_violin(fill=IMPRINT_PALETTE[0], alpha=0.35, color=IMPRINT_PALETTE[0], size=0.8)
    + geom_jitter(position=position_jitter(width=0.15), color=IMPRINT_PALETTE[1], size=2.5, alpha=0.75, stroke=0.3)
    + scale_x_discrete(limits=df[CONDITION].unique().tolist())
    + labs(title="violin-swarm · python · plotnine · anyplot.ai")
    + theme_minimal()
    + anyplot_theme
)

plot.save(f"plot-{THEME}.png", dpi=400, width=8, height=4.5, units="in", verbose=False)
