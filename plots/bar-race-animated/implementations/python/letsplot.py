""" anyplot.ai
bar-race-animated: Animated Bar Chart Race
Library: letsplot 4.9.0 | Python 3.13.13
Quality: 86/100 | Updated: 2026-05-19
"""

import os

import numpy as np
import pandas as pd
from lets_plot import *


LetsPlot.setup_html()

THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

IMPRINT = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD"]

np.random.seed(42)

platforms = ["StreamMax", "ViewHub", "FlixNet", "WatchNow", "CineCloud", "MediaFlow"]
years = list(range(2016, 2024))

# Plausible growth: FlixNet dominates early, WatchNow/CineCloud surge to overtake
base_values = [60, 100, 155, 28, 18, 65]
growth_rates = [1.16, 1.08, 1.03, 1.26, 1.30, 1.10]

data_rows = []
for i, platform in enumerate(platforms):
    value = base_values[i]
    for year in years:
        noise = np.random.uniform(0.9, 1.1)
        value = value * growth_rates[i] * noise
        data_rows.append({"platform": platform, "year": year, "subscribers": round(value, 1)})

df = pd.DataFrame(data_rows)

platform_colors = dict(zip(platforms, IMPRINT))
snapshot_years = [2016, 2018, 2021, 2023]

anyplot_theme = theme(
    plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
    panel_background=element_rect(fill=PAGE_BG),
    panel_grid_major=element_blank(),
    panel_grid_minor=element_blank(),
    axis_title=element_text(color=INK),
    axis_text=element_text(color=INK_SOFT),
    axis_line=element_line(color=INK_SOFT),
    plot_title=element_text(color=INK),
    legend_position="none",
)

plots = []
for year in snapshot_years:
    year_data = df[df["year"] == year].copy()
    year_data = year_data.sort_values("subscribers", ascending=True)
    year_data["platform"] = pd.Categorical(
        year_data["platform"], categories=year_data["platform"].tolist(), ordered=True
    )

    plot = (
        ggplot(year_data, aes(x="platform", y="subscribers", fill="platform"))
        + geom_bar(stat="identity", width=0.7, alpha=0.9)
        + coord_flip()
        + scale_fill_manual(values=platform_colors)
        + labs(title=str(year), x="", y="Subscribers (millions)")
        + theme_minimal()
        + anyplot_theme
        + theme(
            plot_title=element_text(size=28, face="bold", color=INK),
            axis_title_x=element_text(size=18, color=INK),
            axis_title_y=element_blank(),
            axis_text_x=element_text(size=16, color=INK_SOFT),
            axis_text_y=element_text(size=18, color=INK_SOFT),
        )
    )
    plots.append(plot)

grid = (
    gggrid(plots, ncol=2)
    + labs(title="bar-race-animated · python · letsplot · anyplot.ai")
    + theme(
        plot_title=element_text(size=32, face="bold", hjust=0.5, color=INK),
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
    )
    + ggsize(1600, 900)
)

ggsave(grid, f"plot-{THEME}.png", path=".", scale=3)
ggsave(grid, f"plot-{THEME}.html", path=".")
