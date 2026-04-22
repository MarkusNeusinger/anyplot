""" pyplots.ai
radar-innovation-timeline: Innovation Radar with Time-Horizon Rings
Library: plotnine 0.15.3 | Python 3.14.3
Quality: 86/100 | Created: 2026-02-18
"""

import math

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


np.random.seed(42)

# Layout: 270° arc open at bottom
RINGS = ["Adopt", "Trial", "Assess", "Hold"]
R_IN = [0.75, 2.25, 3.75, 5.25]
R_OUT = [2.25, 3.75, 5.25, 6.75]
R_MID = [1.5, 3.0, 4.5, 6.0]
RING_FILL = ["#C8E6C9", "#FFF9C4", "#FFE0B2", "#FFCDD2"]
RING_SIZE = {"Adopt": 7, "Trial": 5.5, "Assess": 4.5, "Hold": 3.5}
RING_ALPHA = {"Adopt": 1.0, "Trial": 0.85, "Assess": 0.7, "Hold": 0.6}

SECTORS = ["AI & ML", "Cloud & Infra", "Data Engineering", "Security"]
SEC_COLOR = {"AI & ML": "#1565C0", "Cloud & Infra": "#00897B", "Data Engineering": "#E65100", "Security": "#AD1457"}

ARC_TOTAL = 1.5 * math.pi  # 270°
ARC_START = -math.pi / 4  # -45°
SEC_SPAN = ARC_TOTAL / len(SECTORS)
SEC_START = {s: ARC_START + i * SEC_SPAN for i, s in enumerate(SECTORS)}

# Innovation data: (name, sector, ring, angular_fraction)
# Fractions tuned to spread labels within each sector and avoid crowding
innovations = [
    ("LLM Agents", "AI & ML", "Adopt", 0.2),
    ("RAG Pipelines", "AI & ML", "Adopt", 0.85),
    ("Vision Transformers", "AI & ML", "Trial", 0.35),
    ("Federated Learning", "AI & ML", "Trial", 0.8),
    ("Neural Arch. Search", "AI & ML", "Assess", 0.5),
    ("Neuromorphic Comp.", "AI & ML", "Hold", 0.15),
    ("Quantum ML", "AI & ML", "Hold", 0.8),
    ("Kubernetes", "Cloud & Infra", "Adopt", 0.5),
    ("WebAssembly", "Cloud & Infra", "Trial", 0.7),
    ("FinOps Platforms", "Cloud & Infra", "Trial", 0.2),
    ("Edge Computing", "Cloud & Infra", "Assess", 0.65),
    ("Serverless Cont.", "Cloud & Infra", "Assess", 0.15),
    ("Confidential Comp.", "Cloud & Infra", "Hold", 0.5),
    ("dbt", "Data Engineering", "Adopt", 0.3),
    ("Apache Iceberg", "Data Engineering", "Adopt", 0.8),
    ("RT Feature Stores", "Data Engineering", "Trial", 0.15),
    ("Data Mesh", "Data Engineering", "Trial", 0.8),
    ("Lakehouse Arch.", "Data Engineering", "Assess", 0.25),
    ("Data Contracts", "Data Engineering", "Assess", 0.8),
    ("Semantic Layer", "Data Engineering", "Hold", 0.5),
    ("Zero Trust", "Security", "Adopt", 0.5),
    ("SBOM Tooling", "Security", "Trial", 0.2),
    ("AI Threat Detect.", "Security", "Trial", 0.75),
    ("Post-Quantum Crypto", "Security", "Assess", 0.45),
    ("Homomorphic Enc.", "Security", "Hold", 0.15),
    ("Deception Tech.", "Security", "Hold", 0.75),
]

# Compute point positions
ri_map = {r: i for i, r in enumerate(RINGS)}
rows = []
for name, sector, ring, frac in innovations:
    ri = ri_map[ring]
    pad = SEC_SPAN * 0.15
    angle = SEC_START[sector] + pad + frac * (SEC_SPAN - 2 * pad)
    r = R_MID[ri] + np.random.uniform(-0.18, 0.18)
    rows.append(
        {
            "name": name,
            "sector": sector,
            "ring": ring,
            "angle": angle,
            "radius": r,
            "x": r * math.cos(angle),
            "y": r * math.sin(angle),
        }
    )

df = pd.DataFrame(rows)
df["ring"] = pd.Categorical(df["ring"], categories=RINGS, ordered=True)

# Ring fill polygons (annular wedges)
arc_angles = np.linspace(ARC_START, ARC_START + ARC_TOTAL, 150)
fill_rows = []
for i, rname in enumerate(RINGS):
    outer = [
        {"x": R_OUT[i] * math.cos(a), "y": R_OUT[i] * math.sin(a), "ring_g": rname, "fc": RING_FILL[i]}
        for a in arc_angles
    ]
    inner = [
        {"x": R_IN[i] * math.cos(a), "y": R_IN[i] * math.sin(a), "ring_g": rname, "fc": RING_FILL[i]}
        for a in reversed(arc_angles)
    ]
    fill_rows.extend(outer + inner)
fill_df = pd.DataFrame(fill_rows)

# Ring boundary arcs
circ_rows = [
    {"x": rb * math.cos(a), "y": rb * math.sin(a), "r": rb} for rb in [0.75, 2.25, 3.75, 5.25, 6.75] for a in arc_angles
]
circ_df = pd.DataFrame(circ_rows)

