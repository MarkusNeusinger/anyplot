""" anyplot.ai
maze-circular: Circular Maze Puzzle
Library: plotnine 0.15.4 | Python 3.13.13
Quality: 88/100 | Updated: 2026-05-20
"""

import os

import numpy as np
import pandas as pd
from plotnine import (
    aes,
    coord_fixed,
    element_rect,
    element_text,
    geom_point,
    geom_segment,
    geom_text,
    ggplot,
    labs,
    theme,
    theme_void,
)


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
GOAL_COLOR = "#009E73"  # Okabe-Ito position 1

# Maze parameters — difficulty controls ring count and complexity
np.random.seed(42)
difficulty = "medium"
n_rings = {"easy": 5, "medium": 7, "hard": 9}[difficulty]
base_sectors = [1, 6, 12, 18, 24, 30, 36, 42, 48, 54]
sectors_per_ring = base_sectors[: n_rings + 1]
ring_width = 1.0
radii = [i * ring_width for i in range(n_rings + 2)]

# Initialize maze walls
radial_walls = []
arc_walls = []
for ring in range(n_rings + 1):
    n_sec = sectors_per_ring[min(ring, len(sectors_per_ring) - 1)]
    radial_walls.append([True] * n_sec)
    arc_walls.append([True] * n_sec)


def get_neighbors(ring, sector):
    n_cur = sectors_per_ring[min(ring, len(sectors_per_ring) - 1)]
    neighbors = [(ring, (sector - 1) % n_cur, "radial_prev"), (ring, (sector + 1) % n_cur, "radial_next")]
    if ring > 0:
        n_inn = sectors_per_ring[min(ring - 1, len(sectors_per_ring) - 1)]
        neighbors.append((ring - 1, int(sector * n_inn / n_cur), "arc_inner"))
    if ring < n_rings:
        n_out = sectors_per_ring[min(ring + 1, len(sectors_per_ring) - 1)]
        s0 = int(sector * n_out / n_cur)
        s1 = int((sector + 1) * n_out / n_cur)
        for s in range(s0, s1):
            neighbors.append((ring + 1, s % n_out, "arc_outer"))
    return neighbors


# DFS maze generation from center
visited = {(0, 0)}
stack = [(0, 0)]
while stack:
    ring, sector = stack[-1]
    n_sec = sectors_per_ring[min(ring, len(sectors_per_ring) - 1)]
    unvisited = [(nr, ns, wt) for nr, ns, wt in get_neighbors(ring, sector) if (nr, ns) not in visited]
    if unvisited:
        nr, ns, wt = unvisited[np.random.randint(len(unvisited))]
        if wt == "radial_prev":
            radial_walls[ring][sector] = False
        elif wt == "radial_next":
            radial_walls[ring][(sector + 1) % n_sec] = False
        elif wt == "arc_inner":
            arc_walls[ring - 1][ns] = False
        else:
            arc_walls[ring][sector] = False
        visited.add((nr, ns))
        stack.append((nr, ns))
    else:
        stack.pop()

# Entry gap on outer ring (sector 0 — rightmost)
n_outer = sectors_per_ring[min(n_rings, len(sectors_per_ring) - 1)]
entry_sector = 0
entry_angle_0 = 2 * np.pi * entry_sector / n_outer
gap_half = np.pi / n_outer * 1.2  # 1.2× sector half-width for a prominent entry gap

# Build wall segments
segments = []

# Outer boundary with prominent entry gap
n_pts = 300
for i in range(n_pts):
    t1 = 2 * np.pi * i / n_pts
    t2 = 2 * np.pi * (i + 1) / n_pts
    t_mid = (t1 + t2) / 2
    if abs(t_mid - entry_angle_0) > gap_half and abs(t_mid - entry_angle_0 - 2 * np.pi) > gap_half:
        r = radii[n_rings + 1]
        segments.append({"x": r * np.cos(t1), "y": r * np.sin(t1), "xend": r * np.cos(t2), "yend": r * np.sin(t2)})

# Arc walls between rings
for ring in range(n_rings):
    n_sec = sectors_per_ring[min(ring, len(sectors_per_ring) - 1)]
    r = radii[ring + 1]
    for sec in range(n_sec):
        if arc_walls[ring][sec]:
            t1 = 2 * np.pi * sec / n_sec
            t2 = 2 * np.pi * (sec + 1) / n_sec
            n_sub = max(3, int(120 / n_sec))
            for j in range(n_sub):
                ta = t1 + (t2 - t1) * j / n_sub
                tb = t1 + (t2 - t1) * (j + 1) / n_sub
                segments.append(
                    {"x": r * np.cos(ta), "y": r * np.sin(ta), "xend": r * np.cos(tb), "yend": r * np.sin(tb)}
                )

# Radial walls within each ring
for ring in range(n_rings + 1):
    n_sec = sectors_per_ring[min(ring, len(sectors_per_ring) - 1)]
    r_in, r_out = radii[ring], radii[ring + 1]
    for sec in range(n_sec):
        if radial_walls[ring][sec]:
            t = 2 * np.pi * sec / n_sec
            segments.append(
                {"x": r_in * np.cos(t), "y": r_in * np.sin(t), "xend": r_out * np.cos(t), "yend": r_out * np.sin(t)}
            )

walls_df = pd.DataFrame(segments)

# Entry and goal markers
entry_angle_mid = 2 * np.pi * (entry_sector + 0.5) / n_outer
entry_r = radii[n_rings + 1] + ring_width * 0.7
entry_df = pd.DataFrame(
    {"x": [entry_r * np.cos(entry_angle_mid)], "y": [entry_r * np.sin(entry_angle_mid)], "label": ["START"]}
)
goal_df = pd.DataFrame({"x": [0.0], "y": [0.0], "label": ["GOAL"]})

# Plot
plot = (
    ggplot()
    + geom_segment(data=walls_df, mapping=aes(x="x", y="y", xend="xend", yend="yend"), color=INK, size=0.7)
    + geom_point(data=goal_df, mapping=aes(x="x", y="y"), color=GOAL_COLOR, size=4)
    + geom_text(
        data=goal_df,
        mapping=aes(x="x", y="y", label="label"),
        color=GOAL_COLOR,
        size=9,
        fontweight="bold",
        nudge_y=0.55,
    )
    + geom_text(data=entry_df, mapping=aes(x="x", y="y", label="label"), color=INK_SOFT, size=9, fontweight="bold")
    + coord_fixed(ratio=1)
    + labs(title="maze-circular · python · plotnine · anyplot.ai")
    + theme_void()
    + theme(
        figure_size=(6, 6),
        plot_title=element_text(size=12, ha="center", weight="bold", color=INK),
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG),
    )
)

# Save
plot.save(f"plot-{THEME}.png", dpi=400, width=6, height=6, units="in")
