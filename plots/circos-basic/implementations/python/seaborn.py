""" anyplot.ai
circos-basic: Circos Plot
Library: seaborn 0.13.2 | Python 3.14.10
Quality: 82/100 | Updated: 2026-11-21
"""

import os

import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from matplotlib.path import Path


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: one position per segment, in canonical order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

sns.set_theme(
    style="white",
    rc={
        "figure.facecolor": PAGE_BG,
        "axes.facecolor": PAGE_BG,
        "axes.edgecolor": INK_SOFT,
        "axes.labelcolor": INK,
        "text.color": INK,
        "legend.facecolor": ELEVATED_BG,
        "legend.edgecolor": INK_SOFT,
    },
)

# Constants
GAP_DEG = 3.0  # empty angle between neighbouring segments

# Columns: set these to your table's column names
ORIGIN = "Origin city"  # role: source
DESTINATION = "Destination city"  # role: target
MOVERS = "Movers per year (thousand)"  # role: value
RENT = "Origin median rent (EUR per m2)"  # role: track_data

# Data: replace this block with your own edge list, for example df = pd.read_csv("flows.csv")
df = pd.DataFrame(
    {
        ORIGIN: [
            "Berlin",
            "Berlin",
            "Berlin",
            "Berlin",
            "Hamburg",
            "Hamburg",
            "Hamburg",
            "Munich",
            "Munich",
            "Munich",
            "Cologne",
            "Cologne",
            "Cologne",
            "Frankfurt",
            "Frankfurt",
            "Frankfurt",
            "Stuttgart",
            "Stuttgart",
            "Leipzig",
            "Leipzig",
            "Dresden",
            "Dresden",
            "Munich",
            "Hamburg",
        ],
        DESTINATION: [
            "Hamburg",
            "Leipzig",
            "Munich",
            "Dresden",
            "Berlin",
            "Cologne",
            "Frankfurt",
            "Stuttgart",
            "Frankfurt",
            "Berlin",
            "Frankfurt",
            "Hamburg",
            "Berlin",
            "Munich",
            "Stuttgart",
            "Cologne",
            "Munich",
            "Frankfurt",
            "Berlin",
            "Dresden",
            "Leipzig",
            "Munich",
            "Leipzig",
            "Munich",
        ],
        MOVERS: [42, 28, 35, 18, 30, 22, 25, 38, 33, 24, 36, 20, 17, 31, 26, 19, 29, 15, 22, 12, 14, 9, 8, 21],
    }
)
rent_by_city = {
    "Berlin": 14.5,
    "Hamburg": 15.8,
    "Munich": 21.5,
    "Cologne": 13.2,
    "Frankfurt": 16.9,
    "Stuttgart": 15.1,
    "Leipzig": 9.4,
    "Dresden": 9.0,
}
df[RENT] = df[ORIGIN].map(rent_by_city)

# Plot: reads only df and the constants above
outflow = df.groupby(ORIGIN, sort=False)[MOVERS].sum()
inflow = df.groupby(DESTINATION, sort=False)[MOVERS].sum()
cities = list(dict.fromkeys(pd.concat([df[ORIGIN], df[DESTINATION]])))
n_cities = len(cities)
total_flow = pd.Series({c: outflow.get(c, 0) + inflow.get(c, 0) for c in cities})
rent = df.groupby(ORIGIN, sort=False)[RENT].mean().reindex(cities)  # track value: median rent per city
rent_share = rent / rent.max()
color_of = {c: IMPRINT_PALETTE[i % len(IMPRINT_PALETTE)] for i, c in enumerate(cities)}

# Segment angles (degrees, clockwise from 90°): arc length follows each city's total flow
usable = 360.0 - GAP_DEG * n_cities
spans = total_flow / total_flow.sum() * usable
seg_start = {}
cursor = 90.0
for c in cities:
    seg_start[c] = cursor
    cursor -= spans[c] + GAP_DEG

# Ribbon slots: every flow gets an arc inside its segment whose length is proportional to the flow
used = dict.fromkeys(cities, 0.0)
slots = []
for origin, dest, value in zip(df[ORIGIN], df[DESTINATION], df[MOVERS], strict=True):
    arcs = []
    for c in (origin, dest):
        width = value / total_flow[c] * spans[c]
        a0 = seg_start[c] - used[c]
        used[c] += width
        arcs.append((a0, a0 - width))
    slots.append((origin, arcs[0], arcs[1]))


