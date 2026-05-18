""" anyplot.ai
lollipop-grouped: Grouped Lollipop Chart
Library: letsplot 4.9.0 | Python 3.13.13
Quality: 88/100 | Updated: 2026-05-17
"""

import os

import pandas as pd
from lets_plot import (
    LetsPlot,
    aes,
    element_blank,
    element_rect,
    element_text,
    geom_point,
    geom_segment,
    ggplot,
    ggsize,
    labs,
    scale_color_manual,
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

# Okabe-Ito palette
OKABE_ITO = ["#009E73", "#D55E00", "#0072B2"]

# Data - Quarterly revenue by product line across regions
regions = ["North", "South", "East", "West"]
products = ["Electronics", "Furniture", "Clothing"]

data_rows = []
revenue_data = {"North": [245, 180, 125], "South": [198, 165, 142], "East": [267, 195, 118], "West": [223, 172, 156]}

for i, region in enumerate(regions):
    for j, product in enumerate(products):
        data_rows.append(
            {
                "region": region,
                "product": product,
                "revenue": revenue_data[region][j],
                "x_pos": i + (j - 1) * 0.25,
                "y_start": 0,
            }
        )

df = pd.DataFrame(data_rows)

# Plot
plot = (
    ggplot(df)
    + geom_segment(mapping=aes(x="x_pos", xend="x_pos", y="y_start", yend="revenue", color="product"), size=2)
    + geom_point(mapping=aes(x="x_pos", y="revenue", color="product"), size=8)
    + scale_color_manual(values=OKABE_ITO, name="Product Line")
    + labs(x="Region", y="Revenue ($ thousands)", title="lollipop-grouped · Python · letsplot · anyplot.ai")
    + scale_x_continuous(breaks=list(range(len(regions))), labels=regions)
    + scale_y_continuous(limits=[0, 300])
    + ggsize(1600, 900)
    + theme_minimal()
    + theme(
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG),
        panel_grid_major_x=element_blank(),
        panel_grid_major_y=element_blank(),
        panel_grid_minor=element_blank(),
        axis_text_x=element_text(size=16, color=INK_SOFT),
        axis_text_y=element_text(size=16, color=INK_SOFT),
        axis_title=element_text(size=20, color=INK),
        plot_title=element_text(size=24, color=INK),
        legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT),
        legend_title=element_text(size=18, color=INK),
        legend_text=element_text(size=16, color=INK_SOFT),
    )
)

# Save
ggsave(plot, filename=f"plot-{THEME}.png", path=".", scale=3)
ggsave(plot, filename=f"plot-{THEME}.html", path=".")
