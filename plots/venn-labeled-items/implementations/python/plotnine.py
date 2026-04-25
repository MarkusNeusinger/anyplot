""" anyplot.ai
venn-labeled-items: Chartgeist-Style Venn Diagram with Labeled Items
Library: plotnine 0.15.3 | Python 3.14.4
Quality: 85/100 | Created: 2026-04-25
"""

import os
import sys


# Avoid name collision so `from plotnine import ...` resolves to the package
_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path = [p for p in sys.path if os.path.abspath(p) != _HERE]

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from plotnine import (  # noqa: E402
    aes,
    coord_fixed,
    element_blank,
    element_rect,
    geom_polygon,
    geom_text,
    ggplot,
    scale_color_identity,
    scale_fill_identity,
    scale_x_continuous,
    scale_y_continuous,
    theme,
)


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Okabe-Ito categorical (positions 1, 2, 3)
COLOR_A = "#009E73"  # brand green — ALWAYS first series
COLOR_B = "#D55E00"  # vermillion
COLOR_C = "#0072B2"  # blue

# Symmetric three-circle Venn geometry
RADIUS = 1.5
circle_meta = [
    ("Overhyped", -0.85, 0.50, COLOR_A),
    ("Actually Useful", 0.85, 0.50, COLOR_B),
    ("Secretly Loved", 0.00, -1.00, COLOR_C),
]

# Polygon ring per circle (semi-transparent fills, colored outline)
theta = np.linspace(0, 2 * np.pi, 240)
circle_rows = []
for name, cx, cy, color in circle_meta:
    for t in theta:
        circle_rows.append({"name": name, "x": cx + RADIUS * np.cos(t), "y": cy + RADIUS * np.sin(t), "fill": color})
circles_df = pd.DataFrame(circle_rows)

# Items placed in their assigned zones
items_df = pd.DataFrame(
    [
        # A only — Overhyped
        ("NFTs", -2.05, 1.05),
        ("Metaverse", -2.10, 0.55),
        ("Smart Fridges", -2.00, 0.05),
        # B only — Actually Useful
        ("Google Maps", 2.05, 1.05),
        ("Spreadsheets", 2.10, 0.55),
        ("Calendar Apps", 2.00, 0.05),
        # C only — Secretly Loved
        ("Roller Skating", -0.70, -2.10),
        ("Soap Operas", 0.70, -2.10),
        # A ∩ B
        ("ChatGPT", 0.00, 1.20),
        ("Smartwatches", 0.00, 0.85),
        # A ∩ C
        ("Crocs", -1.10, -0.20),
        ("Vinyl Records", -1.05, -0.60),
        # B ∩ C
        ("Dolly Parton", 1.10, -0.20),
        ("Spotify", 1.05, -0.60),
        # A ∩ B ∩ C
        ("Sourdough", 0.00, 0.12),
        ("TikTok", 0.00, -0.32),
    ],
    columns=["label", "x", "y"],
)

# Category labels rendered outside each circle, on its outer side
cat_left_df = pd.DataFrame({"label": ["Overhyped"], "x": [-1.95], "y": [2.30], "color": [COLOR_A]})
cat_right_df = pd.DataFrame({"label": ["Actually Useful"], "x": [1.95], "y": [2.30], "color": [COLOR_B]})
cat_bottom_df = pd.DataFrame({"label": ["Secretly Loved"], "x": [0.00], "y": [-2.85], "color": [COLOR_C]})

# Editorial-style title text inside the canvas
title_df = pd.DataFrame({"label": ["Chartgeist 2026"], "x": [0.0], "y": [3.25], "color": [INK]})
subtitle_df = pd.DataFrame(
    {"label": ["venn-labeled-items · plotnine · anyplot.ai"], "x": [0.0], "y": [2.85], "color": [INK_MUTED]}
)

# Plot
plot = (
    ggplot()
    + geom_polygon(
        data=circles_df, mapping=aes(x="x", y="y", group="name", fill="fill", color="fill"), alpha=0.22, size=1.4
    )
    + geom_text(data=items_df, mapping=aes(x="x", y="y", label="label"), size=13, color=INK, family="serif")
    + geom_text(
        data=cat_left_df,
        mapping=aes(x="x", y="y", label="label", color="color"),
        size=22,
        fontweight="bold",
        family="serif",
        ha="center",
    )
    + geom_text(
        data=cat_right_df,
        mapping=aes(x="x", y="y", label="label", color="color"),
        size=22,
        fontweight="bold",
        family="serif",
        ha="center",
    )
    + geom_text(
        data=cat_bottom_df,
        mapping=aes(x="x", y="y", label="label", color="color"),
        size=22,
        fontweight="bold",
        family="serif",
        ha="center",
    )
    + geom_text(
        data=title_df,
        mapping=aes(x="x", y="y", label="label", color="color"),
        size=30,
        fontweight="bold",
        fontstyle="italic",
        family="serif",
    )
    + geom_text(data=subtitle_df, mapping=aes(x="x", y="y", label="label", color="color"), size=12, family="serif")
    + scale_fill_identity()
    + scale_color_identity()
    + scale_x_continuous(limits=(-3.5, 3.5), expand=(0, 0))
    + scale_y_continuous(limits=(-3.5, 3.5), expand=(0, 0))
    + coord_fixed(ratio=1)
    + theme(
        figure_size=(12, 12),
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        axis_title=element_blank(),
        axis_text=element_blank(),
        axis_ticks=element_blank(),
        axis_line=element_blank(),
        panel_grid_major=element_blank(),
        panel_grid_minor=element_blank(),
        legend_position="none",
    )
)

plot.save(f"plot-{THEME}.png", dpi=300, verbose=False)
