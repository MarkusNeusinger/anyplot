"""anyplot.ai
bubble-packed: Basic Packed Bubble Chart
Library: plotnine 0.15.9 | Python 3.14.10
Quality: pending | Updated: 2026-11-27
"""

import os
import sys


# Remove the script's own directory from sys.path so the installed plotnine package is found
_here = os.path.dirname(os.path.abspath(__file__))
if _here in sys.path:
    sys.path.remove(_here)

import numpy as np
import pandas as pd
from plotnine import (
    aes,
    coord_fixed,
    element_rect,
    element_text,
    geom_polygon,
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

# Imprint palette: all eight positions, one per group in order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Constants
GAP = 0.03  # space kept between neighbouring circles
LARGE_SHARE = 0.5  # circles at or above this share of the largest value carry name and value
MEDIUM_SHARE = 0.3  # circles at or above this share carry name and value in a smaller size

# Columns: set these to your table's column names
LABEL = "Item"  # role: label
VALUE = "Revenue (USD billion)"  # role: value
GROUP = "Tech Segment"  # role: group

# Data: replace this block with your own table, for example df = pd.read_csv("items.csv")
df = pd.DataFrame(
    {
        LABEL: [
            "Cloud",
            "SaaS",
            "Security",
            "Analytics",
            "Dev Tools",
            "Chips",
            "Storage",
            "Networks",
            "Displays",
            "Peripherals",
            "Consulting",
            "IT Services",
            "Training",
            "Managed Services",
            "API Platforms",
            "Mobile",
            "Gaming",
            "Streaming",
            "Smart Home",
            "Wearables",
        ],
        VALUE: [52, 38, 29, 24, 16, 48, 31, 27, 18, 12, 34, 22, 14, 11, 9, 44, 35, 26, 17, 13],
        GROUP: ["Software"] * 5 + ["Hardware"] * 5 + ["Services"] * 5 + ["Consumer"] * 5,
    }
)

# Plot: reads only df and the constants above
RADIUS, X, Y, CIRCLE, VALUE_TEXT, LABEL_COLOR = "radius", "x", "y", "circle_id", "value_text", "label_color"

items = df.dropna(subset=[VALUE]).reset_index(drop=True)
groups = items[GROUP].dropna().unique().tolist()
group_colors = {g: IMPRINT_PALETTE[i] for i, g in enumerate(groups)}

# Area-based radius: circle area is proportional to value
items[RADIUS] = np.sqrt(items[VALUE] / items[VALUE].max())

# Circle packing: greedy placement with vectorized collision detection
n = len(items)
order = np.argsort(-items[RADIUS].to_numpy())
sorted_radii = items[RADIUS].to_numpy()[order]
x_pos = np.zeros(n)
y_pos = np.zeros(n)
angles_sweep = np.linspace(0, 2 * np.pi, 72, endpoint=False)

for i in range(1, n):
    best_dist = float("inf")
    best_x, best_y = 0.0, 0.0
    target_r = sorted_radii[i]

    for ref in range(i):
        place_r = sorted_radii[ref] + target_r + GAP
        cx = x_pos[ref] + place_r * np.cos(angles_sweep)
        cy = y_pos[ref] + place_r * np.sin(angles_sweep)

        dists_c = np.hypot(cx[:, np.newaxis] - x_pos[:i][np.newaxis, :], cy[:, np.newaxis] - y_pos[:i][np.newaxis, :])
        valid = np.all(dists_c >= target_r + sorted_radii[:i] + GAP, axis=1)

        valid_dists = np.where(valid, cx**2 + cy**2, float("inf"))
        best_k = np.argmin(valid_dists)
        if valid_dists[best_k] < best_dist:
            best_dist = valid_dists[best_k]
            best_x, best_y = cx[best_k], cy[best_k]

    x_pos[i] = best_x
    y_pos[i] = best_y

# Force simulation tightens the packing (vectorized)
tri = np.triu(np.ones((n, n), dtype=bool), k=1)
min_dists = sorted_radii[:, np.newaxis] + sorted_radii[np.newaxis, :] + GAP

for step in range(3000):
    if step < 2000:
        x_pos *= 0.997
        y_pos *= 0.997

    dx = x_pos[:, np.newaxis] - x_pos[np.newaxis, :]
    dy = y_pos[:, np.newaxis] - y_pos[np.newaxis, :]
    dists = np.hypot(dx, dy)

    overlap = tri & (dists < min_dists) & (dists > 1e-3)
    if overlap.any():
        safe_dists = np.where(dists > 1e-3, dists, 1.0)
        push = ((min_dists - dists) / (2 * safe_dists)) * overlap
        corr_x = push * dx
        corr_y = push * dy
        x_pos += corr_x.sum(axis=1) - corr_x.sum(axis=0)
        y_pos += corr_y.sum(axis=1) - corr_y.sum(axis=0)

# Restore the data's order
items[X] = np.zeros(n)
items[Y] = np.zeros(n)
items.loc[order, X] = x_pos
items.loc[order, Y] = y_pos

# Circle outlines for geom_polygon
angles = np.linspace(0, 2 * np.pi, 64)
circles = pd.DataFrame(
    {
        X: (items[X].to_numpy()[:, None] + items[RADIUS].to_numpy()[:, None] * np.cos(angles)).ravel(),
        Y: (items[Y].to_numpy()[:, None] + items[RADIUS].to_numpy()[:, None] * np.sin(angles)).ravel(),
        GROUP: np.repeat(items[GROUP].to_numpy(), len(angles)),
        CIRCLE: np.repeat(np.arange(n), len(angles)),
    }
)
circles[GROUP] = pd.Categorical(circles[GROUP], categories=groups)


# Labels: name and value per bubble, tiered by bubble size; ink color chosen by fill luminance
def luminance(hex_color):
    rgb = np.array([int(hex_color[i : i + 2], 16) / 255 for i in (1, 3, 5)])
    rgb = np.where(rgb <= 0.03928, rgb / 12.92, ((rgb + 0.055) / 1.055) ** 2.4)
    return float(rgb @ [0.2126, 0.7152, 0.0722])


LABEL_INK = "#1A1A17"
items[LABEL_COLOR] = items[GROUP].map(
    lambda g: LABEL_INK if luminance(group_colors.get(g, IMPRINT_PALETTE[0])) > 0.2 else "white"
)
items[VALUE_TEXT] = items[VALUE].map(lambda v: f"${v:g}B")
share = items[VALUE] / items[VALUE].max()
large = items[share >= LARGE_SHARE]
medium = items[(share >= MEDIUM_SHARE) & (share < LARGE_SHARE)]
small = items[share < MEDIUM_SHARE]

# Group totals for the subtitle
group_totals = items.groupby(GROUP, sort=False)[VALUE].sum()
subtitle_text = " · ".join(f"{g}: \\${t:g}B" for g, t in group_totals.items())

# Square viewport around the packed cluster
pad = 0.12
x_lo = (items[X] - items[RADIUS]).min() - pad
x_hi = (items[X] + items[RADIUS]).max() + pad
y_lo = (items[Y] - items[RADIUS]).min() - pad
y_hi = (items[Y] + items[RADIUS]).max() + pad
half_span = max(x_hi - x_lo, y_hi - y_lo) / 2
cx_mid = (x_lo + x_hi) / 2
cy_mid = (y_lo + y_hi) / 2

# Title with auto-scaled fontsize (67-char baseline)
title = "bubble-packed · python · plotnine · anyplot.ai"
title_fontsize = max(8, round(12 * 67 / len(title))) if len(title) > 67 else 12

plot = (
    ggplot()
    + geom_polygon(data=circles, mapping=aes(x=X, y=Y, fill=GROUP, group=CIRCLE), color=PAGE_BG, size=0.6)
    # Name labels per size tier
    + geom_text(
        data=large, mapping=aes(x=X, y=Y, label=LABEL, color=LABEL_COLOR), size=3.5, fontweight="bold", nudge_y=0.09
    )
    + geom_text(
        data=medium, mapping=aes(x=X, y=Y, label=LABEL, color=LABEL_COLOR), size=3.0, fontweight="bold", nudge_y=0.06
    )
    + geom_text(data=small, mapping=aes(x=X, y=Y, label=LABEL, color=LABEL_COLOR), size=2.5, fontweight="bold")
    # Value labels for large and medium bubbles
    + geom_text(data=large, mapping=aes(x=X, y=Y, label=VALUE_TEXT, color=LABEL_COLOR), size=3.0, nudge_y=-0.12)
    + geom_text(data=medium, mapping=aes(x=X, y=Y, label=VALUE_TEXT, color=LABEL_COLOR), size=2.5, nudge_y=-0.09)
    + scale_color_identity()
    + scale_fill_manual(values=group_colors, limits=groups, name=GROUP)
    + coord_fixed(xlim=(cx_mid - half_span, cx_mid + half_span), ylim=(cy_mid - half_span, cy_mid + half_span))
    + labs(title=title, subtitle=subtitle_text)
    + theme_void()
    + theme(
        figure_size=(6, 6),
        plot_title=element_text(size=title_fontsize, ha="center", weight="bold", color=INK, margin={"b": 4}),
        plot_subtitle=element_text(size=8, ha="center", color=INK_SOFT, margin={"t": 3, "b": 8}),
        legend_title=element_text(size=8, weight="bold", color=INK, margin={"b": 4}),
        legend_text=element_text(size=8, color=INK_SOFT),
        legend_position="right",
        legend_direction="vertical",
        legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT),
        legend_key=element_rect(fill=ELEVATED_BG, color="none"),
        legend_key_size=12,
        legend_box_margin=6,
        plot_background=element_rect(fill=PAGE_BG, color="none"),
        plot_margin=0.02,
    )
)

# Save
plot.save(f"plot-{THEME}.png", dpi=400, width=6, height=6, units="in", verbose=False)
