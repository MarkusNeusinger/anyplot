"""anyplot.ai
bar-stacked: Stacked Bar Chart
Library: plotnine 0.15.4 | Python 3.13.13
Quality: pending | Updated: 2026-11-20
"""

import os
import pathlib

import pandas as pd
from plotnine import (
    aes,
    element_line,
    element_rect,
    element_text,
    geom_bar,
    geom_text,
    ggplot,
    labs,
    position_stack,
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

# Imprint palette: all eight positions, one per component in order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Columns: set these to your table's column names
QUARTER = "Quarter"  # role: category
CATEGORY = "Category"  # role: component
SALES = "Sales (thousands USD)"  # role: value

# Data: replace this block with your own table, for example df = pd.read_csv("sales.csv")
df = pd.DataFrame(
    {
        QUARTER: ["Q1", "Q2", "Q3", "Q4"] * 4,
        CATEGORY: ["Sports"] * 4 + ["Home"] * 4 + ["Clothing"] * 4 + ["Electronics"] * 4,
        SALES: [18, 22, 28, 25, 28, 31, 35, 38, 32, 38, 55, 42, 45, 52, 48, 68],
    }
)

# Plot: reads only df and the constants above
components = df[CATEGORY].unique().tolist()
plot = (
    ggplot(df, aes(x=QUARTER, y=SALES, fill=CATEGORY))
    + geom_bar(stat="identity", position="stack", width=0.7)
    + geom_text(aes(label=SALES), position=position_stack(vjust=0.5), size=5, color="white", fontweight="bold")
    + scale_x_discrete(limits=df[QUARTER].unique().tolist())
    + scale_fill_manual(values=IMPRINT_PALETTE, limits=components)
    + labs(title="bar-stacked · python · plotnine · anyplot.ai")
    + theme_minimal()
    + theme(
        figure_size=(8, 4.5),
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG),
        panel_grid_major=element_line(color=INK, size=0.3, alpha=0.10),
        panel_grid_minor=element_line(color=INK, size=0.2, alpha=0.05),
        panel_border=element_rect(color=INK_SOFT, fill=None),
        plot_title=element_text(size=12, weight="bold", color=INK),
        axis_title=element_text(size=10, color=INK),
        axis_text=element_text(size=8, color=INK_SOFT),
        legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT),
        legend_title=element_text(size=9, color=INK),
        legend_text=element_text(size=8, color=INK_SOFT),
        legend_position="right",
    )
)

# Save
plot.save(pathlib.Path(__file__).parent / f"plot-{THEME}.png", dpi=400, width=8, height=4.5, units="in", verbose=False)
