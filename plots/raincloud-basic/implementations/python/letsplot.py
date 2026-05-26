"""anyplot.ai
raincloud-basic: Basic Raincloud Plot
Library: letsplot | Python 3.13
Quality: pending | Created: 2026-05-26
"""

import os

import numpy as np
import pandas as pd
from lets_plot import (
    LetsPlot,
    aes,
    arrow,
    element_blank,
    element_line,
    element_rect,
    element_text,
    geom_boxplot,
    geom_jitter,
    geom_segment,
    geom_text,
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
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"
RULE = "rgba(26,26,23,0.15)" if THEME == "light" else "rgba(240,239,232,0.15)"

# anyplot categorical palette (canonical order, first series ALWAYS #009E73)
BRAND = "#009E73"
LAVENDER = "#C475FD"
BLUE = "#4467A3"

# Data — reaction times (ms) for three experimental conditions
np.random.seed(42)

control = np.random.normal(450, 60, 80)
treatment_a = np.random.normal(380, 50, 80)
treatment_b = np.concatenate([np.random.normal(300, 30, 50), np.random.normal(540, 35, 30)])

df = pd.DataFrame(
    {
        "condition": ["Control"] * len(control)
        + ["Treatment A"] * len(treatment_a)
        + ["Treatment B"] * len(treatment_b),
        "reaction_time": np.concatenate([control, treatment_a, treatment_b]),
    }
)

palette = {"Control": BRAND, "Treatment A": LAVENDER, "Treatment B": BLUE}

# Display order (bottom to top of y-axis): Treatment B, Treatment A, Control
cat_order = ["Treatment B", "Treatment A", "Control"]

plot = (
    ggplot(df, aes(x="reaction_time", y="condition", fill="condition", color="condition"))
    # Half-violin (cloud) — nudged above the category baseline
    + geom_violin(trim=False, show_half=1, size=0.8, alpha=0.7, position=position_nudge(y=0.12))
    # Boxplot on the baseline with elevated-bg fill for contrast in both themes
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
    # Rain — jittered points below the baseline
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
    # Annotation: Treatment A faster mean (index 1)
    + geom_text(
        x=690, y=1.55, label="~70ms faster mean\nthan Control", size=13, color=INK_SOFT, fontface="italic", hjust=1
    )
    + geom_segment(x=560, y=1.45, xend=420, yend=1.15, color=INK_SOFT, size=0.5, arrow=arrow(length=8, type="closed"))
    # Annotation: Treatment B bimodal (index 0, bottom)
    + geom_text(
        x=690, y=0.55, label="Two distinct\nresponse clusters", size=13, color=INK_SOFT, fontface="italic", hjust=1
    )
    + geom_segment(x=560, y=0.35, xend=310, yend=0.12, color=INK_SOFT, size=0.5, arrow=arrow(length=8, type="closed"))
    + geom_segment(x=590, y=0.30, xend=545, yend=0.12, color=INK_SOFT, size=0.5, arrow=arrow(length=8, type="closed"))
    + scale_fill_manual(values=palette)
    + scale_color_manual(values=palette)
    + scale_y_discrete(limits=cat_order)
    + scale_x_continuous(limits=[200, 700])
    + labs(x="Reaction Time (ms)", y="Experimental Condition", title="raincloud-basic · python · letsplot · anyplot.ai")
    + theme(
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        plot_title=element_text(size=16, face="bold", color=INK),
        axis_title_x=element_text(size=12, color=INK, margin=[12, 0, 0, 0]),
        axis_title_y=element_text(size=12, color=INK, margin=[0, 12, 0, 0]),
        axis_text_x=element_text(size=10, color=INK_SOFT),
        axis_text_y=element_text(size=12, color=INK, face="bold"),
        axis_ticks=element_blank(),
        axis_line_x=element_line(color=INK_SOFT, size=0.5),
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
