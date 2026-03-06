""" pyplots.ai
heatmap-stripes-climate: Climate Warming Stripes
Library: plotnine 0.15.3 | Python 3.14.3
Quality: 90/100 | Created: 2026-03-06
"""

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
    + labs(title="heatmap-stripes-climate · plotnine · pyplots.ai")
    + theme_void()
    + theme(
        figure_size=(16, 5),
        plot_title=element_text(size=24, ha="center", margin={"b": 10}),
        plot_background=element_rect(fill="white", color="white"),
        panel_background=element_rect(fill="white", color="white"),
        plot_margin=0.01,
    )
)

# Save
plot.save("plot.png", dpi=300, verbose=False)
