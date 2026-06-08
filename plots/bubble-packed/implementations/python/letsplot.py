"""anyplot.ai
bubble-packed: Basic Packed Bubble Chart
Library: letsplot 4.10.1 | Python 3.13.13
Quality: 89/100 | Updated: 2026-05-29
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
from lets_plot.export import ggsave as _ggsave


LetsPlot.setup_html()

THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette — semantic mapping for divisions
# Operations→green (brand, active), Tech→blue (tech-cool), Business→ochre (commerce)
PALETTE = {"Operations": "#009E73", "Tech": "#4467A3", "Business": "#BD8233"}

# Department budget allocation ($M)
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

# Area-based radii: area ∝ value
n = len(values)
radii = np.sqrt(values / np.pi) * 3.5
div_names = ["Tech", "Business", "Operations"]
div_angles = {g: i * 2 * np.pi / len(div_names) for i, g in enumerate(div_names)}

# Initial positions with group-based angles
np.random.seed(42)
x = np.zeros(n, dtype=float)
y = np.zeros(n, dtype=float)
for i in range(n):
    angle = div_angles[divisions[i]] + np.random.uniform(-0.4, 0.4)
    r_init = np.random.uniform(3, 20)
    x[i] = r_init * np.cos(angle)
    y[i] = r_init * np.sin(angle)

# Force-directed packing: gravity + group clustering + collision resolution
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

# Center on bounding box midpoint for balanced canvas utilization
x_lo_raw = min(x[i] - radii[i] for i in range(n))
x_hi_raw = max(x[i] + radii[i] for i in range(n))
y_lo_raw = min(y[i] - radii[i] for i in range(n))
y_hi_raw = max(y[i] + radii[i] for i in range(n))
x -= (x_lo_raw + x_hi_raw) / 2
y -= (y_lo_raw + y_hi_raw) / 2

# Axis limits after centering
x_lo = min(x[i] - radii[i] for i in range(n))
x_hi = max(x[i] + radii[i] for i in range(n))
y_lo = min(y[i] - radii[i] for i in range(n))
y_hi = max(y[i] + radii[i] for i in range(n))
pad = (x_hi - x_lo) * 0.04

# Abbreviations for long names
_abbrev = {"Customer Support": "Support", "Operations": "Ops", "Security": "Sec"}

df = pd.DataFrame(
    {
        "x": x,
        "y": y,
        "division": divisions,
        "label": categories,
        "budget_val": values,
        "budget": [f"${v}M" for v in values],
        "diameter": radii * 2,
        "display_label": [
            (_abbrev.get(c, c) + f"\n${v}M") if v >= 55 else _abbrev.get(c, c)
            for c, v in zip(categories, values, strict=True)
        ],
    }
)

# Three text tiers: large circles get name+budget, medium get name, small get short name
df_large = df[df["budget_val"] >= 55].copy()
df_medium = df[(df["budget_val"] >= 35) & (df["budget_val"] < 55)].copy()
df_small = df[df["budget_val"] < 35].copy()

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
    + geom_text(aes(x="x", y="y", label="display_label"), data=df_large, size=5, color="white", fontface="bold")
    + geom_text(aes(x="x", y="y", label="display_label"), data=df_medium, size=4, color="white", fontface="bold")
    + geom_text(aes(x="x", y="y", label="display_label"), data=df_small, size=3, color="white", fontface="bold")
    + scale_fill_manual(values=PALETTE)
    + guides(fill=guide_legend(nrow=1))
    + coord_fixed()
    + xlim(x_lo - pad, x_hi + pad)
    + ylim(y_lo - pad, y_hi + pad)
    + labs(
        title="Department Budget Allocation · bubble-packed · python · letsplot · anyplot.ai",
        subtitle="Tech dominates — 8 of 15 teams control 58% of total budget",
        fill="Division",
    )
    + theme_void()
    + theme(
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        plot_title=element_text(size=16, hjust=0.5, color=INK),
        plot_subtitle=element_text(size=12, hjust=0.5, color=INK_SOFT),
        legend_position="bottom",
        legend_title=element_text(size=12, color=INK),
        legend_text=element_text(size=10, color=INK_SOFT),
        legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT, size=0.5),
    )
    + ggsize(600, 600)
)

_ggsave(plot, f"plot-{THEME}.png", path=".", scale=4)
_ggsave(plot, f"plot-{THEME}.html", path=".")
