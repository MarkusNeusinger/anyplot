"""anyplot.ai
violin-split: Split Violin Plot
Library: plotnine 0.15.4 | Python 3.13.13
Quality: pending | Updated: 2026-11-19
"""

import os

import numpy as np
import pandas as pd
from plotnine import (
    aes,
    element_line,
    element_rect,
    element_text,
    geom_boxplot,
    geom_violin,
    ggplot,
    labs,
    scale_fill_manual,
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

# Imprint palette: all eight positions, one per group in order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Columns: set these to your table's column names
AGE_GROUP = "Age group (years)"  # role: category
BLOOD_PRESSURE = "Systolic blood pressure (mmHg)"  # role: value
PERIOD = "Period"  # role: split_group

# Data: replace this block with your own table, for example df = pd.read_csv("blood_pressure.csv")
np.random.seed(42)
age_groups = ["18-34", "35-49", "50-64", "65+"]
before_means, before_sds = [128, 134, 145, 156], [10, 12, 15, 18]
after_means, after_sds = [118, 123, 128, 136], [8, 10, 11, 13]
sizes = [80, 100, 90, 70]
frames = []
for i, age_group in enumerate(age_groups):
    for period, mean, sd in (
        ("Before treatment", before_means[i], before_sds[i]),
        ("After treatment", after_means[i], after_sds[i]),
    ):
        frames.append(
            pd.DataFrame({AGE_GROUP: age_group, BLOOD_PRESSURE: np.random.normal(mean, sd, sizes[i]), PERIOD: period})
        )
df = pd.concat(frames, ignore_index=True)

# Plot
periods = df[PERIOD].unique().tolist()
plot = (
    ggplot(df, aes(x=AGE_GROUP, y=BLOOD_PRESSURE, fill=PERIOD))
    + geom_violin(df[df[PERIOD] == periods[0]], style="left", alpha=0.85, size=0.4, scale="width", position="identity")
    + geom_violin(df[df[PERIOD] == periods[1]], style="right", alpha=0.85, size=0.4, scale="width", position="identity")
    + geom_boxplot(width=0.12, alpha=0.9, outlier_alpha=0.5, outlier_size=1, size=0.4, color=INK, position="identity")
    + scale_x_discrete(limits=df[AGE_GROUP].unique().tolist())
    + scale_fill_manual(values=IMPRINT_PALETTE, limits=periods)
    + labs(title="violin-split · python · plotnine · anyplot.ai")
    + theme_minimal()
    + theme(
        figure_size=(8, 4.5),
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG),
        panel_grid_major_y=element_line(color=INK, alpha=0.10, size=0.3),
        panel_grid_major_x=element_line(color=INK, alpha=0.05, size=0.2),
        panel_grid_minor=element_line(color=INK, alpha=0.04, size=0.2),
        panel_border=element_rect(color=INK_SOFT, fill=None),
        axis_title=element_text(size=10, color=INK),
        axis_text=element_text(size=8, color=INK_SOFT),
        axis_line=element_line(color=INK_SOFT),
        plot_title=element_text(size=12, color=INK, ha="center"),
        legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT),
        legend_title=element_text(size=9, color=INK),
        legend_text=element_text(size=8, color=INK_SOFT),
        legend_position="right",
    )
)

# Save
plot.save(f"plot-{THEME}.png", dpi=400, width=8, height=4.5, units="in", verbose=False)
