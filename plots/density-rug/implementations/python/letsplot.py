""" anyplot.ai
density-rug: Density Plot with Rug Marks
Library: letsplot 4.9.0 | Python 3.13.13
Quality: 85/100 | Updated: 2026-05-18
"""

import os

import numpy as np
import pandas as pd
from lets_plot import (
    LetsPlot,
    aes,
    element_line,
    element_rect,
    element_text,
    geom_density,
    geom_segment,
    ggplot,
    ggsave,
    ggsize,
    labs,
    theme,
    theme_minimal,
)


LetsPlot.setup_html()

# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
BRAND = "#009E73"  # Okabe-Ito position 1

# Data - Simulated response times (ms) showing bimodal distribution
np.random.seed(42)
fast_responses = np.random.normal(loc=250, scale=40, size=80)
slow_responses = np.random.normal(loc=450, scale=60, size=40)
response_times = np.concatenate([fast_responses, slow_responses])
df = pd.DataFrame({"response_time": response_times})

# Create rug data - small vertical segments at each data point
rug_height = 0.0003
rug_df = pd.DataFrame({"x": response_times, "ymin": 0, "ymax": rug_height})

# Plot
plot = (
    ggplot()
    + geom_density(aes(x="response_time"), data=df, fill=BRAND, color=BRAND, alpha=0.4, size=1.5)
    + geom_segment(aes(x="x", xend="x", y="ymin", yend="ymax"), data=rug_df, color=BRAND, alpha=0.6, size=1.0)
    + labs(x="Response Time (ms)", y="Density", title="density-rug · Python · letsplot · anyplot.ai")
    + ggsize(1600, 900)
    + theme_minimal()
    + theme(
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG),
        panel_grid_major=element_line(color=INK_SOFT, size=0.3),
        panel_grid_minor=element_line(color=INK_SOFT, size=0.2),
        axis_title=element_text(size=20, color=INK),
        axis_text=element_text(size=16, color=INK_SOFT),
        axis_line=element_line(color=INK_SOFT),
        plot_title=element_text(size=24, color=INK),
    )
)

# Save
ggsave(plot, f"plot-{THEME}.png", path=".", scale=3)
ggsave(plot, f"plot-{THEME}.html", path=".")
