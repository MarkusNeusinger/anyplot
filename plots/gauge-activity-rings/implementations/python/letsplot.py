""" anyplot.ai
gauge-activity-rings: Activity Rings Progress Chart
Library: letsplot 4.11.0 | Python 3.14.10
Quality: 84/100 | Updated: 2026-11-26
"""

import os

import numpy as np
import pandas as pd
from lets_plot import *


LetsPlot.setup_html()

# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Imprint palette: all eight positions, one per ring in order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Columns: set these to your table's column names
METRIC = "Metric"  # role: metric
VALUE = "Value"  # role: value
GOAL = "Goal"  # role: goal
UNIT = "Unit"  # role: extra

# Data: replace this block with your own table, for example df = pd.read_csv("activity.csv")
df = pd.DataFrame(
    {METRIC: ["Move", "Exercise", "Stand"], VALUE: [420, 25, 9], GOAL: [600, 30, 12], UNIT: ["kcal", "min", "hr"]}
)

# Plot: reads only df and the constants above
n_rings = len(df)
n_pts = 300

# Ring geometry, outer to inner, equal gaps
outer = 2.5
gap = min(0.8, (outer - 0.5) / max(n_rings - 1, 1))
radii = [outer - i * gap for i in range(n_rings)]
ring_color_map = dict(zip(df[METRIC], IMPRINT_PALETTE, strict=False))

# Build arc path data: a full-circle track and a clockwise progress arc per ring, from 12 o'clock
track_rows, arc_rows = [], []
for (_, ring), r in zip(df.iterrows(), radii, strict=True):
    ratio = ring[VALUE] / ring[GOAL]
    frac = min(ratio, 1.0)
    pct_label = f"{ratio * 100:.0f}%"
    progress = f"{ring[VALUE]:g} / {ring[GOAL]:g} {ring[UNIT]}"

    a_track = np.linspace(np.pi / 2, np.pi / 2 - 2 * np.pi, n_pts + 1)
    track_rows.append(
        pd.DataFrame(
            {"x": r * np.cos(a_track), "y": r * np.sin(a_track), "group": f"track_{ring[METRIC]}", "name": ring[METRIC]}
        )
    )

    n_arc = max(4, int(n_pts * frac) + 1)
    a_arc = np.linspace(np.pi / 2, np.pi / 2 - 2 * np.pi * frac, n_arc)
    arc_rows.append(
        pd.DataFrame(
            {
                "x": r * np.cos(a_arc),
                "y": r * np.sin(a_arc),
                "group": f"arc_{ring[METRIC]}",
                "name": ring[METRIC],
                "pct_label": pct_label,
                "progress": progress,
            }
        )
    )

track_df = pd.concat(track_rows, ignore_index=True)
arc_df = pd.concat(arc_rows, ignore_index=True)

# Labels below the rings, spread evenly across the width
label_x = (np.arange(n_rings) - (n_rings - 1) / 2) * (7.2 / n_rings)
pct = df[VALUE] / df[GOAL] * 100
progress_text = pd.Series(
    [f"{v:g} / {g:g} {u}" for v, g, u in zip(df[VALUE], df[GOAL], df[UNIT], strict=True)], index=df.index
)
pct_text = pd.Series([f"{p:.0f}%" for p in pct], index=df.index)
label_df = pd.DataFrame(
    {
        "x": label_x,
        "y": -outer * 1.28,
        "label": df[METRIC] + "  " + pct_text,
        "name": df[METRIC],
        "pct_label": pct_text,
        "progress": progress_text,
    }
)
sub_df = pd.DataFrame({"x": label_x, "y": -outer * 1.48, "label": progress_text})

# Center annotation, inside the innermost ring
center_df = pd.DataFrame([{"x": 0, "y": 0.22, "label": "Daily"}, {"x": 0, "y": -0.30, "label": "Activity"}])

# Title — scaled for length
title = "gauge-activity-rings · python · letsplot · anyplot.ai"
n_chars = len(title)
title_scale = 67 / n_chars if n_chars > 67 else 1.0
title_size = max(11, round(16 * title_scale))

TRACK_ALPHA = 0.15 if THEME == "light" else 0.25

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
        data=track_df,
        mapping=aes(x="x", y="y", group="group", color="name"),
        size=8,
        alpha=TRACK_ALPHA,
        show_legend=False,
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
        data=sub_df, mapping=aes(x="x", y="y", label="label"), color=INK_MUTED, size=3.5, hjust=0.5, show_legend=False
    )
    # Center text
    + geom_text(data=center_df, mapping=aes(x="x", y="y", label="label"), color=INK_SOFT, size=4.0, show_legend=False)
    + scale_color_manual(values=ring_color_map)
    + scale_x_continuous(limits=[-outer * 1.4, outer * 1.4])
    + scale_y_continuous(limits=[-outer * 1.72, outer * 1.32])
    + coord_fixed()
    + labs(title=title)
    + ggsize(600, 600)
    + anyplot_theme
)

# The one-panel grid paints the whole square canvas; coord_fixed alone leaves transparent strips
plot = gggrid([plot]) + ggsize(600, 600) + theme(plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG))

# Save PNG (square canvas: 600 × 600 × scale=4 = 2400 × 2400 px) and interactive HTML
ggsave(plot, f"plot-{THEME}.png", path=".", scale=4)
ggsave(plot, f"plot-{THEME}.html", path=".")
