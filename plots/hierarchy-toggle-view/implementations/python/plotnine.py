""" pyplots.ai
hierarchy-toggle-view: Interactive Treemap-Sunburst Toggle View
Library: plotnine 0.15.2 | Python 3.13.11
Quality: 90/100 | Created: 2026-01-11
"""

import numpy as np
import pandas as pd
from plotnine import (
    aes,
    annotate,
    geom_polygon,
    geom_rect,
    geom_text,
    ggplot,
    lims,
    scale_fill_identity,
    theme,
    theme_void,
)


# Hierarchical data: Research department budget allocation
hierarchy_data = [
    {"id": "root", "parent": "", "label": "Research", "value": 0},
    # Level 1: Main divisions
    {"id": "bio", "parent": "root", "label": "Biology", "value": 0},
    {"id": "chem", "parent": "root", "label": "Chemistry", "value": 0},
    {"id": "phys", "parent": "root", "label": "Physics", "value": 0},
    {"id": "comp", "parent": "root", "label": "Computing", "value": 0},
    # Level 2: Biology subdepartments
    {"id": "genetics", "parent": "bio", "label": "Genetics", "value": 150},
    {"id": "ecology", "parent": "bio", "label": "Ecology", "value": 120},
    {"id": "micro", "parent": "bio", "label": "Microbio", "value": 90},
    # Level 2: Chemistry subdepartments
    {"id": "organic", "parent": "chem", "label": "Organic", "value": 130},
    {"id": "inorganic", "parent": "chem", "label": "Inorganic", "value": 80},
    {"id": "analytic", "parent": "chem", "label": "Analytic", "value": 70},
    # Level 2: Physics subdepartments
    {"id": "quantum", "parent": "phys", "label": "Quantum", "value": 180},
    {"id": "astro", "parent": "phys", "label": "Astro", "value": 140},
    {"id": "particle", "parent": "phys", "label": "Particle", "value": 100},
    # Level 2: Computing subdepartments
    {"id": "ml", "parent": "comp", "label": "ML/AI", "value": 200},
    {"id": "hpc", "parent": "comp", "label": "HPC", "value": 110},
]

df = pd.DataFrame(hierarchy_data)

# Build hierarchy and calculate parent values
children = {}
for _, row in df.iterrows():
    parent = row["parent"]
    if parent:
        if parent not in children:
            children[parent] = []
        children[parent].append(row["id"])

# Calculate parent values as sum of children
level1_ids = ["bio", "chem", "phys", "comp"]
for nid in level1_ids:
    child_sum = df[df["parent"] == nid]["value"].sum()
    df.loc[df["id"] == nid, "value"] = child_sum

total_value = df[df["id"].isin(level1_ids)]["value"].sum()
df.loc[df["id"] == "root", "value"] = total_value

# Color mapping (colorblind-safe)
colors = {
    "bio": "#306998",  # Python Blue
    "chem": "#FFD43B",  # Python Yellow
    "phys": "#2E8B57",  # Sea Green
    "comp": "#E07B39",  # Burnt Orange
}

# Assign colors to children
for nid in level1_ids:
    if nid in children:
        for cid in children[nid]:
            colors[cid] = colors[nid]


# ============ TREEMAP DATA (flat structure) ============
treemap_rects = []
x_start = 0
treemap_total = df[df["id"].isin(level1_ids)]["value"].sum()

for nid in level1_ids:
    parent_val = df[df["id"] == nid]["value"].iloc[0]
    parent_width = (parent_val / treemap_total) * 100

    child_ids = children.get(nid, [])
    child_vals = [df[df["id"] == cid]["value"].iloc[0] for cid in child_ids]
    child_total = sum(child_vals)

    y_start = 0
    for cid, cval in zip(child_ids, child_vals, strict=True):
        child_height = (cval / child_total) * 100
        label = df[df["id"] == cid]["label"].iloc[0]
        text_col = "#333333" if colors[cid] == "#FFD43B" else "white"
        treemap_rects.append(
            {
                "xmin": x_start + 0.5,
                "xmax": x_start + parent_width - 0.5,
                "ymin": y_start + 0.5,
                "ymax": y_start + child_height - 0.5,
                "fill": colors[cid],
                "label": f"{label}\n${cval}K",
                "label_x": x_start + parent_width / 2,
                "label_y": y_start + child_height / 2,
                "text_color": text_col,
            }
        )
        y_start += child_height
    x_start += parent_width

treemap_df = pd.DataFrame(treemap_rects)


# ============ SUNBURST DATA (flat structure) ============
sunburst_wedges = []
sunburst_labels = []
wedge_id = 0
sunburst_total = df[df["id"].isin(level1_ids)]["value"].sum()
start_angle = np.pi / 2  # Start at top
cx, cy = 50, 50  # Center position
n_points = 50

