""" pyplots.ai
bubble-packed: Basic Packed Bubble Chart
Library: letsplot 4.8.2 | Python 3.14.3
Quality: 89/100 | Updated: 2026-02-23
"""

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
    ggplot,
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
from lets_plot.export import ggsave as export_ggsave


LetsPlot.setup_html()

# Data - department budget allocation ($M)
np.random.seed(42)
categories = [
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
]
values = np.array([85, 62, 58, 45, 32, 48, 72, 38, 22, 55, 68, 35, 42, 28, 30])
divisions = [
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
]

# Circle packing with group-based spatial clustering
n = len(values)
radii = np.sqrt(values / np.pi) * 3.5
div_names = ["Tech", "Business", "Operations"]
div_angles = {g: i * 2 * np.pi / len(div_names) for i, g in enumerate(div_names)}

np.random.seed(42)
x = np.zeros(n, dtype=float)
y = np.zeros(n, dtype=float)
for i in range(n):
    angle = div_angles[divisions[i]] + np.random.uniform(-0.4, 0.4)
    r_init = np.random.uniform(3, 20)
    x[i] = r_init * np.cos(angle)
    y[i] = r_init * np.sin(angle)

# Force-directed packing: gravity, group attraction, and collision resolution
for step in range(1700):
    if step < 1200:
        x *= 0.995
        y *= 0.995
        for g in div_names:
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
            spacing = 1.0 if divisions[i] != divisions[j] else 0.25
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

# Build DataFrame with diameter in data units for geom_point size_unit='x'
abbrev = {"Customer Support": "Support", "Operations": "Ops"}
df = pd.DataFrame(
    {
        "x": x,
        "y": y,
        "division": divisions,
        "label": categories,
        "budget": [f"${v}M" for v in values],
        "diameter": radii * 2,
        "display_label": [
            (f"{abbrev.get(c, c)}\n${v}M" if v >= 48 else (abbrev.get(c, c) if v >= 35 else ""))
            for c, v in zip(categories, values, strict=True)
        ],
    }
)

# Axis limits ensuring all circles are fully visible
x_lo = min(x[i] - radii[i] for i in range(n))
x_hi = max(x[i] + radii[i] for i in range(n))
y_lo = min(y[i] - radii[i] for i in range(n))
y_hi = max(y[i] + radii[i] for i in range(n))
pad = (x_hi - x_lo) * 0.03

# Colorblind-safe palette: Python Blue + Wong (verified for all CVD types)
palette = {"Tech": "#306998", "Business": "#E69F00", "Operations": "#009E73"}

plot = (
    ggplot(df)
    + geom_point(
        aes(x="x", y="y", fill="division", size="diameter"),
        shape=21,
        color="white",
        stroke=1.5,
        alpha=0.88,
        size_unit="x",
        tooltips=(layer_tooltips().title("@label").line("Budget|@budget").line("Division|@division")),
    )
    + scale_size_identity(guide="none")
    + geom_text(aes(x="x", y="y", label="display_label"), size=9, color="white", fontface="bold")
    + scale_fill_manual(values=palette)
    + guides(fill=guide_legend(nrow=1))
    + coord_fixed()
    + xlim(x_lo - pad, x_hi + pad)
    + ylim(y_lo - pad, y_hi + pad)
    + labs(
        title="Department Budget Allocation \u00b7 bubble-packed \u00b7 letsplot \u00b7 pyplots.ai",
        subtitle="Tech departments dominate \u2014 8 of 15 teams control 58% of total budget",
        fill="Division",
    )
    + theme_void()
    + theme(
        plot_title=element_text(size=24, hjust=0.5),
        plot_subtitle=element_text(size=16, hjust=0.5, color="#666666"),
        legend_position="bottom",
        legend_title=element_text(size=20),
        legend_text=element_text(size=16),
        legend_background=element_rect(fill="white", color="#CCCCCC", size=0.5),
    )
    + ggsize(1200, 1200)
)

export_ggsave(plot, "plot.png", path=".", scale=3)
