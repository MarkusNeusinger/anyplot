"""anyplot.ai
dendrogram-radial: Radial Dendrogram
Library: pygal 3.1.0 | Python 3.13.13
Quality: 81/100 | Created: 2026-05-14
"""

import importlib
import math
import os
import sys

import cairosvg
import numpy as np
import pandas as pd
from scipy.cluster.hierarchy import leaves_list, linkage
from scipy.spatial.distance import pdist


# Remove current directory from sys.path so loading 'pygal' finds the installed
# package rather than this script (which is also named pygal.py), then use
# importlib to avoid E402 import-not-at-top violations for the two pygal lines.
_thisdir = os.path.dirname(os.path.abspath(__file__))
sys.path = [p for p in sys.path if p not in ("", _thisdir)]
pygal = importlib.import_module("pygal")
Style = importlib.import_module("pygal.style").Style


THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

TITLE = "dendrogram-radial · python · pygal · anyplot.ai"

# Imprint palette: all eight positions, one per group in order
IMPRINT_PALETTE = ("#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314")

custom_style = Style(
    background=PAGE_BG,
    plot_background=PAGE_BG,
    foreground=INK,
    foreground_strong=INK,
    foreground_subtle=INK_MUTED,
    colors=IMPRINT_PALETTE,
    title_font_size=48,
    legend_font_size=36,
    label_font_size=32,
)

# Columns: set these to your table's column names
GROUP = "Taxonomic group"  # role: clusters

