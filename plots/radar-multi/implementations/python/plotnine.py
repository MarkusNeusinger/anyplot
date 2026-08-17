"""anyplot.ai
radar-multi: Multi-Series Radar Chart
Library: plotnine 0.15.8 | Python 3.13.12
Quality: pending | Updated: 2026-08-17
"""

import math
import os

import numpy as np
import pandas as pd
from plotnine import (
    aes,
    element_blank,
    element_rect,
    element_text,
    geom_path,
    geom_point,
    geom_polygon,
    geom_text,
    ggplot,
    labs,
    scale_color_manual,
    scale_fill_manual,
    scale_x_continuous,
    scale_y_continuous,
    theme,
)


# Theme tokens (see prompts/default-style-guide.md "Background" + "Theme-adaptive Chrome")
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Data - basketball player archetypes scouted across six on-court skills
categories = ["Speed", "Strength", "Endurance", "Accuracy", "Agility", "Consistency"]
n = len(categories)

players = {
    "Playmaker": [75, 55, 70, 90, 95, 80],
    "Enforcer": [60, 95, 85, 55, 50, 75],
    "Finisher": [90, 65, 60, 85, 80, 70],
}

# Imprint palette - first series is always #009E73
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3"]

# Evenly spaced axis angles, starting at 12 o'clock and going clockwise
angles = [i * 2 * math.pi / n for i in range(n)]

# Polygon vertices per player, closing each shape back to its first point
vertex_rows = []
for player, values in players.items():
    for i, (category, value, angle) in enumerate(zip(categories, values, angles, strict=True)):
        vertex_rows.append({"category": category, "value": value, "angle": angle, "player": player, "order": i})
    vertex_rows.append(
        {"category": categories[0], "value": values[0], "angle": angles[0], "player": player, "order": n}
    )

vertices = pd.DataFrame(vertex_rows)
vertices["x"] = vertices["value"] * np.cos(vertices["angle"] - math.pi / 2)
vertices["y"] = vertices["value"] * np.sin(vertices["angle"] - math.pi / 2)

# Concentric reference rings at 20/40/60/80/100 (geom_path keeps angular order,
# unlike geom_line which would re-sort points by x and mangle the circle)
ring_angles = np.linspace(0, 2 * math.pi, 121)
rings = pd.concat(
    [
        pd.DataFrame(
            {
                "x": radius * np.cos(ring_angles - math.pi / 2),
                "y": radius * np.sin(ring_angles - math.pi / 2),
                "radius": radius,
            }
        )
        for radius in (20, 40, 60, 80, 100)
    ],
    ignore_index=True,
)

# Spokes from the center out to each axis
spokes = pd.DataFrame(
    [
        {"x": r * math.cos(angle - math.pi / 2), "y": r * math.sin(angle - math.pi / 2), "axis": angle}
        for angle in angles
        for r in (0, 105)
    ]
)

# Axis labels just outside the outer ring
axis_labels = pd.DataFrame(
    {
        "category": categories,
        "x": [118 * math.cos(a - math.pi / 2) for a in angles],
        "y": [118 * math.sin(a - math.pi / 2) for a in angles],
    }
)

# Plot
plot = (
    ggplot()
    + geom_path(aes(x="x", y="y", group="radius"), data=rings, color=INK_SOFT, size=0.4, alpha=0.2, linetype="dashed")
    + geom_path(aes(x="x", y="y", group="axis"), data=spokes, color=INK_SOFT, size=0.4, alpha=0.2)
    + geom_polygon(aes(x="x", y="y", fill="player", group="player"), data=vertices, alpha=0.25)
    + geom_path(aes(x="x", y="y", color="player", group="player"), data=vertices, size=1.3)
    + geom_point(aes(x="x", y="y", color="player"), data=vertices[vertices["order"] < n], size=3.2)
    + geom_text(aes(x="x", y="y", label="category"), data=axis_labels, size=3.5, color=INK)
    + scale_fill_manual(values=IMPRINT_PALETTE)
    + scale_color_manual(values=IMPRINT_PALETTE)
    + scale_x_continuous(limits=(-140, 140))
    + scale_y_continuous(limits=(-140, 140))
    + labs(title="radar-multi · python · plotnine · anyplot.ai", fill="Archetype", color="Archetype")
    + theme(
        figure_size=(6, 6),
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        plot_title=element_text(size=12, color=INK),
        legend_background=element_rect(fill=PAGE_BG, color=INK_SOFT),
        legend_title=element_text(size=9, color=INK),
        legend_text=element_text(size=8, color=INK_SOFT),
        axis_title=element_blank(),
        axis_text=element_blank(),
        axis_ticks=element_blank(),
        axis_line=element_blank(),
        panel_grid_major=element_blank(),
        panel_grid_minor=element_blank(),
        panel_border=element_blank(),
    )
)

# Save
plot.save(f"plot-{THEME}.png", dpi=400, width=6, height=6, units="in")
