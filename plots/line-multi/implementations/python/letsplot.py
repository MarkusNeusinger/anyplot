"""anyplot.ai
line-multi: Multi-Line Comparison Plot
Library: letsplot 4.11.0 | Python 3.13.14
Quality: 85/100 | Updated: 2026-08-05
"""

import os

import numpy as np
import pandas as pd
from lets_plot import *


LetsPlot.setup_html()

# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette (first 3 categorical positions)
IMPRINT = ["#009E73", "#C475FD", "#4467A3"]

# Data: monthly sales for 3 product lines over 12 months
np.random.seed(42)
months = np.arange(1, 13)
month_labels = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

# Realistic sales trajectories with distinct shapes
electronics = 150 + np.cumsum(np.random.randn(12) * 8) + np.linspace(0, 40, 12)
clothing = 120 + np.cumsum(np.random.randn(12) * 6) + np.sin(np.linspace(0, 2 * np.pi, 12)) * 20
home_goods = 90 + np.cumsum(np.random.randn(12) * 5) + np.linspace(0, 25, 12)

# Long-format DataFrame for ggplot grammar
df = pd.DataFrame(
    {
        "Month": np.tile(months, 3),
        "MonthLabel": np.tile(month_labels, 3),
        "Sales": np.concatenate([electronics, clothing, home_goods]),
        "Product Line": np.repeat(["Electronics", "Clothing", "Home Goods"], 12),
    }
)

# Split so Electronics (top performer) can be drawn with stronger visual weight
electronics_df = df[df["Product Line"] == "Electronics"]
other_df = df[df["Product Line"] != "Electronics"]

# Distinctive lets-plot feature: interactive per-point tooltips (custom formatting,
# not just a ggplot2 port) surfaced in the saved HTML.
line_tooltips = layer_tooltips().line("^color").line("@MonthLabel|@Sales").format("@Sales", "{,.0f}k USD")

plot = (
    ggplot(df, aes(x="Month", y="Sales", color="Product Line"))
    + geom_line(data=other_df, size=0.9, alpha=0.55, tooltips=line_tooltips)
    + geom_point(data=other_df, size=2.5, alpha=0.55, tooltips=line_tooltips)
    + geom_line(data=electronics_df, size=2.2, alpha=1.0, tooltips=line_tooltips)
    + geom_point(data=electronics_df, size=4.5, alpha=1.0, tooltips=line_tooltips)
    + scale_color_manual(values=IMPRINT, breaks=["Electronics", "Clothing", "Home Goods"])
    + scale_x_continuous(breaks=months.tolist(), labels=month_labels)
    + labs(title="line-multi · python · letsplot · anyplot.ai", x="Month", y="Sales (thousands USD)")
    + theme(
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_grid_major=element_blank(),
        panel_grid_minor=element_blank(),
        axis_title=element_text(size=12, color=INK, face="plain"),
        axis_text=element_text(size=10, color=INK_SOFT),
        plot_title=element_text(size=16, color=INK, face="plain"),
        legend_title=element_text(size=10, color=INK),
        legend_text=element_text(size=10, color=INK_SOFT),
        legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT),
        legend_position="right",
        axis_line=element_line(color=INK_SOFT, size=0.5),
    )
    + ggsize(800, 450)
)

# Save PNG (scale 4x for canonical 3200 x 1800 px)
ggsave(plot, f"plot-{THEME}.png", scale=4, path=".")

# Save HTML for interactivity (custom tooltips)
ggsave(plot, f"plot-{THEME}.html", path=".")
