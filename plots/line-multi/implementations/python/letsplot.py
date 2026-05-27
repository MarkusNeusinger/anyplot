""" anyplot.ai
line-multi: Multi-Line Comparison Plot
Library: letsplot 4.9.0 | Python 3.13.13
Quality: 85/100 | Updated: 2026-05-06
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

# Okabe-Ito palette
IMPRINT = ["#009E73", "#C475FD", "#4467A3"]

# Data: Monthly sales for 3 product lines over 12 months
np.random.seed(42)
months = np.arange(1, 13)
month_labels = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

# Generate realistic sales data with distinct trends
electronics = 150 + np.cumsum(np.random.randn(12) * 8) + np.linspace(0, 40, 12)
clothing = 120 + np.cumsum(np.random.randn(12) * 6) + np.sin(np.linspace(0, 2 * np.pi, 12)) * 20
home_goods = 90 + np.cumsum(np.random.randn(12) * 5) + np.linspace(0, 25, 12)

# Create long-format DataFrame for ggplot
df = pd.DataFrame(
    {
        "Month": np.tile(months, 3),
        "MonthLabel": np.tile(month_labels, 3),
        "Sales": np.concatenate([electronics, clothing, home_goods]),
        "Product Line": np.repeat(["Electronics", "Clothing", "Home Goods"], 12),
    }
)

# Create separate dataframe for Electronics to create visual hierarchy
electronics_df = df[df["Product Line"] == "Electronics"]
other_df = df[df["Product Line"] != "Electronics"]

# Plot with visual hierarchy: emphasize Electronics (top performer) with smooth trend
plot = (
    ggplot(df, aes(x="Month", y="Sales", color="Product Line"))
    + geom_line(data=other_df, size=2.2, alpha=0.85)
    + geom_point(data=other_df, size=4.5, alpha=0.75)
    + geom_line(data=electronics_df, size=3, alpha=1.0)
    + geom_point(data=electronics_df, size=5.5, alpha=0.95)
    + geom_smooth(data=electronics_df, method="loess", span=0.4, se=False, color=IMPRINT[0], size=1.2, alpha=0.4)
    + scale_color_manual(values=IMPRINT)
    + scale_x_continuous(breaks=months.tolist(), labels=month_labels)
    + labs(title="line-multi · letsplot · anyplot.ai", x="Month", y="Sales (thousands USD)")
    + theme(
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_grid_major=element_blank(),
        panel_grid_minor=element_blank(),
        axis_title=element_text(size=20, color=INK, face="plain"),
        axis_text=element_text(size=16, color=INK_SOFT),
        plot_title=element_text(size=24, color=INK, face="plain"),
        legend_title=element_text(size=16, color=INK),
        legend_text=element_text(size=16, color=INK_SOFT),
        legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT),
        legend_position="right",
        axis_line=element_line(color=INK_SOFT, size=0.5),
    )
    + ggsize(1600, 900)
)

# Save PNG (scale 3x for 4800 × 2700 px)
ggsave(plot, f"plot-{THEME}.png", scale=3, path=".")

# Save HTML for interactivity
ggsave(plot, f"plot-{THEME}.html", path=".")
