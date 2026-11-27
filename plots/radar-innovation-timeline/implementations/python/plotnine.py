"""anyplot.ai
radar-innovation-timeline: Innovation Radar with Time-Horizon Rings
Library: plotnine 0.15.4 | Python 3.13.13
Quality: pending | Updated: 2026-05-29
"""

import math
import os

import numpy as np
import pandas as pd
from plotnine import (
    aes,
    coord_fixed,
    element_blank,
    element_rect,
    element_text,
    geom_path,
    geom_point,
    geom_polygon,
    geom_segment,
    geom_text,
    ggplot,
    guide_legend,
    guides,
    labs,
    scale_alpha_manual,
    scale_color_manual,
    scale_fill_identity,
    scale_size_manual,
    scale_x_continuous,
    scale_y_continuous,
    theme,
)


THEME = os.getenv("ANYPLOT_THEME", "light")

# Imprint theme-adaptive chrome
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Imprint palette
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]
ANYPLOT_AMBER = "#DDCC77"

# Constants
# Semantic ring fills, looked up by ring name with a palette fallback: green = ready, amber = trial, ochre = assess, red = hold
RING_FILL_COLOR = {
    "Adopt": IMPRINT_PALETTE[0],
    "Trial": ANYPLOT_AMBER,
    "Assess": IMPRINT_PALETTE[3],
    "Hold": IMPRINT_PALETTE[4],
}
# Semantic sector colors with palette fallback: nature = green, digital = blue, life sciences = rose, industry = ochre
SECTOR_COLOR = {
    "Sustainability": IMPRINT_PALETTE[0],
    "AI & ML": IMPRINT_PALETTE[2],
    "Biotech": IMPRINT_PALETTE[6],
    "Infrastructure": IMPRINT_PALETTE[3],
}
RING_FILL_ALPHA = 0.18 if THEME == "light" else 0.28
ARC_TOTAL = 1.5 * math.pi  # 270 degrees, open at the bottom
ARC_START = -math.pi / 4
R_INNER = 2.3  # hub radius
RING_WIDTH = 1.5

NAME = "Innovation"  # role: name
RING = "Time horizon"  # role: ring
SECTOR = "Category"  # role: sector
ANGLE = "Position in sector"  # role: x_angle

# Data: replace this block with your own table, for example df = pd.read_csv("radar.csv")
items = [
    # (name, sector, ring, angular fraction within the sector)
    ("RAG Pipelines", "AI & ML", "Adopt", 0.10),
    ("LLM Inference Opt.", "AI & ML", "Adopt", 0.92),
    ("Multimodal LLMs", "AI & ML", "Trial", 0.30),
    ("AI Agent Frameworks", "AI & ML", "Trial", 0.80),
    ("Causal AI Systems", "AI & ML", "Assess", 0.25),
    ("Neural Arch. Search", "AI & ML", "Assess", 0.80),
    ("Quantum ML", "AI & ML", "Hold", 0.55),
    ("Carbon Accounting SW", "Sustainability", "Adopt", 0.10),
    ("Energy Analytics", "Sustainability", "Adopt", 0.92),
    ("ESG Data Platforms", "Sustainability", "Trial", 0.20),
    ("Green Code Standards", "Sustainability", "Trial", 0.75),
    ("Carbon-Aware Compute", "Sustainability", "Assess", 0.45),
    ("Atmospheric CO2 Tech", "Sustainability", "Hold", 0.25),
    ("mRNA Therapeutics", "Biotech", "Adopt", 0.10),
    ("CRISPR Diagnostics", "Biotech", "Adopt", 0.92),
    ("Synthetic Biology", "Biotech", "Trial", 0.20),
    ("Lab-Grown Proteins", "Biotech", "Trial", 0.75),
    ("Organoid Platforms", "Biotech", "Assess", 0.30),
    ("Xenotransplantation", "Biotech", "Assess", 0.80),
    ("Age-Reversal Therapy", "Biotech", "Hold", 0.50),
    ("Platform Engineering", "Infrastructure", "Adopt", 0.50),
    ("eBPF Observability", "Infrastructure", "Trial", 0.25),
    ("GitOps at Scale", "Infrastructure", "Trial", 0.75),
    ("Confidential Comput.", "Infrastructure", "Assess", 0.30),
    ("Edge AI Chips", "Infrastructure", "Assess", 0.80),
    ("Photonic Computing", "Infrastructure", "Hold", 0.50),
]
df = pd.DataFrame(items, columns=[NAME, SECTOR, RING, ANGLE])

