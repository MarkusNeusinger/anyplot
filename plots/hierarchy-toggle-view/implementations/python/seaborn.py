""" anyplot.ai
hierarchy-toggle-view: Interactive Treemap-Sunburst Toggle View
Library: seaborn 0.13.2 | Python 3.13.13
Quality: 75/100 | Updated: 2026-05-19
"""

import os

import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from matplotlib.patches import FancyBboxPatch, Wedge


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

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
        "grid.color": INK,
        "grid.alpha": 0.10,
        "legend.facecolor": ELEVATED_BG,
        "legend.edgecolor": INK_SOFT,
    },
)

# Okabe-Ito palette — first series always #009E73
IMPRINT = ["#009E73", "#C475FD", "#4467A3", "#BD8233"]

# Data: software project budget allocation (3 levels, 17 nodes)
data = [
    {"id": "root", "parent": "", "label": "Budget", "value": 1350},
    {"id": "dev", "parent": "root", "label": "Development", "value": 600},
    {"id": "infra", "parent": "root", "label": "Infrastructure", "value": 310},
    {"id": "ops", "parent": "root", "label": "Operations", "value": 240},
    {"id": "research", "parent": "root", "label": "Research", "value": 200},
    {"id": "frontend", "parent": "dev", "label": "Frontend", "value": 180},
    {"id": "backend", "parent": "dev", "label": "Backend", "value": 220},
    {"id": "mobile", "parent": "dev", "label": "Mobile", "value": 120},
    {"id": "qa", "parent": "dev", "label": "QA", "value": 80},
    {"id": "cloud", "parent": "infra", "label": "Cloud", "value": 150},
    {"id": "security", "parent": "infra", "label": "Security", "value": 90},
    {"id": "database", "parent": "infra", "label": "Database", "value": 70},
    {"id": "support", "parent": "ops", "label": "Support", "value": 100},
    {"id": "monitoring", "parent": "ops", "label": "Monitoring", "value": 60},
    {"id": "devops", "parent": "ops", "label": "DevOps", "value": 80},
    {"id": "ml", "parent": "research", "label": "ML/AI", "value": 130},
    {"id": "proto", "parent": "research", "label": "Prototyping", "value": 70},
]

df = pd.DataFrame(data)

# Build hierarchy lookup
children = {}
for _, row in df.iterrows():
    if row["parent"]:
        children.setdefault(row["parent"], []).append(row["id"])

# Color map: Okabe-Ito for level-1 nodes, same color inherited by children
level1_ids = ["dev", "infra", "ops", "research"]
color_map = {nid: IMPRINT[i] for i, nid in enumerate(level1_ids)}
for nid in level1_ids:
    for cid in children.get(nid, []):
        color_map[cid] = color_map[nid]

# Plot
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 9))
fig.patch.set_facecolor(PAGE_BG)

# === LEFT: TREEMAP VIEW ===
ax1.set_xlim(0, 100)
ax1.set_ylim(0, 100)
ax1.set_aspect("equal")
ax1.axis("off")
ax1.set_facecolor(PAGE_BG)

l1_values = [df[df["id"] == nid]["value"].iloc[0] for nid in level1_ids]
l1_total = sum(l1_values)
margin = 2
l1_x = margin

for i, nid in enumerate(level1_ids):
    l1_width = (100 - 2 * margin) * (l1_values[i] / l1_total)

    ax1.add_patch(
        FancyBboxPatch(
            (l1_x, margin),
            l1_width,
            100 - 2 * margin,
            boxstyle="round,pad=0.02,rounding_size=1.5",
            facecolor=color_map[nid],
            edgecolor=PAGE_BG,
            linewidth=3,
            alpha=0.35,
        )
    )

    if nid in children:
        c_ids = children[nid]
        c_values = [df[df["id"] == cid]["value"].iloc[0] for cid in c_ids]
        c_total = sum(c_values)
        c_y = margin + 3

        for j, cid in enumerate(c_ids):
            c_height = (100 - 2 * margin - 6) * (c_values[j] / c_total)
            ax1.add_patch(
                FancyBboxPatch(
                    (l1_x + 2, c_y),
                    l1_width - 4,
                    c_height - 1,
                    boxstyle="round,pad=0.01,rounding_size=0.8",
                    facecolor=color_map[cid],
                    edgecolor=PAGE_BG,
                    linewidth=2,
                    alpha=0.9,
                )
            )

            c_label = df[df["id"] == cid]["label"].iloc[0]
            if c_height > 10 and l1_width > 12:
                ax1.text(
                    l1_x + l1_width / 2,
                    c_y + c_height / 2,
                    f"{c_label}\n${c_values[j]}K",
                    ha="center",
                    va="center",
                    fontsize=13,
                    fontweight="bold",
                    color="white",
                )
            c_y += c_height

    cat_label = df[df["id"] == nid]["label"].iloc[0]
    if l1_width > 20:
        label_text = f"{cat_label}: ${l1_values[i]}K"
    elif l1_width > 10:
        label_text = f"${l1_values[i]}K"
    else:
        label_text = None
    if label_text:
        ax1.text(
            l1_x + l1_width / 2,
            margin + 2,
            label_text,
            ha="center",
            va="bottom",
            fontsize=11,
            fontweight="bold",
            color="white",
            bbox={"boxstyle": "round,pad=0.2", "facecolor": color_map[nid], "alpha": 0.85},
        )

    l1_x += l1_width

