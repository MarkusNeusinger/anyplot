"""anyplot.ai
radar-innovation-timeline: Innovation Radar with Time-Horizon Rings
Library: seaborn 0.13.2 | Python 3.14.10
Quality: pending | Updated: 2026-11-27
"""

import os

import matplotlib.lines as mlines
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from matplotlib.text import Text


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Imprint palette
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

sns.set_theme(
    style="ticks",
    rc={
        "figure.facecolor": PAGE_BG,
        "axes.facecolor": PAGE_BG,
        "axes.edgecolor": INK_SOFT,
        "axes.labelcolor": INK,
        "text.color": INK,
        "xtick.color": INK_SOFT,
        "ytick.color": INK_SOFT,
        "legend.facecolor": ELEVATED_BG,
        "legend.edgecolor": INK_SOFT,
    },
)

# Constants
TOTAL_ANGLE_DEG = 270  # three-quarter layout, the open quarter holds ring labels
START_ANGLE_DEG = 135
ANCHOR_FRAC = {
    "left": 0,
    "bottom": 0,
    "center": 0.5,
    "right": 1,
    "top": 1,
}  # share of a label's size left of / below its anchor
SECTOR_MARKERS = ["o", "s", "D", "^", "P", "X"]
MARKER_AREA_NEAR, MARKER_AREA_FAR = 240, 115  # nearest horizon gets the largest marker
FILL_ALPHA_NEAR, FILL_ALPHA_FAR = 0.03, 0.12  # one neutral tint, deepening with the horizon

# Columns
NAME = "Innovation"  # role: name
RING = "Time horizon"  # role: ring
SECTOR = "Sector"  # role: sector

# Data
# Rows are listed nearest horizon first, so each ring and sector is ordered by first appearance
items = [
    ("AI Triage", "Now", "Healthcare"),
    ("Telehealth", "Now", "Healthcare"),
    ("Wearable ECG", "Near-term", "Healthcare"),
    ("Digital Therapeutics", "Near-term", "Healthcare"),
    ("Gene Editing", "Mid-term", "Healthcare"),
    ("Robotic Surgery", "Mid-term", "Healthcare"),
    ("Brain Interfaces", "Future", "Healthcare"),
    ("EV Charging", "Now", "Mobility"),
    ("Ride Pooling", "Near-term", "Mobility"),
    ("Solid-State Cells", "Near-term", "Mobility"),
    ("Robotaxis", "Mid-term", "Mobility"),
    ("Air Taxis", "Mid-term", "Mobility"),
    ("Hyperloop", "Future", "Mobility"),
    ("Instant Payments", "Now", "Finance"),
    ("Open Banking", "Now", "Finance"),
    ("Tokenized Assets", "Near-term", "Finance"),
    ("Digital Euro", "Mid-term", "Finance"),
    ("Embedded Insurance", "Mid-term", "Finance"),
    ("Quantum-Safe Crypto", "Future", "Finance"),
    ("Smallsat Fleets", "Now", "Space"),
    ("Reusable Rockets", "Near-term", "Space"),
    ("In-Orbit Servicing", "Mid-term", "Space"),
    ("Lunar Logistics", "Mid-term", "Space"),
    ("Space Solar Power", "Future", "Space"),
    ("Asteroid Mining", "Future", "Space"),
]
df = pd.DataFrame(items, columns=[NAME, RING, SECTOR])

# Plot
# Layout: angle by sector cell, radius by ring, spread inside each cell (layout, not data)
rings = list(pd.unique(df[RING]))
sectors = list(pd.unique(df[SECTOR]))
n_rings = len(rings)
n_sectors = len(sectors)
sector_width_deg = TOTAL_ANGLE_DEG / n_sectors
sector_palette = {s: IMPRINT_PALETTE[i % len(IMPRINT_PALETTE)] for i, s in enumerate(sectors)}
sector_markers = {s: SECTOR_MARKERS[i % len(SECTOR_MARKERS)] for i, s in enumerate(sectors)}
size_by_ring = np.linspace(MARKER_AREA_NEAR, MARKER_AREA_FAR, n_rings)
fill_alphas = np.linspace(FILL_ALPHA_NEAR, FILL_ALPHA_FAR, n_rings)
ring_boundaries = np.arange(n_rings + 1) + 0.5
r_max = ring_boundaries[-1]
ring_accent = sns.blend_palette([INK_MUTED, INK_SOFT], n_colors=n_rings + 1)

