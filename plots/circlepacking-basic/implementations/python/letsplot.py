""" anyplot.ai
circlepacking-basic: Circle Packing Chart
Library: letsplot 4.11.0 | Python 3.14.10
Quality: 83/100 | Updated: 2026-11-26
"""

import math
import os

import numpy as np
import pandas as pd
from lets_plot import (
    LetsPlot,
    aes,
    coord_fixed,
    element_blank,
    element_rect,
    element_text,
    geom_polygon,
    geom_text,
    gggrid,
    ggplot,
    ggsize,
    labs,
    scale_color_identity,
    scale_fill_identity,
    scale_x_continuous,
    scale_y_continuous,
    theme,
)
from lets_plot.export import ggsave


LetsPlot.setup_html()

# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: all eight positions, one per top-level group in order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Constants
ROOT = "(root)"  # id of the implicit root that holds the top-level nodes
ROOT_RADIUS = 90  # layout units of the outermost circle
LABEL_MIN_SHARE = 0.09  # leaves with a radius below this share of the root radius stay unlabeled

# Columns: set these to your table's column names
NODE = "id"  # role: id
PARENT = "parent"  # role: parent
SIZE = "value"  # role: value
NAME = "label"  # role: label

# Data: replace this block with your own table, for example df = pd.read_csv("folders.csv")
# Top-level nodes have a parent that is not an id; only leaves carry a value (file system sizes in GB).
folders = {
    "Documents": {"Work": 25, "Personal": 18, "Archive": 12, "Taxes": 9, "Contracts": 6},
    "Media": {"Photos": 45, "Videos": 65, "Music": 22, "Podcasts": 14, "Screenshots": 10},
    "Code": {"Projects": 35, "Libraries": 15, "Backups": 8, "Notebooks": 20, "Scripts": 11},
    "Games": {"Library": 55, "Mods": 16, "Saves": 7, "Emulators": 28, "Installers": 12},
}
leaf_rows = [
    (f"{folder}/{leaf}", folder, gb, leaf) for folder, leaves in folders.items() for leaf, gb in leaves.items()
]
df = pd.DataFrame([(folder, None, None, folder) for folder in folders] + leaf_rows, columns=[NODE, PARENT, SIZE, NAME])

# Plot
# Leaf area is proportional to its value; a parent circle encloses its packed children with padding
names = dict(zip(df[NODE], df[NAME], strict=True))
size = dict(zip(df[NODE], df[SIZE], strict=True))
parent_of = dict(zip(df[NODE], df[PARENT].where(df[PARENT].isin(df[NODE]), ROOT), strict=True))
children = {}
for node, parent in parent_of.items():
    children.setdefault(parent, []).append(node)

depth = {ROOT: 0}
for node in parent_of:
    up, level = parent_of[node], 1
    while up in parent_of:
        up, level = parent_of[up], level + 1
    depth[node] = level

# Leaves carry radius sqrt(value); the parents are packed from the deepest level up to the root
radius = {
    node: math.sqrt(size[node]) for node in parent_of if node not in children and size[node] > 0
}  # a missing value compares False and drops the row
offset = {}
for parent in sorted(children, key=lambda p: -depth[p]):
    kids = sorted((k for k in children[parent] if k in radius), key=lambda k: radius[k], reverse=True)
    if not kids:
        continue
    children[parent] = kids
    kid_radii = [radius[k] for k in kids]
    n = len(kids)
    big = max(kid_radii)
    gap = 0.03 * big
    start = np.linspace(0, 2 * np.pi, n, endpoint=False)
    xs = big * np.cos(start) * (n > 1)
    ys = big * np.sin(start) * (n > 1)
    # force simulation: pull to the center, push overlapping circles apart
    for step in range(460):
        if step < 400:
            xs, ys = xs * 0.97, ys * 0.97
        for i in range(n):
            for j in range(i + 1, n):
                dx, dy = xs[j] - xs[i], ys[j] - ys[i]
                dist = math.hypot(dx, dy)
                min_dist = kid_radii[i] + kid_radii[j] + gap
                if dist < min_dist:
                    dx, dy, dist = (dx, dy, dist) if dist > 1e-9 else (1.0, 0.0, 1.0)
                    push = (min_dist - dist) / 2
                    xs[i] -= dx / dist * push
                    ys[i] -= dy / dist * push
                    xs[j] += dx / dist * push
                    ys[j] += dy / dist * push
    offset.update({k: (x, y) for k, x, y in zip(kids, xs, ys, strict=True)})
    radius[parent] = max(math.hypot(x, y) + r for x, y, r in zip(xs, ys, kid_radii, strict=True)) * 1.06