# Plot
rings = list(dict.fromkeys(df[RING]))
sectors = list(dict.fromkeys(df[SECTOR]))
n_rings, n_sectors = len(rings), len(sectors)
r_in = [R_INNER + i * RING_WIDTH for i in range(n_rings)]
r_out = [r + RING_WIDTH for r in r_in]
r_max = r_out[-1]
sec_span = ARC_TOTAL / n_sectors
sec_start = {s: ARC_START + i * sec_span for i, s in enumerate(sectors)}
sector_color = {s: SECTOR_COLOR.get(s, IMPRINT_PALETTE[i % 8]) for i, s in enumerate(sectors)}
ring_fill = {r: RING_FILL_COLOR.get(r, IMPRINT_PALETTE[i % 8]) for i, r in enumerate(rings)}
ring_size = dict(zip(rings, np.linspace(7, 3.8, n_rings), strict=True))
ring_alpha = dict(zip(rings, np.linspace(1.0, 0.65, n_rings), strict=True))

# Ring fills (annular wedges), ring boundary arcs, sector spokes
arc = np.linspace(ARC_START, ARC_START + ARC_TOTAL, 180)
fill_df = pd.concat(
    [
        pd.DataFrame(
            {
                "x": np.r_[r_out[i] * np.cos(arc), r_in[i] * np.cos(arc[::-1])],
                "y": np.r_[r_out[i] * np.sin(arc), r_in[i] * np.sin(arc[::-1])],
                "ring_g": ring,
                "fc": ring_fill[ring],
            }
        )
        for i, ring in enumerate(rings)
    ]
)
circ_df = pd.concat([pd.DataFrame({"x": rb * np.cos(arc), "y": rb * np.sin(arc), "r": rb}) for rb in r_in + [r_max]])
spoke_angles = np.array([ARC_START + i * sec_span for i in range(n_sectors + 1)])
spoke_df = pd.DataFrame(
    {
        "x1": R_INNER * np.cos(spoke_angles),
        "y1": R_INNER * np.sin(spoke_angles),
        "x2": r_max * np.cos(spoke_angles),
        "y2": r_max * np.sin(spoke_angles),
    }
)

# Sector headers along the outer edge, ring names in the open part of the arc
head_angle = np.array([sec_start[s] + sec_span / 2 for s in sectors])
head_r = r_max + 0.8
head_df = pd.DataFrame({"label": sectors, "x": head_r * np.cos(head_angle), "y": head_r * np.sin(head_angle)})
ring_df = pd.DataFrame({"label": rings, "x": 0.0, "y": [-(r_in[i] + RING_WIDTH / 2) for i in range(n_rings)]})

# Marker layout inside each item's own ring and sector cell. Where it sits in the cell is layout, so for
# every item in turn a search over angle and radius takes the spot nearest its preferred position where
# the label (beside the marker, pointing outward) stays clear of placed labels, markers and sector headers
char_w, text_h, gap, mark_r = 0.18, 0.58, 0.5, 0.5
ring_of = {r: i for i, r in enumerate(rings)}
taken = [
    (h.x - len(h.label) * 0.11 - 0.2, h.x + len(h.label) * 0.11 + 0.2, h.y - 0.5, h.y + 0.5)
    for h in head_df.itertuples()
]
placed, marks = [], []
for _, row in df.sort_values(RING, key=lambda s: -s.map(ring_of)).iterrows():
    ri, w = ring_of[row[RING]], len(row[NAME]) * char_w
    best = None
    for f in np.linspace(0, 1, 26):
        for dr in (0.0, -0.3, 0.3, -0.55, 0.55):
            r = R_INNER + (ri + 0.5) * RING_WIDTH + dr
            pad_a = mark_r * 0.9 / r
            a = sec_start[row[SECTOR]] + pad_a + f * (sec_span - 2 * pad_a)
            x, y = r * np.cos(a), r * np.sin(a)
            for side in (1 if x >= 0 else -1, -1 if x >= 0 else 1):
                x0 = x + gap if side > 0 else x - gap - w
                marker = (x - mark_r, x + mark_r, y - mark_r, y + mark_r)
                boxes = [marker, (x0, x0 + w, y - text_h / 2, y + text_h / 2)]
                hits = sum(
                    1 for b in boxes for t in taken if b[0] < t[1] and t[0] < b[1] and b[2] < t[3] and t[2] < b[3]
                )
                same = sum(
                    1 for t in marks if marker[0] < t[1] and t[0] < marker[1] and marker[2] < t[3] and t[2] < marker[3]
                )
                score = (hits + 5 * same, abs(f - row[ANGLE]) + 0.4 * abs(dr) + 0.5 * (side != (1 if x >= 0 else -1)))
                if best is None or score < best[0]:
                    best = (score, x, y, x0, side, boxes)
    _, x, y, x0, side, boxes = best
    taken += boxes
    marks.append(boxes[0])
    placed.append(
        {
            NAME: row[NAME],
            SECTOR: row[SECTOR],
            RING: row[RING],
            "x": x,
            "y": y,
            "x0": x0,
            "ha": "left" if side > 0 else "right",
        }
    )
