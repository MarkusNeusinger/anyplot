""" anyplot.ai
swarm-basic: Basic Swarm Plot
Library: pygal 3.1.0 | Python 3.13.13
Quality: 80/100 | Updated: 2026-05-05
"""

import os

import numpy as np
import pygal
from pygal.style import Style


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

OKABE_ITO = ("#009E73", "#D55E00", "#0072B2", "#CC79A7", "#E69F00", "#56B4E9", "#F0E442")

# Data - Employee performance scores by department
np.random.seed(42)
categories = ["Engineering", "Marketing", "Sales", "Operations"]
data = {
    "Engineering": np.random.normal(82, 8, 45),
    "Marketing": np.random.normal(75, 12, 50),
    "Sales": np.random.normal(78, 15, 40),
    "Operations": np.random.normal(70, 10, 55),
}

# Style
custom_style = Style(
    background=PAGE_BG,
    plot_background=PAGE_BG,
    foreground=INK,
    foreground_strong=INK,
    foreground_subtle=INK_MUTED,
    colors=OKABE_ITO,
    title_font_size=72,
    label_font_size=48,
    major_label_font_size=42,
    legend_font_size=42,
    tooltip_font_size=36,
    opacity=0.85,
    opacity_hover=1.0,
)

# Plot
chart = pygal.XY(
    width=4800,
    height=2700,
    style=custom_style,
    title="swarm-basic · pygal · anyplot.ai",
    x_title="Department",
    y_title="Performance Score",
    show_legend=True,
    legend_at_bottom=True,
    stroke=False,
    dots_size=12,
    show_x_guides=False,
    show_y_guides=True,
    xrange=(0, 5),
    range=(40, 115),
    margin=50,
)

# Beeswarm algorithm - spreads points horizontally to avoid overlap
for cat_idx, (category, values) in enumerate(data.items()):
    center_x = cat_idx + 1
    point_radius = 0.1
    spacing = 0.05

    sorted_indices = np.argsort(values)
    placed = []
    swarm_points = []

    for idx in sorted_indices:
        y = float(values[idx])
        x = center_x
        offset = 0
        direction = 1

        while True:
            test_x = center_x + offset * direction
            overlap = False
            for px, py in placed:
                dist_y = abs(y - py)
                dist_x = abs(test_x - px)
                min_dist = 2 * point_radius + spacing
                if dist_y < min_dist and dist_x < min_dist:
                    overlap = True
                    break
            if not overlap:
                x = test_x
                break
            if direction == 1:
                direction = -1
            else:
                direction = 1
                offset += point_radius + spacing / 2

        placed.append((x, y))
        swarm_points.append((x, y))

    chart.add(category, swarm_points)

# x-axis category labels
chart.x_labels = ["", "Engineering", "Marketing", "Sales", "Operations", ""]

# Save
chart.render_to_png(f"plot-{THEME}.png")
with open(f"plot-{THEME}.html", "wb") as f:
    f.write(chart.render())
