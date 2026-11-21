"""anyplot.ai
venn-basic: Venn Diagram
Library: plotnine 0.15.4 | Python 3.13.13
Quality: pending | Updated: 2026-05-11
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
    labs,
    scale_fill_manual,
    scale_x_continuous,
    scale_y_continuous,
    theme,
)


THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Constants
CIRCLE_POINTS = 200
TRIPLE_OVERLAP = 10  # inclusive size of A∩B∩C
POS_X, POS_Y, TEXT, GROUP = "x", "y", "label", "set"  # columns of the derived drawing tables

# Columns
SET_LABELS = "set_labels"  # role: set_labels
SET_SIZES = "set_sizes"  # role: set_sizes
PAIR_OVERLAP = "pair_overlap"  # role: intersections

# Data: team skills; one row per set with its total size, the inclusive size of
# its overlap with the next set (A∩B, B∩C, C∩A) and the inclusive triple overlap.
df = pd.DataFrame(
    {
        SET_LABELS: ["Python Developers", "Data Scientists", "ML Engineers"],
        SET_SIZES: [100, 80, 60],
        PAIR_OVERLAP: [30, 25, 20],
    }
)

# Plot
# Exclusive count of each of the seven regions from the inclusive sizes
sizes = df[SET_SIZES].to_numpy(dtype=float)
ab, bc, ca = df[PAIR_OVERLAP].to_numpy(dtype=float)
abc = float(TRIPLE_OVERLAP)
region_counts = {
    (1, 0, 0): sizes[0] - ab - ca + abc,
    (0, 1, 0): sizes[1] - ab - bc + abc,
    (0, 0, 1): sizes[2] - bc - ca + abc,
    (1, 1, 0): ab - abc,
    (0, 1, 1): bc - abc,
    (1, 0, 1): ca - abc,
    (1, 1, 1): abc,
}

# Circle radii: area proportional to set size
radii = np.sqrt(sizes / np.pi)


def lens_area(r1, r2, d):
    """Area of the intersection of two circles with centres d apart."""
    if d >= r1 + r2:
        return 0.0
    if d <= abs(r1 - r2):
        return np.pi * min(r1, r2) ** 2
    a1 = np.arccos((d**2 + r1**2 - r2**2) / (2 * d * r1))
    a2 = np.arccos((d**2 + r2**2 - r1**2) / (2 * d * r2))
    return r1**2 * a1 + r2**2 * a2 - 0.5 * np.sqrt((-d + r1 + r2) * (d + r1 - r2) * (d - r1 + r2) * (d + r1 + r2))


def distance_for_overlap(r1, r2, target):
    """Centre distance at which two circles overlap by the target area."""
    lo, hi = abs(r1 - r2), r1 + r2
    for _ in range(60):
        mid = (lo + hi) / 2
        if lens_area(r1, r2, mid) > target:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


# Pairwise centre distances give the layout: A at origin, B on the x axis, C by triangulation
d_ab = distance_for_overlap(radii[0], radii[1], ab)
d_bc = distance_for_overlap(radii[1], radii[2], bc)
d_ca = distance_for_overlap(radii[2], radii[0], ca)
cx_c = (d_ca**2 - d_bc**2 + d_ab**2) / (2 * d_ab)
cy_c = -np.sqrt(max(d_ca**2 - cx_c**2, 0.0))
centers = np.array([[0.0, 0.0], [d_ab, 0.0], [cx_c, cy_c]])
centers = centers - centers.mean(axis=0)
set_names = df[SET_LABELS].tolist()

# Circle outlines as polygons
angles = np.linspace(0, 2 * np.pi, CIRCLE_POINTS + 1)
circle_df = pd.concat(
    [
        pd.DataFrame(
            {
                POS_X: centers[i, 0] + radii[i] * np.cos(angles),
                POS_Y: centers[i, 1] + radii[i] * np.sin(angles),
                GROUP: set_names[i],
            }
        )
        for i in range(len(df))
    ],
    ignore_index=True,
)

# Region label anchor: the point inside each region farthest from every circle edge
lim = (radii.max() + np.abs(centers).max()) * 1.05
gx, gy = np.meshgrid(np.linspace(-lim, lim, 500), np.linspace(-lim, lim, 500))
dist = np.stack([np.hypot(gx - centers[i, 0], gy - centers[i, 1]) for i in range(len(df))])
inside = dist < radii[:, None, None]
edge_gap = np.abs(dist - radii[:, None, None]).min(axis=0)
label_rows = []
for membership, count in region_counts.items():
    mask = np.ones_like(gx, dtype=bool)
    for i, member in enumerate(membership):
        mask &= inside[i] if member else ~inside[i]
    score = np.where(mask, edge_gap, -1.0)
    row, col = np.unravel_index(score.argmax(), score.shape)
    label_rows.append({POS_X: gx[row, col], POS_Y: gy[row, col], TEXT: str(int(count))})
count_labels_df = pd.DataFrame(label_rows)

# Set names just above (A, B) or below (C) each circle
set_rows = []
for i in range(len(df)):
    side = 1.0 if i < 2 else -1.0  # sets A and B above their circles, C below
    anchor = centers[i] + np.array([0.0, side * (radii[i] + 0.35 * radii.max())])
    set_rows.append({POS_X: anchor[0], POS_Y: anchor[1], TEXT: set_names[i].replace(" ", "\n")})
set_name_df = pd.DataFrame(set_rows)

plot = (
    ggplot()
    + geom_polygon(aes(x=POS_X, y=POS_Y, fill=GROUP, group=GROUP), data=circle_df, alpha=0.45, color=INK_SOFT, size=1.0)
    + geom_text(aes(x=POS_X, y=POS_Y, label=TEXT), data=count_labels_df, size=18, fontweight="bold", color=INK)
    + geom_text(aes(x=POS_X, y=POS_Y, label=TEXT), data=set_name_df, size=13, fontweight="bold", color=INK_SOFT)
    + scale_fill_manual(values=IMPRINT_PALETTE, limits=set_names)
    + scale_x_continuous(limits=(-lim * 1.2, lim * 1.2))
    + scale_y_continuous(limits=(-lim * 1.2, lim * 1.2))
    + coord_fixed()
    + labs(title="venn-basic · python · plotnine · anyplot.ai")
    + theme(
        figure_size=(6, 6),
        plot_title=element_text(size=12, ha="center", color=INK),
        axis_title=element_blank(),
        axis_text=element_blank(),
        axis_ticks=element_blank(),
        axis_line=element_blank(),
        panel_grid_major=element_blank(),
        panel_grid_minor=element_blank(),
        panel_background=element_rect(fill=PAGE_BG, color=None),
        plot_background=element_rect(fill=PAGE_BG, color=None),
        legend_position="none",
    )
)

# Save
plot.save(f"plot-{THEME}.png", dpi=400, width=6, height=6, units="in")
