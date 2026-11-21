""" anyplot.ai
bar-3d-categorical: 3D Bar Chart for Categorical Comparison
Library: seaborn 0.13.2 | Python 3.14.10
Quality: 75/100 | Updated: 2026-11-21
"""

import os

import matplotlib.patches as mpatches
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
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

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

# Column constants
PRODUCT = "Product Category"  # role: x_category
REGION = "Region"  # role: y_category
UNITS = "Units Sold (thousands)"  # role: value

# Data: quarterly unit sales (thousands) by product category and region
np.random.seed(42)
_products = ["Laptops", "Tablets", "Phones", "Monitors"]
_regions = ["North", "South", "East", "West"]
_base = np.array(
    [[45.2, 31.8, 38.5, 27.9], [22.1, 18.4, 25.3, 20.1], [68.7, 55.2, 72.1, 60.8], [15.3, 11.9, 18.2, 13.7]]
)
_sales = _base + np.random.normal(0, 1.2, _base.shape)
df = pd.DataFrame(
    {PRODUCT: np.repeat(_products, len(_regions)), REGION: np.tile(_regions, len(_products)), UNITS: _sales.ravel()}
)

# Plot
products = list(dict.fromkeys(df[PRODUCT]))
regions = list(dict.fromkeys(df[REGION]))
colors = {p: IMPRINT_PALETTE[i % len(IMPRINT_PALETTE)] for i, p in enumerate(products)}
top = df[UNITS].max()

fig = plt.figure(figsize=(8, 4.5), dpi=400, facecolor=PAGE_BG)
ax = fig.add_subplot(111, projection="3d")

bar_w = 0.55
for row in df.itertuples(index=False):
    x = products.index(row[0])
    y = regions.index(row[1])
    h = row[2]
    ax.bar3d(x - bar_w / 2, y - bar_w / 2, 0, bar_w, bar_w, h, color=colors[row[0]], alpha=0.85, shade=True)
    ax.text(x, y, h + top * 0.02, f"{h:.0f}", ha="center", va="bottom", fontsize=7, color=INK, fontweight="medium")

ax.set_xticks(range(len(products)))
ax.set_xticklabels(products, fontsize=8)
ax.set_yticks(range(len(regions)))
ax.set_yticklabels(regions, fontsize=8)
ax.tick_params(axis="x", colors=INK_SOFT, pad=2)
ax.tick_params(axis="y", colors=INK_SOFT, pad=2)
ax.tick_params(axis="z", labelsize=8, colors=INK_SOFT)
ax.set_zlim(0, top * 1.1)

ax.set_xlabel(PRODUCT, fontsize=10, color=INK, labelpad=8)
ax.set_ylabel(REGION, fontsize=10, color=INK, labelpad=8)
ax.set_zlabel(UNITS, fontsize=10, color=INK, labelpad=6)
ax.set_title("bar-3d-categorical · python · seaborn · anyplot.ai", fontsize=12, fontweight="medium", color=INK, pad=4)

ax.view_init(elev=30, azim=45)

# Base-plane and wall grid lines, subtle; panes transparent
ax.grid(True)
for axis in (ax.xaxis, ax.yaxis, ax.zaxis):
    axis.pane.fill = False
    axis.pane.set_edgecolor(INK_SOFT)
    axis.pane.set_alpha(0.25)
    axis._axinfo["grid"].update(color=INK, alpha=0.18, linewidth=0.6)

patches = [mpatches.Patch(color=colors[p], label=p) for p in products]
legend = ax.legend(
    handles=patches,
    loc="upper right",
    fontsize=8,
    title=PRODUCT,
    title_fontsize=9,
    facecolor=ELEVATED_BG,
    edgecolor=INK_SOFT,
    labelcolor=INK_SOFT,
)
legend.get_title().set_color(INK)

plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
