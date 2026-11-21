"""anyplot.ai
circos-basic: Circos Plot
Library: matplotlib 3.10.9 | Python 3.13.13
Quality: pending | Updated: 2026-05-15
"""

import os

import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.path import Path


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: one position per segment, in canonical order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Constants
GAP_DEGREES = 2  # empty space between neighbouring segments on the outer ring
MAX_RIBBON_HALF_WIDTH = 0.12  # half-width in radians of the strongest connection

# Columns: set these to your table's column names
SOURCE = "Source chromosome"  # role: source
TARGET = "Target chromosome"  # role: target
VALUE = "Synteny blocks"  # role: value
SEGMENT_SIZE = "Size (Mb)"  # role: segment_size
TRACK = "Expression level"  # role: track_data

# Data: replace this block with your own tables, for example df = pd.read_csv("connections.csv")
rng = np.random.default_rng(42)
segment_rows = pd.DataFrame(
    {
        SOURCE: [f"chr{i}" for i in range(1, 9)],
        SEGMENT_SIZE: [200, 180, 160, 140, 120, 100, 80, 60],
        TRACK: rng.uniform(0.4, 0.95, 8).round(2),
    }
)
edge_rows = pd.DataFrame(
    {
        SOURCE: [
            "chr1",
            "chr1",
            "chr1",
            "chr2",
            "chr2",
            "chr3",
            "chr3",
            "chr4",
            "chr4",
            "chr5",
            "chr6",
            "chr7",
            "chr1",
            "chr2",
        ],
        TARGET: [
            "chr2",
            "chr3",
            "chr4",
            "chr3",
            "chr5",
            "chr4",
            "chr6",
            "chr5",
            "chr7",
            "chr6",
            "chr7",
            "chr8",
            "chr8",
            "chr8",
        ],
        VALUE: [25, 18, 12, 22, 15, 20, 10, 16, 8, 14, 12, 9, 11, 7],
    }
)
# One table: connection rows carry no size or track, segment rows carry no target or value
df = pd.concat([edge_rows, segment_rows], ignore_index=True)

# Plot: reads only df and the constants above
edges = df.dropna(subset=[TARGET])
# Every segment named by a row or a connection; a segment without size or track gets the average
names = list(pd.unique(pd.concat([df[SOURCE], df[TARGET]]).dropna()))
segments = (
    df.dropna(subset=[SEGMENT_SIZE])
    .drop_duplicates(SOURCE)
    .set_index(SOURCE)
    .reindex(names)[[SEGMENT_SIZE, TRACK]]
    .astype(float)
)
segments = segments.fillna(segments.mean()).fillna(1.0)
n_segments = len(names)
colors = [IMPRINT_PALETTE[i % len(IMPRINT_PALETTE)] for i in range(n_segments)]
position = {name: i for i, name in enumerate(names)}

# Segment spans in degrees, clockwise from the top, separated by gaps
spans = segments[SEGMENT_SIZE].to_numpy() / segments[SEGMENT_SIZE].sum() * (360 - GAP_DEGREES * n_segments)
starts = 90 - np.concatenate([[0], np.cumsum(spans + GAP_DEGREES)[:-1]])
ends = starts - spans
mids = np.radians((starts + ends) / 2)

R_OUTER, R_INNER = 1.0, 0.85
R_TRACK_OUTER, R_TRACK_INNER = 0.82, 0.70
R_RIBBON = R_INNER - 0.02
N_ARC = 50


def ring_sector(start, end, r_in, r_out):
    """Closed polygon of an annular sector between two angles in degrees."""
    theta = np.radians(np.linspace(end, start, N_ARC))
    return np.concatenate([r_out * np.cos(theta), r_in * np.cos(theta[::-1])]), np.concatenate(
        [r_out * np.sin(theta), r_in * np.sin(theta[::-1])]
    )


fig, ax = plt.subplots(figsize=(6, 6), dpi=400, facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)
ax.set_aspect("equal")
ax.axis("off")
fig.subplots_adjust(left=0.02, right=0.98, top=0.9, bottom=0.17)

for i, name in enumerate(names):
    color = colors[i]

    # Outer ring segment and its label
    x, y = ring_sector(starts[i], ends[i], R_INNER, R_OUTER)
    ax.fill(x, y, color=color, alpha=0.85, edgecolor=PAGE_BG, linewidth=1.0)
    ax.text(
        1.13 * np.cos(mids[i]),
        1.13 * np.sin(mids[i]),
        name,
        fontsize=10,
        fontweight="bold",
        ha="center",
        va="center",
        color=INK,
    )

    # Inner data track: bar height follows the track value
    height = (R_TRACK_OUTER - R_TRACK_INNER) * segments[TRACK].iloc[i]
    x, y = ring_sector(starts[i], ends[i], R_TRACK_INNER, R_TRACK_INNER + height)
    ax.fill(x, y, color=color, alpha=0.5, edgecolor="none")

# Ribbons: width proportional to the connection value, coloured by the source segment
for source, target, value in zip(edges[SOURCE], edges[TARGET], edges[VALUE], strict=True):
    i, j = position[source], position[target]
    half = value / edges[VALUE].max() * MAX_RIBBON_HALF_WIDTH

    a_start, a_end = (
        R_RIBBON * np.array([np.cos(mids[i] - half), np.sin(mids[i] - half)]),
        R_RIBBON * np.array([np.cos(mids[i] + half), np.sin(mids[i] + half)]),
    )
    b_start, b_end = (
        R_RIBBON * np.array([np.cos(mids[j] - half), np.sin(mids[j] - half)]),
        R_RIBBON * np.array([np.cos(mids[j] + half), np.sin(mids[j] + half)]),
    )

    # Control points pulled towards the centre bend the ribbon through the interior
    ctrl_1 = 0.3 * (a_start + b_end) / 2
    ctrl_2 = 0.3 * (a_end + b_start) / 2
    verts = [a_start, ctrl_1, b_end, b_start, ctrl_2, a_end, a_start]
    codes = [Path.MOVETO, Path.CURVE3, Path.CURVE3, Path.LINETO, Path.CURVE3, Path.CURVE3, Path.CLOSEPOLY]
    ax.add_patch(mpatches.PathPatch(Path(verts, codes), facecolor=colors[i], alpha=0.4, edgecolor="none"))

ax.set_xlim(-1.25, 1.25)
ax.set_ylim(-1.25, 1.25)

# Style
fig.suptitle("circos-basic · python · matplotlib · anyplot.ai", fontsize=12, fontweight="medium", color=INK, y=0.96)

legend = fig.legend(
    handles=[mpatches.Patch(facecolor=colors[i], alpha=0.85, label=name) for i, name in enumerate(names)],
    loc="lower center",
    bbox_to_anchor=(0.5, 0.045),
    ncol=4,
    fontsize=8,
    frameon=True,
    fancybox=False,
    title="Chromosome",
    title_fontsize=9,
)
legend.get_frame().set_facecolor(ELEVATED_BG)
legend.get_frame().set_edgecolor(INK_SOFT)
legend.get_frame().set_linewidth(0.8)
plt.setp(legend.get_texts(), color=INK_SOFT)
plt.setp(legend.get_title(), color=INK)

fig.text(
    0.5,
    0.02,
    f"Outer ring: {SEGMENT_SIZE} · inner ring: {TRACK} · ribbons: {VALUE}",
    ha="center",
    va="center",
    fontsize=8,
    color=INK_SOFT,
)
plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