ANGLE = "angle"
RADIUS = "radius"
SIZE = "size"
ring_idx = df[RING].map({name: i for i, name in enumerate(rings, start=1)})
sector_idx = df[SECTOR].map({name: i for i, name in enumerate(sectors)})
cell_rank = df.groupby([SECTOR, RING]).cumcount()
cell_count = df.groupby([SECTOR, RING])[NAME].transform("size")
cell_frac = (cell_rank + 0.5) / cell_count  # even spread across the cell, margins kept
cell_frac = cell_frac.where(cell_count > 1, 0.32)  # a lone item sits off the sector axis, clear of the header
sector_start = START_ANGLE_DEG - sector_idx * sector_width_deg
df[ANGLE] = np.deg2rad(sector_start - (0.1 + 0.8 * cell_frac) * sector_width_deg)
df[RADIUS] = ring_idx + np.where(cell_rank % 2 == 0, 0.2, -0.2) * (cell_count > 1)
df[SIZE] = ring_idx.map(dict(enumerate(size_by_ring, start=1)))

fig = plt.figure(figsize=(6, 6), dpi=400, facecolor=PAGE_BG)
ax = fig.add_subplot(111, projection="polar")
ax.set_facecolor(PAGE_BG)
ax.set_theta_zero_location("N")
ax.set_theta_direction(-1)
fig.subplots_adjust(left=0.02, right=0.98, top=0.93, bottom=0.16)

# Ring fills (neutral tint, only over the 270° sector span) and boundary lines
theta_fill = np.deg2rad(np.linspace(START_ANGLE_DEG - TOTAL_ANGLE_DEG, START_ANGLE_DEG, 200))
for i in range(n_rings):
    ax.fill_between(
        theta_fill, ring_boundaries[i], ring_boundaries[i + 1], color=INK, alpha=fill_alphas[i], linewidth=0, zorder=0
    )
for i, rb in enumerate(ring_boundaries):
    ax.plot(
        theta_fill,
        np.full_like(theta_fill, rb),
        color=sns.desaturate(ring_accent[i], 0.5),
        linewidth=1.2 if i == 1 else 0.7,
        alpha=0.55,
        zorder=1,
    )

# Sector dividers
for i in range(n_sectors + 1):
    edge = np.deg2rad(START_ANGLE_DEG - i * sector_width_deg)
    ax.plot([edge, edge], [ring_boundaries[0], r_max], color=INK_SOFT, linewidth=0.8, alpha=0.4, zorder=1)

# Items: color + shape by sector, size by time horizon
sns.scatterplot(
    data=df,
    x=ANGLE,
    y=RADIUS,
    hue=SECTOR,
    style=SECTOR,
    size=SIZE,
    sizes=(size_by_ring.min(), size_by_ring.max()),
    markers=sector_markers,
    palette=sector_palette,
    edgecolor=PAGE_BG,
    linewidth=1.2,
    alpha=0.95,
    legend=False,
    ax=ax,
    zorder=5,
)
ax.set_ylim(0, r_max + 0.85)
ax.set_yticks([])
ax.set_xticks([])
ax.set_xlabel("")
ax.set_ylabel("")
ax.grid(False)
ax.spines["polar"].set_visible(False)

# Sector headers along the outer edge
texts = []
for i, sector_name in enumerate(sectors):
    mid = np.deg2rad(START_ANGLE_DEG - (i + 0.5) * sector_width_deg)
    texts.append(
        ax.text(
            mid,
            r_max + 0.6,
            sector_name,
            ha="center",
            va="center",
            fontsize=14,
            fontweight="bold",
            color=sector_palette[sector_name],
            zorder=7,
        )
    )

# Ring names in the open quarter
label_angle = np.deg2rad(START_ANGLE_DEG - TOTAL_ANGLE_DEG - 10)
for r, ring_name in enumerate(rings, start=1):
    texts.append(
        ax.text(
            label_angle,
            r,
            ring_name,
            ha="center",
            va="center",
            fontsize=11,
            fontweight="bold",
            color=INK_SOFT,
            bbox={"boxstyle": "round,pad=0.2", "facecolor": ELEVATED_BG, "edgecolor": "none", "alpha": 0.9},
            zorder=7,
        )
    )

# Directional cues
cue_angle = np.deg2rad(START_ANGLE_DEG - TOTAL_ANGLE_DEG - 26)
texts.append(
    ax.text(
        cue_angle,
        ring_boundaries[0] + 0.1,
        "◂ Ready",
        fontsize=9,
        color=INK_SOFT,
        fontweight="bold",
        ha="center",
        va="center",
        zorder=7,
    )
)
texts.append(
    ax.text(
        cue_angle,
        r_max + 0.2,
        "Emerging ▸",
        fontsize=9,
        color=INK_SOFT,
        fontweight="bold",
        ha="center",
        va="center",
        zorder=7,
    )
)

