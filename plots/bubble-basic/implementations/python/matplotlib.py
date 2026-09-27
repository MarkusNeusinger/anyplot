"""anyplot.ai
bubble-basic: Basic Bubble Chart
Library: matplotlib 3.11.2 | Python 3.13.15
Quality: 89/100 | Updated: 2026-09-27
"""

import os

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.ticker import FuncFormatter, NullLocator
from mpl_toolkits.axes_grid1.inset_locator import inset_axes


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Imprint palette — 8 hues, canonical order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Data — retail product portfolio: price vs quality rating, sales volume as bubble size
np.random.seed(42)

category_specs = [
    {
        "name": "Electronics",
        "price_mean": 320,
        "price_std": 170,
        "quality_mean": 7.2,
        "quality_std": 1.0,
        "sales_mean": 45,
        "sales_std": 22,
        "n": 24,
    },
    {
        "name": "Furniture",
        "price_mean": 680,
        "price_std": 240,
        "quality_mean": 6.7,
        "quality_std": 1.2,
        "sales_mean": 18,
        "sales_std": 9,
        "n": 20,
    },
    {
        "name": "Kitchenware",
        "price_mean": 55,
        "price_std": 30,
        "quality_mean": 6.1,
        "quality_std": 1.4,
        "sales_mean": 68,
        "sales_std": 32,
        "n": 26,
    },
    {
        "name": "Outdoor Gear",
        "price_mean": 190,
        "price_std": 85,
        "quality_mean": 7.6,
        "quality_std": 0.9,
        "sales_mean": 30,
        "sales_std": 14,
        "n": 20,
    },
]

price_parts, quality_parts, sales_parts, category_parts = [], [], [], []
for spec in category_specs:
    n = spec["n"]
    price_parts.append(np.random.normal(spec["price_mean"], spec["price_std"], n))
    quality_parts.append(np.random.normal(spec["quality_mean"], spec["quality_std"], n))
    sales_parts.append(np.random.normal(spec["sales_mean"], spec["sales_std"], n))
    category_parts.extend([spec["name"]] * n)

price = np.clip(np.concatenate(price_parts), 8, 1200)
quality_rating = np.clip(np.concatenate(quality_parts), 1, 10)
sales_volume = np.clip(np.concatenate(sales_parts), 3, 130)
category = np.array(category_parts)

category_names = [spec["name"] for spec in category_specs]
category_colors = IMPRINT_PALETTE[:4]

# Scale bubble sizes by area for accurate visual perception (tuned for 3200×1800 canvas).
size_scaled = (sales_volume / sales_volume.max()) * 380 + 25

# Plot
fig, ax = plt.subplots(figsize=(8, 4.5), dpi=400, facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

for name, color in zip(category_names, category_colors, strict=True):
    mask = category == name
    ax.scatter(
        price[mask],
        quality_rating[mask],
        s=size_scaled[mask],
        alpha=0.5,
        color=color,
        edgecolors=PAGE_BG,
        linewidths=0.8,
        label=name,
        zorder=3,
    )

# Size legend — a real inset panel (matplotlib-native technique), placed in the
# one clear gap in the data (high price, low quality) so it never covers bubbles
legend_caps = [15, 60, 120]
legend_ax = inset_axes(
    ax,
    width="20%",
    height="30%",
    loc="lower left",
    bbox_to_anchor=(0.62, 0.04, 1, 1),
    bbox_transform=ax.transAxes,
    borderpad=0,
)
legend_ax.set_facecolor(ELEVATED_BG)
legend_ax.set_xlim(0, 1)
legend_ax.set_ylim(0, 1)
legend_ax.set_xticks([])
legend_ax.set_yticks([])
for spine in legend_ax.spines.values():
    spine.set_color(INK_SOFT)
    spine.set_linewidth(0.8)
legend_ax.set_title("Sales Volume", fontsize=10, fontweight="bold", color=INK, loc="left", pad=4)
for cap, y in zip(legend_caps, (0.18, 0.5, 0.84), strict=True):
    legend_ax.scatter(
        0.28,
        y,
        s=(cap / sales_volume.max()) * 380 + 25,
        color=INK_MUTED,
        alpha=0.5,
        edgecolors=PAGE_BG,
        linewidths=0.8,
        transform=legend_ax.transAxes,
        clip_on=False,
    )
    legend_ax.text(0.55, y, f"{cap}K units", fontsize=9, color=INK_SOFT, va="center", transform=legend_ax.transAxes)

# Category color legend — upper right, bold title leads the eye ahead of the body text
category_legend = ax.legend(
    fontsize=9,
    loc="upper right",
    framealpha=1.0,
    facecolor=ELEVATED_BG,
    edgecolor=INK_SOFT,
    title="Product Category",
    title_fontsize=10,
    markerscale=0.7,
    handletextpad=0.5,
    borderpad=0.7,
)
plt.setp(category_legend.get_title(), color=INK, fontweight="bold")
plt.setp(category_legend.get_texts(), color=INK_SOFT)

# Focal-point annotation — call out the standout premium Electronics bubble
# (highest price x quality among its category) to sharpen the storytelling
# beyond color/size hierarchy alone.
electronics_mask = category == "Electronics"
standout_local_idx = np.argmax(price[electronics_mask] * quality_rating[electronics_mask])
standout_x = price[electronics_mask][standout_local_idx]
standout_y = quality_rating[electronics_mask][standout_local_idx]
ax.annotate(
    "Premium standout",
    xy=(standout_x, standout_y),
    xytext=(standout_x * 0.57, standout_y - 1.6),
    fontsize=9,
    color=INK_SOFT,
    ha="right",
    arrowprops={"arrowstyle": "-", "color": INK_SOFT, "linewidth": 0.8},
    bbox={"facecolor": ELEVATED_BG, "edgecolor": INK_SOFT, "linewidth": 0.6, "boxstyle": "round,pad=0.3"},
    zorder=4,
)

# Style — descriptive prefix clarifies the retail domain; title fontsize scales
# down since the prefix pushes past the 67-char baseline the style-guide default
# is tuned for.
title = "Retail Product Portfolio · bubble-basic · python · matplotlib · anyplot.ai"
title_fontsize = max(8, round(12 * 67 / len(title))) if len(title) > 67 else 12
ax.set_xlabel("Retail Price ($, log scale)", fontsize=10, color=INK, labelpad=8)
ax.set_ylabel("Customer Quality Rating (1–10)", fontsize=10, color=INK, labelpad=8)
ax.set_title(title, fontsize=title_fontsize, fontweight="medium", color=INK, pad=12)
ax.tick_params(axis="both", labelsize=8, labelcolor=INK_SOFT, length=0)

for spine in ax.spines.values():
    spine.set_visible(False)

ax.yaxis.grid(True, alpha=0.15, linewidth=0.8, color=INK, zorder=0)
ax.xaxis.grid(False)

# Log x-axis: retail price is heavily right-skewed (Kitchenware ~$55 mean vs
# Furniture ~$680 mean), so a linear axis crushes the low-price cluster into an
# unreadable clump. Log spacing gives that region room to breathe while keeping
# the high-price tail proportionate.
ax.set_xscale("log")
ax.set_xlim(7, 1400)
ax.set_xticks([10, 30, 100, 300, 1000])
ax.xaxis.set_minor_locator(NullLocator())
ax.xaxis.set_major_formatter(FuncFormatter(lambda v, _: f"${v:,.0f}"))
ax.set_ylim(1, 10.8)

fig.subplots_adjust(left=0.09, right=0.97, top=0.92, bottom=0.12)

# Save
plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
