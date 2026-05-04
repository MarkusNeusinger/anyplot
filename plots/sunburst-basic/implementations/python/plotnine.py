"""anyplot.ai
sunburst-basic: Basic Sunburst Chart
Library: plotnine 0.15.3 | Python 3.13.13
Quality: 85/100 | Created: 2026-05-04
"""

import sys


sys.path.pop(0)  # prevent this file from shadowing the installed plotnine package

import os

import numpy as np
import pandas as pd
from plotnine import (
    aes,
    coord_equal,
    element_blank,
    element_rect,
    element_text,
    geom_polygon,
    geom_text,
    ggplot,
    labs,
    scale_fill_identity,
    scale_x_continuous,
    scale_y_continuous,
    theme,
)


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
# Slightly lighter than PAGE_BG in dark mode so ring boundaries remain visible
RING_SEP = PAGE_BG if THEME == "light" else "#2E2D2B"

OKABE_ITO = ["#009E73", "#D55E00", "#0072B2", "#CC79A7"]

# Data: company annual budget by department → team ($M)
hierarchy = {
    "Engineering": {"Frontend": 15, "Backend": 15, "DevOps": 10},
    "Marketing": {"Digital": 10, "Brand": 8, "Events": 7},
    "Operations": {"HR": 8, "Finance": 7, "Legal": 5},
    "R&D": {"Product": 8, "Data Science": 7},
}

total = sum(sum(v.values()) for v in hierarchy.values())

# Ring radii
R_INNER_L1, R_OUTER_L1 = 0.35, 0.65
R_INNER_L2, R_OUTER_L2 = 0.67, 0.95
N_PTS = 80  # arc resolution

l1_rows, l2_rows, label_rows = [], [], []
cumsum = 0

for idx, (dept, teams) in enumerate(hierarchy.items()):
    dept_total = sum(teams.values())
    pct = round(dept_total / total * 100)
    a0 = 2 * np.pi * cumsum / total - np.pi / 2
    a1 = 2 * np.pi * (cumsum + dept_total) / total - np.pi / 2
    color = OKABE_ITO[idx]

    # L1 arc polygon: inner arc → outer arc (reversed) → closed shape
    t = np.linspace(a0, a1, N_PTS)
    xs = np.concatenate([R_INNER_L1 * np.cos(t), R_OUTER_L1 * np.cos(t[::-1])])
    ys = np.concatenate([R_INNER_L1 * np.sin(t), R_OUTER_L1 * np.sin(t[::-1])])
    for xi, yi in zip(xs, ys, strict=False):
        l1_rows.append({"x": xi, "y": yi, "group": dept, "fill": color})

    # L1 department name: outer half of inner ring
    a_mid = (a0 + a1) / 2
    r_name = 0.54
    label_rows.append({"x": r_name * np.cos(a_mid), "y": r_name * np.sin(a_mid), "label": dept, "level": 1})
    # Percentage annotation: inner half of inner ring
    r_pct = 0.44
    label_rows.append({"x": r_pct * np.cos(a_mid), "y": r_pct * np.sin(a_mid), "label": f"{pct}%", "level": 3})

    # L2 arc polygons (sub-departments)
    team_cumsum = cumsum
    for t_idx, (team, budget) in enumerate(teams.items()):
        b0 = 2 * np.pi * team_cumsum / total - np.pi / 2
        b1 = 2 * np.pi * (team_cumsum + budget) / total - np.pi / 2

        t2 = np.linspace(b0, b1, N_PTS)
        xs2 = np.concatenate([R_INNER_L2 * np.cos(t2), R_OUTER_L2 * np.cos(t2[::-1])])
        ys2 = np.concatenate([R_INNER_L2 * np.sin(t2), R_OUTER_L2 * np.sin(t2[::-1])])
        grp = f"{dept}_{t_idx}"
        for xi, yi in zip(xs2, ys2, strict=False):
            l2_rows.append({"x": xi, "y": yi, "group": grp, "fill": color})

        # Only label segments wide enough to hold text (≥8% share)
        if budget / total >= 0.08:
            b_mid = (b0 + b1) / 2
            r_mid2 = (R_INNER_L2 + R_OUTER_L2) / 2
            label_rows.append({"x": r_mid2 * np.cos(b_mid), "y": r_mid2 * np.sin(b_mid), "label": team, "level": 2})

        team_cumsum += budget
    cumsum += dept_total

df_l1 = pd.DataFrame(l1_rows)
df_l2 = pd.DataFrame(l2_rows)
df_labels = pd.DataFrame(label_rows)
df_l1_labels = df_labels[df_labels["level"] == 1]
df_l2_labels = df_labels[df_labels["level"] == 2]
df_pct_labels = df_labels[df_labels["level"] == 3]

# Plot
plot = (
    ggplot()
    + geom_polygon(data=df_l1, mapping=aes(x="x", y="y", group="group", fill="fill"), color=RING_SEP, size=1.5)
    + geom_polygon(
        data=df_l2, mapping=aes(x="x", y="y", group="group", fill="fill"), color=RING_SEP, size=0.8, alpha=0.65
    )
    + geom_text(
        data=df_l1_labels,
        mapping=aes(x="x", y="y", label="label"),
        color=INK,
        size=16,
        fontweight="bold",
        ha="center",
        va="center",
    )
    + geom_text(
        data=df_pct_labels, mapping=aes(x="x", y="y", label="label"), color=INK_SOFT, size=13, ha="center", va="center"
    )
    + geom_text(
        data=df_l2_labels, mapping=aes(x="x", y="y", label="label"), color=INK, size=16, ha="center", va="center"
    )
    + scale_fill_identity()
    + coord_equal()
    + scale_x_continuous(limits=(-1.15, 1.15), breaks=[], expand=(0, 0))
    + scale_y_continuous(limits=(-1.15, 1.15), breaks=[], expand=(0, 0))
    + labs(title="sunburst-basic · plotnine · anyplot.ai")
    + theme(
        figure_size=(12, 12),
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG),
        panel_grid_major=element_blank(),
        panel_grid_minor=element_blank(),
        panel_border=element_blank(),
        axis_title=element_blank(),
        axis_text=element_blank(),
        axis_ticks_major_x=element_blank(),
        axis_ticks_major_y=element_blank(),
        axis_ticks_minor_x=element_blank(),
        axis_ticks_minor_y=element_blank(),
        legend_position="none",
        plot_title=element_text(color=INK, size=24, ha="center"),
    )
)

plot.save(f"plot-{THEME}.png", dpi=300, verbose=False)
