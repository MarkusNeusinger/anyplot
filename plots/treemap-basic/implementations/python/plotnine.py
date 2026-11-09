"""anyplot.ai
treemap-basic: Basic Treemap
Library: plotnine 0.15.9 | Python 3.14.10
Quality: 86/100 | Updated: 2026-11-09
"""

import os

import pandas as pd
from plotnine import (
    aes,
    coord_fixed,
    element_blank,
    element_rect,
    element_text,
    geom_rect,
    geom_text,
    ggplot,
    guide_legend,
    guides,
    labs,
    scale_color_identity,
    scale_fill_manual,
    scale_x_continuous,
    scale_y_continuous,
    theme,
    theme_void,
)


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: all eight positions, one per main category in data order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Constants
LAYOUT_W, LAYOUT_H = 175.0, 100.0  # treemap tiling area in layout units (fixed aspect, not data)
MIN_LABEL_SHARE = 0.025  # rectangles below this share of the total stay unlabeled
OTHER = "Other"  # catch-all block once the main categories outnumber the palette
OTHER_FILL = "#6B6A63"  # Imprint muted anchor (other / rest), a fill shared by both themes

# Columns: set these to your table's column names
DEPARTMENT = "Department"  # role: category
COST_CENTER = "Cost center"  # role: subcategory
BUDGET = "Budget (thousand USD)"  # role: value

# Data: replace this block with your own table, for example df = pd.read_csv("budget.csv")
df = pd.DataFrame(
    {
        DEPARTMENT: ["Engineering"] * 3 + ["Marketing"] * 2 + ["Sales"] * 3 + ["Operations"] * 2 + ["HR", "Finance"],
        COST_CENTER: [
            "R&D",
            "Infrastructure",
            "QA",
            "Digital",
            "Events",
            "Direct",
            "Channel",
            "Support",
            "Logistics",
            "Facilities",
            "Recruiting",
            "Accounting",
        ],
        BUDGET: [450, 280, 120, 200, 80, 350, 180, 90, 150, 100, 130, 170],
    }
)


# Plot: reads only df and the constants above
def squarify(values, x, y, w, h):
    """Squarified treemap layout: tile (x, y, w, h) with rectangles whose areas follow values (sorted descending)."""
    rects = []
    values = list(values)
    scale = w * h / sum(values)
    areas = [v * scale for v in values]
    while areas:
        side = min(w, h)
        row, worst = [], float("inf")
        for a in areas:
            candidate = row + [a]
            s = sum(candidate)
            ratio = max(max(side * side * c / (s * s), s * s / (side * side * c)) for c in candidate)
            if ratio > worst:
                break
            row, worst = candidate, ratio
        thickness = sum(row) / side
        offset = 0.0
        for a in row:
            length = a / thickness
            if w >= h:
                rects.append((x, y + offset, thickness, length))
            else:
                rects.append((x + offset, y, length, thickness))
            offset += length
        if w >= h:
            x, w = x + thickness, w - thickness
        else:
            y, h = y + thickness, h - thickness
        areas = areas[len(row) :]
    return rects


leaves = df.dropna(subset=[DEPARTMENT, BUDGET]).loc[lambda d: d[BUDGET] > 0].copy()
leaves[DEPARTMENT] = leaves[DEPARTMENT].astype(str)
departments = leaves[DEPARTMENT].unique().tolist()

# More departments than palette hues: the smallest fold into one muted "Other" block
if len(departments) > len(IMPRINT_PALETTE):
    sizes = leaves.groupby(DEPARTMENT, sort=False)[BUDGET].sum()
    kept = set(sizes.nlargest(len(IMPRINT_PALETTE) - 1).index)
    leaves[DEPARTMENT] = leaves[DEPARTMENT].where(leaves[DEPARTMENT].isin(kept), OTHER)
    departments = [d for d in departments if d in kept] + [OTHER]

