"""anyplot.ai
area-stacked-percent: 100% Stacked Area Chart
Library: plotnine 0.15.4 | Python 3.13.13
Quality: 83/100 | Updated: 2026-05-12
"""

import os

import pandas as pd
from plotnine import (
    aes,
    element_line,
    element_rect,
    element_text,
    geom_area,
    ggplot,
    labs,
    scale_fill_manual,
    scale_x_continuous,
    scale_y_continuous,
    theme,
    theme_minimal,
)


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: all eight positions, one per category in order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Columns: set these to your table's column names
YEAR = "Year"  # role: time
PRODUCT = "Product category"  # role: category
UNITS = "Units sold (millions)"  # role: value

# Data: replace this block with your own table, for example df = pd.read_csv("shipments.csv")
years = list(range(2015, 2025))
df = pd.DataFrame(
    {
        YEAR: years * 4,
        PRODUCT: ["Smartphones"] * 10 + ["Tablets"] * 10 + ["Wearables"] * 10 + ["Laptops"] * 10,
        UNITS: [50, 48, 44, 40, 35, 32, 28, 25, 22, 20]
        + [28, 26, 22, 18, 15, 12, 10, 8, 6, 5]
        + [4, 8, 14, 20, 26, 32, 38, 42, 46, 48]
        + [18, 18, 20, 22, 24, 24, 24, 25, 26, 27],
    }
)

# Plot: reads only df and the constants above
SHARE = "Market share (%)"
df[SHARE] = df[UNITS] / df.groupby(YEAR)[UNITS].transform("sum") * 100
categories = df[PRODUCT].unique().tolist()

plot = (
    ggplot(df, aes(x=YEAR, y=SHARE, fill=PRODUCT))
    + geom_area(position="stack", color=PAGE_BG, size=0.3)
    + scale_fill_manual(values=IMPRINT_PALETTE, limits=categories)
    + scale_x_continuous(breaks=range(int(df[YEAR].min()), int(df[YEAR].max()) + 1, 2), expand=(0, 0))
    + scale_y_continuous(breaks=[0, 25, 50, 75, 100], labels=lambda b: [f"{v:g}%" for v in b], expand=(0, 0))
    + labs(title="area-stacked-percent · python · plotnine · anyplot.ai")
    + theme_minimal()
    + theme(
        figure_size=(8, 4.5),
        text=element_text(size=7),
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG),
        panel_grid_major=element_line(color=INK, size=0.3, alpha=0.10),
        panel_grid_minor=element_line(color=INK, size=0.2, alpha=0.05),
        panel_border=element_rect(color=INK_SOFT, fill=None),
        plot_title=element_text(size=12, weight="bold", color=INK),
        axis_title=element_text(size=10, color=INK),
        axis_text=element_text(size=8, color=INK_SOFT),
        axis_line=element_line(color=INK_SOFT, size=0.4),
        legend_position="right",
        legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT),
        legend_text=element_text(size=8, color=INK_SOFT),
        legend_title=element_text(size=9, color=INK),
    )
)

plot.save(f"plot-{THEME}.png", dpi=400, width=8, height=4.5, units="in", verbose=False)