# Sector spokes
spoke_angles = [ARC_START + i * SEC_SPAN for i in range(len(SECTORS) + 1)]
spoke_df = pd.DataFrame(
    [
        {"x1": 0.75 * math.cos(a), "y1": 0.75 * math.sin(a), "x2": 6.75 * math.cos(a), "y2": 6.75 * math.sin(a)}
        for a in spoke_angles
    ]
)

# Sector header labels
slbl_df = pd.DataFrame(
    [
        {"label": s, "x": 7.8 * math.cos(SEC_START[s] + SEC_SPAN / 2), "y": 7.8 * math.sin(SEC_START[s] + SEC_SPAN / 2)}
        for s in SECTORS
    ]
)

# Ring labels in the bottom gap (270°)
gap_angle = 3 * math.pi / 2
rlbl_df = pd.DataFrame(
    [
        {"label": r, "x": R_MID[i] * math.cos(gap_angle), "y": R_MID[i] * math.sin(gap_angle)}
        for i, r in enumerate(RINGS)
    ]
)

# Innovation labels with text-width-aware collision avoidance
lbl_offset = 0.65
char_w = 0.37  # estimated data units per character at size=11
labels = []
for _, row in df.iterrows():
    lx = (row["radius"] + lbl_offset) * math.cos(row["angle"])
    ly = (row["radius"] + lbl_offset) * math.sin(row["angle"])
    w = len(row["name"]) * char_w
    x_min = lx if lx >= 0 else lx - w
    x_max = (lx + w) if lx >= 0 else lx
    labels.append({"name": row["name"], "x": lx, "y": ly, "sector": row["sector"], "x_min": x_min, "x_max": x_max})

# Iterative nudge: push labels with overlapping bounding boxes apart
min_sep = 0.80
for _ in range(40):
    moved = False
    for i in range(len(labels)):
        for j in range(i + 1, len(labels)):
            x_overlap = labels[i]["x_max"] > labels[j]["x_min"] and labels[j]["x_max"] > labels[i]["x_min"]
            if x_overlap:
                dy = labels[j]["y"] - labels[i]["y"]
                if abs(dy) < min_sep:
                    shift = (min_sep - abs(dy)) / 2
                    labels[i]["y"] -= shift
                    labels[j]["y"] += shift
                    moved = True
    if not moved:
        break

lbl_l_df = pd.DataFrame([lb for lb in labels if lb["x"] >= 0])
lbl_r_df = pd.DataFrame([lb for lb in labels if lb["x"] < 0])

# Build plot
plot = (
    ggplot()
    + geom_polygon(aes(x="x", y="y", group="ring_g", fill="fc"), data=fill_df, size=0, alpha=0.6)
    + scale_fill_identity()
    + geom_path(aes(x="x", y="y", group="r"), data=circ_df, color="#B0B0B0", size=0.5)
    + geom_segment(aes(x="x1", y="y1", xend="x2", yend="y2"), data=spoke_df, color="#B0B0B0", size=0.5)
    + geom_point(aes(x="x", y="y", color="sector", size="ring", alpha="ring"), data=df)
    + scale_size_manual(values=RING_SIZE)
    + scale_alpha_manual(values=RING_ALPHA)
    + geom_text(
        aes(x="x", y="y", label="name", color="sector"),
        data=lbl_l_df,
        size=11,
        ha="left",
        va="center",
        show_legend=False,
    )
    + geom_text(
        aes(x="x", y="y", label="name", color="sector"),
        data=lbl_r_df,
        size=11,
        ha="right",
        va="center",
        show_legend=False,
    )
    + geom_text(aes(x="x", y="y", label="label"), data=slbl_df, size=13, fontweight="bold", color="#222222")
    + geom_text(
        aes(x="x", y="y", label="label"), data=rlbl_df, size=10, fontweight="bold", color="#555555", ha="center"
    )
    + scale_color_manual(values=SEC_COLOR, name="Category")
    + guides(color=guide_legend(override_aes={"size": 5}), size=False, alpha=False)
    + coord_fixed(ratio=1)
    + scale_x_continuous(limits=(-9.5, 9.5))
    + scale_y_continuous(limits=(-7.5, 8))
    + labs(
        title="radar-innovation-timeline \u00b7 plotnine \u00b7 pyplots.ai",
        subtitle="Inner rings \u2192 near-term adoption  \u00b7  Outer rings \u2192 future exploration",
    )
    + theme(
        figure_size=(12, 12),
        plot_title=element_text(size=24, ha="center", weight="bold"),
        plot_subtitle=element_text(size=14, ha="center", color="#666666", style="italic"),
        legend_title=element_text(size=16),
        legend_text=element_text(size=14),
        legend_position=(0.13, 0.10),
        legend_background=element_rect(fill="white", color="#CCCCCC"),
        legend_key=element_rect(fill="white"),
        axis_title=element_blank(),
        axis_text=element_blank(),
        axis_ticks=element_blank(),
        axis_line=element_blank(),
        panel_grid_major=element_blank(),
        panel_grid_minor=element_blank(),
        panel_background=element_rect(fill="white", color="white"),
        plot_background=element_rect(fill="white", color="white"),
        plot_margin=0.02,
    )
)

plot.save("plot.png", dpi=300)
