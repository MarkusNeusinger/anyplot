""" anyplot.ai
histogram-density: Density Histogram
Library: letsplot 4.9.0 | Python 3.13.13
Quality: pending | Updated: 2026-05-11
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
    geom_histogram,
    geom_line,
    ggplot,
    ggsave,
    ggsize,
    labs,
    scale_color_manual,
    scale_y_continuous,
    theme,
    theme_minimal,
)
from scipy import stats


LetsPlot.setup_html()

# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
RULE = "rgba(26,26,23,0.15)" if THEME == "light" else "rgba(240,239,232,0.15)"

# Imprint brand green for the single histogram series
BRAND = "#009E73"

# Columns: set these to your table's column names
SCORE = "Test score (points)"  # role: values

# Data: replace this block with your own table, for example df = pd.read_csv("test_scores.csv")
# Exam scores of 400 students: a main group and a smaller group of high performers, capped at 100 points
np.random.seed(42)
scores = np.concatenate([np.random.normal(72, 8, 300), np.random.normal(88, 5, 100)])
df = pd.DataFrame({SCORE: np.clip(scores, 0, 100)})

# Plot: reads only df and the constants above
# Normal distribution fitted to the sample, drawn on the same density scale as the bars
values = df[SCORE].dropna()
mu, sigma = stats.norm.fit(values)
pad = (values.max() - values.min()) * 0.05
grid = np.linspace(values.min() - pad, values.max() + pad, 300)
fit_label = f"Normal fit\nμ = {mu:.1f}, σ = {sigma:.1f}"
fit = pd.DataFrame({SCORE: grid, "density": stats.norm.pdf(grid, mu, sigma), "curve": fit_label})
# One fixed precision for every density tick, enough for a step of a tenth of the curve's peak
decimals = max(0, 1 - int(np.floor(np.log10(fit["density"].max()))))

plot = (
    ggplot(df, aes(x=SCORE))
    + geom_histogram(aes(y="..density.."), bins=25, fill=BRAND, color=PAGE_BG, size=0.3, alpha=0.9)
    + geom_line(aes(y="density", color="curve"), data=fit, size=1.4)
    + scale_color_manual(values=[INK], name="")
    + scale_y_continuous(format=f".{decimals}f")
    + labs(title="histogram-density · python · letsplot · anyplot.ai", x=SCORE, y="Density (per point)")
    + ggsize(800, 450)
    + theme_minimal()
    + theme(
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_border=element_blank(),
        panel_grid_major_x=element_blank(),
        panel_grid_major_y=element_line(color=RULE, size=0.4),
        panel_grid_minor=element_blank(),
        axis_line_x=element_line(color=INK_SOFT, size=0.5),
        axis_ticks=element_blank(),
        plot_title=element_text(size=16, face="bold", color=INK),
        axis_title=element_text(size=12, color=INK),
        axis_text=element_text(size=10, color=INK_SOFT),
        legend_position=[0.98, 0.96],
        legend_justification=[1, 1],
        legend_background=element_rect(fill=ELEVATED_BG, color=RULE),
        legend_key=element_rect(fill=ELEVATED_BG, color=ELEVATED_BG),
        legend_text=element_text(size=10, color=INK_SOFT),
        legend_title=element_blank(),
        plot_margin=[12, 20, 6, 6],
    )
)

# Save
ggsave(plot, f"plot-{THEME}.png", path=".", scale=4)
ggsave(plot, f"plot-{THEME}.html", path=".")
