"""anyplot.ai
windbarb-basic: Wind Barb Plot for Meteorological Data
Library: letsplot 4.9.0 | Python 3.13.13
Quality: 87/100 | Updated: 2026-05-19
"""

import os

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
    geom_point,
    geom_polygon,
    geom_segment,
    ggplot,
    ggsave,
    ggsize,
    labs,
    scale_x_continuous,
    scale_y_continuous,
    theme,
    theme_minimal,
)


LetsPlot.setup_html()

# Theme tokens (Imprint palette)
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
GRID_COLOR = "rgba(26,26,23,0.15)" if THEME == "light" else "rgba(240,239,232,0.15)"
BRAND = "#009E73"

# Column constants
LON = "Longitude (°E)"  # role: x
LAT = "Latitude (°N)"  # role: y
U_KT = "u wind (kt)"  # role: u
V_KT = "v wind (kt)"  # role: v

# Data
np.random.seed(42)
x_coords = np.linspace(0, 140, 8)
y_coords = np.linspace(0, 100, 6)
grid_x, grid_y = np.meshgrid(x_coords, y_coords)
lon = grid_x.flatten()
lat = grid_y.flatten()

u = 15 * np.sin(lon / 30) + np.random.normal(0, 3, len(lon))
v = 10 * np.cos(lat / 20) + np.random.normal(0, 3, len(lat))

# Two calm stations (< 2.5 kt) and two strong ones (~54 kt) show every barb type
u[[0, 5]] = 0.5
v[[0, 5]] = 0.5
u[[20, 21]] = 45.0
v[[20, 21]] = 30.0

df = pd.DataFrame({LON: lon, LAT: lat, U_KT: u, V_KT: v})

# Plot
# Barb geometry, sized relative to the station spacing
SX, SY, SXEND, SYEND = "x", "y", "xend", "yend"  # derived barb segment columns
PENNANT_ID = "pennant"  # derived: one id per pennant triangle
stations = df.dropna(subset=[LON, LAT, U_KT, V_KT]).reset_index(drop=True)
speed = np.hypot(stations[U_KT], stations[V_KT])
span = max(np.ptp(stations[LON]), np.ptp(stations[LAT])) or 1.0
barb_length = span * 0.057
barb_spacing = barb_length * 0.19
barb_tick_length = barb_length * 0.31

segments = []
pennants = []

for px, py, pu, pv, spd in zip(stations[LON], stations[LAT], stations[U_KT], stations[V_KT], speed, strict=True):
    if spd < 2.5:
        continue

    # Staff points toward the direction the wind blows from
    angle = np.arctan2(-pv, -pu)
    cos_a, sin_a = np.cos(angle), np.sin(angle)
    perp_angle = angle + np.pi / 2
    cos_p, sin_p = np.cos(perp_angle), np.sin(perp_angle)

    segments.append({SX: px, SY: py, SXEND: px + barb_length * cos_a, SYEND: py + barb_length * sin_a})

    remaining = min(spd, 200.0)  # notation tops out well below 200 kt
    pos = barb_length - barb_spacing / 3

    # Pennants: 50 kt each
    while remaining >= 47.5:
        bx, by = px + pos * cos_a, py + pos * sin_a
        base_x, base_y = px + (pos - barb_spacing) * cos_a, py + (pos - barb_spacing) * sin_a
        corners = [(bx, by), (bx + barb_tick_length * cos_p, by + barb_tick_length * sin_p), (base_x, base_y)]
        pennants.extend({SX: cx, SY: cy, PENNANT_ID: len(pennants) // 3} for cx, cy in corners)
        remaining -= 50
        pos -= barb_spacing

    # Full barbs: 10 kt each
    while remaining >= 7.5:
        bx, by = px + pos * cos_a, py + pos * sin_a
        segments.append({SX: bx, SY: by, SXEND: bx + barb_tick_length * cos_p, SYEND: by + barb_tick_length * sin_p})
        remaining -= 10
        pos -= barb_spacing

    # Half barb: 5 kt
    if remaining >= 2.5:
        bx, by = px + pos * cos_a, py + pos * sin_a
        segments.append(
            {SX: bx, SY: by, SXEND: bx + barb_tick_length * 0.5 * cos_p, SYEND: by + barb_tick_length * 0.5 * sin_p}
        )

segment_df = pd.DataFrame(segments, columns=[SX, SY, SXEND, SYEND])
calm_df = stations[speed < 2.5]

anyplot_theme = theme(
    plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
    panel_background=element_rect(fill=PAGE_BG),
    panel_grid_major=element_line(color=GRID_COLOR, size=0.3),
    panel_grid_minor=element_blank(),
    axis_title=element_text(color=INK, size=12),
    axis_text=element_text(color=INK_SOFT, size=10),
    axis_line=element_line(color=INK_SOFT),
    plot_title=element_text(color=INK, size=16),
)

plot = ggplot() + theme_minimal() + anyplot_theme

# Staffs and feathers
plot = plot + geom_segment(aes(x=SX, y=SY, xend=SXEND, yend=SYEND), data=segment_df, color=BRAND, size=0.8)

# Pennants as filled triangles
pennant_df = pd.DataFrame(pennants, columns=[SX, SY, PENNANT_ID])
plot = plot + geom_polygon(aes(x=SX, y=SY, group=PENNANT_ID), data=pennant_df, fill=BRAND, color=BRAND, size=0.4)

# Calm stations: open circle without a staff
plot = plot + geom_point(aes(x=LON, y=LAT), data=calm_df, shape=1, size=5, color=BRAND, stroke=1.2)

# Station anchors
plot = plot + geom_point(aes(x=LON, y=LAT), data=stations, size=1.5, color=BRAND)

plot = (
    plot
    + labs(x=LON, y=LAT, title="windbarb-basic · python · letsplot · anyplot.ai")
    + coord_fixed(ratio=1)
    + scale_x_continuous(expand=[0.1, 0])
    + scale_y_continuous(expand=[0.1, 0])
    + ggsize(800, 450)
)

ggsave(plot, f"plot-{THEME}.png", path=".", scale=4)
ggsave(plot, f"plot-{THEME}.html", path=".")
