""" anyplot.ai
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
    labs,
    scale_color_manual,
    theme,
    theme_minimal,
)


# Theme tokens (see prompts/default-style-guide.md)
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
RULE = "rgba(26,26,23,0.10)" if THEME == "light" else "rgba(240,239,232,0.10)"

# Okabe-Ito palette
IMPRINT = [
    "#009E73",  # Brand green (normal points)
    "#C475FD",  # Vermillion (outliers)
    "#4467A3",  # Blue (LOWESS line)
]

# Data - Generate realistic regression data with better labels
np.random.seed(42)
n_points = 150

# House prices regression example
house_size = np.linspace(1000, 5000, n_points)  # Square feet
price_true = 150 * house_size + 50000 + np.random.normal(0, 30000, n_points)

# Add a few outliers (priced unusually high or low for their size)
outlier_indices = [20, 75, 130]
price_true[outlier_indices] += np.array([150000, -120000, 100000])

# Fit linear regression using OLS
size_mean = np.mean(house_size)
price_mean = np.mean(price_true)
slope = np.sum((house_size - size_mean) * (price_true - price_mean)) / np.sum((house_size - size_mean) ** 2)
intercept = price_mean - slope * size_mean
price_pred = slope * house_size + intercept

# Calculate residuals
residuals = price_true - price_pred

# Identify outliers (beyond 2 standard deviations)
std_resid = np.std(residuals)
is_outlier = np.abs(residuals) > 2 * std_resid
point_type = np.where(is_outlier, "Outlier", "Normal")

# Create DataFrame
df = pd.DataFrame({"fitted": price_pred, "residuals": residuals, "point_type": point_type})

# Create theme customization
anyplot_theme = theme(
    plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
    panel_background=element_rect(fill=PAGE_BG),
    panel_grid_major=element_line(color=INK, size=0.3, alpha=0.10),
    panel_grid_minor=element_line(color=INK, size=0.2, alpha=0.05),
    panel_border=element_rect(color=INK_SOFT, fill=None),
    axis_title=element_text(color=INK, size=20),
    axis_text=element_text(color=INK_SOFT, size=16),
    axis_line=element_line(color=INK_SOFT),
    plot_title=element_text(color=INK, size=24),
    legend_background=element_rect(fill=PAGE_BG, color=INK_SOFT),
    legend_text=element_text(color=INK_SOFT, size=16),
    legend_title=element_text(color=INK, size=18),
    figure_size=(16, 9),
)

# Create residual plot
plot = (
    ggplot(df, aes(x="fitted", y="residuals", color="point_type"))
    + geom_hline(yintercept=0, color=INK_SOFT, size=1.2, linetype="solid", alpha=0.8)
    + geom_hline(yintercept=2 * std_resid, color=INK_SOFT, size=0.8, linetype="dashed", alpha=0.5)
    + geom_hline(yintercept=-2 * std_resid, color=INK_SOFT, size=0.8, linetype="dashed", alpha=0.5)
    + geom_point(size=4, alpha=0.7)
    + geom_smooth(aes(group=1), method="lowess", color=IMPRINT[2], size=1.5, se=False, span=0.5)
    + scale_color_manual(values={"Normal": IMPRINT[0], "Outlier": IMPRINT[1]}, name="Point Type")
    + labs(x="Fitted Values ($)", y="Residuals ($)", title="residual-plot · plotnine · anyplot.ai")
    + theme_minimal()
    + anyplot_theme
)

# Save
output_path = os.path.join(os.path.dirname(__file__), f"plot-{THEME}.png")
plot.save(output_path, dpi=300)
