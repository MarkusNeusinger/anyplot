"""anyplot.ai
scatter-pitch-events: Soccer Pitch Event Map
Library: letsplot 4.10.1 | Python 3.13.14
Quality: 87/100 | Updated: 2026-06-21
"""

import os

import numpy as np
import pandas as pd
from lets_plot import (
    LetsPlot,
    aes,
    arrow,
    coord_fixed,
    element_rect,
    element_text,
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

# Theme tokens (Imprint palette, theme-adaptive chrome)
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Pitch color is data context: it stays constant across themes
PITCH_GREEN = "#1A5C2A"  # darker forest green keeps #009E73 markers visually distinct
PITCH_LINE = "#FFFFFF"

# Imprint palette (canonical order): one position per event type
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Constants: the FIFA pitch and the event vocabulary hold for any match data
PITCH_LENGTH, PITCH_WIDTH = 105.0, 68.0  # meters
EVENT_ORDER = ["Pass", "Shot", "Tackle", "Interception"]  # palette position follows this order
MARKER_SHAPES = [21, 23, 24, 22, 25, 21, 23, 24]  # circle, diamond, triangle, square, ...
SUCCESS = "Successful"  # outcome value drawn as a filled, opaque marker
ARROW_EVENTS = ["Pass", "Shot"]  # events drawn with a direction arrow
EMPHASIS_EVENT = "Shot"  # drawn larger for tactical emphasis

# Columns: set these to your table's column names
X = "x"  # role: x
Y = "y"  # role: y
EVENT_TYPE = "event_type"  # role: event_type
OUTCOME = "outcome"  # role: outcome
END_X = "end_x"  # role: end_x
END_Y = "end_y"  # role: end_y

# Data: replace this block with your own table, for example df = pd.read_csv("events.csv")
np.random.seed(42)
n_events = 100
event_types = np.random.choice(["Pass", "Shot", "Tackle", "Interception"], size=n_events, p=[0.45, 0.15, 0.22, 0.18])
success_rates = {"Pass": 0.78, "Shot": 0.30, "Tackle": 0.60, "Interception": 0.70}
outcomes = [
    np.random.choice(["Successful", "Unsuccessful"], p=[success_rates[et], 1 - success_rates[et]]) for et in event_types
]

x_pos, y_pos, x_end, y_end = [], [], [], []
for et in event_types:
    if et == "Pass":
        x = np.random.uniform(10, 95)
        y = np.random.uniform(5, 63)
        dx = np.random.uniform(5, 25) * np.random.choice([-1, 1], p=[0.2, 0.8])
        dy = np.random.uniform(-15, 15)
        xe, ye = np.clip(x + dx, 0, 105), np.clip(y + dy, 0, 68)
    elif et == "Shot":
        x = np.random.uniform(55, 100)
        y = np.random.uniform(10, 58)
        xe, ye = 105.0, np.random.uniform(28, 40)
    else:
        x = np.random.uniform(15, 85)
        y = np.random.uniform(5, 63)
        xe, ye = np.nan, np.nan  # tackles and interceptions have no end position
    x_pos.append(x)
    y_pos.append(y)
    x_end.append(xe)
    y_end.append(ye)

df = pd.DataFrame({X: x_pos, Y: y_pos, END_X: x_end, END_Y: y_end, EVENT_TYPE: event_types, OUTCOME: outcomes})

# Plot: reads only df and the constants above
# Names of the pitch-drawing columns, which are not data columns
PX, PY, PXE, PYE = "px", "py", "pxend", "pyend"

# Event styling: palette position, shape and size per event type, in the order of EVENT_ORDER
types = list(dict.fromkeys(EVENT_ORDER + df[EVENT_TYPE].dropna().unique().tolist()))
color_map = {t: IMPRINT_PALETTE[i % len(IMPRINT_PALETTE)] for i, t in enumerate(types)}
shape_map = {t: MARKER_SHAPES[i % len(MARKER_SHAPES)] for i, t in enumerate(types)}
present = [t for t in types if (df[EVENT_TYPE] == t).any()]

events = df.copy()
events["color"] = events[EVENT_TYPE].map(color_map)
events["shape"] = events[EVENT_TYPE].map(shape_map)
successful = (events[OUTCOME] == SUCCESS).fillna(False).to_numpy(dtype=bool)
# Outcome encoding: successful = opaque colored fill, unsuccessful = white fill at 0.42 alpha
events["alpha"] = np.where(successful, 1.0, 0.42)
events["fill"] = np.where(successful, events["color"], "#FFFFFF")
events["marker_size"] = np.where(events[EVENT_TYPE] == EMPHASIS_EVENT, 4.5, 3.0)
arrows = events[events[EVENT_TYPE].isin(ARROW_EVENTS) & events[END_X].notna() & events[END_Y].notna()]

# Pitch geometry from the FIFA dimensions
L, W = PITCH_LENGTH, PITCH_WIDTH
MID_Y = W / 2
CIRCLE_R = 9.15
SPOT = 11.0
PENALTY_DEPTH, PENALTY_HALF = 16.5, 20.16
GOAL_AREA_DEPTH, GOAL_AREA_HALF = 5.5, 9.16
GOAL_HALF = 3.66

theta = np.linspace(0, 2 * np.pi, 80)
df_center_circle = pd.DataFrame({PX: L / 2 + CIRCLE_R * np.cos(theta), PY: MID_Y + CIRCLE_R * np.sin(theta)})

theta_l = np.linspace(-np.pi / 2, np.pi / 2, 40)
arc_lx = SPOT + CIRCLE_R * np.cos(theta_l)
arc_ly = MID_Y + CIRCLE_R * np.sin(theta_l)
df_left_arc = pd.DataFrame({PX: arc_lx[arc_lx >= PENALTY_DEPTH], PY: arc_ly[arc_lx >= PENALTY_DEPTH]})

theta_r = np.linspace(np.pi / 2, 3 * np.pi / 2, 40)
arc_rx = (L - SPOT) + CIRCLE_R * np.cos(theta_r)
arc_ry = MID_Y + CIRCLE_R * np.sin(theta_r)
df_right_arc = pd.DataFrame({PX: arc_rx[arc_rx <= L - PENALTY_DEPTH], PY: arc_ry[arc_rx <= L - PENALTY_DEPTH]})

corner_arcs = []
for cx, cy, t0, t1 in [
    (0, 0, 0, np.pi / 2),
    (0, W, -np.pi / 2, 0),
    (L, 0, np.pi / 2, np.pi),
    (L, W, np.pi, 3 * np.pi / 2),
]:
    t = np.linspace(t0, t1, 20)
    corner_arcs.append(pd.DataFrame({PX: cx + np.cos(t), PY: cy + np.sin(t)}))

df_rects = pd.DataFrame(
    {
        "xmin": [0, 0, 0, L - PENALTY_DEPTH, L - GOAL_AREA_DEPTH],
        "ymin": [0, MID_Y - PENALTY_HALF, MID_Y - GOAL_AREA_HALF, MID_Y - PENALTY_HALF, MID_Y - GOAL_AREA_HALF],
        "xmax": [L, PENALTY_DEPTH, GOAL_AREA_DEPTH, L, L],
        "ymax": [W, MID_Y + PENALTY_HALF, MID_Y + GOAL_AREA_HALF, MID_Y + PENALTY_HALF, MID_Y + GOAL_AREA_HALF],
    }
)
df_halfway = pd.DataFrame({PX: [L / 2], PY: [0], PXE: [L / 2], PYE: [W]})
df_goals = pd.DataFrame({PX: [0, L], PY: [MID_Y - GOAL_HALF] * 2, PXE: [0, L], PYE: [MID_Y + GOAL_HALF] * 2})
df_spots = pd.DataFrame({PX: [L / 2, SPOT, L - SPOT], PY: [MID_Y] * 3})
df_surface = pd.DataFrame({"xmin": [-4], "ymin": [-4], "xmax": [L + 4], "ymax": [W + 4]})

# Thirds of the pitch, lightly shaded: attacking lighter, defensive darker
df_attack_zone = pd.DataFrame({"xmin": [L * 2 / 3], "ymin": [0], "xmax": [L], "ymax": [W]})
df_defend_zone = pd.DataFrame({"xmin": [0], "ymin": [0], "xmax": [L / 3], "ymax": [W]})
df_zone_labels = pd.DataFrame(
    {PX: [L * 5 / 6, L / 6], PY: [W - 2.5] * 2, "label": ["Attacking Third", "Defensive Third"], "alpha": [0.7, 0.65]}
)

# Custom legend below the pitch, one entry per event type present
legend_x = np.linspace(L * 0.115, L * 0.83, len(present))
df_legend_markers = pd.DataFrame(
    {
        PX: legend_x,
        PY: -8.0,
        "color": [color_map[t] for t in present],
        "shape": [shape_map[t] for t in present],
        "fill": [color_map[t] for t in present],
    }
)
df_legend_labels = pd.DataFrame({PX: legend_x, PY: -12.5, "label": present})
df_outcome_text = pd.DataFrame(
    {
        PX: [L * 0.27, L * 0.74],
        PY: [-17.0, -17.0],
        "label": ["● Colored fill = Successful", "○ White fill = Unsuccessful"],
    }
)

plot = (
    ggplot()
    # Pitch surface
    + geom_rect(
        aes(xmin="xmin", ymin="ymin", xmax="xmax", ymax="ymax"), data=df_surface, fill=PITCH_GREEN, color=PITCH_GREEN
    )
    # Zone highlights
    + geom_rect(
        aes(xmin="xmin", ymin="ymin", xmax="xmax", ymax="ymax"),
        data=df_attack_zone,
        fill="#FFFFFF",
        color="rgba(0,0,0,0)",
        alpha=0.15,
    )
    + geom_rect(
        aes(xmin="xmin", ymin="ymin", xmax="xmax", ymax="ymax"),
        data=df_defend_zone,
        fill="#000000",
        color="rgba(0,0,0,0)",
        alpha=0.12,
    )
    # Pitch markings
    + geom_rect(
        aes(xmin="xmin", ymin="ymin", xmax="xmax", ymax="ymax"),
        data=df_rects,
        fill="rgba(0,0,0,0)",
        color=PITCH_LINE,
        size=0.8,
    )
    + geom_segment(aes(x=PX, y=PY, xend=PXE, yend=PYE), data=df_halfway, color=PITCH_LINE, size=0.8)
    + geom_segment(aes(x=PX, y=PY, xend=PXE, yend=PYE), data=df_goals, color="#DDDDDD", size=2.0)
    + geom_path(data=df_center_circle, mapping=aes(x=PX, y=PY), color=PITCH_LINE, size=0.8)
    + geom_path(data=df_left_arc, mapping=aes(x=PX, y=PY), color=PITCH_LINE, size=0.8)
    + geom_path(data=df_right_arc, mapping=aes(x=PX, y=PY), color=PITCH_LINE, size=0.8)
    + geom_path(data=corner_arcs[0], mapping=aes(x=PX, y=PY), color=PITCH_LINE, size=0.8)
    + geom_path(data=corner_arcs[1], mapping=aes(x=PX, y=PY), color=PITCH_LINE, size=0.8)
    + geom_path(data=corner_arcs[2], mapping=aes(x=PX, y=PY), color=PITCH_LINE, size=0.8)
    + geom_path(data=corner_arcs[3], mapping=aes(x=PX, y=PY), color=PITCH_LINE, size=0.8)
    + geom_point(aes(x=PX, y=PY), data=df_spots, color=PITCH_LINE, size=1.5)
    # Directional arrows for passes and shots
    + geom_segment(
        data=arrows,
        mapping=aes(x=X, y=Y, xend=END_X, yend=END_Y, color="color", alpha="alpha"),
        size=0.6,
        arrow=arrow(length=6, type="open"),
    )
    # Event markers (shots enlarged for tactical emphasis)
    + geom_point(
        data=events,
        mapping=aes(x=X, y=Y, color="color", fill="fill", shape="shape", alpha="alpha", size="marker_size"),
        stroke=1.2,
        tooltips=layer_tooltips()
        .line(f"@{{{EVENT_TYPE}}}")
        .line(f"Outcome: @{{{OUTCOME}}}")
        .line(f"{X}=@{{{X}}}, {Y}=@{{{Y}}}"),
    )
    # Zone annotation labels
    + geom_text(
        data=df_zone_labels,
        mapping=aes(x=PX, y=PY, label="label", alpha="alpha"),
        size=5,
        color="#FFFFFF",
        fontface="italic",
    )
    # Custom legend markers and labels
    + geom_point(
        data=df_legend_markers, mapping=aes(x=PX, y=PY, color="color", fill="fill", shape="shape"), size=3.5, stroke=1.0
    )
    + geom_text(data=df_legend_labels, mapping=aes(x=PX, y=PY, label="label"), size=5, color=INK_SOFT, fontface="bold")
    + geom_text(data=df_outcome_text, mapping=aes(x=PX, y=PY, label="label"), size=5, color=INK_MUTED)
    + scale_color_identity()
    + scale_fill_identity()
    + scale_shape_identity()
    + scale_alpha_identity()
    + scale_size_identity()
    + coord_fixed(ratio=1)
    + xlim(-5, L + 7)
    + ylim(-20, W + 8)
    + labs(
        title="scatter-pitch-events · python · letsplot · anyplot.ai",
        subtitle=f"{len(df)} match events — passes, shots, tackles & interceptions with outcome encoding",
    )
    + theme_void()
    + theme(
        plot_title=element_text(size=16, hjust=0.5, color=INK, face="bold"),
        plot_subtitle=element_text(size=10, hjust=0.5, color=INK_SOFT),
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        plot_margin=[25, 15, 10, 15],
    )
)

# The fixed aspect narrows the plot box; a one-panel grid paints the whole canvas with the page color
plot = gggrid([plot]) + ggsize(800, 450) + theme(plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG))

# Save PNG and HTML for this theme
ggsave(plot, f"plot-{THEME}.png", path=".", scale=4)
ggsave(plot, f"plot-{THEME}.html", path=".")
