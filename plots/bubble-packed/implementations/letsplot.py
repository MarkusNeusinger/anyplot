""" pyplots.ai
bubble-packed: Basic Packed Bubble Chart
Library: letsplot 4.8.2 | Python 3.14.3
Quality: 86/100 | Updated: 2026-02-23
"""

import numpy as np
import pandas as pd
from lets_plot import (
    LetsPlot,
    aes,
    coord_fixed,
    element_rect,
    element_text,
    geom_polygon,
    geom_text,
    ggplot,
    ggsize,
    guide_legend,
    guides,
    labs,
    layer_tooltips,
    scale_fill_manual,
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

# Initialize positions in group sectors
np.random.seed(42)
x = np.zeros(n, dtype=float)
y = np.zeros(n, dtype=float)
for i in range(n):
    angle = div_angles[divisions[i]] + np.random.uniform(-0.4, 0.4)
    r = np.random.uniform(3, 20)
    x[i] = r * np.cos(angle)
    y[i] = r * np.sin(angle)

# Force-directed packing with strong gravity and group attraction
for _ in range(1200):
    x *= 0.995
    y *= 0.995

    for g in div_names:
        mask = np.array([divisions[i] == g for i in range(n)])
        if mask.sum() > 1:
            cx, cy = x[mask].mean(), y[mask].mean()
            x[mask] += (cx - x[mask]) * 0.025
            y[mask] += (cy - y[mask]) * 0.025

    for i in range(n):
        for j in range(i + 1, n):
            dx = x[j] - x[i]
            dy = y[j] - y[i]
            dist = np.sqrt(dx * dx + dy * dy)
            spacing = 1.0 if divisions[i] != divisions[j] else 0.25
            min_dist = radii[i] + radii[j] + spacing

            if dist < min_dist and dist > 0:
                overlap = (min_dist - dist) / 2
                ux, uy = dx / dist, dy / dist
                x[i] -= ux * overlap
                y[i] -= uy * overlap
                x[j] += ux * overlap
                y[j] += uy * overlap

# Collision-only pass to ensure no overlaps
for _ in range(500):
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
    if settled:
        break

x -= x.mean()
y -= y.mean()

# Draw circles as polygons in data coordinates for exact size match
theta = np.linspace(0, 2 * np.pi, 72, endpoint=False)
circle_rows = []
for i in range(n):
    r = radii[i]
    for t in theta:
        circle_rows.append(
            {
                "px": x[i] + r * np.cos(t),
                "py": y[i] + r * np.sin(t),
                "division": divisions[i],
                "label": categories[i],
                "budget": f"${values[i]}M",
                "cid": str(i),
            }
        )
circles_df = pd.DataFrame(circle_rows)

# Labels: name + budget for large bubbles, name only for medium
abbrev = {"Customer Support": "Support", "Operations": "Ops"}
labels_df = pd.DataFrame(
    {
        "lx": x,
        "ly": y,
        "display_label": [
            (f"{abbrev.get(c, c)}\n${v}M" if v >= 48 else (abbrev.get(c, c) if v >= 35 else ""))
            for c, v in zip(categories, values, strict=True)
        ],
    }
)

# Tight bounds with minimal padding
x_pad = (circles_df["px"].max() - circles_df["px"].min()) * 0.02
y_pad = (circles_df["py"].max() - circles_df["py"].min()) * 0.02
x_lo = circles_df["px"].min() - x_pad
x_hi = circles_df["px"].max() + x_pad
y_lo = circles_df["py"].min() - y_pad
y_hi = circles_df["py"].max() + y_pad

plot = (
    ggplot()
    + geom_polygon(
        aes(x="px", y="py", fill="division", group="cid"),
        data=circles_df,
        color="white",
        size=1.2,
        alpha=0.88,
        tooltips=layer_tooltips().title("@label").line("Budget|@budget").line("Division|@division"),
    )
    + geom_text(aes(x="lx", y="ly", label="display_label"), data=labels_df, size=8, color="white", fontface="bold")
    + scale_fill_manual(values={"Tech": "#FFD43B", "Business": "#4ECDC4", "Operations": "#306998"})
    + guides(fill=guide_legend(nrow=1))
    + coord_fixed()
    + labs(title="Department Budget Allocation · bubble-packed · letsplot · pyplots.ai", fill="Division")
    + xlim(x_lo, x_hi)
    + ylim(y_lo, y_hi)
    + theme_void()
    + theme(
        plot_title=element_text(size=24, hjust=0.5),
        legend_position="bottom",
        legend_title=element_text(size=20),
        legend_text=element_text(size=16),
        legend_background=element_rect(fill="white", color="#CCCCCC", size=0.5),
    )
    + ggsize(1200, 1200)
)

# Save
export_ggsave(plot, "plot.png", path=".", scale=3)