def polar(radius, deg):
    """Point on a circle, angle in degrees."""
    rad = np.radians(deg)
    return radius * np.cos(rad), radius * np.sin(rad)


def ring_sector(ax, a0, a1, r_in, r_out, **kwargs):
    """Filled annular sector between angles a0 > a1 (degrees)."""
    deg = np.linspace(a0, a1, 60)
    outer = np.array(polar(r_out, deg)).T
    inner = np.array(polar(r_in, deg[::-1])).T
    ax.fill(*np.vstack([outer, inner]).T, **kwargs)


R_OUT, R_RING_IN = 1.0, 0.89
R_TRACK_OUT, R_TRACK_IN = 0.85, 0.68
R_RIBBON = 0.64

fig, ax = plt.subplots(figsize=(6, 6), dpi=400, facecolor=PAGE_BG)
fig.subplots_adjust(left=0.0, right=1.0, top=0.9, bottom=0.14)
ax.set_aspect("equal")
ax.set_xlim(-1.5, 1.5)
ax.set_ylim(-1.35, 1.3)
ax.axis("off")

# Ribbons first, so the rings sit on top
for origin, (a0, a1), (b0, b1) in slots:
    p_a0, p_a1 = polar(R_RIBBON, a0), polar(R_RIBBON, a1)
    p_b0, p_b1 = polar(R_RIBBON, b0), polar(R_RIBBON, b1)
    arc_a = [polar(R_RIBBON, d) for d in np.linspace(a0, a1, 12)]
    arc_b = [polar(R_RIBBON, d) for d in np.linspace(b0, b1, 12)]
    verts = [arc_a[0], *arc_a[1:]]
    codes = [Path.MOVETO] + [Path.LINETO] * (len(arc_a) - 1)
    verts += [(0.0, 0.0), p_b0]  # quadratic bezier from the end of arc A to the start of arc B
    codes += [Path.CURVE3, Path.CURVE3]
    verts += arc_b[1:]
    codes += [Path.LINETO] * (len(arc_b) - 1)
    verts += [(0.0, 0.0), p_a0]  # and back to the start of arc A
    codes += [Path.CURVE3, Path.CURVE3]
    ax.add_patch(
        mpatches.PathPatch(Path(verts, codes), facecolor=color_of[origin], edgecolor="none", alpha=0.45, zorder=1)
    )

for c in cities:
    a0 = seg_start[c]
    a1 = a0 - spans[c]
    # Outer ring: one segment per city
    ring_sector(ax, a0, a1, R_RING_IN, R_OUT, color=color_of[c], alpha=0.95, linewidth=0, zorder=3)
    # Inner track: faint full-span base, bar height = median rent relative to the dearest city
    ring_sector(ax, a0, a1, R_TRACK_IN, R_TRACK_OUT, color=INK_SOFT, alpha=0.12, linewidth=0, zorder=2)
    bar_top = R_TRACK_IN + (R_TRACK_OUT - R_TRACK_IN) * rent_share[c]
    ring_sector(ax, a0, a1, R_TRACK_IN, bar_top, color=color_of[c], alpha=0.85, linewidth=0, zorder=3)

    # Segment label, rotated along the radius and flipped on the left half to stay upright
    mid = (a0 + a1) / 2
    x, y = polar(R_OUT + 0.04, mid)
    flip = np.cos(np.radians(mid)) < 0
    ax.text(
        x,
        y,
        c,
        ha="right" if flip else "left",
        va="center",
        rotation=mid + 180 if flip else mid,
        rotation_mode="anchor",
        fontsize=10,
        fontweight="bold",
        color=INK,
    )

fig.suptitle("circos-basic · python · seaborn · anyplot.ai", fontsize=13, fontweight="bold", color=INK, y=0.96)

legend_handles = [
    mpatches.Patch(facecolor=INK_SOFT, alpha=0.95, label="Outer ring: city (arc length ∝ total moves in + out)"),
    mpatches.Patch(facecolor=INK_SOFT, alpha=0.5, label="Inner track: median rent (bar height, EUR per m2)"),
    mpatches.Patch(facecolor=INK_SOFT, alpha=0.3, label="Ribbons: moves, width ∝ movers, colored by origin"),
]
fig.legend(handles=legend_handles, loc="lower center", bbox_to_anchor=(0.5, 0.01), fontsize=8, frameon=True)

plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
