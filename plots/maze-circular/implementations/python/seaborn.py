""" anyplot.ai
maze-circular: Circular Maze Puzzle
Library: seaborn 0.13.2 | Python 3.13.13
Quality: 84/100 | Updated: 2026-05-20
"""

import collections
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
BRAND = "#009E73"  # Okabe-Ito pos 1 — entry
GOAL_COLOR = "#AE3030"  # Okabe-Ito pos 5 — goal star
PATH_COLOR = "#2ABCCD"  # Okabe-Ito pos 6 — solution path

sns.set_theme(
    style="white",
    rc={
        "figure.facecolor": PAGE_BG,
        "axes.facecolor": PAGE_BG,
        "text.color": INK,
        "legend.facecolor": ELEVATED_BG,
        "legend.edgecolor": INK_SOFT,
    },
)

# Maze parameters
np.random.seed(42)
RINGS = 7
SECTORS = 12
SECTOR_ANGLE = 2 * np.pi / SECTORS
TOTAL_CELLS = 1 + RINGS * SECTORS  # center (0) + ring cells


def cell_id(r, s):
    """Ring r (1..RINGS) sector s → cell index. Center = 0."""
    return 1 + (r - 1) * SECTORS + s


# Geometric constants
INNER_R = 0.12
RING_W = (0.82 - INNER_R) / RINGS
OUTER_R = INNER_R + RINGS * RING_W
FRAME_R = OUTER_R + 0.04
WALL_LW = 2.2

# Union-Find with path compression
parent = list(range(TOTAL_CELLS))
uf_rank = [0] * TOTAL_CELLS


def find(x):
    while parent[x] != x:
        parent[x] = parent[parent[x]]
        x = parent[x]
    return x


def union(a, b):
    ra, rb = find(a), find(b)
    if ra == rb:
        return False
    if uf_rank[ra] < uf_rank[rb]:
        ra, rb = rb, ra
    parent[rb] = ra
    if uf_rank[ra] == uf_rank[rb]:
        uf_rank[ra] += 1
    return True


# Build walls: radial (ring-to-ring) and circular (sector-to-sector within ring)
walls = []
for r in range(RINGS):
    for s in range(SECTORS):
        c1 = 0 if r == 0 else cell_id(r, s)
        c2 = cell_id(r + 1, s)
        walls.append(("radial", r, s, c1, c2))

for r in range(1, RINGS + 1):
    for s in range(SECTORS):
        c1 = cell_id(r, s)
        c2 = cell_id(r, (s + 1) % SECTORS)
        walls.append(("circular", r, s, c1, c2))

np.random.shuffle(walls)

# Kruskal's spanning tree — guarantees exactly one solution
passages = set()
adjacency = collections.defaultdict(set)
for wall in walls:
    wtype, r, s, c1, c2 = wall
    if union(c1, c2):
        passages.add((wtype, r, s))
        adjacency[c1].add(c2)
        adjacency[c2].add(c1)

# BFS from entry cell to center for solution path
ENTRY_SECTOR = 0
entry_cell = cell_id(RINGS, ENTRY_SECTOR)
goal_cell = 0

bfs_q = collections.deque([entry_cell])
prev = {entry_cell: None}
while bfs_q:
    curr = bfs_q.popleft()
    if curr == goal_cell:
        break
    for nxt in sorted(adjacency[curr]):
        if nxt not in prev:
            prev[nxt] = curr
            bfs_q.append(nxt)

solution_path = []
node = goal_cell
while node is not None:
    solution_path.append(node)
    node = prev.get(node)
solution_path.reverse()


def cell_center(cell):
    """(x, y) of cell center in normalized coordinates."""
    if cell == 0:
        return 0.0, 0.0
    idx = cell - 1
    r = idx // SECTORS + 1
    s = idx % SECTORS
    radius = INNER_R + (r - 0.5) * RING_W
    angle = (s + 0.5) * SECTOR_ANGLE
    return radius * np.cos(angle), radius * np.sin(angle)


# ---- Drawing ----
fig, ax = plt.subplots(figsize=(6, 6), dpi=400, facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)
ax.set_aspect("equal")

# Center zone
center_circle = mpatches.Circle((0, 0), INNER_R, facecolor=ELEVATED_BG, edgecolor=INK, linewidth=WALL_LW, zorder=2)
ax.add_patch(center_circle)

