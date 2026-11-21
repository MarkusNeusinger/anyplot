"""anyplot.ai
map-tilegrid: Tile Grid Map for Equal-Area Geographic Comparison
Library: seaborn 0.13.2 | Python 3.13.13
Quality: 86/100 | Updated: 2026-11-21
"""

import os

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
from matplotlib.colors import LinearSegmentedColormap, Normalize


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: all eight positions in canonical order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

sns.set_theme(
    style="ticks",
    rc={
        "figure.facecolor": PAGE_BG,
        "axes.facecolor": PAGE_BG,
        "axes.edgecolor": INK_SOFT,
        "axes.labelcolor": INK,
        "text.color": INK,
        "xtick.color": INK_SOFT,
        "ytick.color": INK_SOFT,
        "grid.color": INK,
        "grid.alpha": 0.10,
        "legend.facecolor": ELEVATED_BG,
        "legend.edgecolor": INK_SOFT,
    },
)

# Columns: set these to your table's column names
REGION = "State"  # role: region
GRAD_RATE = "Graduation rate (%)"  # role: value
ROW = "Grid row"  # role: row
COL = "Grid column"  # role: col

# Data: replace this block with your own table, for example df = pd.read_csv("graduation.csv")
# Four-year high-school graduation rate by US state (illustrative values) on a tile grid, row 0 = top
tiles = [
    ("ME", 0, 9, 87),
    ("VT", 1, 9, 87),
    ("NH", 1, 10, 90),
    ("WA", 2, 0, 84),
    ("ID", 2, 1, 80),
    ("MT", 2, 2, 87),
    ("ND", 2, 3, 90),
    ("MN", 2, 4, 83),
    ("WI", 2, 5, 90),
    ("MI", 2, 7, 81),
    ("NY", 2, 8, 87),
    ("MA", 2, 9, 90),
    ("RI", 2, 10, 84),
    ("OR", 3, 0, 82),
    ("WY", 3, 1, 82),
    ("SD", 3, 2, 84),
    ("IA", 3, 3, 91),
    ("IL", 3, 4, 87),
    ("IN", 3, 5, 88),
    ("OH", 3, 6, 86),
    ("PA", 3, 7, 87),
    ("NJ", 3, 8, 91),
    ("CT", 3, 9, 89),
    ("NV", 4, 0, 81),
    ("UT", 4, 1, 88),
    ("CO", 4, 2, 82),
    ("NE", 4, 3, 89),
    ("MO", 4, 4, 90),
    ("KY", 4, 5, 91),
    ("WV", 4, 6, 91),
    ("VA", 4, 7, 92),
    ("MD", 4, 8, 87),
    ("DE", 4, 9, 88),
    ("CA", 5, 0, 87),
    ("AZ", 5, 1, 77),
    ("NM", 5, 2, 77),
    ("KS", 5, 3, 88),
    ("TN", 5, 4, 90),
    ("NC", 5, 5, 87),
    ("SC", 5, 7, 83),
    ("OK", 6, 2, 82),
    ("AR", 6, 3, 88),
    ("MS", 6, 4, 88),
    ("AL", 6, 5, 91),
    ("GA", 6, 6, 84),
    ("TX", 7, 2, 90),
    ("LA", 7, 4, 83),
    ("FL", 7, 7, 90),
    ("AK", 8, 0, 80),
    ("HI", 8, 1, 85),
]
df = pd.DataFrame(tiles, columns=[REGION, ROW, COL, GRAD_RATE])

# Plot: reads only df and the constants above
n_rows, n_cols = df[ROW].max() + 1, df[COL].max() + 1
grid = df.pivot(index=ROW, columns=COL, values=GRAD_RATE).reindex(index=range(n_rows), columns=range(n_cols))
labels = df.pivot(index=ROW, columns=COL, values=REGION).reindex(index=range(n_rows), columns=range(n_cols))

# Diverging Imprint colormap centred on the mean rate, symmetric around it so the midpoint stays neutral
midpoint = "#FAF8F1" if THEME == "light" else "#1A1A17"
imprint_div = LinearSegmentedColormap.from_list("imprint_div", ["#AE3030", midpoint, "#4467A3"])
centre = df[GRAD_RATE].mean()
half_range = (df[GRAD_RATE] - centre).abs().max()
norm = Normalize(vmin=centre - half_range, vmax=centre + half_range)

fig, ax = plt.subplots(figsize=(6, 6), dpi=400, facecolor=PAGE_BG)
sns.heatmap(
    grid,
    ax=ax,
    mask=grid.isna(),
    cmap=imprint_div,
    norm=norm,
    annot=labels.fillna(""),
    fmt="",
    annot_kws={"fontsize": 8.5, "fontweight": "bold"},
    linewidths=2.2,
    linecolor=PAGE_BG,
    square=True,
    cbar_kws={"orientation": "horizontal", "shrink": 0.7, "pad": 0.03, "aspect": 35},
)
ax.axis("off")

cbar = ax.collections[0].colorbar
cbar.set_label(f"{GRAD_RATE} · midpoint = mean of states ({centre:.1f}%)", fontsize=9.5, color=INK, labelpad=6)
cbar.ax.tick_params(labelsize=8.5, colors=INK_SOFT, length=3)
cbar.outline.set_edgecolor(INK_SOFT)

ax.set_title("map-tilegrid · python · seaborn · anyplot.ai", fontsize=12, fontweight="medium", color=INK, pad=10)
plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
