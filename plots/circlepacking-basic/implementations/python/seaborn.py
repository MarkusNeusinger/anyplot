"""anyplot.ai
circlepacking-basic: Circle Packing Chart
Library: seaborn 0.13.2 | Python 3.13.13
Quality: pending | Updated: 2026-11-21
"""

import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from matplotlib.colors import to_rgb
from matplotlib.patches import Circle
from scipy.optimize import minimize


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: all eight positions, one per top-level group in order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

sns.set_theme(
    style="white",
    rc={"figure.facecolor": PAGE_BG, "axes.facecolor": PAGE_BG, "text.color": INK, "font.family": "sans-serif"},
)

# Constants
PADDING = 0.035  # gap between nested circles, as a share of the root radius
LABEL_MIN_PT = 5.5  # smallest label size worth drawing; smaller leaves stay unlabeled

# Columns: set these to your table's column names
NODE = "Node id"  # role: id
PARENT = "Parent id"  # role: parent
VALUE = "Population (millions)"  # role: value
LABEL = "Name"  # role: label

# Data: replace this block with your own table, for example df = pd.read_csv("tree.csv")
# World population by continent and country (millions, 2023, rounded); leaves carry the values.
countries = {
    "Asia": {"China": 1412, "India": 1428, "Indonesia": 277, "Pakistan": 240, "Bangladesh": 172, "Japan": 124},
    "Africa": {"Nigeria": 224, "Ethiopia": 126, "Egypt": 112, "DR Congo": 102, "Tanzania": 67},
    "Europe": {"Russia": 144, "Germany": 84, "United Kingdom": 68, "France": 68, "Italy": 59},
    "North America": {"United States": 335, "Mexico": 128, "Canada": 39, "Guatemala": 18},
    "South America": {"Brazil": 216, "Colombia": 52, "Argentina": 46, "Peru": 34, "Chile": 19},
    "Oceania": {"Australia": 26, "Papua New Guinea": 10, "New Zealand": 5},
}
rows = [{NODE: "world", PARENT: None, VALUE: np.nan, LABEL: "World"}]
for continent, members in countries.items():
    rows.append({NODE: continent, PARENT: "world", VALUE: np.nan, LABEL: continent})
    for country, population in members.items():
        rows.append({NODE: f"{continent}/{country}", PARENT: continent, VALUE: float(population), LABEL: country})
df = pd.DataFrame(rows)

# Plot: reads only df and the constants above
tree = df.drop_duplicates(NODE)
is_parent = tree[NODE].isin(tree[PARENT])
tree = tree[tree[PARENT].isna() | is_parent | tree[VALUE].notna()]  # a leaf without a value has no area
children = {node: group[NODE].tolist() for node, group in tree.groupby(PARENT, sort=False)}
value_of = tree.set_index(NODE)[VALUE]
label_of = tree.set_index(NODE)[LABEL]
root = tree.loc[tree[PARENT].isna(), NODE].iloc[0]


def pack(radii):
    """Place circles of the given radii tightly; returns centers around the origin."""
    order = np.argsort(radii)[::-1]
    centers = np.zeros((len(radii), 2))
    placed = []
    for rank, i in enumerate(order):
        if rank == 0:
            placed.append(i)
            continue
        if rank == 1:
            centers[i] = (centers[order[0]][0] + radii[order[0]] + radii[i], 0.0)
            placed.append(i)
            continue
        weights = radii[placed] ** 2
        mass_center = (centers[placed] * weights[:, None]).sum(axis=0) / weights.sum()
        best, best_cost = None, np.inf
        for a in placed:
            for b in placed:
                if a >= b:
                    continue
                ra, rb = radii[a] + radii[i], radii[b] + radii[i]
                d = np.linalg.norm(centers[b] - centers[a])
                if d > ra + rb or d < abs(ra - rb) or d == 0:
                    continue
                along = (ra**2 - rb**2 + d**2) / (2 * d)
                height = np.sqrt(max(ra**2 - along**2, 0.0))
                unit = (centers[b] - centers[a]) / d
                normal = np.array([-unit[1], unit[0]])
                for sign in (1, -1):
                    cand = centers[a] + unit * along + sign * normal * height
                    gaps = np.linalg.norm(centers[placed] - cand, axis=1) - radii[placed] - radii[i]
                    if gaps.min() < -1e-9:
                        continue
                    cost = np.linalg.norm(cand - mass_center) + radii[i]
                    if cost < best_cost:
                        best, best_cost = cand, cost
        centers[i] = best
        placed.append(i)
    return centers


