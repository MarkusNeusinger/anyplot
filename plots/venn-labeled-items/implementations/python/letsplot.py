"""anyplot.ai
venn-labeled-items: Chartgeist-Style Venn Diagram with Labeled Items
Library: lets-plot 4.9.0 | Python 3.14
Quality: pending | Created: 2026-04-25
"""

import os

import numpy as np
import pandas as pd
from lets_plot import (
    LetsPlot,
    aes,
    coord_fixed,
    element_blank,
    element_rect,
    geom_polygon,
    geom_text,
    ggplot,
    ggsave,
    ggsize,
    theme,
    theme_void,
)


LetsPlot.setup_html()

# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Okabe-Ito categorical (positions 1, 2, 3)
COLOR_A = "#009E73"
COLOR_B = "#D55E00"
COLOR_C = "#0072B2"

# Geometry — three equally sized overlapping circles
RADIUS = 1.5
centers = {"A": (-0.85, 0.50), "B": (0.85, 0.50), "C": (0.00, -1.00)}
circle_meta = [
    {"key": "A", "name": "Overhyped", "color": COLOR_A},
    {"key": "B", "name": "Actually Useful", "color": COLOR_B},
    {"key": "C", "name": "Secretly Loved", "color": COLOR_C},
]

theta = np.linspace(0, 2 * np.pi, 240)

# Items distributed across the seven interior zones (+ outside)
items = [
    # A — Overhyped
    ("NFTs", -2.00, 1.05),
    ("Metaverse", -2.05, 0.55),
    ("Smart Fridges", -1.95, 0.05),
    # B — Actually Useful
    ("Google Maps", 2.00, 1.05),
    ("Spreadsheets", 2.05, 0.55),
    ("Calendar Apps", 1.95, 0.05),
    # C — Secretly Loved
    ("Roller Skating", -0.75, -2.05),
    ("Soap Operas", 0.75, -2.05),
    # A ∩ B
    ("ChatGPT", 0.00, 1.20),
    ("Smartwatches", 0.00, 0.85),
    # A ∩ C
    ("Crocs", -1.05, -0.20),
    ("Vinyl Records", -1.00, -0.60),
    # B ∩ C
    ("Dolly Parton", 1.05, -0.20),
    ("Spotify", 1.00, -0.60),
    # A ∩ B ∩ C
    ("Sourdough", 0.00, 0.15),
    ("TikTok", 0.00, -0.30),
    # outside
    ("Beige Walls", -3.10, -2.50),
]
items_df = pd.DataFrame(items, columns=["label", "x", "y"])

# Plot
plot = ggplot() + coord_fixed(xlim=[-4.0, 4.0], ylim=[-3.5, 3.5])

# Three overlapping circles with semi-transparent fills
for c in circle_meta:
    cx, cy = centers[c["key"]]
    circle_df = pd.DataFrame({"x": cx + RADIUS * np.cos(theta), "y": cy + RADIUS * np.sin(theta)})
    plot = plot + geom_polygon(
        aes(x="x", y="y"), data=circle_df, fill=c["color"], color=c["color"], alpha=0.22, size=1.4
    )

# Item labels (serif, INK)
plot = plot + geom_text(aes(x="x", y="y", label="label"), data=items_df, size=8, family="serif", color=INK)

# Category names outside each circle, in the circle's color
plot = plot + geom_text(
    x=-2.40, y=1.95, label="Overhyped", size=13, family="serif", fontface="bold", color=COLOR_A, hjust=1.0
)
plot = plot + geom_text(
    x=2.40, y=1.95, label="Actually Useful", size=13, family="serif", fontface="bold", color=COLOR_B, hjust=0.0
)
plot = plot + geom_text(
    x=0.00, y=-2.85, label="Secretly Loved", size=13, family="serif", fontface="bold", color=COLOR_C, hjust=0.5
)

# Hint label for the "outside" item cluster
plot = plot + geom_text(
    x=-3.10,
    y=-2.20,
    label="(neither here nor there)",
    size=6,
    family="serif",
    fontface="italic",
    color=INK_MUTED,
    hjust=0.5,
)

# Editorial kicker + canonical anyplot.ai title line
plot = plot + geom_text(
    x=0, y=3.20, label="Chartgeist 2026", size=18, family="serif", fontface="bold_italic", color=INK, hjust=0.5
)
plot = plot + geom_text(
    x=0, y=2.70, label="venn-labeled-items · letsplot · anyplot.ai", size=7, family="serif", color=INK_MUTED, hjust=0.5
)

# Theme — gridless editorial background
plot = (
    plot
    + theme_void()
    + theme(
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        legend_position="none",
        axis_text=element_blank(),
        axis_title=element_blank(),
        axis_ticks=element_blank(),
    )
)

plot = plot + ggsize(1200, 1200)

# Save
ggsave(plot, f"plot-{THEME}.png", path=".", scale=3)
ggsave(plot, f"plot-{THEME}.html", path=".")
