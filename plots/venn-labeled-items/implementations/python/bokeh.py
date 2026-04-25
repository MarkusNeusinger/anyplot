"""anyplot.ai
venn-labeled-items: Chartgeist-Style Venn Diagram with Labeled Items
Library: bokeh | Python 3.13
Quality: pending | Created: 2026-04-25
"""

import os

import numpy as np
from bokeh.io import export_png, output_file, save
from bokeh.models import Label
from bokeh.plotting import figure


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Okabe-Ito palette — first circle is brand green, then vermillion, then blue
COLOR_A = "#009E73"  # Overhyped
COLOR_B = "#D55E00"  # Actually Useful
COLOR_C = "#0072B2"  # Secretly Loved

# Geometry — equilateral triangle of centers (apex pointing down)
r = 1.0
s = 1.1
h_low = s * np.sqrt(3) / 6
center_a = (-s / 2, h_low)
center_b = (s / 2, h_low)
center_c = (0.0, -2 * h_low)

# Data — circle categories with editorial labels positioned outside each circle
circles = [
    {"name": "Overhyped", "color": COLOR_A, "center": center_a, "label_xy": (-1.65, 1.45), "align": "right"},
    {"name": "Actually Useful", "color": COLOR_B, "center": center_b, "label_xy": (1.65, 1.45), "align": "left"},
    {"name": "Secretly Loved", "color": COLOR_C, "center": center_c, "label_xy": (0.0, -1.92), "align": "center"},
]

# Items distributed across the seven interior zones
items = [
    # A only — Overhyped, neither useful nor loved
    {"label": "NFTs", "x": -1.42, "y": 0.88},
    {"label": "Metaverse", "x": -1.50, "y": 0.32},
    {"label": "Web3", "x": -1.30, "y": -0.05},
    # B only — Useful, neither overhyped nor loved
    {"label": "Google Maps", "x": 1.42, "y": 0.88},
    {"label": "Sticky Notes", "x": 1.40, "y": 0.30},
    # C only — Loved, neither overhyped nor useful
    {"label": "Karaoke", "x": -0.45, "y": -1.30},
    {"label": "Postcards", "x": 0.45, "y": -1.30},
    # AB — Overhyped + Useful
    {"label": "Smartphones", "x": 0.00, "y": 0.92},
    {"label": "Email", "x": 0.00, "y": 0.62},
    # AC — Overhyped + Loved
    {"label": "Crocs", "x": -0.78, "y": -0.18},
    {"label": "Pumpkin Spice", "x": -0.55, "y": -0.50},
    # BC — Useful + Loved
    {"label": "Spotify", "x": 0.78, "y": -0.18},
    {"label": "Dolly Parton", "x": 0.55, "y": -0.50},
    # ABC — all three
    {"label": "Sourdough", "x": 0.00, "y": 0.10},
    {"label": "TikTok", "x": 0.00, "y": -0.20},
]

# Plot — square canvas suits the radial Venn layout
p = figure(
    width=3600,
    height=3600,
    title="Tech Vibes 2026 · venn-labeled-items · bokeh · anyplot.ai",
    x_range=(-2.7, 2.7),
    y_range=(-2.7, 2.7),
    toolbar_location=None,
    tools="",
    match_aspect=True,
)

# Three semi-transparent circles
for circle in circles:
    cx, cy = circle["center"]
    p.ellipse(
        x=cx,
        y=cy,
        width=2 * r,
        height=2 * r,
        fill_color=circle["color"],
        fill_alpha=0.22,
        line_color=circle["color"],
        line_width=4,
        line_alpha=0.85,
    )

# Category names outside each circle, in the circle's own color
for circle in circles:
    lx, ly = circle["label_xy"]
    p.add_layout(
        Label(
            x=lx,
            y=ly,
            text=circle["name"],
            text_font="serif",
            text_font_size="64pt",
            text_font_style="italic",
            text_color=circle["color"],
            text_align=circle["align"],
            text_baseline="middle",
        )
    )

# Items as text-only placements inside their assigned zones
for item in items:
    p.add_layout(
        Label(
            x=item["x"],
            y=item["y"],
            text=item["label"],
            text_font="serif",
            text_font_size="38pt",
            text_color=INK,
            text_align="center",
            text_baseline="middle",
        )
    )

# Editorial subtitle anchored under the diagram
p.add_layout(
    Label(
        x=0.0,
        y=-2.35,
        text="A field guide to fifteen things, three feelings, and seven overlapping truths",
        text_font="serif",
        text_font_size="30pt",
        text_font_style="italic",
        text_color=INK_SOFT,
        text_align="center",
        text_baseline="middle",
    )
)

# Style — gridless editorial chrome
p.background_fill_color = PAGE_BG
p.border_fill_color = PAGE_BG
p.outline_line_color = None

p.title.text_font = "serif"
p.title.text_font_size = "54pt"
p.title.text_font_style = "normal"
p.title.text_color = INK
p.title.align = "center"

p.axis.visible = False
p.grid.visible = False

# Save
export_png(p, filename=f"plot-{THEME}.png")
output_file(f"plot-{THEME}.html")
save(p)
