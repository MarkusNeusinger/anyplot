""" anyplot.ai
choropleth-basic: Choropleth Map with Regional Coloring
Library: seaborn 0.13.2 | Python 3.14.10
Quality: 75/100 | Updated: 2026-11-09
"""

import os

import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from matplotlib.colors import LinearSegmentedColormap


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Imprint palette: categorical positions (unused for this continuous map) and the sequential ramp
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]
imprint_seq = LinearSegmentedColormap.from_list("imprint_seq", ["#009E73", "#4467A3"])
TILE_INK = "#FFFDF6"  # labels on the filled tiles: the fills are identical in both themes

sns.set_theme(
    style="white",
    rc={
        "figure.facecolor": PAGE_BG,
        "axes.facecolor": PAGE_BG,
        "axes.edgecolor": INK_SOFT,
        "axes.labelcolor": INK,
        "text.color": INK,
        "xtick.color": INK_SOFT,
        "ytick.color": INK_SOFT,
        "legend.facecolor": ELEVATED_BG,
        "legend.edgecolor": INK_SOFT,
    },
)

# Columns: set these to your table's column names
STATE = "State"  # role: region_id
GRID_ROW = "Grid row"  # role: extra
GRID_COL = "Grid column"  # role: extra
GDP_GROWTH = "GDP growth rate (%)"  # role: value

# Data: US states as a tile grid map (row, column approximate the US layout);
# replace this block with your own table, for example df = pd.read_csv("states.csv")
states = [
    ("WA", 0, 1, 3.2),
    ("MT", 0, 3, 1.8),
    ("ND", 0, 5, 2.1),
    ("MN", 0, 6, 2.9),
    ("WI", 0, 7, 2.3),
    ("MI", 0, 8, 1.9),
    ("NY", 0, 10, 3.5),
    ("VT", 0, 11, 1.5),
    ("ME", 0, 12, 1.2),
    ("OR", 1, 1, 2.8),
    ("ID", 1, 2, 3.1),
    ("WY", 1, 3, 0.9),
    ("SD", 1, 5, 1.7),
    ("IA", 1, 6, 2.0),
    ("IL", 1, 7, 2.5),
    ("IN", 1, 8, 2.2),
    ("OH", 1, 9, 1.8),
    ("PA", 1, 10, 2.1),
    ("MA", 1, 11, 3.8),
    ("NH", 1, 12, 2.4),
    ("NV", 2, 1, 4.1),
    ("UT", 2, 2, 4.5),
    ("CO", 2, 3, 3.9),
    ("NE", 2, 5, 1.6),
    ("KS", 2, 6, 1.4),
    ("MO", 2, 7, 1.9),
    ("KY", 2, 8, 2.0),
    ("WV", 2, 9, 0.5),
    ("VA", 2, 10, 3.2),
    ("MD", 2, 11, 2.8),
    ("NJ", 2, 12, 2.6),
    ("CA", 3, 1, 3.7),
    ("AZ", 3, 2, 4.2),
    ("NM", 3, 3, 1.3),
    ("OK", 3, 5, 1.1),
    ("AR", 3, 6, 1.5),
    ("TN", 3, 7, 3.0),
    ("NC", 3, 9, 3.4),
    ("SC", 3, 10, 2.7),
    ("DE", 3, 11, 2.3),
    ("CT", 3, 12, 2.9),
    ("TX", 4, 3, 3.6),
    ("LA", 4, 5, 0.8),
    ("MS", 4, 6, 0.6),
    ("AL", 4, 7, 1.7),
    ("GA", 4, 8, 3.3),
    ("FL", 4, 10, 3.8),
    ("RI", 4, 12, 2.0),
    ("PR", 4, 13, np.nan),  # no data
    ("AK", 5, 0, 0.4),
    ("HI", 5, 2, 2.5),
    ("DC", 3, 13, np.nan),  # no data
]
df = pd.DataFrame(states, columns=[STATE, GRID_ROW, GRID_COL, GDP_GROWTH])

# Plot: reads only df and the constants above
rows = np.arange(int(df[GRID_ROW].max()) + 1)
cols = np.arange(int(df[GRID_COL].max()) + 1)
grid = df.pivot_table(index=GRID_ROW, columns=GRID_COL, values=GDP_GROWTH, aggfunc="mean", dropna=False).reindex(
    index=rows, columns=cols
)
values = pd.to_numeric(df[GDP_GROWTH], errors="coerce")
missing = df[values.isna()]
vmin = np.floor(values.min())
vmax = np.ceil(values.max())

fig, ax = plt.subplots(figsize=(8, 4.5), dpi=400)
sns.heatmap(
    grid,
    cmap=imprint_seq,
    vmin=vmin,
    vmax=vmax,
    linewidths=1.2,
    linecolor=PAGE_BG,
    square=True,
    cbar_kws={"label": GDP_GROWTH, "shrink": 0.62, "aspect": 18, "pad": 0.02},
    ax=ax,
)

# No-data regions: muted gray with hatching, never a color of the scale
for _, region in missing.iterrows():
    ax.add_patch(
        mpatches.Rectangle(
            (region[GRID_COL], region[GRID_ROW]),
            1,
            1,
            facecolor=INK_MUTED,
            edgecolor=PAGE_BG,
            linewidth=1.2,
            hatch="///",
            alpha=0.55,
            zorder=2,
        )
    )

# Region labels: state code and value on every tile
for _, region in df.iterrows():
    x, y = region[GRID_COL] + 0.5, region[GRID_ROW] + 0.5
    has_value = pd.notna(region[GDP_GROWTH])
    label_color = TILE_INK if has_value else INK
    ax.text(x, y - 0.13, region[STATE], ha="center", va="center", fontsize=8, fontweight="bold", color=label_color)
    ax.text(
        x,
        y + 0.2,
        f"{region[GDP_GROWTH]:.1f}%" if has_value else "n/a",
        ha="center",
        va="center",
        fontsize=6,
        color=label_color,
        fontstyle="normal" if has_value else "italic",
        zorder=3,
    )

# Colorbar
cbar = ax.collections[0].colorbar
cbar.ax.tick_params(labelsize=8, colors=INK_SOFT, length=0)
cbar.set_label(GDP_GROWTH, fontsize=10, color=INK, labelpad=6)
cbar.outline.set_visible(False)

# Style
title = "choropleth-basic · python · seaborn · anyplot.ai"
ax.set_title(title, fontsize=round(12 * min(1.0, 67 / len(title))), fontweight="medium", color=INK, pad=10)
ax.set_xticks([])
ax.set_yticks([])
ax.set_xlabel("")
ax.set_ylabel("")
sns.despine(ax=ax, left=True, bottom=True)

if not missing.empty:
    no_data = mpatches.Patch(facecolor=INK_MUTED, edgecolor=PAGE_BG, hatch="///", alpha=0.55, label="No data")
    ax.legend(handles=[no_data], loc="lower right", fontsize=8, frameon=True, labelcolor=INK)

ax.text(
    0.5,
    -0.04,
    f"{GDP_GROWTH} by {STATE.lower()} · tile grid map, one equal-size tile per region",
    ha="center",
    va="top",
    fontsize=8,
    color=INK_SOFT,
    transform=ax.transAxes,
)

fig.subplots_adjust(left=0.03, right=0.97, top=0.9, bottom=0.08)
plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
