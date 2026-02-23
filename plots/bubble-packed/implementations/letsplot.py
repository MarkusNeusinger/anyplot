"""pyplots.ai
bubble-packed: Basic Packed Bubble Chart
Library: letsplot 4.8.2 | Python 3.14.3
Quality: /100 | Updated: 2026-02-23
"""

import numpy as np
import pandas as pd
from lets_plot import (
    LetsPlot,
    aes,
    coord_fixed,
    element_text,
    geom_point,
    geom_text,
    ggplot,
    ggsize,
    labs,
    layer_tooltips,
    scale_color_manual,
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

# Circle packing using force simulation
n = len(values)
radii = np.sqrt(values / np.pi) * 3.5

# Initialize positions
np.random.seed(42)
x = np.random.uniform(-100, 100, n)
y = np.random.uniform(-100, 100, n)

# Force-directed packing simulation
for _ in range(600):
    x *= 0.99
    y *= 0.99

    for i in range(n):
        for j in range(i + 1, n):
            dx = x[j] - x[i]
            dy = y[j] - y[i]
            dist = np.sqrt(dx * dx + dy * dy)
            min_dist = radii[i] + radii[j] + 0.5

            if dist < min_dist and dist > 0:
                overlap = (min_dist - dist) / 2
                move_x = (dx / dist) * overlap
                move_y = (dy / dist) * overlap
                x[i] -= move_x
                y[i] -= move_y
                x[j] += move_x
                y[j] += move_y

df = pd.DataFrame(
    {"label": categories, "value": values, "group": groups, "x": x, "y": y, "budget": [f"${v}M" for v in values]}
)

# Show labels only on bubbles large enough to fit text
df["display_label"] = df.apply(lambda row: row["label"] if row["value"] >= 35 else "", axis=1)
# Abbreviate long labels
abbrev = {"Customer Support": "Support", "Operations": "Ops"}
df["display_label"] = df["display_label"].replace(abbrev)

# Plot
plot = (
    ggplot(df, aes(x="x", y="y"))
    + geom_point(
        aes(size="value", color="group"),
        alpha=0.85,
        tooltips=layer_tooltips().title("@label").line("Budget|@budget").line("Division|@group"),
    )
    + geom_text(aes(label="display_label"), size=7, color="white", fontface="bold")
    + scale_size(range=[20, 85], guide="none")
    + scale_color_manual(values=["#FFD43B", "#4ECDC4", "#306998"])
    + labs(title="Department Budget Allocation · bubble-packed · letsplot · pyplots.ai", color="Division")
    + xlim(-70, 70)
    + ylim(-70, 55)
    + theme_void()
    + theme(
        plot_title=element_text(size=24, hjust=0.5),
        legend_position="right",
        legend_title=element_text(size=18),
        legend_text=element_text(size=16),
    )
    + coord_fixed()
    + ggsize(1600, 900)
)

# Save
export_ggsave(plot, "plot.png", path=".", scale=3)
