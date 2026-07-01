"""anyplot.ai
lollipop-basic: Basic Lollipop Chart
Library: letsplot 4.9.0 | Python 3.14.4
Quality: 87/100 | Updated: 2026-07-01
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
    geom_point,
    geom_segment,
    ggplot,
    ggsize,
    labs,
    layer_tooltips,
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
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
RULE = "#D6D3C7" if THEME == "light" else "#3A3A34"
BRAND = "#009E73"

# Data — Product sales by category, sorted by value
categories = ["Electronics", "Clothing", "Home & Garden", "Sports", "Books", "Toys", "Grocery", "Beauty"]
values = [45200, 32800, 28500, 21300, 18900, 15600, 12400, 9800]

df = pd.DataFrame({"category": categories, "value": values})
df = df.sort_values("value", ascending=True).reset_index(drop=True)
df["x_pos"] = range(len(df))
df["y_start"] = 0
df["value_label"] = df["value"].apply(lambda v: f"${v:,.0f}")

y_ceiling = max(values) * 1.08

# Plot — stems + dots with interactive tooltips in HTML
plot = (
    ggplot(df)
    + geom_segment(mapping=aes(x="x_pos", xend="x_pos", y="y_start", yend="value"), size=1.5, color=BRAND)
    + geom_point(
        mapping=aes(x="x_pos", y="value"),
        size=10,
        color=BRAND,
        tooltips=layer_tooltips().line("@category").line("Sales|@value_label"),
    )
    + scale_x_continuous(breaks=df["x_pos"].tolist(), labels=df["category"].tolist())
    + scale_y_continuous(limits=[0, y_ceiling])
    + labs(x="Product Category", y="Sales ($)", title="lollipop-basic · python · letsplot · anyplot.ai")
    + ggsize(800, 450)
    + theme_minimal()
    + theme(
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_grid_major_y=element_line(color=RULE, size=0.3),
        panel_grid_minor=element_blank(),
        panel_grid_major_x=element_blank(),
        axis_line=element_line(color=INK_SOFT, size=0.4),
        axis_ticks=element_line(color=INK_SOFT),
        axis_title=element_text(size=12, color=INK),
        axis_text_x=element_text(size=10, color=INK_SOFT, angle=45, hjust=1),
        axis_text_y=element_text(size=10, color=INK_SOFT),
        plot_title=element_text(size=16, color=INK, hjust=0.5),
        plot_margin=[20, 20, 10, 10],
    )
)

ggsave(plot, f"plot-{THEME}.png", path=".", scale=4)
ggsave(plot, f"plot-{THEME}.html", path=".")
