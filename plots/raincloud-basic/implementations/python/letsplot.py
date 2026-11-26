""" anyplot.ai
raincloud-basic: Basic Raincloud Plot
Library: letsplot 4.11.0 | Python 3.14.10
Quality: 86/100 | Updated: 2026-11-26
"""

import os

import numpy as np
import pandas as pd
from lets_plot import (
    LetsPlot,
    aes,
    element_blank,
    element_line,
    element_rect,
    element_text,
    geom_boxplot,
    geom_jitter,
    geom_violin,
    ggplot,
    ggsave,
    ggsize,
    labs,
    position_nudge,
    scale_color_manual,
    scale_fill_manual,
    scale_x_continuous,
    scale_y_discrete,
    theme,
)


LetsPlot.setup_html()

# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
RULE = "rgba(26,26,23,0.15)" if THEME == "light" else "rgba(240,239,232,0.15)"

# Imprint palette (canonical order, first series always #009E73)
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Columns
CONDITION = "Experimental Condition"  # role: category
REACTION_TIME = "Reaction Time (ms)"  # role: value

# Data: reaction times (ms) for three experimental conditions
np.random.seed(42)
control = np.random.normal(450, 60, 80)
treatment_a = np.random.normal(380, 50, 80)
treatment_b = np.concatenate([np.random.normal(300, 30, 50), np.random.normal(540, 35, 30)])
df = pd.DataFrame(
    {
        CONDITION: ["Control"] * len(control) + ["Treatment A"] * len(treatment_a) + ["Treatment B"] * len(treatment_b),
        REACTION_TIME: np.concatenate([control, treatment_a, treatment_b]),
    }
)

# Plot: first category at the top of the y axis
cat_order = list(df[CONDITION].unique())[::-1]
x_low = np.floor(df[REACTION_TIME].min() / 50) * 50 - 50
x_high = np.ceil(df[REACTION_TIME].max() / 50) * 50 + 50

plot = (
    ggplot(df, aes(x=REACTION_TIME, y=CONDITION, fill=CONDITION, color=CONDITION))
    # Half-violin (cloud) nudged above the category baseline
    + geom_violin(trim=False, show_half=1, size=0.8, alpha=0.7, position=position_nudge(y=0.12))
    # Boxplot on the baseline
    + geom_boxplot(
        width=0.18,
        outlier_size=0,
        outlier_alpha=0,
        fill=ELEVATED_BG,
        color=INK,
        size=0.8,
        alpha=0.95,
        show_legend=False,
    )
    # Rain: jittered points below the baseline
    + geom_jitter(
        width=0,
        height=0.05,
        size=4.0,
        alpha=0.5,
        shape=21,
        stroke=0.3,
        show_legend=False,
        position=position_nudge(y=-0.16),
    )
    + scale_fill_manual(values=IMPRINT_PALETTE)
    + scale_color_manual(values=IMPRINT_PALETTE)
    + scale_y_discrete(limits=cat_order)
    + scale_x_continuous(limits=[x_low, x_high])
    + labs(title="raincloud-basic · python · letsplot · anyplot.ai")
    + theme(
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        plot_title=element_text(size=18, face="bold", color=INK),
        axis_title_x=element_text(size=12, color=INK, margin=[12, 0, 0, 0]),
        axis_title_y=element_text(size=12, color=INK, margin=[0, 12, 0, 0]),
        axis_text_x=element_text(size=10, color=INK_SOFT),
        axis_text_y=element_text(size=12, color=INK, face="bold"),
        axis_ticks=element_blank(),
        axis_line_x=element_blank(),
        axis_line_y=element_blank(),
        legend_position="none",
        panel_grid_major_y=element_blank(),
        panel_grid_minor=element_blank(),
        panel_grid_major_x=element_line(color=RULE, size=0.4),
        plot_margin=[40, 40, 30, 20],
    )
    + ggsize(800, 450)
)

ggsave(plot, f"plot-{THEME}.png", path=".", scale=4)
ggsave(plot, f"plot-{THEME}.html", path=".")
