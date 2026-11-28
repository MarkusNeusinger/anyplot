"""anyplot.ai
pie-basic: Basic Pie Chart
Library: plotnine 0.15.4 | Python 3.13.13
Quality: pending | Created: 2026-05-28
"""

import os
import sys


# Remove this file's directory from sys.path to prevent self-import
# (this file is named plotnine.py, same as the library being imported)
_dir = os.path.dirname(os.path.abspath(__file__))
sys.path = [p for p in sys.path if os.path.abspath(p) != _dir]

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from plotnine import (
    aes,
    coord_equal,
    element_rect,
    element_text,
    geom_polygon,
    geom_segment,
    geom_text,
    ggplot,
    labs,
    scale_color_identity,
    scale_fill_manual,
    theme,
    theme_void,
)


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: all eight positions, one per slice in order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Constants
EXPLODE_OFFSET = 0.07  # how far the largest slice is pulled out, in radii
SMALL_SHARE = 0.06  # slices narrower than this get their label outside with a leader line
DARK_TEXT = "#1A1A17"  # text on light slices, in both themes (slice colors do not change)

# Columns: set these to your table's column names
CATEGORY = "Commute mode"  # role: category
VALUE = "Share of commuters (%)"  # role: value

# Data: replace this block with your own table, for example df = pd.read_csv("shares.csv")
df = pd.DataFrame(
    {CATEGORY: ["Car", "Public transit", "Walking", "Cycling", "Remote work", "Other"], VALUE: [41, 23, 12, 10, 10, 4]}
)

# Plot: reads only df and the constants above
categories = df[CATEGORY].tolist()
shares = df[VALUE] / df[VALUE].sum()
largest = int(df[VALUE].to_numpy().argmax())

# Wedge polygons start at 12 o'clock and run clockwise
ends = shares.cumsum().to_numpy()
starts = ends - shares.to_numpy()
wedge_rows = []
label_rows = []
segment_rows = []
for i, cat in enumerate(categories):
    start_angle = np.pi / 2 - 2 * np.pi * starts[i]
    end_angle = np.pi / 2 - 2 * np.pi * ends[i]
    mid_angle = (start_angle + end_angle) / 2
    offset = EXPLODE_OFFSET if i == largest else 0.0
    dx, dy = offset * np.cos(mid_angle), offset * np.sin(mid_angle)

    arc = np.linspace(start_angle, end_angle, 80)
    xs = np.concatenate([[0.0], np.cos(arc)]) + dx
    ys = np.concatenate([[0.0], np.sin(arc)]) + dy
    wedge_rows.append(pd.DataFrame({"x": xs, "y": ys, "category": cat}))

    label = f"{shares.iloc[i] * 100:.0f}%"
    if not shares.iloc[i] < SMALL_SHARE:
        # Inside the slice; dark or white text, whichever contrasts with the slice color
        r, g, b = (int(IMPRINT_PALETTE[i][k : k + 2], 16) / 255 for k in (1, 3, 5))
        luminance = 0.2126 * r**3 + 0.7152 * g**3 + 0.0722 * b**3  # cheap gamma-ish approximation
        text_color = DARK_TEXT if luminance > 0.12 else "#FFFFFF"
        label_r = 0.62 + offset
        label_rows.append(
            {
                "x": label_r * np.cos(mid_angle) + dx,
                "y": label_r * np.sin(mid_angle) + dy,
                "label": label,
                "ink": text_color,
            }
        )
    else:
        # Narrow slice: label beside it, tied to the slice edge by a short leader line
        segment_rows.append(
            {
                "x": 1.0 * np.cos(mid_angle),
                "y": 1.0 * np.sin(mid_angle),
                "xend": 1.12 * np.cos(mid_angle),
                "yend": 1.12 * np.sin(mid_angle),
            }
        )
        label_rows.append({"x": 1.22 * np.cos(mid_angle), "y": 1.22 * np.sin(mid_angle), "label": label, "ink": INK})

df_wedges = pd.concat(wedge_rows, ignore_index=True)
df_wedges["category"] = pd.Categorical(df_wedges["category"], categories=categories, ordered=True)
df_labels = pd.DataFrame(label_rows)
df_segments = pd.DataFrame(segment_rows)

leader_lines = (
    geom_segment(data=df_segments, mapping=aes(x="x", y="y", xend="xend", yend="yend"), color=INK_SOFT, size=0.5)
    if len(df_segments)
    else []
)

plot = (
    ggplot()
    + geom_polygon(data=df_wedges, mapping=aes(x="x", y="y", fill="category", group="category"))
    + leader_lines
    + geom_text(data=df_labels, mapping=aes(x="x", y="y", label="label", color="ink"), size=8.0)
    + scale_fill_manual(values=IMPRINT_PALETTE, limits=categories)
    + scale_color_identity()
    + coord_equal()
    + labs(title="pie-basic · python · plotnine · anyplot.ai", fill=CATEGORY)
    + theme_void()
    + theme(
        figure_size=(6, 6),
        plot_margin_right=0.04,
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG),
        plot_title=element_text(size=12, color=INK, ha="center"),
        legend_text=element_text(size=9, color=INK_SOFT),
        legend_title=element_text(size=10, color=INK),
        legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT),
        legend_key=element_rect(fill=ELEVATED_BG, color=ELEVATED_BG),
    )
)

# Draw and save; subplots_adjust gives the right-side legend room
fig = plot.draw()
fig.subplots_adjust(left=0.02, right=0.76)
fig.savefig(f"plot-{THEME}.png", dpi=400)
plt.close(fig)
