"""anyplot.ai
radar-multi: Multi-Series Radar Chart
Library: seaborn 0.13.2 | Python 3.13.13
Quality: 89/100 | Updated: 2026-05-07
"""

import os
import sys


# Remove current directory from path to avoid import shadowing
if "" in sys.path:
    sys.path.remove("")
if "." in sys.path:
    sys.path.remove(".")

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

# Imprint palette (first series always #009E73)
IMPRINT = ["#009E73", "#C475FD", "#4467A3"]

# Set seaborn theme with theme-adaptive colors
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
sns.set_context("talk", font_scale=1.2)

# Data - Product comparison across quality dimensions
categories = ["Performance", "Reliability", "Usability", "Features", "Support", "Value"]
n_categories = len(categories)

# Three products with more dramatic variation to showcase radar strengths
products = {
    "Product A": [92, 88, 72, 78, 65, 90],
    "Product B": [65, 70, 95, 88, 85, 60],
    "Product C": [75, 58, 82, 65, 92, 72],
}

# Calculate angles for each axis
angles = np.linspace(0, 2 * np.pi, n_categories, endpoint=False).tolist()
angles += angles[:1]  # Close the polygon

# Create figure with polar subplot (square format for radar) — canonical 2400x2400 canvas
fig, ax = plt.subplots(figsize=(6, 6), dpi=400, subplot_kw={"projection": "polar"}, facecolor=PAGE_BG)

# Plot each product series
for idx, (product_name, values) in enumerate(products.items()):
    values_closed = values + values[:1]  # Close the polygon

    # Fill with transparency
    ax.fill(angles, values_closed, alpha=0.25, color=IMPRINT[idx], label=product_name)

    # Outline with larger markers
    ax.plot(angles, values_closed, "o-", linewidth=2.5, markersize=8, color=IMPRINT[idx])

# Set category labels on each axis
ax.set_xticks(angles[:-1])
ax.set_xticklabels(categories, fontsize=11, color=INK)

# Set radial ticks and limits
ax.set_ylim(0, 100)
ax.set_yticks([20, 40, 60, 80, 100])
ax.set_yticklabels(["20", "40", "60", "80", "100"], fontsize=9, color=INK_SOFT)

# Style gridlines
ax.yaxis.grid(True, linestyle="--", alpha=0.15, linewidth=0.8, color=INK)
ax.xaxis.grid(True, linestyle="-", alpha=0.08, linewidth=0.8, color=INK)

# Style spines
for spine in ax.spines.values():
    spine.set_color(INK_SOFT)
    spine.set_linewidth(1.5)

# Title — the mandated "radar-multi · python · seaborn · anyplot.ai" is 43 chars,
# under the 67-char baseline, so the style-guide default fontsize (12pt) applies unscaled.
# fig.suptitle (not ax.set_title) keeps the title clear of the top axis label and the legend.
fig.suptitle("radar-multi · python · seaborn · anyplot.ai", y=0.98, fontsize=12, fontweight="medium", color=INK)

# Add legend with theme-adaptive styling, placed below the plot clear of the axis labels
legend = ax.legend(
    loc="upper center",
    bbox_to_anchor=(0.5, -0.08),
    ncol=3,
    fontsize=9,
    framealpha=0.95,
    facecolor=ELEVATED_BG,
    edgecolor=INK_SOFT,
)
legend.get_frame().set_linewidth(1)

fig.subplots_adjust(top=0.86, bottom=0.16, left=0.08, right=0.92)
plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)  # bbox_inches MUST stay default (None)
