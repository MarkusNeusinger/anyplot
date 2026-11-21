"""anyplot.ai
venn-basic: Venn Diagram
Library: seaborn 0.13.2 | Python 3.13.13
Quality: pending | Updated: 2026-05-11
"""

import os

import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: all eight positions, one per set in order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

sns.set_theme(
    style="white",
    rc={"figure.facecolor": PAGE_BG, "axes.facecolor": PAGE_BG, "axes.labelcolor": INK, "text.color": INK},
)

# Constants
MAX_SETS = 3  # a Venn diagram stays readable with at most three circles

# Columns: set these to your table's column names
SETS = "Sets"  # role: set_labels
SIZE = "Organizations"  # role: set_sizes
OVERLAP = "Is overlap"  # role: intersections

# Data: one row per set or overlap, SIZE is inclusive (AWS & Google Cloud counts the triple overlap too).
# Replace this block with your own table, for example df = pd.read_csv("overlaps.csv")
df = pd.DataFrame(
    {
        SETS: [
            "AWS",
            "Google Cloud",
            "Azure",
            "AWS & Google Cloud",
            "AWS & Azure",
            "Google Cloud & Azure",
            "AWS & Google Cloud & Azure",
        ],
        SIZE: [120, 95, 75, 35, 28, 22, 12],
        OVERLAP: [False, False, False, True, True, True, True],
    }
)

# Plot: reads only df and the constants above
table = df.dropna(subset=[SETS, SIZE, OVERLAP]).drop_duplicates(subset=[SETS])
members = [tuple(s.strip() for s in str(name).split("&")) for name in table[SETS]]
size_of = {frozenset(m): n for m, n in zip(members, table[SIZE], strict=True)}
names = [m[0] for m, overlap in zip(members, table[OVERLAP], strict=True) if not bool(overlap)][:MAX_SETS]
n_sets = len(names)


def inclusive(*idx):
    return size_of.get(frozenset(names[i] for i in idx), 0)


# Exclusive count of every region by inclusion-exclusion over the inclusive sizes
regions = {}
for mask in range(1, 2**n_sets):
    inside = [i for i in range(n_sets) if mask >> i & 1]
    outside = [i for i in range(n_sets) if not mask >> i & 1]
    count = 0
    for extra in range(2 ** len(outside)):
        added = [outside[j] for j in range(len(outside)) if extra >> j & 1]
        count += (-1) ** len(added) * inclusive(*inside, *added)
    regions[tuple(inside)] = count
total = sum(regions.values())

# Circle areas follow the set sizes; the distance of each pair is solved so the lens area follows the overlap
radii = np.sqrt(np.array([inclusive(i) for i in range(n_sets)]) / np.pi)


def lens_area(d, r1, r2):
    if d >= r1 + r2:
        return 0.0
    if d <= abs(r1 - r2):
        return np.pi * min(r1, r2) ** 2
    a1 = r1**2 * np.arccos((d**2 + r1**2 - r2**2) / (2 * d * r1))
    a2 = r2**2 * np.arccos((d**2 + r2**2 - r1**2) / (2 * d * r2))
    return a1 + a2 - 0.5 * np.sqrt((-d + r1 + r2) * (d + r1 - r2) * (d - r1 + r2) * (d + r1 + r2))


def pair_distance(i, j):
    target = inclusive(i, j)
    lo, hi = abs(radii[i] - radii[j]), radii[i] + radii[j]
    for _ in range(60):
        mid = (lo + hi) / 2
        if lens_area(mid, radii[i], radii[j]) > target:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


centers = np.zeros((n_sets, 2))
if n_sets >= 2:
    centers[1] = (pair_distance(0, 1), 0.0)
if n_sets > 2:
    d01, d02, d12 = pair_distance(0, 1), pair_distance(0, 2), pair_distance(1, 2)
    cx = (d01**2 + d02**2 - d12**2) / (2 * d01)
    centers[2] = (cx, np.sqrt(max(d02**2 - cx**2, 0.0)))
centers -= centers.mean(axis=0)

# Region label anchors: the point of each region closest to its centroid
reach = np.abs(centers).max() + radii.max()
span = reach * 1.3
grid = np.linspace(-reach, reach, 700)
gx, gy = np.meshgrid(grid, grid)
inside_circle = [(gx - c[0]) ** 2 + (gy - c[1]) ** 2 <= r**2 for c, r in zip(centers, radii, strict=True)]
anchors = {}
for key in regions:
    cell = np.ones_like(gx, dtype=bool)
    for i in range(n_sets):
        cell &= inside_circle[i] if i in key else ~inside_circle[i]
    if cell.any():
        px, py = gx[cell], gy[cell]
        best = np.argmin((px - px.mean()) ** 2 + (py - py.mean()) ** 2)
        anchors[key] = (px[best], py[best])

fig, ax = plt.subplots(figsize=(6, 6), dpi=400, facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

for i, (center, radius) in enumerate(zip(centers, radii, strict=True)):
    ax.add_patch(
        mpatches.Circle(
            center, radius, facecolor=IMPRINT_PALETTE[i], edgecolor=IMPRINT_PALETTE[i], alpha=0.4, linewidth=1.8
        )
    )
    # Set label outside its circle, pushed away from the middle of the diagram
    away = center / (np.linalg.norm(center) or 1.0)
    pos = center + away * (radius + radii.max() * 0.08)
    ax.text(
        pos[0],
        pos[1],
        f"{names[i]}\n(n={inclusive(i)})",
        ha="left" if away[0] > 0.3 else "right" if away[0] < -0.3 else "center",
        va="bottom" if away[1] > 0.7 else "center",
        fontsize=11,
        fontweight="bold",
        color=INK,
    )

for key, (x, y) in anchors.items():
    count = regions[key]
    ax.text(
        x,
        y,
        f"{count}\n({count / total * 100:.0f}%)",
        ha="center",
        va="center",
        fontsize=9,
        fontweight="bold",
        color=INK,
        bbox={"boxstyle": "round,pad=0.25", "facecolor": ELEVATED_BG, "edgecolor": INK_SOFT, "alpha": 0.85},
    )

# Style
ax.set_xlim(-span, span)
ax.set_ylim(-span, span)
ax.set_aspect("equal")
ax.axis("off")
ax.set_title("venn-basic · python · seaborn · anyplot.ai", fontsize=12, fontweight="bold", color=INK)
fig.text(
    0.5,
    0.04,
    f"{total} organizations in total; circle areas follow the set sizes",
    ha="center",
    va="bottom",
    fontsize=8,
    style="italic",
    color=INK_SOFT,
)
plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
