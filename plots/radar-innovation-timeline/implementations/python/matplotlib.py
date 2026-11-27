"""anyplot.ai
radar-innovation-timeline: Innovation Radar with Time-Horizon Rings
Library: matplotlib 3.10.9 | Python 3.13.13
Quality: 85/100 | Updated: 2026-05-29
"""

import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.colors import to_rgb
from matplotlib.lines import Line2D


# Theme tokens (Imprint palette — prompts/default-style-guide.md)
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Imprint palette — 8 hues, canonical order, first series always position 1
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Constants
RING_SIZE_RANGE = (110, 50)  # marker area for the innermost and outermost ring
SPREAD_FROM = 2  # a cell with fewer items keeps its marker centred in the sector
INSET_UP_TO = 2  # a cell with this many items or fewer keeps off the sector edges

# Columns: set these to your table's column names
NAME = "Innovation"  # role: name
RING = "Ring"  # role: ring
SECTOR = "Sector"  # role: sector

# Data: replace this block with your own table, for example df = pd.read_csv("radar.csv")
df = pd.DataFrame(
    [
        ("LLM Agents", "Adopt", "AI & ML"),
        ("RAG Pipelines", "Trial", "AI & ML"),
        ("AI Code Assistants", "Trial", "AI & ML"),
        ("Vision Transformers", "Assess", "AI & ML"),
        ("Federated Learning", "Assess", "AI & ML"),
        ("Neuromorphic Chips", "Hold", "AI & ML"),
        ("Kubernetes", "Adopt", "Cloud & Infra"),
        ("FinOps Tooling", "Trial", "Cloud & Infra"),
        ("Edge Computing", "Assess", "Cloud & Infra"),
        ("Platform Engineering", "Assess", "Cloud & Infra"),
        ("Quantum Cloud APIs", "Hold", "Cloud & Infra"),
        ("Serverless Containers", "Hold", "Cloud & Infra"),
        ("Apache Iceberg", "Adopt", "Data Engineering"),
        ("Real-time Lakehouse", "Trial", "Data Engineering"),
        ("Data Contracts", "Trial", "Data Engineering"),
        ("Streaming SQL", "Assess", "Data Engineering"),
        ("Data Mesh", "Hold", "Data Engineering"),
        ("Zero Trust Arch", "Adopt", "Security"),
        ("SBOM Tooling", "Trial", "Security"),
        ("AI Threat Detection", "Assess", "Security"),
        ("Post-Quantum Crypto", "Assess", "Security"),
        ("Confidential Computing", "Hold", "Security"),
        ("Homomorphic Encryption", "Hold", "Security"),
    ],
    columns=[NAME, RING, SECTOR],
)

# Plot: reads only df and the constants above
rings = list(df[RING].unique())  # inner to outer, in the data's order
sectors = list(df[SECTOR].unique())
n_rings = len(rings)
n_sectors = len(sectors)
ring_index = {name: i for i, name in enumerate(rings)}
sector_index = {name: i for i, name in enumerate(sectors)}

# One color and marker shape per sector (Imprint positions in canonical order)
sector_colors = {name: IMPRINT_PALETTE[i % len(IMPRINT_PALETTE)] for i, name in enumerate(sectors)}
marker_shapes = ["o", "s", "D", "^", "v", "P", "X", "h"]
sector_markers = {name: marker_shapes[i % len(marker_shapes)] for i, name in enumerate(sectors)}

# Marker size by ring: near-term prominent, far-future subtle
ring_marker_sizes = dict(zip(rings, np.linspace(*RING_SIZE_RANGE, n_rings), strict=True))

# Layout: 300-degree arc, 60-degree gap for ring labels
arc_span = 5 / 6 * 2 * np.pi
arc_start = np.deg2rad(115)
sector_width = arc_span / n_sectors

# Ring band boundaries: the inner ring starts at 1.5 to give Adopt items arc-space
ring_boundaries = 1.5 + 2.0 * np.arange(n_rings + 1)

# Items per ring-sector cell, and each item's place within its cell
cell = df.groupby([RING, SECTOR], sort=False)[NAME]
df["placed"] = cell.cumcount()
df["total"] = cell.transform("size")

rng = np.random.RandomState(42)
positions = []
for row in df.itertuples(index=False):
    name, ring_name, sector_name, placed, total = row
    r_idx = ring_index[ring_name]
    s_idx = sector_index[sector_name]

    band_width = ring_boundaries[r_idx + 1] - ring_boundaries[r_idx]
    r_lo = ring_boundaries[r_idx] + band_width * 0.25
    r_hi = ring_boundaries[r_idx] + band_width * 0.75
    r = r_lo + (r_hi - r_lo) * (placed + 0.5) / total

    # Angular spread within the sector
    sector_start = arc_start + s_idx * sector_width
    margin = sector_width * 0.08
    a_lo = sector_start + margin
    a_hi = sector_start + sector_width - margin
    if total < SPREAD_FROM:
        frac = 0.5
    else:
        inset = 0.2 if total <= INSET_UP_TO else 0.0
        frac = inset + (1 - 2 * inset) * placed / (total - 1)
    if r_idx % 2 == 1 and total >= SPREAD_FROM:
        frac = 1.0 - frac
    theta = a_lo + (a_hi - a_lo) * frac

    # Minimal jitter, kept inside the cell
    theta += rng.uniform(-0.008, 0.008)
    r += rng.uniform(-0.01, 0.01)

    positions.append((name, theta, r, sector_name, ring_name, placed, total, r_idx))

