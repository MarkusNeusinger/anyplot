""" anyplot.ai
lollipop-grouped: Grouped Lollipop Chart
Library: letsplot 4.11.0 | Python 3.14.10
Quality: 78/100 | Updated: 2026-11-22
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

# Imprint palette
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Column constants
REGION = "Region"  # role: category
PRODUCT = "Product Line"  # role: series
REVENUE = "Revenue ($ thousands)"  # role: value

# Data - Quarterly revenue by product line across regions
raw = {
    "North": {"Electronics": 245, "Furniture": 180, "Clothing": 125},
    "South": {"Electronics": 198, "Furniture": 165, "Clothing": 142},
    "East": {"Electronics": 267, "Furniture": 195, "Clothing": 118},
    "West": {"Electronics": 223, "Furniture": 172, "Clothing": 156},
}
df = pd.DataFrame(
    [
        {REGION: region, PRODUCT: product, REVENUE: value}
        for region, values in raw.items()
        for product, value in values.items()
    ]
)

# Plot
X_POS = "x_pos"
BASELINE = "baseline"
# Regions sorted by total revenue (descending), series keep one order in every group
regions = df.groupby(REGION)[REVENUE].sum().sort_values(ascending=False).index.tolist()
series = list(dict.fromkeys(df[PRODUCT]))
offset = 0.75 / len(series)
df[X_POS] = df[REGION].map(regions.index) + (df[PRODUCT].map(series.index) - (len(series) - 1) / 2) * offset
df[BASELINE] = 0

plot = (
    ggplot(df)
    + geom_segment(aes(x=X_POS, xend=X_POS, y=BASELINE, yend=REVENUE, color=PRODUCT), size=1)
    + geom_point(aes(x=X_POS, y=REVENUE, color=PRODUCT), size=4)
    + scale_color_manual(values=IMPRINT_PALETTE[: len(series)])
    + labs(x=REGION, y=REVENUE, title="lollipop-grouped · python · letsplot · anyplot.ai")
    + scale_x_continuous(breaks=list(range(len(regions))), labels=regions)
    + scale_y_continuous(limits=[0, df[REVENUE].max() * 1.12])
    + ggsize(800, 450)
    + theme_minimal()
    + theme(
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG),
        panel_grid_major_x=element_blank(),
        panel_grid_major_y=element_blank(),
        panel_grid_minor=element_blank(),
        axis_text=element_text(size=10, color=INK_SOFT),
        axis_title=element_text(size=12, color=INK),
        plot_title=element_text(size=16, color=INK),
        legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT),
        legend_title=element_text(size=12, color=INK),
        legend_text=element_text(size=10, color=INK_SOFT),
    )
)

# Save
ggsave(plot, filename=f"plot-{THEME}.png", path=".", scale=4)
ggsave(plot, filename=f"plot-{THEME}.html", path=".")
