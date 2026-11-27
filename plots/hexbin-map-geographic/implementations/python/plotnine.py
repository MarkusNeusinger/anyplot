"""anyplot.ai
hexbin-map-geographic: Hexagonal Binning Map
Library: plotnine 0.15.4 | Python 3.13.13
Quality: 89/100 | Updated: 2026-05-27
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
    geom_label,
    geom_polygon,
    ggplot,
    labs,
    scale_fill_gradientn,
    theme,
    theme_minimal,
)


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Base-map tokens: neighbouring terrain behind the state, the state itself, its border
OUTSIDE_COLOR = "#E4E1D8" if THEME == "light" else "#222220"
STATE_COLOR = "#F4F1E8" if THEME == "light" else "#34342F"
STATE_EDGE = "#8A8980" if THEME == "light" else "#6A6962"

# Imprint palette (positions are used by the continuous field ramp below)
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Imprint sequential ramp for fields (colored cells that fill the plot), as (position, hex) stops
SEQ_FIELDS = (
    [(0.0, "#66E2B2"), (0.369, "#009E73"), (0.803, "#024582"), (1.0, "#351E45")]
    if THEME == "light"
    else [(0.0, "#404C02"), (0.487, "#009E73"), (1.0, "#CDD9FF")]
)

# Constants
HEX_COLUMNS = 26  # hexagons across the width of the data: larger number = smaller cells
BASE_MAP_PAD = 0.6  # degrees of map around the state outline

# Columns: set these to your table's column names
LONGITUDE = "Longitude (°)"  # role: lon
LATITUDE = "Latitude (°)"  # role: lat

# Data: replace this block with your own table, for example df = pd.read_csv("strikes.csv")
# Simulated cloud-to-ground lightning strikes over Texas, clustered along storm corridors
rng = np.random.default_rng(42)
# (centre lon, centre lat, spread lon, spread lat, strikes)
storm_zones = [
    (-95.2, 29.8, 0.60, 0.45, 3200),  # Houston and the Gulf coast
    (-97.0, 32.8, 0.50, 0.40, 2400),  # Dallas-Fort Worth
    (-94.8, 31.6, 0.50, 0.60, 1400),  # East Texas piney woods
    (-98.4, 30.0, 0.60, 0.45, 1600),  # Hill Country and San Antonio
    (-101.8, 35.2, 0.70, 0.50, 1100),  # Panhandle supercells
    (-102.0, 31.4, 0.90, 0.70, 500),  # West Texas, scattered
]
df = pd.concat(
    [
        pd.DataFrame({LONGITUDE: rng.normal(lon0, sd_lon, n), LATITUDE: rng.normal(lat0, sd_lat, n)})
        for lon0, lat0, sd_lon, sd_lat, n in storm_zones
    ],
    ignore_index=True,
)

# Plot
# Texas outline as base map: Red River, Sabine, Gulf coast, Rio Grande, New Mexico line
outline = pd.DataFrame(
    [
        (-103.04, 36.50), (-100.00, 36.50), (-100.00, 34.56), (-99.20, 34.21), (-98.10, 34.14),
        (-97.10, 33.75), (-96.50, 33.82), (-95.50, 33.88), (-94.50, 33.64), (-94.04, 33.55),
        (-94.04, 32.40), (-93.90, 31.90), (-93.55, 31.18), (-93.70, 30.50), (-93.70, 29.75),
        (-94.70, 29.35), (-95.30, 28.90), (-96.40, 28.35), (-97.20, 27.70), (-97.40, 26.90),
        (-97.15, 25.96), (-98.20, 26.05), (-99.10, 26.40), (-99.50, 27.50), (-100.30, 28.30),
        (-100.70, 29.10), (-101.40, 29.77), (-102.30, 29.88), (-102.70, 29.70), (-103.10, 29.00),
        (-104.00, 29.30), (-104.70, 30.00), (-105.00, 30.70), (-106.50, 31.78), (-106.62, 32.00),
        (-103.06, 32.00),
    ],
    columns=[LONGITUDE, LATITUDE],
)  # fmt: skip
outline["region"] = "state"

# Hexagons are regular on screen: bin in x = lon * cos(mid-latitude), then map the corners back
mid_lat = df[LATITUDE].mean()
stretch = np.cos(np.radians(mid_lat))
x = df[LONGITUDE] * stretch
y = df[LATITUDE]
hex_radius = (x.max() - x.min()) / HEX_COLUMNS / np.sqrt(3)

# Cube-round each strike to its hexagon (pointy-top grid) and count strikes per cell
q = (np.sqrt(3) / 3 * x - y / 3) / hex_radius
r = (2 / 3 * y) / hex_radius
cx, cy, cz = q, -q - r, r
rx, ry, rz = np.round(cx), np.round(cy), np.round(cz)
dx, dy, dz = (rx - cx).abs(), (ry - cy).abs(), (rz - cz).abs()
rx = np.where((dx > dy) & (dx > dz), -ry - rz, rx)
rz = np.where((dx <= dy) | (dx <= dz), np.where(dy > dz, rz, -rx - ry), rz)
cells = pd.DataFrame({"q": rx, "r": rz}).value_counts().rename("count").reset_index()
cells["hex_id"] = np.arange(len(cells))
centre_x = hex_radius * np.sqrt(3) * (cells["q"] + cells["r"] / 2)
centre_y = hex_radius * 1.5 * cells["r"]

corners = np.radians(np.arange(6) * 60 + 30)
hexes = cells.loc[cells.index.repeat(6)].reset_index(drop=True)
hexes[LONGITUDE] = (np.repeat(centre_x.to_numpy(), 6) + hex_radius * np.tile(np.cos(corners), len(cells))) / stretch
hexes[LATITUDE] = np.repeat(centre_y.to_numpy(), 6) + hex_radius * np.tile(np.sin(corners), len(cells))

# Direct labels for the three busiest storm zones, set above their cores
labels = pd.DataFrame(
    {
        LONGITUDE: [-95.2, -97.0, -101.8],
        LATITUDE: [30.5, 33.5, 35.9],
        "label": ["Houston", "Dallas–Fort Worth", "Panhandle"],
    }
)

lon_lim = (outline[LONGITUDE].min() - BASE_MAP_PAD, outline[LONGITUDE].max() + BASE_MAP_PAD)
lat_lim = (outline[LATITUDE].min() - BASE_MAP_PAD, outline[LATITUDE].max() + BASE_MAP_PAD)

title = "hexbin-map-geographic · python · plotnine · anyplot.ai"

# sqrt transform spreads the ramp across the right-skewed strike counts
plot = (
    ggplot()
    + geom_polygon(
        aes(x=LONGITUDE, y=LATITUDE, group="region"), data=outline, fill=STATE_COLOR, color=STATE_EDGE, size=0.6
    )
    + geom_polygon(
        aes(x=LONGITUDE, y=LATITUDE, group="hex_id", fill="count"), data=hexes, color=PAGE_BG, size=0.15, alpha=0.88
    )
    + geom_label(
        aes(x=LONGITUDE, y=LATITUDE, label="label"),
        data=labels,
        color=INK,
        fill=ELEVATED_BG,
        size=4.5,
        label_padding=0.2,
        label_size=0.3,
    )
    + scale_fill_gradientn(colors=[c for _, c in SEQ_FIELDS], values=[p for p, _ in SEQ_FIELDS], trans="sqrt")
    + coord_fixed(ratio=1 / stretch, xlim=lon_lim, ylim=lat_lim)
    + labs(title=title, x=LONGITUDE, y=LATITUDE, fill="Strikes")
    + theme_minimal()
    + theme(
        figure_size=(6, 6),
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=OUTSIDE_COLOR, color="none"),
        panel_grid_major=element_blank(),
        panel_grid_minor=element_blank(),
        plot_title=element_text(size=12, color=INK),
        axis_title=element_text(size=10, color=INK),
        axis_text=element_text(size=8, color=INK_SOFT),
        axis_line=element_line(color=INK_SOFT, size=0.3),
        legend_title=element_text(size=8, color=INK),
        legend_text=element_text(size=8, color=INK_SOFT),
        legend_background=element_rect(fill=ELEVATED_BG, color="none"),
        legend_key=element_rect(fill=ELEVATED_BG, color="none"),
        legend_position="right",
    )
)

# Save
plot.save(f"plot-{THEME}.png", dpi=400, width=6, height=6, units="in")
