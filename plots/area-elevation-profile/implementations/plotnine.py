""" pyplots.ai
area-elevation-profile: Terrain Elevation Profile Along Transect
Library: plotnine 0.15.3 | Python 3.14.3
Quality: 91/100 | Created: 2026-03-15
"""

import numpy as np
import pandas as pd
from plotnine import (
    aes,
    coord_cartesian,
    element_blank,
    element_line,
    element_rect,
    element_text,
    geom_line,
    geom_point,
    geom_ribbon,
    geom_segment,
    geom_text,
    ggplot,
    labs,
    scale_x_continuous,
    scale_y_continuous,
    theme,
    theme_minimal,
)


# Data - Alpine hiking trail elevation profile (~120 km)
np.random.seed(42)
n_points = 480
distance = np.linspace(0, 120, n_points)

# Build terrain with controlled peaks at landmark locations
elevation = np.full(n_points, 800.0)
# Major peaks
elevation += 500 * np.exp(-((distance - 18) ** 2) / 50)  # Kleine Scheidegg
elevation += 900 * np.exp(-((distance - 35) ** 2) / 80)  # Jungfraujoch (highest)
elevation += 650 * np.exp(-((distance - 62) ** 2) / 60)  # Mürren
elevation += 750 * np.exp(-((distance - 78) ** 2) / 70)  # Schilthorn
elevation += 400 * np.exp(-((distance - 98) ** 2) / 90)  # Kandersteg
# Broad rolling hills
elevation += 200 * np.sin(distance * np.pi / 20 + 0.8)
elevation += 100 * np.sin(distance * np.pi / 10 + 1.5)
# Small terrain noise
elevation += np.random.normal(0, 15, n_points)
# Smooth
elevation = pd.Series(elevation).rolling(window=8, center=True, min_periods=1).mean().values.copy()
# Valley towns at start and end
elevation[:12] = np.linspace(580, elevation[12], 12)
elevation[-12:] = np.linspace(elevation[-12], 620, 12)

# Y-axis — start closer to data minimum to reduce wasted space
y_min = 450
y_max = int(np.ceil(elevation.max() / 100) * 100) + 280

df = pd.DataFrame({"distance": distance, "elevation": elevation, "y_min": y_min})

# Landmarks
landmarks = pd.DataFrame(
    {
        "name": [
            "Grindelwald",
            "Kleine Scheidegg",
            "Jungfraujoch",
            "Lauterbrunnen",
            "Mürren",
            "Schilthorn",
            "Kandersteg",
            "Adelboden",
        ],
        "distance": [0, 18, 35, 50, 62, 78, 98, 120],
    }
)
# Look up elevation for each landmark from the profile data
landmarks["elevation"] = landmarks["distance"].apply(lambda d: elevation[np.argmin(np.abs(distance - d))])
# Label positioning
landmarks["label_y"] = landmarks["elevation"] + 180
landmarks["label"] = landmarks.apply(lambda r: f"{r['name']}\n{int(r['elevation']):,} m", axis=1)
landmarks["ha"] = "center"
landmarks.loc[landmarks["distance"] < 5, "ha"] = "left"
landmarks.loc[landmarks["distance"] > 115, "ha"] = "right"
# Segment endpoint for vertical marker lines
landmarks["seg_top"] = landmarks["elevation"] + 140

# Plot — idiomatic plotnine layer composition with DataFrame-mapped geoms
plot = (
    ggplot(df, aes(x="distance", y="elevation"))
    + geom_ribbon(aes(ymin="y_min", ymax="elevation"), fill="#306998", alpha=0.7)
    + geom_line(color="#1a3d5c", size=1.4)
    # Vertical marker lines from landmark point to label
    + geom_segment(
        aes(x="distance", xend="distance", y="elevation", yend="seg_top"),
        data=landmarks,
        color="#888888",
        linetype="dotted",
        size=0.5,
    )
    # Landmark points
    + geom_point(
        aes(x="distance", y="elevation"), data=landmarks, size=3.5, color="#1a3d5c", fill="#FFD43B", stroke=0.8
    )
    # Landmark labels — left-aligned group (edge, nudged inward)
    + geom_text(
        aes(x="distance", y="label_y", label="label"),
        data=landmarks[landmarks["ha"] == "left"],
        size=7.5,
        color="#2d2d2d",
        ha="left",
        va="bottom",
        fontweight="bold",
        nudge_x=3,
    )
    # Landmark labels — center-aligned group
    + geom_text(
        aes(x="distance", y="label_y", label="label"),
        data=landmarks[landmarks["ha"] == "center"],
        size=7.5,
        color="#2d2d2d",
        ha="center",
        va="bottom",
        fontweight="bold",
    )
    # Landmark labels — right-aligned group (edge, nudged inward)
    + geom_text(
        aes(x="distance", y="label_y", label="label"),
        data=landmarks[landmarks["ha"] == "right"],
        size=7.5,
        color="#2d2d2d",
        ha="right",
        va="bottom",
        fontweight="bold",
        nudge_x=-5,
    )
    # Scales and labels
    + labs(
        x="Distance (km)",
        y="Elevation (m)",
        title="area-elevation-profile · plotnine · pyplots.ai",
        subtitle="Alpine Trail: Grindelwald to Adelboden (120 km) · Vertical exaggeration ~10×",
    )
    + scale_x_continuous(breaks=range(0, 130, 10), expand=(0.03, 2))
    + scale_y_continuous(breaks=range(500, 2200, 250))
    + coord_cartesian(ylim=(y_min, y_max))
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
        panel_grid_major_x=element_blank(),
        panel_grid_minor=element_blank(),
        axis_line_x=element_line(color="#999999", size=0.6),
        axis_ticks_major_x=element_line(color="#999999", size=0.4),
        axis_ticks_major_y=element_blank(),
        plot_margin=0.04,
    )
)

# Save
plot.save("plot.png", dpi=300, verbose=False)
