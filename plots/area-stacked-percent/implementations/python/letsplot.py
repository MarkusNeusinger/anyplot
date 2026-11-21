""" anyplot.ai
area-stacked-percent: 100% Stacked Area Chart
Library: letsplot 4.11.0 | Python 3.14.10
Quality: 81/100 | Updated: 2026-11-21
"""

import os

import pandas as pd
from lets_plot import (
    LetsPlot,
    aes,
    element_blank,
    element_line,
    element_rect,
    element_text,
    geom_area,
    ggplot,
    ggsize,
    labs,
    scale_fill_manual,
    scale_x_continuous,
    scale_y_continuous,
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
GRID_COLOR = "rgba(26,26,23,0.10)" if THEME == "light" else "rgba(240,239,232,0.10)"

# Imprint palette: all eight positions, one per category in order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Columns: set these to your table's column names
YEAR = "Year"  # role: time
COMPANY = "Company"  # role: category
REVENUE = "Revenue (million USD)"  # role: value

# Data: replace this block with your own table, for example df = pd.read_csv("market.csv")
years = list(range(2016, 2024))
revenue = {
    "Company D": [10, 10, 10, 9, 9, 9, 9, 8],  # smallest, slight decline
    "Company C": [15, 16, 15, 16, 15, 14, 13, 12],  # stable small player
    "Company B": [35, 36, 33, 30, 28, 25, 23, 22],  # declining
    "Company A": [40, 38, 42, 45, 48, 52, 55, 58],  # growing leader
}
df = pd.DataFrame(
    {
        YEAR: years * len(revenue),
        COMPANY: [name for name in revenue for _ in years],
        REVENUE: [v for values in revenue.values() for v in values],
    }
)

# Plot: reads only df and the constants above
plot = (
    ggplot(df, aes(x=YEAR, y=REVENUE, fill=COMPANY))
    + geom_area(position="fill", alpha=0.85, color=PAGE_BG, size=0.4)
    + scale_fill_manual(values=IMPRINT_PALETTE)
    + scale_x_continuous(breaks=sorted(df[YEAR].dropna().unique()), format="d")
    + scale_y_continuous(format=".0%")
    + labs(x=YEAR, y="Share of total (%)", title="area-stacked-percent · python · letsplot · anyplot.ai")
    + theme_minimal()
    + theme(
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG),
        panel_grid_major=element_line(color=GRID_COLOR, size=0.3),
        panel_grid_minor=element_blank(),
        plot_title=element_text(size=16, color=INK),
        axis_title=element_text(size=12, color=INK),
        axis_text=element_text(size=10, color=INK_SOFT),
        axis_line=element_line(color=INK_SOFT),
        legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT),
        legend_text=element_text(size=10, color=INK_SOFT),
        legend_title=element_text(size=12, color=INK),
    )
    + ggsize(800, 450)
)

# Save PNG (scale=4 gives 3200x1800) and HTML
ggsave(plot, f"plot-{THEME}.png", path=".", scale=4)
ggsave(plot, f"plot-{THEME}.html", path=".")
