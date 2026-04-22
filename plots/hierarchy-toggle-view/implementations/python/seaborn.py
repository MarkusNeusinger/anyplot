""" pyplots.ai
hierarchy-toggle-view: Interactive Treemap-Sunburst Toggle View
Library: seaborn 0.13.2 | Python 3.13.11
Quality: 90/100 | Created: 2026-01-11
"""

import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from matplotlib.patches import FancyBboxPatch, Wedge


# Set seaborn style for consistent aesthetics
sns.set_theme(style="white", palette="Set2")
sns.set_context("poster", font_scale=1.0)

# Hierarchical data: Software project budget allocation
# Structure: root -> category -> subcategory (15 nodes, 3 levels)
data = [
    {"id": "root", "parent": "", "label": "Budget", "value": 0},
    # Level 1: Main categories
    {"id": "dev", "parent": "root", "label": "Development", "value": 0},
    {"id": "infra", "parent": "root", "label": "Infrastructure", "value": 0},
    {"id": "ops", "parent": "root", "label": "Operations", "value": 0},
    {"id": "research", "parent": "root", "label": "Research", "value": 0},
    # Level 2: Development subcategories
    {"id": "frontend", "parent": "dev", "label": "Frontend", "value": 180},
    {"id": "backend", "parent": "dev", "label": "Backend", "value": 220},
    {"id": "mobile", "parent": "dev", "label": "Mobile", "value": 120},
    {"id": "qa", "parent": "dev", "label": "QA", "value": 80},
    # Level 2: Infrastructure subcategories
    {"id": "cloud", "parent": "infra", "label": "Cloud", "value": 150},
    {"id": "security", "parent": "infra", "label": "Security", "value": 90},
    {"id": "database", "parent": "infra", "label": "Database", "value": 70},
    # Level 2: Operations subcategories
    {"id": "support", "parent": "ops", "label": "Support", "value": 100},
    {"id": "monitoring", "parent": "ops", "label": "Monitoring", "value": 60},
    {"id": "devops", "parent": "ops", "label": "DevOps", "value": 80},
    # Level 2: Research subcategories
    {"id": "ml", "parent": "research", "label": "ML/AI", "value": 130},
    {"id": "proto", "parent": "research", "label": "Prototyping", "value": 70},
]

df = pd.DataFrame(data)

# Build hierarchy lookup
children = {}
for _, row in df.iterrows():
    parent = row["parent"]
    if parent:
        if parent not in children:
            children[parent] = []
        children[parent].append(row["id"])

# Calculate parent values (sum of children)
for idx, row in df.iterrows():
    node_id = row["id"]
    if node_id in children:
        child_sum = df[df["parent"] == node_id]["value"].sum()
        # For intermediate nodes, recurse
        for child_id in children[node_id]:
            if child_id in children:
                child_sum = sum(df[df["id"] == c]["value"].iloc[0] for c in children[node_id])
        df.at[idx, "value"] = child_sum

# Recalculate for nested structure
df.loc[df["id"] == "dev", "value"] = 600  # 180+220+120+80
df.loc[df["id"] == "infra", "value"] = 310  # 150+90+70
df.loc[df["id"] == "ops", "value"] = 240  # 100+60+80
df.loc[df["id"] == "research", "value"] = 200  # 130+70
df.loc[df["id"] == "root", "value"] = 1350

# Color palette using seaborn - consistent across both views
level1_ids = ["dev", "infra", "ops", "research"]
palette = sns.color_palette("Set2", 4)
color_map = {nid: palette[i] for i, nid in enumerate(level1_ids)}
color_map["root"] = (0.9, 0.9, 0.9)

# Assign same color to children
for nid in level1_ids:
    if nid in children:
        for cid in children[nid]:
            color_map[cid] = color_map[nid]

# Create figure with side-by-side layout (static alternative to toggle)
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 9))

# === LEFT: TREEMAP VIEW ===
ax1.set_xlim(0, 100)
ax1.set_ylim(0, 100)
ax1.set_aspect("equal")
ax1.axis("off")

# Level 1 layout (horizontal slices)
l1_values = [df[df["id"] == nid]["value"].iloc[0] for nid in level1_ids]
l1_total = sum(l1_values)
l1_x = 2
margin = 2

for i, nid in enumerate(level1_ids):
    l1_width = 96 * (l1_values[i] / l1_total)

    # Category background
    rect = FancyBboxPatch(
        (l1_x, margin),
        l1_width,
        96,
        boxstyle="round,pad=0.02,rounding_size=1.5",
        facecolor=color_map[nid],
        edgecolor="white",
        linewidth=3,
        alpha=0.35,
    )
    ax1.add_patch(rect)

    # Draw children as vertical slices within category
    if nid in children:
        c_ids = children[nid]
        c_values = [df[df["id"] == cid]["value"].iloc[0] for cid in c_ids]
        c_total = sum(c_values)
        c_y = margin + 3

        for j, cid in enumerate(c_ids):
            c_height = (96 - 6) * (c_values[j] / c_total)
            child_rect = FancyBboxPatch(
                (l1_x + 2, c_y),
                l1_width - 4,
                c_height - 1,
                boxstyle="round,pad=0.01,rounding_size=0.8",
                facecolor=color_map[cid],
                edgecolor="white",
                linewidth=2,
                alpha=0.9,
            )
            ax1.add_patch(child_rect)

            # Child label
            c_label = df[df["id"] == cid]["label"].iloc[0]
            c_val = c_values[j]
            if c_height > 10 and l1_width > 12:
                ax1.text(
                    l1_x + l1_width / 2,
                    c_y + c_height / 2,
                    f"{c_label}\n${c_val}K",
                    ha="center",
                    va="center",
                    fontsize=12,
                    fontweight="bold",
                    color="white",
                )
            c_y += c_height

    # Category label inside the treemap box (at bottom with darker bg)
    cat_label = df[df["id"] == nid]["label"].iloc[0]
    cat_val = l1_values[i]
    if l1_width > 20:
        label_text = f"{cat_label}: ${cat_val}K"
    elif l1_width > 10:
        label_text = f"${cat_val}K"
    else:
        label_text = None
    if label_text:
        ax1.text(
            l1_x + l1_width / 2,
            margin + 2,
            label_text,
            ha="center",
            va="bottom",
            fontsize=10,
            fontweight="bold",
            color="white",
            bbox={"boxstyle": "round,pad=0.2", "facecolor": color_map[nid], "alpha": 0.85},
        )

    l1_x += l1_width

