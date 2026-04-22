""" pyplots.ai
radar-innovation-timeline: Innovation Radar with Time-Horizon Rings
Library: letsplot 4.8.2 | Python 3.14.3
Quality: 88/100 | Created: 2026-02-18
"""

import math

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
    ggplot,
    ggsave,
    ggsize,
    labs,
    layer_tooltips,
    scale_color_manual,
    scale_x_continuous,
    scale_y_continuous,
    theme,
)


LetsPlot.setup_html()

np.random.seed(42)

# --- Data ---
rings = ["Adopt", "Trial", "Assess", "Hold"]
# Sector order chosen to separate heavy-label sectors (AI & ML, Infrastructure) across the arc
sectors = ["AI & ML", "Biotech", "Sustainability", "Infrastructure"]
sector_colors = {
    "AI & ML": "#306998",
    "Infrastructure": "#E56910",
    "Biotech": "#D63484",  # Deep pink: high contrast vs blue for colorblind viewers
    "Sustainability": "#00897B",  # Teal: clearly distinct from orange for deuteranopia
}
ring_fills = {"Adopt": "#DCEDC8", "Trial": "#FFF9C4", "Assess": "#FFE0B2", "Hold": "#FFCDD2"}
ring_inner = {"Adopt": 0.5, "Trial": 1.5, "Assess": 2.5, "Hold": 3.5}
ring_outer = {"Adopt": 1.5, "Trial": 2.5, "Assess": 3.5, "Hold": 4.5}
# Angular nudge for Hold ring items to prevent overlap with sector header labels
ring_nudge = {"Adopt": 0.0, "Trial": 0.0, "Assess": 0.0, "Hold": 0.20}

# 270-degree arc (gap at top for ring labels)
ARC_START = math.pi * 3 / 4
ARC_SPAN = math.pi * 3 / 2
ARC_END = ARC_START + ARC_SPAN
SECTOR_SPAN = ARC_SPAN / len(sectors)

innovations = [
    {"name": "LLM Agents", "ring": "Adopt", "sector": "AI & ML"},
    {"name": "RAG Pipelines", "ring": "Adopt", "sector": "AI & ML"},
    {"name": "Vision Models", "ring": "Trial", "sector": "AI & ML"},
    {"name": "AI Code Review", "ring": "Trial", "sector": "AI & ML"},
    {"name": "Neuro-symbolic AI", "ring": "Assess", "sector": "AI & ML"},
    {"name": "Quantum ML", "ring": "Hold", "sector": "AI & ML"},
    {"name": "mRNA Platforms", "ring": "Adopt", "sector": "Biotech"},
    {"name": "Gene Editing", "ring": "Trial", "sector": "Biotech"},
    {"name": "Synthetic Biology", "ring": "Trial", "sector": "Biotech"},
    {"name": "Digital Twins (Bio)", "ring": "Assess", "sector": "Biotech"},
    {"name": "Organ-on-Chip", "ring": "Assess", "sector": "Biotech"},
    {"name": "Nanomedicine", "ring": "Hold", "sector": "Biotech"},
    {"name": "Carbon Tracking", "ring": "Adopt", "sector": "Sustainability"},
    {"name": "Green Cloud", "ring": "Trial", "sector": "Sustainability"},
    {"name": "Circular Design", "ring": "Trial", "sector": "Sustainability"},
    {"name": "Biodegradable PCBs", "ring": "Assess", "sector": "Sustainability"},
    {"name": "Ocean Cleanup AI", "ring": "Assess", "sector": "Sustainability"},
    {"name": "Fusion Energy", "ring": "Hold", "sector": "Sustainability"},
    {"name": "Edge Computing", "ring": "Adopt", "sector": "Infrastructure"},
    {"name": "WebAssembly", "ring": "Adopt", "sector": "Infrastructure"},
    {"name": "Service Mesh", "ring": "Trial", "sector": "Infrastructure"},
    {"name": "Satellite Internet", "ring": "Trial", "sector": "Infrastructure"},
    {"name": "Confidential Compute", "ring": "Assess", "sector": "Infrastructure"},
    {"name": "6G Research", "ring": "Hold", "sector": "Infrastructure"},
]

# --- Compute positions ---
df = pd.DataFrame(innovations)
sector_idx_map = {s: i for i, s in enumerate(sectors)}
ring_mid_map = {r: (ring_inner[r] + ring_outer[r]) / 2 for r in rings}

# Vectorized angular placement per sector/ring group
angles = np.zeros(len(df))
for (sector, ring), group in df.groupby(["sector", "ring"], sort=False):
    center = ARC_START + sector_idx_map[sector] * SECTOR_SPAN + SECTOR_SPAN / 2
    n = len(group)
    spread = SECTOR_SPAN * 0.72
    offsets = np.linspace(-spread / 2, spread / 2, n) if n > 1 else np.array([0.0])
    angles[group.index] = center + offsets + ring_nudge[ring]

