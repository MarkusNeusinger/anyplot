""" anyplot.ai
violin-grouped-swarm: Grouped Violin Plot with Swarm Overlay
Library: letsplot 4.11.0 | Python 3.14.10
Quality: 80/100 | Updated: 2026-11-22
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
    geom_point,
    geom_violin,
    ggplot,
    ggsize,
    labs,
    position_dodge,
    position_jitterdodge,
    scale_color_manual,
    scale_fill_manual,
    theme,
    theme_minimal,
)
from lets_plot.export import ggsave


LetsPlot.setup_html()

# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: all eight positions, one per group in order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Columns: set these to your table's column names
DOSAGE = "Dosage Level"  # role: category
GROUP = "Group"  # role: group
EFFICACY = "Efficacy Score"  # role: value

# Data: replace this block with your own table, for example df = pd.read_csv("trial.csv")
np.random.seed(42)
rows = []
for cat, placebo, treatment in [
    ("Low Dose", (3.0, 1.2), (4.2, 0.8)),
    ("Medium Dose", (3.5, 1.3), (6.1, 0.9)),
    ("High Dose", (3.8, 1.4), (7.5, 1.0)),
]:
    for grp, (base, spread) in [("Placebo", placebo), ("Treatment", treatment)]:
        values = np.clip(np.random.normal(base, spread, 45), 1, 10)
        rows.extend({DOSAGE: cat, GROUP: grp, EFFICACY: v} for v in values)
df = pd.DataFrame(rows)

# Plot
plot = (
    ggplot(df, aes(x=DOSAGE, y=EFFICACY, fill=GROUP, color=GROUP))
    + geom_violin(alpha=0.5, position=position_dodge(width=0.75), size=0.3, trim=False)
    + geom_point(alpha=0.6, size=1.0, position=position_jitterdodge(jitter_width=0.1, dodge_width=0.75))
    + scale_fill_manual(values=IMPRINT_PALETTE)
    + scale_color_manual(values=IMPRINT_PALETTE)
    + labs(title="violin-grouped-swarm · python · letsplot · anyplot.ai")
    + theme_minimal()
    + theme(
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_grid_major=element_line(color=INK_SOFT, size=0.1),
        panel_grid_minor=element_blank(),
        axis_title=element_text(size=12, color=INK),
        axis_text=element_text(size=10, color=INK_SOFT),
        axis_line=element_line(color=INK_SOFT, size=0.2),
        plot_title=element_text(size=16, color=INK),
        legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT),
        legend_text=element_text(size=10, color=INK_SOFT),
        legend_title=element_text(size=12, color=INK),
        legend_position="right",
    )
    + ggsize(800, 450)
)

# Save
ggsave(plot, f"plot-{THEME}.png", path=".", scale=4)
ggsave(plot, f"plot-{THEME}.html", path=".")