ax1.set_title("Treemap View", fontsize=20, fontweight="bold", pad=15, color=INK)

# === RIGHT: SUNBURST VIEW ===
ax2.set_xlim(-1.3, 1.3)
ax2.set_ylim(-1.3, 1.3)
ax2.set_aspect("equal")
ax2.axis("off")
ax2.set_facecolor(PAGE_BG)

total_value = df[df["id"] == "root"]["value"].iloc[0]
start_angle = 90
inner_r1, outer_r1 = 0.32, 0.62
inner_r2, outer_r2 = 0.67, 1.05

for i, nid in enumerate(level1_ids):
    ratio = l1_values[i] / total_value
    sweep = 360 * ratio

    ax2.add_patch(
        Wedge(
            (0, 0),
            outer_r1,
            start_angle,
            start_angle + sweep,
            width=outer_r1 - inner_r1,
            facecolor=color_map[nid],
            edgecolor=PAGE_BG,
            linewidth=2.5,
            alpha=0.75,
        )
    )

    if sweep > 30:
        mid_angle = np.radians(start_angle + sweep / 2)
        lx = (inner_r1 + outer_r1) / 2 * np.cos(mid_angle)
        ly = (inner_r1 + outer_r1) / 2 * np.sin(mid_angle)
        angle_deg = (start_angle + sweep / 2) % 360
        text_rot = angle_deg - 180 if 90 < angle_deg <= 270 else angle_deg
        ax2.text(
            lx,
            ly,
            df[df["id"] == nid]["label"].iloc[0],
            ha="center",
            va="center",
            fontsize=14,
            fontweight="bold",
            color="white",
            rotation=text_rot,
        )

    if nid in children:
        c_ids = children[nid]
        c_values = [df[df["id"] == cid]["value"].iloc[0] for cid in c_ids]
        c_total = sum(c_values)
        c_start = start_angle

        for j, cid in enumerate(c_ids):
            c_sweep = sweep * (c_values[j] / c_total)
            ax2.add_patch(
                Wedge(
                    (0, 0),
                    outer_r2,
                    c_start,
                    c_start + c_sweep,
                    width=outer_r2 - inner_r2,
                    facecolor=color_map[cid],
                    edgecolor=PAGE_BG,
                    linewidth=1.5,
                    alpha=0.92,
                )
            )

            if c_sweep > 12:
                c_mid = np.radians(c_start + c_sweep / 2)
                clx = (inner_r2 + outer_r2) / 2 * np.cos(c_mid)
                cly = (inner_r2 + outer_r2) / 2 * np.sin(c_mid)
                angle_deg = (c_start + c_sweep / 2) % 360
                text_rot = angle_deg - 180 if 90 < angle_deg <= 270 else angle_deg
                ax2.text(
                    clx,
                    cly,
                    df[df["id"] == cid]["label"].iloc[0],
                    ha="center",
                    va="center",
                    fontsize=13,
                    fontweight="bold",
                    color="white",
                    rotation=text_rot,
                )

            c_start += c_sweep

    start_angle += sweep

# Center circle showing total
ax2.add_patch(plt.Circle((0, 0), 0.27, color=ELEVATED_BG, zorder=10, ec=INK_SOFT, lw=2))
ax2.text(0, 0.06, "Total", ha="center", va="center", fontsize=14, fontweight="bold", color=INK)
ax2.text(0, -0.08, f"${total_value}K", ha="center", va="center", fontsize=13, color=INK_SOFT)

ax2.set_title("Sunburst View", fontsize=20, fontweight="bold", pad=15, color=INK)

# Style
fig.suptitle("hierarchy-toggle-view · python · seaborn · anyplot.ai", fontsize=24, fontweight="bold", y=0.98, color=INK)

fig.text(
    0.5,
    0.92,
    "Software Project Budget Allocation — Dual Hierarchy View",
    ha="center",
    fontsize=15,
    style="italic",
    color=INK_MUTED,
)

legend_patches = [
    mpatches.Patch(color=color_map[nid], label=df[df["id"] == nid]["label"].iloc[0]) for nid in level1_ids
]
fig.legend(
    handles=legend_patches,
    loc="lower center",
    ncol=4,
    fontsize=14,
    frameon=True,
    fancybox=True,
    facecolor=ELEVATED_BG,
    edgecolor=INK_SOFT,
    labelcolor=INK,
    bbox_to_anchor=(0.5, 0.01),
)

plt.tight_layout(rect=[0, 0.07, 1, 0.90])

# Save
plt.savefig(f"plot-{THEME}.png", dpi=300, bbox_inches="tight", facecolor=PAGE_BG)
