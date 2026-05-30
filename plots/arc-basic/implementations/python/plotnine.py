""" anyplot.ai
arc-basic: Basic Arc Diagram
Library: plotnine 0.15.4 | Python 3.13.13
Quality: 86/100 | Updated: 2026-05-30
"""

import os
import sys


sys.path = [p for p in sys.path if p and not p.endswith("implementations") and not p.endswith("/python")]

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from plotnine import (  # noqa: E402
    aes,
    coord_cartesian,
    element_rect,
    element_text,
    geom_path,
    geom_point,
    geom_segment,
    geom_text,
    ggplot,
    guide_colorbar,
    labs,
    scale_alpha_identity,
    scale_color_gradient,
    scale_size_identity,
    theme,
    theme_void,
)


# Theme tokens (Imprint palette — theme-adaptive chrome)
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Imprint sequential gradient for arc weight encoding (position 1 → position 3)
ARC_LOW = "#009E73"  # weak connections — Imprint brand green
ARC_HIGH = "#4467A3"  # strong connections — Imprint blue

# Data: Character interactions in a story chapter
nodes = ["Alice", "Bob", "Carol", "David", "Eve", "Frank", "Grace", "Henry", "Iris", "Jack"]
n_nodes = len(nodes)

edges = [
    (0, 1, 3),  # Alice-Bob (strong)
    (0, 3, 2),  # Alice-David
    (1, 2, 2),  # Bob-Carol
    (2, 4, 1),  # Carol-Eve
    (3, 5, 2),  # David-Frank
    (4, 6, 1),  # Eve-Grace
    (0, 7, 1),  # Alice-Henry (long-range)
    (1, 5, 2),  # Bob-Frank
    (2, 3, 3),  # Carol-David (strong)
    (5, 8, 1),  # Frank-Iris
    (6, 9, 2),  # Grace-Jack
    (0, 9, 1),  # Alice-Jack (longest range)
    (3, 7, 2),  # David-Henry
    (7, 8, 1),  # Henry-Iris
    (8, 9, 2),  # Iris-Jack
]

x_positions = np.linspace(0, 1, n_nodes)
y_baseline = 0.0

# Node degree for proportional sizing (degree 2→6, 3→7.5, 4→9)
node_degree = [0] * n_nodes
for s, e, _ in edges:
    node_degree[s] += 1
    node_degree[e] += 1
node_sizes = [3.0 + d * 1.5 for d in node_degree]

n_points = 60
theta = np.linspace(0, np.pi, n_points)
arc_rows = []

for arc_id, (start, end, weight) in enumerate(edges):
    x_start, x_end = x_positions[start], x_positions[end]
    x_center = (x_start + x_end) / 2
    arc_radius = abs(x_end - x_start) / 2
    height = 0.08 * abs(end - start)

    x_arc = x_center - arc_radius * np.cos(theta)
    y_arc = y_baseline + height * np.sin(theta)

    arc_rows.append(
        pd.DataFrame(
            {
                "x": x_arc,
                "y": y_arc,
                "arc_id": arc_id,
                "weight": float(weight),
                "size": 1.0 + weight * 0.45,  # weight=1: 1.45, weight=3: 2.35
                "alpha": 0.62 + weight * 0.10,  # weight=1: 0.72, weight=3: 0.92
            }
        )
    )

arc_df = pd.concat(arc_rows, ignore_index=True)

baseline_df = pd.DataFrame({"x": [x_positions[0]], "xend": [x_positions[-1]], "y": [y_baseline], "yend": [y_baseline]})
node_df = pd.DataFrame({"x": x_positions, "y": [y_baseline] * n_nodes, "size": node_sizes})
label_df = pd.DataFrame({"x": x_positions, "y": [y_baseline - 0.035] * n_nodes, "name": nodes})

# Callout annotation for Alice–Jack: the longest-range arc (nodes 0→9, height=0.72)
alice_jack_apex_x = (x_positions[0] + x_positions[9]) / 2  # 0.5
alice_jack_apex_y = 0.08 * abs(9 - 0)  # 0.72
callout_df = pd.DataFrame(
    {"x": [alice_jack_apex_x], "y": [alice_jack_apex_y + 0.04], "label": ["Alice–Jack: longest-range arc"]}
)

# Title: "Character Interactions · arc-basic · python · plotnine · anyplot.ai" = 67 chars, no scaling
title = "Character Interactions · arc-basic · python · plotnine · anyplot.ai"

plot = (
    ggplot()
    + geom_segment(
        baseline_df, aes(x="x", y="y", xend="xend", yend="yend"), color=INK_MUTED, size=0.5, linetype="solid"
    )
    + geom_path(arc_df, aes(x="x", y="y", group="arc_id", color="weight", size="size", alpha="alpha"))
    + scale_color_gradient(
        low=ARC_LOW,
        high=ARC_HIGH,
        name="Interaction\nStrength",
        breaks=[1, 2, 3],
        labels=["Weak", "Medium", "Strong"],
        guide=guide_colorbar(direction="vertical"),
    )
    + scale_size_identity()
    + scale_alpha_identity()
    + geom_point(node_df, aes(x="x", y="y", size="size"), color=INK, stroke=1.2, fill=PAGE_BG)
    + geom_text(label_df, aes(x="x", y="y", label="name"), size=5, color=INK, fontweight="bold", va="top")
    + geom_text(callout_df, aes(x="x", y="y", label="label"), size=3.5, color=INK_SOFT, ha="center")
    + coord_cartesian(xlim=(-0.06, 1.06), ylim=(-0.12, 0.82))
    + labs(
        title=title, subtitle="Narrative connections in Chapter 1 — arc thickness and color encode interaction strength"
    )
    + theme_void()
    + theme(
        figure_size=(8, 4.5),
        plot_title=element_text(size=12, ha="center", weight="bold", color=INK),
        plot_subtitle=element_text(size=8, ha="center", color=INK_SOFT),
        plot_margin=0.02,
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        legend_position="right",
        legend_title=element_text(size=8, weight="bold", color=INK),
        legend_text=element_text(size=7, color=INK_SOFT),
        legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT),
        legend_key_height=30,
        legend_key_width=8,
    )
)

plot.save(f"plot-{THEME}.png", dpi=400, width=8, height=4.5, units="in", verbose=False)
