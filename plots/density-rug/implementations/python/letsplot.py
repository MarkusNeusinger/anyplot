"""anyplot.ai
density-rug: Density Plot with Rug Marks
Library: letsplot 4.9.0 | Python 3.13.13
Quality: pending | Updated: 2026-05-18
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
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
BRAND = "#009E73"  # Imprint palette position 1

# Column constants
RESPONSE_TIME = "Response Time (ms)"  # role: values

# Data: replace this block with your own table, for example df = pd.read_csv("response_times.csv")
rng = np.random.default_rng(42)
fast_responses = rng.normal(loc=250, scale=40, size=80)
slow_responses = rng.normal(loc=450, scale=60, size=40)
df = pd.DataFrame({RESPONSE_TIME: np.concatenate([fast_responses, slow_responses])})

# Plot
rug_height = 0.04 / df[RESPONSE_TIME].std()  # short ticks at the foot of the curve, in density units
plot = (
    ggplot(df, aes(x=RESPONSE_TIME))
    + geom_density(fill=BRAND, color=BRAND, alpha=0.4, size=1.2)
    + geom_segment(aes(x=RESPONSE_TIME, xend=RESPONSE_TIME), y=0, yend=rug_height, color=BRAND, alpha=0.6, size=0.8)
    + labs(y="Density", title="density-rug · python · letsplot · anyplot.ai")
    + ggsize(800, 450)
    + theme_minimal()
    + theme(
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG),
        panel_grid_major=element_line(color=INK_SOFT, size=0.3),
        panel_grid_minor=element_line(color=INK_SOFT, size=0.15),
        axis_title=element_text(size=12, color=INK),
        axis_text=element_text(size=10, color=INK_SOFT),
        axis_line=element_line(color=INK_SOFT),
        plot_title=element_text(size=16, color=INK),
    )
)

# Save
ggsave(plot, f"plot-{THEME}.png", path=".", scale=4)
ggsave(plot, f"plot-{THEME}.html", path=".")
