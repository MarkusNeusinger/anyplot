"""pyplots.ai
heatmap-stripes-climate: Climate Warming Stripes
Library: letsplot | Python 3.13
Quality: pending | Created: 2026-03-06
"""

import numpy as np
import pandas as pd
from lets_plot import (
    LetsPlot,
    aes,
    element_blank,
    element_rect,
    element_text,
    geom_tile,
    ggplot,
    ggsize,
    guide_colorbar,
    labs,
    scale_fill_gradient2,
    theme,
)
from lets_plot.export import ggsave


LetsPlot.setup_html()

# Data - Synthetic global temperature anomalies (1850-2024) relative to 1961-1990 baseline
np.random.seed(42)
years = np.arange(1850, 2025)
n_years = len(years)

# Simulate realistic warming trend: slow rise, acceleration after ~1970
baseline_trend = np.where(
    years < 1910,
    -0.3 + (years - 1850) * 0.002,
    np.where(years < 1970, -0.15 + (years - 1910) * 0.002, -0.03 + (years - 1970) * 0.018),
)
noise = np.random.normal(0, 0.08, n_years)
anomalies = baseline_trend + noise

# Center around zero (1961-1990 baseline adjustment)
baseline_mask = (years >= 1961) & (years <= 1990)
anomalies = anomalies - anomalies[baseline_mask].mean()

df = pd.DataFrame({"year": years, "anomaly": np.round(anomalies, 3), "row": "temp"})

# Symmetric color range
vmax = max(abs(df["anomaly"].min()), abs(df["anomaly"].max()))

# Plot - warming stripes: pure color, no axes
plot = (
    ggplot(df, aes(x="year", y="row", fill="anomaly"))
    + geom_tile(width=1.0, height=1.0)
    + scale_fill_gradient2(
        low="#08306b",
        mid="#f7f7f7",
        high="#67000d",
        midpoint=0,
        limits=[-vmax, vmax],
        name="",
        guide=guide_colorbar(barwidth=400, barheight=14, nbin=256),
    )
    + labs(title="heatmap-stripes-climate · letsplot · pyplots.ai")
    + theme(
        plot_title=element_text(size=22, color="#333333"),
        panel_background=element_blank(),
        panel_grid=element_blank(),
        axis_title=element_blank(),
        axis_text_x=element_blank(),
        axis_text_y=element_blank(),
        axis_ticks=element_blank(),
        axis_line=element_blank(),
        legend_position="none",
        plot_background=element_rect(fill="#ffffff", color="#ffffff"),
        plot_margin=[30, 10, 10, 10],
    )
    + ggsize(1600, 533)
)

# Save
ggsave(plot, "plot.png", path=".", scale=3)
ggsave(plot, "plot.html", path=".")
