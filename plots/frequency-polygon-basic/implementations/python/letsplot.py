""" anyplot.ai
frequency-polygon-basic: Frequency Polygon for Distribution Comparison
Library: letsplot 4.9.0 | Python 3.13.13
Quality: 92/100 | Updated: 2026-05-17
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

# Okabe-Ito palette (first series is brand green #009E73)
IMPRINT = ["#009E73", "#C475FD", "#4467A3"]

# Data - Response times (ms) across three experimental conditions
np.random.seed(42)

# Control group: normal distribution centered at 350ms
control = np.random.normal(loc=350, scale=60, size=200)

# Treatment A: slightly faster responses, centered at 300ms
treatment_a = np.random.normal(loc=300, scale=50, size=200)

# Treatment B: bimodal - mix of fast and slow responders
treatment_b = np.concatenate(
    [np.random.normal(loc=280, scale=40, size=120), np.random.normal(loc=420, scale=45, size=80)]
)

# Combine into DataFrame
df = pd.DataFrame(
    {
        "response_time": np.concatenate([control, treatment_a, treatment_b]),
        "condition": (["Control"] * 200 + ["Treatment A"] * 200 + ["Treatment B"] * 200),
    }
)

# Create frequency polygon with theme-adaptive styling
anyplot_theme = theme(
    plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
    panel_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
    panel_grid_major=element_line(color=RULE, size=0.3),
    panel_grid_minor=element_line(color=RULE, size=0.15),
    axis_title=element_text(size=20, color=INK),
    axis_text=element_text(size=16, color=INK_SOFT),
    axis_line=element_line(color=INK_SOFT, size=0.5),
    plot_title=element_text(size=24, color=INK),
    legend_position="right",
    legend_text=element_text(size=16, color=INK_SOFT),
    legend_title=element_text(size=16, color=INK),
)

plot = (
    ggplot(df, aes(x="response_time", color="condition"))
    + geom_freqpoly(bins=25, size=2.5, alpha=0.9)
    + scale_color_manual(values=IMPRINT)
    + labs(
        x="Response Time (ms)",
        y="Frequency",
        title="frequency-polygon-basic · letsplot · anyplot.ai",
        color="Condition",
    )
    + theme_minimal()
    + anyplot_theme
    + ggsize(1600, 900)
)

# Save PNG (scale 3x for 4800 × 2700 px)
ggsave(plot, f"plot-{THEME}.png", path=".", scale=3)

# Save HTML for interactive version
ggsave(plot, f"plot-{THEME}.html", path=".")
