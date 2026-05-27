""" anyplot.ai
scatter-animated-controls: Animated Scatter Plot with Play Controls
Library: plotnine 0.15.4 | Python 3.13.13
Quality: 94/100 | Created: 2026-05-15
"""

import os

import numpy as np
import pandas as pd
from plotnine import (
    aes,
    element_blank,
    element_line,
    element_rect,
    element_text,
    facet_wrap,
    geom_hline,
    geom_path,
    geom_point,
    geom_vline,
    ggplot,
    ggsave,
    labs,
    scale_color_manual,
    scale_size_continuous,
    theme,
    theme_minimal,
)


THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
REFERENCE_LINE = "#CCB8B0" if THEME == "light" else "#3A3935"

IMPRINT = ["#009E73", "#C475FD", "#4467A3", "#BD8233"]

np.random.seed(42)

entities = [
    "Country A",
    "Country B",
    "Country C",
    "Country D",
    "Country E",
    "Country F",
    "Country G",
    "Country H",
    "Country I",
    "Country J",
]
years = [2000, 2005, 2010, 2015, 2020, 2024]
regions = ["Asia", "Europe", "Americas", "Africa"]

data_list = []
for year in years:
    for i, entity in enumerate(entities):
        region = regions[i % len(regions)]
        base_x = 20 + i * 6
        base_y = 50 + (i % 3) * 15
        x = base_x + np.random.normal(0, 2) + (year - 2000) * 0.3
        y = base_y + np.random.normal(0, 2.5) + (year - 2000) * 0.5
        pop = 50 + i * 5 + (year - 2000) * 0.8 + np.random.normal(0, 1)
        data_list.append(
            {
                "year": year,
                "entity": entity,
                "region": region,
                "gdp_per_capita": np.clip(x, 15, 85),
                "life_expectancy": np.clip(y, 40, 90),
                "population": np.clip(pop, 20, 120),
            }
        )

df = pd.DataFrame(data_list)

# Calculate medians for reference lines (visual structure)
median_gdp = df["gdp_per_capita"].median()
median_life = df["life_expectancy"].median()

plot = (
    ggplot(df, aes(x="gdp_per_capita", y="life_expectancy", color="region", size="population"))
    + geom_vline(aes(xintercept=median_gdp), color=REFERENCE_LINE, size=0.5, alpha=0.4, linetype="dashed")
    + geom_hline(aes(yintercept=median_life), color=REFERENCE_LINE, size=0.5, alpha=0.4, linetype="dashed")
    + geom_path(aes(group="entity"), color=INK_SOFT, size=0.3, alpha=0.15, linetype="solid")
    + geom_point(alpha=0.7, stroke=0.8)
    + scale_color_manual(values=IMPRINT, name="Region")
    + scale_size_continuous(range=(2.5, 9), name="Population\n(millions)")
    + facet_wrap("~year", nrow=2, ncol=3)
    + labs(
        x="GDP per Capita (USD thousands)",
        y="Life Expectancy (years)",
        title="scatter-animated-controls · plotnine · anyplot.ai",
    )
    + theme_minimal()
    + theme(
        figure_size=(16, 9),
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG),
        panel_grid_major=element_line(color=INK, size=0.25, alpha=0.08),
        panel_grid_minor=element_blank(),
        panel_border=element_rect(color=INK_SOFT, fill=None, size=0.4),
        panel_spacing_x=0.15,
        panel_spacing_y=0.15,
        axis_title=element_text(color=INK, size=20, weight="medium"),
        axis_text=element_text(color=INK_SOFT, size=15),
        axis_line=element_line(color=INK_SOFT, size=0.4),
        plot_title=element_text(color=INK, size=26, weight="bold", margin={"t": 0, "b": 15}),
        strip_text=element_text(color=INK, size=19, weight="bold"),
        strip_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT, size=0.3),
        legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT, size=0.4),
        legend_text=element_text(color=INK_SOFT, size=15),
        legend_title=element_text(color=INK, size=16, weight="bold"),
        legend_position="right",
        legend_margin=8,
    )
)

ggsave(plot, filename=f"plot-{THEME}.png", dpi=300, width=16, height=9, verbose=False)
