"""anyplot.ai
circos-basic: Circos Plot
Library: plotnine 0.15.4 | Python 3.13.13
Quality: pending | Updated: 2026-05-15
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
    geom_polygon,
    geom_text,
    ggplot,
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
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: all eight positions, one per hub in order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Constants: ring geometry in unit-circle radii, angles in radians
GAP_ANGLE = 0.09  # empty wedge between neighbouring hubs
OUTER_R, INNER_R = 1.0, 0.92  # hub ring
RIBBON_R = 0.68  # ribbons end just inside the data track
TRACK_BASE, TRACK_SPAN = 0.74, 0.14  # data track: base radius and full-scale thickness
LABEL_R = 1.17
N_ARC = 60  # points per arc edge

# Columns: set these to your table's column names
ORIGIN = "Origin hub"  # role: source
DESTINATION = "Destination hub"  # role: target
PASSENGERS = "Weekly passengers (thousands)"  # role: value
LOAD_FACTOR = "Seats filled (%)"  # role: track_data

# Data: replace this block with your own table, for example df = pd.read_csv("routes.csv")
# Weekly passenger flows between eight airline hubs; the track is derived from the same table.
df = pd.DataFrame(
    {
        ORIGIN: [
            "Atlanta",
            "Atlanta",
            "Atlanta",
            "Atlanta",
            "Chicago",
            "Chicago",
            "Chicago",
            "Dallas",
            "Dallas",
            "Dallas",
            "Denver",
            "Denver",
            "Los Angeles",
            "Los Angeles",
            "Los Angeles",
            "New York",
            "New York",
            "New York",
            "Seattle",
            "Seattle",
            "Miami",
            "Miami",
        ],
        DESTINATION: [
            "New York",
            "Miami",
            "Chicago",
            "Dallas",
            "New York",
            "Denver",
            "Los Angeles",
            "Atlanta",
            "Los Angeles",
            "Denver",
            "Seattle",
            "Los Angeles",
            "Seattle",
            "New York",
            "Chicago",
            "Los Angeles",
            "Miami",
            "Atlanta",
            "Los Angeles",
            "Denver",
            "Atlanta",
            "New York",
        ],
        PASSENGERS: [92, 74, 58, 41, 80, 38, 66, 52, 60, 33, 28, 47, 36, 88, 49, 84, 70, 64, 25, 30, 55, 62],
        LOAD_FACTOR: [88, 91, 84, 79, 86, 72, 90, 81, 87, 70, 66, 78, 74, 93, 85, 92, 89, 90, 68, 71, 83, 88],
    }
)

# Plot: reads only df and the constants above
flows = df.dropna(subset=[PASSENGERS])
hubs = list(dict.fromkeys(flows[ORIGIN].tolist() + flows[DESTINATION].tolist()))
colors = {hub: IMPRINT_PALETTE[i % len(IMPRINT_PALETTE)] for i, hub in enumerate(hubs)}

sent = flows.groupby(ORIGIN)[PASSENGERS].sum().reindex(hubs).fillna(0.0)
received = flows.groupby(DESTINATION)[PASSENGERS].sum().reindex(hubs).fillna(0.0)
totals = sent + received

# Data track: passenger-weighted share of seats filled on a hub's routes (0-100 %)
weighted = flows[LOAD_FACTOR] * flows[PASSENGERS]
load_sum = weighted.groupby(flows[ORIGIN]).sum().reindex(hubs).fillna(0.0) + (
    weighted.groupby(flows[DESTINATION]).sum().reindex(hubs).fillna(0.0)
)
track_share = load_sum / totals / 100

# Arc of each hub proportional to its total traffic, separated by gaps
available = 2 * np.pi - GAP_ANGLE * len(hubs)
per_unit = available / totals.sum()
arcs = {}
cursor = np.pi / 2
for hub in hubs:
    span = totals[hub] * per_unit
    arcs[hub] = (cursor, cursor + span)
    cursor += span + GAP_ANGLE


def ring_sector(start, end, r_out, r_in):
    angles = np.linspace(start, end, N_ARC)
    return np.concatenate(
        [
            np.column_stack([r_out * np.cos(angles), r_out * np.sin(angles)]),
            np.column_stack([r_in * np.cos(angles[::-1]), r_in * np.sin(angles[::-1])]),
        ]
    )


ring_parts, track_bg_parts, track_val_parts, label_rows = [], [], [], []
for hub in hubs:
    start, end = arcs[hub]
    for parts, r_out, r_in in (
        (ring_parts, OUTER_R, INNER_R),
        (track_bg_parts, TRACK_BASE + TRACK_SPAN, TRACK_BASE),
        (track_val_parts, TRACK_BASE + TRACK_SPAN * track_share[hub], TRACK_BASE),
    ):
        xy = ring_sector(start, end, r_out, r_in)
        parts.append(pd.DataFrame({"x": xy[:, 0], "y": xy[:, 1], "hub": hub, "shape": f"{hub}"}))
    mid = (start + end) / 2
    label_rows.append({"x": LABEL_R * np.cos(mid), "y": LABEL_R * np.sin(mid), "label": hub, "hub": hub})

ring_df = pd.concat(ring_parts, ignore_index=True)
track_bg_df = pd.concat(track_bg_parts, ignore_index=True)
track_val_df = pd.concat(track_val_parts, ignore_index=True)
label_df = pd.DataFrame(label_rows)

# Ribbons: width at each end is the flow's share of the circle, anchored inside both hub arcs
offsets = {hub: arcs[hub][0] for hub in hubs}
ribbon_parts = []
u = np.linspace(0, 1, 40)[1:-1, None]
for k, (src, tgt, value) in enumerate(zip(flows[ORIGIN], flows[DESTINATION], flows[PASSENGERS], strict=True)):
    width = value * per_unit
    s0, s1 = offsets[src], offsets[src] + width
    offsets[src] = s1
    t0, t1 = offsets[tgt], offsets[tgt] + width
    offsets[tgt] = t1

    s_arc = np.linspace(s0, s1, 12)
    t_arc = np.linspace(t0, t1, 12)
    s_pts = RIBBON_R * np.column_stack([np.cos(s_arc), np.sin(s_arc)])
    t_pts = RIBBON_R * np.column_stack([np.cos(t_arc), np.sin(t_arc)])
    # quadratic Bezier with its control point at the circle centre, source end to target start and back
    out_curve = (1 - u) ** 2 * s_pts[-1] + u**2 * t_pts[0]
    back_curve = (1 - u) ** 2 * t_pts[-1] + u**2 * s_pts[0]
    poly = np.vstack([s_pts, out_curve, t_pts, back_curve])
    ribbon_parts.append(pd.DataFrame({"x": poly[:, 0], "y": poly[:, 1], "ribbon": f"r{k}", "hub": src}))

ribbon_df = pd.concat(ribbon_parts, ignore_index=True)

limit = LABEL_R + 0.3
title = "circos-basic · python · plotnine · anyplot.ai"
caption = (
    "Outer ring: hubs sized by total weekly passengers; ribbons: flows colored by origin, width = passengers\n"
    "Inner ring: share of seats filled on the hub's routes, passenger-weighted (full ring = 100%)"
)

plot = (
    ggplot()
    + geom_polygon(aes(x="x", y="y", group="ribbon", fill="hub"), data=ribbon_df, alpha=0.55, color=PAGE_BG, size=0.1)
    + geom_polygon(
        aes(x="x", y="y", group="shape"), data=track_bg_df, fill=INK_SOFT, alpha=0.15, color=PAGE_BG, size=0.2
    )
    + geom_polygon(aes(x="x", y="y", group="shape", fill="hub"), data=track_val_df, alpha=0.9, color=PAGE_BG, size=0.2)
    + geom_polygon(aes(x="x", y="y", group="shape", fill="hub"), data=ring_df, alpha=1.0, color=PAGE_BG, size=0.4)
    + geom_text(aes(x="x", y="y", label="label"), data=label_df, size=9, color=INK, fontweight="bold")
    + scale_fill_manual(values=colors, limits=hubs)
    + guides(fill=False)
    + coord_fixed(ratio=1)
    + scale_x_continuous(limits=(-limit, limit), expand=(0, 0))
    + scale_y_continuous(limits=(-limit, limit), expand=(0, 0))
    + labs(title=title, caption=caption)
    + theme(
        figure_size=(6, 6),
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        plot_title=element_text(size=14, ha="center", fontweight="bold", color=INK),
        plot_caption=element_text(size=8, ha="center", color=INK_SOFT, linespacing=1.4),
        plot_margin=0.03,
        axis_title=element_blank(),
        axis_text=element_blank(),
        axis_ticks=element_blank(),
        axis_line=element_blank(),
        panel_grid_major=element_blank(),
        panel_grid_minor=element_blank(),
        legend_position="none",
    )
)

plot.save(f"plot-{THEME}.png", dpi=400, width=6, height=6, units="in")
