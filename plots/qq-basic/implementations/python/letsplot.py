""" anyplot.ai
qq-basic: Basic Q-Q Plot
Library: letsplot 4.9.0 | Python 3.14.4
Quality: 81/100 | Updated: 2026-04-27
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
    geom_line,
    geom_point,
    ggplot,
    ggsize,
    labs,
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
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
BRAND = "#009E73"  # Okabe-Ito position 1

# Data - sample with right skew to demonstrate Q-Q plot characteristics
np.random.seed(42)
sample = np.concatenate([np.random.normal(loc=50, scale=10, size=80), np.random.normal(loc=75, scale=5, size=20)])

# Calculate Q-Q plot values using Blom plotting positions
sample_sorted = np.sort(sample)
n = len(sample_sorted)
probabilities = (np.arange(1, n + 1) - 0.375) / (n + 0.25)

# Inverse normal CDF via Abramowitz & Stegun rational approximation
_a = [
    -3.969683028665376e01,
    2.209460984245205e02,
    -2.759285104469687e02,
    1.383577518672690e02,
    -3.066479806614716e01,
    2.506628277459239e00,
]
_b = [-5.447609879822406e01, 1.615858368580409e02, -1.556989798598866e02, 6.680131188771972e01, -1.328068155288572e01]
_c = [
    -7.784894002430293e-03,
    -3.223964580411365e-01,
    -2.400758277161838e00,
    -2.549732539343734e00,
    4.374664141464968e00,
    2.938163982698783e00,
]
_d = [7.784695709041462e-03, 3.224671290700398e-01, 2.445134137142996e00, 3.754408661907416e00]

p_low, p_high = 0.02425, 1 - 0.02425
theoretical_quantiles = np.zeros(n)

mask_low = probabilities < p_low
q = np.sqrt(-2 * np.log(probabilities[mask_low]))
theoretical_quantiles[mask_low] = (((((_c[0] * q + _c[1]) * q + _c[2]) * q + _c[3]) * q + _c[4]) * q + _c[5]) / (
    (((_d[0] * q + _d[1]) * q + _d[2]) * q + _d[3]) * q + 1
)

mask_mid = (probabilities >= p_low) & (probabilities <= p_high)
q = probabilities[mask_mid] - 0.5
r = q * q
theoretical_quantiles[mask_mid] = ((((((_a[0] * r + _a[1]) * r + _a[2]) * r + _a[3]) * r + _a[4]) * r + _a[5]) * q) / (
    ((((_b[0] * r + _b[1]) * r + _b[2]) * r + _b[3]) * r + _b[4]) * r + 1
)

mask_high = probabilities > p_high
q = np.sqrt(-2 * np.log(1 - probabilities[mask_high]))
theoretical_quantiles[mask_high] = -(
    (((((_c[0] * q + _c[1]) * q + _c[2]) * q + _c[3]) * q + _c[4]) * q + _c[5])
    / ((((_d[0] * q + _d[1]) * q + _d[2]) * q + _d[3]) * q + 1)
)

sample_mean = np.mean(sample_sorted)
sample_std = np.std(sample_sorted, ddof=1)
sample_quantiles = (sample_sorted - sample_mean) / sample_std

df = pd.DataFrame({"theoretical": theoretical_quantiles, "sample": sample_quantiles})

# Reference line (y = x)
line_range = (
    max(
        abs(theoretical_quantiles.min()),
        abs(theoretical_quantiles.max()),
        abs(sample_quantiles.min()),
        abs(sample_quantiles.max()),
    )
    * 1.1
)
line_df = pd.DataFrame({"x": [-line_range, line_range], "y": [-line_range, line_range]})

# Plot
anyplot_theme = theme(
    plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
    panel_background=element_rect(fill=PAGE_BG),
    panel_grid_major=element_line(color=INK_SOFT, size=0.3),
    panel_grid_minor=element_line(color=INK_SOFT, size=0.2),
    axis_title=element_text(color=INK, size=20),
    axis_text=element_text(color=INK_SOFT, size=16),
    axis_line=element_line(color=INK_SOFT),
    plot_title=element_text(color=INK, size=24),
    legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT),
)

plot = (
    ggplot()
    + geom_line(data=line_df, mapping=aes(x="x", y="y"), color=INK_SOFT, size=1.5)
    + geom_point(data=df, mapping=aes(x="theoretical", y="sample"), color=BRAND, size=6, alpha=0.75)
    + labs(x="Theoretical Quantiles", y="Sample Quantiles", title="qq-basic · letsplot · anyplot.ai")
    + ggsize(1600, 900)
    + theme_minimal()
    + anyplot_theme
)

# Save PNG (scale 3x to get 4800 × 2700 px)
ggsave(plot, f"plot-{THEME}.png", path=".", scale=3)

# Save HTML
ggsave(plot, f"plot-{THEME}.html", path=".")
