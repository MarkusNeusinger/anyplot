"""anyplot.ai
heatmap-basic: Basic Heatmap
Library: plotnine 0.15.4 | Python 3.13.13
Quality: 85/100 | Updated: 2026-05-28
"""

import os

import numpy as np
import pandas as pd
from plotnine import (
    aes,
    element_blank,
    element_rect,
    element_text,
    geom_text,
    geom_tile,
    ggplot,
    labs,
    scale_color_identity,
    scale_fill_gradient2,
    scale_x_discrete,
    scale_y_discrete,
    theme,
    theme_minimal,
)


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint diverging colormap (fields): matte-red -> page color at the midpoint -> blue
CMAP_MID = "#FAF8F1" if THEME == "light" else "#1A1A17"

# Constants
DARK_SHARE = 0.6  # a cell beyond this share of the colorbar end gets white text on the light theme
BREAK_STEP = 15  # colorbar tick spacing

# Columns: set these to your table's column names
QUARTER = "Quarter"  # role: x
DEPARTMENT = "Department"  # role: y
GROWTH = "Growth (%)"  # role: value

# Data: replace this block with your own table, for example df = pd.read_csv("growth.csv")
np.random.seed(42)
departments = ["Engineering", "Marketing", "Sales", "Finance", "Operations", "HR", "Research", "Support"]
quarters = ["Q1 '23", "Q2 '23", "Q3 '23", "Q4 '23", "Q1 '24", "Q2 '24", "Q3 '24", "Q4 '24"]

base_trend = np.linspace(-18, 22, 8)
dept_offsets = np.array([-6, 10, 14, -3, 4, -10, 8, -5])
values = np.round(base_trend[np.newaxis, :] + dept_offsets[:, np.newaxis] + np.random.normal(0, 4, (8, 8)), 1)

values[5, 0] = -32.5  # HR deep crisis Q1 '23
values[2, 7] = 38.2  # Sales strong recovery Q4 '24
values[6, 6] = 33.7  # Research surge Q3 '24

dept_idx, qtr_idx = np.meshgrid(np.arange(8), np.arange(8), indexing="ij")
df = pd.DataFrame(
    {
        QUARTER: [quarters[j] for j in qtr_idx.ravel()],
        DEPARTMENT: [departments[i] for i in dept_idx.ravel()],
        GROWTH: values.ravel(),
    }
)

# Plot: reads only df and the constants above
low = np.floor(df[GROWTH].min() / 5) * 5
high = np.ceil(df[GROWTH].max() / 5) * 5
breaks = np.arange(np.ceil(low / BREAK_STEP) * BREAK_STEP, high + 1, BREAK_STEP)

# Cell text: white on the strongly colored cells of the light theme, INK everywhere else
share = np.where(df[GROWTH] > 0, df[GROWTH] / high, df[GROWTH] / low)
df["label"] = [f"{v:+.1f}" for v in df[GROWTH]]
df["text_color"] = np.where((share > DARK_SHARE) & (THEME == "light"), "white", INK)

title = "heatmap-basic · python · plotnine · anyplot.ai"
title_fs = max(8, round(12 * 67 / len(title))) if len(title) > 67 else 12

plot = (
    ggplot(df, aes(x=QUARTER, y=DEPARTMENT))
    + geom_tile(aes(fill=GROWTH), color=INK_SOFT, size=0.6)
    + geom_text(aes(label="label", color="text_color"), size=5, fontweight="bold", show_legend=False)
    + scale_fill_gradient2(low="#AE3030", mid=CMAP_MID, high="#4467A3", midpoint=0, limits=(low, high), breaks=breaks)
    + scale_color_identity()
    + scale_x_discrete(limits=df[QUARTER].unique().tolist(), expand=(0, 0))
    + scale_y_discrete(limits=df[DEPARTMENT].unique().tolist()[::-1], expand=(0, 0))
    + labs(title=title, subtitle="Year-over-year growth rate (%) · Q1 2023 – Q4 2024")
    + theme_minimal()
    + theme(
        figure_size=(6, 6),
        text=element_text(family="sans-serif", color=INK),
        plot_title=element_text(size=title_fs, ha="center", weight="bold", color=INK),
        plot_subtitle=element_text(size=8, ha="center", color=INK_SOFT),
        axis_title_x=element_text(size=10, color=INK, margin={"t": 6}),
        axis_title_y=element_text(size=10, color=INK, margin={"r": 6}),
        axis_text_x=element_text(size=8, color=INK_SOFT, rotation=45, ha="right"),
        axis_text_y=element_text(size=8, color=INK_SOFT, ha="right"),
        legend_title=element_text(size=8, weight="bold", color=INK),
        legend_text=element_text(size=7, color=INK_SOFT),
        legend_position="right",
        legend_key_height=110,
        legend_key_width=22,
        legend_background=element_rect(fill=ELEVATED_BG, color="none"),
        panel_grid_major=element_blank(),
        panel_grid_minor=element_blank(),
        panel_background=element_rect(fill=PAGE_BG),
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        plot_margin=0.04,
    )
)

plot.save(f"plot-{THEME}.png", dpi=400, width=6, height=6, units="in", verbose=False)
