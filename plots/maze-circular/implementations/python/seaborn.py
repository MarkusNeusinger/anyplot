"""anyplot.ai
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
BRAND = "#009E73"  # Imprint pos 1 — entry
GOAL_COLOR = "#AE3030"  # Imprint pos 5 — goal star
PATH_COLOR = "#2ABCCD"  # Imprint pos 6 — solution path

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

# Constants
WALL_LW = 2.2
ENTRY_SECTOR = 0
RADIAL = "radial"  # wall between ring r and ring r+1
CIRCULAR = "circular"  # wall between sector s and s+1 of ring r

# Columns: set these to your table's column names
WALL_KIND = "Wall type"  # role: extra
RING = "Ring"  # role: rings
SECTOR = "Sector"  # role: extra
OPEN = "Open"  # role: extra

# Data: replace this block with your own table of maze walls, one row per wall
# (RADIAL and CIRCULAR rows mark the two kinds of wall, see Constants)
rng = np.random.default_rng(42)
n_rings, n_sectors = 7, 12
walls = [(RADIAL, r, s) for r in range(n_rings) for s in range(n_sectors)]
walls += [(CIRCULAR, r, s) for r in range(1, n_rings + 1) for s in range(n_sectors)]


def _cell(r, s):
    return 0 if r == 0 else 1 + (r - 1) * n_sectors + s


def _ends(kind, r, s):
    if kind == RADIAL:
        return _cell(r, s), _cell(r + 1, s)
    return _cell(r, s), _cell(r, (s + 1) % n_sectors)


# Kruskal's spanning tree over shuffled walls: exactly one route between any two cells
uf = list(range(1 + n_rings * n_sectors))


def _find(x):
    while uf[x] != x:
        uf[x] = uf[uf[x]]
        x = uf[x]
    return x


is_open = {}
for i in rng.permutation(len(walls)):
    c1, c2 = (_find(c) for c in _ends(*walls[i]))
    is_open[walls[i]] = c1 != c2
    if c1 != c2:
        uf[c1] = c2

df = pd.DataFrame(
    {
        WALL_KIND: [w[0] for w in walls],
        RING: [w[1] for w in walls],
        SECTOR: [w[2] for w in walls],
        OPEN: [is_open[w] for w in walls],
    }
)

# Plot: reads only df and the constants above
RINGS = int(df[RING].max())
SECTORS = int(df[SECTOR].max()) + 1
SECTOR_ANGLE = 2 * np.pi / SECTORS
INNER_R = 0.12
RING_W = (0.82 - INNER_R) / RINGS
FRAME_R = INNER_R + RINGS * RING_W


def cell_id(r, s):
    """Ring r (0 = center cell, 1..RINGS) and sector s to a cell index."""
    return 0 if r == 0 else 1 + (r - 1) * SECTORS + s


def cell_polar(cell):
    """(radius, angle) of a cell center."""
    if cell == 0:
        return 0.0, 0.0
    r, s = divmod(cell - 1, SECTORS)
    return INNER_R + (r + 0.5) * RING_W, (s + 0.5) * SECTOR_ANGLE


# Closed walls get drawn, open ones become adjacency
closed = set(df.loc[~df[OPEN], [WALL_KIND, RING, SECTOR]].itertuples(index=False, name=None))
adjacency = collections.defaultdict(set)
for kind, r, s in df.loc[df[OPEN], [WALL_KIND, RING, SECTOR]].itertuples(index=False):
    c1 = cell_id(r, s)
    c2 = cell_id(r + 1, s) if kind == RADIAL else cell_id(r, (s + 1) % SECTORS)
    adjacency[c1].add(c2)
    adjacency[c2].add(c1)

# BFS from the entry cell to the center
entry_cell = cell_id(RINGS, ENTRY_SECTOR)
prev = {entry_cell: None}
bfs_q = collections.deque([entry_cell])
while bfs_q:
    curr = bfs_q.popleft()
    for nxt in sorted(adjacency[curr]):
        if nxt not in prev:
            prev[nxt] = curr
            bfs_q.append(nxt)
solution_path = []
node = 0
while node is not None:
    solution_path.append(node)
    node = prev.get(node)
solution_path.reverse()

# Solution polyline follows the corridors: radial steps straight, ring steps along the arc
path_pts = []
for a, b in zip(solution_path[:-1], solution_path[1:], strict=True):
    (ra, ta), (rb, tb) = cell_polar(a), cell_polar(b)
    if b == 0:
        tb = ta
    dt = (tb - ta + np.pi) % (2 * np.pi) - np.pi
    for f in np.linspace(0, 1, 24, endpoint=False):
        rad, ang = ra + (rb - ra) * f, ta + dt * f
        path_pts.append((rad * np.cos(ang), rad * np.sin(ang)))
path_pts.append((0.0, 0.0))
path_df = pd.DataFrame(path_pts, columns=["x", "y"])

fig, ax = plt.subplots(figsize=(6, 6), dpi=400, facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)
ax.set_aspect("equal")

# Center zone
ax.add_patch(mpatches.Circle((0, 0), INNER_R, facecolor=ELEVATED_BG, edgecolor="none", zorder=2))

# Walls between ring r and ring r+1 are arcs (r = 0 is the center circle)
for r in range(RINGS):
    radius = INNER_R + r * RING_W
    for s in range(SECTORS):
        if (RADIAL, r, s) in closed:
            t1 = np.degrees(s * SECTOR_ANGLE)
            t2 = np.degrees((s + 1) * SECTOR_ANGLE)
            ax.add_patch(
                mpatches.Arc(
                    (0, 0), 2 * radius, 2 * radius, theta1=t1, theta2=t2, color=INK, linewidth=WALL_LW, zorder=3
                )
            )

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

# Walls between sector s and s+1 inside ring r are straight line segments
for r in range(1, RINGS + 1):
    r_inner = INNER_R + (r - 1) * RING_W
    r_outer = INNER_R + r * RING_W
    for s in range(SECTORS):
        if (CIRCULAR, r, s) in closed:
            angle = (s + 1) * SECTOR_ANGLE
            x1, y1 = r_inner * np.cos(angle), r_inner * np.sin(angle)
            x2, y2 = r_outer * np.cos(angle), r_outer * np.sin(angle)
            ax.plot([x1, x2], [y1, y2], color=INK, linewidth=WALL_LW, zorder=3, solid_capstyle="round")

# Solution path — seaborn lineplot traces BFS solution through cell centers
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
plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
