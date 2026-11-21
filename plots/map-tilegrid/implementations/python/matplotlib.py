"""anyplot.ai
map-tilegrid: Tile Grid Map for Equal-Area Geographic Comparison
Library: matplotlib 3.10.9 | Python 3.13.13
Quality: 86/100 | Updated: 2026-11-21
"""

import os

import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.cm import ScalarMappable
from matplotlib.colors import LinearSegmentedColormap, Normalize


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: all eight positions in canonical order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Constants
TILE = 0.82  # tile edge as a share of its grid cell, the rest is the gap between tiles
LIGHT_LABEL, DARK_LABEL = "#F0EFE8", "#1A1A17"  # tile label colors, switched by tile darkness

# Columns: set these to your table's column names
REGION = "State"  # role: region
SHARE = "Renewable energy share (%)"  # role: value
ROW = "Grid row"  # role: row
COL = "Grid column"  # role: col

# Data: replace this block with your own table, for example df = pd.read_csv("regions.csv")
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
df = pd.DataFrame(states, columns=[REGION, ROW, COL, SHARE])

# Plot: reads only df and the constants above
imprint_seq = LinearSegmentedColormap.from_list("imprint_seq", [IMPRINT_PALETTE[0], IMPRINT_PALETTE[2]])
norm = Normalize(vmin=df[SHARE].min(), vmax=df[SHARE].max())
pad = (1.0 - TILE) / 2.0

fig, ax = plt.subplots(figsize=(8, 4.5), dpi=400, facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

for region, row, col, value in df[[REGION, ROW, COL, SHARE]].itertuples(index=False):
    tile_color = imprint_seq(norm(value))
    ax.add_patch(
        mpatches.Rectangle(
            (col + pad, -(row + 1) + pad), TILE, TILE, facecolor=tile_color, edgecolor=PAGE_BG, linewidth=0.8, zorder=2
        )
    )
    red, green, blue = tile_color[:3]
    luminance = 0.2126 * red + 0.7152 * green + 0.0722 * blue
    ax.text(
        col + 0.5,
        -(row + 0.5),
        region,
        ha="center",
        va="center",
        fontsize=7.5,
        fontweight="bold",
        color=DARK_LABEL if luminance > 0.45 else LIGHT_LABEL,
        zorder=3,
    )

ax.set_xlim(-0.2, df[COL].max() + 1.2)
ax.set_ylim(-(df[ROW].max() + 1) - 0.2, 0.2)
ax.set_aspect("equal", adjustable="box")
ax.axis("off")

cbar = fig.colorbar(ScalarMappable(cmap=imprint_seq, norm=norm), ax=ax, fraction=0.03, pad=0.02, shrink=0.8)
cbar.set_label(SHARE, fontsize=10, color=INK, labelpad=8)
cbar.ax.tick_params(labelsize=8, labelcolor=INK_SOFT, colors=INK_SOFT)
cbar.outline.set_edgecolor(INK_SOFT)

title = "US Renewable Energy Share · map-tilegrid · python · matplotlib · anyplot.ai"
ax.set_title(
    title,
    fontsize=max(8, round(12 * 67 / len(title))) if len(title) > 67 else 12,
    fontweight="medium",
    color=INK,
    pad=8,
)
plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
