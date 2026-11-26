"""anyplot.ai
scatter-shot-chart: Basketball Shot Chart
Library: letsplot 4.10.1 | Python 3.13.14
Quality: 90/100 | Updated: 2026-06-21
"""

import os

import numpy as np
import pandas as pd
from lets_plot import (
    LetsPlot,
    aes,
    coord_fixed,
    element_rect,
    element_text,
    geom_density2d,
    geom_path,
    geom_point,
    geom_rect,
    geom_segment,
    geom_text,
    gggrid,
    ggplot,
    ggsave,
    ggsize,
    labs,
    layer_tooltips,
    scale_alpha_identity,
    scale_color_identity,
    scale_fill_identity,
    scale_shape_identity,
    scale_size_identity,
    theme,
    theme_void,
    xlim,
    ylim,
)


LetsPlot.setup_html()

# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette — made = position 1 (green), missed = position 5 (red, semantic: bad outcome)
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]
MADE_COLOR = IMPRINT_PALETTE[0]
MISSED_COLOR = IMPRINT_PALETTE[4]

# Court visual tokens (domain element — warm hardwood tone, theme-variant)
COURT_COLOR = "#E8DCC8" if THEME == "light" else "#2A2318"
LINE_COLOR = "#5A5048" if THEME == "light" else "#8A7E72"
ANNOTATION_BG = "rgba(232,220,200,0.85)" if THEME == "light" else "rgba(42,35,24,0.88)"

# Constants: NBA half-court, in feet from the basket center
COURT_HALF_WIDTH = 25  # 50 ft wide
COURT_DEPTH = 47  # baseline to half-court line
THREE_PT_RADIUS = 23.75  # three-point arc at the top
CORNER_THREE_X = 22  # corner three-point sidelines
CORNER_THREE_TOP = 14  # where the corner sidelines meet the arc
PAINT_HALF_WIDTH = 8  # 16 ft wide key
FREE_THROW_Y = 15  # free-throw line distance from the baseline reference
FREE_THROW_RADIUS = 6
RESTRICTED_RADIUS = 4
RIM_Y = 1.25
BACKBOARD_Y = -0.5
PAINT_ZONE_RADIUS = 8  # shots closer than this to the basket count as "Paint"
ZONE_ORDER = ["Paint", "Mid-Range", "Above Break 3", "Corner 3"]
ZONE_LABELS = {"Paint": "Paint", "Mid-Range": "Mid-Range", "Above Break 3": "3PT", "Corner 3": "Corner 3"}
ZONE_LABEL_POS = {
    "Paint": (17.5, 3.5),
    "Mid-Range": (-20.0, 15.0),
    "Above Break 3": (0.0, 31.0),
    "Corner 3": (-21.0, 2.5),
}
FREE_THROW_TYPE, THREE_POINTER_TYPE = "free-throw", "3-pointer"  # the spec's shot_type categories
MADE_SIZE, MISSED_SIZE = 3.0, 2.5
CIRCLE_SHAPE, CROSS_SHAPE = 21, 4

# Columns: set these to your table's column names
X = "x"  # role: x
Y = "y"  # role: y
MADE = "made"  # role: made
SHOT_TYPE = "shot_type"  # role: shot_type

# Data: replace this block with your own table, for example df = pd.read_csv("shots.csv")
np.random.seed(42)
shot_x = np.concatenate(
    [
        np.random.normal(0, 3, 80),  # paint area
        np.random.normal(0, 7, 60),  # mid-range center
        np.random.normal(-12, 4, 25),  # mid-range left
        np.random.normal(12, 4, 25),  # mid-range right
        np.random.uniform(-22, 22, 60),  # above-break 3
        np.random.normal(-22, 1.2, 20),  # left corner 3
        np.random.normal(22, 1.2, 20),  # right corner 3
        np.random.normal(0, 12, 50),  # deep 3
        np.random.normal(0, 0.5, 10),  # free throws
    ]
)
shot_y = np.concatenate(
    [
        np.random.uniform(0, 6, 80),  # paint area
        np.random.uniform(6, 16, 60),  # mid-range center
        np.random.uniform(4, 14, 25),  # mid-range left
        np.random.uniform(4, 14, 25),  # mid-range right
        np.random.uniform(16, 26, 60),  # above-break 3
        np.random.uniform(0, 12, 20),  # left corner 3
        np.random.uniform(0, 12, 20),  # right corner 3
        np.random.uniform(24, 34, 50),  # deep 3
        np.random.normal(15, 0.3, 10),  # free throws
    ]
)
shot_x = np.clip(shot_x, -25, 25)
shot_y = np.clip(shot_y, 0, 40)