ax1.set_title("Treemap View", fontsize=22, fontweight="bold", pad=15, color="#306998")

# === RIGHT: SUNBURST VIEW ===
ax2.set_xlim(-1.3, 1.3)
ax2.set_ylim(-1.3, 1.3)
ax2.set_aspect("equal")
ax2.axis("off")

total_value = 1350
start_angle = 90
inner_r1, outer_r1 = 0.32, 0.62
inner_r2, outer_r2 = 0.67, 1.05

for i, nid in enumerate(level1_ids):
    ratio = l1_values[i] / total_value
    sweep = 360 * ratio

    # Inner ring (level 1)
    wedge = Wedge(
        (0, 0),
        outer_r1,
        start_angle,
        start_angle + sweep,
        width=outer_r1 - inner_r1,
        facecolor=color_map[nid],
        edgecolor="white",
        linewidth=2.5,
        alpha=0.75,
    )
    ax2.add_patch(wedge)

    # Level 1 label - curved along the ring
    mid_angle = np.radians(start_angle + sweep / 2)
    label_r = (inner_r1 + outer_r1) / 2
    lx, ly = label_r * np.cos(mid_angle), label_r * np.sin(mid_angle)
    cat_label = df[df["id"] == nid]["label"].iloc[0]
    if sweep > 30:
        # Calculate rotation for inner ring labels
        angle_deg = (start_angle + sweep / 2) % 360
        if 90 < angle_deg <= 270:
            text_rot = angle_deg - 180
        else:
            text_rot = angle_deg
        ax2.text(
            lx,
            ly,
            cat_label,
            ha="center",
            va="center",
            fontsize=13,
            fontweight="bold",
            color="white",
            rotation=text_rot,
        )

    # Outer ring (level 2 - children)
    if nid in children:
        c_ids = children[nid]
        c_values = [df[df["id"] == cid]["value"].iloc[0] for cid in c_ids]
        c_total = sum(c_values)
        c_start = start_angle

        for j, cid in enumerate(c_ids):
            c_ratio = c_values[j] / c_total
            c_sweep = sweep * c_ratio

            c_wedge = Wedge(
                (0, 0),
                outer_r2,
                c_start,
                c_start + c_sweep,
                width=outer_r2 - inner_r2,
                facecolor=color_map[cid],
                edgecolor="white",
                linewidth=1.5,
                alpha=0.92,
            )
            ax2.add_patch(c_wedge)

            # Child label (radial text)
            c_mid = np.radians(c_start + c_sweep / 2)
            c_label_r = (inner_r2 + outer_r2) / 2
            clx = c_label_r * np.cos(c_mid)
            cly = c_label_r * np.sin(c_mid)
            c_label = df[df["id"] == cid]["label"].iloc[0]

            if c_sweep > 15:
                # Calculate rotation for readability - keep text right-side up
                angle_deg = (c_start + c_sweep / 2) % 360
                # Text should be readable from the center outward
                if 90 < angle_deg <= 270:
                    # Flip text for left side of sunburst
                    text_rot = angle_deg - 180
                else:
                    text_rot = angle_deg
                ax2.text(
                    clx,
                    cly,
                    c_label,
                    ha="center",
                    va="center",
                    fontsize=11,
                    fontweight="bold",
                    color="white",
                    rotation=text_rot,
                )

            c_start += c_sweep

    start_angle += sweep

# Center circle with total
center = plt.Circle((0, 0), 0.27, color="white", zorder=10, ec="#306998", lw=2)
ax2.add_patch(center)
ax2.text(0, 0.06, "Total", ha="center", va="center", fontsize=13, fontweight="bold", color="#306998")
ax2.text(0, -0.08, f"${total_value}K", ha="center", va="center", fontsize=12, color="#555555")

ax2.set_title("Sunburst View", fontsize=22, fontweight="bold", pad=15, color="#306998")

# Main title
fig.suptitle("hierarchy-toggle-view · seaborn · pyplots.ai", fontsize=26, fontweight="bold", y=0.98, color="#306998")

# Subtitle
fig.text(
    0.5,
    0.92,
    "Software Project Budget Allocation - Dual Hierarchy View",
    ha="center",
    fontsize=15,
    style="italic",
    color="#666666",
)

# Legend at bottom
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
    edgecolor="#cccccc",
    bbox_to_anchor=(0.5, 0.01),
)

plt.tight_layout(rect=[0, 0.07, 1, 0.90])
plt.savefig("plot.png", dpi=300, bbox_inches="tight", facecolor="white")
