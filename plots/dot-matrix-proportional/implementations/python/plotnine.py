""" anyplot.ai
dot-matrix-proportional: Dot Matrix Chart for Proportional Counts
Library: plotnine 0.15.9 | Python 3.14.10
Quality: 85/100 | Updated: 2026-11-18
"""

import os

import numpy as np
import pandas as pd
from plotnine import (
    aes,
    coord_fixed,
    element_rect,
    element_text,
    geom_point,
    ggplot,
    ggsave,
    guide_legend,
    guides,
    labs,
    scale_color_manual,
    theme,
    theme_void,
)


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: all eight positions, one per category in order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Constants
REMAINDER = "Other"  # label for units that belong to no listed category

# Columns: set these to your table's column names
CATEGORY = "Household solar status"  # role: category
COUNT = "Homes"  # role: count
TOTAL = "Survey size"  # role: total

# Data: replace this block with your own table, for example df = pd.read_csv("survey.csv")
df = pd.DataFrame(
    {
        CATEGORY: ["Fully Solar-Powered", "Partially Solar-Powered", "No Solar Panels"],
        COUNT: [24, 41, 35],
        TOTAL: [100, 100, 100],
    }
)

# Plot: reads only df and the constants above
table = df.dropna(subset=[CATEGORY]).astype({CATEGORY: str})
runs = table.groupby(CATEGORY, sort=False)[COUNT].sum().astype(float).fillna(0).astype(int)
categories = runs.index.tolist()
listed = len(categories)
total = max(int(runs.sum()), int(df[TOTAL].astype(float).max(skipna=True) or 0))
remainder = total - int(runs.sum())
if remainder > 0:  # units that belong to no listed category stay in the grid as a neutral remainder
    runs[REMAINDER] = remainder
    categories.append(REMAINDER)

# One dot per unit, filled left to right and top to bottom
cols = int(np.ceil(np.sqrt(total)))
labels = np.repeat(categories, runs.to_numpy())
grid = pd.DataFrame(
    {
        "col": np.arange(total) % cols,
        "row": -(np.arange(total) // cols),
        CATEGORY: pd.Categorical(labels, categories=categories),
    }
)
legend_labels = [f"{cat}  ({n})" for cat, n in runs.items()]
colors = [IMPRINT_PALETTE[i] for i in range(listed)] + [INK_SOFT] * (len(categories) - listed)
title = "dot-matrix-proportional · python · plotnine · anyplot.ai"

plot = (
    ggplot(grid, aes(x="col", y="row", color=CATEGORY))
    + geom_point(size=10)
    + scale_color_manual(values=colors, labels=legend_labels)
    + guides(color=guide_legend(override_aes={"size": 8}))
    + coord_fixed()
    + labs(title=title, subtitle=f"{CATEGORY} · n = {total} homes", color="")
    + theme_void()
    + theme(
        figure_size=(8, 4.5),
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG),
        plot_title=element_text(color=INK, size=15, ha="left", weight="bold"),
        plot_subtitle=element_text(color=INK_SOFT, size=11, ha="left"),
        legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT),
        legend_text=element_text(color=INK_SOFT, size=9, margin={"l": 6, "r": 14}),
        legend_key=element_rect(fill=ELEVATED_BG, color="None"),
        legend_position="right",
        plot_margin=0.03,
    )
)

# Save
ggsave(plot, filename=f"plot-{THEME}.png", dpi=400, width=8, height=4.5, units="in")
