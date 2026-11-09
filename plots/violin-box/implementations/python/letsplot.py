"""anyplot.ai
violin-box: Violin Plot with Embedded Box Plot
Library: letsplot 4.11.0 | Python 3.14.10
Quality: 84/100 | Updated: 2026-11-09
"""

import os

import numpy as np
import pandas as pd
from lets_plot import *


# Theme tokens (see prompts/default-style-guide.md "Theme-adaptive Chrome")
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
GRID = "rgba(26,26,23,0.15)" if THEME == "light" else "rgba(240,239,232,0.15)"

# Imprint palette: all eight positions, one per group in order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

LetsPlot.setup_html()

# Columns: set these to your table's column names
CONFIGURATION = "Server Configuration"  # role: group
RESPONSE_TIME = "Response Time (ms)"  # role: value

# Data: replace this block with your own table, for example df = pd.read_csv("response_times.csv")
np.random.seed(42)
n_per_group = 150
standard = np.random.normal(85, 15, n_per_group)
optimized = np.concatenate([np.random.normal(55, 12, n_per_group - 5), np.random.normal(100, 5, 5)])
premium = np.concatenate([np.random.normal(40, 8, n_per_group // 2), np.random.normal(60, 8, n_per_group // 2)])
enterprise = np.concatenate([np.random.normal(30, 6, n_per_group - 3), np.random.normal(70, 3, 3)])
df = pd.DataFrame(
    {
        CONFIGURATION: ["Standard"] * n_per_group
        + ["Optimized"] * n_per_group
        + ["Premium"] * n_per_group
        + ["Enterprise"] * n_per_group,
        RESPONSE_TIME: np.concatenate([standard, optimized, premium, enterprise]),
    }
)

# Plot: reads only df and the constants above
title = "violin-box · python · letsplot · anyplot.ai"
plot = (
    ggplot(df, aes(x=CONFIGURATION, y=RESPONSE_TIME, fill=CONFIGURATION))
    + geom_violin(alpha=0.75, color=INK_SOFT, size=0.6)
    + geom_boxplot(
        width=0.12,
        fill=ELEVATED_BG,
        color=INK,
        size=0.7,
        outlier_shape=21,
        outlier_size=0.4,
        outlier_stroke=0.4,
        outlier_color=INK,
        outlier_fill=ELEVATED_BG,
    )
    + scale_fill_manual(values=IMPRINT_PALETTE)
    + labs(title=title)
    + theme_minimal()
    + theme(
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        plot_title=element_text(size=round(16 * min(1.0, 67 / len(title))), face="bold", color=INK),
        axis_title=element_text(size=12, color=INK),
        axis_text=element_text(size=10, color=INK_SOFT),
        axis_line=element_line(color=INK_SOFT, size=0.5),
        axis_ticks=element_blank(),
        panel_grid_major_y=element_line(color=GRID, size=0.3),
        panel_grid_major_x=element_blank(),
        panel_grid_minor=element_blank(),
        legend_position="none",
    )
    + ggsize(800, 450)
)

# Save
ggsave(plot, f"plot-{THEME}.png", path=".", scale=4)
ggsave(plot, f"plot-{THEME}.html", path=".")
