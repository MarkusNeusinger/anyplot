""" anyplot.ai
line-filled: Filled Line Plot
Library: letsplot 4.9.0 | Python 3.13.13
Quality: 90/100 | Updated: 2026-05-12
"""

import os

import numpy as np
import pandas as pd
from lets_plot import *  # noqa: F403
from lets_plot.export import ggsave


LetsPlot.setup_html()  # noqa: F405

# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
BRAND = "#009E73"

# Data - Monthly website traffic over a year
np.random.seed(42)
months = np.arange(1, 13)
base_traffic = 50000 + np.cumsum(np.random.randn(12) * 5000)
seasonal_effect = 10000 * np.sin(np.pi * months / 6)
traffic = base_traffic + seasonal_effect + np.random.randn(12) * 3000
traffic = np.maximum(traffic, 20000)

df = pd.DataFrame({"month": months, "visitors": traffic})

# Create filled line plot
plot = (  # noqa: F405
    ggplot(df, aes(x="month", y="visitors"))  # noqa: F405
    + geom_area(fill=BRAND, alpha=0.4)  # noqa: F405
    + geom_line(color=BRAND, size=2)  # noqa: F405
    + geom_point(color=BRAND, size=5)  # noqa: F405
    + labs(x="Month", y="Website Visitors", title="line-filled · letsplot · anyplot.ai")  # noqa: F405
    + scale_x_continuous(breaks=list(range(1, 13)))  # noqa: F405
    + ggsize(1600, 900)  # noqa: F405
    + theme_minimal()  # noqa: F405
    + theme(  # noqa: F405
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),  # noqa: F405
        panel_background=element_rect(fill=PAGE_BG),  # noqa: F405
        panel_grid_major=element_line(color=INK_SOFT, size=0.3),  # noqa: F405
        panel_grid_minor=element_blank(),  # noqa: F405
        axis_title=element_text(color=INK, size=20),  # noqa: F405
        axis_text=element_text(color=INK_SOFT, size=16),  # noqa: F405
        axis_line=element_line(color=INK_SOFT, size=0.5),  # noqa: F405
        plot_title=element_text(color=INK, size=24),  # noqa: F405
    )
)

# Save PNG and HTML (scale 3x for 4800 × 2700 px)
ggsave(plot, filename=f"plot-{THEME}.png", path=".", scale=3)
ggsave(plot, filename=f"plot-{THEME}.html", path=".")