# Data: replace this block with your own table, for example df = pd.read_csv("traits.csv", index_col=0)
# One row per leaf (the index holds the leaf labels), numeric trait columns, plus the cluster column.
np.random.seed(42)
groups_list = ["Marine Mammals", "Canines", "Felines", "Raptors", "Amphibians", "Fish"]
traits = {
    "Dolphin": [4, 5, 3, 4, 4],
    "Whale": [5, 5, 2, 3, 4],
    "Seal": [3, 4, 2, 2, 4],
    "Sea Lion": [3, 4, 2, 3, 4],
    "Wolf": [3, 1, 4, 5, 4],
    "Fox": [2, 1, 4, 1, 4],
    "Dog": [2, 1, 3, 3, 3],
    "Coyote": [2, 1, 4, 1, 4],
    "Lion": [4, 1, 4, 3, 5],
    "Tiger": [4, 1, 4, 1, 5],
    "Leopard": [3, 1, 4, 1, 5],
    "Cheetah": [3, 1, 5, 1, 5],
    "Eagle": [2, 2, 5, 1, 4],
    "Hawk": [2, 2, 4, 1, 4],
    "Falcon": [1, 2, 5, 1, 4],
    "Osprey": [2, 2, 3, 1, 4],
    "Frog": [1, 3, 2, 1, 3],
    "Toad": [1, 3, 1, 1, 3],
    "Salamander": [1, 3, 1, 1, 3],
    "Newt": [1, 3, 1, 1, 3],
    "Salmon": [2, 5, 4, 1, 3],
    "Trout": [2, 5, 3, 1, 3],
    "Bass": [2, 5, 2, 1, 3],
    "Pike": [2, 4, 2, 1, 4],
}
df = pd.DataFrame.from_dict(
    traits, orient="index", columns=["Body size", "Aquatic affinity", "Speed", "Sociality", "Carnivory"]
)
df[GROUP] = [groups_list[i // 4] for i in range(len(df))]

# Plot: reads only df and the constants above
species = df.index.tolist()
group_names = list(dict.fromkeys(df[GROUP]))
group_color = {g: IMPRINT_PALETTE[i] for i, g in enumerate(group_names)}
leaf_group = df[GROUP].tolist()

# Hierarchical clustering via Ward linkage on the numeric trait columns
Z = linkage(pdist(df.drop(columns=GROUP).to_numpy(dtype=float), metric="euclidean"), method="ward")
n = len(species)

# Assign angles to leaves using dendrogram leaf ordering
leaf_order = leaves_list(Z)
leaf_angles = {leaf_order[i]: 2 * math.pi * i / n for i in range(n)}

# Radii: leaves at outer edge (1.0), internal nodes proportional to merge distance
max_dist = Z[-1][2]
node_radii = dict.fromkeys(range(n), 1.0)
for i, row in enumerate(Z):
    node_radii[n + i] = 1.0 - row[2] / max_dist

# Angular positions: midpoint of each subtree's angular span
node_min_ang = dict(leaf_angles)
node_max_ang = dict(leaf_angles)
node_angles = dict(leaf_angles)
for i, row in enumerate(Z):
    left, right = int(row[0]), int(row[1])
    nid = n + i
    node_min_ang[nid] = min(node_min_ang[left], node_min_ang[right])
    node_max_ang[nid] = max(node_max_ang[left], node_max_ang[right])
    node_angles[nid] = (node_min_ang[nid] + node_max_ang[nid]) / 2

# Propagate cluster labels: a node gets a color only if all its leaves share one cluster
node_cluster = dict(enumerate(leaf_group))
for i, row in enumerate(Z):
    left, right = int(row[0]), int(row[1])
    cl, cr = node_cluster[left], node_cluster[right]
    node_cluster[n + i] = cl if cl == cr else None

# Canvas setup
W, H = 2400, 2400
cx, cy = W // 2, H // 2 + 40
R = 800  # Dendrogram outer radius in pixels
LABEL_R = R + 40  # Label placement radius


def polar_xy(r, theta):
    return (cx + r * math.cos(theta - math.pi / 2), cy + r * math.sin(theta - math.pi / 2))


elems = []

# Draw dendrogram branches (arcs + radial lines)
for i, row in enumerate(Z):
    left, right = int(row[0]), int(row[1])
    nid = n + i
    par_r = node_radii[nid] * R
    par_theta = node_angles[nid]

    for child in (left, right):
        ch_r = node_radii[child] * R
        ch_theta = node_angles[child]
        color = group_color.get(node_cluster[child], INK_SOFT)
        sw = 5 if child < n else 4

        # Arc at par_r from par_theta to ch_theta
        if par_r > 1:
            x1, y1 = polar_xy(par_r, par_theta)
            x2, y2 = polar_xy(par_r, ch_theta)
            d_theta = ch_theta - par_theta
            while d_theta > math.pi:
                d_theta -= 2 * math.pi
            while d_theta < -math.pi:
                d_theta += 2 * math.pi
            sweep = 1 if d_theta > 0 else 0
            large = 1 if abs(d_theta) > math.pi else 0
            elems.append(
                f'<path d="M{x1:.1f},{y1:.1f} A{par_r:.1f},{par_r:.1f} 0 {large},{sweep} {x2:.1f},{y2:.1f}" '
                f'stroke="{color}" stroke-width="{sw}" fill="none" stroke-linecap="round" opacity="0.88"/>'
            )

        # Radial line from (par_r, ch_theta) to (ch_r, ch_theta)
        rx1, ry1 = polar_xy(max(par_r, 1), ch_theta)
        rx2, ry2 = polar_xy(ch_r, ch_theta)
        elems.append(
            f'<line x1="{rx1:.1f}" y1="{ry1:.1f}" x2="{rx2:.1f}" y2="{ry2:.1f}" '
            f'stroke="{color}" stroke-width="{sw}" stroke-linecap="round" opacity="0.88"/>'
        )

# Center root dot
elems.append(f'<circle cx="{cx}" cy="{cy}" r="12" fill="{INK_SOFT}" opacity="0.55"/>')

# Leaf dots and radially-oriented labels
for i in range(n):
    theta = leaf_angles[i]
    lx, ly = polar_xy(R, theta)
    color = group_color[leaf_group[i]]

    elems.append(f'<circle cx="{lx:.1f}" cy="{ly:.1f}" r="11" fill="{color}" opacity="0.95"/>')

    label_x, label_y = polar_xy(LABEL_R, theta)
    svg_angle = math.degrees(theta - math.pi / 2) % 360
    if svg_angle <= 90 or svg_angle >= 270:
        anchor, rot = "start", svg_angle
    else:
        anchor, rot = "end", svg_angle + 180

    elems.append(
        f'<text x="{label_x:.1f}" y="{label_y:.1f}" '
        f'transform="rotate({rot:.1f},{label_x:.1f},{label_y:.1f})" '
        f'text-anchor="{anchor}" dominant-baseline="middle" '
        f'font-family="sans-serif" font-size="32" fill="{color}" font-weight="500">'
        f"{species[i]}</text>"
    )

# Legend
lx0, ly0 = 70, 170
elems.append(
    f'<text x="{lx0}" y="{ly0}" font-family="sans-serif" font-size="36" fill="{INK}" font-weight="600">{GROUP}</text>'
)
for g, name in enumerate(group_names):
    gy = ly0 + 55 + g * 56
    elems.append(f'<circle cx="{lx0 + 14}" cy="{gy}" r="13" fill="{group_color[name]}"/>')
    elems.append(
        f'<text x="{lx0 + 42}" y="{gy}" font-family="sans-serif" font-size="32" '
        f'fill="{INK}" dominant-baseline="middle">{name}</text>'
    )

# Title
elems.append(
    f'<text x="{W // 2}" y="80" text-anchor="middle" font-family="sans-serif" '
    f'font-size="48" fill="{INK}" font-weight="600">{TITLE}</text>'
)

svg = (
    '<?xml version="1.0" encoding="utf-8"?>\n'
    f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}">\n'
    f'  <rect width="{W}" height="{H}" fill="{PAGE_BG}"/>\n' + "\n".join(f"  {e}" for e in elems) + "\n</svg>\n"
)

# PNG via cairosvg (pygal's PNG rendering backend)
cairosvg.svg2png(bytestring=svg.encode(), write_to=f"plot-{THEME}.png")

# Interactive HTML via pygal's XY chart — leaf nodes plotted as interactive scatter
# with hover tooltips (species name + group); uses pygal's JS rendering pipeline
xy_chart = pygal.XY(
    style=custom_style, width=W, height=H, title=TITLE, show_x_labels=False, show_y_labels=False, dots_size=6
)

for name in group_names:
    group_pts = []
    for i in range(n):
        if leaf_group[i] == name:
            theta = leaf_angles[i]
            group_pts.append(
                {"value": (R * math.cos(theta - math.pi / 2), R * math.sin(theta - math.pi / 2)), "label": species[i]}
            )
    xy_chart.add(name, group_pts)

with open(f"plot-{THEME}.html", "wb") as f:
    f.write(xy_chart.render())
