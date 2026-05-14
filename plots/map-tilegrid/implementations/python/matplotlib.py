""" anyplot.ai
map-tilegrid: Tile Grid Map for Equal-Area Geographic Comparison
Library: matplotlib 3.10.9 | Python 3.13.13
Quality: 86/100 | Created: 2026-05-14
"""

import os

import matplotlib
import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
from matplotlib.cm import ScalarMappable
from matplotlib.colors import Normalize


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# US states tile grid layout: (abbreviation, row, col, renewable_energy_pct)
states = [
    ("ME", 0, 10, 72),
    ("MT", 1, 3, 65),
    ("ND", 1, 4, 54),
    ("MN", 1, 5, 48),
    ("WI", 1, 6, 22),
    ("MI", 1, 7, 18),
    ("VT", 1, 9, 88),
    ("NH", 1, 10, 32),
    ("WA", 2, 0, 84),
    ("ID", 2, 1, 78),
    ("WY", 2, 2, 15),
    ("SD", 2, 3, 81),
    ("IA", 2, 4, 62),
    ("IL", 2, 5, 24),
    ("IN", 2, 6, 11),
    ("OH", 2, 7, 10),
    ("PA", 2, 8, 16),
    ("NY", 2, 9, 38),
    ("MA", 2, 10, 19),
    ("OR", 3, 0, 72),
    ("NV", 3, 1, 42),
    ("CO", 3, 2, 35),
    ("NE", 3, 3, 43),
    ("MO", 3, 4, 17),
    ("KY", 3, 5, 9),
    ("WV", 3, 6, 6),
    ("VA", 3, 7, 21),
    ("NJ", 3, 8, 11),
    ("CT", 3, 9, 14),
    ("RI", 3, 10, 22),
    ("CA", 4, 0, 58),
    ("UT", 4, 1, 24),
    ("AZ", 4, 2, 38),
    ("KS", 4, 3, 55),
    ("AR", 4, 4, 18),
    ("TN", 4, 5, 16),
    ("NC", 4, 6, 24),
    ("SC", 4, 7, 18),
    ("MD", 4, 8, 12),
    ("DE", 4, 9, 10),
    ("NM", 5, 2, 45),
    ("OK", 5, 3, 52),
    ("LA", 5, 4, 11),
    ("MS", 5, 5, 8),
    ("AL", 5, 6, 13),
    ("GA", 5, 7, 17),
    ("TX", 6, 3, 28),
    ("FL", 6, 7, 20),
    ("DC", 6, 8, 5),
    ("AK", 7, 0, 30),
    ("HI", 7, 1, 36),
]

# Color mapping — sequential viridis for unipolar renewable energy data
values = [v for _, _, _, v in states]
vmin, vmax = min(values), max(values)
norm = Normalize(vmin=vmin, vmax=vmax)
cmap = matplotlib.colormaps["viridis"]

# Plot
fig, ax = plt.subplots(figsize=(16, 9), facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

TILE = 0.82
PAD = (1.0 - TILE) / 2.0

for abbr, row, col, value in states:
    tile_color = cmap(norm(value))
    rect = mpatches.Rectangle(
        (col + PAD, -(row + 1) + PAD), TILE, TILE, facecolor=tile_color, edgecolor=PAGE_BG, linewidth=2.0, zorder=2
    )
    ax.add_patch(rect)

    r_c, g_c, b_c = tile_color[:3]
    lum = 0.2126 * r_c + 0.7152 * g_c + 0.0722 * b_c
    label_color = "#1A1A17" if lum > 0.45 else "#F0EFE8"

    ax.text(
        col + 0.5,
        -(row + 0.5),
        abbr,
        ha="center",
        va="center",
        fontsize=13,
        fontweight="bold",
        color=label_color,
        zorder=3,
    )

# Axes bounds — grid spans cols 0–10 (12 units) × rows 0–7 (8.5 units)
ax.set_xlim(-0.5, 11.5)
ax.set_ylim(-8.5, 0.5)
ax.set_aspect("equal", adjustable="box")
ax.axis("off")

# Colorbar
sm = ScalarMappable(cmap=cmap, norm=norm)
sm.set_array([])
cbar = plt.colorbar(sm, ax=ax, fraction=0.025, pad=0.04, shrink=0.75, aspect=25)
cbar.set_label("Renewable Energy Share (%)", fontsize=16, color=INK_SOFT, labelpad=10)
cbar.ax.tick_params(labelsize=13, labelcolor=INK_SOFT, colors=INK_SOFT)
cbar.outline.set_edgecolor(INK_SOFT)

# Title
ax.set_title(
    "US Renewable Energy Share · map-tilegrid · matplotlib · anyplot.ai",
    fontsize=22,
    fontweight="medium",
    color=INK,
    pad=15,
)

plt.tight_layout()
plt.savefig(f"plot-{THEME}.png", dpi=300, bbox_inches="tight", facecolor=PAGE_BG)
