""" anyplot.ai
circlepacking-basic: Circle Packing Chart
Library: letsplot 4.11.0 | Python 3.14.10
Quality: 78/100 | Updated: 2026-11-21
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
    ggplot,
    ggsize,
    labs,
    scale_fill_manual,
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
ROOT_RADIUS = 90  # layout units of the outermost circle
LABEL_MIN_SHARE = 0.09  # leaves with a radius below this share of the root radius stay unlabeled

# Columns: set these to your table's column names
NODE = "id"  # role: id
PARENT = "parent"  # role: parent
SIZE = "value"  # role: value
NAME = "label"  # role: label

# Data: replace this block with your own table, for example df = pd.read_csv("folders.csv")
# Top-level nodes have a parent that is not an id; only leaves carry a value (file system sizes in GB).
df = pd.DataFrame(
    {
        NODE: [
            "Documents",
            "Media",
            "Code",
            "Work",
            "Personal",
            "Archive",
            "Photos",
            "Videos",
            "Music",
            "Projects",
            "Libraries",
            "Backups",
        ],
        PARENT: [None, None, None] + ["Documents"] * 3 + ["Media"] * 3 + ["Code"] * 3,
        SIZE: [None, None, None, 25, 18, 12, 45, 65, 22, 35, 15, 8],
        NAME: [
            "Documents",
            "Media",
            "Code",
            "Work",
            "Personal",
            "Archive",
            "Photos",
            "Videos",
            "Music",
            "Projects",
            "Libraries",
            "Backups",
        ],
    }
)


# Plot
def circle_rows(cx, cy, radius, circle_id, depth, fill):
    angles = np.linspace(0, 2 * np.pi, 60, endpoint=False)
    return [
        {
            "x": cx + radius * np.cos(a),
            "y": cy + radius * np.sin(a),
            "circle_id": circle_id,
            "depth": depth,
            "fill": fill,
        }
        for a in angles
    ]


def pack(radii, iterations=400, gap=0.03):
    """Pack circles around the origin with a simple force simulation: pull to the center, push apart."""
    n = len(radii)
    gap = gap * max(radii, default=1.0)
    start = np.linspace(0, 2 * np.pi, n, endpoint=False)
    xs = max(radii, default=1.0) * np.cos(start) * (n > 1)
    ys = max(radii, default=1.0) * np.sin(start) * (n > 1)
    for step in range(iterations + 60):
        if step < iterations:
            xs, ys = xs * 0.97, ys * 0.97
        for i in range(n):
            for j in range(i + 1, n):
                dx, dy = xs[j] - xs[i], ys[j] - ys[i]
                dist = math.hypot(dx, dy)
                min_dist = radii[i] + radii[j] + gap
                if dist < min_dist:
                    dx, dy, dist = (dx, dy, dist) if dist > 1e-9 else (1.0, 0.0, 1.0)
                    push = (min_dist - dist) / 2
                    xs[i] -= dx / dist * push
                    ys[i] -= dy / dist * push
                    xs[j] += dx / dist * push
                    ys[j] += dy / dist * push
    return xs, ys


# Leaf area is proportional to its value; a parent circle encloses its packed children with padding
size = df.groupby(NODE)[SIZE].sum()
names = df.set_index(NODE)[NAME]
children = df.groupby(PARENT, sort=False)[NODE].apply(list).to_dict()
ROOT = "(root)"
children[ROOT] = df.loc[~df[PARENT].isin(df[NODE]), NODE].tolist()
radius, offset = {}, {}


def layout(node):
    if node not in children:
        radius[node] = math.sqrt(size[node])
        return
    # a row without a value and without children has nothing to draw
    kids = [k for k in children[node] if k in children or size[k] > 0]
    for kid in kids:
        layout(kid)
    kids = sorted(kids, key=lambda k: radius[k], reverse=True)
    children[node] = kids
    kid_radii = [radius[k] for k in kids]
    xs, ys = pack(kid_radii)
    if not kids:
        radius[node] = 1.0
        return
    offset.update({k: (x, y) for k, x, y in zip(kids, xs, ys, strict=True)})
    radius[node] = max(math.hypot(x, y) + r for x, y, r in zip(xs, ys, kid_radii, strict=True)) * 1.06


layout(ROOT)
scale = ROOT_RADIUS / radius.get(ROOT, ROOT_RADIUS)
group_color = {"root": INK_SOFT}
polygon_rows, group_labels, leaf_labels = [], [], []


def place(node, cx, cy, depth, color):
    r = radius[node] * scale
    polygon_rows.extend(circle_rows(cx, cy, r, len(polygon_rows) // 60, depth, node))
    group_color[node] = color
    if node in children:
        if depth > 0:
            group_labels.append({"x": cx, "y": cy + (r + 5) * (1 if cy >= 0 else -1), "text": names[node]})
        for i, kid in enumerate(children[node]):
            kid_color = IMPRINT_PALETTE[i % len(IMPRINT_PALETTE)] if depth == 0 else color
            place(kid, cx + offset[kid][0] * scale, cy + offset[kid][1] * scale, depth + 1, kid_color)
    elif r > LABEL_MIN_SHARE * ROOT_RADIUS:
        leaf_labels.append({"x": cx, "y": cy, "text": names[node]})


place(ROOT, 0, 0, 0, INK_SOFT)
group_color[ROOT] = INK_SOFT

polygon_df = pd.DataFrame(polygon_rows, columns=["x", "y", "circle_id", "depth", "fill"])
group_label_df = pd.DataFrame(group_labels, columns=["x", "y", "text"])
leaf_label_df = pd.DataFrame(leaf_labels, columns=["x", "y", "text"])
fills = [group_color[f] for f in polygon_df["fill"].unique()]
extent = ROOT_RADIUS * 1.12

plot = (
    ggplot(polygon_df)
    + geom_polygon(aes(x="x", y="y", fill="fill", group="circle_id"), color=PAGE_BG, size=0.4, alpha=0.92)
    + scale_fill_manual(values=fills)
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
    plot += geom_text(aes(x="x", y="y", label="text"), data=leaf_label_df, size=5, color=INK)

# Save
ggsave(plot, f"plot-{THEME}.png", path=".", scale=4)
ggsave(plot, f"plot-{THEME}.html", path=".")
