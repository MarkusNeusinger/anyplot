"""anyplot.ai
radar-multi: Multi-Series Radar Chart
Library: seaborn 0.13.2 | Python 3.14.10
Quality: 83/100 | Updated: 2026-11-09
"""

import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: all eight positions, first series always #009E73
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
        "grid.alpha": 0.15,
        "legend.facecolor": ELEVATED_BG,
        "legend.edgecolor": INK_SOFT,
    },
)

# Constants
SCALE_MAX = 100  # the value scale runs 0 to 100
GRID_STEP = 20  # gridline rings every 20 points

# Columns: set these to your table's column names
DIMENSION = "Dimension"  # role: category
SCORE = "Score (0-100)"  # role: value
PRODUCT = "Product"  # role: series

# Data: replace this block with your own table, for example df = pd.read_csv("scores.csv")
dimensions = ["Performance", "Reliability", "Usability", "Features", "Support", "Value"]
products = {
    "Nimbus Pro 14": [92, 88, 72, 78, 65, 90],
    "Vela Air 13": [65, 70, 95, 88, 85, 60],
    "Orion Flex 15": [75, 58, 82, 65, 92, 72],
}
df = pd.DataFrame(
    {
        DIMENSION: dimensions * len(products),
        PRODUCT: [name for name in products for _ in dimensions],
        SCORE: [score for scores in products.values() for score in scores],
    }
)

# Plot: reads only df and the constants above
axes_order = list(df[DIMENSION].unique())
series_order = list(df[PRODUCT].unique())
angle_of = dict(zip(axes_order, np.linspace(0, 2 * np.pi, len(axes_order), endpoint=False), strict=True))
colors = dict(zip(series_order, IMPRINT_PALETTE, strict=False))

# Spokes as angles; each polygon closes by repeating its first vertex at 2π
radar = df.assign(angle=df[DIMENSION].map(angle_of)).dropna(subset=[SCORE])
first = radar.groupby(PRODUCT, sort=False).head(1).assign(angle=2 * np.pi)
closed = pd.concat([radar, first]).sort_values([PRODUCT, "angle"], kind="stable")

fig, ax = plt.subplots(figsize=(6, 6), dpi=400, subplot_kw={"projection": "polar"})
ax.set_theta_offset(np.pi / 2)
ax.set_theta_direction(-1)

for product, polygon in closed.groupby(PRODUCT, sort=False):
    ax.fill(polygon["angle"], polygon[SCORE], color=colors[product], alpha=0.22, zorder=2)

sns.lineplot(
    data=closed,
    x="angle",
    y=SCORE,
    hue=PRODUCT,
    hue_order=series_order,
    palette=colors,
    sort=False,
    estimator=None,
    units=PRODUCT,
    marker="o",
    markersize=6,
    markeredgecolor=PAGE_BG,
    markeredgewidth=0.8,
    linewidth=2,
    ax=ax,
    zorder=3,
)

# Style
ax.set_xticks(list(angle_of.values()), axes_order)
ax.tick_params(axis="x", labelsize=10, colors=INK, pad=10)
ax.set_ylim(0, SCALE_MAX)
rings = np.arange(GRID_STEP, SCALE_MAX + GRID_STEP, GRID_STEP)
ax.set_yticks(rings, [str(r) for r in rings])
ax.tick_params(axis="y", labelsize=8, colors=INK_SOFT)
rlabel_deg = 180 / len(axes_order)
ax.set_rlabel_position(rlabel_deg)
ax.set_xlabel("")
ax.set_ylabel("")
# Name the value scale once, just outside the outer ring above the ring labels
ax.text(
    np.deg2rad(rlabel_deg),
    SCALE_MAX * 1.1,
    SCORE,
    fontsize=8,
    color=INK_SOFT,
    ha="left",
    va="center",
    rotation=90 - rlabel_deg,
    rotation_mode="anchor",
)
ax.yaxis.grid(True, linestyle="--", linewidth=0.7, color=INK, alpha=0.18)
ax.xaxis.grid(True, linestyle="-", linewidth=0.7, color=INK, alpha=0.12)
ax.spines["polar"].set_color(INK_SOFT)
ax.spines["polar"].set_linewidth(0.8)

ax.set_title("radar-multi · python · seaborn · anyplot.ai", fontsize=12, color=INK, pad=24)
sns.move_legend(
    ax,
    "lower right",
    bbox_to_anchor=(1.12, -0.06),
    title=PRODUCT,
    fontsize=8,
    title_fontsize=9,
    frameon=True,
    framealpha=0.95,
)

fig.subplots_adjust(left=0.12, right=0.88, top=0.86, bottom=0.08)
plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
