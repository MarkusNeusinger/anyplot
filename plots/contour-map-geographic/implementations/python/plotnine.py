"""anyplot.ai
contour-map-geographic: Contour Lines on Geographic Map
Library: plotnine 0.15.9 | Python 3.14.10
Quality: pending | Updated: 2026-11-26
"""

import os
import sys


# Remove script directory so "import plotnine" resolves to the library, not this file
_sd = os.path.abspath(os.path.dirname(__file__))
sys.path = [p for p in sys.path if os.path.abspath(p) != _sd]

import matplotlib


matplotlib.use("Agg")

import numpy as np
import pandas as pd
from contourpy import contour_generator
from matplotlib.path import Path
from plotnine import (
    aes,
    coord_cartesian,
    element_blank,
    element_line,
    element_rect,
    element_text,
    geom_label,
    geom_path,
    geom_polygon,
    geom_raster,
    ggplot,
    labs,
    scale_fill_gradientn,
    scale_x_continuous,
    scale_y_continuous,
    theme,
)
from scipy.ndimage import gaussian_filter


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
LAND_FILL = "#E6E1D0" if THEME == "light" else "#2D2C27"

# Imprint sequential ramp for filled fields (single-polarity data), per theme
SEQ_FIELDS = (
    [(0.0, "#66E2B2"), (0.369, "#009E73"), (0.803, "#024582"), (1.0, "#351E45")]
    if THEME == "light"
    else [(0.0, "#404C02"), (0.487, "#009E73"), (1.0, "#CDD9FF")]
)

# Constants
CONTOUR_STEP = 0.25  # isohaline interval in psu
LABEL_EVERY = 2  # label every 2nd isohaline (0.5 psu)

# Columns: set these to your table's column names
LON = "Longitude (°E)"  # role: lon
LAT = "Latitude (°N)"  # role: lat
SALINITY = "Salinity (psu)"  # role: value

# Data: replace this block with your own gridded table, for example df = pd.read_csv("salinity.csv")
# Synthetic Mediterranean sea-surface salinity: saltier toward the east, fresher near river-fed basins
lon_vec = np.linspace(-6, 28, 100)
lat_vec = np.linspace(30, 46, 70)
lon_grid, lat_grid = np.meshgrid(lon_vec, lat_vec)

east_ramp = 1 / (1 + np.exp(-(lon_grid - 14) / 8))  # Atlantic inflow to Levantine basin
salinity = 36.3 + 2.7 * east_ramp
salinity -= 0.9 * np.exp(-(((lon_grid - 13.5) / 2.2) ** 2 + ((lat_grid - 44.3) / 1.3) ** 2))  # Po / Adriatic
salinity -= 0.6 * np.exp(-(((lon_grid - 4.5) / 2.0) ** 2 + ((lat_grid - 42.8) / 1.0) ** 2))  # Rhône plume
salinity -= 0.7 * np.exp(-(((lon_grid - 25.0) / 2.0) ** 2 + ((lat_grid - 40.0) / 1.2) ** 2))  # Black Sea outflow
salinity += 0.3 * np.exp(-(((lon_grid - 26) / 4.0) ** 2 + ((lat_grid - 34.5) / 1.8) ** 2))  # Levantine evaporation
salinity = gaussian_filter(salinity, sigma=2)

df = pd.DataFrame({LON: lon_grid.ravel(), LAT: lat_grid.ravel(), SALINITY: salinity.ravel()})

