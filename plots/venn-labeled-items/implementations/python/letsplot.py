"""anyplot.ai
venn-labeled-items: Chartgeist-Style Venn Diagram with Labeled Items
Library: letsplot 4.11.0 | Python 3.14.10
Quality: 83/100 | Updated: 2026-11-26
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

# Imprint palette: all eight positions, one per circle in order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Constants: the standard symmetric three-circle layout
RADIUS = 1.5
CENTERS = [(-0.85, 0.50), (0.85, 0.50), (0.00, -1.00)]  # circles A, B, C
NAME_OFFSETS = [(-1.3, 1.45), (1.3, 1.45), (0.00, -1.85)]  # category name, from each circle's center
NAME_HJUST = [1.0, 0.0, 0.5]  # aligned away from the diagram's center
OUTSIDE = "outside"
MARGIN_X = 1.55  # empty space left and right of the circles
HEADROOM = 1.3  # height above the circles for the kicker and title line
NAME_ZONE = "name "  # zone prefix of a row that holds a circle's category name

# Columns: set these to your table's column names
LABEL = "label"  # role: label
ZONE = "zone"  # role: zone
X = "x"  # role: extra
Y = "y"  # role: extra

# Data: replace this block with your own table, for example df = pd.read_csv("items.csv")
# Zone codes: A, B, C, AB, AC, BC, ABC or outside; x and y are the label's place inside its zone
df = pd.DataFrame(
    [
        ("Overhyped", NAME_ZONE + "A", np.nan, np.nan),
        ("Actually Useful", NAME_ZONE + "B", np.nan, np.nan),
        ("Secretly Loved", NAME_ZONE + "C", np.nan, np.nan),
        ("NFTs", "A", -1.60, 1.15),
        ("Metaverse", "A", -1.60, 0.65),
        ("Smart Fridges", "A", -1.60, 0.25),
        ("Google Maps", "B", 1.60, 1.15),
        ("Spreadsheets", "B", 1.60, 0.65),
        ("Calendar Apps", "B", 1.60, 0.25),
        ("Roller Skating", "C", 0.00, -1.65),
        ("Soap Operas", "C", 0.00, -2.10),
        ("ChatGPT", "AB", 0.00, 1.20),
        ("Smartwatches", "AB", 0.00, 0.85),
        ("Crocs", "AC", -0.95, -0.25),
        ("Vinyl Records", "AC", -0.80, -0.65),
        ("Podcasts", "BC", 0.90, -0.25),
        ("Spotify", "BC", 0.95, -0.65),
        ("Sourdough", "ABC", 0.00, 0.15),
        ("TikTok", "ABC", 0.00, -0.30),
        ("Beige Walls", OUTSIDE, -3.10, -2.50),
    ],
    columns=[LABEL, ZONE, X, Y],
)

# Plot: reads only df and the constants above
theta = np.linspace(0, 2 * np.pi, 240)
centers = np.array(CENTERS)
half = centers[:, 0].max() + RADIUS + MARGIN_X
content_top = centers[:, 1].max() + RADIUS + HEADROOM
content_bottom = min(cy + dy for (_, cy), (_, dy) in zip(CENTERS, NAME_OFFSETS, strict=True)) - 0.2
mid_y = (content_top + content_bottom) / 2  # centre the whole block, titles included
xlim = [-half, half]
ylim = [mid_y - half, mid_y + half]  # square panel: fills the square canvas

is_name = df[ZONE].str.startswith(NAME_ZONE)
names = df[is_name].drop_duplicates(ZONE)
items = df[~is_name]

plot = ggplot() + coord_fixed(xlim=xlim, ylim=ylim)

# Three overlapping circles with semi-transparent fills
for i, (cx, cy) in enumerate(CENTERS):
    circle_df = pd.DataFrame({X: cx + RADIUS * np.cos(theta), Y: cy + RADIUS * np.sin(theta)})
    plot += geom_polygon(
        aes(x=X, y=Y), data=circle_df, fill=IMPRINT_PALETTE[i], color=IMPRINT_PALETTE[i], alpha=0.22, size=0.7
    )

# Item labels (serif, INK)
plot += geom_text(aes(x=X, y=Y, label=LABEL), data=items, size=5.5, family="serif", color=INK)

# Category names outside each circle, in the circle's color
for i, name in enumerate(names[LABEL].head(len(CENTERS))):
    dx, dy = NAME_OFFSETS[i]
    plot += geom_text(
        x=CENTERS[i][0] + dx,
        y=CENTERS[i][1] + dy,
        label=name,
        size=7,
        family="serif",
        fontface="bold",
        color=IMPRINT_PALETTE[i],
        hjust=NAME_HJUST[i],
    )

# Hint above the outside items
outside = items[items[ZONE] == OUTSIDE]
if len(outside):
    plot += geom_text(
        x=outside[X].mean(),
        y=outside[Y].max() + 0.30,
        label="(neither here nor there)",
        size=3.5,
        family="serif",
        fontface="italic",
        color=INK_MUTED,
        hjust=0.5,
    )

# Editorial kicker + canonical anyplot.ai title line
mid = sum(xlim) / 2
plot += geom_text(
    x=mid, y=content_top - 0.30, label="Chartgeist 2026", size=9, family="serif", fontface="bold_italic", color=INK
)
plot += geom_text(
    x=mid,
    y=content_top - 0.80,
    label="venn-labeled-items · python · letsplot · anyplot.ai",
    size=5,
    family="serif",
    color=INK_MUTED,
)

# Style: gridless editorial background
plot += theme_void() + theme(
    plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
    panel_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
    legend_position="none",
)
plot += ggsize(600, 600)

# Save
ggsave(plot, f"plot-{THEME}.png", path=".", scale=4)
ggsave(plot, f"plot-{THEME}.html", path=".")
