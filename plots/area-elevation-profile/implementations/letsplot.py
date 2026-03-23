""" pyplots.ai
area-elevation-profile: Terrain Elevation Profile Along Transect
Library: letsplot 4.9.0 | Python 3.14.3
Quality: 85/100 | Created: 2026-03-15
"""

import numpy as np
import pandas as pd
from lets_plot import *  # noqa: F403, F401
from lets_plot.export import ggsave as export_ggsave


LetsPlot.setup_html()  # noqa: F405

# Data — Alpine hiking trail elevation profile (120 km)
np.random.seed(42)
n_points = 480
distance = np.linspace(0, 120, n_points)

# Build realistic terrain with multiple overlapping features
base_elevation = 1200
broad_shape = 600 * np.sin(distance * np.pi / 120)
ridge1 = 400 * np.exp(-((distance - 35) ** 2) / 80)
ridge2 = 550 * np.exp(-((distance - 65) ** 2) / 120)
ridge3 = 350 * np.exp(-((distance - 95) ** 2) / 60)
valley = -300 * np.exp(-((distance - 50) ** 2) / 50)
noise = np.cumsum(np.random.randn(n_points) * 3)
elevation = base_elevation + broad_shape + ridge1 + ridge2 + ridge3 + valley + noise
elevation = np.clip(elevation, 800, None)

df = pd.DataFrame({"distance": distance, "elevation": elevation})

# Landmarks along the trail
landmark_names = [
    "Talbach Village",
    "Steinberg Pass",
    "Grünsee Lake",
    "Hochwand Summit",
    "Felsentor Saddle",
    "Alpenhof Hut",
    "Gipfelkreuz Peak",
    "Bergdorf Village",
]
landmark_distances = [0, 20, 38, 50, 65, 80, 95, 120]
landmark_elevations = [float(np.interp(d, distance, elevation)) for d in landmark_distances]

# Stagger label offsets — alternate high/low in crowded 50-100 km region
# Alternating low/high nudge with horizontal shifts to prevent overlap
nudge_y = [80, 250, 80, 250, 80, 250, 80, 80]
nudge_x = [0, -2, 2, -3, 0, 0, 0, 0]
landmarks_df = pd.DataFrame(
    {
        "distance": landmark_distances,
        "elevation": landmark_elevations,
        "name": landmark_names,
        "label_y": [e + n for e, n in zip(landmark_elevations, nudge_y, strict=True)],
        "label_x": [d + n for d, n in zip(landmark_distances, nudge_x, strict=True)],
    }
)

# Compute slope for gradient coloring — smoothed to reduce visual fragmentation
slope = np.gradient(elevation, distance)
slope_abs = np.abs(slope)
# Rolling average to prevent rapid color switching on steep transitions
slope_smooth = pd.Series(slope_abs).rolling(window=25, center=True, min_periods=1).mean()
slope_category = pd.cut(slope_smooth, bins=[0, 15, 40, np.inf], labels=["Flat/Gentle", "Moderate", "Steep"])
df["slope_category"] = slope_category

# Segment data for vertical landmark lines (using geom_segment)
segments_df = pd.DataFrame(
    {"x": landmark_distances, "y": landmark_elevations, "yend": [float(min(elevation)) - 20] * len(landmark_distances)}
)

# Colorblind-safe slope palette: blue, amber, deep purple
slope_colors = ["#306998", "#E69F00", "#882255"]

# Y-axis range — tighten floor to reduce dead space
y_floor = int(min(elevation)) - 30
y_max = int(max(elevation) * 1.15)

# Plot
plot = (
    ggplot(df, aes(x="distance", y="elevation"))  # noqa: F405
    # Filled area for terrain silhouette with gradient-like effect
    + geom_area(fill="#306998", alpha=0.15)  # noqa: F405
    + geom_area(fill="#306998", alpha=0.10)  # noqa: F405
    # Profile line colored by slope steepness
    + geom_line(  # noqa: F405
        aes(color="slope_category"),  # noqa: F405
        size=2.5,
        tooltips=layer_tooltips()  # noqa: F405
        .line("@|@elevation")
        .line("Distance: @distance km")
        .line("Slope: @slope_category"),
    )
    + scale_color_manual(  # noqa: F405
        values=slope_colors, name="Slope Steepness"
    )
    # Vertical marker lines at landmarks using geom_segment
    + geom_segment(  # noqa: F405
        data=segments_df,
        mapping=aes(x="x", y="yend", xend="x", yend="y"),  # noqa: F405
        color="#AAAAAA",
        size=0.6,
        linetype="dashed",
        inherit_aes=False,
    )
    # Landmark points — white filled circles with colored border
    + geom_point(  # noqa: F405
        data=landmarks_df,
        mapping=aes(x="distance", y="elevation"),  # noqa: F405
        size=7,
        color="#306998",
        fill="white",
        shape=21,
        stroke=2.5,
        inherit_aes=False,
        tooltips=layer_tooltips()  # noqa: F405
        .line("@name")
        .line("Elevation: @elevation m")
        .line("Distance: @distance km"),
    )
    # Connector lines from labels to landmark points
    + geom_segment(  # noqa: F405
        data=landmarks_df,
        mapping=aes(x="distance", y="elevation", xend="label_x", yend="label_y"),  # noqa: F405
        color="#BBBBBB",
        size=0.4,
        linetype="dotted",
        inherit_aes=False,
    )
    # Landmark labels — sized to match other text elements, well-staggered
    + geom_text(  # noqa: F405
        data=landmarks_df,
        mapping=aes(x="label_x", y="label_y", label="name"),  # noqa: F405
        size=14,
        color="#2C3E50",
        angle=40,
        hjust=0,
        fontface="bold",
        inherit_aes=False,
    )
    # Scales and labels
    + scale_x_continuous(  # noqa: F405
        name="Distance (km)", breaks=list(range(0, 121, 20)), limits=[-2, 150]
    )
    + scale_y_continuous(  # noqa: F405
        name="Elevation (m)", limits=[y_floor, y_max + 200], breaks=list(range(1000, y_max + 200, 200))
    )
    + labs(  # noqa: F405
        title="Alpine Trail Elevation Profile · area-elevation-profile · letsplot · pyplots.ai",
        subtitle="120 km hiking transect with 8 landmarks — vertical exaggeration ~10×",
    )
    + ggsize(1600, 900)  # noqa: F405
    + theme_minimal()  # noqa: F405
    + theme(  # noqa: F405
        axis_text=element_text(size=16, color="#555555"),  # noqa: F405
        axis_title=element_text(size=20, color="#333333"),  # noqa: F405
        plot_title=element_text(size=24, color="#1A1A2E", face="bold"),  # noqa: F405
        plot_subtitle=element_text(size=16, color="#666666"),  # noqa: F405
        legend_text=element_text(size=14),  # noqa: F405
        legend_title=element_text(size=16, face="bold"),  # noqa: F405
        legend_position="bottom",
        panel_grid_major_y=element_line(color="#E8E8E8", size=0.3),  # noqa: F405
        panel_grid_major_x=element_blank(),  # noqa: F405
        panel_grid_minor=element_blank(),  # noqa: F405
        plot_margin=[40, 80, 20, 20],
        plot_background=element_rect(fill="#FAFAFA", color="#FAFAFA"),  # noqa: F405
        panel_background=element_rect(fill="#FAFAFA", color="#FAFAFA"),  # noqa: F405
    )
)

# Save
export_ggsave(plot, filename="plot.png", path=".", scale=3)
export_ggsave(plot, filename="plot.html", path=".")
