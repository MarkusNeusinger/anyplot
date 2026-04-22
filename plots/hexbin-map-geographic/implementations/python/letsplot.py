""" pyplots.ai
hexbin-map-geographic: Hexagonal Binning Map
Library: letsplot 4.8.2 | Python 3.13.11
Quality: 91/100 | Created: 2026-01-20
"""

import numpy as np
import pandas as pd
from lets_plot import (
    LetsPlot,
    aes,
    coord_fixed,
    element_blank,
    element_line,
    element_rect,
    element_text,
    geom_hex,
    geom_polygon,
    ggplot,
    ggsize,
    labs,
    layer_tooltips,
    scale_fill_viridis,
    theme,
    theme_minimal,
)
from lets_plot.export import ggsave


LetsPlot.setup_html()

# Data: Simulated taxi pickup locations in New York City area
# Large dataset to demonstrate hexagonal binning aggregation
np.random.seed(42)
n_points = 15000

# Manhattan cluster (heavy taxi activity)
manhattan_lat = np.random.normal(40.758, 0.025, n_points // 2)
manhattan_lon = np.random.normal(-73.985, 0.015, n_points // 2)

# Midtown East cluster
midtown_lat = np.random.normal(40.752, 0.018, n_points // 4)
midtown_lon = np.random.normal(-73.972, 0.012, n_points // 4)

# JFK Airport area cluster
jfk_lat = np.random.normal(40.641, 0.012, n_points // 6)
jfk_lon = np.random.normal(-73.778, 0.015, n_points // 6)

# LaGuardia Airport area cluster
lga_lat = np.random.normal(40.773, 0.008, n_points // 12)
lga_lon = np.random.normal(-73.872, 0.010, n_points // 12)

# Combine all locations
latitude = np.concatenate([manhattan_lat, midtown_lat, jfk_lat, lga_lat])
longitude = np.concatenate([manhattan_lon, midtown_lon, jfk_lon, lga_lon])

df = pd.DataFrame({"lat": latitude, "lon": longitude})

# Simplified basemap: NYC borough outlines for geographic context
# Manhattan outline (simplified polygon)
manhattan_outline = pd.DataFrame(
    {
        "lon": [-74.02, -73.97, -73.93, -73.91, -73.93, -73.97, -74.01, -74.02],
        "lat": [40.70, 40.71, 40.78, 40.82, 40.88, 40.80, 40.73, 40.70],
        "borough": ["Manhattan"] * 8,
        "order": list(range(8)),
    }
)

# Brooklyn outline (simplified)
brooklyn_outline = pd.DataFrame(
    {
        "lon": [-74.04, -73.95, -73.85, -73.83, -73.86, -73.95, -74.03, -74.04],
        "lat": [40.57, 40.57, 40.58, 40.64, 40.70, 40.70, 40.64, 40.57],
        "borough": ["Brooklyn"] * 8,
        "order": list(range(8)),
    }
)

# Queens outline (simplified)
queens_outline = pd.DataFrame(
    {
        "lon": [-73.96, -73.82, -73.70, -73.72, -73.76, -73.85, -73.93, -73.96],
        "lat": [40.70, 40.60, 40.60, 40.73, 40.80, 40.81, 40.78, 40.70],
        "borough": ["Queens"] * 8,
        "order": list(range(8)),
    }
)

# Combine borough outlines
df_boroughs = pd.concat([manhattan_outline, brooklyn_outline, queens_outline], ignore_index=True)

# Create hexbin map with geographic context
plot = (
    ggplot()
    # Basemap: Borough outlines for geographic context
    + geom_polygon(
        aes(x="lon", y="lat", group="borough"), data=df_boroughs, fill="#E8E8E8", color="#999999", size=0.6, alpha=0.7
    )
    # Hexagonal binning layer - the main visualization
    + geom_hex(
        aes(x="lon", y="lat"), data=df, bins=[40, 40], alpha=0.85, tooltips=layer_tooltips().line("Pickups|@..count..")
    )
    # Sequential colormap for count aggregation
    + scale_fill_viridis(name="Pickup\nCount", option="plasma")
    + labs(x="Longitude", y="Latitude", title="NYC Taxi Pickups · hexbin-map-geographic · letsplot · pyplots.ai")
    + coord_fixed(ratio=1.0, xlim=[-74.05, -73.68], ylim=[40.55, 40.90])
    + ggsize(1600, 900)
    + theme_minimal()
    + theme(
        plot_title=element_text(size=24, face="bold"),
        axis_title=element_text(size=20),
        axis_text=element_text(size=16),
        legend_title=element_text(size=16),
        legend_text=element_text(size=14),
        legend_position="right",
        panel_grid_major=element_line(color="#D0D0D0", size=0.3),
        panel_grid_minor=element_blank(),
        panel_background=element_rect(fill="#F5F5F5"),
    )
)

# Save PNG (scale 3x for 4800 x 2700 px)
ggsave(plot, "plot.png", path=".", scale=3)

# Save HTML for interactive version with tooltips
ggsave(plot, "plot.html", path=".")
