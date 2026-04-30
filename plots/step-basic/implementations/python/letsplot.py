""" anyplot.ai
step-basic: Basic Step Plot
Library: letsplot 4.9.0 | Python 3.13.13
Quality: 88/100 | Updated: 2026-04-30
"""

import os

import numpy as np
import pandas as pd
from lets_plot import (
    LetsPlot,
    aes,
    element_blank,
    element_line,
    element_rect,
    element_text,
    geom_area,
    geom_point,
    geom_step,
    geom_text,
    ggplot,
    ggsave,
    ggsize,
    labs,
    scale_x_continuous,
    theme,
    theme_minimal,
)


LetsPlot.setup_html()

# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
RULE = "rgba(26,26,23,0.10)" if THEME == "light" else "rgba(240,239,232,0.10)"
BRAND = "#009E73"  # Okabe-Ito position 1 — always first series

# Data - Monthly cumulative sales figures (in thousands)
np.random.seed(42)
months = np.arange(1, 13)
monthly_sales = np.array([45, 52, 48, 61, 55, 72, 68, 75, 82, 78, 91, 95])
cumulative_sales = np.cumsum(monthly_sales)

df = pd.DataFrame({"month": months, "cumulative_sales": cumulative_sales})

# Annotation: label the year-end total near the final data point
total = int(cumulative_sales[-1])
label_df = pd.DataFrame({"month": [11.4], "cumulative_sales": [total + 52], "label": [f"Year-end total: ${total}K"]})

# Plot
plot = (
    ggplot(df, aes(x="month", y="cumulative_sales"))
    + geom_area(fill=BRAND, alpha=0.15)
    + geom_step(color=BRAND, size=2, direction="hv")
    + geom_point(color=BRAND, size=6, alpha=0.9)
    + geom_text(
        data=label_df, mapping=aes(x="month", y="cumulative_sales", label="label"), color=INK_SOFT, size=13, hjust=1
    )
    + labs(x="Month", y="Cumulative Sales ($K)", title="step-basic · letsplot · anyplot.ai")
    + scale_x_continuous(breaks=list(range(1, 13)))
    + ggsize(1600, 900)
    + theme_minimal()
    + theme(
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG),
        panel_grid_major_x=element_blank(),
        panel_grid_major_y=element_line(color=RULE, size=0.3),
        panel_grid_minor=element_blank(),
        axis_title=element_text(color=INK, size=20),
        axis_text=element_text(color=INK_SOFT, size=16),
        axis_line=element_line(color=INK_SOFT),
        plot_title=element_text(color=INK, size=24),
    )
)

# Save PNG (scale 3x to get 4800 x 2700 px)
ggsave(plot, f"plot-{THEME}.png", path=".", scale=3)

# Save HTML for interactive version
ggsave(plot, f"plot-{THEME}.html", path=".")
