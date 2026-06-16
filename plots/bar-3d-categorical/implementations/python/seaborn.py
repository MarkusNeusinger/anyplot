""" anyplot.ai
bar-3d-categorical: 3D Bar Chart for Categorical Comparison
Library: seaborn 0.13.2 | Python 3.13.13
Quality: 85/100 | Created: 2026-05-15
"""

import os

import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

IMPRINT = ["#009E73", "#C475FD", "#4467A3", "#BD8233"]

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

# Data — quarterly unit sales (thousands) by product category and region
np.random.seed(42)

products = ["Laptops", "Tablets", "Phones", "Monitors"]
regions = ["North", "South", "East", "West"]
n_prod = len(products)
n_reg = len(regions)

sales_base = np.array(
    [[45.2, 31.8, 38.5, 27.9], [22.1, 18.4, 25.3, 20.1], [68.7, 55.2, 72.1, 60.8], [15.3, 11.9, 18.2, 13.7]]
)
sales = sales_base + np.random.normal(0, 1.2, (n_prod, n_reg))

# Plot
fig = plt.figure(figsize=(16, 9), facecolor=PAGE_BG)
ax = fig.add_subplot(111, projection="3d")

bar_w = 0.55
bar_d = 0.55

for i, (_product, color) in enumerate(zip(products, IMPRINT, strict=False)):
    for j in range(n_reg):
        h = sales[i, j]
        ax.bar3d(i - bar_w / 2, j - bar_d / 2, 0, bar_w, bar_d, h, color=color, alpha=0.85, shade=True)
        ax.text(i, j, h + 1.5, f"{h:.0f}", ha="center", va="bottom", fontsize=11, color=INK, fontweight="medium")

# Style — axis ticks and labels
ax.set_xticks(range(n_prod))
ax.set_xticklabels(products, fontsize=14)
ax.set_yticks(range(n_reg))
ax.set_yticklabels(regions, fontsize=14)
ax.tick_params(axis="x", colors=INK_SOFT, pad=6)
ax.tick_params(axis="y", colors=INK_SOFT, pad=6)
ax.tick_params(axis="z", labelsize=14, colors=INK_SOFT)

ax.set_xlabel("Product Category", fontsize=18, color=INK, labelpad=18)
ax.set_ylabel("Region", fontsize=18, color=INK, labelpad=18)
ax.set_zlabel("Units Sold (thousands)", fontsize=18, color=INK, labelpad=12)

ax.set_title("bar-3d-categorical · seaborn · anyplot.ai", fontsize=22, fontweight="medium", color=INK, pad=22)

ax.view_init(elev=30, azim=45)

# Pane backgrounds — transparent with subtle edges
for pane in (ax.xaxis.pane, ax.yaxis.pane, ax.zaxis.pane):
    pane.fill = False
    pane.set_edgecolor(INK_SOFT)
    pane.set_alpha(0.25)

# Legend
patches = [mpatches.Patch(color=IMPRINT[i], label=p) for i, p in enumerate(products)]
legend = ax.legend(
    handles=patches,
    loc="upper left",
    fontsize=14,
    title="Product",
    title_fontsize=15,
    facecolor=ELEVATED_BG,
    edgecolor=INK_SOFT,
    labelcolor=INK_SOFT,
)
legend.get_title().set_color(INK)

# Save
plt.savefig(f"plot-{THEME}.png", dpi=300, bbox_inches="tight", facecolor=PAGE_BG)
