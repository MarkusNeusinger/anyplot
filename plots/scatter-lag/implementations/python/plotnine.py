""" anyplot.ai
scatter-lag: Lag Plot for Time Series Autocorrelation Diagnosis
Library: plotnine 0.15.7 | Python 3.13.14
Quality: 86/100 | Updated: 2026-06-24
"""

import os

import numpy as np
import pandas as pd
from plotnine import (
    aes,
    element_blank,
    element_line,
    element_rect,
    element_text,
    facet_wrap,
    geom_abline,
    geom_point,
    ggplot,
    labs,
    scale_color_gradient,
    theme,
    theme_minimal,
)


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
GRID = "#D8D7D0" if THEME == "light" else "#3A3A36"

# Data — daily temperature readings with AR(1) autocorrelation (phi=0.85)
np.random.seed(42)
n = 300
phi = 0.85
noise = np.random.normal(0, 2.5, n)
temperatures = np.zeros(n)
temperatures[0] = 20 + noise[0]
for i in range(1, n):
    temperatures[i] = (1 - phi) * 20 + phi * temperatures[i - 1] + noise[i]

# Build lag dataframe for lags 1, 3, and 7
lags = [1, 3, 7]
rows = []
for lag in lags:
    for i in range(n - lag):
        rows.append(
            {
                "temp_t": temperatures[i],
                "temp_t_lag": temperatures[i + lag],
                "day": i,
                "lag": f"Lag = {lag} day{'s' if lag > 1 else ''}",
            }
        )
df = pd.DataFrame(rows)
df["lag"] = pd.Categorical(df["lag"], categories=[f"Lag = {k} day{'s' if k > 1 else ''}" for k in lags], ordered=True)

# Plot
plot = (
    ggplot(df, aes(x="temp_t", y="temp_t_lag", color="day"))
    + geom_abline(intercept=0, slope=1, color=INK_SOFT, linetype="dashed", size=0.7)
    + geom_point(size=2.5, alpha=0.55)
    + facet_wrap("lag", ncol=3)
    + scale_color_gradient(low="#009E73", high="#4467A3", name="Day")
    + labs(
        x="Temperature at Day t (°C)",
        y="Temperature at Day t+k (°C)",
        title="scatter-lag · python · plotnine · anyplot.ai",
    )
    + theme_minimal()
    + theme(
        figure_size=(8, 4.5),
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG),
        strip_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT),
        strip_text=element_text(color=INK, size=8, weight="bold"),
        panel_grid_major=element_line(color=GRID, size=0.4),
        panel_grid_minor=element_blank(),
        axis_ticks=element_blank(),
        axis_title=element_text(color=INK, size=10),
        axis_text=element_text(color=INK_SOFT, size=8),
        plot_title=element_text(color=INK, size=12, weight="bold"),
        legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT),
        legend_text=element_text(color=INK_SOFT, size=8),
        legend_title=element_text(color=INK, size=8),
    )
)

# Save
plot.save(f"plot-{THEME}.png", dpi=400, width=8, height=4.5, units="in")
