"""anyplot.ai
polar-bar: Polar Bar Chart (Wind Rose)
Library: plotnine 0.15.4 | Python 3.13.13
Quality: 90/100 | Updated: 2026-05-13
"""

import os

import numpy as np
import pandas as pd
from matplotlib.ticker import MaxNLocator
from plotnine import (
    aes,
    coord_fixed,
    element_blank,
    element_rect,
    element_text,
    geom_path,
    geom_polygon,
    geom_segment,
    geom_text,
    ggplot,
    guide_legend,
    guides,
    labs,
    scale_fill_manual,
    scale_x_continuous,
    scale_y_continuous,
    theme,
)


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: one position per stacked wind-speed bin, in order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Constants
BAR_FILL = 0.8  # share of each direction's angular slot that the bar fills
ARC_STEPS = 12  # points along each arc of a stacked segment
RADIUS_TICKS = 4  # target number of concentric gridlines

# Columns: set these to your table's column names
DIRECTION = "Wind direction"  # role: direction
SPEED_BIN = "Wind speed (m/s)"  # role: extra
FREQUENCY = "Frequency (%)"  # role: frequency

# Columns of the geometry tables built below the Data block
PX = "px"  # role: extra
PY = "py"  # role: extra
PX_END = "px_end"  # role: extra
PY_END = "py_end"  # role: extra
SHAPE_ID = "shape_id"  # role: extra
LABEL = "label"  # role: extra

# Data: replace this block with your own table, for example df = pd.read_csv("wind.csv")
rng = np.random.default_rng(7)
compass = ["N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE", "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"]
speed_bins = ["0-3", "3-6", "6-9", "9+"]
bearing = np.arange(len(compass)) * 360 / len(compass)
# Prevailing flow from the east-north-east, a weaker secondary flow from the south-south-west
weight = 1.0 + 6.0 * np.exp(-((((bearing - 70) + 180) % 360 - 180) ** 2) / (2 * 28**2))
weight += 2.5 * np.exp(-((((bearing - 205) + 180) % 360 - 180) ** 2) / (2 * 25**2))
# Stronger winds are more common in the prevailing directions
strength = weight / weight.max()
shares = np.array([[0.40 - 0.18 * s, 0.32, 0.18 + 0.05 * s, 0.10 + 0.13 * s] for s in strength])
shares = shares / shares.sum(axis=1, keepdims=True)
values = weight[:, None] * shares * rng.uniform(0.85, 1.15, size=shares.shape)
values = values / values.sum() * 100
df = pd.DataFrame(
    {
        DIRECTION: np.repeat(compass, len(speed_bins)),
        SPEED_BIN: speed_bins * len(compass),
        FREQUENCY: np.round(values.ravel(), 2),
    }
)

# Plot: reads only df and the constants above
directions = df[DIRECTION].dropna().unique().tolist()
bins = df[SPEED_BIN].dropna().unique().tolist()
table = df.pivot_table(index=DIRECTION, columns=SPEED_BIN, values=FREQUENCY, sort=False).reindex(
    index=directions, columns=bins
)
cumulative = table.cumsum(axis=1).to_numpy()
top = np.nanmax(cumulative)
slot = 360 / len(directions)
half_width = slot * BAR_FILL / 2
centers = np.arange(len(directions)) * slot  # compass bearing, clockwise from north


def to_xy(radius, bearing_deg):
    """Compass bearing (north up, clockwise) to cartesian coordinates."""
    theta = np.radians(90 - np.asarray(bearing_deg))
    return radius * np.cos(theta), radius * np.sin(theta)


# Stacked wedges: each segment spans from the previous cumulative radius to its own
wedge_rows = []
shape_id = 0
for i in range(len(directions)):
    arc = np.linspace(centers[i] - half_width, centers[i] + half_width, ARC_STEPS)
    for j, speed in enumerate(bins):
        inner = cumulative[i, j - 1] if j > 0 else 0.0
        outer = cumulative[i, j]
        ox, oy = to_xy(outer, arc)
        ix, iy = to_xy(inner, arc[::-1])
        wedge_rows.append(pd.DataFrame({PX: np.r_[ox, ix], PY: np.r_[oy, iy], SHAPE_ID: shape_id, SPEED_BIN: speed}))
        shape_id += 1
