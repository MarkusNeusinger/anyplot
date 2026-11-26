"""anyplot.ai
contour-map-geographic: Contour Lines on Geographic Map
Library: letsplot 4.10.1 | Python 3.13.13
Quality: pending | Updated: 2026-05-20
"""

import math
import os
from itertools import pairwise

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
    geom_contour,
    geom_contourf,
    geom_label,
    geom_path,
    geom_point,
    geom_text,
    gggrid,
    ggplot,
    ggsize,
    labs,
    scale_fill_gradientn,
    theme,
)
from lets_plot.export import ggsave


LetsPlot.setup_html()

# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
CONTOUR_COLOR = "#F0EFE8" if THEME == "light" else "#1A1A17"
GRID_MAJOR = "#CCCAC3" if THEME == "light" else "#2E2E2B"
GRID_MINOR = "#E0DDD7" if THEME == "light" else "#252522"

# Imprint palette: all eight positions in canonical order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]
COAST_COLOR = IMPRINT_PALETTE[2]
CITY_COLOR = IMPRINT_PALETTE[1]

# Imprint sequential ramp for fields (filled contours), stops per theme
SEQ_FIELDS = (
    [(0.0, "#66E2B2"), (0.368, "#009E73"), (0.582, "#4467A3"), (1.0, "#002850")]
    if THEME == "light"
    else [(0.0, "#00573D"), (0.467, "#009E73"), (1.0, "#CDD9FF")]
)


def ramp_color(stops, t):
    """The hex at t (0 to 1) along (position, hex) stops, blended linearly in sRGB."""
    t = min(max(t, 0.0), 1.0)
    (p0, c0), (p1, c1) = next((a, b) for a, b in pairwise(stops) if t <= b[0])
    share = (t - p0) / (p1 - p0)
    return "#" + "".join(
        f"{round(int(c0[i : i + 2], 16) * (1 - share) + int(c1[i : i + 2], 16) * share):02X}" for i in (1, 3, 5)
    )


# Constants
LABEL_STEP = 500  # contour label interval in metres

# Columns: set these to your table's column names
LON = "Longitude (°W)"  # role: lon
LAT = "Latitude (°N)"  # role: lat
ELEVATION = "Elevation (m)"  # role: value

# Data: replace this block with your own grid, for example df = pd.read_csv("elevation_grid.csv")
np.random.seed(42)
lon_range = np.linspace(-120, -105, 60)
lat_range = np.linspace(35, 45, 50)
lon_grid, lat_grid = np.meshgrid(lon_range, lat_range)
peaks = [
    (40.5, -111.5, 2800, 2.0),  # Wasatch Range near Salt Lake City
    (39.0, -114.0, 2600, 1.8),  # Nevada peak (Great Basin)
    (43.5, -110.5, 3200, 2.5),  # Tetons area
    (37.5, -118.5, 3500, 2.2),  # Sierra Nevada
    (41.0, -106.5, 2900, 2.0),  # Rocky Mountains
]
elevation = 1200 + np.random.randn(*lat_grid.shape) * 30
for peak_lat, peak_lon, peak_height, spread in peaks:
    distance = np.sqrt((lat_grid - peak_lat) ** 2 + (lon_grid - peak_lon) ** 2)
    elevation += peak_height * np.exp(-(distance**2) / (2 * spread**2))
df = pd.DataFrame({LON: lon_grid.ravel(), LAT: lat_grid.ravel(), ELEVATION: elevation.ravel()})

# Plot: reads only df and the constants above
lon_min, lon_max = df[LON].min(), df[LON].max()
lat_min, lat_max = df[LAT].min(), df[LAT].max()
elev_min = math.floor(df[ELEVATION].min() / LABEL_STEP) * LABEL_STEP
elev_max = math.ceil(df[ELEVATION].max() / LABEL_STEP) * LABEL_STEP
ramp = [ramp_color(SEQ_FIELDS, k / 255) for k in range(256)]

# Range names and reference cities: other text on the map that contour labels keep clear of
range_labels = pd.DataFrame(
    {
        LON: [-118.8, -111.2, -110.8, -106.8],
        LAT: [37.2, 39.9, 43.8, 41.3],
        "label": ["Sierra\nNevada", "Wasatch\nRange", "Teton\nRange", "Rocky\nMts."],
    }
)
cities = pd.DataFrame(
    {
        LON: [-119.81, -115.14, -111.89, -116.20],
        LAT: [39.53, 36.18, 40.76, 43.62],
        "label": ["Reno", "Las Vegas", "SLC", "Boise"],
    }
)
keep_out = pd.concat([range_labels[[LON, LAT]], cities[[LON, LAT]]]).to_numpy()
KEEP_OUT_DISTANCE = 2.3  # degrees