# Circular arc walls at each ring boundary r=1..RINGS (smooth vector arcs)
for r in range(1, RINGS + 1):
    radius = INNER_R + r * RING_W
    for s in range(SECTORS):
        if ("circular", r, s) not in passages:
            t1 = np.degrees(s * SECTOR_ANGLE)
            t2 = np.degrees((s + 1) * SECTOR_ANGLE)
            arc = mpatches.Arc(
                (0, 0), 2 * radius, 2 * radius, theta1=t1, theta2=t2, color=INK, linewidth=WALL_LW, zorder=3
            )
            ax.add_patch(arc)

# Outer boundary frame with entry gap
entry_angle_mid = (ENTRY_SECTOR + 0.5) * SECTOR_ANGLE
gap_half_rad = SECTOR_ANGLE * 0.32
gap_start_deg = np.degrees(entry_angle_mid - gap_half_rad)
gap_end_deg = np.degrees(entry_angle_mid + gap_half_rad)
frame_arc = mpatches.Arc(
    (0, 0),
    2 * FRAME_R,
    2 * FRAME_R,
    theta1=gap_end_deg,
    theta2=gap_start_deg + 360,
    color=INK,
    linewidth=WALL_LW + 0.5,
    zorder=4,
)
ax.add_patch(frame_arc)

# Radial walls (smooth vector line segments)
for r in range(RINGS):
    r_inner = INNER_R + r * RING_W
    r_outer = INNER_R + (r + 1) * RING_W
    for s in range(SECTORS):
        if ("radial", r, s) not in passages:
            angle = s * SECTOR_ANGLE
            x1, y1 = r_inner * np.cos(angle), r_inner * np.sin(angle)
            x2, y2 = r_outer * np.cos(angle), r_outer * np.sin(angle)
            ax.plot([x1, x2], [y1, y2], color=INK, linewidth=WALL_LW, zorder=3, solid_capstyle="round")

# Solution path — seaborn lineplot traces BFS solution through cell centers
px = [cell_center(c)[0] for c in solution_path]
py = [cell_center(c)[1] for c in solution_path]
path_df = pd.DataFrame({"x": px, "y": py})
sns.lineplot(
    data=path_df,
    x="x",
    y="y",
    ax=ax,
    color=PATH_COLOR,
    linewidth=2.2,
    alpha=0.65,
    zorder=2,
    label="Solution Path",
    sort=False,
    estimator=None,
)

# Entry marker — seaborn scatterplot
ex = (FRAME_R + 0.07) * np.cos(entry_angle_mid)
ey = (FRAME_R + 0.07) * np.sin(entry_angle_mid)
entry_df = pd.DataFrame({"x": [ex], "y": [ey]})
sns.scatterplot(data=entry_df, x="x", y="y", ax=ax, color=BRAND, s=120, zorder=7, label="Entry Point")

ax.annotate(
    "START",
    xy=(ex, ey),
    xytext=(ex + 0.17, ey + 0.04),
    fontsize=8,
    fontweight="bold",
    ha="left",
    va="center",
    color=BRAND,
    bbox={"boxstyle": "round,pad=0.3", "facecolor": ELEVATED_BG, "edgecolor": BRAND, "alpha": 0.9},
    arrowprops={"arrowstyle": "-", "color": BRAND, "lw": 0.8},
    zorder=7,
)

# Goal star at center
ax.text(0, 0, "★", fontsize=16, ha="center", va="center", color=GOAL_COLOR, fontweight="bold", zorder=5)

# Legend — combine seaborn-generated handles with manual goal entry
goal_handle = plt.Line2D(
    [0], [0], marker="*", color="w", markerfacecolor=GOAL_COLOR, markersize=10, label="Goal (Center)"
)
handles, labels = ax.get_legend_handles_labels()
handles.append(goal_handle)
labels.append("Goal (Center)")
leg = ax.legend(
    handles=handles,
    labels=labels,
    loc="upper right",
    fontsize=8,
    framealpha=0.95,
    facecolor=ELEVATED_BG,
    edgecolor=INK_SOFT,
    fancybox=True,
    borderpad=0.8,
)
for text in leg.get_texts():
    text.set_color(INK)

# Clean axes
ax.set_xlim(-1.3, 1.3)
ax.set_ylim(-1.3, 1.3)
ax.set_xticks([])
ax.set_yticks([])
ax.set_xlabel("")
ax.set_ylabel("")
for spine in ax.spines.values():
    spine.set_visible(False)

ax.set_title("maze-circular · python · seaborn · anyplot.ai", fontsize=12, fontweight="medium", color=INK, pad=10)

plt.tight_layout()
plt.savefig(f"plot-{THEME}.png", dpi=400, bbox_inches="tight", facecolor=PAGE_BG)
