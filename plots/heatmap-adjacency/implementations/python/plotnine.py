"""anyplot.ai
heatmap-adjacency: Network Adjacency Matrix Heatmap
Library: plotnine | Python 3.13
Quality: pending | Created: 2026-05-08
"""

import os

import numpy as np
import pandas as pd
from plotnine import (
    aes,
    element_blank,
    element_rect,
    element_text,
    geom_hline,
    geom_tile,
    geom_vline,
    ggplot,
    labs,
    scale_fill_cmap,
    scale_x_discrete,
    scale_y_discrete,
    theme,
)


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
ABSENT_CELL = "#E0DED7" if THEME == "light" else "#2A2A25"

# Data: researcher collaboration network — 3 scientific fields (Physics, Biology, CompSci)
np.random.seed(42)

n_per_group = 10
prefixes = ["P", "B", "C"]
node_names = [f"{p}{i + 1:02d}" for p in prefixes for i in range(n_per_group)]
n_nodes = len(node_names)

W = np.zeros((n_nodes, n_nodes))

# Within-field: dense, strong collaborations (block-diagonal structure)
for gi in range(3):
    members = list(range(gi * n_per_group, (gi + 1) * n_per_group))
    for idx_i, i in enumerate(members):
        for j in members[idx_i + 1 :]:
            if np.random.rand() < 0.72:
                w = np.random.uniform(0.45, 1.0)
                W[i, j] = w
                W[j, i] = w

# Cross-field: sparse, weaker connections
for i in range(n_nodes):
    for j in range(i + 1, n_nodes):
        if i // n_per_group != j // n_per_group and W[i, j] == 0:
            if np.random.rand() < 0.09:
                w = np.random.uniform(0.05, 0.38)
                W[i, j] = w
                W[j, i] = w

# Long-format DataFrame; absent edges (including diagonal) → NaN
all_pairs = [(r, c) for r in range(n_nodes) for c in range(n_nodes)]
df = pd.DataFrame(
    {
        "source": pd.Categorical([node_names[r] for r, _ in all_pairs], categories=node_names, ordered=True),
        "target": pd.Categorical([node_names[c] for _, c in all_pairs], categories=node_names, ordered=True),
        "weight": [W[r, c] if W[r, c] > 0 else np.nan for r, c in all_pairs],
    }
)

# Community separator positions (between groups of 10)
boundaries = [n_per_group + 0.5, 2 * n_per_group + 0.5]

# Plot
anyplot_theme = theme(
    figure_size=(12, 12),
    plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
    panel_background=element_rect(fill=ABSENT_CELL),
    panel_grid_major=element_blank(),
    panel_grid_minor=element_blank(),
    panel_border=element_rect(color=INK_SOFT, fill=None),
    axis_title=element_text(color=INK, size=18),
    axis_text=element_text(color=INK_SOFT, size=9),
    axis_text_x=element_text(angle=45, ha="right", color=INK_SOFT, size=9),
    plot_title=element_text(color=INK, size=20, ha="center"),
    legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT),
    legend_text=element_text(color=INK_SOFT, size=14),
    legend_title=element_text(color=INK, size=16),
)

plot = (
    ggplot(df, aes(x="target", y="source", fill="weight"))
    + geom_tile()
    + geom_vline(xintercept=boundaries, color=INK, size=0.9, alpha=0.5, linetype="dashed")
    + geom_hline(yintercept=boundaries, color=INK, size=0.9, alpha=0.5, linetype="dashed")
    + scale_fill_cmap("viridis", na_value=ABSENT_CELL, name="Collaboration\nStrength")
    + scale_x_discrete(limits=node_names)
    + scale_y_discrete(limits=node_names[::-1])
    + labs(x="Target Researcher", y="Source Researcher", title="heatmap-adjacency · plotnine · anyplot.ai")
    + anyplot_theme
)

# Save
plot.save(f"plot-{THEME}.png", dpi=300, width=12, height=12, units="in")
