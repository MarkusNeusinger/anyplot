""" pyplots.ai
map-animated-temporal: Animated Map over Time
Library: letsplot 4.8.2 | Python 3.13.11
Quality: 91/100 | Created: 2026-01-20
"""

import numpy as np
import pandas as pd
from lets_plot import (
    LetsPlot,
    aes,
    element_text,
    geom_point,
    geom_polygon,
    gggrid,
    ggplot,
    ggsave,
    ggsize,
    labs,
    scale_color_gradient,
    scale_size,
    theme,
    theme_void,
    xlim,
    ylim,
)


LetsPlot.setup_html()

np.random.seed(42)

# Data: Simulated seismic activity spreading across a region over 6 weeks
# Earthquake aftershock sequence radiating outward from an epicenter

# Epicenter location (central California)
epicenter_lon, epicenter_lat = -119.5, 36.0

# Generate 200 events over 6 weeks with spreading pattern
n_events = 200
weeks = 6
events_per_week = [20, 45, 50, 40, 30, 15]  # Decay pattern typical of aftershocks

data_rows = []
cumulative_events = 0

for week in range(weeks):
    n_week = events_per_week[week]
    # Events spread outward over time (radius increases each week)
    max_radius = 0.5 + week * 0.4  # Degrees, starting small and expanding

    for _ in range(n_week):
        # Random angle and distance from epicenter
        angle = np.random.uniform(0, 2 * np.pi)
        distance = np.random.exponential(max_radius * 0.4)  # Clustered near center
        distance = min(distance, max_radius * 1.5)  # Cap maximum distance

        lon = epicenter_lon + distance * np.cos(angle)
        lat = epicenter_lat + distance * np.sin(angle) * 0.8  # Slightly compressed latitude

        # Magnitude decreases over time on average (main shock first)
        base_mag = 4.5 - week * 0.3
        magnitude = max(2.0, base_mag + np.random.normal(0, 0.8))

        data_rows.append(
            {"week": week + 1, "lon": lon, "lat": lat, "magnitude": round(magnitude, 1), "event_id": cumulative_events}
        )
        cumulative_events += 1

df = pd.DataFrame(data_rows)

# Create cumulative data for each week (show all events up to that point)
df_snapshots = []
for week in range(1, weeks + 1):
    week_data = df[df["week"] <= week].copy()
    week_data["snapshot_week"] = week
    # Mark recent events (current week) differently
    week_data["is_recent"] = week_data["week"] == week
    df_snapshots.append(week_data)

df_all = pd.concat(df_snapshots, ignore_index=True)

# Simplified California outline for basemap
ca_coords = [
    (-124.4, 42.0),
    (-124.2, 40.0),
    (-123.8, 38.5),
    (-122.5, 37.8),
    (-122.4, 37.0),
    (-121.8, 36.5),
    (-121.0, 36.0),
    (-120.5, 35.0),
    (-120.0, 34.5),
    (-119.0, 34.0),
    (-118.5, 34.0),
    (-117.5, 33.0),
    (-117.1, 32.5),
    (-116.0, 32.5),
    (-115.5, 32.8),
    (-114.6, 33.0),
    (-114.5, 34.0),
    (-114.1, 34.3),
    (-114.4, 35.0),
    (-114.6, 36.0),
    (-117.0, 37.0),
    (-118.0, 37.5),
    (-118.5, 38.0),
    (-119.5, 38.5),
    (-120.0, 39.0),
    (-120.0, 39.5),
    (-121.0, 40.0),
    (-122.0, 41.0),
    (-124.0, 41.5),
    (-124.4, 42.0),
]

df_ca = pd.DataFrame(ca_coords, columns=["x", "y"])
df_ca["group"] = 0

# Select 4 key time snapshots (weeks 1, 2, 4, 6)
snapshot_weeks = [1, 2, 4, 6]

# Build individual plots for each snapshot
plots = []
for week in snapshot_weeks:
    week_data = df_all[df_all["snapshot_week"] == week].copy()

    # Count events for subtitle
    n_events_week = len(week_data)

    plot = (
        ggplot()
        # California background
        + geom_polygon(data=df_ca, mapping=aes(x="x", y="y", group="group"), fill="#E8E8E8", color="#AAAAAA", size=0.5)
        # All events up to this week
        + geom_point(
            data=week_data, mapping=aes(x="lon", y="lat", size="magnitude", color="magnitude"), alpha=0.7, stroke=0.3
        )
        # Scales
        + scale_color_gradient(low="#FFD43B", high="#DC2626", name="Magnitude")
        + scale_size(range=[3, 12], name="Magnitude")
        # Labels
        + labs(title=f"Week {week}", subtitle=f"{n_events_week} events")
        # Theme
        + theme_void()
        + theme(
            plot_title=element_text(size=24, face="bold", hjust=0.5),
            plot_subtitle=element_text(size=16, hjust=0.5, color="#666666"),
            legend_position="none",
        )
        # Limits (focus on affected area)
        + xlim(-122.5, -116.5)
        + ylim(33.5, 38.5)
    )
    plots.append(plot)

# Create 2x2 grid with overall title
grid = (
    gggrid(plots, ncol=2)
    + labs(
        title="Seismic Activity Spread · map-animated-temporal · letsplot · pyplots.ai",
        caption="Aftershock sequence spreading from epicenter over 6 weeks | Central California region",
    )
    + theme(
        plot_title=element_text(size=28, face="bold", hjust=0.5),
        plot_caption=element_text(size=14, hjust=0.5, color="#666666"),
    )
    + ggsize(1600, 900)
)

# Save as PNG (scale=3 for 4800x2700 px output)
ggsave(grid, "plot.png", path=".", scale=3)

# Save interactive HTML version
ggsave(grid, "plot.html", path=".")
