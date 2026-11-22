"""anyplot.ai
network-hierarchical: Hierarchical Network Graph with Tree Layout
Library: matplotlib 3.10.9 | Python 3.13.13
Quality: 92/100 | Updated: 2026-05-17
"""

import os

import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: one position per level, in canonical order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Constants
LEVEL_NAMES = ["Root module", "Core modules", "Sub-modules", "Leaf modules"]  # legend text per level, root first
TEXT_ON_NODE = ["#FFFFFF", "#1A1A17", "#FFFFFF", "#1A1A17"]  # label color with enough contrast on each level's fill
NODE_AREA = [1500, 1250, 1100, 750]  # marker area in points^2 per level, shrinking with depth
LABEL_SIZE = [10, 9, 7, 7]  # label font size in points per level

# Columns: set these to your table's column names
MODULE = "Module"  # role: nodes
PARENT = "Parent module"  # role: edges
LEVEL = "Level"  # role: level

# Data: replace this block with your own table, for example df = pd.read_csv("modules.csv")
# One row per node; the parent column holds the parent's name (empty for the root).
df = pd.DataFrame(
    {
        MODULE: [
            "App",
            "Core",
            "UI",
            "Data",
            "Utils",
            "Auth",
            "Config",
            "Widget",
            "Theme",
            "Models",
            "Store",
            "Logger",
            "Helper",
            "Login",
            "Sess",
            "Btns",
            "Forms",
            "Grid",
            "User",
            "Prod",
            "Cache",
            "DB",
            "REST",
            "Fmt",
        ],
        PARENT: [
            None,
            "App",
            "App",
            "App",
            "App",
            "Core",
            "Core",
            "UI",
            "UI",
            "Data",
            "Data",
            "Utils",
            "Utils",
            "Auth",
            "Auth",
            "Widget",
            "Widget",
            "Theme",
            "Models",
            "Models",
            "Store",
            "Store",
            "Logger",
            "Helper",
        ],
        LEVEL: [0] + [1] * 4 + [2] * 8 + [3] * 11,
    }
)

# Plot: tree layout computed from df only
children = {name: [] for name in df[MODULE]}
for name, parent in zip(df[MODULE], df[PARENT], strict=True):
    if pd.notna(parent):
        children[parent].append(name)
roots = df.loc[df[PARENT].isna(), MODULE].tolist()
level_of = dict(zip(df[MODULE], df[LEVEL], strict=True))
max_level = int(df[LEVEL].max())

# Leaves take consecutive slots in depth-first order; each parent centers over its children
pos = {}
leaves = []


def place(name):
    if children[name]:
        xs = [place(child) for child in children[name]]
        x = float(np.mean(xs))
    else:
        x = float(len(leaves))
        leaves.append(name)
    pos[name] = (x, max_level - level_of[name])
    return x


for root in roots:
    place(root)
slot = len(leaves)

title = "Software Module Hierarchy · network-hierarchical · python · matplotlib · anyplot.ai"
title_fontsize = max(8, round(12 * 67 / len(title))) if len(title) > 67 else 12

fig, ax = plt.subplots(figsize=(8, 4.5), dpi=400, facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

# Edges: thin, soft straight lines from parent to child
for name, parent in zip(df[MODULE], df[PARENT], strict=True):
    if pd.notna(parent):
        (x1, y1), (x2, y2) = pos[parent], pos[name]
        ax.plot([x1, x2], [y1, y2], color=INK_SOFT, linewidth=1.2, alpha=0.45, zorder=1, solid_capstyle="round")

# Nodes and labels, colored and sized by level
for name, (x, y) in pos.items():
    level = level_of[name]
    ax.scatter(
        x, y, s=NODE_AREA[level], color=IMPRINT_PALETTE[level], edgecolors=PAGE_BG, linewidths=1.2, zorder=10 + level
    )
    ax.text(
        x,
        y,
        name,
        ha="center",
        va="center",
        fontsize=LABEL_SIZE[level],
        fontweight="bold",
        color=TEXT_ON_NODE[level],
        zorder=20 + level,
    )

legend_handles = [
    mpatches.Patch(color=IMPRINT_PALETTE[level], label=LEVEL_NAMES[level]) for level in range(max_level + 1)
]
leg = ax.legend(handles=legend_handles, loc="upper left", fontsize=8, frameon=True, framealpha=1.0)
leg.get_frame().set_facecolor(ELEVATED_BG)
leg.get_frame().set_edgecolor(INK_SOFT)
plt.setp(leg.get_texts(), color=INK_SOFT)

# Style
ax.set_title(title, fontsize=title_fontsize, fontweight="medium", color=INK, pad=10)
ax.set_xlim(-0.8, slot - 1 + 0.8)
ax.set_ylim(-0.6, max_level + 0.6)
ax.axis("off")
fig.subplots_adjust(left=0.02, right=0.98, top=0.92, bottom=0.03)
plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
