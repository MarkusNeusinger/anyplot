"""anyplot.ai
lollipop-grouped: Grouped Lollipop Chart
Library: plotnine 0.15.4 | Python 3.13.13
Quality: 92/100 | Updated: 2026-05-17
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
    geom_point,
    geom_segment,
    ggplot,
    labs,
    position_dodge,
    scale_color_manual,
    scale_x_discrete,
    scale_y_continuous,
    theme,
)


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: all eight positions, one per series in order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Columns: set these to your table's column names
REGION = "Region"  # role: category
PRODUCT_LINE = "Product line"  # role: series
REVENUE = "Revenue (Million USD)"  # role: value

# Data: replace this block with your own table, for example df = pd.read_csv("revenue.csv")
np.random.seed(42)
regions = ["North America", "Europe", "Asia Pacific", "Latin America"]
region_factor = {"North America": 1.2, "Europe": 1.0, "Asia Pacific": 0.9, "Latin America": 0.7}
product_base = {"Software": 85, "Hardware": 65, "Services": 50}
rows = []
for region in regions:
    for product in product_base:
        value = product_base[product] * region_factor[region] + np.random.uniform(-8, 8)
        rows.append({REGION: region, PRODUCT_LINE: product, REVENUE: value})
df = pd.DataFrame(rows)

# Plot: reads only df and the constants above
dodge = position_dodge(width=0.6)
series_order = df[PRODUCT_LINE].unique().tolist()
# A categorical keeps the data's series order in every dodged group (plotnine sorts strings alphabetically)
df[PRODUCT_LINE] = pd.Categorical(df[PRODUCT_LINE], categories=series_order, ordered=True)
plot = (
    ggplot(df, aes(x=REGION, y=REVENUE, color=PRODUCT_LINE))
    # Stems from the shared zero baseline to the value
    + geom_segment(aes(xend=REGION, y=0, yend=REVENUE), position=dodge, size=0.9)
    # Circular markers at the value
    + geom_point(position=dodge, size=4)
    + scale_x_discrete(limits=df[REGION].unique().tolist())
    + scale_color_manual(values=IMPRINT_PALETTE, limits=series_order)
    + scale_y_continuous(limits=(0, df[REVENUE].max() * 1.08))
    + labs(title="lollipop-grouped · python · plotnine · anyplot.ai")
    + theme(
        figure_size=(8, 4.5),
        text=element_text(size=7, color=INK),
        axis_title=element_text(size=10, color=INK),
        axis_text=element_text(size=8, color=INK_SOFT),
        plot_title=element_text(size=12, color=INK),
        legend_title=element_text(size=9, color=INK),
        legend_text=element_text(size=8, color=INK_SOFT),
        legend_position="right",
        legend_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        legend_key=element_rect(fill=PAGE_BG, color=PAGE_BG),
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_grid_major_y=element_line(color=INK, size=0.3, alpha=0.10),
        panel_grid_major_x=element_blank(),
        panel_grid_minor=element_blank(),
        panel_border=element_blank(),
        axis_line=element_line(color=INK_SOFT, size=0.5),
    )
)

plot.save(f"plot-{THEME}.png", dpi=400, width=8, height=4.5, units="in", verbose=False)
