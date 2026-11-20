"""anyplot.ai
bar-stacked: Stacked Bar Chart
Library: letsplot 4.9.0 | Python 3.13.13
Quality: pending | Updated: 2026-05-09
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

# Imprint palette
IMPRINT = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Column constants
QUARTER = "quarter"  # role: category
PRODUCT = "product"  # role: component
SALES = "sales"  # role: value

# Data: quarterly sales by product category (thousands of dollars)
sales_by_product = {
    "Electronics": [120, 145, 165, 190],
    "Furniture": [85, 92, 78, 110],
    "Clothing": [65, 88, 95, 72],
    "Office Supplies": [45, 52, 48, 58],
}
quarters = ["Q1", "Q2", "Q3", "Q4"]
df = pd.DataFrame(
    [
        {QUARTER: quarter, PRODUCT: product, SALES: values[i]}
        for product, values in sales_by_product.items()
        for i, quarter in enumerate(quarters)
    ]
)

# Plot
plot = (
    ggplot(df, aes(x=QUARTER, y=SALES, fill=PRODUCT))
    + geom_bar(
        stat="identity",
        position="stack",
        width=0.65,
        color=PAGE_BG,
        size=0.3,
        tooltips=layer_tooltips().title(f"@{PRODUCT}").line(f"Sales: @{SALES} K$").format(SALES, ".0f"),
    )
    + scale_fill_manual(values=IMPRINT)
    + labs(title="bar-stacked · python · letsplot · anyplot.ai", x="Quarter", y="Sales (Thousands $)", fill="Product")
    + theme(
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG),
        panel_grid_major_y=element_line(color=RULE, size=0.25),
        panel_grid_major_x=element_blank(),
        panel_grid_minor=element_blank(),
        axis_title=element_text(size=12, color=INK),
        axis_text=element_text(size=10, color=INK_SOFT),
        axis_ticks=element_blank(),
        axis_line=element_line(color=INK_SOFT, size=0.3),
        plot_title=element_text(size=16, color=INK),
        legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT, size=0.3),
        legend_text=element_text(size=10, color=INK_SOFT),
        legend_title=element_text(size=10, color=INK),
        legend_position="right",
    )
    + ggsize(800, 450)
)

# Save
ggsave(plot, f"plot-{THEME}.png", path=".", scale=4)
ggsave(plot, f"plot-{THEME}.html", path=".")
