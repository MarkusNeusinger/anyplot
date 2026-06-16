# ruff: noqa: F405
"""anyplot.ai
line-styled: Styled Line Plot
Library: lets-plot | Python 3.13
Quality: pending | Created: 2025-12-30
"""

import os

import numpy as np
import pandas as pd
from lets_plot import *  # noqa: F403, F401


LetsPlot.setup_html()

# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Okabe-Ito palette
IMPRINT = ["#009E73", "#C475FD", "#4467A3", "#BD8233"]

# Data - Daily rainfall across different cities over a month
np.random.seed(42)
days = np.arange(1, 31)

# Realistic rainfall patterns for different cities (mm/day)
paris = 15 + np.cumsum(np.random.randn(30) * 2) / 5
athens = 5 + np.cumsum(np.random.randn(30) * 1) / 5
seattle = 20 + np.cumsum(np.random.randn(30) * 2.5) / 5
delhi = 8 + np.cumsum(np.random.randn(30) * 1.5) / 5

# Create long-format DataFrame for lets-plot
df = pd.DataFrame(
    {
        "Day": np.tile(days, 4),
        "Rainfall": np.concatenate([paris, athens, seattle, delhi]),
        "City": np.repeat(["Paris", "Athens", "Seattle", "Delhi"], 30),
    }
)

# Custom theme for anyplot
anyplot_theme = theme(
    plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
    panel_background=element_rect(fill=PAGE_BG),
    panel_grid_major=element_line(color=INK, size=0.2),
    panel_grid_minor=element_blank(),
    axis_title=element_text(size=20, color=INK),
    axis_text=element_text(size=16, color=INK_SOFT),
    axis_line=element_line(color=INK_SOFT, size=0.5),
    plot_title=element_text(size=24, color=INK),
    legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT),
    legend_text=element_text(size=16, color=INK_SOFT),
    legend_title=element_text(size=16, color=INK),
    legend_position="right",
)

# Create plot with different line styles
plot = (
    ggplot(df, aes(x="Day", y="Rainfall", color="City", linetype="City"))
    + geom_line(size=2)
    + geom_point(size=3.5, alpha=0.7)
    + scale_color_manual(values=IMPRINT)
    + scale_linetype_manual(values=["solid", "dashed", "dotted", "longdash"])
    + labs(
        x="Day of Month", y="Rainfall (mm)", title="line-styled · letsplot · anyplot.ai", color="City", linetype="City"
    )
    + anyplot_theme
    + ggsize(1600, 900)
)

# Save as PNG (scale 3x = 4800 × 2700 px)
ggsave(plot, f"plot-{THEME}.png", path=".", scale=3)

# Save as HTML for interactive viewing
ggsave(plot, f"plot-{THEME}.html", path=".")
