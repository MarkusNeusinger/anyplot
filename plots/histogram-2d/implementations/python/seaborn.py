""" anyplot.ai
histogram-2d: 2D Histogram Heatmap
Library: seaborn 0.13.2 | Python 3.13.13
Quality: 91/100 | Updated: 2026-05-08
"""

import os

import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Set theme
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

# Data - Customer behavior: age vs. annual spending (physics experiment context)
# Using a real-world distribution of customer data with correlation
np.random.seed(42)
n_points = 3000
age = np.random.normal(45, 15, n_points)
age = np.clip(age, 18, 75)  # Realistic age range
spending = 500 + 8 * (age - 18) + np.random.normal(0, 800, n_points)
spending = np.clip(spending, 0, 6000)  # Realistic spending range

# Create figure with marginal histograms using JointGrid
g = sns.JointGrid(x=age, y=spending, height=10, ratio=5, space=0.2)

# Plot 2D histogram heatmap with improved bin sizing
sns.histplot(x=age, y=spending, bins=35, cmap="viridis", cbar=True, cbar_kws={"label": "Customer Count"}, ax=g.ax_joint)

# Plot marginal 1D histograms with theme-adaptive color
marginal_color = "#009E73"  # Okabe-Ito brand green
sns.histplot(x=age, bins=30, color=marginal_color, alpha=0.7, edgecolor=PAGE_BG, linewidth=0.5, ax=g.ax_marg_x)
sns.histplot(y=spending, bins=30, color=marginal_color, alpha=0.7, edgecolor=PAGE_BG, linewidth=0.5, ax=g.ax_marg_y)

# Styling - scale fonts for large canvas
g.ax_joint.set_xlabel("Customer Age (years)", fontsize=20, color=INK, labelpad=10)
g.ax_joint.set_ylabel("Annual Spending ($)", fontsize=20, color=INK, labelpad=10)
g.ax_joint.tick_params(axis="both", labelsize=16, colors=INK_SOFT)

# Style colorbar
cbar = g.ax_joint.collections[0].colorbar
cbar.ax.tick_params(labelsize=14, colors=INK_SOFT)
cbar.ax.yaxis.label.set_size(16)
cbar.ax.yaxis.label.set_color(INK)

# Title
g.figure.suptitle("histogram-2d · seaborn · anyplot.ai", fontsize=24, y=0.98, color=INK)

# Hide marginal axis labels for cleaner look
g.ax_marg_x.set_ylabel("")
g.ax_marg_y.set_xlabel("")
g.ax_marg_x.tick_params(labelsize=12, colors=INK_SOFT)
g.ax_marg_y.tick_params(labelsize=12, colors=INK_SOFT)

# Adjust layout for better spacing
g.figure.set_size_inches(16, 9)
g.figure.tight_layout()
g.figure.subplots_adjust(top=0.93)

# Save at 4800x2700
plt.savefig(f"plot-{THEME}.png", dpi=300, bbox_inches="tight", facecolor=PAGE_BG)
plt.close()
