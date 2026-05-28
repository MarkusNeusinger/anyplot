""" anyplot.ai
line-markers: Line Plot with Markers
Library: letsplot 4.9.0 | Python 3.13.13
Quality: 91/100 | Updated: 2026-05-12
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

# Data - Quarterly product performance metrics
np.random.seed(42)
quarters = np.arange(1, 13)

# Three product lines with different growth patterns
product_a = 45 + np.cumsum(np.random.randn(12) * 3) + np.arange(12) * 2
product_b = 60 + np.cumsum(np.random.randn(12) * 4) + np.arange(12) * 1.5
product_c = 35 + np.cumsum(np.random.randn(12) * 2.5) + np.arange(12) * 2.5

df = pd.DataFrame(
    {
        "Quarter": list(quarters) * 3,
        "Revenue": np.concatenate([product_a, product_b, product_c]),
        "Product": ["Product A"] * 12 + ["Product B"] * 12 + ["Product C"] * 12,
    }
)

# Create plot
plot = (
    ggplot(df, aes(x="Quarter", y="Revenue", color="Product"))
    + geom_line(size=2.5)
    + geom_point(size=6, alpha=0.9)
    + scale_color_manual(values=IMPRINT)
    + scale_x_continuous(breaks=list(range(1, 13)))
    + labs(x="Quarter", y="Revenue (Million USD)", title="line-markers · letsplot · anyplot.ai")
    + theme_minimal()
    + theme(
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG),
        panel_grid_major=element_line(color=INK_SOFT, size=0.3),
        plot_title=element_text(size=24, color=INK, face="bold"),
        axis_title=element_text(size=20, color=INK),
        axis_text=element_text(size=16, color=INK_SOFT),
        axis_line=element_line(color=INK_SOFT, size=0.5),
        legend_background=element_rect(fill=ELEVATED_BG),
        legend_text=element_text(size=16, color=INK_SOFT),
        legend_title=element_text(size=18, color=INK),
        legend_position="right",
    )
    + ggsize(1600, 900)
)

# Save outputs
ggsave(plot, f"plot-{THEME}.png", path=".", scale=3)
ggsave(plot, f"plot-{THEME}.html", path=".")