# One value label per contour level, set where the level lies farthest from the labels placed so far
contour_levels = np.arange(math.ceil(df[ELEVATION].min() / LABEL_STEP) * LABEL_STEP, df[ELEVATION].max(), LABEL_STEP)
label_data = []
used_positions = []
for level in contour_levels:
    candidates = df[
        ((df[ELEVATION] - level).abs() < 80)
        & (df[LON] > lon_min + 2.0)  # left buffer to prevent text clipping
        & (df[LON] < lon_max - 7.0)  # right buffer to avoid panel clipping
        & (df[LAT] > lat_min + 0.5)
        & (df[LAT] < lat_max - 0.5)
    ]
    near_text = np.hypot(
        candidates[LON].to_numpy()[:, None] - keep_out[:, 0], candidates[LAT].to_numpy()[:, None] - keep_out[:, 1]
    ).min(axis=1)
    candidates = candidates[near_text > KEEP_OUT_DISTANCE]
    if candidates.empty:
        continue
    if used_positions:
        used = np.array(used_positions)
        gaps = np.hypot(
            candidates[LON].to_numpy()[:, None] - used[:, 0], candidates[LAT].to_numpy()[:, None] - used[:, 1]
        )
        min_dist = gaps.min(axis=1)
    else:
        min_dist = np.full(len(candidates), np.inf)
    best = int(np.argmax(min_dist))
    if min_dist[best] > 2.0:
        row = candidates.iloc[best]
        label_data.append({LON: row[LON], LAT: row[LAT], "label": f"{int(level)}m"})
        used_positions.append((row[LON], row[LAT]))
label_df = pd.DataFrame(label_data, columns=[LON, LAT, "label"])

# Basemap overlay: Pacific coastline, state borders, range names and reference cities
coast_df = pd.DataFrame(
    {
        LON: [-120, -120, -120, -120, -119.8, -119.5, -119.2, -118.8, -118.5, -118.2, -118],
        LAT: [35, 36, 37.5, 39, 40, 41, 42, 43, 43.8, 44.5, 45],
    }
)
border_segments = [
    {LON: [-120, -120, -117, -114], LAT: [42, 39, 36, 35]},
    {LON: [-114, -114], LAT: [35, 42]},
    {LON: [-111, -111], LAT: [41, 45]},
    {LON: [-117, -111], LAT: [45, 45]},
]

plot = (
    ggplot(df, aes(x=LON, y=LAT, z=ELEVATION))
    + geom_contourf(aes(fill="..level.."), bins=12)
    + geom_contour(color=CONTOUR_COLOR, size=0.5, bins=12, alpha=0.7)
    + scale_fill_gradientn(colors=ramp, limits=[elev_min, elev_max], name=ELEVATION)
    + geom_path(data=coast_df, mapping=aes(x=LON, y=LAT), color=COAST_COLOR, size=2.0, inherit_aes=False)
)

for segment in border_segments:
    plot += geom_path(
        data=pd.DataFrame(segment),
        mapping=aes(x=LON, y=LAT),
        color=INK_SOFT,
        size=0.8,
        linetype="dashed",
        inherit_aes=False,
    )

# Contour values on small page-colored plaques so they read on any fill
plot += geom_label(
    data=label_df,
    mapping=aes(x=LON, y=LAT, label="label"),
    color=INK,
    fill=ELEVATED_BG,
    alpha=0.85,
    size=8,
    fontface="bold",
    label_padding=0.15,
    label_r=0.1,
    label_size=0,
    inherit_aes=False,
)
plot += geom_label(
    data=range_labels,
    mapping=aes(x=LON, y=LAT, label="label"),
    color=INK_SOFT,
    fill=ELEVATED_BG,
    alpha=0.7,
    size=8,
    fontface="italic",
    label_padding=0.15,
    label_r=0.1,
    label_size=0,
    inherit_aes=False,
)
plot += geom_point(
    data=cities,
    mapping=aes(x=LON, y=LAT),
    color=CITY_COLOR,
    size=4,
    shape=21,
    fill=ELEVATED_BG,
    stroke=1.5,
    inherit_aes=False,
)
plot += geom_text(
    data=cities,
    mapping=aes(x=LON, y=LAT, label="label"),
    color=INK,
    size=8,
    nudge_y=0.45,
    fontface="bold",
    inherit_aes=False,
)

# Theme-adaptive chrome
anyplot_theme = theme(
    plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
    panel_background=element_rect(fill=PAGE_BG),
    panel_border=element_blank(),
    panel_grid_major=element_line(color=GRID_MAJOR, size=0.3),
    panel_grid_minor=element_line(color=GRID_MINOR, size=0.2),
    axis_title=element_text(color=INK, size=12),
    axis_text=element_text(color=INK_SOFT, size=10),
    axis_line=element_line(color=INK_SOFT, size=0.5),
    plot_title=element_text(color=INK, size=16),
    legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT),
    legend_text=element_text(color=INK_SOFT, size=10),
    legend_title=element_text(color=INK, size=12),
    legend_position="right",
)

# Longitude degrees shrink with latitude: correct the aspect at the map's mid-latitude
geo_ratio = 1.0 / np.cos(np.radians((lat_min + lat_max) / 2))

plot = (
    plot
    + labs(title="contour-map-geographic · python · letsplot · anyplot.ai", x=LON, y=LAT)
    + anyplot_theme
    + coord_fixed(ratio=geo_ratio)
)

# The fixed aspect narrows the plot box: a one-panel grid paints the whole canvas
plot = gggrid([plot]) + ggsize(800, 450) + theme(plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG))

ggsave(plot, f"plot-{THEME}.png", path=".", scale=4)
ggsave(plot, f"plot-{THEME}.html", path=".")