wedge_df = pd.concat(wedge_rows, ignore_index=True)
wedge_df[SPEED_BIN] = pd.Categorical(wedge_df[SPEED_BIN], categories=bins)

# Concentric gridlines at round values, starting at zero
ticks = [t for t in MaxNLocator(RADIUS_TICKS, steps=[1, 2, 5, 10]).tick_values(0, top) if t > 0]
rim = ticks[-1] if ticks[-1] >= top else top
full_circle = np.linspace(0, 360, 181)
grid_df = pd.concat(
    [
        pd.DataFrame({PX: to_xy(t, full_circle)[0], PY: to_xy(t, full_circle)[1], SHAPE_ID: k})
        for k, t in enumerate(ticks)
    ],
    ignore_index=True,
)

# Radial spokes at every direction
sx, sy = to_xy(rim * 1.04, centers)
spoke_df = pd.DataFrame({PX: 0.0, PY: 0.0, PX_END: sx, PY_END: sy})

# Direction labels at the rim; the four cardinal points are bold
lx, ly = to_xy(rim * 1.17, centers)
label_df = pd.DataFrame({PX: lx, PY: ly, LABEL: directions})
cardinal = label_df[LABEL].str.len() == 1

# Value labels along the gap between the last and first bars
gap_bearing = centers[0] - slot / 2
vx, vy = to_xy(np.array(ticks), gap_bearing)
value_df = pd.DataFrame({PX: vx - rim * 0.015, PY: vy, LABEL: [f"{t:g}%" for t in ticks]})

limit = rim * 1.32
title = "Wind Rose · polar-bar · python · plotnine · anyplot.ai"
title_size = round(12 * (67 / len(title) if len(title) > 67 else 1.0))

plot = (
    ggplot()
    + geom_path(aes(x=PX, y=PY, group=SHAPE_ID), data=grid_df, color=INK_SOFT, size=0.3, alpha=0.35, linetype="dashed")
    + geom_segment(aes(x=PX, y=PY, xend=PX_END, yend=PY_END), data=spoke_df, color=INK_SOFT, size=0.3, alpha=0.25)
    + geom_polygon(aes(x=PX, y=PY, group=SHAPE_ID, fill=SPEED_BIN), data=wedge_df, color=PAGE_BG, size=0.25, alpha=0.95)
    + geom_text(aes(x=PX, y=PY, label=LABEL), data=label_df[cardinal], size=11, color=INK, fontweight="bold")
    + geom_text(aes(x=PX, y=PY, label=LABEL), data=label_df[~cardinal], size=8, color=INK_SOFT)
    + geom_text(aes(x=PX, y=PY, label=LABEL), data=value_df, size=7, color=INK_SOFT, ha="right")
    + scale_fill_manual(values=IMPRINT_PALETTE, limits=bins)
    + guides(fill=guide_legend(nrow=1))
    + coord_fixed(ratio=1)
    + scale_x_continuous(limits=(-limit, limit))
    + scale_y_continuous(limits=(-limit, limit))
    + labs(title=title, fill=SPEED_BIN)
    + theme(
        figure_size=(6, 6),
        text=element_text(color=INK_SOFT),
        plot_title=element_text(size=title_size, ha="center", color=INK),
        axis_title=element_blank(),
        axis_text=element_blank(),
        axis_ticks=element_blank(),
        axis_line=element_blank(),
        panel_grid_major=element_blank(),
        panel_grid_minor=element_blank(),
        panel_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        legend_position="bottom",
        legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT),
        legend_key=element_rect(fill=ELEVATED_BG, color=ELEVATED_BG),
        legend_text=element_text(size=8, color=INK_SOFT),
        legend_title=element_text(size=9, color=INK),
    )
)

plot.save(f"plot-{THEME}.png", dpi=400, width=6, height=6, units="in", verbose=False)
