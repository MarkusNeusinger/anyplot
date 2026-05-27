""" anyplot.ai
bar-stacked-labeled: Stacked Bar Chart with Total Labels
Library: letsplot 4.9.0 | Python 3.13.13
Quality: 85/100 | Updated: 2026-05-18
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

# Okabe-Ito palette
IMPRINT = ["#009E73", "#C475FD", "#4467A3"]

# Data - Quarterly revenue by product category (in millions)
data = {
    "Quarter": ["Q1", "Q1", "Q1", "Q2", "Q2", "Q2", "Q3", "Q3", "Q3", "Q4", "Q4", "Q4"],
    "Product": [
        "Electronics",
        "Software",
        "Services",
        "Electronics",
        "Software",
        "Services",
        "Electronics",
        "Software",
        "Services",
        "Electronics",
        "Software",
        "Services",
    ],
    "Revenue": [45, 32, 18, 52, 38, 22, 48, 41, 25, 58, 45, 28],
}
df = pd.DataFrame(data)

# Calculate totals for each quarter
totals = df.groupby("Quarter", sort=False)["Revenue"].sum().reset_index()
totals.columns = ["Quarter", "Total"]
totals["Label"] = totals["Total"].apply(lambda x: f"${x}M")

# Create stacked bar chart with total labels
plot = (
    ggplot()
    + geom_bar(
        data=df, mapping=aes(x="Quarter", y="Revenue", fill="Product"), stat="identity", position="stack", width=0.7
    )
    + geom_text(
        data=totals,
        mapping=aes(x="Quarter", y="Total", label="Label"),
        position="identity",
        vjust=-0.5,
        size=18,
        fontface="bold",
        color=INK,
    )
    + scale_fill_manual(values=IMPRINT)
    + labs(
        title="bar-stacked-labeled · Python · letsplot · anyplot.ai",
        x="Quarter",
        y="Revenue (Millions USD)",
        fill="Product",
    )
    + theme_minimal()
    + theme(
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG),
        panel_grid_major=element_line(color=INK_SOFT, size=0.3),
        axis_title=element_text(size=20, color=INK),
        axis_text=element_text(size=16, color=INK_SOFT),
        axis_line=element_line(color=INK_SOFT),
        plot_title=element_text(size=24, face="bold", color=INK),
        legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT),
        legend_text=element_text(size=16, color=INK_SOFT),
        legend_title=element_text(size=18, color=INK),
    )
    + ggsize(1600, 900)
)

# Save as PNG and HTML with theme suffix (scale 3x for 4800 × 2700 px)
ggsave(plot, f"plot-{THEME}.png", scale=3)
ggsave(plot, f"plot-{THEME}.html")

# Move files from lets-plot-images subdirectory to current directory (lets-plot quirk)
if os.path.exists("lets-plot-images"):
    for f in [f"plot-{THEME}.png", f"plot-{THEME}.html"]:
        src = os.path.join("lets-plot-images", f)
        if os.path.exists(src):
            shutil.move(src, f)
    # Clean up subdirectory if empty
    if not os.listdir("lets-plot-images"):
        shutil.rmtree("lets-plot-images")
