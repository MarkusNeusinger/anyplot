"""anyplot.ai
windbarb-basic: Wind Barb Plot for Meteorological Data
Library: letsplot 4.9.0 | Python 3.13.13
Quality: pending | Updated: 2026-05-19
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
    gggrid,
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

THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
GRID_COLOR = "rgba(26,26,23,0.15)" if THEME == "light" else "rgba(240,239,232,0.15)"
BRAND = "#009E73"  # Imprint palette position 1

# Constants
CALM_KNOTS = 2.5  # below this, a station is calm: an open circle without a staff
PENNANT_KNOTS = 50
FULL_BARB_KNOTS = 10
HALF_BARB_KNOTS = 5
MAX_BARB_KNOTS = 195  # four pennants, one full and one half barb

X = "Longitude (°E)"  # role: x
Y = "Latitude (°N)"  # role: y
U = "Zonal wind u (kt)"  # role: u
V = "Meridional wind v (kt)"  # role: v

# Data: replace this block with your own table, for example df = pd.read_csv("stations.csv")
np.random.seed(42)
n_x, n_y = 8, 6
grid_x, grid_y = np.meshgrid(np.linspace(0, 140, n_x), np.linspace(0, 100, n_y))
x_pos = grid_x.flatten()
y_pos = grid_y.flatten()
u_wind = 15 * np.sin(x_pos / 30) + np.random.normal(0, 3, len(x_pos))
v_wind = 10 * np.cos(y_pos / 20) + np.random.normal(0, 3, len(y_pos))
# Two calm stations and two strong ones (pennants) among the moderate winds
u_wind[[0, 5]], v_wind[[0, 5]] = 0.5, 0.5
u_wind[[20, 21]], v_wind[[20, 21]] = 45.0, 30.0
df = pd.DataFrame({X: x_pos, Y: y_pos, U: u_wind, V: v_wind})

# Plot
speed = np.hypot(df[U], df[V])
calm = speed < CALM_KNOTS

# Barb geometry scales with the station spacing so neighbours stay apart
spacing_x = np.diff(np.sort(df[X].unique())).min() if df[X].nunique() > 1 else 1.0
spacing_y = np.diff(np.sort(df[Y].unique())).min() if df[Y].nunique() > 1 else 1.0
barb_length = 0.55 * min(spacing_x, spacing_y)
barb_spacing = barb_length * 0.13
barb_tick = barb_length * 0.3

segments = []
pennants = []
for i, (sx, sy, su, sv, knots) in enumerate(zip(df[X], df[Y], df[U], df[V], speed, strict=True)):
    if not np.isfinite(knots) or knots < CALM_KNOTS:
        continue
    # The staff points toward the direction the wind blows from
    angle = np.arctan2(-sv, -su)
    cos_a, sin_a = np.cos(angle), np.sin(angle)
    side_x, side_y = -sin_a, cos_a  # all feathers on the left side of the staff
    segments.append({"x": sx, "y": sy, "xend": sx + barb_length * cos_a, "yend": sy + barb_length * sin_a})

    remaining = min(knots, MAX_BARB_KNOTS)  # feathers must fit on the staff
    pos = barb_length - 0.06 * barb_length
    while remaining >= PENNANT_KNOTS - CALM_KNOTS:
        tip = (sx + pos * cos_a + barb_tick * side_x, sy + pos * sin_a + barb_tick * side_y)
        base = pos - 2 * barb_spacing
        pennants.append(
            {
                "pennant": i * 100 + len(pennants),
                "x": [sx + pos * cos_a, tip[0], sx + base * cos_a],
                "y": [sy + pos * sin_a, tip[1], sy + base * sin_a],
            }
        )
        remaining -= PENNANT_KNOTS
        pos -= 2.5 * barb_spacing
    while remaining >= FULL_BARB_KNOTS - CALM_KNOTS:
        bx, by = sx + pos * cos_a, sy + pos * sin_a
        segments.append({"x": bx, "y": by, "xend": bx + barb_tick * side_x, "yend": by + barb_tick * side_y})
        remaining -= FULL_BARB_KNOTS
        pos -= barb_spacing
    if remaining >= HALF_BARB_KNOTS - CALM_KNOTS:
        bx, by = sx + pos * cos_a, sy + pos * sin_a
        segments.append(
            {"x": bx, "y": by, "xend": bx + 0.5 * barb_tick * side_x, "yend": by + 0.5 * barb_tick * side_y}
        )

segment_df = pd.DataFrame(segments, columns=["x", "y", "xend", "yend"])
pennant_df = pd.DataFrame(
    [{"pennant": p["pennant"], "x": px, "y": py} for p in pennants for px, py in zip(p["x"], p["y"], strict=True)],
    columns=["pennant", "x", "y"],
)

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

plot = (
    ggplot()
    + theme_minimal()
    + anyplot_theme
    + geom_segment(aes(x="x", y="y", xend="xend", yend="yend"), data=segment_df, color=BRAND, size=0.9)
    + geom_polygon(aes(x="x", y="y", group="pennant"), data=pennant_df, fill=BRAND, color=BRAND, size=0.4)
    + geom_point(aes(x=X, y=Y), data=df[calm], shape=1, size=5, color=BRAND, stroke=1.2)
    + geom_point(aes(x=X, y=Y), data=df, size=1.5, color=BRAND)
    + labs(x=X, y=Y, title="windbarb-basic · python · letsplot · anyplot.ai")
    + coord_fixed(ratio=1)
    + scale_x_continuous(expand=[0.08, 0])
    + scale_y_continuous(expand=[0.1, 0])
)

# The one-panel grid paints the whole canvas with the page color around the fixed-aspect plot
plot = gggrid([plot]) + ggsize(800, 450) + theme(plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG))

ggsave(plot, f"plot-{THEME}.png", path=".", scale=4)
ggsave(plot, f"plot-{THEME}.html", path=".")
