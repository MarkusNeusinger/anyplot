"""pyplots.ai
bubble-packed: Basic Packed Bubble Chart
Library: letsplot 4.8.2 | Python 3.14.3
"""

import numpy as np
import pandas as pd
from lets_plot import (
    LetsPlot,
    aes,
    element_rect,
    element_text,
    geom_point,
    geom_text,
    ggplot,
    ggsize,
    labs,
    layer_tooltips,
    scale_fill_manual,
    scale_size,
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
groups = [
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
group_names = ["Tech", "Business", "Operations"]
group_angles = {g: i * 2 * np.pi / len(group_names) for i, g in enumerate(group_names)}

# Initialize positions in group sectors for spatial clustering
np.random.seed(42)
x = np.zeros(n, dtype=float)
y = np.zeros(n, dtype=float)
for i in range(n):
    angle = group_angles[groups[i]] + np.random.uniform(-0.4, 0.4)
    r = np.random.uniform(5, 30)
    x[i] = r * np.cos(angle)
    y[i] = r * np.sin(angle)

# Force-directed packing with group attraction
for _ in range(800):
    # Mild gravity toward center
    x *= 0.997
    y *= 0.997

    # Group attraction: pull toward group centroid
    for g in group_names:
        mask = np.array([groups[i] == g for i in range(n)])
        if mask.sum() > 1:
            cx, cy = x[mask].mean(), y[mask].mean()
            x[mask] += (cx - x[mask]) * 0.015
            y[mask] += (cy - y[mask]) * 0.015

    # Collision resolution with inter-group spacing
    for i in range(n):
        for j in range(i + 1, n):
            dx = x[j] - x[i]
            dy = y[j] - y[i]
            dist = np.sqrt(dx * dx + dy * dy)
            spacing = 2.0 if groups[i] != groups[j] else 0.5
            min_dist = radii[i] + radii[j] + spacing

            if dist < min_dist and dist > 0:
                overlap = (min_dist - dist) / 2
                move_x = (dx / dist) * overlap
                move_y = (dy / dist) * overlap
                x[i] -= move_x
                y[i] -= move_y
                x[j] += move_x
                y[j] += move_y

# Center positions and compute tight limits
x -= x.mean()
y -= y.mean()
pad = 5
x_lo = (x - radii).min() - pad
x_hi = (x + radii).max() + pad
y_lo = (y - radii).min() - pad
y_hi = (y + radii).max() + pad

df = pd.DataFrame(
    {"label": categories, "value": values, "group": groups, "x": x, "y": y, "budget": [f"${v}M" for v in values]}
)

# Show labels on bubbles large enough; abbreviate long names
abbrev = {"Customer Support": "Support", "Operations": "Ops"}
df["display_label"] = df.apply(lambda row: abbrev.get(row["label"], row["label"]) if row["value"] >= 35 else "", axis=1)

# Plot using shape=21 (filled circle with border) for polished look
plot = (
    ggplot(df, aes(x="x", y="y"))
    + geom_point(
        aes(size="value", fill="group"),
        shape=21,
        color="white",
        stroke=1.2,
        alpha=0.88,
        tooltips=layer_tooltips().title("@label").line("Budget|@budget").line("Division|@group"),
    )
    + geom_text(aes(label="display_label"), size=7, color="white", fontface="bold")
    + scale_size(range=[20, 85], guide="none")
    + scale_fill_manual(values=["#FFD43B", "#4ECDC4", "#306998"])
    + labs(title="Department Budget Allocation · bubble-packed · letsplot · pyplots.ai", fill="Division")
    + xlim(x_lo, x_hi)
    + ylim(y_lo, y_hi)
    + theme_void()
    + theme(
        plot_title=element_text(size=24, hjust=0.5),
        legend_position="right",
        legend_title=element_text(size=20),
        legend_text=element_text(size=16),
        legend_background=element_rect(fill="white", color="#CCCCCC", size=0.5),
    )
    + ggsize(1200, 1200)
)

# Save
export_ggsave(plot, "plot.png", path=".", scale=3)
