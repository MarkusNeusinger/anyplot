""" anyplot.ai
histogram-overlapping: Overlapping Histograms
Library: letsplot 4.9.0 | Python 3.13.13
Quality: 83/100 | Updated: 2026-05-08
"""

import os
import shutil

import numpy as np
import pandas as pd
from lets_plot import (
    LetsPlot,
    aes,
    element_blank,
    element_line,
    element_rect,
    element_text,
    geom_histogram,
    ggplot,
    ggsave,
    ggsize,
    labs,
    scale_fill_manual,
    theme,
)


LetsPlot.setup_html()

# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
RULE = "rgba(26,26,23,0.10)" if THEME == "light" else "rgba(240,239,232,0.10)"

# Okabe-Ito palette (first series always #009E73)
COLORS = ["#009E73", "#C475FD"]

# Data - comparing response times between two experimental conditions
np.random.seed(42)

# Control group - baseline response times (ms)
control = np.random.normal(loc=450, scale=80, size=200)

# Treatment group - faster response times with intervention
treatment = np.random.normal(loc=380, scale=70, size=200)

# Create DataFrame
df = pd.DataFrame(
    {"response_time": np.concatenate([control, treatment]), "group": ["Control"] * 200 + ["Treatment"] * 200}
)

# Theme-adaptive styling
anyplot_theme = theme(
    plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
    panel_background=element_rect(fill=PAGE_BG),
    panel_grid_major_y=element_line(color=RULE, size=0.3),
    panel_grid_minor_y=element_blank(),
    panel_grid_major_x=element_blank(),
    axis_title=element_text(size=20, color=INK),
    axis_text=element_text(size=16, color=INK_SOFT),
    axis_line=element_line(color=INK_SOFT, size=0.3),
    plot_title=element_text(size=24, color=INK),
    legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT),
    legend_text=element_text(size=16, color=INK_SOFT),
    legend_title=element_text(size=18, color=INK),
    legend_position="top",
)

# Create overlapping histograms
plot = (
    ggplot(df, aes(x="response_time", fill="group"))
    + geom_histogram(alpha=0.5, bins=25, position="identity", color=PAGE_BG, size=0.3)
    + scale_fill_manual(values=COLORS)
    + labs(x="Response Time (ms)", y="Count", title="histogram-overlapping · letsplot · anyplot.ai", fill="Condition")
    + ggsize(1600, 900)
    + anyplot_theme
)

# Save as PNG (scale 3x to get 4800 × 2700 px)
ggsave(plot, filename=f"plot-{THEME}.png", scale=3)

# Save as HTML for interactivity
ggsave(plot, filename=f"plot-{THEME}.html")

# Move files from lets-plot-images subdirectory to current directory
if os.path.exists("lets-plot-images"):
    for file in os.listdir("lets-plot-images"):
        src = os.path.join("lets-plot-images", file)
        if os.path.isfile(src):
            shutil.move(src, file)
    shutil.rmtree("lets-plot-images")
