"""anyplot.ai
polar-scatter: Polar Scatter Plot
Library: plotnine 0.15.4 | Python 3.13.13
Quality: 95/100 | Updated: 2026-05-09
"""

import os
import sys

import numpy as np
import pandas as pd


# Work around naming conflict with plotnine.py script and plotnine package
script_dir = os.path.dirname(os.path.abspath(__file__))
if script_dir in sys.path:
    sys.path.remove(script_dir)
if "" in sys.path:
    sys.path.remove("")
if "." in sys.path:
    sys.path.remove(".")

from plotnine import (  # noqa: E402
    aes,
    coord_fixed,
    element_blank,
    element_rect,
    element_text,
    geom_path,
    geom_point,
    geom_segment,
    geom_text,
    ggplot,
    labs,
    scale_color_manual,
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

# Imprint palette
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Constants
TIME_ORDER = ["Morning", "Afternoon", "Evening"]  # time-of-day scale
COMPASS = {"N": 0, "NE": 45, "E": 90, "SE": 135, "S": 180, "SW": 225, "W": 270, "NW": 315}
RADIUS_STEP = 5  # m/s between circular gridlines

THETA = "Wind direction (°)"  # role: theta
RADIUS = "Wind speed (m/s)"  # role: radius
TIME = "Time of day"  # role: category

# Data: replace this block with your own table, for example df = pd.read_csv("wind.csv")
rng = np.random.default_rng(42)
n_half = 60
# Prevailing wind from SW (~225°) and secondary from NE (~45°)
angles = np.concatenate([rng.normal(225, 30, n_half), rng.normal(45, 25, n_half)]) % 360
speeds = np.clip(np.abs(np.concatenate([rng.normal(12, 4, n_half), rng.normal(8, 3, n_half)])), 1, 25)
times = rng.choice(["Morning", "Afternoon", "Evening"], 2 * n_half, p=[0.35, 0.40, 0.25])
df = pd.DataFrame({THETA: angles, RADIUS: speeds, TIME: times})

# Plot
X, Y, GROUP = "x", "y", "ring"
rim = int(np.ceil(df[RADIUS].max() / RADIUS_STEP)) * RADIUS_STEP
ring_radii = np.arange(RADIUS_STEP, rim + 1, RADIUS_STEP)
label_ring = rim + 5


def to_xy(deg, radius):
    """North-up, clockwise compass degrees to Cartesian."""
    rad = np.radians(90 - np.asarray(deg, dtype=float))
    return radius * np.cos(rad), radius * np.sin(rad)


points = df.assign(**{X: to_xy(df[THETA], df[RADIUS])[0], Y: to_xy(df[THETA], df[RADIUS])[1]})

ring_angles = np.linspace(0, 360, 101)
grid_df = pd.DataFrame([{X: to_xy(a, r)[0], Y: to_xy(a, r)[1], GROUP: r} for r in ring_radii for a in ring_angles])

spoke_ends = [to_xy(deg, rim + 2) for deg in COMPASS.values()]
spoke_df = pd.DataFrame({"x1": 0.0, "y1": 0.0, "x2": [e[0] for e in spoke_ends], "y2": [e[1] for e in spoke_ends]})

label_pos = [to_xy(deg, label_ring) for deg in COMPASS.values()]
label_df = pd.DataFrame({"label": list(COMPASS), X: [p[0] for p in label_pos], Y: [p[1] for p in label_pos]})

# Speed labels along the NNE axis, unit on the outermost ring
nne_x, nne_y = to_xy(22.5, ring_radii)
radius_label_df = pd.DataFrame(
    {"label": [f"{r}" for r in ring_radii[:-1]] + [f"{ring_radii[-1]} m/s"], X: nne_x + 0.04 * rim, Y: nne_y}
)

colors = dict(zip(TIME_ORDER, IMPRINT_PALETTE, strict=False))
extent = label_ring + 4

plot = (
    ggplot()
    + geom_path(aes(x=X, y=Y, group=GROUP), data=grid_df, color=INK_SOFT, size=0.25, alpha=0.15, linetype="dashed")
    + geom_segment(aes(x="x1", y="y1", xend="x2", yend="y2"), data=spoke_df, color=INK_SOFT, size=0.25, alpha=0.15)
    + geom_point(aes(x=X, y=Y, color=TIME), data=points, size=2.5, alpha=0.75)
    + geom_text(aes(x=X, y=Y, label="label"), data=label_df, size=8, color=INK, fontweight="bold")
    + geom_text(aes(x=X, y=Y, label="label"), data=radius_label_df, size=5, color=INK_SOFT)
    + scale_color_manual(values=colors, limits=TIME_ORDER, name=TIME)
    + coord_fixed(ratio=1)
    + scale_x_continuous(limits=(-extent, extent))
    + scale_y_continuous(limits=(-extent, extent))
    + labs(title="polar-scatter · python · plotnine · anyplot.ai")
    + theme(
        figure_size=(6, 6),
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_grid_major=element_blank(),
        panel_grid_minor=element_blank(),
        panel_border=element_blank(),
        axis_title=element_blank(),
        axis_text=element_blank(),
        axis_ticks=element_blank(),
        axis_line=element_blank(),
        plot_title=element_text(size=12, ha="center", color=INK),
        legend_title=element_text(size=8, color=INK),
        legend_text=element_text(size=7, color=INK_SOFT),
        legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT),
        legend_position="right",
    )
)

plot.save(f"plot-{THEME}.png", dpi=400, width=6, height=6, units="in")
