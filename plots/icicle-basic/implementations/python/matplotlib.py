""" anyplot.ai
icicle-basic: Basic Icicle Chart
Library: matplotlib 3.11.2 | Python 3.14.10
Quality: 84/100 | Updated: 2026-11-09
"""

import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.colors import to_rgb
from matplotlib.patches import Rectangle


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: one hue per hierarchy level, root first
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Constants
LABEL_PAD = 0.9  # a label may fill at most this share of its rectangle

# Columns: set these to your table's column names
NAME = "Name"  # role: name
PARENT = "Parent"  # role: parent
SIZE = "Size (MB)"  # role: value

# Data: replace this block with your own table, for example df = pd.read_csv("files.csv")
# Leaves carry a size; folders are left empty and sum their children
hierarchy = [
    ("Root", None, None),
    ("Documents", "Root", None),
    ("Pictures", "Root", None),
    ("Music", "Root", None),
    ("Reports", "Documents", None),
    ("Letters", "Documents", None),
    ("Spreadsheets", "Documents", None),
    ("Photos", "Pictures", None),
    ("Screenshots", "Pictures", None),
    ("Icons", "Pictures", None),
    ("Albums", "Music", None),
    ("Playlists", "Music", None),
    ("Podcasts", "Music", None),
    ("Q1_Report", "Reports", 45),
    ("Q2_Report", "Reports", 55),
    ("Q3_Report", "Reports", 50),
    ("Cover_Letter", "Letters", 25),
    ("Resume", "Letters", 35),
    ("Thank_You", "Letters", 20),
    ("Budget", "Spreadsheets", 60),
    ("Forecast", "Spreadsheets", 40),
    ("Analysis", "Spreadsheets", 20),
    ("Photo_1", "Photos", 65),
    ("Photo_2", "Photos", 75),
    ("Photo_3", "Photos", 60),
    ("Screen_1", "Screenshots", 25),
    ("Screen_2", "Screenshots", 25),
    ("Icon_1", "Icons", 15),
    ("Icon_2", "Icons", 15),
    ("Rock", "Albums", 60),
    ("Jazz", "Albums", 55),
    ("Pop", "Albums", 65),
    ("Favorites", "Playlists", 40),
    ("Podcast_1", "Podcasts", 45),
    ("Podcast_2", "Podcasts", 45),
]
df = pd.DataFrame(hierarchy, columns=[NAME, PARENT, SIZE]).astype({SIZE: float})

# Plot: reads only df and the constants above
names = df[NAME].astype(str).tolist()
parents = dict(zip(names, df[PARENT].where(df[PARENT].notna(), None), strict=True))
children = {name: [] for name in names}
for name, parent in parents.items():
    if parent is not None and parent in children:
        children[parent].append(name)
roots = [name for name, parent in parents.items() if parent is None or parent not in children]

# Breadth-first order gives each node's depth; reversed, it sums sizes bottom-up
depth = dict.fromkeys(roots, 0)
order = list(roots)
for node in order:
    for child in children[node]:
        depth[child] = depth[node] + 1
        order.append(child)
own_size = dict(zip(names, df[SIZE], strict=True))
total = {}
for node in reversed(order):
    total[node] = np.nansum([total[c] for c in children[node]]) if children[node] else np.nan_to_num(own_size[node])

# Top-down layout: each child takes its share of its parent's horizontal extent
grand_total = sum(total[root] for root in roots)
x0 = {}
cursor = 0.0
for root in roots:
    x0[root] = cursor
    cursor += total[root] / grand_total
for node in order:
    start = x0[node]
    for child in children[node]:
        x0[child] = start
        start += total[child] / grand_total

levels = max(depth.values()) + 1
row_height = 1.0 / levels
row_gap = row_height * 0.04

fig, ax = plt.subplots(figsize=(8, 4.5), dpi=400, facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)
fig.subplots_adjust(left=0.02, right=0.865, top=0.9, bottom=0.03)
ax.set_xlim(0, 1)
ax.set_ylim(0, 1)
ax.axis("off")
fig.canvas.draw()
renderer = fig.canvas.get_renderer()

for node in order:
    width = total[node] / grand_total
    if width <= 0:
        continue
    level = depth[node]
    fill = IMPRINT_PALETTE[level]
    y = 1.0 - (level + 1) * row_height
    ax.add_patch(
        Rectangle(
            (x0[node], y + row_gap / 2), width, row_height - row_gap, facecolor=fill, edgecolor=PAGE_BG, linewidth=1.2
        )
    )

    # Label only where the text fits inside its rectangle: horizontal first, then upright
    red, green, blue = to_rgb(fill)
    text_color = "#1A1A17" if 0.299 * red + 0.587 * green + 0.114 * blue > 0.5 else "#FAF8F1"
    label = ax.text(
        x0[node] + width / 2,
        y + row_height / 2,
        str(node).replace("_", " "),
        ha="center",
        va="center",
        fontsize=9 if level < 2 else 7,
        fontweight="bold" if level < 2 else "normal",
        color=text_color,
    )
    box = ax.transData.transform([(x0[node], y + row_gap / 2), (x0[node] + width, y + row_height - row_gap / 2)])
    room_w, room_h = (box[1] - box[0]) * LABEL_PAD
    extent = label.get_window_extent(renderer)
    if extent.width > room_w or extent.height > room_h:
        label.set_rotation(90)
        extent = label.get_window_extent(renderer)
        if extent.width > room_w * LABEL_PAD or extent.height > room_h:
            label.remove()

# Row captions in the right margin name each hierarchy level
for level in range(levels):
    ax.text(
        1.015,
        1.0 - (level + 0.5) * row_height,
        f"Level {level + 1}",
        transform=ax.transAxes,
        ha="left",
        va="center",
        fontsize=9,
        color=INK_SOFT,
    )

# Style
ax.set_title("icicle-basic · python · matplotlib · anyplot.ai", fontsize=12, fontweight="bold", color=INK, pad=10)

plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
