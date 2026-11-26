"""anyplot.ai
bubble-packed: Basic Packed Bubble Chart
Library: letsplot 4.10.1 | Python 3.13.13
Quality: pending | Updated: 2026-06-16
"""

import os

import numpy as np
import pandas as pd
from lets_plot import (
    LetsPlot,
    aes,
    coord_fixed,
    element_rect,
    element_text,
    geom_point,
    geom_text,
    gggrid,
    ggplot,
    ggsave,
    ggsize,
    guide_legend,
    guides,
    labs,
    layer_tooltips,
    scale_fill_manual,
    scale_size_identity,
    theme,
    theme_void,
    xlim,
    ylim,
)


LetsPlot.setup_html()

# Theme-adaptive chrome (see prompts/default-style-guide.md "Theme-adaptive Chrome")
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: all eight positions in canonical order; the first group leads as brand green
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Constants
BUBBLE_SCALE = 3.5  # circle radius per square root of a value, in layout units
SAME_GROUP_GAP = 0.25  # layout gap between circles of one group
OTHER_GROUP_GAP = 1.0  # layout gap between circles of different groups
NAME_SHARE = 0.35  # circles above this share of the largest value carry their name
VALUE_SHARE = 0.52  # circles above this share of the largest value also carry the value

# Columns: set these to your table's column names
LABEL = "Department"  # role: label
VALUE = "Budget ($M)"  # role: value
DIVISION = "Division"  # role: group

# Data: replace this block with your own table, for example df = pd.read_csv("budgets.csv")
df = pd.DataFrame(
    {
        LABEL: [
            "Engineering",
            "Marketing",
            "Sales",
            "Operations",
            "HR",
            "Finance",
            "R&D",
            "Customer Support",
            "Legal",
            "IT",
            "Product",
            "Design",
            "Analytics",
            "QA",
            "Security",
        ],
        VALUE: [85, 62, 58, 45, 32, 48, 72, 38, 22, 55, 68, 35, 42, 28, 30],
        DIVISION: [
            "Tech",
            "Business",
            "Business",
            "Operations",
            "Operations",
            "Operations",
            "Tech",
            "Operations",
            "Operations",
            "Tech",
            "Tech",
            "Tech",
            "Tech",
            "Tech",
            "Tech",
        ],
    }
)

# Plot
values = df[VALUE].to_numpy(dtype=float)
divisions = df[DIVISION].tolist()
groups = list(dict.fromkeys(divisions))
n = len(df)

# Circle packing with group-based spatial clustering; circle area encodes the value
radii = np.sqrt(values / np.pi) * BUBBLE_SCALE
group_angles = {g: i * 2 * np.pi / len(groups) for i, g in enumerate(groups)}

np.random.seed(42)
x = np.zeros(n, dtype=float)
y = np.zeros(n, dtype=float)
for i in range(n):
    angle = group_angles[divisions[i]] + np.random.uniform(-0.4, 0.4)
    r_init = np.random.uniform(3, 20)
    x[i] = r_init * np.cos(angle)
    y[i] = r_init * np.sin(angle)

# Force-directed packing: gravity, group attraction, and collision resolution
for step in range(1700):
    if step < 1200:
        x *= 0.995
        y *= 0.995
        for g in groups:
            mask = np.array([divisions[i] == g for i in range(n)])
            if mask.sum() > 1:
                cx, cy = x[mask].mean(), y[mask].mean()
                x[mask] += (cx - x[mask]) * 0.025
                y[mask] += (cy - y[mask]) * 0.025

    settled = True
    for i in range(n):
        for j in range(i + 1, n):
            dx = x[j] - x[i]
            dy = y[j] - y[i]
            dist = np.sqrt(dx * dx + dy * dy)
            spacing = OTHER_GROUP_GAP if divisions[i] != divisions[j] else SAME_GROUP_GAP
            min_dist = radii[i] + radii[j] + spacing
            if dist < min_dist and dist > 0:
                settled = False
                overlap = (min_dist - dist) / 2
                ux, uy = dx / dist, dy / dist
                x[i] -= ux * overlap
                y[i] -= uy * overlap
                x[j] += ux * overlap
                y[j] += uy * overlap

    if step >= 1200 and settled:
        break

