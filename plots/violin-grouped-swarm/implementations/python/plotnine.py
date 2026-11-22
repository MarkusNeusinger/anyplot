"""anyplot.ai
violin-grouped-swarm: Grouped Violin Plot with Swarm Overlay
Library: plotnine 0.15.4 | Python 3.13.13
Quality: pending | Updated: 2026-05-18
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
    geom_point,
    geom_violin,
    ggplot,
    guides,
    labs,
    position_dodge,
    position_jitterdodge,
    scale_color_manual,
    scale_fill_manual,
    scale_x_discrete,
    theme,
)


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: all eight positions, one per group in order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Columns: set these to your table's column names
TASK_TYPE = "Task type"  # role: category
EXPERTISE = "Expertise"  # role: group
RESPONSE_TIME = "Response time (ms)"  # role: value

# Data: replace this block with your own table, for example df = pd.read_csv("response_times.csv")
rng = np.random.default_rng(42)
tasks = {"Simple": 400, "Moderate": 700, "Complex": 1100}
spreads = {"Simple": 60, "Moderate": 100, "Complex": 150}
levels = {"Novice": 0, "Expert": -150}
rows = []
for task, task_mean in tasks.items():
    for level, shift in levels.items():
        center = task_mean + shift
        values = np.clip(rng.normal(center, spreads[task], 40), center - 3 * spreads[task], center + 3 * spreads[task])
        rows.append(pd.DataFrame({TASK_TYPE: task, EXPERTISE: level, RESPONSE_TIME: values}))
df = pd.concat(rows, ignore_index=True)

# Plot
group_order = df[EXPERTISE].unique().tolist()
task_order = df[TASK_TYPE].unique().tolist()

plot = (
    ggplot(df, aes(x=TASK_TYPE, y=RESPONSE_TIME, fill=EXPERTISE))
    + geom_violin(position=position_dodge(width=0.8), alpha=0.45, size=0.5, color=INK_SOFT)
    + geom_point(
        aes(color=EXPERTISE),
        position=position_jitterdodge(jitter_width=0.12, jitter_height=0, dodge_width=0.8, random_state=42),
        size=1.1,
        alpha=0.85,
        stroke=0,
    )
    + scale_x_discrete(limits=task_order)
    + scale_fill_manual(values=IMPRINT_PALETTE, limits=group_order)
    + scale_color_manual(values=IMPRINT_PALETTE, limits=group_order)
    + guides(color="none")
    + labs(title="violin-grouped-swarm · python · plotnine · anyplot.ai")
    + theme(
        figure_size=(8, 4.5),
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_border=element_blank(),
        panel_grid_major_x=element_blank(),
        panel_grid_major_y=element_line(color=INK, size=0.3, alpha=0.10),
        panel_grid_minor=element_blank(),
        axis_title=element_text(size=10, color=INK),
        axis_text=element_text(size=8, color=INK_SOFT),
        axis_line=element_line(color=INK_SOFT, size=0.6),
        plot_title=element_text(size=12, color=INK),
        legend_background=element_rect(fill=PAGE_BG, color=INK_SOFT),
        legend_key=element_rect(fill=PAGE_BG, color=PAGE_BG),
        legend_text=element_text(size=8, color=INK_SOFT),
        legend_title=element_text(size=9, color=INK),
        text=element_text(size=7),
    )
)

# Save
plot.save(f"plot-{THEME}.png", dpi=400, width=8, height=4.5, units="in", verbose=False)
