""" anyplot.ai
errorbar-asymmetric: Asymmetric Error Bars Plot
Library: letsplot 4.11.0 | Python 3.14.10
Quality: 81/100 | Updated: 2026-11-21
"""
# ruff: noqa: F405

import os

import pandas as pd
from lets_plot import *  # noqa: F403, F401
from lets_plot.export import ggsave


LetsPlot.setup_html()

# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: all eight positions in canonical order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Columns: set these to your table's column names
QUARTER = "Quarter"  # role: x
SALES = "Sales (thousand USD)"  # role: y
ERROR_LOWER = "Lower error"  # role: error_lower
ERROR_UPPER = "Upper error"  # role: error_upper

# Data: replace this block with your own table, for example df = pd.read_csv("sales.csv")
df = pd.DataFrame(
    {
        QUARTER: ["Q1", "Q2", "Q3", "Q4"],
        SALES: [85, 92, 78, 105],
        ERROR_LOWER: [8, 5, 12, 7],
        ERROR_UPPER: [15, 18, 6, 22],
    }
)

# Plot: reads only df and the constants above
LOW = "Lower bound"
HIGH = "Upper bound"
df[LOW] = df[SALES] - df[ERROR_LOWER]
df[HIGH] = df[SALES] + df[ERROR_UPPER]

anyplot_theme = theme(
    plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
    panel_background=element_rect(fill=PAGE_BG),
    panel_grid_major=element_line(color=INK_SOFT, size=0.2),
    panel_grid_minor=element_blank(),
    axis_title=element_text(color=INK, size=12),
    axis_text=element_text(color=INK_SOFT, size=10),
    axis_line=element_line(color=INK_SOFT, size=0.5),
    plot_title=element_text(color=INK, size=16, face="bold"),
    plot_caption=element_text(color=INK_SOFT, size=10),
    legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT),
    legend_text=element_text(color=INK_SOFT, size=10),
)

plot = (
    ggplot(df, aes(x=QUARTER, y=SALES))
    + geom_errorbar(aes(ymin=LOW, ymax=HIGH), width=0.3, size=1.5, color=IMPRINT_PALETTE[0])
    + geom_point(
        size=6,
        color=IMPRINT_PALETTE[0],
        alpha=0.9,
        tooltips=layer_tooltips()
        .line(f"{QUARTER}|@{{{QUARTER}}}")
        .line(f"Sales|@{{{SALES}}}")
        .line(f"Min|@{{{LOW}}}")
        .line(f"Max|@{{{HIGH}}}"),
    )
    + labs(
        x=QUARTER,
        y=SALES,
        title="errorbar-asymmetric · python · letsplot · anyplot.ai",
        caption="Error bars represent 10th-90th percentile forecast range",
    )
    + scale_y_continuous(limits=[df[LOW].min() * 0.75, df[HIGH].max() * 1.1])
    + theme_minimal()
    + anyplot_theme
    + ggsize(800, 450)
)

# Save
ggsave(plot, filename=f"plot-{THEME}.png", path=".", scale=4)
ggsave(plot, filename=f"plot-{THEME}.html", path=".")
