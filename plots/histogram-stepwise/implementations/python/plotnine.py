""" anyplot.ai
histogram-stepwise: Step Histogram
Library: plotnine 0.15.4 | Python 3.13.13
Quality: 87/100 | Updated: 2026-05-12
"""

import os
import sys


# Remove script directory from path to avoid plotnine.py shadowing the plotnine package
script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path = [p for p in sys.path if os.path.abspath(p) != script_dir and p not in ("", ".")]

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from plotnine import (  # noqa: E402
    aes,
    element_line,
    element_rect,
    element_text,
    geom_step,
    ggplot,
    labs,
    scale_color_manual,
    theme,
)


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Okabe-Ito palette (first series is always #009E73)
IMPRINT = ["#009E73", "#C475FD"]

# Data - Response times (ms) for two server configurations
np.random.seed(42)

# Configuration A: Standard server setup
config_a = np.random.normal(loc=250, scale=60, size=400)

# Configuration B: Optimized server setup (faster, tighter distribution)
config_b = np.random.normal(loc=180, scale=40, size=400)

# Calculate histograms with shared bins for comparison
n_bins = 30
all_data = np.concatenate([config_a, config_b])
bin_edges = np.linspace(all_data.min() - 10, all_data.max() + 10, n_bins + 1)

# Compute histogram counts for each configuration
counts_a, _ = np.histogram(config_a, bins=bin_edges)
counts_b, _ = np.histogram(config_b, bins=bin_edges)

# Create step data: for step histogram, use bin edges for x values
step_x_a = np.repeat(bin_edges, 2)[1:-1]
step_y_a = np.repeat(counts_a, 2)

step_x_b = np.repeat(bin_edges, 2)[1:-1]
step_y_b = np.repeat(counts_b, 2)

# Create DataFrames
df_a = pd.DataFrame({"x": step_x_a, "count": step_y_a, "config": "Standard Setup"})
df_b = pd.DataFrame({"x": step_x_b, "count": step_y_b, "config": "Optimized Setup"})
df = pd.concat([df_a, df_b], ignore_index=True)

# Plot
plot = (
    ggplot(df, aes(x="x", y="count", color="config"))
    + geom_step(size=2, alpha=0.9)
    + labs(
        x="Response Time (ms)", y="Frequency", title="histogram-stepwise · plotnine · anyplot.ai", color="Configuration"
    )
    + scale_color_manual(values=IMPRINT)
    + theme(
        figure_size=(16, 9),
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG),
        panel_grid_major=element_line(color=INK, size=0.3, alpha=0.10),
        panel_grid_minor=element_line(color=INK, size=0.2, alpha=0.05),
        panel_border=element_rect(color=INK_SOFT, fill=None),
        axis_title=element_text(size=20, color=INK),
        axis_text=element_text(size=16, color=INK_SOFT),
        axis_line=element_line(color=INK_SOFT),
        plot_title=element_text(size=24, color=INK),
        legend_position="bottom",
        legend_background=element_rect(fill=PAGE_BG, color=INK_SOFT),
        legend_text=element_text(size=16, color=INK_SOFT),
        legend_title=element_text(size=18, color=INK),
        text=element_text(size=14),
    )
)

# Save in the script's directory
output_dir = os.path.dirname(os.path.abspath(__file__))
plot.save(os.path.join(output_dir, f"plot-{THEME}.png"), dpi=300, verbose=False)
