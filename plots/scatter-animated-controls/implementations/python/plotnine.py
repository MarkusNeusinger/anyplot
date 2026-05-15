""" anyplot.ai
scatter-animated-controls: Animated Scatter Plot with Play Controls
Library: plotnine 0.15.4 | Python 3.13.13
Quality: 87/100 | Created: 2026-05-15
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
    geom_point,
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

OKABE_ITO = ["#009E73", "#D55E00", "#0072B2", "#CC79A7"]

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

plot = (
    ggplot(df, aes(x="gdp_per_capita", y="life_expectancy", color="region", size="population"))
    + geom_point(alpha=0.6, stroke=0.5)
    + scale_color_manual(values=OKABE_ITO)
    + scale_size_continuous(range=(2, 8))
    + facet_wrap("~year", nrow=2, ncol=3)
    + labs(
        x="GDP per Capita (USD thousands)",
        y="Life Expectancy (years)",
        title="scatter-animated-controls · plotnine · anyplot.ai",
        color="Region",
        size="Population\n(millions)",
    )
    + theme_minimal()
    + theme(
        figure_size=(16, 9),
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG),
        panel_grid_major=element_line(color=INK, size=0.3, alpha=0.10),
        panel_grid_minor=element_blank(),
        panel_border=element_rect(color=INK_SOFT, fill=None, size=0.3),
        axis_title=element_text(color=INK, size=20),
        axis_text=element_text(color=INK_SOFT, size=16),
        axis_line=element_line(color=INK_SOFT, size=0.3),
        plot_title=element_text(color=INK, size=24, weight="medium"),
        strip_text=element_text(color=INK, size=18, weight="medium"),
        legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT, size=0.3),
        legend_text=element_text(color=INK_SOFT, size=16),
        legend_title=element_text(color=INK, size=16),
        legend_position="right",
    )
)

ggsave(plot, filename=f"plot-{THEME}.png", dpi=300, width=16, height=9, verbose=False)