df["angle"] = angles
df["radius"] = df["ring"].map(ring_mid_map) + np.random.uniform(-0.15, 0.15, len(df))
df["x"] = df["radius"] * np.cos(df["angle"])
df["y"] = df["radius"] * np.sin(df["angle"])

# Label positions: pushed radially outward (more offset for inner rings)
label_offsets = {"Adopt": 0.72, "Trial": 0.62, "Assess": 0.52, "Hold": 0.42}
df["label_r"] = df["radius"] + df["ring"].map(label_offsets)
df["lx"] = df["label_r"] * np.cos(df["angle"])
df["ly"] = df["label_r"] * np.sin(df["angle"])
df["side"] = np.where(df["lx"] < 0, "left", "right")

# Label repulsion: push overlapping labels apart vertically on each side
MIN_Y_SEP = 0.60
for _ in range(35):
    for side in ["left", "right"]:
        side_idx = df.loc[df["side"] == side].sort_values("ly").index.tolist()
        for k in range(len(side_idx) - 1):
            i, j = side_idx[k], side_idx[k + 1]
            if abs(df.loc[j, "lx"] - df.loc[i, "lx"]) < 2.5:
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
for r in [0.5, 1.5, 2.5, 3.5, 4.5]:
    for idx, a in enumerate(arc_pts):
        bnd_rows.append({"x": r * math.cos(a), "y": r * math.sin(a), "g": f"r{r}", "o": idx})
bnd_df = pd.DataFrame(bnd_rows).sort_values(["g", "o"])

# Sector divider spokes
spoke_angles = [ARC_START + i * SECTOR_SPAN for i in range(len(sectors) + 1)]
spoke_df = pd.DataFrame(
    [
        {"x": 0.5 * math.cos(a), "y": 0.5 * math.sin(a), "xend": 4.5 * math.cos(a), "yend": 4.5 * math.sin(a)}
        for a in spoke_angles
    ]
)

# Sector header labels along outer edge
sector_label_df = pd.DataFrame(
    [
        {
            "label": s,
            "x": 5.5 * math.cos(ARC_START + (i + 0.5) * SECTOR_SPAN),
            "y": 5.5 * math.sin(ARC_START + (i + 0.5) * SECTOR_SPAN),
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
    plot += geom_polygon(aes("x", "y"), data=rdata, fill=ring_fills[rname], alpha=0.55)

# Structural lines: ring boundaries and sector spokes
plot += geom_path(aes("x", "y", group="g"), data=bnd_df, color="#CCCCCC", size=0.3, alpha=0.7)
plot += geom_segment(aes(x="x", y="y", xend="xend", yend="yend"), data=spoke_df, color="#CCCCCC", size=0.3, alpha=0.7)

# Sector header labels
plot += geom_text(aes("x", "y", label="label"), data=sector_label_df, size=15, color="#1A1A1A", fontface="bold")

# Ring labels with background box (letsplot geom_label for visual clarity over ring fills)
plot += geom_label(
    aes("x", "y", label="label"),
    data=ring_label_df,
    size=12,
    color="#555555",
    fontface="bold",
    fill="white",
    alpha=0.85,
)

# Thin connector lines from points to labels (aids readability after repulsion)
plot += geom_segment(aes(x="x", y="y", xend="lx", yend="ly"), data=df, size=0.3, alpha=0.30, color="#888888")

# Innovation points with interactive tooltips (letsplot-specific for HTML export)
plot += geom_point(
    aes("x", "y", color="sector"),
    data=df,
    size=8,
    alpha=0.9,
    tooltips=layer_tooltips().line("@name").line("Ring: @ring").line("Sector: @sector"),
)

# Innovation labels split by side for outward text alignment
for side, hj in [("left", 1), ("right", 0)]:
    side_df = df[df["side"] == side]
    plot += geom_text(aes("lx", "ly", label="name", color="sector"), data=side_df, size=12, hjust=hj)

# Styling
plot += (
    scale_color_manual(values=sector_colors)
    + scale_x_continuous(limits=(-7.0, 7.0))
    + scale_y_continuous(limits=(-6.8, 5.5))
    + coord_fixed()
    + labs(title="radar-innovation-timeline · letsplot · pyplots.ai", color="Sector")
    + ggsize(1200, 1200)
    + theme(
        plot_title=element_text(size=24, face="bold"),
        legend_title=element_text(size=18),
        legend_text=element_text(size=16),
        legend_position="bottom",
        axis_title=element_blank(),
        axis_text=element_blank(),
        axis_ticks=element_blank(),
        axis_line=element_blank(),
        panel_grid=element_blank(),
        plot_background=element_rect(fill="white", color="white"),
        panel_background=element_rect(fill="white", color="white"),
    )
)

# Save PNG (scale=3 → 3600×3600 px) and interactive HTML
ggsave(plot, "plot.png", path=".", scale=3)
ggsave(plot, "plot.html", path=".")