# Plot: reads only df and the constants above
# Simplified land polygons (lon, lat), closed through points outside the map frame
north_shore = [
    (-8, 36.0), (-5.6, 36.0), (-5.4, 36.1), (-4.4, 36.7), (-2.4, 36.8), (-0.9, 37.6), (-0.2, 38.4), (0.2, 38.7),
    (-0.3, 39.5), (0.8, 40.7), (2.2, 41.4), (3.3, 42.3), (3.0, 43.2), (4.5, 43.4), (5.4, 43.3), (6.0, 43.1),
    (7.3, 43.7), (8.9, 44.4), (9.8, 44.1), (10.3, 43.5), (10.5, 42.9), (11.8, 42.1), (12.3, 41.7), (13.5, 41.2),
    (14.3, 40.8), (15.0, 40.5), (15.3, 40.0), (16.1, 39.0), (15.65, 38.0), (16.0, 37.9), (16.5, 38.4),
    (17.1, 38.9), (16.7, 39.7), (17.2, 40.4), (18.0, 40.0), (18.4, 39.8), (18.5, 40.1), (17.9, 40.65),
    (16.9, 41.1), (16.2, 41.95), (15.0, 42.0), (14.2, 42.5), (13.5, 43.6), (12.6, 44.1), (12.5, 44.9),
    (12.3, 45.4), (13.7, 45.6), (13.6, 45.1), (14.4, 45.3), (15.2, 44.1), (16.4, 43.5), (18.1, 42.6),
    (18.7, 42.4), (19.4, 41.3), (19.4, 40.4), (20.0, 39.7), (20.2, 39.3), (20.7, 38.95), (21.2, 38.4),
    (21.8, 38.3), (21.4, 37.8), (21.7, 36.9), (22.5, 36.4), (23.2, 36.45), (22.8, 37.5), (23.0, 37.9),
    (23.6, 37.9), (24.0, 37.65), (24.0, 38.0), (23.6, 38.4), (22.9, 39.3), (22.6, 40.5), (23.8, 40.0),
    (24.3, 40.2), (24.4, 40.9), (25.9, 40.85), (26.2, 40.2), (26.5, 39.3), (27.1, 38.4), (27.3, 37.9),
    (27.4, 37.0), (28.2, 36.8), (30, 36.6), (30, 50), (-8, 50),
]  # fmt: skip
south_shore = [
    (-8, 35.8), (-5.9, 35.8), (-5.3, 35.9), (-4.5, 35.2), (-3.9, 35.2), (-2.9, 35.3), (-2.0, 35.1), (-0.6, 35.8),
    (3.0, 36.8), (5.1, 36.75), (7.8, 36.9), (9.8, 37.3), (10.3, 36.8), (11.0, 37.05), (10.5, 36.4), (10.6, 35.8),
    (10.8, 34.7), (10.1, 33.9), (10.9, 33.7), (13.2, 32.9), (15.1, 32.4), (16.5, 31.2), (18.0, 30.4),
    (20.1, 32.1), (21.5, 32.9), (22.6, 32.8), (24.0, 32.1), (25.2, 31.6), (28, 31.2), (30, 31.2), (30, 20), (-8, 20),
]  # fmt: skip
islands = {
    "sardinia": [(8.2, 40.9), (9.2, 41.25), (9.8, 40.5), (9.6, 39.5), (9.4, 39.0), (8.5, 38.9), (8.4, 39.5), (8.5, 40.4)],
    "corsica": [(8.6, 42.4), (9.4, 43.0), (9.55, 42.2), (9.4, 41.4), (9.0, 41.5), (8.6, 41.9)],
    "sicily": [(12.4, 38.1), (13.4, 38.2), (15.6, 38.3), (15.1, 37.3), (15.2, 36.7), (14.3, 36.8), (13.0, 37.5)],
    "mallorca": [(2.4, 39.5), (3.2, 39.9), (3.4, 39.7), (3.0, 39.3), (2.6, 39.3)],
    "crete": [(23.5, 35.5), (24.5, 35.4), (25.7, 35.3), (26.3, 35.3), (26.1, 35.0), (25.0, 34.95), (24.0, 35.2)],
}  # fmt: skip
land = {"north": north_shore, "south": south_shore, **islands}
df_land = pd.DataFrame([{"lon": x, "lat": y, "group": name} for name, pts in land.items() for x, y in pts])

# Grid cells inside a land polygon carry no salinity: mask them for the isohalines
points = df[[LON, LAT]].to_numpy()
on_land = np.zeros(len(df), dtype=bool)
for pts in land.values():
    on_land |= Path(pts).contains_points(points)

