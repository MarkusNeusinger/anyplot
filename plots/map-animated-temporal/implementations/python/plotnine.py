""" anyplot.ai
map-animated-temporal: Animated Map over Time
Library: plotnine 0.15.4 | Python 3.13.13
Quality: 88/100 | Updated: 2026-05-27
"""

import os
import sys


_here = os.path.dirname(os.path.abspath(__file__))
sys.path = [p for p in sys.path if os.path.abspath(p or os.getcwd()) != _here]

import numpy as np
import pandas as pd
from plotnine import (
    aes,
    coord_fixed,
    element_line,
    element_rect,
    element_text,
    facet_wrap,
    geom_path,
    geom_point,
    ggplot,
    labs,
    scale_color_gradient,
    theme,
    theme_minimal,
)


THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Data - Simulated earthquake aftershock sequence across California region
np.random.seed(42)

n_timesteps = 6
timestamps = pd.date_range("2024-03-01", periods=n_timesteps, freq="D")

california_coast = pd.DataFrame(
    {
        "lon": [
            -124.4,
            -124.2,
            -123.8,
            -122.4,
            -122.0,
            -121.8,
            -121.5,
            -120.6,
            -120.1,
            -119.5,
            -118.5,
            -117.9,
            -117.2,
            -117.1,
            -117.3,
            -114.6,
            -114.6,
            -117.1,
            -119.0,
            -120.0,
            -121.0,
            -122.4,
            -123.2,
            -124.2,
            -124.4,
        ],
        "lat": [
            40.0,
            41.0,
            41.8,
            42.0,
            41.0,
            39.5,
            38.5,
            37.5,
            36.5,
            35.0,
            34.0,
            33.5,
            33.0,
            32.5,
            32.6,
            32.7,
            34.8,
            34.8,
            36.5,
            38.0,
            39.0,
            40.0,
            41.0,
            41.5,
            40.0,
        ],
    }
)

epicenter_lat, epicenter_lon = 36.0, -118.5
data_rows = []

for i, ts in enumerate(timestamps):
    n_points = int(30 + 20 * np.sin(np.pi * i / (n_timesteps - 1)))
    spread = 0.5 + i * 0.3
    for _ in range(n_points):
        lat = epicenter_lat + np.random.normal(0, spread)
        lon = epicenter_lon + np.random.normal(0, spread * 1.2)
        magnitude = max(1.0, 5.5 - i * 0.3 + np.random.exponential(0.8))
        data_rows.append(
            {
                "lat": lat,
                "lon": lon,
                "timestamp": ts,
                "magnitude": magnitude,
                "day": f"Day {i + 1}: {ts.strftime('%b %d')}",
            }
        )

df = pd.DataFrame(data_rows)

day_order = [f"Day {i + 1}: {ts.strftime('%b %d')}" for i, ts in enumerate(timestamps)]
df["day"] = pd.Categorical(df["day"], categories=day_order, ordered=True)

# Title fontsize scaled for length
title = "Earthquake Aftershocks · map-animated-temporal · python · plotnine · anyplot.ai"
n = len(title)
title_fontsize = max(8, round(12 * 67 / n)) if n > 67 else 12

# Plot
plot = (
    ggplot(df, aes(x="lon", y="lat"))
    + geom_path(data=california_coast, mapping=aes(x="lon", y="lat"), color=INK_MUTED, size=0.6, inherit_aes=False)
    + geom_point(aes(color="magnitude"), size=3.0, alpha=0.75)
    + facet_wrap("~day", ncol=3)
    + scale_color_gradient(low="#009E73", high="#4467A3", name="Magnitude")
    + coord_fixed(ratio=1.0)
    + labs(
        title=title,
        subtitle="Spatial spread of aftershocks over 6 days following M5.5 main event",
        x="Longitude (°)",
        y="Latitude (°)",
    )
    + theme_minimal()
    + theme(
        figure_size=(8, 4.5),
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG),
        panel_grid_major=element_line(color=INK, size=0.3, alpha=0.15),
        panel_grid_minor=element_line(color=INK, size=0.2, alpha=0.05),
        panel_border=element_rect(color=INK_SOFT, fill=None),
        axis_title=element_text(color=INK, size=8),
        axis_text=element_text(color=INK_SOFT, size=6),
        strip_text=element_text(color=INK, size=7, weight="bold"),
        plot_title=element_text(color=INK, size=title_fontsize, weight="bold"),
        plot_subtitle=element_text(color=INK_SOFT, size=7),
        legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT),
        legend_text=element_text(color=INK_SOFT, size=7),
        legend_title=element_text(color=INK, size=8),
    )
)

# Save
plot.save(f"plot-{THEME}.png", dpi=400, width=8, height=4.5, units="in", verbose=False)
