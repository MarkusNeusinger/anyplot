""" pyplots.ai
map-route-path: Route Path Map
Library: letsplot 4.8.2 | Python 3.13.11
Quality: 90/100 | Created: 2026-01-19
"""

import numpy as np
import pandas as pd
from lets_plot import *  # noqa: F403
from lets_plot.export import ggsave as export_ggsave


LetsPlot.setup_html()  # noqa: F405

# Generate a realistic hiking trail route (simulated GPS track)
np.random.seed(42)

# Starting point (approximate coordinates for a scenic trail area)
start_lat, start_lon = 46.85, 9.85  # Near Swiss Alps area

# Generate 150 waypoints for a hiking trail
n_points = 150

# Create a winding path with natural-looking movement
t = np.linspace(0, 4 * np.pi, n_points)

# Path with curves and some elevation-driven meandering
lat_offset = np.cumsum(np.sin(t) * 0.002 + np.random.randn(n_points) * 0.0003)
lon_offset = np.cumsum(np.cos(t * 0.7) * 0.003 + np.random.randn(n_points) * 0.0004)

lat = start_lat + lat_offset
lon = start_lon + lon_offset

# Sequence numbers and timestamps
sequence = np.arange(n_points)
base_time = pd.Timestamp("2026-01-19 08:00:00")
timestamps = [base_time + pd.Timedelta(minutes=i * 2) for i in range(n_points)]

# Create DataFrame
df = pd.DataFrame(
    {
        "lat": lat,
        "lon": lon,
        "sequence": sequence,
        "timestamp": timestamps,
        "progress": sequence / (n_points - 1) * 100,  # 0-100% progress
    }
)

# Start and end points for markers with labels for legend
start_point = df.iloc[[0]].copy()
start_point["marker"] = "Start"
end_point = df.iloc[[-1]].copy()
end_point["marker"] = "End"

# Combine markers for legend
markers_df = pd.concat([start_point, end_point], ignore_index=True)

# Create the plot with path and markers
plot = (
    ggplot()  # noqa: F405
    # Main route path with color gradient showing progress
    + geom_path(  # noqa: F405
        aes(x="lon", y="lat", color="progress"),  # noqa: F405
        data=df,
        size=2.5,
        alpha=0.9,
        tooltips=layer_tooltips()  # noqa: F405
        .line("Progress|@progress%")
        .line("Lat|@lat")
        .line("Lon|@lon")
        .format("@progress", ".1f")
        .format("@lat", ".4f")
        .format("@lon", ".4f"),
    )
    # Start and end markers with fill aesthetic for legend
    + geom_point(  # noqa: F405
        aes(x="lon", y="lat", fill="marker"),  # noqa: F405
        data=markers_df,
        size=8,
        shape=21,
        stroke=2,
        color="white",
        show_legend=True,
        tooltips=layer_tooltips().line("@marker"),  # noqa: F405
    )
    # Color scale for progress (blue to yellow - Python colors)
    + scale_color_gradient(low="#306998", high="#FFD43B", name="Progress (%)")  # noqa: F405
    # Manual fill scale for start/end markers
    + scale_fill_manual(values={"Start": "#22C55E", "End": "#DC2626"}, name="Markers")  # noqa: F405
    # Labels with degree symbols for units
    + labs(x="Longitude (°)", y="Latitude (°)", title="map-route-path · letsplot · pyplots.ai")  # noqa: F405
    # Theme with larger text and subtle grid lines
    + theme_minimal()  # noqa: F405
    + theme(  # noqa: F405
        plot_title=element_text(size=24, face="bold"),  # noqa: F405
        axis_title=element_text(size=20),  # noqa: F405
        axis_text=element_text(size=16),  # noqa: F405
        legend_title=element_text(size=18),  # noqa: F405
        legend_text=element_text(size=14),  # noqa: F405
        legend_position="right",
        panel_grid_major=element_line(color="#CCCCCC", size=0.5),  # noqa: F405
        panel_grid_minor=element_line(color="#E5E5E5", size=0.3),  # noqa: F405
    )
    # Figure size (will be 4800x2700 with scale=3)
    + ggsize(1600, 900)  # noqa: F405
    # Fixed aspect ratio for geographic data
    + coord_fixed(ratio=1.0)  # noqa: F405
)

# Save as PNG (scale 3x for 4800x2700 px)
export_ggsave(plot, filename="plot.png", path=".", scale=3)

# Save interactive HTML version
export_ggsave(plot, filename="plot.html", path=".")
