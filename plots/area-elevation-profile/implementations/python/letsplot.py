"""anyplot.ai
area-elevation-profile: Terrain Elevation Profile Along Transect
Library: letsplot 4.9.0 | Python 3.14.3
Quality: 85/100 | Updated: 2026-06-10
"""

import os

import numpy as np
import pandas as pd
from lets_plot import (  # noqa: F401
    LetsPlot,
    aes,
    element_blank,
    element_line,
    element_rect,
    element_text,
    geom_area,
    geom_line,
    geom_point,
    geom_segment,
    geom_text,
    ggplot,
    ggsave,
    ggsize,
    labs,
    layer_tooltips,
    scale_color_manual,
    scale_x_continuous,
    scale_y_continuous,
    theme,
    theme_minimal,
)


LetsPlot.setup_html()

# Theme tokens (Imprint palette — theme-adaptive chrome)
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Slope steepness colors — semantic exception from Imprint palette:
# green=easy/flat, amber(warning anchor)=moderate, red=steep/strenuous
SLOPE_FLAT = "#009E73"  # Imprint position 1 — green, flat/gentle
SLOPE_MOD = "#DDCC77"  # Imprint amber anchor — warning/caution, moderate slope
SLOPE_STEEP = "#AE3030"  # Imprint position 5 — matte red, steep/strenuous

# Data — Alpine hiking trail elevation profile (120 km)
np.random.seed(42)
n_points = 480
distance = np.linspace(0, 120, n_points)

# Realistic terrain: broad valley shape + ridges + noise
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

# Slope — smoothed rolling average to prevent rapid color switching
slope_smooth = pd.Series(np.abs(np.gradient(elevation, distance))).rolling(window=25, center=True, min_periods=1).mean()
slope_category = pd.cut(slope_smooth, bins=[0, 15, 40, np.inf], labels=["Flat / Gentle", "Moderate", "Steep"])
df["slope_category"] = slope_category

# Landmarks
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

# Two-tier label staggering: alternate high/low rows in the dense 20-65 km region
# Positions 1,3 (Steinberg, Hochwand) go high; 2,4 (Grünsee, Felsentor) go low
# Last label (Bergdorf Village) is right-aligned (hjust=1) so it doesn't overflow
nudge_y = [200, 440, 160, 500, 180, 380, 440, 200]
nudge_x = [-2, -5, 4, -5, 4, 1, 1, 0]
label_hjust = [0, 0, 0, 0, 0, 0, 0, 1]
landmarks_df = pd.DataFrame(
    {
        "distance": landmark_distances,
        "elevation": landmark_elevations,
        "name": landmark_names,
        "label_y": [e + n for e, n in zip(landmark_elevations, nudge_y, strict=True)],
        "label_x": [d + n for d, n in zip(landmark_distances, nudge_x, strict=True)],
        "hjust": label_hjust,
    }
)

# Vertical landmark lines from terrain surface to baseline
y_floor = int(min(elevation)) - 50
y_max = int(max(elevation))

segments_df = pd.DataFrame(
    {"x": landmark_distances, "y": landmark_elevations, "yend": [y_floor] * len(landmark_distances)}
)

# Title scaled for 91-char string: round(16 × 67/91) = 12
title_str = "Alpine Trail Elevation Profile · area-elevation-profile · python · letsplot · anyplot.ai"

# Plot
plot = (
    ggplot(df, aes(x="distance", y="elevation"))
    # Terrain silhouette fill
    + geom_area(fill="#4467A3", alpha=0.12)
    # Profile line colored by slope steepness
    + geom_line(
        aes(color="slope_category"),
        size=1.5,
        tooltips=layer_tooltips()
        .line("Elevation: @elevation m")
        .line("Distance: @distance km")
        .line("Slope: @slope_category"),
    )
    + scale_color_manual(values=[SLOPE_FLAT, SLOPE_MOD, SLOPE_STEEP], name="Slope Steepness")
    # Vertical dashed landmark lines
    + geom_segment(
        data=segments_df,
        mapping=aes(x="x", y="yend", xend="x", yend="y"),
        color=INK_MUTED,
        size=0.5,
        linetype="dashed",
        inherit_aes=False,
    )
    # Landmark points — circle outline with page-background fill
    + geom_point(
        data=landmarks_df,
        mapping=aes(x="distance", y="elevation"),
        size=5,
        color=SLOPE_FLAT,
        fill=PAGE_BG,
        shape=21,
        stroke=2.0,
        inherit_aes=False,
        tooltips=layer_tooltips().line("@name").line("Elevation: @elevation m").line("Distance: @distance km"),
    )
    # Dotted connector lines from labels to points
    + geom_segment(
        data=landmarks_df,
        mapping=aes(x="distance", y="elevation", xend="label_x", yend="label_y"),
        color=INK_MUTED,
        size=0.35,
        linetype="dotted",
        inherit_aes=False,
    )
    # Landmark labels — size 5mm ≈ 14pt, upright; last label right-aligned to avoid overflow
    + geom_text(
        data=landmarks_df,
        mapping=aes(x="label_x", y="label_y", label="name", hjust="hjust"),
        size=5,
        color=INK,
        fontface="bold",
        inherit_aes=False,
    )
    # Axis scales
    + scale_x_continuous(name="Distance (km)", breaks=list(range(0, 121, 20)), limits=[-3, 126])
    + scale_y_continuous(
        name="Elevation (m)", limits=[y_floor, y_max + 600], breaks=list(range(1000, y_max + 600, 200))
    )
    + labs(title=title_str, subtitle="120 km Alpine hiking transect — 8 landmarks — vertical exaggeration ~10×")
    # Canvas — hard rule: ggsize(800, 450) + scale=4 → 3200 × 1800 px
    + ggsize(800, 450)
    + theme_minimal()
    + theme(
        axis_text=element_text(size=10, color=INK_SOFT),
        axis_title=element_text(size=12, color=INK),
        plot_title=element_text(size=12, color=INK, face="bold"),
        plot_subtitle=element_text(size=10, color=INK_SOFT),
        legend_text=element_text(size=10, color=INK_SOFT),
        legend_title=element_text(size=12, color=INK, face="bold"),
        legend_position="bottom",
        panel_grid_major_y=element_line(color=INK, size=0.15),
        panel_grid_major_x=element_blank(),
        panel_grid_minor=element_blank(),
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT),
    )
)

# Save — scale=4 produces 3200 × 1800 px PNG; path="." saves to current directory
ggsave(plot, f"plot-{THEME}.png", path=".", scale=4)
ggsave(plot, f"plot-{THEME}.html", path=".")
