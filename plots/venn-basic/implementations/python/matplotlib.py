"""anyplot.ai
venn-basic: Venn Diagram
Library: matplotlib 3.10.9 | Python 3.13.13
Quality: pending | Updated: 2026-05-11
"""

import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.patches import Circle
from scipy.ndimage import distance_transform_edt
from scipy.optimize import brentq


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"

# Imprint palette
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Column constants
SETS = "Sets"  # role: set_labels
SET_SIZE = "Set size"  # role: set_sizes
INTERSECTION = "Intersection size"  # role: intersections

# Data: Developer survey on language proficiency. One row per set and per overlap,
# sizes inclusive (an overlap counts the elements of every larger overlap it contains).
df = pd.DataFrame(
    {
        SETS: [
            "Python",
            "JavaScript",
            "SQL",
            "Python & JavaScript",
            "Python & SQL",
            "JavaScript & SQL",
            "Python & JavaScript & SQL",
        ],
        SET_SIZE: [80, 70, 50, np.nan, np.nan, np.nan, np.nan],
        INTERSECTION: [np.nan, np.nan, np.nan, 30, 20, 25, 10],
    }
)

# Plot
names = df.loc[df[SET_SIZE].notna(), SETS].tolist()
set_sizes = df[SET_SIZE].dropna().tolist()
# Overlap rows in the order AB, AC, BC, ABC
s_ab, s_ac, s_bc, s_abc = df[INTERSECTION].dropna().tolist()
s_a, s_b, s_c = set_sizes

# Circle areas follow the set sizes
radii = [np.sqrt(size / np.pi) for size in set_sizes]


def lens_area(d, r1, r2):
    """Overlap area of two circles whose centers are d apart."""
    p1 = r1**2 * np.arccos((d**2 + r1**2 - r2**2) / (2 * d * r1))
    p2 = r2**2 * np.arccos((d**2 + r2**2 - r1**2) / (2 * d * r2))
    p3 = 0.5 * np.sqrt((-d + r1 + r2) * (d + r1 - r2) * (d - r1 + r2) * (d + r1 + r2))
    return p1 + p2 - p3


def center_distance(overlap, r1, r2):
    """Distance at which two circles overlap by the given area."""
    lo, hi = abs(r1 - r2) + 1e-9, r1 + r2 - 1e-9
    return brentq(lambda d: lens_area(d, r1, r2) - overlap, lo, hi)


# Pairwise overlaps set the center distances; the third circle follows by triangulation
d_ab = center_distance(s_ab, radii[0], radii[1])
d_ac = center_distance(s_ac, radii[0], radii[2])
d_bc = center_distance(s_bc, radii[1], radii[2])
cx_c = (d_ac**2 - d_bc**2 + d_ab**2) / (2 * d_ab)
centers = np.array([[0.0, 0.0], [d_ab, 0.0], [cx_c, np.sqrt(max(d_ac**2 - cx_c**2, 0.0))]])

# Exclusive region sizes by membership code (bit i set = inside circle i)
exclusive = {
    0b001: s_a - s_ab - s_ac + s_abc,
    0b010: s_b - s_ab - s_bc + s_abc,
    0b100: s_c - s_ac - s_bc + s_abc,
    0b011: s_ab - s_abc,
    0b101: s_ac - s_abc,
    0b110: s_bc - s_abc,
    0b111: s_abc,
}

# Label spot of each region: the point deepest inside it, found on a fine grid
pad = 0.45 * max(radii)
x_min, y_min = (centers - np.array(radii)[:, None]).min(axis=0) - pad
x_max, y_max = (centers + np.array(radii)[:, None]).max(axis=0) + pad
gx, gy = np.meshgrid(np.linspace(x_min, x_max, 1200), np.linspace(y_min, y_max, 1200))
inside = [(gx - cx) ** 2 + (gy - cy) ** 2 < r**2 for (cx, cy), r in zip(centers, radii, strict=True)]
membership = sum(m.astype(int) << i for i, m in enumerate(inside))

fig, ax = plt.subplots(figsize=(8, 4.5), dpi=400, facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)
ax.set_aspect("equal")
ax.axis("off")

for i, ((cx, cy), r) in enumerate(zip(centers, radii, strict=True)):
    ax.add_patch(Circle((cx, cy), r, facecolor=IMPRINT_PALETTE[i], alpha=0.55, edgecolor="none"))
    ax.add_patch(Circle((cx, cy), r, facecolor="none", edgecolor=IMPRINT_PALETTE[i], linewidth=1.6))

# Region counts
for code, count in exclusive.items():
    mask = membership == code
    if not mask.any():
        continue
    depth = distance_transform_edt(mask)
    iy, ix = np.unravel_index(depth.argmax(), depth.shape)
    ax.text(gx[iy, ix], gy[iy, ix], f"{count:g}", ha="center", va="center", fontsize=12, fontweight="bold", color=INK)

# Set labels sit just outside each circle, pushed away from the middle of the figure
middle = centers.mean(axis=0)
for name, (cx, cy), r in zip(names, centers, radii, strict=True):
    away = np.array([cx, cy]) - middle
    away = away / np.linalg.norm(away)
    gap = r + 0.1 * max(radii)
    ax.text(
        cx + away[0] * gap,
        cy + away[1] * gap,
        name,
        ha="right" if away[0] < -0.3 else "left" if away[0] > 0.3 else "center",
        va="bottom" if away[1] > 0.5 else "top" if away[1] < -0.5 else "center",
        fontsize=13,
        fontweight="bold",
        color=INK,
    )

ax.set_xlim(x_min, x_max)
ax.set_ylim(y_min, y_max)
ax.set_title("venn-basic · python · matplotlib · anyplot.ai", fontsize=12, fontweight="medium", color=INK, pad=10)

plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
