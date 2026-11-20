"""anyplot.ai
residual-plot: Residual Plot
Library: plotnine 0.15.4 | Python 3.13.13
Quality: 86/100 | Updated: 2026-05-10
"""

import os

import numpy as np
import pandas as pd
from plotnine import (
    aes,
    element_line,
    element_rect,
    element_text,
    geom_hline,
    geom_point,
    geom_smooth,
    ggplot,
    guide_legend,
    guides,
    labs,
    scale_color_manual,
    theme,
    theme_minimal,
)


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: all eight positions in canonical order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Constants
OUTLIER_SIGMA = 2  # residuals beyond this many standard deviations count as outliers
NORMAL, OUTLIER = "Normal", "Outlier"

# Columns: set these to your table's column names
Y_TRUE = "Observed price ($)"  # role: y_true
Y_PRED = "Fitted price ($)"  # role: y_pred

# Data: replace this block with your own table, for example df = pd.read_csv("predictions.csv")
rng = np.random.default_rng(42)
n_points = 150
house_size = np.linspace(1000, 5000, n_points)  # square feet
price = 150 * house_size + 50000 + rng.normal(0, 30000, n_points)
price[[20, 75, 130]] += np.array([150000, -120000, 100000])  # unusually priced houses
slope, intercept = np.polyfit(house_size, price, 1)  # OLS fit
df = pd.DataFrame({Y_TRUE: price, Y_PRED: slope * house_size + intercept})

# Plot: reads only df and the constants above
RESIDUAL = "Residual ($)"
df[RESIDUAL] = df[Y_TRUE] - df[Y_PRED]
sigma = df[RESIDUAL].std(ddof=0)
POINT_TYPE = "Point type"
df[POINT_TYPE] = np.where(df[RESIDUAL].abs() > OUTLIER_SIGMA * sigma, OUTLIER, NORMAL)

anyplot_theme = theme(
    figure_size=(8, 4.5),
    text=element_text(color=INK_SOFT),
    plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
    panel_background=element_rect(fill=PAGE_BG),
    panel_grid_major=element_line(color=INK, size=0.3, alpha=0.15),
    panel_grid_minor=element_line(color=INK, size=0.2, alpha=0.05),
    panel_border=element_rect(color=INK_SOFT, fill=None),
    axis_title=element_text(color=INK, size=10),
    axis_text=element_text(color=INK_SOFT, size=8),
    axis_line=element_line(color=INK_SOFT),
    plot_title=element_text(color=INK, size=12),
    legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT),
    legend_key=element_rect(fill=ELEVATED_BG, color=ELEVATED_BG),
    legend_text=element_text(color=INK_SOFT, size=8),
    legend_title=element_text(color=INK, size=9),
)

plot = (
    ggplot(df, aes(x=Y_PRED, y=RESIDUAL, color=POINT_TYPE))
    + geom_hline(yintercept=0, color=INK_SOFT, size=0.6, linetype="solid")
    + geom_hline(yintercept=OUTLIER_SIGMA * sigma, color=INK_SOFT, size=0.5, linetype="dashed", alpha=0.7)
    + geom_hline(yintercept=-OUTLIER_SIGMA * sigma, color=INK_SOFT, size=0.5, linetype="dashed", alpha=0.7)
    + geom_point(size=2.5, alpha=0.7)
    + geom_smooth(aes(group=1), method="lowess", color=IMPRINT_PALETTE[2], size=1.0, se=False, span=0.5)
    + scale_color_manual(values=IMPRINT_PALETTE, limits=[NORMAL, OUTLIER])
    + guides(color=guide_legend(override_aes={"alpha": 1}))
    + labs(title="residual-plot · python · plotnine · anyplot.ai")
    + theme_minimal()
    + anyplot_theme
)

# Save
plot.save(f"plot-{THEME}.png", dpi=400, width=8, height=4.5, units="in", verbose=False)
