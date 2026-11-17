""" anyplot.ai
scatter-color-mapped: Color-Mapped Scatter Plot
Library: letsplot 4.11.0 | Python 3.14.10
Quality: 82/100 | Updated: 2026-11-17
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
    geom_point,
    ggplot,
    ggsave,
    ggsize,
    labs,
    layer_tooltips,
    scale_fill_gradient,
    theme,
    theme_minimal,
)


LetsPlot.setup_html()

# Theme tokens (see prompts/default-style-guide.md "Theme-adaptive Chrome")
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: sequential ramp for the continuous variable (green -> blue)
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]
IMPRINT_SEQ = (IMPRINT_PALETTE[0], IMPRINT_PALETTE[2])

# Columns: set these to your table's column names
X = "X coordinate (m)"  # role: x
Y = "Y coordinate (m)"  # role: y
TEMPERATURE = "Temperature (°C)"  # role: color

# Data: replace this block with your own table, for example df = pd.read_csv("readings.csv")
rng = np.random.default_rng(42)
n_points = 150
n_a = n_points // 3
n_b = n_points // 3
n_c = n_points - n_a - n_b

# Three spatial clusters of sensors
x = np.concatenate([rng.normal(20, 8, n_a), rng.normal(50, 10, n_b), rng.normal(75, 6, n_c)])
y = np.concatenate([rng.normal(30, 10, n_a), rng.normal(60, 12, n_b), rng.normal(40, 8, n_c)])

# Temperature correlated with position, plus sensor noise
temperature = 15 + 0.2 * x + 0.15 * y + rng.normal(0, 3, n_points)

df = pd.DataFrame({X: x, Y: y, TEMPERATURE: temperature})

# Plot: reads only df and the constants above
anyplot_theme = theme(
    plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
    panel_background=element_rect(fill=PAGE_BG),
    panel_grid_major=element_line(color=INK_SOFT, size=0.3),
    panel_grid_minor=element_blank(),
    axis_title=element_text(color=INK, size=12),
    axis_text=element_text(color=INK_SOFT, size=10),
    axis_line=element_line(color=INK_SOFT, size=0.5),
    plot_title=element_text(color=INK, size=16),
    legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT),
    legend_text=element_text(color=INK_SOFT, size=10),
    legend_title=element_text(color=INK, size=12),
)

# Filled circles with a thin outline keep both ends of the ramp visible on either page
plot = (
    ggplot(df, aes(x=X, y=Y, fill=TEMPERATURE))
    + geom_point(
        shape=21,
        size=4,
        stroke=0.6,
        color=INK_SOFT,
        alpha=0.85,
        tooltips=layer_tooltips().line(f"{X}|@{{{X}}}").line(f"{Y}|@{{{Y}}}").line(f"{TEMPERATURE}|@{{{TEMPERATURE}}}"),
    )
    + scale_fill_gradient(low=IMPRINT_SEQ[0], high=IMPRINT_SEQ[1], name=TEMPERATURE)
    + labs(title="scatter-color-mapped · python · letsplot · anyplot.ai")
    + theme_minimal()
    + anyplot_theme
    + ggsize(800, 450)
)

# Save PNG (scale 4x = 3200 x 1800 px) and interactive HTML
ggsave(plot, filename=f"plot-{THEME}.png", path=".", scale=4)
ggsave(plot, filename=f"plot-{THEME}.html", path=".")
