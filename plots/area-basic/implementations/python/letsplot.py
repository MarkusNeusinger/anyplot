"""anyplot.ai
area-basic: Basic Area Chart
Library: letsplot 4.11.0 | Python 3.14.10
Quality: 81/100 | Updated: 2026-11-26
"""

import os

import numpy as np
import pandas as pd
from lets_plot import *  # noqa: F403, F401
from lets_plot.export import ggsave


LetsPlot.setup_html()  # noqa: F405

# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
GRID = "rgba(26,26,23,0.15)" if THEME == "light" else "rgba(240,239,232,0.15)"  # INK at 15 %

# Imprint palette: single series uses position 1
BRAND = "#009E73"

# Columns: set these to your table's column names
DATE = "Date"  # role: x
VISITORS = "Daily visitors"  # role: y

# Data: replace this block with your own table, for example df = pd.read_csv("visitors.csv")
np.random.seed(42)
days = pd.date_range(start="2024-01-01", periods=30, freq="D")
trend = np.linspace(0, 2000, 30)
weekly_pattern = 1000 * np.sin(np.arange(30) * 2 * np.pi / 7)
noise = np.random.randn(30) * 300
visitors = np.clip(5000 + trend + weekly_pattern + noise, 2000, None).astype(int)
df = pd.DataFrame({DATE: days, VISITORS: visitors})

# Plot: reads only df and the constants above
anyplot_chrome = theme(  # noqa: F405
    plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),  # noqa: F405
    panel_background=element_rect(fill=PAGE_BG, size=0),  # noqa: F405
    panel_grid_major_y=element_line(color=GRID, size=0.3),  # noqa: F405
    panel_grid_major_x=element_blank(),  # noqa: F405
    panel_grid_minor=element_blank(),  # noqa: F405
    axis_title=element_text(color=INK, size=12),  # noqa: F405
    axis_text=element_text(color=INK_SOFT, size=10),  # noqa: F405
    axis_line=element_line(color=INK_SOFT),  # noqa: F405
    plot_title=element_text(color=INK, size=16),  # noqa: F405
    plot_margin=[40, 60, 20, 20],
)

plot = (
    ggplot(df, aes(x=DATE, y=VISITORS))  # noqa: F405
    + geom_area(  # noqa: F405
        fill=BRAND,
        alpha=0.35,
        tooltips=layer_tooltips().line(f"@{{{VISITORS}}} visitors"),  # noqa: F405
    )
    + geom_line(color=BRAND, size=1.0)  # noqa: F405
    + scale_x_datetime(format="%b %d")  # noqa: F405
    + scale_y_continuous(limits=[0, df[VISITORS].max() * 1.06])  # noqa: F405
    + labs(title="area-basic · python · letsplot · anyplot.ai")  # noqa: F405
    + ggsize(800, 450)  # noqa: F405
    + theme_minimal()  # noqa: F405
    + anyplot_chrome
)

ggsave(plot, filename=f"plot-{THEME}.png", path=".", scale=4)
ggsave(plot, filename=f"plot-{THEME}.html", path=".")