# Item labels: placed radially outward from each marker, greedy against measured boxes
fig.canvas.draw()
renderer = fig.canvas.get_renderer()
PT = fig.dpi / 72.0
fig_w, fig_h = fig.canvas.get_width_height()
cx, cy = ax.transData.transform((0, 0))
rows = df.sort_values(RADIUS, ascending=True)  # crowded inner items choose their label spot first
placed = [(b.x0, b.y0, b.x1, b.y1) for b in (t.get_window_extent(renderer) for t in texts)]
marker_boxes = []
for _, row in rows.iterrows():
    px, py = ax.transData.transform((row[ANGLE], row[RADIUS]))
    half = (np.sqrt(row[SIZE]) / 2 + 2) * PT
    marker_boxes.append((px - half, py - half, px + half, py + half))
placed += marker_boxes

for k, (_, row) in enumerate(rows.iterrows()):
    px, py = ax.transData.transform((row[ANGLE], row[RADIUS]))
    base = np.arctan2(py - cy, px - cx)
    own = marker_boxes[k]
    best = None
    for dist in [11, 17, 25, 35, 47, 60, 76, 94, 112]:
        for turn in [0, 35, -35, 70, -70, 110, -110, 150, -150, 180]:
            ang = base + np.deg2rad(turn)
            ux, uy = np.cos(ang), np.sin(ang)
            dx, dy = dist * ux, dist * uy
            ha = "left" if ux > 0.35 else ("right" if ux < -0.35 else "center")
            va = "bottom" if uy > 0.35 else ("top" if uy < -0.35 else "center")
            t = ax.annotate(
                row[NAME],
                xy=(row[ANGLE], row[RADIUS]),
                xytext=(dx, dy),
                textcoords="offset points",
                fontsize=9,
                fontweight="medium",
                ha=ha,
                va=va,
                color=INK,
                bbox={"boxstyle": "round,pad=0.18", "facecolor": ELEVATED_BG, "edgecolor": "none", "alpha": 0.9},
                arrowprops={"arrowstyle": "-", "color": INK_SOFT, "linewidth": 0.5},
                zorder=6,
            )
            bb = Text.get_window_extent(t, renderer)  # size of the text alone; its position is set below
            ax_x, ax_y = px + dx * PT, py + dy * PT
            x0 = ax_x - bb.width * ANCHOR_FRAC[ha]
            y0 = ax_y - bb.height * ANCHOR_FRAC[va]
            pad = 2.5 * PT
            box = (x0 - pad, y0 - pad, x0 + bb.width + pad, y0 + bb.height + pad)
            hits = sum(
                not (box[2] < o[0] or o[2] < box[0] or box[3] < o[1] or o[3] < box[1]) for o in placed if o is not own
            )
            # keep labels clear of the title (top) and the legend (bottom) bands
            out = (box[0] < 6 * PT) + (box[2] > fig_w - 6 * PT) + (box[1] < 0.17 * fig_h) + (box[3] > 0.925 * fig_h)
            # the leader runs from the marker edge to the label anchor; count the boxes it crosses
            leader = [(px + f * dx * PT, py + f * dy * PT) for f in np.linspace(0.3, 1, 12)]
            hits += sum(
                any(o[0] <= lx <= o[2] and o[1] <= ly <= o[3] for lx, ly in leader) for o in placed if o is not own
            )
            score = hits + 5 * out + 0.002 * dist + 0.0005 * abs(turn)
            if best is None or score < best[0]:
                if best is not None:
                    best[1].remove()
                best = (score, t, box)
            else:
                t.remove()
            if best[0] < 0.5:
                break
        if best[0] < 0.5:
            break
    placed.append(best[2])

title = "radar-innovation-timeline · python · seaborn · anyplot.ai"
fig.suptitle(title, fontsize=max(8, round(12 * 67 / len(title))), fontweight="medium", color=INK, y=0.97)

# Legend: sectors (shape + color) and time horizons (size)
sector_handles = [
    mlines.Line2D(
        [],
        [],
        linestyle="",
        marker=sector_markers[s],
        markerfacecolor=sector_palette[s],
        markeredgecolor=PAGE_BG,
        markersize=np.sqrt(size_by_ring.max()),
        label=s,
    )
    for s in sectors
]
ring_handles = [
    mlines.Line2D(
        [],
        [],
        linestyle="",
        marker="o",
        markerfacecolor=INK_MUTED,
        markeredgecolor=PAGE_BG,
        markersize=np.sqrt(sz),
        label=name,
    )
    for name, sz in zip(rings, size_by_ring, strict=True)
]
legend = fig.legend(
    handles=sector_handles + ring_handles,
    loc="lower center",
    bbox_to_anchor=(0.5, 0.01),
    ncols=4,
    fontsize=9,
    title="Sectors (shape + color) · Time horizons (marker size)",
    title_fontsize=10,
    framealpha=0.95,
    fancybox=True,
    handletextpad=0.8,
    borderpad=0.9,
)
legend.get_frame().set_facecolor(ELEVATED_BG)

plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