# Isohalines with contourpy (path computation only), over a masked grid
lons = np.sort(df[LON].unique())
lats = np.sort(df[LAT].unique())
field = np.ma.masked_array(
    df[SALINITY].to_numpy().reshape(len(lats), len(lons)), mask=on_land.reshape(len(lats), len(lons))
)
levels = np.arange(np.ceil(field.min() / CONTOUR_STEP), np.floor(field.max() / CONTOUR_STEP) + 1) * CONTOUR_STEP
gen = contour_generator(x=lons, y=lats, z=field)

iso_rows, label_rows = [], []
for i, level in enumerate(levels):
    segs = gen.lines(level)
    if not segs:
        continue
    if i % LABEL_EVERY == 0:
        longest = max(segs, key=len)
        # prefer the point nearest the middle whose label box (about 1.8 x 1 degrees) stays clear of land
        order = np.argsort(np.abs(np.arange(len(longest)) - len(longest) // 2))
        box = np.array([(dx, dy) for dx in (-0.9, 0, 0.9) for dy in (-0.5, 0, 0.5)])
        mid = next(
            (
                longest[j]
                for j in order
                if not any(Path(pts).contains_points(longest[j] + box).any() for pts in land.values())
            ),
            longest[len(longest) // 2],
        )
        label_rows.append({"lon": mid[0], "lat": mid[1], "label": f"{level:.1f}"})
    for seg_idx, seg in enumerate(segs):
        iso_rows += [{"lon": x, "lat": y, "group": f"iso_{level:.2f}_{seg_idx}"} for x, y in seg]
df_iso = pd.DataFrame(iso_rows)
df_labels = pd.DataFrame(label_rows)

lon_breaks = list(range(0, int(df[LON].max()) + 1, 5))
lon_labels = [f"{x}°E" if x > 0 else "0°" for x in lon_breaks]
lat_breaks = list(range(30, int(df[LAT].max()) + 1, 5))
lat_labels = [f"{y}°N" for y in lat_breaks]

title = "contour-map-geographic · python · plotnine · anyplot.ai"

anyplot_theme = theme(
    figure_size=(8, 4.5),
    plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
    panel_background=element_rect(fill=PAGE_BG),
    panel_grid_major=element_blank(),
    panel_grid_minor=element_blank(),
    axis_title=element_text(color=INK, size=10),
    axis_text=element_text(color=INK_SOFT, size=8),
    axis_line=element_line(color=INK_SOFT),
    plot_title=element_text(color=INK, size=12),
    legend_background=element_rect(fill=ELEVATED_BG, color="none"),
    legend_key=element_rect(fill=ELEVATED_BG, color="none"),
    legend_text=element_text(color=INK_SOFT, size=8),
    legend_title=element_text(color=INK, size=9),
)

plot = (
    ggplot(df, aes(LON, LAT))
    + geom_raster(aes(fill=SALINITY))
    + geom_path(
        data=df_iso, mapping=aes("lon", "lat", group="group"), color=PAGE_BG, size=1.1, alpha=0.55, inherit_aes=False
    )
    + geom_path(
        data=df_iso, mapping=aes("lon", "lat", group="group"), color=INK, size=0.45, alpha=0.9, inherit_aes=False
    )
    + geom_polygon(
        data=df_land,
        mapping=aes("lon", "lat", group="group"),
        fill=LAND_FILL,
        color=INK_SOFT,
        size=0.5,
        inherit_aes=False,
    )
    + geom_label(
        data=df_labels,
        mapping=aes("lon", "lat", label="label"),
        color=INK,
        fill=PAGE_BG,
        size=8,
        label_padding=0.12,
        label_size=0.2,
        inherit_aes=False,
    )
    + scale_fill_gradientn(colors=[c for _, c in SEQ_FIELDS], values=[p for p, _ in SEQ_FIELDS], name="Salinity\n(psu)")
    + scale_x_continuous(breaks=lon_breaks, labels=lon_labels, expand=(0, 0))
    + scale_y_continuous(breaks=lat_breaks, labels=lat_labels, expand=(0, 0))
    + coord_cartesian(xlim=(df[LON].min(), df[LON].max()), ylim=(df[LAT].min(), df[LAT].max()))
    + labs(x=LON, y=LAT, title=title)
    + anyplot_theme
)

plot.save(f"plot-{THEME}.png", dpi=400, width=8, height=4.5, units="in", verbose=False)
