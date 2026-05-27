""" anyplot.ai
bar-stacked: Stacked Bar Chart
Library: letsplot 4.9.0 | Python 3.13.13
Quality: 88/100 | Updated: 2026-05-09
"""

import os

import pandas as pd
from lets_plot import *


LetsPlot.setup_html()

# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
RULE = "rgba(26,26,23,0.15)" if THEME == "light" else "rgba(240,239,232,0.15)"

# Okabe-Ito palette
IMPRINT = ["#009E73", "#C475FD", "#4467A3", "#BD8233"]

# Data: Quarterly sales by product category
data = {
    "quarter": ["Q1", "Q2", "Q3", "Q4"] * 4,
    "product": ["Electronics"] * 4 + ["Furniture"] * 4 + ["Clothing"] * 4 + ["Office Supplies"] * 4,
    "sales": [
        120,
        145,
        165,
        190,  # Electronics
        85,
        92,
        78,
        110,  # Furniture
        65,
        88,
        95,
        72,  # Clothing
        45,
        52,
        48,
        58,  # Office Supplies
    ],
}
df = pd.DataFrame(data)

# Create stacked bar chart with refined visual presentation
plot = (
    ggplot(df, aes(x="quarter", y="sales", fill="product"))
    + geom_bar(
        stat="identity",
        position="stack",
        width=0.65,
        color="white",
        size=0.3,
        tooltips=layer_tooltips().title("@product").line("Sales: @sales K$").format("sales", ".0f"),
    )
    + scale_fill_manual(values=IMPRINT)
    + labs(title="bar-stacked · letsplot · anyplot.ai", x="Quarter", y="Sales (Thousands $)", fill="Product")
    + theme(
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG),
        panel_grid_major_y=element_line(color=RULE, size=0.25),
        panel_grid_major_x=element_blank(),
        panel_grid_minor=element_blank(),
        axis_title=element_text(size=20, color=INK),
        axis_text=element_text(size=16, color=INK_SOFT),
        axis_ticks=element_blank(),
        axis_line_y=element_line(color=INK_SOFT, size=0.3),
        axis_line_x=element_line(color=INK_SOFT, size=0.3),
        plot_title=element_text(size=24, color=INK),
        legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT, size=0.3),
        legend_text=element_text(size=16, color=INK_SOFT),
        legend_title=element_text(size=16, color=INK),
        legend_position="right",
    )
    + ggsize(1600, 900)
)

# Save PNG (scale 3x for 4800 × 2700 px)
ggsave(plot, f"plot-{THEME}.png", path=".", scale=3)

# Save HTML
ggsave(plot, f"plot-{THEME}.html", path=".")