shot_dist = np.sqrt(shot_x**2 + shot_y**2)
corner_three = (np.abs(shot_x) > 21) & (shot_y < 14)
three = (shot_dist > 23.75) | corner_three
free_throw = (np.abs(shot_x) < 1) & (np.abs(shot_y - 15) < 1)
shot_kind = np.where(free_throw, "free-throw", np.where(three, "3-pointer", "2-pointer"))

base_pct = np.where(shot_kind == "free-throw", 0.78, np.where(shot_kind == "2-pointer", 0.50, 0.35))
make_prob = np.clip(base_pct - shot_dist * 0.004, 0.15, 0.85)

df = pd.DataFrame({X: shot_x, Y: shot_y, MADE: np.random.random(len(shot_x)) < make_prob, SHOT_TYPE: shot_kind})

# Plot: reads only df and the constants above
n_shots = len(df)
made = df[MADE].to_numpy()
n_made = int(made.sum())
n_missed = n_shots - n_made
fg_percent = n_made / n_shots * 100

# Zone of each shot, derived from position and shot type
dist = np.hypot(df[X], df[Y])
is_corner = (df[X].abs() > CORNER_THREE_X - 1) & (df[Y] < CORNER_THREE_TOP)
is_free_throw = df[SHOT_TYPE] == FREE_THROW_TYPE
zone = np.full(n_shots, "Mid-Range", dtype=object)
zone[(dist < PAINT_ZONE_RADIUS).to_numpy()] = "Paint"
zone[(df[SHOT_TYPE] == THREE_POINTER_TYPE).to_numpy() & ~is_corner.to_numpy()] = "Above Break 3"
zone[is_corner.to_numpy()] = "Corner 3"
zone[is_free_throw.to_numpy()] = "Free Throw"

# Pre-mapped visual columns for the identity scales
RESULT, COLOR, SIZE, SHAPE, LABEL, ZONE, POSITION = (
    "result",
    "color",
    "point_size",
    "point_shape",
    "label",
    "zone",
    "position",
)
shots = df.copy()
shots[RESULT] = np.where(made, "Made", "Missed")
shots[COLOR] = np.where(made, MADE_COLOR, MISSED_COLOR)
shots[SIZE] = np.where(made, MADE_SIZE, MISSED_SIZE)
shots[SHAPE] = np.where(made, CIRCLE_SHAPE, CROSS_SHAPE)  # circle vs X
shots[ZONE] = zone
shots[POSITION] = [f"({px:.1f}, {py:.1f})" for px, py in zip(df[X], df[Y], strict=True)]
shots_made = shots[shots[MADE]]

zone_rows = []
for z in ZONE_ORDER:
    in_zone = zone == z
    if in_zone.any():
        pct = made[in_zone].sum() / in_zone.sum() * 100
        zone_rows.append(
            {
                X: ZONE_LABEL_POS[z][0],
                Y: ZONE_LABEL_POS[z][1],
                LABEL: f"{ZONE_LABELS[z]}\n{pct:.0f}% ({int(in_zone.sum())})",
            }
        )
zone_annotations = pd.DataFrame(zone_rows)

