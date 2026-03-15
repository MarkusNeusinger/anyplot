""" pyplots.ai
area-elevation-profile: Terrain Elevation Profile Along Transect
Library: letsplot 4.9.0 | Python 3.14.3
Quality: 83/100 | Created: 2026-03-15
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

# Stagger label offsets to avoid crowding in regions with similar elevations
nudge_offsets = [100, 100, 100, 100, 100, 140, 180, 100]
landmarks_df = pd.DataFrame(
    {
        "distance": landmark_distances,
        "elevation": landmark_elevations,
        "name": landmark_names,
        "nudge_y": [e + n for e, n in zip(landmark_elevations, nudge_offsets, strict=True)],
    }
)

# Compute slope for gradient coloring
slope = np.gradient(elevation, distance)
slope_abs = np.abs(slope)
slope_category = pd.cut(slope_abs, bins=[0, 15, 40, np.inf], labels=["Flat/Gentle", "Moderate", "Steep"])
df["slope_category"] = slope_category

# Vertical lines for landmarks — each as a separate group to avoid connecting them
y_floor = 900
vline_rows = []
for i, (d, e) in enumerate(zip(landmark_distances, landmark_elevations, strict=True)):
    vline_rows.append({"distance": d, "elevation": y_floor, "group": i})
    vline_rows.append({"distance": d, "elevation": e, "group": i})
vline_df = pd.DataFrame(vline_rows)

# Y-axis range
y_min = y_floor
y_max = int(max(elevation) * 1.12)

# Plot
plot = (
    ggplot(df, aes(x="distance", y="elevation"))  # noqa: F405
    # Filled area for terrain silhouette
    + geom_area(fill="#306998", alpha=0.25)  # noqa: F405
    # Profile line colored by slope steepness
    + geom_line(  # noqa: F405
        aes(color="slope_category"),  # noqa: F405
        size=2.0,
        tooltips=layer_tooltips()  # noqa: F405
        .line("Elevation: @elevation m")
        .line("Distance: @distance km"),
    )
    + scale_color_manual(  # noqa: F405
        values=["#306998", "#d4780a", "#c0392b"], name="Slope"
    )
    # Vertical marker lines at landmarks
    + geom_line(  # noqa: F405
        data=vline_df,
        mapping=aes(x="distance", y="elevation", group="group"),  # noqa: F405
        color="#999999",
        size=0.5,
        linetype="dotted",
        inherit_aes=False,
    )
    # Landmark points
    + geom_point(  # noqa: F405
        data=landmarks_df,
        mapping=aes(x="distance", y="elevation"),  # noqa: F405
        size=6,
        color="#306998",
        fill="white",
        shape=21,
        stroke=2.0,
        inherit_aes=False,
    )
    # Landmark labels — positioned at staggered heights to avoid overlap
    + geom_text(  # noqa: F405
        data=landmarks_df,
        mapping=aes(x="distance", y="nudge_y", label="name"),  # noqa: F405
        size=10,
        color="#333333",
        angle=30,
        hjust=0,
        inherit_aes=False,
    )
    # Scales and labels
    + scale_x_continuous(  # noqa: F405
        name="Distance (km)", breaks=list(range(0, 121, 20)), limits=[-2, 135]
    )
    + scale_y_continuous(  # noqa: F405
        name="Elevation (m)", limits=[y_min, y_max]
    )
    + labs(  # noqa: F405
        title="Alpine Trail Elevation Profile · area-elevation-profile · letsplot · pyplots.ai",
        subtitle="120 km hiking transect with 8 landmarks — vertical exaggeration ~10×",
    )
    + ggsize(1600, 900)  # noqa: F405
    + theme_minimal()  # noqa: F405
    + theme(  # noqa: F405
        axis_text=element_text(size=16),  # noqa: F405
        axis_title=element_text(size=20),  # noqa: F405
        plot_title=element_text(size=24),  # noqa: F405
        plot_subtitle=element_text(size=16, color="#555555"),  # noqa: F405
        legend_text=element_text(size=14),  # noqa: F405
        legend_title=element_text(size=16),  # noqa: F405
        legend_position="bottom",
        panel_grid_major_y=element_line(color="#E0E0E0", size=0.3),  # noqa: F405
        panel_grid_major_x=element_blank(),  # noqa: F405
        panel_grid_minor=element_blank(),  # noqa: F405
        plot_margin=[40, 80, 20, 20],
    )
)

# Save
export_ggsave(plot, filename="plot.png", path=".", scale=3)
export_ggsave(plot, filename="plot.html", path=".")
