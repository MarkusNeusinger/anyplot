""" anyplot.ai
linked-views-selection: Multiple Linked Views with Selection Sync
Library: matplotlib 3.10.9 | Python 3.13.13
Quality: 96/100 | Created: 2026-05-17
"""

import os
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.patches import Patch


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Okabe-Ito palette
IMPRINT = ["#009E73", "#C475FD", "#4467A3", "#BD8233"]
BRAND = IMPRINT[0]

# Data
np.random.seed(42)
n = 300
x = np.random.normal(50, 15, n)
y = x * 0.7 + np.random.normal(0, 10, n)
categories = np.random.choice(["Group A", "Group B", "Group C", "Group D"], n)
df = pd.DataFrame({"x": x, "y": y, "category": categories})

# Highlight one category to demonstrate linked views concept
highlighted_category = "Group A"
is_selected = df["category"] == highlighted_category

# Plot
fig = plt.figure(figsize=(16, 9), facecolor=PAGE_BG)
gs = fig.add_gridspec(2, 3, hspace=0.3, wspace=0.3)

ax_scatter = fig.add_subplot(gs[:, 0:2])
ax_hist_x = fig.add_subplot(gs[0, 2])
ax_hist_y = fig.add_subplot(gs[1, 2])

# Set background for all axes
ax_scatter.set_facecolor(PAGE_BG)
ax_hist_x.set_facecolor(PAGE_BG)
ax_hist_y.set_facecolor(PAGE_BG)

# Scatter plot: full data with deemphasized points, selected highlighted
ax_scatter.scatter(df["x"], df["y"], alpha=0.15, s=100, color=INK_SOFT, edgecolors="none")
ax_scatter.scatter(
    df[is_selected]["x"], df[is_selected]["y"], alpha=0.8, s=150, color=BRAND, edgecolors=PAGE_BG, linewidth=0.5
)

ax_scatter.set_xlabel("X Dimension", fontsize=20, color=INK)
ax_scatter.set_ylabel("Y Dimension", fontsize=20, color=INK)
ax_scatter.set_title("Scatter Plot", fontsize=18, color=INK_SOFT)
ax_scatter.tick_params(axis="both", labelsize=16, colors=INK_SOFT)
ax_scatter.spines["top"].set_visible(False)
ax_scatter.spines["right"].set_visible(False)
for s in ("left", "bottom"):
    ax_scatter.spines[s].set_color(INK_SOFT)
ax_scatter.yaxis.grid(True, alpha=0.10, linewidth=0.8, color=INK)

# Histogram of X dimension
bins = np.linspace(df["x"].min(), df["x"].max(), 20)
ax_hist_x.hist(df["x"], bins=bins, alpha=0.15, color=INK_SOFT, edgecolor="none")
ax_hist_x.hist(df[is_selected]["x"], bins=bins, alpha=0.8, color=BRAND, edgecolor="none")
ax_hist_x.set_xlabel("X", fontsize=16, color=INK)
ax_hist_x.set_ylabel("Count", fontsize=16, color=INK)
ax_hist_x.set_title("X Distribution", fontsize=18, color=INK_SOFT)
ax_hist_x.tick_params(axis="both", labelsize=14, colors=INK_SOFT)
ax_hist_x.spines["top"].set_visible(False)
ax_hist_x.spines["right"].set_visible(False)
for s in ("left", "bottom"):
    ax_hist_x.spines[s].set_color(INK_SOFT)

# Histogram of Y dimension
bins = np.linspace(df["y"].min(), df["y"].max(), 20)
ax_hist_y.hist(df["y"], bins=bins, alpha=0.15, color=INK_SOFT, edgecolor="none")
ax_hist_y.hist(df[is_selected]["y"], bins=bins, alpha=0.8, color=BRAND, edgecolor="none")
ax_hist_y.set_xlabel("Y", fontsize=16, color=INK)
ax_hist_y.set_ylabel("Count", fontsize=16, color=INK)
ax_hist_y.set_title("Y Distribution", fontsize=18, color=INK_SOFT)
ax_hist_y.tick_params(axis="both", labelsize=14, colors=INK_SOFT)
ax_hist_y.spines["top"].set_visible(False)
ax_hist_y.spines["right"].set_visible(False)
for s in ("left", "bottom"):
    ax_hist_y.spines[s].set_color(INK_SOFT)

# Main title
fig.suptitle("linked-views-selection · matplotlib · anyplot.ai", fontsize=24, fontweight="medium", color=INK, y=0.98)

# Add legend to explain highlighting
legend_elements = [
    Patch(facecolor=INK_SOFT, alpha=0.15, label="Other data"),
    Patch(facecolor=BRAND, alpha=0.8, label=f"Selected: {highlighted_category}"),
]
fig.legend(
    handles=legend_elements,
    loc="lower center",
    fontsize=16,
    frameon=True,
    fancybox=False,
    shadow=False,
    bbox_to_anchor=(0.5, -0.02),
    facecolor=ELEVATED_BG,
    edgecolor=INK_SOFT,
)

script_dir = Path(__file__).parent
output_path = script_dir / f"plot-{THEME}.png"
plt.savefig(output_path, dpi=300, bbox_inches="tight", facecolor=PAGE_BG)
