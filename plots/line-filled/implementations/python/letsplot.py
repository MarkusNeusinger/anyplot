"""anyplot.ai
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

# Imprint palette: first position is the single series
BRAND = "#009E73"

# Columns: set these to your table's column names
MONTH = "Month"  # role: x
VISITORS = "Website Visitors"  # role: y

# Data: replace this block with your own table, for example df = pd.read_csv("traffic.csv")
np.random.seed(42)
months = np.arange(1, 13)
base_traffic = 50000 + np.cumsum(np.random.randn(12) * 5000)
seasonal_effect = 10000 * np.sin(np.pi * months / 6)
traffic = base_traffic + seasonal_effect + np.random.randn(12) * 3000
traffic = np.maximum(traffic, 20000)

df = pd.DataFrame({MONTH: months, VISITORS: traffic})

# Plot: reads only df and the constants above
plot = (  # noqa: F405
    ggplot(df, aes(x=MONTH, y=VISITORS))  # noqa: F405
    + geom_area(fill=BRAND, alpha=0.4)  # noqa: F405
    + geom_line(color=BRAND, size=1.2)  # noqa: F405
    + geom_point(color=BRAND, size=3)  # noqa: F405
    + labs(title="line-filled · python · letsplot · anyplot.ai")  # noqa: F405
    + scale_x_continuous(breaks=sorted(df[MONTH].unique().tolist()))  # noqa: F405
    + scale_y_continuous(limits=[0, df[VISITORS].max() * 1.1], expand=[0, 0])  # noqa: F405
    + ggsize(800, 450)  # noqa: F405
    + theme_minimal()  # noqa: F405
    + theme(  # noqa: F405
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),  # noqa: F405
        panel_background=element_rect(fill=PAGE_BG),  # noqa: F405
        panel_grid_major=element_line(color=INK_SOFT, size=0.3),  # noqa: F405
        panel_grid_minor=element_blank(),  # noqa: F405
        axis_title=element_text(color=INK, size=12),  # noqa: F405
        axis_text=element_text(color=INK_SOFT, size=10),  # noqa: F405
        axis_line=element_line(color=INK_SOFT, size=0.5),  # noqa: F405
        plot_title=element_text(color=INK, size=16),  # noqa: F405
    )
)

# Save PNG (scale 4x = 3200 x 1800 px) and HTML
ggsave(plot, filename=f"plot-{THEME}.png", path=".", scale=4)
ggsave(plot, filename=f"plot-{THEME}.html", path=".")
