""" anyplot.ai
histogram-stepwise: Step Histogram
Library: plotnine 0.15.9 | Python 3.14.10
Quality: 81/100 | Updated: 2026-11-21
"""

import os

import numpy as np
import pandas as pd
from plotnine import (
    aes,
    element_line,
    element_rect,
    element_text,
    geom_path,
    ggplot,
    labs,
    scale_color_manual,
    scale_y_continuous,
    theme,
)


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: all eight positions, one per group in order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Constants
N_BINS = 30  # bins shared by every distribution

# Columns: set these to your table's column names, one per distribution
VALUES = ["Standard", "Optimized"]  # role: values
MEASURE = "Response time (ms)"  # role: extra
SETUP = "Server setup"  # role: extra

# Data: replace this block with your own table, for example df = pd.read_csv("response_times.csv")
rng = np.random.default_rng(42)
df = pd.DataFrame({VALUES[0]: rng.normal(250, 60, 400), VALUES[1]: rng.normal(180, 40, 400)})

# Plot: reads only df and the constants above
bin_edges = np.linspace(np.nanmin(df[VALUES].to_numpy()), np.nanmax(df[VALUES].to_numpy()), N_BINS + 1)

# Outline of each histogram: a horizontal segment per bin, vertical segments at the edges
outlines = []
for group in VALUES:
    counts, _ = np.histogram(df[group].dropna(), bins=bin_edges)
    outlines.append(
        pd.DataFrame(
            {MEASURE: np.repeat(bin_edges, 2), "Count": np.concatenate([[0], np.repeat(counts, 2), [0]]), SETUP: group}
        )
    )
steps = pd.concat(outlines, ignore_index=True)

plot = (
    ggplot(steps, aes(x=MEASURE, y="Count", color=SETUP))
    + geom_path(size=1.4, alpha=0.95, lineend="butt", linejoin="mitre")
    + labs(x=MEASURE, y="Count", title="histogram-stepwise · python · plotnine · anyplot.ai", color=SETUP)
    + scale_color_manual(values=IMPRINT_PALETTE, limits=VALUES)
    + scale_y_continuous(limits=(0, None), expand=(0, 0, 0.06, 0))
    + theme(
        figure_size=(8, 4.5),
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG),
        panel_grid_major=element_line(color=INK, size=0.3, alpha=0.15),
        panel_grid_minor=element_line(color=INK, size=0.2, alpha=0.05),
        panel_border=element_rect(color=INK_SOFT, fill=None),
        axis_title=element_text(size=10, color=INK),
        axis_text=element_text(size=8, color=INK_SOFT),
        axis_line=element_line(color=INK_SOFT),
        plot_title=element_text(size=12, color=INK),
        legend_position="right",
        legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT),
        legend_key=element_rect(fill=ELEVATED_BG, color=ELEVATED_BG),
        legend_text=element_text(size=8, color=INK_SOFT),
        legend_title=element_text(size=9, color=INK),
    )
)

plot.save(f"plot-{THEME}.png", dpi=400, width=8, height=4.5, units="in", verbose=False)
