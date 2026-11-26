"""anyplot.ai
radar-innovation-timeline: Innovation Radar with Time-Horizon Rings
Library: letsplot 4.10.1 | Python 3.13.13
Quality: 85/100 | Updated: 2026-05-29
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
    geom_label,
    geom_path,
    geom_point,
    geom_polygon,
    geom_segment,
    geom_text,
    gggrid,
    ggplot,
    ggsave,
    ggsize,
    labs,
    layer_tooltips,
    scale_color_manual,
    scale_x_continuous,
    scale_y_continuous,
    theme,
    theme_void,
)


LetsPlot.setup_html()

# Theme tokens — Imprint palette + theme-adaptive chrome
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Imprint categorical palette — 8 hues, hybrid-v3 sort
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Columns: set these to your table's column names
NAME = "Technology"  # role: name
RING = "Ring"  # role: ring
SECTOR = "Sector"  # role: sector

# Data: replace this block with your own table, for example df = pd.read_csv("radar.csv")
# Rows are listed ring-first within each sector; the first appearance of each ring (inner to outer)
# and of each sector (around the arc) sets the layout order.
df = pd.DataFrame(
    [
        ("LLM Agents", "Adopt", "AI & ML"),
        ("RAG Pipelines", "Adopt", "AI & ML"),
        ("Vision Models", "Trial", "AI & ML"),
        ("AI Code Review", "Trial", "AI & ML"),
        ("Neuro-symbolic AI", "Assess", "AI & ML"),
        ("Quantum ML", "Hold", "AI & ML"),
        ("mRNA Platforms", "Adopt", "Biotech"),
        ("Gene Editing", "Trial", "Biotech"),
        ("Synthetic Biology", "Trial", "Biotech"),
        ("Digital Twins (Bio)", "Assess", "Biotech"),
        ("Organ-on-Chip", "Assess", "Biotech"),
        ("Nanomedicine", "Hold", "Biotech"),
        ("Carbon Tracking", "Adopt", "Sustainability"),
        ("Green Cloud", "Trial", "Sustainability"),
        ("Circular Design", "Trial", "Sustainability"),
        ("Biodegradable PCBs", "Assess", "Sustainability"),
        ("Ocean Cleanup AI", "Assess", "Sustainability"),
        ("Fusion Energy", "Hold", "Sustainability"),
        ("Edge Computing", "Adopt", "Infrastructure"),
        ("WebAssembly", "Adopt", "Infrastructure"),
        ("Service Mesh", "Trial", "Infrastructure"),
        ("Satellite Internet", "Trial", "Infrastructure"),
        ("Confidential Compute", "Assess", "Infrastructure"),
        ("6G Research", "Hold", "Infrastructure"),
    ],
    columns=[NAME, RING, SECTOR],
)

# Plot
np.random.seed(42)
rings = list(dict.fromkeys(df[RING]))
sectors = list(dict.fromkeys(df[SECTOR]))
n_rings = len(rings)

# Sector colors: Imprint palette positions in canonical order
sector_colors = dict(zip(sectors, IMPRINT_PALETTE, strict=False))

# Ring fills: semantic green -> amber -> ochre -> red gradient communicates adoption readiness
if THEME == "light":
    ring_fill_seq = ["#DCEDC8", "#FFF9C4", "#FFE0B2", "#FFCDD2"]
    ring_alpha = 0.55
else:
    # Imprint-derived tints at low alpha for dark background
    ring_fill_seq = ["#009E73", "#DDCC77", "#BD8233", "#AE3030"]
    ring_alpha = 0.14

ring_inner = {r: 0.5 + i for i, r in enumerate(rings)}
ring_outer = {r: 1.5 + i for i, r in enumerate(rings)}
ring_fills = {r: ring_fill_seq[i % len(ring_fill_seq)] for i, r in enumerate(rings)}
# Angular nudge for the outermost ring to prevent overlap with sector header labels
ring_nudge = {r: (0.20 if i == n_rings - 1 else 0.0) for i, r in enumerate(rings)}

# 270-degree arc (gap at top for ring labels)
ARC_START = math.pi * 3 / 4
ARC_SPAN = math.pi * 3 / 2
ARC_END = ARC_START + ARC_SPAN
SECTOR_SPAN = ARC_SPAN / len(sectors)
R_MAX = ring_outer[rings[-1]]

# --- Compute positions ---
sector_idx_map = {s: i for i, s in enumerate(sectors)}
ring_mid_map = {r: (ring_inner[r] + ring_outer[r]) / 2 for r in rings}

# Angular placement per sector/ring group
angles = np.zeros(len(df))
for (sector, ring), group in df.groupby([SECTOR, RING], sort=False):
    center = ARC_START + sector_idx_map[sector] * SECTOR_SPAN + SECTOR_SPAN / 2
    n = len(group)
    spread = SECTOR_SPAN * 0.72
    offsets = np.linspace(-spread / 2, spread / 2, n) if n > 1 else np.array([0.0])
    angles[df.index.get_indexer(group.index)] = center + offsets + ring_nudge[ring]

df["angle"] = angles
df["radius"] = df[RING].map(ring_mid_map) + np.random.uniform(-0.15, 0.15, len(df))
df["x"] = df["radius"] * np.cos(df["angle"])
df["y"] = df["radius"] * np.sin(df["angle"])

# Label positions: pushed radially outward, less for outer rings
label_offsets = {r: 0.72 - 0.10 * i for i, r in enumerate(rings)}
df["label_r"] = df["radius"] + df[RING].map(label_offsets)
df["lx"] = df["label_r"] * np.cos(df["angle"])
df["ly"] = df["label_r"] * np.sin(df["angle"])
df["side"] = np.where(df["lx"] < 0, "left", "right")

# Label repulsion: push overlapping labels apart vertically on each side
MIN_Y_SEP = 0.9
for _ in range(60):
    for side in ["left", "right"]:
        side_idx = df.loc[df["side"] == side].sort_values("ly").index.tolist()
        for k in range(len(side_idx) - 1):
            i, j = side_idx[k], side_idx[k + 1]
            if abs(df.loc[j, "lx"] - df.loc[i, "lx"]) < 3.6:
                dy = df.loc[j, "ly"] - df.loc[i, "ly"]
                if dy < MIN_Y_SEP:
                    push = (MIN_Y_SEP - dy) / 2
                    df.loc[j, "ly"] += push
                    df.loc[i, "ly"] -= push

# --- Structural geometry ---
arc_pts = np.linspace(ARC_START, ARC_END, 120)

# Ring background polygons (annular sectors)
ring_bg_rows = []
for rname in rings:
    r_in, r_out = ring_inner[rname], ring_outer[rname]
    xs = np.concatenate([r_out * np.cos(arc_pts), r_in * np.cos(arc_pts[::-1])])
    ys = np.concatenate([r_out * np.sin(arc_pts), r_in * np.sin(arc_pts[::-1])])
    for px, py in zip(np.append(xs, xs[0]), np.append(ys, ys[0]), strict=True):
        ring_bg_rows.append({"x": px, "y": py, "ring": rname})
ring_bg_df = pd.DataFrame(ring_bg_rows)

# Ring boundary arcs
bnd_rows = []
for r in [0.5] + [ring_outer[r] for r in rings]:
    for idx, a in enumerate(arc_pts):
        bnd_rows.append({"x": r * math.cos(a), "y": r * math.sin(a), "g": f"r{r}", "o": idx})
bnd_df = pd.DataFrame(bnd_rows).sort_values(["g", "o"])

# Sector divider spokes
spoke_angles = [ARC_START + i * SECTOR_SPAN for i in range(len(sectors) + 1)]
spoke_df = pd.DataFrame(
    [
        {"x": 0.5 * math.cos(a), "y": 0.5 * math.sin(a), "xend": R_MAX * math.cos(a), "yend": R_MAX * math.sin(a)}
        for a in spoke_angles
    ]
)

# Sector header labels along outer edge
sector_label_df = pd.DataFrame(
    [
        {
            "label": s,
            "x": (R_MAX + 1.7) * math.cos(ARC_START + (i + 0.5) * SECTOR_SPAN),
            "y": (R_MAX + 1.7) * math.sin(ARC_START + (i + 0.5) * SECTOR_SPAN),
        }
        for i, s in enumerate(sectors)
    ]
)

# Ring name labels in arc gap (90 degrees = top center)
gap_angle = math.pi / 2
ring_label_df = pd.DataFrame(
    [
        {"label": r, "x": ring_mid_map[r] * math.cos(gap_angle), "y": ring_mid_map[r] * math.sin(gap_angle)}
        for r in rings
    ]
)

# --- Build plot ---
plot = ggplot()

# Ring background fills with semantic color gradient (green=safe → pink=risky)
for rname in rings:
    rdata = ring_bg_df[ring_bg_df["ring"] == rname]
    plot += geom_polygon(aes("x", "y"), data=rdata, fill=ring_fills[rname], alpha=ring_alpha)

# Structural lines: ring boundaries and sector spokes
plot += geom_path(aes("x", "y", group="g"), data=bnd_df, color=INK_SOFT, size=0.3, alpha=0.5)
plot += geom_segment(aes(x="x", y="y", xend="xend", yend="yend"), data=spoke_df, color=INK_SOFT, size=0.3, alpha=0.5)

# Sector header labels
plot += geom_text(aes("x", "y", label="label"), data=sector_label_df, size=5, color=INK, fontface="bold")

# Ring labels with background box (geom_label for visual clarity over ring fills)
plot += geom_label(
    aes("x", "y", label="label"),
    data=ring_label_df,
    size=4,
    color=INK_SOFT,
    fontface="bold",
    fill=ELEVATED_BG,
    alpha=0.9,
)

# Thin connector lines from points to labels (aids readability after repulsion)
plot += geom_segment(aes(x="x", y="y", xend="lx", yend="ly"), data=df, size=0.3, alpha=0.25, color=INK_MUTED)

# Innovation points with interactive tooltips (letsplot-specific for HTML export)
plot += geom_point(
    aes("x", "y", color=SECTOR),
    data=df,
    size=4,
    alpha=0.9,
    tooltips=layer_tooltips().line(f"@{{{NAME}}}").line(f"{RING}: @{{{RING}}}").line(f"{SECTOR}: @{{{SECTOR}}}"),
)

# Innovation labels split by side for outward text alignment
for side, hj in [("left", 1), ("right", 0)]:
    side_df = df[df["side"] == side]
    plot += geom_text(aes("lx", "ly", label=NAME, color=SECTOR), data=side_df, size=5, hjust=hj)

title = "radar-innovation-timeline · python · letsplot · anyplot.ai"

# Styling — theme_void() removes all axis/grid defaults; custom theme restores chrome
plot += (
    theme_void()
    + scale_color_manual(values=sector_colors)
    + scale_x_continuous(limits=(-6.6, 6.6))
    + scale_y_continuous(limits=(-6.0, 5.4))
    + coord_fixed()
    + labs(title=title, color=SECTOR)
    + theme(
        plot_title=element_text(size=16, color=INK, face="bold"),
        legend_title=element_text(size=12, color=INK),
        legend_text=element_text(size=10, color=INK_SOFT),
        legend_position="bottom",
        axis_title=element_blank(),
        axis_text=element_blank(),
        axis_ticks=element_blank(),
        axis_line=element_blank(),
        panel_grid=element_blank(),
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT),
    )
)

# One-panel grid paints the whole square canvas with the page color (coord_fixed leaves strips otherwise)
plot = gggrid([plot]) + ggsize(600, 600) + theme(plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG))

# Save PNG (scale=4 → 2400×2400 px) and interactive HTML
ggsave(plot, f"plot-{THEME}.png", path=".", scale=4)
ggsave(plot, f"plot-{THEME}.html", path=".")
