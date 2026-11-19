""" anyplot.ai
violin-split: Split Violin Plot
Library: letsplot 4.11.0 | Python 3.14.10
Quality: 82/100 | Updated: 2026-11-19
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
    geom_violin,
    ggplot,
    ggsize,
    labs,
    position_nudge,
    scale_fill_manual,
    theme,
    theme_minimal,
)
from lets_plot.export import ggsave


LetsPlot.setup_html()

# Theme tokens (see prompts/default-style-guide.md)
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
GRID_LINE = "rgba(26,26,23,0.10)" if THEME == "light" else "rgba(240,239,232,0.10)"

# Imprint palette: all eight positions, one per group in order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Columns: set these to your table's column names
DEPARTMENT = "Department"  # role: category
SATISFACTION = "Satisfaction Score (0-100)"  # role: value
PERIOD = "Period"  # role: split_group

# Data: replace this block with your own table, for example df = pd.read_csv("satisfaction.csv")
# Employee satisfaction scores before and after an office redesign, per department
np.random.seed(42)
distributions = {
    "Engineering": {"Before": (65, 12), "After": (78, 10)},
    "Marketing": {"Before": (58, 15), "After": (72, 11)},
    "Sales": {"Before": (70, 14), "After": (75, 12)},
    "Design": {"Before": (55, 18), "After": (82, 8)},
}
rows = []
for dept, periods in distributions.items():
    for period, (mean, std) in periods.items():
        n_samples = np.random.randint(80, 150)
        values = np.clip(np.random.normal(mean, std, n_samples), 20, 100)
        rows.append(pd.DataFrame({DEPARTMENT: dept, SATISFACTION: values, PERIOD: period}))
df = pd.concat(rows, ignore_index=True)

# Plot: reads only df and the constants above
periods = list(df[PERIOD].drop_duplicates())
left, right = periods[0], periods[-1]
df_left = df[df[PERIOD] == left]
df_right = df[df[PERIOD] == right]

violin = {"trim": True, "size": 0.4, "alpha": 0.75}
box = {"width": 0.08, "outlier_shape": None, "alpha": 0.9, "size": 0.3, "show_legend": False}
mapping = aes(x=DEPARTMENT, y=SATISFACTION, fill=PERIOD)

plot = (
    ggplot()
    # Left half: first split group; right half: last split group
    + geom_violin(mapping, data=df_left, show_half=-1, **violin)
    + geom_violin(mapping, data=df_right, show_half=1, **violin)
    # Inner boxplots at the quartiles of each half
    + geom_boxplot(mapping, data=df_left, position=position_nudge(x=-0.05), **box)
    + geom_boxplot(mapping, data=df_right, position=position_nudge(x=0.05), **box)
    + scale_fill_manual(values=IMPRINT_PALETTE, limits=periods, name=PERIOD)
    + labs(x=DEPARTMENT, y=SATISFACTION, title="violin-split · python · letsplot · anyplot.ai")
    + theme_minimal()
    + theme(
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG),
        panel_grid_major_x=element_blank(),
        panel_grid_minor=element_blank(),
        panel_grid_major_y=element_line(color=GRID_LINE, size=0.3),
        plot_title=element_text(size=16, face="bold", color=INK),
        axis_title=element_text(size=12, color=INK),
        axis_text=element_text(size=10, color=INK_SOFT),
        axis_line=element_line(color=INK_SOFT, size=0.3),
        legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT),
        legend_title=element_text(size=12, color=INK),
        legend_text=element_text(size=10, color=INK_SOFT),
        legend_position="right",
    )
    + ggsize(800, 450)
)

# Save: 800 x 450 at scale 4 = 3200 x 1800 px
ggsave(plot, f"plot-{THEME}.png", scale=4, path=".")
ggsave(plot, f"plot-{THEME}.html", path=".")
