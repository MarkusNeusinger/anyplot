""" anyplot.ai
bar-stacked-percent: 100% Stacked Bar Chart
Library: letsplot 4.9.0 | Python 3.13.13
Quality: 94/100 | Updated: 2026-05-08
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
    geom_bar,
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
GRID_COLOR = "rgba(26,26,23,0.10)" if THEME == "light" else "rgba(240,239,232,0.10)"

# Okabe-Ito palette (first series always #009E73)
IMPRINT = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030"]

# Data: Energy source mix by country (renewable adoption comparison)
data = {
    "country": ["Germany"] * 5 + ["France"] * 5 + ["UK"] * 5 + ["Spain"] * 5 + ["Italy"] * 5 + ["Poland"] * 5,
    "source": ["Coal", "Natural Gas", "Nuclear", "Renewables", "Other"] * 6,
    "value": [
        # Germany
        26,
        15,
        6,
        46,
        7,
        # France
        2,
        7,
        68,
        21,
        2,
        # UK
        5,
        38,
        15,
        39,
        3,
        # Spain
        3,
        22,
        21,
        50,
        4,
        # Italy
        6,
        42,
        0,
        45,
        7,
        # Poland
        68,
        10,
        0,
        17,
        5,
    ],
}

df = pd.DataFrame(data)

# Set category order for proper stacking
df["country"] = pd.Categorical(
    df["country"], categories=["Germany", "France", "UK", "Spain", "Italy", "Poland"], ordered=True
)
df["source"] = pd.Categorical(
    df["source"], categories=["Coal", "Natural Gas", "Nuclear", "Renewables", "Other"], ordered=True
)

# Create 100% stacked bar chart with position="fill"
plot = (
    ggplot(df, aes(x="country", y="value", fill="source"))
    + geom_bar(stat="identity", position="fill", width=0.75, alpha=0.9)
    + scale_fill_manual(values=IMPRINT)
    + scale_y_continuous(format=".0%")
    + labs(
        title="bar-stacked-percent · letsplot · anyplot.ai", x="Country", y="Share of Energy Mix", fill="Energy Source"
    )
    + theme_minimal()
    + theme(
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG),
        panel_grid_major=element_line(color=GRID_COLOR, size=0.2),
        panel_grid_minor=element_blank(),
        axis_title=element_text(size=20, color=INK),
        axis_text=element_text(size=16, color=INK_SOFT),
        plot_title=element_text(size=24, face="bold", color=INK),
        legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT),
        legend_title=element_text(size=16, color=INK),
        legend_text=element_text(size=16, color=INK_SOFT),
        legend_position="right",
        panel_grid_major_x=element_blank(),
    )
    + ggsize(1600, 900)
)

# Save as PNG (scale 3x for 4800 x 2700 px) and HTML
ggsave(plot, f"plot-{THEME}.png", path=".", scale=3)
ggsave(plot, f"plot-{THEME}.html", path=".")