def enclose(centers, radii):
    """Center and radius of a circle enclosing all given circles (iterative minimax)."""

    def reach(p):
        return (np.linalg.norm(centers - p, axis=1) + radii).max()

    start = (centers * (radii**2)[:, None]).sum(axis=0) / (radii**2).sum()
    best = minimize(reach, start, method="Nelder-Mead", options={"xatol": 1e-9, "fatol": 1e-9, "maxiter": 4000})
    return best.x, best.fun


# Leaf area is proportional to value: radius = sqrt(value) up to a common scale
layout = {}


def build(node):
    """Return the radius of `node` and store its children's offsets relative to its center."""
    kids = children.get(node)
    if not kids:
        return float(np.sqrt(value_of[node])) if pd.notna(value_of[node]) else 1.0
    radii = np.array([build(k) for k in kids])
    pad = PADDING * radii.max()
    centers = pack(radii + pad / 2)
    center, enclosing = enclose(centers, radii + pad / 2)
    layout[node] = [(k, tuple(c - center), r) for k, c, r in zip(kids, centers, radii, strict=True)]
    return float(enclosing + pad)


root_radius = build(root)
circles = {root: (0.0, 0.0, root_radius, 0)}


def place(node, cx, cy, depth):
    for kid, (dx, dy), r in layout.get(node, []):
        circles[kid] = (cx + dx, cy + dy, r, depth + 1)
        place(kid, cx + dx, cy + dy, depth + 1)


place(root, 0.0, 0.0, 0)

top_level = children.get(root, [])
color_of = {}
for i, group in enumerate(top_level):
    color_of[group] = IMPRINT_PALETTE[i]
    for member in children.get(group, []):
        color_of[member] = IMPRINT_PALETTE[i]


def text_on(fill):
    """Pick white or near-black text, whichever contrasts more with the fill."""

    def lum(c):
        r, g, b = (v / 12.92 if v <= 0.03928 else ((v + 0.055) / 1.055) ** 2.4 for v in to_rgb(c))
        return 0.2126 * r + 0.7152 * g + 0.0722 * b

    return "#FFFFFF" if 1.05 / (lum(fill) + 0.05) > (lum(fill) + 0.05) / 0.06 else "#1A1A17"


fig, ax = plt.subplots(figsize=(6, 6), dpi=400, facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)
margin = root_radius * 1.04
ax.set_xlim(-margin, margin)
ax.set_ylim(-margin * 1.04, margin * 1.04)
ax.set_aspect("equal")
ax.axis("off")
fig.subplots_adjust(left=0.02, right=0.98, bottom=0.02, top=0.92)
pt_per_unit = ax.get_window_extent().width / fig.dpi * 72 / (2 * margin)

for node, (x, y, r, depth) in circles.items():
    if depth == 0:
        ax.add_patch(Circle((x, y), r, facecolor=ELEVATED_BG, edgecolor=INK_SOFT, linewidth=1.2))
    elif node in layout:
        ax.add_patch(Circle((x, y), r, facecolor=color_of[node], alpha=0.22, edgecolor="none"))
        ax.add_patch(Circle((x, y), r, facecolor="none", edgecolor=color_of[node], linewidth=1.6))
    else:
        ax.add_patch(Circle((x, y), r, facecolor=color_of[node], edgecolor=PAGE_BG, linewidth=0.8))
        label = str(label_of[node])
        size = min(8.5, 1.75 * r * pt_per_unit / (0.74 * max(len(label), 4)))
        if size >= LABEL_MIN_PT:
            ax.text(
                x, y, label, ha="center", va="center", fontsize=size, fontweight="bold", color=text_on(color_of[node])
            )

# Group names sit on the top edge of their circle, backed by the page color so they stay readable
for node, (x, y, r, depth) in circles.items():
    if depth == 1:
        ax.text(
            x,
            y + r,
            label_of[node].upper(),
            ha="center",
            va="center",
            fontsize=7,
            fontweight="bold",
            color=INK,
            bbox={"facecolor": PAGE_BG, "edgecolor": color_of[node], "boxstyle": "round,pad=0.25", "linewidth": 1.0},
        )

fig.suptitle(
    "circlepacking-basic · python · seaborn · anyplot.ai", fontsize=13, fontweight="medium", color=INK, y=0.975
)
plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