# Court geometry
# The arc runs from the right corner sideline over the top to the left one
theta_corner = np.arccos(CORNER_THREE_X / THREE_PT_RADIUS)
theta_three = np.linspace(theta_corner, np.pi - theta_corner, 100)
three_arc = pd.DataFrame({X: THREE_PT_RADIUS * np.cos(theta_three), Y: THREE_PT_RADIUS * np.sin(theta_three)})
theta_upper = np.linspace(0, np.pi, 60)
ft_arc = pd.DataFrame(
    {X: FREE_THROW_RADIUS * np.cos(theta_upper), Y: FREE_THROW_Y + FREE_THROW_RADIUS * np.sin(theta_upper)}
)
theta_lower = np.linspace(np.pi, 2 * np.pi, 60)
ft_dash = pd.DataFrame(
    {X: FREE_THROW_RADIUS * np.cos(theta_lower), Y: FREE_THROW_Y + FREE_THROW_RADIUS * np.sin(theta_lower)}
)
theta_restricted = np.linspace(0, np.pi, 40)
restricted = pd.DataFrame(
    {X: RESTRICTED_RADIUS * np.cos(theta_restricted), Y: RESTRICTED_RADIUS * np.sin(theta_restricted)}
)

XMIN, YMIN, XMAX, YMAX = "xmin", "ymin", "xmax", "ymax"
XEND, YEND = "xend", "yend"
PAD_X, PAD_BOTTOM, PAD_TOP = 3, 10, 2
page_rect = pd.DataFrame(
    {
        XMIN: [-COURT_HALF_WIDTH - PAD_X],
        YMIN: [-PAD_BOTTOM],
        XMAX: [COURT_HALF_WIDTH + PAD_X],
        YMAX: [COURT_DEPTH + PAD_TOP],
    }
)
court_rect = pd.DataFrame({XMIN: [-COURT_HALF_WIDTH], YMIN: [-2], XMAX: [COURT_HALF_WIDTH], YMAX: [COURT_DEPTH]})
paint_rect = pd.DataFrame({XMIN: [-PAINT_HALF_WIDTH], YMIN: [0], XMAX: [PAINT_HALF_WIDTH], YMAX: [19]})
arc_join_y = THREE_PT_RADIUS * np.sin(theta_corner)  # where the arc meets the corner sidelines
corner_lines = pd.DataFrame(
    {
        X: [-CORNER_THREE_X, CORNER_THREE_X],
        Y: [0, 0],
        XEND: [-CORNER_THREE_X, CORNER_THREE_X],
        YEND: [arc_join_y, arc_join_y],
    }
)
backboard = pd.DataFrame({X: [-3], Y: [BACKBOARD_Y], XEND: [3], YEND: [BACKBOARD_Y]})
rim = pd.DataFrame({X: [0], Y: [RIM_Y]})

# Manual legend below the court
legend_y = -6.5
legend_marks = pd.DataFrame(
    {X: [-16.0, 7.0], Y: [legend_y, legend_y], COLOR: [MADE_COLOR, MISSED_COLOR], SHAPE: [CIRCLE_SHAPE, CROSS_SHAPE]}
)
legend_text = pd.DataFrame(
    {X: [-13.5, 9.5], Y: [legend_y, legend_y], LABEL: [f"Made ({n_made})", f"Missed ({n_missed})"]}
)
summary = pd.DataFrame({X: [0], Y: [COURT_DEPTH - 3], LABEL: [f"FG: {fg_percent:.1f}%  ·  {n_made}/{n_shots}"]})

# Title — 51 chars, under the 67-char baseline so size 16 fits
title = "scatter-shot-chart · python · letsplot · anyplot.ai"
title_size = round(16 * 67 / len(title)) if len(title) > 67 else 16

