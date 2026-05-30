"""anyplot.ai
arc-basic: Basic Arc Diagram
Library: pygal | Python 3.13
Quality: pending | Created: 2026-05-30
"""

import math
import os

import numpy as np
import pygal
from pygal.style import Style


# Theme tokens (see prompts/default-style-guide.md)
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Imprint categorical palette — arc weight encoding uses positions 1→3
IMPRINT_PALETTE = ("#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314")
NODE_FILL = "#DDCC77"  # Imprint amber — outside categorical pool

# Data: word co-occurrences in a scientific corpus (10 nodes)
np.random.seed(42)
nodes = ["science", "data", "research", "study", "analysis", "result", "method", "evidence", "theory", "review"]
n_nodes = len(nodes)

# Edges: (source_idx, target_idx, weight) — weight 1=rare, 2=moderate, 3=frequent
# "review" (index 9) has just one connection — demonstrates a peripheral node
edges = [
    (0, 2, 3),  # science–research (frequent)
    (1, 4, 3),  # data–analysis (frequent)
    (4, 5, 3),  # analysis–result (frequent)
    (0, 4, 2),  # science–analysis (moderate)
    (1, 5, 2),  # data–result (moderate)
    (2, 6, 2),  # research–method (moderate)
    (3, 6, 2),  # study–method (moderate)
    (6, 7, 2),  # method–evidence (moderate)
    (7, 8, 2),  # evidence–theory (moderate)
    (2, 8, 1),  # research–theory (rare)
    (3, 5, 1),  # study–result (rare)
    (1, 8, 1),  # data–theory (rare)
    (0, 9, 1),  # science–review (rare, long range — "review" has only this edge)
]

# Arc appearance — Imprint positions 1→3 in canonical order
arc_colors = {3: IMPRINT_PALETTE[0], 2: IMPRINT_PALETTE[1], 1: IMPRINT_PALETTE[2]}
arc_widths = {1: 5, 2: 14, 3: 26}
weight_labels = {1: "Rare", 2: "Moderate", 3: "Frequent"}

# Node positions along x-axis
x_positions = np.linspace(1, 9, n_nodes)
y_baseline = 0.5

# Colors tuple: 3 legend entries → 13 edge arcs → node outline → node fill
colors = tuple([arc_colors[3], arc_colors[2], arc_colors[1]] + [arc_colors[w] for _, _, w in edges] + [INK, NODE_FILL])

title = "Word Co-occurrences · arc-basic · python · pygal · anyplot.ai"

custom_style = Style(
    background=PAGE_BG,
    plot_background=PAGE_BG,
    foreground=INK,
    foreground_strong=INK,
    foreground_subtle=INK_MUTED,
    colors=colors,
    title_font_size=66,
    label_font_size=56,
    major_label_font_size=44,
    legend_font_size=44,
    value_font_size=36,
    stroke_width=2.5,
    opacity=0.85,
    opacity_hover=1.0,
)

chart = pygal.XY(
    width=3200,
    height=1800,
    style=custom_style,
    fill=False,
    title=title,
    show_legend=True,
    legend_at_bottom=True,
    legend_at_bottom_columns=3,
    legend_box_size=30,
    x_title="",
    y_title="",
    show_x_guides=False,
    show_y_guides=False,
    show_x_labels=True,
    show_y_labels=False,
    stroke=True,
    dots_size=0,
    stroke_style={"width": 6, "linecap": "round"},
    range=(0, 4.2),
    xrange=(0, 10),
    x_labels=[{"value": float(x_positions[i]), "label": nodes[i]} for i in range(n_nodes)],
    truncate_label=-1,
    css=[
        "file://style.css",  # pygal's color/stroke template — must come first
        "file://graph.css",  # title text-anchor:middle and layout rules
        f"inline:.plot .background {{fill: {PAGE_BG}; stroke: none !important;}}",
        "inline:.axis .line {stroke: none !important;}",
        "inline:.axis .guides .line {stroke: none !important;}",
        "inline:.plot .axis {stroke: none !important;}",
        "inline:.series .line {fill: none !important;}",
        # Hide all legend entries after the 3 weight categories
        "inline:.legends > g:nth-child(n+4) {display: none !important;}",
    ],
    js=[],
)

# Legend series (Frequent → Moderate → Rare, matching color assignment order)
for w_val, w_label in [(3, "Frequent"), (2, "Moderate"), (1, "Rare")]:
    chart.add(
        f"{w_label} co-occurrence",
        [None],
        stroke=True,
        show_dots=False,
        stroke_style={"width": arc_widths[w_val], "linecap": "round"},
    )

# Arc generation — semi-circle above baseline, height ∝ node distance
arc_resolution = 50

for start_idx, end_idx, weight in edges:
    x_start = x_positions[start_idx]
    x_end = x_positions[end_idx]
    x_center = (x_start + x_end) / 2
    arc_radius = abs(x_end - x_start) / 2
    distance = abs(end_idx - start_idx)
    height_scale = 0.4 * distance

    arc_points = [
        {
            "value": (
                x_center - arc_radius * math.cos(math.pi * i / arc_resolution),
                y_baseline + height_scale * math.sin(math.pi * i / arc_resolution),
            ),
            "label": f"{nodes[start_idx]} ↔ {nodes[end_idx]} ({weight_labels[weight]})",
        }
        for i in range(arc_resolution + 1)
    ]

    chart.add(
        "", arc_points, stroke=True, show_dots=False, stroke_style={"width": arc_widths[weight], "linecap": "round"}
    )

# Node outline ring (INK color) + amber fill on top for crisp visibility on both themes
node_points = [
    {
        "value": (float(x_positions[i]), y_baseline),
        "label": f"{nodes[i]} ({sum(1 for s, t, _ in edges if s == i or t == i)} connections)",
    }
    for i in range(n_nodes)
]
chart.add("", node_points, stroke=False, dots_size=42)
chart.add("", node_points, stroke=False, dots_size=32)

# Save PNG and interactive HTML
chart.render_to_png(f"plot-{THEME}.png")

with open(f"plot-{THEME}.html", "wb") as f:
    f.write(chart.render())
