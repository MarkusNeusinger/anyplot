"""anyplot.ai
residual-plot: Residual Plot
Library: letsplot 4.11.0 | Python 3.14.10
Quality: 80/100 | Updated: 2026-11-09
"""
# ruff: noqa: F405

import os

import numpy as np
import pandas as pd
from lets_plot import *  # noqa: F403, F405


LetsPlot.setup_html()

# Theme tokens (read from environment)
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"
RULE = "rgba(26,26,23,0.10)" if THEME == "light" else "rgba(240,239,232,0.10)"

# Imprint palette: position 1 for the bulk of the residuals, semantic matte red for outliers
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]
NORMAL_COLOR = IMPRINT_PALETTE[0]
OUTLIER_COLOR = IMPRINT_PALETTE[4]

# Constants
OUTLIER_SIGMA = 2  # residuals beyond this many standard deviations count as outliers
RESIDUAL = "Residual: sale price − predicted ($k)"
POINT_TYPE = "Point type"
NORMAL_LABEL = "Within ±2σ"
OUTLIER_LABEL = "Outlier (>2σ)"

# Columns: set these to your table's column names
OBSERVED = "Sale price ($k)"  # role: y_true
FITTED = "Predicted sale price ($k)"  # role: y_pred

# Data: replace this block with your own table, for example df = pd.read_csv("predictions.csv")
# House sales: price grows slightly faster than linearly with living area, fitted by a straight line
np.random.seed(42)
n = 150
living_area = np.linspace(40, 220, n)  # m²
noise = np.random.normal(0, 6, n)
sale_price = 60 + 1.2 * living_area + 0.005 * living_area**2 + noise * (0.5 + 0.006 * living_area)
slope, intercept = np.polyfit(living_area, sale_price, 1)
df = pd.DataFrame({OBSERVED: sale_price, FITTED: slope * living_area + intercept})

# Plot: reads only df and the constants above
plot_df = df.dropna(subset=[OBSERVED, FITTED]).copy()
plot_df[RESIDUAL] = plot_df[OBSERVED].astype(float) - plot_df[FITTED].astype(float)
threshold = OUTLIER_SIGMA * plot_df[RESIDUAL].std(ddof=0)
plot_df[POINT_TYPE] = np.where(plot_df[RESIDUAL].abs() > threshold, OUTLIER_LABEL, NORMAL_LABEL)

title = "residual-plot · python · letsplot · anyplot.ai"
title_size = round(16 * (67 / len(title) if len(title) > 67 else 1.0))

plot = (
    ggplot(plot_df, aes(x=FITTED, y=RESIDUAL))
    # Reference line at zero: perfect predictions
    + geom_hline(yintercept=0, color=INK_SOFT, size=0.9)
    # Outlier bands at ±2 standard deviations
    + geom_hline(yintercept=threshold, color=INK_MUTED, size=0.6, linetype="dashed", alpha=0.7)
    + geom_hline(yintercept=-threshold, color=INK_MUTED, size=0.6, linetype="dashed", alpha=0.7)
    + geom_point(aes(color=POINT_TYPE), size=2.8, alpha=0.75)
    # LOESS smoother to reveal curvature left in the residuals
    + geom_smooth(method="loess", color=INK, size=1.1, se=False, span=0.6)
    + scale_color_manual(values={NORMAL_LABEL: NORMAL_COLOR, OUTLIER_LABEL: OUTLIER_COLOR}, name=POINT_TYPE)
    + labs(title=title)
    + theme_minimal()
    + theme(
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_grid_major=element_line(color=RULE, size=0.4),
        panel_grid_minor=element_blank(),
        plot_title=element_text(size=title_size, face="bold", color=INK),
        axis_title=element_text(size=12, color=INK),
        axis_text=element_text(size=10, color=INK_SOFT),
        axis_line=element_line(color=INK_SOFT, size=0.5),
        legend_title=element_text(size=10, color=INK),
        legend_text=element_text(size=10, color=INK_SOFT),
        legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT),
        legend_position="right",
    )
    + ggsize(800, 450)
)

# Save as PNG (3200 × 1800) and HTML with theme-suffixed filenames
ggsave(plot, f"plot-{THEME}.png", path=".", scale=4)
ggsave(plot, f"plot-{THEME}.html", path=".")
