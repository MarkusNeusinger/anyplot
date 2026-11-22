"""anyplot.ai
heatmap-geographic: Geographic Heatmap for Spatial Density
Library: plotnine 0.15.4 | Python 3.13.13
Quality: 87/100 | Updated: 2026-05-19
"""

import os

import numpy as np
import pandas as pd
from plotnine import (
    aes,
    coord_fixed,
    element_blank,
    element_line,
    element_rect,
    element_text,
    geom_polygon,
    geom_tile,
    ggplot,
    labs,
    scale_fill_gradient,
    theme,
    theme_minimal,
)
from scipy.stats import gaussian_kde


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
OCEAN_BG = "#D4E8F7" if THEME == "light" else "#1A2A3A"
CONTINENT_COLOR = "#505050" if THEME == "light" else "#A0A09A"

# Imprint palette: the sequential density ramp runs from position 1 (brand green) to position 3 (blue)
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Constants
BANDWIDTH = 0.08  # KDE bandwidth factor: wide enough to merge a port cluster, narrow enough to keep hubs apart
DENSITY_FLOOR = 0.06  # cells below this share of the peak density stay uncolored so the basemap shows through
GRID_LON = 120  # grid columns across the longitude extent
GRID_LAT = 70  # grid rows across the latitude extent
CONTINENTS = {  # simplified outlines as (lon, lat) vertices, a basemap for orientation
    "N. America": [
        (-170, 60),
        (-168, 65),
        (-140, 70),
        (-125, 55),
        (-124, 48),
        (-117, 33),
        (-105, 25),
        (-97, 26),
        (-82, 25),
        (-77, 35),
        (-68, 45),
        (-55, 48),
        (-52, 45),
        (-80, 27),
        (-87, 30),
        (-97, 20),
        (-105, 22),
        (-125, 50),
        (-145, 60),
        (-165, 55),
    ],
    "S. America": [
        (-80, 10),
        (-68, 12),
        (-60, 5),
        (-50, 0),
        (-35, -5),
        (-40, -22),
        (-50, -35),
        (-55, -52),
        (-68, -55),
        (-72, -18),
        (-75, -5),
        (-80, 0),
        (-82, 8),
    ],
    "Europe": [
        (-10, 35),
        (0, 37),
        (10, 36),
        (20, 35),
        (30, 35),
        (40, 40),
        (50, 45),
        (60, 55),
        (50, 70),
        (35, 70),
        (25, 70),
        (20, 65),
        (10, 60),
        (0, 50),
        (-10, 40),
    ],
    "Africa": [
        (-17, 15),
        (-5, 37),
        (10, 37),
        (35, 32),
        (50, 12),
        (52, 0),
        (43, -25),
        (35, -35),
        (30, -35),
        (15, -25),
        (0, 5),
        (-17, 20),
    ],
    "Asia": [
        (60, 55),
        (80, 70),
        (100, 75),
        (120, 70),
        (140, 55),
        (145, 45),
        (140, 35),
        (130, 30),
        (105, 0),
        (100, 5),
        (80, 10),
        (60, 25),
        (45, 30),
        (30, 35),
        (25, 42),
        (30, 55),
        (35, 70),
        (50, 70),
    ],
    "Australia": [
        (113, -22),
        (125, -15),
        (135, -12),
        (145, -15),
        (152, -25),
        (150, -38),
        (140, -38),
        (130, -33),
        (115, -35),
    ],
}

# Columns: set these to your table's column names
LONGITUDE = "Longitude (°)"  # role: longitude
LATITUDE = "Latitude (°)"  # role: latitude
DENSITY = "Relative density"  # role: extra

# Data: replace this block with your own table, for example df = pd.read_csv("ship_positions.csv")
rng = np.random.default_rng(42)
# Synthetic vessel positions around major shipping hubs: (lon, lat, lon spread, lat spread, count)
hubs = [
    (122, 31, 3, 3, 400),  # Shanghai and the East China Sea
    (104, 2, 5, 2, 350),  # Strait of Malacca and Singapore
    (3, 52, 4, 2, 300),  # North Sea and English Channel
    (33, 28, 3, 5, 250),  # Suez Canal and Red Sea
    (-79, 9, 3, 2, 200),  # Panama Canal approaches
    (-90, 27, 5, 2, 200),  # Gulf of Mexico
    (72, 16, 4, 4, 200),  # Arabian Sea off Mumbai
]
lon_parts = [rng.normal(lon, sx, n) for lon, lat, sx, sy, n in hubs]
lat_parts = [rng.normal(lat, sy, n) for lon, lat, sx, sy, n in hubs]
# Open-ocean transit between hubs
lon_parts.append(rng.uniform(-170, 170, 150))
lat_parts.append(rng.uniform(-50, 60, 150))
df = pd.DataFrame({LONGITUDE: np.concatenate(lon_parts), LATITUDE: np.concatenate(lat_parts)})

# Plot: reads only df and the constants above
lon_grid = np.linspace(-180, 180, GRID_LON)
lat_grid = np.linspace(-60, 80, GRID_LAT)
lon_mesh, lat_mesh = np.meshgrid(lon_grid, lat_grid)

kde = gaussian_kde(df[[LONGITUDE, LATITUDE]].to_numpy().T, bw_method=BANDWIDTH)
density = kde(np.vstack([lon_mesh.ravel(), lat_mesh.ravel()]))
density = density / density.max()

df_heatmap = pd.DataFrame({LONGITUDE: lon_mesh.ravel(), LATITUDE: lat_mesh.ravel(), DENSITY: density})
df_heatmap = df_heatmap[df_heatmap[DENSITY] > DENSITY_FLOOR]

df_continents = pd.DataFrame(
    [(name, i, lon, lat) for name, vertices in CONTINENTS.items() for i, (lon, lat) in enumerate(vertices)],
    columns=["continent", "order", LONGITUDE, LATITUDE],
)

tile_width = lon_grid[1] - lon_grid[0]
tile_height = lat_grid[1] - lat_grid[0]

plot = (
    ggplot()
    + geom_tile(
        aes(x=LONGITUDE, y=LATITUDE, fill=DENSITY),
        data=df_heatmap,
        width=tile_width * 1.02,
        height=tile_height * 1.02,
        alpha=0.85,
    )
    + scale_fill_gradient(low=IMPRINT_PALETTE[0], high=IMPRINT_PALETTE[2], name=DENSITY)
    + geom_polygon(
        aes(x=LONGITUDE, y=LATITUDE, group="continent"),
        data=df_continents,
        fill="none",
        color=CONTINENT_COLOR,
        size=0.4,
    )
    + coord_fixed(ratio=1.0, xlim=(-180, 180), ylim=(-60, 80))
    + labs(title="Global Shipping Traffic · heatmap-geographic · python · plotnine · anyplot.ai")
    + theme_minimal()
    + theme(
        figure_size=(8, 4.5),
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=OCEAN_BG),
        panel_grid_major=element_blank(),
        panel_grid_minor=element_blank(),
        axis_line=element_line(color=INK_SOFT, size=0.3),
        plot_title=element_text(size=11, weight="bold", color=INK),
        axis_title=element_text(size=10, color=INK),
        axis_text=element_text(size=8, color=INK_SOFT),
        legend_title=element_text(size=10, color=INK),
        legend_text=element_text(size=8, color=INK_SOFT),
        legend_background=element_rect(fill=ELEVATED_BG, color="none"),
        legend_key=element_rect(fill=ELEVATED_BG, color="none"),
        legend_position="right",
    )
)

plot.save(f"plot-{THEME}.png", dpi=400, width=8, height=4.5, units="in", verbose=False)
