"""anyplot.ai
frequency-polygon-basic: Frequency Polygon for Distribution Comparison
Library: letsplot 4.9.0 | Python 3.13.13
Quality: pending | Updated: 2026-05-17
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
    geom_freqpoly,
    ggplot,
    ggsize,
    labs,
    scale_color_manual,
    theme,
    theme_minimal,
)
from lets_plot.export import ggsave


LetsPlot.setup_html()

# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
RULE = "rgba(26,26,23,0.10)" if THEME == "light" else "rgba(240,239,232,0.10)"

# Imprint palette: all eight positions, one per group in order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Columns: set these to your table's column names
RESPONSE_TIME = "Response time (ms)"  # role: values
CONDITION = "Condition"  # role: group

# Data: replace this block with your own table, for example df = pd.read_csv("response_times.csv")
np.random.seed(42)
control = np.random.normal(loc=350, scale=60, size=200)
treatment_a = np.random.normal(loc=300, scale=50, size=200)
treatment_b = np.concatenate(
    [np.random.normal(loc=280, scale=40, size=120), np.random.normal(loc=420, scale=45, size=80)]
)
df = pd.DataFrame(
    {
        RESPONSE_TIME: np.concatenate([control, treatment_a, treatment_b]),
        CONDITION: ["Control"] * 200 + ["Treatment A"] * 200 + ["Treatment B"] * 200,
    }
)

# Plot: reads only df and the constants above
anyplot_theme = theme(
    plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
    panel_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
    panel_grid_major=element_line(color=RULE, size=0.3),
    panel_grid_minor=element_line(color=RULE, size=0.15),
    axis_title=element_text(size=12, color=INK),
    axis_text=element_text(size=10, color=INK_SOFT),
    axis_line=element_line(color=INK_SOFT, size=0.5),
    plot_title=element_text(size=16, color=INK),
    legend_position="right",
    legend_text=element_text(size=10, color=INK_SOFT),
    legend_title=element_text(size=12, color=INK),
)

plot = (
    ggplot(df, aes(x=RESPONSE_TIME, color=CONDITION))
    + geom_freqpoly(bins=25, size=1.2, alpha=0.9)
    + scale_color_manual(values=IMPRINT_PALETTE)
    + labs(y="Frequency", title="frequency-polygon-basic · python · letsplot · anyplot.ai")
    + theme_minimal()
    + anyplot_theme
    + ggsize(800, 450)
)

# Save PNG (scale 4x for 3200 × 1800 px) and the interactive HTML
ggsave(plot, f"plot-{THEME}.png", path=".", scale=4)
ggsave(plot, f"plot-{THEME}.html", path=".")
