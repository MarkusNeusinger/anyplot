"""anyplot.ai
heatmap-stripes-climate: Climate Warming Stripes
Library: plotnine | Python 3.13
Quality: pending | Updated: 2026-06-02
"""

import os

import numpy as np
import pandas as pd
from plotnine import (
    aes,
    after_stat,
    element_rect,
    element_text,
    geom_tile,
    ggplot,
    guides,
    labs,
    scale_fill_gradientn,
    scale_x_continuous,
    scale_y_continuous,
    theme,
    theme_void,
)


# Theme tokens (see prompts/default-style-guide.md "Theme-adaptive Chrome")
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"

# Data
np.random.seed(42)
years = np.arange(1850, 2025)
n_years = len(years)

base_trend = np.linspace(-0.3, 0.2, n_years)
years_since_1980 = np.maximum(years - 1980, 0).astype(float)
acceleration = years_since_1980**1.6 * 0.0008
noise = np.random.normal(0, 0.08, n_years)
anomaly = base_trend + acceleration + noise
anomaly -= np.mean(anomaly[(years >= 1961) & (years <= 1990)])

df = pd.DataFrame({"year": years, "anomaly": anomaly})

# Plot
vmax = max(abs(anomaly.min()), abs(anomaly.max()))

title = "heatmap-stripes-climate · python · plotnine · anyplot.ai"
n = len(title)
title_size = round(12 * (67 / n)) if n > 67 else 12

plot = (
    ggplot(df, aes(x="year", y=after_stat("1"), fill="anomaly"))
    + geom_tile(aes(width=1, height=1))
    + scale_fill_gradientn(
        colors=["#08306b", "#2171b5", "#6baed6", "#deebf7", "#ffffff", "#fee0d2", "#fc9272", "#de2d26", "#67000d"],
        limits=(-vmax, vmax),
    )
    + scale_x_continuous(expand=(0, 0))
    + scale_y_continuous(expand=(0, 0))
    + guides(fill=False)
    + labs(title=title)
    + theme_void()
    + theme(
        figure_size=(8, 4.5),
        plot_title=element_text(size=title_size, ha="center", weight="bold", color=INK, margin={"b": 10}),
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG),
        plot_margin=0.01,
    )
)

# Save
plot.save(f"plot-{THEME}.png", dpi=400, width=8, height=4.5, units="in", verbose=False)
