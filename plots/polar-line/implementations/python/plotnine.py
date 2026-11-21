""" anyplot.ai
polar-line: Polar Line Plot
Library: plotnine 0.15.9 | Python 3.14.10
Quality: 83/100 | Updated: 2026-11-21
"""

import os

import numpy as np
import pandas as pd
from plotnine import (
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
    guides,
    labs,
    scale_color_manual,
    theme,
    theme_void,
    xlim,
    ylim,
)


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: all eight positions, one per series in order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Constants
FULL_TURN = 360  # the angle column is in degrees and one cycle spans a full turn
SPOKE_STEP = 45  # degrees between radial grid lines

# Columns: set these to your table's column names
THETA = "Angle (degrees)"  # role: theta
RADII = ["Week 1", "Week 2"]  # role: radius
SERIES = "Week"  # role: extra
VALUE = "Activity (events per hour)"  # role: extra

# Data: replace this block with your own table, for example df = pd.read_csv("activity.csv")
np.random.seed(42)
angle = np.arange(24) * 15  # 24 hours around a full circle
df = pd.DataFrame(
    {
        THETA: angle,
        RADII[0]: 40 + 35 * np.sin(np.radians(angle - 90)) + np.random.randn(24) * 3,
        RADII[1]: 45 + 30 * np.sin(np.radians(angle - 120)) + np.random.randn(24) * 3,
    }
)

# Plot: reads only df and the constants above
long = df.melt(id_vars=THETA, value_vars=RADII, var_name=SERIES, value_name=VALUE).dropna()
groups = long[SERIES].unique().tolist()

# Each series joins its points in theta order and closes the loop back to its first point
paths = []
for name in groups:
    part = long[long[SERIES] == name].sort_values(THETA)
    part = pd.concat([part, part.iloc[:1]], ignore_index=True)
    part["order"] = np.arange(len(part))
    part["closing"] = part["order"] == len(part) - 1
    paths.append(part)
paths = pd.concat(paths, ignore_index=True)

# Angle 0 sits at the top and angles run clockwise, like a clock face
phi = np.radians(paths[THETA])
paths["x"] = paths[VALUE] * np.sin(phi)
paths["y"] = paths[VALUE] * np.cos(phi)
points = paths[~paths["closing"]]

# Grid: rings at round radius values, spokes at fixed angle steps
r_max = long[VALUE].max()
raw_step = r_max / 4
mag = 10 ** np.floor(np.log10(raw_step))
step = next(m * mag for m in (1, 2, 5, 10) if m * mag >= raw_step)
r_top = np.ceil(r_max / step) * step
ring_radii = np.arange(step, r_top + step / 2, step)

circle = np.radians(np.linspace(0, FULL_TURN, 361))
rings = pd.DataFrame(
    {
        "x": np.concatenate([r * np.sin(circle) for r in ring_radii]),
        "y": np.concatenate([r * np.cos(circle) for r in ring_radii]),
        "ring": np.repeat(ring_radii, len(circle)),
    }
)
spoke_angles = np.arange(0, FULL_TURN, SPOKE_STEP)
spokes = pd.DataFrame({"x": r_top * np.sin(np.radians(spoke_angles)), "y": r_top * np.cos(np.radians(spoke_angles))})

# Labels: angles as hours of the day outside the outer ring, radius values along one spoke
hours_per_degree = 24 / FULL_TURN
angle_labels = pd.DataFrame(
    {
        "x": r_top * 1.1 * np.sin(np.radians(spoke_angles)),
        "y": r_top * 1.1 * np.cos(np.radians(spoke_angles)),
        "label": [f"{a * hours_per_degree:g}h" for a in spoke_angles],
    }
)
label_angle = np.radians(SPOKE_STEP / 2)
radius_labels = pd.DataFrame(
    {
        "x": ring_radii * np.sin(label_angle),
        "y": ring_radii * np.cos(label_angle),
        "label": [f"{r:g}" for r in ring_radii],
    }
)

lim = r_top * 1.22
plot = (
    ggplot()
    + geom_path(rings, aes(x="x", y="y", group="ring"), color=INK, alpha=0.18, size=0.4)
    + geom_segment(spokes, aes(x=0, y=0, xend="x", yend="y"), color=INK, alpha=0.18, size=0.4)
    + geom_path(paths, aes(x="x", y="y", color=SERIES, group=SERIES), size=1.2, alpha=0.9)
    + geom_point(points, aes(x="x", y="y", color=SERIES), size=2.2, alpha=0.9)
    + geom_text(angle_labels, aes(x="x", y="y", label="label"), color=INK_SOFT, size=9)
    + geom_text(radius_labels, aes(x="x", y="y", label="label"), color=INK_SOFT, size=7)
    + scale_color_manual(values=IMPRINT_PALETTE, limits=groups)
    + guides(color="legend")
    + xlim(-lim, lim)
    + ylim(-lim, lim)
    + coord_fixed()
    + labs(title="polar-line · python · plotnine · anyplot.ai", color=SERIES, caption=f"Rings: {VALUE}")
    + theme_void()
    + theme(
        figure_size=(6, 6),
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        plot_title=element_text(size=12, color=INK, ha="center", margin={"b": 10}),
        plot_caption=element_text(size=8, color=INK_SOFT),
        legend_position="bottom",
        legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT),
        legend_text=element_text(size=9, color=INK_SOFT),
        legend_title=element_text(size=9, color=INK),
        legend_key=element_blank(),
        axis_line=element_blank(),
        plot_margin=0.03,
    )
)

# Save
plot.save(f"plot-{THEME}.png", dpi=400, width=6, height=6, units="in", verbose=False)