plot = (
    ggplot()
    # Outer background (page surface)
    + geom_rect(aes(xmin=XMIN, ymin=YMIN, xmax=XMAX, ymax=YMAX), data=page_rect, fill=PAGE_BG, color=PAGE_BG)
    # Court surface
    + geom_rect(
        aes(xmin=XMIN, ymin=YMIN, xmax=XMAX, ymax=YMAX), data=court_rect, fill=COURT_COLOR, color=LINE_COLOR, size=1.2
    )
    # Paint / key area
    + geom_rect(
        aes(xmin=XMIN, ymin=YMIN, xmax=XMAX, ymax=YMAX),
        data=paint_rect,
        fill="rgba(0,0,0,0)",
        color=LINE_COLOR,
        size=1.0,
    )
    # Corner three-point sidelines
    + geom_segment(aes(x=X, y=Y, xend=XEND, yend=YEND), data=corner_lines, color=LINE_COLOR, size=1.0)
    # Three-point arc
    + geom_path(data=three_arc, mapping=aes(x=X, y=Y), color=LINE_COLOR, size=1.0)
    # Free-throw circle (solid top, dashed bottom)
    + geom_path(data=ft_arc, mapping=aes(x=X, y=Y), color=LINE_COLOR, size=1.0)
    + geom_path(data=ft_dash, mapping=aes(x=X, y=Y), color=LINE_COLOR, size=0.6, linetype="dashed")
    # Restricted area arc
    + geom_path(data=restricted, mapping=aes(x=X, y=Y), color=LINE_COLOR, size=1.0)
    # Backboard
    + geom_segment(aes(x=X, y=Y, xend=XEND, yend=YEND), data=backboard, color=LINE_COLOR, size=2.0)
    # Rim
    + geom_point(aes(x=X, y=Y), data=rim, color=LINE_COLOR, size=3, shape=1)
    # Density contours for made shots — shows hot zones
    + geom_density2d(
        data=shots_made, mapping=aes(x=X, y=Y), color=MADE_COLOR, alpha=0.3, size=0.7, bins=6, show_legend=False
    )
    # Shot data with lets-plot interactive tooltips
    + geom_point(
        data=shots,
        mapping=aes(x=X, y=Y, color=COLOR, fill=COLOR, size=SIZE, shape=SHAPE),
        stroke=0.3,
        alpha=0.5,
        tooltips=layer_tooltips()
        .line(f"@{RESULT} | @{SHOT_TYPE}")
        .line(f"Zone: @{ZONE}")
        .line(f"Position: @{POSITION}"),
    )
    # Zone FG% annotations — positioned in sparse court areas to minimize overlap
    + geom_text(
        data=zone_annotations,
        mapping=aes(x=X, y=Y, label=LABEL),
        size=10,
        color=INK,
        fontface="bold",
        label_padding=0.4,
        fill=ANNOTATION_BG,
        label_size=0,
    )
    # Overall FG% summary
    + geom_text(data=summary, mapping=aes(x=X, y=Y, label=LABEL), size=13, color=INK, fontface="bold")
    # Legend markers and labels
    + geom_point(aes(x=X, y=Y, color=COLOR, fill=COLOR, shape=SHAPE), data=legend_marks, size=5, stroke=0.5)
    + geom_text(data=legend_text, mapping=aes(x=X, y=Y, label=LABEL), size=12, color=INK_SOFT, hjust=0)
    + scale_color_identity()
    + scale_fill_identity()
    + scale_size_identity()
    + scale_shape_identity()
    + scale_alpha_identity()
    + coord_fixed(ratio=1)
    + xlim(-COURT_HALF_WIDTH - PAD_X, COURT_HALF_WIDTH + PAD_X)
    + ylim(-PAD_BOTTOM, COURT_DEPTH + PAD_TOP)
    + labs(title=title)
    + theme_void()
    + theme(
        plot_title=element_text(size=title_size, hjust=0.5, color=INK, face="bold"),
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        plot_margin=[30, 15, 10, 15],
    )
    + ggsize(600, 600)
)
# The fixed aspect leaves the canvas edges transparent: a one-panel grid paints them in the page color
plot = gggrid([plot]) + ggsize(600, 600) + theme(plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG))

# Save — square canvas: ggsize(600, 600) × scale=4 → 2400×2400 px
ggsave(plot, f"plot-{THEME}.png", path=".", scale=4)
ggsave(plot, f"plot-{THEME}.html", path=".")