x -= x.mean()
y -= y.mean()

# Layout columns: position from the packing, diameter in data units for geom_point size_unit="x"
abbrev = {"Customer Support": "Support", "Operations": "Ops"}
names = [abbrev.get(c, c) for c in df[LABEL]]
share = values / np.nanmax(values)
df = df.assign(
    pack_x=x,
    pack_y=y,
    diameter=radii * 2,
    display_label=[
        f"{name}\n${v:.0f}M" if s > VALUE_SHARE else (name if s > NAME_SHARE else "")
        for name, v, s in zip(names, values, share, strict=True)
    ],
    budget_text=[f"${v:.0f}M" for v in values],
)

# Axis limits ensuring all circles are fully visible
x_lo, x_hi = (x - radii).min(), (x + radii).max()
y_lo, y_hi = (y - radii).min(), (y + radii).max()
pad = (x_hi - x_lo) * 0.02

# Colors looked up per group, in order of first appearance
palette = {g: IMPRINT_PALETTE[i] for i, g in enumerate(groups)}

# Subtitle claim computed from the data: the group with the largest total
totals = df.groupby(DIVISION, sort=False)[VALUE].sum()
lead = totals.idxmax()
lead_count = int((df[DIVISION] == lead).sum())
lead_share = totals[lead] / totals.sum() * 100
subtitle = f"{lead} departments dominate — {lead_count} of {n} teams control {lead_share:.0f}% of total budget"

# Title scaled off the 67-char baseline (see prompts/plot-generator.md)
title = "Department Budget Allocation · bubble-packed · python · letsplot · anyplot.ai"
title_size = max(11, round(16 * 67 / len(title))) if len(title) > 67 else 16

plot = (
    ggplot(df)
    + geom_point(
        aes(x="pack_x", y="pack_y", fill=DIVISION, size="diameter"),
        shape=21,
        color=PAGE_BG,
        stroke=1.5,
        alpha=0.92,
        size_unit="x",
        tooltips=(
            layer_tooltips().title(f"@{{{LABEL}}}").line("Budget|@budget_text").line(f"{DIVISION}|@{{{DIVISION}}}")
        ),
    )
    + scale_size_identity(guide="none")
    # Dark in-bubble text reads well across green/lavender/blue fills (white fails on the lighter hues)
    + geom_text(aes(x="pack_x", y="pack_y", label="display_label"), size=5, color="#1A1A17", fontface="bold")
    + scale_fill_manual(values=palette, breaks=groups)
    + guides(fill=guide_legend(nrow=1))
    + coord_fixed()
    + xlim(x_lo - pad, x_hi + pad)
    + ylim(y_lo - pad, y_hi + pad)
    + labs(title=title, subtitle=subtitle, fill=DIVISION)
    + theme_void()
    + theme(
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        plot_title=element_text(size=title_size, color=INK, hjust=0.5),
        plot_subtitle=element_text(size=11, color=INK_SOFT, hjust=0.5),
        legend_position="bottom",
        legend_title=element_text(size=12, color=INK),
        legend_text=element_text(size=11, color=INK_SOFT),
        legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT, size=0.5),
    )
)

# The fixed aspect leaves transparent strips; a one-panel grid paints the whole square canvas
plot = gggrid([plot]) + ggsize(600, 600) + theme(plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG))

# Save (square: ggsize 600 x scale 4 = 2400 x 2400 px)
ggsave(plot, f"plot-{THEME}.png", path=".", scale=4)
ggsave(plot, f"plot-{THEME}.html", path=".")
