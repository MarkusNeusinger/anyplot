"""anyplot.ai
histogram-cumulative: Cumulative Histogram
Library: letsplot 4.9.0 | Python 3.13.13
Quality: pending | Updated: 2026-05-11
"""

import os

import numpy as np
import pandas as pd
from lets_plot import *


LetsPlot.setup_html()

# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: first series is always brand green
BRAND = "#009E73"

# Constants
N_BINS = 20  # number of contiguous bins in the cumulative histogram

# Columns: set these to your table's column names
LIFETIME = "Bearing lifetime (hours)"  # role: numeric

# Data: replace this block with your own table, for example df = pd.read_csv("lifetimes.csv")
rng = np.random.default_rng(7)
df = pd.DataFrame({LIFETIME: rng.weibull(2.2, size=320) * 4200})

# Plot: reads only df and the constants above
counts, edges = np.histogram(df[LIFETIME].dropna(), bins=N_BINS)
steps = pd.DataFrame({"xmin": edges[:-1], "xmax": edges[1:], "ymin": 0, "ymax": np.cumsum(counts)})

title = "histogram-cumulative · python · letsplot · anyplot.ai"

plot = (
    ggplot(steps)
    + geom_rect(aes(xmin="xmin", xmax="xmax", ymin="ymin", ymax="ymax"), fill=BRAND, color=PAGE_BG, alpha=0.9, size=0.4)
    + labs(x=LIFETIME, y="Cumulative count (units failed)", title=title)
    + scale_x_continuous(expand=[0.02, 0])
    + scale_y_continuous(expand=[0, 0, 0.05, 0])
    + theme_minimal()
    + theme(
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG),
        panel_grid_major=element_line(color=INK, size=0.2),
        panel_grid_minor=element_blank(),
        axis_title=element_text(size=12, color=INK),
        axis_text=element_text(size=10, color=INK_SOFT),
        axis_line=element_line(color=INK_SOFT),
        plot_title=element_text(size=16, color=INK),
    )
    + ggsize(800, 450)
)

# Save with absolute paths
script_dir = os.path.dirname(os.path.abspath(__file__))
ggsave(plot, os.path.join(script_dir, f"plot-{THEME}.png"), scale=4)
ggsave(plot, os.path.join(script_dir, f"plot-{THEME}.html"))
