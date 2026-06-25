"""anyplot.ai
venn-labeled-items: Chartgeist-Style Venn Diagram with Labeled Items
Library: letsplot | Python
"""

import os

import numpy as np
import pandas as pd
from lets_plot import (
    LetsPlot,
    aes,
    coord_fixed,
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
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Imprint palette positions 1, 2, 3
COLOR_A = "#009E73"
COLOR_B = "#C475FD"
COLOR_C = "#4467A3"

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
    ("Roller Skating", -1.10, -2.10),
    ("Soap Operas", 1.10, -2.10),
    # A ∩ B
    ("ChatGPT", 0.00, 1.20),
    ("Smartwatches", 0.00, 0.85),
    # A ∩ C
    ("Crocs", -1.05, -0.20),
    ("Vinyl Records", -1.00, -0.60),
    # B ∩ C
    ("Dolly Parton", 1.05, -0.20),
    ("Spotify", 1.00, -0.60),
    # A ∩ B ∩ C — spread vertically to reduce crowding
    ("Sourdough", 0.00, 0.30),
    ("TikTok", 0.00, -0.35),
    # outside
    ("Beige Walls", -3.10, -2.50),
]
items_df = pd.DataFrame(items, columns=["label", "x", "y"])

# Plot — equal xlim/ylim so coord_fixed fills the square canvas without black bars
plot = ggplot() + coord_fixed(xlim=[-4.0, 4.0], ylim=[-4.0, 4.0])

# Three overlapping circles with semi-transparent fills
for c in circle_meta:
    cx, cy = centers[c["key"]]
    circle_df = pd.DataFrame({"x": cx + RADIUS * np.cos(theta), "y": cy + RADIUS * np.sin(theta)})
    plot = plot + geom_polygon(
        aes(x="x", y="y"), data=circle_df, fill=c["color"], color=c["color"], alpha=0.22, size=1.4
    )

# Item labels (serif, INK) — size=9 for legibility on 2400×2400 canvas
plot = plot + geom_text(aes(x="x", y="y", label="label"), data=items_df, size=9, family="serif", color=INK)

# Category names outside each circle, centered on their quadrant — hjust=0.5 avoids edge clipping
plot = plot + geom_text(
    x=-2.10, y=2.15, label="Overhyped", size=11, family="serif", fontface="bold", color=COLOR_A, hjust=0.5
)
plot = plot + geom_text(
    x=2.10, y=2.15, label="Actually Useful", size=11, family="serif", fontface="bold", color=COLOR_B, hjust=0.5
)
plot = plot + geom_text(
    x=0.00, y=-3.10, label="Secretly Loved", size=11, family="serif", fontface="bold", color=COLOR_C, hjust=0.5
)

# Hint label for the "outside" item cluster
plot = plot + geom_text(
    x=-3.10,
    y=-2.20,
    label="(neither here nor there)",
    size=7,
    family="serif",
    fontface="italic",
    color=INK_MUTED,
    hjust=0.5,
)

# Editorial kicker + canonical anyplot.ai title line
plot = plot + geom_text(
    x=0, y=3.50, label="Chartgeist 2026", size=16, family="serif", fontface="bold_italic", color=INK, hjust=0.5
)
plot = plot + geom_text(
    x=0, y=3.00, label="venn-labeled-items · letsplot · anyplot.ai", size=6, family="serif", color=INK_MUTED, hjust=0.5
)

# Theme — gridless editorial background
plot = (
    plot
    + theme_void()
    + theme(
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        legend_position="none",
    )
)

# Canvas: 2400×2400 px (square — canonical for symmetric Venn layout)
plot = plot + ggsize(600, 600)

# Save PNG and interactive HTML
ggsave(plot, f"plot-{THEME}.png", path=".", scale=4)
ggsave(plot, f"plot-{THEME}.html", path=".")
