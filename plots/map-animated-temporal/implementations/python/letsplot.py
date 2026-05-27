"""anyplot.ai
map-animated-temporal: Animated Map over Time
Library: letsplot | Python 3.13
Quality: pending | Created: 2026-05-27
"""

import os

import numpy as np
import pandas as pd
from lets_plot import (
    LetsPlot,
    aes,
    element_rect,
    element_text,
    facet_wrap,
    geom_point,
    geom_polygon,
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

# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"
MAP_FILL = "#E0DDD5" if THEME == "light" else "#2A2A26"
MAP_BORDER = "#B0ADA5" if THEME == "light" else "#4A4A44"

# Data: earthquake aftershock sequence spreading outward over 6 weeks
np.random.seed(42)

epicenter_lon, epicenter_lat = -119.5, 36.0
events_per_week = [20, 45, 50, 40, 30, 15]

data_rows = []
for week in range(6):
    n_week = events_per_week[week]
    max_radius = 0.5 + week * 0.4
    for _ in range(n_week):
        angle = np.random.uniform(0, 2 * np.pi)
        distance = min(np.random.exponential(max_radius * 0.4), max_radius * 1.5)
        lon = epicenter_lon + distance * np.cos(angle)
        lat = epicenter_lat + distance * np.sin(angle) * 0.8
        magnitude = max(2.0, 4.5 - week * 0.3 + np.random.normal(0, 0.8))
        data_rows.append({"week": week + 1, "lon": lon, "lat": lat, "magnitude": round(magnitude, 1)})

df = pd.DataFrame(data_rows)

# Build cumulative snapshots for 4 key time steps
snapshot_weeks = [1, 2, 4, 6]
df_snapshots = []
for week in snapshot_weeks:
    week_data = df[df["week"] <= week].copy()
    week_data["week_label"] = f"Week {week}"
    df_snapshots.append(week_data)

df_facet = pd.concat(df_snapshots, ignore_index=True)

# Simplified California outline basemap
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

# Title fontsize scaled for longer-than-baseline title
title = "Seismic Activity Spread · map-animated-temporal · python · letsplot · anyplot.ai"
n_chars = len(title)
ratio = 67 / n_chars if n_chars > 67 else 1.0
title_fontsize = max(11, round(16 * ratio))

# Plot using facet_wrap for clean multi-panel layout
plot = (
    ggplot(data=df_facet, mapping=aes(x="lon", y="lat"))
    + geom_polygon(data=df_ca, mapping=aes(x="x", y="y", group="group"), fill=MAP_FILL, color=MAP_BORDER, size=0.5)
    + geom_point(aes(size="magnitude", color="magnitude"), alpha=0.75)
    + scale_color_gradient(low="#009E73", high="#4467A3", name="Magnitude (M)")
    + scale_size(range=[2, 9], name="Magnitude (M)")
    + facet_wrap("week_label", ncol=2)
    + xlim(-122.5, -116.5)
    + ylim(33.5, 38.5)
    + labs(
        x="Longitude",
        y="Latitude",
        title=title,
        caption="Cumulative aftershock sequence radiating from epicenter | Central California region",
    )
    + theme_void()
    + theme(
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG),
        plot_title=element_text(size=title_fontsize, color=INK, face="bold", hjust=0.5),
        plot_caption=element_text(size=9, color=INK_MUTED, hjust=0.5),
        strip_text=element_text(size=13, color=INK, face="bold"),
        legend_text=element_text(size=10, color=INK_SOFT),
        legend_title=element_text(size=11, color=INK),
        legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT),
        legend_position="right",
        axis_title=element_text(size=10, color=INK_SOFT),
        axis_text=element_text(size=8, color=INK_MUTED),
    )
    + ggsize(800, 450)
)

# Save
ggsave(plot, f"plot-{THEME}.png", path=".", scale=4)
ggsave(plot, f"plot-{THEME}.html", path=".")
