""" pyplots.ai
area-basic: Basic Area Chart
Library: plotnine 0.15.3 | Python 3.14.2
Quality: 95/100 | Created: 2025-12-23
"""

import functools

import numpy as np
import pandas as pd
from plotnine import (
    aes,
    annotate,
    element_blank,
    element_line,
    element_rect,
    element_text,
    geom_line,
    geom_ribbon,
    geom_smooth,
    ggplot,
    labs,
    scale_x_datetime,
    scale_y_continuous,
    theme,
    theme_minimal,
)


# Data - daily website visitors over a month
np.random.seed(42)
dates = pd.date_range(start="2024-01-01", periods=31, freq="D")
base_traffic = 4800
trend = np.linspace(0, 2200, 31)
weekly_pattern = 1000 * np.sin(np.arange(31) * 2 * np.pi / 7)
amplitude_growth = np.linspace(1.0, 1.8, 31)
noise = np.random.normal(0, 500, 31) * amplitude_growth
visitors = base_traffic + trend + weekly_pattern * amplitude_growth + noise
# Brief dip mid-month (server maintenance) for richer feature coverage
visitors[14:16] -= np.array([1400, 600])
# Plateau around days 20-23 to show growth stalling briefly
visitors[19:23] = np.mean(visitors[19:23]) * np.ones(4) + np.random.normal(0, 100, 4)
visitors = np.maximum(visitors, 1000)

df = pd.DataFrame({"date": dates, "visitors": visitors})

# Identify key data points for annotations
peak_idx = int(df["visitors"].idxmax())
peak_val = int(df["visitors"].max())
dip_idx = 14
dip_val = int(df.loc[dip_idx, "visitors"])

# Y-axis range: start near data minimum to maximize data region usage
y_min = int(np.floor(df["visitors"].min() / 500) * 500)
y_max = int(np.ceil(df["visitors"].max() / 500) * 500) + 500

# Smooth gradient fill: cumulative geom_ribbon layers create smooth bottom→top gradient
n_layers = 24
max_vis = df["visitors"].max()
gradient_layers = [
    geom_ribbon(
        aes(x="date", ymin="y_lower", ymax="y_upper"),
        data=df.assign(y_lower=y_min, y_upper=np.minimum(visitors, max_vis * (i + 1) / n_layers)),
        fill="#306998",
        alpha=0.03,
    )
    for i in range(n_layers)
]

# Compose gradient layers using functools.reduce
base_plot = ggplot(df, aes(x="date", y="visitors"))
plot = functools.reduce(lambda p, layer: p + layer, gradient_layers, base_plot)

plot = (
    plot
    + geom_line(color="#1e4d6d", size=1.8)
    + geom_smooth(method="lowess", color="#FFD43B", size=2.0, se=False, span=0.5)
    # Peak annotation
    + annotate(
        "text",
        x=dates[peak_idx],
        y=peak_val + 300,
        label=f"Peak: {peak_val:,}",
        size=14,
        color="#1e4d6d",
        fontweight="bold",
        ha="right",
    )
    # Maintenance dip annotation
    + annotate(
        "text",
        x=dates[dip_idx + 1],
        y=dip_val - 200,
        label=f"Maintenance: {dip_val:,}",
        size=11,
        color="#444444",
        fontstyle="italic",
        ha="left",
    )
    # Trend label
    + annotate(
        "text",
        x=dates[25],
        y=df.loc[25, "visitors"] + 500,
        label="Trend (LOWESS)",
        size=11,
        color="#b8930a",
        fontweight="bold",
    )
    + labs(
        x="Date (January 2024)",
        y="Daily Visitors (count)",
        title="area-basic · plotnine · pyplots.ai",
        subtitle="Upward trend with weekly cycles, a mid-month maintenance dip, and a brief plateau",
    )
    + scale_x_datetime(date_labels="%b %d")
    + scale_y_continuous(labels=lambda lst: [f"{int(v):,}" for v in lst], limits=(y_min, y_max))
    + theme_minimal()
    + theme(
        figure_size=(16, 9),
        text=element_text(size=14, color="#2d2d2d"),
        axis_title=element_text(size=20, color="#2d2d2d"),
        axis_text=element_text(size=16, color="#555555"),
        plot_title=element_text(size=24, weight="bold", color="#1a1a1a"),
        plot_subtitle=element_text(size=16, color="#555555", style="italic"),
        panel_background=element_rect(fill="#f8f9fa", color="none"),
        plot_background=element_rect(fill="#ffffff", color="none"),
        panel_grid_major_y=element_line(color="#d0d0d0", size=0.4),
        panel_grid_major_x=element_line(color="#e0e0e0", size=0.3),
        panel_grid_minor=element_blank(),
        axis_line_x=element_line(color="#999999", size=0.6),
        axis_ticks_major_x=element_line(color="#999999", size=0.4),
        axis_ticks_major_y=element_blank(),
        plot_margin=0.04,
    )
)

plot.save("plot.png", dpi=300, verbose=False)
