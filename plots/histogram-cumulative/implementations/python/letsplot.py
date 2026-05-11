"""anyplot.ai
histogram-cumulative: Cumulative Histogram
Library: letsplot | Python 3.13
Quality: pending | Created: 2025-12-21
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
BRAND = "#009E73"  # Okabe-Ito position 1

# Data - Response times in milliseconds (realistic API monitoring scenario)
np.random.seed(42)
response_times = np.concatenate(
    [
        np.random.exponential(scale=50, size=400),  # Normal requests
        np.random.exponential(scale=150, size=80),  # Slower requests
        np.random.uniform(300, 500, size=20),  # Occasional slow outliers
    ]
)

# Compute cumulative histogram data
n_bins = 25
counts, bin_edges = np.histogram(response_times, bins=n_bins)
cumulative_counts = np.cumsum(counts)

df = pd.DataFrame({"xmin": bin_edges[:-1], "xmax": bin_edges[1:], "ymin": 0, "ymax": cumulative_counts})

# Plot
plot = (
    ggplot(df)
    + geom_rect(aes(xmin="xmin", xmax="xmax", ymin="ymin", ymax="ymax"), fill=BRAND, color=BRAND, alpha=0.85, size=0.5)
    + labs(x="Response Time (ms)", y="Cumulative Count", title="histogram-cumulative · letsplot · anyplot.ai")
    + scale_x_continuous(expand=[0.02, 0])
    + scale_y_continuous(expand=[0, 0, 0.05, 0])
    + theme_minimal()
    + theme(
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG),
        panel_grid_major=element_line(color=INK, size=0.3),
        panel_grid_minor=element_blank(),
        axis_title=element_text(size=20, color=INK),
        axis_text=element_text(size=16, color=INK_SOFT),
        axis_line=element_line(color=INK_SOFT),
        plot_title=element_text(size=24, color=INK),
    )
    + ggsize(1600, 900)
)

# Save with absolute paths
script_dir = os.path.dirname(os.path.abspath(__file__))
png_path = os.path.join(script_dir, f"plot-{THEME}.png")
html_path = os.path.join(script_dir, f"plot-{THEME}.html")

ggsave(plot, png_path, scale=3)
ggsave(plot, html_path)