for nid in level1_ids:
    parent_val = df[df["id"] == nid]["value"].iloc[0]
    parent_sweep = (parent_val / sunburst_total) * 2 * np.pi

    # Inner ring wedge (level 1)
    inner_r, outer_r = 12, 28
    angles_outer = np.linspace(start_angle, start_angle + parent_sweep, n_points)
    angles_inner = np.linspace(start_angle + parent_sweep, start_angle, n_points)
    x_outer = cx + outer_r * np.cos(angles_outer)
    y_outer = cy + outer_r * np.sin(angles_outer)
    x_inner = cx + inner_r * np.cos(angles_inner)
    y_inner = cy + inner_r * np.sin(angles_inner)
    x = np.concatenate([x_outer, x_inner])
    y = np.concatenate([y_outer, y_inner])

    for xi, yi in zip(x, y, strict=True):
        sunburst_wedges.append({"x": xi, "y": yi, "wedge_id": wedge_id, "fill": colors[nid]})
    wedge_id += 1

    # Inner ring label with budget
    mid_angle = start_angle + parent_sweep / 2
    text_col = "#333333" if colors[nid] == "#FFD43B" else "white"
    label_r = 20
    lx = cx + label_r * np.cos(mid_angle)
    ly = cy + label_r * np.sin(mid_angle)
    parent_label = df[df["id"] == nid]["label"].iloc[0]
    sunburst_labels.append({"x": lx, "y": ly, "label": f"{parent_label}\n${int(parent_val)}K", "text_color": text_col})

    # Outer ring wedges (level 2 - children)
    child_ids = children.get(nid, [])
    child_vals = [df[df["id"] == cid]["value"].iloc[0] for cid in child_ids]
    child_total = sum(child_vals)
    child_start = start_angle

    for cid, cval in zip(child_ids, child_vals, strict=True):
        child_sweep = (cval / child_total) * parent_sweep

        inner_r, outer_r = 30, 45
        angles_outer = np.linspace(child_start, child_start + child_sweep, n_points)
        angles_inner = np.linspace(child_start + child_sweep, child_start, n_points)
        x_outer = cx + outer_r * np.cos(angles_outer)
        y_outer = cy + outer_r * np.sin(angles_outer)
        x_inner = cx + inner_r * np.cos(angles_inner)
        y_inner = cy + inner_r * np.sin(angles_inner)
        x = np.concatenate([x_outer, x_inner])
        y = np.concatenate([y_outer, y_inner])

        for xi, yi in zip(x, y, strict=True):
            sunburst_wedges.append({"x": xi, "y": yi, "wedge_id": wedge_id, "fill": colors[cid]})
        wedge_id += 1

        # Outer ring label with budget (only for large enough segments)
        if child_sweep > 0.2:
            child_mid = child_start + child_sweep / 2
            text_col = "#333333" if colors[cid] == "#FFD43B" else "white"
            label_r = 37.5
            lx = cx + label_r * np.cos(child_mid)
            ly = cy + label_r * np.sin(child_mid)
            child_label = df[df["id"] == cid]["label"].iloc[0]
            sunburst_labels.append({"x": lx, "y": ly, "label": f"{child_label}\n${cval}K", "text_color": text_col})
        child_start += child_sweep

    start_angle += parent_sweep

sunburst_df = pd.DataFrame(sunburst_wedges)
sunburst_labels_df = pd.DataFrame(sunburst_labels)

# Split labels by color for proper text rendering
treemap_white_labels = treemap_df[treemap_df["text_color"] == "white"]
treemap_dark_labels = treemap_df[treemap_df["text_color"] == "#333333"]

sunburst_white_labels = sunburst_labels_df[sunburst_labels_df["text_color"] == "white"]
sunburst_dark_labels = sunburst_labels_df[sunburst_labels_df["text_color"] == "#333333"]

# Create the combined plot with both views
plot = (
    ggplot()
    # Treemap rectangles
    + geom_rect(
        data=treemap_df,
        mapping=aes(xmin="xmin", xmax="xmax", ymin="ymin", ymax="ymax", fill="fill"),
        color="white",
        size=1.2,
    )
    # Treemap labels - white text
    + geom_text(
        data=treemap_white_labels,
        mapping=aes(x="label_x", y="label_y", label="label"),
        color="white",
        size=11,
        fontweight="bold",
    )
    # Treemap labels - dark text (for yellow backgrounds)
    + geom_text(
        data=treemap_dark_labels,
        mapping=aes(x="label_x", y="label_y", label="label"),
        color="#333333",
        size=11,
        fontweight="bold",
    )
    # Sunburst polygons (offset to right)
    + geom_polygon(
        data=sunburst_df.assign(x=lambda d: d["x"] + 110),
        mapping=aes(x="x", y="y", fill="fill", group="wedge_id"),
        color="white",
        size=0.7,
    )
    # Sunburst labels - white text (offset to right)
    + geom_text(
        data=sunburst_white_labels.assign(x=lambda d: d["x"] + 110),
        mapping=aes(x="x", y="y", label="label"),
        color="white",
        size=10,
        fontweight="bold",
    )
    # Sunburst labels - dark text (offset to right)
    + geom_text(
        data=sunburst_dark_labels.assign(x=lambda d: d["x"] + 110),
        mapping=aes(x="x", y="y", label="label"),
        color="#333333",
        size=10,
        fontweight="bold",
    )
    # Use identity scale to respect literal color values
    + scale_fill_identity()
    # Sunburst center circle
    + annotate("point", x=160, y=50, size=40, color="white")
    + annotate("text", x=160, y=53, label="Total", size=12, fontweight="bold", color="#306998")
    + annotate("text", x=160, y=47, label=f"${int(total_value)}K", size=11, color="#555555")
    # View titles
    + annotate("text", x=50, y=108, label="Treemap View", size=16, fontweight="bold", color="#333333")
    + annotate("text", x=160, y=108, label="Sunburst View", size=16, fontweight="bold", color="#333333")
    # Main title
    + annotate(
        "text",
        x=105,
        y=120,
        label="hierarchy-toggle-view · plotnine · pyplots.ai",
        size=18,
        fontweight="bold",
        color="#306998",
    )
    # Subtitle
    + annotate("text", x=105, y=114, label="Research Department Budget Allocation", size=13, color="#666666")
    + lims(x=(-5, 215), y=(-10, 130))
    + theme_void()
    + theme(figure_size=(16, 9), legend_position="none")
)

# Save the plot
plot.save("plot.png", dpi=300)
