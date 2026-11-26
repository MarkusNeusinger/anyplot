""" anyplot.ai
raincloud-basic: Basic Raincloud Plot
Library: plotnine 0.15.9 | Python 3.14.10
Quality: 87/100 | Updated: 2026-11-26
"""

import os

import numpy as np
import pandas as pd
from plotnine import (
    aes,
    coord_flip,
    element_blank,
    element_line,
    element_rect,
    element_text,
    geom_boxplot,
    geom_jitter,
    geom_violin,
    ggplot,
    labs,
    scale_color_manual,
    scale_fill_manual,
    scale_x_discrete,
    scale_y_continuous,
    stage,
    theme,
    theme_minimal,
)


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Imprint palette — first series ALWAYS #009E73
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Columns: set these to your table's column names
CONDITION = "Experimental Condition"  # role: category
REACTION_TIME = "Reaction Time (ms)"  # role: value

# Data: replace this block with your own table, for example df = pd.read_csv("reaction_times.csv")
np.random.seed(42)
control = np.random.normal(450, 60, 80)
treatment_a = np.random.normal(380, 50, 80)
treatment_b = np.concatenate([np.random.normal(350, 40, 50), np.random.normal(500, 45, 30)])

df = pd.DataFrame(
    {
        CONDITION: ["Control"] * len(control) + ["Treatment A"] * len(treatment_a) + ["Treatment B"] * len(treatment_b),
        REACTION_TIME: np.concatenate([control, treatment_a, treatment_b]),
    }
)

# Plot — horizontal raincloud via coord_flip
# Pre-flip: x=condition (categorical), y=value. After flip: categories on y, values on x.
groups = df[CONDITION].unique().tolist()
plot = (
    ggplot(df, aes(x=CONDITION, y=REACTION_TIME, fill=CONDITION, color=CONDITION))
    # Cloud (half-violin) — style="right" extends positive x = upward after flip
    + geom_violin(
        aes(x=stage(CONDITION, after_scale="x+0.15")),
        style="right",
        trim=True,
        scale="width",
        size=0.3,
        alpha=0.78,
        show_legend=False,
    )
    # Boxplot — centered on category baseline, theme-adaptive fill/edge
    + geom_boxplot(width=0.06, outlier_shape="", fill=ELEVATED_BG, color=INK, size=0.5, alpha=0.95, show_legend=False)
    # Rain (jittered points) — nudged negative x = downward after flip
    + geom_jitter(
        aes(x=stage(CONDITION, after_scale="x-0.18")), width=0.06, height=0, size=3.0, alpha=0.6, show_legend=False
    )
    + scale_fill_manual(values=IMPRINT_PALETTE, limits=groups)
    + scale_color_manual(values=IMPRINT_PALETTE, limits=groups)
    # First group on top after coord_flip; room above the top cloud
    + scale_x_discrete(limits=groups[::-1], expand=(0, 0.6, 0, 0.75))
    + scale_y_continuous(expand=(0.03, 0, 0.03, 0))
    + coord_flip()
    + labs(title="raincloud-basic · python · plotnine · anyplot.ai")
    + theme_minimal()
    + theme(
        figure_size=(8, 4.5),
        text=element_text(size=7, color=INK),
        axis_title=element_text(size=10, color=INK),
        axis_text=element_text(size=8, color=INK_SOFT),
        plot_title=element_text(size=14, color=INK),
        panel_grid_major_y=element_blank(),
        panel_grid_minor=element_blank(),
        panel_grid_major_x=element_line(color=INK, size=0.3, alpha=0.15),
        panel_border=element_blank(),
        axis_line=element_line(color=INK_SOFT, size=0.4),
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        legend_position="none",
        plot_margin=0.02,
    )
)

# Save
plot.save(f"plot-{THEME}.png", dpi=400, width=8, height=4.5, units="in", verbose=False)