fill_of = {dept: OTHER_FILL if dept == OTHER else IMPRINT_PALETTE[i] for i, dept in enumerate(departments)}
totals = leaves.groupby(DEPARTMENT, sort=False)[BUDGET].sum().sort_values(ascending=False)

# Level 1: one block per department; level 2: its cost centers tiled inside that block
blocks, cells = [], []
for dept, (bx, by, bw, bh) in zip(totals.index, squarify(totals.values, 0, 0, LAYOUT_W, LAYOUT_H), strict=True):
    blocks.append({DEPARTMENT: dept, "xmin": bx, "xmax": bx + bw, "ymin": by, "ymax": by + bh})
    members = leaves[leaves[DEPARTMENT] == dept].sort_values(BUDGET, ascending=False)
    for (_, row), (cx, cy, cw, ch) in zip(
        members.iterrows(), squarify(members[BUDGET].values, bx, by, bw, bh), strict=True
    ):
        cells.append({**row.to_dict(), "xmin": cx, "xmax": cx + cw, "ymin": cy, "ymax": cy + ch})

blocks = pd.DataFrame(blocks)
cells = pd.DataFrame(cells)
cells["xc"] = (cells["xmin"] + cells["xmax"]) / 2
cells["yc"] = (cells["ymin"] + cells["ymax"]) / 2


# Label ink per fill: dark text on light fills, white on dark ones (WCAG relative luminance)
luminance_of = {
    fill: sum(
        k * (c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4)
        for k, c in zip((0.2126, 0.7152, 0.0722), (int(fill[i : i + 2], 16) / 255 for i in (1, 3, 5)), strict=True)
    )
    for fill in fill_of.values()
}
ink_of = {dept: "#1A1A17" if luminance_of[fill] > 0.25 else "#FFFFFF" for dept, fill in fill_of.items()}
cells["ink"] = cells[DEPARTMENT].map(ink_of)
cells["label"] = cells[COST_CENTER].astype(str) + "\n$" + cells[BUDGET].map("{:,.0f}".format) + "K"
labeled = cells[cells[BUDGET] >= MIN_LABEL_SHARE * cells[BUDGET].sum()]

title = "treemap-basic · python · plotnine · anyplot.ai"
title_size = round(12 * (67 / len(title) if len(title) > 67 else 1.0))

plot = (
    ggplot()
    # Cost-center rectangles with thin page-colored seams
    + geom_rect(
        aes(xmin="xmin", xmax="xmax", ymin="ymin", ymax="ymax", fill=DEPARTMENT), data=cells, color=PAGE_BG, size=0.5
    )
    # Department blocks drawn on top as thicker outlines: the hierarchy boundary
    + geom_rect(
        aes(xmin="xmin", xmax="xmax", ymin="ymin", ymax="ymax"), data=blocks, fill=None, color=PAGE_BG, size=2.2
    )
    + geom_text(
        aes(x="xc", y="yc", label="label", color="ink"), data=labeled, size=6.5, fontweight="bold", lineheight=1.15
    )
    + scale_fill_manual(values=fill_of, limits=departments)
    + scale_color_identity()
    + scale_x_continuous(expand=(0, 0))
    + scale_y_continuous(expand=(0, 0))
    + coord_fixed(ratio=1)
    + guides(fill=guide_legend(override_aes={"color": PAGE_BG}))
    + labs(title=title, fill=DEPARTMENT)
    + theme_void()
    + theme(
        figure_size=(8, 4.5),
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        plot_title=element_text(size=title_size, color=INK, weight="bold", ha="center", margin={"b": 8}),
        legend_title=element_text(size=9, color=INK),
        legend_text=element_text(size=8, color=INK_SOFT),
        legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT, size=0.3),
        legend_key=element_blank(),
        legend_position="right",
        legend_margin=6,
        legend_key_spacing_y=3,
        plot_margin=0.03,
    )
)

# Save
plot.save(f"plot-{THEME}.png", dpi=400, width=8, height=4.5, units="in", verbose=False)
