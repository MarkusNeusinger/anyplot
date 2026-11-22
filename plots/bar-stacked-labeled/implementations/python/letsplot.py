""" anyplot.ai
bar-stacked-labeled: Stacked Bar Chart with Total Labels
Library: letsplot 4.11.0 | Python 3.14.10
Quality: 81/100 | Updated: 2026-11-22
"""

import os
import shutil

import pandas as pd
from lets_plot import (
    LetsPlot,
    aes,
    element_line,
    element_rect,
    element_text,
    geom_bar,
    geom_text,
    ggplot,
    ggsave,
    ggsize,
    labs,
    scale_fill_manual,
    scale_y_continuous,
    theme,
    theme_minimal,
)


LetsPlot.setup_html()

# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Column constants
QUARTER = "Quarter"  # role: category
PRODUCT = "Product"  # role: component
REVENUE = "Revenue (Millions USD)"  # role: value

# Data: replace this block with your own table, for example df = pd.read_csv("revenue.csv")
df = pd.DataFrame(
    {
        QUARTER: ["Q1"] * 3 + ["Q2"] * 3 + ["Q3"] * 3 + ["Q4"] * 3,
        PRODUCT: ["Electronics", "Software", "Services"] * 4,
        REVENUE: [45, 32, 18, 52, 38, 22, 48, 41, 25, 58, 45, 28],
    }
)

# Plot
totals = df.groupby(QUARTER, sort=False)[REVENUE].sum().reset_index()
totals["Label"] = totals[REVENUE].map(lambda total: f"${total:g}M")

plot = (
    ggplot()
    + geom_bar(data=df, mapping=aes(x=QUARTER, y=REVENUE, fill=PRODUCT), stat="identity", position="stack", width=0.7)
    + geom_text(
        data=totals,
        mapping=aes(x=QUARTER, y=REVENUE, label="Label"),
        position="identity",
        vjust=-0.5,
        size=6,
        fontface="bold",
        color=INK,
    )
    + scale_fill_manual(values=IMPRINT_PALETTE)
    + scale_y_continuous(limits=[0, totals[REVENUE].max() * 1.12])
    + labs(title="bar-stacked-labeled · python · letsplot · anyplot.ai")
    + theme_minimal()
    + theme(
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG),
        panel_grid_major=element_line(color=INK_SOFT, size=0.3),
        axis_title=element_text(size=12, color=INK),
        axis_text=element_text(size=10, color=INK_SOFT),
        axis_line=element_line(color=INK_SOFT),
        plot_title=element_text(size=16, face="bold", color=INK),
        legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT),
        legend_text=element_text(size=10, color=INK_SOFT),
        legend_title=element_text(size=12, color=INK),
    )
    + ggsize(800, 450)
)

# Save as PNG (3200 x 1800 px) and HTML
ggsave(plot, f"plot-{THEME}.png", scale=4)
ggsave(plot, f"plot-{THEME}.html")

# lets-plot writes into a lets-plot-images subdirectory; move the files here
if os.path.exists("lets-plot-images"):
    for f in [f"plot-{THEME}.png", f"plot-{THEME}.html"]:
        src = os.path.join("lets-plot-images", f)
        if os.path.exists(src):
            shutil.move(src, f)
    if not os.listdir("lets-plot-images"):
        shutil.rmtree("lets-plot-images")