scale = ROOT_RADIUS / radius.get(ROOT, ROOT_RADIUS)


def luminance(hex_color):
    rgb = [int(hex_color[i : i + 2], 16) / 255 for i in (1, 3, 5)]
    lin = [c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4 for c in rgb]
    return 0.2126 * lin[0] + 0.7152 * lin[1] + 0.0722 * lin[2]


# Place circles top-down (a parent is drawn before its children); the list grows while it is walked
queue = [(ROOT, 0.0, 0.0, 0, INK_SOFT)] if ROOT in radius else []
polygon_frames, group_labels, leaf_labels = [], [], []
for circle_id, (node, cx, cy, level, color) in enumerate(queue):
    r = radius[node] * scale
    n_vertices = max(48, int(r * 4))  # big circles get more vertices so their outline stays round
    angles = np.linspace(0, 2 * np.pi, n_vertices, endpoint=False)
    polygon_frames.append(
        pd.DataFrame(
            {"x": cx + r * np.cos(angles), "y": cy + r * np.sin(angles), "circle_id": circle_id, "fill": color}
        )
    )
    if node in children:
        if level > 0:
            group_labels.append({"x": cx, "y": cy + (r + 5) * (1 if cy >= 0 else -1), "text": names[node]})
        for i, kid in enumerate(children[node]):
            kid_color = IMPRINT_PALETTE[i % len(IMPRINT_PALETTE)] if level == 0 else color
            queue.append((kid, cx + offset[kid][0] * scale, cy + offset[kid][1] * scale, level + 1, kid_color))
    elif r > LABEL_MIN_SHARE * ROOT_RADIUS:
        # dark or light text, whichever contrasts more with the leaf fill
        dark_contrast = (luminance(color) + 0.05) / (luminance("#1A1A17") + 0.05)
        light_contrast = (luminance("#F0EFE8") + 0.05) / (luminance(color) + 0.05)
        text_color = "#1A1A17" if dark_contrast >= light_contrast else "#F0EFE8"
        leaf_labels.append({"x": cx, "y": cy, "text": names[node], "ink": text_color})

polygon_df = pd.concat(polygon_frames or [pd.DataFrame(columns=["x", "y", "circle_id", "fill"])], ignore_index=True)
group_label_df = pd.DataFrame(group_labels, columns=["x", "y", "text"])
leaf_label_df = pd.DataFrame(leaf_labels, columns=["x", "y", "text", "ink"])
extent = ROOT_RADIUS * 1.12

plot = (
    ggplot(polygon_df)
    + geom_polygon(aes(x="x", y="y", fill="fill", group="circle_id"), color=PAGE_BG, size=0.4, alpha=0.92)
    + scale_fill_identity()
    + coord_fixed(ratio=1)
    + scale_x_continuous(limits=(-extent, extent))
    + scale_y_continuous(limits=(-extent, extent))
    + labs(title="circlepacking-basic · python · letsplot · anyplot.ai")
    + ggsize(600, 600)
    + theme(
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        plot_title=element_text(size=14, hjust=0.5, color=INK),
        legend_position="none",
        axis_title=element_blank(),
        axis_text=element_blank(),
        axis_ticks=element_blank(),
        axis_line=element_blank(),
        panel_grid=element_blank(),
    )
)

# Labels are layers of their own, drawn only when there is something to label
if len(group_label_df):
    plot += geom_text(aes(x="x", y="y", label="text"), data=group_label_df, size=7, color=PAGE_BG, fontface="bold")
if len(leaf_label_df):
    plot += geom_text(aes(x="x", y="y", label="text", color="ink"), data=leaf_label_df, size=4) + scale_color_identity()

# A fixed aspect leaves the canvas edges transparent; a one-panel grid paints the whole canvas
plot = gggrid([plot]) + ggsize(600, 600) + theme(plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG))

# Save
ggsave(plot, f"plot-{THEME}.png", path=".", scale=4)
ggsave(plot, f"plot-{THEME}.html", path=".")
