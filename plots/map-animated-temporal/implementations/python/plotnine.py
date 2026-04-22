""" pyplots.ai
map-animated-temporal: Animated Map over Time
Library: plotnine 0.15.2 | Python 3.13.11
Quality: 90/100 | Created: 2026-01-20
"""

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
    scale_color_cmap,
    scale_size_continuous,
    theme,
    theme_minimal,
)


# Data - Simulated earthquake aftershock sequence across California region
np.random.seed(42)

# Time steps (6 days of aftershocks for small multiples grid)
n_timesteps = 6
timestamps = pd.date_range("2024-03-01", periods=n_timesteps, freq="D")

# Simplified California coastline coordinates for geographic context
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

# Generate earthquake aftershock data spreading from epicenter
epicenter_lat, epicenter_lon = 36.0, -118.5
data_rows = []

for i, ts in enumerate(timestamps):
    # Number of points increases then decreases (aftershock pattern)
    n_points = int(30 + 20 * np.sin(np.pi * i / (n_timesteps - 1)))
    # Spread increases over time
    spread = 0.5 + i * 0.3

    for _ in range(n_points):
        lat = epicenter_lat + np.random.normal(0, spread)
        lon = epicenter_lon + np.random.normal(0, spread * 1.2)
        # Magnitude decreases over time (aftershocks get weaker)
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

# Order factor for facets
day_order = [f"Day {i + 1}: {ts.strftime('%b %d')}" for i, ts in enumerate(timestamps)]
df["day"] = pd.Categorical(df["day"], categories=day_order, ordered=True)

# Create small multiples visualization with coastline for geographic context
plot = (
    ggplot(df, aes(x="lon", y="lat"))
    + geom_path(data=california_coast, mapping=aes(x="lon", y="lat"), color="#5A5A5A", size=0.8, inherit_aes=False)
    + geom_point(aes(color="magnitude", size="magnitude"), alpha=0.7)
    + facet_wrap("~day", ncol=3)
    + scale_color_cmap(cmap_name="viridis", name="Magnitude")
    + scale_size_continuous(range=(2, 8), name="Magnitude")
    + coord_fixed(ratio=1.0)
    + labs(
        title="Earthquake Aftershock Sequence · map-animated-temporal · plotnine · pyplots.ai",
        subtitle="Small multiples showing spatial spread of aftershocks over 6 days",
        x="Longitude (°)",
        y="Latitude (°)",
    )
    + theme_minimal()
    + theme(
        figure_size=(16, 10),
        plot_title=element_text(size=22, weight="bold"),
        plot_subtitle=element_text(size=16),
        axis_title=element_text(size=16),
        axis_text=element_text(size=12),
        strip_text=element_text(size=14, weight="bold"),
        legend_title=element_text(size=14),
        legend_text=element_text(size=12),
        panel_background=element_rect(fill="#F5F5F0"),
        plot_background=element_rect(fill="white"),
        panel_grid_major=element_line(color="#CCCCCC", size=0.3, alpha=0.4),
        panel_grid_minor=element_line(color="#DDDDDD", size=0.2, alpha=0.3),
    )
)

# Save
plot.save("plot.png", dpi=300, verbose=False)
