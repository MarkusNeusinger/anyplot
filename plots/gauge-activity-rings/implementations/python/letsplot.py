""" anyplot.ai
gauge-activity-rings: Activity Rings Progress Chart
Library: letsplot 4.10.1 | Python 3.13.13
Quality: 88/100 | Created: 2026-06-14
"""

import os

import numpy as np
import pandas as pd
from lets_plot import *


LetsPlot.setup_html()

# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Imprint palette — positions 1-3 for the three rings
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Data — daily fitness tracker activity rings
rings_data = [
    {"name": "Move", "value": 420, "goal": 600, "unit": "kcal"},
    {"name": "Exercise", "value": 25, "goal": 30, "unit": "min"},
    {"name": "Stand", "value": 9, "goal": 12, "unit": "hr"},
]
ring_color_map = {r["name"]: IMPRINT_PALETTE[i] for i, r in enumerate(rings_data)}

# Ring geometry — outer to inner
radii = [2.5, 1.7, 0.9]
n_pts = 300

# Build arc path data
track_rows, arc_rows = [], []
for ring, r in zip(rings_data, radii, strict=False):
    frac = min(ring["value"] / ring["goal"], 1.0)
    pct = ring["value"] / ring["goal"] * 100

    # Background track (full circle, low opacity)
    a_track = np.linspace(np.pi / 2, np.pi / 2 - 2 * np.pi, n_pts + 1)
    for a in a_track:
        track_rows.append(
            {"x": r * np.cos(a), "y": r * np.sin(a), "group": f"track_{ring['name']}", "name": ring["name"]}
        )

    # Progress arc sweeping clockwise from 12 o'clock
    n_arc = max(4, int(n_pts * frac) + 1)
    a_arc = np.linspace(np.pi / 2, np.pi / 2 - 2 * np.pi * frac, n_arc)
    for a in a_arc:
        arc_rows.append(
            {
                "x": r * np.cos(a),
                "y": r * np.sin(a),
                "group": f"arc_{ring['name']}",
                "name": ring["name"],
                "pct_label": f"{pct:.0f}%",
                "progress": f"{ring['value']} / {ring['goal']} {ring['unit']}",
            }
        )

track_df = pd.DataFrame(track_rows)
arc_df = pd.DataFrame(arc_rows)

# Labels below the rings — centered under each ring's approximate x position
label_x = [-2.4, 0.0, 2.4]
label_rows, sub_rows = [], []
for ring, xp in zip(rings_data, label_x, strict=False):
    pct = ring["value"] / ring["goal"] * 100
    label_rows.append(
        {
            "x": xp,
            "y": -3.2,
            "label": f"{ring['name']}  {pct:.0f}%",
            "name": ring["name"],
            "pct_label": f"{pct:.0f}%",
            "progress": f"{ring['value']} / {ring['goal']} {ring['unit']}",
        }
    )
    sub_rows.append(
        {"x": xp, "y": -3.7, "label": f"{ring['value']} / {ring['goal']} {ring['unit']}", "name": ring["name"]}
    )

label_df = pd.DataFrame(label_rows)
sub_df = pd.DataFrame(sub_rows)

# Center annotation
center_df = pd.DataFrame([{"x": 0, "y": 0.22, "label": "Daily"}, {"x": 0, "y": -0.30, "label": "Activity"}])

# Title — scaled for length
title = "gauge-activity-rings · python · letsplot · anyplot.ai"
n_chars = len(title)
ratio = 67 / n_chars if n_chars > 67 else 1.0
title_size = max(11, round(16 * ratio))

anyplot_theme = theme_void() + theme(
    plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
    panel_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
    panel_border=element_blank(),
    plot_title=element_text(color=INK, size=title_size, hjust=0.5),
    legend_position="none",
)

plot = (
    ggplot()
    # Background tracks (full circles, faint)
    + geom_path(
        data=track_df, mapping=aes(x="x", y="y", group="group", color="name"), size=8, alpha=0.15, show_legend=False
    )
    # Progress arcs with rounded end caps for the iconic activity-ring look
    + geom_path(
        data=arc_df,
        mapping=aes(x="x", y="y", group="group", color="name"),
        size=8,
        show_legend=False,
        lineend="round",
        tooltips=layer_tooltips().line("@name").line("Progress: @pct_label").line("@progress"),
    )
    # Ring name + percentage labels (with letsplot interactive tooltips)
    + geom_text(
        data=label_df,
        mapping=aes(x="x", y="y", label="label", color="name"),
        size=4.0,
        hjust=0.5,
        show_legend=False,
        tooltips=layer_tooltips().line("@name").line("@pct_label").line("@progress"),
    )
    # Value / goal sub-labels
    + geom_text(
        data=sub_df, mapping=aes(x="x", y="y", label="label"), color=INK_MUTED, size=3.0, hjust=0.5, show_legend=False
    )
    # Center text
    + geom_text(data=center_df, mapping=aes(x="x", y="y", label="label"), color=INK_SOFT, size=4.0, show_legend=False)
    + scale_color_manual(values=ring_color_map)
    + scale_x_continuous(limits=[-3.5, 3.5])
    + scale_y_continuous(limits=[-4.3, 3.3])
    + coord_fixed()
    + labs(title=title)
    + ggsize(600, 600)
    + anyplot_theme
)

# Save PNG (square canvas: 600 × 600 × scale=4 = 2400 × 2400 px)
ggsave(plot, f"plot-{THEME}.png", path=".", scale=4)
ggsave(plot, f"plot-{THEME}.html", path=".")
