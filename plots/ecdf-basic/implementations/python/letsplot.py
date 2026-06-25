"""anyplot.ai
ecdf-basic: Basic ECDF Plot
Library: letsplot 4.10.1 | Python 3.13.14
Quality: 88/100 | Updated: 2026-06-25
"""

import os

import numpy as np
import pandas as pd
from lets_plot import (
    LetsPlot,
    aes,
    element_blank,
    element_line,
    element_rect,
    element_text,
    geom_hline,
    geom_text,
    geom_vline,
    ggplot,
    ggsize,
    labs,
    layer_tooltips,
    scale_y_continuous,
    stat_ecdf,
    theme,
    theme_minimal,
)
from lets_plot.export import ggsave


LetsPlot.setup_html()

# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
GRID = "#D8D7D0" if THEME == "light" else "#3A3A36"
BRAND = "#009E73"
AMBER = "#DDCC77"

# Data — web service response times (ms) with bimodal distribution
np.random.seed(42)
response_times = np.concatenate(
    [np.random.exponential(scale=50, size=150), np.random.normal(loc=200, scale=30, size=50)]
)
df = pd.DataFrame({"response_time": response_times})

# Percentile x-values for storytelling annotations
p25_x = np.percentile(response_times, 25)
p50_x = np.percentile(response_times, 50)
p75_x = np.percentile(response_times, 75)
pct_df = pd.DataFrame(
    {
        "x": [p25_x, p50_x, p75_x],
        "y": [0.25, 0.5, 0.75],
        "label": [f"P25: {p25_x:.0f} ms", f"P50: {p50_x:.0f} ms", f"P75: {p75_x:.0f} ms"],
    }
)
# Inflection annotation data (geom_text instead of annotate)
inflection_df = pd.DataFrame({"x": [45], "y": [0.1], "label": ["Bimodal inflection: ~40 ms"]})

# Title — 3-part format
title = "ecdf-basic · python · letsplot · anyplot.ai"

# Plot — ECDF with percentile reference lines, bimodal inflection marker, and text annotations
plot = (
    ggplot(df, aes(x="response_time"))
    # Background reference lines drawn first so ECDF renders on top
    + geom_hline(yintercept=0.25, color=INK_SOFT, linetype="dashed", size=0.5, alpha=0.5)
    + geom_hline(yintercept=0.5, color=INK_SOFT, linetype="dashed", size=0.5, alpha=0.5)
    + geom_hline(yintercept=0.75, color=INK_SOFT, linetype="dashed", size=0.5, alpha=0.5)
    # Bimodal inflection marker — gap between exponential fast-path and compute cluster
    + geom_vline(xintercept=40, color=AMBER, linetype="dotted", size=0.7, alpha=0.7)
    # Main ECDF step line — drawn on top of reference elements
    + stat_ecdf(
        geom="step", color=BRAND, size=1.5, tooltips=layer_tooltips().line("Response Time: @response_time{,.0f} ms")
    )
    # Percentile x-value labels at each reference line
    + geom_text(data=pct_df, mapping=aes(x="x", y="y", label="label"), color=INK_SOFT, size=3.5, hjust=0, vjust=-0.5)
    # Inflection annotation label
    + geom_text(data=inflection_df, mapping=aes(x="x", y="y", label="label"), color=AMBER, size=3.5, hjust=0)
    + labs(x="Response Time (ms)", y="Cumulative Proportion", title=title)
    + scale_y_continuous(limits=[0, 1], breaks=[0, 0.25, 0.5, 0.75, 1.0])
    + ggsize(800, 450)
    + theme_minimal()
    + theme(
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_border=element_rect(color=GRID, fill=None, size=0.5),
        legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT),
        panel_grid_major=element_line(color=GRID, size=0.5),
        panel_grid_minor=element_blank(),
        axis_line=element_line(color=INK_SOFT, size=0.6),
        axis_ticks=element_line(color=INK_SOFT, size=0.5),
        axis_text=element_text(size=10, color=INK_SOFT, family="monospace"),
        axis_title=element_text(size=12, color=INK),
        plot_title=element_text(size=16, color=INK),
        plot_margin=[10, 10, 10, 10],
    )
)

# Save
ggsave(plot, filename=f"plot-{THEME}.png", path=".", scale=4)
ggsave(plot, filename=f"plot-{THEME}.html", path=".")