pts = pd.DataFrame(placed)
pts["x1"] = pts["x0"] + pts[NAME].str.len() * char_w
pts["lx"] = np.where(pts["ha"] == "left", pts["x0"], pts["x1"])
pts[RING] = pd.Categorical(pts[RING], categories=rings, ordered=True)
lab_right, lab_left = pts[pts["ha"] == "left"], pts[pts["ha"] == "right"]

x_lim = head_df["x"].abs().max() + 1.3
x_lim = max(x_lim, pts[["x0", "x1"]].abs().max().max() + 0.3)
y_top = max(r_max, head_df["y"].max(), pts["y"].max()) + 0.6
y_bot = ring_df["y"].min() - 0.5

plot = (
    ggplot()
    + geom_polygon(aes(x="x", y="y", group="ring_g", fill="fc"), data=fill_df, size=0, alpha=RING_FILL_ALPHA)
    + scale_fill_identity()
    + geom_path(aes(x="x", y="y", group="r"), data=circ_df, color=INK_MUTED, size=0.3)
    + geom_segment(aes(x="x1", y="y1", xend="x2", yend="y2"), data=spoke_df, color=INK_MUTED, size=0.3)
    + geom_point(aes(x="x", y="y", color=SECTOR, size=RING, alpha=RING), data=pts)
    + scale_size_manual(values=ring_size)
    + scale_alpha_manual(values=ring_alpha)
    + geom_text(aes(x="lx", y="y", label=NAME), data=lab_right, size=3.9, ha="left", va="center", color=INK)
    + geom_text(aes(x="lx", y="y", label=NAME), data=lab_left, size=3.9, ha="right", va="center", color=INK)
    + geom_text(aes(x="x", y="y", label="label"), data=head_df, size=5.0, fontweight="bold", color=INK)
    + geom_text(aes(x="x", y="y", label="label"), data=ring_df, size=4.4, fontweight="bold", color=INK_SOFT)
    + scale_color_manual(values=sector_color, limits=sectors, name=SECTOR)
    + guides(color=guide_legend(override_aes={"size": 5}, nrow=1), size=False, alpha=False)
    + coord_fixed(ratio=1)
    + scale_x_continuous(limits=(-x_lim, x_lim), expand=(0, 0))
    + scale_y_continuous(limits=(y_bot, y_top), expand=(0, 0))
    + labs(
        title="radar-innovation-timeline · python · plotnine · anyplot.ai",
        subtitle="Inner rings: near-term adoption  ·  Outer rings: future exploration",
    )
    + theme(
        figure_size=(6, 6),
        plot_title=element_text(size=12, ha="center", weight="bold", color=INK),
        plot_subtitle=element_text(size=9, ha="center", color=INK_SOFT, style="italic"),
        legend_title=element_text(size=9, color=INK),
        legend_text=element_text(size=9, color=INK_SOFT),
        legend_position="bottom",
        legend_background=element_rect(fill=PAGE_BG, color="none"),
        legend_key=element_rect(fill=PAGE_BG, color="none"),
        axis_title=element_blank(),
        axis_text=element_blank(),
        axis_ticks=element_blank(),
        axis_line=element_blank(),
        panel_grid_major=element_blank(),
        panel_grid_minor=element_blank(),
        panel_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        plot_margin=0.02,
    )
)

plot.save(f"plot-{THEME}.png", dpi=400, width=6, height=6, units="in")