# Figure — square canvas 2400×2400 px (figsize=(6,6), dpi=400)
fig = plt.figure(figsize=(6, 6), dpi=400, facecolor=PAGE_BG)
ax = fig.add_subplot(111, polar=True)
ax.set_facecolor(PAGE_BG)

# Ring fills — Imprint-tinted pastels (light) / darks (dark) for ring separation
tint = 0.13 if THEME == "light" else 0.14
ring_fill_colors = [
    tuple((1 - tint) * np.array(to_rgb(PAGE_BG)) + tint * np.array(to_rgb(IMPRINT_PALETTE[i % len(IMPRINT_PALETTE)])))
    for i in range(n_rings)
]

for i in range(n_rings):
    theta_fill = np.linspace(arc_start, arc_start + arc_span, 300)
    ax.fill_between(
        theta_fill,
        np.full(300, ring_boundaries[i]),
        np.full(300, ring_boundaries[i + 1]),
        color=ring_fill_colors[i],
        alpha=1.0,
    )

# Ring boundary arcs
for boundary in ring_boundaries:
    theta_arc = np.linspace(arc_start, arc_start + arc_span, 300)
    ax.plot(theta_arc, np.full(300, boundary), color=INK_MUTED, linewidth=0.7, alpha=0.6)

# Sector divider lines
for i in range(n_sectors + 1):
    angle = arc_start + i * sector_width
    ax.plot([angle, angle], [ring_boundaries[0], ring_boundaries[-1]], color=INK_MUTED, linewidth=0.7, alpha=0.6)

# Ring labels in the arc gap — push labels 0.35 rad past arc end to clear the boundary divider
label_angle = arc_start + arc_span + 0.35
for i, ring_name in enumerate(rings):
    r_mid = (ring_boundaries[i] + ring_boundaries[i + 1]) / 2
    ax.text(
        label_angle,
        r_mid,
        ring_name,
        ha="left",
        va="center",
        fontsize=9,
        fontweight="bold",
        color=INK_SOFT,
        fontstyle="italic",
        clip_on=False,
        zorder=10,
    )

# Sector labels along outer edge
for i, sector_name in enumerate(sectors):
    angle = arc_start + (i + 0.5) * sector_width
    ax.text(
        angle,
        ring_boundaries[-1] + 0.50,
        sector_name,
        ha="center",
        va="center",
        fontsize=10,
        fontweight="bold",
        color=INK,
        clip_on=False,
        zorder=10,
    )

# Label background for readability — theme-adaptive elevated surface
label_bbox = {"boxstyle": "round,pad=0.10", "facecolor": ELEVATED_BG, "alpha": 0.92, "edgecolor": "none"}

# Markers and labels
for name, theta, r, sector_name, ring_name, placed, _total, r_idx in positions:
    color = sector_colors[sector_name]
    marker = sector_markers[sector_name]
    msize = ring_marker_sizes[ring_name]

    ax.scatter(theta, r, s=msize, color=color, marker=marker, edgecolors=PAGE_BG, linewidth=0.8, zorder=5, alpha=0.95)

    # Alternate labels above/below their marker, offset in screen points so they clear the marker
    outward = placed % 2 == 0
    if r_idx >= 2:  # Assess / Hold: flip to avoid outer boundary crowding
        outward = not outward
    # Inner rings: smaller font
    label_fontsize = 7 if r_idx <= 1 else 8
    va = "bottom" if outward else "top"

    ax.annotate(
        name,
        xy=(theta, r),
        xytext=(0, 9 if outward else -9),
        textcoords="offset points",
        fontsize=label_fontsize,
        ha="center",
        va=va,
        color=INK,
        fontweight="medium",
        bbox=label_bbox,
        zorder=6,
        annotation_clip=False,
    )

# Style — hide default polar decorations
ax.set_ylim(0, ring_boundaries[-1] + 1.8)
ax.set_yticklabels([])
ax.set_xticklabels([])
ax.set_xticks([])
ax.set_yticks([])
ax.grid(False)
ax.spines["polar"].set_visible(False)

# Title — scale fontsize with title length per prompts/plot-generator.md
title = "radar-innovation-timeline · python · matplotlib · anyplot.ai"
n = len(title)
ratio = 67 / n if n > 67 else 1.0
title_fontsize = max(8, round(12 * ratio))
ax.set_title(title, fontsize=title_fontsize, fontweight="medium", pad=20, color=INK)

# Legend — theme-adaptive frame and text
legend_handles = [
    Line2D(
        [],
        [],
        marker=sector_markers[s],
        linestyle="None",
        markersize=8,
        markerfacecolor=sector_colors[s],
        markeredgecolor=PAGE_BG,
        markeredgewidth=0.8,
        label=s,
    )
    for s in sectors
]
leg = fig.legend(
    handles=legend_handles,
    loc="lower right",
    fontsize=8,
    title=SECTOR,
    title_fontsize=9,
    handletextpad=0.8,
    borderpad=0.8,
    bbox_to_anchor=(0.97, 0.02),
)
if leg:
    leg.get_frame().set_facecolor(ELEVATED_BG)
    leg.get_frame().set_edgecolor(INK_SOFT)
    plt.setp(leg.get_texts(), color=INK_SOFT)
    leg.get_title().set_color(INK_SOFT)

fig.subplots_adjust(left=0.07, right=0.91, top=0.92, bottom=0.08)
plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
